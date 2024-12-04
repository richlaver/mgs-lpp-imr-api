import pydeck
import streamlit as st
import pandas as pd
import classes


def assignColourScales(plotdata_df: pd.DataFrame, field_names: list) -> pd.DataFrame:
    for summary_name in [
        'start',
        'end',
        'change',
        'max_in_period',
        'min_in_period'
    ]:
        # Initialise new columns to store RGBA values for each output summary type
        plotdata_df[summary_name + '_colour'] = [(None, None, None)] * len(plotdata_df)

        for field_name in field_names:
            # Isolate values unique to a plot
            plot_values = plotdata_df.loc[plotdata_df['field_name'] == field_name][summary_name + '_value']

            min_value = plot_values.min()
            max_value = plot_values.max()
            maxabs_value = max(abs(max_value), abs(min_value))
            if summary_name == 'change':
                # Apply divergent colour scale for changes
                get_colour = classes.MPLColorHelper(
                    cmap_name='PiYG',
                    start_val=-maxabs_value,
                    stop_val=maxabs_value
                )
            else:
                # Apply sequential colour scale for absolute values i.e. start and end readings
                get_colour = classes.MPLColorHelper(
                    cmap_name='OrRd' if abs(max_value) == maxabs_value else 'OrRd_r',
                    start_val=min_value,
                    stop_val=max_value
                )
            for index, value in plot_values.dropna().items():
                # The get_rgb method returns RGBA values. We only want RGB.
                # Also, RGB is on a scale of 0 to 1. We want 0 to 255 as an integer.
                plotdata_df.at[index, summary_name + '_colour'] = tuple([int(colour_value * 255 + 0.5) for colour_value in get_colour.get_rgb(val=value)[0:3]])
                
    # Initialise new columns to store RGBA values for review level
    # plotdata_df['review_level_colour'] = [(None, None, None)] * len(plotdata_df)

    # for index, levels in plotdata_df[['lower_review_level', 'upper_review_level']]:
    #     review_level = [{
    #         'alert': 1,
    #         'alarm': 2,
    #         'action': 3
    #     }[level] if level != None else None for level in levels].max()
    #     st.write('review_level: ': review_level)

    return(plotdata_df)


def plotChartTabs(plotdata_df: pd.DataFrame, field_name: str):
    for index, tab in enumerate(st.tabs(['Start', 'End', 'Change', 'Max', 'Min'])):
        plotChart(
            plotdata_df=plotdata_df,
            field_name=field_name,
            tab=tab,
            tab_index=index
        )


def plotChart(plotdata_df: pd.DataFrame, field_name: str, tab, tab_index: int):
    with tab:
        st.subheader(field_name)
        st.caption([
            'Start of period',
            'End of period',
            'Change over period',
            'Maximum within period',
            'Minimum within period'
        ][tab_index])
        st.markdown(':arrow_up_small: ' + f"{plotdata_df.loc[plotdata_df['field_name'] == field_name][['start', 'end', 'change', 'max_in_period', 'min_in_period'][tab_index] + '_value'].max():.3f}" + '  ' 
                    + ':arrow_down_small: ' + f"{plotdata_df.loc[plotdata_df['field_name'] == field_name][['start', 'end', 'change', 'max_in_period', 'min_in_period'][tab_index] + '_value'].min():.3f}")
    
    tooltip_html = [
        "{id}<br>{field_name}: <b>{start_value}</b>",
        "{id}<br>{field_name}: <b>{end_value}</b>",
        "{id}<br>{field_name}: <b>{change_value}</b>",
        "{id}<br>{field_name}: <b>{max_in_period_value}</b>",
        "{id}<br>{field_name}: <b>{min_in_period_value}</b>"
    ][tab_index]
    
    tab.pydeck_chart(
        pydeck.Deck(
            map_style='light',
            initial_view_state=pydeck.ViewState(
                latitude=22.2981,
                longitude=113.9681,
                zoom=13,
                pitch=20
            ),
            tooltip = {
                "html": tooltip_html,
                "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
            },
            layers=[
                pydeck.Layer(
                    type='ScatterplotLayer',
                    data=plotdata_df.loc[plotdata_df['field_name'] == field_name].dropna(subset=[['start', 'end', 'change', 'max_in_period', 'min_in_period'][tab_index] + '_value']),
                    get_position='coordinates',
                    get_fill_color= ['start', 'end', 'change', 'max_in_period', 'min_in_period'][tab_index] + '_colour',
                    get_line_color=[0, 0, 0],
                    pickable=True,
                    opacity=0.8,
                    stroked=True,
                    filled=True,
                    get_radius=5
                )
            ]
        )
    )