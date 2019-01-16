import logging
from discord.ext import commands

from f1 import data

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix='!')


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
