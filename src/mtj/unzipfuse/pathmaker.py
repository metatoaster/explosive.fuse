from os.path import basename


def default(zipfile_path, inner_path):
    """
    By default ignore the zipfile_path and only treat the inner_path by
    taking the final item and returning the rest as fragments as
    specified.
    """

    frags = inner_path.split('/')
    filename = frags.pop()

    return frags, filename


def ziproot(zipfile_path, inner_path):
    """
    Same as default_pathmaker, but this adds the name of the zipfile to
    the beginning of the dir fragments returned.
    """

    frags = [basename(zipfile_path)]
    frags.extend(inner_path.split('/'))
    filename = frags.pop()

    return frags, filename

