import unittest
import tempfile
import shutil
from os.path import dirname
from os.path import join

from fuse import FuseOSError

from explosive.fuse.fs import ExplosiveFUSE
from explosive.fuse.fs import ManagedExplosiveFUSE
from explosive.fuse.fs import SymlinkFUSE
from explosive.fuse import pathmaker

path = lambda p: join(dirname(__file__), 'data', p)


class BaseExplosiveFsTestCase(object):

    def test_simple(self):
        fs = self.factory([path('demo1.zip')])
        self.assertEqual(fs.mapping.pathmaker.__name__, 'default')

        fs = self.factory([path('demo1.zip')], _pathmaker=pathmaker.default())
        self.assertEqual(fs.mapping.pathmaker.__name__, 'default')

        fs = self.factory([path('demo1.zip')], pathmaker_name='junk')
        self.assertEqual(fs.mapping.pathmaker.__name__, 'junk')

    def test_load_dupe(self):
        fs = self.factory(
            [path('demo1.zip'), path('demo1.zip')],
            include_arcname=True,
        )
        self.assertEqual(list(fs.mapping.mapping.keys()), ['demo1.zip'])

    def test_getattr(self):
        fs = self.factory([path('demo1.zip')])
        self.assertEqual(fs.getattr('/')['st_mode'], 0o40555)
        self.assertEqual(fs.getattr('/file1')['st_mode'], 0o100444)
        self.assertEqual(fs.getattr('/file1')['st_size'], 33)
        with self.assertRaises(FuseOSError):
            fs.getattr('/no_such_file')

        fs = self.factory([path('demo1.zip')], include_arcname=True)
        self.assertEqual(fs.getattr('/demo1.zip')['st_mode'], 0o40555)
        self.assertEqual(fs.getattr('/demo1.zip/file1')['st_mode'], 0o100444)
        with self.assertRaises(FuseOSError):
            fs.getattr('/file1')

    def test_open_release(self):
        fs = self.factory([path('demo1.zip')], include_arcname=True)
        fh = fs.open('/demo1.zip/file1', 0)
        self.assertTrue(fh > 0)
        self.assertIn(fh, fs.open_entries)
        open_entry = fs.open_entries[fh]
        self.assertEqual(
            open_entry[2], id(fs.mapping.mapping['demo1.zip']['file1']))
        fp = open_entry[0]
        fs.release('/demo1.zip/file1', fh)
        self.assertTrue(fp.closed)

    def test_read(self):
        fs = self.factory(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )
        fh = fs.open('/demo1.zip/file1', 0)
        self.assertEqual(fs.read('/demo1.zip/file1', 1, 0, fh), b'b')
        self.assertEqual(fs.read('/demo1.zip/file1', 1, 1, fh), b'0')
        self.assertEqual(fs.read('/demo1.zip/file1', 1, 2, fh), b'2')

    def test_reread(self):
        fs = self.factory([path('demo3.zip')],
            include_arcname=False, overwrite=True)
        fh = fs.open('/demo/dir1/file1', 0)
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 0, fh), b'b')
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 0, fh), b'b')
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 2, fh), b'2')
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 0, fh), b'b')
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 1, fh), b'0')
        fs.mapping.load_archive(path('demo4.zip'))
        # keep reading should be fine
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 2, fh), b'2')
        # but try to restart, it will fail because demo4.zip was read.
        # and overwrite was specified.
        with self.assertRaises(FuseOSError):
            fs.read('/demo/dir1/file1', 1, 0, fh)

    def test_read_no_such_path(self):
        fs = self.factory([path('demo3.zip')],
            include_arcname=False, overwrite=True)
        with self.assertRaises(FuseOSError):
            fs.open('/no/such/file', 0)

    def test_read_misbehaved(self):
        # this normally shouldn't happen
        fs = self.factory([path('demo3.zip')],
            include_arcname=False, overwrite=True)
        fh = fs.open('/demo/dir1/file1', 0)
        self.assertEqual(fs.read('/demo/dir1/file1', 1, 0, fh), b'b')
        fs.release('/demo/dir1/file1', fh)
        with self.assertRaises(FuseOSError):
            fs.read('/demo/dir1/file1', 1, 0, fh)

    def test_readdir(self):
        fs = self.factory(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )
        self.assertEqual(
            sorted(fs.readdir('/', 0)), ['.', '..', 'demo1.zip', 'demo2.zip'])
        self.assertEqual(
            sorted(fs.readdir('/demo1.zip', 0)), [
                '.', '..', 'file1', 'file2', 'file3', 'file4',
                'file5', 'file6'])

    def test_readdir_omit_arcname(self):
        fs = self.factory(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=False,
        )
        self.assertEqual(
            sorted(fs.readdir('', 0)), [
                '.', '..', 'demo', 'file1', 'file2', 'file3', 'file4',
                'file5', 'file6'])

    def test_splitext_arcname(self):
        fs = self.factory(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
            splitext_arcname=True,
        )
        self.assertEqual(
            sorted(fs.readdir('/demo1', 0)), [
                '.', '..', 'file1', 'file2', 'file3', 'file4',
                'file5', 'file6'])
        fh = fs.open('/demo1/file1', 0)
        self.assertEqual(fs.read('/demo1/file1', 1, 0, fh), b'b')

    def test_statfs(self):
        fs = self.factory(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )
        report = fs.statfs('/')
        # This should always be true.
        self.assertEqual(report['f_bavail'], 0)


