# flake8: noqa
import os
import sys
import logging
import configparser

logger = logging.getLogger(__name__)

CONFIG = configparser.ConfigParser()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_DIR, 'config.ini')

OUT_DIR = os.path.join(BASE_DIR, 'out')


def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            CONFIG.read_file(f)
            logger.info('Config loaded!')
            print(CONFIG['BOT']['TOKEN'])
    except IOError:
        logger.critical('Could not load config.ini file, check it exists.')
        sys.exit(0)


load_config()
