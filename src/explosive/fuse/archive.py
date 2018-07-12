import os.path

from zipfile import ZipFile
try:
    from zipfile import BadZipFile
    FileNotFoundError = FileNotFoundError  # pragma: no cover
except ImportError:  # pragma: no cover
    # Assume python 2
    from zipfile import BadZipfile as BadZipFile
    FileNotFoundError = IOError  # This is raised by zipfile.

from ._rarfile import RarFile
from ._rarfile import BadRarFile

from .exception import BadArchiveFile
from .exception import UnsupportedArchiveFile


# Lookup table for archive filename extension to its respective class.
_archive_lookup = {
    'zip': ZipFile,
    'rar': RarFile,
}


class ArchiveFile(object):
    """
    Generic archive file implementation.
    """

    def __init__(self, archive_filename):
        archive_type = archive_filename.rsplit('.', 1)[-1]
        archive_class = _archive_lookup.get(archive_type)
        if archive_class is None:
            # attempt zip fallback, because out of the archive formats
            # currently supported it is the most popular one used by
            # various file formats that bundle stuff together (such as
            # .odt or .docx).
            try:
                self.archive_file = ZipFile(archive_filename)
            except Exception:
                raise UnsupportedArchiveFile('unsupported archive format.')
            else:
                return

        try:
            self.archive_file = archive_class(archive_filename)
        except BadZipFile:
            raise BadArchiveFile()
        except BadRarFile:
            # this can be raised if file wasn't found, check first.
            if not os.path.exists(archive_filename):
                raise FileNotFoundError
            else:  # pragma: no cover
                # it's really a bad archive.
                raise BadArchiveFile()
        except FileNotFoundError:  # pragma: no cover
            raise
        except Exception:  # pragma: no cover
            raise

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.archive_file.close()

    def infolist(self):
        return self.archive_file.infolist()

    def open(self, *a, **kw):
        return self.archive_file.open(*a, **kw)
