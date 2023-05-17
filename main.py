import logging
import dotenv
import os

from f1.config import Config
from f1 import commands  # noqa

dotenv.load_dotenv()
cfg = Config()

logger = logging.getLogger("f1-bot")
logger.warning("Starting bot...")

cfg.bot.run(os.getenv("BOT_TOKEN"))
