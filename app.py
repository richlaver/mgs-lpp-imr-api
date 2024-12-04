import streamlit as st
from urllib.parse import urlencode
import datetime
import inputs
import processes
import outputs
import datetime
import pandas as pd

def type_selected(selected_types):
    st.session_state.type_selected = bool(selected_types)

# Get API key
def get_api_key():
    st.session_state.api_key = inputs.apiKey(
        username=username,
        password=password
    )

if 'api_key' not in st.session_state:
    st.session_state.api_key = False

if 'type_selected' not in st.session_state:
    st.session_state.type_selected = False

if 'instruments' not in st.session_state:
    st.session_state.instruments = None

if 'plotdata_df' not in st.session_state:
    st.session_state.plotdata_df = None

if 'appendixf_df' not in st.session_state:
    st.session_state.appendixf_df = None

if 'appendixg_df' not in st.session_state:
    st.session_state.appendixg_df = None

st.title('Weekly Report Plotting')
st.subheader('Lantau Portfolio Project')

st.divider()
# Requires credentials for public release
st.subheader('Enter credentials')
username = st.text_input(label='Username')
password = st.text_input(
    label='Password',
    type='password'
)
st.button(
    label='Login',
    help='Get authentication token using entered credentials',
    type='primary',
    disabled=not(username) and not(password),
    on_click=get_api_key
)
st.divider()

# Report period is returned as a tuple comprising the start date and the end date as datetime values
report_period = st.date_input(
    label='Select a reporting period',
    help='Selected dates are inclusive i.e. 00:00 on the start date to 23:59 on the end date',
    value=[
        datetime.datetime.today() - datetime.timedelta(days=8),
        datetime.datetime.today() - datetime.timedelta(days=2)
    ],
    max_value=datetime.datetime.today(),
    format='DD/MM/YYYY'
)

# Buffer periods are returned as an integer number of days
buffer_start = st.number_input(
    label='Select a period (in days) prior to the start date to search for missing readings',
    help='Select the maximum number of days before the start date of the reporting period within which to search for readings',
    min_value=0,
    value=3,
    step=1,
    format='%d'
)

period_exceedances = st.checkbox(
    label='Find exceedances strictly within specified report period',
    help='Leave unchecked if you want to include exceedance of the first reading found before the specified start date',
    value=True
)

imc_maxdatediff = st.number_input(
    label='Select the longest period (in days) to compare IMC and Contractor readings',
    help='A longer period will yield more comparisons but with less accuracy',
    min_value=0,
    value=3,
    step=1,
    format='%d'
)

all_types = inputs.getInstrumentTypes(
    api_key=st.session_state.api_key
)
selected_types = []
selected_types = st.multiselect(
    label='Choose the instrument types you want to plot',
    help='Plotting will be easier if you try to select instruments which measure the same thing',
    options=all_types,
    default=None,
    placeholder='Choose some types',
    on_change=type_selected(selected_types)
)

available_subtypes_list = []
if selected_types:
    available_subtypes_dict = inputs.getInstrumentSubTypes(
        type_list=selected_types,        
        api_key=st.session_state.api_key
    )
    available_subtypes_list = [': '.join([instr_type, subtype]) for instr_type, subtypes in available_subtypes_dict.items() for subtype in subtypes]

selected_subtypes_list = st.multiselect(
    label='And sub-types too...',
    help='Select instrument types first',
    options=available_subtypes_list,
    default=available_subtypes_list,
    placeholder='Choose some sub-types',
    disabled=st.session_state.type_selected
)

imc_cc_selection = st.multiselect(
    label='Include IMC and contractor\'s instruments?',
    help='To compare differences in readings between the two, choose both',
    options=['IMC', 'Contractor'],
    default=['IMC', 'Contractor'],
    placeholder='Choose IMC, Contractor or both'
)

