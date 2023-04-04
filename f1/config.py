import os
from pathlib import Path
import sys
import logging
from configparser import ConfigParser
from discord import Intents
from discord.ext import commands

# Root directory of the bot
BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))

# Path to config file
CONFIG_FILE = BASE_DIR.joinpath('config.ini')

# Output directory for temp files, like plot images
OUT_DIR = BASE_DIR.joinpath('out')

# Where to store static data files
DATA_DIR = BASE_DIR.joinpath('data')

# Logs output
LOG_DIR = BASE_DIR.joinpath('logs')
LOG_FILE = LOG_DIR.joinpath('f1-bot.log')


class Config:
    """Creates a singleton for the parsed config settings and bot client instance."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.settings = cls._instance._load_config()
            cls._instance.bot = cls._instance._setup_bot()
        return cls._instance

    def __init__(self):
        pass

    def _create_output_and_data_dir(self):
        try:
            Path.mkdir(OUT_DIR, parents=True, exist_ok=True)
            Path.mkdir(DATA_DIR, parents=True, exist_ok=True)
            Path.mkdir(LOG_DIR, parents=True, exist_ok=True)
        except FileExistsError:
            logging.info("Output directory already exists, skipping.")

    def _setup_bot(self):
        intents = Intents.default()
        bot = commands.Bot(
            command_prefix=f"{self.settings['BOT']['PREFIX']}f1 ",
            help_command=commands.DefaultHelpCommand(dm_help=True),
            case_insensitive=True,
            intents=intents
        )
        return bot

    def _load_config(self):
        try:
            with CONFIG_FILE.open() as f:
                parsed = ConfigParser()
                parsed.read_file(f)
                logging.info('Config loaded!')
                self._create_output_and_data_dir()

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

                return parsed

        except OSError:
            logging.critical(f'Could not load config.ini file at {CONFIG_FILE}, check it exists.')
            sys.exit(0)
