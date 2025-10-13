import numpy as np
import pandas as pd
import os

def main():
    """
    Calculate the Economic Complexity Index (ICE) from a binary matrix.
    """
    data_dir = "../Data/cnae/2020/"
    bin_file = os.path.join(data_dir, "binary_matrix.csv")
    
    # Read the binary matrix
    M = pd.read_csv(bin_file, index_col=0)  # First column as index (location IDs)
    
    # Get location names from index
    location_names = M.index.values
    
    # Convert to numpy array (this should contain ONLY 0s and 1s)
    M_np = M.values.astype(float)
    
    print(f"Binary matrix shape: {M_np.shape}")
    print(f"Number of locations: {len(location_names)}")
    print(f"Number of activities: {M_np.shape[1]}")
    
    # Verify the binary matrix contains only 0s and 1s
    unique_values = np.unique(M_np)
    print(f"Unique values in matrix: {unique_values}")
    
    # Calculate diversity and ubiquity
    k_p = M_np.sum(axis=1)  # diversity: number of activities per location
    k_i = M_np.sum(axis=0)  # ubiquity: number of locations per activity
    
    print(f"Diversity range: {k_p.min()} to {k_p.max()}")
    print(f"Ubiquity range: {k_i.min()} to {k_i.max()}")
    
    # Avoid division by zero
    k_p_safe = np.where(k_p == 0, 1, k_p)
    k_i_safe = np.where(k_i == 0, 1, k_i)
    
    # Normalize M by diversity (rows) and ubiquity (columns)
    M_div_kp = M_np / k_p_safe.reshape(-1, 1)
    M_div_ki = M_np / k_i_safe.reshape(1, -1)
    
    # Calculate M̃ matrix
    M_tilde = M_div_kp @ M_div_ki.T
    
    # Calculate eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(M_tilde)
    
    # Sort by absolute value of eigenvalues
    sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues_sorted = eigenvalues[sorted_idx]
    eigenvectors_sorted = eigenvectors[:, sorted_idx]
    
    # Use the second eigenvector for ICE (first is trivial)
    K_2 = np.real(eigenvectors_sorted[:, 1])
    
    # Standardize to get ICE
    ice = (K_2 - np.mean(K_2)) / np.std(K_2)
    
    # Save location order
    with open(os.path.join(data_dir, "ordem.txt"), "w") as f:
        for i, location in enumerate(location_names):
            f.write(f"{i}: {location}\n")
    print(f"Location order saved to: {os.path.join(data_dir, 'ordem.txt')}")
    
    # Save ICE results
    ice_df = pd.DataFrame({
        'location': location_names,
        'ice_value': ice
    })
    ice_df.to_csv(os.path.join(data_dir, "ice_results.csv"), index=False)
    print(f"ICE results saved to: {os.path.join(data_dir, 'ice_results.csv')}")
    
    # Print diagnostics
    print(f"\nICE Statistics:")
    print(f"ICE range: {ice.min():.6f} to {ice.max():.6f}")
    print(f"Mean ICE: {ice.mean():.6f}")
    print(f"Std ICE: {ice.std():.6f}")
    
    # Check for duplicate values
    unique_ice, counts = np.unique(ice, return_counts=True)
    duplicates = [(val, count) for val, count in zip(unique_ice, counts) if count > 1]
    if duplicates:
        print(f"Duplicate ICE values found: {duplicates}")
    else:
        print(f"No duplicate ICE values - all values are unique")
    
    # Show top and bottom 5
    ice_df_sorted = ice_df.sort_values('ice_value', ascending=False)
    print(f"\nTop 5 locations by ICE:")
    print(ice_df_sorted.head().to_string(index=False))
    
    print(f"\nBottom 5 locations by ICE:")
    print(ice_df_sorted.tail().to_string(index=False))
    
    return ice

if __name__ == "__main__":
    main()

