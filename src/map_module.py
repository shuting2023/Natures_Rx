from generativepy.color import Color
import matplotlib.pyplot as plt
from PIL import ImageColor
import contextily as cx
import geopandas as gpd
import pandas as pd
import numpy as np


import warnings
warnings.filterwarnings("ignore")

#### Below functions are for data manipulation for bivariate choropleth map (also can be used for monovariate choropleth map, however useless columns may be generated)
# df_manipulation_for_bimap is designed for merged dataset and geodataframe
# if use df_manipulation_for_bimap, the following functions can be skipped
# df_manipulation_for_bimap returns the key geodataframe and colorlist for bivariate choropleth map

### example usage of df_manipulation_for_bimap
# color_df, colorlist = map.df_manipulation_for_bimap(geo_path, merged_path, env_feature, merge_on='UC_Grouping',...)

def df_manipulation_for_bimap(geo_path, merged_path, env_feature,other_features, lefton='UC_Grouping', righton='UC_Grouping',mh_feature='MH_Score', percentile = np.linspace(0.33, 1, 3), color_list=['#ffb000', '#dc267f', '#648fff', '#785ef0'],
    env_color_01 = 'c1_env',
    mh_col = 'MH_Score',
    mh_color_02 = 'c2_mh'):
    """
    Consolidate functions return the key geodataframe and colorlist for bivariate choropleth map.

    Consolidated functions:
        - merge_geo_df
        - df_focused_env_feature
        - normalize_features
        - mikhailsirenko_colorscale
        - assign_color_cells
    """
    geo_df = merge_geo_df(geo_path, merged_path, lefton, righton)
    focused_df = df_focused_env_feature(geo_df, env_feature, other_features)
    normalized_df = normalize_features(focused_df, env_feature, mh_feature=mh_feature)

    colorlist = mikhailsirenko_colorscale(percentile, color_list)
    color_df = assign_color_cells(normalized_df, env_feature, env_color_01, mh_col, mh_color_02, percentile)

    return color_df, colorlist

def merge_geo_df(geo_path, merged_path, lefton, righton):
    geo_us = gpd.read_file(geo_path)
    merged_df = pd.read_csv(merged_path, index_col=0)
    merge_geo_df = merged_df.merge(geo_us, left_on= lefton,right_on = righton, how='left')
    geo_df = gpd.GeoDataFrame(merge_geo_df, geometry='geometry')
    return geo_df

def df_focused_env_feature(gdf, env_feature, other_features):
    focused_df = gdf[['geometry', 'MH_Score', env_feature] + other_features]
    return focused_df

def normalize_features(df, env_feature, mh_feature='MH_Score'):
    """
    Normalize the features to [0, 1] range
    In order to present the features in the same scale
    """
    indf = df.copy()
    for feature_name in [env_feature, mh_feature]:
        indf[feature_name] = indf[feature_name].astype(float)
        max_value = indf[feature_name].max()
        min_value = indf[feature_name].min()
        indf[feature_name] = (indf[feature_name] - min_value) / (max_value - min_value)
    return indf


def hex_to_Color(hexcode):
    """
    Helping function to convert hex color codes to rgb to Color object

    Code from Mikhail Sirenko, slightly modified to fit our project
    More information: https://github.com/mikhailsirenko/bivariate-choropleth/blob/main/bivariate-choropleth.ipynb
    
    """
    rgb = ImageColor.getcolor(hexcode, "RGB")
    rgb = [v / 255 for v in rgb]  # normalize RGB values to [0,1] for matplotlib
    rgb = Color(
        *rgb
    )  # * unpacks the list into arguments, converts RGB values to Color object
    return rgb  # color object is stored in rgba(4 values) format

