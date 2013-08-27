#Embedded file name: pynt/dlls/gdi32.py
from __future__ import absolute_import
from ctypes import c_int
from ctypes.wintypes import HDC, BOOL
from ..lazydll import FakeDLL, LazyDLL
from ..types import LPPOINT

class Gdi32(LazyDLL):

    def __init__(self):
        super(Gdi32, self).__init__()
        self._dllname = u'Gdi32'
        self._func_defs = {'SetBrushOrgEx': {'restype': BOOL,
                           'argtypes': [HDC,
                                        c_int,
                                        c_int,
                                        LPPOINT],
                           'when_not_found': self.return_false}}


gdi32 = FakeDLL(Gdi32)
