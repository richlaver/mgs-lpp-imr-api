# Functions for manipulating the MSWord template
# ==============================================
from pathlib import Path
from datetime import datetime
from docxtpl import DocxTemplate
from src.data.data import region_groups, triggers, instruments
from src.operations.count import countInstruments
import comtypes.client
import time


def outputFilepath(gui_data: dict) -> Path:
    """
    **outputFilepath** Generate a path name to the generated MSWord document. Data to construct the filename is taken from the dictionary of graphical user interface data. An example of the generated filename is '16HK12026 - WR056 Rev0'.

    :param gui_data: Dictionary containing data from the graphical user interface.
    :type gui_data: dict
    :return: Path. Filepath to the generated MSWord document.
    """
    # The report number is three digits and left-padded with zeros.
    reportnumber = '{:0>3d}'.format(gui_data['reportnumber'])
    # The revision number is at least one digit.
    reportrevision = '{:1d}'.format(gui_data['reportrevision'])
    reportref = '16HK12026 - ' + gui_data['reportprefix'] + reportnumber + ' Rev' + reportrevision
    return Path(gui_data['outputfolder']).joinpath(reportref + '.docx')


def pdfOutput(gui_data: dict) -> None:
    """
    **pdfOutput** Save the MSWord document in portable document format (PDF). This function is unable to execute due to an unknown error.

    :param gui_data: Dictionary containing data from the graphical user interface.
    :type gui_data: dict
    """
    wdFormatPDF = 17
    msWordObj = comtypes.client.CreateObject('Word.Application')
    msWordObj.Visible = True
    time.sleep(3)
    wordFilepath = outputFilepath(gui_data=gui_data)
    msWordDoc = msWordObj.Documents.Open(str(wordFilepath))
    msWordDoc.ExportAsFixedFormat(
        OutputFileName=str(wordFilepath).replace('.docx', '.pdf'),
        ExportFormat=wdFormatPDF
    )
    # msWordDoc.SaveAs(str(wordFilepath).replace('.docx', '.pdf'), FileFormat=wdFormatPDF)
    msWordDoc.Close()
    msWordDoc.Visible = False
    msWordDoc.Quit()


