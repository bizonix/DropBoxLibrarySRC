#Embedded file name: arch/mac/tracing.py
from __future__ import absolute_import
import os
from Foundation import NSLog
from ctypes import c_void_p
from signal import alarm, SIGSEGV, SIGBUS, SIGILL, SIGFPE
from pymac.dlls import libc
from pymac.types import sig_handler_t
import build_number
from hard_trace import MAX_REPORT_LENGTH
from dropbox.mac.internal import get_frameworks_dir
from dropbox.mac.version import MAC_VERSION, TIGER
from arch.posix_common.tracing import send_report, watch_faults
from .util import hard_exit
fatal_signals = {SIGSEGV: 'SIGSEGV',
 SIGBUS: 'SIGBUS',
 SIGILL: 'SIGILL',
 SIGFPE: 'SIGFPE'}
SIGNAL_HANDLER_TIMEOUT = 5
_death_bell_flag = False

def death_bell():
    global _death_bell_flag
    if not _death_bell_flag:
        alarm(SIGNAL_HANDLER_TIMEOUT)
        _death_bell_flag = True


if MAC_VERSION > TIGER:

    @sig_handler_t
    def handle_fatal(signal):
        death_bell()
        try:
            trace = (c_void_p * 65536)()
            trace_length = libc.backtrace(trace, len(trace))
            data = libc.backtrace_symbols(trace, trace_length)
            if data:
                data = [ data[i] for i in xrange(trace_length) ]
                data.reverse()
                c_trace = '\n'.join(data)
            else:
                c_trace = '\n'.join(('%#.8x' % trace[i] for i in xrange(trace_length)))
            signal_s = fatal_signals[signal]
            NSLog('%s\n%s' % (c_trace, signal_s))
            send_report(signal_s, c_trace)
            hard_exit(exit_code=-signal)
        except Exception:
            os._exit(-signal)


else:
    import re
    from ctypes import POINTER, c_char_p, c_int, create_string_buffer, cdll, byref
    libQCR = cdll.LoadLibrary('%s/libQCR.dylib' % (get_frameworks_dir() if hasattr(build_number, 'frozen') else 'mac_dependencies'))
    QCrashReportRef = c_void_p
    QCRCreateFromSelf = libQCR.QCRCreateFromSelf
    QCRCreateFromSelf.restype = c_int
    QCRCreateFromSelf.argtypes = [POINTER(QCrashReportRef)]
    QCRDropboxFormatBacktrace = libQCR.QCRDropboxFormatBacktrace
    QCRDropboxFormatBacktrace.restype = c_int
    QCRDropboxFormatBacktrace.argtypes = [QCrashReportRef, c_char_p, c_int]
    buffer = create_string_buffer(MAX_REPORT_LENGTH)
    addr_re = re.compile('\\[0x.*\\]')

    @sig_handler_t
    def handle_fatal(signal):
        death_bell()
        try:
            crRef = QCrashReportRef(0)
            if QCRCreateFromSelf(byref(crRef)):
                NSLog("Couldn't generate crash report")
                os._exit(-signal)
            valid_lines = QCRDropboxFormatBacktrace(crRef, buffer, MAX_REPORT_LENGTH)
            formatted = '\n'.join(buffer.value.splitlines()[:valid_lines][::-1])
            signal_s = fatal_signals[signal]
            NSLog('%s\n%s' % (formatted, signal_s))
            send_report(signal_s, formatted)
            hard_exit(exit_code=-signal)
        except Exception:
            os._exit(-signal)


for sig in fatal_signals:
    libc.signal(sig, handle_fatal)

watch_faults()
