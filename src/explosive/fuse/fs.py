import logging

from errno import ENOENT
from stat import S_IFDIR
# from stat import S_IFLNK
from stat import S_IFREG
from time import time

from fuse import FuseOSError, Operations, LoggingMixIn

from explosive.fuse.mapper import DefaultMapper

logger = logging.getLogger(__name__)

now = time()
# Turn this into a type that always return those key/values to avoid
# data repetition.
file_records = dict(
    st_mode=(S_IFREG | 0o444),
    st_nlink=1,
    st_ctime=now,
    st_mtime=now,
    st_atime=now,
)

dir_record = dict(
    st_mode=(S_IFDIR | 0o555),
    st_ctime=now,
    st_mtime=now,
    st_atime=now,
    st_nlink=2,
)


class ExplosiveFUSE(LoggingMixIn, Operations):
    """
    The interface between the mapping and the FUSE bindings (provided
    by the Operations class).
    """

    def __init__(self, archive_paths, pathmaker_name='default', _pathmaker=None,
            overwrite=False, include_arcname=False):
        # if include_arcname is not defined, define it based whether
        # there is a single or multiple archives.
        self.fd = 0
        self.mapping = DefaultMapper(
            pathmaker_name=pathmaker_name,
            _pathmaker=_pathmaker,
            overwrite=overwrite,
            include_arcname=include_arcname,
        )
        loaded = sum(self.mapping.load_archive(p) for p in archive_paths)
        logger.info('loaded %d archive(s).', loaded)

    def getattr(self, path, fh=None):
        key = path[1:]

        info = self.mapping.traverse(key)
        if info is None:
            raise FuseOSError(ENOENT)

        if isinstance(info, dict):
            return dir_record

        result = {'st_size': info[2]}
        result.update(file_records)
        return result

    def open(self, path, flags):
        # TODO implement memory usage tracking by reusing cache.
        self.fd += 1
        return self.fd

    def release(self, path, fh):
        """
        TODO: implement of release of file handle for better memory
        handling.
        """

    def read(self, path, size, offset, fh):
        key = path[1:]
        logger.info('reading data for %s', key)
        data = self.mapping.readfile(key)
        return data[offset:offset + size]

    def readdir(self, path, fh):
        key = path[1:]
        return ['.', '..'] + self.mapping.readdir(key)

    def statfs(self, path):
        # TODO report total size of the zips?
        return dict(f_bsize=1024, f_blocks=1024, f_bavail=0)
