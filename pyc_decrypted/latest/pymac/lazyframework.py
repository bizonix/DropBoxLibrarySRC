#Embedded file name: pymac/lazyframework.py
from __future__ import absolute_import
import ctypes
import ctypes.macholib.dyld
from .lazydll import LazyDLL

class LazyFramework(LazyDLL):

    def init(self):
        self._dll = ctypes.cdll.LoadLibrary(ctypes.macholib.dyld.framework_find(self._dllname))
