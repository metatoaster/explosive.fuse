import logging
from os.path import join
from os.path import abspath
from os.path import basename
from os import getcwd

from errno import ENOENT
from errno import EPERM
from stat import S_IFDIR
from stat import S_IFLNK
from stat import S_IFREG
from time import time

from fuse import FuseOSError, Operations, LoggingMixIn
from fuse import ENOTSUP

from explosive.fuse.mapper import DefaultMapper

logger = logging.getLogger(__name__)

now = time()
# Turn this into a type that always return those key/values to avoid
# data repetition.
file_record = dict(
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

link_record = dict(
    st_mode=(S_IFLNK | 0o444),
    st_nlink=1,
    st_ctime=now,
    st_mtime=now,
    st_atime=now,
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
        loaded = sum(self.mapping.load_archive(abspath(p))
                     for p in archive_paths)
        logger.info('loaded %d archive(s).', loaded)

    def getattr(self, path, fh=None):
        key = path[1:]

        info = self.mapping.traverse(key)
        if info is None:
            raise FuseOSError(ENOENT)

        if isinstance(info, dict):
            return dir_record

        result = {'st_size': info[2]}
        result.update(file_record)
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


class SymlinkFUSE(LoggingMixIn, Operations):
    """
    A symlink only filesystem that exist in memory.
    """

    def __init__(self, mount_root, base_path='/'):
        """
        The base directory where the symlinks are exposed.
        """

        # assert that base_path starts with '/'.  This is not a key
        # like the mapping where it's relative to where it's based.

        self.base_path = base_path
        self.mount_root = mount_root
        self.fd = 0
        self.symlinks = {}  # keys are the basename.

    def getattr(self, path, fh=None):
        if path == '/':
            path = ''
        if not path.startswith(self.base_path):
            # might not be a real path in the system.
            if (self.base_path.startswith(path) and
                    self.base_path[len(path)] == '/'):
                # a valid parent directory to the base_path.
                return dir_record
            raise FuseOSError(ENOENT)

        if path == self.base_path:
            return dir_record

        symkey = basename(path)
        data = self.symlinks.get(symkey)
        if data is None:
            raise FuseOSError(ENOENT)
        result = {'st_size': len(data)}
        result.update(link_record)
        return result

    def create(self, path, mode, fi=None):
        raise FuseOSError(ENOTSUP)

    def mkdir(self, path, mode):
        raise FuseOSError(ENOTSUP)

    def readlink(self, path):
        symkey = basename(path)
        return self.symlinks[symkey]

    def readdir(self, path, fh):
        if not path == self.base_path:
            if path == '/':
                path = ''
            return ['.', '..', self.base_path[len(path):].split('/')[1]]
        return ['.', '..'] + list(self.symlinks.keys())

    def symlink(self, path, source):
        if not path.startswith(self.base_path):
            # symlinks must be created inside base_path.
            raise FuseOSError(EPERM)
        symkey = basename(path)
        self.symlinks[symkey] = abspath(join(
            self.mount_root, self.base_path[1:], source))

    def unlink(self, path):
        symkey = basename(path)
        if symkey not in self.symlinks:
            raise FuseOSError(ENOTSUP)
        self.symlinks.pop(symkey)

    def statfs(self, path):
        return {'f_bsize': 0, 'f_blocks': 0, 'f_bavail': 0}
