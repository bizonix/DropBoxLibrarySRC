#Embedded file name: pynt/helpers/general.py
from __future__ import absolute_import
import struct
from contextlib import contextmanager
from ctypes import addressof, byref, cast, sizeof, memmove
from ctypes.wintypes import HLOCAL, LPCWSTR, BOOL
from ..constants import ERROR_SUCCESS, KEY_READ, KEY_WRITE, FORMAT_MESSAGE_ALLOCATE_BUFFER, FORMAT_MESSAGE_FROM_SYSTEM, FORMAT_MESSAGE_IGNORE_INSERTS, LANG_US_ENGLISH, NO_INHERITANCE, SECURITY_DESCRIPTOR_REVISION
from ..dlls.advapi32 import advapi32
from ..dlls.kernel32 import kernel32
from ..dlls.dwmapi import dwmapi
from ..trace import TRACE
from ..types import BYTE, EXPLICIT_ACCESSW, LPVOID, PACL, SECURITY_ATTRIBUTES, SECURITY_DESCRIPTOR, SET_ACCESS

def create_byte_buffer(size):
    return (BYTE * size)()


def format_message(err, language = 0):
    buf = LPCWSTR()
    succ = kernel32.FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, None, err, language, cast(byref(buf), LPCWSTR), 0, None)
    if not succ:
        return
    retval = buf.value
    local_free_ret = kernel32.LocalFree(buf)
    if local_free_ret:
        TRACE('!! LocalFree on buffer returned from FormatMessageW failed, leaking memory! (Errno: %d)', kernel32.GetLastError())
    return retval


class FormattedWindowsError(WindowsError):

    def __init__(self, unsigned_err, *n):
        signed_err = unsigned_err
        if signed_err >= 2147483648L:
            signed_err -= 4294967296L
        super(FormattedWindowsError, self).__init__(signed_err, *n)
        self.unsigned_err = unsigned_err

    def __str__(self):
        extra = ''
        if len(self.args) >= 3 and self.args[2] is not None:
            extra = ': %r' % self.args[2]
        error_code_fmt = '%d' if self.unsigned_err < 16000 else '0x%08x'
        error_code_str = error_code_fmt % (self.unsigned_err,)
        return '[Error %s] %s%s' % (error_code_str, self.args[1], extra)


def windows_error(err = None, filename = None):
    if err is None:
        err = kernel32.GetLastError()
    message = format_message(err, LANG_US_ENGLISH)
    if message is None:
        message = format_message(err)
    if message is None:
        message = u''
    return FormattedWindowsError(err, message.encode('utf8'), filename)


def windows_error_check(result, func, args):
    if result == ERROR_SUCCESS:
        return
    raise windows_error(result)


def windows_null_check(result, func, args):
    if not result:
        raise windows_error()


STANDARD_RIGHTS_REQUIRED = 983040
SPECIFIC_RIGHTS_ALL = 65535

@contextmanager
def get_sa_for_current_user():
    security_desc = SECURITY_DESCRIPTOR()
    succ = advapi32.InitializeSecurityDescriptor(byref(security_desc), SECURITY_DESCRIPTOR_REVISION)
    if not succ:
        TRACE('!! Error calling InitializeSecurityDescriptor')
        yield
        return
    ea = EXPLICIT_ACCESSW()
    advapi32.BuildExplicitAccessWithNameW(byref(ea), u'CURRENT_USER', STANDARD_RIGHTS_REQUIRED | SPECIFIC_RIGHTS_ALL, SET_ACCESS, NO_INHERITANCE)
    pacl = PACL()
    retval = advapi32.SetEntriesInAclW(1, byref(ea), None, byref(pacl))
    if retval != ERROR_SUCCESS:
        TRACE('!! SetEntriesInAclW')
        yield
        return
    try:
        succ = advapi32.SetSecurityDescriptorDacl(byref(security_desc), True, pacl, False)
        if not succ:
            TRACE('!! SetSecurityDescriptorDacl')
            yield
            return
        sa = SECURITY_ATTRIBUTES()
        sa.nLength = sizeof(SECURITY_ATTRIBUTES)
        sa.lpSecurityDescriptor = addressof(security_desc)
        sa.bInheritHandle = False
        yield sa
    finally:
        kernel32.LocalFree(pacl)


def IsDWMEnabled():
    result = BOOL()
    if dwmapi.DwmIsCompositionEnabled(byref(result)):
        TRACE('!! Failed to determine whether DWM is running.')
        return False
    return bool(result)
