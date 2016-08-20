Introduction
============

This package, ``explosive.fuse``, provides a command-line tool,
``explode``, for mounting of archive files (such as zip) to a directory
using `FUSE`_, enabling access to individual file entries within the
compressed archives as normal files directly without the typical
intermediate step of decompression to some temporary location, i.e. all
file decompression is done dynamically, on demand.  This library is
constructed with modularity in mind to enable customization, such as how
the file entries within the archives are to be presented at the mounted
location, and that the helper classes and functions within can be reused
elsewhere.

.. _FUSE: https://github.com/libfuse/libfuse

Currently, the following archive formats are supported:

- zip (builtin package ``zipfile``)
- rar (require third-party package |unrar|_)

.. |unrar| replace:: ``unrar``
.. _unrar: https://pypi.python.org/pypi/unrar/

Archive formats that require third-party packages are not enabled by
default.  To enable, please install the packages as specified, and more
information about them can be accessed via the links provided above.

.. image:: https://travis-ci.org/metatoaster/explosive.fuse.svg?branch=master
    :target: https://travis-ci.org/metatoaster/explosive.fuse
.. image:: https://coveralls.io/repos/metatoaster/explosive.fuse/badge.svg?branch=master
   :target: https://coveralls.io/r/metatoaster/explosive.fuse?branch=master


Installation
============

If all system level dependencies are satisfied, the installation
process is simply a single ``pip`` call, like so::

    $ pip install explosive.fuse

This can be done either at the system level (i.e. using ``sudo``) to
make this available for all users on the system, or inside a virtualenv
for just a single user.

System level dependencies
-------------------------

ExplosiveFUSE requires the FUSE kernel module for your operating system
and its user space tools be available, and Python 2.7/3.3+/PyPy.

First off, install the FUSE kernel module and user space tools if they
are not already installed.

Linux
~~~~~

Arch Linux::

    $ sudo pacman -S fuse

Debian/Ubuntu::

    $ sudo apt-get install fuse

Gentoo (also, please refer to its `wiki entry on FUSE`_)::

    $ sudo emerge --ask sys-fs/fuse

.. _wiki entry on FUSE: https://wiki.gentoo.org/wiki/Filesystem_in_Userspace

RedHat/CentOS/Fedora::

    $ sudo yum install fuse

OS X
~~~~

This has been somewhat tested through the experimental build features
provided by Travis-CI, with dependencies installed via `Homebrew`_.
For installation of Homebrew, please refer to instructions outlined at
http://brew.sh/.

Once that's done, the packages for `FUSE for OS X`_ and `pyenv`_ (which
provides Python version management) can be installed using the following
commands::

    $ brew update
    $ brew install osxfuse
    $ brew install pyenv
    $ pyenv install 3.5.0  # or your desired version of Python
    $ pyenv global 3.5.0
    $ pyenv rehash

.. _Homebrew: http://brew.sh
.. _pyenv: https://github.com/yyuu/pyenv
.. _FUSE for OS X: https://osxfuse.github.io/

Other installation methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

This may be installed into the default user specific library directory 
(typically ``~/.local``) using the following command::

    $ pip install --user explosive.fuse

The executable will then be available at ``~/.local/bin/explode``.

Or be installed in a virtualenv, too::

    $ virtualenv ~/.venv
    $ source ~/.venv/bin/activate
    $ pip install explosive.fuse

Naturally, installation from source can be done, and provided ``git`` is
installed, the latest development version can be done like so::

    $ pip install git+https://github.com/metatoaster/explosive.fuse#egg=explosive.fuse

Alternatively, manual usage of ``git`` and ``python setup.py develop``
will work also.

Usage
=====

Simply invoking ``explode`` from the shell this help message will be
presented::

    usage: explode [-h] [-l <strategy>] [--layout-info] [-d] [-f] [-m]
                   [--manager-dir [MANAGER_DIR]] [--overwrite] [--omit-arcname]
                   [-V]
                   dir archives [archives ...]

In the most simple form the command can simply be invoked like so::

    $ mkdir /tmp/mnt
    $ explode /tmp/mnt demo1.zip

This will mount the contents of ``demo1.zip`` to ``/tmp/mnt``.  To
verify that this worked, a simple ``ls`` can be used::

    $ ls -l /tmp/mnt/
    total 0
    -r--r--r-- 1 user user 33 Oct 26 23:19 file1
    -r--r--r-- 1 user user 33 Oct 26 23:19 file2
    -r--r--r-- 1 user user 33 Oct 26 23:19 file3
    -r--r--r-- 1 user user 33 Oct 26 23:19 file4
    -r--r--r-- 1 user user 33 Oct 26 23:19 file5
    -r--r--r-- 1 user user 33 Oct 26 23:19 file6

