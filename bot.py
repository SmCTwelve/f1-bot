import logging
import dotenv
import os

from f1 import commands  # noqa
from f1 import admin  # noqa


logger = logging.getLogger(__name__)
logger.warn('Starting bot...')

dotenv.load_dotenv()

commands.bot.run(os.getenv('BOT_TOKEN'))
