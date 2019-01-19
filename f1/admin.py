'''Administrator restricted commands.'''
import logging

from f1.commands import bot

logger = logging.getLogger(__name__)


@bot.command
async def stop(ctx):
    '''Stop the running bot process.

    The worker will be shutdown making the bot unavailable. It must be manually
    started again from the host.
    '''
    pass


@bot.command
async def restart(ctx):
    '''Command the worker process to restart.

    The bot will be temporarily unavailable as the dyno reboots. A ready message
    will be posted when the bot can receive commands again.
    '''
    pass
