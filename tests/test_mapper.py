import unittest
from zipfile import ZipFile
from os.path import dirname
from os.path import join

from explosive.fuse.mapper import DefaultMapper

path = lambda p: join(dirname(__file__), 'data', p)


class DefaultMapperTestCase(unittest.TestCase):

    maxDiff = 12300

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_null_traverse(self):
        m = DefaultMapper()
        self.assertIs(m.traverse(''), m.mapping)
        self.assertIsNone(m.traverse('nowhere'))

    def test_mkdir(self):
        m = DefaultMapper()
        result = m.mkdir(['1', '2', '3'])
        self.assertEqual(result, m.mapping['1']['2']['3'])
        result = m.mkdir(['1', '2', '3'])
        self.assertEqual(result, m.mapping['1']['2']['3'])

    def test_mkdir_blocked(self):
        m = DefaultMapper()
        m.mapping['notdir'] = ('somezip.zip', 'afile', 1)

        with self.assertRaises(ValueError) as cm:
            m.mkdir(['notdir', '2', '3'])

        self.assertEqual(cm.exception.args[0],
            'cannot create directory `notdir` at `/`: file entry exists.'
        )
        self.assertEqual(m.mapping, {'notdir': ('somezip.zip', 'afile', 1)})

        # simple case should fail, too
        with self.assertRaises(ValueError) as cm:
            m.mkdir(['notdir',])

    def test_readdir(self):
        m = DefaultMapper()
        self.assertEqual(m.readdir(''), [])
        m.mkdir(['1'])
        self.assertEqual(m.readdir(''), ['1'])
        m.mkdir(['2'])
        m.mkdir(['3', '4', '5'])
        self.assertEqual(sorted(m.readdir('')), ['1', '2', '3'])
        self.assertEqual(sorted(m.readdir('3')), ['4'])
        self.assertEqual(sorted(m.readdir('3/4')), ['5'])

    def test_readdir_alt(self):
        m = DefaultMapper()
        m.mkdir(['1'])
        m.mapping['notdir'] = ('somezip.zip', 'afile', 1)
        self.assertEqual(sorted(m.readdir('')), ['1', 'notdir'])
        self.assertEqual(sorted(m.readdir('notdir')), [])
        self.assertEqual(sorted(m.readdir('nowhere')), [])

    def test_load_infolist(self):
        demo1 = path('demo1.zip')

        m = DefaultMapper()
        with ZipFile(demo1) as zf:
            m._load_infolist('/tmp/demo1.zip', zf.infolist())

        self.assertEqual(m.mapping, {
            'file1': ('/tmp/demo1.zip', 'file1', 33),
            'file2': ('/tmp/demo1.zip', 'file2', 33),
            'file3': ('/tmp/demo1.zip', 'file3', 33),
            'file4': ('/tmp/demo1.zip', 'file4', 33),
            'file5': ('/tmp/demo1.zip', 'file5', 33),
            'file6': ('/tmp/demo1.zip', 'file6', 33),
        })

        # archive filenames not duplicated in memory (check memory id)
        self.assertEqual(len(m.mapping.values()), 6)
        self.assertEqual(len(set(id(v[0]) for v in m.mapping.values())), 1)
        self.assertIs(m.mapping['file1'][0], list(m.archives.keys())[0])
        self.assertIs(m.mapping['file1'][0],
            list(m.archive_ifilenames.keys())[0])

        self.assertEqual(m.archive_ifilenames, {
            '/tmp/demo1.zip': [
                'file1', 'file2', 'file3', 'file4', 'file5', 'file6']
        })

        self.assertEqual({k: list(v) for k, v in m.reverse_mapping.items()}, {
            'file1': ['/tmp/demo1.zip'],
            'file2': ['/tmp/demo1.zip'],
            'file3': ['/tmp/demo1.zip'],
            'file4': ['/tmp/demo1.zip'],
            'file5': ['/tmp/demo1.zip'],
            'file6': ['/tmp/demo1.zip'],
        })

    def test_load_infolist_nested(self):
        demo1 = path('demo2.zip')

        m = DefaultMapper()
        with ZipFile(demo1) as zf:
            m._load_infolist('/tmp/demo2.zip', zf.infolist())

        self.assertEqual(m.mapping['demo'], {
            'file1': ('/tmp/demo2.zip', 'demo/file1', 33),
            'file2': ('/tmp/demo2.zip', 'demo/file2', 33),
            'file3': ('/tmp/demo2.zip', 'demo/file3', 33),
            'file4': ('/tmp/demo2.zip', 'demo/file4', 33),
            'file5': ('/tmp/demo2.zip', 'demo/file5', 33),
            'file6': ('/tmp/demo2.zip', 'demo/file6', 33),
        })

        self.assertEqual(m.archive_ifilenames, {
            '/tmp/demo2.zip': [
                'demo/', 'demo/file4', 'demo/file3', 'demo/file5',
                'demo/file6', 'demo/file1', 'demo/file2']
        })

        self.assertEqual({k: list(v) for k, v in m.reverse_mapping.items()}, {
            'demo/': ['/tmp/demo2.zip'],
            'demo/file1': ['/tmp/demo2.zip'],
            'demo/file2': ['/tmp/demo2.zip'],
            'demo/file3': ['/tmp/demo2.zip'],
            'demo/file4': ['/tmp/demo2.zip'],
            'demo/file5': ['/tmp/demo2.zip'],
            'demo/file6': ['/tmp/demo2.zip'],
        })

    def test_mapping_bad(self):
        bad_target = path('bad.zip')
        missing_target = path('nosuchzip.zip')
        m = DefaultMapper()
        m.load_archive(bad_target)
        m.load_archive(missing_target)
        m.load_archive(object())
        self.assertEqual(m.mapping, {})

    def test_mapping_simple(self):
        target = path('demo1.zip')
        m = DefaultMapper(target)
        self.assertEqual(m.mapping, {
            'file1': (target, 'file1', 33),
            'file2': (target, 'file2', 33),
            'file3': (target, 'file3', 33),
            'file4': (target, 'file4', 33),
            'file5': (target, 'file5', 33),
            'file6': (target, 'file6', 33),
        })

        self.assertEqual(m.traverse('file1'), (target, 'file1', 33))
        self.assertEqual(
            m.readfile('file1'), b'b026324c6904b2a9cb4b88d6d61c81d1\n')

    def test_mapping_simple_nested(self):
        target = path('demo2.zip')
        m = DefaultMapper(target)
        self.assertEqual(m.mapping, {
            'demo': {
                'file1': (target, 'demo/file1', 33),
                'file2': (target, 'demo/file2', 33),
                'file3': (target, 'demo/file3', 33),
                'file4': (target, 'demo/file4', 33),
                'file5': (target, 'demo/file5', 33),
                'file6': (target, 'demo/file6', 33),
            }
        })

        self.assertEqual(m.traverse('demo/file1'), (target, 'demo/file1', 33))
        self.assertEqual(
            m.readfile('demo/file1'), b'b026324c6904b2a9cb4b88d6d61c81d1\n')

    def test_mapping_simple_nested_blocked(self):
        target = path('demo2.zip')
        m = DefaultMapper()
        # create a file entry named 'demo' to block creation of dir
        m.mapping['demo'] = ('somezip.zip', 'notadir', 0)
        m.load_archive(target)
        self.assertEqual(m.mapping, {'demo': ('somezip.zip', 'notadir', 0)})

    def test_mapping_complex_nested(self):
        target = path('demo3.zip')
        m = DefaultMapper(target)
        self.assertEqual(m.mapping['demo'], {
            'dir1': {
                'file1': (target, 'demo/dir1/file1', 33),
                'file2': (target, 'demo/dir1/file2', 33),
                'file3': (target, 'demo/dir1/file3', 33),
                'file4': (target, 'demo/dir1/file4', 33),
            },
            'dir2': {
            },
            'dir3': {
                'dir3': {
                    'file5': (target, 'demo/dir3/dir3/file5', 33),
                },
            },
            'dir4': {
                'dir5': {
                    'dir6': {
                        'file6': (target, 'demo/dir4/dir5/dir6/file6', 33),
                        'dir7': {
                        },
                    },
                },
            },
            'some': {
                'path': (target, 'demo/some/path', 31),
            },
            'some_path': (target, 'demo/some_path', 32),
        })

    def test_mapping_complex_multiple(self):
        demo3 = path('demo3.zip')
        demo4 = path('demo4.zip')
        m = DefaultMapper()
        # load order matters, new entries will not overwrite old ones.
        m.load_archive(demo3)
        m.load_archive(demo4)
        self.assertEqual(list(sorted(m.mapping.keys())), ['demo', 'hello'])
        self.assertEqual(m.mapping['hello'], (demo4, 'hello', 6))
        self.assertEqual(m.mapping['demo'], {
            'dir1': {
                'file1': (demo3, 'demo/dir1/file1', 33),
                'file2': (demo3, 'demo/dir1/file2', 33),
                'file3': (demo3, 'demo/dir1/file3', 33),
                'file4': (demo3, 'demo/dir1/file4', 33),
                'file5': (demo4, 'demo/dir1/file5', 26),
            },
            'dir2': {
                'file2': (demo4, 'demo/dir2/file2', 26),
            },
            'dir3': {
                'dir3': {
                    'file5': (demo3, 'demo/dir3/dir3/file5', 33),
                },
            },
            'dir4': {
                'dir5': {
                    'dir6': {
                        'file6': (demo3, 'demo/dir4/dir5/dir6/file6', 33),
                        'dir7': {
                        },
                    },
                },
            },
            'some': {
                'path': (demo3, 'demo/some/path', 31),
            },
            'some_path': (demo3, 'demo/some_path', 32),
        })

        self.assertEqual(
            m.traverse('demo/dir1/file1'), (demo3, 'demo/dir1/file1', 33))
        self.assertEqual(
            m.readfile('demo/dir1/file1'),
            b'b026324c6904b2a9cb4b88d6d61c81d1\n')

        self.assertEqual(
            m.traverse('demo/dir1/file5'), (demo4, 'demo/dir1/file5', 26))
        self.assertEqual(
            m.traverse('demo/dir4/dir5/dir6/file6'),
            (demo3, 'demo/dir4/dir5/dir6/file6', 33))

        self.assertEqual(
            m.readfile('demo/dir1/file5'),
            b'demo4.zip demo/dir1/file5\n')

        self.assertEqual(sorted(m.readdir('')), ['demo', 'hello'])

    def test_mapping_overwrite_false(self):
        target = path('demo1.zip')
        m = DefaultMapper(overwrite=False)
        m.mapping = {
            'file5': ('dummy.zip', 'file5', 1),
            'file6': ('dummy.zip', 'file6', 1),
            'file7': ('dummy.zip', 'file7', 1),
        }

        m.load_archive(target)
        self.assertEqual(m.mapping, {
            'file1': (target, 'file1', 33),
            'file2': (target, 'file2', 33),
            'file3': (target, 'file3', 33),
            'file4': (target, 'file4', 33),
            'file5': ('dummy.zip', 'file5', 1),
            'file6': ('dummy.zip', 'file6', 1),
            'file7': ('dummy.zip', 'file7', 1),
        })

    def test_mapping_overwrite_true(self):
        target = path('demo1.zip')
        m = DefaultMapper(overwrite=True)
        m.mapping = {
            'file5': ('dummy.zip', 'file5', 1),
            'file6': ('dummy.zip', 'file6', 1),
            'file7': ('dummy.zip', 'file7', 1),
        }

        m.load_archive(target)
        self.assertEqual(m.mapping, {
            'file1': (target, 'file1', 33),
            'file2': (target, 'file2', 33),
            'file3': (target, 'file3', 33),
            'file4': (target, 'file4', 33),
            'file5': (target, 'file5', 33),
            'file6': (target, 'file6', 33),
            'file7': ('dummy.zip', 'file7', 1),
        })
