#Embedded file name: dropbox/linux_libc.py
from __future__ import absolute_import
from ctypes import CFUNCTYPE, POINTER, c_int, c_long, c_uint32, c_void_p, c_char_p
import ctypes.util
_libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
MAX_TRACE_LENGTH = 65536
sig_handler_t = CFUNCTYPE(c_int, c_int)
backtrace = _libc.backtrace
backtrace.restype = c_int
backtrace.argtypes = [c_void_p, c_int]
backtrace_symbols = _libc.backtrace_symbols
backtrace_symbols.restype = POINTER(c_char_p)
backtrace_symbols.argtypes = [c_void_p, c_int]
signal = _libc.signal
signal.restype = sig_handler_t
signal.argtypes = [c_int, sig_handler_t]
exit = _libc.exit
exit.argtypes = [c_int]
syscall = _libc.syscall
syscall.restype = c_int
syscall.argtypes = [c_int]
LOG_PID = 1
LOG_USER = 8
LOG_DAEMON = 24
openlog = _libc.openlog
openlog.argtypes = [c_char_p, c_int, c_int]
LOG_EMERG = 0
LOG_ALERT = 1
LOG_CRIT = 2
LOG_ERR = 3
LOG_WARNING = 4
LOG_NOTICE = 5
LOG_INFO = 6
LOG_DEBUG = 7
syslog = _libc.syslog
syslog.argtypes = [c_int, c_char_p, c_void_p]
import os

def errcheck(ret, func, args):
    if ret < 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    return ret


func_dict = {}
for name, restype, argtypes in (('inotify_init', c_int, ()), ('inotify_add_watch', c_int, (c_int, c_char_p, c_uint32)), ('inotify_rm_watch', c_int, (c_int, c_uint32))):
    the_func = CFUNCTYPE(c_int, use_errno=True, *argtypes)((name, _libc))
    func_dict[name] = the_func
    the_func.errcheck = errcheck

inotify_init = func_dict['inotify_init']
inotify_add_watch = func_dict['inotify_add_watch']
inotify_rm_watch = func_dict['inotify_rm_watch']

def errcheck_posix(ret, func, args):
    if ret != 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    return ret


try:
    try:
        posix_fadvise = CFUNCTYPE(c_int, use_errno=True, *[c_int,
         c_long,
         c_long,
         c_long])(('posix_fadvise', _libc))
    except:
        posix_fadvise = CFUNCTYPE(c_int, *[c_int,
         c_long,
         c_long,
         c_long])(('posix_fadvise', _libc))

    posix_fadvise.errcheck = errcheck_posix
except:

    def posix_fadvise(*n, **kw):
        raise Exception('Not implemented')


POSIX_FADV_SEQUENTIAL = 2
