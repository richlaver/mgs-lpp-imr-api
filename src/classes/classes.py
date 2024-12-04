# Definition of classes
# =====================
from inspect import stack


class Output:
    """
    Output
    ======
    ``class`` storing summary output for each instrument, indicated by the name attribute.
    
    ----
    
    **Attributes:**

    **name :** *str*
        Takes one of three values depending upon the timing of the summary output:
            * ``'absolute_start'``  start of the reporting period
            * ``'absolute_end'``  end of the reporting period
            * ``'difference'``  change across the reporting period
    **stratum :** *str*
        Defined only for extensometers and piezometers, and can take one of three values:
            * ``'fill'``
            * ``'marine deposit'``
            * ``'alluvium'``
    **start_reading :** *Reading*
        Corresponds to start of output period:
            * name=``'absolute_start'``  ``instrument.readings[0]`` (corresponding to initial reading)
            * name=``'absolute_end'``  ``instrument.readings[0]`` (corresponding to initial reading)
            * name=``'difference'``  *Reading* instance at start of reporting period
    **end_reading :** *Reading*
        Corresponds to end of output period:
            * name=``'absolute_start'``  *Reading* instance at start of reporting period
            * name=``'absolute_end'``  *Reading* instance at end of reporting period
            * name=``'difference'``  *Reading* instance at end of reporting period
    **elevation :** *Elevation*
        For inclinometers and extensometers, this will correspond to the elevation with maximum displacement. For
        piezometers and markers, only a single *Elevation* instance is defined and this is taken here.
    **output_magnitude :** *float*
        Depends upon the instrument type :**
            * *inclinometers*  magnitude of vector with greatest 2-norm
            * *extensometers*  vertical displacement
            * *piezometers*  rise in groundwater level
            * *markers*  heave
    **output_magnitude2 :** *float*
        Defined only for extensometers, as the extension.
    **output_magnitude3 :**
        Reserved for future development.
    **output_bearing :** *float*
        Define only for inclinometers, as the bearing of the vector with greatest 2-norm.
    **observation :** *bool*
        ``True`` if output exceeds the threshold for classification as an observation.
    """
    def __init__(self) -> None:
        self.name = None
        self.stratum = None
        self.start_reading = None
        self.end_reading = None
        self.elevation = None
        self.output_magnitude = None
        self.output_magnitude2 = None
        self.output_magnitude3 = None
        self.output_bearing = None
        self.observation = False


class Reading:
    """
    Reading
    =======
    ``class`` storing data for a single reading.

    ----

    **Attributes:**

    **date :** *datetime*
        Date of reading.
    **value :** *float*
        Depends upon the instrument type:
            * *inclinometer*  Face A deflection (only for the initial reading)
            * *extensometer*  Elevation
            * *piezometer*  Groundwater level
            * *marker*  Vertical displacement
    **value2 :** *float*
        Only defined for inclinometers and extensometers:
            * *inclinometer*  Face B deflection (only for the initial reading)
            * *extensometer*  Vertical displacement
    **value3 :** *float*
        Only defined for inclinometers, as the displacement of the face perpendicular to the seawall (only for readings following the initial)
    **value4 :** *float*
        Only defined for inclinometers, as the displacement of the face parallel to the seawall (only for readings following the initial)
    """
    def __init__(self) -> None:
        self.date = None
        self.value = None
        self.value2 = None
        self.value3 = None
        self.value4 = None
        self.ignore = False


