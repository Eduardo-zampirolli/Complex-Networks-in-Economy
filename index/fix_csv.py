import pandas as pd
import numpy as np
import os

def fix_ice_csv():
    data_dir = "/home/c-ec2024/ra281154/Complex-Networks-in-Economy/Data/cnae/2023/"
    file_path = "/home/c-ec2024/ra281154/Complex-Networks-in-Economy/index/ice_results.csv"
    
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Convert the ice_value column from string representation of complex numbers to real numbers
    def extract_real(complex_str):
        """Extract real part from string like '(-4.299454933249337+0j)'"""
        try:
            # Convert string to complex number, then take real part
            complex_num = complex(complex_str)
            return complex_num.real
        except:
            # If conversion fails, try to parse manually
            if isinstance(complex_str, str):
                # Remove parentheses and extract the part before '+'
                clean_str = complex_str.strip('()')
                if '+' in clean_str:
                    real_part = clean_str.split('+')[0]
                elif '-' in clean_str[1:]:  # Check for negative imaginary part
                    real_part = clean_str.split('-')[0] + '-' + clean_str.split('-')[1]
                else:
                    real_part = clean_str
                return float(real_part)
            return complex_str
    
    # Apply the conversion
    df['ice_value'] = df['ice_value'].apply(extract_real)
    
    # Save the corrected file
    output_path = "/home/c-ec2024/ra281154/Complex-Networks-in-Economy/index/ice_results_fixed.csv"
    df.to_csv(output_path, index=False)
    
    # Also save to the data directory
    df.to_csv(os.path.join(data_dir, "ice_results_fixed.csv"), index=False)
    
    print(f"Fixed CSV saved to:")
    print(f"  - {output_path}")
    print(f"  - {os.path.join(data_dir, 'ice_results_fixed.csv')}")
    print(f"\nFirst 10 rows of corrected data:")
    print(df.head(10))
    
    # Show statistics
    print(f"\nICE Statistics:")
    print(f"  Mean: {df['ice_value'].mean():.6f}")
    print(f"  Std:  {df['ice_value'].std():.6f}")
    print(f"  Min:  {df['ice_value'].min():.6f}")
    print(f"  Max:  {df['ice_value'].max():.6f}")
    
    return df

if __name__ == "__main__":
    fix_ice_csv()
