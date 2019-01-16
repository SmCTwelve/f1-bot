import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)


def contains(first, second):
    '''Returns true if any item in `first` matches an item in `second`.'''
    return any(i in first for i in second)


def age(yob):
    current_year = date.today().year
    age = (current_year - int(yob))
    return age


def date_parser(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d %b')


def time_parser(time_str):
    return datetime.strptime(time_str, '%H:%M:%SZ').strftime('%X')


def countdown(target):
    '''
    Calculate time to `target` datetime object from current time when invoked.
    Returns string tuple as (days, hrs, mins, sec).
    '''
    delta = target - datetime.now()
    d = str(delta.days) if delta.days > -1 else 0
    h, m, s = str(delta).split(', ')[1].split(':')
    return (d, h, m, s)