class Elevation:
    """
    Elevation
    =========
    ``class`` storing data for a single instrument sensor (for inclinometers and extensometers) or for the instrument
    (for markers and piezometers).
    
    ----
    
    **Attributes:**

     **elevation :** *float*
         Depends upon the instrument type:
            * *inclinometers*  elevation of the inclinometer reading
            * *extensometers*  elevation of the spider
            * *markers*  elevation of the marker
            * *piezometers*  elevation of the piezometer tip
     **name :** *str or float*
         Depends upon the instrument type:
            * *inclinometer*  elevation of the sensor as type *float*
            * *extensometer*  name of the spider as type *str*
            * *marker*  elevation of the marker as type *float*
            * *piezometer*  elevation of the piezometer tip as type *float*
     **readings :** *list of Reading*
        *Reading*\s taken at the sensor or instrument.
     **start_reading :** *Reading*
        *Reading* corresponding to start of reporting period at the sensor or instrument.
     **end_reading :** *Reading*
        *Reading* corresponding to end of reporting period at the sensor or instrument.
    """
    def __init__(self) -> None:
        self.elevation = None
        self.name = None
        self.readings = []
        self.start_reading = None
        self.end_reading = None

    def appendReading(self, reading: Reading) -> None:
        """
        **appendReading** Append *Reading* instance to list in *readings* attribute.

        :param reading: Reading instance to append.
        :type reading: Reading
        """
        self.readings.append(reading)


class Stratum:
    """
    Stratum
    =======
    ``class`` storing data specific to stratum. Only defined for extensometers and piezometers. For piezometers, only the
    *name* attribute is defined to record the stratum within which the tip is installed.
    
    ----
    
    **Attributes:**
    
    **upper_elevation_value :** *float*
        Elevation of stratum upper boundary.
    **lower_elevation_value :** *float*
        Elevation of stratum lower boundary.
    **upper_elevation :** *Elevation*
        *Elevation* instance representing sensor corresponding to stratum upper boundary.
    **lower_elevation :** *Elevation*
        *Elevation* instance representing sensor corresponding to stratum lower boundary.
    **name :** *str*
        Name of stratum, taking one of three values: ``'fill'``, ``'marine deposit'`` or ``'alluvium'``.
    **displacement :** *float*
        Displacement of sensor corresponding to stratum upper boundary.
    **extension :** *float*
        Extension between sensors corresponding to stratum upper and lower boundaries.
    """
    def __init__(self) -> None:
        self.upper_elevation_value = None
        self.lower_elevation_value = None
        self.upper_elevation = None
        self.lower_elevation = None
        self.name = None
        self.displacement = None
        self.extension = None


class Region:
    """
    Region
    ======
    ``class`` storing the regions an instrument lies within for a specific region group.

    ----

    **Attributes:**

    **group_name :** *str*
        Name of region group.
    **attr region_names :** *list*
        Names of regions within which the instrument lies.
    """
    def __init__(self) -> None:
        self.group_name = None
        self.region_names = []

    def appendRegionName(self, region_name: str) -> None:
        """
        **appendRegion** Append region name to list in *region_names* attribute.

        :param region_name: Region name to append.
        :type region_name: str
        """
        self.region_names.append(region_name)


