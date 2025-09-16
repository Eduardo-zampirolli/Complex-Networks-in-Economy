import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
import pandas as pd
from rpy2.rinterface_lib.embedded import RRuntimeError

# Install and load R packages with error handling
try:
    # Try to load NetworkToolbox
    robjects.r('library(NetworkToolbox)')
    print("NetworkToolbox already installed and loaded.")
except RRuntimeError:
    print("NetworkToolbox not found. Installing...")
    try:
        # Install NetworkToolbox
        robjects.r('install.packages("NetworkToolbox", repos="https://cran.r-project.org")')
        robjects.r('library(NetworkToolbox)')
        print("NetworkToolbox successfully installed and loaded.")
    except RRuntimeError as e:
        print(f"Failed to install NetworkToolbox: {e}")
        print("Trying alternative installation methods...")
        
        # Try installing dependencies first
        try:
            robjects.r('''
            # Install dependencies
            if (!require("devtools")) install.packages("devtools", repos="https://cran.r-project.org")
            if (!require("igraph")) install.packages("igraph", repos="https://cran.r-project.org")
            if (!require("Matrix")) install.packages("Matrix", repos="https://cran.r-project.org")
            
            # Try installing NetworkToolbox again
            install.packages("NetworkToolbox", repos="https://cran.r-project.org")
            library(NetworkToolbox)
            ''')
            print("NetworkToolbox installed successfully after installing dependencies.")
        except RRuntimeError as e2:
            print(f"All installation attempts failed: {e2}")
            print("Please install NetworkToolbox manually in R using: install.packages('NetworkToolbox')")
            exit(1)

# Import NetworkToolbox
try:
    network_toolbox = importr('NetworkToolbox')
except Exception as e:
    print(f"Failed to import NetworkToolbox: {e}")
    exit(1)

# Read the proximity matrix
try:
    proximity_matrix = pd.read_csv('Data/prox/location_proximity_matrix.csv', index_col=0)
    print(f"Successfully loaded proximity matrix with shape: {proximity_matrix.shape}")
except FileNotFoundError:
    print("Error: Could not find 'Data/prox/location_proximity_matrix.csv'")
    print("Please check if the file exists and the path is correct.")
    exit(1)
except Exception as e:
    print(f"Error reading proximity matrix: {e}")
    exit(1)

# Convert to numpy array and ensure it's symmetric
proximity_array = proximity_matrix.values

# Ensure the matrix is symmetric (in case there are small numerical differences)
proximity_array = (proximity_array + proximity_array.T) / 2

# Check if the matrix needs to be converted to correlation format
# If proximity values are distances, you might want to convert them to similarities
# For example, if using inverse distance: similarity = 1 / (1 + distance)
# Uncomment the next line if your proximity matrix represents distances:
# proximity_array = 1 / (1 + proximity_array)

# Fill diagonal with 1s (self-similarity) if not already done
np.fill_diagonal(proximity_array, 1.0)

print(f"Proximity matrix shape: {proximity_array.shape}")
print(f"Matrix min value: {proximity_array.min():.4f}")
print(f"Matrix max value: {proximity_array.max():.4f}")

# Apply TMFG using R
try:
    r_matrix = robjects.r.matrix(robjects.FloatVector(proximity_array.flatten()), 
                                nrow=proximity_array.shape[0])
    tmfg_adjacency = np.array(network_toolbox.TMFG(r_matrix))
    print("TMFG algorithm applied successfully.")
except Exception as e:
    print(f"Error applying TMFG: {e}")
    exit(1)

# Create NetworkX graph
G = nx.from_numpy_array(tmfg_adjacency)

# Use the original column names as node labels if available
if proximity_matrix.columns is not None:
    node_labels = {i: label for i, label in enumerate(proximity_matrix.columns)}
    G = nx.relabel_nodes(G, node_labels)

# Save the network
try:
    nx.write_graphml(G, "2023_loc_tmfg_R.graphml")
    nx.to_pandas_edgelist(G).to_csv("2023_loc_tmfg_R.csv", index=False)
    print("Network files saved successfully.")
except Exception as e:
    print(f"Error saving network files: {e}")

# Visualize the network
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, seed=42)

# Adjust visualization based on number of nodes
num_nodes = G.number_of_nodes()
if num_nodes > 50:
    # For large networks, reduce label size and node size
    nx.draw(G, pos, with_labels=False, node_color='lightblue', 
            node_size=100, alpha=0.7)
    plt.title("TMFG Network Structure (Large Network - Labels Hidden)")
elif num_nodes > 20:
    # For medium networks, smaller labels
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=300, font_size=6, font_weight='bold')
    plt.title("TMFG Network Structure")
else:
    # For small networks, normal visualization
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=500, font_size=8, font_weight='bold')
    plt.title("TMFG Network Structure")

plt.tight_layout()
plt.savefig("tmfg_network_visualization.png", dpi=300, bbox_inches='tight')
plt.show()

# Print network statistics
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")
print(f"Network density: {nx.density(G):.4f}")

# Additional network analysis
if G.number_of_edges() > 0:
    print(f"Average clustering coefficient: {nx.average_clustering(G):.4f}")
    
    # Check if the graph is connected
    if nx.is_connected(G):
        print(f"Average shortest path length: {nx.average_shortest_path_length(G):.4f}")
        print(f"Network diameter: {nx.diameter(G)}")
    else:
        print("Network is not connected")
        components = list(nx.connected_components(G))
        print(f"Number of connected components: {len(components)}")
        largest_component = max(components, key=len)
        print(f"Size of largest component: {len(largest_component)}")

# Degree distribution analysis
degrees = [d for n, d in G.degree()]
print(f"Average degree: {np.mean(degrees):.2f}")
print(f"Degree standard deviation: {np.std(degrees):.2f}")

# Plot degree distribution
plt.figure(figsize=(10, 6))
plt.hist(degrees, bins=max(1, len(set(degrees))), alpha=0.7, edgecolor='black')
plt.xlabel('Degree')
plt.ylabel('Frequency')
plt.title('Degree Distribution of TMFG Network')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("tmfg_degree_distribution.png", dpi=300, bbox_inches='tight')
plt.show()

print("Script completed successfully!")

