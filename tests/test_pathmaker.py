import unittest

from explosive.fuse import pathmaker


class PathmakerTestCase(unittest.TestCase):

    def test_default(self):
        self.assertEqual(
            pathmaker.default('path/to/file'),
            (['path', 'to'], 'file'),
        )

        self.assertEqual(
            pathmaker.default('rootfile'),
            ([], 'rootfile'),
        )

        self.assertEqual(
            pathmaker.default('somedir/'),
            (['somedir'], ''),
        )

        self.assertEqual(
            pathmaker.default('some/nested/dir/'),
            (['some', 'nested', 'dir'], ''),
        )

    def test_flatten(self):
        self.assertEqual(
            pathmaker.flatten('path/to/file'),
            ([], 'path_to_file'),
        )

        self.assertEqual(
            pathmaker.flatten('rootfile'),
            ([], 'rootfile'),
        )

        self.assertEqual(
            pathmaker.flatten('somedir/'),
            ([], ''),
        )

        self.assertEqual(
            pathmaker.flatten('some/nested/dir/'),
            ([], ''),
        )

    def test_junk(self):
        self.assertEqual(
            pathmaker.junk('path/to/file'),
            ([], 'file'),
        )

        self.assertEqual(
            pathmaker.junk('rootfile'),
            ([], 'rootfile'),
        )

        self.assertEqual(
            pathmaker.junk('somedir/'),
            ([], ''),
        )

        self.assertEqual(
            pathmaker.junk('some/nested/dir/'),
            ([], ''),
        )
