import pandas as pd
import numpy as np

def main():
    df = pd.read_csv('Data/cnae/2020/RAIS_vinculos_2020.csv')
    
    # Create the matrix m
    m = df.pivot_table(index='Municipality ID', 
                      columns='Class ID', 
                      values='Workers', 
                      aggfunc='sum',  # Ensure summing workers
                      fill_value=0).values
    # Calculate totals
    X = np.sum(m)
    X_c = np.sum(m, axis=0, keepdims=True)  # Sum over locations (for each activity)
    X_p = np.sum(m, axis=1, keepdims=True)  # Sum over activities (for each location)

    #RCA = (m[p,i] * X) / (X_p[p] * X_c[i])
    with np.errstate(divide='ignore', invalid='ignore'):
        R = (m * X) / (X_p * X_c)
        R[~np.isfinite(R)] = 0  
    # Convert back to DataFrame
    municipalities = df['Municipality ID'].unique()
    classes = df['Class'].unique()
    
    Rcp_df = pd.DataFrame(R, 
                         index=municipalities, 
                         columns=classes)
    
    Rcp_df.to_csv('Data/cnae/2020/normalized_2020.csv')
    print("Specialization matrix saved to normalized.csv")

if __name__ == "__main__":
    main()
