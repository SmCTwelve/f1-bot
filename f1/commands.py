import logging
from discord.embeds import Embed
from discord.ext import commands

from f1 import data, utils

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    logger.info('Bot ready')


@bot.event
async def on_command(ctx):
    logger.info(f'Command: {ctx.prefix} {ctx.command} {ctx.invoked_subcommand}')


@bot.event
async def on_command_error(ctx, err):
    logger.error(f'Command failed: {ctx.prefix} {ctx.command} {ctx.invoked_subcommand}\n {err}')


@bot.command
async def ping(ctx):
    '''Display the current latency.'''
    await ctx.send(bot.latency)


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    '''Commands to get F1 data. Invoke with !f1.'''
    await ctx.send('Command not recognised. Type !f1 help.')


@f1.command(aliases=['wdc'])
async def drivers(ctx, *args):
    '''Display the current Driver Championship standings as of the last race.'''
    result = await data.get_driver_standings()
    if result:
        table = utils.make_table(result['data'])
        await ctx.send(
            (
                f"World Driver Championship\n"
                f"Season: {result['season']} Round: {result['round']}\n"
                f"```\n{table}\n```"
            )
        )
    else:
        logger.warning('Unable to get driver data. Command will do nothing.')


@f1.command(aliases=['teams', 'wcc'])
async def constructors(ctx, *args):
    '''Display the current Constructor Championship standings as of the last race.'''
    result = await data.get_team_standings()
    if result:
        table = utils.make_table(result['data'])
        await ctx.send(
            (
                f"World Constructor Championship\n"
                f"Season: {result['season']} Round: {result['round']}\n"
                f"```\n{table}\n```"
            )
        )
    else:
        logger.warning('No constructor data available. Command will do nothing.')


@f1.command
async def grid(ctx, *args):
    '''Display all the drivers and teams participating in the current season.'''
    result = await data.get_all_drivers_and_teams()
    if result:
        table = utils.make_table(result['data'])
        await ctx.send(
            (
                f"Formula 1 Grid {result['season']}\n"
                f"```\n{table}\n```"
            )
        )
    else:
        logger.warning('Could not access grid data. Command will do nothing.')


@f1.command(aliases=['calendar', 'schedule'])
async def races(ctx, *args):
    '''Display the full race schedule for the current season.'''
    result = await data.get_race_schedule()
    if result:
        table = utils.make_table(result['data'])
        await ctx.send(
            (
                f"Formula 1 Race Calendar {result['season']}\n"
                f"```\n{table}\n```"
            )
        )
    else:
        logger.warn('Race schedule unavailable. Result was None.')


@f1.command(aliases=['timer', 'next'])
async def countdown(ctx, *args):
    '''Display details of the next race on the calendar and a countdown.'''
    result = await data.get_next_race()
    if result:
        embed = Embed(title=f"Next Race {result['season']}", description=f"**{result['countdown']}**")
        embed.add_field(name='Round', value=result['data']['Round'], inline=True)
        embed.add_field(name='Name', value=result['data']['Name'], inline=True)
        embed.add_field(name='Country', value=result['data']['Country'], inline=True)
        embed.add_field(name='Circuit', value=result['data']['Circuit'])
        embed.add_field(name='Date', value=result['data']['Date'], inline=True)
        embed.add_field(name='Time', value=result['data']['Time'], inline=True)
        await ctx.send(embed=embed)
    else:
        logger.warning('Could not fetch next race. Nothing returned.')
