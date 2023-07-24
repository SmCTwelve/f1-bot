import asyncio
import logging
from typing import Literal

import fastf1 as ff1
import pandas as pd
from fastf1.core import Lap, Laps, Session, SessionResults
from fastf1.ergast import Ergast
from fastf1.events import Event
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from plottable import ColDef, Table

from f1 import utils
from f1.api import ergast
from f1.errors import MissingDataError

logger = logging.getLogger("f1-bot")

ff1_erg = Ergast()


def get_session_type(name: str):
    """Return one of `["R", "Q", "P"]` depending on session `name`.

    E.g. "Race/Sprint" is type "R".
    "Qualifying/Sprint Shootout" is type "Q".
    """
    if "Practice" in name:
        return "P"
    if name in ("Qualifying", "Sprint Shootout"):
        return "Q"
    return "R"


def plot_table(df: pd.DataFrame, col_defs: list[ColDef], idx: str, figsize: tuple[float]):
    """Returns plottable table from data."""
    fig, ax = plt.subplots(figsize=figsize, dpi=200, layout="constrained")

    table = Table(
        df=df,
        ax=ax,
        index_col=idx,
        textprops={"fontsize": 10, "ha": "center"},
        column_border_kw={"color": fig.get_facecolor(), "lw": 2},
        col_label_cell_kw={"facecolor": (0, 0, 0, 0.35)},
        col_label_divider_kw={"color": fig.get_facecolor(), "lw": 4},
        row_divider_kw={"color": fig.get_facecolor(), "lw": 1.2},
        column_definitions=col_defs,
    )
    table.col_label_row.set_fontsize(11)

    return table


async def to_event(year: str, rnd: str) -> Event:
    """Get a `fastf1.events.Event` for a race weekend corresponding to `year` and `round`.

    Handles conversion of "last" round and "current" season from Ergast API.

    The `round` can also be a GP name or circuit.
    """
    # Get the actual round id from the last race endpoint
    if rnd == "last":
        data = await ergast.race_info(year, "last")
        rnd = data["round"]

    if str(rnd).isdigit():
        rnd = int(rnd)

    try:
        event = await asyncio.to_thread(ff1.get_event, year=utils.convert_season(year), gp=rnd)
    except Exception:
        raise MissingDataError()

    return event


async def load_session(event: Event, name: str, **kwargs) -> Session:
    """Searches for a matching `Session` using `name` (session name, abbreviation or number).

    Loads and returns the `Session`.
    """
    try:
        # Run FF1 blocking I/O in async thread so the bot can await
        session = await asyncio.to_thread(event.get_session, identifier=name)
        await asyncio.to_thread(session.load,
                                laps=kwargs.get("laps", False),
                                telemetry=kwargs.get('telemetry', False),
                                weather=kwargs.get("weather", False),
                                messages=kwargs.get("messages", False),
                                livedata=kwargs.get("livedata", None))
    except Exception:
        raise MissingDataError("Unable to get session data, check the round and year is correct.")

    return session


