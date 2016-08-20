Changelog
=========

0.4 (2016-08-20)
----------------

- RAR archive format support added using the package ``unrar``.

0.3 (2015-12-12)
----------------

- Mappings now use absolute path to ensure this works in daemon mode.
- New layout strategy: codepage can be used to remap non-unicode name
  encodings to unicode.
- File ownership now shown as being owned by the user that started the
  mount process.
- Symlink management support added; this is enabled using the ``-m``
  flag, optionally with ``--manager-dir`` to explicitly change where
  that lies.  This allows loading and unloading of files via the adding
  and removing of symlinks in the management directory.
- Decreased memory consumption and performance from reads as inflate
  is called only on demand.  This however requires single-thread mode
  for the mean time.

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
