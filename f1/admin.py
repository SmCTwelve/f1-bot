'''Administrator restricted commands.'''
import logging
from discord.ext import commands

from f1.commands import bot

logger = logging.getLogger(__name__)


@bot.command()
@commands.is_owner()
async def stop(ctx):
    '''Stop the running bot process.

    The worker will be shutdown making the bot unavailable. It must be manually
    started again from the host.
    '''
    pass


@bot.command()
@commands.is_owner()
async def restart(ctx):
    '''Command the worker process to restart.

    The bot will be temporarily unavailable as the dyno reboots. A ready message
    will be posted when the bot can receive commands again.
    '''
    pass


@bot.command()
@commands.is_owner()
async def status(ctx, *args):
    '''Current worker status. Returns the worker process, dyno hours, uptime.'''
    pass