Files are presented as being owned by the user that created this mount
point.  For specifics on access permissions, please consult the fuse
user manual (i.e. ``man fuse``).

To unmount, simply call::

    $ fusermount -u /tmp/mnt/

Or terminate the process if it was ran in the foreground.

It is possible to explode multiple archives onto the target directory::

    $ explode /tmp/mnt demo1.zip demo2.zip

By default, a new layout strategy will be used, which will include the
name of the source archive file.  This can be verified::

    $ ls -l /tmp/mnt/
    total 0
    dr-xr-xr-x 2 user user 0 Oct 26 23:22 demo1.zip
    dr-xr-xr-x 2 user user 0 Oct 26 23:22 demo2.zip

Layout Strategies
-----------------

The way the file entries are laid out in the resulting filesystem can be
modified by the use of a layout strategy.  This is specified using the
``-l`` or the ``--layout`` flag.  Naturally, the final result is also
influenced by the usage of the ``--overwrite`` and the
``--omit-arcname`` flags and the arguments associated with each of the
strategies (which are specified by appending ``:``, followed by the
value of each positional argument(s)).  Detailed information on every
available strategies are available by calling ``explode --layout-info``,
but for completeness sake the following strategies are provided by a
default installation:

codepage
    Decode the filename entries into unicode from the specified
    codepage.  Example: ``-l codepage:shift_jis`` will decode filenames
    that look like ``é▒é±é╔é┐é═`` into ``こんにちは``.

default
    Present file entries as they were within their respective directory
    structures to the root of its source archive.

flatten
    Flattens the directory structure to the root of the mount point by
    replacing all path separators for each file entries with the ``_``
    character by default. This character can be specified by using the
    argument syntax (e.g. use ``-l flatten:-`` will replace all path
    separators with the ``-`` character.)

junk
    Junk paths, keep only directories counting from root up to the level
    specified for a positive keep number, otherwise junking all but the
    absolute number of keep levels previous to the basename of the
    filename for a negative keep number. Default is to keep no
    directories. Useful value is ``1`` if it is desirable to keep the
    source archive name as a container directory (i.e. ``-l junk:1``) if
    ``--omit-arcname`` is not used.

An important note: by default, the basename of the archive file will be
prepended to each of its file entries before being filtered through the
layout strategy, unless the ``--omit-arcname`` flag is used.

Flags for fine-tuning filesystem behavior
-----------------------------------------

``--debug``
    Print debug messages to stdout.

``--foreground``
    Run in foreground.

``-m, --manager``
    Enable the symlink manager directory.  This option exposes all the
    archive files under the management directory (defined by the
    ``--manager-dir`` flag, default is ``.manager`` under the root of
    the mount point) as symlinks.  Creating symlinks to valid archive
    files will add the file entries in them to the filesystem, and
    removing the symlinks will remove its associated entries from the
    filesystem.

``--omit-arcname``
    Sometimes it may be desirable to omit the name of the source archive
    files from the generated paths.

    For example, if we have multiple archive files with names
    ``SNS_001.zip`` up to ``SNS_100.zip``, and inside there we simply
    have files like ``01.jpg`` up to ``20.jpg`` lying at the root level,
    activating the ``--omit-arcname`` flag flag will result in only 20
    files from ``SNS_001.zip`` archive being accessible as by default as
    that was the first file specified to be loaded.

``--overwrite``
    Useful when there are multiple file entries of the same name from
    multiple archives and only the latest one is desired, this flag will
    "overwrite" any existing entries the mapping process may encounter.


Troubleshooting
===============

Error messages
--------------

Mounting shows the following error message::

    fusermount: failed to open /etc/fuse.conf: Permission denied

This can be safely ignored, or alternatively have your system's
administrator grant you read access to that file by putting your account
into the ``fuse`` user group or equivalent on your system, or change the
permission to that file to world readable, as that file does not contain
any sensitive information under typical usage.

Other issues
------------

If you encountered any other problems using this software please file an
issue using the `issue tracker`_ for this project.

.. _issue tracker: https://github.com/metatoaster/explosive.fuse/issues


License
=======

This work is licensed under `GNU Generic Public License, version 3`_.

.. _GNU Generic Public License, version 3:
    http://opensource.org/licenses/gpl-3.0.html
