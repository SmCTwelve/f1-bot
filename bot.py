import logging
import os

import f1.config
from f1 import commands  # noqa


logger = logging.getLogger(__name__)
logger.warn('Starting bot...')


commands.bot.run(os.getenv('BOT_TOKEN', f1.config.CONFIG['BOT']['TOKEN']))
