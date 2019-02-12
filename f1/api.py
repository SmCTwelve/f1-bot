"""
Utilities to grab latest F1 results from Ergast API.
"""
import logging
import asyncio
from operator import itemgetter
from bs4 import BeautifulSoup
from datetime import datetime

from f1 import utils
from f1.errors import MissingDataError
from f1.fetch import fetch

BASE_URL = 'http://ergast.com/api/f1'

logger = logging.getLogger(__name__)


async def get_soup(url):
    """Request the URL and parse response as BeautifulSoup object."""
    res = await fetch(url)
    if res is None:
        logger.warning('Unable to get soup, response was None.')
        return None
    return BeautifulSoup(res, 'lxml')


async def get_driver_info(driver_id):
    """Returns a dict with driver first and last name, age, nationality, code and number.

    `driver_id` - must be a valid ID used by Ergast API, e.g. 'alonso', 'michael_schumacher'.
    """
    url = f'{BASE_URL}/drivers/{driver_id}'
    soup = await get_soup(url)
    if soup:
        driver = soup.find('driver')
        res = {
            'firstname': driver.givenname.string,
            'surname': driver.familyname.string,
            'code': driver['code'],
            'id': driver['id'],
            'url': driver['url'],
            'number': driver.permenantnumber.string,
            'age': utils.age(driver.dateofbirth.string[:4]),
            'nationality': driver.nationality.string,
        }
        return res
    raise MissingDataError()


async def get_driver_standings(season):
    """Returns the driver championship standings as dict.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, driver code, total points and wins.

    Raises `MissingDataError` if API response unavailable.
    """
    url = f'{BASE_URL}/{season}/driverStandings'
    soup = await get_soup(url)
    if soup:
        # tags are lowercase
        standings = soup.standingslist
        results = {
            'season': standings['season'],
            'round': standings['round'],
            'data': [],
        }
        for standing in standings.find_all('driverstanding'):
            results['data'].append(
                {
                    'Pos': int(standing['position']),
                    'Driver': standing.driver['code'],
                    'Points': int(standing['points']),
                    'Wins': int(standing['wins']),
                }
            )
        return results
    raise MissingDataError()


async def get_team_standings(season):
    """Returns the constructor championship standings as dict.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, team, total points and wins.

    Raises `MissingDataError` if API response unavailable.
    """
    url = f'{BASE_URL}/{season}/constructorStandings'
    soup = await get_soup(url)
    if soup:
        standings = soup.standingslist
        results = {
            'season': standings['season'],
            'round': standings['round'],
            'data': [],
        }
        for standing in standings.find_all('constructorstanding'):
            results['data'].append(
                {
                    'Pos': int(standing['position']),
                    'Team': standing.constructor.find('name').string,
                    'Points': int(standing['points']),
                    'Wins': int(standing['wins']),
                }
            )
        return results
    raise MissingDataError()


async def get_all_drivers_and_teams(season):
    """Return all drivers and teams on the grid as dict.

    Raises `MissingDataError` if API response unavailable.
    """
    url = f'{BASE_URL}/{season}/driverStandings'
    soup = await get_soup(url)
    if soup:
        standings = soup.find_all('driverstanding')
        results = {
            'season': soup.standingslist['season'],
            'round': soup.standingslist['round'],
            'data': []
        }
        for standing in standings:
            driver = standing.driver
            team = standing.constructor
            results['data'].append(
                {
                    'Code': driver['code'],
                    'No': int(driver.permanentnumber.string),
                    'Name': f'{driver.givenname.string} {driver.familyname.string}',
                    'Age': utils.age(driver.dateofbirth.string[:4]),
                    'Nationality': driver.nationality.string,
                    'Team': team.find('name').string,
                }
            )
        return results
    raise MissingDataError()


async def get_race_schedule():
    """Return full race calendar with circuit names and date as dict.

    Raises `MissingDataError` if API response unavailable.
    """
    url = f'{BASE_URL}/current'
    soup = await get_soup(url)
    if soup:
        races = soup.find_all('race')
        results = {
            'season': soup.racetable['season'],
            'data': []
        }
        for race in races:
            results['data'].append(
                {
                    'Round': int(race['round']),
                    'Circuit': race.circuit.circuitname.string,
                    'Date': utils.date_parser(race.date.string),
                    'Time': utils.time_parser(race.time.string),
                    'Country': race.location.country.string,
                }
            )
        return results
    raise MissingDataError()


