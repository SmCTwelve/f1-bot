'''
Utilities to grab latest F1 results from Ergast API.
'''
import logging
from bs4 import BeautifulSoup
from datetime import date, datetime
from tabulate import tabulate

from fetch import fetch

BASE_URL = 'http://ergast.com/api/f1/current'

# -- Use caching for all requests to reuse results from previous command use, only request directly from API if expired --
# -- Check if race weekend, lower cache period --
# !f1 -- return all driver and constructor standings as table/embed
# !f1 wdc | drivers -- only drivers standings
# !f1 <driverName> points -- current points in season for the driver
# !f1 <driverName> -- details about the driver, name, age, all-time wins, poles - get picture
# !f1 wcc | constructors -- only constructors standings
# !f1 <constructor> points -- constructor points this season
# !f1 calendar | races -- all race weekends, ciruits, dates
# !f1 countdown | next -- next race circuit, weekend, date and countdown timer (use /next/ ergast round)
# !f1 update -- ADMIN, manually reset cache
# !f1 results [<round> | <circuitID>] -- qualifying and race results
# !f1 results race | qualifying
# !f1 help | <command> help -- help text and usage example

logger = logging.getLogger(__name__)


def age(yob):
    current_year = date.today().year
    age = (current_year - int(yob))
    return age


def date_parser(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %b')


def time_parser(time_str):
    return datetime.strptime(time_str, '%H:%M:%SZ').strftime('%X')


def make_table(data, headers='keys'):
    return tabulate(data, headers=headers, tablefmt='fancy_grid')


async def get_soup(url):
    '''Request the URL and parse response as BeautifulSoup object.'''
    res = await fetch(url)
    if res is None:
        logger.warning('Unable to get soup, response was None.')
        return None
    return BeautifulSoup(res, 'lxml')


async def get_driver_standings():
    '''Returns the latest driver championship standings or None.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, driver code, total points and wins.
    '''
    url = f'{BASE_URL}/driverStandings'
    soup = await get_soup(url)
    if soup:
        # tags are lowercase
        standings = soup.standingslist
        result = {
            'season': standings['season'],
            'round': standings['round'],
            'data': [],
        }
        for standing in standings.find_all('driverstanding'):
            result['data'].append(
                {
                    'Pos': standing['position'],
                    'No': standing.driver['permanentnumber'],
                    'Driver': standing.driver['code'],
                    'Points': standing['points'],
                    'Wins': standing['wins'],
                }
            )
        return result
    return None


async def get_team_standings():
    '''Returns the latest constructor championship standings or None.

    Fetches results from API. Response XML is parsed into a list of dicts to be tabulated.
    Data includes position, team, total points and wins.
    '''
    url = f'{BASE_URL}/constructorStandings'
    soup = await get_soup(url)
    if soup:
        standings = soup.standingslist
        result = {
            'season': standings['season'],
            'round': standings['round'],
            'data': [],
        }
        for standing in standings.find_all('constructorstanding'):
            result['data'].append(
                {
                    'Pos': standing['position'],
                    'Team': standing.constructor.name,
                    'Points': standing['points'],
                    'Wins': standing['wins'],
                }
            )
        return result
    return None


async def get_all_drivers_and_teams():
    '''Return all drivers and teams on the grid as a list of dicts. Returns None if data unavailable.

    Example: `[{'No': 44, 'Code': 'HAM', 'Name': 'Lewis Hamilton', 'Age': 34,
    'Nationality': 'British', 'Team': 'Mercedes'}]`
    '''
    url = f'{BASE_URL}/driverStandings'
    soup = await get_soup(url)
    if soup:
        standings = soup.find_all('driverstanding')
        results = {
            'season': soup.standingstable['season'],
            'data': []
        }
        for standing in standings:
            driver = standing.driver
            team = standing.constructor
            results['data'].append(
                {
                    'No': driver.permanentnumber,
                    'Code': driver['code'],
                    'Name': f'{driver.givenname} {driver.familyname}',
                    'Age': age(driver.dateofbirth.string[:4]),
                    'Nationality': driver.nationality,
                    'Team': team.name,
                }
            )
        return results
    return None


async def get_race_schedule():
    '''Return full race calendar with circuit names and date or None.'''
    url = BASE_URL
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
                    'Round': race['round'],
                    'Name': race.racename,
                    'Date': date_parser(race.date),
                    'Time': time_parser(race.time),
                    'Circuit': race.circuit.circuitname,
                    'Country': race.location.country,
                }
            )
        return results
    return None
