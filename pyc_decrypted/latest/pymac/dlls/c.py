#Embedded file name: pymac/dlls/c.py
from __future__ import absolute_import
import os
from ctypes import c_long, c_int, c_void_p, c_size_t, c_uint64, POINTER, c_char_p, c_uint, c_ulong
from ..types import FILE, ifaddrs, kern_return_t, mach_msg_type_number_t_p, mach_port_name_t, mach_port_name_t_p, mach_port_t, mach_timebase_info_t, sig_handler_t, struct_statfs, task_flavor_t, task_info_t, task_name_t, thread_flavor_t, thread_info_t, struct_attrlist
from ..lazydll import FakeDLL, LazyCDLL

def errno_check(ret, func, args):
    if ret < 0:
        e = libc.__error().contents.value
        raise OSError(e, os.strerror(e))
    return ret


class LibC(LazyCDLL):

    def __init__(self):
        super(LibC, self).__init__()
        self._dllname = u'c'

        def F(name, ret = None, args = [], when_not_found = None, errcheck = None):
            argtypes = []
            for arg in args:
                if isinstance(arg, tuple):
                    argtype, _ = arg
                else:
                    argtype = arg
                argtypes.append(argtype)

            self._func_defs[name] = {'restype': ret,
             'argtypes': argtypes}
            if when_not_found:
                self._func_defs[name]['when_not_found'] = when_not_found
            if errcheck:
                self._func_defs[name]['errcheck'] = errcheck

        self._func_defs = {'srandomdev': {'restype': None,
                        'argtypes': None},
         'random': {'restype': c_long,
                    'argtypes': None},
         'memcmp': {'restype': c_int,
                    'argtypes': [c_void_p, c_void_p, c_size_t]},
         'mach_timebase_info': {'restype': kern_return_t,
                                'argtypes': [mach_timebase_info_t]},
         'mach_absolute_time': {'restype': c_uint64,
                                'argtypes': []}}
        F('backtrace', c_int, [POINTER(c_void_p), c_int])
        F('backtrace_symbols', POINTER(c_char_p), [POINTER(c_void_p), c_int], when_not_found=self.return_none)
        F('fclose', c_int, [POINTER(FILE)])
        F('signal', sig_handler_t, [c_int, sig_handler_t])
        F('syscall', c_int, [c_int])
        F('openlog', None, [c_char_p, c_int, c_int])
        F('syslog', None, [c_int, c_char_p, c_void_p])
        F('mach_thread_self', mach_port_t)
        F('sched_yield')
        F('task_for_pid', kern_return_t, [mach_port_name_t, c_int, mach_port_name_t_p])
        F('task_info', kern_return_t, [task_name_t,
         task_flavor_t,
         task_info_t,
         mach_msg_type_number_t_p])
        F('mach_task_self', mach_port_t)
        F('mach_port_deallocate', kern_return_t, [mach_port_name_t, mach_port_name_t])
        F('thread_info', kern_return_t, [mach_port_t,
         thread_flavor_t,
         thread_info_t,
         mach_msg_type_number_t_p])
        F('__error', POINTER(c_int))
        F('sysctl', c_int, [POINTER(c_int),
         c_uint,
         c_void_p,
         POINTER(c_size_t),
         c_void_p,
         c_size_t], errcheck=errno_check)
        F('sysctlnametomib', c_int, [c_char_p, POINTER(c_int), POINTER(c_size_t)], errcheck=errno_check)
        F('statfs', c_int, [c_char_p, POINTER(struct_statfs)], errcheck=errno_check)
        F('sysctlbyname', c_int, [c_char_p,
         c_void_p,
         POINTER(c_size_t),
         c_void_p,
         c_size_t], errcheck=errno_check)
        F('getifaddrs', c_int, [POINTER(POINTER(ifaddrs))], errcheck=errno_check)
        F('freeifaddrs', None, [POINTER(ifaddrs)])
        F('getattrlist', c_int, [(c_char_p, 'path'),
         (POINTER(struct_attrlist), 'attrList'),
         (c_void_p, 'attrBuf'),
         (c_size_t, 'attrBufSize'),
         (c_ulong, 'options')], errcheck=errno_check)
        F('fgetattrlist', c_int, [(c_int, 'fd'),
         (POINTER(struct_attrlist), 'attrList'),
         (c_void_p, 'attrBuf'),
         (c_size_t, 'attrBufSize'),
         (c_ulong, 'options')], errcheck=errno_check)
        F('exchangedata', c_int, [(c_char_p, 'path1'), (c_char_p, 'path2'), (c_uint, 'options')], errcheck=errno_check)


libc = FakeDLL(LibC)
