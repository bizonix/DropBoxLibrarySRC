#Embedded file name: pynt/dlls/crypt32.py
from __future__ import absolute_import
from ctypes.wintypes import BOOL, DWORD, LPCWSTR
from ..lazydll import FakeDLL, LazyDLL
from ..types import LPCRYPTPROTECT_PROMPTSTRUCT, LPDATA_BLOB, LPVOID

class Crypt32(LazyDLL):

    def __init__(self):
        super(Crypt32, self).__init__()
        self._dllname = u'Crypt32'
        self._func_defs = {'CryptProtectData': {'restype': BOOL,
                              'argtypes': [LPDATA_BLOB,
                                           LPCWSTR,
                                           LPDATA_BLOB,
                                           LPVOID,
                                           LPCRYPTPROTECT_PROMPTSTRUCT,
                                           DWORD,
                                           LPDATA_BLOB],
                              'unicode': False,
                              'when_not_found': self.return_false},
         'CryptUnprotectData': {'restype': BOOL,
                                'argtypes': [LPDATA_BLOB,
                                             LPCWSTR,
                                             LPDATA_BLOB,
                                             LPVOID,
                                             LPCRYPTPROTECT_PROMPTSTRUCT,
                                             DWORD,
                                             LPDATA_BLOB],
                                'unicode': False,
                                'when_not_found': self.return_false}}


crypt32 = FakeDLL(Crypt32)
