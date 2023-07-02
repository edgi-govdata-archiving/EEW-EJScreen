import geopandas as gpd
import os
import pandas as pd
from ECHO_modules.get_data import get_echo_data
import sqlite3
import numpy


# from git import Repo

def log_generation(state, cd, success):
    """
    Logs the results of a generation to a file.

    Parameter state: 2 letter str representation of a state
    Paramter cd: str representing the congressional district
    Parameter success: boolean representing whether the generation was successful or not
    """
    with open('logs/score_generation_logs.txt', 'a') as f:
        f.write(f'{state}, {cd}, {success}\n')


def lookup(state):
    df = pd.read_csv("EEW-EJScreen/state-fips-codes.csv")
    df = df[df['State_Code'] == state]
    return str(df['FIPS_Code'].iloc[0]).zfill(2)


def gen_score(state, cd):
    """
    Parameter state: 2 letter str representation of a state
    Paramter cd: str representing the congressional district

    Returns: a dataframe
    """
    print(f'Generating score for {state} {cd}')
    # INITIAL OUTLINE
    url = f"https://theunitedstates.io/districts/cds/2016/{state}-{str(cd)}/shape.geojson"
    cd_boundary = gpd.read_file(url)
    ### The map isn't needed here.
    # bounds = cd_boundary.bounds
    # map = folium.Map(location=((bounds.miny+bounds.maxy)/2.,
    #                  (bounds.minx+bounds.maxx)/2.), zoom_level=4)
    # folium.GeoJson(cd_boundary, name="Congressional Districts").add_to(map)

    ################################## TO DO ###################################
    select_columns = '"ID", "P_LDPNT_D2", "P_DSLPM_D2", "P_CANCR_D2", '
    select_columns += '"P_RESP_D2", "P_PTRAF_D2", "P_PWDIS_D2", '
    select_columns += '"P_PNPL_D2", "P_PRMP_D2", "P_PTSDF_D2", '
    select_columns += '"P_OZONE_D2", "P_PM25_D2"'

    sql = 'select {} from "EJSCREEN_2021_USPR" where DIV("ID", 10000000000) = {}'
    sql = sql.format(select_columns, lookup(state))

    # ej_state_df = cd_to_block(state, cd)
    ej_state_df = get_echo_data(sql)
    # Rename the ID field to match the field in the census data block group.
    ej_state_df.rename(columns={'ID': 'GEOID'}, inplace=True)
    ej_state_df['GEOID'] = ej_state_df['GEOID'].astype(int)

    ############################################################################

    # GET CENSUS
    conn = sqlite3.connect("EEW-EJScreen/census-shapefiles/census2010.db")

    bg_point_list = []
    for index, row in ej_state_df.iterrows():
        # Use row['GEOID'] to look for the block group in the census db.
        sql = 'select GEOID, INTPTLAT, INTPTLON from census_block_groups where GEOID=\'{}\''.format(
            row['GEOID'])
        c = conn.cursor()
        c.execute(sql)
        block_group = c.fetchone()
        bg_point_list.append(block_group)
    conn.close()

    # EJ Screen Records
    bg_points_df = pd.DataFrame(bg_point_list, columns=[
        'GEOID', 'INTPTLAT', 'INTPTLON'])
    bg_points_gdf = gpd.GeoDataFrame(bg_points_df, crs='epsg:4269',
                                     geometry=gpd.points_from_xy(bg_points_df.INTPTLON, bg_points_df.INTPTLAT))
    bg_points_gdf = bg_points_gdf.to_crs(4326)
    ### Exception -- sjoin() got an unexpected keyword argument 'predicate'
    # within_points = gpd.sjoin(bg_points_gdf, cd_boundary, predicate='within')
    within_points = gpd.sjoin(bg_points_gdf, cd_boundary)

    # PLOT
    ### The map isn't used.
    # for i in range(0, len(within_points)):
    #     folium.Marker(
    #         location=[within_points.iloc[i]['INTPTLAT'],
    #                   within_points.iloc[i]['INTPTLON']],
    #         popup=within_points.iloc[i]['GEOID'],
    #     ).add_to(map)
    #     map

    # FILTER
    ej_columns = ['GEOID', 'P_LDPNT_D2', 'P_DSLPM_D2', 'P_CANCR_D2', 'P_RESP_D2', 'P_PTRAF_D2', 'P_PWDIS_D2',
                  'P_PNPL_D2', 'P_PRMP_D2', 'P_PTSDF_D2', 'P_OZONE_D2', 'P_PM25_D2']

    ej_cd_df = within_points.merge(ej_state_df[ej_columns], on='GEOID')

    # STATISTICS
    columns = ['P_LDPNT_D2', 'P_DSLPM_D2', 'P_CANCR_D2', 'P_RESP_D2', 'P_PTRAF_D2', 'P_PWDIS_D2',
               'P_PNPL_D2', 'P_PRMP_D2', 'P_PTSDF_D2', 'P_OZONE_D2', 'P_PM25_D2']
    ej_cd_df[columns] = ej_cd_df[columns].apply(pd.to_numeric)
    ej_cd_scores = ej_cd_df[columns]
    means = pd.DataFrame(ej_cd_scores.mean())
    new_columns = ['Lead paint', 'Diesel', 'Air toxics cancer', 'Air toxics resp',
                   'Traffic', 'Water discharge', 'NPL sites', 'RMP facilities',
                   'TSDF facilities', 'Ozone', 'PM2.5']
    means = means.set_axis(new_columns, axis=0)

    stdev = pd.DataFrame(ej_cd_scores.std())
    stdev = stdev.set_axis(new_columns, axis=0)
    # Make the percentiles directory if it doesn't already exist.
    if not os.path.exists('percentiles'):
        os.makedirs('percentiles')
    ej_cd_scores.to_csv('percentiles/ejscreen-{}{}-percentiles.csv'.format(state, cd))

    df2 = pd.melt(ej_cd_scores)
    df2['value2'] = pd.to_numeric(df2['value'], errors='ignore')
    df2['bins'] = pd.cut(df2['value2'], bins=[0, 5, 10, 15, 20, 25,
                                              30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100])

    newdf = pd.DataFrame(columns=['metric', 'value', 'count'])
    for metric in columns:
        tempdf = df2[df2['variable'] == metric]
        for bin in tempdf['bins'].unique():
            try:
                midpoint = (bin.left + bin.right) / 2
                tempdf2 = tempdf[tempdf['bins'] == bin]
                count = 2 * tempdf2['value'].count()
                new_row = {'metric': metric,
                           'value': midpoint, 'count': float(count)}
                # breakpoint()
                # Use pd.concat to append the new_row to the newdf
                newdf = pd.concat([newdf, pd.DataFrame([new_row])])
                # newdf = newdf.append(new_row, ignore_index=True)
            except AttributeError:
                continue
    return newdf


