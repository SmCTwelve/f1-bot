import logging

import discord
import fastf1.plotting
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from discord.commands import ApplicationContext
from discord.ext import commands
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.figure import Figure

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

        fig = Figure(figsize=(6, 10), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        for driver in drivers:
            stints = data.loc[data["Driver"] == driver]

            prev_stint_end = 0
            # Iterate each stint per driver
            for r in stints.itertuples():
                # Plot the stint compound and laps to the bar stack
                ax.barh(
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
        ax.set_title(f"Race Tyre Stints - \n {event['EventName']} ({yr})")
        ax.set_xlabel("Lap Number"),
        ax.grid(False)
        ax.legend(handles=patches, loc="upper center", ncols=len(patches))
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

        del event, session, data

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

        fig = Figure(figsize=(8.5, 5.46), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        # Plot the drivers position per lap
        for d in session.drivers:
            laps = session.laps.pick_drivers(d)
            id = laps["Driver"].iloc[0]
            ax.plot(laps["LapNumber"], laps["Position"], label=id,
                    color=utils.get_driver_or_team_color(id, session, api_only=True))

        # Presentation
        ax.set_title(f"Race Position - {ev['EventName']} ({ev['EventDate'].year})")
        ax.set_xlabel("Lap")
        ax.set_ylabel("Position")
        ax.set_yticks(np.arange(1, len(session.drivers) + 1))
        ax.tick_params(axis="y", right=True, left=True, labelleft=True, labelright=False)
        ax.invert_yaxis()
        ax.legend(bbox_to_anchor=(1.01, 1.0))

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

        # Get the fastest lap per driver
        fastest_laps = stats.fastest_laps(s)
        top = fastest_laps.iloc[0]

        # Map each driver to their team colour
        clr = [utils.get_driver_or_team_color(d, s, api_only=True)
               for d in fastest_laps["Driver"].values]

        # Plotting
        fig = Figure(figsize=(8, 6.75), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()
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
        ax.set_xlabel("Time Delta")
        ax.set_title(f"{s.name} - {ev['EventName']} ({ev['EventDate'].year})")
        fig.suptitle(f"Fastest: {top['LapTime']} ({top['Driver']})")

        f = utils.plot_to_file(fig, f"plt_fastlap-{s.name}-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(name="track-speed", description="View driver speed on track.")
    async def track_speed(self, ctx: ApplicationContext, driver: options.DriverOptionRequired(),
                          year: options.SeasonOption, round: options.RoundOption):
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
        lap = session.laps.pick_drivers(drv_id).pick_fastest()
        pos = lap.get_pos_data()
        car = lap.get_car_data()

        # Reshape positional data to 3-d array of [X, Y] segments on track
        # (num of samples) x (sample row) x (x and y pos)
        # Then stack the points to get the beginning and end of each segment so they can be coloured
        points = np.array([pos["X"], pos["Y"]]).T.reshape(-1, 1, 2)
        segs = np.concatenate([points[:-1], points[1:]], axis=1)
        speed = car["Speed"]
        del lap, car

        fig = Figure(figsize=(12, 6.75), dpi=DPI, layout="constrained")
        ax = fig.subplots(sharex=True, sharey=True)
        ax.axis("off")

        # Create the track outline from pos coordinates
        ax.plot(pos["X"], pos["Y"], color="black", linestyle="-", linewidth=12, zorder=0)

        # Map the segments to colours
        norm = Normalize(speed.min(), speed.max())
        lc = LineCollection(segs, cmap="plasma", norm=norm, linestyle="-", linewidth=5)
        lc.set_array(speed)

        # Plot the coloured speed segments on track
        speed_line = ax.add_collection(lc)

        # Add legend
        cax = fig.add_axes([0.25, 0.05, 0.5, 0.025])
        fig.colorbar(speed_line, cax=cax, location="bottom", label="Speed (km/h)")
        fig.suptitle(f"{drv_id} Track Speed - {ev['EventDate'].year} {ev['EventName']}", size=16)

        f = utils.plot_to_file(fig, f"plot_trackspeed-{drv_id}-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="Compare fastest lap telemetry between two drivers.")
    async def telemetry(self, ctx: ApplicationContext,
                        driver1: discord.Option(str, required=True), driver2: discord.Option(str, default=None),
                        year: options.SeasonOption, round: options.RoundOption, session: options.SessionOption):
        """Plot lap telemetry (speed, distance, rpm, gears, brake) between two driver's fastest lap."""

        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        yr, rd, nm = ev["EventDate"].year, ev["RoundNumber"], ev["EventName"]
        s = await stats.load_session(ev, session, laps=True, telemetry=True)
        drivers = [driver1, driver2]
        drv_ids = [utils.find_driver(d, await ergast.get_all_drivers(yr, rd))["code"]
                   for d in drivers if d is not None]

        # Get data for each driver
        data: dict[str, pd.DataFrame] = {}
        laptimes = []
        for d in drv_ids:
            if d not in s.laps["Driver"].unique():
                raise MissingDataError(f"No lap data for driver {d}")
            lap = s.laps.pick_drivers(d).pick_fastest()
            laptimes.append(lap["LapTime"])
            data[d] = lap.get_car_data().add_distance()
            del lap

        # Determine the x-axis position for each sector divider
        # based on the percentage of each sector time from the total lap time
        fl = s.laps.pick_fastest()
        max_dis = data[drv_ids[0]]["Distance"].max()
        s1_dis = max_dis * (fl["Sector1Time"] / fl["LapTime"])
        s2_dis = s1_dis + max_dis * (fl["Sector2Time"] / fl["LapTime"])
        del fl

        # Plot 6 subplots for each telemetry graph
        fig = Figure(figsize=(18, 14), dpi=DPI, layout="constrained")
        ax = fig.subplots(7, gridspec_kw={"height_ratios": [3, 2, 1, 1.25, 2, 1, 1.35]},
                          sharex=True)

        for d, t in data.items():
            c = utils.get_driver_or_team_color(d, s)
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

        # Plot delta when comparing two drivers
        if driver2:
            delta = stats.compare_lap_telemetry_delta(data[drv_ids[0]], data[drv_ids[1]])
            ax[6].plot(
                data[drv_ids[0]]["Distance"].values,
                delta,
                linestyle="--",
                color="w"
            )
            ax[6].set_ylabel(f"<- {drv_ids[1]} | {drv_ids[0]} ->")
            ax[6].axhline(0, linestyle="--", linewidth=0.5, color="w", zorder=0, alpha=0.5)

        del data

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
        ax[5].set_yticks([0.0, 15.0])
        ax[5].set_yticklabels([])
        ax[5].set_xlabel("Distance (m)")

        # Show sector dividers
        for a in ax:
            a.yaxis.label.set_fontsize(13)
            ylim = a.get_ylim()
            a.vlines([s1_dis, s2_dis], ylim[0], ylim[1], colors="w",
                     linestyles="dotted", linewidth=1, zorder=0, alpha=0.5)

        ax[0].set_title("".join([
            f"Lap Comparison - {session} - {yr} {nm}",
            f"\n{drv_ids[0]}: {utils.format_timedelta(laptimes[0])}",
            (f" | {drv_ids[1]}: {utils.format_timedelta(laptimes[1])}"
             if len(laptimes) > 1 else "")
        ])).set_fontsize(18)

        # File
        f = utils.plot_to_file(fig, f"plt_telemetry_{yr}_{rd}_{'-'.join(drv_ids)}")
        await MessageTarget(ctx).send(file=f, content="**Lap Telemetry**")

    @plot.command(name="track-sectors", description="Compare fastest driver sectors on track map.")
    async def track_sectors(self, ctx: ApplicationContext, first: options.DriverOptionRequired(),
                            second: options.DriverOptionRequired(), year: options.SeasonOption,
                            round: options.RoundOption, session: options.SessionOption,
                            lap: options.LapOption):
        """Plot a track map showing where a driver was faster based on minisectors."""
        await utils.check_season(ctx, year)
        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, session, laps=True, telemetry=True)

        # Check API support
        if not s.f1_api_support:
            raise MissingDataError("Session does not support lap data.")

        # Check lap number is valid and within range
        if lap and (not str(lap).isdigit() or int(lap) > s.total_laps):
            raise ValueError("Lap number out of range.")

        yr, rd = ev["EventDate"].year, ev["RoundNumber"]
        drivers = [utils.find_driver(d, await ergast.get_all_drivers(yr, rd))["code"]
                   for d in (first, second)]

        # Get telemetry and minisectors for each driver
        telemetry = stats.minisectors([
            s.laps.pick_drivers(d).pick_laps(int(lap)).iloc[0] if lap else
            s.laps.pick_drivers(d).pick_fastest()
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
        del mTimes, fastest

        # Assign fastest driver to int for plotting
        telemetry.loc[telemetry["Fastest"] == drivers[0], ["Fastest"]] = 1
        telemetry.loc[telemetry["Fastest"] == drivers[1], ["Fastest"]] = 2

        # Reshape positional data to 3-d array of [X, Y] segments on track
        # (num of samples) x (sample row) x (x and y pos)
        # Then stack the points to get the beginning and end of each segment so they can be coloured
        points = np.array([telemetry["X"].values, telemetry["Y"].values]).T.reshape(-1, 1, 2)
        segs = np.concatenate([points[:-1], points[1:]], axis=1)
        fastest_drivers = telemetry["Fastest"].astype(float).values

        fig = Figure(figsize=(10, 8), dpi=DPI, layout="constrained")
        ax = fig.subplots(sharex=True, sharey=True)
        ax.axis("off")

        # Create track outline from pos
        ax.plot(telemetry["X"].values, telemetry["Y"].values,
                color="black",
                linestyle="-",
                linewidth=12,
                zorder=0)

        del telemetry

        # Map minisector segments to fastest driver colour
        cmap = ListedColormap([utils.get_driver_or_team_color(d, s) for d in drivers])
        lc = LineCollection(segs, norm=Normalize(1, cmap.N + 1), cmap=cmap, linestyle="-", linewidth=4)
        lc.set_array(fastest_drivers)

        # Add sectors to plot
        sectors = ax.add_collection(lc)

        # Add colorbar legend
        cax = fig.add_axes([0.05, 0.05, 0.1, 0.02])
        fig.colorbar(sectors, cax=cax, location="bottom", ticks=[1.5, 2.5]).set_ticklabels([d for d in drivers])
        lap_label = f"{lap}" if lap else "Fastest"
        ax.set_title(
            f"Fastest Sectors | {drivers[0]} v {drivers[1]} | (L: {lap_label}))\n{yr} {ev['EventName']} - {session}"
        ).set_fontsize(14)

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

        fig = Figure(figsize=(10, 5), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        # Plot pos diff for each driver
        for row in data.itertuples():
            bar = ax.bar(
                x=row.Driver,
                height=row.Diff,
                color="firebrick" if int(row.Diff) < 0 else "forestgreen",
                label=row.Diff,
            )
            ax.bar_label(bar, label_type="center")
        del data

        ax.set_title(f"Pos Gain/Loss - {ev['EventName']} ({(ev['EventDate'].year)})")
        ax.set_xlabel("Driver")
        ax.set_ylabel("Change")
        ax.grid(True, alpha=0.1)

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

        fig = Figure(figsize=(8, 6), dpi=DPI, layout="constrained")
        ax = fig.add_subplot(aspect="equal")

        ax.pie(sorted_percent, colors=clrs, autopct="%1.1f%%", textprops={"color": "black"})

        ax.legend(sorted_count.index)
        ax.set_title(f"Tyre Distribution - {session}\n{ev['EventName']} ({ev['EventDate'].year})")

        f = utils.plot_to_file(fig, f"plt_tyrechoice-{ev['RoundNumber']}-{ev['EventDate'].year}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(name="lap-compare", description="Compare laptime difference between two drivers.")
    async def compare_laps(self, ctx: ApplicationContext,
                           first: options.DriverOptionRequired(),
                           second: options.DriverOptionRequired(),
                           year: options.SeasonOption, round: options.RoundOption):
        """Plot the lap times between two drivers for all laps, excluding pitstops and slow laps."""
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, "R", laps=True, telemetry=True)
        # Get driver codes from the identifiers given
        drivers = [utils.find_driver(d, await ergast.get_all_drivers(year, ev["RoundNumber"]))["code"]
                   for d in (first, second)]

        # Group laps using only quicklaps to exclude pitstops and slow laps
        laps = s.laps.pick_drivers(drivers).pick_quicklaps()
        times = laps.loc[:, ["Driver", "LapNumber", "LapTime"]].groupby("Driver")
        del laps

        fig = Figure(figsize=(8, 5), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        for d, t in times:
            ax.plot(
                t["LapNumber"],
                t["LapTime"],
                label=d,
                color=utils.get_driver_or_team_color(d, s)
            )
        del times

        ax.set_title(f"Lap Difference -\n{ev['EventName']} ({ev['EventDate'].year})")
        ax.set_xlabel("Lap")
        ax.set_ylabel("Time")
        ax.grid(True, alpha=0.1)
        ax.legend()

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

        fig = Figure(figsize=(10, 5), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        sns.violinplot(data=laps,
                       x=laps.index,
                       y="LapTime (s)",
                       inner=None,
                       scale="area",
                       order=labels,
                       palette=[utils.get_driver_or_team_color(d, s) for d in labels])

        sns.swarmplot(data=laps,
                      x="Driver",
                      y="LapTime (s)",
                      order=labels,
                      hue="Compound",
                      palette=[fastf1.plotting.COMPOUND_COLORS[c] for c in compounds],
                      linewidth=0,
                      size=5)
        del laps

        ax.set_xlabel("Driver (Point Finishers)")
        ax.set_title(f"Lap Distribution - {ev['EventName']} ({ev['EventDate'].year})")
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

        fig = Figure(figsize=(10, 5), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        for cmp in compounds:
            mask = data["Compound"] == cmp
            ax.plot(
                data.loc[mask, "TyreLife"].values,
                data.loc[mask, "Seconds"].values,
                label=cmp,
                color=fastf1.plotting.COMPOUND_COLORS[cmp]
            )
        del data

        ax.set_xlabel("Tyre Life")
        ax.set_ylabel("Lap Time (s)")
        ax.set_title(f"Tyre Performance - {ev['EventDate'].year} {ev['EventName']}")
        ax.legend()

        f = utils.plot_to_file(fig, f"plt_tyreperf-{ev['EventDate'].year}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)

    @plot.command(description="Plots the delta in seconds between two drivers over a lap.")
    async def gap(self, ctx: ApplicationContext, driver1: options.DriverOptionRequired(),
                  driver2: options.DriverOptionRequired(), year: options.SeasonOption,
                  round: options.RoundOption, session: options.SessionOption, lap: options.LapOption):
        """Get the delta over lap distance between two drivers and return a line plot.

        `driver1` is comparison, `driver2` is reference lap.
        """
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, session, laps=True, telemetry=True)
        yr, rd = ev["EventDate"].year, ev["EventName"]

        # Check lap data support
        if not s.f1_api_support:
            raise MissingDataError("Lap data not available for the session.")

        # Check lap number is valid and within range
        if lap and (not str(lap).isdigit() or int(lap) > s.total_laps):
            raise ValueError("Lap number out of range.")

        # Get drivers
        drivers = [utils.find_driver(d, await ergast.get_all_drivers(year, ev["RoundNumber"]))["code"]
                   for d in (driver1, driver2)]

        # Load each driver lap telemetry
        telemetry = {}
        for d in drivers:
            if lap:
                driver_lap = s.laps.pick_drivers(d).pick_laps(int(lap)).iloc[0]
            else:
                driver_lap = s.laps.pick_drivers(d).pick_fastest()
            telemetry[d] = driver_lap.get_car_data(interpolate_edges=True).add_distance()

        # Get interpolated delta between drivers
        # where driver1 is ref lap and driver2 is compared
        delta = stats.compare_lap_telemetry_delta(telemetry[drivers[1]], telemetry[drivers[0]])

        # Mask the delta values to plot + green and - red
        ahead = np.ma.masked_where(delta >= 0., delta)
        behind = np.ma.masked_where(delta < 0., delta)

        fig = Figure(figsize=(10, 3), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        # Use ref driver distance for X
        lap_label = f"Lap {lap}" if lap else "Fastest Lap"
        x = telemetry[drivers[1]]["Distance"].values
        ax.plot(x, ahead, color="green")
        ax.plot(x, behind, color="red")
        ax.axhline(0.0, linestyle="--", linewidth=0.5, color="w", zorder=0, alpha=0.5)
        ax.set_title(f"{drivers[0]} Delta to {drivers[1]} ({lap_label})\n{yr} {rd} | {session}").set_fontsize(16)
        ax.set_ylabel(f"<-  {drivers[0]}  |  {drivers[1]}  ->")

        f = utils.plot_to_file(fig, f"plt_gap-{yr}-{ev['RoundNumber']}-{session[0]}")
        await MessageTarget(ctx).send(content="**Driver Gap**", file=f)

    @plot.command(name="avg-lap-delta",
                  description="Bar chart comparing average time per driver with overall race average as a delta.")
    async def avg_lap_delta(self, ctx: ApplicationContext, year: options.SeasonOption, round: options.RoundOption):
        """Get the overall average lap time of the session and plot the delta for each driver."""
        await utils.check_season(ctx, year)

        ev = await stats.to_event(year, round)
        s = await stats.load_session(ev, "R", laps=True)
        yr, rd = ev["EventDate"].year, ev["EventName"]

        # Check lap data support
        if not s.f1_api_support:
            raise MissingDataError("Lap data not available for the session.")

        # Get the overall session average
        session_avg: pd.Timedelta = s.laps.pick_wo_box()["LapTime"].mean()

        fig = Figure(figsize=(10, 6), dpi=DPI, layout="constrained")
        ax = fig.add_subplot()

        # Plot the average lap delta to session average for each driver
        for d in s.drivers:
            laps = s.laps.pick_drivers(d).pick_wo_box().loc[:, ["Driver", "LapTime"]]
            driver_avg: pd.Timedelta = laps["LapTime"].mean()

            # Filter out non-runners
            if pd.isna(driver_avg):
                continue

            delta = session_avg.total_seconds() - driver_avg.total_seconds()
            driver_id = laps["Driver"].iloc[0]
            ax.bar(x=driver_id, height=delta, width=0.75,
                   color=utils.get_driver_or_team_color(driver_id, s, api_only=True))
            del laps

        ax.minorticks_on()
        ax.tick_params(axis="x", which="minor", bottom=False)
        ax.tick_params(axis="y", which="minor", grid_alpha=0.1)
        ax.tick_params(axis="y", which="major", grid_alpha=0.3)
        ax.grid(True, which="both", axis="y")
        ax.set_xlabel("Finishing Order")
        ax.set_ylabel("Delta (s)")
        ax.set_title(f"{yr} {rd}\nDelta to Avgerage ({utils.format_timedelta(session_avg)})").set_fontsize(16)

        f = utils.plot_to_file(fig, f"plt_avgdelta-{yr}-{ev['RoundNumber']}")
        await MessageTarget(ctx).send(file=f)


def setup(bot: discord.Bot):
    bot.add_cog(Plot(bot))
