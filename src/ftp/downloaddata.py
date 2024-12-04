# Functions for interfacing with the FTP server
# =============================================
import ftplib
import logging
import os
import dateutil.parser
from datetime import datetime, timedelta
from io import BytesIO
from math import isclose
from pathlib import Path
from re import compile, IGNORECASE, search
from numpy import add, array, floor_divide, intersect1d, isnan, less, minimum, zeros
from pandas import read_excel
from src.classes.classes import Elevation, Instrument, Reading
from src.data.data import instruments
from src.jsontools.jsontools import readJSON, writeJSON


def checkLastQuery(guidata: dict, lastquery: dict) -> bool:
    """
    **checkLastQuery** Check whether the requested dates for data fall within the date range covered by data already downloaded from the FTP server.

    :param guidata: Dictionary of data inputted through the graphical user interface.
    :type guidata: dict
    :param lastquery: Dictionary recording the date range entered the last time data was successfully downloaded. The dictionary must contain the keys 'startdate', 'enddate' and 'ignoreperiod'.
    :type lastquery: dict
    :return: Boolean. True if requested data falls outside the date range covered by the already-downloaded data.
    """
    # Initialise return value.
    downloadFlag = False
    # Read date range implied by the lastquery dictionary as a list of tuples. Each tuple represents a period, with the
    # first element as the start date and the second element as the end date of the period.
    lastquery_dateranges = evaluateDownloadDates(data=lastquery)
    for gui_daterange in evaluateDownloadDates(data=guidata):
        for gui_date in gui_daterange:
            if gui_date > lastquery_dateranges[0][1]:
                downloadFlag = True
                break
            if gui_date < lastquery_dateranges[1][0]:
                downloadFlag = True
                break
            if lastquery_dateranges[1][1] < gui_date < lastquery_dateranges[0][0]:
                downloadFlag = True
                break
        if downloadFlag:
            break
    return downloadFlag


def updateLastQuery(guidata: dict, lastquery_path: Path) -> None:
    """
    **updateLastQuery** Keep a record of the date range requested through the graphical user interface.
    
    :param guidata: Dictionary of data inputted through the graphical user interface.
    :type guidata: dict
    :param lastquery: Dictionary recording the date range entered the last time data was successfully downloaded. The dictionary must contain the keys 'startdate', 'enddate' and 'ignoreperiod'.
    :type lastquery: dict
    """
    lastquery = readJSON(filepath=str(lastquery_path))
    lastquery['startdate'] = guidata['startdate']
    lastquery['enddate'] = guidata['enddate']
    lastquery['ignoreperiod'] = guidata['ignoreperiod']
    writeJSON(filepath=str(lastquery_path), data=lastquery)


def evaluateDownloadDates(data: dict) -> list:
    """
    **evaluateDownloadDates** Define the start and end dates for periods in the date range specified by the fields ``startdate``, ``enddate`` and ``ignoreperiod``. The first period spans from *startdate* - *ignoreperiod* to *startdate*. The second period spans from *enddate - ignoreperiod* to *enddate*.
    
    :param data: Dictionary with the keys 'startdate', 'enddate' and 'ignoreperiod'.
    :type data: dict
    :return: List of tuples. Each tuple represents a period, with the first element as the start date and the second element as the end date of the period.
    """
    enddate = datetime.strptime(data['enddate'], '%d-%m-%Y %H:%M:%S') + timedelta(days=1) - timedelta(seconds=1)
    startdate = datetime.strptime(data['startdate'], '%d-%m-%Y %H:%M:%S') + timedelta(days=1) - timedelta(seconds=1)
    ignoreperiod = timedelta(days=int(data['ignoreperiod']))
    dateranges = [
        (enddate - ignoreperiod, enddate),
        (startdate - ignoreperiod, startdate)
    ]
    return dateranges


