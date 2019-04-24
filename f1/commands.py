import logging
import asyncio
import random
import re
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

# Disables sending DM temporarily for the command, overrides any config setting
# Is reset on error or after command completion
DISABLE_DM = False

# Store the message target
target = None

# Prefix includes the config symbol and the 'f1' name with hard-coded space
bot = commands.Bot(
    command_prefix=f"{CONFIG['BOT']['PREFIX']}f1 ",
    help_command=commands.DefaultHelpCommand(dm_help=True),
    case_insensitive=True
)


def reset_dm():
    """Resets the global `DISABLE_DM` flag if a command temporarily disabled it."""
    global DISABLE_DM
    if DISABLE_DM:
        DISABLE_DM = False
        logger.info('DISABLE_DM reset to False.')


async def get_target(ctx, msg_type):
    """Check if the target of a command response should be direct message or channel.

    Returns an object of `ctx.author` or the original `ctx`.

    Parameters
    ----------
    `ctx` : Context
        The invocation context of the command.
    `msg_type`: str
        Type of message response: 'table', 'file', 'image', 'error' or 'embed'. Regular text will
        be sent to the channel unless part of the command response of the previous types.
    """
    if DISABLE_DM:
        DM = False
    else:
        if msg_type == 'table' and CONFIG['MESSAGE'].getboolean('TABLE_DM'):
            DM = True
        elif (msg_type == 'file' or msg_type == 'image') and CONFIG['MESSAGE'].getboolean('FILE_DM'):
            DM = True
        elif msg_type == 'embed' and CONFIG['MESSAGE'].getboolean('EMBED_DM'):
            DM = True
        elif msg_type == 'error' and CONFIG['MESSAGE'].getboolean('ERROR'):
            DM = True
        else:
            DM = False
    if DM:
        return ctx.author
    else:
        return ctx


async def check_season(ctx, season):
    """Raise error if the given season is in the future."""
    if is_future(season):
        await ctx.send(f"Can't predict future :thinking:")
        raise commands.BadArgument('Given season is in the future.')


@bot.event
async def on_ready():
    logger.info('Bot ready...')
    job = Activity(name=bot.command_prefix, type=ActivityType.watching)
    await bot.change_presence(activity=job)


@bot.event
async def on_message(message):
    global DISABLE_DM
    pattern = re.compile(r'(\s*)(no-dm|public)(\s*)')
    # Prefix given with no command
    if re.match(r'^' + bot.command_prefix + r'?\s*$', message.content):
        await message.channel.send("No subcommand provided. Check the Readme at <https://bit.ly/2tYRNSd>.")
    # Check for presence of 'no-dm' or 'public' flags
    elif re.search(pattern, message.content.lower()):
        logger.warning('Command has temporarily set DISABLE_DM to True.')
        # Temporarily set disable DM flag
        DISABLE_DM = True
        # strip flag from message content and assign it back to the message for command parsing
        message.content = pattern.sub(' ', message.content)

    await bot.process_commands(message)


@bot.event
async def on_command(ctx):
    channel = ctx.message.channel
    user = ctx.message.author
    logger.info(f'Command: {ctx.prefix}{ctx.command} in {channel} by {user}')


@bot.event
async def on_command_completion(ctx):
    await ctx.message.add_reaction(u'🏁')
    reset_dm()


@bot.event
async def on_command_error(ctx, err):
    logger.exception(f'Command failed: {ctx.prefix}{ctx.command}\n {err}')
    await ctx.message.add_reaction(u'❌')
    target = await get_target(ctx, 'error')
    rng = random.randint(1, 60)
    reset_dm()

    # Catch TimeoutError
    if isinstance(err, asyncio.TimeoutError) or 'TimeoutError' in str(err):
        await target.send(f"Response timed out. Check `{bot.command_prefix}status`.")

    # Catch DriverNotFoundError
    elif isinstance(err, DriverNotFoundError):
        await target.send("Could not find a matching driver. Check ID is correct.")

    # Catch all other errors
    else:
        # Catch CommandNotFound
        if isinstance(err, commands.CommandNotFound):
            await target.send(f"Command not recognised.")
        else:
            await target.send(
                f"Command failed: {err.message if hasattr(err, 'message') or hasattr(err, 'msg') else ''}"
            )
        await target.send(f"Try `{bot.command_prefix}help [command]` or check the Readme at <https://bit.ly/2tYRNSd>.")

    # Random chance to show img with error output if rng is multiple of 12
    if rng % 12 == 0:
        n = random.randint(1, 3)
        img = {1: 'https://i.imgur.com/xocNTde.jpg',
               2: 'https://i.imgur.com/morumoC.jpg',
               3: 'https://i.imgur.com/Cn8Gdh1.gifv'}
        await ctx.send(img[n])


# Main command group
# ==================


