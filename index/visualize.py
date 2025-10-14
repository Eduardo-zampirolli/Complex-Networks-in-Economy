import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Read municipality data
mun_df = pd.read_csv('../Data/municipios.csv', encoding='utf-8', 
                     usecols=['codigo_ibge', 'latitude', 'longitude', 'nome', 'codigo_uf'])

# Read ICE results (now with Municipality_ID column)
ice_df = pd.read_csv('../Data/cnae/2020/ice_results.csv', encoding='utf-8', 
                     usecols=['Municipality_ID', 'ICE'])

# Rename columns for consistency
ice_df = ice_df.rename(columns={'Municipality_ID': 'codigo_ibge', 'ICE': 'ice_value'})

# Merge ICE data with municipality data
mun_ice_df = mun_df.merge(ice_df, on='codigo_ibge', how='inner')

# Create GeoDataFrame
geometry = [Point(lon, lat) for lon, lat in zip(mun_ice_df['longitude'], mun_ice_df['latitude'])]
mun_gdf = gpd.GeoDataFrame(
    mun_ice_df, 
    geometry=geometry,
    crs="EPSG:4326"
)

# Visualize ICE on map
fig = plt.figure(figsize=(16, 14))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent for Brazil
ax.set_extent([-75, -30, -35, 10], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.7)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.7)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=0.5, alpha=0.3)

# Plot cities colored by ICE values
if not mun_gdf.empty:
    # Create scatter plot with ICE values as colors
    scatter = ax.scatter(
        mun_gdf['longitude'], 
        mun_gdf['latitude'],
        c=mun_gdf['ice_value'],
        cmap='RdYlBu_r',  # Red for low complexity, Blue for high complexity
        s=30,  # Point size
        alpha=0.7,
        edgecolors='black',
        linewidths=0.3,
        transform=ccrs.PlateCarree()
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Economic Complexity Index (ICE)', fontsize=12)
    
    # Add title
    ax.set_title('Economic Complexity Index (ICE) by Brazilian Municipalities', 
                fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.show()

# Print statistics
print(f"Total municipalities with ICE data: {len(mun_gdf)}")
print(f"ICE range: {mun_gdf['ice_value'].min():.3f} to {mun_gdf['ice_value'].max():.3f}")
print(f"Mean ICE: {mun_gdf['ice_value'].mean():.3f}")
print(f"Top 5 municipalities by ICE:")
top_5 = mun_gdf.nlargest(5, 'ice_value')[['codigo_ibge', 'nome', 'ice_value']]
print(top_5.to_string(index=False))
'''

import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from shapely.geometry import Point

#arquivos
#Pegar os ids
with open('../Data/cnae/2020/ordem.txt', 'r') as f:
    ordem = f.read().split('\n')
print(ordem)
id_to_code = {i+1: (code) for i, code in enumerate(ordem)}
mun_df = pd.read_csv('../Data/municipios.csv', encoding='utf-8', usecols=['codigo_ibge', 'latitude', 'longitude', 'nome', 'codigo_uf'])
#mun_df['codigo_ibge'] = mun_df['codigo_ibge']//10

ice_df = pd.read_csv('../Data/cnae/2020/ice_results.csv', encoding='utf-8', usecols=['region_index', 'ice_value'])

# Merge ICE data with municipality data
# Assuming region_index corresponds to the order in ordem.txt
ice_df['codigo_ibge'] = ice_df['region_index'].map(lambda x: int(ordem[x]) if x < len(ordem) else None)
mun_ice_df = mun_df.merge(ice_df, on='codigo_ibge', how='inner')

geometry = [Point(lon, lat) for lon, lat in zip(mun_ice_df['longitude'], mun_ice_df['latitude'])]
mun_gdf = gpd.GeoDataFrame(
        mun_ice_df, 
        geometry=geometry,
        crs="EPSG:4326"
)
#visualize ICE on map

fig = plt.figure(figsize=(16, 14))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent for Brazil
ax.set_extent([-75, -30, -35, 10], crs=ccrs.PlateCarree())

ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.7)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.7)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=0.5, alpha=0.3)

# Plot cities colored by ICE values
if not mun_gdf.empty:
    # Create scatter plot with ICE values as colors
    scatter = ax.scatter(
        mun_gdf['longitude'], 
        mun_gdf['latitude'],
        c=mun_gdf['ice_value'],
        cmap='RdYlBu_r',  # Red for low complexity, Blue for high complexity
        s=30,  # Point size
        alpha=0.7,
        edgecolors='black',
        linewidths=0.3,
        transform=ccrs.PlateCarree()
    )
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Economic Complexity Index (ICE)', fontsize=12)
    
    # Add title
    ax.set_title('Economic Complexity Index (ICE) by Brazilian Municipalities', 
                fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.show()

# Print some statistics
print(f"Total municipalities with ICE data: {len(mun_gdf)}")
print(f"ICE range: {mun_gdf['ice_value'].min():.3f} to {mun_gdf['ice_value'].max():.3f}")
print(f"Mean ICE: {mun_gdf['ice_value'].mean():.3f}")
print(f"Top 5 municipalities by ICE:")
top_5 = mun_gdf.nlargest(5, 'ice_value')[['codigo_ibge', 'nome', 'ice_value']]
print(top_5.to_string(index=False))

'''



