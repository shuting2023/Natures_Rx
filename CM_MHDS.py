import pandas as pd
import geopandas as gpd
import os

def remove_warnings(): 
    import warnings
    return warnings.filterwarnings("ignore", category=pd.core.common.SettingWithCopyWarning)

def load_cleaning(file_path, key_lst, geo_data='Geolocation', csv_path = 'MHDS/Cleaned/mental_health_cleaned.csv'):
    raw_df = pd.read_csv(file_path)
    # Remove the other chronic diseases
    mh_lst = [x for x in raw_df.columns if 'mh' in x.lower()]
    df = raw_df[key_lst + mh_lst]
    # Remove missing values
    df.dropna(how='any', inplace=True)

    # Split Confidence Interval
    df['Crude95CI_Low'] = df['MHLTH_Crude95CI'].apply(lambda x: x[1:].split(',')[0]).astype(float)
    df['Crude95CI_High'] = df['MHLTH_Crude95CI'].apply(lambda x: x[:-1].split(',')[1]).astype(float)
    df['Adjusted95CI_Low'] = df['MHLTH_Adj95CI'].apply(lambda x: x[1:].split(',')[0]).astype(float)
    df['Adjusted95CI_High'] = df['MHLTH_Adj95CI'].apply(lambda x: x[:-1].split(',')[1]).astype(float)
    df.drop(columns=['MHLTH_Crude95CI', 'MHLTH_Adj95CI'], inplace=True)

    df[geo_data] = df[geo_data].apply(lambda x: x.replace('(', '').replace(')', ''))
    df[geo_data] = df[geo_data].apply(lambda x: x.split(','))
    df[geo_data] = df[geo_data].apply(lambda x: [float(x[0]), float(x[1])])

    if os.path.exists(csv_path) == False:
        df.to_csv(csv_path, index=False)
    return df

def convert_geodf(df):
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Geolocation.apply(lambda x: x[1]), df.Geolocation.apply(lambda x: x[0])))

