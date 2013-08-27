#Embedded file name: pynt/dlls/ole32.py
from __future__ import absolute_import
from ctypes.wintypes import ULONG
from ctypes import POINTER
from comtypes.automation import VARIANT
from ..lazydll import FakeDLL, LazyDLL
from ..types import LPVOID, VOID

class Ole32(LazyDLL):

    def __init__(self):
        super(Ole32, self).__init__()
        self._dllname = u'Ole32'
        self._func_defs = {'CoTaskMemFree': {'restype': VOID,
                           'argtypes': [LPVOID],
                           '__doc__': u'Frees a block of task memory.',
                           'when_not_found': self.return_none},
         'PropVariantClear': {'restype': ULONG,
                              'argtypes': [POINTER(VARIANT)],
                              '__doc__': u'This function clears a variant',
                              'when_not_found': self.return_e_fail}}


ole32 = FakeDLL(Ole32)
