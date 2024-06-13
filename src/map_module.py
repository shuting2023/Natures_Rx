from generativepy.color import Color
import matplotlib.pyplot as plt
from PIL import ImageColor
import contextily as cx
import geopandas as gpd
import pandas as pd
import numpy as np


import warnings

warnings.filterwarnings("ignore")

### Below one_function_bimap_state_level is a consolidated function that combines all functions to plot a state_level bivariate choropleth map
### Note there is no subplot option for this function, as it is designed to plot a single map

## example usage of one_function_bimap_state_level
# map.one_function_bimap_state_level(state_data, merged_data, env_feature = 'Avg Greenness')


def one_function_bimap_state_level(
    geo_path,
    merged_path,
    env_feature="Avg Greenness",
    other_features=["State"],
    lefton="State",
    righton="STUSPS",
    mh_feature="MH_Score",
    env_color_01="c1_env",
    mh_col="MH_Score",
    mh_color_02="c2_mh",
    percentile=np.linspace(0.33, 1, 3),
    color_list=["#ffb000", "#dc267f", "#648fff", "#785ef0"],
    legend_position=[0, 0.1, 0.1, 0.1],
    tick_fontsize=5,
    label_fontsize=5,
    x_label="Mental Illness Score Index",
    y_label="Average Greenness Index",
    title_fontsize=10,
):
    """
    Consolidate functions return the normalized geodataframe with key features and colorlist for bivariate choropleth map.

    Consolidated functions:
        - merge_geo_df
        - df_focused_env_feature
        - normalize_features
        - mikhailsirenko_colorscale
        - assign_color_cells
        - mat_subplots
        - matplotlib_map
        - set_off_axis
        - bicolor_legend
    """
    geo_df = merge_geo_df(geo_path, merged_path, lefton, righton)
    focused_df = df_focused_env_feature(geo_df, env_feature, other_features)
    normalized_df = normalize_features(focused_df, env_feature, mh_feature=mh_feature)

    colorlist = mikhailsirenko_colorscale(percentile, color_list)
    state_df = normalized_df.groupby(["State", "geometry"]).mean().reset_index()
    state_df = gpd.GeoDataFrame(state_df, geometry="geometry")
    state_color_df = assign_color_cells(
        state_df,
        env_feature,
        env_color_01=env_color_01,
        mh_col=mh_col,
        mh_color_02=mh_color_02,
        percentile=percentile,
    )

    # functions that build the bivariate choropleth map
    _, ax = mat_subplots(1, 1, fig_size=(14, 20))
    matplotlib_map(
        ax,
        state_color_df,
        "c1_env",
        "c2_mh",
        colorlist,
        xlim=[-125, -66.7],
        ylim=[25, 50],
        figsize=(20, 20),
    )
    # adding color legend
    bicolor_legend(
        ax,
        colorlist,
        percentile=percentile,
        legend_position=legend_position,
        tick_fontsize=tick_fontsize,
        label_fontsize=label_fontsize,
        x_label=x_label,
        y_label=y_label,
    )
    # remove axis
    set_off_axis(ax)
    # title
    ax.set_title(
        label=f"Normalized Mental Illness Score and {env_feature} Score by State",
        fontsize=title_fontsize,
    )

    return None


def merge_geo_df(geo_path, merged_path_or_df, lefton, righton):
    """
    Input file path for the geojson file and the merged data file,
    Return the merged geodataframe with the key features
    """
    geo_us = gpd.read_file(geo_path)
    merged_df = pd.read_csv(merged_path_or_df, index_col=0)
    merge_geo_df = merged_df.merge(geo_us, left_on=lefton, right_on=righton, how="left")
    geo_df = gpd.GeoDataFrame(merge_geo_df, geometry="geometry")
    return geo_df


def df_focused_env_feature(gdf, env_feature, other_features):
    """
    Input the merged geodataframe and the key features,
    Return the focused geodataframe with the key features
    """

    focused_df = gdf[["geometry", "MH_Score", env_feature] + other_features]
    return focused_df


def normalize_features(df, env_feature, mh_feature="MH_Score"):
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
    percentile=np.linspace(0.33, 1, 3),
    color_list=["#ffb000", "#dc267f", "#648fff", "#785ef0"],
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
        c00_to_c10.append(c00.lerp(c10, 1 / (num_grps - 1) * i))
        c01_to_c11.append(c01.lerp(c11, 1 / (num_grps - 1) * i))

    for i in range(num_grps):  # filling in the grid vertically
        for j in range(num_grps):
            colorlist.append(c00_to_c10[i].lerp(c01_to_c11[i], 1 / (num_grps - 1) * j))

    # convert colorlist(rgba) back to RGB values
    colorlist = [[c.r, c.g, c.b] for c in colorlist]

    color_list = np.array(colorlist[::-1]).reshape(3, 3, 3)
    return color_list


