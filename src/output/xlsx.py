# Function to write Excel workbook with output
# ============================================
import os
from re import compile, search
from importlib import import_module
from pathlib import Path
from datetime import datetime
import logging
from xlsxwriter import Workbook
from numpy import unique, floating, issubdtype
from src.data.data import instruments, region_groups
from src.operations.count import countInstruments


def writeXlsxSurfer(surfer_path: Path, plots_data: dict) -> None:
    """
    **writeXlsxSurfer** Write an Excel workbook with the data used by the Surfer Scripter executable to create the Surfer plots. Each plot corresponds to a separate worksheet.

    :param surfer_path: Directory path to write the workbook.
    :type surfer_path: Path
    :param plots_data: Dictionary containing data for each plot. The data defines the content, formatting and collation of the plots.
    :type plots_data: dict
    """
    class PlotData:
        """
        **PlotData** Class containing the data defining the contents of each worksheet. Since each worksheet also corresponds to the Surfer plot, the data also describes the contents of the plot.

        Attributes
        ==========
        **appendix_figure :** *str* Reference for the figure as it is in the appendix; this is also the name of the worksheet e.g. *'E2'*.
        **plot_type :** *str* Type of the plot, either *'bubble'* or *'vector'*.
        **type_codes :** *List of str* Type codes of instruments included in the plot.
        **instrument_type :** *str or None* Name of instrument type e.g. *'extensometer'*.
        **output_name :** *str or None* Name of output type e.g. *'absolute_end'*.
        **magnitude_name :** *str or None* Name of output magnitude e.g. *'output_magnitude2'*.
        **stratum :** *str or None* Name of stratum e.g. *'marine deposit'*
        **instruments :** *List of str* Instances of **Instrument** included in the plot.
        **num_activeinstruments :** *float* Number of instruments with output that can be plotted in the plot.
        """

        def __init__(self) -> None:
            self.appendix_figure = None
            self.plot_type = None
            self.type_codes = []
            self.instrument_type = None
            self.output_name = None
            self.magnitude_name = None
            self.stratum = None
            self.instruments = []
            self.num_activeinstruments = 0

        def setInstruments(self) -> None:
            """
            **setInstruments** Set a list of instruments based upon the *instrument_type* attribute.
            """
            for instrument in instruments.values():
                if instrument.type_name not in self.type_codes:
                    continue
                self.instruments.append(instrument)
                # Count the number of instruments with output.
                for output in instrument.outputs:
                    if output.name != self.output_name:
                        continue
                    if output.stratum != self.stratum:
                        continue
                    if hasattr(output, self.magnitude_name):
                        symbol = getattr(output, self.magnitude_name)
                        if issubdtype(type(symbol), floating):
                            self.num_activeinstruments += 1

    # Initialise a list of PlotData instances, one for each worksheet or plot.
    plotDatas = []
    for plotDict in plots_data['plots']:
        plotData = PlotData()
        plotData.appendix_figure = plotDict['appendix_figure']
        plotData.plot_type = plotDict['plot_type']
        plotData.type_codes = plotDict['type_codes']
        plotData.output_name = plotDict['output_name']
        plotData.magnitude_name = plotDict['magnitude_name']
        plotData.stratum = plotDict['stratum']
        plotData.setInstruments()
        plotDatas.append(plotData)
    logger = logging.getLogger(__name__)
    workbook = Workbook(filename=str(surfer_path.joinpath('surfer-input.xlsx')))
    workbook.set_properties({
        'title': f'Input data for updating Surfer plots',
        'subject': 'Instrumentation and monitoring',
        'author': 'Rich Laver',
        'company': 'Golder WSP',
        'category': 'data',
        'keywords': f'3RS, I&M, data',
        'created': datetime.now()
    })
    base_format_dict = {
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True,
        'left': 1,
        'right': 1,
        'top': 1,
        'bottom': 1,
        'border_color': '#000000'
    }
    # Defining the number of columns as a variable makes it easy to add columns when revising the code.
    num_cols = 7
    # Count the total number of instruments in the plotDatas collection to formulate the yield statement.
    num_instruments = 0
    for plotData in plotDatas:
        num_instruments += plotData.num_activeinstruments
    # Initialise a count of instruments.
    instrument_count = 0
    for plotData in plotDatas:
        worksheet = workbook.add_worksheet(name=plotData.appendix_figure)
        # Initialise a list of lists with each element corresponding to the format of a cell on the worksheet.
        cell_formats = [[None for _col in range(num_cols)] for _row in range(1 + plotData.num_activeinstruments)]
        for col in range(num_cols):
            cell_formats[0][col] = workbook.add_format(base_format_dict)
            # Define a solid cell background.
            cell_formats[0][col].set_pattern(1)
        worksheet.set_column_pixels(first_col=0, last_col=0, width=120)
        worksheet.set_column_pixels(first_col=1, last_col=1, width=80)
        worksheet.set_column_pixels(first_col=2, last_col=2, width=80)
        worksheet.set_column_pixels(first_col=3, last_col=3, width=80)
        worksheet.set_column_pixels(first_col=4, last_col=4, width=80)
        worksheet.set_column_pixels(first_col=5, last_col=5, width=80)
        worksheet.set_column_pixels(first_col=6, last_col=6, width=170)
        cell_formats[0][0].set_bg_color('#DEDEDE')
        cell_formats[0][1].set_bg_color('#D8E9F1')
        cell_formats[0][2].set_bg_color('#D8E9F1')
        cell_formats[0][3].set_bg_color('#F9DCD2')
        cell_formats[0][4].set_bg_color('#F9DCD2')
        cell_formats[0][5].set_bg_color('#F9DCD2')
        cell_formats[0][6].set_bg_color('#F9DCD2')
        worksheet.write(0, 0, 'Label', cell_formats[0][0])
        worksheet.write(0, 1, 'x', cell_formats[0][1])
        worksheet.write(0, 2, 'y', cell_formats[0][2])
        worksheet.write(0, 3, 'Symbol', cell_formats[0][3])
        worksheet.write(0, 4, 'Angle', cell_formats[0][4])
        worksheet.write(0, 5, 'Size', cell_formats[0][5])
        worksheet.write(0, 6, 'Set:Index', cell_formats[0][6])
        # Initialise a count of rows
        row = 1
        for instrument in plotData.instruments:
            for output in instrument.outputs:
                if output.name != plotData.output_name:
                    continue
                if output.stratum != plotData.stratum:
                    continue
                # Only write instruments with output. If instruments without output are included in the worksheet, the
                # instruments without readings would disrupt correct symbol scaling in Surfer.
                if hasattr(output, plotData.magnitude_name):
                    symbol = getattr(output, plotData.magnitude_name)
                    # The issubdtype function recognises both numpy float d-types and floats.
                    if issubdtype(type(symbol), floating):
                        for col in range(num_cols):
                            cell_formats[row][col] = workbook.add_format(base_format_dict)
                        cell_formats[row][0].set_num_format("General")
                        cell_formats[row][1].set_num_format("0.00")
                        cell_formats[row][2].set_num_format("0.00")
                        cell_formats[row][3].set_num_format("0.0")
                        cell_formats[row][4].set_num_format("0.0")
                        cell_formats[row][5].set_num_format("0.0")
                        cell_formats[row][6].set_num_format("General")
                        if instrument.tip_name is None:
                            label = instrument.name
                        else:
                            label = ' '.join([instrument.name, instrument.tip_name])
                        worksheet.write(row, 0, label, cell_formats[row][0])
                        worksheet.write(row, 1, instrument.easting, cell_formats[row][1])
                        worksheet.write(row, 2, instrument.northing, cell_formats[row][2])
                        if any([type_code in [
                            'SM1',
                            'SM1a',
                            'SM2',
                            'SM4',
                            'SMF',
                            'SMS3',
                            'SR',
                            'MPX'
                        ] for type_code in plotData.type_codes]):
                            symbol = -symbol
                        if any([type_code in [
                            'SA',
                            'INC'
                        ] for type_code in plotData.type_codes]):
                            angle = output.output_bearing
                        else:
                            angle = ''
                        try:
                            worksheet.write(row, 3, symbol, cell_formats[row][3])
                        except:
                            worksheet.write(row, 3, '', cell_formats[row][3])
                        try:
                            worksheet.write(row, 4, angle, cell_formats[row][4])
                        except:
                            worksheet.write(row, 4, '', cell_formats[row][4])
                        try:
                            worksheet.write(row, 5, abs(symbol), cell_formats[row][5])
                        except:
                            worksheet.write(row, 5, '', cell_formats[row][5])
                        if any([type_code in [
                            'SA',
                            'INC'
                        ] for type_code in plotData.type_codes]):
                            # For an inclinometer, an arrow is plotted. This is Symbol 61 in the Symbol Properties menu of Surfer.
                            # The symbol number must be incremented by 32 to give the ASCII index.
                            worksheet.write(row, 6, 'GSI Default Symbols:93', cell_formats[row][6])
                        else:
                            # For instruments which are not inclinometers, a circle is plotted. This is Symbol 12 in the Symbol
                            # Properties menu of Surfer. The symbol number must be incremented by 32 to give the ASCII index.
                            worksheet.write(row, 6, 'GSI Default Symbols:44', cell_formats[row][6])
                        row += 1
                        instrument_count += 1
                        yield 'Writing Surfer input data...', 0, num_instruments, instrument_count
                break
        # Define cell borders.
        for _row in range(row):
            for _col in range(num_cols):
                if _col == 0:
                    cell_formats[_row][_col].set_left(2)
                if _col == num_cols - 1:
                    cell_formats[_row][_col].set_right(2)
                if _row == 0 or _row == 1:
                    cell_formats[_row][_col].set_top(2)
                if _row == row - 1 or _row == 0:
                    cell_formats[_row][_col].set_bottom(2)
        # Define a grey cell background for cells with missing data.
        worksheet.conditional_format(
            first_row=1,
            first_col=0,
            last_row=row - 1,
            last_col=num_cols - 1,
            options={
                'type': 'blanks',
                'format': workbook.add_format({'bg_color': '#F2F2F2'})
            }
        )
        worksheet.freeze_panes(1, 0)
    workbook.close()


