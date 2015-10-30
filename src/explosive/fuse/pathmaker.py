from os.path import basename

FLATTEN_CHAR = '_'

__all__ = [
    'default',
    'flatten',
    'junk',
]


def default():
    """
    Present file entries as they were within their respective directory
    structures to the root of its source archive.
    """

    def default(inner_path):
        frags = inner_path.split('/')
        filename = frags.pop()

        return frags, filename

    return default


def flatten(flatten_char='_'):
    """
    Flattens the directory structure to the root of the mount point by
    replacing all path separators for each file entries with the `_`
    character by default.
    """

    def flatten(inner_path):
        if inner_path.endswith('/'):
            # Directories shouldn't result in a file entry.
            return [], ''

        return [], inner_path.replace('/', flatten_char)

    return flatten


def junk():
    """
    Junk all paths, keep only the basename of file entries.
    """

    def junk(inner_path):
        return [], basename(inner_path)  # basename will truncate dirs.

    return junk
