# Functions for plotting figures
# ==============================
from plotly import figure_factory, graph_objects
from plotly.express import colors as plotly_colors
from numpy import count_nonzero, digitize, interp, deg2rad, cos, sin
import logging
import math
from pathlib import Path
from src.data.data import instruments


def plotMaps(plots_data: dict, basemap_geojson: dict, images_path: Path) -> None:
    """
    **plotMaps** Wrapper for executing the *_plotMap* function for each plot in the plots_data dictionary.

    :param plots_data: Dictionary containing data for each plot. The data defines the content, formatting and collation of the plots.
    :type plots_data: dict
    :param basemap_geojson: GeoJSON dictionary containing a FeatureCollection of the base map for each plot.
    :type basemap_geojson: dict
    :param images_path: Path to the directory where the images of the plots will be saved.
    :type images_path: Path
    """
    num_plots = len(plots_data['plots'])
    # Initialise a count of plots.
    plot_count = 0
    yield 'Generating plots...', 0, num_plots, plot_count
    for plot_data in plots_data['plots']:
        _plotMap(plot_data=plot_data, basemap_geojson=basemap_geojson, images_path=images_path)
        plot_count += 1
        yield 'Generating plots...', 0, num_plots, plot_count


def _plotMap(plot_data: dict, basemap_geojson: dict, images_path: Path) -> None:
    """
    **_plotMap** Plot the plot described by the entry of the plots_data dictionary inputted as the argument plot_data.

    :param plot_data: Dictionary containing data for the plot to be plotted. The data defines the content, formatting and collation of the plot.
    :type plot_data: dict
    :param basemap_geojson: GeoJSON dictionary containing a FeatureCollection of the base map for the plot.
    :type basemap_geojson: dict
    :param images_path: Path to the directory where the image of the plot will be saved.
    :type images_path: Path
    """
    logger = logging.getLogger(__name__)
    # Generate a dictionary of factors to multiply instrument values by. Vertical displacements for 'marker' and
    # 'extensometer' instrument types are negated to yield settlements.
    multipliers = {
        'marker': -1,
        'extensometer': -1,
        'inclinometer': 1,
        'piezometer': 1
    }
    # Generate a mapping of type codes to full instrument type names. The mapping differs from that defined by the
    # instrument-specific typeCodes() functions in the module operations.instruments in that markers 'SM1' and 'SMS3'
    # are included in addition to 'SM2'.
    typenames = {
        'SA': 'inclinometer',
        'INC': 'inclinometer',
        'MPX': 'extensometer',
        'VWP': 'piezometer',
        'SP': 'piezometer',
        'SM1': 'marker',
        'SM2': 'marker',
        'SMS3': 'marker'
    }
    # Initialise lists of coordinates, values and labels for plotting the markers.
    longitudes = []
    latitudes = []
    values = []
    bearings = []
    texts = []
    for instrument in instruments.values():
        # The 'type_codes' field comprises a list of type codes of instruments to include on the plot.
        if instrument.type_name not in plot_data['type_codes']:
            continue
        for output in instrument.outputs:
            # The 'output_name' and 'stratum' fields enable the desired Output instance to be identified for each
            # Instrument instance, from which the plotted value will be read.
            if output.name != plot_data['output_name']:
                continue
            if output.stratum != plot_data['stratum']:
                continue
            # The 'magnitude_name' field specifies which attribute of the Output instance to access to read the plotted
            # value e.g. 'output_magnitude2'.
            value = getattr(output, plot_data['magnitude_name'])
            if value is not None:
                # For markers and extensometers, convert vertical displacements to settlements.
                value *= multipliers[typenames[instrument.type_name]]
                longitudes.append(instrument.longitude)
                latitudes.append(instrument.latitude)
                # The elements in the texts list will be displayed as hover-over labels and will not appear in the
                # generated image file.
                texts.append(('Name: {name}<br>' +
                              'Value: {value:.1f}').format(name=instrument.name,
                                                       value=value))
                values.append(value)
                bearings.append(output.output_bearing)
            break
    if not values:
        logger.info(f'No values found when plotting {plot_data["plot_title"]}')
        return
    # Generate list defining the boundaries of bins with which to group markers according to their values. The lowermost
    # and uppermost boundaries are set as negative infinity and positive infinity respectively so that no values fall
    # outside the bin range.
    bins = [-math.inf, *plot_data['bins'], math.inf]
    # Generate a list of names for the bins. The Unicode character \u2013 represents an en-dash. The list is first
    # created for the bounded bins in the format '<lower bound> -- <upper bound>'.
    names = ['{0} \u2013 {1}'.format(lower_edge, upper_edge) for lower_edge, upper_edge in zip(bins[1:-2], bins[2:-1])]
    # Add the name of the lower unbounded bin to the list of bin names.
    names.insert(0, '< {}'.format(bins[1]))
    # Add the name of the upper unbounded bin to the list of bin names.
    names.append('> {}'.format(bins[-2]))
    # The numpy.digitize() function returns a list the same size as the values list, populated with indices indicating
    # the bin within which each value falls.
    bin_indices = digitize(x=values, bins=bins)
    # Define the minimum scale of the colour scale applied to fill the markers as the lowest bin index.
    cmin = 1
    # Define the middle of the colour scale as the bin index corresponding to a bin value of zero. This will be a
    # non-integer mulitple of 0.5 if zero is a boundary between two bins. This ensures that the diverging colour scale
    # plots symmetrically about zero.
    cmid = interp(x=0, xp=bins, fp=range(0, len(bins))) + 0.5
    # Define the maximum scale of the colour scale applied to fill the markers as the highest bin index.
    cmax = len(bins)
    # For a bubble plot, a diverging colour scale is defined (white at zero and extending in positive and negative
    # directions with different colours). In this case, it is desirable that the colour gradient is equal for both
    # positive and negative sides. The colour gradient is set by the side with the largest range, so that the most
    # intense colour is attained for the maximum value on that side.
    if plot_data['plot_type'] == 'bubble':
        if (cmax - cmid) > (cmid - cmin):
            cmin = 2 * cmid - cmax
        elif (cmax - cmid) < (cmid - cmin):
            cmax = 2 * cmid - cmin
    # The maximum value is required to scale marker or vector sizes to a readable scale.
    max_value = max(values)
    # The scale factor for bubble area follows the recommendation in the online guidance.
    area_sizeref = 2. * max_value / (40. ** 2)
    # The scale factor for vector length is derived by trial-and-error.
    vector_scale = 0.02 / max_value
    if plot_data['plot_type'] == 'bubble':
        figure = graph_objects.Figure()
        figure.add_trace(_baseMapScatterGeo(basemap_geojson=basemap_geojson))
        # Add a trace of markers for each bin.
        for bin_index in range(1, len(bins)):
            num_markers = count_nonzero(a=(bin_indices == bin_index))
            # The 'symbol_scaling' field specified as 'equal' defines all symbols as the same size.
            if plot_data['symbol_scaling'] == 'equal':
                sizes = [1.] * num_markers
            # The 'symbol_scaling' field specified as 'by_value' scales the symbols according to their absolute value.
            elif plot_data['symbol_scaling'] == 'by_value':
                sizes = [abs(value) for index, value in enumerate(values) if bin_indices[index] == bin_index]
            figure.add_trace(graph_objects.Scattergeo(
                lon=[value for index, value in enumerate(longitudes) if bin_indices[index] == bin_index],
                lat=[value for index, value in enumerate(latitudes) if bin_indices[index] == bin_index],
                text=[value for index, value in enumerate(texts) if bin_indices[index] == bin_index],
                marker={
                    'size': sizes,
                    # The Picnic colour scale ranges from dark blue through white to dark red.
                    'colorscale': plotly_colors.diverging.Picnic,
                    'color': [bin_index] * num_markers,
                    'cmin': cmin,
                    'cmax': cmax,
                    'cmid': cmid,
                    # The line colour is dark grey.
                    'line_color': 'rgb(40, 40, 40)',
                    'line_width': 0.5,
                    'sizemode': 'area',
                    'sizeref': area_sizeref,
                    # Some transparency assists visualisation of overlapping markers.
                    'opacity': 0.7
                },
                # Define the legend entry text.
                name=names[bin_index - 1]
            ))
        figure.update_geos(
            # Zoom the plot to the plotted entities.
            fitbounds='locations',
            # Hide the world map because the resolution is too coarse and the reclamation is missing.
            visible=False
        )
        figure.update_layout(
            # Prevent re-sizing of the plot after plotting to ensure the correct size in the image file.
            autosize=False,
            title_text=plot_data['plot_title'],
            showlegend=True,
            legend={
                # Ensure uniform symbol sizes in the legend.
                'itemsizing': 'constant',
                'xanchor': 'left',
                'x': 0.01,
                'yanchor': 'top',
                'y': 0.99
            },
            legend_title_text=plot_data['legend_title'],
            # The width attribute was determined by trial-and-error to produce the correct size in the image file.
            width=2000
        )
    elif plot_data['plot_type'] == 'vector':
        # Evaluate longitude and latitude components for each vector.
        longitude_components = cos(deg2rad(bearings)) * values
        latitude_components = sin(deg2rad(bearings)) * values
        figure = figure_factory.create_quiver(
            x=longitudes,
            y=latitudes,
            u=longitude_components,
            v=latitude_components,
            scaleratio=1,
            scale=vector_scale,
            # The vectors should be omitted from the legend.
            showlegend=False,
            name='vector',
            line={
                'color': 'steelblue'
            }
        )
        figure.add_trace(_baseMapScatter(basemap_geojson=basemap_geojson))
        # Swap the plotting order of the base map and the vectors so that the base map is in the background.
        quiver_trace, basemap_trace = figure.data
        figure.data = basemap_trace, quiver_trace
        # Add a trace of markers for each bin.
        for bin_index in range(1, len(bins)):
            num_markers = count_nonzero(a=(bin_indices == bin_index))
            figure.add_trace(graph_objects.Scatter(
                x=[value for index, value in enumerate(longitudes) if bin_indices[index] == bin_index],
                y=[value for index, value in enumerate(latitudes) if bin_indices[index] == bin_index],
                text=[value for index, value in enumerate(texts) if bin_indices[index] == bin_index],
                mode='markers',
                marker={
                    # All markers are the same size in a vector plot.
                    'size': [1.] * num_markers,
                    # The Jet colour scale advances through the rainbow from dark blue to dark red.
                    'colorscale': plotly_colors.sequential.Jet,
                    'color': [bin_index] * num_markers,
                    'cmin': cmin,
                    'cmax': cmax,
                    'cmid': cmid,
                    # The line colour is dark grey.
                    'line_color': 'rgb(40, 40, 40)',
                    'line_width': 0.5,
                    'sizemode': 'area',
                    'sizeref': area_sizeref,
                    # Some transparency assists visualisation of overlapping markers.
                    'opacity': 0.7
                },
                # Define the legend entry text.
                name=names[bin_index - 1],
                # Marker size is determined by trial-and-error.
                marker_size=12
            ))
        figure.update_layout(
            # Prevent re-sizing of the plot after plotting to ensure the correct size in the image file.
            autosize=False,
            title_text=plot_data['plot_title'],
            showlegend=True,
            legend={
                # Ensure uniform symbol sizes in the legend.
                'itemsizing': 'constant',
                'xanchor': 'left',
                'x': 0.01,
                'yanchor': 'top',
                'y': 0.99
            },
            legend_title_text=plot_data['legend_title'],
            paper_bgcolor='white',
            plot_bgcolor='white',
            # The width attribute was determined by trial-and-error to produce the correct size in the image file.
            width=2000
        )
        # Hide the axes and the corresponding tick marks and labels so that the plot appears more like a map.
        figure.update_xaxes(
            showgrid=False,
            showticklabels=False
        ),
        figure.update_yaxes(
            showgrid=False,
            showticklabels=False
        )
    figure.write_image(
        file=images_path.joinpath(plot_data['appendix_figure'] + '.png'),
        format='png',
        # The scale, width and height were determined by trial-and-error to ensure the correct size in the image file.
        scale=5,
        width = 4 * 297,
        height = 4 * 210
    )
    figure.update_layout(title_text='Figure ' + plot_data['appendix_figure'] + '   ' + plot_data['plot_title'])
    figure.write_image(
        file=images_path.joinpath(plot_data['appendix_figure'] + '.pdf'),
        format='pdf',
        # The width and height were determined by trial-and-error to ensure the correct size in the image file.
        width = 4 * 297,
        height = 4 * 210
    )


