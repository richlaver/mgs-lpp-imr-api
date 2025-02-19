import pandas as pd
import streamlit as st
from contextlib import suppress
from hk1980 import HK80
import datetime
import numpy as np
import math

def map1202Sites(instruments: dict) -> dict:
    mapping1202sites = {
        'A': 'East of TCE',
        'B': 'East of TCE',
        'C': 'East of TCE',
        'D': 'East of TCE',
        'E': 'East of TCE',
        'F': 'East of TCE',
        'G': 'East of TCE',
        'H': 'TCE Station',
        'J': 'TCE Station',
        'K': 'West of TCE',
        'L': 'West of TCE',
        'M': 'West of TCE',
        'N': 'West of TCE',
        'O': 'West of TCE',
        'P': 'West of TCE'
    }
    for instrument in instruments.values():
        if instrument.contract == '1202':
            if instrument.site in mapping1202sites.keys():
                instrument.site = mapping1202sites[instrument.site]

    return(instruments)

def findSummaryOutput(instruments: dict, report_period: tuple) -> dict:
    status_container = st.status(
        label='Finding summary output...',
        expanded=False,
        state='running'
    )

    for instrument in instruments.values():
        if instrument.readings is not None:
            if not instrument.readings.drop(columns='Timestamp').isnull().all(axis=None):
                readings = instrument.readings.loc[~instrument.readings.drop(columns='Timestamp').isnull().all(axis=1)].reset_index(drop=True)
                if not readings.empty:
                    instrument.end_reading = readings.iloc[readings['Timestamp'].idxmax()]
                    if not readings.loc[readings['Timestamp'] <= pd.to_datetime(report_period[0] + datetime.timedelta(days=1))].empty:
                        instrument.start_reading = readings.iloc[readings['Timestamp'].loc[readings['Timestamp'] <= pd.to_datetime(report_period[0] + datetime.timedelta(days=1))].idxmax()]
                        instrument.change = instrument.end_reading - instrument.start_reading
                    if not readings.loc[(readings['Timestamp'] >= pd.to_datetime(report_period[0] + datetime.timedelta(days=1)))].empty:
                        instrument.max_in_period = readings.max(axis=0)
                        instrument.min_in_period = readings.min(axis=0)

    status_container.update(
        label='Found summary output!',
        state='complete',
        expanded=False
    )

    return(instruments)


def findInclinometerOutput(
        instruments: dict,
        inclinometer_types: list,
        displacement_scale_factor: float
):
    status_container = st.status(
        label='Building a tabular inclinometer summary for output...',
        expanded=False,
        state='running'
    )

    inclinometer_children = [instrument for instrument in instruments.values() if (instrument.type in inclinometer_types) & (instrument.parents is not None) & (instrument.readings is not None)]
    inc_plotdata_list = [[
        instrument.id,
        instrument.easting + displacement_scale_factor * instrument.start_reading['east_displacement'],
        instrument.northing + displacement_scale_factor * instrument.start_reading['north_displacement'],
        instrument.instrument_level,
        displacement_scale_factor * instrument.change['east_displacement'],
        displacement_scale_factor * instrument.change['north_displacement'],
        0,
        instrument.contract,
        instrument.site
    ] for instrument in inclinometer_children if (instrument.change is not None) & bool(list(set(['east_displacement', 'north_displacement']) & set(instrument.readings.columns)))]
    inc_plotdata_df = pd.DataFrame(
        data=inc_plotdata_list,
        columns=[
            'id',
            'x',
            'y',
            'z',
            'u',
            'v',
            'w',
            'contract',
            'site'
        ]
    )

    status_container.update(
        label='Built a tabular inclinometer summary!',
        state='complete',
        expanded=False
    )
    st.write(inc_plotdata_df)

    return(inc_plotdata_df)



