import sys
import logging

from argparse import ArgumentParser
from argparse import Action
from argparse import HelpFormatter
from fuse import FUSE

from explosive.fuse import pathmaker
from explosive.fuse.fs import ExplosiveFUSE


class _LayoutHelp(Action):

    def __init__(self, *a, **kw):
        super(_LayoutHelp, self).__init__(nargs=0, *a, **kw)

    def __call__(self, *a, **kw):
        actions = [
            Action([i], help=getattr(pathmaker, i).__doc__, dest='')
            for i in sorted(pathmaker.__all__)
            if not i.startswith('_') and callable(getattr(pathmaker, i))
        ]
        formatter = HelpFormatter('')
        formatter.add_text(
            'An explicit layout strategy can be specified.  This is to '
            'instruct how ExplosiveFUSE should present file entries across '
            'all archive files within its mount point.  Do note that '
            'the final outcome of the layout is also influenced by the usage '
            'of the ``--overwrite`` and the ``--omit-arcname`` flags.'
        )
        formatter.start_section('Available layout strategies')
        formatter.add_arguments(actions)
        formatter.end_section()
        print(formatter.format_help())
        sys.exit(0)


def get_argparse():
    layout_choices = sorted(
        i for i in pathmaker.__all__
        if not i.startswith('_') and callable(getattr(pathmaker, i))
    )

    parser = ArgumentParser(
        description='ExplosiveFUSE: Explode compressed files into a '
                    'filesystem, carefully.'
    )
    parser.register('action', 'layout_help', _LayoutHelp)

    parser.add_argument(
        '-l', '--layout', dest='pathmaker_name', choices=layout_choices,
        metavar='<strategy>', default='default',
        help='Directory layout presentation strategy.  '
             'Available strategies are: ' +
             ', '.join(layout_choices) + '. '
             'If unspecified, the default is `%(default)s`.'
    )
    parser.add_argument(
        '--layout-info', action='layout_help',
        help='Information on the various layout presentation strategy.')
    parser.add_argument(
        '-f', '--foreground', dest='foreground', action='store_true',
        help='Run in foreground.')
    parser.add_argument(
        '-d', '--debug', dest='debug', action='store_true',
        help='Run with debug messages.')
    parser.add_argument(
        'dir',
        help='The directory to mount the compressed archive(s) to.')
    parser.add_argument(
        'archives', metavar='archives', nargs='+',
        help='The archive(s) to generate directory structures with')
    parser.add_argument(
        '--overwrite', dest='overwrite', action='store_true',
        help='Existing file entries will be overwritten by later file entries '
             'if they share the same generated path.')
    parser.add_argument(
        '--omit-arcname', dest='include_arcname', action='store_false',
        help='Omit the basename of the origin archive from the generated '
             'paths.')

    return parser


def main(args=None):
    if args is None:  # pragma: no cover
        args = sys.argv[1:]

    parser = get_argparse()

    parsed_args = parser.parse_args(args)

    if parsed_args.debug:
        logging.basicConfig(
            level='INFO',
            format='%(asctime)s %(levelname)s %(name)s %(message)s'
        )

    try:
        FUSE(
            ExplosiveFUSE(
                parsed_args.archives,
                pathmaker_name=parsed_args.pathmaker_name,
                overwrite=parsed_args.overwrite,
                include_arcname=parsed_args.include_arcname,
            ),
            parsed_args.dir,
            foreground=parsed_args.foreground,
        )
    except RuntimeError:
        # assume error messages are properly handled.
        sys.exit(255)

if __name__ == '__main__':  # pragma: no cover
    main()