with st.expander(
    label='Advanced settings',
    expanded=False,
    icon=':material/settings:'
):
    inclinometer_types = st.multiselect(
        label='Inclinometer instrument types',
        help='Select instrument types which are inclinometers. We will attempt to plot inclinometer profiles.',
        options=all_types,
        default=[instr_type for instr_type in ['IS', 'IW'] if instr_type in all_types]
    )

get_data = st.button(
    label='Get data',
    help='Download instrument set-up and readings',
    type='primary',
    disabled=st.session_state.type_selected
)

if get_data:
    selected_subtypes_dict = {}
    for type_subtype in selected_subtypes_list:
        instr_type, subtype = type_subtype.split(': ')
        if instr_type in selected_subtypes_dict.keys():
            selected_subtypes_dict[instr_type] += [subtype]
        else:
            selected_subtypes_dict[instr_type] = [subtype]
    # Get instrument setup from API
    st.session_state.instruments = inputs.getInstrumentSetup(
        subtype_list=selected_subtypes_dict,
        imc_cc_selection=imc_cc_selection,
        api_key=st.session_state.api_key
    )

    # Get parent-child relationships from API
    st.session_state.instruments = inputs.getParentChildRelationships(
        instruments=st.session_state.instruments,
        api_key=st.session_state.api_key
    )

    # for instrument in st.session_state.instruments.values():
    #     st.write(instrument.id)
    #     st.write(instrument.parents)
    #     st.write(instrument.children)

    # Get IMC-Contractor pairing, if both instrument owners were selected
    st.session_state.instruments = inputs.identifyIMCPairing(
        instruments=st.session_state.instruments
    )

    # Get instrument readings from API
    st.session_state.instruments = inputs.getInstrumentReadings(
        instruments=st.session_state.instruments,
        report_period=report_period,
        buffer_start=buffer_start,
        api_key=st.session_state.api_key
    )

    # Get instrument review levels from API
    st.session_state.instruments = inputs.getInstrumentReviewLevels(
        instruments=st.session_state.instruments,
        api_key=st.session_state.api_key
    )

    # if list(set(selected_types) & set(inclinometer_types)):
    #     st.session_state.instruments = inputs.getCalibrationData(
    #         instruments=st.session_state.instruments,
    #         inclinometer_types=inclinometer_types,
            # api_key=st.session_state.api_key
    #     )
    #     # inclinometer_displacement_fields = {
    #     #     'A': 'child_cum_diff_a',
    #     #     'B': 'child_cum_diff_b'
    #     # }
    #     inclinometer_displacement_fields = {
    #         'A': 'child_cumulative_displacement_a',
    #         'B': 'child_cumulative_displacement_b'
    #     }
    #     st.session_state.instruments = processes.ab_to_ne(
    #         instruments=st.session_state.instruments,
    #         inclinometer_types=inclinometer_types,
    #         inclinometer_displacement_fields=inclinometer_displacement_fields
    #     )

    # Find the readings most exceeding the review levels
    st.session_state.instruments = processes.findMaxExceedance(
        instruments=st.session_state.instruments,
        report_period=report_period,
        period_exceedances=period_exceedances
    )

    # Find start and end readings, and the change between the two
    st.session_state.instruments = processes.findSummaryOutput(
        instruments=st.session_state.instruments,
        report_period=report_period
    )

    # Calculate differences in reading at period end between an IMC and Contractor pair
    st.session_state.instruments = processes.compareIMCWithContractor(
        instruments=st.session_state.instruments,
        report_period=report_period,
        imc_maxdatediff=imc_maxdatediff
    )

    # Map contractor 1202 sites ("A", "B", etc.) to IMR sites ("West of TCE", "TCE Station", "East of TCE")
    st.session_state.instruments = processes.map1202Sites(
        instruments=st.session_state.instruments
    )

    # if list(set(selected_types) & set(inclinometer_types)):
    #     st.session_state.instruments = processes.findInclinometerOutput(
    #         instruments=st.session_state.instruments,
    #         inclinometer_types=inclinometer_types,
    #         displacement_scale_factor=100 / 1000
    #     )

    # Construct dataframe from which to filter data for plotting and output tables
    st.session_state.plotdata_df = processes.collatePlotData(instruments=st.session_state.instruments)

    # Construct dataframe for Appendix F
    st.session_state.appendixf_df = processes.collateAppendixF(all_data=st.session_state.plotdata_df)

    # Construct dataframe for Appendix G
    st.session_state.appendixg_df = processes.collateAppendixG(
        all_data=st.session_state.plotdata_df
    )

