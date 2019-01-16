import logging
import os

from f1 import commands  # noqa

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(name)s] %(levelname)s: %(message)s'
)

commands.bot.run(os.getenv('BOT_TOKEN'))
