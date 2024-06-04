
import geopandas as gpd
import os
import folium
import json

# regions and divisions data built based on census regions of the US: https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf
# download related boundary files from: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
# unzip the downloaded file and set the path to the .shp file
# NOTE: Do not delete any files in the unzipped folder. Although only the .shp file is used, the other files are necessary for the .shp file to work.
# regional_path = 'MHDS/Original/cb_2018_us_region_500k/cb_2018_us_region_500k.shp' 
# division_path = 'MHDS/Original/cb_2018_us_division_500k/cb_2018_us_division_500k.shp'
# city_path = 'MHDS/Original/500Cities_City_11082016/CityBoundaries.shp'

def us_region():
    """
    Returns a dictionary of US regions and their respective states.
    """

    us_regions = {
        "West": ["AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY"],
        "Midwest": ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"],
        "Northeast": ["CT", "DE", "ME", "MD", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
        "South": ["AL", "AR", "FL", "GA", "KY", "LA", "MS", "NC", "OK", "SC", "TN", "TX", "VA", "WV", "DC"]
    }
    return us_regions


def us_division():
    """
    Returns a dictionary of US divisions and their respective states.
    """
    us_divisions = {
        "New England": ["CT", "ME", "MA", "NH", "RI", "VT"],
        "Middle Atlantic": ["NJ", "NY", "PA"],
        "East North Central": ["IL", "IN", "MI", "OH", "WI"],
        "West North Central": ["IA", "KS", "MN", "MO", "NE", "ND", "SD"],
        "South Atlantic": ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "WV", "DC"],
        "East South Central": ["AL", "KY", "MS", "TN"],
        "West South Central": ["AR", "LA", "OK", "TX"],
        "Mountain": ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY"],
        "Pacific": ["AK", "CA", "HI", "OR", "WA"]
    }
    return us_divisions


def bound_load_file_output_geojson(file_path, df, file = False, full_state=False, cond_col='StateAbbr', cond_value=['CA'], convert_coordinate=False, convert_num=4326, output=False, output_folder='MHDS/', output_filename='gdf.geojson'):
    """
    Load the boundary file and output the GeoJSON file.
    Convert the coordinate to WGS84 (standard coordinate) if convert_coordinate is True.
    Output full state boundary if full_state is True, otherwise output the boundary of the specified states.

    Parameters:
    file_path (str): path to the boundary file.
    full_state (bool): whether to output the full state boundary.
    cond_col (str): if full_state is False, input column name to filter the boundary file.
    cond_value (list): if full_state is False, input list of values to filter the boundary file.
    convert_coordinate (bool): whether to convert the coordinate.
    convert_num (int): if convert_coordinate is true, input number to convert the coordinate. Default is 4326 (WGS84).
    output (bool): whether to output the file.
    output_folder (str): if output is True, input folder name to output the file.
    output_filename (str): if output is True, input file name to output the file.
    """
    if file:
        gdf = gpd.read_file(file_path)
        gdf.dropna(how='any', inplace=True)
    else:
        gdf = df

    # if full_state is True, then it will return the full state boundary
    if full_state:
        print('Be aware of large dataset!')
    else:
        gdf = gdf[gdf[cond_col].isin(cond_value)]

    # if convert_coordinate is True, then it will convert the coordinate to the specified number
    if convert_coordinate:
        gdf = gdf.to_crs(epsg=convert_num)

    # if output is True, then it will output the file to the specified folder
    if output:
        if os.path.exists(output_folder + output_filename):
            print('File already exists.')
        else:
            gdf.to_file(output_folder + output_filename, driver='GeoJSON')

    return gdf


def choropleth_map(boundary_file, df, lat=39.5, lon=-98.35, geo_col=['Regions', 'MHLTH_AdjPrev'], key='feature.properties.NAME', color='YlGnBu', opacity=0.7, weight=1, zoom_start=3, legend='Average Mental Health Prevalence (%)'):
    """
    Output interactive choropleth map.

    Parameters:
    boundary_file (str): path to the boundary file.
    df (DataFrame): DataFrame containing the data to be displayed on the map.
    lat (float): latitude of the center of the map.
    lon (float): longitude of the center of the map.
    geo_col (list): list of columns in df, column[0] should be the geographic boundary, column[1] is the series to be displayed on the map.
    key (str): key to be used to match the data in df with the boundary file.
    color (str): color scheme to be used for the map.
    opacity (float): opacity of the fill color.
    weight (int): weight of the boundary lines.
    zoom_start (int): initial zoom level of the map.
    legend (str): legend title.
    """

    m = folium.Map(location=[lat, lon], zoom_start=zoom_start)

    geodata = json.load(open(boundary_file, 'r'))

    cp = folium.Choropleth(
        geo_data=geodata,
        data=df,
        columns=geo_col,
        key_on=key,
        fill_color=color,
        fill_opacity=opacity,
        line_weight=weight,
        legend_name=legend
    ).add_to(m)

    # add labels to the map
    # firstly, add mental health prevalence to the geojson file
    for s in cp.geojson.data['features']:
        s['properties'][geo_col[1]] = round(df[df[geo_col[0]] == s['properties']['NAME']][geo_col[1]].values[0], 2)
    # then, add labels to map through GeoJsonTooltip
    folium.GeoJsonTooltip(['NAME', geo_col[1]]).add_to(cp.geojson)

    return m
