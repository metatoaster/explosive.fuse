import unittest
from zipfile import ZipFile
from zipfile import ZipInfo
from os.path import dirname
from os.path import join

from explosive.fuse.exception import UnsupportedArchiveFile
from explosive.fuse import _rarfile

path = lambda p: join(dirname(__file__), 'data', p)


class ArchiveFileZipTestCase(unittest.TestCase):

    def setUp(self):
        self.missing = _rarfile.LIBUNRAR_MISSING

    def tearDown(self):
        _rarfile.LIBUNRAR_MISSING = self.missing

    def test_libunrar_missing(self):
        _rarfile.LIBUNRAR_MISSING = True
        with self.assertRaises(UnsupportedArchiveFile) as c:
            _rarfile.FakeRarFile('fake')

        self.assertTrue(str(c.exception).startswith(
            'unrar failed to find UnRAR library'))

    def test_unrar_not_found(self):
        _rarfile.LIBUNRAR_MISSING = False
        with self.assertRaises(UnsupportedArchiveFile) as c:
            _rarfile.FakeRarFile('fake')

        self.assertTrue(str(c.exception).startswith(
            'unrar package not installed'))
