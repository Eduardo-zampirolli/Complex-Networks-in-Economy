#!/usr/bin/env python3
"""
Comparison between old (incorrect) and new (correct) ICE calculation.
This demonstrates why the fix was necessary.
"""

import numpy as np
import pandas as pd

def calculate_ice_old(M):
    """Old (incorrect) implementation"""
    k_p = M.sum(axis=1)
    k_i = M.sum(axis=0)
    
    # Old approximation (INCORRECT)
    M_normalized = M / k_p.reshape(-1, 1)
    M_tilde = (M_normalized @ M.T) / k_i.mean()
    
    eigenvalues, eigenvectors = np.linalg.eig(M_tilde)
    sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
    K_2 = np.real(eigenvectors[:, sorted_idx[1]])
    ice = (K_2 - np.mean(K_2)) / np.std(K_2)
    return ice, M_tilde

def calculate_ice_new(M):
    """New (correct) implementation"""
    k_p = M.sum(axis=1)
    k_i = M.sum(axis=0)
    
    # Correct formula according to equation (3.6)
    k_p_safe = np.where(k_p == 0, 1, k_p)
    k_i_safe = np.where(k_i == 0, 1, k_i)
    
    M_div_kp = M / k_p_safe.reshape(-1, 1)
    M_div_ki = M / k_i_safe.reshape(1, -1)
    M_tilde = M_div_kp @ M_div_ki.T
    
    eigenvalues, eigenvectors = np.linalg.eig(M_tilde)
    sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
    K_2 = np.real(eigenvectors[:, sorted_idx[1]])
    ice = (K_2 - np.mean(K_2)) / np.std(K_2)
    return ice, M_tilde

def main():
    print("="*70)
    print("Comparison: Old (Incorrect) vs New (Correct) ICE Calculation")
    print("="*70)
    print()
    
    # Create a test binary matrix with varying diversity and ubiquity
    M = np.array([
        [1, 1, 1, 0, 0, 0],  # Location 0: diverse (3 industries)
        [1, 0, 0, 0, 0, 0],  # Location 1: specialized (1 industry)
        [0, 1, 0, 1, 0, 0],  # Location 2: medium (2 industries)
        [0, 0, 1, 1, 1, 0],  # Location 3: diverse (3 industries)
        [0, 0, 0, 0, 1, 1],  # Location 4: medium (2 industries)
    ], dtype=float)
    
    print("Test Binary Matrix M (5 locations × 6 industries):")
    print(M)
    print()
    
    k_p = M.sum(axis=1)
    k_i = M.sum(axis=0)
    print(f"Diversity (k_p): {k_p}")
    print(f"Ubiquity (k_i): {k_i}")
    print()
    
    # Calculate ICE using both methods
    ice_old, M_tilde_old = calculate_ice_old(M)
    ice_new, M_tilde_new = calculate_ice_new(M)
    
    print("M̃ Matrix (Old - Incorrect):")
    print(M_tilde_old)
    print()
    
    print("M̃ Matrix (New - Correct):")
    print(M_tilde_new)
    print()
    
    print("Difference in M̃ matrices:")
    print(M_tilde_new - M_tilde_old)
    print(f"Max absolute difference: {np.max(np.abs(M_tilde_new - M_tilde_old)):.6f}")
    print()
    
    print("-"*70)
    print("ICE Results Comparison:")
    print("-"*70)
    print(f"{'Location':<15} {'Old ICE':<15} {'New ICE':<15} {'Difference':<15}")
    print("-"*70)
    for i in range(len(ice_old)):
        diff = ice_new[i] - ice_old[i]
        print(f"Location {i:<7} {ice_old[i]:>13.6f}  {ice_new[i]:>13.6f}  {diff:>13.6f}")
    print("-"*70)
    print()
    
    # Calculate correlation between old and new rankings
    from scipy.stats import spearmanr, pearsonr
    
    rank_correlation, _ = spearmanr(ice_old, ice_new)
    value_correlation, _ = pearsonr(ice_old, ice_new)
    
    print("Correlation Analysis:")
    print(f"  Spearman rank correlation: {rank_correlation:.4f}")
    print(f"  Pearson value correlation: {value_correlation:.4f}")
    print()
    
    if rank_correlation < 0.99:
        print("⚠️  WARNING: Rankings differ significantly between old and new methods!")
        print("   This shows the old formula was producing incorrect results.")
    else:
        print("✓  Rankings are similar, but values differ due to correct normalization.")
    
    print()
    print("="*70)
    print("Conclusion:")
    print("="*70)
    print("The old implementation used k_i.mean() (average ubiquity) instead of")
    print("dividing by each individual k_i (ubiquity per industry). This produced")
    print("an approximation that doesn't correctly follow equation (3.6).")
    print()
    print("The new implementation correctly implements:")
    print("  M̃pp′ = ∑i (Mpi × Mp′i) / (kp,0 × ki,0)")
    print()
    print("This ensures proper normalization by both diversity and ubiquity.")
    print("="*70)

if __name__ == "__main__":
    main()
