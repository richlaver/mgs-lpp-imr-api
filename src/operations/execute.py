# Function to execute type-specific operations defined in the operations.instruments modules
# ==========================================================================================
from importlib import import_module
from pathlib import Path
import os
from re import compile, search


def findRequestedOutput() -> None:
    """
    **findRequestedOutput** Execute functions to find requested output that are specific to the instrument type. The type-specific functions are defined in a dedicated module of operations called instruments.
    """
    # Hidden files are prefixed and suffixed by '__'.
    hiddenfile_pattern = compile('__\S*__')
    for name in os.listdir(str(Path(__file__).parents[0].joinpath('instruments'))):
        if not os.path.isdir(str(Path(__file__).parents[0].joinpath('instruments', name))):
            continue
        # Skip hidden files.
        if bool(search(hiddenfile_pattern, name)):
            continue
        module = import_module('src.operations.instruments.' + name + '.periodoutput')
        yield from module.processData()