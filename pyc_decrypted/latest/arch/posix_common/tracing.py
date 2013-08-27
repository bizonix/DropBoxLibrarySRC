#Embedded file name: arch/posix_common/tracing.py
from __future__ import absolute_import
import faulthandler
from hashlib import md5
from tempfile import TemporaryFile
import hard_trace
from dropbox.trace import TRACE

class StackTraceBuffer(object):

    def __init__(self):
        self.f = None

    def fileno(self):
        if not self.f:
            self.f = TemporaryFile()
        return self.f.fileno()

    def getvalue(self):
        if self.f:
            self.f.seek(0)
            return self.f.read()
        return ''


_stack_buffer = None

def watch_faults():
    global _stack_buffer
    if not _stack_buffer:
        _stack_buffer = StackTraceBuffer()
        faulthandler.enable(_stack_buffer)


def send_report(signal_s, c_stack):
    py_stack = _stack_buffer.getvalue()
    hash = md5(py_stack if py_stack else c_stack).hexdigest()
    report = c_stack + '\n' + signal_s + '\n' + py_stack
    TRACE('!! Terrible crash! Here are the details: \n%s', report)
    hard_trace.unhandled_exc_handler(hash, report)
