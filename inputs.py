from classes import instrument
import pandas as pd
import json
import requests as rq
import streamlit as st
import datetime
import numpy as np
import re
from contextlib import suppress

def identifyIMCPairing(instruments: dict) -> dict:
    for instrument in instruments.values():
        # Identify IMC instruments from the suffix '_I'
        instrument.is_imc=instrument.id[-2:] == '_I'
        # Extract contract, site and short ID from the instrument ID
        id_components_0 = instrument.id.split('_')
        id_components_1 = id_components_0[0].split('/')
        try:
            instrument.contract = id_components_1[0]
            instrument.site = id_components_1[1]
            instrument.short_id = '/'.join(id_components_1[2:])
        except:
            pass

        # Try to find the instrument corresponding to the IMC-CC instrument pair, if it exists
        if instrument.is_imc:
            try:
                instrument.imc_id = instruments[id_components_0[0]].id
                instruments[id_components_0[0]].imc_id = instrument.id
            except:
                pass

    return(instruments)


@st.cache_data(show_spinner=False)
def readInstrumentSetupFromCSV(
        instruments: dict,
        filepath: str
    ) -> dict:
    """
    **readInstrumentSetupFromCSV** Reads instrument coordinates, trigger levels and correspondences between the contractor's and IMC's instruments

    :param filepath: File path to the csv containing the data in the following columns:
    1: Instrument ID <str>
    2: Easting <float>
    3: Northing <float>
    4: Field pertaining to review value <str>
    5: Review value aka trigger level value <float>
    6: Review name aka trigger level name i.e. alert, action or alarm <str>
    :type str:
    """
    setup_data = pd.read_csv(filepath)
    
    for instr_id in pd.unique(setup_data.instr_id):
        try:
            instrument = instruments[instr_id]
            st.write('instr_id: ', instr_id)

            instr_reviewlevels = setup_data.loc[(setup_data.instr_id == instr_id)].sort_values(
                by='review_value',
                axis=0,
                ascending=True
            ).drop_duplicates()
            st.write(instr_reviewlevels)

            if len(instr_reviewlevels) == 6:
                instrument.review_levels.lower.action,
                instrument.review_levels.lower.alarm,
                instrument.review_levels.lower.alert,
                instrument.review_levels.upper.alert,
                instrument.review_levels.upper.alarm,
                instrument.review_levels.upper.action = instr_reviewlevels['review_value']
            if len(instr_reviewlevels) == 3:
                if instr_reviewlevels.loc[instr_reviewlevels.review_name == 'Action'] > instr_reviewlevels.loc[instr_reviewlevels.review_name == 'Alert']:
                    instrument.review_levels.upper.alert,
                    instrument.review_levels.upper.alarm,
                    instrument.review_levels.upper.action = instr_reviewlevels['review_value']
                else:
                    instrument.review_levels.upper.action,
                    instrument.review_levels.upper.alarm,
                    instrument.review_levels.upper.alert = instr_reviewlevels['review_value']
        except:
            pass

    return instruments


@st.cache_data(show_spinner=False)
def apiKey(
    username: str,
    password: str
) -> str:
    url = 'http://lpp_api.maxwellgeosystems.com'
    login = rq.post('{}/login'.format(url), data={
        "username": username,
        "password": password
    })
    api_key = json.loads(login.text)['token']
    return api_key


@st.cache_data(show_spinner=False)
def getInstrumentTypes(
    api_key: str
) -> list:
    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}

    response = rq.get('{}/api/get_instrument_type'.format(url), headers=headers)
    type_list = json.loads(response.text)

    return type_list


@st.cache_data(show_spinner=False)
def getInstrumentSubTypes(
    type_list: list,
    api_key: str
) -> dict:
    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}

    response = rq.post('{}/api/get_instrument_sub_type'.format(url),
                       headers=headers,
                       data={'types': ','.join(type_list)})
    subtype_dict = json.loads(response.text)

    return subtype_dict


