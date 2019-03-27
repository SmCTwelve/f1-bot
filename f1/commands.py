import logging
import asyncio
import random
from operator import itemgetter
from discord import Colour, File
from discord.activity import Activity, ActivityType
from discord.embeds import Embed
from discord.ext import commands

from f1 import api
from f1.stats import chart
from f1.config import CONFIG, OUT_DIR
from f1.errors import DriverNotFoundError
from f1.utils import is_future, make_table, filter_times, rank_best_lap_times, rank_pitstops, filter_laps_by_driver


logger = logging.getLogger(__name__)

bot = commands.Bot(command_prefix=CONFIG['BOT']['PREFIX'])


async def check_season(ctx, season):
    """Raise error if the given season is in the future."""
    if is_future(season):
        await ctx.send(f"Can't predict future :thinking:")
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
    rng = random.randint(1, 60)
    # Catch TimeoutError
    if isinstance(err, asyncio.TimeoutError) or 'TimeoutError' in str(err):
        await ctx.send(f"Response timed out. Check `{bot.command_prefix}f1 status`.")
    # Catch DriverNotFoundError
    elif isinstance(err, DriverNotFoundError):
        await ctx.send("Could not find a matching driver. Check ID is correct.")
    # Catch all other errors
    else:
        await ctx.send(f"Command failed: {err.message if hasattr(err, 'message') else ''}")
        await ctx.send(f"Try `{bot.command_prefix}help f1 <command>` or check the Readme at <https://bit.ly/2tYRNSd>.")
    # Random chance to show img with error output if rng is multiple of 12
    if rng % 12 == 0:
        n = random.randint(1, 3)
        img = {1: 'https://i.imgur.com/xocNTde.jpg',
               2: 'https://i.imgur.com/morumoC.jpg',
               3: 'https://i.imgur.com/Cn8Gdh1.gifv'}
        await ctx.send(img[n])


@bot.command()
async def ping(ctx, *args):
    """Display the current latency."""
    await ctx.send(bot.latency)

# Main command group
# ==================


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    """Commands to get F1 data. Check the list of subcommands and usage at: https://bit.ly/2tYRNSd"""
    await ctx.send(f'Command not recognised: {ctx.prefix}{ctx.command}.\n' +
                   f'Type `{bot.command_prefix}help f1` or check the Readme at <https://bit.ly/2tYRNSd>.')


@f1.command(aliases=['source', 'git'])
async def github(ctx, *args):
    """Display a link to the GitHub repository."""
    await ctx.send("https://github.com/SmCTwelve/f1-bot")


@f1.command(aliases=['drivers', 'championship'])
async def wdc(ctx, season='current'):
    """Display the Driver Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 wdc             Current WDC standings as of last race.
        !f1 wdc <season>    WDC standings from <season>.
    """
    await check_season(ctx, season)
    result = await api.get_driver_standings(season)
    table = make_table(result['data'])
    await ctx.send(
        f"**World Driver Championship**\n" +
        f"Season: {result['season']} Round: {result['round']}\n"
    )
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['teams', 'constructors'])
async def wcc(ctx, season='current'):
    """Display Constructor Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 wcc            Current WCC standings as of the last race.
        !f1 wcc [season]   WCC standings from [season].
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
        !f1 grid            All drivers and teams in the current season as of the last race.
        !f1 grid [season]   All drivers and teams at the end of [season].
    """
    await check_season(ctx, season)
    result = await api.get_all_drivers_and_teams(season)
    # Use simple table to not exceed content limit
    table = make_table(sorted(result['data'], key=itemgetter('Team')), fmt='simple')
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
    result = await api.get_next_race()
    thumb_url = await api.get_wiki_thumbnail(result['url'])
    embed = Embed(
        title=f"**{result['data']['Name']}**",
        description=f"{result['countdown']}",
        url=result['url'],
        colour=Colour.teal(),
    )
    embed.set_thumbnail(url=thumb_url)
    embed.add_field(name='Circuit', value=result['data']['Circuit'], inline=False)
    embed.add_field(name='Round', value=result['data']['Round'], inline=True)
    embed.add_field(name='Country', value=result['data']['Country'], inline=True)
    embed.add_field(name='Date', value=result['data']['Date'], inline=True)
    embed.add_field(name='Time', value=result['data']['Time'], inline=True)
    await ctx.send(embed=embed)


