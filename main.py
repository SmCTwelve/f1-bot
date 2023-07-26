import logging
import dotenv
import os

from f1.config import Config

# If the bot is active
RUNNING = False

if __name__ == "__main__":

    dotenv.load_dotenv()
    cfg = Config()

    logger = logging.getLogger("f1-bot")
    logger.warning("Starting bot...")

    from f1 import commands  # noqa

    cfg.bot.run(os.getenv("BOT_TOKEN"))

    RUNNING = True
