# Functions operating on Region instances
# =======================================
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from pathlib import Path
from re import compile, search
from numpy import nanpercentile, isnan
import os
from src.data.data import instruments, region_groups
from src.classes.classes import Region


def countRegions() -> int:
    """
    **countRegions** Count the number of *Region* instances stored in the region_group dictionary.

    :return: int. Number of Region instances.
    """
    region_count = 0
    for region_group in region_groups['region_groups']:
        region_count += len(region_group['regions'])
    return region_count


def readRegions(regiongroups_data: dict) -> None:
    """
    **readRegions** Initialise the region_groups dictionary structure.

    :param regiongroups_data: Dictionary for region_groups.
    :type regiongroups_data: dict
    """
    # Hidden files are prefixed and suffixed with '__'.
    hiddenfile_pattern = compile('__\S*__')
    # Generate a list of instrument names as they are recorded in the directory names under the operations.instruments
    # module. The instrument names are 'extensometer', 'inclinometer', 'marker' and 'piezometer'.
    instrument_names = []
    for instrument_name in os.listdir(str(Path(__file__).parents[0].joinpath('instruments'))):
        if not os.path.isdir(str(Path(__file__).parents[0].joinpath('instruments', instrument_name))):
            continue
        # Skip hidden files.
        if bool(search(hiddenfile_pattern, instrument_name)):
            continue
        instrument_names.append(instrument_name)
    region_groups['region_groups'] = []
    for region_group in regiongroups_data['region_groups']:
        for region in region_group['regions']:
            region['instruments'] = []
            for instrument_name in instrument_names:
                region['instruments'].append({
                    'name': instrument_name,
                    'outputs': []
                })
        region_groups['region_groups'].append(region_group)


def assignRegions() -> None:
    """
    **assignRegions** Record whether an *Instrument* instance falls within a region, for each *Instrument* instance in  the instrument dictionary. If an *Instrument* instance falls within a region, a *Region* instance is created in the regions attribute of the *Instrument* instance to indicate this.
    """
    # The length of the search range is necessary to yield the maximum scale for the progress dialog.
    num_assignments = countRegions() * len(instruments)
    # Initialise a count of searches.
    assignment_count = 0
    for region_group in region_groups['region_groups']:
        for region in region_group['regions']:
            polygon = Polygon([(vertex['easting'], vertex['northing']) for vertex in region['vertices']])
            for instrument in instruments.values():
                # Initialise flag defined as True if the region contains the Instrument instance.
                containsInstrument = False
                if all([instrument.easting is not None, instrument.northing is not None]):
                    point = Point(float(instrument.easting), float(instrument.northing))
                    if polygon.contains(point):
                        containsInstrument = True
                # Initialise flag defined as True if the Instrument instance already has a Region instance with the same
                # region group name. If such a Region instance already exists, the region is added to the instance. If
                # not, a new Region instance is generated. There is therefore one Region instance for each region group.
                hasRegionFlag = False
                for regionInstance in instrument.regions:
                    if regionInstance.group_name == region_group['name']:
                        hasRegionFlag = True
                        if containsInstrument:
                            regionInstance.appendRegionName(region['name'])
                        break
                if not hasRegionFlag:
                    regionInstance = Region()
                    regionInstance.group_name = region_group['name']
                    if containsInstrument:
                        regionInstance.appendRegionName(region['name'])
                    instrument.appendRegion(regionInstance)
                assignment_count += 1
                yield f'Assigning regions to instruments...', 0, num_assignments, assignment_count