def fillTemplate(template_path: Path, gui_data: dict, plots_data: dict, images_path: Path) -> None:
    """
    **fillTemplate** Fill fields in the MSWord template and save the generated document.

    :param template_path: Filepath to the MSWord template.
    :type template_path: Path
    :param gui_data: Dictionary containing data from the graphical user interface.
    :type gui_data: dict
    :param plots_data: Dictionary containing data defining the content, format and collation of plots.
    :type plots_data: dict
    :param images_path: Directory path to the generated plots.
    :type images_path: Path
    """
    document = DocxTemplate(str(template_path))
    reportnumber = '{:0>3d}'.format(gui_data['reportnumber'])
    reportrevision = '{:1d}'.format(gui_data['reportrevision'])
    reportref = '16HK12026 - ' + gui_data['reportprefix'] + reportnumber + ' Rev' + reportrevision
    issuedate = (datetime.strptime(gui_data['issuedate'], '%d-%m-%Y %H:%M:%S')).strftime('%d %B %Y')
    startdate = (datetime.strptime(gui_data['startdate'], '%d-%m-%Y %H:%M:%S')).strftime('%d %B %Y')
    enddate = (datetime.strptime(gui_data['enddate'], '%d-%m-%Y %H:%M:%S')).strftime('%d %B %Y')
    # The context dictionary maps jinja fields in the MSWord template (keys of the dictionary) to Python variables
    # (values of the dictionary).
    context = {
        'reportrevision': reportrevision,
        'reportnumber': reportnumber,
        'reportref': reportref,
        'issuedate': issuedate,
        'startdate': startdate,
        'enddate': enddate
    }
    # Generate a list of output value names.
    magnitude_names = [
        'output_magnitude',
        'output_magnitude2',
        'output_magnitude3'
    ]
    # Generate a mapping for the number format of each instrument type.
    number_formats = {
                    'marker': '{:.0f}',
                    'extensometer': '{:.0f}',
                    'inclinometer': '{:.0f}',
                    'piezometer': '{:.1f}'
    }
    # Generate a mapping for the multiplier to apply to the value for each instrument type. For markers and
    # extensometers, the vertical displacement value is negated to yield settlement.
    multipliers = {
        'marker': -1,
        'extensometer': -1,
        'inclinometer': 1,
        'piezometer': 1
    }
    # Generate a mapping that clarifies type code confusion, namely that SM1 markers should include SM1a markers as
    # well. This is used to count the numbers of active instruments for each type code.
    activeinstr_typecodes = {
        'MPX': ['MPX'],
        'VWP': ['VWP'],
        'SP': ['SP'],
        'SM1': ['SM1', 'SM1a'],
        'SM2': ['SM2'],
        'SMS3': ['SMS3'],
        'SR': ['SR'],
        'SA': ['SA'],
        'INC': ['INC']
    }
    # Generate a mapping for units for each instrument type code. The units apply to changes in the value so that for
    # groundwater monitoring instruments, the unit is 'm' rather than 'mPD'.
    reading_units = {
        'INC': 'mm',
        'SA': 'mm',
        'MPX': 'mm',
        'OW': 'm',
        'VWP': 'm',
        'SP':'m',
        'SM1': 'mm',
        'SM1a': 'mm',
        'SM2': 'mm',
        'SMS2': 'mm',
        'SM4': 'mm',
        'SMF': 'mm',
        'SR': 'mm'
    }
    # Generate a mapping between instrument type codes and full instrument type names.
    instrument_types = {
        'INC': 'inclinometer',
        'SA': 'inclinometer',
        'MPX': 'extensometer',
        'OW': 'piezometer',
        'VWP': 'piezometer',
        'SP':'piezometer',
        'SM1': 'marker',
        'SM1a': 'marker',
        'SM2': 'marker',
        'SMS2': 'marker',
        'SM4': 'marker',
        'SMF': 'marker',
        'SR': 'marker'
    }
    yield 'Generating context table...', 0, 3, 0
    for region_group in region_groups['region_groups']:
        # Generate a three-character identifier for the region group name.
        group_ref = region_group['name'][0:2] + region_group['name'][-1]
        for region in region_group['regions']:
            # Generate a three-character identifier for the region name.
            region_ref = region['name'][0:2] + region['name'][-1]
            for instrument in region['instruments']:
                # Generate a three-character identifier for the instrument type.
                instrument_ref = {
                    'marker': 'sm2',
                    'extensometer': 'mpx',
                    'inclinometer': 'inc',
                    'piezometer': 'vwp'
                }[instrument['name']]
                # Generate a three-character identifier for the output type.
                for output in instrument['outputs']:
                    # Generate a three-character identifier for the output type.
                    output_ref = {
                        'absolute_start': 'abs',
                        'absolute_end': 'abe',
                        'difference': 'dif'
                    }[output['name']]
                    # Generate a three-character identifier for the stratum name.
                    stratum_ref = {
                        'fill': 'fil',
                        'marine deposit': 'mad',
                        'alluvium': 'alm',
                        None: 'xxx'
                    }[output['stratum']]
                    for magnitude_name in magnitude_names:
                        # Generate a three-character identifier for the output magnitude name.
                        magnitude_ref = {
                            'output_magnitude': 'ma1',
                            'output_magnitude2': 'ma2',
                            'output_magnitude3': 'ma3'
                        }[magnitude_name]
                        # Concatenate the identifiers to generate a root for appending further identifiers. This will
                        # constitute the variable name for the field in the MSWord template.
                        root_variablename = ''.join([
                            group_ref,
                            region_ref,
                            instrument_ref,
                            output_ref,
                            stratum_ref,
                            magnitude_ref
                        ])
                        if output[magnitude_name]['percentiles'] is not None:
                            for percentile in output[magnitude_name]['percentiles']:
                                # Generate a three-digit identifier for the percentile rank.
                                percentile_ref = '{:0>3d}'.format(percentile['rank'])
                                # Negate the percentile value to a settlement if necessary, and format as a string.
                                percentile_value = number_formats[instrument['name']].format(multipliers[instrument['name']] * percentile['value'])
                                variable_name = ''.join([root_variablename, percentile_ref])
                                context[variable_name] = percentile_value
                        if output[magnitude_name]['maximum'] is not None:
                            variable_name = ''.join([root_variablename, 'mxn'])
                            context[variable_name] = output[magnitude_name]['maximum']['name']
                        if output[magnitude_name]['minimum'] is not None:
                            variable_name = ''.join([root_variablename, 'mnn'])
                            context[variable_name] = output[magnitude_name]['minimum']['name']
    yield 'Generating context table...', 0, 3, 1
    # Update context dictionary with the numbers of active instruments. Active instruments are defined as those with at
    # least one Reading instance. This assumes that instruments with readings 'ignoreperiod' days before the start date
    # and end date of the requested period are active. Note that readings in the middle of the requested period may be
    # ignored since they may not have been downloaded from the FTP server. The limitation on downloaded data shortens
    # the run time.
    for suffix, typecodes in activeinstr_typecodes.items():
        context['num_active' + suffix] = '{:1d}'.format(countInstruments(typeCodes=typecodes, readingsInPeriod=True))
    for plot_data in plots_data['plots']:
        if plot_data['main_insertion'] is not None:
            # Insert the plots by replacing dummy figures in the template.
            document.replace_pic(
                embedded_file=plot_data['main_insertion'],
                dst_file=images_path.joinpath(plot_data['appendix_figure'] + '.png')
            )
    yield 'Generating context table...', 0, 3, 2
    # Formulate a sentence describing the trigger status of inclinometers.
    inctrigger_statements = ''
    for trigger_name, trigger_instruments in triggers.items():
        inclist_string = ', '.join([trigger_instrument.name for trigger_instrument in trigger_instruments])
        inclist_string = ' & '.join(inclist_string.rsplit(', ', 1))
        inctrigger_statements = '; '.join([inctrigger_statements, inclist_string + ' have exceeded the ' + trigger_name + ' level'])
    if len(inctrigger_statements) > 0:
        inctrigger_statements = ' and '.join(inctrigger_statements.rsplit('; ', 1))
        inctrigger_statements = inctrigger_statements.replace(';', ',')
        inctrigger_statements = 'At the end of this reporting period' + inctrigger_statements + '.'
    context['incExceedances'] = inctrigger_statements
    yield 'Generating context table...', 0, 3, 3
    # Initialise a count of observations.
    observation_count = 0
    # Initialise a list for populating the table of observations.
    observationtable_contents = []
    for key, instrument in instruments.items():
        for output in instrument.outputs:
            if output.observation:
                # Each field of the row_data dictionary corresponds to a column.
                row_data = {
                    'number': '{:1d}'.format(observation_count),
                    # The value in the 'name' field is the name followed by the tip name separated by a whitespace, if
                    # the instrument is a piezometer.
                    'name': ' '.join(key.split('::')),
                    'readings': number_formats[instrument_types[instrument.type_name]].format(
                        multipliers[instrument_types[instrument.type_name]] * output.output_magnitude
                    ) + ' ' + reading_units[instrument.type_name]
                }
                observationtable_contents.append(row_data)
                observation_count += 1
    context['observationtable_contents'] = observationtable_contents
    yield 'Generating context table...', 0, 10, 10
    # Apply the context dictionary to fill the fields in the template.
    yield 'Rendering MSWord template...', 0, 10, 1
    document.render(context=context)
    yield 'Rendering MSWord template...', 0, 10, 10
    yield 'Saving generated MSWord document...', 0, 10, 1
    document.save(str(outputFilepath(gui_data=gui_data)))
    yield 'Saving generated MSWord document...', 0, 10, 10