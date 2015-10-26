from os.path import basename

FLATTEN_CHAR = '_'

__all__ = [
    'root',
    'flatten',
    'junk',
    'ziproot',
    'ziproot_flatten',
]


def root(zipfile_path, inner_path):
    """
    Present file entries to the root of the mount point.
    """

    frags = inner_path.split('/')
    filename = frags.pop()

    return frags, filename


def flatten_maker(flatten_char=FLATTEN_CHAR):

    def flatten(zipfile_path, inner_path):

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


def junk(zipfile_path, inner_path):
    """
    Junk all paths, keep only the basename of file entries.
    """

    return [], basename(inner_path)  # basename will truncate dirs.


def ziproot(zipfile_path, inner_path):
    """
    Present file entries inside a directory named after its source
    archive file.
    """

    frags = [basename(zipfile_path)]
    frags.extend(inner_path.split('/'))
    filename = frags.pop()

    return frags, filename


def ziproot_flatten_maker(flatten_char=FLATTEN_CHAR):
    def ziproot_flatten(zipfile_path, inner_path):

        if inner_path.endswith('/'):
            # Directories shouldn't result in a file entry.
            return [], ''

        fn = (basename(zipfile_path) + FLATTEN_CHAR +
              inner_path.replace('/', FLATTEN_CHAR))
        return [], fn

    ziproot_flatten.__doc__ = """
    Combining ziproot and flatten.  Flattens the directory structure to
    the root by replacing all path separators for each file entries with
    the `%s` character, with all file names prepended with its source
    archive file name.
    """ % flatten_char

    return ziproot_flatten

ziproot_flatten = ziproot_flatten_maker()
