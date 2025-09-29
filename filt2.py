import numpy as np
from scipy.spatial.distance import squareform
import networkx as nx
import planarity
import pandas as pd

def compute_PMFG(sorted_edges, nb_nodes):
    """
    Compute Planar Maximally Filtered Graph (PMFG)
    """
    PMFG = nx.Graph()
    
    # Add all nodes first to ensure we have the correct number
    for i in range(nb_nodes):
        PMFG.add_node(i)
    
    edges_added = 0
    max_edges = 3 * (nb_nodes - 2)  # Maximum edges for planar graph
    
    for edge in sorted_edges:
        # Add the edge temporarily
        PMFG.add_edge(edge['source'], edge['dest'], weight=edge['weight'])
        
        # Check if graph remains planar
        if not planarity.is_planar(PMFG):
            # Remove edge if it violates planarity
            PMFG.remove_edge(edge['source'], edge['dest'])
        else:
            edges_added += 1
            
        # Stop when we reach maximum edges for planar graph
        if edges_added >= max_edges:
            break
    
    return PMFG

def sort_graph_edges(G):
    """
    Sort edges by weight (ascending order for PMFG - strongest connections first)
    """
    sorted_edges = []
    
    # Sort edges by weight (you might want descending order for strongest connections)
    for source, dest, data in sorted(G.edges(data=True),
                                     key=lambda x: x[2]['weight'], reverse=True):
        sorted_edges.append({
            'source': source,
            'dest': dest,
            'weight': data['weight']
        })
        
    return sorted_edges

def create_complete_graph_from_proximity_matrix(proximity_matrix):
    """
    Create a complete graph from proximity matrix
    """
    G = nx.Graph()
    
    # Get node names from index
    nodes = proximity_matrix.index.tolist()
    
    # Add nodes
    for node in nodes:
        G.add_node(node)
    
    # Add edges with weights from proximity matrix
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if i < j:  # Avoid duplicate edges and self-loops
                weight = proximity_matrix.iloc[i, j]
                if not np.isnan(weight):  # Only add edges with valid weights
                    G.add_edge(node1, node2, weight=weight)
    
    return G

def main():
    try:
        # Load proximity matrix
        proximity_matrix = pd.read_csv('Data/location_proximity_matrix.csv', index_col=0)
        
        print(f"Loaded proximity matrix: {proximity_matrix.shape}")
        
        # Create complete graph from proximity matrix
        complete_graph = create_complete_graph_from_proximity_matrix(proximity_matrix)
        
        print(f"Complete graph: {len(complete_graph.nodes())} nodes, {len(complete_graph.edges())} edges")
        
        # Sort edges by weight
        sorted_edges = sort_graph_edges(complete_graph)
        
        print(f"Sorted {len(sorted_edges)} edges")
        
        # Compute PMFG
        PMFG = compute_PMFG(sorted_edges, len(complete_graph.nodes()))
        
        print(f"PMFG: {len(PMFG.nodes())} nodes, {len(PMFG.edges())} edges")
        
        # Verify planarity
        if planarity.is_planar(PMFG):
            print("✓ PMFG is planar")
        else:
            print("✗ ERROR: PMFG is not planar!")
            
        return PMFG
        
    except FileNotFoundError:
        print("Error: Could not find 'Data/prox/product_proximity_matrix.csv'")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    pmfg_result = main()
