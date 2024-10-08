# logging_setup.py
import logging
from os import makedirs, path

def setup_logging(write_path, runtime):
    if not path.exists(write_path):
        makedirs(write_path)

    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    logger.addHandler(logging.FileHandler(f'{write_path}/RunLog-{runtime}.log', 'a'))
    return logger