@bot.command(aliases=['source', 'git'])
async def github(ctx, *args):
    """Display a link to the GitHub repository."""
    await ctx.send("https://github.com/SmCTwelve/f1-bot")


@bot.command(aliases=['drivers', 'championship'])
async def wdc(ctx, season='current'):
    """Display the Driver Championship standings as of the last race or `season`.

    Usage:
    ------
        !f1 wdc [season]    WDC standings from [season].
    """
    await check_season(ctx, season)
    result = await api.get_driver_standings(season)
    table = make_table(result['data'], fmt='simple')
    target = await get_target(ctx, 'table')
    await target.send(
        f"**World Driver Championship**\n" +
        f"Season: {result['season']} Round: {result['round']}\n"
    )
    await target.send(f"```\n{table}\n```")


@bot.command(aliases=['teams', 'constructors'])
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
    target = await get_target(ctx, 'table')
    await target.send(
        f"**World Constructor Championship**\n" +
        f"Season: {result['season']} Round: {result['round']}\n"
    )
    await target.send(f"```\n{table}\n```")


@bot.command()
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
    target = await get_target(ctx, 'table')
    await target.send(
        f"**Formula 1 {result['season']} Grid**\n" +
        f"Round: {result['round']}\n"
    )
    await target.send(f"```\n{table}\n```")


@bot.command(aliases=['calendar', 'schedule'])
async def races(ctx, *args):
    """Display the full race schedule for the current season."""
    result = await api.get_race_schedule()
    # Use simple table to not exceed content limit
    table = make_table(result['data'], fmt='simple')
    target = await get_target(ctx, 'table')
    await target.send(f"**{result['season']} Formula 1 Race Calendar**\n")
    await target.send(f"```\n{table}\n```")


@bot.command(aliases=['timer', 'next'])
async def countdown(ctx, *args):
    """Display an Embed with details and countdown to the next calendar race."""
    result = await api.get_next_race()
    page_url = result['url'].replace(f"{result['season']}_", '')
    thumb_url_task = asyncio.create_task(api.get_wiki_thumbnail(page_url))
    embed = Embed(
        title=f"**{result['data']['Name']}**",
        description=f"{result['countdown']}",
        url=page_url,
        colour=Colour.teal(),
    )
    embed.set_thumbnail(url=await thumb_url_task)
    embed.add_field(name='Circuit', value=result['data']['Circuit'], inline=False)
    embed.add_field(name='Round', value=result['data']['Round'], inline=True)
    embed.add_field(name='Country', value=result['data']['Country'], inline=True)
    embed.add_field(name='Date', value=result['data']['Date'], inline=True)
    embed.add_field(name='Time', value=result['data']['Time'], inline=True)
    target = await get_target(ctx, 'embed')
    await target.send(embed=embed)


@bot.command(aliases=['finish'])
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
    target = await get_target(ctx, 'table')
    await target.send(f"**Race Results - {result['race']} ({result['season']})**")
    await target.send(f"```\n{table}\n```")


@bot.command(aliases=['quali'])
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
    target = await get_target(ctx, 'table')
    await target.send(f"**Qualifying Results - {result['race']} ({result['season']})**")
    await target.send(f"```\n{table}\n```")


@bot.command(aliases=['driver'])
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
    target = await get_target(ctx, 'embed')
    await target.send("*Gathering driver data, this may take a few moments...*")
    driver = api.get_driver_info(driver_id)
    result = await api.get_driver_career(driver)
    thumb_url_task = asyncio.create_task(api.get_wiki_thumbnail(driver['url']))
    season_list = result['data']['Seasons']['years']
    champs_list = result['data']['Championships']['years']
    embed = Embed(
        title=f"**{result['driver']['firstname']} {result['driver']['surname']} Career**",
        url=result['driver']['url'],
        colour=Colour.teal(),
    )
    embed.set_thumbnail(url=await thumb_url_task)
    embed.add_field(name='Number', value=result['driver']['number'], inline=True)
    embed.add_field(name='Nationality', value=result['driver']['nationality'], inline=True)
    embed.add_field(name='Age', value=result['driver']['age'], inline=True)
    embed.add_field(
        name='Seasons',
        # Total and start to latest season
        value=f"{result['data']['Seasons']['total']} ({season_list[0]}-{season_list[len(season_list)-1]})",
        inline=True
    )
    embed.add_field(name='Wins', value=result['data']['Wins'], inline=True)
    embed.add_field(name='Poles', value=result['data']['Poles'], inline=True)
    embed.add_field(
        name='Championships',
        # Total and list of seasons
        value=(
            f"{result['data']['Championships']['total']} " + "\n"
            + ", ".join(y for y in champs_list if champs_list)
        ),
        inline=False
    )
    embed.add_field(
        name='Teams',
        # Total and list of teams
        value=(
            f"{result['data']['Teams']['total']} " + "\n"
            + ", ".join(t for t in result['data']['Teams']['names'])
        ),
        inline=False
    )
    await target.send(embed=embed)


