#Embedded file name: dropbox/sync_engine_file_system/exceptions.py
import errno
import functools
import operator
import os
import re
from dropbox.dirtraverse import DirectoryModifiedError

class InvalidPathError(Exception):
    pass


class BadPathComponentError(InvalidPathError):
    pass


class AttrsModifiedError(IOError):
    pass


assert issubclass(DirectoryModifiedError, IOError), 'DirectoryModifiedError should be a subclass of IOError'

class FileSystemError(OSError):
    errnomap = {}

    def __new__(cls, *n):
        if cls == FileSystemError:
            subclass = FileSystemError.errnomap.get(n[0])
        else:
            subclass = None
        if subclass is None:
            return super(FileSystemError, cls).__new__(cls, *n)
        else:
            return subclass(*n)

    def __init__(self, *n):
        if len(n) == 3 and n[2] is None:
            n = n[:2]
        super(FileSystemError, self).__init__(*n)


def create_file_system_error(errno, message = None, filename = None):
    if message is None:
        message = os.strerror(errno)
    return FileSystemError(errno, message, filename)


def create_io_error(errno, message = None, filename = None):
    if message is None:
        message = os.strerror(errno)
    if filename is None:
        n = ()
    else:
        n = (filename,)
    return IOError(errno, message, *n)


def _upper_case_to_underscored(name):
    matches = re.findall('[A-Z][^A-Z]*', name)
    return '_'.join(map(operator.methodcaller('lower'), matches))


for name, errno_ in [('FileNotFoundError', errno.ENOENT),
 ('FileExistsError', errno.EEXIST),
 ('NotADirectoryError', errno.ENOTDIR),
 ('DirectoryNotEmptyError', errno.ENOTEMPTY),
 ('IsADirectoryError', errno.EISDIR),
 ('PermissionDeniedError', errno.EACCES)]:
    _Error = type(name, (FileSystemError,), {})
    FileSystemError.errnomap[errno_] = _Error
    globals()[name] = _Error
    globals()['create_' + _upper_case_to_underscored(name)] = functools.partial(create_file_system_error, errno_)
