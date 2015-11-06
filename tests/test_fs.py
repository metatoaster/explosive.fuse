import unittest
from os.path import dirname
from os.path import join

from fuse import FuseOSError

from explosive.fuse.fs import ExplosiveFUSE
from explosive.fuse.fs import SymlinkFUSE
from explosive.fuse import pathmaker

path = lambda p: join(dirname(__file__), 'data', p)


class ExplosiveFsTestCase(unittest.TestCase):

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


class SymlinkFUSETestCase(unittest.TestCase):

    def test_simple(self):
        fs = SymlinkFUSE('/mnt')
        self.assertEqual(fs.symlinks, {})
        self.assertEqual(fs.base_path, '/')
        self.assertEqual(fs.mount_root, '/mnt')

    def test_getattr(self):
        fs = SymlinkFUSE('/mnt')
        self.assertEqual(fs.getattr('/')['st_mode'], 0o40555)
        with self.assertRaises(FuseOSError):
            fs.getattr('/no_such_file')

        fs = SymlinkFUSE('/mnt', base_path='/.control')
        self.assertEqual(fs.getattr('/')['st_mode'], 0o40555)
        self.assertEqual(fs.getattr('/.control')['st_mode'], 0o40555)
        with self.assertRaises(FuseOSError):
            fs.getattr('/.control/here')
        with self.assertRaises(FuseOSError):
            fs.getattr('/.cont')

        fs.symlinks['here'] = '/home/somewhere'
        self.assertEqual(fs.getattr('/.control/here')['st_mode'], 0o120444)

    def test_create(self):
        fs = SymlinkFUSE('/mnt', base_path='/.control')
        with self.assertRaises(FuseOSError):
            fs.create('/.cont', 0)

    def test_mkdir(self):
        fs = SymlinkFUSE('/mnt', base_path='/.control')
        with self.assertRaises(FuseOSError):
            fs.mkdir('/.cont', 0)

    def test_readlink(self):
        fs = SymlinkFUSE('/mnt', base_path='/.control')
        fs.symlinks['here'] = '/home/somewhere'
        self.assertEqual(fs.readlink('/.control/here'), '/home/somewhere')

    def test_readdir(self):
        fs = SymlinkFUSE('/mnt')
        self.assertEqual(fs.readdir('/', 0), ['.', '..'])

        fs = SymlinkFUSE('/mnt', base_path='/some/nested/structure')
        self.assertEqual(fs.readdir('/', 0), ['.', '..', 'some'])
        self.assertEqual(fs.readdir('/some', 0), ['.', '..', 'nested'])
        self.assertEqual(
            fs.readdir('/some/nested', 0), ['.', '..', 'structure'])
        self.assertEqual(
            fs.readdir('/some/nested/structure', 0), ['.', '..'])

        fs.symlinks['here'] = '/home/somewhere'
        self.assertEqual(
            fs.readdir('/some/nested/structure', 0), ['.', '..', 'here'])

    def test_symlink(self):
        fs = SymlinkFUSE('/mnt')
        fs.symlink('/somewhere/else', '/target/to/file')
        self.assertEqual(fs.symlinks['else'], '/target/to/file')
        # relative links gets resolved to absolute
        fs.symlink('/somewhere/else', 'target')
        self.assertEqual(fs.symlinks['else'], '/mnt/target')

        fs = SymlinkFUSE('/mnt/somewhere', base_path='/some/nested/structure')

        with self.assertRaises(FuseOSError):
            fs.symlink('/somewhere/else', '/target')

        with self.assertRaises(FuseOSError):
            fs.symlink('/some/nested/struct', '/target')

        fs.symlink('/some/nested/structure/target', '/target')
        self.assertEqual(fs.symlinks['target'], '/target')

        fs.symlink('/some/nested/structure/target2', '../../../../target')
        self.assertEqual(fs.symlinks['target2'], '/mnt/target')

    def test_unlink(self):
        fs = SymlinkFUSE('/mnt')
        fs.symlinks['else'] = '/home/else'
        fs.unlink('/else')
        self.assertEqual(fs.symlinks, {})

        fs = SymlinkFUSE('/mnt', base_path='/a/dir')
        with self.assertRaises(FuseOSError):
            fs.unlink('/a/dir')

    def test_statfs(self):
        fs = SymlinkFUSE('/mnt')
        report = fs.statfs('/')
        self.assertEqual(report['f_bavail'], 0)
