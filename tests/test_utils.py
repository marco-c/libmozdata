# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import datetime
import json
from clouseau import utils


class UtilsTest(unittest.TestCase):

    def test_get_best(self):
        self.assertEqual(utils.get_best(None), None)
        self.assertEqual(utils.get_best({}), None)
        self.assertEqual(utils.get_best({'key1': 7, 'key2': 99, 'key3': 4}), 'key2')

    def test_get_timestamp(self):
        date = '1991-04-16'
        self.assertEqual(utils.get_timestamp(date), 671760000)
        self.assertEqual(utils.get_timestamp(datetime.datetime.strptime(date, '%Y-%m-%d')), 671760000)
        self.assertGreater(utils.get_timestamp('today'), utils.get_timestamp(date))

    def test_get_date_ymd(self):
        self.assertIsNotNone(utils.get_date_ymd('today'))
        self.assertIsNotNone(utils.get_date_ymd('yesterday'))
        self.assertIsNotNone(utils.get_date_ymd('tomorrow'))
        self.assertTrue(utils.get_date_ymd('yesterday') < utils.get_date_ymd('today') < utils.get_date_ymd('tomorrow'))
        date = datetime.datetime.strptime('1991-04-16', '%Y-%m-%d')
        self.assertEqual(utils.get_date_ymd('1991/04/16'), date)
        self.assertEqual(utils.get_date_ymd('1991-04-16'), date)
        self.assertEqual(utils.get_date_ymd('1991 04 16'), date)

        with self.assertRaises(Exception):
            utils.get_date_ymd('04/16/1991')
        with self.assertRaises(Exception):
            utils.get_date_ymd('16/04/1991')
        with self.assertRaises(Exception):
            utils.get_date_ymd('1991-04-16 12:00:00')
        with self.assertRaises(Exception):
            utils.get_date_ymd('')

    def test_get_today(self):
        self.assertIsNotNone(utils.get_today())

    def test_get_date_str(self):
        date = '1991-04-16'
        self.assertEqual(utils.get_date_str(datetime.datetime.strptime(date, '%Y-%m-%d')), date)

    def test_get_date(self):
        self.assertEqual(utils.get_date('1991/04/16'), '1991-04-16')
        self.assertEqual(utils.get_date('1991/04/16', 1), '1991-04-15')

    def test_get_now_timestamp(self):
        date = '1991-04-16'
        self.assertGreater(utils.get_now_timestamp(), utils.get_timestamp(date))

    def test_is64(self):
        self.assertEqual(utils.is64('64bit'), True)
        self.assertEqual(utils.is64('A 64 bit machine'), True)
        self.assertEqual(utils.is64('A 32 bit machine'), False)

    def test_percent(self):
        self.assertEqual(utils.percent(0.23), '23%')
        self.assertEqual(utils.percent(1), '100%')
        self.assertEqual(utils.percent(1.5), '150%')

    def test_simple_percent(self):
        self.assertEqual(utils.simple_percent(3), '3%')
        self.assertEqual(utils.simple_percent(3.0), '3%')
        self.assertEqual(utils.simple_percent(3.5), '3.5%')

    def test_get_credentials(self):
        with self.assertRaises(Exception):
            utils.get_credentials('doesntexist')

        with open('/tmp/afile', 'w') as f:
            f.write('nothing')

        with self.assertRaises(Exception):
            utils.get_credentials('/tmp/afile')

        with open('/tmp/afile', 'w') as f:
            json.dump({'key': 'value'}, f)

        self.assertEqual(utils.get_credentials('/tmp/afile'), {'key': 'value'})

    def test_get_sample(self):
        arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(utils.get_sample(arr, -7), arr)
        self.assertEqual(utils.get_sample(arr, 0), [])
        self.assertEqual(utils.get_sample(arr, 1), arr)
        self.assertEqual(utils.get_sample(arr, 7), arr)
        self.assertEqual(len(utils.get_sample(arr, 0.1)), 1)

    def test_get_date_from_buildid(self):
        self.assertEqual(utils.get_date_from_buildid('20160407164938'), datetime.datetime(2016, 4, 7, 0, 0))
        self.assertEqual(utils.get_date_from_buildid(20160407164938), datetime.datetime(2016, 4, 7, 0, 0))

if __name__ == '__main__':
    unittest.main()
