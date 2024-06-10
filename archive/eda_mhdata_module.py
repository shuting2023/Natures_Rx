import pandas as pd
import plotly.express as px
import altair as alt
import os

# mh_file_path = 'MHDS/Original/500_Cities__City-level_Data__GIS_Friendly_Format___2017_release_20240514.csv'


def mh_load_file(file_path):
    """
    Load the file from the file path.
    """
    df = pd.read_csv(file_path)
    return df


def mh_remove_chronics(df, remove_key_words=["Crude", "Adj"], mh_key_words="MH"):
    """
    Remove columns with key words in remove_key_words and keep columns with key words in mh_key_words
    """
    col_lst = df.columns
    remove_lst = [
        x
        for x in col_lst
        if any(word in x for word in remove_key_words) and mh_key_words not in x
    ]
    return df.drop(columns=remove_lst)


def mh_secondary_remove_and_transform(
    df, col_lst=["MHLTH_CrudePrev", "MHLTH_Crude95CI"], trans_col="Geolocation"
):
    """
    Return a new dataframe with columns in col_lst removed and Geolocation transformed to a list of float
    """
    new_df = df.drop(columns=col_lst)
    new_df[trans_col] = new_df[trans_col].apply(
        lambda x: x.replace("(", "").replace(")", "")
    )
    new_df[trans_col] = new_df[trans_col].apply(lambda x: x.split(","))
    new_df[trans_col] = new_df[trans_col].apply(lambda x: [float(x[0]), float(x[1])])
    return new_df


def mh_to_csv(df, file_path="MH_cleaned.csv"):
    """
    Output the dataframe to a csv file if the file does not exist
    """
    if os.path.exists(file_path):
        print(f"{file_path} already exists.")
    else:
        return df.to_csv(file_path, index=False)


def mh_plotly_treemap(
    df,
    path_lst=[px.Constant("US"), "StateAbbr", "PlaceName"],
    color="MHLTH_AdjPrev",
    values="MHLTH_AdjPrev",
    style="Blues",
    title="Mental Health Prevalence by State and City",
    width=1000,
    height=600,
):
    """
    Return a plotly treemap figure

    Parameters:
        df: dataframe
        path_lst: list, the path of the treemap to have a constant parent node, use px.Constant()
        color: str, the column name for color
        values(str), the column name for values
        style: str, the color style
        title: str, the title of the treemap
        width: int, the width of the treemap
        height: int, the height of the treemap
    """
    fig = px.treemap(
        df,
        path=path_lst,
        values=values,
        title=title,
        color=color,
        color_continuous_scale=style,
        width=width,
        height=height,
    )
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return fig


def mh_city_level_treemap(
    df,
    color="MHLTH_AdjPrev",
    values="MHLTH_AdjPrev",
    style="Blues",
    title="Mental Health Prevalence by State and City",
    width=1000,
    height=600,
):
    """
    Return city level treemap figure
    """

    df["City_State"] = df["PlaceName"] + ", " + df["StateAbbr"]
    path_lst = [px.Constant("US"), "City_State"]

    return mh_plotly_treemap(
        df=df,
        path_lst=path_lst,
        color=color,
        values=values,
        style=style,
        title=title,
        width=width,
        height=height,
    )


def mh_aggregation(unagg_df, groupby_col, agg_dict):
    """
    This function takes in an unaggregated dataframe, a column to group by and a column to aggregate.
    It returns a dataframe with the mean of the aggregated column by the group.
    """

    agg_df = unagg_df.groupby(groupby_col).agg(agg_dict).reset_index()
    return agg_df


def output_visuals(file, file_name, tohtml=False):
    """
    Output the visuals to a png file or an html file
    """
    if os.path.exists(file_name):
        print(f"{file_name} already exists.")
    else:
        if tohtml:
            file.write_html(file_name)
        else:
            file.write_image(file_name)


def mh_geo_centroid(df, state_col, state_lst, geo_col="Geolocation"):
    """
    Compute the centroid geolocation of selected states
    """
    lat = df[df[state_col].isin(state_lst)][geo_col].apply(lambda x: x[0]).mean()
    lon = df[df[state_col].isin(state_lst)][geo_col].apply(lambda x: x[1]).mean()
    return lat, lon


def mh_OECD_CitySize():
    """
    Return OECD Classification of City Size based on Population Size
    """
    return {
        "Small Urban Areas": [50000, 200000],
        "Medium-Size Urban Areas": [200000, 500000],
        "Metropolitan Areas": [500000, 1500000],
        "Large Metropolitan Areas": [1500000, 100**100],
    }


def mh_apply_CitySize(df, city_size_dict, col="Population2010", new_col="CitySize"):
    """
    Return a new dataframe with CitySize column added based on the city_size_dict.
    Also add a column of square of MHLTH_AdjPrev for better visualization.
    """
    for key, value in city_size_dict.items():
        df.loc[df[col].apply(lambda x: value[0] <= x < value[1]), new_col] = key

    new_df = (
        df.groupby(new_col)
        .agg({"Population2010": "count", "MHLTH_AdjPrev": "mean"})
        .reset_index()
    )
    new_df["square_MHLTH_AdjPrev"] = new_df["MHLTH_AdjPrev"] ** 2
    return new_df


def mh_pop_vs_mh(
    df,
    x_col="CitySize",
    bar_ycol="Population2010",
    point_ycol="square_MHLTH_AdjPrev",
    y_title="Number of Cities and Average (squared) MH Prevalence",
    title="Population vs MH Prev",
    width=500,
    height=200,
):
    """
    Return combined bar chart and point chart for population vs mental health prevalence
    """
    count_cities = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(x_col, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(bar_ycol, title=y_title),
        )
        .properties(width=width, height=height, title=title)
    )

    avg_prev = (
        alt.Chart(df)
        .mark_point(size=50)
        .encode(x=x_col, y=alt.Y(point_ycol), color="CitySize")
    )
    return count_cities + avg_prev
