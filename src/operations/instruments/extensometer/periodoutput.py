# Functions for evaluating extensometer output
# ============================================
import logging
from numpy import abs, isnan, nan, nanmax, nanmin, where
from numpy import subtract
from src.operations.instruments.extensometer.typecodes import typeCodes
from src.operations.count import countInstruments
from src.data.data import instruments
from src.classes.classes import Output, Reading


def assignStrataElevations(num_instruments: int, elevation_tol: float = 2.) -> None:
    """
    **assignStrataElevations** Define *Elevation* instances to represent the upper and lower boundaries of each *Stratum* instance for each extensometer.

    :param num_instruments: Number of extensometers in the instruments dictionary.
    :type num_instruments: int
    :param elevation_tol: Distance in metres below the upper boundary of a stratum within which to find a spider to represent the upper boundary.
    :type elevation_tol: float
    """
    logger = logging.getLogger(__name__)
    # Initialise a count of extensometers.
    instrument_count = 0
    for instrument in instruments.values():
        # Skip the Instrument instance if it is not an extensometer.
        if instrument.type_name not in typeCodes():
            continue
        if len(instrument.strata) == 0:
            logger.warning(f'No strata defined for {instrument.name}')
            continue
        # Generate a list of spider elevations for the extensometer, replacing None with nan.
        elevations = [elevation.elevation if elevation is not None else nan for elevation in instrument.elevations]
        # Skip the Instrument instance if no spider elevations are stored.
        if not elevations:
            continue
        # Generate a list of upper elevations for each stratum, replacing None with nan.
        strata_upper_elevations = [stratum.upper_elevation_value if stratum.upper_elevation_value is not None else nan
                                   for stratum in instrument.strata]
        # Evaluate a table of differences between the spider elevations and the upper elevations of the strata.
        separations = subtract.outer(elevations, strata_upper_elevations)
        # Find the spider closest to the upper boundary of each stratum within a region extending upwards from a
        # distance elevation_tol below the upper boundary.
        cond_separations = abs(where(separations > -elevation_tol, separations, nan))
        try:
            min_separations = nanmin(cond_separations, axis=0)
        except Exception:
            logger.debug(f'instrument.name: {instrument.name}')
            logger.debug(f'separations: {separations}')
            logger.debug(f'elevations: {elevations}')
        for sndex, stratum in enumerate(instrument.strata):
            # Skip the top Stratum instance, for which Elevation instances will be defined later.
            if sndex == 0:
                continue
            if stratum.upper_elevation_value is None:
                logger.info(f'No elevations defined for {stratum.name} strata in {instrument.name}')
                continue
            if not isnan(min_separations[sndex]):
                stratum.upper_elevation = instrument.elevations[
                    where(cond_separations[:, sndex] == min_separations[sndex])[0][0]]
                # Set the lower Elevation instance of the Stratum instance above as the upper Elevation instance of the
                # currently-referenced Stratum instance.
                instrument.strata[sndex - 1].lower_elevation = stratum.upper_elevation
            else:
                logger.debug(f'No spiders fall within valid range for {stratum.name} strata in {instrument.name}')
        # Assign the Elevation instance for the top spider to the upper boundary of the uppermost Stratum instance.
        max_elevation = nanmax(elevations)
        top_stratum = instrument.strata[0]
        if top_stratum.lower_elevation_value is not None:
            # Only if a spider lies within or above the uppermost stratum...
            if max_elevation > top_stratum.lower_elevation_value:
                top_stratum.upper_elevation = instrument.elevations[where(elevations == max_elevation)[0][0]]
        # Assign the Elevation instance for the bottom spider to the lower boundary of the lowermost Stratum instance.
        min_elevation = nanmin(elevations)
        bottom_stratum = instrument.strata[-1]
        if bottom_stratum.upper_elevation_value is not None:
            # Only if a spider lies within or below the lowermost stratum...
            if min_elevation < bottom_stratum.upper_elevation_value:
                bottom_stratum.lower_elevation = instrument.elevations[where(elevations == min_elevation)[0][0]]
        instrument_count += 1
        yield 'Assigning magnets for each strata...', 0, num_instruments, instrument_count
        
        
