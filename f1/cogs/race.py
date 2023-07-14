import asyncio
import logging
from datetime import datetime

import discord
import pandas as pd
from discord import ApplicationCommandError, ApplicationContext, Embed
from discord.ext import commands

from f1 import errors, options, utils
from f1.api import ergast, stats
from f1.config import Config
from f1.target import MessageTarget

logger = logging.getLogger('f1-bot')


class Race(commands.Cog, guild_ids=Config().guilds):
    """All race related commands including qualifying, race results and pitstop data."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.slash_command(description="Result data for the session. Default last race.")
    async def results(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                      session: options.SessionOption):
        """Get the results for a session. The `round` can be the event name, location or round number in the season.
        The `session` is the identifier selected from the command choices.

        If no options given the latest race results will be returned, as defined by Ergast.

        Usage:
        ----------
            /results [year] [round] [session]
        """
        await utils.check_season(ctx, year)

        # Load and format API data
        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, session)
        data = await stats.format_results(s, session)

        table, ax = stats.results_table(data, session)
        ax.set_title(
            f"{ev['EventDate'].year} {ev['EventName']} - {session}"
        ).set_fontsize(12)

        f = utils.plot_to_file(table, f"results_{s.name}_{ev['EventDate'].year}_{ev['RoundNumber']}")
        await MessageTarget(ctx).send(
            file=f,
            content=f"**{session} Results | {ev['EventDate'].year} {ev['EventName']}**")

    @commands.slash_command(description="Race pitstops ranked by duration or filtered to a driver.", name="pitstops")
    async def pitstops(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                       filter: options.RankedPitstopFilter, driver: options.DriverOption):
        """Display pitstops for the race ranked by `filter` or `driver`.

        All parameters are optional. Defaults to the best pitstop per driver for the most recent race.
        Pitstop data unavailable before 2012.

        Usage:
        ----------
            /pitstops-ranked [season] [round] [filter]
        """

        # Pit data only available from 2012 so catch seasons before
        if not year == 'current':
            if int(year) < 2012:
                raise commands.BadArgument(message="Pitstop data unavailable before 2012.")
        await utils.check_season(ctx, year)

        # Get event info to match race name idenfifiers from command
        event = await stats.to_event(year, round)
        yr, rd = event["EventDate"].year, event["RoundNumber"]

        # Process pitstop data
        data = await stats.filter_pitstops(yr, rd, filter, driver)
        table = utils.make_table(
            data,
            fmt="simple", showindex=False)

        await MessageTarget(ctx).send(embed=Embed(
            title=f"**Pitstops ({filter})** | {event['EventName']} ({yr})",
            description=f"```\n{table}\n```"
        ))

    @commands.slash_command(description="Best ranked lap times per driver.")
    async def laptimes(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                       tyre: options.TyreOption):
        """Best ranked lap times per driver in the race. All parameters optional.

        Only the best recorded lap for each driver in the race.

        Usage:
        ----------
            /laptimes [season] [round] [tyre]
        """
        await utils.check_season(ctx, year)
        event = await stats.to_event(year, round)
        s = await stats.load_session(event, "R", laps=True)
        data = stats.fastest_laps(s, tyre)

        # Get the table
        table, ax = stats.laptime_table(data)
        ax.set_title(
            f"{event['EventDate'].year} {event['EventName']}\nFastest Lap Times"
        ).set_fontsize(12)

        f = utils.plot_to_file(table, f"laptimes_{event['EventDate'].year}_{event['RoundNumber']}")
        await MessageTarget(ctx).send(
            file=f,
            content=f"**Fastest Laps | {event['EventDate'].year} {event['EventName']}**")

    @commands.slash_command(
        description="View fastest sectors and speed trap based on quick laps. Seasons >= 2018.")
    async def sectors(self, ctx: ApplicationContext, year: options.SeasonOption,
                      round: options.RoundOption, tyre: options.TyreOption):
        """View min sector times and max speedtrap per driver. Based on recorded quicklaps only."""
        ev = await stats.to_event(year, round)
        yr, rd = ev["EventDate"].year, ev["RoundNumber"]
        s = await stats.load_session(ev, "R", laps=True)
        data = stats.sectors(s, tyre)

        table, ax = stats.sectors_table(data)
        ax.set_title(
            f"{yr} {ev['EventName']} - Sectors" + f"\nTyre: {tyre}" if tyre else ""
        ).set_fontsize(12)

        f = utils.plot_to_file(table, f"sectors_{yr}_{rd}")
        await MessageTarget(ctx).send(
            file=f,
            content=f"**Sector Times | {yr} {ev['EventName']}**")

    @commands.slash_command(description="Tyre compound stints in a race.")
    async def stints(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                     driver: options.DriverOption):
        """Get the race stints on each tyre compound during the race, optionally for a specific driver.

        Usage:
            /stints [season] [round] [driver]
        """
        await utils.check_season(ctx, year)
        event = await stats.to_event(year, round)
        session = await stats.load_session(event, 'R', laps=True)
        stints = await stats.tyre_stints(session, driver)

        if driver:
            table = stints.to_string()
        else:
            # Group data as pivot table with laps driven per compound and indexed by driver
            # Does not show individual stints but total laps for each compound.
            pivot = pd.pivot_table(stints, values="Laps",
                                   index=["Driver"],
                                   columns="Compound",
                                   aggfunc="sum").fillna(0).astype(int)
            table = utils.make_table(pivot, showindex=True)

        await MessageTarget(ctx).send(embed=Embed(
            title=f"**Race Tyre Stints - {event['EventName']} ({event['EventDate'].year})**",
            description=f"```\n{table}\n```"
        ))

    @sectors.error
    @laptimes.error
    @stints.error
    async def on_application_command_error(self, ctx: ApplicationContext, err: ApplicationCommandError):
        """Specifically handle error loading laps data if the session is not supported."""
        if isinstance(err.__cause__, errors.MissingDataError):
            logger.error(f"Command {ctx.command} failed with\n {err}")
            await MessageTarget(ctx).send(f":x: {err.__cause__.message}")
        else:
            raise err

    @commands.slash_command(description="Details and countdown to the next race weekend.")
    async def next(self, ctx: ApplicationContext):
        result = await ergast.get_next_race()

        # Extract wiki data and country flag for use in embed
        page_url = str(result['url']).replace(f"{result['season']}_", '')
        flag_img_task = asyncio.create_task(
            utils.get_wiki_thumbnail(f"/{result['data']['Country']}")
        )

        date, time = result['data']['Date'], result['data']['Time']
        ts = datetime.strptime(f"{date} {time}", "%d %b %Y %H:%M %Z").timestamp()
        cd = str(result['countdown']).split(', ')

        emd = Embed(
            title=f"**{result['data']['Name']}**",
            description=f"{cd[0]}, {cd[1]}, {cd[2]}",
            url=page_url,
            colour=utils.F1_RED,
        )
        emd.set_thumbnail(url=await flag_img_task)
        emd.set_author(name="View schedule", url="https://f1calendar.com/")
        emd.add_field(name='Circuit', value=result['data']['Circuit'], inline=False)
        emd.add_field(name='Round', value=result['data']['Round'], inline=True)
        emd.add_field(name='Country', value=result['data']['Country'], inline=True)
        emd.add_field(name='Date', value=f"<t:{int(ts)}>", inline=False)

        await MessageTarget(ctx).send(embed=emd)

    @commands.slash_command(description="Career stats for a driver.")
    async def career(ctx: ApplicationContext, driver: options.DriverOption):
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

        driver = await ergast.get_driver_info(driver)
        result = await ergast.get_driver_career(driver)
        thumb_url_task = asyncio.create_task(utils.get_wiki_thumbnail(driver['url']))
        season_list = result['data']['Seasons']['years']
        champs_list = result['data']['Championships']['years']

        embed = Embed(
            title=f"**{result['driver']['firstname']} {result['driver']['surname']} Career**",
            url=result['driver']['url'],
            colour=utils.F1_RED,
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


def setup(bot: discord.Bot):
    bot.add_cog(Race(bot))
