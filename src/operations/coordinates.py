# Functions to manipulate and convert coordinates of Instrument instances
# =======================================================================
from scipy.optimize import brentq
from numpy import cos, pi, rad2deg, sin, sqrt, tan
from src.data.data import instruments
from src.classes.classes import Instrument
from src.operations.count import countInstruments


def convertCoordinates() -> None:
    """
    **convertCoordinates** Wrapper for converting HK1980 grid coordinates (eastings & northings) to WGS 84 geographic coordinates (longitude & latitude) for each *Instrument* in the instruments dictionary.
    """
    # Initialise a count of instruments.
    instrument_count = 0
    num_instruments = countInstruments()
    for instrument in instruments.values():
        # Convert the coordinates of an instrument.
        hk1980ToWGS84(instrument)
        instrument_count += 1
        yield 'Converting coordinates...', 0, num_instruments, instrument_count


def swapCoordinates() -> None:
    """
    **swapCoordinates** Switch the easting and northing of instruments which appear to be inputted incorrectly on the FTP server. Incorrect readings are detected by the easting being greater than the northing.
    """
    # Initialise a count of instruments.
    instrument_count = 0
    num_instruments = countInstruments()
    for instrument in instruments.values():
        instrument_count += 1
        if None in [instrument.northing, instrument.easting]:
            continue
        # Detect incorrectly inputted coordinates by the easting being greater than the northing.
        if instrument.northing < instrument.easting:
            temp = instrument.northing
            instrument.northing = instrument.easting
            instrument.easting = temp
        yield 'Swapping disordered coordinates...', 0, num_instruments, instrument_count


def hk1980ToWGS84(instrument: Instrument) -> None:
    """
    **hk1980ToWGS84** Convert HK1980 grid coordinates (eastings & northings) to WGS 84 geographic coordinates (longitude & latitude) for an Instrument instance. The algorithm for conversion is sourced from Survey & Mapping Office (1995) Explanatory Notes on Geodetic Datums in Hong Kong, Hong Kong Government Lands Department, 2nd edition (2018).

    :param instrument: Instrument instance for converting coordinates.
    :type instrument: Instrument
    """
    if None in [instrument.easting, instrument.northing]:
        return
    northing_0 = 819069.8
    easting_0 = 836694.05
    longitude_0 = 1.99279173
    meridian_factor = 1.
    meridian_distance_0 = 2468395.728
    semimajor_axis = 6378388
    eccentricity = 0.006722670022
    meridian_distance = (instrument.northing - northing_0 + meridian_distance_0) / meridian_factor
    # Perform a numerical solution to find latitude_p.
    latitude_p = brentq(meridian, 0., 2. * pi, args=(meridian_distance, eccentricity, semimajor_axis))
    tan_p = tan(latitude_p)
    sec_p = 1. / cos(latitude_p)
    sin_p = sin(latitude_p)
    sin2_p = sin_p * sin_p
    radius_denominator = 1. - eccentricity * sin2_p
    sqr_radius_denominator = sqrt(radius_denominator)
    radius_vertical = semimajor_axis / sqr_radius_denominator
    radius_meridian = radius_vertical * (1. - eccentricity) / sqr_radius_denominator
    delta_easting = instrument.easting - easting_0
    dE_m0nu = delta_easting / (meridian_factor * radius_vertical)
    isometric_latitude = radius_vertical / radius_meridian
    instrument.latitude = rad2deg(latitude_p - 0.5 * tan_p * dE_m0nu * dE_m0nu * isometric_latitude) - 0.001527777778
    instrument.longitude = rad2deg(longitude_0 + sec_p * dE_m0nu - sec_p * dE_m0nu * dE_m0nu * dE_m0nu * (
                isometric_latitude + 2. * tan_p * tan_p) / 6.) + 0.002444444444


def meridian(latitude: float, meridian_distance: float, eccentricity: float, semimajor_axis: float) -> float:
    """
    **meridian** Return meridian value in Equation 3 of Survey & Mapping Office (1995) Explanatory Notes on Geodetic Datums in Hong Kong, Hong Kong Government Lands Department, 2nd edition (2018).

    :param latitude: Latitude.
    :type latitude: float
    :param meridian_distance: Meridian distance.
    :type meridian_distance: float
    :param eccentricity: Eccentricity.
    :type eccentricity: float
    :param semimajor_axis: Semi-major axis.
    :type semimajor_axis: float
    :return: float. Value of meridian.
    """
    # Evaluate Equation 3 of Survey & Mapping Office (1995) Explanatory Notes on Geodetic Datums in Hong Kong,
    # Hong Kong Government Lands Department, 2nd edition (2018).
    coeff_a0 = 1. - eccentricity * (0.25 + 0.046875 * eccentricity)
    coeff_a2 = 0.375 * eccentricity * (1. + 0.25 * eccentricity)
    coeff_a4 = 0.05859375 * eccentricity * eccentricity
    result = semimajor_axis * (
                coeff_a0 * latitude - coeff_a2 * sin(2. * latitude) + coeff_a4 * sin(4. * latitude)) - meridian_distance
    return result
