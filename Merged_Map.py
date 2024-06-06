import geopandas as gpd
import pandas as pd
import numpy as np
import folium
import json
import os

from shapely.geometry import Point

# gpkg_path = 'GreenspaceDownload/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.gpkg'

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


def loading_and_cleaning(gpkg_path):
    """
    Load geopackage file and apply the cleaning process of Greenspace data.
    Returns cleaned geopandas dataframe.
    """
    if os.path.exists('GEOJSON/cleaned_geopackage.geojson'):
        print("Loading existing cleaned file...")
        df = gpd.read_file('GEOJSON/cleaned_geopackage.geojson')
    else:
        print("Loading large file, may take 1-2 minutes...")
        rawdf = gpd.read_file(gpkg_path)
        print("File loaded successfully.")

        print('Beginning cleaning process, may take 2-3 minutes...')

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

        print("Cleaning process completed.")
        df.to_file('GEOJSON/geopackage.geojson', driver="GeoJSON")

    return df

def rows_matching_with_merged(df_path, df, key_col="UC_Grouping"):
    """
    Input path of merged file, df to be matched and key_col to be matched,
    Returns merged_greenspace_mh df and updated df with only matching rows
    """

    mer_df = pd.read_csv(df_path, index_col=0)

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


def df_to_geojson(df, filename="GEOJSON/Greenspace_US.geojson"):
    """
    Input df, filename to save,
    Returns None, saves geojson file
    """
    if os.path.exists(filename):
        print("Geojson file already exists.")
    else:
        df.to_file(filename, driver="GeoJSON")

    return None

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
            val = df[df[geo_col[0]] == s["properties"][key]][col].values[0]
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

def apply_geo_labels(df, label_col_name, label_dict, base_col):
    """
    Apply labels based on existing column.
    Input df, name for labeled column, label dictionary, and based column.
    Returns the dataframe with the labeled column.
    """
    new_df = df.copy()
    new_df[label_col_name] = ["None" for x in range(len(df))]
    for key, value in label_dict.items():
        new_df.loc[new_df[base_col].isin(value), label_col_name] = key
    return new_df

def cate_to_num_labels(df, col_name):
    """
    Convert categorical data to numerical labels.
    Input dataframe and column name.
    Return dictionary with key as the numerical label and value as the categorical data.
    """
    lst = [x for x in df[col_name].unique()]
    label_dict = {}
    for n, string in [x for x in enumerate(lst)]:
        label_dict[n] = string
    return label_dict

def apply_num_labels(df, label_col_name, label_dict, base_col):
    """
    Apply labels based on existing column.
    Input df, name for labeled column, label dictionary, and based column.
    Returns the dataframe with the labeled column.
    """
    df[label_col_name] = ["None" for x in range(len(df))]
    for key, value in label_dict.items():
        df.loc[df[base_col]==(value), label_col_name] = key
    return df

def div_merged_dropcols(df, drop_lst):
    """
    Manipulate the merged dataset by dropping columns.
    Input dataframe.
    Returns the manipulated dataframe.
    """
    return df.drop(columns = drop_lst)

def aggregate_division(df, non_mean_cols = ['Biome_Class', 'Division'], mode_col = 'Biome_Class',groupby_col = 'Division'):  

    """
    Input dataframe, non_mean_cols, mode_col, and groupby_col.
    Returns the aggregated dataframe.
    """
    agg_dict = {}
    for x in df.columns:
        if x not in non_mean_cols:
            agg_dict[x] = 'mean'
        elif x == 'Biome_Class':
            agg_dict[x] = lambda x: pd.Series.mode(x)[0]

    group_df = df.groupby(groupby_col).agg(agg_dict)
    group_df['Biome_Class'] = group_df['Biome_Class'].astype('str')
    group_df.reset_index(inplace=True)
    return group_df

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

def aggregation_manipulation(label_dict, raw_df, drop_lst = ['E_BM_NM_LST','State', 'Cities in Urban Center_copy','INCM_CMI', 'DEV_CMI','Latitude', 'Longitude','UC_Grouping','Population2010'], non_mean_cols = ['Biome_Class', 'Region'], mode_col = 'Biome_Class',groupby_col = 'Region'):
    """
    Input label_dict, raw_df, drop_lst, non_mean_cols, mode_col, and groupby_col.
    Returns the final aggregated dataframe.    
    """
    df_v1 = apply_geo_labels(raw_df, 'Region', label_dict, 'State')

    env_dict = cate_to_num_labels(df_v1, 'E_BM_NM_LST')
    df_v2 = apply_num_labels(df_v1, 'Biome_Class', env_dict, 'E_BM_NM_LST')

    drop_lst = drop_lst
    df_v3 = div_merged_dropcols(df_v2, drop_lst)

    final_df = aggregate_division(df_v3, non_mean_cols, mode_col, groupby_col)
    return final_df