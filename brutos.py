import pandas as pd
import numpy as np
import glob
import os

def main():
    directory_path = '2023/'
    all_files = glob.glob(os.path.join(directory_path, '*.txt'))
    
    if not all_files:
        print("No files found")
        return
    
    df_list = []
    
    for file_path in all_files:
        try:
            temp_df = pd.read_csv(
                file_path,
                usecols=["CBO Ocupação 2002", "CNAE 2.0 Classe", "Mun Trab"],
                encoding='latin-1',
                sep=';'
            )
            df_list.append(temp_df)
            print(f"Read {len(temp_df)} rows from {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    if not df_list:
        print("No data was successfully read")
        return
    
    df = pd.concat(df_list, ignore_index=True)
    print(f"Combined DataFrame: {len(df)} rows")
    
    # Create the matrix using pivot_table
    matrix_df = df.pivot_table(
        index='Mun Trab',
        columns='CBO Ocupação 2002',
        values='CNAE 2.0 Classe',
        aggfunc='count',
        fill_value=0
    )
    
    print(f"Matrix shape: {matrix_df.shape}")
    
    # Convert to NumPy array for mathematical operations
    m = matrix_df.values
    
    # Calculate totals using NumPy (now m is a numpy array, not pandas DataFrame)
    X = np.sum(m)          # Grand total
    X_c = np.sum(m, axis=1, keepdims=True)  # Column sums (locations) - now works!
    X_p = np.sum(m, axis=0, keepdims=True)  # Row sums (activities) - now works!
    
    # Calculate Rcp with broadcasting and zero division handling
    with np.errstate(divide='ignore', invalid='ignore'):
        R = (m * X) / (X_c * X_p)
        R[~np.isfinite(R)] = 0  # Replace inf/nan with 0
    
    # Convert back to DataFrame with original index and columns
    Rcp_df = pd.DataFrame(R, 
                         index=matrix_df.index, 
                         columns=matrix_df.columns)
    
    # Save to CSV
    Rcp_df.to_csv('normalized_UF_2020.csv')
    print("Specialization matrix saved to normalized_UF_2020.csv")

if __name__ == "__main__":
    main()