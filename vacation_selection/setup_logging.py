# logging_setup.py
import logging
from os import makedirs, path

def setup_logging(filename="default.log", base=".\\output\\", debug=False):
    """Setup logging configuration."""
    if debug:
        loglevel=logging.DEBUG
    else:
        loglevel=logging.INFO
    full_log_path = path.abspath(path.join(base, filename))
    if not logging.getLogger().hasHandlers():  # Check if handlers already exist
        makedirs(base, exist_ok=True)
        logging.basicConfig(
            level=loglevel,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(full_log_path),
                logging.StreamHandler(),  # Optionally add console output
            ],
        )
    logging.info(f"Logging initialized: {full_log_path}")
    return logging.getLogger(filename)