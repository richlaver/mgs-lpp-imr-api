# Functions for interfacing with the SQLite database
# ===========================================
# Functions include clearing, reading and writing to the database from the instrument dictionary
# ----------------------------------------------------------------------------------------------
import os
from datetime import datetime
from pathlib import Path
from src.classes.classes import Elevation, InsertInstrument, InsertReading, Instrument, Reading
from .sqliteapi import initialiseDatabase, readTable, writeDictionaryList
from src.data.data import instruments


def clearDatabase(database_path: Path) -> None:
    """
    **clearDatabase** Clear database and initialise with blank ``instruments`` and ``reading`` tables

    :param database_path: Path to database.
    :type database_path: Path
    """
    try:
        os.remove(os.path.join('.', 'db', str(database_path)))
    except OSError:
        pass
    initialiseDatabase(filename=str(database_path))


def readDatabase(database_path: Path, layout_initial: dict) -> None:
    """
    **readDatabase** Populate ``instruments`` dictionary from SQLite database.

    :param database_path: Path to the database.
    :type database_path: Path
    :param layout_initial: Path to the JSON file specifying layout of INITIAL files in FTP server.
    :type layout_initial: dict
    """
    # ----------------------
    # Read instruments table
    # ----------------------
    # instrument_columns is populated with the description of the table.
    # instrument_rows is populated with queried rows from the table.
    instrument_columns, instrument_rows = readTable(
        filename=str(database_path),
        table_name='instruments'
    )
    if instrument_rows is None:
        return
    # Each element of the description is a tuple corresponding to a column in the table.
    # The first element of each tuple is the column name.
    attr_names = [instrument_column[0] for instrument_column in instrument_columns]
    instrument_count = 0
    for instrument_row in instrument_rows:
        instrument = Instrument()
        instrument.name = instrument_row[attr_names.index('name')]
        instrument.type_name = instrument_row[attr_names.index('type_name')]
        key = instrument.name
        if 'tip_name' in layout_initial[instrument.type_name]['general']:
            instrument.tip_name = instrument_row[attr_names.index('name2')]
            key = '::'.join([key, instrument.tip_name])
        try:
            instrument = instruments[key]
        except KeyError:
            easting = instrument_row[attr_names.index('easting')]
            if easting is not None:
                instrument.easting = float(easting)
            northing = instrument_row[attr_names.index('northing')]
            if northing is not None:
                instrument.northing = float(northing)
            install_date = instrument_row[attr_names.index('install_date')]
            if install_date is not None:
                instrument.install_date = datetime.strptime(install_date, '%Y-%m-%d %H:%M:%S')
            if 'bearing_north' in layout_initial[instrument.type_name]['general']:
                bearing_north = instrument_row[attr_names.index('bearing_north')]
                if bearing_north is not None:
                    instrument.bearing_north = float(bearing_north)
                bearing_seawall = instrument_row[attr_names.index('bearing_seawall')]
                if bearing_seawall is not None:
                    instrument.bearing_seawall = float(bearing_seawall)
            instruments[key] = instrument
        elevation = Elevation()
        elevationvalue = instrument_row[attr_names.index('elevation')]
        if elevationvalue is not None:
            elevation.elevation = float(elevationvalue)
        elevation.name = instrument_row[attr_names.index('name2')]
        instrument.appendElevation(elevation)
        instrument_count += 1
        yield 'Reading instrument details from database...', 0, len(instrument_rows), instrument_count
    # -------------------
    # Read readings table
    # -------------------
    # reading_columns is populated with the description of the table.
    # reading_rows is populated with queried rows from the table.
    reading_columns, reading_rows = readTable(
        filename=str(database_path),
        table_name='readings'
    )
    if reading_rows is None:
        return
    # Each element of the description is a tuple corresponding to a column in the table.
    # The first element of each tuple is the column name.
    attr_names = [reading_column[0] for reading_column in reading_columns]
    reading_count = 0
    for reading_row in reading_rows:
        instrument_name = reading_row[attr_names.index('name')]
        instrument_name2 = reading_row[attr_names.index('name2')]
        try:
            instrument = instruments[instrument_name]
        except KeyError:
            try:
                instrument = instruments['::'.join([instrument_name, instrument_name2])]
            except KeyError:
                continue
        elevationvalue = reading_row[attr_names.index('elevation')]
        if elevationvalue is not None:
            reading_elevation = float(elevationvalue)
        # Attempt to match the reading entry to an instrument or sensor via elevation. If a match is found, the reading
        # is stored in the elevations attribute of the instrument or sensor within an Elevation instance.
        for elevation in instrument.elevations:
            if elevation.elevation == reading_elevation:
                reading = Reading()
                date = reading_row[attr_names.index('date')]
                if date is not None:
                    reading.date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                for reading_attr in ['value', 'value2', 'value3', 'value4']:
                    value = reading_row[attr_names.index(reading_attr)]
                    if value is not None:
                        setattr(reading, reading_attr, float(value))
                elevation.appendReading(reading)
                break
        reading_count += 1
        yield 'Reading instrument readings from database...', 0, len(reading_rows), reading_count


