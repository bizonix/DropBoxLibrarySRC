#Embedded file name: dropbox/monotonic_time/__init__.py
from __future__ import absolute_import
import sys
if sys.platform.startswith('darwin'):
    from .monotonic_time_mac import get_monotonic_time, get_monotonic_frequency
elif sys.platform.startswith('win32'):
    from .monotonic_time_win32 import get_monotonic_time, get_monotonic_frequency
else:
    from .monotonic_time_linux import get_monotonic_time, get_monotonic_frequency

def get_monotonic_time_seconds():
    return get_monotonic_time() / get_monotonic_frequency()
