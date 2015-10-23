import sys
import logging

from argparse import ArgumentParser
from fuse import FUSE

from explosive.fuse import pathmaker
from explosive.fuse.fs import ExplosiveFUSE


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

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parsed_args = parser.parse_args(args)

    if parsed_args.debug:
        logging.basicConfig(
            level='INFO',
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )

    fuse = FUSE(
        ExplosiveFUSE(
            parsed_args.archives, pathmaker_name=parsed_args.pathmaker_name),
        parsed_args.dir,
        foreground=parsed_args.foreground,
    )

if __name__ == '__main__':
    main()