def downloadInstrumentReadings(
        server_info: dict,
        dir_structure: dict,
        layout: dict,
        instrument_types: dict,
        gui_data: dict
) -> None:
    """
    **downloadInstrumentReadings** Download instrument readings from the FTP server and store in the instruments dictionary.

    :param server_info: Dictionary storing FTP server access information. The dictionary should contain the keys ``'host'``, ``'user'`` and ``'password'``.
    :type server_info: dict
    :param dir_structure: Dictionary listing directories to search in the FTP server. The dictionary should contain the keys ``'_INITIAL_'`` and ``'_MEASURE_'``, through which the respective list of directories is accessed.
    :type dir_structure: dict
    :param layout: Dictionary defining the layout of reading data in MEASURE files on the FTP server. Top-level keys should comprise the instrument type codes.
    :type layout: dict
    :param instrument_types: Dictionary listing instrument types to read on the FTP server. The list is accessed through a key named ``'instrumenttypes'``.
    :type instrument_types: dict
    :param gui_data: Dictionary of data inputted through the graphical user interface.
    :type gui_data: dict
    """
    logger = logging.getLogger(__name__)
    ftp = ftplib.FTP(host=server_info['host'], user=server_info['user'], passwd=server_info['password'])
    ftp.encoding = 'utf-8'
    # Multiply the file count by 1000 to smoothen advance of the progress dialog, since the value attribute must be an
    # integer.
    file_count = 1000 * countFiles(
        ftp=ftp,
        subdirs=dir_structure['_MEASURE_'],
        layout=layout,
        pattern='_MEASURE_',
        instrument_types=instrument_types['instrumenttypes'],
        gui_data=gui_data
    )
    logger.info(f'Counted {int(0.001 * file_count)} MEASURE files to download')
    # Initialise a count of files.
    num_file = 0
    date_ranges = evaluateDownloadDates(data=gui_data)
    # Define patterns for filtering filenames.
    measure_pattern = compile(r'_MEASURE_', IGNORECASE)
    excel_pattern = compile(r'\.xls[xm]$')
    date_pattern = compile(r'\D2[01]\d\d(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\D')
    # Only read instrument types specified in the instrument_types dictionary.
    for instrument_type in intersect1d(ar1=ftp.nlst(), ar2=instrument_types['instrumenttypes']):
        # Skip instrument type directory if the corresponding layout is missing in the layout dictionary.
        if instrument_type not in layout.keys():
            logger.error(f'Layout of {instrument_type} not specified in MEASURE layout file')
            continue
        # Find the row and column of the most upper-left cell with data in the layout dictionary.
        min_cell = array([1000, 1000])
        for category in layout[instrument_type].values():
            try:
                for location in category.values():
                    minimum(min_cell, [location['row'], location['col']], out=min_cell)
            except:
                pass
        if (min_cell == array([1000, 1000])).all():
            logger.error(f'No row or column layout found in MEASURE layout file for {instrument_type}')
            continue
        logger.debug(f'Detected uppermost data row in MEASURE layout as {min_cell[0]}')
        logger.debug(f'Detected leftmost data column in MEASURE layout as {min_cell[1]}')
        for subdir in dir_structure['_MEASURE_']:
            pathname = os.path.join(instrument_type, subdir)
            # Record the current working directory to return to after testing whether a subdirectory exists.
            original_dir = ftp.pwd()
            try:
                # Determine whether a subdirectory exists by attempting to change the working directory.
                ftp.cwd(pathname)
                ftp.cwd(original_dir)
                logger.info(f'Successfully accessed path {pathname} to get MEASURE files')
            except Exception:
                logger.warning(f'Failed to access path {pathname} to get MEASURE files')
                continue
            for filename in ftp.nlst(pathname):
                # Skip the file if the filename does not match the desired pattern for a MEASURE filename.
                if not bool(search(pattern=measure_pattern, string=filename)):
                    logger.info(f'Found {filename} in MEASURE directory not matching _MEASURE_ filename pattern')
                    continue
                if not bool(search(pattern=excel_pattern, string=filename)):
                    logger.info(f'Found {filename} in MEASURE directory not Excel workbook (.xlsx)')
                    continue
                match_object = search(pattern=date_pattern, string=filename)
                if not bool(match_object):
                    logger.info(f'Found {filename} in MEASURE directory without valid date')
                    continue
                try:
                    date = datetime.strptime(match_object[0][1:-1], '%Y%m%d')
                    logger.debug(f'Successfully detected date {date} in filename {filename}')
                except ValueError:
                    logger.warning(f'Unable to detect date in filename {filename}')
                    continue
                # Initialise a boolean flag indicating whether the date in the filename falls within the requested date
                # range.
                valid_date = False
                for min_date, max_date in date_ranges:
                    if min_date < date < max_date:
                        valid_date = True
                        break
                if not valid_date:
                    continue
                num_file += 1
                # Download the file as a binary object.
                binary = BytesIO()
                ftp.retrbinary(f'RETR {filename}', binary.write)
                logger.debug(f'Downloaded binary file for {filename}')
                try:
                    dataframe = read_excel(io=binary, sheet_name=0, header=None, names=None, index_col=None)
                    logger.debug(f'Converted binary file for {filename} into dataframe')
                except Exception:
                    logger.error(f'Failed to convert binary file for {filename} into dataframe')
                    continue
                # Initialise a translation vector to advance through successive instruments in a file.
                cell_shift = array([0, 0])
                # Initialise the most upper-left cell location in each successive instrument record in the file.
                min_shift = add(min_cell, cell_shift)
                # The 'repeat' field in the layout dictionary specifies the number of rows and columns to advance by to
                # move to the next instrument record in a file.
                instrument_count = max(floor_divide(
                    dataframe.shape,
                    [layout[instrument_type]['repeat']['row'], layout[instrument_type]['repeat']['col']],
                    out=zeros((1, 2)),
                    where=array(
                        [layout[instrument_type]['repeat']['row'], layout[instrument_type]['repeat']['col']]) > 0
                )[0])
                logger.debug(f'Counted {int(instrument_count)} instruments listed in file {filename}')
                num_instruments = 0
                # Iterate until the most upper-left cell location of the currently-read instrument record falls outside
                # the range of data in the file.
                while all(less(min_shift, dataframe.shape)):
                    # Yield a tuple for the progress dialog comprising (label text, minimum, maximum, value)
                    # Multiply the number of files by 1000 to smoothen the advance of the progress dialog, since the
                    # value attribute must be an integer.
                    yield f'Reading instrument measurements in {filename}', 0, file_count, 1000 * (
                                num_file + num_instruments / instrument_count)
                    # The 'single' field in the layout dictionary defines the layout for attributes which are listed only
                    # once for each instrument record.
                    name = dataframe.iloc[layout[instrument_type]['single']['name']['row'] + cell_shift[0],
                                          layout[instrument_type]['single']['name']['col'] + cell_shift[1]]
                    tip_name = None
                    try:
                        # Create the key in the instruments dictionary as the name appended by the tip name, if it
                        # exists.
                        tip_name = dataframe.iloc[layout[instrument_type]['single']['tip_name']['row'] + cell_shift[0],
                                                  layout[instrument_type]['single']['tip_name']['col'] + cell_shift[1]]
                        key = '::'.join([segment for segment in (name, tip_name) if segment])
                    except:
                        key = name
                    # Attempt to get an existing Instrument instance in the instruments dictionary, otherwise create a
                    # new one.
                    try:
                        instrument = instruments[key]
                        create_instrument_data = False
                    except:
                        instrument = Instrument()
                        instrument.name = name
                        if tip_name is not None:
                            instrument.tip_name = tip_name
                        instrument.type_name = instrument_type
                        create_instrument_data = True
                        logger.warning(f'Unable to find matching dictionary instance with INITIAL data for {key}')
                    # For single-valued instruments, e.g. piezometer or marker...
                    # In the layout dictionary, single-valued instruments are indicated by a None value in the 'array'
                    # field.
                    if layout[instrument_type]['array'] is None:
                        reading = Reading()
                        for attr_name, loc in layout[instrument_type]['single'].items():
                            try:
                                setattr(reading, attr_name,
                                        dataframe.iloc[loc['row'] + cell_shift[0], loc['col'] + cell_shift[1]])
                            except IndexError:
                                logger.warning(f'Cell for {attr_name} in {filename} out of bounds.'
                                               f'Attempting to access cell {loc["row"] + cell_shift[0], loc["col"] + cell_shift[1]}'
                                               f'in dataframe with shape: {dataframe.shape}')
                                break
                        if isinstance(reading.date, str):
                            reading.date = dateutil.parser.parse(reading.date)
                        # Attempt to append the Reading instance to an existing Elevation instance, otherwise create a
                        # new one.
                        try:
                            elevation = instrument.elevations[0]
                        except:
                            elevation = Elevation()
                            instrument.appendElevation(elevation)
                            logger.warning(f'Unable to find matching dictionary elevation instance for {key} '
                                           f'at {instrument.elevations[0].elevation} mPD on {date}. Creating new elevation instance')
                        elevation.appendReading(reading)
                    # For array-valued instruments, e.g. inclinometer or extensometer...
                    else:
                        row = layout[instrument_type]['array']['name']['row']
                        # Iterate through each sensor of the array-valued instrument.
                        while True:
                            try:
                                elevation_name = dataframe.iloc[
                                    row, layout[instrument_type]['array']['name']['col'] + cell_shift[1]]
                            except IndexError:
                                logger.warning(f'Cell for {instrument.name} in {filename} out of bounds.'
                                               f'Attempting to access cell {row, layout[instrument_type]["array"]["name"]["col"] + cell_shift[1]}'
                                               f'in dataframe with shape: {dataframe.shape}')
                                break
                            if elevation_name == '':
                                break
                            if isinstance(elevation_name, float) and isnan([elevation_name])[0]:
                                break
                            reading = Reading()
                            reading.date = dataframe.iloc[
                                layout[instrument_type]['single']['date']['row'] + cell_shift[0],
                                layout[instrument_type]['single']['date']['col'] + cell_shift[1]]
                            if isinstance(reading.date, str):
                                reading.date = dateutil.parser.parse(reading.date)
                            for attr_name, loc in layout[instrument_type]['array'].items():
                                try:
                                    setattr(reading, attr_name, dataframe.iloc[row, loc['col'] + cell_shift[1]])
                                except IndexError:
                                    logger.warning(f'Cell for {attr_name} in {filename} out of bounds.'
                                                   f'Attempting to access cell {row, loc["col"] + cell_shift[1]}'
                                                   f'in dataframe with shape: {dataframe.shape}')
                                    break
                            # Test whether an Elevation instance already exists.
                            create_elevation = True
                            for elevation in instrument.elevations:
                                if isinstance(elevation.name, float) and isinstance(elevation_name, float):
                                    # Apply a tolerance when matching the name attribute of the Elevation instance, if
                                    # the name attribute is a string representation of the elevation value. This allows
                                    # for inaccuracies introduced by string conversion of the float.
                                    if isclose(a=elevation.name, b=elevation_name, abs_tol=0.01):
                                        elevation.appendReading(reading)
                                        create_elevation = False
                                        break
                                else:
                                    try:
                                        if elevation.name == elevation_name:
                                            elevation.appendReading(reading)
                                            create_elevation = False
                                            break
                                    except:
                                        logger.error(
                                            f'Unable to compare existing elevation name {elevation.name} with new elevation name {elevation_name}')
                            if create_elevation:
                                elevation = Elevation()
                                elevation.name = elevation_name
                                elevation.elevation = dataframe.iloc[
                                    row, layout[instrument_type]['array']['elevation']['col'] + cell_shift[1]]
                                elevation.appendReading(reading)
                                instrument.appendElevation(elevation)
                                logger.warning(f'Unable to find matching dictionary elevation instance for {key} '
                                               f'at {elevation.elevation} mPD on {reading.date}. Creating new elevation instance')
                            # Increment the row to shift to the next sensor.
                            row += 1
                            if row >= len(dataframe.index):
                                break
                    if create_instrument_data:
                        instruments[key] = instrument
                        logger.warning(f'Creating new dictionary instance with only MEASURE data for {key}')
                    # Increment the translation vector to reference the next instrument record in the file.
                    add([layout[instrument_type]['repeat']['row'], layout[instrument_type]['repeat']['col']],
                        cell_shift, out=cell_shift)
                    # Update the location of the most upper-left cell in the instrument record.
                    add(min_cell, cell_shift, out=min_shift)
                    num_instruments += 1


