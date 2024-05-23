
import geopandas as gpd
import os

# city_path = '500Cities_City_11082016/CityBoundaries.shp'

def load_shp_convert_geo(file_path, num = 4326):
    """
    Load shapefile and convert the coordinate from Web Mercator projection to WGS 84"""

    return gpd.read_file(file_path).to_crs(epsg=num)


def export_geojson(df, all_data = False, state_lst = ['CA'], important_lst =['NAME', 'ST', 'geometry']):
    """
    Export GeoDataFrame to GeoJSON file
    :param df: GeoDataFrame
    :param all_data: bool, default False
    :param state_lst: list, default ['CA']
    :param important_lst: list, default ['NAME', 'ST', 'geometry']
    :return: GeoJSON file"""

    if all_data:
        print('Warining: Using all data may take a long time to load into the Folium map.')
        if os.path.exists(f'{state_lst}_city_bound.geojson') == False:
            return df[important_lst].to_file('city_bound.geojson', driver='GeoJSON')
    else:
        partial_df = df[df['ST'].isin(state_lst)][important_lst]
        print('Output geojson file only contains data of the following states:', state_lst)
        if os.path.exists(f'partial_city_bound.geojson') == False:
            return partial_df.to_file('partial_city_bound.geojson', driver='GeoJSON')
