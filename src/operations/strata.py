# Functions for operating on Stratum instances
# ============================================
import logging
from glob import glob
from pathlib import Path
from string import ascii_uppercase
from numpy import isnan
from pandas import read_excel
from re import compile, IGNORECASE, search
from src.data.data import instruments
from src.classes.classes import Stratum
from src.operations.count import countInstruments
from src.operations.instruments.piezometer.typecodes import typeCodes as piezometerTypeCodes
from src.operations.instruments.extensometer.typecodes import typeCodes as extensometerTypeCodes


def assignVwpStrata() -> None:
    """
    **assignVwpStrata** Assign a stratum to each piezometer by generating a *Stratum* instance with a name attribute
    indicating the stratum name for each piezometer.
    """
    type_codes = piezometerTypeCodes()
    # Count the total number of piezometers to define maximum value of the progress bar for the progress dialog.
    num_vwps = countInstruments(typeCodes=type_codes)
    # Specify regular expressions for identifying the stratum from the tip name.
    alluvium_pattern = compile(r'L', IGNORECASE)
    marinedeposit_pattern = compile(r'M', IGNORECASE)
    # Initialise a count of piezometers.
    vwp_count = 0
    for instrument in instruments.values():
        if instrument.type_name not in type_codes:
            continue
        stratum = Stratum()
        if instrument.type_name == 'SP':
            # It is assumed that standpipes are always installed in the fill.
            stratum.name = 'fill'
        else:
            if bool(search(pattern=alluvium_pattern, string=instrument.tip_name)):
                stratum.name = 'alluvium'
            elif bool(search(pattern=marinedeposit_pattern, string=instrument.tip_name)):
                stratum.name = 'marine deposit'
        instrument.appendStrata(stratum=stratum)
        vwp_count += 1
        yield f'Assigning strata to vibrating wire piezometers...', 0, num_vwps, vwp_count


def readStrataElevations(stratadir_path: Path, layoutstrata_data: dict) -> None:
    """
    **readStrataElevations** Read the elevations of the strata boundaries from the Excel workbook saved in
    resources/strata.

    :param stratadir_path: Path to the directory containing the Excel workbook listing the strata boundary elevations.
    :type stratadir_path: Path
    :param layoutstrata_data: Dictionary defining the layout of the Excel workbook.
    :type layoutstrata_data: dict
    """
    logger = logging.getLogger(__name__)
    # Generate a list of uppercase letters in alphabetical order, for easy conversion between Excel worksheet column
    # letters and numbers.
    alphabet = list(ascii_uppercase)
    strata_data = layoutstrata_data['strata']
    # Generate a list of column names (as column letters) to read.
    col_names = [stratum['elevation_col'] for stratum in strata_data if stratum['elevation_col'] is not None]
    elevation_cols = col_names
    # Include first column as an index column.
    elevation_cols.insert(0, layoutstrata_data['name_col'])
    # Argument in pandas.read_excel() should be a comma-separated value string.
    elevation_cols = ','.join(elevation_cols)
    # Generate list of Excel workbooks in the directory containing the Excel workbook to read.
    boundary_filenames = glob(str(Path.joinpath(stratadir_path, '*.xls*')))
    # Only one Excel workbook is expected.
    if len(boundary_filenames) > 1:
        logger.critical(f'More than one file defining strata elevations in {str(stratadir_path)}')
        return
    dataframe = read_excel(
        io=boundary_filenames[0],
        sheet_name=layoutstrata_data['sheet_name'],
        header=None,
        names=col_names,
        index_col=alphabet.index(layoutstrata_data['name_col']),
        usecols=elevation_cols,
        skiprows=list(range(layoutstrata_data['data_row'] - 1))
    )
    num_extensometers = countInstruments(extensometerTypeCodes())
    # Initialise a count of extensometers.
    extensometer_count = 0
    for instrument in instruments.values():
        if instrument.type_name not in extensometerTypeCodes():
            continue
        extensometer_count += 1
        yield 'Reading extensometer boundary elevations...', 0, num_extensometers, extensometer_count
        try:
            # Extract from the dataframe the rows corresponding to the particular instrument.
            elevations = dataframe.loc[[instrument.name]]
        except KeyError:
            logger.error(f'Unable to find {instrument.name} in strata elevations file '
                         f'{str(stratadir_path.joinpath(boundary_filenames[0]))}')
            continue
        if len(elevations) > 1:
            # If more than one row exists for the particular instrument, consider only the first row.
            elevations = elevations.iloc[[0]]
            logger.error(f'Found more than one instance of {instrument.name} in '
                         f'{str(stratadir_path.joinpath(boundary_filenames[0]))}.'
                         f'Using first instance.')
        for index, stratum_data in enumerate(strata_data):
            # Skip entries in the strata dictionary corresponding to boundaries in between the strata.
            if stratum_data['type'] != 'stratum':
                continue
            stratum = Stratum()
            stratum.name = stratum_data['name']
            # Leave the upper boundary of the uppermost stratum undefined.
            if index > 0:
                # Read the letter of the column to read from the entry for the boundary above the particular stratum.
                stratum.upper_elevation_value = elevations[strata_data[index - 1]['elevation_col']][0]
                if isnan(stratum.upper_elevation_value):
                    stratum.upper_elevation_value = None
            # Leave the lower boundary of the lowermost stratum undefined.
            if index < len(strata_data) - 1:
                # Read the letter of the column to read from the entry for the boundary below the particular stratum.
                stratum.lower_elevation_value = elevations[strata_data[index + 1]['elevation_col']][0]
                if isnan(stratum.lower_elevation_value):
                    stratum.lower_elevation_value = None
            instrument.appendStrata(stratum)
