import re
import unittest
import asyncio
from unittest.mock import patch
from datetime import datetime

from f1 import api
from f1 import utils
from f1.errors import MissingDataError, MessageTooLongError
from f1.tests.async_test import async_test
from f1.tests.mock_response.response import get_mock_response

# Path for patch should be module where it is used, not where defined
fetch_path = 'f1.api.fetch'


class BaseTest(unittest.TestCase):
    """Base testing class."""

    def check_data(self, data):
        self.assertTrue(data, "Results are empty.")
        self.assertNotIn(None, [i for i in data[0]], "None values present. Check keys.")


class UtilityTests(BaseTest):
    """Testing utility functions not tied to API data."""

    def test_driver_age(self):
        age_str = '1981-07-29'
        age = utils.age(age_str[:4])
        # arbirary check for extreme values, active F1 drivers avg 18-40
        self.assertTrue(int(age) > 0 and int(age) < 99, "Age not valid.")

    def test_age_with_future_yob(self):
        yob = '3000'
        self.assertEqual(utils.age(yob), 0)

    def test_message_too_long_raises_exception(self):
        # discord limit 2000 chars
        msg = ['x'] * 3000
        with self.assertRaises(MessageTooLongError):
            utils.make_table(msg, headers='first_row')

    def test_is_future_with_future_year(self):
        year = '3000'
        self.assertTrue(utils.is_future(year))

    def test_is_future_with_past_year(self):
        year = '1999'
        self.assertFalse(utils.is_future(year))

    def test_lap_time_to_seconds(self):
        laps = ['1:30.202', '1:29.505', '0:00.000']
        seconds = [utils.lap_time_to_seconds(x) for x in laps]
        self.assertEqual(seconds[0], 90.202)
        self.assertEqual(seconds[1], 89.505)
        self.assertEqual(seconds[2], 0.0)

    def test_countdown_with_past_date(self):
        past_date = datetime(1999, 1, 1)
        result = utils.countdown(past_date)
        countdown_str = result[0]
        d, h, m, s = result[1]
        self.assertTrue(d is 0, "No of days for past date should be zero.")
        self.assertTrue(re.findall(r'(\d+ days?|\d+ hours?|\d+ minutes?|\d+ seconds?)+',
                                   countdown_str), "Invalid string output.")


class MockAPITests(BaseTest):
    """Using mock data models to test response parsing and data output."""

    @patch(fetch_path)
    @async_test
    async def test_none_result_raises_error(self, mock_fetch):
        # return None to simulate invalid API response
        mock_fetch.return_value = get_mock_response(None)
        with self.assertRaises(MissingDataError):
            await api.get_driver_standings('current')

    @patch(fetch_path)
    @async_test
    async def test_get_driver_standings(self, mock_fetch):
        mock_fetch.return_value = get_mock_response('driver_standings')
        res = await api.get_driver_standings('current')
        self.check_data(res['data'])

    @patch(fetch_path)
    @async_test
    async def test_get_team_standings(self, mock_fetch):
        mock_fetch.return_value = get_mock_response('constructor_standings')
        res = await api.get_team_standings('current')
        self.check_data(res['data'])

    @patch(fetch_path)
    @async_test
    async def test_get_race_results(self, mock_fetch):
        mock_fetch.return_value = get_mock_response('race_results')
        res = await api.get_race_results('last', 'current')
        self.check_data(res['data'])
        self.check_data(res['timings'])

    @patch(fetch_path)
    @async_test
    async def test_get_qualifying_results(self, mock_fetch):
        mock_fetch.return_value = get_mock_response('qualifying_results')
        res = await api.get_qualifying_results('last', 'current')
        self.assertTrue(utils.make_table(res['data']), "Table empty.")

    @patch(fetch_path)
    @async_test
    async def test_get_all_driver_lap_times(self, mock_fetch):
        # Two fetch calls are made, first to get laps, second to get driver info
        mock_fetch.side_effect = [get_mock_response('driver1_laps'), get_mock_response('driver_info')]
        res = await api.get_all_driver_lap_times('alonso', 15, 2008)
        self.check_data(res['data'])
        self.check_data(res['driver'])

    # test career

    @async_test
    async def test_rank_best_lap_times(self):
        times = get_mock_response('best_laps')
        fast, slow, top, bottom = await asyncio.gather(
            api.rank_best_lap_times(times, 'fastest'),
            api.rank_best_lap_times(times, 'slowest'),
            api.rank_best_lap_times(times, 'top'),
            api.rank_best_lap_times(times, 'bottom')
        )
        # Check lengths
        self.assertEqual(len(fast), 1, "Fastest filter should return 1 item.")
        self.assertEqual(len(slow), 1, "Slowest filter should return 1 item.")
        self.assertEqual(len(top), 5, "Should return top 5.")
        self.assertEqual(len(bottom), 5, "Should return bottom 5.")
        # Compare data with mocked model data which has 5 laps
        self.assertEqual(fast[0]['Rank'], 1, "Fastest should return top rank.")
        self.assertEqual(slow[0]['Rank'], 5, "Slowest should return bottom rank.")

    # boundary tests


class LiveAPITests(BaseTest):
    """Using real requests to check API status, validate response structure and error handling."""

    @async_test
    async def test_response_structure(self):
        # test response for alonso info against mocked data
        # Get BeautifulSoup obj from API response to test tags
        actual_result = await api.get_soup(f'{api.BASE_URL}/drivers/alonso')
        with patch(fetch_path) as mock_get:
            mock_get.return_value = get_mock_response('driver_info')
            # url never used as fetch is mocked
            expected_result = await api.get_soup('mock_url')
        # Check root tag of real response body for changes
        self.assertTrue(actual_result.body.find('mrdata'),
                        "Parent response tag not as expected, API may have changed.")
        # Check tag structure matches for real and mocked
        self.assertEqual(expected_result.drivertable, actual_result.drivertable,
                         "Expected and actual tags don't match. Check API data structure.")

    @async_test
    async def test_get_past_race_results(self):
        past_res = await api.get_race_results('12', '2017')
        self.check_data(past_res['data'])
        self.assertEqual(past_res['season'], '2017', "Requested season and result don't match.")
        self.assertEqual(past_res['round'], '12', "Requested round and result don't match.")

    @async_test
    async def test_get_next_race_countdown(self):
        res = await api.get_next_race()
        time = res['data']['Time']
        date = res['data']['Date']
        self.assertTrue(res['data'], "Results empty.")
        self.assertTrue(datetime.strptime(date, '%d %b %Y'), "Date not valid.")
        self.assertTrue(datetime.strptime(time, '%H:%M UTC'), "Time not valid.")
