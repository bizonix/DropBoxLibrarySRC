#Embedded file name: pynt/types.py
from __future__ import absolute_import
from ctypes import c_buffer, c_char, c_int, c_uint, c_long, c_ulong, c_void_p, memmove, POINTER, Structure, c_ubyte, Union, sizeof, addressof, byref
from ctypes.wintypes import RECT, POINT, LPARAM
from .basetypes import BOOL, BYTE, DWORD, HANDLE, HBITMAP, HICON, HKEY, HMENU, HWND, LPCWSTR, LONG, LPVOID, LPWSTR, PVOID, SIZE_T, TCHAR, UINT, ULONG, ULONG_PTR, WORD, ULONGLONG
from .headers.WinBase import FILETIME
from comtypes.GUID import GUID
VOID = None
UINT_PTR = c_uint
PBYTE = LPBYTE = POINTER(BYTE)
PHKEY = POINTER(HKEY)
PDWORD = LPDWORD = POINTER(DWORD)
LPPOINT = PPOINT = POINTER(POINT)
MULTIPLE_TRUSTEE_OPERATION = c_int
NO_MULTIPLE_TRUSTEE = 0
TRUSTEE_IS_IMPERSONATE = 1
TRUSTEE_TYPE = c_int
TRUSTEE_IS_UNKNOWN = 0
TRUSTEE_IS_USER = 1
TRUSTEE_IS_GROUP = 2
TRUSTEE_IS_DOMAIN = 3
TRUSTEE_IS_ALIAS = 4
TRUSTEE_IS_WELL_KNOWN_GROUP = 5
TRUSTEE_IS_DELETED = 6
TRUSTEE_IS_INVALID = 7
TRUSTEE_IS_COMPUTER = 8
TRUSTEE_FORM = c_int
TRUSTEE_IS_SID = 0
TRUSTEE_IS_NAME = 1
TRUSTEE_BAD_FORM = 2
TRUSTEE_IS_OBJECTS_AND_SID = 3
TRUSTEE_IS_OBJECTS_AND_NAME = 4
ACCESS_MODE = c_int
NOT_USED_ACCESS = 0
GRANT_ACCESS = 1
SET_ACCESS = 2
DENY_ACCESS = 3
REVOKE_ACCESS = 4
SET_AUDIT_SUCCESS = 5
SET_AUDIT_FAILURE = 6

class TRUSTEEW(Structure):

    def __repr__(self):
        return 'TRUSTEEW(%d, 0x%x, 0x%x, %r)' % (self.MultipleTrusteeOperation,
         self.TrusteeForm,
         self.TrusteeType,
         self.ptstrName)


TRUSTEEW._fields_ = [('pMultipleTrustee', POINTER(TRUSTEEW)),
 ('MultipleTrusteeOperation', MULTIPLE_TRUSTEE_OPERATION),
 ('TrusteeForm', TRUSTEE_FORM),
 ('TrusteeType', TRUSTEE_TYPE),
 ('ptstrName', LPWSTR)]
PTRUSTEEW = LPTRUSTEEW = POINTER(TRUSTEEW)

class EXPLICIT_ACCESSW(Structure):
    _fields_ = [('grfAccessPermissions', DWORD),
     ('grfAccessMode', ACCESS_MODE),
     ('grfInheritance', DWORD),
     ('Trustee', TRUSTEEW)]

    def __repr__(self):
        return 'EXPLICIT_ACCESSW(0x%x, 0x%0x, 0x%0x, %r)' % (self.grfAccessPermissions,
         self.grfAccessMode,
         self.grfInheritance,
         self.Trustee)


PEXPLICIT_ACCESSW = LPEXPLICIT_ACCESSW = POINTER(EXPLICIT_ACCESSW)

class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [('nLength', DWORD), ('lpSecurityDescriptor', LPVOID), ('bInheritHandle', BOOL)]


PSECURITY_ATTRIBUTES = LPSECURITY_ATTRIBUTES = POINTER(SECURITY_ATTRIBUTES)
HCRYPTPROV = ULONG_PTR

class DATA_BLOB(Structure):
    _fields_ = [('cbData', DWORD), ('pbData', PBYTE)]

    def __init__(self, data = ''):
        self.cbData = len(data)
        d = (BYTE * self.cbData)()
        memmove(d, data, self.cbData)
        self.pbData = d
        self.d_ref = d

    def __repr__(self):
        return '%s(cbData=%r)' % (DATA_BLOB, self.pbData)

    @property
    def raw(self):
        cbuf = c_buffer(self.cbData)
        memmove(cbuf, self.pbData, self.cbData)
        return cbuf.raw


PDATA_BLOB = LPDATA_BLOB = POINTER(DATA_BLOB)

class CRYPTPROTECT_PROMPTSTRUCT(Structure):
    _fields_ = [('cbSize', DWORD),
     ('dwPromptFlags', DWORD),
     ('hwndApp', HWND),
     ('szPrompt', LPCWSTR)]


