#Embedded file name: pynt/helpers/crypt.py
from __future__ import absolute_import
from ctypes import byref, create_unicode_buffer
from .general import windows_error
from ..constants import CRYPTPROTECT_UI_FORBIDDEN
from ..dlls.crypt32 import crypt32
from ..dlls.kernel32 import kernel32
from ..types import DATA_BLOB

def protect_data(data, extra_entropy = None):
    data_in = DATA_BLOB(data)
    data_desc = create_unicode_buffer('')
    data_out = DATA_BLOB()
    if extra_entropy:
        ent_data = DATA_BLOB(extra_entropy)
    succ = crypt32.CryptProtectData(byref(data_in), data_desc, byref(ent_data) if extra_entropy else None, None, None, CRYPTPROTECT_UI_FORBIDDEN, byref(data_out))
    if not succ:
        raise windows_error()
    ret = data_out.raw
    kernel32.LocalFree(data_out.pbData)
    return ret


def unprotect_data(data, extra_entropy = None):
    data_in = DATA_BLOB(data)
    data_desc = create_unicode_buffer('')
    data_out = DATA_BLOB()
    if extra_entropy:
        ent_data = DATA_BLOB(extra_entropy)
    succ = crypt32.CryptUnprotectData(byref(data_in), data_desc, byref(ent_data) if extra_entropy else None, None, None, CRYPTPROTECT_UI_FORBIDDEN, byref(data_out))
    if not succ:
        raise windows_error()
    ret = data_out.raw
    kernel32.LocalFree(data_out.pbData)
    return ret
