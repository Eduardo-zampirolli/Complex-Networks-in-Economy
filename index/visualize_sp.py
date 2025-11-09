import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

# Read municipality shapefile
mun_shapes = gpd.read_file('/home/edu/Downloads/limites/GEOFT_MUNICIPIO_2022.shp')

# Read ICE results
ice_df = pd.read_csv('/home/edu/Downloads/ice_results.csv', encoding='utf-8', 
                     usecols=['Municipality_ID', 'ICE'])

# Rename columns for consistency
ice_df = ice_df.rename(columns={'Municipality_ID': 'codigo_ibge', 'ICE': 'ice_value'})

# Rename shapefile column and convert data types
mun_shapes = mun_shapes.rename(columns={'CD_MUN': 'codigo_ibge'})
mun_shapes['codigo_ibge'] = mun_shapes['codigo_ibge'].astype('int64')
ice_df['codigo_ibge'] = ice_df['codigo_ibge'].astype('int64')

# Merge ICE data with municipality shapes
mun_gdf = mun_shapes.merge(ice_df, on='codigo_ibge', how='inner')

# Filter for São Paulo state (código IBGE starts with 35)
sp_gdf = mun_gdf[mun_gdf['codigo_ibge'].astype(str).str.startswith('35')].copy()

# Ensure the GeoDataFrame is in the correct CRS
if sp_gdf.crs is None:
    sp_gdf = sp_gdf.set_crs("EPSG:4326")
else:
    sp_gdf = sp_gdf.to_crs("EPSG:4326")

# Visualize ICE on map for São Paulo state
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent for São Paulo state
ax.set_extent([-53.5, -44.0, -25.5, -19.5], crs=ccrs.PlateCarree())

# Add background features
ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.1)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=2, edgecolor='black', alpha=0.8)

# Plot municipalities as polygons colored by ICE values
if not sp_gdf.empty:
    # Plot using GeoPandas with Cartopy
    sp_gdf.plot(
        column='ice_value',
        cmap='RdYlBu_r',  # Red for low complexity, Blue for high complexity
        linewidth=0.3,
        ax=ax,
        edgecolor='black',
        alpha=0.8,
        legend=False,  # We'll add a custom colorbar
        transform=ccrs.PlateCarree()
    )
    
    # Add colorbar manually
    vmin = sp_gdf['ice_value'].min()
    vmax = sp_gdf['ice_value'].max()
    sm = plt.cm.ScalarMappable(
        cmap='RdYlBu_r',
        norm=plt.Normalize(vmin=vmin, vmax=vmax)
    )
    sm._A = []
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Índice de Complexidade Econômica (ICE)', fontsize=12)

    # Add title
    ax.set_title('Índice de Complexidade Econômica (ICE) - Municípios de São Paulo',
                fontsize=16, fontweight='bold', pad=20)
    
    # Add grid
    ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')

plt.tight_layout()
plt.savefig('/home/edu/Downloads/limites/ice_sp_municipalities_choropleth.png', dpi=300, bbox_inches='tight')
# plt.show()

# Print statistics
print(f"\n=== ESTATÍSTICAS ===")
print(f"Total de municípios em São Paulo com dados ICE: {len(sp_gdf)}")
print(f"ICE range em São Paulo: {sp_gdf['ice_value'].min():.3f} to {sp_gdf['ice_value'].max():.3f}")
print(f"ICE médio em São Paulo: {sp_gdf['ice_value'].mean():.3f}")
print(f"Top 5 municípios em São Paulo por ICE:")

# Get municipality names if available in the shapefile
name_columns = ['NM_MUN', 'nome', 'NOME', 'name', 'NAME']
municipality_name_col = None
for col in name_columns:
    if col in sp_gdf.columns:
        municipality_name_col = col
        break

if municipality_name_col:
    top_5_sp = sp_gdf.nlargest(5, 'ice_value')[['codigo_ibge', municipality_name_col, 'ice_value']]
    print(top_5_sp.to_string(index=False))
else:
    top_5_sp = sp_gdf.nlargest(5, 'ice_value')[['codigo_ibge', 'ice_value']]
    print(top_5_sp.to_string(index=False))