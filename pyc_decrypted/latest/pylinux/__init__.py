#Embedded file name: pylinux/__init__.py
from __future__ import absolute_import
from cffi import FFI
from dropbox.platform import platform
import os
import sys

def statvfs(path):
    if isinstance(path, unicode):
        path = path.encode(sys.getfilesystemencoding())
    if not isinstance(path, str):
        raise TypeError('path must be a string')
    buf = __ffi__.new('struct statvfs64 *')
    ret = _lib.statvfs64(path, buf)
    if ret == -1:
        raise OSError(ret, os.strerror(ret))
    return buf


def fstatvfs(fd):
    if not isinstance(fd, (int, long)):
        raise TypeError('fd must be a number')
    buf = __ffi__.new('struct statvfs64 *')
    ret = _lib.fstatvfs64(fd, buf)
    if ret == -1:
        raise OSError(ret, os.strerror(ret))
    return buf


def res_init():
    ret = _lib.res_init()
    if ret == -1:
        raise OSError(ret, os.strerror(__ffi__.errno))


if platform == 'linux':
    __ffi__ = FFI()
    __ffi__.cdef('\n       typedef uint64_t fsblkcnt_t;\n       typedef uint64_t fsfilcnt_t;\n       struct statvfs64 {\n           unsigned long  f_bsize;\n           unsigned long  f_frsize;\n           fsblkcnt_t     f_blocks;\n           fsblkcnt_t     f_bfree;\n           fsblkcnt_t     f_bavail;\n           fsfilcnt_t     f_files;\n           fsfilcnt_t     f_ffree;\n           fsfilcnt_t     f_favail;\n           unsigned long  f_fsid;\n           unsigned long  f_flag;\n           unsigned long  f_namemax;\n           ...;\n       };\n       int statvfs64(const char *path, struct statvfs64 *buf);\n       int fstatvfs64(int fd, struct statvfs64 *buf);\n\n       int res_init(void);\n    ')
    _lib = __ffi__.verify('\n    #include <sys/statvfs.h>\n    #include <resolv.h>\n    ')
