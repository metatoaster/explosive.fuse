import sys
from argparse import ArgumentParser

from explosive.fuse import pathmaker

layout_choices = sorted(
    i for i in pathmaker.__all__
    if not i.startswith('_') and callable(getattr(pathmaker, i))
)

parser = ArgumentParser(
    description='Explode compressed files into a filesystem, carefully.')
parser.add_argument(
    '-l', '--layout', dest='pathmaker_name', choices=layout_choices,
    help='Directory layout choices.')
parser.add_argument(
    '-f', '--foreground', dest='foreground', const=True, default=False,
    action='store_const',
    help='Run in foreground.')
parser.add_argument(
    '-d', '--debug', dest='debug', const=True, default=False,
    action='store_const',
    help='Run with debug messages.')
parser.add_argument(
    'dir',
    help='The directory to mount the compressed archive(s) to.')
parser.add_argument(
    'archives', metavar='archives', nargs='+',
    help='The archive(s) to generate directory structures with')
