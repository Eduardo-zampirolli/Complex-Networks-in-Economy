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

# Read ICE results
ice_df = pd.read_csv('../Data/cnae/2020/ice_results.csv', encoding='utf-8', 
                     usecols=['Municipality_ID', 'ICE'])

# Rename columns for consistency
ice_df = ice_df.rename(columns={'Municipality_ID': 'codigo_ibge', 'ICE': 'ice_value'})

# Merge ICE data with municipality data
mun_ice_df = mun_df.merge(ice_df, on='codigo_ibge', how='inner')

# Filter for São Paulo state
sp_df = mun_ice_df[mun_ice_df['codigo_ibge'].astype(str).str.startswith('35')].copy()

# Create GeoDataFrame for São Paulo points
geometry = [Point(lon, lat) for lon, lat in zip(sp_df['longitude'], sp_df['latitude'])]
sp_gdf = gpd.GeoDataFrame(
    sp_df, 
    geometry=geometry,
    crs="EPSG:4326"
)

# Load São Paulo municipality shapefile (already filtered)
sp_mun_shapes = gpd.read_file('../Data/SP_Municipios_2024.shp')  # Adjust path as needed

# Ensure CRS matches
sp_mun_shapes = sp_mun_shapes.to_crs("EPSG:4326")

# Merge ICE data with municipality shapes for choropleth mapping
# This will create a proper choropleth map colored by municipality
sp_mun_ice = sp_mun_shapes.merge(sp_df, left_on='CD_MUN', right_on='codigo_ibge', how='left')

# Create the plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10), 
                               subplot_kw={'projection': ccrs.PlateCarree()})

# Set extent for São Paulo
for ax in [ax1, ax2]:
    ax.set_extent([-53.5, -44.0, -25.5, -19.5], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.2)
    ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.5)
    ax.add_feature(cfeature.COASTLINE, linewidth=1)
    ax.add_feature(cfeature.BORDERS, linewidth=1)
    ax.add_feature(cfeature.STATES, linewidth=2, edgecolor='black', alpha=0.8)

# Plot 1: Choropleth map (municipalities colored by ICE value)
if not sp_mun_ice.empty:
    # Plot municipality boundaries
    sp_mun_shapes.plot(ax=ax1, color='none', edgecolor='gray', linewidth=0.3, alpha=0.7)
    
    # Plot choropleth
    choropleth = sp_mun_ice.plot(column='ice_value', ax=ax1, cmap='RdYlBu_r', 
                                legend=True, alpha=0.8, edgecolor='black', linewidth=0.2)
    
    ax1.set_title('ICE by Municipality (Choropleth)\nSão Paulo State', 
                 fontsize=14, fontweight='bold', pad=20)

# Plot 2: Scatter points over municipality boundaries
if not sp_gdf.empty:
    # Plot municipality boundaries
    sp_mun_shapes.plot(ax=ax2, color='none', edgecolor='gray', linewidth=0.3, alpha=0.7)
    
    # Plot scatter points
    scatter = ax2.scatter(
        sp_gdf['longitude'], 
        sp_gdf['latitude'],
        c=sp_gdf['ice_value'],
        cmap='RdYlBu_r',
        s=40,
        alpha=0.9,
        edgecolors='black',
        linewidths=0.5,
        transform=ccrs.PlateCarree()
    )
    
    # Add colorbar for scatter plot
    cbar = plt.colorbar(scatter, ax=ax2, shrink=0.8, pad=0.02)
    cbar.set_label('Economic Complexity Index (ICE)', fontsize=10)
    
    ax2.set_title('ICE by Municipality (Points)\nSão Paulo State', 
                 fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.show()

# Alternative: Single plot with better choropleth
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

ax.set_extent([-53.5, -44.0, -25.5, -19.5], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.1)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=2, edgecolor='black', alpha=0.8)

# Create choropleth map
if not sp_mun_ice.empty:
    # Plot municipality boundaries with ICE colors
    choropleth = sp_mun_ice.plot(column='ice_value', ax=ax, cmap='RdYlBu_r', 
                                legend=True, alpha=0.8, edgecolor='black', linewidth=0.3)
    
    # Add municipality names (optional - can be crowded)
    # for idx, row in sp_mun_ice.iterrows():
    #     ax.text(row.geometry.centroid.x, row.geometry.centroid.y, 
    #             row['nome'][:10] + '...', fontsize=6, ha='center', 
    #             transform=ccrs.PlateCarree())
    
    ax.set_title('Economic Complexity Index (ICE) - São Paulo Municipalities\n(Choropleth Map)', 
                fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.show()

# Print statistics
print(f"Total municipalities in São Paulo with ICE data: {len(sp_gdf)}")
print(f"Total municipality shapes loaded: {len(sp_mun_shapes)}")
print(f"ICE range in São Paulo: {sp_gdf['ice_value'].min():.3f} to {sp_gdf['ice_value'].max():.3f}")
print(f"Mean ICE in São Paulo: {sp_gdf['ice_value'].mean():.3f}")
print(f"Top 5 municipalities in São Paulo by ICE:")
top_5_sp = sp_gdf.nlargest(5, 'ice_value')[['codigo_ibge', 'nome', 'ice_value']]
print(top_5_sp.to_string(index=False))

# Check if any municipalities are missing ICE data
missing_ice = len(sp_mun_shapes) - len(sp_gdf)
if missing_ice > 0:
    print(f"\nNote: {missing_ice} municipalities in shapefile don't have ICE data")
