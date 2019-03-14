import json
import logging
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
    d = (delta.days) if delta.days > -1 else 0
    # str() on delta nicely outputs 'D days, H:M:S'
    # split 'H:M:S' to get individual values as floats
    h, m, s = [float(x) for x in str(delta).split(', ')[1].split(':')]
    # text representation
    stringify = (
        f"{d} {'days' if d is not 1 else 'day'}, "
        f"{h} {'hours' if h is not 1 else 'hour'}, "
        f"{m} {'minutes' if m is not 1 else 'minute'}, "
        f"{s} {'seconds' if s is not 1 else 'second'} "
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
        if d.get('driverId', '') == str(id):
            return d
        elif d.get('code', '') == str(id):
            return d
        elif d.get('permanentNumber', '') == str(id):
            return d
        else:
            continue
    raise DriverNotFoundError()
