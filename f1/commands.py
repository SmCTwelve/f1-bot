import logging
import asyncio
import random
import re
from discord import ApplicationCommandInvokeError, ApplicationContext, Colour, File, Message
from discord.activity import Activity, ActivityType
from discord.embeds import Embed
from discord.ext import commands

from f1.api import ergast
from f1.stats import chart
from f1.target import MessageTarget
from f1.config import Config, CACHE_DIR
from f1.errors import DriverNotFoundError
from f1.utils import check_season, rank_best_lap_times, filter_laps_by_driver


logger = logging.getLogger("f1-bot")

bot = Config().bot

bot.load_extensions(
    'f1.cogs.race',
    'f1.cogs.season',
    # 'f1.cogs.admin',
)

# TODO
# Add new Emphemeral (only you can see) option preferred over DM and enabled by default
# Use "public" param to override ephemeral/dm for that specific message - check for it in on_command() hook ??


@bot.event
async def on_ready():
    logger.info("Bot ready...")
    job = Activity(name=bot.command_prefix, type=ActivityType.watching)
    await bot.change_presence(activity=job)


@bot.event
async def on_message(message: Message):
    if re.match(r'^' + bot.command_prefix + r'?\s*$', message.content):
        await message.reply(f"No subcommand provided. Try {bot.command_prefix}help [command].")
    await bot.process_commands(message)


def on_command_handler(ctx: commands.Context | ApplicationContext):
    logger.info(f"Command: {ctx.command} in {ctx.channel} by {ctx.user}")


async def on_error_handler(ctx: commands.Context | ApplicationContext, err):
    logger.error(f"Command failed: {ctx.command}\n {err}")
    target = MessageTarget(ctx)

    # Catch TimeoutError
    if isinstance(err, asyncio.TimeoutError) or 'TimeoutError' in str(err):
        await target.send("Response timed out. Check connection status.")

    # Catch DriverNotFoundError
    elif isinstance(err, DriverNotFoundError):
        await target.send("Could not find a matching driver. Check ID.")

    # Invocation errors
    elif isinstance(err, ApplicationCommandInvokeError):
        await target.send(f":x: Error: {str(err.original)}")

    # Catch all other errors
    else:
        if isinstance(err, commands.CommandNotFound):
            await target.send("Command not recognised.")
        else:
            await target.send(
                f"Command failed: {err.message if (hasattr(err, 'message') or hasattr(err, 'msg')) else err}"
            )

    # Random chance to show img with error output if rng is multiple of 12
    rng = random.randint(1, 60)
    if rng % 12 == 0:
        n = random.randint(1, 3)
        img = {1: 'https://i.imgur.com/xocNTde.jpg',
               2: 'https://i.imgur.com/morumoC.jpg',
               3: 'https://i.imgur.com/Cn8Gdh1.gifv'}
        await ctx.send(img[n])


@bot.event
async def on_command(ctx: commands.Context):
    await on_command_handler(ctx)


@bot.event
async def on_application_command(ctx: ApplicationContext):
    await ctx.defer(ephemeral=Config().settings["MESSAGE"]["EPHEMERAL"])
    on_command_handler(ctx)


@bot.event
async def on_command_completion(ctx: commands.Context):
    await ctx.message.add_reaction(u'🏁')


@bot.event
async def on_command_error(ctx: commands.Context, err):
    await on_error_handler(ctx, err)


@bot.event
async def on_application_command_error(ctx: ApplicationContext, err):
    await on_error_handler(ctx, err)


# Main command group
# ==================


@bot.command(aliases=['source', 'git'])
async def github(ctx, *args):
    """Display a link to the GitHub repository."""
    await MessageTarget(ctx).send("https://github.com/SmCTwelve/f1-bot")


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
    target = MessageTarget(ctx)
    await target.send("*Gathering driver data, this may take a few moments...*")
    driver = ergast.get_driver_info(driver_id)
    result = await ergast.get_driver_career(driver)
    thumb_url_task = asyncio.create_task(ergast.get_wiki_thumbnail(driver['url']))
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
    target = MessageTarget(ctx)
    await check_season(ctx, season)
    # No drivers specified, skip filter and plot all
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [ergast.get_driver_info(d)['id'] for d in drivers]
    else:
        driver_list = []
    laps_task = asyncio.create_task(ergast.get_all_laps(rnd, season))
    await target.send("*Gathering lap data; this may take a few moments...*")

    laps_to_plot = filter_laps_by_driver(await laps_task, driver_list)

    chart.plot_all_driver_laps(laps_to_plot)

    f = File(f"{CACHE_DIR}/plot_laps.png", filename='plot_laps.png')
    await target.send(f"**Lap timings - {laps_to_plot['race']} ({laps_to_plot['season']})**")
    await target.send(file=f)