def writeXlsxRegions(xlsx_path: Path, layout: dict) -> None:
    """
    **writeXlsxRegions** Write an Excel workbook with output data for each region in Group A. Output from each region is written on a separate worksheet.

    :param xlsx_path: Directory path to write workbook.
    :type xlsx_path: Path
    :param layout: Dictionary defining the layout of each worksheet.
    :type layout: dict
    """
    # Initialise list of regions in region group Group A.
    regions = []
    for region_group in region_groups['region_groups']:
        if region_group['name'] != 'Group A':
            continue
        regions = region_group['regions']
    if not regions:
        return
    # Flatten the region group dictionary into a structure:
    # {
    #    <str region name e.g. '3rd Runway and Taxiway'>: [
    #        {
    #            'instrument_name': <str instrument typename e.g. 'extensometer'>,
    #            'output_name': <str output type e.g. 'absolute end'>,
    #            'output_stratum': <str output stratum e.g. 'marine deposit'>,
    #            'magnitude_name': <str measurand e.g. 'displacement'>,
    #            'percentile_rank': <float percentile rank e.g. '75'>,
    #            'percentile_value': <str percentile value e.g. '-175.2 mm'>
    #        }, ...
    #    ], ...
    # }
    flat_regions = {}
    for region in regions:
        flat_percentiles = []
        for instrument in region['instruments']:
            for output in instrument['outputs']:
                for magnitude_name in [
                    'output_magnitude',
                    'output_magnitude2',
                    'output_magnitude3'
                ]:
                    if 'percentiles' in output[magnitude_name]:
                        if output[magnitude_name]['percentiles'] is not None:
                            for percentile in output[magnitude_name]['percentiles']:
                                flat_percentile = {
                                    'instrument_name': instrument['name'],
                                    'output_name': output['name'],
                                    'output_stratum': output['stratum'],
                                    'magnitude_name': {
                                        'absolute_end::extensometer::output_magnitude': 'displacement',
                                        'absolute_start::extensometer::output_magnitude': 'displacement',
                                        'difference::extensometer::output_magnitude': 'change in displacement',
                                        'absolute_end::extensometer::output_magnitude2': 'extension',
                                        'absolute_start::extensometer::output_magnitude2': 'extension',
                                        'difference::extensometer::output_magnitude2': 'change in extension',
                                        'absolute_end::extensometer::output_magnitude3': '',
                                        'absolute_start::extensometer::output_magnitude3': '',
                                        'difference::extensometer::output_magnitude3': '',
                                        'absolute_end::inclinometer::output_magnitude': 'deflection magnitude',
                                        'absolute_start::inclinometer::output_magnitude': 'deflection magnitude',
                                        'difference::inclinometer::output_magnitude': 'displacement magnitude',
                                        'absolute_end::inclinometer::output_magnitude2': '',
                                        'absolute_start::inclinometer::output_magnitude2': '',
                                        'difference::inclinometer::output_magnitude2': '',
                                        'absolute_end::inclinometer::output_magnitude3': '',
                                        'absolute_start::inclinometer::output_magnitude3': '',
                                        'difference::inclinometer::output_magnitude3': '',
                                        'absolute_end::marker::output_magnitude': 'heave',
                                        'absolute_start::marker::output_magnitude': 'heave',
                                        'difference::marker::output_magnitude': 'change in heave',
                                        'absolute_end::marker::output_magnitude2': '',
                                        'absolute_start::marker::output_magnitude2': '',
                                        'difference::marker::output_magnitude2': '',
                                        'absolute_end::marker::output_magnitude3': '',
                                        'absolute_start::marker::output_magnitude3': '',
                                        'difference::marker::output_magnitude3': '',
                                        'absolute_end::piezometer::output_magnitude': 'groundwater level',
                                        'absolute_start::piezometer::output_magnitude': 'groundwater level',
                                        'difference::piezometer::output_magnitude': 'rise in groundwater level',
                                        'absolute_end::piezometer::output_magnitude2': '',
                                        'absolute_start::piezometer::output_magnitude2': '',
                                        'difference::piezometer::output_magnitude2': '',
                                        'absolute_end::piezometer::output_magnitude3': '',
                                        'absolute_start::piezometer::output_magnitude3': '',
                                        'difference::piezometer::output_magnitude3': ''
                                    }['::'.join([output['name'], instrument['name'], magnitude_name])],
                                    'percentile_rank': percentile['rank'],
                                    'percentile_value': '{:.1f}'.format(percentile['value']) + ' ' + {
                                        'absolute_end::extensometer': 'mm',
                                        'absolute_start::extensometer': 'mm',
                                        'difference::extensometer': 'mm',
                                        'absolute_end::inclinometer': 'mm',
                                        'absolute_start::inclinometer': 'mm',
                                        'difference::inclinometer': 'mm',
                                        'absolute_end::marker': 'mm',
                                        'absolute_start::marker': 'mm',
                                        'difference::marker': 'mm',
                                        'absolute_end::piezometer': 'mPD',
                                        'absolute_start::piezometer': 'mPD',
                                        'difference::piezometer': 'm',
                                    }['::'.join([output['name'], instrument['name']])]
                                }
                                flat_percentiles.append(flat_percentile)
        flat_regions[region['name']] = flat_percentiles
    num_percentiles = sum([len(percentiles) for percentiles in flat_regions.values()])
    if num_percentiles == 0:
        return
    logger = logging.getLogger(__name__)
    workbook = Workbook(filename=str(xlsx_path.joinpath('region-outputs.xlsx')))
    workbook.set_properties({
        'title': f'Region outputs',
        'subject': 'Instrumentation and monitoring',
        'author': 'Rich Laver',
        'company': 'Golder WSP',
        'category': 'data',
        'keywords': f'3RS, I&M, data',
        'created': datetime.now()
    })
    base_format_dict = {
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True,
        'left': 1,
        'right': 1,
        'top': 1,
        'bottom': 1,
        'border_color': '#000000'
    }
    # Initialise a count of percentiles.
    percentile_count = 0
    for region_name, flat_percentiles in flat_regions.items():
        worksheet = workbook.add_worksheet(name=region_name)
        # Initialise a list of lists with each element corresponding to the format of a cell on the worksheet.
        cell_formats = [[None for _col in layout] for _row in range(2 + len(flat_percentiles))]
        # Initialise a count of columns.
        col = 0
        # Iterate through each column.
        for header in layout:
            # The top two rows contain the header.
            for row in range(2):
                cell_formats[row][col] = workbook.add_format(base_format_dict)
                # Define a solid cell background.
                cell_formats[row][col].set_pattern(1)
                if 'format' in header:
                    cell_formats[row][col].set_num_format(str(header['format']))
                if 'colour' in header:
                    cell_formats[row][col].set_bg_color(str(header['colour']))
            if 'width' in header:
                worksheet.set_column_pixels(first_col=col, last_col=col, width=header['width'])
            if 'label' in header:
                worksheet.write(0, col, header['label'], cell_formats[0][col])
            if 'unit' in header:
                worksheet.write(1, col, header['unit'], cell_formats[1][col])
            row = 2
            for flat_percentile in flat_percentiles:
                try:
                    content = flat_percentile[header['attribute'][0][0]]
                except:
                    content = ''
                cell_formats[row][col] = workbook.add_format(base_format_dict)
                if 'format' in header:
                    cell_formats[row][col].set_num_format(str(header['format']))
                    try:
                        worksheet.write(row, col, content, cell_formats[row][col])
                    except Exception:
                        logger.exception(f'Encountered exception when writing {header["label"]} for {flat_percentile}')
                yield 'Writing region data in Excel format...', 0, num_percentiles, percentile_count
                percentile_count += 1
                row += 1
            col += 1
        # Define cell borders.
        for _row in range(row):
            for _col in range(col):
                if _col == 0:
                    cell_formats[_row][_col].set_left(2)
                if _col == col - 1:
                    cell_formats[_row][_col].set_right(2)
                if _row == 0 or _row == 2:
                    cell_formats[_row][_col].set_top(2)
                if _row == row - 1 or _row == 1:
                    cell_formats[_row][_col].set_bottom(2)
                if 0 < _row and _row < 2:
                    cell_formats[_row][_col].set_top(0)
                if _row < 1:
                    cell_formats[_row][_col].set_bottom(0)
        # Define a grey cell background for cells with missing data.
        worksheet.conditional_format(
            first_row=2,
            first_col=0,
            last_row=row - 1,
            last_col=col - 1,
            options={
                'type': 'blanks',
                'format': workbook.add_format({'bg_color': '#F2F2F2'})
            }
        )
        worksheet.freeze_panes(2, 0)
    workbook.close()