if st.session_state.plotdata_df is not None:
    st.divider()
    st.subheader('Download CSV data')
    all_data_col, app_f_col, app_g_col = st.columns(3)
    with all_data_col:
        download_all_data = st.download_button(
            label='All data',
            help='Download all data, including start, end & change, IMC-Contractor comparison and review level status',
            type='secondary',
            data=st.session_state.plotdata_df.to_csv(path_or_buf=None, index=False),
            file_name='lpp_data_' + report_period[0].strftime('%Y%m%d') + '–' + report_period[1].strftime('%Y%m%d') + '.csv',
            mime='text/csv'
        )
    with app_f_col:
        download_appendix_f = st.download_button(
            label='Appendix F',
            help='Download details of exceedances',
            type='secondary',
            data=st.session_state.appendixf_df.to_csv(path_or_buf=None, index=False),
            file_name='lpp_appendixf_' + report_period[0].strftime('%Y%m%d') + '–' + report_period[1].strftime('%Y%m%d') + '.csv',
            mime='text/csv'
        )
    with app_g_col:
        download_appendix_g = st.download_button(
            label='Appendix G',
            help='Download comparison of Contractor and IMC readings',
            type='secondary',
            data=st.session_state.appendixg_df.to_csv(path_or_buf=None, index=False),
            file_name='lpp_appendixg_' + report_period[0].strftime('%Y%m%d') + '–' + report_period[1].strftime('%Y%m%d') + '.csv',
            mime='text/csv'
        )

    available_fieldnames = []
    # Get unique list of field names
    available_fieldnames = list(set().union(*[list(instrument.readings) for instrument in st.session_state.instruments.values() if instrument.readings is not None]))
    if 'Timestamp' in available_fieldnames:
        available_fieldnames.remove('Timestamp')

    if list(set(selected_types) & set(inclinometer_types)):
        st.divider()
        st.subheader('Plot vector data')

    st.divider()
    st.subheader('Plot scalar data')
    selected_fieldnames = st.multiselect(
        label='Choose fields to plot',
        help='Each selection will produce three plots: change over and values at start and end of reporting period',
        options=available_fieldnames,
        default=None,
        placeholder='Choose some fields'
    )
    hidden_instruments = st.multiselect(
        label='Choose instruments to hide',
        help='Selected instruments will be omitted from the plots',
        options=[instrument.id for instrument in st.session_state.instruments.values()],
        default=None,
        placeholder='Choose zero or more instruments'
    )

    plot_data = st.button(
        label='Plot data',
        help='Plot a change map and a map of values at end of reporting period for each selected field',
        type='primary'
    )
    
    if plot_data:
        # Convert eastings and northings to latitudes and longitudes
        st.session_state.plotdata_df = processes.hk1980_to_latlong(plotdata_df=st.session_state.plotdata_df)

        # Hardcode omission of markers with erroneous values
        st.session_state.plotdata_df = st.session_state.plotdata_df.loc[~st.session_state.plotdata_df['id'].isin(hidden_instruments)]

        # Assign colour scales to start, end and change values
        st.session_state.plotdata_df = outputs.assignColourScales(
            plotdata_df=st.session_state.plotdata_df,
            field_names=selected_fieldnames
        )

        st.write(st.session_state.plotdata_df)
        
        # Plot one chart for each field name
        for selected_fieldname in selected_fieldnames:
            outputs.plotChartTabs(
                plotdata_df=st.session_state.plotdata_df,
                field_name=selected_fieldname
            )
            st.write(st.session_state.plotdata_df.loc[st.session_state.plotdata_df['field_name'] == selected_fieldname])    