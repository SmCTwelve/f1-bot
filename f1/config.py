import os
from pathlib import Path
import sys
import logging
import configparser

# Dict parsed from config file
CONFIG = configparser.ConfigParser()

# Root directory of the bot
BASE_DIR = Path(os.path.realpath(os.path.dirname(__file__)))

# Path to config file
CONFIG_FILE = BASE_DIR.joinpath('config.ini')

# Output directory for temp files, like plot images
OUT_DIR = BASE_DIR.joinpath('out')

# Where to store static data files
DATA_DIR = BASE_DIR.joinpath('data')

# Logs output
LOG_DIR = BASE_DIR.joinpath('logs')
LOG_FILE = LOG_DIR.joinpath('f1-bot.log')


def create_output_and_data_dir():
    try:
        Path.mkdir(OUT_DIR, parents=True, exist_ok=True)
        Path.mkdir(DATA_DIR, parents=True, exist_ok=True)
        Path.mkdir(LOG_DIR, parents=True, exist_ok=True)
    except FileExistsError:
        logging.info("Output directory already exists, skipping.")


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            CONFIG.read_file(f)
            logging.info('Config loaded!')
            create_output_and_data_dir()

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

            # Base logger config
            logger = logging.getLogger("f1-bot")
            logger.setLevel(level)
            formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

            # stdout log handler
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.addHandler(console)

            # log to file
            file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            discord_log = logging.getLogger("discord")
            discord_log.addHandler(console)

    except IOError:
        logging.critical(f'Could not load config.ini file at {CONFIG_FILE}, check it exists.')
        sys.exit(0)
