import sys
from argparse import ArgumentParser
from argparse import ArgumentError
from contextlib import contextmanager
import unittest
from os.path import dirname
from os.path import join

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
                ctrl.main(['-d', 'somezip.zip', '/tmp/to/no/such/dir'])

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
