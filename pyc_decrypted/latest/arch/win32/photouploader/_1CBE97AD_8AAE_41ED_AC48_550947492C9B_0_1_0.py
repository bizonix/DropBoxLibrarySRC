#Embedded file name: arch/win32/photouploader/_1CBE97AD_8AAE_41ED_AC48_550947492C9B_0_1_0.py
_lcid = 0
from ctypes import *
from ctypes.wintypes import _ULARGE_INTEGER, WORD, DWORD, ULONG
from ctypes.wintypes import _FILETIME
import _00020430_0000_0000_C000_000000000046_0_2_0
WSTRING = c_wchar_p
from comtypes import IPersist
from comtypes import GUID
from comtypes import BSTR
from ctypes.wintypes import _POINTL
from ctypes import HRESULT
from comtypes import helpstring
from comtypes import COMMETHOD
from comtypes import dispid
from comtypes import _COAUTHINFO
from comtypes import IUnknown
from comtypes import tagBIND_OPTS2
from ctypes.wintypes import _LARGE_INTEGER
from comtypes import _COAUTHIDENTITY
from comtypes import tagBIND_OPTS2
from comtypes import _COSERVERINFO
from comtypes import CoClass

class tagFORMATETC(Structure):
    pass


class _userCLIPFORMAT(Structure):
    pass


wireCLIPFORMAT = POINTER(_userCLIPFORMAT)

class tagDVTARGETDEVICE(Structure):
    pass


tagFORMATETC._fields_ = [('cfFormat', WORD),
 ('ptd', POINTER(tagDVTARGETDEVICE)),
 ('dwAspect', c_ulong),
 ('lindex', c_int),
 ('tymed', c_ulong)]
assert sizeof(tagFORMATETC) == 20, sizeof(tagFORMATETC)
assert alignment(tagFORMATETC) == 4, alignment(tagFORMATETC)

class tagSTATSTG(Structure):
    pass


tagSTATSTG._fields_ = [('pwcsName', WSTRING),
 ('type', c_ulong),
 ('cbSize', _ULARGE_INTEGER),
 ('mtime', _FILETIME),
 ('ctime', _FILETIME),
 ('atime', _FILETIME),
 ('grfMode', c_ulong),
 ('grfLocksSupported', c_ulong),
 ('clsid', _00020430_0000_0000_C000_000000000046_0_2_0.GUID),
 ('grfStateBits', c_ulong),
 ('reserved', c_ulong)]
assert sizeof(tagSTATSTG) == 72, sizeof(tagSTATSTG)
assert alignment(tagSTATSTG) == 8, alignment(tagSTATSTG)

class __MIDL_IWinTypes_0006(Union):
    pass


class _BYTE_BLOB(Structure):
    pass


__MIDL_IWinTypes_0006._fields_ = [('hInproc', c_int), ('hRemote', POINTER(_BYTE_BLOB)), ('hInproc64', c_longlong)]
assert sizeof(__MIDL_IWinTypes_0006) == 8, sizeof(__MIDL_IWinTypes_0006)
assert alignment(__MIDL_IWinTypes_0006) == 8, alignment(__MIDL_IWinTypes_0006)

