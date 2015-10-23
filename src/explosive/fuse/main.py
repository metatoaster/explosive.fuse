import sys
import logging

from fuse import FUSE

from explosive.fuse.ctrl import parser
from explosive.fuse.fs import ExplosiveFUSE


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
