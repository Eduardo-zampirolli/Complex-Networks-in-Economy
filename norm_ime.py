import pandas as pd
import numpy as np
#Class ID,Class,Municipality ID,Municipality,Workers
import pandas as pd
import numpy as np

def main():
    # Load data
    df = pd.read_csv('Data/RAIS_vinculos_2020.csv', encoding='utf-8', 
                     usecols=['Municipality ID', 'Municipality','Class','Class ID', 'Workers'])
    inter = pd.read_csv('Data/mun-ime-inter.csv', usecols=['cod_mun','cod_imm'])
    
    # Merge to add cod_imm to each municipality
    df_merged = df.merge(inter, left_on='Municipality ID', right_on='cod_mun', how='inner')
    
    print(f"Original records: {len(df)}")
    print(f"After merge: {len(df_merged)}")
    print(f"Unique municipalities: {df_merged['Municipality ID'].nunique()}")
    print(f"Unique IMM regions: {df_merged['cod_imm'].nunique()}")
    print(f"Unique activities: {df_merged['Class'].nunique()}")
    
    # Create the pivot table: cod_imm x Class, summing workers
    m = df_merged.pivot_table(index='cod_imm', 
                               columns='Class', 
                               values='Workers', 
                               aggfunc='sum',  # Sum workers across municipalities in same IMM
                               fill_value=0)
    
    print(f"\nMatrix shape: {m.shape}")
    print(f"IMM regions (rows): {m.shape[0]}")
    print(f"Activities (columns): {m.shape[1]}")
    
    # Convert to numpy array for calculations
    m_np = m.values
    
    # Calculate totals
    X = np.sum(m_np)          # Grand total
    X_c = np.sum(m_np, axis=1, keepdims=True)  # Row sums (IMM regions)
    X_p = np.sum(m_np, axis=0, keepdims=True)  # Column sums (activities)
    
    print(f"\nTotal workers: {X:,.0f}")
    print(f"Workers per IMM region - min: {X_c.min():,.0f}, max: {X_c.max():,.0f}")
    print(f"Workers per activity - min: {X_p.min():,.0f}, max: {X_p.max():,.0f}")
    
    # Calculate Rcp (Location Quotient / Revealed Comparative Advantage)
    with np.errstate(divide='ignore', invalid='ignore'):
        R = (m_np * X) / (X_c * X_p)
        R[~np.isfinite(R)] = 0  # Replace inf/nan with 0
    
    # Convert back to DataFrame with proper index and columns
    Rcp_df = pd.DataFrame(R, 
                         index=m.index,  # cod_imm values
                         columns=m.columns)  # Class names
    
    # Save to CSV
    m.to_csv('Data/workers_imm_2020.csv')
    Rcp_df.to_csv('Data/normalized_imm_2020.csv')
    
    print("\nWorkers matrix saved to workers_imm_2020.csv")
    print("Specialization matrix saved to normalized_imm_2020.csv")
    
    return m, Rcp_df

if __name__ == "__main__":
    main()

'''
def main():
    # Load data
    df = pd.read_csv('Data/RAIS_vinculos_2020.csv', encoding='utf-8', usecols=['Municipality ID', 'Municipality','Class','Class ID', 'Workers'])
    inter = pd.read_csv('Data/mun-ime-inter.csv', usecols=['cod_mun','cod_imm'])
    #I need to join the workers
    merged_df = pd.merge(df, inter, left_on='Municipality ID', right_on='cod_mun', how='inner')
    m = merged_df.pivot_table(index='cod_imm', 
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
    #municipalities = df['Microregion ID'].unique()
    #classes = df['Class'].unique()
    
    Rcp_df = pd.DataFrame(R, 
                         index=m.index, 
                         columns=m.columns)
    
    # Save to CSV
    Rcp_df.to_csv('Data/normalized_ime_2020.csv')

    print("Specialization matrix saved to normalized_ime_2020.csv")

if __name__ == "__main__":
    main()
'''