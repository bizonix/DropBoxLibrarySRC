#Embedded file name: dropbox/sync_engine_file_system/util.py
from __future__ import with_statement, absolute_import
import contextlib
import errno
import functools
import os
import sys
from dropbox.dirtraverse import Directory
from dropbox.low_functions import RuntimeMixin, add_inner_methods
from dropbox.misc import protect_closed
from dropbox.platform import platform
from dropbox.trace import unhandled_exc_handler
from .abstract_file_system import AbstractDirectory, AbstractFile
from .constants import SEEK_CUR, SEEK_END, SEEK_SET
from .exceptions import create_file_system_error
if platform == 'win':
    from pynt.headers.WinError import ERROR_FILENAME_EXCED_RANGE
else:
    ERROR_FILENAME_EXCED_RANGE = None

def convert_os_error():

    def handle_exc(e):
        if isinstance(e, EnvironmentError) and e.errno is not None:
            err = e.errno
            try:
                filename = e.filename
            except AttributeError:
                filename = None

            if ERROR_FILENAME_EXCED_RANGE is not None and getattr(e, 'winerror', None) == ERROR_FILENAME_EXCED_RANGE:
                err = errno.ENAMETOOLONG
            return create_file_system_error(err, filename=filename)
        else:
            return

    return convert_error(handle_exc)


def convert_os_error_dec(f):

    @functools.wraps(f)
    def wrapped(*n, **kw):
        with convert_os_error():
            return f(*n, **kw)

    return wrapped


def convert_errno_to_ioerror():

    def handle_exc(e):
        try:
            e.errno
        except AttributeError:
            return None

        return IOError(*e.args)

    return convert_error(handle_exc)


@contextlib.contextmanager
def convert_error(f):
    try:
        yield
    except Exception as e:
        exc = sys.exc_info()
        try:
            try:
                ret = f(e)
            except Exception:
                ret = e
                unhandled_exc_handler()
            else:
                if ret is None:
                    ret = e

            raise type(ret), ret, exc[2]
        finally:
            del exc


@add_inner_methods('readdir', 'reset', 'close')

class FileSystemDirectory(AbstractDirectory):

    @convert_os_error_dec
    def __init__(self, path, **kw):
        self.inner = Directory(path, **kw)


class IterableBasedDirectory(AbstractDirectory):

    def __init__(self, get_entries):
        self.get_entries = get_entries
        self.reset()

    def reset(self):
        self.curiter = iter(self.get_entries())

    def close(self):
        pass

    def readdir(self):
        try:
            return self.curiter.next()
        except StopIteration:
            return None


CAN_READ = {'r': True,
 'r+': True,
 'w': False,
 'w+': True,
 'a': False,
 'a+': True}
CAN_WRITE = {'r': False,
 'r+': True,
 'w': True,
 'w+': True,
 'a': True,
 'a+': True}
mode_map = {'r': os.O_RDONLY,
 'r+': os.O_RDWR,
 'w': os.O_WRONLY | os.O_TRUNC | os.O_CREAT,
 'w+': os.O_RDWR | os.O_TRUNC | os.O_CREAT,
 'a': os.O_WRONLY | os.O_APPEND | os.O_CREAT,
 'a+': os.O_RDWR | os.O_APPEND | os.O_CREAT}

def mode_string_to_flags(mode):
    return mode_map[mode]


class IndexingAttributes(object):

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def copy(self):
        return IndexingAttributes(**self.__dict__)

    def __repr__(self):
        return '<_IndexingAttributes %s>' % ','.join(('%s=%r' % (k, v) for k, v in self.__dict__.iteritems()))


class FunctionBasedFile(AbstractFile):

    def __init__(self, name, mode, read_function, write_function):
        self._name = name
        self.mode = mode
        self.read_all = read_function
        self.write_all = write_function
        self._closed = False
        self.offset = 0

    def close(self):
        self._closed = True

    @property
    def closed(self):
        return self._closed

    @property
    def name(self):
        return self._name

    @protect_closed
    def flush(self):
        pass

    @protect_closed
    def read(self, size = None):
        all_data = self.read_all()
        slice_ = slice(self.offset, None if size is None else self.offset + size)
        return all_data[slice_]

    @protect_closed
    def seek(self, offset, whence = 0):
        if whence == SEEK_CUR:
            self.offset += offset
        elif whence == SEEK_END:
            end = len(self.read_all())
            self.offset = end + offset
        elif whence == SEEK_SET:
            self.offset = offset
        else:
            raise IOError(errno.EINVAL, os.strerror(errno.EINVAL))

    @protect_closed
    def sync(self):
        pass

    @protect_closed
    def tell(self):
        return self.offset

    @protect_closed
    def truncate(self):
        all_data = self.read_all()
        all_data = all_data[:self.offset]
        all_data = all_data + '\x00' * (self.offset - len(all_data))
        self.write_all(all_data)

    @protect_closed
    def write(self, data):
        all_data = self.read_all()
        new_offset = self.offset + len(data)
        new_str = '%s%s%s' % (all_data[:self.offset], data, all_data[new_offset:])
        self.write_all(new_str)
        self.offset = new_offset


class WrappedFileSystem(RuntimeMixin):

    @property
    def fs(self):
        return self.inner
