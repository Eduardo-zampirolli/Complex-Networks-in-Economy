import numpy as np
import pandas as pd
import os

def main():
    """
    Calculate the Economic Complexity Index (ICE) from a binary matrix.
    
    The calculation follows Hidalgo & Hausmann (2009) methodology:
    1. Load binary matrix M (locations × industries)
    2. Calculate diversity k_p and ubiquity k_i
    3. Compute M̃ matrix using equation (3.6)
    4. Find eigenvectors of M̃
    5. Use 2nd eigenvector to compute ICE
    
    Equation (3.6): M̃pp′ = ∑i (Mpi × Mp′i) / (kp,0 × ki,0)
    where:
    - Mpi: binary matrix element (location p, industry i)
    - kp,0: diversity of location p (number of industries)
    - ki,0: ubiquity of industry i (number of locations)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path relative to script location
    bin_dir = os.path.join(script_dir, "..", "Data")
    bin_file = "binary_imm_2020.csv"
 
    #bin_file = "../Data/binary_imm_2020.csv"
    M = pd.read_csv(os.path.join(bin_dir, bin_file), index_col=0)
    M = M.astype(float)
    
    # Store municipality IDs before converting to numpy
    municipality_ids = M.index
    
    # Convert to numpy array for matrix operations
    M_np = M.values
    k_p = M_np.sum(axis=1)  # diversity: number of products per location (kp,0)
    k_i = M_np.sum(axis=0)  # ubiquity: number of locations per product (ki,0)
    
    # Calculate M̃ matrix according to equation (3.6): M̃pp′ = ∑i (Mpi × Mp′i) / (kp,0 × ki,0)
    # Interpretation: M̃pp′ = (1/kp,0) × ∑i [(Mpi × Mp′i) / ki,0]
    # This can be computed as: M̃ = (M / k_p) @ (M / k_i)^T
    
    # Avoid division by zero
    k_p_safe = np.where(k_p == 0, 1, k_p)
    k_i_safe = np.where(k_i == 0, 1, k_i)
    
    # Normalize M by diversity (rows)
    M_div_kp = M_np / k_p_safe.reshape(-1, 1)
    # Normalize M by ubiquity (columns)  
    M_div_ki = M_np / k_i_safe.reshape(1, -1)
    
    # Calculate M̃ = (M / k_p) @ (M / k_i)^T
    M_tilde = M_div_kp @ M_div_ki.T
    
    # Compute eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(M_tilde)
    sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues_sorted = eigenvalues[sorted_idx]
    eigenvectors_sorted = eigenvectors[:, sorted_idx]
    
    # Extract only the real part of the second eigenvector
    K_2 = np.real(eigenvectors_sorted[:, 1])
    K_2 = -K_2
    # Standardize to get ICE
    ice = (K_2 - np.mean(K_2)) / np.std(K_2)
    
    # Create DataFrame with municipality IDs as index
    ice_df = pd.DataFrame({
        'Municipality_ID': municipality_ids,
        'ICE': ice
    })
    ice_df.set_index('Municipality_ID', inplace=True)
    
    # Sort by ICE for easier analysis
    ice_df_sorted = ice_df.sort_values('ICE', ascending=False)
    
    print("Top 10 municipalities by ICE:")
    print(ice_df_sorted.head(10))
    print("\nBottom 10 municipalities by ICE:")
    print(ice_df_sorted.tail(10))
    
    # Save results
    output_file = os.path.join(data_dir, "ice_results.csv")
    ice_df_sorted.to_csv(output_file)
    print(f"\nICE results saved to: {output_file}")
    
    return ice_df_sorted

if __name__ == "__main__":
    main()
import numpy as np
import pandas as pd
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path relative to script location
    bin_dir = os.path.join(script_dir, "..", "Data")
    bin_file = "binary_imm_2020.csv"
 
    #bin_file = "../Data/binary_imm_2020.csv"
    M = pd.read_csv(os.path.join(bin_dir, bin_file), index_col=0)
    M = M.astype(float)
    
    # Convert to numpy array for matrix operations
    M_np = M.values
    k_p = M_np.sum(axis=1)  # product degrees
    k_i = M_np.sum(axis=0)  # sum of all industry degrees
    
    # Calculate M̃ matrix according to equation (3.6): M̃pp′ = ∑i (Mpi × Mi′p) / (kp,0 × ki,0)
    # First attempt - vectorized approximation (not exact but faster)
    M_normalized = M_np / k_p.reshape(-1, 1)  # Normalize by kp,0
    M_tilde = (M_normalized @ M_np.T) / k_i.mean()  # Approximate division by ki,0
    eigenvalues, eigenvectors = np.linalg.eig(M_tilde)
    sorted_idx = np.argsort(np.abs(eigenvalues))[::-1]
    eigenvalues_sorted = eigenvalues[sorted_idx]
    eigenvectors_sorted = eigenvectors[:, sorted_idx]
    
    # Extract only the real part of the second eigenvector
    K_2 = np.real(eigenvectors_sorted[:, 1])

    ice = (K_2 - np.mean(K_2)) / np.std(K_2)
    print(ice)
    
    # Option 1: Save as CSV
    ice_df = pd.DataFrame({
        'region_index': M.index,
        'ice_value': ice
    })
    ice_df.to_csv(os.path.join(bin_dir, "ice_cod_imm_2020.csv"), index=False)
    print(f"\nSaved results for {len(ice)} locations")
    print(f"First few locations: {M.index[:5].tolist()}")
    
    return ice


if __name__=="__main__":
        main()