@timings.error
async def timings_handler(ctx, error):
    target = MessageTarget(ctx)
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.param.name == 'drivers':
            await target.send("No driver_id provided.")
    # Round or season is missing
    if isinstance(error, commands.BadArgument):
        await target.send("Invalid season or round provided.")


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
    target = MessageTarget(ctx)
    await check_season(ctx, season)
    # Filter by driver
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [ergast.get_driver_info(d)['id'] for d in drivers]
    # No drivers specified, skip filter and plot all
    else:
        driver_list = []
    laps_task = asyncio.create_task(ergast.get_all_laps(rnd, season))
    await target.send("*Gathering lap data; this may take a few moments...*")

    laps_to_plot = filter_laps_by_driver(await laps_task, driver_list)

    chart.plot_race_pos(laps_to_plot)

    f = File(f"{CACHE_DIR}/plot_pos.png", filename='plot_pos.png')
    await target.send(f"**Race position - {laps_to_plot['race']} ({laps_to_plot['season']})**")
    await target.send(file=f)


@position.error
async def position_handler(ctx, error):
    target = MessageTarget(ctx)
    # Check error is missing arguments
    if isinstance(error, commands.MissingRequiredArgument):
        # Drivers are missing
        if error.param.name == 'drivers':
            await target.send("No driver_id provided.")
    # Round or season is missing
    if isinstance(error, commands.BadArgument):
        await target.send("Invalid season or round provided.")


@plot.command(aliases=['best'])
async def fastest(ctx, season: int = 'current', rnd: int = 'last', *drivers):
    """Plot fastest lap times for all drivers in the race as a bar chart.

    Usage:
    ------
        !f1 plot fastest [<season> <round>]
        !f1 plot fastest <season> <round> [driver1 driver2... | all]
    """
    target = MessageTarget(ctx)
    await check_season(ctx, season)
    res = await ergast.get_best_laps(rnd, season)
    sorted_laps = rank_best_lap_times(res)
    # Filter by driver if specified
    if not (len(drivers) == 0 or drivers[0] == 'all'):
        driver_list = [ergast.get_driver_info(d)['code'] for d in drivers]
        sorted_laps = [lap for lap in sorted_laps if lap['Driver'] in driver_list]
    res['data'] = sorted_laps
    chart.plot_best_laps(res)

    f = File(f"{CACHE_DIR}/plot_fastest.png", filename='plot_fastest.png')
    await target.send(f"**Fastest laps - {res['race']} ({res['season']})**")
    await target.send(file=f)


@fastest.error
async def fastest_handler(ctx, error):
    target = MessageTarget(ctx)
    # Round or season is missing
    if isinstance(error, commands.BadArgument):
        await target.send("Invalid season or round provided.")


@plot.command(aliases=['stops', 'pits', 'pitstops'])
async def stints(ctx, season='current', rnd='last'):
    """Plot race stints and pit stops per driver.

    Usage:
        !f1 plot stints [<season> <round>]
    """
    target = MessageTarget(ctx)
    # Pit data only available from 2012 so catch seasons before
    if not season == 'current':
        if int(season) < 2012:
            await ctx.send("Pitstop data not available before 2012.")
            raise commands.BadArgument(message="Tried to get pitstops before 2012.")
    await check_season(ctx, season)
    res = await ergast.get_pitstops(rnd, season)
    chart.plot_pitstops(res)

    f = File(f"{CACHE_DIR}/plot_pitstops.png", filename='plot_pitstops.png')
    await target.send(f"**Race stints - {res['race']} ({res['season']})**")
    await target.send(file=f)
