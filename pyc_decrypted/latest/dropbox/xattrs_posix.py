#Embedded file name: dropbox/xattrs_posix.py
from __future__ import with_statement, absolute_import
import ctypes.util
import errno
import os
import sys
from ctypes import c_int, c_uint32, c_void_p, c_char_p, c_size_t, c_ssize_t, create_string_buffer, CFUNCTYPE
from dropbox.trace import TRACE, report_bad_assumption
if sys.version_info[0] >= 3:

    def _fs_to_unicode(name):
        return name.decode(sys.getfilesystemencoding(), 'surrogateescape')


    def _unicode_to_fs(name):
        return name.encode(sys.getfilesystemencoding(), 'surrogateescape')


else:

    def _fs_to_unicode(name):
        if isinstance(name, unicode):
            return name
        try:
            return name.decode(sys.getfilesystemencoding())
        except UnicodeDecodeError:
            return name


    def _unicode_to_fs(name):
        if isinstance(name, unicode):
            return name.encode(sys.getfilesystemencoding())
        else:
            return name


_libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

def _errcheck(ret, func, args):
    if ret < 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    return ret


if sys.platform.startswith('linux'):
    c_calls = {'fgetxattr': (c_ssize_t, [c_int,
                    c_char_p,
                    c_void_p,
                    c_size_t]),
     'fsetxattr': (c_int, [c_int,
                    c_char_p,
                    c_void_p,
                    c_size_t,
                    c_int]),
     'flistxattr': (c_ssize_t, [c_int, c_char_p, c_size_t]),
     'fremovexattr': (c_int, [c_int, c_char_p])}
    errno.ENOATTR = errno.ENODATA
    ENOATTR_LIST = (errno.ENOATTR,)
    XATTR_CREATE = 1
    XATTR_REPLACE = 2
elif sys.platform.startswith('darwin'):
    c_calls = {'fgetxattr': (c_ssize_t, [c_int,
                    c_char_p,
                    c_void_p,
                    c_size_t,
                    c_uint32,
                    c_int]),
     'fsetxattr': (c_int, [c_int,
                    c_char_p,
                    c_void_p,
                    c_size_t,
                    c_uint32,
                    c_int]),
     'flistxattr': (c_ssize_t, [c_int,
                     c_char_p,
                     c_size_t,
                     c_int]),
     'fremovexattr': (c_int, [c_int, c_char_p, c_int])}
    errno.ENOATTR = 93
    ENOATTR_LIST = (errno.ENOATTR, errno.EINVAL, errno.EPERM)
    XATTR_CREATE = 2
    XATTR_REPLACE = 4
else:
    raise Exception('Xattrs not supported on this platform!')
_func_types = {}
for name, (restype, argtypes) in c_calls.iteritems():
    _func_types[name] = CFUNCTYPE(restype, use_errno=True, *argtypes)((name, _libc))
    _func_types[name].errcheck = _errcheck

c_fgetxattr = _func_types['fgetxattr']
c_fsetxattr = _func_types['fsetxattr']
c_flistxattr = _func_types['flistxattr']
c_fremovexattr = _func_types['fremovexattr']
if sys.platform.startswith('linux'):

    def fsetxattr(fd, name, buf, options):
        name = _unicode_to_fs(name)
        return c_fsetxattr(fd, name, buf, len(buf), options)


    def fremovexattr(fd, name):
        name = _unicode_to_fs(name)
        return c_fremovexattr(fd, name)


else:

    def fsetxattr(fd, name, buf, options):
        name = _unicode_to_fs(name)
        return c_fsetxattr(fd, name, buf, len(buf), 0, options)


    def fremovexattr(fd, name):
        name = _unicode_to_fs(name)
        return c_fremovexattr(fd, name, 0)


def fgetxattr(fd, name):
    name = _unicode_to_fs(name)
    for retry_count, retries_left in enumerate(xrange(100, -1, -1)):
        size = c_fgetxattr(fd, name, None, 0, 0, 0)
        p = create_string_buffer(size)
        try:
            size = c_fgetxattr(fd, name, p, size, 0, 0)
        except OSError as e:
            if e.errno == errno.ERANGE and retries_left > 0:
                if retry_count == 3:
                    report_bad_assumption('xattr value grew multiple times (ERANGE): fd=%r, name=%r', fd, name)
                elif retry_count > 3:
                    TRACE('!! Still retrying fgetxattr(fd=%r, name=%r) (retry_count=%r, retries_left=%r)', fd, name, retry_count, retries_left)
            else:
                raise
        else:
            return p.raw[:size]


def flistxattrb(fd):
    for retry_count, retries_left in enumerate(xrange(100, -1, -1), 1):
        try:
            size = c_flistxattr(fd, None, 0, 0)
        except OSError as e:
            if e.errno in ENOATTR_LIST:
                return []
            raise

        p = create_string_buffer(size)
        try:
            size = c_flistxattr(fd, p, size, 0)
        except OSError as e:
            if e.errno in ENOATTR_LIST:
                return []
            if e.errno == errno.ERANGE and retries_left > 0:
                if retry_count == 3:
                    report_bad_assumption('xattr list grew multiple times (ERANGE): fd=%r', fd)
                elif retry_count > 3:
                    TRACE('!! Still retrying flistxattr(fd=%r) (retry_count=%r, retries_left=%r)', fd, retry_count, retries_left)
            else:
                raise
        else:
            return p.raw[:size].split('\x00')[:-1]


def flistxattru(fd):
    return list((_fs_to_unicode(name) for name in flistxattrb(fd)))


if sys.version_info[0] >= 3:
    flistxattr = flistxattru
else:
    flistxattr = flistxattrb
