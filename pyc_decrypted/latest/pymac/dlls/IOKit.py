#Embedded file name: pymac/dlls/IOKit.py
from __future__ import absolute_import
from ctypes import c_char_p, POINTER
from ..types import CFAllocatorRef, CFDictionaryRef, CFStringRef, CFTypeRef, IOOptionBits, io_registry_entry_t, io_service_t, kern_return_t, mach_port_t
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework

class LazyIOKit(LazyFramework):

    def __init__(self):
        super(LazyIOKit, self).__init__()
        self._dllname = u'IOKit'
        self._func_defs = {}

        def F(name, ret = None, args = []):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        def C(name, const_type):
            self._const_defs[name] = const_type

        F('IOServiceGetMatchingService', io_service_t, [mach_port_t, CFDictionaryRef])
        F('IOServiceMatching', CFDictionaryRef, [c_char_p])
        F('IORegistryEntryCreateCFProperty', CFTypeRef, [io_service_t,
         CFStringRef,
         CFAllocatorRef,
         IOOptionBits])
        F('IOObjectRelease', kern_return_t, [io_service_t])
        F('IORegistryEntryFromPath', io_registry_entry_t, [mach_port_t, c_char_p])
        F('IORegistryEntryCreateCFProperties', CFTypeRef, [io_registry_entry_t,
         POINTER(CFDictionaryRef),
         CFAllocatorRef,
         IOOptionBits])


IOKit = FakeDLL(LazyIOKit)
