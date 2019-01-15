import os
import logging
from discord.ext import commands

import data

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix='!')


def contains(first, second):
    '''Returns true if any item in `first` matches an item in `second`.'''
    return any(i in first for i in second)


@bot.event
async def on_ready():
    logger.info('Bot ready')


@bot.command
async def ping(ctx):
    '''Display the current latency.'''
    await ctx.send(bot.latency)


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    await ctx.send('Command not recognised. Type !f1 help.')


@f1.command(aliases=['wdc'])
async def drivers(ctx, *args):
    result = await data.get_driver_standings()


@f1.command(aliases=['teams', 'wcc'])
async def constructors(ctx, *args):
    result = await data.get_team_standings()


@f1.command
async def grid(ctx, *args):
    result = await data.get_all_drivers_and_teams()


@f1.command(aliases=['calendar', 'schedule'])
async def races(ctx, *args):
    pass


@f1.command(aliases=['timer', 'next'])
async def countdown(ctx, *args):
    pass

bot.run(os.getenv('BOT_TOKEN'))
