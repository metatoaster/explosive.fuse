import unittest

from explosive.fuse import pathmaker


class PathmakerTestCase(unittest.TestCase):

    def assertPathmaker(self, func, pairs):
        """
        For each of the pairs, assume each are 2-tuple of input and the
        expected output, where the input will be passed into `func`.
        """

        for path, output in pairs:
            self.assertEqual(func(path), output)

    def test_default(self):
        self.assertPathmaker(pathmaker.default(), [
            ('path/to/file', (['path', 'to'], 'file')),
            ('rootfile', ([], 'rootfile')),
            ('somedir/', (['somedir'], '')),
            ('some/nested/dir/', (['some', 'nested', 'dir'], '')),
        ])

    def test_flatten(self):
        self.assertPathmaker(pathmaker.flatten(), [
            ('path/to/file', ([], 'path_to_file')),
            ('rootfile', ([], 'rootfile')),
            ('somedir/', ([], '')),
            ('some/nested/dir/', ([], '')),
        ])

        with self.assertRaises(ValueError) as cm:
            pathmaker.flatten('/')

        with self.assertRaises(ValueError) as cm:
            pathmaker.flatten('hi')

        self.assertPathmaker(pathmaker.flatten('.'), [
            ('path/to/file', ([], 'path.to.file')),
            ('rootfile', ([], 'rootfile')),
            ('somedir/', ([], '')),
            ('some/nested/dir/', ([], '')),
        ])

    def test_junk(self):
        self.assertPathmaker(pathmaker.junk(), [
            ('path/to/file', ([], 'file')),
            ('rootfile', ([], 'rootfile')),
            ('somedir/', ([], '')),
            ('some/nested/dir/', ([], '')),
        ])

        with self.assertRaises(ValueError) as cm:
            pathmaker.junk('/')

        with self.assertRaises(ValueError) as cm:
            pathmaker.junk('1.0')

        with self.assertRaises(ValueError) as cm:
            pathmaker.junk('1-')

        self.assertPathmaker(pathmaker.junk('1'), [
            ('path/to/file', (['path'], 'file')),
            ('path/file', (['path'], 'file')),
            ('path/to/some/file', (['path'], 'file')),
            ('rootfile', ([], 'rootfile')),
            ('somedir/', (['somedir'], '')),
            ('some/nested/dir/', (['some'], '')),
        ])

        self.assertPathmaker(pathmaker.junk('2'), [
            ('path/to/file', (['path', 'to'], 'file')),
            ('path/to/some/file', (['path', 'to'], 'file')),
        ])

        self.assertPathmaker(pathmaker.junk('-2'), [
            ('path/to/file', (['path', 'to'], 'file')),
            ('path/to/some/file', (['to', 'some'], 'file')),
        ])


class ProcessArgTestCase(unittest.TestCase):

    def test_process_tokenize(self):
        f = pathmaker._tokenize_arg
        self.assertEqual(f('simple'), ['simple'])
        self.assertEqual(f('simple:split'), ['simple', 'split'])
        self.assertEqual(f('simple:split\\:cont:split'),
            ['simple', 'split:cont', 'split'])
        self.assertEqual(f('simple:\\:'), ['simple', ':'])
        # empty paramets omitted.
        self.assertEqual(f('simple:\\:::'), ['simple', ':'])

    def test_process(self):
        self.assertEqual(pathmaker._process_arg('default').__name__, 'default')
        self.assertEqual(pathmaker._process_arg('flatten').__name__, 'flatten')
        self.assertEqual(pathmaker._process_arg('junk').__name__, 'junk')

        with self.assertRaises(ValueError):
            pathmaker._process_arg('nosuchpm')

    def test_process_callable(self):
        self.assertTrue(callable(pathmaker._process_arg('default')))
        self.assertTrue(callable(pathmaker._process_arg('flatten')))
        self.assertTrue(callable(pathmaker._process_arg('junk')))

    def test_process_default(self):
        f = pathmaker._process_arg('default')
        self.assertEqual(f('path/to/file'), (['path', 'to',], 'file'))

        with self.assertRaises(ValueError):
            pathmaker._process_arg('default:hihihi')

    def test_process_flatten(self):
        f = pathmaker._process_arg('flatten')
        self.assertEqual(f('path/to/file'), ([], 'path_to_file'))

        f = pathmaker._process_arg('flatten:\\:')
        self.assertEqual(f('path/to/file'), ([], 'path:to:file'))

        with self.assertRaises(ValueError):
            pathmaker._process_arg('flatten:hihihi')

    def test_process_junk(self):
        f = pathmaker._process_arg('junk:1')
        self.assertEqual(f('path/to/file'), (['path'], 'file'))

        f = pathmaker._process_arg('junk:-1')
        self.assertEqual(f('path/to/file'), (['to'], 'file'))
