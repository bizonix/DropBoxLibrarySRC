#Embedded file name: dropbox/dirtraverse_common.py
from __future__ import absolute_import
from dropbox.trace import unhandled_exc_handler
from dropbox.debugging import easy_repr

class DirectoryModifiedError(IOError):
    pass


class _DirectoryAbstract(object):

    def __iter__(self):
        return self

    def next(self):
        a = self.readdir()
        if not a:
            raise StopIteration
        return a

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        try:
            self.close()
        except Exception:
            unhandled_exc_handler()

    def __del__(self):
        try:
            self.close()
        except Exception:
            unhandled_exc_handler()


class DirectoryEntryFull(object):
    __slots__ = ('name', 'parent_path', '_size', 'mtime', 'type', 'inode', '_fullpath', '_stat', '_lstat', 'ctime')

    def __init__(self, parent_path, name, _type, size, mtime, inode = None, ctime = None):
        self.name = name
        self.type = _type
        self.parent_path = parent_path
        if size is not None:
            self._size = size
        self.mtime = mtime
        self.inode = inode
        self.ctime = ctime

    @property
    def size(self):
        try:
            return self._size
        except AttributeError:
            return self.lstat.st_size

    def __repr__(self):
        try:
            self._size
        except AttributeError:
            return easy_repr(self, 'name', 'type', 'mtime', 'inode', 'ctime')

        return easy_repr(self, 'name', 'type', '_size', 'mtime', 'inode', 'ctime')
