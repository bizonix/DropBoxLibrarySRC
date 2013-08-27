#Embedded file name: pynt/dlls/rstrtmgr.py
from __future__ import absolute_import
from ctypes import POINTER, Structure, c_void_p
from ctypes.wintypes import WCHAR, ULONG, UINT, LPCWSTR, FILETIME
from ..lazydll import FakeDLL, LazyDLL
from ..types import DWORD, RM_UNIQUE_PROCESS
from ..helpers.general import windows_error_check

class Rstrtmgr(LazyDLL):

    def __init__(self):
        super(Rstrtmgr, self).__init__()
        self._dllname = u'Rstrtmgr'
        self._func_defs = {'RmStartSession': {'restype': DWORD,
                            'argtypes': [POINTER(DWORD), DWORD, POINTER(WCHAR)],
                            '__doc__': u'Starts a new Restart Manager session.',
                            'when_not_found': self.raise_not_implemented_error,
                            'errcheck': windows_error_check},
         'RmRegisterResources': {'restype': DWORD,
                                 'argtypes': [DWORD,
                                              UINT,
                                              LPCWSTR,
                                              UINT,
                                              POINTER(RM_UNIQUE_PROCESS),
                                              UINT,
                                              LPCWSTR],
                                 '__doc__': u'Registers resources to a Restart Manager session.',
                                 'when_not_found': self.raise_not_implemented_error,
                                 'errcheck': windows_error_check},
         'RmShutdown': {'restype': DWORD,
                        'argtypes': [DWORD, ULONG, c_void_p],
                        'when_not_found': self.raise_not_implemented_error,
                        'errcheck': windows_error_check},
         'RmRestart': {'restype': DWORD,
                       'argtypes': [DWORD, DWORD, c_void_p],
                       'when_not_found': self.raise_not_implemented_error,
                       'errcheck': windows_error_check},
         'RmEndSession': {'restype': DWORD,
                          'argtypes': [DWORD],
                          '__doc__': u'Ends the Restart Manager session.',
                          'when_not_found': self.raise_not_implemented_error,
                          'errcheck': windows_error_check}}


rstrtmgr = FakeDLL(Rstrtmgr)