class IDropTarget(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{00000122-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IDataObject(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{0000010E-0000-0000-C000-000000000046}')
    _idlflags_ = []


IDropTarget._methods_ = [COMMETHOD([], HRESULT, 'DragEnter', (['in'], POINTER(IDataObject), 'pDataObj'), (['in'], c_ulong, 'grfKeyState'), (['in'], _POINTL, 'pt'), (['in', 'out'], POINTER(c_ulong), 'pdwEffect')),
 COMMETHOD([], HRESULT, 'DragOver', (['in'], c_ulong, 'grfKeyState'), (['in'], _POINTL, 'pt'), (['in', 'out'], POINTER(c_ulong), 'pdwEffect')),
 COMMETHOD([], HRESULT, 'DragLeave'),
 COMMETHOD([], HRESULT, 'Drop', (['in'], POINTER(IDataObject), 'pDataObj'), (['in'], c_ulong, 'grfKeyState'), (['in'], _POINTL, 'pt'), (['in', 'out'], POINTER(c_ulong), 'pdwEffect'))]

class IBindCtx(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{0000000E-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IRunningObjectTable(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{00000010-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IEnumString(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{00000101-0000-0000-C000-000000000046}')
    _idlflags_ = []


IBindCtx._methods_ = [COMMETHOD([], HRESULT, 'RegisterObjectBound', (['in'], POINTER(IUnknown), 'punk')),
 COMMETHOD([], HRESULT, 'RevokeObjectBound', (['in'], POINTER(IUnknown), 'punk')),
 COMMETHOD([], HRESULT, 'ReleaseBoundObjects'),
 COMMETHOD([], HRESULT, 'RemoteSetBindOptions', (['in'], POINTER(tagBIND_OPTS2), 'pbindopts')),
 COMMETHOD([], HRESULT, 'RemoteGetBindOptions', (['in', 'out'], POINTER(tagBIND_OPTS2), 'pbindopts')),
 COMMETHOD([], HRESULT, 'GetRunningObjectTable', (['out'], POINTER(POINTER(IRunningObjectTable)), 'pprot')),
 COMMETHOD([], HRESULT, 'RegisterObjectParam', (['in'], WSTRING, 'pszKey'), (['in'], POINTER(IUnknown), 'punk')),
 COMMETHOD([], HRESULT, 'GetObjectParam', (['in'], WSTRING, 'pszKey'), (['out'], POINTER(POINTER(IUnknown)), 'ppunk')),
 COMMETHOD([], HRESULT, 'EnumObjectParam', (['out'], POINTER(POINTER(IEnumString)), 'ppenum')),
 COMMETHOD([], HRESULT, 'RevokeObjectParam', (['in'], WSTRING, 'pszKey'))]

class _remoteMETAFILEPICT(Structure):
    pass


class _userHMETAFILE(Structure):
    pass


_remoteMETAFILEPICT._fields_ = [('mm', c_int),
 ('xExt', c_int),
 ('yExt', c_int),
 ('hMF', POINTER(_userHMETAFILE))]
assert sizeof(_remoteMETAFILEPICT) == 16, sizeof(_remoteMETAFILEPICT)
assert alignment(_remoteMETAFILEPICT) == 4, alignment(_remoteMETAFILEPICT)

class ISequentialStream(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{0C733A30-2A1C-11CE-ADE5-00AA0044773D}')
    _idlflags_ = []


ISequentialStream._methods_ = [COMMETHOD([], HRESULT, 'RemoteRead', (['out'], POINTER(c_ubyte), 'pv'), (['in'], c_ulong, 'cb'), (['out'], POINTER(c_ulong), 'pcbRead')), COMMETHOD([], HRESULT, 'RemoteWrite', (['in'], POINTER(c_ubyte), 'pv'), (['in'], c_ulong, 'cb'), (['out'], POINTER(c_ulong), 'pcbWritten'))]

class tagLOGPALETTE(Structure):
    pass


class tagPALETTEENTRY(Structure):
    pass


tagLOGPALETTE._pack_ = 2
tagLOGPALETTE._fields_ = [('palVersion', c_ushort), ('palNumEntries', c_ushort), ('palPalEntry', POINTER(tagPALETTEENTRY))]
assert sizeof(tagLOGPALETTE) == 8, sizeof(tagLOGPALETTE)
assert alignment(tagLOGPALETTE) == 2, alignment(tagLOGPALETTE)

class _userBITMAP(Structure):
    pass


_userBITMAP._fields_ = [('bmType', c_int),
 ('bmWidth', c_int),
 ('bmHeight', c_int),
 ('bmWidthBytes', c_int),
 ('bmPlanes', c_ushort),
 ('bmBitsPixel', c_ushort),
 ('cbSize', c_ulong),
 ('pBuffer', POINTER(c_ubyte))]
assert sizeof(_userBITMAP) == 28, sizeof(_userBITMAP)
assert alignment(_userBITMAP) == 4, alignment(_userBITMAP)

class _userHMETAFILEPICT(Structure):
    pass


class __MIDL_IWinTypes_0005(Union):
    pass


__MIDL_IWinTypes_0005._fields_ = [('hInproc', c_int), ('hRemote', POINTER(_remoteMETAFILEPICT)), ('hInproc64', c_longlong)]
assert sizeof(__MIDL_IWinTypes_0005) == 8, sizeof(__MIDL_IWinTypes_0005)
assert alignment(__MIDL_IWinTypes_0005) == 8, alignment(__MIDL_IWinTypes_0005)
_userHMETAFILEPICT._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0005)]
assert sizeof(_userHMETAFILEPICT) == 16, sizeof(_userHMETAFILEPICT)
assert alignment(_userHMETAFILEPICT) == 8, alignment(_userHMETAFILEPICT)

class IEnumMoniker(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{00000102-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IPersistStream(IPersist):
    _case_insensitive_ = True
    _iid_ = GUID('{00000109-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IMoniker(IPersistStream):
    _case_insensitive_ = True
    _iid_ = GUID('{0000000F-0000-0000-C000-000000000046}')
    _idlflags_ = []


IEnumMoniker._methods_ = [COMMETHOD([], HRESULT, 'RemoteNext', (['in'], c_ulong, 'celt'), (['out'], POINTER(POINTER(IMoniker)), 'rgelt'), (['out'], POINTER(c_ulong), 'pceltFetched')),
 COMMETHOD([], HRESULT, 'Skip', (['in'], c_ulong, 'celt')),
 COMMETHOD([], HRESULT, 'Reset'),
 COMMETHOD([], HRESULT, 'Clone', (['out'], POINTER(POINTER(IEnumMoniker)), 'ppenum'))]

class _userSTGMEDIUM(Structure):
    pass


wireSTGMEDIUM = POINTER(_userSTGMEDIUM)

class _STGMEDIUM_UNION(Structure):
    pass


class __MIDL_IAdviseSink_0003(Union):
    pass


class _userHENHMETAFILE(Structure):
    pass


class _GDI_OBJECT(Structure):
    pass


class _userHGLOBAL(Structure):
    pass


__MIDL_IAdviseSink_0003._fields_ = [('hMetaFilePict', POINTER(_userHMETAFILEPICT)),
 ('hHEnhMetaFile', POINTER(_userHENHMETAFILE)),
 ('hGdiHandle', POINTER(_GDI_OBJECT)),
 ('hGlobal', POINTER(_userHGLOBAL)),
 ('lpszFileName', WSTRING),
 ('pstm', POINTER(_BYTE_BLOB)),
 ('pstg', POINTER(_BYTE_BLOB))]
assert sizeof(__MIDL_IAdviseSink_0003) == 4, sizeof(__MIDL_IAdviseSink_0003)
assert alignment(__MIDL_IAdviseSink_0003) == 4, alignment(__MIDL_IAdviseSink_0003)
_STGMEDIUM_UNION._fields_ = [('tymed', c_ulong), ('u', __MIDL_IAdviseSink_0003)]
assert sizeof(_STGMEDIUM_UNION) == 8, sizeof(_STGMEDIUM_UNION)
assert alignment(_STGMEDIUM_UNION) == 4, alignment(_STGMEDIUM_UNION)
_userSTGMEDIUM._fields_ = [('DUMMYUNIONNAME', _STGMEDIUM_UNION), ('pUnkForRelease', POINTER(IUnknown))]
assert sizeof(_userSTGMEDIUM) == 12, sizeof(_userSTGMEDIUM)
assert alignment(_userSTGMEDIUM) == 4, alignment(_userSTGMEDIUM)

class __MIDL_IWinTypes_0008(Union):
    pass


__MIDL_IWinTypes_0008._fields_ = [('hInproc', c_int), ('hRemote', POINTER(tagLOGPALETTE)), ('hInproc64', c_longlong)]
assert sizeof(__MIDL_IWinTypes_0008) == 8, sizeof(__MIDL_IWinTypes_0008)
assert alignment(__MIDL_IWinTypes_0008) == 8, alignment(__MIDL_IWinTypes_0008)

class __MIDL_IAdviseSink_0002(Union):
    pass


class _userHBITMAP(Structure):
    pass


class _userHPALETTE(Structure):
    pass


__MIDL_IAdviseSink_0002._fields_ = [('hBitmap', POINTER(_userHBITMAP)), ('hPalette', POINTER(_userHPALETTE)), ('hGeneric', POINTER(_userHGLOBAL))]
assert sizeof(__MIDL_IAdviseSink_0002) == 4, sizeof(__MIDL_IAdviseSink_0002)
assert alignment(__MIDL_IAdviseSink_0002) == 4, alignment(__MIDL_IAdviseSink_0002)

class _userFLAG_STGMEDIUM(Structure):
    pass


wireFLAG_STGMEDIUM = POINTER(_userFLAG_STGMEDIUM)

class IEnumFORMATETC(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{00000103-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IAdviseSink(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{0000010F-0000-0000-C000-000000000046}')
    _idlflags_ = []


class IEnumSTATDATA(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{00000105-0000-0000-C000-000000000046}')
    _idlflags_ = []


IDataObject._methods_ = [COMMETHOD([], HRESULT, 'GetData', (['in'], POINTER(tagFORMATETC), 'pformatetcIn'), (['out'], POINTER(_userSTGMEDIUM), 'pRemoteMedium')),
 COMMETHOD([], HRESULT, 'GetDataHere', (['in'], POINTER(tagFORMATETC), 'pformatetc'), (['in', 'out'], POINTER(wireSTGMEDIUM), 'pRemoteMedium')),
 COMMETHOD([], HRESULT, 'QueryGetData', (['in'], POINTER(tagFORMATETC), 'pformatetc')),
 COMMETHOD([], HRESULT, 'GetCanonicalFormatEtc', (['in'], POINTER(tagFORMATETC), 'pformatectIn'), (['out'], POINTER(tagFORMATETC), 'pformatetcOut')),
 COMMETHOD([], HRESULT, 'SetData', (['in'], POINTER(tagFORMATETC), 'pformatetc'), (['in'], POINTER(wireFLAG_STGMEDIUM), 'pmedium'), (['in'], c_int, 'fRelease')),
 COMMETHOD([], HRESULT, 'EnumFormatEtc', (['in'], c_ulong, 'dwDirection'), (['out'], POINTER(POINTER(IEnumFORMATETC)), 'ppenumFormatEtc')),
 COMMETHOD([], HRESULT, 'DAdvise', (['in'], POINTER(tagFORMATETC), 'pformatetc'), (['in'], c_ulong, 'advf'), (['in'], POINTER(IAdviseSink), 'pAdvSink'), (['out'], POINTER(c_ulong), 'pdwConnection')),
 COMMETHOD([], HRESULT, 'DUnadvise', (['in'], c_ulong, 'dwConnection')),
 COMMETHOD([], HRESULT, 'EnumDAdvise', (['out'], POINTER(POINTER(IEnumSTATDATA)), 'ppenumAdvise'))]
_userHENHMETAFILE._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0006)]
assert sizeof(_userHENHMETAFILE) == 16, sizeof(_userHENHMETAFILE)
assert alignment(_userHENHMETAFILE) == 8, alignment(_userHENHMETAFILE)
_GDI_OBJECT._fields_ = [('ObjectType', c_ulong), ('u', __MIDL_IAdviseSink_0002)]
assert sizeof(_GDI_OBJECT) == 8, sizeof(_GDI_OBJECT)
assert alignment(_GDI_OBJECT) == 4, alignment(_GDI_OBJECT)

class __MIDL_IWinTypes_0004(Union):
    pass


__MIDL_IWinTypes_0004._fields_ = [('hInproc', c_int), ('hRemote', POINTER(_BYTE_BLOB)), ('hInproc64', c_longlong)]
assert sizeof(__MIDL_IWinTypes_0004) == 8, sizeof(__MIDL_IWinTypes_0004)
assert alignment(__MIDL_IWinTypes_0004) == 8, alignment(__MIDL_IWinTypes_0004)
_userHMETAFILE._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0004)]
assert sizeof(_userHMETAFILE) == 16, sizeof(_userHMETAFILE)
assert alignment(_userHMETAFILE) == 8, alignment(_userHMETAFILE)

class Library(object):
    name = u'PhotoUploaderLib'
    _reg_typelib_ = ('{1CBE97AD-8AAE-41ED-AC48-550947492C9B}', 1, 0)


IRunningObjectTable._methods_ = [COMMETHOD([], HRESULT, 'Register', (['in'], c_ulong, 'grfFlags'), (['in'], POINTER(IUnknown), 'punkObject'), (['in'], POINTER(IMoniker), 'pmkObjectName'), (['out'], POINTER(c_ulong), 'pdwRegister')),
 COMMETHOD([], HRESULT, 'Revoke', (['in'], c_ulong, 'dwRegister')),
 COMMETHOD([], HRESULT, 'IsRunning', (['in'], POINTER(IMoniker), 'pmkObjectName')),
 COMMETHOD([], HRESULT, 'GetObject', (['in'], POINTER(IMoniker), 'pmkObjectName'), (['out'], POINTER(POINTER(IUnknown)), 'ppunkObject')),
 COMMETHOD([], HRESULT, 'NoteChangeTime', (['in'], c_ulong, 'dwRegister'), (['in'], POINTER(_FILETIME), 'pfiletime')),
 COMMETHOD([], HRESULT, 'GetTimeOfLastChange', (['in'], POINTER(IMoniker), 'pmkObjectName'), (['out'], POINTER(_FILETIME), 'pfiletime')),
 COMMETHOD([], HRESULT, 'EnumRunning', (['out'], POINTER(POINTER(IEnumMoniker)), 'ppenumMoniker'))]

class IWiaEventCallback(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{AE6287B0-0084-11D2-973B-00A0C9068F2E}')
    _idlflags_ = []


IWiaEventCallback._methods_ = [COMMETHOD([], HRESULT, 'ImageEventCallback', (['in'], POINTER(GUID), 'pEventGUID'), (['in'], BSTR, 'bstrEventDescription'), (['in'], BSTR, 'bstrDeviceID'), (['in'], BSTR, 'bstrDeviceDescription'), (['in'], DWORD, 'dwDeviceType'), (['in'], BSTR, 'bstrFullItemName'), (['in'], POINTER(ULONG), 'pulEventType'), (['in'], ULONG, 'ulReserved'))]

class IHWEventHandler(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{C1FB73D0-EC3A-4BA2-B512-8CDB9187B6D1}')
    _idlflags_ = []


IHWEventHandler._methods_ = [COMMETHOD([], HRESULT, 'Initialize', (['in'], WSTRING, 'pszParams')), COMMETHOD([], HRESULT, 'HandleEvent', (['in'], WSTRING, 'pszDeviceID'), (['in'], WSTRING, 'pszAltDeviceID'), (['in'], WSTRING, 'pszEventType')), COMMETHOD([], HRESULT, 'HandleEventWithContent', (['in'], WSTRING, 'pszDeviceID'), (['in'], WSTRING, 'pszAltDeviceID'), (['in'], WSTRING, 'pszEventType'), (['in'], WSTRING, 'pszContentTypeHandler'), (['in'], POINTER(IDataObject), 'pdataobject'))]
_BYTE_BLOB._fields_ = [('clSize', c_ulong), ('abData', POINTER(c_ubyte))]
assert sizeof(_BYTE_BLOB) == 8, sizeof(_BYTE_BLOB)
assert alignment(_BYTE_BLOB) == 4, alignment(_BYTE_BLOB)
IEnumFORMATETC._methods_ = [COMMETHOD([], HRESULT, 'RemoteNext', (['in'], c_ulong, 'celt'), (['out'], POINTER(tagFORMATETC), 'rgelt'), (['out'], POINTER(c_ulong), 'pceltFetched')),
 COMMETHOD([], HRESULT, 'Skip', (['in'], c_ulong, 'celt')),
 COMMETHOD([], HRESULT, 'Reset'),
 COMMETHOD([], HRESULT, 'Clone', (['out'], POINTER(POINTER(IEnumFORMATETC)), 'ppenum'))]

class IStream(ISequentialStream):
    _case_insensitive_ = True
    _iid_ = GUID('{0000000C-0000-0000-C000-000000000046}')
    _idlflags_ = []


IStream._methods_ = [COMMETHOD([], HRESULT, 'RemoteSeek', (['in'], _LARGE_INTEGER, 'dlibMove'), (['in'], c_ulong, 'dwOrigin'), (['out'], POINTER(_ULARGE_INTEGER), 'plibNewPosition')),
 COMMETHOD([], HRESULT, 'SetSize', (['in'], _ULARGE_INTEGER, 'libNewSize')),
 COMMETHOD([], HRESULT, 'RemoteCopyTo', (['in'], POINTER(IStream), 'pstm'), (['in'], _ULARGE_INTEGER, 'cb'), (['out'], POINTER(_ULARGE_INTEGER), 'pcbRead'), (['out'], POINTER(_ULARGE_INTEGER), 'pcbWritten')),
 COMMETHOD([], HRESULT, 'Commit', (['in'], c_ulong, 'grfCommitFlags')),
 COMMETHOD([], HRESULT, 'Revert'),
 COMMETHOD([], HRESULT, 'LockRegion', (['in'], _ULARGE_INTEGER, 'libOffset'), (['in'], _ULARGE_INTEGER, 'cb'), (['in'], c_ulong, 'dwLockType')),
 COMMETHOD([], HRESULT, 'UnlockRegion', (['in'], _ULARGE_INTEGER, 'libOffset'), (['in'], _ULARGE_INTEGER, 'cb'), (['in'], c_ulong, 'dwLockType')),
 COMMETHOD([], HRESULT, 'Stat', (['out'], POINTER(tagSTATSTG), 'pstatstg'), (['in'], c_ulong, 'grfStatFlag')),
 COMMETHOD([], HRESULT, 'Clone', (['out'], POINTER(POINTER(IStream)), 'ppstm'))]

class __MIDL_IWinTypes_0001(Union):
    pass


__MIDL_IWinTypes_0001._fields_ = [('dwValue', c_ulong), ('pwszName', WSTRING)]
assert sizeof(__MIDL_IWinTypes_0001) == 4, sizeof(__MIDL_IWinTypes_0001)
assert alignment(__MIDL_IWinTypes_0001) == 4, alignment(__MIDL_IWinTypes_0001)
_userCLIPFORMAT._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0001)]
assert sizeof(_userCLIPFORMAT) == 8, sizeof(_userCLIPFORMAT)
assert alignment(_userCLIPFORMAT) == 4, alignment(_userCLIPFORMAT)
tagDVTARGETDEVICE._fields_ = [('tdSize', c_ulong),
 ('tdDriverNameOffset', c_ushort),
 ('tdDeviceNameOffset', c_ushort),
 ('tdPortNameOffset', c_ushort),
 ('tdExtDevmodeOffset', c_ushort),
 ('tdData', POINTER(c_ubyte))]
assert sizeof(tagDVTARGETDEVICE) == 16, sizeof(tagDVTARGETDEVICE)
assert alignment(tagDVTARGETDEVICE) == 4, alignment(tagDVTARGETDEVICE)

class tagSTATDATA(Structure):
    pass


IEnumSTATDATA._methods_ = [COMMETHOD([], HRESULT, 'RemoteNext', (['in'], c_ulong, 'celt'), (['out'], POINTER(tagSTATDATA), 'rgelt'), (['out'], POINTER(c_ulong), 'pceltFetched')),
 COMMETHOD([], HRESULT, 'Skip', (['in'], c_ulong, 'celt')),
 COMMETHOD([], HRESULT, 'Reset'),
 COMMETHOD([], HRESULT, 'Clone', (['out'], POINTER(POINTER(IEnumSTATDATA)), 'ppenum'))]
IEnumString._methods_ = [COMMETHOD([], HRESULT, 'RemoteNext', (['in'], c_ulong, 'celt'), (['out'], POINTER(WSTRING), 'rgelt'), (['out'], POINTER(c_ulong), 'pceltFetched')),
 COMMETHOD([], HRESULT, 'Skip', (['in'], c_ulong, 'celt')),
 COMMETHOD([], HRESULT, 'Reset'),
 COMMETHOD([], HRESULT, 'Clone', (['out'], POINTER(POINTER(IEnumString)), 'ppenum'))]
wireASYNC_STGMEDIUM = POINTER(_userSTGMEDIUM)
IAdviseSink._methods_ = [COMMETHOD([], HRESULT, 'RemoteOnDataChange', (['in'], POINTER(tagFORMATETC), 'pformatetc'), (['in'], POINTER(wireASYNC_STGMEDIUM), 'pStgmed')),
 COMMETHOD([], HRESULT, 'RemoteOnViewChange', (['in'], c_ulong, 'dwAspect'), (['in'], c_int, 'lindex')),
 COMMETHOD([], HRESULT, 'RemoteOnRename', (['in'], POINTER(IMoniker), 'pmk')),
 COMMETHOD([], HRESULT, 'RemoteOnSave'),
 COMMETHOD([], HRESULT, 'RemoteOnClose')]

class __MIDL_IWinTypes_0003(Union):
    pass


class _FLAGGED_BYTE_BLOB(Structure):
    pass


__MIDL_IWinTypes_0003._fields_ = [('hInproc', c_int), ('hRemote', POINTER(_FLAGGED_BYTE_BLOB)), ('hInproc64', c_longlong)]
assert sizeof(__MIDL_IWinTypes_0003) == 8, sizeof(__MIDL_IWinTypes_0003)
assert alignment(__MIDL_IWinTypes_0003) == 8, alignment(__MIDL_IWinTypes_0003)
_userHGLOBAL._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0003)]
assert sizeof(_userHGLOBAL) == 16, sizeof(_userHGLOBAL)
assert alignment(_userHGLOBAL) == 8, alignment(_userHGLOBAL)
tagPALETTEENTRY._fields_ = [('peRed', c_ubyte),
 ('peGreen', c_ubyte),
 ('peBlue', c_ubyte),
 ('peFlags', c_ubyte)]
assert sizeof(tagPALETTEENTRY) == 4, sizeof(tagPALETTEENTRY)
assert alignment(tagPALETTEENTRY) == 1, alignment(tagPALETTEENTRY)

class __MIDL_IWinTypes_0007(Union):
    pass


__MIDL_IWinTypes_0007._fields_ = [('hInproc', c_int), ('hRemote', POINTER(_userBITMAP)), ('hInproc64', c_longlong)]
assert sizeof(__MIDL_IWinTypes_0007) == 8, sizeof(__MIDL_IWinTypes_0007)
assert alignment(__MIDL_IWinTypes_0007) == 8, alignment(__MIDL_IWinTypes_0007)
_userHBITMAP._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0007)]
assert sizeof(_userHBITMAP) == 16, sizeof(_userHBITMAP)
assert alignment(_userHBITMAP) == 8, alignment(_userHBITMAP)
_userHPALETTE._fields_ = [('fContext', c_int), ('u', __MIDL_IWinTypes_0008)]
assert sizeof(_userHPALETTE) == 16, sizeof(_userHPALETTE)
assert alignment(_userHPALETTE) == 8, alignment(_userHPALETTE)
IPersistStream._methods_ = [COMMETHOD([], HRESULT, 'IsDirty'),
 COMMETHOD([], HRESULT, 'Load', (['in'], POINTER(IStream), 'pstm')),
 COMMETHOD([], HRESULT, 'Save', (['in'], POINTER(IStream), 'pstm'), (['in'], c_int, 'fClearDirty')),
 COMMETHOD([], HRESULT, 'GetSizeMax', (['out'], POINTER(_ULARGE_INTEGER), 'pcbSize'))]
IMoniker._methods_ = [COMMETHOD([], HRESULT, 'RemoteBindToObject', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], POINTER(IMoniker), 'pmkToLeft'), (['in'], POINTER(_00020430_0000_0000_C000_000000000046_0_2_0.GUID), 'riidResult'), (['out'], POINTER(POINTER(IUnknown)), 'ppvResult')),
 COMMETHOD([], HRESULT, 'RemoteBindToStorage', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], POINTER(IMoniker), 'pmkToLeft'), (['in'], POINTER(_00020430_0000_0000_C000_000000000046_0_2_0.GUID), 'riid'), (['out'], POINTER(POINTER(IUnknown)), 'ppvObj')),
 COMMETHOD([], HRESULT, 'Reduce', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], c_ulong, 'dwReduceHowFar'), (['in', 'out'], POINTER(POINTER(IMoniker)), 'ppmkToLeft'), (['out'], POINTER(POINTER(IMoniker)), 'ppmkReduced')),
 COMMETHOD([], HRESULT, 'ComposeWith', (['in'], POINTER(IMoniker), 'pmkRight'), (['in'], c_int, 'fOnlyIfNotGeneric'), (['out'], POINTER(POINTER(IMoniker)), 'ppmkComposite')),
 COMMETHOD([], HRESULT, 'Enum', (['in'], c_int, 'fForward'), (['out'], POINTER(POINTER(IEnumMoniker)), 'ppenumMoniker')),
 COMMETHOD([], HRESULT, 'IsEqual', (['in'], POINTER(IMoniker), 'pmkOtherMoniker')),
 COMMETHOD([], HRESULT, 'Hash', (['out'], POINTER(c_ulong), 'pdwHash')),
 COMMETHOD([], HRESULT, 'IsRunning', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], POINTER(IMoniker), 'pmkToLeft'), (['in'], POINTER(IMoniker), 'pmkNewlyRunning')),
 COMMETHOD([], HRESULT, 'GetTimeOfLastChange', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], POINTER(IMoniker), 'pmkToLeft'), (['out'], POINTER(_FILETIME), 'pfiletime')),
 COMMETHOD([], HRESULT, 'Inverse', (['out'], POINTER(POINTER(IMoniker)), 'ppmk')),
 COMMETHOD([], HRESULT, 'CommonPrefixWith', (['in'], POINTER(IMoniker), 'pmkOther'), (['out'], POINTER(POINTER(IMoniker)), 'ppmkPrefix')),
 COMMETHOD([], HRESULT, 'RelativePathTo', (['in'], POINTER(IMoniker), 'pmkOther'), (['out'], POINTER(POINTER(IMoniker)), 'ppmkRelPath')),
 COMMETHOD([], HRESULT, 'GetDisplayName', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], POINTER(IMoniker), 'pmkToLeft'), (['out'], POINTER(WSTRING), 'ppszDisplayName')),
 COMMETHOD([], HRESULT, 'ParseDisplayName', (['in'], POINTER(IBindCtx), 'pbc'), (['in'], POINTER(IMoniker), 'pmkToLeft'), (['in'], WSTRING, 'pszDisplayName'), (['out'], POINTER(c_ulong), 'pchEaten'), (['out'], POINTER(POINTER(IMoniker)), 'ppmkOut')),
 COMMETHOD([], HRESULT, 'IsSystemMoniker', (['out'], POINTER(c_ulong), 'pdwMksys'))]
