import unittest

from f1 import data
from f1.tests.async_test import async_test


class DataTests(unittest.TestCase):

    @async_test
    async def test_get_driver_standings(self):
        res = await data.get_driver_standings()
        self.assertTrue(len(res['data'] > 0), "Results are empty.")
        self.assertNotIn(None, [i for i in res['data'][0]])
