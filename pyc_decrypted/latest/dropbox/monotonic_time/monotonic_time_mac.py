#Embedded file name: dropbox/monotonic_time/monotonic_time_mac.py
from __future__ import absolute_import
import time
from dropbox.trace import unhandled_exc_handler
from pymac.helpers.process import get_boottime

def get_monotonic_time():
    try:
        return time.time() - get_boottime()
    except Exception:
        unhandled_exc_handler()
        return 0


def get_monotonic_frequency():
    return 1.0
