import shutil
import logging
from pathlib import Path

from main import RUNNING
from f1.config import CACHE_DIR


"""Delete the contents of the ./cache directory.

Ensure the bot is not running. A new cache will be built when starting the bot.
"""

logger = logging.getLogger("f1-bot")

if __name__ == "__main__":

    if RUNNING:
        logger.warning("Bot is running. Exit the process or use /stop command.")
        exit()

    if Path.exists(CACHE_DIR):
        logger.warning("Removing cache directory...")
        try:
            shutil.rmtree(CACHE_DIR)
        except Exception as err:
            logger.error(f"Error removing cache\n{err}")
            exit()

        logger.info("Cache removed successfully!\nStart the bot with python -m main.py to build a new cache.")
        exit()