async def format_results(session: Session, name: str):
    """Format the data from `Session` results with data pertaining to the relevant session `name`.

    The session should be already loaded.

    Returns
    ------
    `DataFrame` with columns:

    Qualifying / Sprint Shootout - `[Pos, Code, Driver, Team, Q1, Q2, Q3]` \n
    Race / Sprint - `[Pos, Code, Driver, Team, Grid, Finish, Points, Status]` \n
    Practice - `[Code, Driver, Team, Fastest, Laps]`
    """

    try:
        _sr: SessionResults = session.results
    except Exception:
        raise MissingDataError(
            "Session data unavailable. If the session finished recently, check again later."
        )

    # Results presentation
    res_df: SessionResults = _sr.rename(columns={
        "Position": "Pos",
        "DriverNumber": "No",
        "Abbreviation": "Code",
        "BroadcastName": "Driver",
        "GridPosition": "Grid",
        "TeamName": "Team"
    })

    session_type = get_session_type(name)

    # FP1, FP2, FP3
    ###############
    if session_type == "P":
        # Reload the session to fetch missing lap info
        await asyncio.to_thread(session.load, laps=True, telemetry=False,
                                weather=False, messages=False, livedata=None)

        # Get each driver's fastest lap in the session
        fastest_laps = session.laps.groupby("DriverNumber")["LapTime"] \
            .min().reset_index().set_index("DriverNumber")

        # Combine the fastest lap data with the results data
        fp = pd.merge(
            res_df[["Code", "Driver", "Team"]],
            fastest_laps["LapTime"],
            left_index=True, right_index=True)

        # Get a count of lap entries for each driver
        lap_totals = session.laps.groupby("DriverNumber").count()
        fp["Laps"] = lap_totals["LapNumber"]

        # Format the lap timedeltas to strings
        fp["LapTime"] = fp["LapTime"].apply(lambda x: utils.format_timedelta(x))
        fp = fp.rename(columns={"LapTime": "Fastest"}).sort_values(by="Fastest")

        return fp

    # QUALI / SS
    ############
    if session_type == "Q":
        res_df["Pos"] = res_df["Pos"].astype(int)
        qs_res = res_df.loc[:, ["Pos", "Code", "Driver", "Team", "Q1", "Q2", "Q3"]]

        # Format the timedeltas to readable strings, replacing NaT with blank
        qs_res.loc[:, ["Q1", "Q2", "Q3"]] = res_df.loc[:, [
            "Q1", "Q2", "Q3"]].applymap(lambda x: utils.format_timedelta(x))

        return qs_res

    # RACE / SPRINT
    ###############

    # Get leader finish time
    leader_time = res_df["Time"].iloc[0]

    # Format the Time column:
    # Leader finish time; followed by gap in seconds to leader
    # Drivers who were a lap behind or retired show the finish status instead, e.g. '+1 Lap' or 'Collision'
    res_df["Finish"] = res_df.apply(lambda r: f"+{r['Time'].total_seconds():.3f}"
                                    if r['Status'] == 'Finished' else r['Status'], axis=1)

    # Format the timestamp of the leader lap
    res_df.loc[res_df.first_valid_index(), "Finish"] = utils.format_timedelta(leader_time, hours=True)

    res_df["Pos"] = res_df["Pos"].astype(int)
    res_df["Pts"] = res_df["Points"].astype(int)
    res_df["Grid"] = res_df["Grid"].astype(int)

    return res_df.loc[:, ["Pos", "Driver", "Team", "Grid", "Finish", "Pts", "Status"]]


async def filter_pitstops(year, round, filter: str = None, driver: str = None) -> pd.DataFrame:
    """Return the best ranked pitstops for a race. Optionally restrict results to a `driver` (surname, number or code).

    Use `filter`: `['Best', 'Worst', 'Ranked']` to only show the fastest or slowest stop.
    If not specified the best stop per driver will be used.

    Returns
    ------
    `DataFrame`: `[Code, Stop, Lap, Duration]`
    """

    # Create a dict with driver info from all drivers in the session
    drv_lst = await ergast.get_all_drivers(year, round)
    drv_info = {d["driverId"]: d for d in drv_lst}

    if driver is not None:
        driver = utils.find_driver(driver, drv_lst)["driverId"]

    # Run FF1 I/O in separate thread
    res = await asyncio.to_thread(
        ff1_erg.get_pit_stops,
        season=year, round=round,
        driver=driver, limit=1000)

    data = res.content[0]

    # Group the rows
    # Show all stops for a driver, which can then be filtered
    if driver is not None:
        row_mask = data["driverId"] == driver
    # Get the fastest stop for each driver when no specific driver is given
    else:
        row_mask = data.groupby("driverId")["duration"].idxmin()

    df = data.loc[row_mask].sort_values(by="duration").reset_index(drop=True)

    # Convert timedelta into seconds for stop duration
    df["duration"] = df["duration"].transform(lambda x: x.total_seconds())

    # Add driver abbreviations and numbers from driver info dict
    df[["No", "Code"]] = df.apply(lambda x: pd.Series({
        "No": drv_info[x.driverId]["permanentNumber"],
        "Code": drv_info[x.driverId]["code"],
    }), axis=1)

    # Get row indices for best/worst stop if provided
    if filter.lower() == "best":
        df = df.loc[[df["duration"].idxmin()]]
    if filter.lower() == "worst":
        df = df.loc[[df["duration"].idxmax()]]

    # Presentation
    df.columns = df.columns.str.capitalize()
    return df.loc[:, ["Code", "Stop", "Lap", "Duration"]]