async def get_next_race():
    """Returns the next race in the calendar and a countdown (from moment of req) as dict.

    Raises `MissingDataError` if API response unavailable.
    """
    #  TODO - Get image of circuit

    url = f'{BASE_URL}/current/next'
    soup = await get_soup(url)
    if soup:
        race = soup.race
        date, time = (race.date.string, race.time.string)
        cd = utils.countdown(datetime.strptime(
            f'{date} {time}', '%Y-%m-%d %H:%M:%SZ'
        ))
        result = {
            'season': race['season'],
            'countdown': cd[0],
            'url': race['url'],
            'data': {
                'Round': int(race['round']),
                'Name': race.racename.string,
                'Date': f"{utils.date_parser(date)} {race['season']}",
                'Time': utils.time_parser(time),
                'Circuit': race.circuit.circuitname.string,
                'Country': race.location.country.string,
            }
        }
        return result
    raise MissingDataError()


async def get_race_results(rnd, season):
    """Returns race results for `round` in `season` as dict.

    E.g. `get_race_results(12, 2008)` --> Results for 2008 season, round 12.

    Data includes finishing position, fastest lap, finish status, pit stops per driver.
    Raises `MissingDataError` if API response unavailable.
    """
    url = f'{BASE_URL}/{season}/{rnd}/results'
    soup = await get_soup(url)
    if soup:
        race = soup.race
        race_results = race.resultslist.find_all('result')
        date, time = (race.date.string, race.time.string)
        res = {
            'season': race['season'],
            'round': race['round'],
            'race': race.racename.string,
            'url': race['url'],
            'date': f"{utils.date_parser(date)} {race['season']}",
            'time': utils.time_parser(time),
            'data': [],
            'timings': [],
        }
        for result in race_results:
            driver = result.driver
            # Finish time and fastest lap both use <time> tag, soup.find() will return first match
            # use sibling search instead to get second time
            finish_time = result.find_next_sibling('time')
            fastest_lap = result.fastestlap
            res['data'].append(
                {
                    'Pos': int(result['position']),
                    'Driver': f'{driver.givenname.string} {driver.familyname.string}',
                    'Team': result.constructor.find('name').string,
                    'Laps': int(result.laps.string),
                    'Start': int(result.grid.string),
                    # If DNF finish time will be missing so replace with None
                    'Time': None if finish_time is None else finish_time.string,
                    'Status': result.status.string,
                    'Points': int(result['points']),
                }
            )
            # Fastest lap data if available
            if fastest_lap is not None:
                res['timings'].append(
                    {
                        'Rank': int(fastest_lap['rank']),
                        'Driver': driver['code'],
                        'Time': fastest_lap.time.string,
                        'Speed (kph)': int(float(fastest_lap.averagespeed.string)),
                    }
                )
        return res
    raise MissingDataError()


async def get_qualifying_results(rnd, season):
    """Returns qualifying results for `round` in `season` as dict.

    E.g. `get_qualifying_results(12, 2008)` --> Results for round 12 in 2008 season.

    Data includes Q1, Q2, Q3 times per driver, position, laps per driver. Raises `MissingDataError`.
    """
    url = f'{BASE_URL}/{season}/{rnd}/qualifying'
    soup = await get_soup(url)
    if soup:
        race = soup.race
        quali_results = race.qualifyinglist.find_all('qualifyingresult')
        date, time = (race.date.string, race.time.string)
        res = {
            'season': race['season'],
            'round': race['round'],
            'race': race.racename.string,
            'url': race['url'],
            'date': f"{utils.date_parser(date)} {race['season']}",
            'time': utils.time_parser(time),
            'data': []
        }
        for result in quali_results:
            res['data'].append(
                {
                    'Pos': int(result['position']),
                    'Driver': result.driver['code'],
                    'Team': result.constructor.find('name').string,
                    'Q1': result.q1.string if result.q1 is not None else None,
                    'Q2': result.q2.string if result.q2 is not None else None,
                    'Q3': result.q3.string if result.q3 is not None else None,
                }
            )
        return res
    raise MissingDataError()


async def get_driver_wins(driver_id):
    """Returns dict with total wins for the driver and a list of dicts for each race."""
    url = f'{BASE_URL}/drivers/{driver_id}/results/1'
    soup = await get_soup(url)
    if soup:
        races = soup.racetable.find_all('race')
        res = {
            'total': int(soup.MRData['total']),
            'driver': await get_driver_info(driver_id),
            'data': []
        }
        for race in races:
            race_result = race.racelist.result
            res['data'].append(
                {
                    'Race': race.racename.string,
                    'Circuit': race.circuitname.string,
                    'Date': utils.date_parser(race.date.string),
                    'Team': race_result.constructor.name.string,
                    'Grid': race_result.grid.string,
                    'Laps': race_result.laps.string,
                    'Time': race_result.time.string,
                }
            )
        return res
    return MissingDataError()