def writeXlsxInstruments(xlsx_path: Path, layout: dict) -> None:
    """
    **writeXlsxInstruments** Write an Excel workbook with output data for each instrument. Output from each instrument is written on a separate worksheet.

    :param xlsx_path: Directory path to write workbook.
    :type xlsx_path: Path
    :param layout: Dictionary defining the layout of each worksheet.
    :type layout: dict
    """
    num_instruments = countInstruments()
    if num_instruments == 0:
        return
    instrument_typecodes = unique([instrument.type_name for instrument in instruments.values()])
    # Skip writing the workbook if none of the instrument types are included in the layout dictionary.
    typecodes = (set(instrument_typecodes) & set(layout.keys()))
    if not typecodes:
        return
    logger = logging.getLogger(__name__)
    workbook = Workbook(filename=str(xlsx_path.joinpath('instrument-outputs.xlsx')))
    workbook.set_properties({
        'title': f'Instrument outputs',
        'subject': 'Instrumentation and monitoring',
        'author': 'Rich Laver',
        'company': 'Golder WSP',
        'category': 'data',
        'keywords': f'3RS, I&M, data',
        'created': datetime.now()
    })
    base_format_dict = {
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True,
        'left': 1,
        'right': 1,
        'top': 1,
        'bottom': 1,
        'border_color': '#000000'
    }
    # Initialise a count of instruments.
    instrument_count = 0
    for typecode in typecodes:
        worksheet = workbook.add_worksheet(name=typecode)
        num_typeinstruments = countInstruments(typeCodes=[typecode])
        # Initialise a list of lists with each element corresponding to the format of a cell on the worksheet.
        cell_formats = [[None for _col in layout[typecode]] for _row in range(2 + num_typeinstruments)]
        # Initialise a count of columns.
        col = 0
        # Iterate through each column.
        for header in layout[typecode]:
            # The top two rows contain the header.
            for row in range(2):
                cell_formats[row][col] = workbook.add_format(base_format_dict)
                # Define a solid cell background.
                cell_formats[row][col].set_pattern(1)
                if 'format' in header:
                    cell_formats[row][col].set_num_format(str(header['format']))
                if 'colour' in header:
                    cell_formats[row][col].set_bg_color(str(header['colour']))
            if 'width' in header:
                worksheet.set_column_pixels(first_col=col, last_col=col, width=header['width'])
            if 'label' in header:
                worksheet.write(0, col, header['label'], cell_formats[0][col])
            if 'unit' in header:
                worksheet.write(1, col, header['unit'], cell_formats[1][col])
            row = 2
            for key, instrument in instruments.items():
                if instrument.type_name != typecode:
                    continue
                # Initialise a top-level object as the Instrument instance.
                object = instrument
                # Iterate through the children of objects as defined in the attribute field in the layout dictionary.
                for attr in header['attribute']:
                    if type(attr[0]) == int:
                        # Access an element in an array, if the object is an array.
                        if attr[0] < len(object):
                            object = object[attr[0]]
                        else:
                            object = ''
                            break
                    elif type(attr[0]) == str:
                        # Access a field of a dictionary via a given key.
                        if hasattr(object, attr[0]):
                            # The second element of attr comprises a dictionary of child element attributes that must match
                            # if the child is an array. For instance, in the outputs array, an Output instance is typically
                            # found to match the name and stratum attributes of the Output instance.
                            if attr[1] is not None:
                                for element in getattr(object, attr[0]):
                                    # Initialise a flag which is True if the fields of an element satisfy all of the values
                                    # specified in the layout dictionary.
                                    get_element = True
                                    for element_attrname, element_attrvalue in attr[1].items():
                                        # Skip the element in the array if the element fails to possess any of the
                                        # attributes or their values as listed in the layout dictionary.
                                        if hasattr(element, element_attrname):
                                            if getattr(element, element_attrname) != element_attrvalue:
                                                get_element = False
                                                break
                                        else:
                                            get_element = False
                                            break
                                    if get_element:
                                        object = element
                                        break
                            # The second element of attr is None if the child is a single instance (not an array).
                            else:
                                object = getattr(object, attr[0])
                        else:
                            # Define an empty cell if the output defined in the layout dictionary is not found in the
                            # Instrument instance.
                            object = ''
                            break
                    else:
                        object = ''
                        break
                cell_formats[row][col] = workbook.add_format(base_format_dict)
                if 'format' in header:
                    cell_formats[row][col].set_num_format(str(header['format']))
                    try:
                        worksheet.write(row, col, object, cell_formats[row][col])
                    except Exception:
                        logger.exception(f'Encountered exception when writing {header["label"]} for {key}')
                yield 'Writing instrument data in Excel format...', 0, num_instruments, instrument_count
                instrument_count += 1
                row += 1
            col += 1
        # Define cell borders.
        for _row in range(row):
            for _col in range(col):
                if _col == 0:
                    cell_formats[_row][_col].set_left(2)
                if _col == col - 1:
                    cell_formats[_row][_col].set_right(2)
                if _row == 0 or _row == 2:
                    cell_formats[_row][_col].set_top(2)
                if _row == row - 1 or _row == 1:
                    cell_formats[_row][_col].set_bottom(2)
                if 0 < _row and _row < 2:
                    cell_formats[_row][_col].set_top(0)
                if _row < 1:
                    cell_formats[_row][_col].set_bottom(0)
        # Define a grey cell background for cells with missing data.
        worksheet.conditional_format(
            first_row=2,
            first_col=0,
            last_row=row - 1,
            last_col=col - 1,
            options={
                'type': 'blanks',
                'format': workbook.add_format({'bg_color': '#F2F2F2'})
            }
        )
        worksheet.freeze_panes(2, 0)
    workbook.close()
