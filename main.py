import logging
import dotenv
import os

from f1.config import Config

dotenv.load_dotenv()
cfg = Config()

logger = logging.getLogger(__name__)
logger.warn('Starting bot...')

cfg.bot.run(os.getenv('BOT_TOKEN'))
