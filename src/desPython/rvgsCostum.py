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
    #=======================================================================
    # Converts a normalized value back to the original scale.
    # 
    # Parameters:
    #   normalized_value: value from the normalized distribution
    #   original_l: original lower bound
    #   original_h: original upper bound
    #   normalized_l: normalized lower bound (default 0.1)
    #   normalized_h: normalized upper bound (default 1.0)
    #
    # Returns:
    #   value in the original scale
    #=======================================================================
    
    # Reverse the normalization transformation
    # normalized_value = normalized_l + (normalized_h - normalized_l) * (original_value - original_l) / (original_h - original_l)
    # Solving for original_value:
    # original_value = original_l + (original_h - original_l) * (normalized_value - normalized_l) / (normalized_h - normalized_l)
    
    original_value = original_l + (original_h - original_l) * (normalized_value - normalized_l) / (normalized_h - normalized_l)
    return original_value


def generate_denormalized_bounded_pareto(a, k, l, h, original_l, original_h):
    #=======================================================================
    # Generates a bounded Pareto sample and automatically denormalizes it.
    # 
    # This is a convenience function that handles the full process:
    # 1. Generate from normalized distribution
    # 2. Denormalize to original scale
    #
    # Parameters:
    #   a, k, l, h: normalized distribution parameters
    #   original_l, original_h: original bounds for denormalization
    #
    # Returns:
    #   sample in the original scale
    #=======================================================================
    
    # Generate normalized sample
    normalized_sample = BoundedPareto(a, k, l, h)
    
    # Denormalize to original scale
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
    
    # Validate parameters
    if a <= 0:
        raise ValueError("Shape parameter 'a' must be positive")
    if k <= 0:
        raise ValueError("Scale parameter 'k' must be positive")
    if l < k:
        raise ValueError("Lower bound 'l' must be >= scale parameter 'k'")
    if h <= l:
        raise ValueError("Upper bound 'h' must be > lower bound 'l'")
    
    # Generate uniform random variable
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


def BoundedParetoFromMean(target_mean, k, l, h, tolerance=0.01, max_iterations=100):
    #=======================================================================
    # Find the shape parameter 'a' that gives approximately the target mean
    # for a Bounded Pareto distribution with given k, l, h parameters.
    # 
    # Parameters:
    #   target_mean: desired mean value
    #   k: scale parameter (k > 0)
    #   l: lower bound (l >= k)
    #   h: upper bound (h > l)
    #   tolerance: acceptable error in mean (default 0.01)
    #   max_iterations: maximum search iterations (default 100)
    #
    # Returns:
    #   a: shape parameter that achieves approximately the target mean
    #=======================================================================
    
    if target_mean < l or target_mean > h:
        raise ValueError(f"Target mean {target_mean} must be between bounds [{l}, {h}]")
    
    # Binary search for the shape parameter 'a'
    a_low = 0.1   # Lower bound for 'a'
    a_high = 10.0 # Upper bound for 'a'
    
    for iteration in range(max_iterations):
        a_mid = (a_low + a_high) / 2.0
        
        # Generate samples to estimate mean
        n_samples = 1000
        samples = [BoundedPareto(a_mid, k, l, h) for _ in range(n_samples)]
        empirical_mean = sum(samples) / len(samples)
        
        error = abs(empirical_mean - target_mean)
        
        if error < tolerance:
            print(f"Found a = {a_mid:.4f} after {iteration + 1} iterations")
            print(f"Target mean: {target_mean:.4f}, Achieved mean: {empirical_mean:.4f}")
            return a_mid
        
        # Adjust search bounds
        # If empirical mean is too high, increase 'a' (makes distribution more concentrated at lower values)
        # If empirical mean is too low, decrease 'a' (makes distribution more spread out)
        if empirical_mean > target_mean:
            a_low = a_mid
        else:
            a_high = a_mid
    
    # If we reach here, we didn't converge
    a_final = (a_low + a_high) / 2.0
    samples = [BoundedPareto(a_final, k, l, h) for _ in range(1000)]
    final_mean = sum(samples) / len(samples)
    print(f"Warning: Did not converge after {max_iterations} iterations")
    print(f"Best approximation: a = {a_final:.4f}, mean = {final_mean:.4f}")
    return a_final


