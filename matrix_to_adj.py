import pandas as pd
import numpy as np

def matrix_to_adjacency_list(csv_filename, output_filename=None, threshold=0.0):
    print(f"Reading matrix from {csv_filename}...")
    df = pd.read_csv(csv_filename, index_col=0)
    nodes = df.index.tolist()
    adjacency_list = []
    
    # Convert matrix to adjacency list
    for i, source_node in enumerate(nodes):
        for j, target_node in enumerate(df.columns):
            weight = df.iloc[i, j]
            if pd.notna(weight) and abs(weight) > threshold:
                adjacency_list.append([source_node, target_node, weight])
    
    print(f"Generated {len(adjacency_list)} edges from matrix")
    
    # Save to file if output filename is provided
    adj_df = pd.DataFrame(adjacency_list, columns=['source', 'target', 'weight'])
    adj_df.to_csv(output_filename, index=False)
    return adjacency_list

if __name__ == "__main__":
    # Main execution
    input_file = "filtered_matrix.csv"
    output_file = "adjacency_list.csv"
    
    threshold = 0.0  
    adj_list = matrix_to_adjacency_list(input_file, output_file, threshold)
