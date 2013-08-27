#Embedded file name: arch/linux/tracing.py
from __future__ import absolute_import
import os
from ctypes import create_string_buffer
from signal import alarm, SIGSEGV, SIGBUS, SIGILL, SIGFPE
import hard_trace
from dropbox.linux_libc import MAX_TRACE_LENGTH, sig_handler_t, signal, backtrace, backtrace_symbols
from ..posix_common.tracing import send_report, watch_faults
from .util import hard_exit
SIGNAL_HANDLER_TIMEOUT = 5
fatal_signals = {SIGSEGV: 'SIGSEGV',
 SIGBUS: 'SIGBUS',
 SIGILL: 'SIGILL',
 SIGFPE: 'SIGFPE'}
_death_bell_flag = False

def death_bell():
    global _death_bell_flag
    if not _death_bell_flag:
        alarm(SIGNAL_HANDLER_TIMEOUT)
        _death_bell_flag = True


def generate_trace():
    try:
        trace = create_string_buffer(MAX_TRACE_LENGTH)
        trace_length = backtrace(trace, len(trace))
        symbols = backtrace_symbols(trace, trace_length)
        a = [ symbols[i] for i in range(trace_length) ]
        return a
    except:
        return []


@sig_handler_t
def handle_fatal(signum):
    death_bell()
    try:
        trace = generate_trace()
        c_stack = '\n'.join(trace)
        signal_s = fatal_signals[signum]
        send_report(signal_s, c_stack)
        hard_exit(exit_code=-signum)
    except:
        os._exit(-signum)


for sig in fatal_signals:
    signal(sig, handle_fatal)

watch_faults()
