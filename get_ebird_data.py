#%%
import pandas as pd
from datetime import datetime

def get_ebird_data(submission_ids:list[str] = None) -> pd.DataFrame:
    df = pd.read_csv('ebird_lists/MyEBirdData.csv')
    return df

def get_filtered_ebird_data(
    submission_ids:list[str] = None,
    years:list[int] = None,
    countries:list[str] = None,
    ScientificNames:list[str] = None
) -> pd.DataFrame:
    df = get_ebird_data()
    df['Year'] = pd.to_datetime(df['Date'], errors='coerce').dt.year
    df['Country'] = df['State/Province'].str.split('-').str[0].str.strip()
    if submission_ids is not None:
        df = df[df['Submission ID'].isin(submission_ids)]
    if years is not None:
        df = df[df['Year'].isin(years)]
    if countries is not None:
        df = df[df['Country'].isin(countries)]
    if ScientificNames is not None:
        df = df[df['Scientific Name'].isin(ScientificNames)]
    return df

if __name__ == "__main__":
    filtered_df = get_filtered_ebird_data(
        submission_ids=None,
        years=[2026],
        countries=None,#['FI']
    )
    print(filtered_df)