Changelog
=========

Unreleased
----------

- Mappings now use absolute path to ensure this works in daemon mode.

0.2 (2015-10-31)
----------------

- Removed specialized archive layout strategies (i.e. the zip* ones)
- By default, basename of archive will be prepended to the path for each
  file entries.  This behavior can directly be disabled using the
  ``--omit-arcname`` flag.  (Naturally, a layout strategy can still
  modify that path, like ``junk``.
- All pathmaker callables are now actually factories that produce the
  actual pathmaker.  They can now take arguments to influence how the
  produced pathmaker behaves.  The arguments can be entered using the
  extended ``-l`` or ``--layout`` syntax.  Details documented in
  ``--layout-info``.
- Implemented the ``--overwrite`` flag, allowing newer entries to
  "overwrite" existing ones.
- A number of other internal API changes.

0.1 (2015-10-26)
----------------

- Initial release with just basic zip file support.
- File extraction is naive, such that the entire contents of a single
  given file entry will be extracted to memory per read.
