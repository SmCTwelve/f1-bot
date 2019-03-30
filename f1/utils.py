import json
import logging
from operator import itemgetter
from tabulate import tabulate
from datetime import date, datetime

from f1.config import DATA_DIR
from f1.errors import MessageTooLongError, DriverNotFoundError

logger = logging.getLogger(__name__)


def contains(first, second):
    """Returns True if any item in `first` matches an item in `second`."""
    return any(i in first for i in second)


def is_future(year):
    """Return True if `year` is greater than current year."""
    if year is 'current':
        return False
    return datetime.now().year < int(year)


def too_long(message):
    """Returns True if the message exceeds discord's 2000 character limit."""
    return len(message) >= 2000


def make_table(data, headers='keys', fmt='fancy_grid'):
    """Tabulate data into an ASCII table. Return value is a str.

    The `fmt` param defaults to 'fancy_grid' which includes borders for cells. If the table exceeds
    Discord message limit the table is rebuilt with borders removed.

    If still too large raise `MessageTooLongError`.
    """
    table = tabulate(data, headers=headers, tablefmt=fmt)
    # remove cell borders if too long
    if too_long(table):
        table = tabulate(data, headers=headers, tablefmt='simple')
        # cannot send table if too large even without borders
        if too_long(table):
            raise MessageTooLongError('Table too large to send.', table)
    return table


def age(yob):
    current_year = date.today().year
    if current_year < int(yob):
        return 0
    return current_year - int(yob)


def date_parser(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %b')


def time_parser(time_str):
    return datetime.strptime(time_str, '%H:%M:%SZ').strftime('%H:%M UTC')


def countdown(target: datetime):
    """
    Calculate time to `target` datetime object from current time when invoked.
    Returns a list containing the string output and tuple of (days, hrs, mins, sec).
    """
    delta = target - datetime.now()
    d = delta.days if delta.days > 0 else 0
    # timedelta only stores seconds so calculate mins and hours by dividing remainder
    h, rem = divmod(delta.seconds, 3600)
    m, s = divmod(rem, 60)
    # text representation
    stringify = (
        f"{int(d)} {'days' if d is not 1 else 'day'}, "
        f"{int(h)} {'hours' if h is not 1 else 'hour'}, "
        f"{int(m)} {'minutes' if m is not 1 else 'minute'}, "
        f"{int(s)} {'seconds' if s is not 1 else 'second'} "
    )
    return [stringify, (d, h, m, s)]


def lap_time_to_seconds(time_str):
    """Returns the lap time string as a float representing total seconds.

    E.g. '1:30.202' -> 90.202
    """
    min, secs = time_str.split(':')
    total = int(min) * 60 + float(secs)
    return total


def load_drivers():
    """Load drivers JSON from file and return as dict."""
    with open(f'{DATA_DIR}/drivers.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        DRIVERS = data['MRData']['DriverTable']['Drivers']
        logger.info('Drivers loaded.')
        return DRIVERS


def find_driver(id, drivers):
    """Find the driver entry and return as a dict.

    Parameters
    ----------
    `id` : str
        Can be either a valid Ergast API ID e.g. 'alonso', 'max_verstappen' or the
        driver code e.g. 'HAM' or the driver number e.g. '44'.
    `drivers` : list[dict]
        The drivers dataset to search.

    Returns
    -------
    `driver` : dict

    Raises
    ------
    `DriverNotFoundError`
    """
    for d in drivers:
        if d.get('driverId', '').lower() == str(id).lower():
            return d
        elif d.get('code', '').lower() == str(id).lower():
            return d
        elif d.get('permanentNumber', '') == str(id):
            return d
        else:
            continue
    raise DriverNotFoundError()


def rank_best_lap_times(timings):
    """Sorts the list of lap times returned by `api.get_best_laps()` dataset."""
    sorted_times = sorted(timings['data'], key=itemgetter('Rank'))
    return sorted_times


def rank_pitstops(times):
    """Sort pitstop times based on the duration. `times` is the response from `api.get_pitstops()`."""
    sorted_times = sorted(times['data'], key=itemgetter('Duration'))
    return sorted_times


def filter_laps_by_driver(laps, drivers):
    """Filter lap time data to get only laps driven by the driver in `drivers`.

    Parameters
    ----------
    `laps` : dict
        Timings for each driver per lap as returned by `api.get_all_laps` data key
    `*drivers` : list
        A valid driver_id used by Ergast API

    Returns
    -------
    dict
        `laps` filtered to contain only a list of timings per lap for the specified drivers
    """
    if len(drivers) == 0:
        return laps
    else:
        result = {
            'data': {},
            'race': laps.get('race', ''),
            'season': laps.get('season', ''),
            'round': laps.get('round', '')
        }

        for lap, times in laps['data'].items():
            result['data'][lap] = [t for t in times if t['id'] in drivers]
        return result


def filter_times(sorted_times, filter):
    """Filters the list of times by the filter keyword. If no filter is given the
    times are returned unfiltered.

    Parameters
    -----------
    `sorted_times` : list
        Collection of already sorted items, e.g. pitstops or laptimes data.
    `filter` : str
        The type of filter to apply;
            'slowest' - single slowest time
            'fastest' - single fastest time
            'top'     - top 5 fastest times
            'bottom'  - bottom 5 slowest times

    Returns
    -------
    list
        A subset of the `sorted_times` according to the filter.
    """
    # Force list return type instead of pulling out single string element for slowest and fastest
    # Top/Bottom already outputs a list type with slicing
    # slowest
    if filter == 'slowest':
        return [sorted_times[len(sorted_times) - 1]]
    # fastest
    elif filter == 'fastest':
        return [sorted_times[0]]
    # fastest 5
    elif filter == 'top':
        return sorted_times[:5]
    # slowest 5
    elif filter == 'bottom':
        return sorted_times[len(sorted_times) - 5:]
    # no filter given, return full sorted results
    else:
        return sorted_times
