import unittest
from zipfile import ZipFile
from zipfile import ZipInfo
from os.path import dirname
from os.path import join

try:
    from unrar.rarfile import RarFile
except (ImportError, LookupError, OSError) as e:
    RarFile = None

from explosive.fuse.archive import ArchiveFile
from explosive.fuse.archive import FileNotFoundError
from explosive.fuse.exception import UnsupportedArchiveFile

path = lambda p: join(dirname(__file__), 'data', p)


class ArchiveFileZipTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_unsupported(self):
        unsupported = path('empty.txt')

        with self.assertRaises(UnsupportedArchiveFile) as c:
            ArchiveFile(unsupported)

        self.assertEqual(str(c.exception), 'unsupported archive format.')

    def test_load_archive_file_zip_missing(self):
        missing = path('missing.zip')

        with self.assertRaises(FileNotFoundError):
            ArchiveFile(missing)

    def test_load_archive_file_zip(self):
        demo1 = path('demo1.zip')

        with ArchiveFile(demo1) as af:
            infolist = af.infolist()

        self.assertEqual(sorted(f.filename for f in infolist), [
            'file1', 'file2', 'file3', 'file4', 'file5', 'file6'])

        # ensure it's closed outside of the `with` context.
        self.assertIsNone(af.archive_file.fp)

    def test_load_archive_file_zip2(self):
        demo2 = path('demo2.zip')

        with ArchiveFile(demo2) as af:
            infolist = af.infolist()

        self.assertEqual(sorted(f.filename for f in infolist), [
            'demo/', 'demo/file1', 'demo/file2', 'demo/file3',
            'demo/file4', 'demo/file5', 'demo/file6',
        ])


@unittest.skipIf(RarFile is None, reason='unrar not found')
class ArchiveFileRarTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_archive_file_missing(self):
        missing = path('missing.rar')

        with self.assertRaises(FileNotFoundError):
            ArchiveFile(missing)

    def test_load_archive_file_rar(self):
        demo1 = path('demo1.rar')

        with ArchiveFile(demo1) as af:
            infolist = af.infolist()

        self.assertEqual(sorted(f.filename for f in infolist), [
            'file1', 'file2', 'file3', 'file4', 'file5', 'file6'])

    def test_load_archive_file_rar2(self):
        demo2 = path('demo2.rar')

        with ArchiveFile(demo2) as af:
            infolist = af.infolist()

        self.assertEqual(sorted(f.filename for f in infolist), [
            'demo/', 'demo/file1', 'demo/file2', 'demo/file3',
            'demo/file4', 'demo/file5', 'demo/file6',
        ])
