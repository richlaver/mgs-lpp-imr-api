# Functions to read and write JSON files
# ======================================
from json import dump, load


def readJSON(filepath: str) -> dict:
    """
    **readJSON** Reads JSON-formatted data from a file into a dictionary.

    :param filepath: File path to the JSON file to be read.
    :type filepath: str
    :return: Dictionary containing the read data.
    """
    with open(file=filepath, mode='r') as json_file:
        info = load(json_file)
    return info

def writeJSON(filepath: str, data) -> None:
    """
    **writeJSON** Writes data from a dictionary into a file in JSON format.

    :param filepath: File path to the JSON file to be written.
    :type filepath: str
    :param data: Dictionary containing the data to write.
    :type data: dict
    """
    with open(file=filepath, mode='w') as json_file:
        dump(data, json_file, indent=4, sort_keys=True)