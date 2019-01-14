import os
import logging
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    logger.info('Bot ready')


@bot.event
async def on_message(message):
    # read message contents and do something
    pass


@bot.command
async def ping(ctx):
    '''Display the current latency.'''
    await ctx.send(bot.latency)


bot.run(os.getenv('BOT_TOKEN'))
