import unittest
from os.path import dirname
from os.path import join

from fuse import FuseOSError

from explosive.fuse.fs import ExplosiveFUSE
from explosive.fuse import pathmaker

path = lambda p: join(dirname(__file__), 'data', p)


class FsTestCase(unittest.TestCase):

    def test_simple(self):
        fs = ExplosiveFUSE([path('demo1.zip')])
        self.assertEqual(fs.mapping.pathmaker.__name__, 'default')

        fs = ExplosiveFUSE([path('demo1.zip')], _pathmaker=pathmaker.default())
        self.assertEqual(fs.mapping.pathmaker.__name__, 'default')

        fs = ExplosiveFUSE([path('demo1.zip')], pathmaker_name='junk')
        self.assertEqual(fs.mapping.pathmaker.__name__, 'junk')

    def test_getattr(self):
        fs = ExplosiveFUSE([path('demo1.zip')])
        self.assertEqual(fs.getattr('/')['st_mode'], 0o40555)
        self.assertEqual(fs.getattr('/file1')['st_mode'], 0o100444)
        self.assertEqual(fs.getattr('/file1')['st_size'], 33)
        with self.assertRaises(FuseOSError):
            fs.getattr('/no_such_file')

        fs = ExplosiveFUSE([path('demo1.zip')], include_arcname=True)
        self.assertEqual(fs.getattr('/demo1.zip')['st_mode'], 0o40555)
        self.assertEqual(fs.getattr('/demo1.zip/file1')['st_mode'], 0o100444)
        with self.assertRaises(FuseOSError):
            fs.getattr('/file1')

    def test_open(self):
        fs = ExplosiveFUSE([path('demo1.zip')], include_arcname=True)
        # TODO figure out what the flags are.
        self.assertEqual(fs.open('/demo1.zip/file1', 0), 1)
        self.assertEqual(fs.open('/demo1.zip/file1', 0), 2)

    def test_read(self):
        fs = ExplosiveFUSE(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )
        # TODO figure out how to test correct usage of fh.
        fh = fs.open('/demo1.zip/file1', 0)
        self.assertEqual(fs.read('/demo1.zip/file1', 1, 0, fh), b'b')
        self.assertEqual(fs.read('/demo1.zip/file1', 1, 1, fh), b'0')
        self.assertEqual(fs.read('/demo1.zip/file1', 1, 2, fh), b'2')

    def test_readdir(self):
        fs = ExplosiveFUSE(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )
        self.assertEqual(
            sorted(fs.readdir('/', 0)), ['.', '..', 'demo1.zip', 'demo2.zip'])
        self.assertEqual(
            sorted(fs.readdir('/demo1.zip', 0)), [
                '.', '..', 'file1', 'file2', 'file3', 'file4',
                'file5', 'file6'])

    def test_statfs(self):
        fs = ExplosiveFUSE(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )
        report = fs.statfs('/')
        # This should always be true.
        self.assertEqual(report['f_bavail'], 0)
