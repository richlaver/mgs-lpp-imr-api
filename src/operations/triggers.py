# Function finding trigger-level exceedances.
# ===========================================
from operator import itemgetter
from src.operations.instruments.inclinometer.typecodes import typeCodes
from src.operations.count import countInstruments
from src.data.data import instruments, triggers


def findIncExceedances(triggers_data: dict) -> None:
    """
    **findIncExceedances** Find absolute magnitudes of inclinometer displacement which exceed defined trigger levels at the end of the requested period. Instruments with movements exceeding a trigger level are recorded in the triggers dictionary.

    :param triggers_data: Dictionary defining trigger levels for instruments. The dictionary should be structured as follows: {<type code>: {'alert': <alert level>, 'alarm': <alarm level>, 'action': <action level>}, ... }
    :type triggers_data: dict
    """
    num_instruments = countInstruments(typeCodes=typeCodes())
    # Initialise a count of inclinometers.
    instrument_count = 0
    for typecode in typeCodes():
        trigger_levels = [(trigger_name, trigger_value) for trigger_name, trigger_value in triggers_data[typecode].items()]
        # Sorting the trigger levels by the trigger value is necessary to record each exceeding inclinometer only once
        # in the hierarchy of trigger level exceedances. For instance, an inclinometer exceeding the alarm level will
        # not be listed in the list of inclinometers exceeding the alert level below.
        trigger_levels.sort(key=itemgetter(1))
        for instrument in instruments.values():
            if instrument.type_name != typecode:
                continue
            for output in instrument.outputs:
                # Only the value at the end of the requested period is compared with the trigger levels.
                if output.name != 'absolute_end':
                    continue
                # Initialise the trigger status. If a trigger level is exceeded, this will be the name of the trigger
                # level e.g. 'alert', otherwise it will be None.
                trigger_status = None
                for trigger_level in trigger_levels:
                    if output.output_magnitude < trigger_level[1]:
                        break
                    trigger_status = trigger_level[0]
                if trigger_status is not None:
                    triggers[trigger_status].append(instrument)
                break
            instrument_count += 1
            yield f'Finding inclinometer trigger level exceedances. Searched {instrument_count} inclinometers...', 0, num_instruments, instrument_count