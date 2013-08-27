#Embedded file name: dropbox/win32/psapi.py
import ctypes
from ctypes import c_void_p, POINTER
from ctypes.wintypes import DWORD, BOOL, HANDLE
from dropbox.debugging import ReprStructure
from .kernel32 import GetLastError, win_strerror
SIZE_T = c_void_p

class PROCESS_MEMORY_COUNTERS(ReprStructure):
    _fields_ = [('cb', DWORD),
     ('PageFaultCount', DWORD),
     ('PeakWorkingSetSize', SIZE_T),
     ('WorkingSetSize', SIZE_T),
     ('QuotaPeakPagedPoolUsage', SIZE_T),
     ('QuotaPagedPoolUsage', SIZE_T),
     ('QuotaPeakNonPagedPoolUsage', SIZE_T),
     ('QuotaNonPagedPoolUsage', SIZE_T),
     ('PagefileUsage', SIZE_T),
     ('PeakPagefileUsage', SIZE_T)]


_psapi = ctypes.windll.psapi
try:
    GetProcessMemoryInfo = _psapi.GetProcessMemoryInfo
    GetProcessMemoryInfo.argtypes = [HANDLE, POINTER(PROCESS_MEMORY_COUNTERS), DWORD]
    GetProcessMemoryInfo.restype = BOOL
except:
    pass

try:
    _EnumProcesses = _psapi.EnumProcesses
    _EnumProcesses.argtypes = [POINTER(DWORD), DWORD, POINTER(DWORD)]
    _EnumProcesses.restype = BOOL
except:
    pass

def EnumProcesses():
    cur_pids = 100
    size_of_dword = ctypes.sizeof(DWORD)
    while True:
        pids = (DWORD * cur_pids)()
        bytes_allocated = cur_pids * size_of_dword
        bytes_returned = DWORD(0)
        if not _EnumProcesses(pids, bytes_allocated, ctypes.byref(bytes_returned)):
            win_errno = GetLastError()
            raise WindowsError(win_errno, win_strerror(win_errno))
        if bytes_returned.value != bytes_allocated:
            break
        cur_pids *= 2

    return pids[:bytes_returned.value / size_of_dword]
