Changelog
=========

0.2 (2015-??-??)
----------------

- Removed specialized archive layout strategies, replaced it with a
  flag that controls whether the name of archive is to be prepended,
  being the ``-n`` flag.
- Internally, the pathmakers have been changed back again to taking only
  the single path parameter, and removed all zip* pathmakers.
- Implemented the overwrite flag (``-o``).

0.1 (2015-10-26)
----------------

- Initial release with just basic zip file support.
- File extraction is naive, such that the entire contents of a single
  given file entry will be extracted to memory per read.
