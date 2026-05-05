#%%
# read in the MyEBirdData.csv file
import pandas as pd

from datetime import datetime
from pyproj import Proj, transform

df = pd.read_csv('ebird_lists/MyEBirdData.csv')


#%%
# filter by "Submission ID"
submission_id = 'S332532149'
submission_df = df[df['Submission ID'] == submission_id]
print(submission_df.columns)
#print(submission_df)

#%%
# read the template file
template_df = pd.read_excel('artsobs_template.xlsx', sheet_name='Fugl')
print(template_df)
print(template_df.columns)
#%%
# create our own dataframe
state_or_province = submission_df['State/Province']
location_name = submission_df['Location']
latitude_4326 = submission_df['Latitude']
longitude_4326 = submission_df['Longitude']
# convert lat and long to EPSG:32632

in_proj = Proj('epsg:4326')
out_proj = Proj('epsg:32632')
east, north = transform(in_proj, out_proj, latitude_4326, longitude_4326)
#print(north, east)
ebird_name = submission_df['Common Name']
species = submission_df['Scientific Name']
count = submission_df['Count']

ebird_time = submission_df['Time']
ebird_date = submission_df['Date']
ebird_protocol = submission_df['Protocol']
ebird_duration_min = submission_df['Duration (Min)']

# Parse Date + Time into proper datetimes before adding duration.
artsobs_datetime_from = pd.to_datetime(
    ebird_date.astype(str) + ' ' + ebird_time.astype(str),
    errors='coerce'
)
artsobs_datetime_to = artsobs_datetime_from + pd.to_timedelta(ebird_duration_min, unit='m')

artsobs_date_from = artsobs_datetime_from.dt.strftime('%d.%m.%Y')
artsobs_date_to = artsobs_datetime_to.dt.strftime('%d.%m.%Y')
artsobs_time_from = artsobs_datetime_from.dt.strftime('%H:%M')
artsobs_time_to = artsobs_datetime_to.dt.strftime('%H:%M')

artsobs_dict = {
    'navn': ebird_name,
    'Artsnavn': species,
    "Lokalitetsnavn": location_name,
    'Nord': north,
    'Øst': east,
    'Nøyaktighet': '100m',
    'Fra dato': artsobs_date_from,
    'Fra klokkeslett': artsobs_time_from,
    'Til dato': artsobs_date_to,
    'Til klokkeslett': artsobs_time_to,
    'Antall': count,
}
extra_columns = [
    'Hovedlokalitet',
    'Aktivitet',
    'Alder',
    'Kjønn',
    'Prosjekt',
    'Medobservatør',
    'Medobservatør',
    'Medobservatør',
    'Medobservatør',
    'Medobservatør',
    'Medobservatør',
    'Medobservatør',
    'Kommentar',
]


artsobs_df = pd.DataFrame(artsobs_dict)
empty_extra_df = pd.DataFrame('', index=artsobs_df.index, columns=extra_columns)
artsobs_df = pd.concat([artsobs_df, empty_extra_df], axis=1)

# Place Hovedlokalitet directly before Lokalitetsnavn.
cols = artsobs_df.columns.tolist()
if 'Hovedlokalitet' in cols and 'Lokalitetsnavn' in cols:
    cols.remove('Hovedlokalitet')
    loc_idx = cols.index('Lokalitetsnavn')
    cols.insert(loc_idx, 'Hovedlokalitet')
    artsobs_df = artsobs_df[cols]

print(artsobs_df)

# %%
# write to an excel file named with the location and date:
output_path = 'artsobs_output'
output_filename = f"{output_path}/{location_name.iloc[0]}_{ebird_date.iloc[0]}.xlsx"
artsobs_df.to_excel(output_filename, index=False)

# %%
