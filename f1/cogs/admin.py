import logging
import time
import sys
import discord
from discord import Colour, Embed
from discord.ext import commands

from f1.api import check_status
from f1.target import MessageTarget
from f1.config import Config

logger = logging.getLogger("f1-bot")

# set global time bot started
START_TIME = time.time()


class Admin(commands.Cog, guild_ids=Config().guilds):
    """Commands to manage the bot and view info."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    admin = discord.SlashCommandGroup(
        name="admin",
        description="Restricted commands."
    )

    def get_uptime(self):
        """Get running time since bot started. Return tuple (days, hours, minutes)."""
        invoke_time = time.time()
        uptime = invoke_time - START_TIME
        days, rem = divmod(uptime, 86400)
        hours, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        return (int(days), int(hours), int(mins), int(secs))

    @commands.slash_command(description="Bot information and status.")
    async def info(self, ctx):
        uptime = self.get_uptime()
        api_status = await check_status()
        app_info = await self.bot.application_info()
        latency = int(self.bot.latency * 1000)

        if api_status in [0, 3]:
            api_txt = "```diff\n- Slow\n```"
        else:
            api_txt = "```diff\n+ Good\n```"

        if self.bot.is_closed():
            ws = "```diff\n- Closed\n```"
        else:
            ws = "```diff\n+ Open\n```"

        emd = Embed(
            title=f"Info - {app_info.name}",
            description=app_info.description,
            colour=Colour.teal()
        )
        emd.set_thumbnail(url=app_info.icon.url)
        emd.set_author(name="github.com/SmCTwelve", url="https://github.com/SmCTwelve/f1-bot")
        emd.add_field(name="Owner", value=app_info.owner.display_name, inline=False)
        emd.add_field(name="Uptime", value=f"{uptime[0]}d, {uptime[1]}h, {uptime[2]}m", inline=True)
        emd.add_field(name="Ping", value=f"{latency} ms", inline=True)
        emd.add_field(name="Connection", value=ws, inline=True)
        emd.add_field(name="API", value=api_txt, inline=True)

        MessageTarget().send(embed=emd)

    @admin.command(description="Shut down the bot application. Bot owner only.")
    @commands.is_owner()
    async def stop(self, ctx):
        logger.warning("Owner used stop command. Closing the bot connection...")
        await self.bot.close()
        logger.warning("Shutting down application.")
        sys.exit()
