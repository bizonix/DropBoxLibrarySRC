#Embedded file name: dropbox/win32/kernel32.py
import win32con
import ctypes
import ctypes.util
from ctypes import c_void_p, c_int, c_wchar, c_wchar_p, POINTER, Structure
from ctypes.wintypes import DWORD, BOOL, LPCWSTR, LPWSTR, HANDLE, LONG
from dropbox.debugging import ReprStructure
LPCVOID = c_void_p
HLOCAL = c_void_p
PDWORD = POINTER(DWORD)
_kernel32 = ctypes.windll.kernel32
GetLastError = _kernel32.GetLastError
GetLastError.argtypes = []
GetLastError.restype = DWORD
SetLastError = _kernel32.SetLastError
SetLastError.argtypes = [DWORD]
CreateMutex = _kernel32.CreateMutexW
CreateMutex.argtypes = [c_void_p, BOOL, LPCWSTR]
CreateMutex.restype = HANDLE
ReleaseMutex = _kernel32.ReleaseMutex
ReleaseMutex.argtypes = [HANDLE]
ReleaseMutex.restype = BOOL
CreateSemaphore = _kernel32.CreateSemaphoreW
CreateSemaphore.argtypes = [c_void_p,
 LONG,
 LONG,
 LPCWSTR]
CreateSemaphore.restype = HANDLE
ReleaseSemaphore = _kernel32.ReleaseSemaphore
ReleaseSemaphore.argtypes = [HANDLE, LONG, c_void_p]
ReleaseSemaphore.restype = BOOL
CreateEvent = _kernel32.CreateEventW
CreateEvent.argtypes = [c_void_p,
 BOOL,
 BOOL,
 LPCWSTR]
CreateEvent.restype = HANDLE
SetEvent = _kernel32.SetEvent
SetEvent.argtypes = [HANDLE]
SetEvent.restype = BOOL
WaitForSingleObject = _kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [HANDLE, DWORD]
WaitForSingleObject.restype = DWORD
SignalObjectAndWait = _kernel32.SignalObjectAndWait
SignalObjectAndWait.argtypes = [HANDLE,
 HANDLE,
 DWORD,
 BOOL]
SignalObjectAndWait.restype = DWORD
CloseHandle = _kernel32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

class FILETIME(ReprStructure):
    _fields_ = [('dwLowDateTime', DWORD), ('dwHighDateTime', DWORD)]


class WIN32_FIND_DATAW(ReprStructure):
    _fields_ = [('dwFileAttributes', DWORD),
     ('ftCreationTime', FILETIME),
     ('ftLastAccessTime', FILETIME),
     ('ftLastWriteTime', FILETIME),
     ('nFileSizeHigh', DWORD),
     ('nFileSizeLow', DWORD),
     ('dwReserved0', DWORD),
     ('dwReserved1', DWORD),
     ('cFileName', c_wchar * win32con.MAX_PATH),
     ('cAlternateFileName', c_wchar * 14)]


FindExInfoStandard = 0
FindExInfoBasic = 1
FindExSearchNameMatch = 0
FIND_FIRST_EX_LARGE_FETCH = 2
FindFirstFileExW = _kernel32.FindFirstFileExW
FindFirstFileExW.argtypes = [LPCWSTR,
 c_int,
 POINTER(WIN32_FIND_DATAW),
 c_int,
 c_void_p,
 DWORD]
FindFirstFileExW.restype = HANDLE
FindNextFileW = _kernel32.FindNextFileW
FindNextFileW.argtypes = [HANDLE, POINTER(WIN32_FIND_DATAW)]
FindNextFileW.restype = BOOL
FindClose = _kernel32.FindClose
FindClose.argtypes = [HANDLE]
FindClose.restype = BOOL
FindFirstVolumeW = _kernel32.FindFirstVolumeW
FindFirstVolumeW.argtypes = [LPCWSTR, DWORD]
FindFirstVolumeW.restype = HANDLE
FindNextVolumeW = _kernel32.FindNextVolumeW
FindNextVolumeW.argtypes = [HANDLE, LPCWSTR, DWORD]
FindNextVolumeW.restype = BOOL
FindVolumeClose = _kernel32.FindVolumeClose
FindVolumeClose.argtypes = [HANDLE]
FindVolumeClose.restype = BOOL
FORMAT_MESSAGE_ALLOCATE_BUFFER = 256
FORMAT_MESSAGE_FROM_SYSTEM = 4096
FORMAT_MESSAGE_IGNORE_INSERTS = 512
FormatMessageW = _kernel32.FormatMessageW
FormatMessageW.argtypes = [DWORD,
 LPCVOID,
 DWORD,
 DWORD,
 LPCWSTR,
 DWORD,
 LPCVOID]
FormatMessageW.restype = DWORD
LocalFree = _kernel32.LocalFree
LocalFree.argtypes = [HLOCAL]
LocalFree.restype = HLOCAL
try:
    GetVolumePathNamesForVolumeNameW = _kernel32.GetVolumePathNamesForVolumeNameW
    GetVolumePathNamesForVolumeNameW.argtypes = [LPCWSTR,
     LPWSTR,
     DWORD,
     PDWORD]
    GetVolumePathNamesForVolumeNameW.restype = BOOL
except:

    def GetVolumePathNamesForVolumeNameW(*n, **kw):
        SetLastError(1)
        return 0


def win_strerror(err):
    a = c_wchar_p()
    if FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, None, err, 0, ctypes.cast(ctypes.byref(a), LPCWSTR), 0, None):
        try:
            return a.value
        finally:
            LocalFree(ctypes.cast(a, HLOCAL))

    else:
        return


SwitchToThread = _kernel32.SwitchToThread
SwitchToThread.argtypes = []
SwitchToThread.restype = BOOL
