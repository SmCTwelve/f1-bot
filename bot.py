import logging

from f1 import config
from f1 import commands  # noqa

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(name)s] %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)

logger.warn('Starting bot...')
commands.bot.run(config.CONFIG['BOT']['TOKEN'])
