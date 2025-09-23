import csv
import numpy as np

def adjacency_list_to_matrix(input_file, output_file):
    # First pass: collect all unique node labels
    nodes = set()
    edges = []
    with open(input_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        # Detect if header or data
        if all(h.lower() in ['source','target','from','to','weight','proximity','value'] for h in header):
            # Assume header, skip
            pass
        else:
            # No header, treat as data
            csvfile.seek(0)
            reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 3:
                continue
            u, v, w = row[0], row[1], float(row[2])
            nodes.add(u)
            nodes.add(v)
            edges.append((u, v, w))

    # Map node labels to indices
    node_list = sorted(list(nodes))
    node_index = {node: idx for idx, node in enumerate(node_list)}
    N = len(node_list)
    matrix = np.zeros((N, N))

    # Fill the matrix
    for u, v, w in edges:
        i, j = node_index[u], node_index[v]
        matrix[i, j] = w
        matrix[j, i] = w  # undirected

    # Save to CSV
    with open(output_file, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write optional header
        writer.writerow([""] + node_list)
        for i, node in enumerate(node_list):
            writer.writerow([node] + list(matrix[i]))

    print(f"Matrix saved to {output_file} with shape {matrix.shape}")

if __name__ == "__main__":
    # Change these as needed
    input_csv = "Data/prox/location_proximity_matrix.csv"
    output_csv = "Data/prox/location_proximity_matrix_NxN.csv"
    adjacency_list_to_matrix(input_csv, output_csv)
