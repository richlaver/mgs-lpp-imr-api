# Initialisation of data dictionaries
# ===================================
# Dictionary of instruments, containing installation details and readings for each instrument. The structure of the
# dictionary is as follows:
# {
#    <instrument name>::<instrument tip name> or <instrument name> if no tip name exists: Instrument()
#        .name
#        .tip_name
#        .easting
#        .northing
#        .longitude
#        .latitude
#        .bearing_north
#        .bearing_seawall
#        .type_name
#        .install_date
#        .elevations = [
#             Elevation()
#                .elevation
#                .name
#                .start_reading = Reading()
#                .end_reading = Reading()
#                .readings = [
#                    Reading()
#                       .date,
#                       .value,
#                       .value2,
#                       .value3,
#                       .value4
#                   ...
#                ]
#            ...
#        ]
#        .strata = [
#            Stratum()
#                .name
#                .upper_elevation_value
#                .lower_elevation_value
#                .upper_elevation = Elevation()
#                .lower_elevation = Elevation()
#                .displacement
#                .extension
#            ...
#        ]
#        .outputs = [
#            Output()
#                .name
#                .stratum
#                .start_reading = Reading()
#                .end_reading = Reading()
#                .elevation = Elevation()
#                .output_magnitude
#                .output_magnitude2
#                .output_magnitude3
#                .output_bearing
#                .observation
#            ...
#        ]
#        .regions = [
#            Region()
#                .group_name
#                .region_names = [
#                    region_name,
#                    ...
#                ]
#            ...
#        ],
#    ...
instruments = {}
# Dictionary of region groups, containing data on each region. The structure of the region_groups dictionary is as
# follows:
# {
#    'region_groups': [
#        {
#            'name': <region group name e.g. 'Group A'>,
#            'regions': [
#                {
#                    'name': <region name e.g. '3rd Runway and Taxiway'>,
#                    'instruments': [
#                        {
#                           'name': <full instrument type name e.g. 'extensometer'>,
#                           'outputs': [
#                                {
#                                    'name': <output name e.g. 'absolute_end'>,
#                                    'stratum': <stratum name e.g. 'marine deposit'>,
#                                    'output_magnitude': {
#                                        'names': [
#                                            {
#                                                'name': <instrument name e.g. 'VWP-C20'>
#                                                'tip_name': <instrument tip name e.g. 'L1'>
#                                            }, ...
#                                        ],
#                                       'values': [ ... <value of output for the corresponding instrument in the 'names' list> ... ],
#                                       'percentiles': [
#                                            {
#                                                'rank': <percentile rank e.g. 0.25 (equivalent to lower quartile)>,
#                                                'value': <percentile value>
#                                            }
#                                        ],
#                                        'minimum': {
#                                            'name': <instrument name e.g. 'VWP-C20'>,
#                                            'tip_name': <instrument tip name e.g. 'L1'>,
#                                            'value': <minimum value of output>
#                                         },
#                                        'maximum': {
#                                            'name': <instrument name e.g. 'VWP-C20'>,
#                                            'tip_name': <instrument tip name e.g. 'L1'>,
#                                            'value': <maximum value of output>
#                                        }
#                                    }
#                                    'output_magnitude2': {<fields as output_magnitude>},
#                                    'output_magnitude3': {<fields as output_magnitude>}
#                                }, ...
region_groups = {}
# Dictionary of instruments exceeding a trigger level. A list for a trigger level e.g. 'alert' is populated with
# instruments with readings which have exceeded that level, but not the level above it.
triggers = {
    "alert": [],
    "alarm": [],
    "action": []
}