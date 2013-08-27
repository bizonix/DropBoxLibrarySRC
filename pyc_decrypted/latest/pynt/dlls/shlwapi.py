#Embedded file name: pynt/dlls/shlwapi.py
from __future__ import absolute_import
from ctypes import POINTER
from ctypes.wintypes import HRESULT, HKEY, DWORD, LONG, LPCWSTR, LPWSTR
from ..helpers.general import windows_error_check
from ..lazydll import FakeDLL, LazyDLL

class Shlwapi(LazyDLL):

    def __init__(self):
        super(Shlwapi, self).__init__()
        self._dllname = u'Shlwapi'
        self._func_defs = {'SHDeleteKeyW': {'restype': LONG,
                          'argtypes': [HKEY, LPCWSTR],
                          '__doc__': u'Deletes a subkey and all its descendants.',
                          'unicode': True,
                          'when_not_found': self.return_error_not_found},
         'AssocQueryStringW': {'restype': HRESULT,
                               'argtypes': [DWORD,
                                            DWORD,
                                            LPCWSTR,
                                            LPCWSTR,
                                            LPWSTR,
                                            POINTER(DWORD)],
                               '__doc__': u'Queries file type associations from the OS.',
                               'unicode': True,
                               'when_not_found': self.return_error_not_found,
                               'errcheck': windows_error_check}}


shlwapi = FakeDLL(Shlwapi)