class Instrument:
    """
    Instrument
    ==========
    ``class`` storing installation details and readings for an instrument.

    ----

    **Attributes:**

    **name :** *str*
        Name of instrument. If the instrument is a piezometer, the name excludes the name of the piezometer tip.
    **tip_name :** *str*
        Name of piezometer tip, if the instrument is a piezometer, e.g. ``'1M1'`` or ``'L2'``.
    **easting :** *float*
        Easting of the instrument, according to the Hong Kong 1980 grid coordinate system.
    **northing :** *float*
        Northing of the instrument, according to the Hong Kong 1980 grid coordinate system.
    **longitude :** *float*
        Longitude of the instrument, according to the WGS 84 geographic coordinate system.
    **latitude :** *float*
        Latitude of the instrument, according to the WGS 84 geographic coordinate system.
    **bearing_north :** *float*
        Defined only for inclinometers as the bearing of the positive Face A vector measured clockwise from true north.
        The positive Face B vector points |pi|/2 clockwise from the positive Face A vector when viewed from above.
    **bearing_seawall :** *float*
        Defined only for inclinometers as the bearing of vector parallel to the seawall measured clockwise from the Face
        A direction. The vector parallel to the seawall is defined as pointing |pi|/2 clockwise from the vector
        perpendicular to the seawall pointing seaward when viewed from above.
    **type_name :** *str*
        Code for instrument type, which typically forms a prefix in the instrument name. Instrument type names are
        defined as dictionary keys in ``resources/ftp/layoutinitial.json`` and ``resources/ftp/layoutmeasure.json``. The
        following type names are supported: ``'INC'``, ``'SA'``, ``'MPX'``, ``'VWP'``, ``'OW'``, ``'SP'``, ``'SM1'``,
        ``'SM1a'``, ``'SM2'``, ``'SMS3'``, ``'SM4'``, ``'SMF'`` and ``'SR'``.
    **install_date :** *datetime*
        Date of instrument installation.
    **elevations :** *list of Elevation*
        For a marker or piezometer, a single *Elevation* instance. For an inclinometer or extensometer, an *Elevation*
        instance for each sensor. The *Elevation* instances store reading data recorded at the respective elevation.
    **strata :** *List of Stratum*
        Populated only for extensometers and piezometers. For extensometers, a maximum of three *Stratum* instances are
        typically defined, with the name attributes as ``'fill'``, ``'marine deposit'`` and ``'alluvium'``. For
        piezometers, only one *Stratum* instance should be defined, typically with the name attribute as either
        ``'marine deposit'`` or ``'alluvium'``.
    **outputs :** *List of Output*
        *Output* instances, each with one of the three names ``'absolute_start'``, ``'absolute_end'`` and
        ``'difference'``. For each of these names, the output instance should contain summary data for the start of the
        reporting period, the end of the reporting period and the change across the reporting period respectively. For
        extensometers, multiple *Output* instances may be defined under each of these names according to each *Stratum* 
        instance stored in the strata attribute.
    **regions :** *List of Region*
        *Region* instances associated with the instrument.

    .. |pi|    unicode:: U+003C0 .. LOWERCASE PI SYMBOL
    """
    def __init__(self) -> None:
        self.name = None
        self.tip_name = None
        self.easting = None
        self.northing = None
        self.longitude = None
        self.latitude = None
        self.bearing_north = None
        self.bearing_seawall = None
        self.type_name = None
        self.install_date = None
        self.elevations = []
        self.strata = []
        self.outputs = []
        self.regions = []

    def appendElevation(self, elevation: Elevation) -> None:
        """
        **appendElevation** Append *Elevation* to list in *elevations* attribute.

        :param elevation: Elevation to append.
        :type elevation: Elevation
        """
        self.elevations.append(elevation)

    def appendStrata(self, stratum: Stratum) -> None:
        """
        **appendStrata** Append *Stratum* to list in *strata* attribute.

        :param stratum: Stratum to append.
        :type stratum: stratum
        """
        self.strata.append(stratum)

    def appendRegion(self, region: Region) -> None:
        """
        **appendRegion** Append *Region* to list in *regions* attribute.

        :param region: Region to append.
        :type region: Region
        """
        self.regions.append(region)

    def appendOutput(self, output: Output) -> None:
        """
        **appendOutput** Append *Output* to list in *outputs* attribute.

        :param output: Output to append.
        :type output: Output
        """
        self.outputs.append(output)


