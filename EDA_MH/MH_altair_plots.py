import altair as alt
import numpy as np

def bar_plot(df, x_col, y_col, title, x_title, y_title, 
             width = 800, height =400, opacity = 0.7, color = 'Indigo'):
    """
    Present feature of variable, sort by y-axis descendingly
    :param df: DataFrame
    :param x_col: str, x-axis column
    :param y_col: str, y-axis column
    :param title: str, title of the plot
    :param x_title: str, x-axis title
    :param y_title: str, y-axis title
    :param width: int, width of the plot
    :param height: int, height of the plot
    """
    return alt.Chart(df).mark_bar().encode(
        x = alt.X(x_col, sort ='-y', title=x_title),
        y = alt.Y(y_col, title = y_title)
        ).properties(
            width=width, height=height, title=title
            ).configure_mark(
            opacity=opacity,
            color=color)

def scatter_plot(df, x_col, y_col, title, x_title, y_title, shape = 'circle', 
                 size = 60, opacity = 0.7):
    """
    Present correlations between two numerical variables
    :param df: DataFrame
    :param x_col: str, x-axis column
    :param y_col: str, y-axis column
    :param title: str, title of the plot
    :param x_title: str, x-axis title
    :param y_title: str, y-axis title
    :param shape: str, shape of the points
    :param size: int, size of the points
    :param opacity: float, opacity of the points
    """
    return alt.Chart(df).mark_point(size = size, shape = shape).encode(
        x = alt.X(x_col, title=x_title, scale=alt.Scale(zero=False)),
        y = alt.Y(y_col, title=y_title, scale=alt.Scale(zero=False)),
        opacity=alt.value(opacity)
        ).properties(title=title)

def feature_trans(df, col, new_col, func):
    df[new_col] = df[col].apply(func)
    return df

def box_plot(df, x_col, y_col, title, x_title, y_title, 
             width = 800, height =400, opacity = 0.7, color = 'Brown'):
    """
    Present overall status of categorical variable
    :param df: DataFrame
    :param x_col: str, categorical variable, x-axis column
    :param y_col: str, numerical variable, y-axis column
    :param title: str, title of the plot
    :param x_title: str, x-axis title
    :param y_title: str, y-axis title
    :param width: int, width of the plot
    :param height: int, height of the plot
    """
    return alt.Chart(df).mark_boxplot().encode(
        x = alt.X(x_col, title=x_title),
        y = alt.Y(y_col, title=y_title, scale=alt.Scale(zero=False)),
        ).properties(
            width=width, height=height, title=title
        ).configure_mark(
            opacity=opacity,
            color=color)