import unittest

from mtj.unzipfuse import pathmaker


class PathmakerTestCase(unittest.TestCase):

    def test_default(self):
        self.assertEqual(
            pathmaker.default('/tmp/some/test.zip', 'path/to/file'),
            (['path', 'to'], 'file'),
        )

        self.assertEqual(
            pathmaker.default('/tmp/some/test.zip', 'rootfile'),
            ([], 'rootfile'),
        )

    def test_ziproot(self):
        self.assertEqual(
            pathmaker.ziproot('/tmp/some/test.zip', 'path/to/file'),
            (['test.zip', 'path', 'to'], 'file'),
        )

        self.assertEqual(
            pathmaker.ziproot('/tmp/some/test.zip', 'rootfile'),
            (['test.zip'], 'rootfile'),
        )
