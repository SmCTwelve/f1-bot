import re
import unittest
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
        mock_fetch.return_value = get_mock_response('none')
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

    # test career

    # boundary tests


class LiveAPITests(BaseTest):
    """Using real requests to check API status, validate response structure and error handling."""

    @async_test
    async def test_response_structure(self):
        # test response for alonso info against mocked data
        actual_result = await api.get_driver_info('alonso')
        with patch(fetch_path) as mock_get:
            mock_get.return_value = await get_mock_response('driver_info')
            # url never used as fetch is mocked
            expected_result = await api.get_soup('mock_url')

        self.assertTrue(actual_result.find('MRData'), "Parent response tag not as expected, API may have changed.")

        for expected_tag in expected_result:
            for actual_tag in actual_result:
                self.assertEqual(expected_tag, actual_tag,
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
