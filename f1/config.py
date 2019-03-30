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

# Output directory for temp files, like plot images
OUT_DIR = os.path.join(BASE_DIR, 'out')

# Where to store static data files
DATA_DIR = os.path.join(BASE_DIR, 'data')


def create_output_dir():
    try:
        os.mkdir(OUT_DIR)
        logger.info(f"Created output directory at {OUT_DIR}.")
    except FileExistsError:
        logger.info(f"Output directory already exists at {OUT_DIR}.")


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            CONFIG.read_file(f)
            logger.info('Config loaded!')
            create_output_dir()

            # logging
            cfg_level = CONFIG['LOGGING']['LEVEL']
            if cfg_level == 'DEBUG':
                level = logging.DEBUG
            elif cfg_level == 'WARNING':
                level = logging.WARNING
            elif cfg_level == 'ERROR':
                level = logging.ERROR
            else:
                level = logging.INFO

            logging.basicConfig(
                level=level,
                format='[%(asctime)s][%(name)s] %(levelname)s: %(message)s'
            )
    except IOError:
        logger.critical(f'Could not load config.ini file at {CONFIG_FILE}, check it exists.')
        sys.exit(0)


load_config()
