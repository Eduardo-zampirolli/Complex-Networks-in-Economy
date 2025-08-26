import pandas as pd
import numpy as np

# Load your CSV file with RCA values
# First column contains locality IDs, first row contains activity IDs
df = pd.read_csv('Data/cnae/normalized_CNAE_2023.csv', index_col=0)

# Display the first few rows to verify structure
print("RCA data:")
print(df.head())
print(f"Shape: {df.shape}")
print(f"Locality IDs: {df.index.tolist()[:5]}...")
print(f"Activity IDs: {df.columns.tolist()[:5]}...")

# Create binary matrix (1 if RCA >= 1, else 0)
binary_matrix = (df >= 1.0).astype(int)

print("\nBinary matrix:")
print(binary_matrix.head())
print(f"Binary matrix shape: {binary_matrix.shape}")

# Check some statistics
print(f"\nStatistics:")
print(f"Total entries: {binary_matrix.size}")
print(f"Ones (RCA >= 1): {binary_matrix.sum().sum()}")
print(f"Zeros (RCA < 1): {binary_matrix.size - binary_matrix.sum().sum()}")
print(f"Percentage with RCA >= 1: {binary_matrix.sum().sum()/binary_matrix.size*100:.2f}%")

# Calculate diversity and ubiquity (key metrics for economic complexity)
diversity = binary_matrix.sum(axis=1)  # Number of activities per location
ubiquity = binary_matrix.sum(axis=0)   # Number of locations per activity

print("\nDiversity (activities per location):")
print(diversity.head())

print("\nUbiquity (locations per activity):")
print(ubiquity.head())

# Save the binary matrix to a new CSV file
binary_matrix.to_csv('binary_matrix.csv')
print("\nBinary matrix saved to 'binary_matrix.csv'")

# Optional: Save diversity and ubiquity as well
diversity.to_csv('diversity.csv', header=['Diversity'])
ubiquity.to_csv('ubiquity.csv', header=['Ubiquity'])
print("Diversity and ubiquity saved to CSV files")