@bot.command(aliases=['bestlap'])
async def best(ctx, filter=None, season='current', rnd='last'):
    """Display the best lap times and delta for each driver in `round`.

    If no `round` specified returns results for the most recent race.

    Usage:
    ---------------
        !f1 best                             Return all best laps for the latest race.
        !f1 best [filter] [<season> <round>] Return best laps sorted by [filter].

        Optional filter:
        ----------------
        `all`     -  Do not apply a filter.
        `fastest` -  Only show the fastest lap of the race.
        `slowest` -  Only show the slowest lap of the race.
        `top`     -  Top 5 fastest drivers.
        `bottom`  -  Bottom 5 slowest drivers.
    """
    target = await get_target(ctx, 'table')
    if filter not in ['all', 'top', 'fastest', 'slowest', 'bottom', None]:
        await target.send("Invalid filter given.")
        raise commands.BadArgument(message="Invalid filter given.")
    await check_season(ctx, season)
    results = await api.get_best_laps(rnd, season)
    sorted_times = rank_best_lap_times(results)
    filtered = filter_times(sorted_times, filter)
    table = make_table(filtered)
    await target.send(
        f"**Fastest laps ranked {filter}**\n" +
        f"{results['season']} {results['race']}"
    )
    await target.send(f"```\n{table}\n```")


@bot.command(aliases=['pits', 'pitstops'])
async def stops(ctx, filter, season='current', rnd='last'):
    """Display pitstops for each driver in the race, optionally sorted with filter.

    If no `round` specified returns results for the most recent race. Data not available
    before 2012.

    Usage:
    ---------------
        !f1 stops <filter> [season] [round]     Return pitstops sorted by [filter].
        !f1 stops <driver_id> [season] [round]  Return pitstops for the driver.

        Filter:
        ----------------
        `<driver_id>`  -  Get the stops for the driver.
        `fastest` -  Only show the fastest pitstop the race.
        `slowest` -  Only show the slowest pitstop the race.
        `top`     -  Top 5 fastest pitstops.
        `bottom`  -  Bottom 5 slowest pitstops.
    """
    target = await get_target(ctx, 'table')
    # Pit data only available from 2012 so catch seasons before
    if not season == 'current':
        if int(season) < 2012:
            await ctx.send("Pitstop data not available before 2012.")
            raise commands.BadArgument(message="Tried to get pitstops before 2012.")
    await check_season(ctx, season)

    # Get stops
    res = await api.get_pitstops(rnd, season)

    # The filter is for stop duration
    if filter in ['top', 'bottom', 'fastest', 'slowest']:
        sorted_times = rank_pitstops(res)
        filtered = filter_times(sorted_times, filter)
    # The filter is for all stops by a driver
    else:
        try:
            driver = api.get_driver_info(filter)
            filtered = [s for s in res['data'] if s['Driver'] == driver['code']]
        except DriverNotFoundError:
            await ctx.send("Invalid filter or driver provided.")
            raise commands.BadArgument("Invalid filter or driver.")

    table = make_table(filtered)

    await target.send(
        f"**Pit stops ranked {filter}**\n" +
        f"{res['season']} {res['race']}"
    )
    await target.send(f"```\n{table}\n```")


@stops.error
async def stops_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        if error.param.name == 'filter':
            await ctx.send("Filter or driver is required.")

# Plotting commands
# ==================


@bot.group(invoke_without_command=True, case_insensitive=True)
async def plot(ctx, *args):
    """Command group for all plotting functions."""
    await ctx.send(f"Command not recognised. Type `{bot.command_prefix}help plot` for plotting subcommands.")


@plot.command(aliases=['laps'])
async def timings(ctx, season: int = 'current', rnd: int = 'last', *drivers):
    """Plot all lap data for the specified driver(s) or all drivers.

    **NOTE**: It may take some time to gather all the lap data. Consider using `plot best` command instead.

    Both the season and round must be given before any drivers. A single driver or multiple drivers seperated by
    a space may be given as the last parameter. Suppling 'all' or not specifying any drivers
    will return all driver laps.

    A valid driver ID must be used, which can be either of:
        - name-based ID as used by Ergast API, e.g. 'alonso', 'vettel', 'max_verstappen';
        - driver code, e.g. 'HAM', 'VET';
        - driver number e.g. 44, 6

    Usage:
    ------
        !f1 plot position [season] [round]
        !f1 plot position <season> <round> [driver1 driver2... | all]
    """
    target = await get_target(ctx, 'file')
    await check_season(ctx, season)
    # No drivers specified, skip filter and plot all
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [api.get_driver_info(d)['id'] for d in drivers]
    else:
        driver_list = []
    laps_task = asyncio.create_task(api.get_all_laps(rnd, season))
    await target.send("*Gathering lap data; this may take a few moments...*")

    laps_to_plot = filter_laps_by_driver(await laps_task, driver_list)

    chart.plot_all_driver_laps(laps_to_plot)

    f = File(f"{OUT_DIR}/plot_laps.png", filename='plot_laps.png')
    await target.send(f"**Lap timings - {laps_to_plot['race']} ({laps_to_plot['season']})**")
    await target.send(file=f)


