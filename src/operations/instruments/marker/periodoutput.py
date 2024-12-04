# Functions for evaluating marker output
# ======================================
import logging
from src.operations.instruments.marker.typecodes import typeCodes
from src.operations.count import countInstruments
from src.data.data import instruments
from src.classes.classes import Output


def findInstrumentOutput(num_instruments: int) -> None:
    """
    **findInstrumentOutput** Evaluate summary output for markers, essentially to populate the *outputs* attribute of each *Instrument* instance with *Output* instances with the name attributes ``'absolute_start'``, ``'absolute_end'`` and ``'difference'``.

    :param num_instruments: Number of markers in the instruments dictionary.
    :type num_instruments: int
    """
    logger = logging.getLogger(__name__)
    instrument_count = 0
    for key, instrument in instruments.items():
        # Skip the Instrument instance if it is not a marker.
        if instrument.type_name not in typeCodes():
            continue
        if instrument.elevations is None:
            logger.warning(f'Unable to find elevation instance for {key}')
            continue
        # Store the absolute settlement at the end of the requested period.
        output = Output()
        output.name = 'absolute_end'
        # If the data on the FTP server is correct, there should exist only a single Elevation instance for each marker.
        if instrument.elevations[-1].end_reading is not None:
            output.end_reading = instrument.elevations[-1].end_reading
            output.elevation = instrument.elevations[-1].elevation
            # Copy all values in the Reading instance to the corresponding output_magnitude attributes of the Output
            # instance.
            for value_suffix in ['', '2', '3']:
                try:
                    setattr(output, 'output_magnitude' + value_suffix,
                            getattr(instrument.elevations[-1].end_reading, 'value' + value_suffix))
                except:
                    pass
        instrument.appendOutput(output=output)
        # Store the absolute settlement at the start of the requested period.
        output = Output()
        output.name = 'absolute_start'
        if instrument.elevations[-1].start_reading is not None:
            output.end_reading = instrument.elevations[-1].start_reading
            output.elevation = instrument.elevations[-1].elevation
            # Copy all values in the Reading instance to the corresponding output_magnitude attributes of the Output
            # instance.
            for value_suffix in ['', '2', '3']:
                try:
                    setattr(output, 'output_magnitude' + value_suffix,
                            getattr(instrument.elevations[-1].start_reading, 'value' + value_suffix))
                except:
                    pass
        instrument.appendOutput(output=output)
        # Store the difference in settlement across the requested period.
        output = Output()
        output.name = 'difference'
        if instrument.elevations[-1].end_reading is not None and instrument.elevations[-1].start_reading is not None:
            output.end_reading = instrument.elevations[-1].end_reading
            output.start_reading = instrument.elevations[-1].start_reading
            # Copy all values in the Reading instance to the corresponding output_magnitude attributes of the Output
            # instance.
            for value_suffix in ['', '2', '3']:
                try:
                    setattr(output, 'output_magnitude' + value_suffix,
                            getattr(instrument.elevations[-1].end_reading, 'value' + value_suffix) -
                            getattr(instrument.elevations[-1].start_reading, 'value' + value_suffix))
                except:
                    pass
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