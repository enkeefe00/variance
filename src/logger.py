import logging
from logging.config import fileConfig
from pathlib import Path

# Logging Setup
log_levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}

# Get path to the current Python source file
current_file_path = Path(__file__).resolve()

# Goes oustide 'src' directory
config_file_path = current_file_path.parent.parent / 'logging.conf'

# Check if the config file exists
if not config_file_path.exists():
    raise FileNotFoundError(f"logging.conf not found at '{config_file_path}'")

fileConfig(config_file_path)
logger = logging.getLogger()