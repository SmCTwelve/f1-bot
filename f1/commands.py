import gc
import logging
import asyncio
import re

from discord import ApplicationContext, Message
from discord.errors import ApplicationCommandInvokeError
from discord.activity import Activity, ActivityType
from discord.ext import commands
from matplotlib import pyplot as plt

from f1.target import MessageTarget
from f1.config import Config


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
    logger.info(f"Command: /{ctx.command} in {ctx.guild.name} {ctx.channel} by {ctx.user}")


async def handle_errors(ctx: commands.Context | ApplicationContext, err):
    # Force cleanup
    plt.close("all")
    gc.collect()

    logger.error(f"Command failed: /{ctx.command} in {ctx.guild.name} {ctx.channel} by {ctx.user}")
    logger.error(f"Selected Options: {ctx.selected_options}")
    logger.error(f"Reason: {err}")
    target = MessageTarget(ctx)

    # Catch TimeoutError
    if isinstance(err, asyncio.TimeoutError) or 'TimeoutError' in str(err):
        await target.send("Response timed out. Check connection status.")

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
async def on_application_command_completion(ctx: ApplicationContext):
    gc.collect()


@bot.event
async def on_command_error(ctx: commands.Context, err):
    await handle_errors(ctx, err)


@bot.event
async def on_application_command_error(ctx: ApplicationContext, err):
    await handle_errors(ctx, err)
