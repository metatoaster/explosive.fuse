import unittest
from zipfile import ZipFile
from zipfile import ZipInfo
from os.path import dirname
from os.path import join

from explosive.fuse.mapper import DefaultMapper

path = lambda p: join(dirname(__file__), 'data', p)


def zipinfo(name, size=0):
    zi = ZipInfo(name)
    zi.file_size = zi.compress_size = size
    return zi


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
            'file1': [('/tmp/demo1.zip', 'file1', 33)],
            'file2': [('/tmp/demo1.zip', 'file2', 33)],
            'file3': [('/tmp/demo1.zip', 'file3', 33)],
            'file4': [('/tmp/demo1.zip', 'file4', 33)],
            'file5': [('/tmp/demo1.zip', 'file5', 33)],
            'file6': [('/tmp/demo1.zip', 'file6', 33)],
        })

    def test_load_infolist_nested(self):
        demo2 = path('demo2.zip')

        m = DefaultMapper()
        with ZipFile(demo2) as zf:
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
            'demo/': [('/tmp/demo2.zip', 'demo/', 0)],
            'demo/file1': [('/tmp/demo2.zip', 'demo/file1', 33)],
            'demo/file2': [('/tmp/demo2.zip', 'demo/file2', 33)],
            'demo/file3': [('/tmp/demo2.zip', 'demo/file3', 33)],
            'demo/file4': [('/tmp/demo2.zip', 'demo/file4', 33)],
            'demo/file5': [('/tmp/demo2.zip', 'demo/file5', 33)],
            'demo/file6': [('/tmp/demo2.zip', 'demo/file6', 33)],
        })

    def test_load_infolist_alternative_pathmaking(self):
        demo1 = path('demo1.zip')
        demo2 = path('demo2.zip')

        m = DefaultMapper(pathmaker_name='flatten', include_arcname=True)
        with ZipFile(demo1) as zf:
            # loading as demo_demo to conflict with below
            m._load_infolist('/tmp/demo_demo', zf.infolist())

        with ZipFile(demo2) as zf:
            m._load_infolist('/tmp/demo', zf.infolist())

        self.assertEqual({k: list(v) for k, v in m.reverse_mapping.items()}, {
            '': [('/tmp/demo', 'demo/', 0)],
            'demo_demo_file1': [('/tmp/demo_demo', 'file1', 33),
                                ('/tmp/demo', 'demo/file1', 33)],
            'demo_demo_file2': [('/tmp/demo_demo', 'file2', 33),
                                ('/tmp/demo', 'demo/file2', 33)],
            'demo_demo_file3': [('/tmp/demo_demo', 'file3', 33),
                                ('/tmp/demo', 'demo/file3', 33)],
            'demo_demo_file4': [('/tmp/demo_demo', 'file4', 33),
                                ('/tmp/demo', 'demo/file4', 33)],
            'demo_demo_file5': [('/tmp/demo_demo', 'file5', 33),
                                ('/tmp/demo', 'demo/file5', 33)],
            'demo_demo_file6': [('/tmp/demo_demo', 'file6', 33),
                                ('/tmp/demo', 'demo/file6', 33)],
        })

        self.assertEqual(m.mapping, {
            'demo_demo_file1': ('/tmp/demo_demo', 'file1', 33),
            'demo_demo_file2': ('/tmp/demo_demo', 'file2', 33),
            'demo_demo_file3': ('/tmp/demo_demo', 'file3', 33),
            'demo_demo_file4': ('/tmp/demo_demo', 'file4', 33),
            'demo_demo_file5': ('/tmp/demo_demo', 'file5', 33),
            'demo_demo_file6': ('/tmp/demo_demo', 'file6', 33),
        })

        m._unload_infolist('/tmp/demo_demo')

        self.assertEqual({k: list(v) for k, v in m.reverse_mapping.items()}, {
            '': [('/tmp/demo', 'demo/', 0)],
            'demo_demo_file1': [('/tmp/demo', 'demo/file1', 33)],
            'demo_demo_file2': [('/tmp/demo', 'demo/file2', 33)],
            'demo_demo_file3': [('/tmp/demo', 'demo/file3', 33)],
            'demo_demo_file4': [('/tmp/demo', 'demo/file4', 33)],
            'demo_demo_file5': [('/tmp/demo', 'demo/file5', 33)],
            'demo_demo_file6': [('/tmp/demo', 'demo/file6', 33)],
        })

        self.assertEqual(m.mapping, {
            'demo_demo_file1': ('/tmp/demo', 'demo/file1', 33),
            'demo_demo_file2': ('/tmp/demo', 'demo/file2', 33),
            'demo_demo_file3': ('/tmp/demo', 'demo/file3', 33),
            'demo_demo_file4': ('/tmp/demo', 'demo/file4', 33),
            'demo_demo_file5': ('/tmp/demo', 'demo/file5', 33),
            'demo_demo_file6': ('/tmp/demo', 'demo/file6', 33),
        })

    def assertDemo3ThenDemo4(self, m, demo3, demo4):
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

    def test_load_infolist_multiple(self):
        demo3 = path('demo3.zip')
        demo4 = path('demo4.zip')

        m = DefaultMapper()
        with ZipFile(demo3) as zf:
            m._load_infolist('/tmp/demo3.zip', zf.infolist())

        with ZipFile(demo4) as zf:
            m._load_infolist('/tmp/demo4.zip', zf.infolist())

        self.assertEqual(m.archive_ifilenames, {
            '/tmp/demo3.zip': [
                'demo/', 'demo/some/', 'demo/some/path', 'demo/dir3/',
                'demo/dir3/dir3/', 'demo/dir3/dir3/file5', 'demo/some_path',
                'demo/dir1/', 'demo/dir1/file4', 'demo/dir1/file3',
                'demo/dir1/file1', 'demo/dir1/file2', 'demo/dir2/',
                'demo/dir4/', 'demo/dir4/dir5/', 'demo/dir4/dir5/dir6/',
                'demo/dir4/dir5/dir6/file6', 'demo/dir4/dir5/dir6/dir7/'
            ],
            '/tmp/demo4.zip': [
                'demo/', 'demo/dir1/', 'demo/dir1/file3', 'demo/dir1/file5',
                'demo/dir1/file1', 'demo/dir2/', 'demo/dir2/file2', 'hello'
            ]
        })

        self.assertEqual({k: list(v) for k, v in m.reverse_mapping.items()}, {
            'demo/': [
                ('/tmp/demo3.zip', 'demo/', 0),
                ('/tmp/demo4.zip', 'demo/', 0),
            ],
            'demo/dir1/': [
                ('/tmp/demo3.zip', 'demo/dir1/', 0),
                ('/tmp/demo4.zip', 'demo/dir1/', 0),
            ],
            'demo/dir1/file1': [
                ('/tmp/demo3.zip', 'demo/dir1/file1', 33),
                ('/tmp/demo4.zip', 'demo/dir1/file1', 26),
            ],
            'demo/dir1/file2': [
                ('/tmp/demo3.zip', 'demo/dir1/file2', 33),
            ],
            'demo/dir1/file3': [
                ('/tmp/demo3.zip', 'demo/dir1/file3', 33),
                ('/tmp/demo4.zip', 'demo/dir1/file3', 26),
            ],
            'demo/dir1/file4': [
                ('/tmp/demo3.zip', 'demo/dir1/file4', 33),
            ],
            'demo/dir1/file5': [
                ('/tmp/demo4.zip', 'demo/dir1/file5', 26),
            ],
            'demo/dir2/': [
                ('/tmp/demo3.zip', 'demo/dir2/', 0),
                ('/tmp/demo4.zip', 'demo/dir2/', 0),
            ],
            'demo/dir2/file2': [
                ('/tmp/demo4.zip', 'demo/dir2/file2', 26),
            ],
            'demo/dir3/': [
                ('/tmp/demo3.zip', 'demo/dir3/', 0),
            ],
            'demo/dir3/dir3/': [
                ('/tmp/demo3.zip', 'demo/dir3/dir3/', 0),
            ],
            'demo/dir3/dir3/file5': [
                ('/tmp/demo3.zip', 'demo/dir3/dir3/file5', 33),
            ],
            'demo/dir4/': [
                ('/tmp/demo3.zip', 'demo/dir4/', 0),
            ],
            'demo/dir4/dir5/': [
                ('/tmp/demo3.zip', 'demo/dir4/dir5/', 0),
            ],
            'demo/dir4/dir5/dir6/': [
                ('/tmp/demo3.zip', 'demo/dir4/dir5/dir6/', 0),
            ],
            'demo/dir4/dir5/dir6/dir7/': [
                ('/tmp/demo3.zip', 'demo/dir4/dir5/dir6/dir7/', 0),
            ],
            'demo/dir4/dir5/dir6/file6': [
                ('/tmp/demo3.zip', 'demo/dir4/dir5/dir6/file6', 33),
            ],
            'demo/some/': [
                ('/tmp/demo3.zip', 'demo/some/', 0),
            ],
            'demo/some/path': [
                ('/tmp/demo3.zip', 'demo/some/path', 31),
            ],
            'demo/some_path': [
                ('/tmp/demo3.zip', 'demo/some_path', 32),
            ],
            'hello': [
                ('/tmp/demo4.zip', 'hello', 6),
            ],

        })

        # test contents of m.mapping with the helper
        self.assertDemo3ThenDemo4(m, '/tmp/demo3.zip', '/tmp/demo4.zip')

    def test_load_infolist_dirfile_conflict(self):
        m = DefaultMapper()
        m._load_infolist('/tmp/conflict.zip', [zipinfo('demo')])
        demo2 = path('demo2.zip')
        with ZipFile(demo2) as zf:
            m._load_infolist('/tmp/demo2.zip', zf.infolist())

        self.assertEqual(m.mapping, {
            'demo': ('/tmp/conflict.zip', 'demo', 0),
        })

        self.assertEqual(m.archive_ifilenames, {
            '/tmp/conflict.zip': [
                'demo',
            ],
            '/tmp/demo2.zip': [
                'demo/', 'demo/file4', 'demo/file3', 'demo/file5',
                'demo/file6', 'demo/file1', 'demo/file2',
            ]
        })

        self.assertEqual({k: list(v) for k, v in m.reverse_mapping.items()}, {
            'demo': [('/tmp/conflict.zip', 'demo', 0)],
            'demo/': [('/tmp/demo2.zip', 'demo/', 0)],
            'demo/file1': [('/tmp/demo2.zip', 'demo/file1', 33)],
            'demo/file2': [('/tmp/demo2.zip', 'demo/file2', 33)],
            'demo/file3': [('/tmp/demo2.zip', 'demo/file3', 33)],
            'demo/file4': [('/tmp/demo2.zip', 'demo/file4', 33)],
            'demo/file5': [('/tmp/demo2.zip', 'demo/file5', 33)],
            'demo/file6': [('/tmp/demo2.zip', 'demo/file6', 33)],
        })

    def test_unload_infolist_simple(self):
        demo1 = path('demo1.zip')

        m = DefaultMapper()
        with ZipFile(demo1) as zf:
            m._load_infolist('/tmp/demo1.zip', zf.infolist())

        m._unload_infolist('/tmp/demo1.zip')

        self.assertEqual(m.mapping, {})
        self.assertEqual(m.reverse_mapping, {})
        self.assertEqual(m.archives, {})
        self.assertEqual(m.archive_ifilenames, {})

    def test_unload_infolist_multiple(self):
        demo = path('demo2.zip')

        m = DefaultMapper()
        # XXX should just store the zf.infolist() somewhere.
        with ZipFile(demo) as zf:
            m._load_infolist('/tmp/demo1.zip', zf.infolist())
            m._load_infolist('/tmp/demo2.zip', zf.infolist())
            m._load_infolist('/tmp/demo3.zip', zf.infolist())

        self.assertEqual(
            list(f[0] for f in m.reverse_mapping['demo/']),
            ['/tmp/demo1.zip', '/tmp/demo2.zip', '/tmp/demo3.zip']
        )

        # lazy way to check
        old_reverse_mapping = str(m.reverse_mapping)

        m._unload_infolist('/tmp/demo2.zip')

        # Not the oldest entry
        self.assertEqual(m.mapping['demo'], {
            'file1': ('/tmp/demo1.zip', 'demo/file1', 33),
            'file2': ('/tmp/demo1.zip', 'demo/file2', 33),
            'file3': ('/tmp/demo1.zip', 'demo/file3', 33),
            'file4': ('/tmp/demo1.zip', 'demo/file4', 33),
            'file5': ('/tmp/demo1.zip', 'demo/file5', 33),
            'file6': ('/tmp/demo1.zip', 'demo/file6', 33),
        })
        self.assertEqual(str(m.reverse_mapping), old_reverse_mapping)
        self.assertEqual(len(m.archives), 2)
        self.assertNotIn('/tmp/demo2.zip', m.archives)
        self.assertEqual(
            list(m.archive_ifilenames.keys()), list(m.archives.keys()))

        with self.assertRaises(KeyError):
            m._unload_infolist('/tmp/demo2.zip')

        m._unload_infolist('/tmp/demo1.zip')
        self.assertEqual(m.mapping, {'demo': {
            'file1': ('/tmp/demo3.zip', 'demo/file1', 33),
            'file2': ('/tmp/demo3.zip', 'demo/file2', 33),
            'file3': ('/tmp/demo3.zip', 'demo/file3', 33),
            'file4': ('/tmp/demo3.zip', 'demo/file4', 33),
            'file5': ('/tmp/demo3.zip', 'demo/file5', 33),
            'file6': ('/tmp/demo3.zip', 'demo/file6', 33),
        }})

        self.assertEqual(
            list(m.reverse_mapping['demo/']),
            [('/tmp/demo3.zip', 'demo/', 0)],
        )
        self.assertEqual(sorted(m.archives.keys()), ['/tmp/demo3.zip'])
        self.assertEqual(
            sorted(m.archive_ifilenames['/tmp/demo3.zip']), [
                'demo/', 'demo/file1', 'demo/file2', 'demo/file3',
                'demo/file4', 'demo/file5', 'demo/file6'
        ])

        # finally, unload the final one.
        m._unload_infolist('/tmp/demo3.zip')

        self.assertEqual(m.mapping, {})
        self.assertEqual(m.reverse_mapping, {})
        self.assertEqual(m.archives, {})
        self.assertEqual(m.archive_ifilenames, {})

    def test_unload_infolist_multiple_reload(self):
        demo = path('demo2.zip')

        m = DefaultMapper()
        with ZipFile(demo) as zf:
            m._load_infolist('/tmp/demo1.zip', zf.infolist())
            m._load_infolist('/tmp/demo2.zip', zf.infolist())
            m._load_infolist('/tmp/demo3.zip', zf.infolist())

        m._unload_infolist('/tmp/demo1.zip')
        d2list = {
            'file1': ('/tmp/demo2.zip', 'demo/file1', 33),
            'file2': ('/tmp/demo2.zip', 'demo/file2', 33),
            'file3': ('/tmp/demo2.zip', 'demo/file3', 33),
            'file4': ('/tmp/demo2.zip', 'demo/file4', 33),
            'file5': ('/tmp/demo2.zip', 'demo/file5', 33),
            'file6': ('/tmp/demo2.zip', 'demo/file6', 33),
        }
        self.assertEqual(m.mapping, {'demo': d2list})

        with ZipFile(demo) as zf:
            m._load_infolist('/tmp/demo4.zip', zf.infolist())

        # Shouldn't overwrite now.
        self.assertEqual(m.mapping['demo'], d2list)

        m._unload_infolist('/tmp/demo2.zip')

        # Shouldn't be affected because they don't belong to demo2.
        self.assertEqual(m.mapping['demo'], {
            k: ('/tmp/demo3.zip', v[1], v[2]) for k, v in d2list.items()
        })

        # latest one is unloaded.
        self.assertEqual(list(v[0] for v in m.reverse_mapping['demo/']),
                         ['/tmp/demo3.zip', '/tmp/demo4.zip'])
        self.assertEqual(sorted(m.archives.keys()),
                         ['/tmp/demo3.zip', '/tmp/demo4.zip'])
        self.assertEqual(
            sorted(m.archive_ifilenames['/tmp/demo3.zip']), [
                'demo/', 'demo/file1', 'demo/file2', 'demo/file3',
                'demo/file4', 'demo/file5', 'demo/file6'
        ])

        m._unload_infolist('/tmp/demo4.zip')
        self.assertEqual(m.mapping['demo'], {
            k: ('/tmp/demo3.zip', v[1], v[2]) for k, v in d2list.items()
        })

        # everything still removed, at last.
        m._unload_infolist('/tmp/demo3.zip')
        self.assertEqual(m.mapping, {})

    def test_unload_infolist_multiple_overwrite(self):
        demo = path('demo2.zip')
        m = DefaultMapper(overwrite=True)
        with ZipFile(demo) as zf:
            m._load_infolist('/tmp/demo1.zip', zf.infolist())
            m._load_infolist('/tmp/demo2.zip', zf.infolist())
            m._load_infolist('/tmp/demo3.zip', zf.infolist())

        d3list = {
            'file1': ('/tmp/demo3.zip', 'demo/file1', 33),
            'file2': ('/tmp/demo3.zip', 'demo/file2', 33),
            'file3': ('/tmp/demo3.zip', 'demo/file3', 33),
            'file4': ('/tmp/demo3.zip', 'demo/file4', 33),
            'file5': ('/tmp/demo3.zip', 'demo/file5', 33),
            'file6': ('/tmp/demo3.zip', 'demo/file6', 33),
        }

        self.assertEqual(m.mapping, {'demo': d3list})

        # Unloading the latest one.
        m._unload_infolist('/tmp/demo3.zip')

        self.assertEqual(m.mapping['demo'], {
            k: ('/tmp/demo2.zip', v[1], v[2]) for k, v in d3list.items()
        })

        self.assertEqual(list(f[0] for f in m.reverse_mapping['demo/']),
                         ['/tmp/demo1.zip', '/tmp/demo2.zip'])
        self.assertEqual(sorted(m.archives.keys()),
                         ['/tmp/demo1.zip', '/tmp/demo2.zip'])
        self.assertEqual(
            sorted(m.archive_ifilenames['/tmp/demo1.zip']), [
                'demo/', 'demo/file1', 'demo/file2', 'demo/file3',
                'demo/file4', 'demo/file5', 'demo/file6'
        ])

        with ZipFile(demo) as zf:
            m._load_infolist('/tmp/demo4.zip', zf.infolist())

        m._unload_infolist('/tmp/demo1.zip')
        self.assertEqual(m.mapping['demo'], {
            k: ('/tmp/demo4.zip', v[1], v[2]) for k, v in d3list.items()
        })
        self.assertEqual(
            list(f[0] for f in m.reverse_mapping['demo/']),
           ['/tmp/demo1.zip', '/tmp/demo2.zip', '/tmp/demo4.zip']
        )

        m._unload_infolist('/tmp/demo2.zip')
        self.assertEqual(m.mapping['demo'], {
            k: ('/tmp/demo4.zip', v[1], v[2]) for k, v in d3list.items()
        })
        self.assertEqual(
            list(f[0] for f in m.reverse_mapping['demo/']),
           ['/tmp/demo1.zip', '/tmp/demo2.zip', '/tmp/demo4.zip']
        )

        # Finally everything that can be cleaned, cleaned.
        m._unload_infolist('/tmp/demo4.zip')
        self.assertEqual(m.mapping, {})
        self.assertEqual(m.reverse_mapping, {})
        self.assertEqual(m.archives, {})
        self.assertEqual(m.archive_ifilenames, {})

    def test_unload_infolist_dir_file_conflict(self):
        m = DefaultMapper()
        m._load_infolist('/tmp/demo1.zip', [zipinfo('demo/')])
        m._load_infolist('/tmp/demo2.zip', [zipinfo('demo')])
        self.assertEqual(m.mapping, {'demo': {}})
        m._unload_infolist('/tmp/demo2.zip')
        self.assertEqual(m.mapping, {'demo': {}})

    def test_unload_infolist_file_dir_conflict(self):
        m = DefaultMapper()
        m._load_infolist('/tmp/demo1.zip', [zipinfo('demo')])
        m._load_infolist('/tmp/demo2.zip', [zipinfo('demo/')])
        self.assertEqual(m.mapping, {'demo': ('/tmp/demo1.zip', 'demo', 0)})
        m._unload_infolist('/tmp/demo1.zip')
        # directory not created.
        self.assertEqual(m.mapping, {})

    def test_unload_infolist_file_dir_dir_conflict(self):
        m = DefaultMapper()
        m._load_infolist('/tmp/demo1.zip', [zipinfo('demo')])
        m._load_infolist('/tmp/demo2.zip', [zipinfo('demo/')])
        m._load_infolist('/tmp/demo3.zip', [zipinfo('demo/demo.txt', 1)])
        self.assertEqual(m.mapping, {'demo': ('/tmp/demo1.zip', 'demo', 0)})
        m._unload_infolist('/tmp/demo1.zip')
        # directory not created.  Alternative implementation could have
        # added the same entry to a shadow location so it would show up
        # here, hide it again when inactive.
        self.assertEqual(m.mapping, {})
        m._unload_infolist('/tmp/demo3.zip')
        self.assertEqual(m.mapping, {})

    def test_unload_infolist_dir_unloading(self):
        m = DefaultMapper()
        m._load_infolist('/tmp/demo1.zip', [zipinfo('demo/demo/1.txt', 1)])
        m._load_infolist('/tmp/demo2.zip', [zipinfo('demo/')])
        m._load_infolist('/tmp/demo3.zip', [zipinfo('demo')])
        m._load_infolist('/tmp/demo4.zip', [zipinfo('demo/demo4.txt', 1)])
        self.assertEqual(m.mapping, {'demo': {
            'demo': {'1.txt': ('/tmp/demo1.zip', 'demo/demo/1.txt', 1)},
            'demo4.txt': ('/tmp/demo4.zip', 'demo/demo4.txt', 1),
        }})
        m._unload_infolist('/tmp/demo1.zip')
        self.assertEqual(m.mapping, {'demo': {
            'demo4.txt': ('/tmp/demo4.zip', 'demo/demo4.txt', 1),
        }})

        m._load_infolist('/tmp/demo1.zip', [zipinfo('demo/demo/1.txt', 1)])
        m._unload_infolist('/tmp/demo4.zip')
        self.assertEqual(m.mapping, {'demo': {
            'demo': {'1.txt': ('/tmp/demo1.zip', 'demo/demo/1.txt', 1)},
        }})

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

        self.assertDemo3ThenDemo4(m, demo3, demo4)

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
