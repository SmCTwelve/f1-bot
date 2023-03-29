import os
import sys
import logging
import configparser

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

# Logs output
LOG_DIR = os.path.join(DATA_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'f1-bot.log')


def create_output_and_data_dir():
    try:
        os.mkdir(OUT_DIR)
        os.mkdir(DATA_DIR)
        os.makedirs(LOG_FILE)
    except FileExistsError:
        logging.info("Output directory already exists, skipping.")
    finally:
        logging.info("Finished setting up directories /out, /data and /logs")


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

            logger = logging.getLogger("f1-bot")
            logger.setLevel(level)
            formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.addHandler(console)

            file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            discord_log = logging.getLogger("discord")
            discord_log.addHandler(console)

    except IOError:
        logging.critical(f'Could not load config.ini file at {CONFIG_FILE}, check it exists.')
        sys.exit(0)
