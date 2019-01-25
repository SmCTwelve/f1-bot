import logging
from discord import Colour
from discord.activity import Activity, ActivityType
from discord.embeds import Embed
from discord.ext import commands

from f1 import api, utils

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    logger.info('Bot ready...')
    job = Activity(name='!f1', type=ActivityType.watching)
    bot.change_presence(activity=job)


@bot.event
async def on_command(ctx):
    channel = ctx.message.channel
    user = ctx.message.author
    logger.info(f'Command: {ctx.prefix}{ctx.command} in {channel} by {user}')


@bot.event
async def on_command_error(ctx, err):
    logger.error(f'Command failed: {ctx.prefix}{ctx.command}\n {err}')


@bot.command()
async def ping(ctx, *args):
    '''Display the current latency.'''
    await ctx.send(bot.latency)


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    '''Command group of all F1 related commands.

    Function is only called when the invoked command does not match one of the subcommands
    in `f1.commands`. Otherwise context and args are passed down to the approriate subcommand.
    '''
    await ctx.send(f'Command not recognised: {ctx.prefix}{ctx.command}. Type `!help f1`.')


@f1.command(aliases=['wdc'])
async def drivers(ctx, season='current'):
    '''Display the Driver Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 drivers             Current WDC standings as of last race.
        !f1 drivers <season>    WDC standings from <season>.
    '''
    result = await api.get_driver_standings(season)
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
async def constructors(ctx, season='current'):
    '''Display Constructor Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 constructors            Current WCC standings as of the last race.
        !f1 constructors [season]   WCC standings from [season].
    '''
    result = await api.get_team_standings(season)
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
async def grid(ctx, season='current'):
    '''Display all the drivers and teams participating in the current season or `season`.

    Usage:
    ------
        !f1 grid            All drivers and teams in the current season as of last race.
        !f1 grid [season]   All drivers and teams at the end of [season].
    '''
    result = await api.get_all_drivers_and_teams(season)
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
    result = await api.get_race_schedule()
    if result:
        # Use simple table to not exceed content limit
        table = utils.make_table(result['data'], fmt='simple')
        await ctx.send(f"**{result['season']} Formula 1 Race Calendar**\n")
        await ctx.send(f"```\n{table}\n```")
    else:
        logger.warn('Race schedule unavailable. Result was None.')


@f1.command(aliases=['timer', 'next'])
async def countdown(ctx, *args):
    '''Display an Embed with details and countdown to the next calendar race.'''
    # ## TODO - Display thumbnail for circuits ##

    result = await api.get_next_race()
    if result:
        embed = Embed(
            title=f"**{result['data']['Name']}**",
            description=f"{result['countdown']}",
            url=result['url'],
            colour=Colour.dark_blue(),
        )
        # placeholder
        embed.set_thumbnail(url='https://i.imgur.com/1tpFlpv.jpg')
        embed.add_field(name='Circuit', value=result['data']['Circuit'], inline=False)
        embed.add_field(name='Round', value=result['data']['Round'], inline=True)
        embed.add_field(name='Country', value=result['data']['Country'], inline=True)
        embed.add_field(name='Date', value=result['data']['Date'], inline=True)
        embed.add_field(name='Time', value=result['data']['Time'], inline=True)
        await ctx.send(embed=embed)
    else:
        logger.warning('Could not fetch next race. Nothing returned.')


@f1.command(aliases=['times', 'laps'])
async def timings(ctx, rnd='last', *args):
    '''Display fastest lap times and delta per driver for `round`.

    If no `round` specified returns results for the most recent race.

    Optional param:
    ---------------
    `fastest` -  Only show the fastest lap of the race.
    `slowest` -  Only show the slowest lap of the race.
    `top`     -  Top 5 fastest drivers.
    `bottom`  -  Bottom 5 slowest drivers.
    '''
    await ctx.send('no')


@f1.command(aliases=['finish', 'result'])
async def results(ctx, rnd='last', season='current'):
    '''Results for race `round`. Default most recent.

    Data includes finishing position, fastest lap, finish status, pit stops per driver.

    Usage:
    ------
        !f1 results                     Results for last race.
        !f1 results [round]             Results for [round] in current season.
        !f1 results [round] [season]    Results for [round] in [season].
    '''
    await ctx.send('no')


@f1.command(aliases=['qual', 'quali'])
async def qualifying(ctx, rnd='last', season='current'):
    '''Qualifying results for `round`. Defaults to latest.

    Includes best Q1, Q2 and Q3 times per driver.

    Usage:
    ------
        !f1 quali                    Latest results.
        !f1 quali [round]            Results for [round] in current season.
        !f1 quali [round] [season]   Results for [round] in [season].
    '''
    pass


@f1.command(aliases=['driver'])
async def career(ctx, driver):
    '''Career stats for the `driver` (code).

    Includes total poles, wins, points, seasons, teams, fastest laps, and DNFs.

    Usage:
    --------
        !f1 career VET     Get career stats for Vettel (code VET).
    '''
    await ctx.send('no')
