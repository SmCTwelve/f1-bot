import logging
import asyncio

import pandas as pd
import fastf1 as ff1
from fastf1.events import Event
from fastf1.ergast import Ergast
from fastf1.core import Session, SessionResults

from f1 import utils
from f1.api import ergast

logger = logging.getLogger("f1-bot")

ff1_erg = Ergast()


async def to_event(year: str, round: str) -> Event:
    """Get a `fastf1.events.Event` for a race weekend corresponding to `year` and `round`.

    Handles conversion of "last" round and "current" season from Ergast API.

    The `round` can also be a GP name or circuit.
    """
    # Get the actual round number from the last race identifier
    if round == "last":
        data = await ergast.race_info(year, "last")
        round = data["round"]

    if str(round).isdigit():
        round = int(round)

    return await asyncio.to_thread(ff1.get_event, year=utils.convert_season(year), gp=round)


async def load_session(event: Event, name: str, **kwargs) -> Session:
    """Searches for a matching `Session` using `name` (session name, abbreviation or number).

    Loads and returns the `Session`.
    """
    # Run FF1 blocking I/O in async thread so the bot can await
    session = await asyncio.to_thread(event.get_session, identifier=name)
    await asyncio.to_thread(session.load,
                            laps=kwargs.get("laps", False),
                            telemetry=kwargs.get('telemetry', False),
                            weather=kwargs.get("weather", False),
                            messages=kwargs.get("messages", False),
                            livedata=kwargs.get("livedata", None))
    return session


async def format_results(session: Session, name: str):
    """Format the data from `Session` results with data pertaining to the relevant session `name`.

    The session should be already loaded.

    Returns
    ------
    `DataFrame` with columns:

    Qualifying / Sprint Shootout - `[Pos, Code, Driver, Team, Q1, Q2, Q3]` \n
    Race / Sprint - `[Pos, Code, Driver, Team, Grid, Finish, Points]` \n
    Practice - `[No, Code, Driver, Team, Fastest, Laps]`
    """

    _sr: SessionResults = session.results

    # Results presentation
    res_df: SessionResults = _sr.rename(columns={
        "Position": "Pos",
        "DriverNumber": "No",
        "Abbreviation": "Code",
        "BroadcastName": "Driver",
        "GridPosition": "Grid",
        "TeamName": "Team"
    })

    # FP1, FP2, FP3
    if "Practice" in name:
        # Reload the session to fetch missing lap info
        await asyncio.to_thread(session.load, laps=True, telemetry=False,
                                weather=False, messages=False, livedata=None)

        # Get each driver's fastest lap in the session
        fastest_laps = session.laps.groupby("DriverNumber")["LapTime"] \
            .min().reset_index().set_index("DriverNumber")

        # Combine the fastest lap data with the results data
        fp = pd.merge(
            res_df[["No", "Code", "Driver", "Team"]],
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
    if name in ("Qualifying", "Sprint Shootout"):
        res_df["Pos"] = res_df["Pos"].astype(int)
        qs_res = res_df.loc[:, ["Pos", "Code", "Driver", "Team", "Q1", "Q2", "Q3"]]

        # Format the timedeltas to readable strings, replacing NaT with blank
        qs_res.loc[:, ["Q1", "Q2", "Q3"]] = res_df.loc[:, [
            "Q1", "Q2", "Q3"]].applymap(lambda x: utils.format_timedelta(x))

        return qs_res

    # RACE / SPRINT
    # Session must be Race or Sprint race

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

    return res_df.loc[:, ["Pos", "Code", "Driver", "Team", "Grid", "Finish", "Pts"]]


async def filter_pitstops(year, round, filter: str = None, driver: str = None) -> pd.DataFrame:
    """Return the best ranked pitstops for a race. Optionally restrict results to a `driver` (surname, number or code).

    Use `filter`: `['Best', 'Worst', 'Ranked']` to only show the fastest or slowest stop.
    If not specified the best stop per driver will be used.

    Returns
    ------
    `DataFrame`: `[No, Code, Stop Num, Lap, Duration]`
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
    return df.loc[:, ["No", "Code", "Stop", "Lap", "Duration"]]
