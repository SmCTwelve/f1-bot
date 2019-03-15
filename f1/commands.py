import logging
import asyncio
from discord import Colour, File
from discord.activity import Activity, ActivityType
from discord.embeds import Embed
from discord.ext import commands

from f1 import api
from f1.stats import chart
from f1.config import CONFIG, OUT_DIR
from f1.utils import is_future, make_table, filter_times, rank_best_lap_times, rank_pitstops


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
    if isinstance(err, asyncio.TimeoutError) or 'TimeoutError' in str(err):
        await ctx.send(f"Response timed out. Check `{bot.command_prefix}f1 status`.")
    else:
        await ctx.send(f":confused: Command failed: {err.message if hasattr(err, 'message') else ''}")
        await ctx.send(f"Try `{bot.command_prefix}help f1 <command>`.")


@bot.command()
async def ping(ctx, *args):
    """Display the current latency."""
    await ctx.send(bot.latency)

# Main command group
# ==================


@bot.group(invoke_without_command=True, case_insensitive=True)
async def f1(ctx, *args):
    """Commands to get F1 data. Check the list of subcommands and usage: https://bit.ly/2tYRNSd

    Function is only called when the invoked command does not match one of the subcommands
    in `f1.commands`. Otherwise context and args are passed down to the approriate subcommand.
    """
    await ctx.send(f'Command not recognised: {ctx.prefix}{ctx.command}. Type `{bot.command_prefix}help f1`.')


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
        !f1 grid            All drivers and teams in the current season as of the last race.
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


@f1.command(aliases=['finish'])
async def results(ctx, season='current', rnd='last'):
    """Results for race `round`. Default most recent.

    Displays an embed with details about the race event and wikipedia link. Followed by table
    of results. Data includes finishing position, fastest lap, finish status, pit stops per driver.

    Usage:
    ------
        !f1 results                     Results for last race.
        !f1 results [season] [round]    Results for [round] in [season].
    """
    await check_season(ctx, season)
    result = await api.get_race_results(rnd, season)
    table = make_table(result['data'], fmt='simple')
    await ctx.send(f"{result['season']} {result['race']} Race Results")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['quali'])