def _baseMapScatterGeo(basemap_geojson: dict) -> graph_objects.Scattergeo:
    """
    **baseMapScatterGeo** Return a *Scattergeo* instance rendering the basemap. The *Scattergeo* rendition of the basemap is required for bubble plots.

    :param basemap_geojson: GeoJSON dictionary defining a FeatureCollection for the basemap, comprising Polygons.
    :type basemap_geojson: dict
    :return: Scattergeo instance of the basemap.
    """
    longitudes = [point[0] for point in basemap_geojson['features'][0]['geometry']['coordinates'][0]]
    latitudes = [point[1] for point in basemap_geojson['features'][0]['geometry']['coordinates'][0]]
    return graph_objects.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        # Connect ends of Polygon trace to form a closed shape for filling.
        fill='toself',
        fillcolor='lavender',
        showlegend=False,
        opacity=0.5,
        mode='lines',
        line={
            # The white line will be invisible against the white background, but will generate a visible boundary with
            # adjoining Polygons.
            'color': 'white',
            'width': 1
        }
    )


def _baseMapScatter(basemap_geojson: dict) -> graph_objects.Scatter:
    """
    **baseMapScatter** Return a *Scatter* instance rendering the basemap. The *Scatter* rendition of the basemap is required for vector plots.

    :param basemap_geojson: GeoJSON dictionary defining a FeatureCollection for the basemap, comprising Polygons.
    :type basemap_geojson: dict
    :return: Scatter instance of the basemap.
    """
    longitudes = [point[0] for point in basemap_geojson['features'][0]['geometry']['coordinates'][0]]
    latitudes = [point[1] for point in basemap_geojson['features'][0]['geometry']['coordinates'][0]]
    return graph_objects.Scatter(
        x=longitudes,
        y=latitudes,
        # Connect ends of Polygon trace to form a closed shape for filling.
        fill='toself',
        fillcolor='lavender',
        showlegend=False,
        opacity=0.5,
        mode='lines',
        line={
            # The white line will be invisible against the white background, but will generate a visible boundary with
            # adjoining Polygons.
            'color': 'white',
            'width': 1
        }
    )