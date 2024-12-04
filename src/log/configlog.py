# Function to configure logging
# =============================
import logging
import logging.config
import yaml


def configLog(filepath: str) -> None:
    """
    **configLog** Configure logging.

    :param filepath: File path to configuration file in YAML format.
    :type filepath: str
    """
    with open(file=filepath, mode='r') as file:
        config = yaml.safe_load(file.read())
        logging.config.dictConfig(config)