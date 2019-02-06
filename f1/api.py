'''
Utilities to grab latest F1 results from Ergast API.
'''
import logging
from operator import itemgetter
from bs4 import BeautifulSoup
from datetime import datetime

from f1 import utils
from f1.errors import MissingDataError
from f1.fetch import fetch

BASE_URL = 'http://ergast.com/api/f1'

# -- Use caching for all requests to reuse results from previous command use, only request directly from API if expired --
# -- Check if race weekend, lower cache period --
# !f1 -- return all driver and constructor standings as table/embed
# !f1 wdc | drivers -- only drivers standings
# !f1 <driverName> points -- current points in season for the driver
# !f1 <driverName> -- details about the driver, name, utils.age, all-time wins, poles - get picture
# !f1 wcc | constructors -- only constructors standings
# !f1 <constructor> points -- constructor points this season
# !f1 calendar | races -- all race weekends, ciruits, dates
# !f1 countdown | next -- next race circuit, weekend, date and countdown timer (use /next/ ergast round)
# !f1 update -- ADMIN, manually reset cache
# !f1 results [<round> | <circuitID>] -- qualifying and race results
# !f1 results race | qualifying
# !f1 help | <command> help -- help text and usage example

logger = logging.getLogger(__name__)


async def get_soup(url):
    '''Request the URL and parse response as BeautifulSoup object.'''
    res = await fetch(url)
    if res is None:
        logger.warning('Unable to get soup, response was None.')
        return None
    return BeautifulSoup(res, 'lxml')


async def get_driver_standings(season):
    '''Returns the driver championship standings as dict.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, driver code, total points and wins.

    Raises `MissingDataError` if API response unavailable.
    '''
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
    '''Returns the constructor championship standings as dict.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, team, total points and wins.

    Raises `MissingDataError` if API response unavailable.
    '''
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
    '''Return all drivers and teams on the grid as dict.

    Raises `MissingDataError` if API response unavailable.
    '''
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
    '''Return full race calendar with circuit names and date as dict.

    Raises `MissingDataError` if API response unavailable.
    '''
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
    '''Returns the next race in the calendar and a countdown (from moment of req) as dict.

    Raises `MissingDataError` if API response unavailable.
    '''
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
    '''Returns race results for `round` in `season` as dict.

    E.g. `get_race_results(12, 2008)` --> Results for 2008 season, round 12.

    Data includes finishing position, fastest lap, finish status, pit stops per driver.
    Raises `MissingDataError` if API response unavailable.
    '''
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
            # Finish time and nested fastest lap have same <time> tag so use sibling search
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
    '''Returns qualifying results for `round` in `season` as dict.

    E.g. `get_qualifying_results(12, 2008)` --> Results for round 12 in 2008 season.

    Data includes Q1, Q2, Q3 times per driver, position, laps per driver.
    '''
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


async def rank_lap_times(data, filter):
    '''Returns filtered best lap times based on race results data obtained
    from `get_race_results()`.

    Sorts the list of dicts of lap times returned by `get_race_results()` and splits
    the results based on the filter keyword.

    Parameters
    ----------
    `data` : list
        Race results (from `get_race_results()`) dataset.
    `filter` : str
        Type of filter to be applied:
            'slowest' - slowest lap
            'fastest' - fastest lap
            'top'     - top 5 laps
            'bottom'  - bottom 5 laps
    '''
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
