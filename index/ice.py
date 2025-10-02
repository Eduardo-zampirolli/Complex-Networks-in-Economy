import numpy as np
import pandas as pd
import os

def main():
    data_dir = "/home/c-ec2024/ra281154/Complex-Networks-in-Economy/Data/cnae/2023/"
    bin_file = os.path.join(data_dir, "binary_matrix.csv")
    M = pd.read_csv(bin_file)
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
        'region_index': range(len(ice)),
        'ice_value': ice
    })
    ice_df.to_csv(os.path.join(data_dir, "ice_results.csv"), index=False)
    print(f"ICE results saved to: {os.path.join(data_dir, 'ice_results.csv')}") 
    return ice


if __name__=="__main__":
        main()

