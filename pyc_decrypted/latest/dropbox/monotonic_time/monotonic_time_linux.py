#Embedded file name: dropbox/monotonic_time/monotonic_time_linux.py
from __future__ import absolute_import
import ctypes
import ctypes.util
import functools
import platform
from ctypes import POINTER, byref, c_int, c_long, CFUNCTYPE, sizeof
from dropbox.trace import unhandled_exc_handler, report_bad_assumption
_rt = None
clock_gettime = None
clockid_t = c_long
CLOCK_REALTIME = 0
CLOCK_MONOTONIC = 1
__NR_clock_gettime = 228 if sizeof(c_long) == 8 else 265

class timespec(ctypes.Structure):
    _fields_ = [('tv_sec', c_long), ('tv_nsec', c_long)]

    def __repr__(self):
        return 'timespec(tv_sec=%d, tv_nsec=%d)' % (self.tv_sec, self.tv_nsec)

    def __float__(self):
        return self.tv_sec + float(self.tv_nsec) / 1000000000.0


def lazy_load_time_bindings():
    global clock_gettime
    global _rt
    if _rt:
        return
    try:
        if platform.machine() not in ('x86_64', 'i686', 'i386'):
            report_bad_assumption('This machine is not supported! %r' % platform.machine())
        rt = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
        clock_gettime = functools.partial(CFUNCTYPE(c_int, c_int, clockid_t, POINTER(timespec))(('syscall', rt)), __NR_clock_gettime)
        _rt = rt
    except Exception:
        unhandled_exc_handler()


def get_monotonic_time():
    lazy_load_time_bindings()
    try:
        ts = timespec()
        clock_gettime(CLOCK_MONOTONIC, byref(ts))
        return float(ts)
    except Exception:
        unhandled_exc_handler()
        return 0


def get_monotonic_frequency():
    return 1.0
