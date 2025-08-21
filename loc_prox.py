import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def calculate_location_proximity(rca_matrix):
    """
    Calculate location proximity matrix using the formula:
    ϕ_cc' = corr(log(R_cp), log(R_c'p))
    
    Parameters:
    rca_matrix: DataFrame with localities as rows and products as columns
                Contains RCA values
    
    Returns:
    proximity_df: DataFrame with location proximity values
    """
    # Apply log transformation (add small epsilon to avoid log(0))
    log_rca = np.log(rca_matrix + 1e-10)
    
    locations = rca_matrix.index.tolist()
    n_locations = len(locations)
    
    # Initialize proximity matrix
    proximity_matrix = np.zeros((n_locations, n_locations))
    
    # Calculate proximity for each location pair
    for i in range(n_locations):
        for j in range(i + 1, n_locations):  # Only calculate upper triangle
            # Get the RCA profiles for both locations
            loc_i_profile = log_rca.iloc[i].values
            loc_j_profile = log_rca.iloc[j].values
            
            # Calculate Pearson correlation
            correlation, _ = pearsonr(loc_i_profile, loc_j_profile)
            
            # Handle NaN values (if standard deviation is zero)
            if np.isnan(correlation):
                correlation = 0
                
            proximity_matrix[i, j] = correlation
            proximity_matrix[j, i] = correlation  # Symmetric matrix
    
    # Create DataFrame with location labels
    proximity_df = pd.DataFrame(proximity_matrix, 
                               index=locations, 
                               columns=locations)
    
    return proximity_df

def calculate_location_proximity_optimized(rca_matrix):
    """
    Optimized version using matrix correlation (faster for large datasets)
    """
    # Apply log transformation
    log_rca = np.log(rca_matrix + 1e-10)
    
    # Convert to numpy array and transpose to get products as rows
    data = log_rca.values.T  # Now shape: (products × locations)
    
    # Calculate correlation matrix between locations
    correlation_matrix = np.corrcoef(data, rowvar=False)  # rowvar=False because columns are locations
    
    # Handle NaN values (set to 0)
    correlation_matrix = np.nan_to_num(correlation_matrix, nan=0)
    
    # Create DataFrame
    proximity_df = pd.DataFrame(correlation_matrix,
                               index=rca_matrix.index,
                               columns=rca_matrix.index)
    
    return proximity_df

def calculate_location_proximity_custom(rca_matrix):
    """
    Alternative implementation with manual correlation calculation
    for better control and understanding
    """
    log_rca = np.log(rca_matrix + 1e-10)
    locations = log_rca.index.tolist()
    n_locations = len(locations)
    n_products = len(log_rca.columns)
    
    # Standardize the data (z-scores)
    standardized = (log_rca - log_rca.mean(axis=1).values[:, None]) / log_rca.std(axis=1).values[:, None]
    standardized = standardized.fillna(0)  # Replace NaN with 0
    
    proximity_matrix = np.zeros((n_locations, n_locations))
    
    for i in range(n_locations):
        for j in range(i + 1, n_locations):
            # Dot product of standardized vectors
            dot_product = np.dot(standardized.iloc[i], standardized.iloc[j])
            correlation = dot_product / (n_products - 1)  # Sample correlation
            
            proximity_matrix[i, j] = correlation
            proximity_matrix[j, i] = correlation
    
    return pd.DataFrame(proximity_matrix, index=locations, columns=locations)

# Example usage
def main():
    # Load your RCA matrix (replace with your actual data)
    # rca_matrix = pd.read_csv('your_rca_data.csv', index_col=0)
    
   # Load your RCA matrix
    rca_matrix = pd.read_csv('Data/cnae/normalized_2022.csv', index_col=0)

    # Calculate location proximity matrix
    proximity_matrix = calculate_location_proximity_optimized(rca_matrix)

    # Save the results
    proximity_matrix.to_csv('location_proximity_matrix.csv')

    # Display basic information
    print(f"Location proximity matrix shape: {proximity_matrix.shape}")
    print(f"Number of location pairs: {len(proximity_matrix) * (len(proximity_matrix) - 1) // 2}")
    print(f"Average proximity: {proximity_matrix.values.mean():.3f}")

    # Create a heatmap for visualization (optional)
    import seaborn as sns
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 8))
    sns.heatmap(proximity_matrix, cmap='RdBu_r', center=0, 
                xticklabels=proximity_matrix.index, yticklabels=proximity_matrix.columns)
    plt.title('Location Proximity Matrix')
    plt.tight_layout()
    plt.savefig('location_proximity_heatmap.png')
    plt.show()

if __name__ == "__main__":
    main()