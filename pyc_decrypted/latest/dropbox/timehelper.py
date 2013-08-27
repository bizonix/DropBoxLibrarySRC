#Embedded file name: dropbox/timehelper.py
from __future__ import absolute_import
from datetime import datetime
import time

def tz_offset_minutes(datetime_obj):
    timestamp = time.mktime(datetime_obj.timetuple())
    offset = datetime.fromtimestamp(timestamp) - datetime.utcfromtimestamp(timestamp)
    return (offset.days * 24 * 60 * 60 + offset.seconds) / 60


def tz_offset_string(datetime_obj):
    offset_minutes = tz_offset_minutes(datetime_obj)
    sign = '-' if offset_minutes < 0 else '+'
    offset_minutes = abs(offset_minutes)
    dummy_time = (0,
     0,
     0,
     int(offset_minutes / 60),
     offset_minutes % 60,
     0,
     0,
     0,
     0)
    return sign + time.strftime('%H%M', dummy_time)
