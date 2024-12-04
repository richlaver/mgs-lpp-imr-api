# Functions for evaluating inclinometer output
# ============================================
from numpy import arctan2, cos, deg2rad, isnan, rad2deg, sin
from numpy.linalg import norm
import logging
from src.operations.instruments.inclinometer.typecodes import typeCodes
from src.operations.count import countInstruments
from src.data.data import instruments
from src.classes.classes import Output


def transformReadings(num_instruments: int) -> None:
    """
    **transformReadings** Transform inclinometer readings from axes orthogonal to the seawall to Face A and Face B axes. Displacements are also replaced by deflections for consistent manipulation of the readings.

    :param num_instruments: Number of inclinometers in the instruments dictionary.
    :type num_instruments: int
    """
    logger = logging.getLogger(__name__)
    # Initialise a count of inclinometers.
    instrument_count = 0
    for instrument in instruments.values():
        # Skip the Instrument instance if it is not an inclinometer.
        if instrument.type_name not in typeCodes():
            continue
        if instrument.bearing_seawall is None:
            logger.error(f'Unable to find bearing data for {instrument.name}')
            continue
        bearing = deg2rad(instrument.bearing_seawall)
        for elevation in instrument.elevations:
            for reading in [elevation.start_reading, elevation.end_reading]:
                if reading is not None:
                    # reading.value is only populated for the initial reading, and is equal to the Face A deflection.
                    # reading.value2 is only populated for the initial reading, and is equal to the Face B deflection.
                    # reading.value3 is only populated for readings subsequent to the initial reading, and is equal to
                    # the displacement perpendicular to the seawall.
                    # reading.value4 is only populated for readings subsequent to the initial reading, and is equal to
                    # the displacement parallel to the seawall.
                    # Transformation between coordinate systems is only performed if readings orthogonal to the seawall
                    # are defined and readings in the Face A and Face B directions are not defined.
                    if all([
                        reading.value is None or isnan([reading.value])[0],
                        reading.value2 is None or isnan([reading.value2])[0],
                        reading.value3 is not None and not isnan([reading.value3])[0],
                        reading.value4 is not None and not isnan([reading.value4])[0]
                    ]):
                        sin_bearing = sin(bearing)
                        cos_bearing = cos(bearing)
                        # In addition to transformation, the initial deflection is added to the displacement so that the
                        # final value is a deflection.
                        reading.value = reading.value3 * sin_bearing + reading.value4 * cos_bearing + elevation.readings[0].value
                        reading.value2 = -reading.value3 * cos_bearing + reading.value4 * sin_bearing + elevation.readings[0].value2
                    # The following elif condition is in case of a mistake in the reading file stored on the FTP server,
                    # where the readings are stored as Face A and Face B displacements rather than orthogonal to the
                    # seawall.
                    elif all([
                        reading.value is not None and not isnan([reading.value])[0],
                        reading.value2 is not None and not isnan([reading.value2])[0]
                    ]):
                        # No transformation is required, only conversion from displacement to deflection.
                        reading.value = reading.value + elevation.readings[0].value
                        reading.value2 = reading.value2 + elevation.readings[0].value2
                    else:
                        logger.error(f'Found reading at {elevation.elevation} mPD for {instrument.name} on {reading.date} but unable to transform reading')
        instrument_count += 1
        yield 'Transforming instruments readings...', 0, num_instruments, instrument_count


