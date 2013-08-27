#Embedded file name: dropbox/misc.py
from __future__ import absolute_import
import functools
import operator
import os

def len_list_of_strings(st):
    return reduce(operator.add, st, 0)


def protect_closed(f):

    @functools.wraps(f)
    def wrapped(self, *n, **kw):
        if self.closed:
            raise ValueError('I/O operation on closed file')
        return f(self, *n, **kw)

    return wrapped


READ_SIZE = 4096

class LineReaderMixin(object):

    def __iter__(self):
        return self

    def __next__(self):
        raise self.next()

    def readline(self, size = None):
        if size is not None:
            raise NotImplementedError('size argument is not supported')
        bufs = []
        while True:
            data = self.read(READ_SIZE)
            if not data:
                return ''.join(bufs)
            npos = data.find('\n')
            if npos == -1:
                bufs.append(data)
            else:
                bufs.append(data[:npos + 1])
                line = ''.join(bufs)
                self.seek(npos + 1 - len(data), os.SEEK_CUR)
                return line

    def next(self):
        ret = self.readline()
        if not ret:
            raise StopIteration()
        return ret

    def readlines(self, sizehint = None):
        return list(self)
