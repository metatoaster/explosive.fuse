from logging import getLogger
from os.path import abspath
from os.path import basename
from glob import glob
from zipfile import ZipFile
from zipfile import BadZipFile


logger = getLogger(__name__)


def normalize(zip_fn, path, _char='_'):
    """
    Return a normalized identifier that can serve as a filename.  The
    replacement character should not be a path separator.
    """

    return zip_fn + _char + path.replace('/', _char)


class Mapping(object):
    """
    Map zip files to a string.
    """

    def __init__(self, path=None):
        """
        """

        # An identifier that maps an identifer to a 3-tuple that contain
        # a path to zip file, a path to a compressed file and its size.
        self.mapping = {}
        if path:
            self.glob(path)

    def glob(self, path):
        """
        Glob all the zip files in path into the mapping
        """

        for path in glob(abspath(path)):
            try:
                with ZipFile(path) as zf:
                    for info in zf.infolist():
                        if info.file_size == 0:
                            continue
                        key = normalize(basename(path), info.filename)
                        self.mapping[key] = (path, info, info.file_size)
            except BadZipFile:
                continue

    def readfile(self, key):
        """
        Return the complete file with information contained in key.
        """

        zipfn, filename, _ = self.mapping[key]
        with ZipFile(zipfn) as zf:
            with zf.open(filename) as f:
                return f.read()
