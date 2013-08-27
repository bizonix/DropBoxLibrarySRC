#Embedded file name: pynt/helpers/com.py
from ctypes import byref, POINTER, Structure, c_ulong, c_ushort, cast
from comtypes import COMError, IUnknown
from comtypes.automation import VARIANT, VT_VECTOR, VT_UI2
from comtypes.GUID import GUID
import datetime
from dropbox.functions import handle_exceptions
from dropbox.trace import TRACE, unhandled_exc_handler
from ..types import SYS_WIN32
from ..dlls.ole32 import ole32
from ..dlls.oleaut32 import oleaut32
from ..constants import S_OK

def register_tlb(tlb_path, this_user_only):
    ptypelib = POINTER(IUnknown)()
    hresult = oleaut32.LoadTypeLib(tlb_path, byref(ptypelib))
    if hresult != S_OK:
        raise COMError(hresult, "Couldn't load type library!", None)
    reg_func = oleaut32.RegisterTypeLibForUser if this_user_only else oleaut32.RegisterTypeLib
    hresult = reg_func(ptypelib, tlb_path, None)
    if hresult != S_OK:
        raise COMError(hresult, 'Failed to register type library!', None)


def unregister_tlb(str_lib_id, major_version_number, minor_version_number, this_user_only = True):
    guid = GUID(str_lib_id)
    if this_user_only:
        unreg_func = oleaut32.UnRegisterTypeLibForUser
    else:
        unreg_func = oleaut32.UnRegisterTypeLib
    hresult = unreg_func(byref(guid), major_version_number, minor_version_number, 0, SYS_WIN32)
    if hresult != S_OK:
        raise COMError(hresult, 'Failed to unregister type library!', None)


class tagCAUI(Structure):
    _fields_ = [('cElems', c_ulong), ('pElems', POINTER(c_ushort))]


class PROPVARIANT(VARIANT):

    def __del__(self):
        if self._b_needsfree_:
            ole32.PropVariantClear(cast(byref(self), POINTER(VARIANT)))


def datetime_from_var_date(var):
    try:
        if var.vt & VT_VECTOR and var.vt & ~VT_VECTOR == VT_UI2:
            caui = cast(byref(var._), POINTER(tagCAUI)).contents
            systemtime = [ caui.pElems[i] for i in xrange(caui.cElems) ]
            del systemtime[2]
            systemtime[-1] *= 1000
            return datetime.datetime(*systemtime)
        raise 'Item date returned unexpected type!'
    except Exception:
        TRACE('!! WIA item date returned an unexpected type!  Expected: %r, got: %r', VT_VECTOR | VT_UI2, var.vt)
        unhandled_exc_handler()