@st.cache_data(show_spinner=False)
def getInstrumentSetup(
        subtype_list: list,
        imc_cc_selection: list,
        api_key: str
    ) -> dict:
    status_container = st.status(
        label='Downloading set-up data...',
        expanded=False,
        state='running'
    )

    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}
    
    # Get dictionary and list of instruments
    response = rq.post('{}/api/get_instruments'.format(url),
                       headers=headers,
                       data={'types': json.dumps(subtype_list)})
    instr_dict = json.loads(response.text)
    instr_list = [instr for types in instr_dict.values()
                  for subtypes in types.values()
                  for instr in subtypes]
    
    # Filter instrument list by who it belongs to: IMC or Contractor
    if 'IMC' in imc_cc_selection and 'Contractor' not in imc_cc_selection:
        instr_list = [instr for instr in instr_list if instr[-2:] == '_I']
    elif 'Contractor' in imc_cc_selection and 'IMC' not in imc_cc_selection:
        instr_list = [instr for instr in instr_list if instr[-2:] != '_I']
    
    # Initialise a dictionary to store the instrument set-up data
    setup_dict = {}
    num_chunks = 1
    request_success = False
    while not request_success:
        for chunk in np.array_split(instr_list, num_chunks):
            response = rq.get('{}/api/get_instrument_setup'.format(url),
                            headers=headers,
                            params={'instruments': ','.join(chunk)})
            if response.status_code == 414:
                break
            else:
                setup_dict.update(json.loads(response.text))
        request_success = response.status_code != 414
        num_chunks += 1

    instruments = {}
    for name, setup_data in setup_dict.items():
        instruments[name] = instrument(id=name)
        with suppress(Exception):
            instruments[name].date_installed = datetime.datetime.strptime(setup_data['date_installed'], '%Y-%m-%d %H:%M:%S')
        with suppress(Exception):
            instruments[name].easting = float(setup_data['easting'])
        with suppress(Exception):
            instruments[name].ground_level = float(setup_data['ground_level'])
        with suppress(Exception):
            instruments[name].instrument_level = float(setup_data['instrument_level'])
        with suppress(Exception):
            instruments[name].location = setup_data['location']
        with suppress(Exception):
            instruments[name].northing = float(setup_data['northing'])
        with suppress(Exception):
            instruments[name].parent = setup_data['parent']
        with suppress(Exception):
            instruments[name].parent_gr_level = float(setup_data['parent_gr_level'])
        with suppress(Exception):
            instruments[name].sensor_depth = float(setup_data['sensor_depth'])
        with suppress(Exception):
            instruments[name].type = setup_data['type']
        with suppress(Exception):
            instruments[name].subtype = setup_data['subtype']
        with suppress(Exception):
            instruments[name].project = setup_data['project']
        with suppress(Exception):
            instruments[name].contract = setup_data['contract']
        with suppress(Exception):
            instruments[name].site = setup_data['site']
        with suppress(Exception):
            instruments[name].zone = setup_data['zone']

    status_container.update(
        label='Set-up data downloaded!',
        state='complete',
        expanded=False
    )

    return(instruments)


def getCalibrationData(
        instruments: dict,
        inclinometer_types: list,
        api_key: str
    ) -> dict:
    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}
    query = {'instruments': ','.join([instrument.id for instrument in instruments.values() if instrument.type in inclinometer_types])}

    response = rq.get(
        '{}/api/get_calib_data'.format(url),
        headers=headers,
        params=query
    )
    calib_data = json.loads(response.text)
    for id, instr_calib in calib_data.items():
        for revision in reversed(instr_calib):
            if 'bearing' in revision.keys():
                try:
                    instruments[id].bearing = float(revision['bearing'])
                except:
                    instruments[id].bearing = None
                continue

    return instruments