@f1.command(aliases=['finish'])
async def results(ctx, season='current', rnd='last'):
    """Results for race `round`. Default most recent.

    Displays an embed with details about the race event and wikipedia link. Followed by table
    of results. Data includes finishing position, fastest lap, finish status, pit stops per driver.

    Usage:
    ------
        !f1 results                     Results for last race.
        !f1 results [<season> <round>]  Results for [round] in [season].
    """
    await check_season(ctx, season)
    result = await api.get_race_results(rnd, season)
    table = make_table(result['data'], fmt='simple')
    await ctx.send(f"**Race Results - {result['race']} ({result['season']})**")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['quali'])
async def qualifying(ctx, season='current', rnd='last'):
    """Qualifying results for `round`. Defaults to latest.

    Includes best Q1, Q2 and Q3 times per driver.

    Usage:
    ------
        !f1 quali                    Latest results.
        !f1 quali [<season> <round>] Results for [round] in [season].
    """
    await check_season(ctx, season)
    result = await api.get_qualifying_results(rnd, season)
    table = make_table(result['data'])
    await ctx.send(f"**Qualifying Results - {result['race']} ({result['season']})**")
    await ctx.send(f"```\n{table}\n```")


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
        !f1 career vettel | VET | 55   Get career stats for Sebastian Vettel.
    """
    await ctx.send("*Gathering driver data, this may take a few moments...*")
    driver = api.get_driver_info(driver_id)
    result = await api.get_driver_career(driver)
    thumb_url = await api.get_wiki_thumbnail(driver['url'])
    season_list = result['data']['Seasons']['years']
    embed = Embed(
        title=f"**{result['driver']['firstname']} {result['driver']['surname']} Career**",
        url=result['driver']['url'],
        colour=Colour.teal(),
    )
    embed.set_thumbnail(url=thumb_url)
    embed.add_field(name='Number', value=result['driver']['number'], inline=True)
    embed.add_field(name='Nationality', value=result['driver']['nationality'], inline=True)
    embed.add_field(name='Age', value=result['driver']['age'], inline=False)
    embed.add_field(
        name='Championships',
        # Total and list of seasons
        value=f"{result['data']['Championships']['total']} " +
        f"{tuple(int(y) for y in result['data']['Championships']['years'])}",
        inline=False
    )
    embed.add_field(name='Wins', value=result['data']['Wins'], inline=True)
    embed.add_field(name='Poles', value=result['data']['Poles'], inline=True)
    embed.add_field(
        name='Seasons',
        # Total and start to latest season
        value=f"{result['data']['Seasons']['total']} ({season_list[0]}-{season_list[len(season_list)-1]})",
        inline=True
    )
    embed.add_field(
        name='Teams',
        # Total and list of teams
        value=f"{result['data']['Teams']['total']} {tuple(str(t) for t in result['data']['Teams']['names'])}",
        inline=True
    )
    await ctx.send(embed=embed)


@f1.command(aliases=['timings'])
async def laps(ctx, driver_id, season='current', rnd='last'):
    """Display all lap times for the driver.

    Season and round may be omitted to get latest race. A valid driver ID must be given as the first parameter
    in either one of the following formats:
        - name-based ID as used by Ergast API e.g. 'alonso', 'vettel', 'max_verstappen';
        - driver code e.g. 'VET', 'HAM';
        - driver number e.g. 44, 6

    **Note**: This command can take a long time to respond. Consider using `best` command instead.

    Usage:
    ------
        !f1 laps <driver_id> [<season> <round>]
    """
    await check_season(ctx, season)
    driver = api.get_driver_info(driver_id)
    laps_future = api.get_all_laps(rnd, season)
    await ctx.send("*Gathering lap data; this may take a few moments...*")
    result = await api.get_all_laps_for_driver(driver, await laps_future)
    table = make_table(result['data'])
    await ctx.send(f"**Lap times for {result['driver']['firstname']} {result['driver']['surname']}**")
    await ctx.send(f"{result['season']} {result['race']}")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['bestlap'])
async def best(ctx, filter=None, season='current', rnd='last'):
    """Display the best lap times and delta for each driver in `round`.

    If no `round` specified returns results for the most recent race.

    Usage:
    ---------------
        !f1 best                             Return all best laps for the latest race.
        !f1 best [<season> <round>]          Return all best laps for [round] in [season].
        !f1 best [filter] [<season> <round>] Return best laps sorted by [filter].

        Optional filter:
        ----------------
        `fastest` -  Only show the fastest lap of the race.
        `slowest` -  Only show the slowest lap of the race.
        `top`     -  Top 5 fastest drivers.
        `bottom`  -  Bottom 5 slowest drivers.
    """
    await check_season(ctx, season)
    results = await api.get_best_laps(rnd, season)
    sorted_times = rank_best_lap_times(results)
    filtered = filter_times(sorted_times, filter)
    table = make_table(filtered)
    await ctx.send(f"**Fastest laps ranked {filter}**")
    await ctx.send(f"{results['season']} {results['race']}")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['pits', 'pitstops'])
async def stops(ctx, filter=None, season='current', rnd='last'):
    """Display pitstops for each driver in the race, optionally sorted with filter.

    If no `round` specified returns results for the most recent race.

    Usage:
    ---------------
        !f1 stops                             Return all pitstops for the latest race.
        !f1 stops [<season> <round>]          Return all pitstops for [round] in [season].
        !f1 stops [filter] [<season> <round>] Return pitstops sorted by [filter].

        Optional filter:
        ----------------
        `fastest` -  Only show the fastest pitstop the race.
        `slowest` -  Only show the slowest pitstop the race.
        `top`     -  Top 5 fastest pitstops.
        `bottom`  -  Bottom 5 slowest pitstops.
    """
    await check_season(ctx, season)
    res = await api.get_pitstops(rnd, season)
    if filter is not None:
        sorted_times = rank_pitstops(res)
        filtered = filter_times(sorted_times, filter)
        table = make_table(filtered)
    else:
        table = make_table(res['data'])
    await ctx.send(f"**Pit stops ranked {filter}**")
    await ctx.send(f"{res['season']} {res['race']}")
    await ctx.send(f"```\n{table}\n```")


# Plotting commands
# ==================


@f1.group(invoke_without_command=True, case_insensitive=True)
async def plot(ctx, *args):
    """Command group for all plotting functions."""
    await ctx.send(f"Command not recognised. Type `{bot.command_prefix}help f1 plot` for plotting subcommands.")


@plot.command(aliases=['laps'])
async def timings(ctx, season: int, rnd: int, *drivers):
    """Plot all lap data for the specified driver(s) or all drivers.
    **NOTE**: It may take some time to gather all the lap data. Consider using `plot best` command instead.

    Both the season and round must be given first. A single driver or multiple drivers seperated by
    a space may be given as the last parameter.

    Suppling 'all' or not specifying any drivers will return all driver laps. Supplying 'top' or 'bottom' will
    plot the top 3 or bottom 3 drivers, respectively.

    A valid driver ID must be used, which can be either of:
        - name-based ID as used by Ergast API, e.g. 'alonso', 'vettel', 'max_verstappen';
        - driver code, e.g. 'HAM', 'VET';
        - driver number e.g. 44, 6

    Usage:
    ------
        !f1 plot timings <season> <round> [all]
        !f1 plot timings <season> <round> [driver1 driver2...]
    """
    await check_season(ctx, season)
    # No drivers specified, skip filter and plot all
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [api.get_driver_info(d)['id'] for d in drivers]
    else:
        driver_list = []
    laps_future = api.get_all_laps(rnd, season)
    await ctx.send("*Gathering lap data; this may take a few moments...*")

    laps_to_plot = filter_laps_by_driver(await laps_future, driver_list)

    chart.plot_all_driver_laps(laps_to_plot)

    f = File(f"{OUT_DIR}/plot.png", filename='plot_laps.png')
    await ctx.send(f"**Lap timings - {laps_to_plot['race']} ({laps_to_plot['season']})**")
    await ctx.send(file=f)


@timings.error
async def timings_handler(ctx, error):
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.param.name == 'drivers':
            await ctx.send("No driver_id provided.")
        else:
            await ctx.send(
                f"Season and round must be specified: " +
                f"`{bot.command_prefix}f1 timings <season> <round> [all | driver1 driver2]`"
            )
    elif isinstance(error, DriverNotFoundError):
        await ctx.send("Could not find a matching driver. Check ID is correct.")
    # Round or season is missing
    else:
        await ctx.send(
            f"Invalid season or round provided: " +
            f"`{bot.command_prefix}f1 timings <season> <round> [all | driver1 driver2]`"
        )


@plot.command(aliases=['pos', 'overtakes'])
async def position(ctx, season: int, rnd: int, *drivers):
    """Plot race position per lap for the specified driver(s) or all drivers.
    **NOTE**: It may take some time to gather all the lap data. Consider using `plot best` command instead.

    Both the season and round must be given first. A single driver or multiple drivers seperated by
    a space may be given as the last parameter.

    Suppling 'all' or not specifying any drivers will return all driver laps. Supplying 'top' or 'bottom' will
    plot the top 3 or bottom 3 drivers, respectively.

    A valid driver ID must be used, which can be either of:
        - name-based ID as used by Ergast API, e.g. 'alonso', 'vettel', 'max_verstappen';
        - driver code, e.g. 'HAM', 'VET';
        - driver number e.g. 44, 6

    Usage:
    ------
        !f1 plot position <season> <round> [all]
        !f1 plot position <season> <round> [driver1 driver2...]
    """
    await check_season(ctx, season)
    # No drivers specified, skip filter and plot all
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [api.get_driver_info(d)['id'] for d in drivers]
    else:
        driver_list = []
    laps_future = api.get_all_laps(rnd, season)
    await ctx.send("*Gathering lap data; this may take a few moments...*")

    laps_to_plot = filter_laps_by_driver(await laps_future, driver_list)

    chart.plot_race_pos(laps_to_plot)

    f = File(f"{OUT_DIR}/plot.png", filename='plot_pos.png')
    await ctx.send(f"**Race position - {laps_to_plot['race']} ({laps_to_plot['season']})**")
    await ctx.send(file=f)


@plot.error
async def position_handler(ctx, error):
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.param.name == 'drivers':
            await ctx.send("No driver_id provided.")
        else:
            await ctx.send(
                f"Season and round must be specified: " +
                f"`{bot.command_prefix}f1 timings <season> <round> [all | driver1 driver2]`"
            )
    elif isinstance(error, DriverNotFoundError):
        await ctx.send("Could not find a matching driver. Check ID is correct.")
    # Round or season is missing
    else:
        await ctx.send(
            f"Invalid season or round provided: " +
            f"`{bot.command_prefix}f1 timings <season> <round> [all | driver1 driver2]`"
        )


@plot.command(aliases=['best'])
async def fastest(ctx, season='current', rnd='last'):
    """Plot fastest lap times for all drivers in the race as a bar chart.

    Usage:
    ------
        !f1 plot fastest [<season> <round>]
    """
    await check_season(ctx, season)
    res = await api.get_best_laps(rnd, season)
    sorted_laps = rank_best_lap_times(res)
    res['data'] = sorted_laps
    chart.plot_best_laps(res)

    f = File(f"{OUT_DIR}/plot.png", filename='plot_fastest.png')
    await ctx.send(f"**Fastest laps - {res['race']} ({res['season']})**")
    await ctx.send(file=f)


@plot.command(aliases=['stops', 'pits', 'pitstops'])
async def stints(ctx, season='current', rnd='last'):
    """Plot race stints and pit stops per driver.

    Usage:
        !f1 plot stints [<season> <round>]
    """
    await check_season(ctx, season)
    res = await api.get_pitstops(rnd, season)
    chart.plot_pitstops(res)

    f = File(f"{OUT_DIR}/plot.png", filename='plot_pitstops.png')
    await ctx.send(f"**Race stints - {res['race']} ({res['season']})**")
    await ctx.send(file=f)