class InsertInstrument:
    """
    InsertInstrument
    ================
    ``class`` storing installation details and readings for an instrument or sensor in preparation for insertion into
    the SQLite database.

    ----

    **Attributes:**

    **name :** *str*
        Name of instrument. If the instrument is a piezometer, the name excludes the name of the piezometer tip.
    **name2 :** *str*
        Depends upon the instrument type:
            * *inclinometer*  Elevation of the sensor as type *float*
            * *extensometer*  Name of the sensor as type *str*, e.g. ``'MPX-C60-A'`` or ``'MPX-C60-B'``
            * *piezometer*  Name of piezometer tip as type *str*, e.g. ``'1M1'`` or ``'L2'``
            * *marker*  ``None``
    **easting :** *float*
        Easting of the instrument, according to the Hong Kong 1980 grid coordinate system.
    **northing :** *float*
        Northing of the instrument, according to the Hong Kong 1980 grid coordinate system.
    **bearing_north :** *float*
        Defined only for inclinometers as the bearing of the positive Face A vector measured clockwise from true north.
        The positive Face B vector points |pi|/2 clockwise from the positive Face A vector when viewed from above.
    **bearing_seawall :** *float*
        Defined only for inclinometers as the bearing of vector parallel to the seawall measured clockwise from the Face
        A direction. The vector parallel to the seawall is defined as pointing |pi|/2 clockwise from the vector
        perpendicular to the seawall pointing seaward when viewed from above.
    **type_name :** *str*
        Code for instrument type, which typically forms a prefix in the instrument name. Instrument type names are
        defined as dictionary keys in ``resources/ftp/layoutinitial.json`` and ``resources/ftp/layoutmeasure.json``. The
        following type names are supported: ``'INC'``, ``'SA'``, ``'MPX'``, ``'VWP'``, ``'OW'``, ``'SP'``, ``'SM1'``,
        ``'SM1a'``, ``'SM2'``, ``'SMS3'``, ``'SM4'``, ``'SMF'`` and ``'SR'``.
    **install_date :** *datetime*
        Date of instrument installation.

    .. |pi|    unicode:: U+003C0 .. LOWERCASE PI SYMBOL
    """
    def __init__(self) -> None:
        self.name = ''
        self.name2 = ''
        self.easting = None
        self.northing = None
        self.elevation = None
        self.bearing_north = None
        self.bearing_seawall = None
        self.type_name = None
        self.install_date = None

    def asDict(self) -> dict:
        """
        **asDict** Generate dictionary of class attributes

        :return: Dictionary of class attributes.
        """
        method_name = stack()[0][3]
        attr_names = [attr_name for attr_name in dir(self) if not attr_name.endswith('_') and attr_name != method_name]
        dictionary = {}
        for attr_name in attr_names:
            dictionary[attr_name] = getattr(self, attr_name)
        return dictionary


class InsertReading():
    """
    InsertReading
    =============
    ``class`` storing data for a single reading in preparation for insertion into the SQLite database.

    ----

    **Attributes:**

    **date :** *datetime*
        Date of reading.
    **elevation :** *float*
        Elevation of reading.
    **value :** *float*
        Depends upon the instrument type:
            * *inclinometer*  Face A deflection (only for the initial reading)
            * *extensometer*  Elevation
            * *piezometer*  Groundwater level
            * *marker*  Vertical displacement
    **value2 :** *float*
        Only defined for inclinometers and extensometers:
            * *inclinometer*  Face B deflection (only for the initial reading)
            * *extensometer*  Vertical displacement
    **value3 :** *float*
        Only defined for inclinometers, as the displacement of the face perpendicular to the seawall (only for readings following the initial)
    **value4 :** *float*
        Only defined for inclinometers, as the displacement of the face parallel to the seawall (only for readings following the initial)
    """
    def __init__(self) -> None:
        self.name = ''
        self.name2 = ''
        self.date = ''
        self.elevation = None
        self.value = None
        self.value2 = None
        self.value3 = None
        self.value4 = None

    def asDict(self) -> dict:
        """
        **asDict** Generate dictionary of class attributes

        :return: Dictionary of class attributes.
        """
        method_name = stack()[0][3]
        attr_names = [attr_name for attr_name in dir(self) if not attr_name.endswith('_') and attr_name != method_name]
        dictionary = {}
        for attr_name in attr_names:
            dictionary[attr_name] = getattr(self, attr_name)
        return dictionary

    def setInstrument_(self, instrument: InsertInstrument) -> None:
        """
        *setInstrument_* Set *name* and *name2* attributes from an *InsertInstrument* instance.

        :param instrument: InsertInstrument instance
        :type instrument: InserInstrument
        """
        self.name = instrument.name
        self.name2 = instrument.name2
