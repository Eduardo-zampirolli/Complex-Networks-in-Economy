#!/usr/bin/env python3
"""
Test script to verify the ICE calculation formula is correct.
Tests the M̃ matrix calculation against the mathematical definition.
"""

import numpy as np
import pandas as pd

def test_m_tilde_calculation():
    """Test that M̃ is calculated correctly according to equation (3.6)"""
    
    # Create a simple test binary matrix (5 locations x 4 products)
    M = np.array([
        [1, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [1, 0, 0, 1]
    ], dtype=float)
    
    print("Test Binary Matrix M:")
    print(M)
    print()
    
    # Calculate diversity (k_p) and ubiquity (k_i)
    k_p = M.sum(axis=1)  # diversity: sum over products for each location
    k_i = M.sum(axis=0)  # ubiquity: sum over locations for each product
    
    print("Diversity (k_p):", k_p)
    print("Ubiquity (k_i):", k_i)
    print()
    
    # Method 1: Direct calculation using the formula
    # M̃pp′ = ∑i (Mpi × Mp′i) / (kp,0 × ki,0)
    n_locations = M.shape[0]
    M_tilde_direct = np.zeros((n_locations, n_locations))
    
    for p in range(n_locations):
        for p_prime in range(n_locations):
            sum_val = 0
            for i in range(M.shape[1]):
                if k_p[p] > 0 and k_i[i] > 0:
                    sum_val += (M[p, i] * M[p_prime, i]) / (k_p[p] * k_i[i])
            M_tilde_direct[p, p_prime] = sum_val
    
    print("M̃ (direct calculation):")
    print(M_tilde_direct)
    print()
    
    # Method 2: Vectorized calculation (as in the fixed ice.py)
    k_p_safe = np.where(k_p == 0, 1, k_p)
    k_i_safe = np.where(k_i == 0, 1, k_i)
    
    M_div_kp = M / k_p_safe.reshape(-1, 1)
    M_div_ki = M / k_i_safe.reshape(1, -1)
    M_tilde_vectorized = M_div_kp @ M_div_ki.T
    
    print("M̃ (vectorized calculation):")
    print(M_tilde_vectorized)
    print()
    
    # Check if both methods give the same result
    diff = np.abs(M_tilde_direct - M_tilde_vectorized)
    max_diff = np.max(diff)
    print(f"Maximum difference between methods: {max_diff}")
    
    if max_diff < 1e-10:
        print("✓ PASS: Both methods produce identical results!")
    else:
        print("✗ FAIL: Methods produce different results!")
        print("Difference matrix:")
        print(diff)
        return False
    
    # Verify M̃ is symmetric
    is_symmetric = np.allclose(M_tilde_vectorized, M_tilde_vectorized.T)
    print(f"M̃ is symmetric: {is_symmetric}")
    if not is_symmetric:
        print("✗ WARNING: M̃ should be symmetric but it's not!")
    
    # Test eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eig(M_tilde_vectorized)
    sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues_sorted = eigenvalues[sorted_idx]
    
    print(f"\nTop 3 eigenvalues: {eigenvalues_sorted[:3]}")
    
    # Extract the second eigenvector
    K_2 = np.real(eigenvectors[:, sorted_idx[1]])
    
    # Calculate ICE
    ice = (K_2 - np.mean(K_2)) / np.std(K_2)
    print(f"ICE values: {ice}")
    print(f"ICE mean (should be ~0): {np.mean(ice):.6f}")
    print(f"ICE std (should be ~1): {np.std(ice):.6f}")
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("Testing ICE Calculation Formula")
    print("="*60)
    print()
    
    success = test_m_tilde_calculation()
    
    print()
    print("="*60)
    if success:
        print("All tests PASSED ✓")
    else:
        print("Some tests FAILED ✗")
    print("="*60)
