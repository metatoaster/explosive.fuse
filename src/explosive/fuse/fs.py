import logging
from os.path import join
from os.path import abspath
from os.path import basename
from os import getcwd
from os import getgid
from os import getuid

from errno import ENOENT
from errno import EIO
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
st_uid = getuid()
st_gid = getgid()

# Turn this into a type that always return those key/values to avoid
# data repetition.
file_record = dict(
    st_mode=(S_IFREG | 0o444),
    st_nlink=1,
    st_ctime=now,
    st_mtime=now,
    st_atime=now,
    st_uid=st_uid,
    st_gid=st_gid,
)

dir_record = dict(
    st_mode=(S_IFDIR | 0o555),
    st_ctime=now,
    st_mtime=now,
    st_atime=now,
    st_nlink=2,  # emulated value, ignores links by subdirectories.
    st_uid=st_uid,
    st_gid=st_gid,
)

link_record = dict(
    st_mode=(S_IFLNK | 0o444),
    st_nlink=1,
    st_ctime=now,
    st_mtime=now,
    st_atime=now,
    st_uid=st_uid,
    st_gid=st_gid,
)


class ExplosiveFUSE(LoggingMixIn, Operations):
    """
    The interface between the mapping and the FUSE bindings (provided
    by the Operations class).
    """

    def __init__(self, archive_paths, pathmaker_name='default',
            _pathmaker=None, overwrite=False, include_arcname=False):
        # if include_arcname is not defined, define it based whether
        # there is a single or multiple archives.
        self.mapping = DefaultMapper(
            pathmaker_name=pathmaker_name,
            _pathmaker=_pathmaker,
            overwrite=overwrite,
            include_arcname=include_arcname,
        )
        loaded = sum(self.mapping.load_archive(abspath(p))
                     for p in archive_paths)
        logger.info('loaded %d archive(s).', loaded)

        self.open_entries = {}

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

    def _mapping_open(self, key):
        idfe_fp = self.mapping.open(key)
        if not idfe_fp:
            # should this errno instead be transport error? io error?
            raise FuseOSError(ENOENT)
        return idfe_fp

    def open(self, path, flags):
        # TODO implement memory usage tracking by reusing cache.
        key = path[1:]
        logger.info('opening for %s', key)

        # the idfe is the stable identifier for this "version" of the
        # given path (id of fileentry), fp is the file pointer.
        idfe, fp = self._mapping_open(key)
        # initial position is 0
        pos = 0
        # add this to mapping, accompanied by the current position of 0
        # this is the open_entry and its id is the fh returned.
        open_entry = [fp, pos, idfe]
        # TODO ideally, the idfe is returned as the fh, but we need
        # additional tracking on all open handles.  Reference counting
        # should be use.
        fh = id(open_entry)
        self.open_entries[fh] = open_entry
        return fh

    def release(self, path, fh):
        fp, pos, idfe = self.open_entries.pop(fh, None)
        if fp:
            fp.close()

    def read(self, path, size, offset, fh):
        key = path[1:]
        logger.info(
            'reading data for %s (fh:%#x, size:%d, offset:%d)',
            key, fh, size, offset)
        open_entry = self.open_entries.get(fh)
        if not open_entry:
            raise FuseOSError(EIO)
        zf, pos, idfe = open_entry
        logger.debug(
            'open_entry: zf: %s, pos: %d, idfe: %s', zf, pos, idfe)
        seek = offset - pos
        if seek < 0:
            # have to reopen...
            logger.info('seek position is %d, need reopening', seek)
            new_idfe, zf = self._mapping_open(key)
            if idfe != new_idfe:
                # different file entry, ignoring by kiling this
                raise FuseOSError(EIO)
            # overwrite the open_entry's zipfile with the new one.
            open_entry[0] = zf
            # reset rest of the values
            seek = offset
            pos = 0
        junk = zf.read(seek)
        open_entry[1] = pos + size
        return zf.read(size)

    def readdir(self, path, fh):
        key = path[1:]
        return ['.', '..'] + self.mapping.readdir(key)

    def statfs(self, path):
        # TODO report total size of the zips?
        return dict(f_bsize=1024, f_blocks=1024, f_bavail=0)


class _SymlinkFUSE(LoggingMixIn, Operations):
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

    def rename(self, old, new):
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

        target = abspath(join(self.mount_root, self.base_path[1:], source))
        self.symlinks[symkey] = target
        # Warning: non-standard return value
        return target

    def unlink(self, path):
        symkey = basename(path)
        if symkey not in self.symlinks:
            raise FuseOSError(ENOTSUP)
        # Warning: non-standard return value
        return self.symlinks.pop(symkey)

    def statfs(self, path):
        return {'f_bsize': 0, 'f_blocks': 0, 'f_bavail': 0}


class SymlinkFUSE(_SymlinkFUSE):
    """
    Standardized implementation that traps the return values for methods
    that return non-standard values.
    """

    def symlink(self, path, source):
        super(SymlinkFUSE, self).symlink(path, source)

    def unlink(self, path):
        super(SymlinkFUSE, self).unlink(path)


class ManagedExplosiveFUSE(ExplosiveFUSE):
    """
    ExplosiveFS with a management path
    """

    def __init__(self, mount_root, management_node, *a, **kw):
        if '/' in management_node:
            raise ValueError('Management node must be a valid directory name')
        self.management_node = management_node
        base_path = '/' + management_node
        self.symlinkfs = _SymlinkFUSE(mount_root, base_path)
        super(ManagedExplosiveFUSE, self).__init__(*a, **kw)
        symlinks = self.symlinkfs.symlinks
        for n, k in enumerate(sorted(self.mapping.archives.keys())):
            fn = basename(k)
            fn = fn if fn not in symlinks else '%s_%d' % (basename(fn), n)
            symlinks[fn] = k

    def readdir(self, path, fh):
        result = super(ManagedExplosiveFUSE, self).readdir(path, fh)
        if path == '/' and self.management_node not in result:
            result.append(self.management_node)
        return result

    def __call__(self, op, path, *args):
        if path.startswith(self.symlinkfs.base_path):
            result = getattr(self.symlinkfs, op)(path, *args)

            if op == 'symlink':
                if result in self.mapping.archives:
                    # no support of multiple symlinks to the same target
                    self.symlinkfs.unlink(path)
                    raise FuseOSError(ENOTSUP)

                if not self.mapping.load_archive(result):
                    self.symlinkfs.unlink(path)
                    # Assume I/O error due to archive inaccessible.
                    raise FuseOSError(EIO)
                return None

            elif op == 'unlink':
                self.mapping.unload_archive(result)
                return None

            return result
        return super(ManagedExplosiveFUSE, self).__call__(op, path, *args)
