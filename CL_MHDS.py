import pandas as pd
import os
import warnings

# mh_file_path = 'MHDS/Original/500_Cities__City-level_Data__GIS_Friendly_Format___2017_release_20240514.csv'
# key_lst = ['StateAbbr','PlaceName','PlaceFIPS','Population2010','Geolocation']


def remove_warnings(): 
    """
    Remove the SettingWithCopyWarning
    """
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=pd.core.common.SettingWithCopyWarning)

def load_cleaning(file_path, key_lst, geo_data='Geolocation', csv_path = 'MHDS/Cleaned/mental_health_cleaned.csv'):
    """
    Load the raw data and clean the data
    output the cleaned data to a csv file if not in the directory
    :param file_path: str, file path
    :param key_lst: list, key columns
    :param geo_data: str, default 'Geolocation'
    :param csv_path: str, default 'MHDS/Cleaned/mental_health_cleaned.csv'
    :return: DataFrame
    """
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