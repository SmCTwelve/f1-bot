import logging
from discord import Colour
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
    logger.info(f'Command: {ctx.prefix}{ctx.command}')


@bot.event
async def on_command_error(ctx, err):
    logger.error(f'Command failed: {ctx.prefix}{ctx.command}\n {err}')


@bot.command()
async def ping(ctx, *args):
    '''Display the current latency.'''
    await ctx.send(bot.latency)


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    '''Commands to get F1 data. Invoke with !f1.'''
    await ctx.send('Command not recognised. Type !help f1.')


@f1.command(aliases=['wdc'])
async def drivers(ctx, *args):
    '''Display the current Driver Championship standings as of the last race.'''
    result = await data.get_driver_standings()
    if result:
        table = utils.make_table(result['data'])
        await ctx.send(
            f"**World Driver Championship**\n" +
            f"Season: {result['season']} Round: {result['round']}\n"
        )
        await ctx.send(f"```\n{table}\n```")
    else:
        logger.warning('Unable to get driver data. Command will do nothing.')


@f1.command(aliases=['teams', 'wcc'])
async def constructors(ctx, *args):
    '''Display the current Constructor Championship standings as of the last race.'''
    result = await data.get_team_standings()
    if result:
        table = utils.make_table(result['data'])
        await ctx.send(
            f"**World Constructor Championship**\n" +
            f"Season: {result['season']} Round: {result['round']}\n"
        )
        await ctx.send(f"```\n{table}\n```")
    else:
        logger.warning('No constructor data available. Command will do nothing.')


@f1.command()
async def grid(ctx, *args):
    '''Display all the drivers and teams participating in the current season.'''
    result = await data.get_all_drivers_and_teams()
    if result:
        # Use simple table to not exceed content limit
        table = utils.make_table(result['data'], fmt='simple')
        await ctx.send(
            f"**Formula 1 {result['season']} Grid**\n" +
            f"Round: {result['round']}\n"
        )
        await ctx.send(f"```\n{table}\n```")
    else:
        logger.warning('Could not access grid data. Command will do nothing.')


@f1.command(aliases=['calendar', 'schedule'])
async def races(ctx, *args):
    '''Display the full race schedule for the current season.'''
    result = await data.get_race_schedule()
    if result:
        # Use simple table to not exceed content limit
        table = utils.make_table(result['data'], fmt='simple')
        await ctx.send(f"**{result['season']} Formula 1 Race Calendar**\n")
        await ctx.send(f"```\n{table}\n```")
    else:
        logger.warn('Race schedule unavailable. Result was None.')


# ## TODO - Display thumbnail for circuits ##
@f1.command(aliases=['timer', 'next'])
async def countdown(ctx, *args):
    '''Display details of the next race on the calendar and a countdown.'''
    result = await data.get_next_race()
    if result:
        embed = Embed(
            title=f"{result['data']['Name']}",
            description=f"{result['countdown']}",
            url=result['url'],
            colour=Colour.dark_blue(),
        )
        # placeholder
        embed.set_thumbnail('https://i.imgur.com/1tpFlpv.jpg')
        embed.add_field(name='Circuit', value=result['data']['Circuit'])
        embed.add_field(name='Round', value=result['data']['Round'], inline=True)
        embed.add_field(name='Country', value=result['data']['Country'], inline=True)
        embed.add_field(name='Date', value=result['data']['Date'], inline=True)
        embed.add_field(name='Time', value=result['data']['Time'], inline=True)
        await ctx.send(embed=embed)
    else:
        logger.warning('Could not fetch next race. Nothing returned.')


@f1.command(aliases=['times', 'laps'])
async def timings(ctx, round='last', *args):
    '''Display fastest lap times and delta per driver for `round`.

    If no `round` number specified returns results for the most recent race.

    **Optional param**:
    `fastest` -  Only show the fastest lap of the race
    `slowest` -  Only show the slowest lap of the race
    `top`     -  Top 5 fastest drivers
    `bottom`  -  Bottom 5 slowest drivers
    '''
    await ctx.send('no')


@f1.command(aliases=['finish', 'result'])
async def results(ctx, round='last', *args):
    '''Results for race `round`. Default most recent.

    Data includes finishing position, fastest lap, finish status, pit stops per driver.

    **Optional param**:
    `quali` -   Show qualifying results with position and fastest Q1, Q2, Q3 time.
    '''
    await ctx.send('no')


@f1.command()
async def career(ctx, driver, *args):
    '''Career stats for the `driver`.

    Includes total poles, wins, points, seasons, teams, fastest laps, and DNFs.
    '''
    await ctx.send('no')
