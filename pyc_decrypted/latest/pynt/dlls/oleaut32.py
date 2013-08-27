#Embedded file name: pynt/dlls/oleaut32.py
from __future__ import absolute_import
from ..lazydll import FakeDLL, LazyDLL
from ctypes.wintypes import LPCOLESTR, WORD, POINTER, ULONG
from ..types import LPVOID, LCID, SYSKIND
from comtypes.GUID import GUID

class OleAut32(LazyDLL):

    def __init__(self):
        super(OleAut32, self).__init__()
        self._dllname = u'OleAut32'
        self._func_defs = {'LoadTypeLib': {'restype': ULONG,
                         'argtypes': [LPCOLESTR, POINTER(LPVOID)],
                         '__doc__': u'This function loads and registers a typelib2 type library',
                         'when_not_found': self.return_e_fail},
         'RegisterTypeLibForUser': {'restype': ULONG,
                                    'argtypes': [LPVOID, LPCOLESTR, LPCOLESTR],
                                    '__doc__': u'Registers a type library for use by the calling user',
                                    'when_not_found': self.return_e_fail},
         'UnRegisterTypeLibForUser': {'restype': ULONG,
                                      'argtypes': [POINTER(GUID),
                                                   WORD,
                                                   WORD,
                                                   LCID,
                                                   SYSKIND],
                                      '__doc__': u'Removes type library information that was registered by using RegisterTypeLibForUser',
                                      'when_not_found': self.return_e_fail},
         'RegisterTypeLib': {'restype': ULONG,
                             'argtypes': [LPVOID, LPCOLESTR, LPCOLESTR],
                             '__doc__': u'This function adds information about a type library to the system registry',
                             'when_not_found': self.return_e_fail},
         'UnRegisterTypeLib': {'restype': ULONG,
                               'argtypes': [POINTER(GUID),
                                            WORD,
                                            WORD,
                                            LCID,
                                            SYSKIND],
                               '__doc__': u'This function removes type library information from the system registry',
                               'when_not_found': self.return_e_fail}}


oleaut32 = FakeDLL(OleAut32)