def gen_score_safe(state, cd):
    """
    Generate a score for a given state and congressional district, with error handling.

    gen_score_safe will call the gen_score function and return a df with the scores if the generation worked,
    otherwise it will return an empty df. This function will also log the results of the generation to a file.

    Parameter state: 2 letter str representation of a state
    Paramter cd: str representing the congressional district

    Returns: a dataframe
    """

    try:
        newdf = gen_score(state, cd)
        log_generation(state, cd, "successful")
        print(f'Generation of {state}, {cd} successful')
        print("Created the following dataframe:")
        print(newdf)
        print("\n")
    except Exception as e:
        newdf = pd.DataFrame(columns=['metric', 'value', 'count'])
        log_generation(state, cd, "failed with exception: {}".format(e))
        print(f'Generation of {state}, {cd} failed with exception: {e}')
    return newdf


def clone_repo():
    """
    Clone the EEW-EJScreen repo and the EEW-EJScreen repo if it doesn't exist.
    """
    try:
        Repo.clone_from("https://github.com/edgi-govdata-archiving/ECHO_modules", "ECHO_modules")
    except:
        print("Failed to clone ECHO_modules repo")

    try:
        Repo.clone_from("https://github.com/edgi-govdata-archiving/EEW-EJScreen.git", "EEW-EJScreen")
    except:
        print("Failed to clone EEW-EJScreen repo")
