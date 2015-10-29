from os.path import basename

FLATTEN_CHAR = '_'

__all__ = [
    'root',
    'flatten',
    'junk',
]


def root(inner_path):
    """
    Present file entries to the root of the mount point.
    """

    frags = inner_path.split('/')
    filename = frags.pop()

    return frags, filename


def flatten_maker(flatten_char=FLATTEN_CHAR):

    def flatten(inner_path):

        if inner_path.endswith('/'):
            # Directories shouldn't result in a file entry.
            return [], ''

        return [], inner_path.replace('/', flatten_char)

    flatten.__doc__ = """
    Flattens the directory structure to the root by replacing all
    path separators for each file entries with the `%s` character.
    """ % flatten_char

    return flatten

flatten = flatten_maker()


def junk(inner_path):
    """
    Junk all paths, keep only the basename of file entries.
    """

    return [], basename(inner_path)  # basename will truncate dirs.