def downloadInstrumentDetails(
        server_info: dict,
        dir_structure: dict,
        layout: dict,
        instrument_types: dict,
        gui_data: dict
) -> None:
    """
    **downloadInstrumentDetails** Download instrument installation details from the FTP server and store in the instruments dictionary.

    :param server_info: Dictionary storing FTP server access information. The dictionary should contain the keys ``'host'``, ``'user'`` and ``'password'``.
    :type server_info: dict
    :param dir_structure: Dictionary listing directories to search in the FTP server. The dictionary should contain the keys ``'_INITIAL_'`` and ``'_MEASURE_'``, through which the respective list of directories is accessed.
    :type dir_structure: dict
    :param layout: Dictionary defining the layout of reading data in INITIAL files on the FTP server. Top-level keys should comprise the instrument type codes.
    :type layout: dict
    :param instrument_types: Dictionary listing instrument types to read on the FTP server. The list is accessed through a key named ``'instrumenttypes'``.
    :type instrument_types: dict
    :param gui_data: Dictionary of data inputted through the graphical user interface.
    :type gui_data: dict
    """
    logger = logging.getLogger(__name__)
    ftp = ftplib.FTP(host=server_info['host'], user=server_info['user'], passwd=server_info['password'])
    ftp.encoding = 'utf-8'
    file_count = countFiles(
        ftp=ftp,
        subdirs=dir_structure['_INITIAL_'],
        layout=layout,
        pattern='_INITIAL_',
        instrument_types=instrument_types['instrumenttypes'],
        gui_data=gui_data
    )
    logger.info(f'Counted {file_count} INITIAL files to download')
    # Initialise a count of files.
    num_file = 0
    # Define patterns for filtering filenames.
    initial_pattern = compile(r'_INITIAL_', IGNORECASE)
    excel_pattern = compile(r'\.xls[xm]$')
    # Only read instrument types specified in the instrument_types dictionary.
    for instrument_type in intersect1d(ar1=ftp.nlst(), ar2=instrument_types['instrumenttypes']):
        # Skip instrument type directory if the corresponding layout is missing in the layout dictionary.
        if instrument_type not in layout.keys():
            logger.error(f'Layout of {instrument_type} not specified in INITIAL layout file')
            continue
        for subdir in dir_structure['_INITIAL_']:
            pathname = os.path.join(instrument_type, subdir)
            # Record the current working directory to return to after testing whether a subdirectory exists.
            original_dir = ftp.pwd()
            try:
                # Determine whether a subdirectory exists by attempting to change the working directory.
                ftp.cwd(pathname)
                ftp.cwd(original_dir)
                logger.info(f'Successfully accessed path {pathname} to get INITIAL files')
            except Exception:
                logger.warning(f'Failed to access path {pathname} to get INITIAL files')
                continue
            for filename in ftp.nlst(pathname):
                num_file += 1
                # Yield a tuple for the progress dialog comprising (label text, minimum, maximum, value).
                yield f'Reading instrument details in {filename}', 0, file_count, num_file
                # Skip the file if the filename does not match the desired pattern for a INITIAL filename.
                if not bool(search(pattern=initial_pattern, string=filename)):
                    logger.info(f'Found {filename} in INITIAL directory not matching _INITIAL_ filename pattern')
                    continue
                if not bool(search(pattern=excel_pattern, string=filename)):
                    logger.info(f'Found {filename} in INITIAL directory not Excel workbook (.xlsx)')
                    continue
                # Download the file as a binary object.
                binary = BytesIO()
                ftp.retrbinary(f'RETR {filename}', binary.write)
                logger.debug(f'Downloaded binary file for {filename}')
                try:
                    dataframe = read_excel(io=binary, sheet_name=0, header=None, names=None, index_col=None)
                    logger.debug(f'Converted binary file for {filename} into dataframe')
                except Exception:
                    logger.error(f'Failed to convert binary file for {filename} into dataframe')
                    continue
                instrument = Instrument()
                # The 'general' field in the layout dictionary defines the layout of attribte data for both
                # single-valued and array-valued instruments.
                for attr_name, loc in layout[instrument_type]['general'].items():
                    if loc['row'] is None or loc['col'] is None:
                        setattr(instrument, attr_name, loc['initial'])
                    else:
                        setattr(instrument, attr_name, dataframe.iloc[loc['row'], loc['col']])
                # Create the key in the instruments dictionary as the name appended by the tip name, if it exists.
                key = '::'.join([segment for segment in (instrument.name, instrument.tip_name) if segment])
                if key in instruments.keys():
                    logger.error(f'Found duplicate INITIAL file named {filename} for {instrument.name}')
                    continue
                instrument.type_name = instrument_type
                if isinstance(instrument.install_date, str):
                    instrument.install_date = dateutil.parser.parse(instrument.install_date)
                # Create & populate a single Elevation instance with a single Reading instance for single-valued
                # instruments, e.g. marker or piezometer.
                # In the layout dictionary, single-valued instruments are indicated by the 'single' field having a value
                # other than None.
                if not layout[instrument_type]['single'] is None:
                    elevation = Elevation()
                    reading = Reading()
                    reading.date = instrument.install_date
                    for attr_name, loc in layout[instrument_type]['single'].items():
                        # Differentiate whether an attribute belongs to the Reading instance or the Elevation instance
                        # based upon whether the attribute name contains the string 'value'.
                        object = {True: reading, False: elevation}['value' in attr_name]
                        if loc['row'] is None or loc['col'] is None:
                            # If an attribute is not specified in the file, this is indicated in the layout dictionary
                            # with None for both row and column locations. In this case, the attribute value is given by
                            # the 'initial' field. An example is the value of settlement for a marker, which is defined
                            # as zero for the initial reading.
                            setattr(object, attr_name, loc['initial'])
                        else:
                            setattr(object, attr_name, dataframe.iloc[loc['row'], loc['col']])
                    elevation.appendReading(reading)
                    instrument.appendElevation(elevation)
                # Create & populate Elevation instances, each with a single Reading instance, for array-valued
                # instruments, e.g. inclinometers or extensometers.
                # Array-valued instruments are indicated by the 'array' field having a value other than None.
                if not layout[instrument_type]['array'] is None:
                    start_row = layout[instrument_type]['array']['elevation']['row']
                    # Iterate through each sensor of the array-valued instrument.
                    for row_data in dataframe.iloc[start_row:, ].iterrows():
                        elevation = Elevation()
                        reading = Reading()
                        reading.date = instrument.install_date
                        for attr_name, loc in layout[instrument_type]['array'].items():
                            # Differentiate whether an attribute belongs to the Reading instance or the Elevation
                            # instance based upon whether the attribute name contains the string 'value'.
                            object = {True: reading, False: elevation}['value' in attr_name]
                            if loc['row'] is None or loc['col'] is None:
                                # If an attribute is not specified in the file, this is indicated in the layout
                                # dictionary with None for both row and column locations. In this case, the attribute
                                # value is given by the 'initial' field. An example is the value of extension for an
                                # extensometer spider, which is defined as zero for the initial reading.
                                setattr(object, attr_name, loc['initial'])
                            else:
                                # The second element of row_data is the row expressed as a pandas Series.
                                setattr(object, attr_name, row_data[1][loc['col']])
                        elevation.appendReading(reading)
                        instrument.appendElevation(elevation)
                instruments[key] = instrument
                logger.debug(f'Successfully stored instance of {key} with INITIAL data in dictionary')


