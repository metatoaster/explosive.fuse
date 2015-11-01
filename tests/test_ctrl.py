import sys
import os
from argparse import ArgumentParser
from argparse import ArgumentError
from contextlib import contextmanager
import unittest
from os.path import dirname
from os.path import join
from multiprocessing import Process
from subprocess import Popen
from subprocess import PIPE
from tempfile import mkdtemp

from explosive.fuse import ctrl

path = lambda p: join(dirname(__file__), 'data', p)


# mixture of unicode and str in python2.7 version of argparse means that
# default IO classes would be painful to use; use my own thing here.
class Input(object):

    def __init__(self, inputs):
        self.inputs = inputs.splitlines()

    def readline(self):
        if self.inputs:
            return self.inputs.pop(0)
        else:
            raise EOFError()


class Output(object):

    def __init__(self):
        self.items = []

    def write(self, s):
        self.items.append(s)

    def flush(self):
        pass


@contextmanager
def capture_stdio(inputs=''):
    dummy_in, dummy_out, dummy_err = Input(inputs), Output(), Output()
    curr_in, curr_out, curr_err = sys.stdin, sys.stdout, sys.stderr
    try:
        sys.stdin, sys.stdout, sys.stderr = dummy_in, dummy_out, dummy_err
        yield dummy_in, dummy_out, dummy_err
    finally:
        sys.stdin, sys.stdout, sys.stderr = curr_in, curr_out, curr_err


class PathMakerChoiceTestCase(unittest.TestCase):

    def test_argument_error(self):
        ap = ArgumentParser()
        action = ctrl._PathmakerChoiceStoreAction(None, 'dummy', 1)
        with self.assertRaises(ArgumentError) as cm:
            action(ap, ap, 'nothing', None)

    def test_argument_success(self):
        ap = ArgumentParser()
        action = ctrl._PathmakerChoiceStoreAction(None, 'dummy', 1)
        action(ap, ap, 'flatten', None)
        self.assertEqual(ap.dummy.__name__, 'flatten')


class IntegrationTestCase(unittest.TestCase):

    def test_simple(self):
        with capture_stdio() as stdio:
            with self.assertRaises(SystemExit):
                ctrl.main([])

    def test_layout_help(self):
        with capture_stdio() as stdio:
            with self.assertRaises(SystemExit):
                ctrl.main(['--layout-info'])

    def test_failure(self):
        with capture_stdio() as stdio:
            with self.assertRaises(SystemExit):
                ctrl.main(['-d', '/tmp/to/no/such/dir', 'somezip.zip'])

    def test_invalid_layout_choice(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            with self.assertRaises(SystemExit):
                ctrl.main(['-l', 'nothing'])
            self.assertTrue(err.items[-1].endswith(
                "error: argument -l/--layout: "
                "invalid choice: 'nothing' (choose from 'default', "
                "'flatten', 'junk')\n",
            ))

    def test_invalid_layout_arg(self):
        with capture_stdio() as stdio:
            in_, out, err = stdio
            with self.assertRaises(SystemExit):
                ctrl.main(['-l', 'junk:hi'])
            self.assertTrue(err.items[-1].endswith(
                "error: argument -l/--layout: "
                "invalid argument to 'junk': 'keep' must be a number\n"
            ))


# Acceptance testing
# to enable, do something like:
# $ ACCEPTANCE=1 python setup.py test
#
# Disabling by default due to issues with getting this working reliably
# with other CI systems.

@unittest.skipUnless(os.environ.get('ACCEPTANCE'),
                     'skipping acceptance test by default')
class AcceptanceTestCase(unittest.TestCase):

    def setUp(self):
        self.mountpoint = mkdtemp()
        # maybe validate that this works?
        # subprocess.check_output(["fusermount", "-V"])

    def tearDown(self):
        sp = Popen(['fusermount', '-u', self.mountpoint],
                   stdout=PIPE, stderr=PIPE)
        result = sp.communicate()

    def test_success_basic(self):
        dummy1 = path('demo1.zip')
        dummy2 = path('demo2.zip')

        # This will terminate, so spawn a separate process.
        p = Process(
            target=ctrl.main, args=(['-d', self.mountpoint, dummy1, dummy2],))
        p.start()
        p.join()

        self.assertEqual(
            sorted(os.listdir(self.mountpoint)),
            ['demo1.zip', 'demo2.zip'],
        )

        self.assertEqual(
            sorted(os.listdir(join(self.mountpoint, 'demo1.zip'))),
            ['file1', 'file2', 'file3', 'file4', 'file5', 'file6']
        )

        self.assertEqual(
            sorted(os.listdir(join(self.mountpoint, 'demo2.zip'))),
            ['demo']
        )

        self.assertEqual(
            sorted(os.listdir(join(self.mountpoint, 'demo2.zip', 'demo'))),
            ['file1', 'file2', 'file3', 'file4', 'file5', 'file6']
        )
