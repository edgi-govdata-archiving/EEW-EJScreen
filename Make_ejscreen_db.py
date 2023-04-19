import pandas as pd
import sqlite3

# Read selected fields from the EJScreen CSV file
df = pd.read_csv('EJSCREEN_2022_StatePct_with_AS_CNMI_GU_VI.csv',
                usecols=['OBJECTID', 
                         'ID', 
                         'STATE_NAME', 
                         'ST_ABBREV', 
                         'CNTY_NAME', 
                         'REGION', 
                         'ACSTOTPOP',
                        'MINORPCT', 
                         'LOWINCPCT', 
                         'P_PM25_D2', 
                         'P_OZONE_D2', 
                         'P_DSLPM_D2', 
                         'P_CANCR_D2',
                        'P_RESP_D2', 
                         'P_PTRAF_D2', 
                         'P_LDPNT_D2', 
                         'P_PNPL_D2', 
                         'P_PRMP_D2', 
                         'P_PTSDF_D2',
                        'P_UST_D2', 
                         'P_PWDIS_D2'])

# Rename the ID column to GEOID to match with the census name
df = df.rename(columns={'ID' : 'GEOID'})

# Read the 2020 census data that has been collected into census2020.db
# It contains GEOID, INTPTLAT, INTPTLON fields--the centroid point of
# the census block group
conn = sqlite3.connect('census-shapefiles/census2020.db')
df2 = pd.read_sql_query('select * from census_block_groups', conn)

# Merge the two dataframes to put the INTPTLAT and INTPTLON fields in the
# EJScreen records
df3 = pd.merge(df, df2, on='GEOID')

# Find the points not in the intersection, to make sure we know why.
dfx = df[~df['GEOID'].isin(df2['GEOID'])]
print('EJScreen data contains {} records not found in census2020.db'.format(
        dfx.shape[0]))

print('Missing states are:')
for state in dfx.STATE_NAME.unique():
    print(state)

dfx = df2[~df2['GEOID'].isin(df['GEOID'])]
print('census2020.db contains {} records not found in EJScreen'.format(
        dfx.shape[0]))

# Write the EJ Screen data to the ejscreen2022.db Sqlite database
conn = sqlite3.connect('ejscreen2022.db')
print('Wrote {} records to ejscreen2020.db table ejscreen'.format(
        df3.to_sql('ejscreen', conn, if_exists='replace', index=False)))
