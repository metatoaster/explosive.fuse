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

    def test_flatten(self):
        self.assertEqual(
            pathmaker.flatten('/tmp/some/test.zip', 'path/to/file'),
            ([], 'path_to_file'),
        )

        self.assertEqual(
            pathmaker.flatten('/tmp/some/test.zip', 'rootfile'),
            ([], 'rootfile'),
        )

    def test_junk(self):
        self.assertEqual(
            pathmaker.junk('/tmp/some/test.zip', 'path/to/file'),
            ([], 'file'),
        )

        self.assertEqual(
            pathmaker.junk('/tmp/some/test.zip', 'rootfile'),
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

    def test_ziproot_flatten(self):
        self.assertEqual(
            pathmaker.ziproot_flatten('/tmp/some/test.zip', 'path/to/file'),
            ([], 'test.zip_path_to_file'),
        )

        self.assertEqual(
            pathmaker.ziproot_flatten('/tmp/some/test.zip', 'rootfile'),
            ([], 'test.zip_rootfile'),
        )
