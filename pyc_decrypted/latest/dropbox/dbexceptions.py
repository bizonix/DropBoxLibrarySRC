#Embedded file name: dropbox/dbexceptions.py
from __future__ import absolute_import
import errno

class TagFolderError(Exception):

    def __init__(self, parent_e):
        self.parent_e = parent_e

    def __str__(self):
        return 'TagFolderError(%r)' % (self.parent_e,)

    def __repr__(self):
        return str(self)


class TimeoutError(Exception):
    pass


class EOFError(Exception):
    pass


class InterruptError(Exception):
    pass


class LowDiskSpaceError(IOError):

    def __init__(self, free_space, min_space):
        IOError.__init__(self, (errno.ENOSPC, 'Available space %.2fMB < %.2fMB requested' % (free_space / 1048576.0, min_space / 1048576.0)))


class RequestDataOversizeError(Exception):

    def __init__(self, size, max_size, item_count):
        self.size = size
        self.max_size = max_size
        self.item_count = item_count
