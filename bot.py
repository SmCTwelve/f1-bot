import logging

import f1.config
from f1 import commands  # noqa


logger = logging.getLogger(__name__)
logger.warn('Starting bot...')


commands.bot.run(f1.config.CONFIG['BOT']['TOKEN'])
