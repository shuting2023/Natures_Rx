
import geopandas as gpd
import os
import folium
import json

# regions and divisions data duilt based on census regions of the US: https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf
# download related boundary files from: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
# unzip the downloaded file and set the path to the .shp file
# NOTE: Do not delete any files in the unzipped folder. Although only the .shp file is used, the other files are necessary for the .shp file to work.
# regional_path = 'MHDS/Original/cb_2018_us_region_500k/cb_2018_us_region_500k.shp' 
# division_path = 'MHDS/Original/cb_2018_us_division_500k/cb_2018_us_division_500k.shp'
# city_path = 'MHDS/Original/500Cities_City_11082016/CityBoundaries.shp'

def us_region():
    us_regions = {
    "West": ["AK", "AZ", "CA", "CO", "HI", "ID", "MT", "NV", "NM", "OR", "UT", "WA", "WY"],
    "Midwest": ["IL", "IN", "IA", "KS", "MI", "MN", "MO", "NE", "ND", "OH", "SD", "WI"],
    "Northeast": ["CT", "DE", "ME", "MD", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"],
    "South": ["AL", "AR", "FL", "GA", "KY", "LA", "MS", "NC", "OK", "SC", "TN", "TX", "VA", "WV","DC"]
    }
    return us_regions

def us_division():
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

def bound_load_file_output_geojson(file_path, full_state = False, cond_col = 'StateAbbr', cond_value = ['CA'], convert_coordinate = False, convert_num = 4326, output = False, output_folder = 'MHDS/', output_filename ='gdf.geojson'):
    gdf = gpd.read_file(file_path)
    gdf.dropna(how='any', inplace=True)

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


def choropleth_map(boundary_file, df, lat = 39.5, lon= -98.35, geo_col = ['Regions', 'MHLTH_AdjPrev'], key = 'feature.properties.NAME', color = 'YlGnBu', opacity = 0.7, weight = 1, zoom_start = 3, legend = 'Average Mental Health Prevalence (%)'):

    m = folium.Map(location=[lat, lon], zoom_start=zoom_start)
    
    geodata = json.load(open(boundary_file, 'r'))

    cp = folium.Choropleth(
        geo_data=geodata,
        data=df,
        columns= geo_col,
        key_on = key,
        fill_color=color,
        fill_opacity=opacity,
        line_weight=weight,
        legend_name= legend
        ).add_to(m)

    # add labels to the map
    # firstly, add mental health prevalence to the geojson file 
    for s in cp.geojson.data['features']:
        s['properties'][geo_col[1]] = round(df[df[geo_col[0]]== s['properties']['NAME']][geo_col[1]].values[0],2)
    # then, add labels to map through GeoJsonTooltip
    folium.GeoJsonTooltip(['NAME',geo_col[1]]).add_to(cp.geojson)

    return m