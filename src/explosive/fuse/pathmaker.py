from os.path import basename

FLATTEN_CHAR = '_'


def default(zipfile_path, inner_path):
    """
    By default ignore the zipfile_path and only treat the inner_path by
    taking the final item and returning the rest as fragments as
    specified.
    """

    frags = inner_path.split('/')
    filename = frags.pop()

    return frags, filename


def flatten(zipfile_path, inner_path):
    """
    Flattens the inner_path by replacing all path separators with the
    FLATTEN_CHAR defined in this module.
    """

    if inner_path.endswith('/'):
        # Directories shouldn't result in a file entry.
        return [], ''

    return [], inner_path.replace('/', FLATTEN_CHAR)


def junk(zipfile_path, inner_path):
    """
    Junk the entire path by only returning the inner filename.
    """

    return [], basename(inner_path)  # basename will truncate dirs.


def ziproot(zipfile_path, inner_path):
    """
    Same as default, but this adds the name of the zipfile to the
    beginning of the dir fragments returned.
    """

    frags = [basename(zipfile_path)]
    frags.extend(inner_path.split('/'))
    filename = frags.pop()

    return frags, filename


def ziproot_flatten(zipfile_path, inner_path):
    """
    Combining ziproot and flatten.  Essentially the name of the zipfile
    is prepended to the resulting filename.
    """

    if inner_path.endswith('/'):
        # Directories shouldn't result in a file entry.
        return [], ''

    fn = basename(zipfile_path) + '_' + inner_path.replace('/', FLATTEN_CHAR)
    return [], fn
