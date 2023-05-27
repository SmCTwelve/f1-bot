import logging
from io import BytesIO

import discord
from discord.commands import ApplicationContext
from discord.ext import commands

import numpy as np
import fastf1.plotting
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from f1 import options
from f1.api import stats
from f1.config import Config
from f1.target import MessageTarget
from f1.errors import MissingDataError

logger = logging.getLogger("f1-bot")


def plot_to_file(fig: Figure, name: str):
    """Generates a `discord.File` object without saving to disk. Takes a plot Figure and
        saves it to a `BytesIO` memory buffer as `name`.
        """
    with BytesIO() as buffer:
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        file = discord.File(buffer, filename=f"{name}.png")
        return file


class Plot(commands.Cog, guild_ids=Config().guilds):
    """Commands to create charts from race data."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    fastf1.plotting.setup_mpl(misc_mpl_mods=False)

    plot = discord.SlashCommandGroup(
        name="plot",
        description="Commands for plotting charts"
    )

    @plot.command(description="Plot race tyre stints. Only 2018 or later.")
    async def stints(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Get a stacked barh chart displaying tyre compound stints for each driver."""

        # Load race session and lap data
        event = await stats.to_event(year, round)
        session = await stats.load_session(event, 'R', laps=True)
        data = await stats.tyre_stints(session)

        # Get driver labels
        drivers = [session.get_driver(d)["Abbreviation"] for d in session.drivers]

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(5, 8), dpi=300)

        for driver in drivers:
            stints = data.loc[data["Driver"] == driver]

            prev_stint_end = 0
            # Iterate each stint per driver
            for r in stints.itertuples():
                # Plot the stint compound and laps to the bar stack
                plt.barh(
                    y=driver,
                    width=r.Laps,
                    height=0.5,
                    left=prev_stint_end,
                    color=fastf1.plotting.COMPOUND_COLORS[r.Compound],
                    edgecolor="black",
                    fill=True
                )
                # Update the end lap to stack the next stint
                prev_stint_end += r.Laps

        # Get compound colors for legend
        patches = [
            mpatches.Patch(color=fastf1.plotting.COMPOUND_COLORS[c], label=c)
            for c in data["Compound"].unique()
        ]

        # Presentation
        yr, rd = event['EventDate'].year, event['RoundNumber']
        plt.title(f"Race Tyre Stints - \n {event['EventName']} ({yr})")
        plt.xlabel("Lap Number"),
        plt.grid(False)
        plt.legend(handles=patches)
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        plt.tight_layout()

        # Get plot image
        file = plot_to_file(fig, f"plot_stints-{yr}-{rd}")
        await MessageTarget(ctx).send(file=file)

    @plot.command(description="Plot driver position changes in the race.")
    async def position(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Line graph per driver showing position for each lap."""
        # Load the data
        ev = await stats.to_event(year, round)
        session = await stats.load_session(ev, 'R', laps=True)

        fig, ax = plt.subplots(figsize=(8.5, 5.46), dpi=300)

        # Plot the drivers position per lap
        for d in session.drivers:
            laps = session.laps.pick_driver(d)
            id = laps["Driver"].iloc[0]
            ax.plot(laps["LapNumber"], laps["Position"], label=id, color=fastf1.plotting.driver_color(id))

        # Presentation
        plt.title(f"Race Position - {ev['EventName']} ({ev['EventDate'].year})")
        plt.xlabel("Lap")
        plt.ylabel("Position")
        plt.yticks(np.arange(1, len(session.drivers) + 1))
        plt.tick_params(axis='y', right=True, left=True, labelleft=True, labelright=False)
        ax.invert_yaxis()
        ax.legend(bbox_to_anchor=(1.01, 1.0))
        plt.tight_layout()

        # Create image
        file = plot_to_file(fig, f"plot_pos-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=file)

    @plot.command(description="Show a bar chart comparing fastest laps in the session.")
    async def fastestlap(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                         session: options.SessionOption):
        """Bar chart for each driver's fastest lap in `session`."""
        pass

    @plot.command(description="Plot track sector speed or time for a driver (2018 or later).")
    async def sectors(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                      driver: options.DriverOption, data: options.SectorFilter):
        """Plot per sector times for best lap, worst lap or average of all laps as bar chart."""
        # Pick the best/worst lap or use .mean
        # Get the SectorXTime/Speeds
        pass

    @plot.command(description="Plot the fastest lap speed telemetry on track.")
    async def telemetry(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                        driver: options.DriverOption):
        """Get the `driver` fastest lap data and use the lap position and speed
        telemetry to produce a track speed visualisation.
        """
        # Pick driver's fastest lap
        # Load lap telemetry

        pass

    @plot.command(description="Compare the lap speed of up to 4 drivers.")
    async def speed(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                    drivers: str):
        """Compare up to 4 drivers fastest lap speed as a line graph."""
        # drivers option should be a list with max=4 min of 1

        pass

    @plot.command(description="Display on track gear shifts of the driver's fastest lap.")
    async def gears(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                    driver: options.DriverOption):
        """Load fastest lap telemetry and plot position and gear as a track map."""
        pass

    @plot.command(description="Show the position gains/losses per driver in the race.")
    async def gains(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Plot each driver position change from starting grid position to finish position as a bar chart."""

        # Load session results data
        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, 'R')
        data = stats.pos_change(s)

        fig, ax = plt.subplots(figsize=(12, 5), dpi=300)

        # Plot pos diff for each driver
        for row in data.itertuples():
            bar = plt.bar(
                x=row.Driver,
                height=row.Diff,
                color="firebrick" if int(row.Diff) < 0 else "forestgreen",
                label=row.Diff,
            )
            ax.bar_label(bar, label_type="center")

        plt.title(f"Pos Gain/Loss - {ev['EventName']} ({(ev['EventDate'].year)})")
        plt.xlabel("Driver")
        plt.ylabel("Pos Change")
        ax.grid(True, alpha=0.03)
        plt.tight_layout()

        file = plot_to_file(fig, f"plot_poschange-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=file)

    async def cog_command_error(self, ctx: ApplicationContext, error: discord.ApplicationCommandError):
        """Handle loading errors from unsupported API lap data."""
        if isinstance(error.__cause__, MissingDataError):
            logger.error(f"/{ctx.command} failed with\n {error}")
            await MessageTarget(ctx).send(f":x: {error.__cause__.message}")
        else:
            raise error


def setup(bot: discord.Bot):
    bot.add_cog(Plot(bot))
