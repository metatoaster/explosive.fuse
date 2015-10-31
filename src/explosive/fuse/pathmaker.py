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


def flatten(char='_'):
    """
    Flattens the directory structure to the root of the mount point by
    replacing all path separators for each file entries with the `_`
    character by default.
    """

    if char == '/':
        raise ValueError('`char` cannot be `/` path separator.')

    if len(char) != 1:
        raise ValueError('`char` must be a single character.')

    def flatten(inner_path):
        if inner_path.endswith('/'):
            # Directories shouldn't result in a file entry.
            return [], ''

        return [], inner_path.replace('/', char)

    return flatten


def junk():
    """
    Junk all paths, keep only the basename of file entries.
    """

    def junk(inner_path):
        return [], basename(inner_path)  # basename will truncate dirs.

    return junk


# TODO consider keeping the "plugins" within a class either by some
# sort of registration mechanism or other.

def _tokenize_arg(arg):
    # limitations: no empty parameters.
    return [i.replace('\\:', ':')
            for i in re.findall(r'((?:[^:\\]*(?:\\.)?)+)', arg) if i]

def _process_arg(arg):
    """
    Convert the string argument into a pathmaker callable.
    """

    g = globals()
    args = _tokenize_arg(arg)
    if args[0] not in __all__:
        raise ValueError('No such pathmaker')
    pm = g.get(args[0])
    if pm is None:
        raise ValueError('No such pathmaker')

    try:
        return pm(*args[1:])
    except TypeError:
        raise ValueError('Invalid argument')