@timings.error
async def timings_handler(ctx, error):
    target = await get_target(ctx, 'file')
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.param.name == 'drivers':
            await target.send("No driver_id provided.")
    # Round or season is missing
    if isinstance(error, commands.BadArgument):
        await target.send(f"Invalid season or round provided.")


@plot.command(aliases=['pos', 'overtakes'])
async def position(ctx, season: int = 'current', rnd: int = 'last', *drivers):
    """Plot race position per lap for the specified driver(s) or all drivers.

    **NOTE**: It may take some time to gather all the lap data. Consider using `plot best` command instead.

    Both the season and round must be given before any drivers. A single driver or multiple drivers seperated by
    a space may be given as the last parameter. Suppling 'all' or not specifying any drivers
    will return all driver laps.

    A valid driver ID must be used, which can be either of:
        - name-based ID as used by Ergast API, e.g. 'alonso', 'vettel', 'max_verstappen';
        - driver code, e.g. 'HAM', 'VET';
        - driver number e.g. 44, 6

    Usage:
    ------
        !f1 plot position [season] [round]
        !f1 plot position <season> <round> [driver1 driver2... | all]
    """
    target = await get_target(ctx, 'file')
    await check_season(ctx, season)
    # Filter by driver
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [api.get_driver_info(d)['id'] for d in drivers]
    # No drivers specified, skip filter and plot all
    else:
        driver_list = []
    laps_task = asyncio.create_task(api.get_all_laps(rnd, season))
    await target.send("*Gathering lap data; this may take a few moments...*")

    laps_to_plot = filter_laps_by_driver(await laps_task, driver_list)

    chart.plot_race_pos(laps_to_plot)

    f = File(f"{OUT_DIR}/plot_pos.png", filename='plot_pos.png')
    await target.send(f"**Race position - {laps_to_plot['race']} ({laps_to_plot['season']})**")
    await target.send(file=f)


@position.error
async def position_handler(ctx, error):
    target = await get_target(ctx, 'file')
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.param.name == 'drivers':
            await target.send("No driver_id provided.")
    # Round or season is missing
    if isinstance(error, commands.BadArgument):
        await target.send(f"Invalid season or round provided.")


@plot.command(aliases=['best'])
async def fastest(ctx, season: int = 'current', rnd: int = 'last', *drivers):
    """Plot fastest lap times for all drivers in the race as a bar chart.

    Usage:
    ------
        !f1 plot fastest [<season> <round>]
        !f1 plot fastest <season> <round> [driver1 driver2... | all]
    """
    target = await get_target(ctx, 'file')
    await check_season(ctx, season)
    res = await api.get_best_laps(rnd, season)
    sorted_laps = rank_best_lap_times(res)
    # Filter by driver if specified
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [api.get_driver_info(d)['code'] for d in drivers]
        sorted_laps = [lap for lap in sorted_laps if lap['Driver'] in driver_list]
    res['data'] = sorted_laps
    chart.plot_best_laps(res)

    f = File(f"{OUT_DIR}/plot_fastest.png", filename='plot_fastest.png')
    await target.send(f"**Fastest laps - {res['race']} ({res['season']})**")
    await target.send(file=f)


@fastest.error
async def fastest_handler(ctx, error):
    target = await get_target(ctx, 'file')
    # Round or season is missing
    if isinstance(error, commands.BadArgument):
        await target.send(f"Invalid season or round provided.")


@plot.command(aliases=['stops', 'pits', 'pitstops'])
async def stints(ctx, season='current', rnd='last'):
    """Plot race stints and pit stops per driver.

    Usage:
        !f1 plot stints [<season> <round>]
    """
    target = await get_target(ctx, 'file')
    # Pit data only available from 2012 so catch seasons before
    if not season == 'current':
        if int(season) < 2012:
            await ctx.send("Pitstop data not available before 2012.")
            raise commands.BadArgument(message="Tried to get pitstops before 2012.")
    await check_season(ctx, season)
    res = await api.get_pitstops(rnd, season)
    chart.plot_pitstops(res)

    f = File(f"{OUT_DIR}/plot_pitstops.png", filename='plot_pitstops.png')
    await target.send(f"**Race stints - {res['race']} ({res['season']})**")
    await target.send(file=f)