def findInstrumentOutput(num_instruments: int) -> None:
    """
    **findInstrumentOutput** Evaluate summary output for extensometers, essentially to populate the *outputs* attribute of each *Instrument* instance with *Output* instances with the name attributes ``'absolute_start'``, ``'absolute_end'`` and ``'difference'``.

    :param num_instruments: Number of extensometers in the instruments dictionary.
    :type num_instruments: int
    """
    logger = logging.getLogger(__name__)
    instrument_count = 0
    for instrument in instruments.values():
        # Skip the Instrument instance if it is not an extensometer.
        if instrument.type_name not in typeCodes():
            continue
        if len(instrument.strata) == 0:
            continue
        if instrument.install_date is None:
            logger.error(f'Unable to find installation date for {instrument.name}')
            continue
        for stratum in instrument.strata:
            if stratum.upper_elevation is None:
                logger.info(f'No valid upper spider found for {stratum.name} strata in {instrument.name}')
                continue
            # Evaluate the absolute displacement and extension at the end of the requested period.
            output = Output()
            output.name = 'absolute_end'
            output.stratum = stratum.name
            if stratum.upper_elevation.end_reading is not None:
                # Store displacement in the output_magnitude attribute.
                output.output_magnitude = stratum.upper_elevation.end_reading.value2
                # Store a reading instance purely to record the end date.
                output.end_reading = Reading()
                output.end_reading.date = stratum.upper_elevation.end_reading.date
                if stratum.lower_elevation is not None:
                    if stratum.lower_elevation.end_reading is not None:
                        if stratum.upper_elevation.end_reading.date == stratum.lower_elevation.end_reading.date:
                            # Store extension in the output_magnitude2 attribute.
                            output.output_magnitude2 = stratum.upper_elevation.end_reading.value2 - stratum.lower_elevation.end_reading.value2
                if stratum.upper_elevation.readings:
                    # Store a reading instance purely to record the start date as the initial reading date.
                    output.start_reading = Reading()
                    output.start_reading.date = stratum.upper_elevation.readings[0].date
            instrument.appendOutput(output=output)
            # Evaluate the absolute displacement and extension at the start of the requested period.
            output = Output()
            output.name = 'absolute_start'
            output.stratum = stratum.name
            if stratum.upper_elevation.start_reading is not None:
                # Store displacement in the output_magnitude attribute.
                output.output_magnitude = stratum.upper_elevation.start_reading.value2
                # Store a reading instance purely to record the end date.
                output.end_reading = Reading()
                output.end_reading.date = stratum.upper_elevation.start_reading.date
                if stratum.lower_elevation is not None:
                    if stratum.lower_elevation.start_reading is not None:
                        if stratum.upper_elevation.start_reading.date == stratum.lower_elevation.start_reading.date:
                            # Store extension in the output_magnitude2 attribute.
                            output.output_magnitude2 = stratum.upper_elevation.start_reading.value2 - stratum.lower_elevation.start_reading.value2
                if stratum.upper_elevation.readings:
                    # Store a reading instance purely to record the start date as the initial reading date.
                    output.start_reading = Reading()
                    output.start_reading.date = stratum.upper_elevation.readings[0].date
            instrument.appendOutput(output=output)
            # Evaluate the change in displacement and extension during the requested period.
            output = Output()
            output.name = 'difference'
            output.stratum = stratum.name
            if stratum.upper_elevation.end_reading is not None and stratum.upper_elevation.start_reading is not None:
                # Store displacement in the output_magnitude attribute.
                output.output_magnitude = stratum.upper_elevation.end_reading.value2 - stratum.upper_elevation.start_reading.value2
                # Store a reading instances purely to record the start and end dates.
                output.end_reading = Reading()
                output.end_reading.date = stratum.upper_elevation.end_reading.date
                output.start_reading = Reading()
                output.start_reading.date = stratum.upper_elevation.start_reading.date
                if stratum.lower_elevation is None:
                    logger.info(f'No valid lower spider found for {stratum.name} strata in {instrument.name}')
                    continue
                if stratum.lower_elevation.end_reading is not None and stratum.lower_elevation.start_reading is not None:
                    # Check if all the reading dates required for evaluating the difference in extension over the period
                    # are defined.
                    try:
                        reading_dates = [
                            stratum.upper_elevation.start_reading.date,
                            stratum.upper_elevation.end_reading.date,
                            stratum.lower_elevation.start_reading.date,
                            stratum.lower_elevation.end_reading.date
                        ]
                    except:
                        logger.info(f'Start or end readings missing for {stratum.name} strata in {instrument.name}')
                        continue
                    # Ensure that the reading dates in pairs to subtract are concurrent.
                    if reading_dates.count(reading_dates[0]) != reading_dates.count(reading_dates[2]) or \
                        reading_dates.count(reading_dates[1]) != reading_dates.count(reading_dates[3]):
                        logger.info(f'Readings for {stratum.name} strata in {instrument.name} differ between top '
                                    f'(start: {stratum.upper_elevation.start_reading.date}, '
                                    f'end: {stratum.upper_elevation.end_reading.date}) and bottom '
                                    f'(start: {stratum.lower_elevation.start_reading.date}, '
                                    f'end: {stratum.lower_elevation.end_reading.date})')
                        continue
                    # Store extension in the output_magnitude2 attribute.
                    output.output_magnitude2 = stratum.upper_elevation.end_reading.value2 - stratum.upper_elevation.start_reading.value2 - \
                                            (stratum.lower_elevation.end_reading.value2 - stratum.lower_elevation.start_reading.value2)
            instrument.appendOutput(output=output)
        instrument_count += 1
        yield 'Finding instruments output...', 0, num_instruments, instrument_count


def processData() -> None:
    """
    **processData** Wrapper for executing functions evaluating outputs for *Instrument* instances.
    """
    num_instruments = countInstruments(typeCodes=typeCodes())
    # Pass on the generator from the executed functions to the progress dialog.
    yield from assignStrataElevations(num_instruments=num_instruments)
    yield from findInstrumentOutput(num_instruments=num_instruments)