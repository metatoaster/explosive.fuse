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

    def test_junk(self):
        self.assertPathmaker(pathmaker.junk(), [
            ('path/to/file', ([], 'file')),
            ('rootfile', ([], 'rootfile')),
            ('somedir/', ([], '')),
            ('some/nested/dir/', ([], '')),
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

    def test_process_callable(self):
        self.assertTrue(callable(pathmaker._process_arg('default')))
        self.assertTrue(callable(pathmaker._process_arg('flatten')))
        self.assertTrue(callable(pathmaker._process_arg('junk')))

    def test_process_flatten(self):
        f = pathmaker._process_arg('flatten')
        self.assertEqual(f('path/to/file'), ([], 'path_to_file'))

        f = pathmaker._process_arg('flatten:\\:')
        self.assertEqual(f('path/to/file'), ([], 'path:to:file'))
