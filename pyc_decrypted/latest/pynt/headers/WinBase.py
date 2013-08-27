#Embedded file name: pynt/headers/WinBase.py
from ctypes import Structure, POINTER, Union
from ctypes.wintypes import FILETIME
from ..basetypes import HANDLE, DWORD, PVOID, ULONG_PTR
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
FILE_SHARE_DELETE = 4
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 33554432
FILE_FLAG_NO_BUFFERING = 536870912
FILE_FLAG_WRITE_THROUGH = 2147483648L
REPLACEFILE_WRITE_THROUGH = 1
MOVEFILE_REPLACE_EXISTING = 1
VOLUME_NAME_NT = 2
INVALID_HANDLE_VALUE = HANDLE(-1).value
INVALID_FILE_ATTRIBUTES = DWORD(-1).value

class BY_HANDLE_FILE_INFORMATION(Structure):
    _fields_ = [('dwFileAttributes', DWORD),
     ('ftCreationTime', FILETIME),
     ('ftLastAccessTime', FILETIME),
     ('ftLastWriteTime', FILETIME),
     ('dwVolumeSerialNumber', DWORD),
     ('nFileSizeHigh', DWORD),
     ('nFileSizeLow', DWORD),
     ('nNumberOfLinks', DWORD),
     ('nFileIndexHigh', DWORD),
     ('nFileIndexLow', DWORD)]


PBY_HANDLE_FILE_INFORMATION = POINTER(BY_HANDLE_FILE_INFORMATION)
LPBY_HANDLE_FILE_INFORMATION = PBY_HANDLE_FILE_INFORMATION

class _OVERLAPPED_INNER1(Structure):
    _fields_ = [('Offset', DWORD), ('OffsetHigh', DWORD)]


class _OVERLAPPED_INNER(Union):
    _anonymous_ = ['_u']
    _fields_ = [('_u', _OVERLAPPED_INNER1), ('Pointer', PVOID)]


class OVERLAPPED(Structure):
    _anonymous_ = ['_a']
    _fields_ = [('Internal', ULONG_PTR),
     ('InternalHigh', ULONG_PTR),
     ('_a', _OVERLAPPED_INNER),
     ('hEvent', HANDLE)]


LPOVERLAPPED = POINTER(OVERLAPPED)
