#Embedded file name: pymac/dlls/SystemConfiguration.py
from __future__ import absolute_import
from ctypes import POINTER
from ..lazyframework import LazyFramework
from ..lazydll import FakeDLL
from ..types import CFAllocatorRef, CFArrayRef, CFIndex, CFRunLoopSourceRef, CFStringRef, SCDynamicStoreCallback, SCDynamicStoreContext, SCDynamicStoreRef

class LazySystemConfiguration(LazyFramework):

    def __init__(self):
        super(LazySystemConfiguration, self).__init__()
        self._dllname = u'SystemConfiguration'
        self._func_defs = {}

        def F(name, ret = None, args = []):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        F('SCDynamicStoreCreate', SCDynamicStoreRef, [CFAllocatorRef,
         CFStringRef,
         SCDynamicStoreCallback,
         POINTER(SCDynamicStoreContext)])
        F('SCDynamicStoreKeyCreateProxies', CFStringRef, [CFAllocatorRef])
        F('SCDynamicStoreSetNotificationKeys', None, [SCDynamicStoreRef, CFArrayRef, CFArrayRef])
        F('SCDynamicStoreCreateRunLoopSource', CFRunLoopSourceRef, [CFAllocatorRef, SCDynamicStoreRef, CFIndex])


SystemConfiguration = FakeDLL(LazySystemConfiguration)
