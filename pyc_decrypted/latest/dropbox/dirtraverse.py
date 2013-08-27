#Embedded file name: dropbox/dirtraverse.py
from __future__ import absolute_import
import errno
import functools
import itertools
import os
import sys
import ctypes
import ctypes.util
from dropbox.sync_engine_file_system.constants import FILE_TYPE_POSIX_SYMLINK
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.debugging import easy_repr, ReprStructure
from dropbox.dirtraverse_common import _DirectoryAbstract, DirectoryModifiedError
_is_mac = sys.platform.startswith('darwin')
_is_linux = sys.platform.startswith('linux')
_is_win = sys.platform.startswith('win')
try:
    if _is_win:
        from dropbox import dirtraverse_win32 as _module
    elif _is_mac:
        from dropbox import dirtraverse_mac as _module
    elif _is_linux:
        from dropbox import dirtraverse_posix as _module
    else:
        raise Exception('System not supported!')
    Directory = _module.Directory
except Exception:

    class _DirectoryEntry(object):
        __slots__ = ('name',)

        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return easy_repr(self, 'name')


    class Directory(_DirectoryAbstract):
        __slots__ = ('ents', 'idx', 'path')

        def __init__(self, path, **kw):
            self.path = path
            self.ents = os.listdir(path)
            for i in xrange(len(self.ents)):
                self.ents[i] = _DirectoryEntry(self.ents[i])

            self.idx = 0

        def close(self):
            pass

        def reset(self):
            self.__init__(self.path)

        def readdir(self):
            try:
                toret = self.ents[self.idx]
            except IndexError:
                return None

            self.idx += 1
            return toret