def findInstrumentOutput(num_instruments: int) -> None:
    """
    **findInstrumentOutput** Evaluate summary output for inclinometers, essentially to populate the *outputs* attribute of each *Instrument* instance with *Output* instances with the name attributes ``'absolute_start'``, ``'absolute_end'`` and ``'difference'``.

    :param num_instruments: Number of inclinometers in the instruments dictionary.
    :type num_instruments: int
    """
    class MaxVector:
        """
        MaxVector
        =========
        ``class`` for storing data about the vector with the highest magnitude.

        ----

        **Attributes**

        *elevation :* *float or None*
            Elevation of the sensor exhibiting the vector.
        *magnitude :* *float*
            Magnitude of the vector.
        *vector :* *list[float, float] or None*
            List with the first element as the Face A displacement and the second element as the Face B displacement of
            the vector.
        """
        def __init__(self) -> None:
            self.elevation = None
            self.magnitude = 0.
            self.vector = None

    logger = logging.getLogger(__name__)
    # Initialise a count of inclinometers.
    instrument_count = 0
    for instrument in instruments.values():
        # Skip the Instrument instance if it is not an inclinometer.
        if instrument.type_name not in typeCodes():
            continue
        if instrument.bearing_north is None:
            continue
        if instrument.install_date is None:
            logger.error(f'Unable to find installation date for {instrument.name}')
            continue
        # Initialise a dictionary for recording MaxVector instances for each output name.
        max_vectors = {
            'absolute_end': MaxVector(),
            'absolute_start': MaxVector(),
            'difference': MaxVector()
        }
        for elevation in instrument.elevations:
            if elevation.end_reading is not None:
                # Evaluate the absolute displacement vector at the end of the requested period.
                vector_absoluteend = [elevation.end_reading.value - elevation.readings[0].value,
                          elevation.end_reading.value2 - elevation.readings[0].value2]
                magnitude = norm(vector_absoluteend, ord=2)
                # Update the vector recorded in the relevant MaxVector instance if the vector just evaluated is of a
                # greater magnitude.
                if magnitude > max_vectors['absolute_end'].magnitude:
                    for attr_name, variable in {'elevation': elevation, 'magnitude': magnitude, 'vector': vector_absoluteend}.items():
                        setattr(max_vectors['absolute_end'], attr_name, variable)
            if elevation.start_reading is not None:
                # Evaluate the absolute displacement vector at the start of the requested period.
                vector_absolutestart = [elevation.start_reading.value - elevation.readings[0].value,
                          elevation.start_reading.value2 - elevation.readings[0].value2]
                magnitude = norm(vector_absolutestart, ord=2)
                # Update the vector recorded in the relevant MaxVector instance if the vector just evaluated is of a
                # greater magnitude.
                if magnitude > max_vectors['absolute_start'].magnitude:
                    for attr_name, variable in {'elevation': elevation, 'magnitude': magnitude, 'vector': vector_absolutestart}.items():
                        setattr(max_vectors['absolute_start'], attr_name, variable)
            if elevation.end_reading is not None and elevation.start_reading is not None:
                # Evaluate the displacement vector between the start and the end of the requested period.
                vector_difference = [elevation.end_reading.value - elevation.start_reading.value,
                          elevation.end_reading.value2 - elevation.start_reading.value2]
                magnitude = norm(vector_difference, ord=2)
                # Update the vector recorded in the relevant MaxVector instance if the vector just evaluated is of a
                # greater magnitude.
                if magnitude > max_vectors['difference'].magnitude:
                    for attr_name, variable in {'elevation': elevation, 'magnitude': magnitude, 'vector': vector_difference}.items():
                        setattr(max_vectors['difference'], attr_name, variable)
        # Record an Output instance in the outputs attribute of the Instrument instance for each MaxVector instance that
        # corresponds to the output types 'absolute_end', 'absolute_start' and 'difference'.
        for output_type, max_vector in max_vectors.items():
            if max_vector.elevation is None:
                logger.info(f'Unable to find maximum vector for {instrument.name}')
                continue
            output = Output()
            output.name = output_type
            output.end_reading = {
                'absolute_end': max_vector.elevation.end_reading,
                'absolute_start': max_vector.elevation.start_reading,
                'difference': max_vector.elevation.end_reading
            }[output_type]
            output.start_reading = {
                'absolute_end': max_vector.elevation.readings[0],
                'absolute_start': max_vector.elevation.readings[0],
                'difference': max_vector.elevation.start_reading
            }[output_type]
            output.elevation = max_vector.elevation
            output.output_magnitude = max_vector.magnitude
            output.output_bearing = (rad2deg(arctan2(max_vector.vector[1], max_vector.vector[0])) + instrument.bearing_north) % 360
            instrument.appendOutput(output)
        instrument_count += 1
        yield 'Finding instruments output...', 0, num_instruments, instrument_count


def processData() -> None:
    """
    **processData** Wrapper for executing functions evaluating outputs for *Instrument* instances.
    """
    num_instruments = countInstruments(typeCodes=typeCodes())
    # Pass on the generator from the executed functions to the progress dialog.
    yield from transformReadings(num_instruments=num_instruments)
    yield from findInstrumentOutput(num_instruments=num_instruments)