def ab_to_ne(
        instruments: dict,
        inclinometer_types: list,
        inclinometer_displacement_fields: dict
    ) -> dict:

    status_container = st.status(
        label='Converting A and B to N and E inclinometer readings...',
        expanded=False,
        state='running'
    )

    inclinometer_instruments = [instrument for instrument in instruments.values() if instrument.type in inclinometer_types]
    for instrument in inclinometer_instruments:
        # Assume only one parent
        if (instrument.parents is not None) & (instrument.readings is not None):
            parent_instrument = instruments[instrument.parents[0]]
            if (parent_instrument.bearing is not None) & all([field_name in instrument.readings.columns for field_name in inclinometer_displacement_fields.values()]):
                cos_bearing = math.cos(math.radians(parent_instrument.bearing))
                sin_bearing = math.sin(math.radians(parent_instrument.bearing))
                instrument.readings['north_displacement'] = instrument.readings[inclinometer_displacement_fields['A']] * cos_bearing - instrument.readings[inclinometer_displacement_fields['B']] * sin_bearing
                instrument.readings['east_displacement'] = instrument.readings[inclinometer_displacement_fields['A']] * sin_bearing + instrument.readings[inclinometer_displacement_fields['B']] * cos_bearing

    status_container.update(
        label='Converted A and B to N and E inclinometer readings!',
        state='complete',
        expanded=False
    )

    return(instruments)    


def compareIMCWithContractor(
        instruments: dict,
        report_period: tuple,
        imc_maxdatediff: int
    ) -> dict:
    status_container = st.status(
        label='Comparing IMC and Contractor readings...',
        expanded=False,
        state='running'
    )

    for instrument in instruments.values():
        if instrument.is_imc or instrument.imc_id is None:
            continue
        if instrument.readings is not None and instruments[instrument.imc_id].readings is not None:
            # Constrain readings strictly within selected report period.
            readings = instrument.readings.loc[(instrument.readings['Timestamp'] >= pd.to_datetime(report_period[0])) & (instrument.readings['Timestamp'] <= pd.to_datetime(report_period[1] + datetime.timedelta(days=1)))]
            readings_imc = instruments[instrument.imc_id].readings.loc[(instruments[instrument.imc_id].readings['Timestamp'] >= pd.to_datetime(report_period[0])) & (instruments[instrument.imc_id].readings['Timestamp'] <= pd.to_datetime(report_period[1] + datetime.timedelta(days=1)))]
            
            if not readings.drop(columns='Timestamp').isnull().all(axis=None) and not readings_imc.drop(columns='Timestamp').isnull().all(axis=None):
                readings = readings.loc[~readings.drop(columns='Timestamp').isnull().all(axis=1)].reset_index(drop=True)
                readings_imc = readings_imc.loc[~readings_imc.drop(columns='Timestamp').isnull().all(axis=1)].reset_index(drop=True)

                # Find IMC-contractor readings pair with the minimum date separation.
                date_diffs = pd.DataFrame(abs(readings['Timestamp'].values - readings_imc['Timestamp'].values[:, None]))
                index_imc, index = date_diffs.stack().idxmin()

                if date_diffs.iloc[(index_imc, index)] / datetime.timedelta(days=1) <= imc_maxdatediff:
                    instrument.imc_compare_reading = readings.iloc[index]
                    instruments[instrument.imc_id].imc_compare_reading = readings_imc.iloc[index_imc]
                    instrument.end_imc_diff = readings.iloc[index] - readings_imc.iloc[index_imc]
                    instruments[instrument.imc_id].end_imc_diff = readings_imc.iloc[index_imc] - readings.iloc[index]

    status_container.update(
        label='Compared IMC and Contractor readings!',
        state='complete',
        expanded=False
    )

    return(instruments)