def mikhailsirenko_colorscale(
    percentile = np.linspace(0.33, 1, 3),
    color_list=['#ffb000', '#dc267f', '#648fff', '#785ef0']
):
    """
    Creating color gradient list for bivariate choropleth map legend

    Code from Mikhail Sirenko, slightly modified to fit our project
    More information: https://github.com/mikhailsirenko/bivariate-choropleth/blob/main/bivariate-choropleth.ipynb

    """

    # basic colors for the gradient
    c00 = hex_to_Color(color_list[0])
    c10 = hex_to_Color(color_list[1])
    c01 = hex_to_Color(color_list[2])
    c11 = hex_to_Color(color_list[3])

    # generate colorlist
    num_grps = len(percentile)
    c00_to_c10 = []
    c01_to_c11 = []
    colorlist = []
    for i in range(num_grps):  # creating top and bottom horizontal color gradient
        # Using lerp to compute intermediate color between two colors at position t
        c00_to_c10.append(c00.lerp(c10, 1 / (num_grps-1) * i))
        c01_to_c11.append(c01.lerp(c11, 1 / (num_grps-1) * i))

    for i in range(num_grps):  # filling in the grid vertically
        for j in range(num_grps):
            colorlist.append(c00_to_c10[i].lerp(c01_to_c11[i], 1 / (num_grps-1) * j))

    # convert colorlist(rgba) back to RGB values
    colorlist = [[c.r, c.g, c.b] for c in colorlist]

    color_list = np.array(colorlist[::-1]).reshape(3, 3, 3)
    return color_list


def assign_color_cells(
    df,
    env_col,
    env_color_01,
    mh_col,
    mh_color_02,
    percentile=np.linspace(0.33, 1, 3).tolist(),
):
    """
    Assigning color index to the cells based on the percentile of the features
    """

    def assign_color_num(x):
        """
        Helping function to assign color index to the cells
        """
        for n in range(len(percentile)):
            if x <= percentile[n]:
                return len(percentile)-1 - n

    indf = df.copy()
    indf[env_color_01] = indf[env_col].apply(lambda x: assign_color_num(x))
    indf[mh_color_02] = indf[mh_col].apply(lambda x: assign_color_num(x))
    return indf


#### Below functions are for plotting bivariate choropleth map using matplotlib

### example usage of bi-map
# fig, ax = map.mat_subplots(1,1,fig_size = (14,20)) # 1,1 means 1 plot
# map.matplotlib_map(ax,color_df, 'c1_env', 'c2_mh', colorlist, xlim= [-125,-70], ylim = [25,50], figsize = (20,20))
## adding color legend
# map.bicolor_legend(ax, colorlist,percentile = np.linspace(0.33, 1, 3), legend_position = [0,0.1,0.1,0.1], tick_fontsize = 5, label_fontsize = 5, x_label = 'Mental Illness Score', y_label = 'Annual Average Precipitation')
# map.set_off_axis(ax) # to remove axis

def mat_subplots(n_row, n_col, fig_size=(20, 10)):
    fig, ax = plt.subplots(n_row, n_col, figsize=fig_size)
    return fig, ax


def matplotlib_map(
    ax,
    df,
    color_col_01,
    color_col_02,
    color_list,
    xlim=[-123, -115],
    ylim=[32, 40],
    alpha=1,
    edge_color="black",
    line_width=0.35,
    figsize=(20, 10)
):
    """
    Create bivariate choropleth map using matplotlib
    """
    ax.set_xlim(xlim[0], xlim[1])
    ax.set_ylim(ylim[0], ylim[1])
    df.plot(
        ax=ax,
        legend=False,
        color=color_list[df[color_col_01], df[color_col_02]],
        alpha=alpha,
        edgecolor=edge_color,
        linewidth=line_width,
    )
    cx.add_basemap(ax, crs=df.crs, source=cx.providers.OpenStreetMap.Mapnik)

    return ax

def set_off_axis(ax):
    ax.set_axis_off()
    return None

