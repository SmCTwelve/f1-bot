import logging

import discord
from discord import Embed
from discord.ext import commands

from f1 import options
from f1 import utils
from f1.api import ergast, stats
from f1.config import Config
from f1.target import MessageTarget
from f1.utils import F1_RED, check_season

logger = logging.getLogger("f1-bot")


class Season(commands.Cog, guild_ids=Config().guilds):
    """Commands related to F1 season, e.g. championship standings and schedule."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(description="Driver championship standings.")
    async def wdc(self, ctx, year: options.SeasonOption):
        """Display the Driver Championship standings as of the last race or `season`.

        Usage:
        ------
            /wdc [season]    WDC standings from [season].
        """
        await check_season(ctx, year)
        result = await ergast.get_driver_standings(year)
        table, ax = stats.championship_table(result['data'], type="wdc")
        yr, rd = result['season'], result['round']
        ax.set_title(f"{yr} Driver Championship - Round {rd}").set_fontsize(12)

        f = utils.plot_to_file(table, f"wdc_{yr}_{rd}")
        await MessageTarget(ctx).send(file=f)

    @commands.slash_command(description="Constructors Championship standings.")
    async def wcc(self, ctx, year: options.SeasonOption):
        """Display Constructor Championship standings as of the last race or `season`.

        Usage:
        ------
            /wcc [season]   WCC standings from [season].
        """
        await check_season(ctx, year)
        result = await ergast.get_team_standings(year)
        table, ax = stats.championship_table(result['data'], type="wcc")
        yr, rd = result['season'], result['round']
        ax.set_title(f"{yr} Constructor Championship - Round {rd}").set_fontsize(12)

        f = utils.plot_to_file(table, f"wcc_{yr}_{rd}")
        await MessageTarget(ctx).send(file=f)

    @commands.slash_command(desciption="All drivers and teams participating in the season.")
    async def grid(self, ctx, year: options.SeasonOption):
        """Display all the drivers and teams participating in the `season`.

        Usage:
        ------
            /grid            All drivers and teams in the current season as of the last race.
            /grid [season]   All drivers and teams at the end of [season].
        """
        await check_season(ctx, year)
        result = await ergast.get_all_drivers_and_teams(year)
        table, ax = stats.grid_table(result['data'])
        yr, rd = result['season'], result['round']
        ax.set_title(f"{yr} Formula 1 Grid").set_fontsize(12)

        f = utils.plot_to_file(table, f"grid_{yr}_{rd}")
        await MessageTarget(ctx).send(file=f)

    @commands.slash_command(description="Race schedule for the season.")
    async def schedule(self, ctx):
        await MessageTarget(ctx).send(
            embed=Embed(
                title="Formula 1 Season Calendar",
                description="Start times for each session in your local timezone.",
                type="link",
                url="https://f1calendar.com/",
                colour=F1_RED
            )
        )


def setup(bot: discord.Bot):
    bot.add_cog(Season(bot))
