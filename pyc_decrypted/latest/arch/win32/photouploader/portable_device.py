#Embedded file name: arch/win32/photouploader/portable_device.py
from comtypes.GUID import GUID
from comtypes.automation import VARIANT
from comtypes import IUnknown, COMMETHOD, BSTR
from ctypes.wintypes import LPWSTR, HRESULT, DWORD, ULONG, LPCWSTR, LONG, HANDLE, WCHAR
from ctypes import POINTER, Structure, Union, c_void_p
WIA_ITEM_TYPE_FOLDER = 4

class PROPSPEC_DUMMYUNIONNAME(Union):
    _fields_ = [('propid', ULONG), ('lpwstr', POINTER(WCHAR))]


class PROPSPEC(Structure):
    _fields_ = [('ulKind', ULONG), ('u', PROPSPEC_DUMMYUNIONNAME)]


class IWiaItem(IUnknown):
    _iid_ = GUID('{4DB1AD10-3391-11D2-9A33-00C04FA36145}')
    _idlflags_ = []


class IEnumWiaItem(IUnknown):
    _iid_ = GUID('{5E8383FC-3391-11D2-9A33-00C04FA36145}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'Next', (['in'], ULONG, 'celt'), (['in, out'], POINTER(POINTER(IWiaItem)), 'ppIWiaItem'), (['out'], POINTER(ULONG), 'pceltFetched')),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'GetCount', (['out'], POINTER(ULONG), 'celt'))]


IWiaItem._methods_ = [COMMETHOD([], HRESULT, 'GetItemType', (['out'], POINTER(LONG), 'pItemType')),
 (None,
  '',
  [],
  None,
  [],
  None),
 COMMETHOD([], HRESULT, 'EnumChildItems', (['out'], POINTER(POINTER(IEnumWiaItem)), 'ppIEnumWiaItem')),
 COMMETHOD([], HRESULT, 'DeleteItem', (['in'], LONG, 'lFlags'))]

class IWiaPropertyStorage(IUnknown):
    _iid_ = GUID('{98B5E8A0-29CC-491a-AAC0-E6DB4FDCCEB6}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'ReadMultiple', (['in'], ULONG, 'cpspec'), (['in'], POINTER(PROPSPEC), 'rgpspec'), (['in, out'], POINTER(VARIANT), 'rgpropvar')), COMMETHOD([], HRESULT, 'WriteMultiple', (['in'], ULONG, 'cpspec'), (['in'], POINTER(PROPSPEC), 'rgpspec'), (['in'], POINTER(VARIANT), 'rgpropvar'), (['in'], ULONG, 'propidNameFirst'))]


class IWiaDevMgr(IUnknown):
    _iid_ = GUID('{5EB2502A-8CF1-11D1-BF92-0060081ED811}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'CreateDevice', (['in'], BSTR, 'bstrDeviceID'), (['out'], POINTER(POINTER(IWiaItem)), 'ppWiaItemRoot')),
     COMMETHOD([], HRESULT, 'SelectDeviceDlg', (['in'], HANDLE, 'hwndParent'), (['in'], LONG, 'lDeviceType'), (['in'], LONG, 'lFlags'), (['in, out'], POINTER(BSTR), 'pbstrDeviceID'), (['out'], POINTER(POINTER(IWiaItem)), 'ppItemRoot')),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'RegisterEventCallbackProgram', (['in'], LONG, 'lFlags'), (['in'], BSTR, 'bstrDeviceID'), (['in'], POINTER(GUID), 'pEventGUID'), (['in'], BSTR, 'bstrCommandline'), (['in'], BSTR, 'bstrName'), (['in'], BSTR, 'bstrDescription'), (['in'], BSTR, 'bstrIcon')),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'RegisterEventCallbackCLSID', (['in'], LONG, 'lFlags'), (['in'], BSTR, 'bstrDeviceID'), (['in'], POINTER(GUID), 'pEventGUID'), (['in'], POINTER(GUID), 'pClsID'), (['in'], BSTR, 'bstrName'), (['in'], BSTR, 'bstrDescription'), (['in'], BSTR, 'bstrIcon'))]


class PROPERTYKEY(Structure):
    _fields_ = [('fmtid', GUID), ('pid', DWORD)]


