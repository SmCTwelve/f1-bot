'''
Utilities to grab latest F1 results from Ergast API.
'''
import logging
from bs4 import BeautifulSoup
from datetime import datetime

from f1.fetch import fetch
from f1 import utils

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
    '''Returns the driver championship standings or None.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, driver code, total points and wins.
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
    return None


async def get_team_standings(season):
    '''Returns the constructor championship standings or None.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, team, total points and wins.
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
    return None


async def get_all_drivers_and_teams(season):
    '''Return all drivers and teams on the grid as a list of dicts. Returns None if data unavailable.

    Example: `[{'No': 44, 'Code': 'HAM', 'Name': 'Lewis Hamilton', 'Age': 34,
    'Nationality': 'British', 'Team': 'Mercedes'}]`
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
    return None


async def get_race_schedule():
    '''Return full race calendar with circuit names and date or None.'''
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
    return None


async def get_next_race():
    '''Returns the next race in the calendar and a countdown (from moment of req).'''
    #  TODO - Get image of circuit

    url = f'{BASE_URL}/next'
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
    return None
