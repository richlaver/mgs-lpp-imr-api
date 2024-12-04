# Functions for evaluating piezometer output
# ==========================================
import logging
from src.operations.instruments.piezometer.typecodes import typeCodes
from src.operations.count import countInstruments
from src.data.data import instruments
from src.classes.classes import Output


def findInstrumentOutput(num_instruments: int) -> None:
    """
    **findInstrumentOutput** Evaluate summary output for piezometers, essentially to populate the *outputs* attribute of each *Instrument* instance with *Output* instances with the name attributes ``'absolute_start'``, ``'absolute_end'`` and ``'difference'``.

    :param num_instruments: Number of piezometers in the instruments dictionary.
    :type num_instruments: int
    """
    logger = logging.getLogger(__name__)
    instrument_count = 0
    for key, instrument in instruments.items():
        # Skip the Instrument instance if it is not a piezometer.
        if instrument.type_name not in typeCodes():
            continue
        if instrument.elevations is None:
            logger.warning(f'Unable to find elevation instance for {key}')
            continue
        try:
            stratum_name = instrument.strata[0].name
        except Exception:
            stratum_name = None
        # Store the groundwater level at the end of the requested period.
        output = Output()
        output.name = 'absolute_end'
        output.stratum = stratum_name
        # If the data on the FTP server is correct, there should exist only a single Elevation instance for each
        # piezometer.
        if instrument.elevations[-1].end_reading is not None:
            output.end_reading = instrument.elevations[-1].end_reading
            output.elevation = instrument.elevations[-1].elevation
            output.output_magnitude = instrument.elevations[-1].end_reading.value
        instrument.appendOutput(output=output)
        # Store the groundwater level at the start of the requested period.
        output = Output()
        output.name = 'absolute_start'
        output.stratum = stratum_name
        if instrument.elevations[-1].start_reading is not None:
            output.end_reading = instrument.elevations[-1].start_reading
            output.elevation = instrument.elevations[-1].elevation
            output.output_magnitude = instrument.elevations[-1].start_reading.value
        instrument.appendOutput(output=output)
        # Store the change in groundwater level across the requested period.
        output = Output()
        output.name = 'difference'
        output.stratum = stratum_name
        if instrument.elevations[-1].end_reading is not None and instrument.elevations[-1].start_reading is not None:
            output.end_reading = instrument.elevations[-1].end_reading
            output.start_reading = instrument.elevations[-1].start_reading
            output.output_magnitude = instrument.elevations[-1].end_reading.value - instrument.elevations[-1].start_reading.value
        instrument.appendOutput(output=output)
        instrument_count += 1
        yield 'Finding instruments output...', 0, num_instruments, instrument_count


def processData() -> None:
    """
    **processData** Wrapper for executing functions evaluating outputs for *Instrument* instances.
    """
    num_instruments = countInstruments(typeCodes=typeCodes())
    # Pass on the generator from the executed functions to the progress dialog.
    yield from findInstrumentOutput(num_instruments=num_instruments)