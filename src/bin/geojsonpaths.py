# Conversion path coordinates comprising polygons of the base map for plots from Excel workbook format to GeoJSON format
# ======================================================================================================================
from src.jsontools.jsontools import writeJSON
from pandas import read_excel
from pathlib import Path
from src.operations.coordinates import hk1980ToWGS84
from src.classes.classes import Instrument


def convertXlsPathsToGeojson(plots_path: Path, xls_path: Path) -> None:
    """
    **convertXlsPathsToGeojson** Convert path coordinates comprising polygons of the base map for plots from Excel workbook format to GeoJSON format.

    :param plots_path: New or existing file path for generated GeoJSON file. The file defines a FeatureCollection of Features, each with a Polygon geometry. Coordinates are written as longitude and latitude, ready for plotting.
    :type plots_path: Path
    :param xls_path: Existing file path to Excel workbook containing path coordinates. For multiple paths, use one worksheet for each path. In each worksheet, the first row should comprise the header containing the column names 'Easting' and 'Northing'. Subsequent rows should define the eastings and northings of successive points along the path. The first point should be repeated as the last point to close the polygon.
    :type xls_path: Path
    """
    dataframes = read_excel(io=str(xls_path), sheet_name=None, header=0, names=None, index_col=None)
    feature_collection = {
        'type': 'FeatureCollection',
        'features': []
    }
    for sheetname, dataframe in dataframes.items():
        geometry_type = 'Polygon'
        geometry = {"type": geometry_type}
        coordinates = []
        for index, row in dataframe.iterrows():
            # Populate instrument instance with eastings and northings for argument in longitude-latitude conversion function hk1980ToWGS84
            instrument = Instrument()
            instrument.easting = row.filter(regex='[Ee]asting').iloc[0]
            instrument.northing = row.filter(regex='[Nn]orthing').iloc[0]
            # Convert eastings and northings to longitudes and latitudes
            hk1980ToWGS84(instrument=instrument)
            vertex = [instrument.longitude, instrument.latitude]
            coordinates.append(vertex)
    geometry["coordinates"] = [coordinates]
    feature = {
        "type": 'Feature',
        "geometry": geometry
    }
    feature_collection['features'].append(feature)
    writeJSON(str(plots_path), feature_collection)


if __name__ == '__main__':
    # Execution of convertXlsPathsToGeojson
    plots_path = Path(__file__).parents[2].joinpath('resources', 'plots', 'basemap.json')
    xls_path = Path(__file__).parents[2].joinpath('resources', 'plots', 'basemap.xlsx')
    convertXlsPathsToGeojson(
        plots_path=plots_path,
        xls_path=xls_path
    )
