import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from PIL import ImageColor
from generativepy.color import Color
import contextily as cx

import warnings
warnings.filterwarnings("ignore")


# geo_file = 'GEOJSON/Greenspace_US.geojson'
# merge_file = 'merged_greenspace_mh.csv'
# state_file = 'cb_2018_us_state_500k/cb_2018_us_state_500k.shp'

def df_convert_gdf(df):
    gdf = gpd.GeoDataFrame(df, geometry="geometry")
    return gdf


def load_geo_df_files(file_path):
    gdf = gpd.read_file(file_path)
    return gdf


def convert_col_type(df, col, type):
    df[col] = df[col].astype(type)
    return df


def drop_cols(df, drop_cols):
    indf = df.drop(columns=drop_cols)
    return indf


def merge_dfs(df1, df2, join_type, col1, col2):
    merged_geo_df = df1.merge(df2, how=join_type, left_on=col1, right_on=col2)
    return merged_geo_df


def extarct_imp_cols(df, imp_cols):
    indf = df[imp_cols]
    return indf


def normalize_features(df, features_col):
    """
    Normalize the features to [0, 1] range
    In order to present the features in the same scale
    """
    indf = df.copy()
    for feature_name in features_col:
        indf[feature_name] = indf[feature_name].astype(float)
        max_value = indf[feature_name].max()
        min_value = indf[feature_name].min()
        indf[feature_name] = (indf[feature_name] - min_value) / (max_value - min_value)
    return indf


def mikhailsirenko_colorscale(
    percentile,
    color_list=['#ffb000', '#dc267f', '#648fff', '#785ef0'],
):
    """
    Creating color gradient list for bivariate choropleth map legend

    Code from Mikhail Sirenko, slightly modified to fit our project
    More information: https://github.com/mikhailsirenko/bivariate-choropleth/blob/main/bivariate-choropleth.ipynb

    """

    def hex_to_Color(hexcode):
        """
        Helping function to convert hex color codes to rgb to Color object
        """
        rgb = ImageColor.getcolor(hexcode, "RGB")
        rgb = [v / 255 for v in rgb]  # normalize RGB values to [0,1] for matplotlib
        rgb = Color(
            *rgb
        )  # * unpacks the list into arguments, converts RGB values to Color object
        return rgb  # color object is stored in rgba(4 values) format

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
    ax.set_axis_off()
    return None


def bicolor_legend(
    ax,
    color_list,
    legend_position=[0.6, 0.7, 0.2, 0.2],
    tick_fontsize=6,
    label_fontsize=8,
    x_label="Mental Illness",
    y_label="Total Area of Greenness",
    percentile = np.linspace(0.33, 1, 3)[::-1].tolist()
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

    ax.set_xticklabels(percentile + [0], fontsize=tick_fontsize)
    ax.set_yticklabels(percentile + [0], fontsize=tick_fontsize)

    ax.tick_params(axis="y", labelleft=False, labelright=True)

    ax.yaxis.set_ticks_position("right")
    ax.yaxis.set_label_position("right")
    ax.set_xlabel(x_label, fontsize=label_fontsize)
    _ = ax.set_ylabel(y_label, fontsize=label_fontsize)
    return None
