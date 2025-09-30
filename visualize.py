import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import Point

#arquivos
#Pegar os ids
with open('Data/ordem_id.txt', 'r') as f:
    ordem = f.read().split(',')
id_to_code = {i+1: int(code) for i, code in enumerate(ordem)}
mun_df = pd.read_csv('Data/municipios.csv', encoding='utf-8', usecols=['codigo_ibge', 'latitude', 'longitude', 'nome', 'codigo_uf'])
mun_df['codigo_ibge'] = mun_df['codigo_ibge']//10

#GeoDataframe
geometry = [Point(lon, lat) for lon, lat in zip(mun_df['longitude'], mun_df['latitude'])]
mun_gdf = gpd.GeoDataFrame(
        mun_df, 
        geometry=geometry,
        crs="EPSG:4326"
)
G = nx.read_graphml('2023_loc_tmfg_lib.graphml')
a = G.number_of_edges()
node_pos = {}
for node_id in G.nodes():
    codigo = id_to_code.get(int(node_id))
    if codigo:
        city_info = mun_gdf[mun_gdf['codigo_ibge'] == int(codigo)]
        if not city_info.empty:
            point = city_info.iloc[0].geometry
            node_pos[node_id] = (point.x, point.y)

#visualize

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
    
    # Calculate node sizes based on degree
    degrees = dict(G_sub.degree())
    node_sizes = [50 + 20 * degrees[node] for node in G_sub.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G_sub, node_pos, 
        node_color='red', 
        node_size=node_sizes, 
        alpha=0.7, 
        ax=ax,
        edgecolors='black',
        linewidths=0.5
    )
    
    # Draw edges with weights
    edge_weights = [G_sub[u][v].get('d0', 1.0) for u, v in G_sub.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [0.5 + 2.5 * (w / max_weight) for w in edge_weights]
    
    nx.draw_networkx_edges(
        G_sub, node_pos, 
        edge_color='blue', 
        alpha=0.3, 
        width=edge_widths, 
        ax=ax
    )
    
    # Optional: Draw labels for major cities
    major_cities = [node for node in G_sub.nodes() if degrees[node] > 10]
    major_positions = {node: node_pos[node] for node in major_cities}
    
    if major_positions:
        # Create labels dictionary with the same node IDs
        labels = {node: str(node) for node in major_cities}
        nx.draw_networkx_labels(
            G_sub, major_positions, 
            labels=labels,
            font_size=6, 
            font_weight='bold',
            ax=ax
        )




#Código para os estados

# Load states data
estados_df = pd.read_csv('Data/estados.csv', encoding='utf-8', usecols=['codigo_uf', 'uf', 'nome', 'latitude', 'longitude'])

# Create state-level graph
G_uf = nx.Graph()
uf_positions = {}
uf_sizes = {}

# Map municipalities to their states
mun_to_uf = {}
for node_id in G.nodes():
    codigo = id_to_code.get(int(node_id))
    if codigo:
        city_info = mun_gdf[mun_gdf['codigo_ibge'] == int(codigo)]
        if not city_info.empty:
            uf_code = city_info.iloc[0]['codigo_uf']
            mun_to_uf[node_id] = uf_code

# Count nodes per state and aggregate edges
uf_node_count = {}
for node_id, uf_code in mun_to_uf.items():
    uf_node_count[uf_code] = uf_node_count.get(uf_code, 0) + 1

# Add state nodes
for uf_code in uf_node_count.keys():
    state_info = estados_df[estados_df['codigo_uf'] == uf_code]
    if not state_info.empty:
        state = state_info.iloc[0]
        G_uf.add_node(uf_code, name=state['nome'], uf=state['uf'])
        uf_positions[uf_code] = (state['longitude'], state['latitude'])
        uf_sizes[uf_code] = 300 + uf_node_count[uf_code] * 5  # Size based on number of municipalities

# Add edges between states (aggregate municipal connections with weights)
for edge in G.edges(data=True):
    uf1 = mun_to_uf.get(edge[0])
    uf2 = mun_to_uf.get(edge[1])
    weight = edge[2].get('d0', 1.0)  # Get the weight from the graphml data
    
    if uf1 and uf2 and uf1 != uf2:
        if G_uf.has_edge(uf1, uf2):
            G_uf[uf1][uf2]['weight'] += weight
        else:
            G_uf.add_edge(uf1, uf2, weight=weight)

# Create state-level visualization
fig = plt.figure(figsize=(16, 14))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent for Brazil
ax.set_extent([-75, -30, -35, 10], crs=ccrs.PlateCarree())

ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.7)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.7)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=0.5, alpha=0.3)

# Draw state nodes
if uf_positions:
    node_sizes = [uf_sizes[uf] for uf in G_uf.nodes()]
    
    nx.draw_networkx_nodes(
        G_uf, uf_positions, 
        node_color='green', 
        node_size=node_sizes, 
        alpha=0.8, 
        ax=ax,
        edgecolors='darkgreen',
        linewidths=2
    )
    
    # Draw edges with width based on connection weight
    edge_weights = [G_uf[u][v]['weight'] for u, v in G_uf.edges()]
    max_weight = max(edge_weights) if edge_weights else 1
    edge_widths = [1 + 12 * (w / max_weight) for w in edge_weights]
    
    nx.draw_networkx_edges(
        G_uf, uf_positions, 
        edge_color='purple', 
        alpha=0.6, 
        width=edge_widths, 
        ax=ax
    )
    
    # Add state labels
    labels = {uf_code: estados_df[estados_df['codigo_uf'] == uf_code].iloc[0]['uf'] 
              for uf_code in G_uf.nodes()}
    
    nx.draw_networkx_labels(
        G_uf, uf_positions, 
        labels=labels,
        font_size=10, 
        font_weight='bold',
        ax=ax
    )

plt.title('Brazil States Network (Aggregated from Municipalities)', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.show()

# Print state-level statistics
print(f"\nState Network Statistics:")
print(f"State nodes: {G_uf.number_of_nodes()}")
print(f"State connections: {G_uf.number_of_edges()}")
print(f"States with municipalities: {len(uf_node_count)}")

# Show top interstate connections by weight
print("\nTop interstate connections by weight:")
state_connections = []
for u, v, data in G_uf.edges(data=True):
    state1 = estados_df[estados_df['codigo_uf'] == u].iloc[0]['nome']
    state2 = estados_df[estados_df['codigo_uf'] == v].iloc[0]['nome']
    state_connections.append((state1, state2, data['weight']))

# Sort by weight and show top 10
for state1, state2, weight in sorted(state_connections, key=lambda x: x[2], reverse=True)[:10]:
    print(f"  {state1} - {state2}: {weight:.4f}")





'''
G = nx.read_graphml('2023_loc_tmfg_lib.graphml')
a = G.number_of_edges()
print(a)
plt.figure(figsize=(12, 10))
nx.draw(G,node_size=20, with_labels=False, alpha=0.7)
plt.title("Network Visualization")
plt.axis('off')
plt.tight_layout()
plt.show()
'''