def assign_color_cells(
    df,
    env_col,
    env_color_01="c1_env",
    mh_col="MH_Score",
    mh_color_02="c2_mh",
    percentile=np.linspace(0.33, 1, 3),
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
                return len(percentile) - 1 - n

    indf = df.copy()
    indf[env_color_01] = indf[env_col].apply(lambda x: assign_color_num(x))
    indf[mh_color_02] = indf[mh_col].apply(lambda x: assign_color_num(x))
    return indf


def mat_subplots(n_row, n_col, fig_size=(20, 10)):
    """
    Create subplots using matplotlib
    """

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
    figsize=(20, 10),
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
    """
    Set off axis for the map
    """

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

    default_ticks = np.arange(0, len(percentile) + 1, 1)
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


### Below functions is consolidate function to plot a 2X3 subplots monovariate choropleth map

## example usage of one_function_monoMap_six_urban_centers
# urban_center_lst = ['Cary', 'Winston-Salem', 'Flint', 'New Bedford', 'Manchester', 'Des Moines']
# map.one_function_monoMap_six_urban_centers(geo_data,merged_data, urban_center_lst = urban_center_lst)


def one_function_monoMap_six_urban_centers(
    geo_path,
    merge_path,
    lefton="UC_Grouping",
    righton="UC_Grouping",
    env_feature="Longitude",
    other_features=["Urban Center", "State"],
    mh_feature="MH_Score",
    percentile=np.linspace(0.2, 1, 5),
    colorlst=["#FF0000", "#0000FF"],
    mh_col="MH_Score",
    mh_color_02="mh_color",
    urban_center_lst=[
        "Cary",
        "New Bedford",
        "Flint",
        "Winston-Salem",
        "Manchester",
        "Des Moines",
    ],
    fig_row=2,
    fig_col=3,
    fig_size=(18, 10),
    alpha=0.7,
    filter_col="Urban Center",
    edgecolor="black",
    linewidth=0.5,
    plot_title_fontsize=10,
    legend_position=[-1.1, -1, 0.8, 0.8],
    tick_fontsize=6,
    label_fontsize=8,
    legend_title="Mental Illness Score Index",
):
    """
    Consolidate all functions to plot a 2X3 subplots monovariate choropleth map
    """
    print("It may take 30s to 1min to generate the map, but it is worth waiting :D")

    geo_df = merge_geo_df(geo_path, merge_path, lefton, righton)
    focused_df = df_focused_env_feature(geo_df, env_feature, other_features)
    normalized_df = normalize_features(focused_df, env_feature, mh_feature)
    color_list = mono_mikhailsirenko_colorscale(percentile, colorlst)
    color_df = mono_assign_color_cells(normalized_df, mh_col, mh_color_02, percentile)

    _, ax = plt.subplots(fig_row, fig_col, figsize=fig_size)
    for i in range(fig_row):
        n = i
        if i > 0:
            n = 3
        for j in range(fig_col):
            map_urban_center(
                color_df,
                ax[i, j],
                urban_center_lst[n + j],
                color_list,
                alpha=0.7,
                mh_color_02="mh_color",
                filter_col="Urban Center",
                edgecolor="black",
                linewidth=0.5,
            )
            set_off_axis(ax[i, j])
            ax[i, j].set_title(
                f"Normalized Mental Illness Score of Urban Center: {urban_center_lst[n + j]}, {geo_df[geo_df['Urban Center'] == urban_center_lst[n + j]]['State'].values[0]}",
                fontsize=plot_title_fontsize,
            )

    mono_color_legend(
        ax[1, 2],
        color_list,
        percentile=percentile,
        legend_position=legend_position,
        tick_fontsize=tick_fontsize,
        label_fontsize=label_fontsize,
        title=legend_title,
    )

    return None


def mono_mikhailsirenko_colorscale(
    percentile=np.linspace(0.2, 1, 5), color_list=["#808080", "#FF0000"]
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
    for i in range(num_grps):
        colorlist.append(c00.lerp(c10, 1 / (num_grps - 1) * i))

    # convert colorlist(rgba) back to RGB values
    colorlist = [[c.r, c.g, c.b] for c in colorlist]

    color_list = np.array(colorlist).reshape(1, -1, 3)
    return color_list


def mono_assign_color_cells(
    df,
    mh_col="MH_Score",
    mh_color_02="mh_color",
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
                return len(percentile) - 1 - n

    indf = df.copy()
    indf[mh_color_02] = indf[mh_col].apply(lambda x: assign_color_num(x))
    return indf


def map_urban_center(
    gdf,
    ax,
    urban_center,
    colorlist,
    mh_color_02="mh_color",
    filter_col="Urban Center",
    edgecolor="black",
    linewidth=0.5,
    alpha=1,
):
    fil_df = gdf[gdf[filter_col] == urban_center]
    fil_df.plot(
        ax=ax,
        color=colorlist[0][fil_df["mh_color"]][0].tolist(),
        alpha=alpha,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    cx.add_basemap(ax, crs=gdf.crs, source=cx.providers.OpenStreetMap.Mapnik)
    return None


def mono_color_legend(
    ax,
    color_list,
    percentile=np.linspace(0.2, 1, 5),
    legend_position=[0.6, 0.7, 0.2, 0.2],
    tick_fontsize=6,
    label_fontsize=8,
    title="Mental Illness Score",
):
    """
    Insert mono-variate choropleth map legend
    """
    ax = ax.inset_axes(legend_position)
    ax.set_aspect("equal", adjustable="box")

    ax.imshow(color_list)

    default_ticks = np.arange(0, len(percentile) + 1, 1)
    adjusted_ticks = default_ticks - 0.5

    ax.set_xticks(adjusted_ticks)

    ax.set_xticklabels([0] +[round(x, 2) for x in percentile], fontsize=tick_fontsize)

    ax.set_yticks([])
    ax.set_title(title, fontsize=label_fontsize, y=-0.7)
    return None
