import pandas as pd
import plotly.express as px
import os

def load_file_df(file_path):
    """
    Load the file from the file path.
    Return the dataframe.
    """
    df = pd.read_csv(file_path)
    return df

def mh_remove_chronics(df, remove_key_words=["Crude", "Adj"], mh_key_words="MH"):
    """
    Remove columns with key words in remove_key_words and keep columns with key words in mh_key_words
    """
    indf = df.copy()
    col_lst = indf.columns
    remove_lst = [
        x
        for x in col_lst
        if any(word in x for word in remove_key_words) and mh_key_words not in x
    ]
    indf.drop(columns=remove_lst, inplace=True)
    return indf

def mh_clean_transfrom(
    df, col_lst=["MHLTH_CrudePrev", "MHLTH_Crude95CI"], trans_col="Geolocation"
):
    """
    Return a new dataframe with columns in col_lst removed and Geolocation transformed to a list of float
    """
    new_df = df.drop(columns=col_lst).copy()
    new_df[trans_col] = new_df[trans_col].apply(
        lambda x: x.replace("(", "").replace(")", "")
    )
    new_df[trans_col] = new_df[trans_col].apply(lambda x: x.split(","))
    new_df[trans_col] = new_df[trans_col].apply(lambda x: [float(x[0]), float(x[1])])

    return new_df

def save_csv(df, file_path):
    """
    Output the dataframe to a csv file if the file does not exist
    """
    if os.path.exists(file_path):
        print(f"{file_path} already exists.")
    else:
        return df.to_csv(file_path, index=False)

def show_top5(df, col_name):
    """
    Show the top 5 values of the column in the dataframe
    """
    return df.sort_values(by=col_name, ascending=False).head(5)

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