async def tyre_stints(session: Session, driver: str = None):
    """Return a DataFrame showing each driver's stint on a tyre compound and
    the number of laps driven on the tyre.

    The `session` must be a loaded race session with laps data.

    Raises
    ------
        `MissingDataError`: if session does not support the API lap data
    """
    # Check data availability
    if not session.f1_api_support:
        raise MissingDataError("Lap data not supported before 2018.")

    # Group laps data to individual sints per compound with total laps driven
    stints = session.laps.loc[:, ["Driver", "Stint", "Compound", "LapNumber"]]
    stints = stints.groupby(["Driver", "Stint", "Compound"]).count().reset_index() \
        .rename(columns={"LapNumber": "Laps"})
    stints["Stint"] = stints["Stint"].astype(int)

    # Try to find the driver if given and filter results
    if driver is not None:
        year, rnd = session.event["EventDate"].year, session.event["RoundNumber"]
        drv_code = utils.find_driver(driver, await ergast.get_all_drivers(year, rnd))["code"]

        return stints.loc[stints["Driver"] == drv_code].set_index(["Driver", "Stint"], drop=True)

    return stints


def minisectors(laps: list[Lap]) -> pd.DataFrame:
    """Get driver telemetry and calculate the minisectors for each data row based on distacne.

    The `laps` should be loaded from the session.

    Returns
    ------
        `DataFrame`: [Driver, Time, Distance, Speed, mSector, X, Y]
    """

    tel_list = []

    # Load telemetry for the laps
    for lap in laps:
        t = lap.get_telemetry()
        t["Driver"] = lap["Driver"]
        tel_list.append(t)

    # Create single df with all telemetry
    telemetry = pd.concat(tel_list).reset_index(drop=True)

    # Assign minisectors to each row based on distance
    max_dis = telemetry["Distance"].values.max()
    ms_len = max_dis / 24
    telemetry["mSector"] = telemetry["Distance"].apply(lambda x: (
        int((x // ms_len) + 1)
    ))

    return telemetry.loc[:, ["Driver", "Time", "Distance", "Speed", "X", "Y", "mSector"]]


def team_pace(session: Session):
    """Get the max sector speeds and min sector times from the lap data for each team in the session.

    The `session` must be loaded with laps data.

    Returns
    ------
        `DataFrame` containing max sector speeds and avg times indexed by team.

    Raises
    ------
        `MissingDataError`: if session doesn't support lap data.
    """
    # Check lap data support
    if not session.f1_api_support:
        raise MissingDataError("Lap data not supported before 2018.")

    # Get only the quicklaps in session to exclude pits and slow laps
    laps = session.laps.pick_quicklaps()
    times = laps.groupby(["Team"])[["Sector1Time", "Sector2Time", "Sector3Time"]].mean()
    speeds = laps.groupby(["Team"])[["SpeedI1", "SpeedI2", "SpeedFL", "SpeedST"]].max()

    df = pd.merge(times, speeds, how="left", left_index=True, right_index=True)

    return df


def fastest_laps(session: Session, tyre: str):
    """Get fastest laptimes for all drivers in the session, optionally filtered by `tyre`.

    Returns
    ------
        `DataFrame` [Driver, LapTime, Lap, Tyre, ST]

    Raises
    ------
        `MissingDataError` if lap data unsupported or no lap data for the tyre.
    """
    if not session.f1_api_support:
        raise MissingDataError("Lap data not supported for the session.")

    laps = session.laps.pick_accurate()

    if tyre:
        laps = laps.pick_tyre(tyre)

    if laps["Driver"].size == 0:
        raise MissingDataError("Not enough laps on this tyre.")

    fastest = Laps(
        [laps.pick_driver(d).pick_fastest() for d in laps["Driver"].unique()]
    ).sort_values(by="LapTime").reset_index(drop=True).rename(
        columns={
            "LapNumber": "Lap",
            "Compound": "Tyre",
            "SpeedST": "ST"
        }
    )
    fastest.index.name = "Rank"
    fastest.index += 1
    fastest["LapTime"] = fastest["LapTime"].apply(lambda x: utils.format_timedelta(x))
    fastest[["Lap", "ST"]] = fastest[["Lap", "ST"]].fillna(0.0).astype(int)

    return fastest.loc[:, ["Driver", "LapTime", "Lap",  "Tyre", "ST"]]


def sectors(s: Session, tyre: str = None):
    """Get a DataFrame showing the minimum sector times and max speed trap recorded for each driver.
    Based on quicklaps only. Optionally filter by tyre compound.

    Parameters
    ------
        `s`: a loaded race session

    Returns
    ------
        `DataFrame` [Driver, S1, S2, S3, ST]

    Raises
    ------
        `MissingDataError` if lap data not supported or not enough laps with tyre compound.
    """
    if not s.f1_api_support:
        raise MissingDataError("Lap data not supported for this session.")

    # Get quicklaps
    laps = s.laps.pick_quicklaps()

    # Filter by tyre if chosen
    if tyre:
        laps = laps.pick_tyre(tyre)

    if laps["Driver"].size == 0:
        raise MissingDataError("No quick laps available for this tyre.")

    # Get finish order for sorting
    finish_order = pd.DataFrame(
        {"Driver": s.results["Abbreviation"].values}
    ).set_index("Driver", drop=True)

    # Max speed for each driver
    speeds = laps.groupby("Driver")["SpeedST"].max().reset_index().set_index("Driver", drop=True)

    # Min sectors
    sectors = laps.groupby("Driver")[["Sector1Time", "Sector2Time", "Sector3Time"]] \
        .min().reset_index().set_index("Driver", drop=True)
    sectors["ST"] = speeds["SpeedST"].astype(int)

    # Merge with the finish order to get the data sorted
    df = pd.merge(finish_order, sectors, left_index=True, right_index=True).reset_index().rename(
        columns={
            "Sector1Time": "S1",
            "Sector2Time": "S2",
            "Sector3Time": "S3"
        }
    )
    # Convert timestamps to seconds
    df[["S1", "S2", "S3"]] = df[["S1", "S2", "S3"]].applymap(lambda x: f"{x.total_seconds():.3f}")

    return df


def tyre_performance(session: Session):
    """Get a DataFrame showing the average lap times for each tyre compound based on the
    number of laps driven on the tyre.

    Data is grouped by Compound and TyreLife to get the average time for each lap driven.
    Lap time values are based on quicklaps using a threshold of 105%.

    Parameters
    ------
        `session` should already be loaded with lap data.

    Returns
    ------
        `DataFrame` [Compound, TyreLife, LapTime, Seconds]
    """

    # Check lap data support
    if not session.f1_api_support:
        raise MissingDataError("Lap data not supported for this session.")

    # Filter and group quicklaps within 105% by Compound and TyreLife to get the mean times per driven lap
    laps = session.laps.pick_quicklaps(1.05).groupby(["Compound", "TyreLife"])["LapTime"].mean().reset_index()
    laps["Seconds"] = laps["LapTime"].dt.total_seconds()

    return laps


def pos_change(session: Session):
    """Returns each driver start, finish position and the difference between them. Session must be race."""

    if session.name != "Race":
        raise MissingDataError("The session should be race.")

    diff = session.results.loc[:, ["Abbreviation", "GridPosition", "Position"]].rename(
        columns={
            "Abbreviation": "Driver",
            "GridPosition": "Start",
            "Position": "Finish"
        }
    ).reset_index(drop=True).sort_values(by="Finish")

    diff["Diff"] = diff["Start"] - diff["Finish"]
    diff[["Start", "Finish", "Diff"]] = diff[["Start", "Finish", "Diff"]].astype(int)

    return diff


def results_table(results: pd.DataFrame, name: str) -> tuple[Figure, Axes]:
    """Return a formatted matplotlib table from a session results dataframe.

    `name` is the session name parameter.
    """
    base_defs = [
        ColDef(name="Driver", width=0.9, textprops={"ha": "left"}),
        ColDef(name="Team", width=0.8, textprops={"ha": "left"}),
    ]
    pos_def = ColDef("Pos", width=0.5, textprops={"weight": "bold"}, border="right")

    if get_session_type(name) == "R":
        size = (8, 10)
        idx = "Pos"
        dnfs = results.loc[~results["Status"].isin(["+1 Lap", "Finished"]), "Pos"].astype(int).values
        results = results.drop("Status", axis=1)
        col_defs = base_defs + [
            pos_def,
            ColDef(name="Code", width=0.4),
            ColDef("Grid", width=0.35),
            ColDef("Pts", width=0.35, border="l"),
            ColDef("Finish", width=0.6, textprops={"ha": "right"}, border="l"),
        ]

    if get_session_type(name) == "Q":
        size = (10, 10)
        idx = "Pos"
        col_defs = base_defs.append(ColDef(name="Code", width=0.4)) + [
            ColDef(n, width=0.5) for n in ("Q1", "Q2", "Q3")
        ]

    if get_session_type(name) == "P":
        size = (8, 10)
        idx = "Code"
        col_defs = base_defs + [
            ColDef("Code", width=0.4, textprops={"weight": "bold"}, border="right"),
            ColDef("Fastest", width=0.5, textprops={"ha": "right"}),
            ColDef("Laps", width=0.35, textprops={"ha": "right"}),
        ]

    table = plot_table(df=results, col_defs=col_defs, idx=idx, figsize=size)

    # Highlight DNFs in race
    if get_session_type(name) == "R":
        for i in dnfs:
            table.rows[i - 1].set_facecolor((0, 0, 0, 0.38)).set_hatch("//").set_fontcolor((1, 1, 1, 0.5))

    return table.figure, table.ax


def pitstops_table(results: pd.DataFrame) -> tuple[Figure, Axes]:
    """Returns matplotlib table from pitstops results DataFrame."""
    col_defs = [
        ColDef("Code", width=0.4, textprops={"weight": "bold"}, border="r"),
        ColDef("Stop", width=0.25),
        ColDef("Lap", width=0.25),
        ColDef("Duration", width=0.5, textprops={"ha": "right"}, border="l"),
    ]

    # Different sizes depending on amound of data shown with filters
    table = plot_table(results, col_defs, "Code", figsize=(5, 10))

    return table.figure, table.ax


def championship_table(data: list[dict], type: Literal["wcc", "wdc"]) -> tuple[Figure, Axes]:
    """Return matplotlib table displaying championship results."""

    # make dataframe from dict results
    df = pd.DataFrame(data)
    base_defs = [
        ColDef("Pos", width=0.35, textprops={"weight": "bold"}, border="r"),
        ColDef("Points", width=0.35, textprops={"ha": "right"}),
        ColDef("Wins", width=0.35, textprops={"ha": "right"}, border="l"),
    ]

    # Driver
    if type == "wdc":
        col_defs = base_defs + [ColDef("Driver", width=0.9, textprops={"ha": "left"})]
    # Constructors
    if type == "wcc":
        col_defs = base_defs + [ColDef("Team", width=0.8, textprops={"ha": "left"})]

    table = plot_table(df, col_defs, "Pos", figsize=(6, 10))

    return table.figure, table.ax


def grid_table(data: list[dict]) -> tuple[Figure, Axes]:
    """Return table showing the season grid."""

    df = pd.DataFrame(data)
    col_defs = [
        ColDef("Code", width=0.4, textprops={"weight": "bold"}, border="r"),
        ColDef("No", width=0.35),
        ColDef("Name", width=0.9, textprops={"ha": "left"}),
        ColDef("Age", width=0.35),
        ColDef("Nationality", width=0.75, textprops={"ha": "left"}),
        ColDef("Team", width=0.8, textprops={"ha": "left"}),
    ]
    table = plot_table(df, col_defs, "Code", figsize=(10, 10))

    return table.figure, table.ax


def laptime_table(df: pd.DataFrame) -> tuple[Figure, Axes]:
    """Return table with fastest lap data per driver."""

    col_defs = [
        ColDef("Rank", width=0.25, textprops={"weight": "bold"}, border="r"),
        ColDef("Driver", width=0.25),
        ColDef("LapTime", width=0.35, title="Time", textprops={"ha": "right"}),
        ColDef("Lap", width=0.35),
        ColDef("Tyre", width=0.35),
        ColDef("ST", width=0.25)
    ]
    size = (6, (df["Driver"].size / 3.333) + 1)
    table = plot_table(df, col_defs, "Rank", figsize=size)
    table.rows[0].set_hatch("//").set_facecolor("#b138dd").set_alpha(0.35)
    table.columns["ST"].cells[df["ST"].idxmax() - 1].text.set_color("#b138dd")

    return table.figure, table.ax


def sectors_table(df: pd.DataFrame) -> tuple[Figure, Axes]:
    """Return table with fastest sector times and speed."""

    s_defs = [ColDef(c, width=0.4, textprops={"ha": "right"}) for c in ("S1", "S2", "S3")]
    col_defs = [
        ColDef("Driver", width=0.25, textprops={"weight": "bold"}, border="r"),
        ColDef("ST", width=0.25, textprops={"ha": "right"}, border="l")
    ] + s_defs

    # Calculate table height based on rows
    size = (6, (df["Driver"].size / 3.333) + 1)

    table = plot_table(df, col_defs, "Driver", size)

    # Highlight fastest values
    table.columns["S1"].cells[df["S1"].idxmin()].text.set_color("#b138dd")
    table.columns["S2"].cells[df["S2"].idxmin()].text.set_color("#b138dd")
    table.columns["S3"].cells[df["S3"].idxmin()].text.set_color("#b138dd")
    table.columns["ST"].cells[df["ST"].idxmax()].text.set_color("#b138dd")

    return table.figure, table.ax
