# Convenience functions for interfacing with the SQLite database
# ==============================================================
import logging
from os import path
import sqlite3
from sqlite3 import Error


def readTable(filename: str, table_name: str, columns: list=[], where: list=[]) -> None or tuple:
    """
    **readTable** Query a specified table in a database and return its description and data if successful.

    :param filename: File path to the database being queried.
    :type filename: str
    :param table_name: Name of the table being queried.
    :type table_name: str
    :param columns: List of column names being queried. The output is sorted according to the order of the column names in the list.
    :type columns: list
    :param where: List of equality conditions for the query. Each condition should comprise a tuple with the column name as the first element, and the required value as the second element.
    :return: Tuple comprising the description of the queried columns as the first element, and the row data as the second element. If the query is unsuccessful, None is returned.
    """
    logger = logging.getLogger(__name__)
    if columns:
        sql_statement = 'SELECT ' + ', '.join(columns)
    else:
        sql_statement = 'SELECT *'
    sql_statement += '''
    FROM ''' + table_name
    if where:
        sql_statement += '''
        WHERE ''' + ' AND '.join([' = '.join((condition[0], '\'' + condition[1] + '\'')) for condition in where])
    if columns:
        sql_statement += ''' 
        ORDER BY ''' + ', '.join(columns)
    conn = _createConnection(filename=filename)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_statement)
        description = cursor.description
        rows = cursor.fetchall()
        return description, rows
    except Exception:
        logger.exception(f'Failed to output {", ".join(columns)} from {table_name} database table')
        return None


def writeDictionaryList(filename: str, data_list: list, table_name: str) -> None:
    """
    **writeDictionaryList** Write data from a list of dictionaries into a table of a database.

    :param filename: File path to the database.
    :type filename: str
    :param data_list: List of dictionaries to write to the database table. The keys of each dictionary should be column names in the table.
    :type data_list: list
    :param table_name: Name of the database table to write data to.
    :type table_name: str
    """
    logger = logging.getLogger(__name__)
    if len(data_list) == 0:
        return
    csv_columns = ', '.join(data_list[0].keys())
    csv_keys = ', '.join([':' + key for key in data_list[0].keys()])
    sql_statement = 'INSERT OR IGNORE INTO ' + table_name + '(' + \
                        csv_columns + \
                    ') VALUES(' + \
                        csv_keys + \
                    ')'
    conn = _createConnection(filename=filename)
    cursor = conn.cursor()
    try:
        cursor.executemany(sql_statement, data_list)
        conn.commit()
        logger.debug(f'Successfully inserted {table_name} data into database')
    except Exception:
        logger.exception(f'Unable to insert {table_name} data into database')


def initialiseDatabase(filename: str) -> None:
    """
    **initialiseDatabase** Creates a database with tables to store instruments and readings

    :param filename: File path to the database.
    :type filename: str
    """
    sqlCreateInstrumentsTable = '''CREATE TABLE IF NOT EXISTS instruments (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    name2 text NOT NULL,
                                    easting text,
                                    northing text,
                                    elevation text,
                                    bearing_north text,
                                    bearing_seawall text,
                                    type_name text,
                                    install_date text,
                                    UNIQUE (name, name2)
                                );'''
    sqlCreateReadingsTable = '''CREATE TABLE IF NOT EXISTS readings (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    name2 text NOT NULL,
                                    date text NOT NULL,
                                    elevation text,
                                    value text,
                                    value2 text,
                                    value3 text,
                                    value4 text,
                                    UNIQUE (name, name2, date)
                                );'''
    conn = _createConnection(filename=filename)
    with conn:
        _createTable(conn=conn, sql_statement=sqlCreateInstrumentsTable)
        _createTable(conn=conn, sql_statement=sqlCreateReadingsTable)


def _createConnection(filename: str) -> None or sqlite3.Connection:
    """
    **_createConnection** Private function connecting to a database. A connection object is returned if the connection is successful.
    :param filename: File path to the database.
    :type filename: str
    :return: SQLite Connection object if connection is successful, otherwise None.
    """
    logger = logging.getLogger(__name__)
    conn = None
    try:
        conn = sqlite3.connect(path.join(path.dirname(__file__), filename))
        return conn
    except Error:
        logger.critical(f'Unable to connect to database at {path.join(path.dirname(__file__), filename)}')


def _createTable(conn: sqlite3.Connection, sql_statement: str) -> None:
    """
    **_createTable** Private function creating a table in a database.

    :param conn: SQLite Connection object to the database.
    :type conn: sqlite3.Connection
    :param sql_statement: SQL statement to create the table.
    :type sql_statement: str
    """
    logger = logging.getLogger(__name__)
    try:
        cursor = conn.cursor()
        cursor.execute(sql_statement)
    except Error:
        logger.critical(f'Unable to create table in database with SQL statement: {sql_statement}')
