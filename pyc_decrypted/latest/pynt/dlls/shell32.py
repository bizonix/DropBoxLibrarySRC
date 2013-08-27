#Embedded file name: pynt/dlls/shell32.py
from __future__ import absolute_import
from comtypes.GUID import GUID
from ctypes import c_int, c_uint, c_void_p
from ctypes.wintypes import BOOL, DWORD, HANDLE, HRESULT, HWND, LONG, LPCWSTR, LPWSTR, POINTER, RECT, UINT, ULONG
from ..types import PAPPBARDATA, PIDLIST, PNOTIFYICONDATA, PNOTIFYICONIDENTIFIER, SHFILEOPSTRUCTW, UINT_PTR
from ..lazydll import FakeDLL, LazyDLL

class Shell32(LazyDLL):

    def __init__(self):
        super(Shell32, self).__init__()
        self._dllname = u'Shell32'
        self._func_defs = dict(DragQueryFileW=dict(restype=ULONG, argtypes=[HANDLE,
         ULONG,
         LPWSTR,
         ULONG], __doc__=u'Retrieves the names of dropped files that result from a successful drag-and-drop operation.', unicode=True, when_not_found=self.return_e_fail), ILCreateFromPathW=dict(restype=PIDLIST, argtypes=[LPWSTR], when_not_found=self.return_e_fail), ILFree=dict(restype=None, argtypes=[PIDLIST], when_not_found=self.return_e_fail), Shell_NotifyIconGetRect=dict(restype=HRESULT, argtypes=[PNOTIFYICONIDENTIFIER, POINTER(RECT)], __doc__=u'Gets the screen coordinates of the bounding rectangle of a notification icon.', when_not_found=self.return_e_fail), Shell_NotifyIconW=dict(restype=BOOL, argtypes=[DWORD, PNOTIFYICONDATA], __doc__=u"Sends a message to the taskbar's status area", unicode=True), CommandLineToArgvW=dict(restype=POINTER(LPWSTR), argtypes=[LPWSTR, POINTER(c_int)], when_not_found=self.return_none), SHFileOperationW=dict(restype=c_int, argtypes=[POINTER(SHFILEOPSTRUCTW)], when_not_found=self.return_e_fail), SHChangeNotify=dict(restype=None, argtypes=[LONG,
         UINT,
         c_void_p,
         c_void_p], when_not_found=self.return_none), SHGetFolderPathW=dict(restype=ULONG, argtypes=[HWND,
         c_int,
         HANDLE,
         DWORD,
         LPWSTR], __doc__=u'Gets the path of a folder identified by a CSIDL value.', unicode=True, when_not_found=self.return_e_fail), SHSetFolderPathW=dict(restype=HRESULT, argtypes=[c_int,
         HANDLE,
         DWORD,
         LPCWSTR], __doc__=u'Sets the path of a folder identified by a CSIDL value.', unicode=True, ordinal=232, when_not_found=self.return_e_fail), SHOpenFolderAndSelectItems=dict(restype=ULONG, argtypes=[PIDLIST,
         c_uint,
         POINTER(PIDLIST),
         DWORD], when_not_found=self.return_e_fail), SHSetKnownFolderPath=dict(restype=HRESULT, argtypes=[POINTER(GUID),
         DWORD,
         HANDLE,
         LPCWSTR], __doc__=u'Redirects a known folder to a new location.', when_not_found=self.return_e_fail), SHGetKnownFolderPath=dict(restype=HRESULT, argtypes=[POINTER(GUID),
         DWORD,
         HANDLE,
         POINTER(LPCWSTR)], __doc__=u'Retrieves the full path of a known folder.', when_not_found=self.return_e_fail), SHAppBarMessage=dict(restype=UINT_PTR, argtypes=[DWORD, PAPPBARDATA], __doc__=u'Sends an appbar message to the system.'))


shell32 = FakeDLL(Shell32)
