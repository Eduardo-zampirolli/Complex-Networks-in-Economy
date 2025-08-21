import pandas as pd
import numpy as np
import os

def main():
    try:
        # Load data with the correct column names
        df = pd.read_csv('Data\RAIS\CB0\RAIS_CBO_2022.csv')
        
        print(f"Data loaded successfully with {len(df)} rows")
        print("Columns found:", df.columns.tolist())
        
        # Create the matrix m using the correct column names
        m = df.pivot_table(index='State ID', 
                          columns='Occupation ID', 
                          values='Workers', 
                          aggfunc='sum',  # Sum the workers
                          fill_value=0).values
        
        print(f"Matrix shape: {m.shape}")
        print(f"Number of states: {m.shape[0]}")
        print(f"Number of occupations: {m.shape[1]}")
        
        # Calculate totals
        X = np.sum(m)          # Grand total of all workers
        X_c = np.sum(m, axis=1, keepdims=True)  # Column sums (total workers per state)
        X_p = np.sum(m, axis=0, keepdims=True)  # Row sums (total workers per occupation)
        
        # Calculate Rcp with broadcasting and zero division handling
        with np.errstate(divide='ignore', invalid='ignore'):
            R = (m * X) / (X_c * X_p)
            R[~np.isfinite(R)] = 0  # Replace inf/nan with 0
        
        # Convert back to DataFrame
        states = df['State ID'].unique()
        occupations = df['Occupation ID'].unique()
        
        Rcp_df = pd.DataFrame(R, 
                             index=states, 
                             columns=occupations)
        
        # Save to CSV
        Rcp_df.to_csv('normalized_UF_2022_CBO.csv')
        print("Specialization matrix saved to normalized_UF_2022_CBO.csv")
        
        # Optional: Show some statistics
        print(f"\nMatrix statistics:")
        print(f"Total workers: {X:,.0f}")
        print(f"Number of states: {len(states)}")
        print(f"Number of occupations: {len(occupations)}")
        print(f"R matrix range: [{np.min(R):.6f}, {np.max(R):.6f}]")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()