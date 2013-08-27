#Embedded file name: pynt/dlls/dwmapi.py
from ..lazydll import FakeDLL, LazyDLL
from ctypes.wintypes import BOOL, HRESULT, POINTER

class Dwmapi(LazyDLL):

    def __init__(self):
        super(Dwmapi, self).__init__()
        self._dllname = u'Dwmapi'
        self._func_defs = {'DwmIsCompositionEnabled': {'restype': HRESULT,
                                     'argtypes': [POINTER(BOOL)],
                                     'when_not_found': self.return_false,
                                     '__doc__': u'Obtains a value that indicates whether Desktop Window Manager (DWM) composition is enabled.'}}


dwmapi = FakeDLL(Dwmapi)
