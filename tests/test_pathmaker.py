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
