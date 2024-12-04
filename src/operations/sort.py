# Function for sorting readings
# =============================
from src.data.data import instruments


def sortReadings(num_elevations: int) -> None:
    """
    **sortReadings** Sort the list of *Reading* instances in each *Elevation* instance of each *Instrument* instance in the instruments dictionary by the date attribute of the *Reading* instance.

    :param num_elevations: Number of elevations in the instrument dictionary.
    :type num_elevations: int
    """
    elevation_count = 0
    for instrument in instruments.values():
        for elevation in instrument.elevations:
            elevation.readings.sort(key=lambda reading: reading.date)
            elevation_count += 1
            yield 'Sorting readings...', 0, num_elevations, elevation_count