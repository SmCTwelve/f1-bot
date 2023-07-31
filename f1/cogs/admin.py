import asyncio
import logging
import sys
import time

import discord
from discord import ApplicationContext, Embed, default_permissions
from discord.ext import commands
from fastf1 import Cache as ff1_cache

from f1 import utils
from f1.api import fetch
from f1.api.ergast import check_status
from f1.config import Config
from f1.target import MessageTarget

logger = logging.getLogger("f1-bot")

# set global time bot started
START_TIME = time.time()


class Admin(commands.Cog, guild_ids=Config().guilds):
    """Commands to manage the bot and view info."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    admin = discord.SlashCommandGroup(
        name="admin",
        description="Admin commands."
    )

    def get_uptime(self):
        """Get running time since bot started. Return tuple (days, hours, minutes)."""
        invoke_time = time.time()
        uptime = invoke_time - START_TIME
        days, rem = divmod(uptime, 86400)
        hours, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        return (int(days), int(hours), int(mins), int(secs))

    async def _enable_cache(self, minutes: int):
        await asyncio.sleep(float(minutes * 60))
        fetch.use_cache = True
        ff1_cache.set_enabled()
        logger.warning("Cache re-enabled after timeout")

    @commands.slash_command()
    async def help(self, ctx: ApplicationContext):
        info = await self.bot.application_info()
        emd = Embed(
            title=f"{info.name}",
            description="Type `/command` and choose parameters",
            url="https://github.com/SmCTwelve/f1-bot/blob/v2/README.md#commands",
            colour=utils.F1_RED
        )
        emd.set_thumbnail(url=info.icon.url)
        emd.add_field(
            name="",
            value="[Available commands description]"
            + "(https://github.com/SmCTwelve/f1-bot/wiki/Command-Usage-and-Examples)"
        )
        await MessageTarget(ctx).send(embed=emd)

    @commands.slash_command(description="Bot information and status.")
    async def info(self, ctx: ApplicationContext):
        uptime = self.get_uptime()
        api_status = await check_status()
        app_info = await self.bot.application_info()
        latency = int(self.bot.latency * 1000)

        # Use diff code block styling to get coloured text
        if api_status in [0, 3]:
            api_txt = "```diff\n- Slow\n```"
        else:
            api_txt = "```diff\n+ Good\n```"

        if self.bot.is_closed():
            ws = "```diff\n- Closed\n```"
        else:
            ws = "```diff\n+ Open\n```"

        emd = Embed(
            title=f"{app_info.name}",
            description=app_info.description,
            colour=utils.F1_RED
        )
        emd.set_thumbnail(url=app_info.icon.url)
        emd.add_field(name="Help", value="https://github.com/SmCTwelve/f1-bot", inline=False)
        emd.add_field(name="Owner", value=app_info.owner.name, inline=True)
        emd.add_field(name="Uptime", value=f"{uptime[0]}d, {uptime[1]}h, {uptime[2]}m", inline=True)
        emd.add_field(name="Ping", value=f"{latency} ms", inline=True)
        emd.add_field(name="Connection", value=ws, inline=True)
        emd.add_field(name="API", value=api_txt, inline=True)

        await MessageTarget(ctx).send(embed=emd)

    @admin.command(name="disable-cache", description="Temporarily disable caching for X minutes (default 5).")
    @default_permissions(administrator=True)
    async def disable_cache(self, ctx: ApplicationContext,
                            minutes: discord.Option(int, default=5, max_value=15)):
        """Temporarily disable result caching. Will automatically re-enable the
        cache after `minutes`, default 5."""
        fetch.use_cache = False
        ff1_cache.set_disabled()
        logger.warning(f"Disabling caching for {minutes} minutes")
        # Schedule the sleep task in the background so the command doesn't wait
        asyncio.create_task(self._enable_cache(minutes))
        await MessageTarget(ctx).send(f":warning: Cache disabled for {minutes} minutes.")

    @admin.command(description="Shut down the bot application. Bot owner only.")
    @default_permissions()
    @commands.is_owner()
    async def stop(self, ctx):
        logger.warning("Owner used stop command. Closing the bot connection...")
        await self.bot.close()
        logger.warning("Shutting down application.")
        sys.exit()


def setup(bot: discord.Bot):
    bot.add_cog(Admin(bot))
