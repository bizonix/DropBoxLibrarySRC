#Embedded file name: pymac/dlls/DiskArbitration.py
from __future__ import absolute_import
from ctypes import c_char_p
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework
from ..types import CFAllocatorRef, CFDictionaryRef, DADiskRef, DASessionRef

class LazyDiskArbitration(LazyFramework):

    def __init__(self):
        super(LazyDiskArbitration, self).__init__()
        self._dllname = u'DiskArbitration'
        self._func_defs = {}

        def F(name, ret = None, args = []):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        def C(name, const_type):
            self._const_defs[name] = const_type

        F('DASessionCreate', DASessionRef, [CFAllocatorRef])
        F('DADiskCreateFromBSDName', DADiskRef, [CFAllocatorRef, DASessionRef, c_char_p])
        F('DADiskCopyDescription', CFDictionaryRef, [DADiskRef])


DiskArbitration = FakeDLL(LazyDiskArbitration)
