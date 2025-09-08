#-------------------------------------------------------------------------- 
# This is a Python library for generating random variates from additional 
# continuous distributions not included in the main rvgs.py library
#
# Additional continuous distributions:
#
#     BoundedPareto(a, k, l, h)    l <= x <= h     
#
# For a Bounded Pareto(a, k, l, h) random variable:
#   - a: shape parameter (a > 0)
#   - k: scale parameter (k > 0)  
#   - l: lower bound (l >= k)
#   - h: upper bound (h > l)
#
# The distribution is bounded between l and h, unlike the standard Pareto
# which has support from k to infinity.
#--------------------------------------------------------------------------

from desPython.rngs import random
from math import log, pow

def denormalize_value(normalized_value, original_l, original_h, normalized_l=0.1, normalized_h=1.0):
    
    original_value = original_l + (original_h - original_l) * (normalized_value - normalized_l) / (normalized_h - normalized_l)
    
    return original_value


def find_best_normalized_pareto_params(original_mean, original_l, original_h, 
                                       normalized_l=0.1, normalized_h=1.0, 
                                       save_plot=True, plot_filename=None,
                                       tolerance=0.01, n_samples=10000, verbose=True):
    #=======================================================================
    # Finds the best parameters (a, k) for a normalized bounded Pareto 
    # distribution that when denormalized matches the target original mean.
    # 
    # Parameters:
    #   original_mean: target mean in original scale
    #   original_l, original_h: original bounds
    #   normalized_l, normalized_h: normalized bounds (default 0.1, 1.0)
    #   save_plot: whether to save verification plot
    #   plot_filename: custom filename for plot (auto-generated if None)
    #   tolerance: acceptable error in mean matching
    #   n_samples: number of samples for empirical testing
    #   verbose: whether to print progress messages (default True)
    #
    # Returns:
    #   tuple: (best_a, best_k) - optimal parameters for normalized distribution
    #=======================================================================
    import matplotlib.pyplot as plt
    import numpy as np
    from datetime import datetime
    
   
    # Calculate target normalized mean
    target_normalized_mean = normalized_l + (normalized_h - normalized_l) * (original_mean - original_l) / (original_h - original_l)
    
    # Test configurations with different (a, k) combinations
    test_configs = []
    a_values = [1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    k_values = [0.001, 0.005, 0.01, 0.02, 0.05]
    
    if verbose:
        print(f"   Testing {len(a_values)} × {len(k_values)} = {len(a_values) * len(k_values)} parameter combinations...")
    
    best_config = None
    best_error = float('inf')
    all_results = []
    
    for a in a_values:
        for k in k_values:
            if k >= normalized_l:  # k must be <= l for valid Pareto
                continue
                
            try:
                normalized_samples = [BoundedPareto(a, k, normalized_l, normalized_h) for _ in range(n_samples)]
                normalized_mean = sum(normalized_samples) / len(normalized_samples)
                
                error = abs(normalized_mean - target_normalized_mean)
                
                denormalized_samples = [denormalize_value(s, original_l, original_h, normalized_l, normalized_h) 
                                      for s in normalized_samples]
                denormalized_mean = sum(denormalized_samples) / len(denormalized_samples)
                original_error = abs(denormalized_mean - original_mean)
                
                result = {
                    'a': a, 'k': k,
                    'normalized_mean': normalized_mean,
                    'denormalized_mean': denormalized_mean,
                    'normalized_error': error,
                    'original_error': original_error,
                    'normalized_samples': normalized_samples[:100],  # Store subset for plotting
                    'denormalized_samples': denormalized_samples[:100]
                }
                all_results.append(result)
                
                if error < best_error:
                    best_error = error
                    best_config = result
                    
            except Exception as e:
                if verbose:
                    print(f"   Warning: Failed for a={a}, k={k}: {e}")
                continue
    
    if best_config is None:
        raise ValueError("Could not find valid parameters. Check your bounds and target mean.")
    
   
    # Create verification plot
    if save_plot:
        if plot_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_filename = f"pareto_fit_verification.png"
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Normalized distribution
        ax1.hist(best_config['normalized_samples'], bins=30, density=True, alpha=0.7, 
                color='blue', edgecolor='black', label=f'a={best_config["a"]}, k={best_config["k"]}')
        ax1.axvline(target_normalized_mean, color='red', linestyle='--', linewidth=2, 
                   label=f'Target: {target_normalized_mean:.3f}')
        ax1.axvline(best_config['normalized_mean'], color='green', linestyle='-', linewidth=2,
                   label=f'Actual: {best_config["normalized_mean"]:.3f}')
        ax1.axvline(normalized_l, color='gray', linestyle='-', alpha=0.5)
        ax1.axvline(normalized_h, color='gray', linestyle='-', alpha=0.5)
        ax1.set_xlabel('Normalized Value')
        ax1.set_ylabel('Density')
        ax1.set_title('Normalized Bounded Pareto Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Denormalized distribution  
        ax2.hist(best_config['denormalized_samples'], bins=30, density=True, alpha=0.7,
                color='orange', edgecolor='black')
        ax2.axvline(original_mean, color='red', linestyle='--', linewidth=2,
                   label=f'Target: {original_mean:,.0f}')
        ax2.axvline(best_config['denormalized_mean'], color='green', linestyle='-', linewidth=2,
                   label=f'Actual: {best_config["denormalized_mean"]:,.0f}')
        ax2.axvline(original_l, color='gray', linestyle='-', alpha=0.5)
        ax2.axvline(original_h, color='gray', linestyle='-', alpha=0.5)
        ax2.set_xlabel('Original Scale Value')
        ax2.set_ylabel('Density')
        ax2.set_title('Denormalized Distribution (Original Scale)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Parameter comparison (error analysis)
        if len(all_results) > 1:
            # Sort results by error for better visualization
            sorted_results = sorted(all_results, key=lambda x: x['normalized_error'])[:10]
            
            config_labels = [f"a={r['a']}, k={r['k']}" for r in sorted_results]
            errors = [r['normalized_error'] for r in sorted_results]
            colors = ['green' if r == best_config else 'lightblue' for r in sorted_results]
            
            bars = ax3.bar(range(len(config_labels)), errors, color=colors, alpha=0.7, edgecolor='black')
            ax3.set_xlabel('Parameter Configuration')
            ax3.set_ylabel('Normalized Mean Error')
            ax3.set_title('Top 10 Parameter Configurations by Error')
            ax3.set_xticks(range(len(config_labels)))
            ax3.set_xticklabels(config_labels, rotation=45, ha='right', fontsize=8)
            ax3.grid(True, alpha=0.3)
            
            # Highlight best configuration
            best_idx = next(i for i, r in enumerate(sorted_results) if r == best_config)
            bars[best_idx].set_color('green')
            bars[best_idx].set_alpha(1.0)
        
        # Plot 4: Empirical CDF comparison
        # Normalized CDF
        norm_sorted = sorted(best_config['normalized_samples'])
        norm_cdf = np.arange(1, len(norm_sorted) + 1) / len(norm_sorted)
        ax4.plot(norm_sorted, norm_cdf, 'b-', linewidth=2, label='Normalized CDF', alpha=0.7)
        
        # Theoretical bounds
        ax4.axvline(normalized_l, color='gray', linestyle='--', alpha=0.5, label='Bounds')
        ax4.axvline(normalized_h, color='gray', linestyle='--', alpha=0.5)
        ax4.axvline(target_normalized_mean, color='red', linestyle='--', alpha=0.7, label='Target Mean')
        
        ax4.set_xlabel('Normalized Value')
        ax4.set_ylabel('Cumulative Probability')
        ax4.set_title('Empirical CDF - Normalized Distribution')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Add overall title and summary
        fig.suptitle(f'Bounded Pareto Parameter Fitting Verification\n' +
                    f'Best: a={best_config["a"]}, k={best_config["k"]} | ' +
                    f'Normalized Error: {best_config["normalized_error"]:.4f} | ' +
                    f'Original Error: {best_config["original_error"]:,.0f}', 
                    fontsize=14)
        
        plt.tight_layout()
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        if verbose:
            print(f"Verification plot saved as: {plot_filename}")
        plt.close()
    
    return best_config['a'], best_config['k']


def generate_denormalized_bounded_pareto(a, k, l, h, original_l, original_h):
   
    normalized_sample = BoundedPareto(a, k, l, h)
    
    original_sample = denormalize_value(normalized_sample, original_l, original_h, l, h)
    
    return original_sample


def BoundedPareto(a, k, l, h):
    #=======================================================================
    # Returns a bounded Pareto distributed positive real number.
    # 
    # Parameters:
    #   a: shape parameter (a > 0)
    #   k: scale parameter (k > 0)
    #   l: lower bound (l >= k) 
    #   h: upper bound (h > l)
    #
    # NOTE: use a > 0, k > 0, l >= k, h > l
    #
    # The bounded Pareto distribution is derived from the standard Pareto
    # by truncating it between the bounds l and h.
    #=======================================================================
    
   
    u = random()
    
    # Compute the CDF values at the bounds
    # F(x) = 1 - (k/x)^a for standard Pareto
    F_l = 1.0 - pow(k / l, a)
    F_h = 1.0 - pow(k / h, a)
    
    # Apply inverse transform sampling for bounded distribution
    # Scale u to the interval [F_l, F_h]
    scaled_u = F_l + u * (F_h - F_l)
    
    # Inverse CDF: x = k / ((1 - F)^(1/a))
    x = k / pow(1.0 - scaled_u, 1.0 / a)
    
    return x





