import asyncio
import logging
from operator import itemgetter

from discord import Colour, Embed, Option
from discord.ext import commands

from f1 import api
from f1.target import MessageTarget
from f1.config import Config
from f1.utils import make_table, check_season

logger = logging.getLogger("f1-bot")

SeasonOption = Option(str, default="current", description="Season year. If not specified uses current season.")


class Season(commands.Cog, guild_ids=Config().guilds):
    """Commands related to F1 season, e.g. championship standings and schedule."""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Driver championship standings.")
    async def wdc(self, ctx, season: SeasonOption):
        """Display the Driver Championship standings as of the last race or `season`.

        Usage:
        ------
            /wdc [season]    WDC standings from [season].
        """
        await check_season(ctx, season)
        result = await api.get_driver_standings(season)
        table = make_table(result['data'], fmt='simple')
        target = MessageTarget(ctx)
        await target.send(
            embed=Embed(
                title=f"**World Constructor Championship ({result['season']})**",
                description=f"```\n{table}\n```"
            )
            .set_footer(text=f"Round: {result['round']}")
        )

    @commands.slash_command(description="Constructors Championship standings.")
    async def wcc(self, ctx, season: SeasonOption):
        """Display Constructor Championship standings as of the last race or `season`.

        Usage:
        ------
            /wcc [season]   WCC standings from [season].
        """
        await check_season(ctx, season)
        result = await api.get_team_standings(season)
        table = make_table(result['data'])
        target = MessageTarget(ctx)
        await target.send(
            embed=Embed(
                title=f"**World Constructor Championship ({result['season']})**",
                description=f"```\n{table}\n```"
            )
            .set_footer(name=f"Round: {result['round']}")
        )

    @commands.slash_command(desciption="All drivers and teams participating in the season.")
    async def grid(self, ctx, season: SeasonOption):
        """Display all the drivers and teams participating in the `season`.

        Usage:
        ------
            /grid            All drivers and teams in the current season as of the last race.
            /grid [season]   All drivers and teams at the end of [season].
        """
        await check_season(ctx, season)
        result = await api.get_all_drivers_and_teams(season)
        table = make_table(sorted(result['data'], key=itemgetter('Team')), fmt='simple')
        target = MessageTarget(ctx)
        await target.send(
            content=f"```\n{table}\n```",
            embed=Embed(
                title=f"**Formula 1 Grid ({result['season']})**",
            )
            .set_footer(name=f"Round: {result['round']}")
        )

    @commands.slash_command(description="Race schedule for the season.")
    async def schedule(self, ctx):
        await MessageTarget(ctx).send(
            embed=Embed(
                title="Formula 1 Season Calendar",
                description="Start times for each session in your local timezone.",
                type="link",
                url="https://f1calendar.com/"
            )
        )

    @commands.slash_command(description="Details and countdown to the next race weekend.")
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
        emd.set_author(name="View full schedule", url="https://f1calendar.com/")
        emd.add_field(name='Circuit', value=result['data']['Circuit'], inline=False)
        emd.add_field(name='Round', value=result['data']['Round'], inline=True)
        emd.add_field(name='Country', value=result['data']['Country'], inline=True)
        emd.add_field(name='Date', value=result['data']['Date'], inline=True)
        emd.add_field(name='Time', value=result['data']['Time'], inline=True)
        target = MessageTarget(ctx)
        await target.send(embed=emd)


def setup(bot):
    bot.add_cog(Season(bot))