def getParentChildRelationships(
        instruments: dict,
        api_key: str
    ) -> dict:
    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}

    status_container = st.status(
        label='Reading parent-child relationships...',
        expanded=False,
        state='running'
    )
    
    # Initialise a dictionary to store parent-child relationships
    parentchild_dict = {}
    num_chunks = 1
    request_success = False
    while not request_success:
        for chunk in np.array_split([instrument for instrument in instruments], num_chunks):
            response = rq.get('{}/api/get_master'.format(url),
                            headers=headers,
                            params={'instruments': ','.join(chunk)})
            if response.status_code == 414:
                break
            else:
                parentchild_dict.update(json.loads(response.text))
        request_success = response.status_code != 414
        num_chunks += 1

    if parentchild_dict:
        for child, parents in parentchild_dict.items():
            instruments[child].parents = parents
            for parent in parents:
                if parent in instruments.keys():
                    if instruments[parent].children is None:
                        instruments[parent].children = [child]
                    else:
                        instruments[parent].children.append(child)

    status_container.update(
        label='Set-up data downloaded!',
        state='complete',
        expanded=False
    )

    return(instruments)


def getInstrumentReadings(
        instruments: dict,
        report_period: tuple,
        buffer_start: int,
        api_key: str
    ) -> dict:
    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}

    status_container = st.status(
        label='Downloading readings...',
        expanded=False,
        state='running'
    )
    
    start_date = (report_period[0] - datetime.timedelta(days=buffer_start)).strftime('%Y-%m-%d %H:%M:%S')
    end_date = (report_period[1] + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    response = rq.post('{}/api/get_instrument_data'.format(url),
                            headers=headers,
                            data={'instruments': ','.join([instrument.id for instrument in instruments.values()]),
                                'from_date': start_date,
                                'to_date': end_date
                            })
    readings_dict = json.loads(response.text)

    if isinstance(readings_dict, dict):
        for name, data_dict in readings_dict.items():
            if name == 'comment':
                continue
            dataframe_dict = {}
            for index, (timestamp, reading_data) in enumerate(data_dict.items()):
                dataframe_dict[index] = {'Timestamp': datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')}
                dataframe_dict[index].update(reading_data)
                for key, value in dataframe_dict[index].items():
                    if key != 'Timestamp':
                        try:
                            dataframe_dict[index][key] = float(value)
                        except:
                            dataframe_dict[index][key] = None
            data_df = pd.DataFrame.from_dict(dataframe_dict, 'index')
            try:
                instruments[name].readings = data_df
            except:
                pass

    status_container.update(
        label='Readings downloaded!',
        state='complete',
        expanded=False
    )

    return(instruments)


def getInstrumentReviewLevels(
        instruments: dict,
        api_key: str
    ) -> dict:
    url = 'http://lpp_api.maxwellgeosystems.com'
    headers = {'Authorization': "Bearer " + api_key}

    status_container = st.status(
        label='Downloading review levels...',
        expanded=False,
        state='running'
    )

    response = rq.post('{}/api/get_instrument_setup_review_settings'.format(url),
                                headers=headers,
                                data={'instruments': ','.join([instrument.id for instrument in instruments.values()])}
                            )
    reviewlevels_dict = json.loads(response.text)

    for instr_group in reviewlevels_dict:
        for instr_name in instr_group.values():
            for reviewfield_name, reviewfield_details in instr_name.items():
                if reviewfield_name in ['review_settings']:
                    continue
                for review_level in reviewfield_details.values():
                    for review_direction in review_level.values():
                        if review_direction['review_field_label'] is None:
                            continue
                        if instruments[review_direction['Instrument']].review_levels is None:
                            instruments[review_direction['Instrument']].review_levels = {}
                        try:
                            instruments[review_direction['Instrument']].review_levels.setdefault(review_direction['review_field_label'], {}).setdefault(review_direction['review_direction'].lower(), {})[review_direction['review_level_name'].lower()] = float(review_direction['review_value'])
                        except:
                            pass

    status_container.update(
        label='Review levels downloaded!',
        state='complete',
        expanded=False
    )

    return(instruments)