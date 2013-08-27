#Embedded file name: pynt/dlls/user32.py
from __future__ import absolute_import
from ctypes import POINTER, c_void_p
from ctypes.wintypes import BOOL, HMENU, HWND, UINT
from ..helpers.general import windows_null_check
from ..lazydll import FakeDLL, LazyDLL
from ..types import PMENUITEMINFO, UINT_PTR

class User32(LazyDLL):

    def __init__(self):
        super(User32, self).__init__()
        self._dllname = u'user32'
        self._func_defs = {'InsertMenuItemW': {'restype': BOOL,
                             'argtypes': [HMENU,
                                          UINT,
                                          BOOL,
                                          PMENUITEMINFO],
                             '__doc__': u'Inserts a new menu item at the specified positionin a menu.',
                             'unicode': True},
         'SetTimer': {'restype': POINTER(UINT),
                      'argtypes': [HWND,
                                   UINT_PTR,
                                   UINT,
                                   c_void_p],
                      '__doc__': u'Creates a timer with the specified time-out value.'},
         'KillTimer': {'restype': BOOL,
                       'argtypes': [HWND, UINT_PTR],
                       '__doc__': u'Destroys the specified timer.'},
         'RegisterHotKey': {'restype': BOOL,
                            'argtypes': [HWND,
                                         UINT,
                                         UINT,
                                         UINT],
                            '__doc__': u'Registers Hot Key',
                            'errcheck': windows_null_check},
         'UnregisterHotKey': {'restype': BOOL,
                              'argtypes': [HWND, UINT],
                              '__doc__': u'Unregisters Hot Key',
                              'errcheck': windows_null_check}}


user32 = FakeDLL(User32)
