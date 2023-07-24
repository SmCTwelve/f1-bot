import logging

import discord
import fastf1.plotting
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from discord.commands import ApplicationContext
from discord.ext import commands
from fastf1.core import Laps
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, Normalize

from f1 import options, utils
from f1.api import ergast, stats
from f1.config import Config
from f1.errors import MissingDataError
from f1.target import MessageTarget

logger = logging.getLogger("f1-bot")

# Set the DPI of the figure image output; discord preview seems sharper at higher value
DPI = 300


class Plot(commands.Cog, guild_ids=Config().guilds):
    """Commands to create charts from race data."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    fastf1.plotting.setup_mpl(misc_mpl_mods=False, mpl_timedelta_support=True)
    plot = discord.SlashCommandGroup(
        name="plot",
        description="Commands for plotting charts"
    )

    @plot.command(description="Plot race tyre stints. Only 2018 or later.")
    async def stints(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Get a stacked barh chart displaying tyre compound stints for each driver."""

        await utils.check_season(ctx, year)

        # Load race session and lap data
        event = await stats.to_event(year, round)
        session = await stats.load_session(event, "R", laps=True)
        data = await stats.tyre_stints(session)

        # Get driver labels
        drivers = [session.get_driver(d)["Abbreviation"] for d in session.drivers]

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(5, 8), dpi=DPI)

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
        f = utils.plot_to_file(fig, f"plot_stints-{yr}-{rd}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="Plot driver position changes in the race.")
    async def position(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Line graph per driver showing position for each lap."""

        await utils.check_season(ctx, year)

        # Load the data
        ev = await stats.to_event(year, round)
        session = await stats.load_session(ev, "R", laps=True)

        fig, ax = plt.subplots(figsize=(8.5, 5.46), dpi=DPI)

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
        plt.tick_params(axis="y", right=True, left=True, labelleft=True, labelright=False)
        ax.invert_yaxis()
        ax.legend(bbox_to_anchor=(1.01, 1.0))
        plt.tight_layout()

        # Create image
        f = utils.plot_to_file(fig, f"plot_pos-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="Show a bar chart comparing fastest laps in the session.")
    async def fastestlaps(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                          session: options.SessionOption):
        """Bar chart for each driver's fastest lap in `session`."""
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, session, laps=True)

        drivers = s.laps["Driver"].unique()

        # Get the fastest lap per driver
        fastest_laps = Laps(
            [s.laps.pick_driver(d).pick_fastest() for d in drivers]
        ).sort_values(by="LapTime").reset_index(drop=True)

        # Calculate the deltas to the fastest overall lap in the session
        top = fastest_laps.pick_fastest()
        fastest_laps["Delta"] = fastest_laps["LapTime"] - top["LapTime"]

        # Map each driver to their team colour
        clr = [fastf1.plotting.team_color(t) for t in fastest_laps["Team"].values]

        # Plotting
        fig, ax = plt.subplots(figsize=(8, 6.75), dpi=DPI)
        bars = ax.barh(fastest_laps["Driver"], fastest_laps["Delta"], color=clr)

        # Place a label next to each bar showing the delta in seconds

        bar_labels = [f"{d.total_seconds():.3f}" for d in fastest_laps["Delta"]]
        bar_labels[0] = ""
        ax.bar_label(bars,
                     labels=bar_labels,
                     label_type="edge",
                     fmt="%.3f",
                     padding=5,
                     fontsize=8)
        # Adjust xaxis to fit
        ax.set_xlim(right=fastest_laps["Delta"].max() + pd.Timedelta(seconds=0.5))

        ax.invert_yaxis()
        ax.grid(True, which="major", axis="x", zorder=0, alpha=0.2)
        plt.xlabel("Time Delta")
        plt.title(f"{s.name} - {ev['EventName']} ({ev['EventDate'].year})")
        plt.suptitle(f"Fastest: {utils.format_timedelta(top['LapTime'])} ({top['Driver']})")
        plt.tight_layout()

        f = utils.plot_to_file(fig, f"plt_fastlap-{s.name}-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="View driver speed on track.")
    async def track_speed(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                          driver: options.DriverOption):
        """Get the `driver` fastest lap data and use the lap position and speed
        telemetry to produce a track visualisation.
        """
        await utils.check_season(ctx, year)

        if driver is None:
            raise ValueError("Specify a driver.")

        # Load laps and telemetry data
        ev = await stats.to_event(year, round)
        session = await stats.load_session(ev, "R", laps=True, telemetry=True)

        # Filter laps to the driver's fastest and get telemetry for the lap
        drv_id = utils.find_driver(driver, await ergast.get_all_drivers(year, ev["RoundNumber"]))["code"]
        lap = session.laps.pick_driver(drv_id).pick_fastest()
        pos = lap.get_pos_data()
        car = lap.get_car_data()

        # Reshape positional data to 3-d array of [X, Y] segments on track
        # (num of samples) x (sample row) x (x and y pos)
        # Then stack the points to get the beginning and end of each segment so they can be coloured
        points = np.array([pos["X"], pos["Y"]]).T.reshape(-1, 1, 2)
        segs = np.concatenate([points[:-1], points[1:]], axis=1)
        speed = car["Speed"]

        fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(12, 6.75), dpi=DPI)
        ax.axis("off")

        # Create the track outline from pos coordinates
        ax.plot(pos["X"], pos["Y"], color="black", linestyle="-", linewidth=12, zorder=0)

        # Map the segments to colours
        norm = plt.Normalize(speed.min(), speed.max())
        lc = LineCollection(segs, cmap="plasma", norm=norm, linestyle="-", linewidth=5)
        lc.set_array(speed)

        # Plot the coloured speed segments on track
        speed_line = ax.add_collection(lc)

        # Add legend
        cax = fig.add_axes([0.25, 0.05, 0.5, 0.025])
        fig.colorbar(speed_line, cax=cax, location="bottom", label="Speed (km/h)")
        plt.suptitle(f"{drv_id} Track Speed - {ev['EventDate'].year} {ev['EventName']}", size=16)

        f = utils.plot_to_file(fig, f"plot_trackspeed-{drv_id}-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="Compare fastest lap telemetry between two drivers.")
    async def telemetry(self, ctx: ApplicationContext,
                        driver1: discord.Option(str, required=True), driver2: discord.Option(str, default=None),
                        year: options.SeasonOption, round: options.RoundOption, session: options.SessionOption):
        """Plot lap telemetry (speed, distance, rpm, gears, brake) between two driver's fastest lap."""

        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        yr, rd = ev["EventDate"].year, ev["RoundNumber"]
        s = await stats.load_session(ev, session, laps=True, telemetry=True)
        drivers = [driver1, driver2]
        drv_ids = [utils.find_driver(d, await ergast.get_all_drivers(yr, rd))["code"]
                   for d in drivers if d is not None]

        # Get data for each driver
        data: dict[str, pd.DataFrame] = {}
        for d in drv_ids:
            tel = s.laps.pick_driver(d).pick_fastest().get_car_data().add_distance()
            data[d] = tel

        # Determine the x-axis position for each sector divider
        # based on the percentage of each sector time from the total lap time
        fl = s.laps.pick_fastest()
        max_dis = fl["Distance"].max()
        s1_dis = max_dis * (fl["Sector1Time"] / fl["LapTime"])
        s2_dis = s1_dis + max_dis * (fl["Sector2Time"] / fl["LapTime"])

        # Plot 6 subplots for each telemetry graph
        fig, ax = plt.subplots(6, figsize=(18, 14), dpi=DPI,
                               gridspec_kw={"height_ratios": [3, 2, 1, 1, 2, 1]},
                               sharex=True)

        for d, t in data.items():
            c = fastf1.plotting.driver_color(d)
            # Speed
            ax[0].plot(
                t["Distance"].values,
                t["Speed"].values,
                color=c,
                label=d
            )
            # Throttle
            ax[1].plot(
                t["Distance"].values,
                t["Throttle"].values,
                color=c,
                label=d
            )
            # Brake
            ax[2].plot(
                t["Distance"].values,
                t["Brake"].values,
                color=c,
                label=d
            )
            # Gear
            ax[3].plot(
                t["Distance"].values,
                t["nGear"].values,
                color=c,
                label=d
            )
            # RPM
            ax[4].plot(
                t["Distance"].values,
                t["RPM"].values,
                color=c,
                label=d
            )
            # DRS
            ax[5].plot(
                t["Distance"].values,
                t["DRS"].values,
                color=c,
                label=d
            )

        # Presentation
        ax[0].set_ylabel("Speed (kph)")
        ax[0].legend(loc="lower left")
        ax[0].text(s1_dis - 200, ax[0].get_ylim()[0], "S1")
        ax[0].text(s2_dis - 200, ax[0].get_ylim()[0], "S2")
        ax[0].text(max_dis, ax[0].get_ylim()[0], "S3")

        ax[1].set_ylabel("Throttle %")
        ax[2].set_ylabel("Brake")

        ax[3].set_ylabel("Gear")
        ax[3].set_ylim(bottom=1)

        ax[4].set_ylabel("RPM")

        ax[5].set_ylabel("DRS")
        ax[5].set_yticklabels([""])
        ax[5].set_xlabel("Distance (m)")

        laptimes = [
            utils.format_timedelta(
                s.laps.pick_driver(d).pick_fastest()["LapTime"]
            ) for d in drv_ids
        ]

        ax[0].set_title(
            f"Lap Comparison - {session} - {yr} {ev['EventName']}\n" +
            f"{drv_ids[0]}: {laptimes[0]}" +
            f" | {drv_ids[1]}: {laptimes[1]}" if len(laptimes) > 1 else ""
        ).set_fontsize(18)

        # Show sector dividers
        for a in ax:
            a.yaxis.label.set_fontsize(13)
            ylim = a.get_ylim()
            a.vlines([s1_dis, s2_dis], ylim[0], ylim[1], colors="w",
                     linestyles="dotted", linewidth=1, zorder=0, alpha=0.5)

        # File
        f = utils.plot_to_file(fig, f"plt_telemetry_{yr}_{rd}_{'-'.join(drv_ids)}")
        await MessageTarget(ctx).send(file=f, content="**Lap Telemetry**")

    @plot.command(description="Compare fastest driver sectors on track map.")
    async def track_sectors(self, ctx: ApplicationContext, first_driver: options.DriverOptionRequired,
                            second_driver: options.DriverOptionRequired, year: options.SeasonOption,
                            round: options.RoundOption, session: options.SessionOption):
        """Plot a track map showing where a driver was faster based on minisectors."""
        await utils.check_season(ctx, year)
        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, session, laps=True, telemetry=True)

        # Check API support
        if not s.f1_api_support:
            raise MissingDataError("Session does not support lap data.")

        yr, rd = ev["EventDate"].year, ev["RoundNumber"]
        drivers = [utils.find_driver(d, await ergast.get_all_drivers(yr, rd))["code"]
                   for d in (first_driver, second_driver)]

        # Get telemetry and minisectors for each driver
        telemetry = stats.minisectors([
            s.laps.pick_driver(d).pick_fastest()
            for d in drivers
        ])

        # Get the mean time for each minisector per driver
        mTimes = telemetry.groupby(["mSector", "Driver"])["Time"].mean().reset_index()

        # Find the fastest driver in each minisector
        fastest = mTimes.loc[
            mTimes.groupby(["mSector"])["Time"].idxmin(),
            ["mSector", "Driver"]
        ].rename(columns={"Driver": "Fastest"})
        telemetry = telemetry.merge(fastest, on=["mSector"]).sort_values(by=["Distance"])

        # Assign fastest driver to int for plotting
        telemetry.loc[telemetry["Fastest"] == drivers[0], ["Fastest"]] = 1
        telemetry.loc[telemetry["Fastest"] == drivers[1], ["Fastest"]] = 2

        # Reshape positional data to 3-d array of [X, Y] segments on track
        # (num of samples) x (sample row) x (x and y pos)
        # Then stack the points to get the beginning and end of each segment so they can be coloured
        points = np.array([telemetry["X"].values, telemetry["Y"].values]).T.reshape(-1, 1, 2)
        segs = np.concatenate([points[:-1], points[1:]], axis=1)
        fastest_drivers = telemetry["Fastest"].astype(float).values

        fig, ax = plt.subplots(sharex=True, sharey=True, figsize=(10, 8), dpi=DPI)
        ax.axis("off")

        # Create track outline from pos
        ax.plot(telemetry["X"].values, telemetry["Y"].values,
                color="black",
                linestyle="-",
                linewidth=12,
                zorder=0)

        # Map minisector segments to fastest driver colour
        cmap = ListedColormap([fastf1.plotting.driver_color(d) for d in drivers])
        lc = LineCollection(segs, norm=Normalize(1, cmap.N + 1), cmap=cmap, linestyle="-", linewidth=4)
        lc.set_array(fastest_drivers)

        # Add sectors to plot
        sectors = ax.add_collection(lc)

        # Add colorbar legend
        cax = fig.add_axes([0.15, 0.1, 0.1, 0.02])
        fig.colorbar(sectors, cax=cax, location="bottom", ticks=[1.5, 2.5]).set_ticklabels([d for d in drivers])
        ax.set_title(
            f"Fastest Sectors | {drivers[0]} v {[drivers[1]]}\n{yr} {ev['EventName']} - {session}"
        ).set_fontsize(12)

        f = utils.plot_to_file(fig, f"plt_trksectors_{yr}_{rd}")
        await MessageTarget(ctx).send(file=f, content="**Fastest Sector Comparison**")

    @plot.command(description="Show the position gains/losses per driver in the race.")
    async def gains(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Plot each driver position change from starting grid position to finish position as a bar chart."""

        await utils.check_season(ctx, year)

        # Load session results data
        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, "R")
        data = stats.pos_change(s)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=DPI)

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
        plt.ylabel("Change")
        ax.grid(True, alpha=0.1)
        plt.tight_layout()

        f = utils.plot_to_file(fig, f"plot_poschange-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(name="tyre-choice", description="Percentage distribution of tyre compounds.")
    async def tyre_choice(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption,
                          session: options.SessionOption):
        """Plot the distribution of tyre compound for all laps in the session."""
        await utils.check_season(ctx, year)

        # Get lap data and count occurance of each compound
        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, session, laps=True)
        t_count = s.laps["Compound"].value_counts()

        # Calculate percentages and sort
        t_percent = t_count / len(s.laps) * 100
        sorted_count = t_count.sort_values(ascending=False)
        sorted_percent = t_percent.loc[sorted_count.index]

        # Get tyre colours
        clrs = [fastf1.plotting.COMPOUND_COLORS[i] for i in sorted_count.index]

        fig, ax = plt.subplots(figsize=(8, 6), dpi=DPI, subplot_kw={"aspect": "equal"})
        ax.pie(sorted_percent, colors=clrs, autopct="%1.1f%%", textprops={"color": "black"})

        plt.legend(sorted_count.index)
        plt.title(f"Tyre Distribution - {session}\n{ev['EventName']} ({ev['EventDate'].year})")
        plt.tight_layout()

        f = utils.plot_to_file(fig, f"plt_tyrechoice-{ev['RoundNumber']}-{ev['EventDate'].year}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="Compare laptime difference between two drivers.")
    async def gap(self, ctx: ApplicationContext,
                  first: options.DriverOptionRequired, second: options.DriverOptionRequired,
                  year: options.SeasonOption, round: options.RoundOption):
        """Plot the lap times between two drivers for all laps, excluding pitstops and slow laps."""
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, "R", laps=True, telemetry=True)
        # Get driver codes from the identifiers given
        drivers = [await utils.find_driver(d, await ergast.get_all_drivers(year, ev["RoundNumber"]))["code"]
                   for d in (first, second)]

        # Group laps using only quicklaps to exclude pitstops and slow laps
        laps = s.laps.pick_drivers(drivers).pick_quicklaps()
        times = laps.loc[:, ["Driver", "LapNumber", "LapTime"]].groupby("Driver")

        fig, ax = plt.subplots(figsize=(8, 5), dpi=DPI)

        for d, t in times:
            ax.plot(
                t["LapNumber"],
                t["LapTime"],
                label=d,
                color=fastf1.plotting.driver_color(d)
            )

        plt.title(f"Lap Difference -\n{ev['EventName']} ({ev['EventDate'].year})")
        plt.xlabel("Lap")
        plt.ylabel("Time")
        ax.grid(True, alpha=0.1)
        plt.legend()

        f = utils.plot_to_file(
            fig, f"plt_comparelaps-{drivers[0]}{drivers[1]}-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(name="lap-distribution",
                  description="Violin plot comparing distribution of laptimes on different tyres.")
    async def lap_distribution(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Plot a swarmplot and violin plot showing laptime distributions and tyre compound
        for the top 10 point finishers."""
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, "R", laps=True)

        # Get the point finishers
        point_finishers = s.drivers[:10]

        laps = s.laps.pick_drivers(point_finishers).pick_quicklaps().set_index("Driver")
        # Convert laptimes to seconds for seaborn compatibility
        laps["LapTime (s)"] = laps["LapTime"].dt.total_seconds()
        labels = [s.get_driver(d)["Abbreviation"] for d in point_finishers]
        compounds = laps["Compound"].unique()

        fig, ax = plt.subplots(figsize=(10, 5), dpi=DPI)

        sns.violinplot(data=laps,
                       x=laps.index,
                       y="LapTime (s)",
                       inner=None,
                       scale="area",
                       order=labels,
                       palette=[fastf1.plotting.driver_color(d) for d in labels])

        sns.swarmplot(data=laps,
                      x="Driver",
                      y="LapTime (s)",
                      order=labels,
                      hue="Compound",
                      palette=[fastf1.plotting.COMPOUND_COLORS[c] for c in compounds],
                      linewidth=0,
                      size=5)

        ax.set_xlabel("Driver (Point Finishers)")
        plt.title(f"Lap Distribution - {ev['EventName']} ({ev['EventDate'].year})")
        sns.despine(left=True, right=True)

        f = utils.plot_to_file(fig, f"plt_lapdist-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(name="tyre-performance",
                  description="Plot the performance of each tyre compound based on the age of the tyre.")
    async def tyreperf(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Plot a line graph showing the performance of each tyre compound based on the age of the tyre."""
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, "R", laps=True)

        data = stats.tyre_performance(s)
        compounds = data["Compound"].unique()

        fig, ax = plt.subplots(figsize=(10, 5), dpi=DPI)

        for cmp in compounds:
            mask = data["Compound"] == cmp
            ax.plot(
                data.loc[mask, "TyreLife"].values,
                data.loc[mask, "Seconds"].values,
                label=cmp,
                color=fastf1.plotting.COMPOUND_COLORS[cmp]
            )

        plt.xlabel("Tyre Life")
        plt.ylabel("Lap Time (s)")
        plt.title(f"Tyre Performance - {ev['EventDate'].year} {ev['EventName']}")
        plt.tight_layout()

        f = utils.plot_to_file(fig, f"plt_tyreperf-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    async def cog_command_error(self, ctx: ApplicationContext, error: discord.ApplicationCommandError):
        """Handle loading errors from unsupported API lap data."""
        if isinstance(error.__cause__, MissingDataError):
            logger.error(f"/{ctx.command} failed with\n {error}")
            await MessageTarget(ctx).send(f":x: {error.__cause__.message}")
        else:
            raise error


def setup(bot: discord.Bot):
    bot.add_cog(Plot(bot))
