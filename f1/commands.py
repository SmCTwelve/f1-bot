import logging
import asyncio
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
import f1.utils


logger = logging.getLogger("f1-bot")

bot = Config().bot

bot.load_extensions(
    'f1.cogs.race',
    'f1.cogs.season',
    'f1.cogs.plot',
    'f1.cogs.admin',
)


@bot.event
async def on_ready():
    logger.info("Bot ready...")
    job = Activity(name="/f1", type=ActivityType.watching)
    await bot.change_presence(activity=job)


@bot.event
async def on_message(message: Message):
    if re.match(r'^' + bot.command_prefix + r'?\s*$', message.content):
        await message.reply(f"No subcommand provided. Try {bot.command_prefix}help [command].")
    await bot.process_commands(message)


def handle_command(ctx: commands.Context | ApplicationContext):
    logger.info(f"Command: /{ctx.command} in {ctx.channel} by {ctx.user}")


async def handle_errors(ctx: commands.Context | ApplicationContext, err):
    # Command or Cog handler already responded
    if ctx.response.is_done():
        return

    logger.error(f"Command failed: /{ctx.command}\n {err}")
    target = MessageTarget(ctx)

    # Catch TimeoutError
    if isinstance(err, asyncio.TimeoutError) or 'TimeoutError' in str(err):
        await target.send("Response timed out. Check connection status.")

    # Catch DriverNotFoundError
    elif isinstance(err, DriverNotFoundError):
        await target.send("Could not find a matching driver. Check ID.")

    # Invocation errors
    elif isinstance(err, ApplicationCommandInvokeError):
        await target.send(f":x: {str(err.__cause__)}")

    # Catch all other errors
    else:
        if isinstance(err, commands.CommandNotFound):
            await target.send("Command not recognised.")
        else:
            await target.send(
                f"Command failed: {err}"
            )


@bot.event
async def on_command(ctx: commands.Context):
    await handle_command(ctx)


@bot.event
async def on_application_command(ctx: ApplicationContext):
    # Defer slash commands by default
    handle_command(ctx)
    await ctx.defer(
        ephemeral=Config().settings["MESSAGE"].getboolean("EPHEMERAL"),
    )


@bot.event
async def on_command_completion(ctx: commands.Context):
    await ctx.message.add_reaction(u'🏁')


@bot.event
async def on_command_error(ctx: commands.Context, err):
    await handle_errors(ctx, err)


@bot.event
async def on_application_command_error(ctx: ApplicationContext, err):
    await handle_errors(ctx, err)


# Main command group
# ==================


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
    thumb_url_task = asyncio.create_task(f1.utils.get_wiki_thumbnail(driver['url']))
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
