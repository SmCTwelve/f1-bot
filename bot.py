import logging
import dotenv
import os

from f1.config import load_config
from f1 import commands  # noqa
from f1 import admin  # noqa

dotenv.load_dotenv()
load_config()

logger = logging.getLogger(__name__)
logger.warn('Starting bot...')

commands.bot.run(os.getenv('BOT_TOKEN'))
