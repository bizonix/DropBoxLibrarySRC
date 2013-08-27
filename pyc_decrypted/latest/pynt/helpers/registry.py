#Embedded file name: pynt/helpers/registry.py
import _winreg
import struct
from contextlib import contextmanager
from ctypes import addressof, byref, c_buffer, cast, create_unicode_buffer, sizeof, wstring_at, create_string_buffer
from ctypes.wintypes import DWORD, WCHAR, HANDLE
from types import NoneType
from ..constants import ERROR_ACCESS_DENIED, ERROR_CALL_NOT_IMPLEMENTED, ERROR_FILE_NOT_FOUND, ERROR_INVALID_PARAMETER, ERROR_MORE_DATA, ERROR_NO_MORE_ITEMS, ERROR_SUCCESS, HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, HKEY_CLASSES_ROOT, INVALID_HANDLE_VALUE, KEY_ALL_ACCESS, KEY_READ, KEY_WRITE, REG_BINARY, REG_CREATED_NEW_KEY, REG_DWORD, REG_DWORD_BIG_ENDIAN, REG_DWORD_LITTLE_ENDIAN, REG_EXPAND_SZ, REG_MULTI_SZ, REG_QWORD, REG_QWORD_LITTLE_ENDIAN, REG_SZ, KEY_WOW64_64KEY
from ..dlls.advapi32 import advapi32
from ..dlls.shlwapi import shlwapi
from ..types import LPBYTE
from .general import get_sa_for_current_user, windows_error
from dropbox.functions import handle_exceptions
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption

@contextmanager
def registry_key(key, subkey, permission = KEY_READ):
    assert isinstance(subkey, unicode), 'subkey is not unicode type!'
    hkey = HANDLE(INVALID_HANDLE_VALUE)
    try:
        ret = advapi32.RegOpenKeyExW(key, subkey, 0, permission, byref(hkey))
        if ret != ERROR_SUCCESS:
            if ret == ERROR_ACCESS_DENIED:
                TRACE('!! Access denied error accessing %s', key_to_str(key, subkey))
            if ret != ERROR_FILE_NOT_FOUND and ret != ERROR_ACCESS_DENIED:
                report_bad_assumption('registry key error: %r', windows_error(ret))
            yield
        else:
            yield hkey
    finally:
        advapi32.RegCloseKey(hkey)


def enum_registry_values(hkey):
    buf = create_unicode_buffer(512)
    for i in xrange(100):
        buflen = DWORD(sizeof(buf))
        ret = advapi32.RegEnumValueW(hkey, i, buf, byref(buflen), None, None, None, None)
        if ret == ERROR_NO_MORE_ITEMS:
            break
        if ret == ERROR_SUCCESS:
            yield buf.value


def enum_registry_subkeys(hkey):
    buf = create_unicode_buffer(512)
    for i in xrange(100):
        buflen = DWORD(sizeof(buf))
        ret = advapi32.RegEnumKeyExW(hkey, i, buf, byref(buflen), None, None, None, None)
        if ret == ERROR_NO_MORE_ITEMS:
            break
        if ret == ERROR_SUCCESS:
            yield buf.value


def has_values(hkey):
    buf = create_unicode_buffer(512)
    buflen = DWORD(sizeof(buf))
    ret = advapi32.RegEnumValueW(hkey, 0, buf, byref(buflen), None, None, None, None)
    return ret != ERROR_NO_MORE_ITEMS


@contextmanager
def create_registry_key(key, subkey, permission = KEY_READ | KEY_WRITE, restrict_to_current_user = False):
    assert isinstance(subkey, unicode), 'subkey is not unicode type!'
    hkey = HANDLE(INVALID_HANDLE_VALUE)
    disp = DWORD(0)
    try:
        if restrict_to_current_user:
            with get_sa_for_current_user() as sa:
                ret = advapi32.RegCreateKeyExW(key, subkey, 0, None, 0, permission, byref(sa), byref(hkey), byref(disp))
        else:
            ret = advapi32.RegCreateKeyExW(key, subkey, 0, None, 0, permission, None, byref(hkey), byref(disp))
        if ret == ERROR_SUCCESS:
            yield (hkey, True if disp.value == REG_CREATED_NEW_KEY else False)
        else:
            report_bad_assumption('Error creating registry key %s: %r', key_to_str(key, subkey), windows_error(ret), full_stack=True)
            yield (None, False)
    finally:
        advapi32.RegCloseKey(hkey)


def _reg_key_to_python(key_type, value, length):
    if key_type in (REG_SZ, REG_EXPAND_SZ):
        retval = wstring_at(addressof(value))
    elif key_type in (REG_DWORD, REG_DWORD_LITTLE_ENDIAN):
        retval = struct.unpack('l', value[:length])[0]
    elif key_type == REG_DWORD_BIG_ENDIAN:
        retval = struct.unpack('>l', value[:length])[0]
    elif key_type in (REG_QWORD, REG_QWORD_LITTLE_ENDIAN):
        retval = struct.unpack('q', value[:length])[0]
    elif key_type == REG_BINARY:
        retval = value.raw[:length - 1]
    elif key_type == REG_MULTI_SZ:
        consumed = 0
        retval = []
        while consumed < length - 2:
            s = wstring_at(addressof(value) + consumed)
            retval.append(s)
            consumed += (len(s) + 1) * sizeof(WCHAR)

    else:
        raise TypeError("Can't unpack unknown registry key type: %r" % key_type)
    return retval