def findMaxExceedance(
        instruments: dict,
        report_period: tuple,
        period_exceedances: bool
    ) -> dict:
    status_container = st.status(
        label='Finding maximum exceedances...',
        expanded=False,
        state='running'
    )

    for instrument in instruments.values():
        if instrument.readings is None or instrument.review_levels is None:
            continue

        field_names = list(instrument.readings)
        if 'Timestamp' in field_names:
            field_names.remove('Timestamp')

        for field_name in field_names:
            if instrument.start_reading is not None:
                readings = instrument.readings.loc[instrument.readings['Timestamp'] >= {
                    False: instrument.start_reading['Timestamp'],
                    True: pd.to_datetime(report_period[0])
                }[period_exceedances]]
            else:
                readings = instrument.readings
            
            if field_name not in instrument.review_levels.keys():
                continue
            
            if readings[field_name].isnull().all():
                continue
            
            reviewlevel_dict = instrument.review_levels[field_name]
            instrument.maxexceedance = {}

            for review_direction, review_levels in reviewlevel_dict.items():
                exceeding_readings = readings

                match review_direction:
                    case 'upper':
                        instrument.maxexceedance.setdefault(field_name, {})[review_direction] = {
                            'maxabs_reading': exceeding_readings.iloc[exceeding_readings[field_name].idxmax()],
                            'level': None
                        }
                    case 'lower':
                        instrument.maxexceedance.setdefault(field_name, {})[review_direction] = {
                            'maxabs_reading': exceeding_readings.iloc[exceeding_readings[field_name].idxmin()],
                            'level': None
                        }

                for reviewlevel_name in ['alert', 'alarm', 'action']:
                    if reviewlevel_name in review_levels:
                        match review_direction:
                            case 'upper':
                                exceeding_readings = readings.loc[readings[field_name] >= review_levels[reviewlevel_name]].reset_index()
                            case 'lower':
                                exceeding_readings = readings.loc[readings[field_name] <= review_levels[reviewlevel_name]].reset_index()
                        if exceeding_readings.empty:
                            break
                        else:
                            match review_direction:
                                case 'upper':
                                    instrument.maxexceedance[field_name][review_direction]['maxabs_reading'] = exceeding_readings.iloc[exceeding_readings[field_name].idxmax()]
                                case 'lower':
                                    instrument.maxexceedance[field_name][review_direction]['maxabs_reading'] = exceeding_readings.iloc[exceeding_readings[field_name].idxmin()]
                            instrument.maxexceedance[field_name][review_direction]['level'] = reviewlevel_name

    status_container.update(
        label='Found maximum exceedances!',
        state='complete',
        expanded=False
    )
    
    return(instruments)        


