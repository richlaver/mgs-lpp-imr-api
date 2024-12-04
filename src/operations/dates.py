# Function to find dates with valid readings for the requested period
# ===================================================================
from datetime import datetime, timedelta
import logging
from numpy import isnan
from src.data.data import instruments


def findOutputDates(gui_data: dict, num_elevations: int) -> None:
    """
    **findOutputDates** Find dates with valid readings at the start and end of the requested period.

    :param gui_data: Dictionary with data from the graphical user interface.
    :type gui_data: dict
    :param num_elevations: Number of Elevation instances in the instrument dictionary.
    :type num_elevations: int
    """
    # Initialise a count of Elevation instances.
    elevation_count = 0
    logger = logging.getLogger(__name__)
    enddate = datetime.strptime(gui_data['enddate'], '%d-%m-%Y %H:%M:%S')
    startdate = datetime.strptime(gui_data['startdate'], '%d-%m-%Y %H:%M:%S')
    ignoreperiod = timedelta(days=int(gui_data['ignoreperiod']))
    for instrument in instruments.values():
        for elevation in instrument.elevations:
            # Initialise index to commence search for start reading.
            endex = -1
            # Iterate through readings in reverse chronological order to find most recent dates first.
            for index, reading in enumerate(elevation.readings[::-1]):
                # The ignore attribute of the Reading class is reserved for future development.
                if reading.ignore:
                    continue
                if not isinstance(reading.date, datetime):
                    logger.error(
                        f'Unable to interpret {reading.date} as date at elevation {elevation.elevation} mPD for {instrument.name}')
                    continue
                if reading.date < enddate - ignoreperiod:
                    break
                if reading.date <= enddate:
                    for value_name in ['value', 'value2', 'value3', 'value4']:
                        if getattr(reading, value_name) is None:
                            continue
                        if isnan([getattr(reading, value_name)])[0]:
                            continue
                        # Label Reading instance as the Reading at the end of the requested period if any non-None value
                        # is stored in the Reading instance.
                        elevation.end_reading = reading
                        # Record the index corresponding to the Reading instance before the end reading. The search for
                        # the Reading at the start of the requested period will begin from this index.
                        endex = -index - 1
                        break
                    if elevation.end_reading is not None:
                        break
            # Search for Reading instance at the start of the requested period in reverse chronological order
            # starting from the Reading instance one earlier than the found Reading instance for the end of the
            # period.
            for jndex, reading in enumerate(elevation.readings[endex::-1]):
                # The ignore attribute of the Reading class is reserved for future development.
                if reading.ignore:
                    continue
                if not isinstance(reading.date, datetime):
                    logger.error(
                        f'Unable to interpret {reading.date} as date at elevation {elevation.elevation} mPD for {instrument.name}')
                    continue
                if reading.date < startdate - ignoreperiod:
                    break
                if reading.date <= startdate:
                    for value_name in ['value', 'value2', 'value3', 'value4']:
                        if getattr(reading, value_name) is None:
                            continue
                        if isnan([getattr(reading, value_name)])[0]:
                            continue
                        # Label Reading instance as the Reading at the start of the requested period if any non-None
                        # value is stored in the Reading instance.
                        elevation.start_reading = reading
                        break
                    if not elevation.start_reading is None:
                        break
            elevation_count += 1
            yield 'Finding readings on output dates...', 0, num_elevations, elevation_count