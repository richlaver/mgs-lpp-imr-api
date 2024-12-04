# Functions to count Instrument and Elevation instances in the instrument dictionary
# ==================================================================================
from src.data.data import instruments


def countInstruments(typeCodes: list = [], readingsInPeriod: bool = False) -> int:
    """
    **countInstruments** Count the number of *Instrument* instances in the instrument dictionary, with options to filter according to instrument type and whether the instrument has yielded readings within the requested period.

    :param typeCodes: Optional. Type codes of instruments to include in the count. If left blank, all instrument types will be counted.
    :type typeCodes: list
    :param readingsInPeriod: Optional. If True, only instruments with readings in the requested period will be counted. If left blank, instruments both with and without readings will be counted.
    :type readingsInPeriod: bool
    :return: int. Number of Instrument instances.
    """
    if not typeCodes:
        num_instruments = len(instruments)
        return num_instruments
    num_instruments = 0
    for instrument in instruments.values():
        if instrument.type_name in typeCodes:
            if readingsInPeriod:
                for elevation in instrument.elevations:
                    if elevation.end_reading is not None:
                        num_instruments += 1
                        break
            else:
                num_instruments += 1
    return num_instruments


def countElevations(typeCodes: list = []) -> int:
    """
    **countElevations** Count the number of *Elevation* instances in the instrument dictionary, with an option to filter according to instrument type.

    :param typeCodes: Optional. Type codes of instruments to include in the count. If left blank, all instrument types will be counted.
    :type typeCodes: list
    :return: int. Number of Elevation instances.
    """
    num_elevations = 0
    for instrument in instruments.values():
        if not typeCodes:
            num_elevations += len(instrument.elevations)
            continue
        if instrument.type_name in typeCodes:
            num_elevations += len(instrument.elevations)
    return num_elevations