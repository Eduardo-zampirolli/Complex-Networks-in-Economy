import pandas as pd
import numpy as np
from fast_tmfg import TMFG

# Load your data
proximity_matrix = pd.read_csv('Data/prox/location_proximity_matrix.csv', index_col=0)

# Keep it as a DataFrame instead of converting to numpy array
# corr = proximity_matrix.values  # Remove this line
corr = proximity_matrix  # Use the DataFrame directly

# Calculate covariance matrix if needed
cov = np.cov(proximity_matrix.values, rowvar=False)  # if needed

# Use the optimized implementation
model = TMFG()
cliques, separators, adj_matrix = model.fit_transform(
    weights=corr,  # Pass the DataFrame, not the numpy array
    cov=cov, 
    output='weighted_sparse_W_matrix'
)

# Convert to NetworkX if needed
import networkx as nx
G = nx.from_numpy_array(adj_matrix)
nx.write_graphml(G, "2023_loc_tmfg_lib.graphml")
nx.to_pandas_edgelist(G).to_csv("2023_loc_tmfg_lib.csv", index=False) 


