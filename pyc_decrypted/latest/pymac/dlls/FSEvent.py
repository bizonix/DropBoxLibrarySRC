#Embedded file name: pymac/dlls/FSEvent.py
from __future__ import absolute_import
from ctypes import POINTER, c_ubyte
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework
from ..types import CFAllocatorRef, CFArrayRef, CFUUIDRef, CFRunLoopRef, CFStringRef, CFTimeInterval, dev_t, FSEventStreamCallback, FSEventStreamContext, FSEventStreamCreateFlags, FSEventStreamEventId, FSEventStreamRef

class LazyFSEvent(LazyFramework):

    def __init__(self):
        super(LazyFSEvent, self).__init__()
        self._dllname = u'Foundation'
        self._func_defs = {}

        def F(name, ret = None, args = [], errcheck = None):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        F('FSEventsCopyUUIDForDevice', CFUUIDRef, [dev_t])
        F('FSEventStreamCreate', FSEventStreamRef, [CFAllocatorRef,
         FSEventStreamCallback,
         POINTER(FSEventStreamContext),
         CFArrayRef,
         FSEventStreamEventId,
         CFTimeInterval,
         FSEventStreamCreateFlags])
        F('FSEventStreamGetLatestEventId', FSEventStreamEventId, [FSEventStreamRef])
        F('FSEventsGetCurrentEventId', FSEventStreamEventId, None)
        F('FSEventStreamStart', c_ubyte, [FSEventStreamRef])
        F('FSEventStreamInvalidate', None, [FSEventStreamRef])
        F('FSEventStreamRelease', None, [FSEventStreamRef])
        F('FSEventStreamStop', None, [FSEventStreamRef])
        F('FSEventStreamScheduleWithRunLoop', None, [FSEventStreamRef, CFRunLoopRef, CFStringRef])


FSEvent = FakeDLL(LazyFSEvent)
