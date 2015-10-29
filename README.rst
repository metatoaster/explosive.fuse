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

.. _FUSE: http://fuse.sourceforge.net/

Currently, only ``zip`` archives are supported, with plans to support at
least ``rar``.

.. image:: https://travis-ci.org/metatoaster/explosive.fuse.svg?branch=master
    :target: https://travis-ci.org/metatoaster/explosive.fuse
.. image:: https://coveralls.io/repos/metatoaster/explosive.fuse/badge.svg?branch=master
   :target: https://coveralls.io/r/metatoaster/explosive.fuse?branch=master


Installation
============

If all system level dependencies are satisified, the installation
process is simply a single ``pip`` call, like so::

    $ pip install explosive.fuse

This can be done either at the system level (i.e. using ``sudo``) to
make this available for all users on the system, or inside a virtualenv
for just a single user.

System level dependencies
-------------------------

ExplosiveFUSE requires the FUSE kernel module for your operating system
and its userspace tools be available, and Python 2.7/3.3+/PyPy.

First off, install the FUSE kernel module and userspace tools if they
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

    usage: explode [-h] [-l <strategy>] [--layout-info] [-f] [-d]
                   dir archives [archives ...]

In the most simple form the command can simply be invoked like so::

    $ mkdir /tmp/mnt
    $ explode /tmp/mnt demo1.zip

This will mount the contents of ``demo1.zip`` to ``/tmp/mnt``.  To
verify that this worked, a simple ``ls`` can be used::

    $ ls -l /tmp/mnt/
    total 0
    -r--r--r-- 1 root root 33 Oct 26 23:19 file1
    -r--r--r-- 1 root root 33 Oct 26 23:19 file2
    -r--r--r-- 1 root root 33 Oct 26 23:19 file3
    -r--r--r-- 1 root root 33 Oct 26 23:19 file4
    -r--r--r-- 1 root root 33 Oct 26 23:19 file5
    -r--r--r-- 1 root root 33 Oct 26 23:19 file6

Currently, all files will simply be presented as owned by root and is
read-only by all users.  If you wish to restrict this simply ensure the
directory before is only accessible to the desired users.

To unmount, simply call::

    $ fusermount -u /tmp/mnt/

Or terminate the process if it was ran in the foreground.

It is possible to explode multiple archives onto the target directory::

    $ explode /tmp/mnt demo1.zip demo2.zip

By default, a new layout strategy will be used, which will include the
name of the source archive file.  This can be verified::

    $ ls -l /tmp/mnt/
    total 0
    dr-xr-xr-x 2 root root 0 Oct 26 23:22 demo1.zip
    dr-xr-xr-x 2 root root 0 Oct 26 23:22 demo2.zip

Naturally, this can be changed by specifying the layout strategy with
the ``-l`` or the ``--layout`` flag.  For a detailed list please refer
to the listing generated by ``explode --layout-info``, but for
completeness sake this is what is provided by a default installation:

flatten
    Flattens the directory structure to the root by replacing all path
    separators for each file entries with the ``_`` character.

junk
    Junk all paths, keep only the basename of file entries.

root
    Present file entries to the root of the mount point.

ziproot
    Present file entries inside a directory named after its source
    archive file.

ziproot_flatten
    Combining ziproot and flatten. Flattens the directory structure to
    the root by replacing all path separators for each file entries with
    the ``_`` character, with all file names prepended with its source
    archive file name.


Troubleshooting
===============

Mounting shows the following error message::

    fusermount: failed to open /etc/fuse.conf: Permission denied

This can be safely ignored, or alternatively have your system's
adminstrator grant you read access to that file by putting your account
into the ``fuse`` user group or equivalent on your system, or change the
permission to that file to world readable, as that file does not contain
any sensitive information under typical usage.

If you encountered any other problems using this software please file an
issue using the `issue tracker`_ for this project.

.. _issue tracker: https://github.com/metatoaster/explosive.fuse/issues


License
=======

This work is licensed under `GNU Generic Public License, version 3`_.

.. _GNU Generic Public License, version 3:
    http://opensource.org/licenses/gpl-3.0.html
