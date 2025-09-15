import numpy as np
import networkx as nx
from networkx.algorithms import planarity
import matplotlib.pyplot as plt
import pandas as pd

def verify_planarity(adjacency_matrix):
    """
    Verify if a graph represented by an adjacency matrix is planar
    
    Parameters:
    adjacency_matrix: numpy array representing the adjacency matrix
    
    Returns:
    is_planar: Boolean indicating if the graph is planar
    """
    # Create a graph from the adjacency matrix
    G = nx.from_numpy_array(adjacency_matrix)
    
    # Check if the graph is planar
    is_planar, _ = planarity.check_planarity(G)
    
    return is_planar

def construct_pmfg(proximity_matrix):
    """
    Construct a Planar Maximally Filtered Graph (PMFG) from a proximity matrix
    
    Parameters:
    proximity_matrix: numpy array representing the proximity matrix ϕpp′
    
    Returns:
    pmfg: NetworkX graph representing the PMFG
    """
    n = proximity_matrix.shape[0]
    
    # Create a list of all edges with their proximity values
    edges = []
    for i in range(n):
        for j in range(i+1, n):
            if proximity_matrix[i, j] > 0:  # Only consider positive proximities
                edges.append((i, j, proximity_matrix[i, j]))
    
    # Sort edges by proximity in descending order
    edges.sort(key=lambda x: x[2], reverse=True)
    
    # Initialize an empty graph
    G = nx.Graph()
    G.add_nodes_from(range(n))
    
    # Add edges while maintaining planarity
    for edge in edges:
        i, j, weight = edge
        G.add_edge(i, j, weight=weight)
        
        # Check if the graph is still planar
        is_planar, _ = planarity.check_planarity(G)
        
        if not is_planar:
            # Remove the edge if it makes the graph non-planar
            G.remove_edge(i, j)
    
    return G

def visualize_graph(graph, labels=None):
    """
    Visualize a graph with optional node labels
    
    Parameters:
    graph: NetworkX graph to visualize
    labels: Optional list of node labels
    """
    plt.figure(figsize=(10, 8))
    
    # Use spring layout for better visualization
    pos = nx.spring_layout(graph, weight='weight', seed=42)
    
    # Draw the graph
    nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=500)
    nx.draw_networkx_edges(graph, pos, edge_color='gray')
    
    # Add labels if provided
    if labels:
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=10)
    else:
        nx.draw_networkx_labels(graph, pos, font_size=10)
    
    plt.title("Planar Maximally Filtered Graph (PMFG)")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Create a sample proximity matrix (ϕpp′)
    # In practice, this would come from your economic data
    
    proximity_matrix = pd.read_csv('Data/prox/product_proximity_matrix.csv', index_col=0)


    
    # Make it symmetric (proximity matrices are symmetric)
    #proximity_matrix = (proximity_matrix + proximity_matrix.T) / 2
    
    # Set diagonal to zero (no self-proximity)
    #np.fill_diagonal(proximity_matrix, 0)
    
    #print("Original proximity matrix:")
    #print(proximity_matrix)
    
    # Verify if the complete graph is planar (it shouldn't be for n > 4)
    complete_graph_planar = verify_planarity(proximity_matrix)
    print(f"\nComplete graph is planar: {complete_graph_planar}")
    
    # Construct the PMFG
    pmfg = construct_pmfg(proximity_matrix)
    
    print(f"\nPMFG has {pmfg.number_of_nodes()} nodes and {pmfg.number_of_edges()} edges")
    
    # Verify that the PMFG is planar
    pmfg_planar = verify_planarity(nx.to_numpy_array(pmfg))
    print(f"PMFG is planar: {pmfg_planar}")
    pmfg.to_csv('pmfg_2023_prod.csv') 
    # Create some sample labels (in practice, these would be product/activity names)
    
    # Visualize the PMFG
    #visualize_graph(pmfg, labels)
    
    # Print the edges in the PMFG with their weights
    #print("\nEdges in the PMFG:")
    #for edge in pmfg.edges(data=True):
    #    print(f"P{edge[0]+1} -- P{edge[1]+1} (weight: {edge[2]['weight']:.3f})")