def collatePlotData(instruments: dict) -> pd.DataFrame:
    status_container = st.status(
        label='Building a tabular summary for output...',
        expanded=False,
        state='running'
    )

    plotdata_list = [[
        instrument.id,
        field_name,
        instrument.easting,
        instrument.northing,
        instrument.date_installed,
        instrument.start_reading[field_name] if instrument.start_reading is not None else None,
        field_value,
        instrument.change[field_name] if instrument.change is not None else None,
        abs(instrument.change[field_name]) if instrument.change is not None else None,
        1/math.tan(math.radians(abs(instrument.change[field_name]))) if instrument.change is not None and instrument.change[field_name] != 0 and all(x in str(field_name).lower() for x in ['deg', 'change']) else None,
        1/abs(instrument.change[field_name]) if instrument.change is not None and instrument.change[field_name] != 0 and any(x in str(field_name).lower() for x in ['tilt', 'ratio', 'gradient']) and 'change' in str(field_name).lower() else None,
        instrument.max_in_period[field_name] if instrument.max_in_period is not None else None,
        instrument.min_in_period[field_name] if instrument.min_in_period is not None else None,
        instrument.max_in_period[field_name] - instrument.min_in_period[field_name] if instrument.max_in_period is not None and instrument.min_in_period is not None and instrument.max_in_period[field_name] is not None and instrument.min_in_period[field_name] is not None else None,
        instrument.start_reading['Timestamp'] if instrument.start_reading is not None else None,
        instrument.end_reading['Timestamp'],
        instrument.change['Timestamp'] if instrument.change is not None else None,
        instrument.is_imc,
        instrument.imc_id,
        instrument.imc_compare_reading[field_name] if instrument.end_imc_diff is not None else None,
        instrument.imc_compare_reading['Timestamp'] if instrument.end_imc_diff is not None else None,
        instrument.end_imc_diff[field_name] if instrument.end_imc_diff is not None else None,
        instrument.end_imc_diff['Timestamp'] if instrument.end_imc_diff is not None else None,
        instrument.maxexceedance[field_name]['lower']['level'] if instrument.maxexceedance is not None and field_name in instrument.maxexceedance.keys() and 'lower' in instrument.maxexceedance[field_name].keys() else None,
        instrument.maxexceedance[field_name]['lower']['maxabs_reading'][field_name] if instrument.maxexceedance is not None and field_name in instrument.maxexceedance.keys() and 'lower' in instrument.maxexceedance[field_name].keys() else None,
        instrument.maxexceedance[field_name]['lower']['maxabs_reading']['Timestamp'] if instrument.maxexceedance is not None and field_name in instrument.maxexceedance.keys() and 'lower' in instrument.maxexceedance[field_name].keys() else None,
        instrument.maxexceedance[field_name]['upper']['level'] if instrument.maxexceedance is not None and field_name in instrument.maxexceedance.keys() and 'upper' in instrument.maxexceedance[field_name].keys() else None,
        instrument.maxexceedance[field_name]['upper']['maxabs_reading'][field_name] if instrument.maxexceedance is not None and field_name in instrument.maxexceedance.keys() and 'upper' in instrument.maxexceedance[field_name].keys() else None,
        instrument.maxexceedance[field_name]['upper']['maxabs_reading']['Timestamp'] if instrument.maxexceedance is not None and field_name in instrument.maxexceedance.keys() and 'upper' in instrument.maxexceedance[field_name].keys() else None,
        instrument.review_levels[field_name]['lower']['alert'] if instrument.review_levels is not None and field_name in instrument.review_levels.keys() and 'lower' in instrument.review_levels[field_name].keys() else None,
        instrument.review_levels[field_name]['lower']['alarm'] if instrument.review_levels is not None and field_name in instrument.review_levels.keys() and 'lower' in instrument.review_levels[field_name].keys() else None,
        instrument.review_levels[field_name]['lower']['action'] if instrument.review_levels is not None and field_name in instrument.review_levels.keys() and 'lower' in instrument.review_levels[field_name].keys() else None,
        instrument.review_levels[field_name]['upper']['alert'] if instrument.review_levels is not None and field_name in instrument.review_levels.keys() and 'upper' in instrument.review_levels[field_name].keys() else None,
        instrument.review_levels[field_name]['upper']['alarm'] if instrument.review_levels is not None and field_name in instrument.review_levels.keys() and 'upper' in instrument.review_levels[field_name].keys() else None,
        instrument.review_levels[field_name]['upper']['action'] if instrument.review_levels is not None and field_name in instrument.review_levels.keys() and 'upper' in instrument.review_levels[field_name].keys() else None,
        instrument.contract,
        instrument.site,
        instrument.type,
        instrument.subtype
    ] for instrument in instruments.values() if instrument.end_reading is not None for field_name, field_value in instrument.end_reading.items() if field_name != 'Timestamp']
    plotdata_df = pd.DataFrame(
        data=plotdata_list,
        columns=[
            'id',
            'field_name',
            'easting',
            'northing',
            'installation_date',
            'start_value',
            'end_value',
            'change_value',
            'abs_change',
            'gradient_from_degrees',
            'gradient_from_ratio',
            'max_in_period_value',
            'min_in_period_value',
            'range_in_period',
            'start_date',
            'end_date',
            'change_period',
            'is_imc',
            'corresponding_imc_id',
            'imc_compare_reading',
            'imc_compare_date',
            'end_diff_with_imc',
            'date_diff_with_imc',
            'lower_review_level',
            'lower_max_exceedance_value',
            'lower_max_exceedance_date',
            'upper_review_level',
            'upper_max_exceedance_value',
            'upper_max_exceedance_date',
            'lower_alert',
            'lower_alarm',
            'lower_action',
            'upper_alert',
            'upper_alarm',
            'upper_action',
            'contract',
            'site',
            'type',
            'sub-type'
        ]
    )

    status_container.update(
        label='Built a tabular summary!',
        state='complete',
        expanded=False
    )

    return(plotdata_df)


