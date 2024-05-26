import folium
import geopandas as gpd
import json
import folium
import requests

def convert_geodf(df, geo_col = 'Geolocation'):
    """
    Convert DataFrame to GeoDataFrame and 'geolocation' to GeoSeries
    
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

def state_choropleth_map(state_df, cent_lat = 39.5, cent_lon = -98.35,
               start = 5, color = 'YlGnBu', opacity = 0.7, l_weight = 1,
               column_lst =['StateAbbr','MHLTH_AdjPrev'], on = 'feature.id'):
    """
    input state-level df and output state-level choropleth map
    
    parameters:
    state_df(df): state-level DataFrame, groupby state
    cent_lat: float, centroid latitude for the map, default 39.5 (centroid of US)
    cent_lon: float, centroid longitude for the map, default -98.35 (centroid of US)
    start: int, determine starting zooming level for the map, default 7
    color: str, determine colors, default 'YlGnBu'
    opacity: float, determine opacity, default 0.7
    l_weight: int, determine weight of boundary line, default 1
    column_lst: list, 1st-column: geo-column 2nd-column: indicator presented by map, default ['StateAbbr','MHLTH_AdjPrev']
    on: str, determine key_on, aligning geojson and state_df, default 'feature.id'

    """

    m = folium.Map(location=[cent_lat,cent_lon], zoom_start = start)

    # state ploygon geolocation data from Folium examples 
    geodata = requests.get("https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json").json()

    folium.Choropleth(
        geo_data = geodata, data = state_df,
        columns = column_lst, key_on = on,
        fill_color = color, fill_opacity = opacity, 
        line_weight = l_weight
    ).add_to(m)

    return m
    

def city_choropleth_map(df,cent_lat, cent_lon, start = 7, 
                        color = 'YlGnBu', opacity = 0.7, 
                        l_weight = 1, geojson_path = 'partial_city_bound.geojson',
                        column_lst = ['PlaceName','MHLTH_AdjPrev'], 
                        on = 'feature.properties.NAME'):
    """
    input city-level df and output city-level choropleth map
    parameters are similar to state_choropleth_map
    except:
    geojson_path: str, path to geojson file for city boundary

    """

    m = folium.Map(location=[cent_lat,cent_lon], zoom_start = start)
        
    folium.Choropleth(
        geo_data = json.load(open(geojson_path,'r')),
        data = df,
        columns = column_lst,
        key_on = on,
        fill_color = color,
        fill_opacity = opacity,
        line_weight = l_weight
    ).add_to(m)

    return m