class ExplosiveFsTestCase(BaseExplosiveFsTestCase, unittest.TestCase):

    factory = ExplosiveFUSE


class ManagedExplosiveFsTestCase(BaseExplosiveFsTestCase, unittest.TestCase):
    """
    Ensures that the basic functions are unaffected.
    """

    def factory(self, *args, **kwargs):
        fs = ManagedExplosiveFUSE('/mnt', '.management', *args, **kwargs)
        return fs

    def test_init_error(self):
        with self.assertRaises(ValueError):
            fs = ManagedExplosiveFUSE('/mnt', '/nested/.management', [])

    def test_load_dupe(self):
        # overriding this for an extra test.
        fs = self.factory(
            [path('demo1.zip'), path('demo1.zip')],
            include_arcname=True,
        )
        self.assertEqual(list(fs.mapping.mapping.keys()), ['demo1.zip'])

        self.assertEqual(
            sorted(fs('readdir', '/.management', 0)),
            ['.', '..', 'demo1.zip'],
        )

    def test_load_dupe_name(self):
        # A test for the symlink with two filenames with different full
        # paths but same basename.
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(tmpdir))
        target = join(tmpdir, 'demo1.zip')
        shutil.copy(path('demo2.zip'), target)
        fs = self.factory([path('demo1.zip'), target], include_arcname=True)
        self.assertEqual(list(fs.mapping.mapping.keys()), ['demo1.zip'])

        # Test to see that both entries are created, one with a suffix.
        self.assertEqual(
            sorted(fs('readdir', '/.management', 0)),
            ['.', '..', 'demo1.zip', 'demo1.zip_1'],
        )

        self.assertEqual(
            sorted(fs('readdir', '/', 0)),
            ['.', '..', '.management', 'demo1.zip']
        )

        self.assertEqual(
            sorted(fs('readdir', '/demo1.zip', 0)), [
                '.', '..', 'demo', 'file1', 'file2', 'file3',
                'file4', 'file5', 'file6']
        )

    def test_readdir(self):
        # have to override this.
        fs = self.factory(
            [path('demo1.zip'), path('demo2.zip')],
            include_arcname=True,
        )

        self.assertEqual(
            sorted(fs('readdir', '/', 0)),
            ['.', '..', '.management', 'demo1.zip', 'demo2.zip'],
        )

        self.assertEqual(
            sorted(fs('readdir', '/demo1.zip', 0)), [
                '.', '..', 'file1', 'file2', 'file3', 'file4',
                'file5', 'file6'])

        self.assertEqual(
            sorted(fs('readdir', '/.management', 0)),
            ['.', '..', 'demo1.zip', 'demo2.zip'],
        )

    def test_unloaded_preloaded(self):
        # have to override this.
        fs = self.factory([path('demo1.zip'), path('demo2.zip')])

        self.assertEqual(
            sorted(fs('readdir', '/', 0)), [
                '.', '..', '.management', 'demo',
                'file1', 'file2', 'file3', 'file4', 'file5', 'file6'])

        fs('unlink', '/.management/demo1.zip')
        self.assertEqual(sorted(fs('readdir', '/', 0)), [
            '.', '..', '.management', 'demo'])

    def test_overload_dupes(self):
        # have to override this.
        fs = self.factory([path('demo2.zip')])

        self.assertEqual(
            sorted(fs('readdir', '/', 0)), ['.', '..', '.management', 'demo'])
        self.assertEqual(sorted(fs('readdir', '/.management', 0)), [
                '.', '..', 'demo2.zip'])

        # this is not supported because the internal mapping has that
        # path to that demo2.zip.
        with self.assertRaises(FuseOSError):
            fs('symlink', '/.management/demo2_alt.zip', path('demo2.zip'))

        self.assertEqual(sorted(fs('readdir', '/.management', 0)), [
                '.', '..', 'demo2.zip'])

    def test_getattr_mangement(self):
        fs = ManagedExplosiveFUSE('/mnt', '.management', [])
        self.assertEqual(fs('getattr', '/.management')['st_mode'], 0o40555)

    def test_symlink(self):
        fs = ManagedExplosiveFUSE('/mnt', '.management', [])
        self.assertEqual(fs.readdir('/', 0), ['.', '..', '.management'])
        self.assertEqual(sorted(fs('readdir', '/.management', 0)), ['.', '..'])

        with self.assertRaises(FuseOSError):
            fs('symlink', '/somewhere/else', '/target')
        self.assertEqual(fs.readdir('/', 0), ['.', '..', '.management'])
        self.assertEqual(sorted(fs('readdir', '/.management', 0)), ['.', '..'])

        fs('symlink', '/.management/demo1.zip', path('demo1.zip'))
        self.assertEqual(sorted(fs('readdir', '/', 0)), [
            '.', '..', '.management', 'file1', 'file2', 'file3', 'file4',
            'file5', 'file6',
        ])

        fs('unlink', '/.management/demo1.zip')
        self.assertEqual(fs('readdir', '/', 0), ['.', '..', '.management'])

    def test_symlink_bad_archive(self):
        fs = ManagedExplosiveFUSE('/mnt', '.management', [])
        self.assertEqual(fs.readdir('/.management', 0), ['.', '..'])

        with self.assertRaises(FuseOSError):
            fs('symlink', '/.management/bad_archive', '/no_such_archive')
        self.assertEqual(fs.readdir('/.management', 0), ['.', '..'])

    def test_management_supercede_getattr_file_conflict(self):
        # test getattr actually get the directory version not the
        # file version.
        fs = ManagedExplosiveFUSE('/mnt', 'file1', [path('demo1.zip')])
        self.assertEqual(fs('getattr', '/file1')['st_mode'], 0o40555)
        self.assertEqual(fs('getattr', '/file2')['st_mode'], 0o100444)
        self.assertEqual(fs('readdir', '/file1', 0), [
            '.', '..', 'demo1.zip'])

    def test_management_supercede_getattr_dir_confict(self):
        # test getattr actually get the directory version not the
        # file version.
        fs = ManagedExplosiveFUSE(
            '/mnt', 'demo1.zip', [], include_arcname=True)
        fs('symlink', '/demo1.zip/demo1.zip', path('demo1.zip'))
        self.assertEqual(fs('readdir', '/', 0), ['.', '..', 'demo1.zip'])
        self.assertEqual(fs('readdir', '/demo1.zip', 0), [
            '.', '..', 'demo1.zip'])
        self.assertEqual(fs('getattr', '/demo1.zip')['st_mode'], 0o40555)


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

    def test_rename(self):
        fs = SymlinkFUSE('/mnt', base_path='/.control')
        with self.assertRaises(FuseOSError):
            fs.rename('/.cont', '/.cont2')

    def test_symlink(self):
        fs = SymlinkFUSE('/mnt')
        fs.symlink('/somewhere/else', '/target/to/file')
        self.assertEqual(fs.symlinks['else'], '/target/to/file')
        # relative links gets resolved to absolute
        fs.symlink('/somewhere/else2', 'target')
        self.assertEqual(fs.symlinks['else2'], '/mnt/target')

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
