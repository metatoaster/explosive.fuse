import sys
import logging
from os.path import abspath
from os.path import join
from os import getcwd

from argparse import ArgumentError
from argparse import ArgumentParser
from argparse import Action
from argparse import _StoreAction
from argparse import HelpFormatter
from fuse import FUSE

from explosive.fuse import pathmaker
from explosive.fuse.fs import ExplosiveFUSE
from explosive.fuse.fs import ManagedExplosiveFUSE


class _Version(Action):

    def __init__(self, *a, **kw):
        super(_Version, self).__init__(nargs=0, *a, **kw)

    def __call__(self, *a, **kw):
        try:
            import pkg_resources
            r = pkg_resources.require('explosive.fuse')[0]
            print('explode ' + r.version)
            print(repr(r))
        except ImportError:  # pragma: no cover
            print('explode ?')
        except pkg_resources.DistributionNotFound:  # pragma: no cover
            print('explode ?')
        print(
            'License GPLv3+: GNU GPL version 3 or later '
            '<http://gnu.org/licenses/gpl.html>.\n'
            'This is free software: '
            'you are free to change and redistribute it.\n'
            'There is NO WARRANTY, to the extent permitted by law.'
        )
        sys.exit(0)


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
            "An explicit layout strategy can be specified.  This is to "
            "instruct how ExplosiveFUSE should present file entries across "
            "all archive files within its mount point.  Do note that "
            "the final outcome of the layout is also influenced by the usage "
            "of the '--overwrite' and the '--omit-arcname' flags, and "
            "arguments which may associate with each of the strategies. "
            "They are specified by appending ':', followed by the value of "
            "each positional argument(s)."
        )
        formatter.start_section('Available layout strategies')
        formatter.add_arguments(actions)
        formatter.end_section()
        print(formatter.format_help())
        sys.exit(0)


class _PathmakerChoiceStoreAction(_StoreAction):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            pm = pathmaker._process_arg(values)
            # pass pm as values as it is the callable to be used.
            return super(_PathmakerChoiceStoreAction, self).__call__(
                parser, namespace, pm, option_string)
        except ValueError as e:
            raise ArgumentError(self, e.args[0])


def get_argparse():
    layout_choices = sorted(
        i for i in pathmaker.__all__
        if not i.startswith('_') and callable(getattr(pathmaker, i))
    )

    parser = ArgumentParser(
        description='ExplosiveFUSE: Explode compressed files into a '
                    'filesystem, carefully.'
    )
    parser.register('action', 'version_verbose', _Version)
    parser.register('action', 'layout_help', _LayoutHelp)
    parser.register('action', 'pathmaker_store', _PathmakerChoiceStoreAction)

    parser.add_argument(
        '-l', '--layout', dest='pathmaker', action='pathmaker_store',
        metavar='<strategy>', default=pathmaker.default(),
        help="Directory layout presentation strategy.  "
             "Available strategies are: '" +
             "', '".join(layout_choices) + "'. "
             "If unspecified, the default is '%(default)s'."
    )
    parser.add_argument(
        '--layout-info', action='layout_help',
        help='More detailed information on the usage of layout presentation '
             'strategy (such as extra arguments).')
    parser.add_argument(
        '-d', '--debug', dest='debug', action='store_true',
        help='Run with debug messages.')
    parser.add_argument(
        '-f', '--foreground', dest='foreground', action='store_true',
        help='Run in foreground.')
    parser.add_argument(
        '-m', '--manager', dest='manager', action='store_true',
        help='Enable the symlink manager directory, where all the archives '
             'indexed and available within this ExplosiveFUSE instance are '
             'exposed as symlinks.  These symlinks can be removed to remove '
             'the associated files from the filesystem, and new symlinks to '
             'other archives can be created to add them to the filesystem.')
    parser.add_argument(
        '--manager-dir', dest='manager_dir', nargs='?', default='.manager',
        help='Explictly define the name of the symlink manager directory. '
             "Default is '%(default)s'.")
    parser.add_argument(
        '--overwrite', dest='overwrite', action='store_true',
        help='Newly added entries will overlay existing entries of a given '
             'name for a name collision, as if overwriting the existing '
             'version. Default behavior to keep the oldest added file in '
             'that place until its source archive is removed, then the next '
             'one added with that name then be presented there.')
    parser.add_argument(
        '--omit-arcname', dest='include_arcname', action='store_false',
        help='Omit the basename of the origin archive from the generated '
             'paths.')
    parser.add_argument(
        '-V', '--version', action='version_verbose',
        help='Print version information and exit.')
    parser.add_argument(
        'dir',
        help='The directory to mount the compressed archive(s) to.')
    parser.add_argument(
        'archives', metavar='archives', nargs='+',
        help='The archive(s) to generate directory structures with')

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

    if parsed_args.manager:
        mount_root = abspath(join(getcwd(), parsed_args.dir))
        fuse = ManagedExplosiveFUSE(
            mount_root,
            parsed_args.manager_dir,
            parsed_args.archives,
            _pathmaker=parsed_args.pathmaker,
            overwrite=parsed_args.overwrite,
            include_arcname=parsed_args.include_arcname,
        )
    else:
        fuse = ExplosiveFUSE(
            parsed_args.archives,
            _pathmaker=parsed_args.pathmaker,
            overwrite=parsed_args.overwrite,
            include_arcname=parsed_args.include_arcname,
        )

    try:
        FUSE(fuse, parsed_args.dir, foreground=parsed_args.foreground,
             nothreads=True)
    except RuntimeError:
        # assume error messages are properly handled.
        sys.exit(255)

if __name__ == '__main__':  # pragma: no cover
    main()
