from logging import getLogger
from os.path import abspath
from os.path import basename
from glob import glob
from zipfile import ZipFile
from zipfile import BadZipFile

logger = getLogger(__name__)


def default_pathmaker(zipfile_path, inner_path):
    """
    By default ignore the zipfile_path and only treat the inner_path by
    taking the final item and returning the rest as fragments as
    specified.
    """

    frags = inner_path.split('/')
    filename = frags.pop()

    return frags, filename


class DefaultMapper(object):
    """
    Mapper that tracks the nested structure within a zip file.
    """

    def __init__(self, path=None, pathmaker=default_pathmaker):
        """
        Initialize the mapping, optionally with a path to a zip file.

        Mapping dict keys are names of file or directory, values are
        either a tuple that represent a file, or a dict to represent a
        directory.
        """

        self.pathmaker = pathmaker
        self.mapping = {}
        if path:
            self.load_zip(path)

    def mkdir(self, path_fragments):
        """
        Creates the dir entries identified by path if not already exists
        and return the complete directory.
        """

        # set current to root node
        current = self.mapping

        for frag in path_fragments:
            if not isinstance(current, dict):
                # make better error message.
                logger.warning(
                    'Fail to create directory entry at `%s` blocked by file '
                    'entry `%s`.',
                    '/'.join(path_fragments),
                    frag,
                )
                # XXX fix this as this is the WRONG result type.
                return current
            if frag in current:
                # directory dict entry exists, set current to that.
                current = current[frag]
                continue
            # create directory dict entry and set current.
            current[frag] = current = {}

        return current

    def traverse(self, path):
        """
        Traverse to path, or return the entry identified by path.
        """

        path_fragments = path.split('/')
        current = self.mapping

        for frag in path_fragments:
            if not isinstance(current, dict) or frag not in current:
                # No such frag in dir.
                return None
            current = current[frag]

        return current

    def _load_infolist(self, zipfile_path, infolist):
        for info in infolist:
            frags, filename = self.pathmaker(zipfile_path, info.filename)
            target = self.mkdir(frags)
            if not filename:
                # was a directory entry
                continue
            if not isinstance(target, dict):
                logger.info(
                    'Could not create `%s` as preceding dir is a file',
                    info.filename,
                )
                continue
            if filename in target:
                logger.info('`%s` already exists; ignoring', info.filename)
                continue
            target[filename] = (zipfile_path, info.filename, info.file_size)

    def load_zip(self, zipfile_path):
        """
        Load a zip file identified by zipfile_path into the mapping.
        """

        try:
            with ZipFile(zipfile_path) as zf:
                self._load_infolist(zipfile_path, zf.infolist())
        except BadZipFile:
            logger.warning(
                '`%s` appears to be an invalid zipfile', zipfile_path)

    def readfile(self, path):
        """
        Return the complete file with information contained in path.
        """

        # TODO: alternative implementation return zipinfo.open handler

        info = self.traverse(path)

        zipfn, filename, _ = info
        with ZipFile(zipfn) as zf:
            with zf.open(filename) as f:
                return f.read()
