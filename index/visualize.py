import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

# Read municipality shapefile
# Note: You only need to specify the .shp file, GeoPandas will automatically load the other files
mun_shapes = gpd.read_file('/home/edu/Downloads/limites/GEOFT_MUNICIPIO_2022.shp')  # Adjust path to your shapefile

# Read ICE results
ice_df = pd.read_csv('/home/edu/Downloads/ice_results.csv', encoding='utf-8', 
                     usecols=['Municipality_ID', 'ICE'])

# Rename columns for consistency
ice_df = ice_df.rename(columns={'Municipality_ID': 'codigo_ibge', 'ICE': 'ice_value'})

# The shapefile likely has a column with IBGE codes. Common names are:
# 'CD_MUN', 'CD_GEOCMU', 'codigo_ibge', 'COD_MUN', 'GEOCODIGO'
# Check your shapefile columns with: print(mun_shapes.columns)
# Adjust the column name below as needed:

# If the column is named differently, rename it:
mun_shapes = mun_shapes.rename(columns={'CD_MUN': 'codigo_ibge'})
mun_shapes['codigo_ibge'] = mun_shapes['codigo_ibge'].astype('int64')
ice_df['codigo_ibge'] = ice_df['codigo_ibge'].astype('int64')

# Merge ICE data with municipality shapes
mun_gdf = mun_shapes.merge(ice_df, on='codigo_ibge', how='inner')

# Ensure the GeoDataFrame is in the correct CRS
if mun_gdf.crs is None:
    mun_gdf = mun_gdf.set_crs("EPSG:4326")
else:
    mun_gdf = mun_gdf.to_crs("EPSG:4326")

# Visualize ICE on map
fig = plt.figure(figsize=(16, 14))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set extent for Brazil
ax.set_extent([-75, -30, -35, 10], crs=ccrs.PlateCarree())

# Add background features
ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.7)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=0.5, alpha=0.5)

# Plot municipalities as polygons colored by ICE values
if not mun_gdf.empty:
    # Plot using GeoPandas with Cartopy
    mun_gdf.plot(
        column='ice_value',
        cmap='RdYlBu_r',  # Red for low complexity, Blue for high complexity
        linewidth=0.1,
        ax=ax,
        edgecolor='black',
        alpha=0.8,
        legend=False,  # We'll add a custom colorbar
        transform=ccrs.PlateCarree()
    )
    
    # Add colorbar manually
    vmin = mun_gdf['ice_value'].min()
    vmax = mun_gdf['ice_value'].max()
    sm = plt.cm.ScalarMappable(
        cmap='RdYlBu_r',
        norm=plt.Normalize(vmin=vmin, vmax=vmax)
    )
    sm._A = []
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Índice de Complexidade Econômica (ICE)', fontsize=12)

    # Add title em portugues
    ax.set_title('Índice de Complexidade Econômica (ICE) por Municípios Brasileiros',
                fontsize=16, fontweight='bold', pad=20)
    
    # Add grid
    ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')

plt.tight_layout()
plt.savefig('/home/edu/Downloads/limites/ice_brazil_municipalities.png', dpi=300)
#plt.show()

