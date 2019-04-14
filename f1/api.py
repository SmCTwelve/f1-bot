"""
Utilities to grab latest F1 results from Ergast API.
"""
import logging
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime

from f1 import utils
from f1.fetch import fetch
from f1.errors import MissingDataError


BASE_URL = 'http://ergast.com/api/f1'

DRIVERS = utils.load_drivers()

logger = logging.getLogger(__name__)


async def get_soup(url):
    """Request the URL and return response as BeautifulSoup object or None."""
    res = await fetch(url)
    if res is None:
        logger.warning('Unable to get soup, response was None.')
        return None
    return BeautifulSoup(res, 'lxml')


async def get_wiki_thumbnail(url):
    """Get image thumbnail from Wikipedia link. Returns the thumbnail URL."""
    if url is None or url == '':
        return 'https://i.imgur.com/kvZYOue.png'
    # Get URL name after the first '/'
    wiki_title = url.rsplit('/', 1)[1]
    # Get page thumbnail from wikipedia API if it exists
    api_query = ('https://en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2' +
                 '&prop=pageimages&piprop=thumbnail&pithumbsize=600' + f'&titles={wiki_title}')
    res = await fetch(api_query)
    first = res['query']['pages'][0]
    # Get page thumb or return placeholder
    if 'thumbnail' in first:
        return first['thumbnail']['source']
    else:
        return 'https://i.imgur.com/kvZYOue.png'


async def check_status():
    """Monitor connection to Ergast API by recording connection status and time for response.

    Returns int: 1 = Good, 2 = Medium, 3 = Bad, 0 = Down.
    """
    start_time = datetime.now()
    res = await get_soup(f'{BASE_URL}/current/driverStandings')
    end_time = datetime.now()
    delta = end_time - start_time
    if res is None:
        return 0
    if delta.seconds > 5:
        return 2
    elif delta.seconds > 15:
        return 3
    else:
        return 1


async def get_all_drivers():
    """Fetch all driver data as JSON. Returns a dict."""
    url = f'{BASE_URL}/drivers.json?limit=1000'
    # Get JSON data as dict
    res = await fetch(url)
    if res is None:
        raise MissingDataError()
    return res


def get_driver_info(driver_id):
    """Get the driver name, age, nationality, code and number.

    Searches a dictionary containing all drivers from the Ergast API for an
    entry with a matching ID, surname or number given in the `driver_id` arg.

    Parameters
    ----------
    `driver_id`
        Either of: a driver ID used by Ergast API, e.g. 'alonso', 'michael_schumacher';
        the driver code, e.g. 'HAM', 'VET'; or the driver number, e.g. 44, 6.

    Returns
    -------
    dict
        {
            'firstname': str,
            'surname': str,
            'code': str,
            'id': str,
            'url': str,
            'number': str,
            'age': int,
            'nationality': str
        }

    Raises
    ------
    `DriverNotFoundError`
        if no match found.
    """
    driver = utils.find_driver(driver_id, DRIVERS)
    res = {
        'firstname': driver['givenName'],
        'surname': driver['familyName'],
        'code': driver.get('code', None),
        'id': driver['driverId'],
        'url': driver.get('url', None),
        'number': driver.get('permanentNumber', None),
        'age': utils.age(driver['dateOfBirth'][:4]),
        'nationality': driver['nationality'],
    }
    return res