def bicolor_legend(
    ax,
    color_list,
    percentile,
    legend_position=[0.6, 0.7, 0.2, 0.2],
    tick_fontsize=6,
    label_fontsize=8,
    x_label="Mental Illness",
    y_label="Total Area of Greenness",
     
):
    """
    Insert bivariate choropleth map legend
    """
    ax = ax.inset_axes(legend_position)
    ax.set_aspect("equal", adjustable="box")

    ax.imshow(color_list)

    default_ticks = np.arange(0, len(percentile)+1, 1)
    adjusted_ticks = default_ticks - 0.5

    ax.set_xticks(adjusted_ticks)
    ax.set_yticks(adjusted_ticks)

    ax.set_xticklabels(percentile[::-1].tolist() + [0], fontsize=tick_fontsize)
    ax.set_yticklabels(percentile[::-1].tolist() + [0], fontsize=tick_fontsize)

    ax.tick_params(axis="y", labelleft=False, labelright=True)

    ax.yaxis.set_ticks_position("right")
    ax.yaxis.set_label_position("right")
    ax.set_xlabel(x_label, fontsize=label_fontsize)
    _ = ax.set_ylabel(y_label, fontsize=label_fontsize)
    return None

#### Below functions are for plotting monovariate choropleth map using matplotlib

def mono_mikhailsirenko_colorscale(
    percentile = np.linspace(0.2, 1, 5),
    color_list=['#808080', '#FF0000']
):
    """
    Creating color gradient list for mono-variable choropleth map legend

    Code from Mikhail Sirenko, slightly modified to fit our project
    More information: https://github.com/mikhailsirenko/bivariate-choropleth/blob/main/bivariate-choropleth.ipynb

    """

    # basic colors for the gradient
    c00 = hex_to_Color(color_list[0])
    c10 = hex_to_Color(color_list[1])

    # generate colorlist
    num_grps = len(percentile)
    colorlist = []
    for i in range(num_grps):  # creating top and bottom horizontal color gradient
        # Using lerp to compute intermediate color between two colors at position t
        colorlist.append(c00.lerp(c10, 1 / (num_grps-1) * i))

    # convert colorlist(rgba) back to RGB values
    colorlist = [[c.r, c.g, c.b] for c in colorlist]

    color_list = np.array(colorlist).reshape(1, -1, 3)
    return color_list

def mono_assign_color_cells(
    df,
    mh_col = 'MH_Score',
    mh_color_02 = 'mh_color',
    percentile=np.linspace(0.2, 1, 5),
):
    """
    Assigning color index to the cells based on the percentile of the features
    """

    def assign_color_num(x):
        """
        Helping function to assign color index to the cells
        """
        for n in range(len(percentile)):
            if x <= percentile[n]:
                return len(percentile)-1 - n

    indf = df.copy()
    # indf[env_color_01] = indf[env_col].apply(lambda x: assign_color_num(x))
    indf[mh_color_02] = indf[mh_col].apply(lambda x: assign_color_num(x))
    return indf

def map_urban_center(gdf, ax, urban_center, colorlist, mh_color_02 = 'mh_color',filter_col = 'Urban Center',edgecolor='black', linewidth=0.5, alpha=1):
    fil_df = gdf[gdf[filter_col] == urban_center]
    fil_df.plot(ax=ax, color= colorlist[0][fil_df['mh_color']][0].tolist(), alpha = alpha, edgecolor=edgecolor, linewidth=linewidth)
    cx.add_basemap(ax, crs=gdf.crs, source=cx.providers.OpenStreetMap.Mapnik)
    return None

def mono_color_legend(ax,color_list,percentile = np.linspace(0.2, 1, 5),
    legend_position=[0.6, 0.7, 0.2, 0.2],
    tick_fontsize=6,
    label_fontsize=8,
    title = 'Mental Illness Score',    
):
    """
    Insert mono-variate choropleth map legend
    """
    ax = ax.inset_axes(legend_position)
    ax.set_aspect("equal", adjustable="box")

    ax.imshow(color_list)

    default_ticks = np.arange(0, len(percentile)+1, 1)
    adjusted_ticks = default_ticks - 0.5

    ax.set_xticks(adjusted_ticks)

    ax.set_xticklabels([0] + [round(x,2) for x in percentile], fontsize=tick_fontsize)

    ax.set_yticks([])
    ax.set_title(title, fontsize=label_fontsize, y = -0.7)
    return None