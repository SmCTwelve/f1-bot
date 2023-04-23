import asyncio
import logging
from discord import Colour, Embed, Option
import discord
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
    """All race related commands including qualifying, race results and pitstop data."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    race = discord.SlashCommandGroup(
        name="race",
        description="Race related commands"
    )

    @race.command(description="Qualifying results. Default latest.")
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
            content=f"```\n{table}\n```",
            embed=Embed(title=f"**Qualifying Results - {result['race']} ({result['season']})**", url=result['url'])
        )

    @race.command(description="Final race results. Default latest.")
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
            content=f"```\n{table}\n```",
            embed=Embed(title=f"**Race Results - {result['race']} ({result['season']})**", url=result['url']),
        )

    @race.command(description="Race pitstops ranked by duration.", name="pitstops-ranked")
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
            # Keep only the best pitstop per driver from all entries
            filtered = utils.remove_driver_duplicates_from_timing(sorted_res, "Duration")
            table = utils.make_table(filtered)

        emd = Embed(
            title=f"**Pitstops ({filter})** | {res['season']} {res['race']}",
            description=f"```\n{table}\n```"
        )
        await target.send(embed=emd)

    @race.command(description="Driver pitstops.", name="pitstops-driver")
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

        await target.send(embed=Embed(
            title=f"**Pitstops for {driver_id} | {res['season']} {res['race']}**",
            description=f"```\n{table}\n```"
        ))

    @race.command(description="Best ranked lap times per driver in the race.")
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

        await target.send(embed=Embed(
            title=f"**Laptimes ({filter}) | {res['season']} {res['race']}**",
            description=f"```\n{table}\n```"
        ))

    @race.command(description="Details and countdown to the next race weekend.")
    async def next(self, ctx):
        result = await api.get_next_race()
        page_url = str(result['url']).replace(f"{result['season']}_", '')
        flag_img_task = asyncio.create_task(api.get_wiki_thumbnail(f"/{result['data']['Country']}"))
        emd = Embed(
            title=f"**{result['data']['Name']}**",
            description=f"{result['countdown']}",
            url=page_url,
            colour=Colour.brand_red(),
        )
        emd.set_thumbnail(url=await flag_img_task)
        emd.set_author(name="View schedule", url="https://f1calendar.com/")
        emd.add_field(name='Circuit', value=result['data']['Circuit'], inline=False)
        emd.add_field(name='Round', value=result['data']['Round'], inline=True)
        emd.add_field(name='Country', value=result['data']['Country'], inline=True)
        emd.add_field(name='Date', value=result['data']['Date'], inline=True)
        emd.add_field(name='Time', value=result['data']['Time'], inline=True)
        target = MessageTarget(ctx)
        await target.send(embed=emd)


def setup(bot: discord.Bot):
    bot.add_cog(Race(bot))