PCRYPTPROTECT_PROMPTSTRUCT = LPCRYPTPROTECT_PROMPTSTRUCT = POINTER(CRYPTPROTECT_PROMPTSTRUCT)
ACCESS_MASK = DWORD
PACCESS_MASK = POINTER(ACCESS_MASK)
HRESULT = c_long

class ACL(Structure):
    _fields_ = [('AclRevision', BYTE),
     ('Sbz1', BYTE),
     ('AclSize', WORD),
     ('AceCount', WORD),
     ('Sbz2', WORD)]


PACL = POINTER(ACL)

class SID(Structure):
    pass


PSID = POINTER(SID)
SECURITY_DESCRIPTOR_CONTROL = WORD

class SECURITY_DESCRIPTOR(Structure):
    _fields_ = [('Revision', BYTE),
     ('Sbz1', BYTE),
     ('Control', SECURITY_DESCRIPTOR_CONTROL),
     ('Owner', PSID),
     ('Group', PSID),
     ('Sacl', PACL),
     ('Dacl', PACL)]


PSECURITY_DESCRIPTOR = POINTER(SECURITY_DESCRIPTOR)

class RM_UNIQUE_PROCESS(Structure):
    _fields_ = [('dwProcessId', DWORD), ('ProcessStartTime', FILETIME)]


REGSAM = ACCESS_MASK
LCID = DWORD
SYSKIND = c_int
SYS_WIN16 = 0
SYS_WIN32 = SYS_WIN16 + 1
SYS_MAC = SYS_WIN32 + 1
SYS_WIN64 = SYS_MAC + 1
PIDLIST = c_void_p

class NOTIFYICONDATA(Structure):
    _fields_ = [('cbSize', DWORD),
     ('hWnd', HWND),
     ('uID', UINT),
     ('uFlags', UINT),
     ('uCallbackMessage', UINT),
     ('hIcon', HICON),
     ('szTip', TCHAR * 128),
     ('dwState', DWORD),
     ('dwStateMask', DWORD),
     ('szInfo', TCHAR * 256),
     ('uTimeout', UINT),
     ('szInfoTitle', TCHAR * 64),
     ('dwInfoFlags', DWORD),
     ('guidItem', GUID),
     ('hBallonIcon', HICON)]


PNOTIFYICONDATA = LPNOTIFYICONDATA = POINTER(NOTIFYICONDATA)
ABM_GETTASKBARPOS = 5

class APPBARDATA(Structure):
    _fields_ = [('cbSize', DWORD),
     ('hWnd', HWND),
     ('uCallbackMessage', UINT),
     ('uEdge', UINT),
     ('rc', RECT),
     ('lParam', LPARAM)]


PAPPBARDATA = LPAPPBARDATA = POINTER(APPBARDATA)

class NOTIFYICONIDENTIFIER(Structure):
    _fields_ = [('cbSize', DWORD),
     ('hWnd', HWND),
     ('uID', UINT),
     ('guidItem', GUID)]


PNOTIFYICONIDENTIFIER = LPNOTIFYICONIDENTIFIER = POINTER(NOTIFYICONIDENTIFIER)

class SHNAMEMAPPINGW(Structure):
    _pack_ = 1
    _fields_ = [('pszOldPath', LPWSTR),
     ('pszNewPath', LPWSTR),
     ('ccOldPath', c_int),
     ('ccNewPath', c_int)]


class HANDLETOMAPPINGS(Structure):
    _pack_ = 1
    _fields_ = [('uNumberOfMappings', c_uint), ('lpSHNameMapping', POINTER(SHNAMEMAPPINGW))]


FILEOP_FLAGS = WORD

class SHFILEOPSTRUCTW(Structure):
    _pack_ = 1
    _fields_ = [('hwnd', HWND),
     ('wFunc', UINT),
     ('pFrom', LPCWSTR),
     ('pTo', LPCWSTR),
     ('fFlags', FILEOP_FLAGS),
     ('fAnyOperationsAborted', BOOL),
     ('hNameMappings', POINTER(HANDLETOMAPPINGS)),
     ('lpszProgressTitle', LPCWSTR)]


class MENUITEMINFO(Structure):
    _fields_ = [('cbSize', UINT),
     ('fMask', UINT),
     ('fType', UINT),
     ('fState', UINT),
     ('wID', UINT),
     ('hSubMenu', HMENU),
     ('hbmpChecked', HBITMAP),
     ('hbmpUnchecked', HBITMAP),
     ('dwItemData', POINTER(ULONG)),
     ('dwTypeData', LPWSTR),
     ('cch', UINT),
     ('hbmpItem', HBITMAP)]


PMENUITEMINFO = LPMENUITEMINFO = POINTER(MENUITEMINFO)
