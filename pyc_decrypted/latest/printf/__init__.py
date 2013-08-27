#Embedded file name: printf/__init__.py
from __future__ import absolute_import
from cffi import FFI
import os
__ffi__ = FFI()
__ffi__.cdef('\n   int printf(const char *format, ...);\n')
_libc = __ffi__.verify('\n#include <stdio.h>\n')

def printf(fmt, *args):
    ret = _libc.printf(fmt, *args)
    if ret == -1:
        raise OSError(ret, os.strerror(__ffi__.errno))
    return ret