def writeDatabase(database_path: Path, layout_initial: dict) -> None:
    """
    **writeDatabase** Insert data from ``instruments`` dictionary into ``instruments`` and ``readings`` tables in
    database.

    :param database_path: Path to thee database.
    :type database_path: Path
    :param layout_initial: Path to the JSON file specifying layout of INITIAL files in FTP server.
    :type layout_initial: dict
    """
    # insert_instruments and insert_readings are lists populated with instances of InsertInstrument and InsertReading.
    # InsertInstrument and InsertReading have attributes which reflect the column names in the instruments and readings
    # tables of the database respectively. Translating the Instrument and Reading data into these classes is a precursor
    # for writing data to the database.
    insert_instruments = []
    insert_readings = []
    instrument_count = 0
    for instrument in instruments.values():
        for elevation in instrument.elevations:
            insert_instrument = InsertInstrument()
            insert_instrument.name = instrument.name
            if 'tip_name' in layout_initial[instrument.type_name]['general']:
                insert_instrument.name2 = instrument.tip_name
            if layout_initial[instrument.type_name]['array'] is not None:
                insert_instrument.name2 = elevation.name
            insert_instrument.easting = instrument.easting
            insert_instrument.northing = instrument.northing
            insert_instrument.elevation = elevation.elevation
            if 'bearing_north' in layout_initial[instrument.type_name]['general']:
                insert_instrument.bearing_north = instrument.bearing_north
                insert_instrument.bearing_seawall = instrument.bearing_seawall
            insert_instrument.type_name = instrument.type_name
            insert_instrument.install_date = instrument.install_date
            # Instrument data is stored as a list of dictionaries in insert_instruments.
            insert_instruments.append(insert_instrument.asDict())
            for reading in elevation.readings:
                insert_reading = InsertReading()
                insert_reading.name = insert_instrument.name
                insert_reading.name2 = insert_instrument.name2
                insert_reading.date = reading.date
                insert_reading.elevation = insert_instrument.elevation
                insert_reading.value = reading.value
                insert_reading.value2 = reading.value2
                insert_reading.value3 = reading.value3
                insert_reading.value4 = reading.value4
                # Reading data is stored as a list of dictionaries in insert_readings.
                insert_readings.append(insert_reading.asDict())
        instrument_count += 1
        yield f'Converting data for writing to database... Converted {instrument_count} instruments', 0, len(
            instruments), instrument_count
    # All data is converted to a consistent string format prior to writing to the database.
    dataToString(insert_instruments)
    dataToString(insert_readings)
    yield f'Writing data to database...', 0, 1, 0
    writeDictionaryList(filename=str(database_path), data_list=insert_instruments, table_name='instruments')
    yield f'Writing data to database...', 0, 1, 0.5
    writeDictionaryList(filename=str(database_path), data_list=insert_readings, table_name='readings')
    yield f'Writing data to database...', 0, 1, 1


def dataToString(data_list: list) -> None:
    """
    **dataToString** Convert float and datetime values in a list of dictionaries to string values.

    :param data_list: List of dictionaries.
    :type data_list: list
    """
    for data_dict in data_list:
        for attr_name, attr_value in data_dict.items():
            if isinstance(attr_value, float):
                data_dict[attr_name] = '{:.3f}'.format(attr_value)
            if isinstance(attr_value, datetime):
                data_dict[attr_name] = attr_value.strftime('%Y-%m-%d %H:%M:%S')
