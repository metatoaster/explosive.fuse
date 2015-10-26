from logging import getLogger
from os.path import abspath
from os.path import basename
from glob import glob
from zipfile import ZipFile
from zipfile import BadZipFile

from . import pathmaker

logger = getLogger(__name__)


class DefaultMapper(object):
    """
    Mapper that tracks the nested structure within a zip file.
    """

    def __init__(self, path=None, pathmaker_name='root'):
        """
        Initialize the mapping, optionally with a path to a zip file.

        Mapping dict keys are names of file or directory, values are
        either a tuple that represent a file, or a dict to represent a
        directory.
        """

        self.pathmaker = getattr(pathmaker, pathmaker_name)
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

        for c, frag in enumerate(path_fragments):
            if frag in current:
                current = current[frag]
                if not isinstance(current, dict):
                    raise ValueError(
                        'cannot create directory `%(filename)s` at '
                        '`%(path)s/`: file entry exists.' % {
                            'filename': frag,
                            'path': '/'.join(path_fragments[:c]),
                        }
                    )
            else:
                # create directory dict entry and set current.
                current[frag] = current = {}

        return current

    def traverse(self, path):
        """
        Traverse to path, or return the entry identified by path.
        """

        path_fragments = path and path.split('/') or []
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
            try:
                target = self.mkdir(frags)
            except ValueError as e:
                logger.warning(
                    '`%s` could not be created: %s', info.filename, e.args[0])
                continue

            if not filename:
                # was a directory entry
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
            logger.info('loaded `%s`', zipfile_path)
            return True
        except BadZipFile:
            logger.warning(
                '`%s` appears to be an invalid zipfile', zipfile_path)
        except FileNotFoundError:
            logger.warning(
                '`%s` does not exist.', zipfile_path)
        except:
            logger.exception('Exception')
        return False

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

    def readdir(self, path):
        """
        Return a listing of all files in a directory
        """

        info = self.traverse(path)
        if not isinstance(info, dict):
            return []
        return list(info.keys())