def countFiles(
        ftp: ftplib.FTP,
        subdirs: list,
        layout: dict,
        pattern: str,
        instrument_types: list,
        gui_data: dict
) -> int:
    """
    **countFiles** Count the number of files to download. Either the number of INITIAL files is counted, or the number of MEASURE files. Which type of file to count is differentiated by the subdir, layout and pattern arguments.

    :param ftp: Object for FTP connection.
    :type ftp: ftplib.FTP
    :param subdirs: Directories to access in the FTP server at the level below the directory named with the instrument type code.
    :type subdirs: list
    :param layout: Dictionary defining the layout of data in either the INITIAL files or the MEASURE files on the FTP server. Top-level keys should comprise the instrument type codes.
    :type layout: dict
    :param pattern: Either '_INITIAL_' or '_MEASURE_'.
    :type pattern: str
    :param instrument_types: Dictionary listing instrument types to read on the FTP server. The list is accessed through a key named ``'instrumenttypes'``.
    :type instrument_types: dict
    :param gui_data: Dictionary of data inputted through the graphical user interface.
    :type gui_data: dict
    :return: Integer. Number of files to download.
    """
    # Initialise a count of files.
    num_files = 0
    date_ranges = evaluateDownloadDates(data=gui_data)
    # Only read instrument types specified in the instrument_types dictionary.
    for instrument_type in intersect1d(ar1=ftp.nlst(), ar2=instrument_types):
        # Skip instrument type directory if the corresponding layout is missing in the layout dictionary.
        if instrument_type not in layout.keys():
            continue
        for subdir in subdirs:
            pathname = os.path.join(instrument_type, subdir)
            # Record the current working directory to return to after testing whether a subdirectory exists.
            original_dir = ftp.pwd()
            try:
                # Determine whether a subdirectory exists by attempting to change the working directory.
                ftp.cwd(pathname)
                ftp.cwd(original_dir)
            except ftplib.error_perm:
                continue
            for filename in ftp.nlst(pathname):
                # Skip the file if the filename does not match the desired pattern for the filename.
                if not bool(search(pattern=pattern, string=filename)):
                    continue
                if not bool(search(pattern='.xlsx', string=filename)):
                    continue
                if pattern == '_INITIAL_':
                    num_files += 1
                if pattern == '_MEASURE_':
                    try:
                        date = datetime.strptime(filename[-13:-5], '%Y%m%d')
                    except ValueError:
                        continue
                    # Initialise a boolean flag indicating whether the date in the filename falls within the requested
                    # date range.
                    valid_date = False
                    for min_date, max_date in date_ranges:
                        if min_date < date < max_date:
                            valid_date = True
                            break
                    if not valid_date:
                        continue
                    num_files += 1
    return num_files
