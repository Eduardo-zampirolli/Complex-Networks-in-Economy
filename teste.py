import pandas as pd
import numpy as np

def main():
    # Load data
    df = pd.read_csv('Data/RAIS/RAIS_vinculos_2020.csv')
    
    # Create the matrix m
    m = df.pivot_table(index='Municipality ID', 
                      columns='Class', 
                      values='Workers', 
                      aggfunc='sum',  # Ensure summing workers
                      fill_value=0).values
    
    # Calculate totals
    X = np.sum(m)          # Grand total
    X_c = np.sum(m, axis=1, keepdims=True)  # Column sums (locations)
    X_p = np.sum(m, axis=0, keepdims=True)  # Row sums (activities)
    
    # Calculate Rcp with broadcasting and zero division handling
    with np.errstate(divide='ignore', invalid='ignore'):
        R = (m * X) / (X_c * X_p)
        R[~np.isfinite(R)] = 0  # Replace inf/nan with 0
    
    # Convert back to DataFrame
    municipalities = df['Municipality ID'].unique()
    classes = df['Class'].unique()
    
    Rcp_df = pd.DataFrame(R, 
                         index=municipalities, 
                         columns=classes)
    
    # Save to CSV
    Rcp_df.to_csv('normalized.csv')
    print("Specialization matrix saved to normalized.csv")

if __name__ == "__main__":
    main()