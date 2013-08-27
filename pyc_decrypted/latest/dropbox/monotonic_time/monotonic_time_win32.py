#Embedded file name: dropbox/monotonic_time/monotonic_time_win32.py
import math
from pynt.dlls.kernel32 import kernel32
from dropbox.trace import TRACE, report_bad_assumption
_last_ticks = 0
_overflow_count = 0

def get_monotonic_time():
    global _overflow_count
    global _last_ticks
    try:
        return kernel32.GetTickCount64()
    except NotImplementedError:
        try:
            ticks = kernel32.GetTickCount()
        except NotImplementedError:
            TRACE('!! GetTickCount failed')
            report_bad_assumption('GetTickCount failed')
            return 1.0

        if ticks < _last_ticks:
            _overflow_count += 1
        _last_ticks = ticks
        result = math.ldexp(_overflow_count, 32)
        result += ticks
        return result


def get_monotonic_frequency():
    return 1000.0