def collateAppendixF(all_data: pd.DataFrame) -> pd.DataFrame:
    def most_onerous(row):
        if row['lower_review_level'] != None:
            return [row['lower_review_level'], row['lower_max_exceedance_value'], row['lower_max_exceedance_date']]
        elif row['upper_review_level'] != None:
            return [row['upper_review_level'], row['upper_max_exceedance_value'], row['upper_max_exceedance_date']]
        else:
            return [None, None, None]
    
    appendix_f = all_data.dropna(
        axis=0,
        how='all',
        subset=['lower_review_level', 'upper_review_level']
    )

    if not appendix_f.empty:
        appendix_f[['Exceeded Review Level', 'Reporting Period Value (Most Onerous)', 'Reporting Period Date (Most Onerous)']] = appendix_f.apply(most_onerous, axis=1, result_type='expand')
    else:
        appendix_f[['Exceeded Review Level', 'Reporting Period Value (Most Onerous)', 'Reporting Period Date (Most Onerous)']] = [None, None, None]
    
    appendix_f = appendix_f[[
        'contract',
        'site',
        'type',
        'id',
        'field_name',
        'Exceeded Review Level',
        'start_value',
        'end_value',
        'Reporting Period Value (Most Onerous)',
        'start_date',
        'end_date',
        'Reporting Period Date (Most Onerous)',
        'lower_alert',
        'lower_alarm',
        'lower_action',
        'upper_alert',
        'upper_alarm',
        'upper_action'
    ]].sort_values(
        by=['contract', 'site', 'type', 'field_name', 'Reporting Period Value (Most Onerous)'],
        ascending=[True, True, True, True, False]
    ).rename(columns={
        'contract': 'Contract',
        'site': 'Site',
        'type': 'Instrument Type',
        'id': 'Instrument ID',
        'field_name': 'Measurand',
        'start_value': 'Reporting Period Value (Beginning)',
        'end_value': 'Reporting Period Value (End)',
        'start_date': 'Reporting Period Date (Beginning)',
        'end_date': 'Reporting Period Date (End)',
        'lower_alert': 'Lower AAA (Alert)',
        'lower_alarm': 'Lower AAA (Alarm)',
        'lower_action': 'Lower AAA (Action)',
        'upper_alert': 'Upper AAA (Alert)',
        'upper_alarm': 'Upper AAA (Alarm)',
        'upper_action': 'Upper AAA (Action)'
    })
    appendix_f['Exceeded Review Level'] = appendix_f['Exceeded Review Level'].str.title()
    return appendix_f


def collateAppendixG(all_data: pd.DataFrame) -> pd.DataFrame:
    def imc_reading(row):
        imc_row = all_data.loc[(all_data['id'] == row['corresponding_imc_id']) & (all_data['field_name'] == row['field_name'])]
        if not imc_row.empty:
            return [imc_row['imc_compare_reading'].item(), imc_row['imc_compare_date'].item()]
        else:
            return [None, None]

    appendix_g = all_data.loc[~all_data['is_imc']].dropna(subset=['end_diff_with_imc'])
    if not appendix_g.empty:
        appendix_g[['Value (IMC)', 'Date (IMC)']] = appendix_g.apply(imc_reading, axis=1, result_type='expand')
    else:
        appendix_g[['Value (IMC)', 'Date (IMC)']] = [None, None]
    appendix_g = appendix_g[[
        'field_name',
        'contract',
        'site',
        'type',
        'id',
        'corresponding_imc_id',
        'imc_compare_reading',
        'Value (IMC)',
        'end_diff_with_imc',
        'imc_compare_date',
        'Date (IMC)',
        'date_diff_with_imc',
    ]].sort_values(
        by=['field_name', 'contract', 'site', 'type', 'end_diff_with_imc'],
        ascending=[True, True, True, True, False]
    ).rename(columns={
        'field_name': 'Measurand',
        'contract': 'Contract',
        'site': 'Site',
        'type': 'Instrument Type',
        'id': 'Instrument Name (Contractor)',
        'corresponding_imc_id': 'Instrument Name (IMC)',
        'imc_compare_value': 'Value (Contractor)',
        'end_diff_with_imc': 'Value (Difference)',
        'imc_compare_date': 'Date (Contractor)',
        'date_diff_with_imc': 'Date (Difference)'
    })

    return appendix_g


def hk1980_to_latlong(plotdata_df: pd.DataFrame) -> pd.DataFrame:
    plotdata_df['coordinates'] = [(None, None)] * len(plotdata_df)
    plotdata_df['longitude'] = None
    plotdata_df['latitude'] = None
    for index, row in plotdata_df.iterrows():
        coords = HK80(
            # The API seems to swap the eastings and northings
            northing=row['easting'],
            easting=row['northing']
        ).to_wgs84()
        plotdata_df.at[index, 'coordinates'] = (coords.longitude, coords.latitude)
        plotdata_df.at[index, 'longitude'] = coords.longitude
        plotdata_df.at[index, 'latitude'] = coords.latitude

    return(plotdata_df)