async def get_driver_standings(season):
    """Get the driver championship standings.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, driver code, total points and wins.

    Parameters
    ----------
    `season` : int

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'round': str,
            'data': list[dict] [{
                'Pos': int,
                'Driver': str,
                'Points': int,
                'Wins': int,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response unavailable.
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
                    'Driver': f"{standing.driver.givenname.string[0]} {standing.driver.familyname.string}",
                    'Points': int(standing['points']),
                    'Wins': int(standing['wins']),
                }
            )
        return results
    raise MissingDataError()


async def get_team_standings(season):
    """Get the constructor championship standings.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, team, total points and wins.

    Parameters
    ----------
    `season` : int

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'round': str,
            'data': list[dict] [{
                'Pos': int,
                'Team': str,
                'Points': int,
                'Wins': int,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response unavailable.
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
    """Get all drivers and teams on the grid.

    Parameters
    ----------
    `season` : int

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'round': str,
            'data': list[dict] [{
                'Code': str,
                'No': int,
                'Name': str,
                'Age': int,
                'Nationality': str,
                'Team': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response unavailable.
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
    """Get full race calendar with circuit names and date as dict.

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'data': list[dict] [{
                'Round': int,
                'Circuit': str,
                'Date': str,
                'Time': str,
                'Country': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response unavailable.
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
    """Get the next race in the calendar and a countdown (from moment of req) as dict.

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'countdown': str,
            'url': str,
            'data': list[dict] [{
                'Round': int,
                'Name': str,
                'Date': str,
                'Time': str,
                'Circuit': str,
                'Country': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response unavailable.
    """
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


async def get_race_results(rnd, season, winner_only=False):
    """Get race results for `round` in `season` as dict.

    E.g. `get_race_results(12, 2008)` --> Results for 2008 season, round 12.

    Data includes finishing position, fastest lap, finish status, pit stops per driver.

    Parameters
    ----------
    `rnd` : int
    `season` : int
    `winner_only` : bool

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'round': str,
            'race': str,
            'url': str,
            'date': str,
            'time': str,
            'data': list[dict] [{
                'Pos': int,
                'Driver': str,
                'Team': str,
                'Laps': int,
                'Start': int,
                'Time': str,
                'Status': str,
                'Points': int,
            }],
            'timings': list[dict] [{
                'Rank': int,
                'Driver': str,
                'Time': str,
                'Speed': int,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response unavailable.
    """
    if winner_only is True:
        url = f'{BASE_URL}/{season}/{rnd}/results/1'
    else:
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
            # Now get the fastest lap time element
            fastest_lap = result.fastestlap
            res['data'].append(
                {
                    'Pos': int(result['position']),
                    'Driver': f'{driver.givenname.string[0]} {driver.familyname.string}',
                    'Team': result.constructor.find('name').string,
                    'Start': int(result.grid.string),
                    'Laps': int(result.laps.string),
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

# Consider using /laps url without driver id, seems faster to get all laps
    # Then filter the response to find the driver id


async def get_all_laps(rnd, season):
    """Get time and position data for each driver per lap in the race.

    Parameters
    ----------
    `rnd`, `season` : int

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'round': str,
            'race': str,
            'url': str,
            'date': str,
            'time': str,
            'data': dict[list] - dict keys are lap number and values are list of dicts per driver:
                {
                    1: [ {'id': str, 'lap': int, 'pos': int, 'time': str} ... ],
                    2: [ ... ],
                    ...
                }
        }

    Raises
    ------
    `MissingDataError`
        if API response invalid.
    """
    url = f"{BASE_URL}/{season}/{rnd}/laps?limit=2000"
    soup = await get_soup(url)
    if soup:
        race = soup.race
        laps = race.lapslist.find_all('lap')
        date, time = (race.date.string, race.time.string)
        res = {
            'season': race['season'],
            'round': race['round'],
            'race': race.racename.string,
            'url': race['url'],
            'date': f"{utils.date_parser(date)} {race['season']}",
            'time': utils.time_parser(time),
            'data': {},
        }
        for lap in laps:
            res['data'][int(lap['number'])] = [
                {
                    'id': t['driverid'],
                    'Pos': int(t['position']),
                    'Time': t['time']
                }
                for t in lap.find_all('timing')]
        return res
    raise MissingDataError()


async def get_all_laps_for_driver(driver, laps):
    """Get the lap times for each lap of the race for one driver to tabulate.

    Each dict entry contains lap number, race position and lap time. The API can take time to
    process all of the lap time data.

    Parameters
    ----------
    `driver_id` : dict
        Driver dict as returned by `api.get_driver_info()`.
    `laps` : dict
        lap and timing data for the race as returned by `api.get_all_laps`.

    Returns
    -------
    `res` : dict
        {
            'driver': dict,
            'season': race['season'],
            'round': race['round'],
            'race': race.racename.string,
            'url': race['url'],
            'date': f"{utils.date_parser(date)} {race['season']}",
            'time': utils.time_parser(time),
            'data': list[dict] [{
                'No': int,
                'Position': int,
                'Time': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if response invalid.
    """
    # Force list as second arg as filter expects
    driver_laps = utils.filter_laps_by_driver(laps, [driver['id']])
    res = {
        'driver': driver,
        'season': laps['season'],
        'round': laps['round'],
        'race': laps['race'],
        'url': laps['url'],
        'date': laps['date'],
        'time': laps['time'],
        'data': []
    }
    # Loop over lap:timing_list pairs from filtered laps dict
    # Only one driver to filter so each lap's timing list should have single entry at index 0
    for lap, timing in driver_laps['data'].items():
        res['data'].append(
            {
                'Lap': int(lap),
                'Pos': int(timing[0]['Pos']),
                'Time': timing[0]['Time'],
            }
        )
    return res


async def get_qualifying_results(rnd, season):
    """Gets qualifying results for `round` in `season`.

    E.g. `get_qualifying_results(12, 2008)` --> Results for round 12 in 2008 season.

    Data includes Q1, Q2, Q3 times per driver, position, laps per driver.

    Parameters
    ----------
    `rnd` : int or str
        Race number or 'last' for the latest race
    `season` : int or str
        Season year or 'current'

    Returns
    -------
    `res` : dict
        {
            'season': str,
            'round': str,
            'race': str,
            'url': str,
            'date': str,
            'time': str,
            'data': list[dict] [{
                'Pos': int,
                'Driver': str,
                'Team': str,
                'Q1': str,
                'Q2': str,
                'Q3': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response invalid.
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


async def get_pitstops(rnd, season):
    """Get the race pitstop times for each driver.

    Parameters
    ----------
    `season`, `rnd` : int

    Returns
    -------
    `res` : list[dict] {
        'season': str,
        'round': str,
        'race': str,
        'date': str,
        'time': str,
        'total_laps': int,
        'data': list[dict] {
            'Driver_id': str,
            'Stop_no': int,
            'Lap': int,
            'Time': str,
            'Duration': str,
        }
    }

    Raises
    ------
    `MissingDataError`
        if API response invalid.
    """
    url = f"{BASE_URL}/{season}/{rnd}/pitstops?limit=100"
    soup = await get_soup(url)
    if soup:
        race = soup.race
        pitstops = race.pitstopslist.find_all('pitstop')
        date, time = (race.date.string, race.time.string)
        results = await get_race_results(rnd, season, winner_only=True)
        laps = results['data'][0]['Laps']
        res = {
            'season': race['season'],
            'round': race['round'],
            'race': race.racename.string,
            'date': f"{utils.date_parser(date)} {race['season']}",
            'time': utils.time_parser(time),
            'total_laps': laps,
            'data': []
        }
        for stop in pitstops:
            driver = get_driver_info(stop['driverid'])
            res['data'].append(
                {
                    'Driver': f"{driver['code']}",
                    'Stop_no': int(stop['stop']),
                    'Lap': int(stop['lap']),
                    'Time': stop['time'],
                    'Duration': stop['duration'],
                }
            )
        return res
    raise MissingDataError()


async def get_driver_championship_wins(driver_id):
    """Returns dict with driver standings results where the driver placed first.

    Parameters
    ----------
    `driver_id` : str
        must be valid Eargast API ID, e.g. 'alonso', 'michael_schumacher'.

    Returns
    -------
    `res` : dict
        {
            'total': int,
            'data': list[dict] [{
                'Season': str,
                'Points': int,
                'Wins': int,
                'Team': str,
            }]
        }
    Raises
    ------
    `MissingDataError`
    """
    url = f"{BASE_URL}/drivers/{driver_id}/driverStandings/1"
    soup = await get_soup(url)
    if soup:
        standings = soup.standingstable.find_all('standingslist')
        res = {
            'total': int(soup.mrdata['total']),
            'data': []
        }
        for standing in standings:
            res['data'].append(
                {
                    'Season': standing['season'],
                    'Pos': int(standing.driverstanding['position']),
                    'Wins': int(standing.driverstanding['wins']),
                    'Points': int(standing.driverstanding['points']),
                    'Team': standing.driverstanding.constructor.find('name').string,
                }
            )
        return res
    raise MissingDataError()


async def get_driver_wins(driver_id):
    """Get total wins for the driver and a list of dicts with details for each race.

    Parameters
    ----------
    `driver_id` : str
        must be valid Eargast API ID, e.g. 'alonso', 'michael_schumacher'.

    Returns
    -------
    `res` : dict
        {
            'total': int,
            'data': list[dict] [{
                'Race': str,
                'Circuit': str,
                'Date': str,
                'Team': str,
                'Grid': int,
                'Laps': int,
                'Time': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response invalid.
    """
    url = f"{BASE_URL}/drivers/{driver_id}/results/1?limit=200"
    soup = await get_soup(url)
    if soup:
        races = soup.racetable.find_all('race')
        res = {
            'total': int(soup.mrdata['total']),
            'data': []
        }
        for race in races:
            race_result = race.resultslist.result
            res['data'].append(
                {
                    'Race': race.racename.string,
                    'Circuit': race.circuitname.string,
                    'Date': utils.date_parser(race.date.string),
                    'Team': race_result.constructor.find('name').string,
                    'Grid': int(race_result.grid.string),
                    'Laps': int(race_result.laps.string),
                    'Time': race_result.time.string,
                }
            )
        return res
    return MissingDataError()


async def get_driver_poles(driver_id):
    """Get total pole positions for driver with details for each race.

    Parameters
    ----------
    `driver_id` : str
        must be valid Eargast API ID, e.g. 'alonso', 'michael_schumacher'.

    Returns
    -------
    `res` : dict
        {
            'total': int,
            'data': list[dict] [{
                'Race': str,
                'Circuit': str,
                'Date': str,
                'Team': str,
                'Q1': str,
                'Q2': str,
                'Q3': str,
            }]
        }

    Raises
    ------
    `MissingDataError`
        if API response invalid.
    """
    url = f"{BASE_URL}/drivers/{driver_id}/qualifying/1?limit=200"
    soup = await get_soup(url)
    if soup:
        races = soup.racetable.find_all('race')
        res = {
            'total':  int(soup.mrdata['total']),
            'data': []
        }
        for race in races:
            quali_result = race.qualifyinglist.qualifyingresult
            res['data'].append(
                {
                    'Race': race.racename.string,
                    'Circuit': race.circuitname.string,
                    'Date': utils.date_parser(race.date.string),
                    'Team': quali_result.constructor.find('name').string,
                    'Q1': quali_result.q1.string if quali_result.q1 is not None else None,
                    'Q2': quali_result.q2.string if quali_result.q2 is not None else None,
                    'Q3': quali_result.q3.string if quali_result.q3 is not None else None,
                }
            )
        return res
    return MissingDataError()


async def get_driver_seasons(driver_id):
    """Get all seasons the driver has participated in as a dict.

    Raises `MissingDataError`.
    """
    url = f"{BASE_URL}/drivers/{driver_id}/seasons"
    soup = await get_soup(url)
    if soup:
        seasons = soup.seasontable.find_all('season')
        res = {
            'total': int(soup.mrdata['total']),
            'data': [{'year': int(s.string), 'url': s['url']} for s in seasons]
        }
        return res
    raise MissingDataError()


async def get_driver_teams(driver_id):
    """Get all teams the driver has driven with as a dict containing list of constructor names.

    Raises `MissingDataError`.
    """
    url = f"{BASE_URL}/drivers/{driver_id}/constructors"
    soup = await get_soup(url)
    if soup:
        constructors = soup.constructortable.find_all('constructor')
        res = {
            'total': int(soup.mrdata['total']),
            'data': [c.find('name').string for c in constructors]
        }
        return res
    raise MissingDataError


async def get_driver_career(driver):
    """Total wins, poles, points, seasons, teams and DNF's for the driver.

    Parameters
    ----------
    `driver` : dict
        Driver dict as returned by `api.get_driver_info()`.

    Returns
    -------
    `res` : dict
        {
            'driver': dict,
            'data': dict {
                'Wins': int,
                'Poles': int,
                'Championships': dict {
                    'total': int,
                    'years': list
                },
                'Seasons': dict {
                    'total': int,
                    'years': list
                },
                'Teams': dict {
                    'total': int,
                    'names': list
                }
            }
        }
    """
    id = driver['id']
    # prefire standings req first as it takes longest
    standings_task = asyncio.create_task(get_driver_championship_wins(id))
    # Get results concurrently
    [wins, poles, seasons, teams, champs] = await asyncio.gather(
        get_driver_wins(id),
        get_driver_poles(id),
        get_driver_seasons(id),
        get_driver_teams(id),
        standings_task,
    )
    res = {
        'driver': driver,
        'data': {
            'Wins': wins['total'],
            'Poles': poles['total'],
            'Championships': {
                'total': champs['total'],
                'years': [x['Season'] for x in champs['data']],
            },
            'Seasons': {
                'total': seasons['total'],
                'years': [x['year'] for x in seasons['data']],
            },
            'Teams': {
                'total': teams['total'],
                'names': teams['data'],
            },
        }
    }
    return res


async def get_best_laps(rnd, season):
    """Get the best lap for each driver.

    Parameters
    ----------
    `rnd` : int or str
        Race number or 'last' for the latest race
    `season` : int or str
        Season year or 'current'

    Returns
    -------
    `res` : dict
        {   'season': str,
            'round': str,
            'race': str,
            'data': list[dict] {
                'Rank': int,
                'Driver': str,
                'Time': str,
                'Speed': str,
            }
        }

    Raises
    ------
    `MissingDataError`
        If response invalid.
    """
    race_results = await get_race_results(rnd, season)
    res = {
        'season': race_results['season'],
        'round': race_results['round'],
        'race': race_results['race'],
        'data': race_results['timings'],
    }
    return res


# Get DNF's, filter results by not (statusID == 1 or status == 'Finished')
