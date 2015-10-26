import unittest

from explosive.fuse import pathmaker


class PathmakerTestCase(unittest.TestCase):

    def test_default(self):
        self.assertEqual(
            pathmaker.root('/tmp/some/test.zip', 'path/to/file'),
            (['path', 'to'], 'file'),
        )

        self.assertEqual(
            pathmaker.root('/tmp/some/test.zip', 'rootfile'),
            ([], 'rootfile'),
        )

        self.assertEqual(
            pathmaker.root('/tmp/some/test.zip', 'somedir/'),
            (['somedir'], ''),
        )

        self.assertEqual(
            pathmaker.root('/tmp/some/test.zip', 'some/nested/dir/'),
            (['some', 'nested', 'dir'], ''),
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

        self.assertEqual(
            pathmaker.flatten('/tmp/some/test.zip', 'somedir/'),
            ([], ''),
        )

        self.assertEqual(
            pathmaker.flatten('/tmp/some/test.zip', 'some/nested/dir/'),
            ([], ''),
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

        self.assertEqual(
            pathmaker.junk('/tmp/some/test.zip', 'somedir/'),
            ([], ''),
        )

        self.assertEqual(
            pathmaker.junk('/tmp/some/test.zip', 'some/nested/dir/'),
            ([], ''),
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

        self.assertEqual(
            pathmaker.ziproot('/tmp/some/test.zip', 'somedir/'),
            (['test.zip', 'somedir'], ''),
        )

        self.assertEqual(
            pathmaker.ziproot('/tmp/some/test.zip', 'some/nested/dir/'),
            (['test.zip', 'some', 'nested', 'dir'], ''),
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

        self.assertEqual(
            pathmaker.ziproot_flatten('/tmp/some/test.zip', 'somedir/'),
            ([], ''),
        )

        self.assertEqual(
            pathmaker.ziproot_flatten(
                '/tmp/some/test.zip', 'some/nested/dir/'),
            ([], ''),
        )
