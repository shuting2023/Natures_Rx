import geopandas as gpd
import pandas as pd
import numpy as np
import folium
import json
import os

from shapely.geometry import Point

# gpkg_path = 'GreenspaceDownload/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.gpkg'


def load_gpkg(gpkg_path):
    """
    Input file_path of geopackage file,
    Output geopandas dataframe
    """
    print("Loading large file, may take 1-2 minutes...")
    gdf = gpd.read_file(gpkg_path)
    return gdf


def statefinder(row):
    """
    Helping function to find state of a given point in state_boundaries shapefile,
    Returns state abbreviation if found, else np.nan
    """

    stateboundaries = gpd.read_file("cb_2018_us_state_500k/cb_2018_us_state_500k.shp")
    point = Point(row["Longitude"], row["Latitude"])
    state = stateboundaries[stateboundaries.contains(point)]

    if not state.empty:
        return state.iloc[0]["STUSPS"]
    else:
        return np.nan


def Greenspace_Data_Cleaning(rawdf):
    """
    Cleaning process of Greenspace data,
    input rawdf, returns cleaned df
    """

    print('This may take a few minutes...')

    cols_to_keep = [
        "GCPNT_LAT",
        "GCPNT_LON",
        "CTR_MN_NM",
        "UC_NM_MN",
        "UC_NM_LST",
        "E_GR_AV14",
        "E_GR_AT14",
        "SDG_A2G14",
        "SDG_OS15MX",
        "P15",
        "B15",
        "BUCAP15",
        "INCM_CMI",
        "DEV_CMI",
        "GDP15_SM",
        "E_BM_NM_LST",
        "E_WR_T_14",
        "geometry",
    ]  # add 'geometry' to keep the geometry column

    df = rawdf[cols_to_keep]
    df = df[df["CTR_MN_NM"] == "United States"]
    df.replace(
        to_replace=["?", "??", "???", "NAN"],
        value=[np.nan, np.nan, np.nan, np.nan],
        inplace=True,
    )
    df.rename(
        columns={
            "GCPNT_LAT": "Latitude",
            "GCPNT_LON": "Longitude",
            "CTR_MN_NM": "Country",
            "UC_NM_MN": "Urban Center",
            "UC_NM_LST": "Cities in Urban Center",
        },
        inplace=True,
    )

    a1 = df.loc[482]["Cities in Urban Center"]
    a1replace = a1.replace("’", "'")

    df.at[482, "Urban Center"] = "O'Fallon"
    df.at[482, "Cities in Urban Center"] = a1replace

    df["Cities in Urban Center_copy"] = df["Cities in Urban Center"]
    df["Cities in Urban Center"] = df["Cities in Urban Center"].str.split(";")
    df = df.explode("Cities in Urban Center")
    df.reset_index(inplace=True, drop=False)
    df.rename(
        columns={"index": "UC_Grouping"}, inplace=True
    )  # update UC Grouping to UC_Grouping
    df["Cities in Urban Center"] = df["Cities in Urban Center"].str.strip()

    mhdf = pd.read_csv(
        "MHDS/Original/500_Cities__City-level_Data__GIS_Friendly_Format___2017_release_20240514.csv"
    )
    mh_cities = (mhdf["PlaceName"].unique()).tolist()

    ucgroup = df[df["Cities in Urban Center"].isin(mh_cities)]
    ucgrouplist = ucgroup.index.tolist()

    df = df[df.index.isin(ucgrouplist)]

    df["State"] = df.apply(statefinder, axis=1)

    return df


def rows_matching_with_merged(path, df, key_col="UC_Grouping"):
    """
    Input path of merged file, df to be matched and key_col to be matched,
    Returns merged_greenspace_mh df and updated df with only matching rows
    """

    mer_df = pd.read_csv(path, index_col=0)

    key_list = (mer_df[key_col].unique()).tolist()

    matchgroup = df[df[key_col].isin(key_list)]
    matchgrouplist = matchgroup.index.tolist()

    df = df[df.index.isin(matchgrouplist)]

    return mer_df, df


def smaller_file(gdf, key_cols=["UC_Grouping", "geometry"]):
    """
    Input geopandas dataframe, key columns to keep,
    returns smaller geopandas dataframe with only key columns
    """
    df = gdf[key_cols]
    return df.drop_duplicates()


def df_to_geojson(df, filename="Greenspace_US.geojson"):
    """
    Input df, filename to save,
    Returns None, saves geojson file
    """
    if os.path.exists(filename):
        print("Geojson file already exists.")
    else:
        df.to_file(filename, driver="GeoJSON")

    return None


# col_list = ['Population2010', 'MHLTH_AdjPrev', 'E_GR_AV14', 'E_GR_AT14', 'SDG_A2G14', 'SDG_OS15MX', 'P15','B15', 'BUCAP15', 'GDP15_SM', 'E_WR_T_14', 'INCM_CMI','DEV_CMI', 'E_BM_NM_LST']


def merged_choropleth_map(
    boundary_file_path,
    df,
    col_list,
    lat=39.5,
    lon=-98.35,
    geo_col=["UC_Grouping", "MHLTH_AdjPrev"],
    key="UC_Grouping",
    color="YlGnBu",
    opacity=0.7,
    weight=1,
    zoom_start=5,
    legend="Average Mental Health Prevalence (%)",
):
    """
    Input boundary_file_path, df need to be plotted, col_list to be shown in tooltip, lat, lon, geo_col, key, color, opacity, weight, zoom_start, legend,
    Returns choropleth map

    Parameters:
        boundary_file_path: str, path of boundary file
        df: pd.DataFrame, data to be plotted
        col_list: list, list of columns to be shown in tooltip
        lat: float, latitude of the map
        lon: float, longitude of the map
        geo_col: list, columns to be used for plotting
        key: str, key column to be used for plotting
        color: str, color of the map
        opacity: float, opacity of the map
        weight: int, weight of the line
        zoom_start: int, zoom level of the map
        legend: str, legend of the map
    """

    m = folium.Map(location=[lat, lon], zoom_start=zoom_start)

    geodata = json.load(open(boundary_file_path, "r"))

    cp = folium.Choropleth(
        geo_data=geodata,
        data=df,
        columns=geo_col,
        key_on="feature.properties." + key,
        fill_color=color,
        fill_opacity=opacity,
        line_weight=weight,
        legend_name=legend,
    ).add_to(m)

    # add labels to the map
    # firstly, add mental health prevalence to the geojson file
    for s in cp.geojson.data["features"]:
        for col in col_list:
            val = df[df["UC_Grouping"] == s["properties"]["UC_Grouping"]][col].values[0]
            if val:
                try:
                    s["properties"][col] = int(val)
                except:
                    s["properties"][col] = val
            else:
                s["properties"][col] = "N/A"

    # then, add labels to map through GeoJsonTooltip
    tooltip_col = col_list
    tooltip_aliases = [col + ": " for col in col_list]
    folium.GeoJsonTooltip(fields=tooltip_col, aliases=tooltip_aliases).add_to(
        cp.geojson
    )

    return m


def output_map_html(m, filename="map.html"):
    """
    Input m, filename to save,
    Returns None, saves html file
    """
    if os.path.exists(filename):
        print("HTML file already exists.")
    else:
        print(f"Saving map to {filename}")
        m.save(filename)
    return None