tagSTATDATA._fields_ = [('formatetc', tagFORMATETC),
 ('advf', c_ulong),
 ('pAdvSink', POINTER(IAdviseSink)),
 ('dwConnection', c_ulong)]
assert sizeof(tagSTATDATA) == 32, sizeof(tagSTATDATA)
assert alignment(tagSTATDATA) == 4, alignment(tagSTATDATA)

class AutoplayEventHandler(CoClass):
    _reg_clsid_ = GUID('{005A3A96-BAC4-4B0A-94EA-C0CE100EA736}')
    _idlflags_ = []
    _reg_typelib_ = ('{1CBE97AD-8AAE-41ED-AC48-550947492C9B}', 1, 0)


AutoplayEventHandler._com_interfaces_ = [IHWEventHandler,
 IDropTarget,
 IWiaEventCallback,
 _00020430_0000_0000_C000_000000000046_0_2_0.IDispatch]

class DropboxAutoplayProxy(CoClass):
    _reg_clsid_ = GUID('{F38F335B-BC2E-450E-8FC6-0E13E17FC8FE}')
    _idlflags_ = []
    _reg_typelib_ = ('{1CBE97AD-8AAE-41ED-AC48-550947492C9B}', 1, 0)


DropboxAutoplayProxy._com_interfaces_ = [IHWEventHandler, IDropTarget, _00020430_0000_0000_C000_000000000046_0_2_0.IDispatch]
_userFLAG_STGMEDIUM._fields_ = [('ContextFlags', c_int), ('fPassOwnership', c_int), ('Stgmed', _userSTGMEDIUM)]
assert sizeof(_userFLAG_STGMEDIUM) == 20, sizeof(_userFLAG_STGMEDIUM)
assert alignment(_userFLAG_STGMEDIUM) == 4, alignment(_userFLAG_STGMEDIUM)
_FLAGGED_BYTE_BLOB._fields_ = [('fFlags', c_ulong), ('clSize', c_ulong), ('abData', POINTER(c_ubyte))]
assert sizeof(_FLAGGED_BYTE_BLOB) == 12, sizeof(_FLAGGED_BYTE_BLOB)
assert alignment(_FLAGGED_BYTE_BLOB) == 4, alignment(_FLAGGED_BYTE_BLOB)

