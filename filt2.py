import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations

def construct_tmfg(proximity_matrix):
    """
    Construct a Triangulated Maximally Filtered Graph (TMFG) from a proximity matrix.

    This implementation follows the constructive heuristic which is more computationally
    efficient (O(n^2)) than the PMFG's verification-based approach (O(n^3)).

    Parameters:
    proximity_matrix: numpy array representing the proximity matrix (e.g., correlations).

    Returns:
    tmfg: NetworkX graph representing the TMFG.
    """
    # Convert to numpy array if it's a DataFrame
    if isinstance(proximity_matrix, pd.DataFrame):
        proximity_matrix = proximity_matrix.values
    
    # Fix: Get the number of nodes correctly
    n = proximity_matrix.shape[0]  # Get first dimension, not the tuple
    
    if n < 4:
        # For n < 4, the TMFG is simply the complete graph.
        G = nx.from_numpy_array(proximity_matrix)
        return G

    # --- Step 1: Initialization - The Seed Tetrahedron ---
    # Find the four nodes with the highest sum of proximities to all other nodes.
    # This is a common heuristic for selecting the initial 4-clique.
    sum_of_proximities = np.sum(proximity_matrix, axis=1)
    # Get the indices of the four largest sums.
    initial_nodes = np.argsort(sum_of_proximities)[-4:]

    # Create the initial graph as a 4-clique (tetrahedron).
    G = nx.Graph()
    G.add_nodes_from(range(n)) # Add all nodes to have them available.
    
    # Add the edges of the initial tetrahedron.
    for i, j in combinations(initial_nodes, 2):
        G.add_edge(i, j, weight=proximity_matrix[i, j])

    # Initialize the list of unincorporated nodes.
    remaining_nodes = list(set(range(n)) - set(initial_nodes))

    # Initialize the list of triangular faces on the graph's surface.
    # For the initial tetrahedron, these are the four faces.
    triangles = [tuple(sorted(c)) for c in combinations(initial_nodes, 3)]

    # --- Step 3: Iterative Vertex Addition - The Greedy Growth Loop ---
    # This loop runs n-4 times until all nodes are incorporated.
    while remaining_nodes:
        best_gain = -np.inf  # Changed to -inf for better initialization
        best_node_to_add = -1
        best_triangle_to_fill = None

        # --- Calculate Gains and Find the Maximum ---
        # For each remaining node, find the best triangle to connect to.
        for node_to_add in remaining_nodes:
            for triangle in triangles:
                v1, v2, v3 = triangle
                # Fix: Calculate gain correctly - sum of three edge weights
                gain = (proximity_matrix[node_to_add, v1] +
                        proximity_matrix[node_to_add, v2] +
                        proximity_matrix[node_to_add, v3])
                
                if gain > best_gain:
                    best_gain = gain
                    best_node_to_add = node_to_add
                    best_triangle_to_fill = triangle
        
        # --- Update the Graph ---
        # Add the best node and connect it to the vertices of the best triangle.
        v1, v2, v3 = best_triangle_to_fill
        G.add_edge(best_node_to_add, v1, weight=proximity_matrix[best_node_to_add, v1])
        G.add_edge(best_node_to_add, v2, weight=proximity_matrix[best_node_to_add, v2])
        G.add_edge(best_node_to_add, v3, weight=proximity_matrix[best_node_to_add, v3])

        # --- Update State for the Next Iteration ---
        # Remove the added node from the list of remaining nodes.
        remaining_nodes.remove(best_node_to_add)
        
        # The filled triangle is removed from the list of faces.
        triangles.remove(best_triangle_to_fill)

        # Three new triangles are created on the surface of the graph.
        new_triangle1 = tuple(sorted((best_node_to_add, v1, v2)))
        new_triangle2 = tuple(sorted((best_node_to_add, v1, v3)))
        new_triangle3 = tuple(sorted((best_node_to_add, v2, v3)))
        triangles.extend([new_triangle1, new_triangle2, new_triangle3])

    # The final graph is the TMFG. It is planar by construction.
    # Remove isolated nodes that were never connected (should not happen for n>=4).
    G.remove_nodes_from(list(nx.isolates(G)))
    return G

def visualize_graph(graph, labels=None, title="Filtered Graph"):
    """
    Visualize a graph with optional node labels.
    """
    plt.figure(figsize=(12, 10))
    
    # Spring layout is good for visualizing the structure.
    pos = nx.spring_layout(graph, weight='weight', seed=42, iterations=100)
    
    # Draw the graph elements.
    nx.draw_networkx_nodes(graph, pos, node_color='skyblue', node_size=600, alpha=0.9)
    nx.draw_networkx_edges(graph, pos, width=1.5, edge_color='gray', alpha=0.7)
    
    # Add labels if provided.
    if labels:
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=12, font_family='sans-serif')
    else:
        nx.draw_networkx_labels(graph, pos, font_size=12, font_family='sans-serif')
    
    plt.title(title, fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    np.random.seed(42)
    
    # Read the proximity matrix
    proximity_matrix = pd.read_csv('Data/prox/location_proximity_matrix.csv', index_col=0)
    n_nodes = proximity_matrix.shape[0]  # Fix: Get correct number of nodes
    # 1. Use float32
    proximity_matrix = proximity_matrix.astype('float32')

    # 2. Pre-filter weak connections
    threshold = np.percentile(proximity_matrix.values, 95)  # Keep top 5%
    proximity_matrix[proximity_matrix < threshold] = 0

    # 3. Convert triangles to numpy array for vectorization
    print("Constructing TMFG...")
    tmfg = construct_tmfg(proximity_matrix)
   
    nx.write_graphml(tmfg, "2023_loc_tmfg.graphml")
    nx.to_pandas_edgelist(tmfg).to_csv("2023_loc_tmfg.csv", index=False)
    print(f"\nTMFG has {tmfg.number_of_nodes()} nodes and {tmfg.number_of_edges()} edges.")
    # For n>=3, a maximal planar graph has 3n-6 edges.
    print(f"Expected number of edges for a maximal planar graph: {3 * n_nodes - 6}")
    
    # Create sample labels for visualization.
    labels = {i: f"N{i}" for i in range(n_nodes)}
    
    # Visualize the TMFG.
    visualize_graph(tmfg, labels, title="Triangulated Maximally Filtered Graph (TMFG)")
    
    print("\nSample of edges in the TMFG:")
    for i, edge in enumerate(tmfg.edges(data=True)):
        if i >= 10: break
        # Fix: Correct edge printing
        print(f"Node {edge[0]} -- Node {edge[1]} (weight: {edge[2]['weight']:.3f})")
