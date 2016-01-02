LIBUNRAR_MISSING = False

try:
    from unrar.rarfile import RarFile as _RarFile
    from unrar.rarfile import BadRarFile
    UNRAR_SUPPORT = True
except ImportError:  # pragma: no cover
    UNRAR_SUPPORT = False
except (LookupError, OSError):  # pragma: no cover
    UNRAR_SUPPORT = False
    LIBUNRAR_MISSING = True


from .exception import UnsupportedArchiveFile


class FakeRarFile(object):

    def __init__(self, *a, **kw):
        if LIBUNRAR_MISSING:
            raise UnsupportedArchiveFile(
                "unrar failed to find UnRAR library on your system; "
                "refer to https://pypi.python.org/pypi/unrar/ or your "
                "system's package manager."
            )
        else:
            raise UnsupportedArchiveFile(
                "unrar package not installed; "
                "install with 'pip install unrar'."
            )


if UNRAR_SUPPORT:
    # There are a few things that the RarFile class as implemented (as
    # of unrar-0.3), doesn't quite match up with zipfile implementation,
    # so some modifications are done to its subclass.

    class RarFile(_RarFile):

        def infolist(self):
            """
            Custom infolist implementation that appends a forward slash to
            directory entries.
            """

            results = super(RarFile, self).infolist()
            for r in results:
                if r.flag_bits == 32 and not r.filename.endswith('/'):
                    # If this line is not hit in coverage, it means this
                    # override is no longer needed.
                    r.filename += '/'
            return results

    # This is done separately to not override future implementations
    # that may include this.

    if not hasattr(RarFile, 'close'):
        # Again, if these lines are not hit in coverage, it means
        # ``RarFile`` has implemented this.
        def close(self):
            pass

        RarFile.close = close

else:  # pragma: no cover
    RarFile = FakeRarFile

    class BadRarFile(Exception):
        """
        Dummy implementation for import consistency.
        """
