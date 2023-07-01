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
        table = stats.results_table(data, session)
        table.get_axes()[0].set_title(f"{ev['EventDate'].year} {ev['EventName']} - {session}")

        f = utils.plot_to_file(table, f"results_{s.name}_{ev['EventDate'].year}_{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

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
                       filter: options.LaptimeFilter):
        """Best ranked lap times per driver in the race. All parameters optional.

        Only the best recorded lap for each driver in the race.

        Usage:
        ----------
            /laptimes [season] [round] [filter] \n
            /laptimes 2022 5 fastest
        """
        # TODO:
        # Refactor with `driver` param to apply same filters on all laps per driver

        await utils.check_season(ctx, year)
        event = await stats.to_event(year, round)

        # Fetch and sort laptime data from the race results
        res = await ergast.get_best_laps(event["RoundNumber"], year)
        sorted_times = utils.rank_best_lap_times(res)

        # Apply the ranking - best lap per driver by default
        ranking = str(filter).lower()
        filtered_laps = utils.filter_times(sorted_times, ranking)

        table = utils.make_table(filtered_laps)
        await MessageTarget(ctx).send(embed=Embed(
            title=f"**Laptimes ({filter}) - {res['race']} ({res['season']})**",
            description=f"```\n{table}\n```"
        ))

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


def setup(bot: discord.Bot):
    bot.add_cog(Race(bot))