def BoundedParetoMean(a, k, l, h):
    #=======================================================================
    # Calculates the theoretical mean of a Bounded Pareto distribution.
    # 
    # This is a utility function to verify the correctness of the generator
    # and for analytical comparisons.
    #=======================================================================
    
    if a <= 1:
        raise ValueError("Mean exists only for shape parameter a > 1")
    
    # For bounded Pareto, the mean involves integration of the truncated distribution
    # This is a complex calculation involving incomplete gamma functions
    # For practical purposes, use empirical mean from samples
    
    # Simplified approximation using the relationship with standard Pareto
    F_l = 1.0 - pow(k / l, a)
    F_h = 1.0 - pow(k / h, a)
    
    # Approximate mean (this is a simplified calculation)
    # The exact formula involves hypergeometric functions
    if a > 1:
        mean_approx = (a * k) / (a - 1) * (pow(l, 1-a) - pow(h, 1-a)) / (pow(l, -a) - pow(h, -a))
        return mean_approx
    else:
        return float('inf')


# Test function
def test_bounded_pareto_fits(target_mean, l, h, n_samples=5000, normalize=True):
    #=======================================================================
    # Test function that plots different Bounded Pareto fits for given 
    # target mean, lower bound l, and upper bound h.
    # 
    # Tests various combinations of shape parameter 'a' and scale parameter 'k'
    # to show how they affect the distribution while targeting the same mean.
    #
    # Parameters:
    #   normalize: If True, scales values to [0,1] range for better numerics
    #=======================================================================
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Store original values for display
    orig_mean, orig_l, orig_h = target_mean, l, h
    scale_factor = 1.0
    
    # Normalize if requested and values are large
    if normalize and (h - l) > 100:
        scale_factor = h - l
        # Normalize to [0.1, 1.0] range preserving relative position
        normalized_mean = 0.1 + 0.9 * (target_mean - l) / scale_factor
        target_mean = normalized_mean
        l_norm = 0.1
        h_norm = 1.0
        l, h = l_norm, h_norm
        print(f"🔢 Normalizing large values:")
        print(f"  Original: mean={orig_mean:,.0f}, bounds=[{orig_l:,.0f}, {orig_h:,.0f}]")
        print(f"  Normalized: mean={target_mean:.3f}, bounds=[{l:.1f}, {h:.1f}]")
        print(f"  Scale factor: {scale_factor:,.0f}")
    
    print(f"Testing Bounded Pareto fits for:")
    print(f"  Target mean: {target_mean}")
    print(f"  Bounds: [{l}, {h}]")
    print(f"  Samples: {n_samples}")
    print("=" * 50)
    
    # Validate inputs
    if target_mean <= l or target_mean >= h:
        raise ValueError(f"Target mean {target_mean} must be between bounds ({l}, {h})")
    
    # Test different combinations of a and k
    # Ensure k <= l to avoid validation errors
    # For normalized case, use small positive k values
    if normalize and scale_factor > 1:
        # Use small positive k values for normalized range
        test_configs = [
            {"a": 1.5, "k": 0.001, "color": "blue", "label": "a=1.5, k=0.001"},
            {"a": 2.0, "k": 0.001, "color": "red", "label": "a=2.0, k=0.001"},
            {"a": 3.0, "k": 0.001, "color": "green", "label": "a=3.0, k=0.001"},
            {"a": 2.5, "k": 0.005, "color": "orange", "label": "a=2.5, k=0.005"},
            {"a": 1.2, "k": 0.01, "color": "purple", "label": "a=1.2, k=0.01"},
        ]
    else:
        # Use regular k values for non-normalized case
        max_k = min(l, 1.0)  # Keep k reasonable
        test_configs = [
            {"a": 1.5, "k": max_k, "color": "blue", "label": f"a=1.5, k={max_k}"},
            {"a": 2.0, "k": max_k, "color": "red", "label": f"a=2.0, k={max_k}"},
            {"a": 3.0, "k": max_k, "color": "green", "label": f"a=3.0, k={max_k}"},
            {"a": 2.5, "k": max_k * 0.8, "color": "orange", "label": f"a=2.5, k={max_k * 0.8:.1f}"},
            {"a": 1.2, "k": max_k * 0.5, "color": "purple", "label": f"a=1.2, k={max_k * 0.5:.1f}"},
        ]
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Title shows original values if normalized
    if normalize and scale_factor > 1:
        title = f'Bounded Pareto Fits - Target Mean: {orig_mean:,.0f}, Bounds: [{orig_l:,.0f}, {orig_h:,.0f}] (Normalized)'
    else:
        title = f'Bounded Pareto Fits - Target Mean: {target_mean}, Bounds: [{l}, {h}]'
    
    fig.suptitle(title, fontsize=14)
    
    all_samples = {}
    stats_data = []
    
    # Generate samples for each configuration
    for config in test_configs:
        a, k = config["a"], config["k"]
        
        # Generate samples
        try:
            samples = [BoundedPareto(a, k, l, h) for _ in range(n_samples)]
            all_samples[config["label"]] = samples
            
            # Calculate statistics
            actual_mean = sum(samples) / len(samples)
            std_dev = (sum((x - actual_mean)**2 for x in samples) / len(samples))**0.5
            
            stats_data.append({
                "config": config["label"],
                "a": a, "k": k,
                "mean": actual_mean,
                "std": std_dev,
                "mean_error": abs(actual_mean - target_mean),
                "color": config["color"]
            })
            
            print(f"{config['label']:15} -> Mean: {actual_mean:.3f} (error: {abs(actual_mean - target_mean):.3f}), Std: {std_dev:.3f}")
            
        except Exception as e:
            print(f"Error with {config['label']}: {e}")
            continue
    
    # Plot 1: Overlapping Histograms
    for i, (label, samples) in enumerate(all_samples.items()):
        config = next(c for c in test_configs if c["label"] == label)
        ax1.hist(samples, bins=40, density=True, alpha=0.6, 
                color=config["color"], label=label, edgecolor='black', linewidth=0.5)
    
    ax1.axvline(target_mean, color='black', linestyle='--', linewidth=2, label=f'Target Mean: {target_mean}')
    ax1.axvline(l, color='gray', linestyle='-', alpha=0.7, label=f'Bounds: [{l}, {h}]')
    ax1.axvline(h, color='gray', linestyle='-', alpha=0.7)
    ax1.set_xlabel('Value')
    ax1.set_ylabel('Density')
    ax1.set_title('Distribution Comparison')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Mean Error Comparison
    configs = [s["config"] for s in stats_data]
    mean_errors = [s["mean_error"] for s in stats_data]
    colors = [s["color"] for s in stats_data]
    
    bars = ax2.bar(range(len(configs)), mean_errors, color=colors, alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Configuration')
    ax2.set_ylabel('Mean Error')
    ax2.set_title('Mean Error from Target')
    ax2.set_xticks(range(len(configs)))
    ax2.set_xticklabels([c.replace(", ", "\n") for c in configs], rotation=0, fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, error in zip(bars, mean_errors):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{error:.3f}', ha='center', va='bottom', fontsize=8)
    
    # Plot 3: Mean vs Standard Deviation
    means = [s["mean"] for s in stats_data]
    stds = [s["std"] for s in stats_data]
    
    for i, stat in enumerate(stats_data):
        ax3.scatter(stat["mean"], stat["std"], color=stat["color"], s=100, 
                   alpha=0.8, edgecolor='black', linewidth=1)
        ax3.annotate(f'a={stat["a"]}, k={stat["k"]}', 
                    (stat["mean"], stat["std"]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax3.axvline(target_mean, color='black', linestyle='--', alpha=0.7, label=f'Target Mean: {target_mean}')
    ax3.set_xlabel('Actual Mean')
    ax3.set_ylabel('Standard Deviation')
    ax3.set_title('Mean vs Standard Deviation')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: CDFs Comparison
    x_range = np.linspace(l, h, 1000)
    
    for label, samples in all_samples.items():
        config = next(c for c in test_configs if c["label"] == label)
        sorted_samples = sorted(samples)
        empirical_cdf = np.arange(1, len(sorted_samples) + 1) / len(sorted_samples)
        ax4.plot(sorted_samples, empirical_cdf, color=config["color"], 
                linewidth=2, alpha=0.8, label=label)
    
    ax4.set_xlabel('Value')
    ax4.set_ylabel('Cumulative Probability')
    ax4.set_title('Cumulative Distribution Functions')
    ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Summary statistics
    print(f"\n📊 Summary Statistics:")
    if not stats_data:
        print("❌ No valid configurations found! Check parameters.")
        return []
    
    if normalize and scale_factor > 1:
        print(f"{'Configuration':15} {'Mean':>8} {'Std':>8} {'Error':>8} {'Orig_Mean':>12} {'Orig_Error':>12}")
        print("-" * 75)
        for stat in stats_data:
            orig_mean_val = stat['mean'] * scale_factor + orig_l
            orig_error = stat['mean_error'] * scale_factor
            print(f"{stat['config']:15} {stat['mean']:8.3f} {stat['std']:8.3f} {stat['mean_error']:8.3f} "
                  f"{orig_mean_val:12.0f} {orig_error:12.0f}")
    else:
        print(f"{'Configuration':15} {'Mean':>8} {'Std':>8} {'Error':>8}")
        print("-" * 45)
        for stat in stats_data:
            print(f"{stat['config']:15} {stat['mean']:8.3f} {stat['std']:8.3f} {stat['mean_error']:8.3f}")
    
    # Find best fit (closest to target mean)
    best_fit = min(stats_data, key=lambda x: x["mean_error"])
    if normalize and scale_factor > 1:
        best_orig_error = best_fit['mean_error'] * scale_factor
        print(f"\n🎯 Best fit: {best_fit['config']} (normalized error: {best_fit['mean_error']:.3f}, original error: {best_orig_error:,.0f})")
    else:
        print(f"\n🎯 Best fit: {best_fit['config']} (error: {best_fit['mean_error']:.3f})")
    
    return stats_data


def demo_denormalization():
    #=======================================================================
    # Demonstrates how to generate and denormalize bounded Pareto samples
    #=======================================================================
    print("\n" + "="*60)
    print("DENORMALIZATION DEMO")
    print("="*60)
    
    # Original large-scale parameters
    original_mean = 300000
    original_l = 1000
    original_h = 8000000
    
    # Normalized parameters (from previous analysis)
    # We found that a=3.0, k=0.001 gives good fit
    a = 3.0
    k = 0.001
    normalized_l = 0.1
    normalized_h = 1.0
    
    print(f"Original scale: mean≈{original_mean:,}, bounds=[{original_l:,}, {original_h:,}]")
    print(f"Normalized parameters: a={a}, k={k}, bounds=[{normalized_l}, {normalized_h}]")
    print()
    
    # Method 1: Generate normalized sample then denormalize
    print("📊 Method 1: Generate normalized then denormalize")
    for i in range(5):
        # Step 1: Generate normalized sample
        normalized_sample = BoundedPareto(a, k, normalized_l, normalized_h)
        
        # Step 2: Denormalize
        original_sample = denormalize_value(normalized_sample, original_l, original_h, normalized_l, normalized_h)
        
        print(f"  Sample {i+1}: {normalized_sample:.3f} → {original_sample:,.0f}")
    
    print()
    
    # Method 2: Use convenience function
    print("📊 Method 2: Direct generation with auto-denormalization")
    for i in range(5):
        original_sample = generate_denormalized_bounded_pareto(a, k, normalized_l, normalized_h, original_l, original_h)
        print(f"  Sample {i+1}: {original_sample:,.0f}")
    
    print()
    
    # Verify the mean of denormalized samples
    print("📊 Verification: Mean of 1000 denormalized samples")
    samples = []
    for _ in range(1000):
        sample = generate_denormalized_bounded_pareto(a, k, normalized_l, normalized_h, original_l, original_h)
        samples.append(sample)
    
    actual_mean = sum(samples) / len(samples)
    min_val = min(samples)
    max_val = max(samples)
    
    print(f"  Target mean: {original_mean:,}")
    print(f"  Actual mean: {actual_mean:,.0f}")
    print(f"  Error: {abs(actual_mean - original_mean):,.0f}")
    print(f"  Range: [{min_val:,.0f}, {max_val:,.0f}]")
    print(f"  Expected range: [{original_l:,}, {original_h:,}]")


if __name__ == "__main__":
    # Example usage
    print("Bounded Pareto Distribution Fit Analysis")
    print("=" * 45)
    
    # Test with different scenarios including large numbers
    test_scenarios = [
        {"mean": 3.0, "l": 1.0, "h": 8.0, "desc": "Small values"},
        {"mean": 5000, "l": 1000, "h": 15000, "desc": "Medium values (normalized)"},
        {"mean": 300000, "l": 50000, "h": 800000, "desc": "Large values (normalized)"}
    ]
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{'='*70}")
        print(f"SCENARIO {i+1}: {scenario['desc']}")
        print(f"{'='*70}")
        
        try:
            test_bounded_pareto_fits(
                target_mean=scenario["mean"],
                l=scenario["l"], 
                h=scenario["h"],
                normalize=True  # Always normalize for better numerics
            )
        except Exception as e:
            print(f"Error in scenario {i+1}: {e}")
            continue
    
    # Demonstrate denormalization
    demo_denormalization()
