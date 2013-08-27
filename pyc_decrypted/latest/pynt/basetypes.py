#Embedded file name: pynt/basetypes.py
import sys
from ctypes import c_ubyte, c_void_p, c_ulong, c_uint64, c_wchar, c_ulonglong
from ctypes.wintypes import BOOL, DWORD, HANDLE, HBITMAP, HICON, HKEY, HMENU, HWND, LPCWSTR, LONG, LPWSTR, UINT, ULONG, WORD
BYTE = c_ubyte
LPVOID = c_void_p
PVOID = c_void_p
SIZE_T = c_ulong
TCHAR = c_wchar
_is_64bits = sys.maxsize > 4294967296L
ULONG_PTR = c_uint64 if _is_64bits else c_ulong
ULONGLONG = c_ulonglong
