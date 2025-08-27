#!/usr/bin/env python3
"""
Script to plot arrival data from dataset_arrivals.json with smoothing options.
Shows both raw data and smoothened curves to visualize trends over time.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os

# Try to import optional packages
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from scipy.signal import savgol_filter
    from scipy.ndimage import gaussian_filter1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

def load_arrival_data(filename):
    """Load arrival data from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return data['days']

def prepare_data(arrival_data):
    """Convert arrival data to pandas DataFrame for easier manipulation"""
    dates = [datetime.strptime(day['date'], '%Y-%m-%d') for day in arrival_data]
    arrivals = [day['arrivals'] for day in arrival_data]
    lambda_per_sec = [day['lambda_per_sec'] for day in arrival_data]
    
    if HAS_PANDAS:
        df = pd.DataFrame({
            'date': dates,
            'arrivals': arrivals,
            'lambda_per_sec': lambda_per_sec
        })
        return df
    else:
        # Fallback to dictionary format
        return {
            'date': dates,
            'arrivals': arrivals,
            'lambda_per_sec': lambda_per_sec
        }

def smooth_data(data, method='gaussian', **kwargs):
    """
    Apply smoothing to data using various methods
    
    Methods:
    - 'gaussian': Simple Gaussian-like smoothing
    - 'rolling': Rolling average 
    - 'savgol': Savitzky-Golay filter (requires scipy)
    """
    
    if method == 'gaussian':
        # Simple gaussian-like smoothing using convolution
        sigma = kwargs.get('sigma', 1.5)
        if HAS_SCIPY:
            return gaussian_filter1d(data, sigma=sigma)
        else:
            # Fallback: use a simple moving average
            window = max(1, int(sigma * 2))
            if window >= len(data):
                window = len(data) // 3
            if window < 1:
                return data
            
            # Pad data for edge handling
            padded = np.concatenate([
                np.full(window//2, data[0]),
                data,
                np.full(window//2, data[-1])
            ])
            
            # Apply moving average
            smoothed = np.convolve(padded, np.ones(window)/window, mode='valid')
            return smoothed
    
    elif method == 'savgol':
        if not HAS_SCIPY:
            print("Warning: scipy not available, falling back to gaussian smoothing")
            return smooth_data(data, method='gaussian', **kwargs)
            
        window_length = kwargs.get('window_length', 7)
        polyorder = kwargs.get('polyorder', 3)
        # Ensure window_length is odd and smaller than data length
        window_length = min(window_length, len(data))
        if window_length % 2 == 0:
            window_length -= 1
        polyorder = min(polyorder, window_length - 1)
        return savgol_filter(data, window_length, polyorder)
    
    elif method == 'rolling':
        window = kwargs.get('window', 7)
        window = min(window, len(data))
        
        if HAS_PANDAS:
            df = pd.DataFrame({'data': data})
            return df['data'].rolling(window=window, center=True).mean().bfill().ffill().values
        else:
            # Manual rolling average
            result = np.zeros_like(data, dtype=float)
            half_window = window // 2
            
            for i in range(len(data)):
                start = max(0, i - half_window)
                end = min(len(data), i + half_window + 1)
                result[i] = np.mean(data[start:end])
            
            return result
    
    else:
        raise ValueError(f"Unknown smoothing method: {method}")

def plot_arrivals_analysis(df, output_dir="arrival_analysis_graphs"):
    """Create comprehensive arrival analysis plots"""
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Set up the plotting style
    plt.style.use('default')
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    
    # 1. Main arrivals plot with multiple smoothing methods
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    fig.suptitle('Daily Arrivals Analysis - Raw Data vs Smoothed Trends', fontsize=16)
    
    # Plot raw data
    ax1.plot(df['date'], df['arrivals'], 'o-', alpha=0.6, color='lightblue', 
             markersize=3, linewidth=1, label='Raw Data')
    
    # Apply different smoothing methods
    smoothing_methods = [
        {'method': 'gaussian', 'sigma': 2, 'color': 'red', 'label': 'Gaussian (σ=2)'},
        {'method': 'savgol', 'window_length': 11, 'polyorder': 3, 'color': 'green', 'label': 'Savitzky-Golay'},
        {'method': 'rolling', 'window': 7, 'color': 'orange', 'label': 'Rolling Average (7 days)'}
    ]
    
    for smooth_config in smoothing_methods:
        method = smooth_config.pop('method')
        color = smooth_config.pop('color')
        label = smooth_config.pop('label')
        
        smoothed = smooth_data(df['arrivals'].values, method=method, **smooth_config)
        ax1.plot(df['date'], smoothed, '-', color=color, linewidth=2, label=label)
    
    ax1.set_title('Daily Arrivals Over Time')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Number of Arrivals')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Add statistics text
    stats_text = f"""Statistics:
    Max: {df['arrivals'].max():,}
    Min: {df['arrivals'].min():,}
    Mean: {df['arrivals'].mean():.0f}
    Std: {df['arrivals'].std():.0f}"""
    
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Plot lambda per second
    ax2.plot(df['date'], df['lambda_per_sec'], 'o-', alpha=0.6, color='lightcoral', 
             markersize=3, linewidth=1, label='Raw λ/sec')
    
    # Smooth lambda data
    smoothed_lambda = smooth_data(df['lambda_per_sec'].values, method='gaussian', sigma=2)
    ax2.plot(df['date'], smoothed_lambda, '-', color='darkred', linewidth=2, label='Smoothed λ/sec')
    
    ax2.set_title('Arrival Rate (λ per second)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Arrivals per Second')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/arrivals_overview.png', bbox_inches='tight')
    plt.close()
    
    # 2. Seasonal/Weekly patterns analysis
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Arrival Patterns Analysis', fontsize=16)
    
    # Add day of week
    df['day_of_week'] = df['date'].dt.day_name()
    df['week_number'] = df['date'].dt.isocalendar().week
    df['month'] = df['date'].dt.month
    
    # Weekly pattern
    weekly_avg = df.groupby('day_of_week')['arrivals'].mean()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_avg = weekly_avg.reindex(day_order)
    
    ax1.bar(weekly_avg.index, weekly_avg.values, color='lightblue', alpha=0.7)
    ax1.set_title('Average Arrivals by Day of Week')
    ax1.set_ylabel('Average Arrivals')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Monthly trend
    monthly_avg = df.groupby('month')['arrivals'].mean()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    ax2.plot(monthly_avg.index, monthly_avg.values, 'o-', color='green', linewidth=2, markersize=6)
    ax2.set_title('Average Arrivals by Month')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Average Arrivals')
    # Only set tick labels for months that exist in the data
    ax2.set_xticks(monthly_avg.index)
    ax2.set_xticklabels([month_names[i-1] for i in monthly_avg.index])
    ax2.grid(True, alpha=0.3)
    
    # Distribution histogram
    ax3.hist(df['arrivals'], bins=30, alpha=0.7, color='orange', edgecolor='black')
    ax3.axvline(df['arrivals'].mean(), color='red', linestyle='--', 
                label=f'Mean: {df["arrivals"].mean():.0f}')
    ax3.axvline(df['arrivals'].median(), color='blue', linestyle='--', 
                label=f'Median: {df["arrivals"].median():.0f}')
    ax3.set_title('Distribution of Daily Arrivals')
    ax3.set_xlabel('Number of Arrivals')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Correlation between consecutive days
    df['arrivals_prev'] = df['arrivals'].shift(1)
    ax4.scatter(df['arrivals_prev'], df['arrivals'], alpha=0.6, color='purple')
    
    # Add trend line
    mask = ~np.isnan(df['arrivals_prev'])
    if mask.sum() > 1:
        correlation = np.corrcoef(df['arrivals_prev'][mask], df['arrivals'][mask])[0, 1]
        z = np.polyfit(df['arrivals_prev'][mask], df['arrivals'][mask], 1)
        p = np.poly1d(z)
        ax4.plot(df['arrivals_prev'][mask], p(df['arrivals_prev'][mask]), 
                "r--", alpha=0.8, label=f'Correlation: {correlation:.3f}')
    
    ax4.set_title('Day-to-Day Arrival Correlation')
    ax4.set_xlabel('Previous Day Arrivals')
    ax4.set_ylabel('Current Day Arrivals')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/arrival_patterns.png', bbox_inches='tight')
    plt.close()
    
    # 3. Trend decomposition-style plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
    fig.suptitle('Arrival Trend Decomposition', fontsize=16)
    
    # Original data
    ax1.plot(df['date'], df['arrivals'], color='blue', alpha=0.7, linewidth=1)
    ax1.set_title('Original Data')
    ax1.set_ylabel('Arrivals')
    ax1.grid(True, alpha=0.3)
    
    # Long-term trend (heavy smoothing)
    long_trend = smooth_data(df['arrivals'].values, method='gaussian', sigma=10)
    ax2.plot(df['date'], long_trend, color='red', linewidth=2)
    ax2.set_title('Long-term Trend (Heavily Smoothed)')
    ax2.set_ylabel('Arrivals')
    ax2.grid(True, alpha=0.3)
    
    # Residuals (original - trend)
    residuals = df['arrivals'].values - long_trend
    ax3.plot(df['date'], residuals, color='green', alpha=0.7, linewidth=1)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.set_title('Residuals (Original - Trend)')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Residual Arrivals')
    ax3.grid(True, alpha=0.3)
    
    for ax in [ax1, ax2, ax3]:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/trend_decomposition.png', bbox_inches='tight')
    plt.close()
    
    return df

def generate_summary_report(df, output_dir):
    """Generate a summary report of the analysis"""
    report_path = os.path.join(output_dir, 'arrival_analysis_report.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("ARRIVAL DATA ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Analysis Period: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\n")
        f.write(f"Total Days: {len(df)}\n\n")
        
        f.write("ARRIVAL STATISTICS:\n")
        f.write(f"  Total Arrivals: {df['arrivals'].sum():,}\n")
        f.write(f"  Average Daily Arrivals: {df['arrivals'].mean():.0f}\n")
        f.write(f"  Median Daily Arrivals: {df['arrivals'].median():.0f}\n")
        f.write(f"  Maximum Daily Arrivals: {df['arrivals'].max():,}\n")
        f.write(f"  Minimum Daily Arrivals: {df['arrivals'].min():,}\n")
        f.write(f"  Standard Deviation: {df['arrivals'].std():.0f}\n\n")
        
        f.write("ARRIVAL RATE (λ/sec) STATISTICS:\n")
        f.write(f"  Average λ/sec: {df['lambda_per_sec'].mean():.4f}\n")
        f.write(f"  Maximum λ/sec: {df['lambda_per_sec'].max():.4f}\n")
        f.write(f"  Minimum λ/sec: {df['lambda_per_sec'].min():.4f}\n\n")
        
        # Weekly patterns
        weekly_avg = df.groupby('day_of_week')['arrivals'].mean()
        f.write("WEEKLY PATTERNS:\n")
        for day, avg in weekly_avg.items():
            f.write(f"  {day}: {avg:.0f} arrivals\n")
        f.write("\n")
        
        # Monthly patterns
        monthly_avg = df.groupby('month')['arrivals'].mean()
        month_names = {5: 'May', 6: 'June', 7: 'July', 8: 'August', 9: 'September'}
        f.write("MONTHLY PATTERNS:\n")
        for month, avg in monthly_avg.items():
            month_name = month_names.get(month, f"Month {month}")
            f.write(f"  {month_name}: {avg:.0f} arrivals\n")
        f.write("\n")
        
        f.write("GENERATED FILES:\n")
        f.write("  - arrivals_overview.png: Main trends and smoothed curves\n")
        f.write("  - arrival_patterns.png: Weekly, monthly, and distribution analysis\n")
        f.write("  - trend_decomposition.png: Long-term trend analysis\n")
        f.write("  - arrival_analysis_report.txt: This summary report\n")

def main():
    """Main function to run the arrival analysis"""
    # File paths
    input_file = "../conf/dataset_arrivals.json"
    output_dir = "arrival_analysis_graphs"
    
    print("Loading arrival data...")
    try:
        arrival_data = load_arrival_data(input_file)
        print(f"Loaded {len(arrival_data)} days of data")
        
        print("Preparing data for analysis...")
        df = prepare_data(arrival_data)
        
        print("Generating plots...")
        df = plot_arrivals_analysis(df, output_dir)
        
        print("Generating summary report...")
        generate_summary_report(df, output_dir)
        
        print(f"\nAnalysis complete!")
        print(f"Results saved to: {output_dir}/")
        print(f"Generated files:")
        print(f"  - arrivals_overview.png")
        print(f"  - arrival_patterns.png") 
        print(f"  - trend_decomposition.png")
        print(f"  - arrival_analysis_report.txt")
        
        # Print some key insights
        print(f"\nKey Insights:")
        print(f"  - Peak arrivals: {df['arrivals'].max():,} on {df.loc[df['arrivals'].idxmax(), 'date'].strftime('%Y-%m-%d')}")
        print(f"  - Lowest arrivals: {df['arrivals'].min():,} on {df.loc[df['arrivals'].idxmin(), 'date'].strftime('%Y-%m-%d')}")
        print(f"  - Average daily arrivals: {df['arrivals'].mean():.0f}")
        print(f"  - Data shows clear temporal patterns and seasonal trends")
        
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        print("Make sure you're running this script from the src/ directory")
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
