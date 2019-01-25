import unittest
import re
from datetime import datetime

from f1 import api
from f1 import utils
from f1.errors import MissingDataError
from f1.tests.async_test import async_test


class DataTests(unittest.TestCase):

    def check_data(self, data):
        self.assertTrue(data['data'], "Results are empty.")
        self.assertNotIn(None, [i for i in data['data'][0]], "None values present. Check keys.")

    @async_test
    async def test_get_driver_standings(self):
        res = await api.get_driver_standings('current')
        self.check_data(res)

    @async_test
    async def test_get_driver_standings_in_future(self):
        with self.assertRaises(MissingDataError):
            await api.get_driver_standings(3000)

    @async_test
    async def test_get_team_standings(self):
        res = await api.get_team_standings('current')
        self.check_data(res)

    @async_test
    async def test_get_all_drivers_and_teams(self):
        res = await api.get_all_drivers_and_teams('current')
        age = res['data'][0]['Age']
        self.check_data(res)
        # arbirary check for extreme values, active drivers 18-40
        self.assertTrue(int(age) > 0 and int(age) < 99, "Age not valid.")

    @async_test
    async def test_get_next_race(self):
        res = await api.get_next_race()
        time = res['data']['Time']
        date = res['data']['Date']
        self.assertTrue(res['data'], "Results empty.")
        self.assertTrue(datetime.strptime(date, '%d %b %Y'), "Date not valid.")
        self.assertTrue(datetime.strptime(time, '%H:%M UTC'), "Time not valid.")

    @async_test
    async def test_countdown_with_past_date(self):
        past_date = datetime(1999, 1, 1)
        result = utils.countdown(past_date)
        countdown_str = result[0]
        d, h, m, s = result[1]
        self.assertTrue(d is 0, "No of days for past date should be zero.")
        self.assertTrue(re.findall(r'(\d+ days?|\d+ hours?|\d+ minutes?|\d+ seconds?)+',
                                   countdown_str), "Invalid string output.")

    @async_test
    async def test_get_race_results(self):
        res = await api.get_race_results('last', 'current')
        past_res = await api.get_race_results(12, '2017')
        self.assertTrue(utils.make_table(res['data']), "Table too big.")
        self.assertTrue(utils.make_table(past_res['data']), "Table too big.")

    @async_test
    async def test_get_race_results_in_future_raises_exception(self):
        with self.assertRaises(MissingDataError):
            await api.get_race_results(3000, 1)

    @async_test
    async def test_get_qualifying_results(self):
        res = await api.get_qualifying_results('last', 'current')
        self.assertTrue(utils.make_table(res['data']), "Table too big.")
