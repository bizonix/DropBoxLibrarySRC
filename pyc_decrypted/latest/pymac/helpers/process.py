#Embedded file name: pymac/helpers/process.py
from __future__ import absolute_import
import os
import functools
from ctypes import c_int, c_size_t, create_string_buffer, byref, addressof, c_uint32, sizeof, c_uint, string_at
from ..constants import CTL_KERN, KERN_ARGMAX, KERN_PROC, KERN_PROC_ALL, KERN_PROC_PID, KERN_PROCARGS2, CPU_TYPE_X86, CPU_TYPE_X86_64, CPU_TYPE_POWERPC, CTL_MAXNAME
from ..dlls import libc
from ..types import timeval
_sysctl_boottime = None
_sysctl_model = 0

def is_pid_in_64bit_mode(pid):
    mib = (c_int * 4)()
    mib[0] = CTL_KERN
    mib[1] = KERN_PROC
    mib[2] = KERN_PROC_PID
    mib[3] = pid
    ENTRY_SIZE = 492
    FLAGS_OFFSET = 16
    buf_size = c_size_t(ENTRY_SIZE)
    kprocbuf = create_string_buffer(buf_size.value)
    libc.sysctl(mib, 4, kprocbuf, byref(buf_size), None, 0)
    if buf_size.value != ENTRY_SIZE:
        raise Exception('Size mismatch %d vs %d', buf_size.value, ENTRY_SIZE)
    buf_address = addressof(kprocbuf)
    flags = c_uint32.from_address(buf_address + FLAGS_OFFSET).value
    P_LP64 = 4
    return flags & P_LP64


def get_process_arch(pid):
    mib = sysctlnametomib('sysctl.proc_cputype')
    if not mib:
        return
    archs = {CPU_TYPE_X86: 'i386',
     CPU_TYPE_X86_64: 'x86_64',
     CPU_TYPE_POWERPC: 'ppc'}
    mib.append(pid)
    c_mib = (c_int * len(mib))()
    for i, v in enumerate(mib):
        c_mib[i] = v

    cputype = c_int()
    buf_size = c_size_t(sizeof(cputype))
    libc.sysctl(c_mib, len(mib), byref(cputype), byref(buf_size), None, 0)
    try:
        return archs[cputype.value]
    except KeyError:
        return


def get_model_identifier():
    global _sysctl_model
    if _sysctl_model != 0:
        return _sysctl_model
    size = c_size_t(0)
    name = 'hw.model'
    try:
        libc.sysctlbyname(name, None, byref(size), None, 0)
        _buffer = create_string_buffer(size.value)
        libc.sysctlbyname(name, _buffer, byref(size), None, 0)
        _sysctl_model = _buffer.value
    except OSError:
        _sysctl_model = None

    return _sysctl_model


def sysctlnametomib(name):
    c_mib = (c_int * CTL_MAXNAME)()
    l = c_size_t(CTL_MAXNAME)
    try:
        libc.sysctlnametomib(name, c_mib, byref(l))
    except OSError:
        return None

    return c_mib[:l.value]


def get_boottime():
    global _sysctl_boottime
    if _sysctl_boottime is None:
        c_mib = (c_int * CTL_MAXNAME)()
        l = c_size_t(CTL_MAXNAME)
        try:
            libc.sysctlnametomib('kern.boottime', c_mib, byref(l))
        except OSError:
            c_mib[0] = 1
            c_mib[1] = 21
            l = c_size_t(2)

        _sysctl_boottime = functools.partial(libc.sysctl, c_mib, l)
    boottime = timeval()
    buf_size = c_size_t(sizeof(boottime))
    if _sysctl_boottime(byref(boottime), byref(buf_size), None, 0) < 0:
        raise Exception('Failure calling sysctl')
    return float(boottime)


def get_process_argv(pid, unhandled_exc_handler = None):
    argmax = c_int()
    mib = (c_int * 3)()
    mib[0] = CTL_KERN
    mib[1] = KERN_ARGMAX
    size = c_size_t(sizeof(argmax))
    libc.sysctl(mib, 2, byref(argmax), byref(size), None, 0)
    procargs = create_string_buffer(argmax.value)
    mib[0] = CTL_KERN
    mib[1] = KERN_PROCARGS2
    mib[2] = pid
    size = c_uint(argmax.value)
    libc.sysctl(mib, 3, procargs, byref(size), None, 0)
    cp = sizeof(c_int)
    while cp < size.value and procargs[cp] != '\x00':
        cp += 1

    if cp == size.value:
        raise Exception("Couldn't skip exec_path")
    while cp < size.value and procargs[cp] == '\x00':
        cp += 1

    addr = addressof(procargs)
    numargs = c_int.from_address(addr).value
    data = string_at(addr + cp, size.value - cp)
    if numargs == 0:
        try:
            raise Exception('No args for process: %r' % data.split('\x00', 10)[:10])
        except Exception:
            if unhandled_exc_handler:
                unhandled_exc_handler(False)

    return data.split('\x00', numargs)[0:numargs]


def get_process_command_string(pid, unhandled_exc_handler = None):
    x = get_process_argv(pid, unhandled_exc_handler)
    if x:
        return x[0]


def find_instances(cmd_string = None, not_me = True, other_users = False, unhandled_exc_handler = None):
    my_pid = os.getpid()
    my_euid = os.geteuid()
    mib = (c_int * 4)()
    mib[0] = CTL_KERN
    mib[1] = KERN_PROC
    mib[2] = KERN_PROC_ALL
    mib[3] = 0
    buf_size = c_size_t()
    libc.sysctl(mib, 4, None, byref(buf_size), None, 0)
    kprocbuf = create_string_buffer(buf_size.value)
    libc.sysctl(mib, 4, kprocbuf, byref(buf_size), None, 0)
    ENTRY_SIZE = 492
    PID_OFFSET = 24
    EUID_OFFSET = 304
    buf_address = addressof(kprocbuf)
    num_entries = buf_size.value / ENTRY_SIZE
    for i in xrange(num_entries):
        entry_offset = buf_address + i * ENTRY_SIZE
        the_pid = c_uint32.from_address(entry_offset + PID_OFFSET).value
        the_euid = c_uint32.from_address(entry_offset + EUID_OFFSET).value
        if the_pid == 0:
            continue
        if not other_users and my_euid != the_euid or not_me and the_pid == my_pid:
            continue
        if cmd_string is not None:
            try:
                the_cmd_string = get_process_command_string(the_pid, unhandled_exc_handler)
            except OSError:
                pass
            except Exception:
                if unhandled_exc_handler:
                    unhandled_exc_handler()
            else:
                if the_cmd_string and (cmd_string == the_cmd_string or the_cmd_string.endswith('/' + cmd_string)):
                    yield the_pid
        else:
            yield the_pid


if __name__ == '__main__':
    print get_process_command_string(22891)
    print list(find_instances(''))