def findRegionPercentiles(percentile_ranks: list = []) -> None:
    """
    **findRegionPercentiles** Evaluate percentile values for each region in the region_groups dictionary and store the values in the dictionary.

    :param percentile_ranks: List of percentile ranks at which to evaluate percentile values. Ranks should be in the range 0 to 100.
    :type percentile_ranks: list
    """
    # Generate a list of attribute names to access in instances of Output in the outputs attribute of each Instrument
    # instance.
    magnitude_names = [
        'output_magnitude',
        'output_magnitude2',
        'output_magnitude3'
    ]
    # Initialise a count of instruments.
    instrument_count = 0
    # The following code generates the following structure in the region_groups dictionary:
    # {
    #    'region_groups': [
    #        {
    #            'name': <region group name e.g. 'Group A'>,
    #            'regions': [
    #                {
    #                    'name': <region name e.g. '3rd Runway and Taxiway'>,
    #                    'instruments': [
    #                        'name': <full instrument type name e.g. 'extensometer'>,
    #                        'outputs': [
    #                            {
    #                                'name': <output name e.g. 'absolute_end'>,
    #                                'stratum': <stratum name e.g. 'marine deposit'>,
    #                                'output_magnitude': {
    #                                    'names': [
    #                                        {
    #                                            'name': <instrument name e.g. 'VWP-C20'>
    #                                            'tip_name': <instrument tip name e.g. 'L1'>
    #                                        }, ...
    #                                    ],
    #                                    'values': [ ... <value of output for the corresponding instrument in the 'names' list> ... ],
    #                                    'percentiles': [
    #                                        {
    #                                            'rank': <percentile rank e.g. 0.25 (equivalent to lower quartile)>,
    #                                            'value': <percentile value>
    #                                        }
    #                                    ],
    #                                    'minimum': {
    #                                        'name': <instrument name e.g. 'VWP-C20'>,
    #                                        'tip_name': <instrument tip name e.g. 'L1'>,
    #                                        'value': <minimum value of output>
    #                                    },
    #                                    'maximum': {
    #                                        'name': <instrument name e.g. 'VWP-C20'>,
    #                                        'tip_name': <instrument tip name e.g. 'L1'>,
    #                                        'value': <maximum value of output>
    #                                    }
    #                                }
    #                                'output_magnitude2': {<fields as output_magnitude>},
    #                                'output_magnitude3': {<fields as output_magnitude>}
    #                            }, ...
    for region_group in region_groups['region_groups']:
        for region in region_group['regions']:
            # The object region_instrument refers to a dictionary with the 'name' field as the full instrument type
            # name. The object does not refer to an Instrument instance.
            for region_instrument in region['instruments']:
                for instrument_instrument in instruments.values():
                    for instrument_region in instrument_instrument.regions:
                        # Identify Instrument instances which fall within a particular region of a particular region
                        # group.
                        if instrument_region.group_name == region_group['name'] and region['name'] in instrument_region.region_names:
                            # Attempt to derive the full instrument type name from the type code. The full instrument
                            # type name is needed to reference the set of outputs in the region_groups dictionary.
                            try:
                                instrument_instrument_typename = {
                                    'SA': 'inclinometer',
                                    'INC': 'inclinometer',
                                    'MPX': 'extensometer',
                                    'VWP': 'piezometer',
                                    'SM2': 'marker'
                                }[instrument_instrument.type_name]
                            except KeyError:
                                instrument_instrument_typename = None
                            # Identify in the region_groups dictionary the dictionary of outputs referring to the full
                            # type name of the particular Instrument instance.
                            if region_instrument['name'] == instrument_instrument_typename:
                                for instrument_output in instrument_instrument.outputs:
                                    # Initialise flag that is True if a new dictionary is required to store output for a
                                    # particular output type ('absolute_end', 'absolute_start' or 'difference') and
                                    # stratum.
                                    create_newoutput = True
                                    for region_output in region_instrument['outputs']:
                                        if region_output['name'] != instrument_output.name:
                                            continue
                                        if region_output['stratum'] != instrument_output.stratum:
                                            continue
                                        create_newoutput = False
                                        # Record the Instrument instance name, tip name and output_magnitude values
                                        # under the outputs attribute if the Instrument instance falls within the
                                        # region.
                                        for magnitude_name in magnitude_names:
                                            try:
                                                magnitude_value = getattr(instrument_output, magnitude_name)
                                                if magnitude_value is not None:
                                                    region_output[magnitude_name]['names'].append({
                                                        'name': instrument_instrument.name,
                                                        'tip_name': instrument_instrument.tip_name
                                                    })
                                                    region_output[magnitude_name]['values'].append(magnitude_value)
                                            except AttributeError:
                                                pass
                                        break
                                    if create_newoutput:
                                        region_output = {
                                            'name': instrument_output.name,
                                            'stratum': instrument_output.stratum
                                        }
                                        for magnitude_name in magnitude_names:
                                            region_output[magnitude_name] = {
                                                'names': [],
                                                'values': []
                                            }
                                            try:
                                                magnitude_value = getattr(instrument_output, magnitude_name)
                                                if magnitude_value is not None:
                                                    region_output[magnitude_name]['names'].append({
                                                        'name': instrument_instrument.name,
                                                        'tip_name': instrument_instrument.tip_name
                                                    })
                                                    region_output[magnitude_name]['values'].append(magnitude_value)
                                            except AttributeError:
                                                pass
                                        region_instrument['outputs'].append(region_output)
                for region_output in region_instrument['outputs']:
                    for magnitude_name in magnitude_names:
                        magnitude_data = region_output[magnitude_name]
                        percentile_values = nanpercentile(a=magnitude_data['values'], q=percentile_ranks, interpolation='linear', keepdims=True)
                        if not any(isnan(percentile_values)):
                            # Generate array of percentile values, each value corresponding to the percentile rank
                            # specified in percentile_ranks.
                            percentiles = [{'rank': rank, 'value': value[0]} for rank, value in zip(percentile_ranks, percentile_values)]
                            magnitude_data['percentiles'] = percentiles
                        else:
                            magnitude_data['percentiles'] = None
                        # Although minimum and maximum values are given by the percentile values evaluated at percentile
                        # ranks of 0 and 1 respectively, the names of the instruments with the minimum and maximum
                        # values need to be recorded for writing in the report.
                        if magnitude_data['values']:
                            for extreme_name, extreme_value in {
                                'minimum': min(magnitude_data['values']),
                                'maximum': max(magnitude_data['values'])
                            }.items():
                                extreme_index = magnitude_data['values'].index(extreme_value)
                                magnitude_data[extreme_name] = {
                                    'name': magnitude_data['names'][extreme_index]['name'],
                                    'tip_name': magnitude_data['names'][extreme_index]['tip_name'],
                                    'value': extreme_value
                                }
                        else:
                            magnitude_data['minimum'] = None
                            magnitude_data['maximum'] = None
                instrument_count += 1
                yield f'Evaluating percentiles...', 0, len(instruments), instrument_count