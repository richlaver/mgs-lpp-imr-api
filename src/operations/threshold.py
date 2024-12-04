# Function identifying observations
# =================================
import os
from datetime import timedelta
from importlib import import_module
from pathlib import Path
from re import compile, search
from src.data.data import instruments


def defineObservations(gui_data: dict) -> None:
    """
    **defineObservations** Identify which *Output* instances of output attribute of the *Instrument* instances in the instrument dictionary are considered observations. Observations are defined by the output value exceeding the user-specified threshold. Currently, observations apply only to *Output* instances with the name 'difference', which represent changes across the requested period.

    :param gui_data: Dictionary containing data from the graphical user interface.
    :param gui_data: dict
    """
    # Generate a list of names for the value attributes in the Output class.
    magnitude_names = [
        'output_magnitude',
        'output_magnitude2',
        'output_magnitude3'
    ]
    # Generate a dictionary of thresholds for each instrument type. The thresholds are divided by seven to convert from
    # per week as inputted on the graphical user interface to per day.
    thresholds = {
        'marker': gui_data['smxthreshold'] / 7,
        'extensometer': gui_data['mpxthreshold'] / 7,
        'inclinometer': gui_data['incthreshold'] / 7,
        'piezometer': gui_data['vwpthreshold'] / 7
    }
    # Hidden files are prefixed and suffixed with '__'.
    hiddenfile_pattern = compile('__\S*__')
    # Generate a dictionary defining the mapping between instrument type codes and the full instrument type name. The
    # correspondence between the two is read from the typeCodes() functions specific to each instrument type in the operations.instruments module.
    typename_mapping = {}
    for typename in os.listdir(str(Path(__file__).parents[0].joinpath('instruments'))):
        if not os.path.isdir(str(Path(__file__).parents[0].joinpath('instruments', typename))):
            continue
        if bool(search(hiddenfile_pattern, typename)):
            continue
        module = import_module('src.operations.instruments.' + typename + '.typecodes')
        for typecode in module.typeCodes():
            typename_mapping[typecode] = typename
    # Initialise a count of instruments.
    instrument_count = 0
    for key, instrument in instruments.items():
        for output in instrument.outputs:
            # Observations are only identified for changes across the reporting period.
            if output.name == 'difference':
                if output.end_reading is not None and output.start_reading is not None:
                    for magnitude_name in magnitude_names:
                        magnitude_value = getattr(output, magnitude_name)
                        if magnitude_value is not None:
                            # Normalising the datetime subtraction result by a timedelta of a day expresses the result
                            # as a number of days.
                            rate = magnitude_value / ((output.end_reading.date - output.start_reading.date) / timedelta(days=1))
                            if abs(rate) >= thresholds[typename_mapping[instrument.type_name]]:
                                output.observation = True
        instrument_count += 1
        yield f'Searching for observations above specified thresholds...', 0, len(instruments), instrument_count