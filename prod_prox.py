import pandas as pd
import numpy as np

def calculate_product_proximity(binary_matrix):
    """
    Calculate product proximity matrix using the formula:
    ϕ_pp' = sum(M_cp * M_cp') / max(M_p, M_p')
    
    Parameters:
    binary_matrix: DataFrame with localities as rows and products as columns
                   Values are 1 (RCA >= 1) or 0 (RCA < 1)
    
    Returns:
    proximity_df: DataFrame with product proximity values
    """
    # Convert to numpy array for faster computation
    M = binary_matrix.values
    products = binary_matrix.columns.tolist()
    n_products = len(products)
    
    # Calculate ubiquity for each product (M_p)
    ubiquity = binary_matrix.sum(axis=0).values
    
    # Initialize proximity matrix
    proximity_matrix = np.zeros((n_products, n_products))
    
    # Calculate proximity for each product pair
    for i in range(n_products):
        for j in range(i + 1, n_products):  # Only calculate upper triangle 'cause it's symmetric
            numerator = np.sum(M[:, i] * M[:, j])  # Sum of co-occurrences
            denominator = max(ubiquity[i], ubiquity[j])
            
            if denominator > 0:
                proximity_value = numerator / denominator
            else:
                proximity_value = 0
                
            proximity_matrix[i, j] = proximity_value
            proximity_matrix[j, i] = proximity_value  # Symmetric matrix
    
    # Create DataFrame with product labels
    proximity_df = pd.DataFrame(proximity_matrix, 
                               index=products, 
                               columns=products)
    
    return proximity_df

def calculate_product_proximity_optimized(binary_matrix):
    """
    Optimized version using matrix operations (faster for large datasets)
    """
    M = binary_matrix.values.astype(float)
    ubiquity = binary_matrix.sum(axis=0).values
    
    # Calculate co-occurrence matrix: M.T @ M
    co_occurrence = M.T @ M #see why this is equal to sum(M_cp * M_cp')
    
    # Create matrix of max(ubiquity_i, ubiquity_j) for each pair
    max_ubiquity = np.maximum.outer(ubiquity, ubiquity)
    
    # Avoid division by zero
    max_ubiquity[max_ubiquity == 0] = 1
    
    # Calculate proximity matrix
    proximity_matrix = co_occurrence / max_ubiquity
    
    # Set diagonal to 0 (or 1 if you want self-proximity)
    np.fill_diagonal(proximity_matrix, 0)
    
    # Create DataFrame
    proximity_df = pd.DataFrame(proximity_matrix,
                               index=binary_matrix.columns,
                               columns=binary_matrix.columns)
    
    return proximity_df

# Example usage
def main():
    binary_matrix = pd.read_csv('binary_matrix.csv', index_col=0)

    # Calculate product proximity matrix
    proximity_matrix = calculate_product_proximity_optimized(binary_matrix)

    # Save the results
    proximity_matrix.to_csv('product_proximity_matrix.csv')

    # Display basic information
    print(f"Proximity matrix shape: {proximity_matrix.shape}")
    print(f"Number of product pairs: {len(proximity_matrix) * (len(proximity_matrix) - 1) // 2}")
    print(f"Average proximity: {proximity_matrix.values.mean():.3f}")

    
    
    # For larger datasets, use the optimized version
    proximity_matrix_opt = calculate_product_proximity_optimized(binary_matrix)
    
    # Verify both methods give same result
    print(f"\nMethods give identical results: {proximity_matrix.equals(proximity_matrix_opt)}")
    
    # Save results
    proximity_matrix.to_csv('product_proximity_matrix.csv')
    #proximity_matrix_opt.to_csv('product_proximity_matrix_opt.csv')
    print("\nProduct proximity matrix saved to 'product_proximity_matrix.csv'")
    
    # Additional analysis
    print("\nProximity statistics:")
    print(f"Average proximity: {proximity_matrix.values.mean():.3f}")
    print(f"Maximum proximity: {proximity_matrix.values.max():.3f}")
    print(f"Minimum proximity: {proximity_matrix.values.min():.3f}")
    
    # Find most similar product pairs
    upper_triangle = proximity_matrix.where(np.triu(np.ones(proximity_matrix.shape), k=1).astype(bool))
    max_proximity = upper_triangle.stack().max()
    most_similar = upper_triangle.stack().idxmax()
    
    print(f"\nMost similar product pair: {most_similar} with proximity {max_proximity:.3f}")

if __name__ == "__main__":
    main()  