import logging
from tabulate import tabulate
from datetime import date, datetime

logger = logging.getLogger(__name__)


def contains(first, second):
    '''Returns True if any item in `first` matches an item in `second`.'''
    return any(i in first for i in second)


def make_table(data, headers='keys', fmt='fancy_grid'):
    return tabulate(data, headers=headers, tablefmt=fmt)


def age(yob):
    current_year = date.today().year
    age = (current_year - int(yob))
    return age


def date_parser(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %b')


def time_parser(time_str):
    time = datetime.strptime(time_str, '%H:%M:%SZ').strftime('%X')
    # Strip seconds
    return time[:len(time) - 3]


def countdown(target: datetime):
    '''
    Calculate time to `target` datetime object from current time when invoked.
    Returns a list containing the string output and tuple of (days, hrs, mins, sec).
    '''
    delta = target - datetime.now()
    d = str(delta.days) if delta.days > -1 else 0
    h, m, s = str(delta).split(', ')[1].split(':')
    # trim ms
    s = s.split('.')[0]
    stringify = (
        f"{d} {'days' if d is not '1' else 'day'}, "
        f"{h} {'hours' if h is not '1' else 'hour'}, "
        f"{m} {'minutes' if m is not '1' else 'minute'}, "
        f"{s} {'seconds' if s is not '1' else 'second'} "
    )
    return [stringify, (d, h, m, s)]
