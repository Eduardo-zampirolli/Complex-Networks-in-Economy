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

# Load São Paulo municipality shapefile
sp_mun_shapes = gpd.read_file('../Data/shapefiles/SP_Municipios.shp')  # Adjust path as needed

# Check and set CRS if needed
print(f"Original CRS: {sp_mun_shapes.crs}")

if sp_mun_shapes.crs is None:
    # Common CRS for Brazil data: SIRGAS 2000 / UTM zone 23S (EPSG:31983) or similar
    # Try to set the appropriate CRS based on your data source
    sp_mun_shapes = sp_mun_shapes.set_crs("EPSG:31983")  # Common for Brazil
    print("Set CRS to EPSG:31983 (SIRGAS 2000 / UTM zone 23S)")

# Now transform to WGS84 (EPSG:4326)
sp_mun_shapes = sp_mun_shapes.to_crs("EPSG:4326")
print(f"Transformed CRS: {sp_mun_shapes.crs}")

# Merge ICE data with municipality shapes for choropleth mapping
# First, let's check the column names in the shapefile
print("Shapefile columns:", sp_mun_shapes.columns.tolist())

# Common column names for municipality code in Brazilian shapefiles:
# CD_MUN, CD_GEOCODM, codigo_ibge, COD_MUN, etc.
# You may need to adjust this based on your shapefile's actual column names

# Try common column names for the merge
municipality_code_columns = ['CD_MUN', 'CD_GEOCODM', 'codigo_ibge', 'COD_MUN', 'GEOCODE', 'code_muni']

# Find which column exists in the shapefile
municipality_col = None
for col in municipality_code_columns:
    if col in sp_mun_shapes.columns:
        municipality_col = col
        break

if municipality_col:
    print(f"Using column '{municipality_col}' for merging")
    
    # Convert to same data type for merging
    sp_mun_shapes[municipality_col] = sp_mun_shapes[municipality_col].astype(str)
    sp_df['codigo_ibge'] = sp_df['codigo_ibge'].astype(str)
    
    # Merge data
    sp_mun_ice = sp_mun_shapes.merge(sp_df, left_on=municipality_col, right_on='codigo_ibge', how='left')
    
    # Check for missing data
    missing_data = sp_mun_ice['ice_value'].isna().sum()
    if missing_data > 0:
        print(f"Warning: {missing_data} municipalities in shapefile don't have ICE data")
else:
    print("No suitable municipality code column found in shapefile")
    # Fallback: just use the shapes without ICE data
    sp_mun_ice = sp_mun_shapes

# Create the plot
fig = plt.figure(figsize=(16, 12))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

ax.set_extent([-53.5, -44.0, -25.5, -19.5], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.1)
ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
ax.add_feature(cfeature.COASTLINE, linewidth=1)
ax.add_feature(cfeature.BORDERS, linewidth=1)
ax.add_feature(cfeature.STATES, linewidth=2, edgecolor='black', alpha=0.8)

# Create choropleth map if we have ICE data
if 'ice_value' in sp_mun_ice.columns and not sp_mun_ice['ice_value'].isna().all():
    # Plot municipality boundaries with ICE colors
    choropleth = sp_mun_ice.plot(column='ice_value', ax=ax, cmap='RdYlBu_r', 
                                legend=True, alpha=0.8, edgecolor='black', linewidth=0.3,
                                missing_kwds={'color': 'lightgray', 'edgecolor': 'red', 'linewidth': 0.3})
    
    ax.set_title('Economic Complexity Index (ICE) - São Paulo Municipalities\n(Choropleth Map)', 
                fontsize=16, fontweight='bold', pad=20)
else:
    # Fallback: just plot the municipality boundaries
    sp_mun_shapes.plot(ax=ax, color='lightblue', edgecolor='black', linewidth=0.3, alpha=0.7)
    
    # Add scatter points with ICE values
    scatter = ax.scatter(
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
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Economic Complexity Index (ICE)', fontsize=10)
    
    ax.set_title('Economic Complexity Index (ICE) - São Paulo Municipalities\n(Points on Municipality Map)', 
                fontsize=16, fontweight='bold', pad=20)

plt.tight_layout()
plt.show()

# Print statistics
print(f"\n=== STATISTICS ===")
print(f"Total municipalities in São Paulo with ICE data: {len(sp_gdf)}")
print(f"Total municipality shapes loaded: {len(sp_mun_shapes)}")
print(f"ICE range in São Paulo: {sp_gdf['ice_value'].min():.3f} to {sp_gdf['ice_value'].max():.3f}")
print(f"Mean ICE in São Paulo: {sp_gdf['ice_value'].mean():.3f}")
print(f"Top 5 municipalities in São Paulo by ICE:")
top_5_sp = sp_gdf.nlargest(5, 'ice_value')[['codigo_ibge', 'nome', 'ice_value']]
print(top_5_sp.to_string(index=False))

