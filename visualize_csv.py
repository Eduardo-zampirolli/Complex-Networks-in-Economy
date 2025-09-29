import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import csv

def read_graph_from_matrix(filename):
    """
    Read a graph from a CSV file containing an adjacency matrix.
    The CSV can have row/column headers or be a pure numeric matrix.
    """
    try:
        # Try to read as matrix with potential headers
        df = pd.read_csv(filename, index_col=0)
        # Convert to numpy array
        matrix = df.values
        
        # Create graph from adjacency matrix
        G = nx.from_numpy_array(matrix)
        
        # Add node labels if headers were present
        if hasattr(df, 'index') and len(df.index) == len(matrix):
            mapping = {i: str(df.index[i]) for i in range(len(df.index))}
            G = nx.relabel_nodes(G, mapping)
            
        return G
        
    except:
        # If that fails, try reading as pure numeric matrix without headers
        try:
            matrix = pd.read_csv(filename, header=None).values
            G = nx.from_numpy_array(matrix)
            return G
        except:
            # If both fail, try as edge list (fallback to original behavior)
            with open(filename, "r", encoding='utf8') as data:
                read = csv.reader(data)
                GraphT = nx.Graph()
                G = nx.read_edgelist(read, create_using=GraphT, nodetype=int, data=(('weight',float),))
                return G

def read_graph_from_edgelist(filename):
    """
    Read a graph from a CSV file containing an edge list.
    Expected format: source,target,weight or source,target
    """
    try:
        df = pd.read_csv(filename)
        G = nx.Graph()
        
        # Check if weight column exists
        if 'weight' in df.columns:
            edges = [(row['source'], row['target'], {'weight': row['weight']}) 
                    for _, row in df.iterrows()]
        else:
            edges = [(row[0], row[1]) for _, row in df.iterrows()]
        
        G.add_edges_from(edges)
        return G
        
    except Exception as e:
        print(f"Error reading edge list: {e}")
        return None

# Choose your input file and format
# For matrix format:
# filename = 'Data/location_proximity_matrix.csv'
# G = read_graph_from_matrix(filename)

# For edge list format:
filename = 'adjacency_list.csv'
G = read_graph_from_edgelist(filename)

# Alternatively, try to automatically detect format:
# filename = 'filtered_matrix.csv'
# G = read_graph_from_matrix(filename)

if G is not None:
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    
    # Visualization
    plt.figure(figsize=(12, 10))
    
    # For large graphs, use spring layout with iterations limit
    
    pos = nx.spring_layout(G)
    node_size = 20
    
    nx.draw(G, pos, node_size=node_size, with_labels=False, alpha=0.7)
    plt.title("Network Visualization")
    plt.axis('off')
    plt.tight_layout()
    plt.show()
else:
    print("Failed to load graph from file")
