import logging
from discord import Option
from discord.ext import commands

from f1 import utils
from f1 import api
from f1.errors import DriverNotFoundError
from f1.target import MessageTarget
from f1.config import Config

logger = logging.getLogger('f1-bot')

SeasonOption = Option(str, default="current", description="Season year. If not specified uses current season.")
RoundOption = Option(str, default="last", description="Race number. Most recent used if left out.")
RankedPitstopFilter = Option(str, choices=["Best", "Worst", "Ranked"], default="Ranked")
LaptimeFilter = Option(str, choices=["Fastest", "Slowest", "Top 5", "Bottom 5", "Ranked"], default="Ranked")


class Race(commands.Cog, guild_ids=Config().guilds):
    """All race related commands including qualifying, race and pitstop data."""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Qualifying results. Default latest.")
    async def qualifying(self, ctx, season: SeasonOption, round: RoundOption):
        """Qualifying results for the given race.

        Usage:
        ----------
            /qualifying [season] [round]
        """
        await utils.check_season(ctx, season)
        result = await api.get_qualifying_results(round, season)
        table = utils.make_table(result['data'])
        target = MessageTarget(ctx)
        await target.send(
            f"**Qualifying Results - {result['race']} ({result['season']})**" +
            f"```\n{table}\n```"
        )

    @commands.slash_command(description="Final race results. Default latest.")
    async def results(self, ctx, season: SeasonOption, round: RoundOption):
        """Get the complete race results. Both choices optional.

        Usage:
        ----------
            /results [season] [round]
        """
        await utils.check_season(ctx, season)
        result = await api.get_race_results(round, season)
        table = utils.make_table(result['data'], fmt='simple')
        target = MessageTarget(ctx)
        await target.send(
            f"**Race Results - {result['race']} ({result['season']})**" +
            f"```\n{table}\n```"
        )

    @commands.slash_command(description="Race pitstops ranked by duration.", name="pitstops-ranked")
    async def pitstops_ranked(self, ctx, season: SeasonOption, round: RoundOption, filter: RankedPitstopFilter):
        """Display pitstops for the race ranked by `filter`.

        All parameters are optional. Defaults to all pitstops ranked best to worst for the most recent race.
        Pitstop data unavailable before 2012.

        Usage:
        ----------
            /pitstops-ranked [season] [round] [filter]
        """
        target = MessageTarget(ctx)
        # Pit data only available from 2012 so catch seasons before
        if not season == 'current':
            if int(season) < 2012:
                await ctx.send("Pitstop data not available before 2012.")
                raise commands.BadArgument(message="Tried to get pitstops before 2012.")
        await utils.check_season(ctx, season)

        # Get stops and stort them
        res = await api.get_pitstops(round, season)
        sorted_res = utils.rank_pitstops(res)

        # Filter based on choice
        if filter == "Best":
            filtered = utils.filter_times(sorted_res, "fastest")
            table = utils.make_table(filtered)
        elif filter == "Worst":
            filtered = utils.filter_times(sorted_res, "slowest")
            table = utils.make_table(filtered)
        else:
            table = utils.make_table(sorted_res)

        await target.send(
            f"**Pit stops ranked {filter}**\n" +
            f"{res['season']} {res['race']}" +
            f"```\n{table}\n```"
        )

    @commands.slash_command(description="Driver pitstops.", name="pitstops-driver")
    async def pitstops_driver(self, ctx, driver_id: Option(str, required=True),
                              season: SeasonOption, round: RoundOption):
        """Pitstops for a specific driver in the race.

        Both `season` and `round` are optional. `driver_id` is required and must be a driver number or 3 letter code.
        Pitstop data unavailable before 2012.

        Usage:
        ----------
            /pitstops-driver [season] [round] <driver_id>

        e.g.
            /pitstops-driver 2022 5 ALO
        """
        target = MessageTarget(ctx)
        # Check for post-2012 data
        if not season == 'current':
            if int(season) < 2012:
                await ctx.send("Pitstop data not available before 2012.")
                raise commands.BadArgument(message="Tried to get pitstops before 2012.")
        await utils.check_season(ctx, season)

        # Get driver stops
        res = await api.get_pitstops(round, season)
        try:
            driver = api.get_driver_info(driver_id)
            filtered = [s for s in res['data'] if s['Driver'] == driver['code']]
        except DriverNotFoundError:
            await target.send("Invalid driver identifier provided.", ephemeral=True)
            raise commands.BadArgument("Invalid driver")

        table = utils.make_table(filtered)

        await target.send(
            f"**Pitstops for {driver_id}**\n" +
            f"{res['season']} {res['race']}" +
            f"```\n{table}\n```"
        )

    @commands.slash_command(description="Best ranked lap times per driver in the race.")
    async def laptimes(self, ctx, season: SeasonOption, round: RoundOption, filter: LaptimeFilter):
        """Best ranked lap times per driver in the race. All parameters optional.

        Only the best recorded lap for each driver in the race.

        Usage:
        ----------
            /laptimes [season] [round] [filter] \n
            /laptimes 2022 5 fastest
        """
        target = MessageTarget(ctx)
        await utils.check_season(ctx, season)
        res = await api.get_best_laps(round, season)
        sorted_times = utils.rank_best_lap_times(res)

        if filter == "Ranked":
            ranking = "all"
        elif filter == "Top 5":
            ranking = "top"
        elif filter == "Bottom 5":
            ranking = "bottom"
        else:
            ranking = str(filter).lower()

        filtered_laps = utils.filter_times(sorted_times, ranking)
        table = utils.make_table(filtered_laps)

        await target.send(
            f"**Fastest laps ranked {filter}**\n" +
            f"{res['season']} {res['race']}" +
            f"```\n{table}\n```"
        )


def setup(bot):
    bot.add_cog(Race(bot))
