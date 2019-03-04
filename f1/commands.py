import logging
from discord import Colour
from discord.activity import Activity, ActivityType
from discord.embeds import Embed
from discord.ext import commands

from f1 import api
from f1.config import CONFIG
from f1.utils import is_future, make_table

logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix=CONFIG['BOT']['PREFIX'])


async def check_season(ctx, season):
    """Raise error if the given season is in the future."""
    if is_future(season):
        await ctx.send("Can't predict future :thinking:")
        raise commands.BadArgument('Given season is in the future.')


@bot.event
async def on_ready():
    logger.info('Bot ready...')
    job = Activity(name=f'{bot.command_prefix}f1', type=ActivityType.watching)
    await bot.change_presence(activity=job)


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
    """Display the current latency."""
    await ctx.send(bot.latency)


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    """Command group of all F1 related commands.

    Function is only called when the invoked command does not match one of the subcommands
    in `f1.commands`. Otherwise context and args are passed down to the approriate subcommand.
    """
    await ctx.send(f'Command not recognised: {ctx.prefix}{ctx.command}. Type `!help f1`.')


@f1.command(aliases=['wdc'])
async def drivers(ctx, season='current'):
    """Display the Driver Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 drivers             Current WDC standings as of last race.
        !f1 drivers <season>    WDC standings from <season>.
    """
    await check_season(ctx, season)
    result = await api.get_driver_standings(season)
    table = make_table(result['data'])
    await ctx.send(
        f"**World Driver Championship**\n" +
        f"Season: {result['season']} Round: {result['round']}\n"
    )
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['teams', 'wcc'])
async def constructors(ctx, season='current'):
    """Display Constructor Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 constructors            Current WCC standings as of the last race.
        !f1 constructors [season]   WCC standings from [season].
    """
    await check_season(ctx, season)
    result = await api.get_team_standings(season)
    table = make_table(result['data'])
    await ctx.send(
        f"**World Constructor Championship**\n" +
        f"Season: {result['season']} Round: {result['round']}\n"
    )
    await ctx.send(f"```\n{table}\n```")


@f1.command()
async def grid(ctx, season='current'):
    """Display all the drivers and teams participating in the current season or `season`.

    Usage:
    ------
        !f1 grid            All drivers and teams in the current season as of last race.
        !f1 grid [season]   All drivers and teams at the end of [season].
    """
    await check_season(ctx, season)
    result = await api.get_all_drivers_and_teams(season)
    # Use simple table to not exceed content limit
    table = make_table(result['data'], fmt='simple')
    await ctx.send(
        f"**Formula 1 {result['season']} Grid**\n" +
        f"Round: {result['round']}\n"
    )
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['calendar', 'schedule'])
async def races(ctx, *args):
    """Display the full race schedule for the current season."""
    result = await api.get_race_schedule()
    # Use simple table to not exceed content limit
    table = make_table(result['data'], fmt='simple')
    await ctx.send(f"**{result['season']} Formula 1 Race Calendar**\n")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['timer', 'next'])
async def countdown(ctx, *args):
    """Display an Embed with details and countdown to the next calendar race."""
    # ## TODO - Display thumbnail for circuits ##

    result = await api.get_next_race()
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


@f1.command(aliases=['times', 'laps'])
async def timings(ctx, rnd='last', filter=None):
    """Display fastest lap times and delta per driver for `round`.

    If no `round` specified returns results for the most recent race.

    Usage:
    ---------------
        !f1 timings [<round>]           Return all fastet laps.
        !f1 timings [<round>] [filter]  Return fastet laps sorted by [filter].

    Optional filter:
    ---------------
    `fastest` -  Only show the fastest lap of the race.
    `slowest` -  Only show the slowest lap of the race.
    `top`     -  Top 5 fastest drivers.
    `bottom`  -  Bottom 5 slowest drivers.
    """
    results = await api.get_race_results(rnd, season='current')
    filtered = await api.rank_lap_times(results, filter)
    table = make_table(filtered)
    await ctx.send(f"**Fastest laps ranked {filter}**")
    await ctx.send(f"{results['season']} {results['race']}")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['finish', 'result'])
async def results(ctx, rnd='last', season='current'):
    """Results for race `round`. Default most recent.

    Displays an embed with details about the race event and wikipedia link. Followed by table
    of results. Data includes finishing position, fastest lap, finish status, pit stops per driver.

    Usage:
    ------
        !f1 results                     Results for last race.
        !f1 results [round]             Results for [round] in current season.
        !f1 results [round] [season]    Results for [round] in [season].
    """
    await check_season(ctx, season)
    result = await api.get_race_results(rnd, season)
    table = make_table(result['data'], fmt='simple')
    embed = Embed(
        title=f"{result['season']} {result['race']} Race",
        url=result['url'],
        colour=Colour.dark_blue(),
        description=f"```\n{table}\n```",
    )
    await ctx.send(embed=embed)


@f1.command(aliases=['qual', 'quali'])
async def qualifying(ctx, rnd='last', season='current'):
    """Qualifying results for `round`. Defaults to latest.

    Includes best Q1, Q2 and Q3 times per driver.

    Usage:
    ------
        !f1 quali                    Latest results.
        !f1 quali [round]            Results for [round] in current season.
        !f1 quali [round] [season]   Results for [round] in [season].
    """
    await check_season(ctx, season)
    result = await api.get_qualifying_results(rnd, season)
    table = make_table(result['data'])
    embed = Embed(
        title=f"{result['season']} {result['race']} Qualifying",
        url=result['url'],
        colour=Colour.dark_blue(),
        description=f"```\n{table}\n```",
    )
    await ctx.send(embed=embed)


@f1.command(aliases=['driver'])
async def career(ctx, driver_id):
    """Career stats for the `driver_id`.

    Includes total poles, wins, points, seasons, teams, fastest laps, and DNFs.

    Parameters:
    -----------
    `driver_id`
        Supported Ergast API ID, e.g. 'alonso', 'michael_schumacher', 'vettel', 'di_resta'.

    Usage:
    --------
        !f1 career vettel     Get career stats for Sebastian Vettel.
    """
    # TODO - support JSON file to convert driver codes/names to ID's for easier use
    result = await api.get_driver_career(driver_id)
    season_list = result['data']['Seasons']['years']
    embed = Embed(
        title=f"{result['driver']['firstname']} {result['driver']['surname']} Career",
        url=result['driver']['url'],
        colour=Colour.dark_blue(),
    )
    embed.add_field(name='No.', value=result['driver']['number'], inline=False)
    embed.add_field(name='Nationality', value=result['driver']['nationality'], inline=False)
    embed.add_field(name='Age', value=result['driver']['age'], inline=True)
    embed.add_field(name='Wins', value=result['data']['Wins'], inline=True)
    embed.add_field(name='Poles', value=result['data']['Poles'], inline=True)
    embed.add_field(
        name='Championships',
        # Total and list of seasons
        value=f"{result['data']['Championships']['total']} ({result['data']['Championships']['years']})",
        inline=True
    )
    embed.add_field(
        name='Seasons',
        # Total and start to latest season
        value=f"{result['data']['Seasons']['total']} ({season_list[0]}-{season_list[len(season_list)-1]})",
        inline=True
    )
    embed.add_field(
        name='Teams',
        # Total and list of teams
        value=f"{result['data']['Teams']['total']} ({result['data']['Teams']['names']})",
        inline=True
    )
    await ctx.send(embed=embed)
