


import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Read state data
estados_df = pd.read_csv('Data/estados.csv', encoding='utf-8', 
                        usecols=['codigo_uf', 'latitude', 'longitude', 'uf'])

# Create GeoDataFrame for states
geometry = [Point(lon, lat) for lon, lat in zip(estados_df['longitude'], estados_df['latitude'])]
estados_gdf = gpd.GeoDataFrame(
    estados_df, 
    geometry=geometry,
    crs="EPSG:4326"
)

# Read proximity matrix and create graph
proximity_df = pd.read_csv('location_proximity_matrix_UF_2023.csv')

# Create graph from proximity matrix
G = nx.Graph()

# Add nodes (states) - assuming first column contains state IDs
state_ids = proximity_df.iloc[:, 0].unique()
for state_id in state_ids:
    G.add_node(state_id)

# Add edges with weights (proximity values)
# Assuming the CSV has state IDs as both row and column headers
for i, row in proximity_df.iterrows():
    source_state = row.iloc[0]  # First column is the source state ID
    for j, col in enumerate(proximity_df.columns[1:], 1):  # Skip first column (state IDs)
        target_state = int(col)  # Column headers are target state IDs
        weight = row.iloc[j]
        
        # Only add edge if weight exists and states are different
        if pd.notna(weight) and source_state != target_state:
            G.add_edge(source_state, target_state, weight=float(weight))

# Get node positions from estados_gdf
node_pos = {}
for state_id in G.nodes():
    state_info = estados_gdf[estados_gdf['codigo_uf'] == int(state_id)]
    if not state_info.empty:
        point = state_info.iloc[0].geometry
        node_pos[state_id] = (point.x, point.y)

# Visualize
fig = plt.figure(figsize=(16, 14))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent for Brazil
ax.set_extent([-75, -30, -35, 10], crs=ccrs.PlateCarree())

ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.7)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.7)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=0.5, alpha=0.3)

if node_pos:
    # Create a subgraph with only nodes that have coordinates
    nodes_with_coords = list(node_pos.keys())
    G_sub = G.subgraph(nodes_with_coords)
    
    # Calculate node sizes based on SUM OF WEIGHTS (strength) instead of degree
    strength = {}
    for node in G_sub.nodes():
        total_weight = sum(G_sub[node][neighbor].get('weight', 0) for neighbor in G_sub.neighbors(node))
        strength[node] = total_weight
    
    # Normalize node sizes for better visualization
    min_strength = min(strength.values()) if strength else 0
    max_strength = max(strength.values()) if strength else 1
    
    node_sizes = []
    for node in G_sub.nodes():
        if max_strength > min_strength:
            # Scale between 100 and 800 based on weight sum
            normalized_size = 100 + 700 * (strength[node] - min_strength) / (max_strength - min_strength)
        else:
            normalized_size = 300  # Default size if all weights are equal
        node_sizes.append(normalized_size)
    
    # Calculate edge widths based on individual weights
    edge_weights = [G_sub[u][v].get('weight', 1.0) for u, v in G_sub.edges()]
    max_edge_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [0.5 + 4.0 * (w / max_edge_weight) for w in edge_weights]
    
    # Create a colormap for nodes based on strength
    cmap = plt.cm.plasma
    node_colors = []
    for node in G_sub.nodes():
        if max_strength > min_strength:
            normalized_value = (strength[node] - min_strength) / (max_strength - min_strength)
        else:
            normalized_value = 0.5
        node_colors.append(cmap(normalized_value))
    
    # Draw edges first (so they appear behind nodes)
    nx.draw_networkx_edges(
        G_sub, node_pos, 
        edge_color='darkblue', 
        alpha=0.5,
        width=edge_widths, 
        ax=ax
    )
    
    # Draw nodes with color based on total proximity
    nx.draw_networkx_nodes(
        G_sub, node_pos, 
        node_color=node_colors, 
        node_size=node_sizes, 
        alpha=0.8, 
        ax=ax,
        edgecolors='black',
        linewidths=1.0,
        cmap=cmap
    )
    
    # Draw labels for states with better positioning
    labels = {}
    label_positions = {}
    
    for node in G_sub.nodes():
        state_info = estados_gdf[estados_gdf['codigo_uf'] == int(node)]
        if not state_info.empty:
            # Use state abbreviation or code as label
            state_name = state_info.iloc[0]['uf']
            label = str(node)
            labels[node] = label
            label_positions[node] = node_pos[node]
    
    nx.draw_networkx_labels(
        G_sub, label_positions,
        labels=labels,
        font_size=9, 
        font_weight='bold',
        font_color='white',
        ax=ax
    )
    
    # Add colorbar for node strength
    sm = plt.cm.ScalarMappable(cmap=cmap, 
                              norm=plt.Normalize(vmin=min_strength, vmax=max_strength))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.7)
    cbar.set_label('Total Proximity Strength', fontsize=12)

plt.title('State Proximity Network - Brazil 2023\n(Node size and color indicate total proximity strength)', 
          fontsize=14, pad=20)
plt.tight_layout()
plt.show()

# Print detailed statistics
print(f"Number of states: {G.number_of_nodes()}")
print(f"Number of proximity connections: {G.number_of_edges()}")
print(f"Average proximity weight: {np.mean(edge_weights):.4f}")
print(f"Min total proximity (strength): {min_strength:.4f}")
print(f"Max total proximity (strength): {max_strength:.4f}")
print(f"Average total proximity per state: {np.mean(list(strength.values())):.4f}")

# Print top 5 states by total proximity
sorted_strength = sorted(strength.items(), key=lambda x: x[1], reverse=True)
print("\nTop 5 states by total proximity:")
for i, (state_id, strength_val) in enumerate(sorted_strength[:5], 1):
    state_info = estados_gdf[estados_gdf['codigo_uf'] == int(state_id)]
    state_name = state_info.iloc[0]['uf'] if not state_info.empty else f"State {state_id}"
    print(f"{i}. {state_name} (ID: {state_id}): {strength_val:.4f}")
