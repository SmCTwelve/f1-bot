import unittest
from datetime import datetime

from f1 import data
from f1.tests.async_test import async_test


class DataTests(unittest.TestCase):

    def check_data(self, data):
        self.assertTrue(data['data'], "Results are empty.")
        self.assertNotIn(None, [i for i in data['data'][0]], "None values present. Check keys.")

    @async_test
    async def test_get_driver_standings(self):
        res = await data.get_driver_standings()
        self.check_data(res)

    @async_test
    async def test_get_team_standings(self):
        res = await data.get_team_standings()
        self.check_data(res)

    @async_test
    async def test_get_all_drivers_and_teams(self):
        res = await data.get_all_drivers_and_teams()
        age = res['data'][0]['Age']
        print(res['data'][0])
        self.check_data(res)
        self.assertTrue(int(age) > 0 and int(age) < 99, "Age not valid.")

    @async_test
    async def test_countdown(self):
        res = await data.get_next_race()
        self.assertTrue(res['data'], "Results empty.")
        self.assertTrue(datetime.strptime(res['data']['Date'], '%d %b'), "Date not valid.")
