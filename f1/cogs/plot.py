import logging
from io import BytesIO

import discord
from discord.commands import ApplicationContext
from discord.ext import commands

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
    """Generates a `discord.File` object without saving to disk. Takes a plot figure and
        saves it to a `BytesIO` memory buffer as `name` to create the File.
        """
    with BytesIO() as buffer:
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        file = discord.File(buffer, filename=f"{name}.png")
        return file


class Plot(commands.Cog, guild_ids=Config().guilds):

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    plot = discord.SlashCommandGroup(
        name="plot",
        description="Commands for plotting charts"
    )

    @plot.command(description="Plot tyre compound stints. Only 2018 or later supported.")
    async def stints(self, ctx, year: options.SeasonOption, round: options.RoundOption):
        """Get a stacked barh chart displaying tyre compound stints for each driver."""

        # Load race session and lap data
        event = await stats.to_event(year, round)
        session = await stats.load_session(event, 'R', laps=True)
        data = await stats.tyre_stints(session)

        # Get driver labels
        drivers = [session.get_driver(d)["Abbreviation"] for d in session.drivers]

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(5, 8), dpi=300.0)

        for driver in drivers:
            stints = data.loc[data["Driver"] == driver]

            prev_stint_end = 0
            # Iterate each stint per driver
            for i, r in stints.iterrows():
                # Plot the stint compound and laps to the bar stack
                plt.barh(
                    y=driver,
                    width=r["Laps"],
                    height=0.5,
                    left=prev_stint_end,
                    color=fastf1.plotting.COMPOUND_COLORS[r["Compound"]],
                    edgecolor="black",
                    fill=True
                )
                # Update the end lap to stack the next stint
                prev_stint_end += r["Laps"]

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

        file = plot_to_file(fig, f"plot_stints_{yr}_{rd}")
        await MessageTarget(ctx).send(file=file)

    async def cog_command_error(self, ctx: ApplicationContext, error: discord.ApplicationCommandError):
        if isinstance(error.__cause__, MissingDataError):
            logger.error(f"/{ctx.command} failed with\n {error}")
            await MessageTarget(ctx).send(f":x: {error.__cause__.message}")
        else:
            raise error


def setup(bot: discord.Bot):
    bot.add_cog(Plot(bot))
