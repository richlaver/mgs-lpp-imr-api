# Conversion of boundary coordinates of regions from Excel workbook format to JSON format
# =======================================================================================
from src.jsontools.jsontools import readJSON, writeJSON
from pandas import read_excel
from pathlib import Path


def convertXlsRegionsToJson(regions_path: Path, xls_path: Path) -> None:
    """
    **convertXlsRegionsToJson** Convert boundary coordinates of regions from Excel workbook format to JSON format.

    :param regions_path: New or existing file path for generated JSON file with the format {'region_groups': [{'name': <region_group_name>, 'regions': [{'name':<region_name>, 'vertices': [{'easting': , 'northing': }... ]}, ...]},... ]}. If the file already contains region group data, the new region group data will be appended to the file.
    :type regions_path: Path
    :param xls_path: Existing file path to Excel workbook containing boundary coordinates of regions. The workbook name is taken as the region group name. Each region should be defined on a separate worksheet. The name of the worksheet is taken as the region name. The first row should comprise a header with the column names 'Easting' and 'Northing'. Subsequent rows list the eastings and northings of successive points around the region. The first point should be repeated as the last point to close the polygon.
    :type regions_path: Path
    """
    dataframes = read_excel(io=str(xls_path), sheet_name=None, header=0, names=None, index_col=None)
    group_list = []
    for region_name, dataframe in dataframes.items():
        region_dict = {'name': region_name}
        vertices = []
        for index, row in dataframe.iterrows():
            easting = row.filter(regex='[Ee]asting')
            northing = row.filter(regex='[Nn]orthing')
            vertex = {'easting': easting.iloc[0], 'northing': northing.iloc[0]}
            vertices.append(vertex)
        region_dict['vertices'] = vertices
        group_list.append(region_dict)
    group_name = xls_path.stem
    regions_dict = readJSON(str(regions_path))
    try:
        region_groups = regions_dict['region_groups']
        group_exists = False
        for region_group in region_groups:
            if region_group['name'] == group_name:
                region_group['regions'] = group_list
                group_exists = True
                break
        if not group_exists:
            group_dict = {'name': group_name, 'regions': group_list}
            region_groups.append(group_dict)
    except Exception:
        group_dict = {'name': group_name, 'regions': group_list}
        region_groups = [group_dict]
        regions_dict = {'region_groups': region_groups}
    writeJSON(str(regions_path), regions_dict)


if __name__ == '__main__':
    # Execution of convertXlsRegionsToJson
    regions_path = Path(__file__).parents[2].joinpath('resources', 'regions', 'regions.json')
    xls_path = Path(__file__).parents[2].joinpath('resources', 'regions', 'Group A.xlsx')
    convertXlsRegionsToJson(
        regions_path=regions_path,
        xls_path=xls_path
    )
