import logging

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

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
    st_mode=(S_IFDIR | 0o755),
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

    def __init__(self, *path):
        self.fd = 0
        self.mapping = DefaultMapper()
        loaded = sum(self.mapping.load_zip(p) for p in path)
        logger.info('loaded %d zip file(s).', loaded)

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


if __name__ == '__main__':
    if len(argv) < 3:
        print('usage: %s mountpoint zipfile [zipfile ...]' % argv[0])
        exit(1)

    logging.getLogger().setLevel(logging.DEBUG)
    fuse = FUSE(ExplosiveFUSE(*argv[2:]), argv[1], foreground=True)
