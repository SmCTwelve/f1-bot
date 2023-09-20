import os
import sys
import logging
import warnings
from pathlib import Path
from typing import List
from configparser import ConfigParser

import fastf1
from bs4 import XMLParsedAsHTMLWarning
from discord import Intents
from discord.ext import commands

logger = logging.getLogger('f1-bot')

# Root directory of the bot
BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))

# Path to config file
if Path.exists(BASE_DIR.joinpath('config.local.ini')):
    CONFIG_FILE = BASE_DIR.joinpath('config.local.ini')
else:
    CONFIG_FILE = BASE_DIR.joinpath('config.ini')

# Image and text assets
ASSET_DIR = BASE_DIR.joinpath('assets')

# Where to store static cache files
CACHE_DIR = BASE_DIR.joinpath('cache')

# Logs output
LOG_DIR = BASE_DIR.joinpath('logs')
LOG_FILE = LOG_DIR.joinpath('f1-bot.log')

# Version
VERSION = BASE_DIR.joinpath('version.txt')


class Config:
    """Creates a singleton for the parsed config settings and bot client instance."""

    _instance = None

    # Constructor setup
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = cls._instance._load_config()
            cls._instance.guilds = cls._instance._get_guilds()
            cls._instance.bot = cls._instance._setup_bot()
            with open(VERSION) as f:
                cls._instance.version = f.readline()
        return cls._instance

    # Initialise instance with accessible API
    def __init__(self):
        self.settings: ConfigParser
        self.guilds: List[int] | None
        self.bot: commands.Bot
        self.version: str

    def _create_output_and_data_dir(self):
        # Check directories, will skip if they exist
        Path.mkdir(ASSET_DIR, parents=True, exist_ok=True)
        Path.mkdir(CACHE_DIR, parents=True, exist_ok=True)
        Path.mkdir(LOG_DIR, parents=True, exist_ok=True)

    def _setup_bot(self):
        # Message contents needed for any prefix commands
        intents = Intents.default()
        intents.message_content = True

        # Instantiate a single bot instance
        bot = commands.Bot(
            command_prefix=f"{self.settings['BOT']['PREFIX']}f1 ",
            guilds=self.guilds,
            debug_guilds=self._get_guilds(debug=True),
            help_command=commands.DefaultHelpCommand(dm_help=True),
            case_insensitive=True,
            intents=intents
        )
        return bot

    def _get_guilds(self, debug=False):
        # Used for syncing slash commands instantly and limit bot scope
        list_str = self.settings.get('GUILDS', 'LIST' if not debug else 'DEBUG')
        if len(list_str) == 0:
            return None
        # Basic parsing of comma separated list of guilds
        return [int(s.strip()) for s in list_str.split(',')]

    def _load_config(self):
        try:
            with CONFIG_FILE.open() as f:
                parsed = ConfigParser()
                parsed.read_file(f)
                logger.info('Config loaded!')

                # Verify directory structure
                self._create_output_and_data_dir()

                # Enable FastF1 caching
                fastf1.Cache.enable_cache(CACHE_DIR)

                # logging
                cfg_level = parsed['LOGGING']['LEVEL']
                if cfg_level == 'DEBUG':
                    level = logging.DEBUG
                elif cfg_level == 'WARNING':
                    level = logging.WARNING
                elif cfg_level == 'ERROR':
                    level = logging.ERROR
                else:
                    level = logging.INFO

                # Base logger config
                logger.propagate = False
                logger.setLevel(level)
                formatter = logging.Formatter('%(asctime)s %(name)s: %(levelname)8s %(message)s')

                # stdout log handler
                console = logging.StreamHandler()
                console.setFormatter(formatter)
                logger.addHandler(console)

                # log to file
                file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

                discord_logger = logging.getLogger('discord')
                discord_logger.setLevel(logging.WARNING)
                discord_logger.addHandler(file_handler)

                # FastF1 logger config
                if level == logging.DEBUG:
                    fastf1.set_log_level(logging.INFO)
                else:
                    fastf1.set_log_level(logging.WARNING)

                # suppress BS4 warning
                warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

                return parsed

        except OSError:
            logging.critical(
                f'Could not load config.ini file at {CONFIG_FILE}, check it exists (rename example.config.ini).')
            sys.exit(0)
