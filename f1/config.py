# flake8: noqa
import os
import sys
import logging
import configparser

logger = logging.getLogger(__name__)

# Dict parsed from config file
CONFIG = configparser.ConfigParser()

# Root directory of the bot
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to config file
CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')

# Output directory, for plot images
OUT_DIR = os.path.join(BASE_DIR, 'out')


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            CONFIG.read_file(f)
            logger.info('Config loaded!')
    except IOError:
        logger.critical(f'Could not load config.ini file at {CONFIG_FILE}, check it exists.')
        sys.exit(0)


load_config()
