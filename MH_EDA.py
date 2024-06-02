import pandas as pd
import plotly.express as px
import altair as alt
import os

# mh_file_path = 'MHDS/Original/500_Cities__City-level_Data__GIS_Friendly_Format___2017_release_20240514.csv'

def mh_load_file(file_path):
    df = pd.read_csv(file_path)
    return df

def mh_remove_chronics(df, remove_key_words = ['Crude','Adj'], mh_key_words ='MH'):
    col_lst = df.columns
    remove_lst = [x for x in col_lst if any(word in x for word in remove_key_words) and mh_key_words not in x]
    return df.drop(columns = remove_lst)

def mh_secondary_remove_and_transform(df, col_lst = ['PlaceFIPS', 'MHLTH_CrudePrev', 'MHLTH_Crude95CI'], trans_col = 'Geolocation'):
    new_df = df.drop(columns = col_lst)
    new_df[trans_col] = new_df[trans_col].apply(lambda x: x.replace("(", "").replace(")", ""))
    new_df[trans_col] = new_df[trans_col].apply(lambda x: x.split(","))
    new_df[trans_col] = new_df[trans_col].apply(lambda x: [float(x[0]), float(x[1])])
    return new_df

def mh_to_csv(df, file_path = 'MHDS/MH_cleaned.csv'):
    return df.to_csv(file_path, index = False)

def mh_plotly_treemap(df, city_level = False, path_lst = [px.Constant('US'),'StateAbbr','PlaceName'], color ='MHLTH_AdjPrev', values = 'MHLTH_AdjPrev', style = 'Blues', title = 'Mental Health Prevalence by State and City', width = 1000, height = 600):
    if city_level:
        df['City_State'] = df['PlaceName'] + ', ' + df['StateAbbr']
        path_lst = [px.Constant('US'),'City_State']

    fig = px.treemap(df, path = path_lst, values = values, title = title, color = color,
    color_continuous_scale=style,
    width=width, height=height
    )
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    return fig

def output_visuals(file, file_name, tohtml = False):
    if os.path.exists(file_name):
        print(f'{file_name} already exists.')
    else:
        if tohtml:
            file.write_html(file_name)
        else:
            file.write_image(file_name)

def mh_apply_boundary(df, new_geo_col, boundary, key_col = 'StateAbbr'):
    df[new_geo_col] = ['None' for x in range(len(df))]
    for key,value in boundary.items():
        df.loc[df[key_col].isin(value), new_geo_col] = key
    return df.groupby(new_geo_col).mean().reset_index()

def mh_geo_centroid(df, state_col, state_lst, geo_col = 'Geolocation'):
    """
    Compute the centroid geolocation of selected states
    """

    lat = (
        df[df[state_col].isin(state_lst)][geo_col].apply(lambda x: x[0]).mean()
    )
    lon = (
        df[df[state_col].isin(state_lst)][geo_col].apply(lambda x: x[1]).mean()
    )
    return lat, lon

def mh_OECD_CitySize():
    """
    return OECD Classification of City Size based on Population Size
    """

    return {
    'Small Urban Areas': [50000,200000],
    'Medium-Size Urban Areas': [200000,500000],
    'Metropolitan Areas': [500000,1500000],
    'Large Metropolitan Areas': [1500000, 100**100]
    }


def mh_apply_CitySize(df,city_size_dict, col = 'Population2010', new_col = 'CitySize'):
    for key, value in city_size_dict.items():
        df.loc[df[col].apply(lambda x: value[0]<=x<value[1]), new_col] = key

    new_df = df.groupby(new_col).agg({'Population2010': 'count','MHLTH_AdjPrev': 'mean'}).reset_index()
    new_df['square_MHLTH_AdjPrev'] = new_df['MHLTH_AdjPrev'] ** 2
    return new_df


def mh_pop_vs_mh(df, x_col = 'CitySize', bar_ycol = 'Population2010', point_ycol = 'square_MHLTH_AdjPrev', y_title = 'Number of Cities and Average (sqaured) MH Prevalence', title = 'Population vs MH Prev', width = 500, height = 200):


    count_cities = alt.Chart(df).mark_bar().encode(
        x = alt.X(x_col, axis= alt.Axis(labelAngle = 0)),
        y = alt.Y(bar_ycol, title = y_title)
    ).properties( width = width, height = height, title = title)

    avg_prev = alt.Chart(df).mark_point(size = 50).encode(
        x = x_col,
        y = alt.Y(point_ycol),
        color = 'CitySize'
    )
    return count_cities + avg_prev