async def qualifying(ctx, season='current', rnd='last'):
    """Qualifying results for `round`. Defaults to latest.

    Includes best Q1, Q2 and Q3 times per driver.

    Usage:
    ------
        !f1 quali                    Latest results.
        !f1 quali [season] [round]   Results for [round] in [season].
    """
    await check_season(ctx, season)
    result = await api.get_qualifying_results(rnd, season)
    table = make_table(result['data'])
    await ctx.send(f"{result['season']} {result['race']} Qualifying Results")
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
        !f1 career vettel     Get career stats for Sebastian Vettel.
    """
    # TODO - support JSON file to convert driver codes/names to ID's for easier use
    await ctx.send("*Gathering driver data...*")
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


@f1.command(aliases=['timings'])
async def laps(ctx, driver_id, season='current', rnd='last', ):
    """Display all lap times for the driver in `rnd` of `season`.

    A valid `driver_id` is required, other parameters may be omitted to get lastest race.
    **Note**: This command can take a long time to respond. Consider using `best` command instead.

    Usage:
    ------
        !f1 laps <driver_id> [season] [round]
    """
    await check_season(ctx, season)
    await ctx.send("*Gathering lap data; this may take a few moments...*")
    result = await api.get_all_driver_lap_times(driver_id, rnd, season)
    table = make_table(result['data'])
    await ctx.send(f"**Lap times for {result['driver']['firstname']} {result['driver']['surname']}**")
    await ctx.send(f"{result['season']} {result['race']}")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['fastest'])
async def best(ctx, season='current', rnd='last', filter=None):
    """Display the best lap times and delta for each driver in `round`.

    If no `round` specified returns results for the most recent race.

    Usage:
    ---------------
        !f1 best                            Return all best laps for the latest race.
        !f1 best [season] [round]           Return all best laps for [round] in [season].
        !f1 best [season] [round] [filter]  Return best laps sorted by [filter].

        Optional filter:
        ----------------
        `fastest` -  Only show the fastest lap of the race.
        `slowest` -  Only show the slowest lap of the race.
        `top`     -  Top 5 fastest drivers.
        `bottom`  -  Bottom 5 slowest drivers.
    """
    results = await api.get_best_laps(rnd, season='current')
    sorted_times = rank_best_lap_times(results)
    filtered = filter_times(sorted_times, filter)
    table = make_table(filtered)
    await ctx.send(f"**Fastest laps ranked {filter}**")
    await ctx.send(f"{results['season']} {results['race']}")
    await ctx.send(f"```\n{table}\n```")


@f1.command(aliases=['pits', 'pitstops'])
async def stops(ctx, season='current', rnd='last', filter=None):
    """Display pitstops for each driver in the race with, optionally sorted with filter.

    If no `round` specified returns results for the most recent race.

    Usage:
    ---------------
        !f1 stops                           Return all pitstops for the latest race.
        !f1 stops [season] [round]          Return all pitstops for [round] in [season].
        !f1 stops [season] [round] [filter] Return pitstops sorted by [filter].

        Optional filter:
        ----------------
        `fastest` -  Only show the fastest pitstop the race.
        `slowest` -  Only show the slowest pitstop the race.
        `top`     -  Top 5 fastest pitstops.
        `bottom`  -  Bottom 5 slowest pitstops.
    """
    res = await api.get_pitstops(season, rnd)
    if filter is not None:
        sorted_times = rank_pitstops(res)
        filtered = filter_times(sorted_times, filter)
        table = make_table(filtered)
    else:
        table = make_table(res)
    await ctx.send(f"**Pitstops ranked {filter}**")
    await ctx.send(f"{res['season']} {res['race']}")
    await ctx.send(f"```\n{table}\n```")

# Plotting commands
# ==================


@f1.group(invoke_without_command=True, case_insensitive=True)
async def plot(ctx, *args):
    """Command group for all plotting functions."""
    await ctx.send(f"Command not recognised, type `{bot.command_prefix}help f1`.")


@plot.command(aliases=['laps'])
async def timings(ctx, season, rnd, *, drivers):
    """Plot all lap data between the two drivers or a single driver.

    Both the season and round must be specified.

    It may take a few moments to gather the data.

    Usage:
    ------
        !f1 plot timings [season] [round] <driver1_id> [driver2_id]
    """
    drivers_list = drivers.split(' ')
    await ctx.send("*Gathering lap data; this may take a few moments...*")
    # Too many drivers
    if len(drivers_list) > 2:
        raise commands.TooManyArguments("More than 2 drivers given.")
    # No drivers
    elif len(drivers_list) == 0:
        raise commands.MissingRequiredArgument(drivers)
    else:
        await check_season(ctx, season)
        # Two drivers
        # Gather all lap data for both drivers concurrently
        if len(drivers_list) == 2:
            driver1_res, driver2_res = await asyncio.gather(
                api.get_all_driver_lap_times(drivers_list[0], rnd, season),
                api.get_all_driver_lap_times(drivers_list[1], rnd, season)
            )
            await chart.plot_driver_vs_driver_lap_timings(driver1_res, driver2_res)
        # No second driver given so plotting for one
        else:
            driver1_res = await api.get_all_driver_lap_times(drivers_list[0], rnd, season)
            await chart.plot_all_driver_laps(driver1_res)

        f = File(f"{OUT_DIR}/plot.png", filename='plot.png')
        await ctx.send(file=f)


@timings.error
async def timings_handler(ctx, error):
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.command.name == 'drivers':
            await ctx.send("No driver_id provided.")
        # Round or season is missing
        else:
            await ctx.send(
                f"Season and round must be specified: " +
                f"`{bot.command_prefix}f1 timings <season> <round> <driver1_id> [driver2_id]`"
            )


@plot.command(aliases=['best'])
async def fastest(ctx, season='current', rnd='last'):
    """Plot fastest lap times for all drivers in the race as a bar chart.

    Usage:
    ------
        !f1 plot fastest [season] [round]
    """
    await check_season(ctx, season)
    res = await api.get_best_laps(rnd, season)
    await chart.plot_best_laps(res)

    f = File(f"{OUT_DIR}/plot.png", filename='plot.png')
    await ctx.send(file=f)
