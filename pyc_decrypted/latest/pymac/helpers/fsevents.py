#Embedded file name: pymac/helpers/fsevents.py
from __future__ import absolute_import
import os
from ..constants import kCFAllocatorDefault
from ..dlls import Core, FSEvent
from .core import CFString

def fsevent_uuid_for_path(path):
    dev_t = os.stat(path).st_dev
    uuid_ref = FSEvent.FSEventsCopyUUIDForDevice(dev_t)
    if uuid_ref is not None:
        uuid_str = Core.CFUUIDCreateString(kCFAllocatorDefault, uuid_ref)
        Core.CFRelease(uuid_ref)
        return CFString.to_unicode(uuid_str)
    else:
        return