def read_registry_value(hkey, value):
    assert isinstance(value, (NoneType, unicode)), 'value is not unicode type!'
    increment_amount = 1024
    buf = create_string_buffer(512)
    casted_buf = cast(buf, LPBYTE)
    key_type = DWORD(0)
    key_length = DWORD(sizeof(buf))
    succ = advapi32.RegQueryValueExW(hkey, value, None, byref(key_type), casted_buf, byref(key_length))
    while succ == ERROR_MORE_DATA:
        buf = create_string_buffer(len(buf) + increment_amount)
        casted_buf = cast(buf, LPBYTE)
        key_length = DWORD(sizeof(buf))
        succ = advapi32.RegQueryValueExW(hkey, value, None, byref(key_type), casted_buf, byref(key_length))

    if succ == ERROR_SUCCESS:
        retval = _reg_key_to_python(key_type.value, buf, key_length.value)
    elif succ == ERROR_FILE_NOT_FOUND:
        raise KeyError(value)
    else:
        raise windows_error(succ)
    return retval


def safe_read_registry_value(hkey, value):
    try:
        return read_registry_value(hkey, value)
    except KeyError:
        TRACE('Registry value %s under key %r not found', value, hkey)
    except Exception:
        unhandled_exc_handler()


def delete_registry_value(hkey, value):
    assert isinstance(value, unicode), 'value is not unicode type!'
    return advapi32.RegDeleteValueW(hkey, value) == ERROR_SUCCESS


def delete_registry_tree(key, subkey, permission = KEY_ALL_ACCESS):
    TRACE('Delete_registry_tree %s', key_to_str(key, subkey))
    with registry_key(key, u'', permission=permission) as hkey:
        ret = advapi32.RegDeleteTreeW(hkey, subkey)
        if ret == ERROR_CALL_NOT_IMPLEMENTED:
            ret = shlwapi.SHDeleteKeyW(hkey, subkey)
        if ret != ERROR_SUCCESS and ret != ERROR_FILE_NOT_FOUND and ret != ERROR_INVALID_PARAMETER:
            raise windows_error(ret)
    return ret


def set_registry_value(hkey, name, key_type, value):
    assert isinstance(name, (NoneType, unicode)), 'name is not unicode type!'
    if key_type == REG_BINARY:
        val = c_buffer(value)
    elif key_type == REG_SZ:
        val = create_unicode_buffer(value)
    else:
        raise TypeError("Can't pack unknown registry key type: %r" % key_type)
    succ = advapi32.RegSetValueExW(hkey, name, 0, key_type, cast(val, LPBYTE), sizeof(val))
    return succ == ERROR_SUCCESS


@handle_exceptions
def delete_regkey_if_empty(key, subkey, permission = KEY_ALL_ACCESS):
    keyname = key_to_str(key, subkey)
    TRACE('Attempting to delete regkey %s', keyname)
    with registry_key(key, subkey, permission) as hkey:
        if not hkey:
            TRACE('Key %r was not present', keyname)
            return
        if not has_values(hkey):
            ret = advapi32.RegDeleteKeyW(hkey, u'')
            if ret == ERROR_SUCCESS:
                TRACE('Successfully deleted key %s', keyname)
            elif ret == ERROR_ACCESS_DENIED:
                TRACE('key %r has subkeys or we have no permission, not deleting', keyname)
            else:
                raise windows_error(ret)
        else:
            TRACE('key %r has values, not deleting', keyname)


@handle_exceptions
def safe_delete_regvalue(key, subkey, value, delete_key = False, permission = KEY_ALL_ACCESS):
    valuename = '%s\\%s' % (key_to_str(key, subkey), value)
    TRACE('Attempting to delete value %s', valuename)
    with registry_key(key, subkey, permission) as hkey:
        if not hkey:
            TRACE('%r was not present', valuename)
            return
        delete_registry_value(hkey, value)
        TRACE('Successfully deleted %s', valuename)
        if delete_key:
            delete_regkey_if_empty(key, subkey, permission)


@handle_exceptions
def safe_delete_regkey(key, subkey, permission = KEY_ALL_ACCESS):
    keyname = key_to_str(key, subkey)
    TRACE('Attempting to delete key %s', keyname)
    with registry_key(key, subkey, permission) as hkey:
        if not hkey:
            TRACE('Key %r was not present', keyname)
            return
        ret = advapi32.RegDeleteKeyW(hkey, u'')
        if ret == ERROR_SUCCESS:
            TRACE('Successfully deleted key %s', keyname)
        elif ret == ERROR_ACCESS_DENIED:
            TRACE('key %r has subkeys or we have no permission, not deleting', keyname)
        else:
            raise windows_error(ret)


def hkey_to_str(key):
    if key in (HKEY_CURRENT_USER, _winreg.HKEY_CURRENT_USER):
        return 'HKCU'
    elif key in (HKEY_LOCAL_MACHINE, _winreg.HKEY_LOCAL_MACHINE):
        return 'HKLM'
    elif key in (HKEY_CLASSES_ROOT, _winreg.HKEY_CLASSES_ROOT):
        return 'HKCR'
    else:
        return str(key)


def key_to_str(hkey, subkey):
    return '%s\\%s' % (hkey_to_str(hkey), subkey)
