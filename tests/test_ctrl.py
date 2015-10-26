import unittest
from os.path import dirname
from os.path import join

from explosive.fuse import ctrl

path = lambda p: join(dirname(__file__), 'data', p)


class IntegrationTestCase(unittest.TestCase):

    def test_simple(self):
        with self.assertRaises(SystemExit):
            ctrl.main([])

    def test_layout_help(self):
        with self.assertRaises(SystemExit):
            ctrl.main(['--layout-info'])

    def test_failure(self):
        with self.assertRaises(SystemExit):
            ctrl.main(['-d', 'somezip.zip', '/tmp/to/no/such/dir'])
