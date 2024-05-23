import folium
import geopandas as gpd
import json
import folium
import requests

def convert_geodf(df, geo_col = 'Geolocation'):
    """
    Convert DataFrame to GeoDataFrame and 'geolocation' to GeoSeries
    :param df: DataFrame
    :param geo_col: str, default 'Geolocation'
    """

    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[geo_col].apply(lambda x: x[1]), 
                                                            df[geo_col].apply(lambda x: x[0])))

def geo_centroid(df,state_lst):
    """
    Compute the centroid geolocation of selected states
    """

    lat = df[df['StateAbbr'].isin(state_lst)]['Geolocation'].apply(lambda x: x[0]).mean()
    lon = df[df['StateAbbr'].isin(state_lst)]['Geolocation'].apply(lambda x: x[1]).mean()
    return lat, lon

def choropleth_map(df, cent_lat, cent_lon, city_level = True,
               start = 7, color = 'YlGnBu', opacity = 0.7, l_weight = 1,
               geojson_path = 'partial_city_bound.geojson'):
    """
    Creating folium choropleth map based on city_level or not
    if city_level == True, present the city level map
    else, present the state level map
    :param df: DataFrame
    :param cent_lat: float, centroid latitude
    :param cent_lon: float, centroid longitude
    :param city_level: bool, default True
    :param start: int, determine zoom_start, default 7
    :param color: str, determine block colors, default 'YlGnBu'
    :param opacity: float, determine block opacity, default 0.7
    :param l_weight: int, determine weight of boundary line, default 1
    :param geojson_path: str, boundaries for city level map, default 'partial_city_bound.geojson'
    """

    m = folium.Map(location=[cent_lat,cent_lon], zoom_start = start)

    if city_level:
        geo_df = df
        geodata = json.load(open(geojson_path,'r'))
        column_lst =['PlaceName','MHLTH_AdjPrev']
        on = 'feature.properties.NAME'
    else:
        geo_df = df.groupby('StateAbbr').mean().reset_index()
        # got the state ploygon geolocation data from Folium examples 
        geodata = requests.get("https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json").json()
        column_lst =['StateAbbr','MHLTH_AdjPrev']
        on = 'feature.id'
        
    folium.Choropleth(
        geo_data = geodata,
        data = geo_df,
        columns = column_lst,
        key_on = on,
        fill_color = color,
        fill_opacity = opacity,
        line_weight = l_weight
    ).add_to(m)

    return m