class IPortableDeviceValues(IUnknown):
    _iid_ = GUID('{6848f6f2-3155-4f86-b6f5-263eeeab3143}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'GetValue', (['in'], POINTER(PROPERTYKEY), 'key'), (['out'], POINTER(VARIANT), 'pValue')),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'GetStringValue', (['in'], POINTER(PROPERTYKEY), 'key'), (['out'], POINTER(LPWSTR), 'pValue')),
     COMMETHOD([], HRESULT, 'SetUnsignedIntegerValue', (['in'], POINTER(PROPERTYKEY), 'key'), (['in'], ULONG, 'Value')),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'GetGuidValue', (['in'], POINTER(PROPERTYKEY), 'key'), (['out'], POINTER(GUID), 'pValue'))]


class IEnumPortableDeviceObjectIDs(IUnknown):
    _iid_ = GUID('{10ece955-cf41-4728-bfa0-41eedf1bbf19}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'Next', (['in'], ULONG, 'cObjects'), (['in, out'], POINTER(LPWSTR), 'pObjIDs'), (['out'], POINTER(ULONG), 'pcFetched'))]


class IPortableDeviceProperties(IUnknown):
    _iid_ = GUID('{7f6d695c-03df-4439-a809-59266beee3a6}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None), (None,
      '',
      [],
      None,
      [],
      None), COMMETHOD([], HRESULT, 'GetValues', (['in'], LPCWSTR, 'pszObjectID'), (['in, optional'], POINTER(IUnknown), 'pKeys'), (['out'], POINTER(POINTER(IPortableDeviceValues)), 'ppValues'))]


class IStream(IUnknown):
    _iid_ = GUID('{0000000c-0000-0000-C000-000000000046}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'Read', (['in'], c_void_p, 'pv'), (['in'], ULONG, 'cb'), (['out'], POINTER(ULONG), 'pcbRead'))]


class IPortableDeviceResources(IUnknown):
    _iid_ = GUID('{fd8878ac-d841-4d17-891c-e6829cdb6934}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None), (None,
      '',
      [],
      None,
      [],
      None), COMMETHOD([], HRESULT, 'GetStream', (['in'], LPCWSTR, 'pszObjectID'), (['in'], POINTER(PROPERTYKEY), 'Key'), (['in'], DWORD, 'dwMode'), (['out'], POINTER(DWORD), 'pdwOptimalBufferSize'), (['out'], POINTER(POINTER(IStream)), 'ppStream'))]


class IPortableDevicePropVariantCollection(IUnknown):
    _iid_ = GUID('{89b2e422-4f1b-4316-bcef-a44afea83eb3}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'GetCount', (['out'], POINTER(DWORD), 'pcElems')), COMMETHOD([], HRESULT, 'GetAt', (['in'], DWORD, 'dwIndex'), (['out'], POINTER(VARIANT), 'pValue')), COMMETHOD([], HRESULT, 'Add', (['in'], POINTER(VARIANT), 'pValue'))]


class IPortableDeviceContent(IUnknown):
    _iid_ = GUID('{6a96ed84-7c73-4480-9938-bf5af477d426}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'EnumObjects', (['in'], DWORD, 'dwFlags'), (['in'], LPCWSTR, 'pszParentObjectID'), (['in'], POINTER(IPortableDeviceValues), 'pFilter'), (['out'], POINTER(POINTER(IEnumPortableDeviceObjectIDs)), 'ppEnum')),
     COMMETHOD([], HRESULT, 'Properties', (['out'], POINTER(POINTER(IPortableDeviceProperties)), 'ppProperties')),
     COMMETHOD([], HRESULT, 'Transfer', (['out'], POINTER(POINTER(IPortableDeviceResources)), 'ppResources')),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'Delete', (['in'], DWORD, 'dwOptions'), (['in'], POINTER(IPortableDevicePropVariantCollection), 'pObjectIDs'), (['in, optional'], POINTER(POINTER(IUnknown)), 'ppResultsUnused'))]


class IPortableDevice(IUnknown):
    _iid_ = GUID('{625e2df8-6392-4cf0-9ad1-3cfa5f17775c}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'Open', (['in'], LPWSTR, 'pszPnpDeviceID'), (['in'], POINTER(IPortableDeviceValues), 'pClientInfo')), (None,
      '',
      [],
      None,
      [],
      None), COMMETHOD([], HRESULT, 'Content', (['out'], POINTER(POINTER(IPortableDeviceContent)), 'ppContent'))]
