import unittest
from os.path import dirname
from os.path import join

from mtj.unzipfuse.mapper import DefaultMapper


path = lambda p: join(dirname(__file__), 'data', p)

class DefaultMapperTestCase(unittest.TestCase):

    maxDiff = 12300

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_mkdir(self):
        m = DefaultMapper()
        result = m.mkdir(['1', '2', '3'])
        self.assertEqual(result, m.mapping['1']['2']['3'])

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
        m.load_zip(demo3)
        m.load_zip(demo4)
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
