import numpy as np
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

# Read municipality shapefile
mun_shapes = gpd.read_file('/home/edu/Downloads/limites/GEOFT_MUNICIPIO_2022.shp')

# Read municipality to RGI mapping
mun_rgi_df = pd.read_csv('/home/edu/Downloads/mun_imm_inter.csv', encoding='utf-8')

# Read RGI ICE results
rgi_ice_df = pd.read_csv('/home/edu/Downloads/ice_cod_imm_2020.csv', encoding='utf-8')

# Rename columns for consistency
mun_shapes = mun_shapes.rename(columns={'CD_MUN': 'codigo_ibge'})

# Ensure codigo_ibge is in the same format across dataframes
mun_shapes['codigo_ibge'] = mun_shapes['codigo_ibge'].astype('int64')
mun_rgi_df['CD_GEOCODI'] = mun_rgi_df['CD_GEOCODI'].astype('int64')

# Check the column name for RGI code in ice file
print("Columns in RGI ICE file:", rgi_ice_df.columns.tolist())

# The ICE file has 'region_index' (which is cod_rgi) and 'ice_value'
# Rename for consistency
rgi_ice_df = rgi_ice_df.rename(columns={'region_index': 'cod_rgi'})

# Ensure cod_rgi is the same type
mun_rgi_df['cod_rgi'] = mun_rgi_df['cod_rgi'].astype('int64')
rgi_ice_df['cod_rgi'] = rgi_ice_df['cod_rgi'].astype('int64')

print(f"RGI codes in mapping file: {mun_rgi_df['cod_rgi'].nunique()}")
print(f"RGI codes in ICE file: {rgi_ice_df['cod_rgi'].nunique()}")

# Step 1: Merge municipality shapefile with RGI mapping
mun_with_rgi = mun_shapes.merge(
    mun_rgi_df[['CD_GEOCODI', 'cod_rgi', 'nome_rgi']], 
    left_on='codigo_ibge', 
    right_on='CD_GEOCODI', 
    how='inner'
)

# Step 2: Merge with RGI ICE values
mun_with_ice = mun_with_rgi.merge(
    rgi_ice_df[['cod_rgi', 'ice_value']], 
    on='cod_rgi', 
    how='inner'
)

# Step 3: Dissolve municipality boundaries by RGI code to create RGI polygons
print("Dissolving municipalities into RGI regions...")
rgi_gdf = mun_with_ice.dissolve(by='cod_rgi', aggfunc={
    'ice_value': 'first',  # ICE value is the same for all municipalities in the same RGI
    'nome_rgi': 'first'    # Keep RGI name
})

# Reset index to make cod_rgi a regular column
rgi_gdf = rgi_gdf.reset_index()

# Ensure the GeoDataFrame is in the correct CRS
if rgi_gdf.crs is None:
    rgi_gdf = rgi_gdf.set_crs("EPSG:4326")
else:
    rgi_gdf = rgi_gdf.to_crs("EPSG:4326")

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

# Plot RGI regions as polygons colored by ICE values
if not rgi_gdf.empty:
    # Plot using GeoPandas with Cartopy
    rgi_gdf.plot(
        column='ice_value',
        cmap='RdYlBu_r',  # Red for low complexity, Blue for high complexity
        linewidth=0.5,
        ax=ax,
        edgecolor='black',
        alpha=0.8,
        legend=False,  # We'll add a custom colorbar
        transform=ccrs.PlateCarree()
    )
    
    # Add colorbar manually
    vmin = rgi_gdf['ice_value'].min()
    vmax = rgi_gdf['ice_value'].max()
    sm = plt.cm.ScalarMappable(
        cmap='RdYlBu_r',
        norm=plt.Normalize(vmin=vmin, vmax=vmax)
    )
    sm._A = []
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Índice de Complexidade Econômica (ICE)', fontsize=12)

    # Add title
    ax.set_title('Índice de Complexidade Econômica (ICE) por Regiões Geográficas Imediatas',
                fontsize=16, fontweight='bold', pad=20)
    
    # Add grid
    ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')

plt.tight_layout()
plt.savefig('/home/edu/Downloads/limites/ice_brazil_rgi.png', dpi=300, bbox_inches='tight')
# plt.show()

# Print statistics
print(f"\n=== ESTATÍSTICAS ===")
print(f"Total de Regiões Geográficas Imediatas com dados ICE: {len(rgi_gdf)}")
print(f"Total de municípios mapeados: {len(mun_with_ice)}")
print(f"ICE range: {rgi_gdf['ice_value'].min():.3f} a {rgi_gdf['ice_value'].max():.3f}")
print(f"ICE médio: {rgi_gdf['ice_value'].mean():.3f}")
print(f"\nTop 5 RGI por ICE:")
top_5_rgi = rgi_gdf.nlargest(5, 'ice_value')[['cod_rgi', 'nome_rgi', 'ice_value']]
print(top_5_rgi.to_string(index=False))