async def get_driver_poles(driver_id):
    """Returns total pole positions for driver with list of dicts for each race."""
    url = f'{BASE_URL}/drivers/{driver_id}/grid/1'
    soup = await get_soup(url)
    if soup:
        races = soup.racetable.find_all('race')
        res = {
            'total':  int(soup.MRData['total']),
            'driver': await get_driver_info(driver_id),
            'data': []
        }
        for race in races:
            quali_result = race.qualifyinglist.qualifyingresult
            res['data'].append(
                {
                    'Race': race.racename.string,
                    'Circuit': race.circuitname.string,
                    'Date': utils.date_parser(race.date.string),
                    'Team': quali_result.constructor.name.string,
                    'Q1': quali_result.q1.string,
                    'Q2': quali_result.q2.string,
                    'Q3': quali_result.q3.string,
                }
            )
        return res
    return MissingDataError()


async def get_driver_championships(driver_id):
    """Returns total championship wins for the driver and list of dicts for each season, team, points and wins."""
    url = f'{BASE_URL}/drivers/{driver_id}/driverStandings/1'
    soup = await get_soup(url)
    if soup:
        standings = soup.standingstable.find_all('standingslist')
        res = {
            'total': int(soup.MRData['total']),
            'driver': await get_driver_info(driver_id),
            'data': []
        }
        for standing in standings:
            res['data'].append(
                {
                    'Season': standing['season'],
                    'Points': standing.driverstanding['points'],
                    'Wins': standing.driverstanding['wins'],
                    'Team': standing.driverstanding.constructor.name.string,
                }
            )
        return res
    raise MissingDataError()


async def get_driver_teams(driver_id):
    """Returns a dict with total number of teams the driver has driven for and a list of names."""
    url = f'{BASE_URL}/drivers/{driver_id}/constructors'
    soup = await get_soup(url)
    if soup:
        constructors = soup.constructortable.find_all('constructor')
        res = {
            'total': int(soup.MRData['total']),
            'teams': [constructor.name.string for constructor in constructors]
        }
        return res
    return MissingDataError()


async def get_driver_seasons(driver_id):
    """Returns a dict with the total number of seasons in F1 and a list of dicts with year, team, and pos.

    The Ergast API is queried for all driver championships that `driver_id` has participated in, which may cause a
    slight delay in processing for veteran drivers with many seasons.

    Raises `MissingDataError` if results not found or invalid.
    """
    url = f'{BASE_URL}/drivers/{driver_id}/driverStandings'
    soup = await get_soup(url)
    if soup:
        standings = soup.standingstable.find_all('standingslist')
        res = {
            'total': int(soup.MRData['total']),
            'data': []
        }
        for standing in standings:
            res['data'].append(
                {
                    'Season': standing['season'],
                    'Pos': standing['position'],
                    'Team': standing.constructor.name.string,
                }
            )
        return res
    raise MissingDataError()


async def get_driver_career(driver_id):
    """Returns total wins, poles, points, seasons, teams and DNF's for the driver as dict.

    `driver_id` must be valid, e.g. 'alonso', 'vettel', 'di_resta'.
    """
    # Get results concurrently
    [wins, poles, champs, seasons, teams] = await asyncio.gather(
        get_driver_wins(driver_id),
        get_driver_poles(driver_id),
        get_driver_championships(driver_id),
        get_driver_seasons(driver_id),
        get_driver_teams(driver_id),
    )
    driver_name = f"{wins['driver']['firstname']} {wins['driver']['surname']}"
    res = {
        'Name': driver_name,
        'Wins': wins['total'],
        'Poles': poles['total'],
        'Championships': champs['total'],
        'Seasons': seasons['total'],
        'Teams': teams['total'],
    }
    return res


async def rank_lap_times(data, filter):
    """Returns filtered best lap times based on race results data obtained
    from `get_race_results()`.

    Sorts the list of lap times returned by `get_race_results()` dataset and splits
    the results based on the filter keyword.

    Parameters
    ----------
    `data` : list
        Returned data from `get_race_results()`.
    `filter` : str
        Type of filter to be applied:
            'slowest' - slowest lap
            'fastest' - fastest lap
            'top'     - top 5 laps
            'bottom'  - bottom 5 laps
    """
    sorted_times = sorted(data['timings'], key=itemgetter('Rank'))
    # slowest lap
    if filter is 'slowest':
        return sorted_times[len(sorted_times) - 1]
    # fastest lap
    elif filter is 'fastest':
        return sorted_times[0]
    # fastest 5 laps
    elif filter is 'top':
        return sorted_times[:5]
    # slowest 5 laps
    elif filter is 'bottom':
        return sorted_times[len(sorted_times) - 5:]
    # no filter given, return full sorted results
    else:
        return sorted_times