class DropboxWiaDataCallback(CoClass):
    _reg_clsid_ = GUID('{E69341A3-E6D2-4175-B60C-C9D3D6FA40F6}')
    _idlflags_ = []
    _reg_typelib_ = ('{1CBE97AD-8AAE-41ED-AC48-550947492C9B}', 1, 0)


class IWiaDataCallback(_00020430_0000_0000_C000_000000000046_0_2_0.IUnknown):
    _case_insensitive_ = True
    _iid_ = GUID('{A558A866-A5B0-11D2-A08F-00C04F72DC3C}')
    _idlflags_ = []


DropboxWiaDataCallback._com_interfaces_ = [IWiaDataCallback]
IWiaDataCallback._methods_ = [COMMETHOD([], HRESULT, 'BandedDataCallback', (['in'], c_int, 'lMessage'), (['in'], c_int, 'lStatus'), (['in'], c_int, 'lPercentComplete'), (['in'], c_int, 'lOffset'), (['in'], c_int, 'lLength'), (['in'], c_int, 'lReserved'), (['in'], c_int, 'lResLength'), (['in'], POINTER(c_ubyte), 'pbBuffer'))]
__all__ = ['IBindCtx',
 'IEnumString',
 '_userHMETAFILEPICT',
 '_userHPALETTE',
 'AutoplayEventHandler',
 '_userFLAG_STGMEDIUM',
 '_FLAGGED_BYTE_BLOB',
 '__MIDL_IAdviseSink_0002',
 'tagSTATDATA',
 'wireCLIPFORMAT',
 'IDataObject',
 'wireASYNC_STGMEDIUM',
 '__MIDL_IWinTypes_0008',
 'tagSTATSTG',
 'IHWEventHandler',
 '_remoteMETAFILEPICT',
 '__MIDL_IWinTypes_0007',
 'tagFORMATETC',
 'ISequentialStream',
 '_userBITMAP',
 '__MIDL_IAdviseSink_0003',
 '_userHMETAFILE',
 'tagPALETTEENTRY',
 'wireFLAG_STGMEDIUM',
 'IEnumFORMATETC',
 '_BYTE_BLOB',
 'IRunningObjectTable',
 'IPersistStream',
 'IEnumSTATDATA',
 '__MIDL_IWinTypes_0001',
 '__MIDL_IWinTypes_0003',
 '_userHBITMAP',
 '__MIDL_IWinTypes_0005',
 '_userHENHMETAFILE',
 'tagDVTARGETDEVICE',
 '__MIDL_IWinTypes_0006',
 '_userSTGMEDIUM',
 '_userCLIPFORMAT',
 '_STGMEDIUM_UNION',
 'IEnumMoniker',
 'IDropTarget',
 'IAdviseSink',
 'IMoniker',
 'wireSTGMEDIUM',
 'tagLOGPALETTE',
 'IStream',
 '_userHGLOBAL',
 '_GDI_OBJECT',
 '__MIDL_IWinTypes_0004',
 'DropboxWiaDataCallback']
