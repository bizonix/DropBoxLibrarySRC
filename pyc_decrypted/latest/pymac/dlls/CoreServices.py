#Embedded file name: pymac/dlls/CoreServices.py
from __future__ import absolute_import
from ctypes import c_char_p, POINTER, c_uint32
from ..constants import errNone
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework
from ..types import Boolean, ByteCount, CFAllocatorRef, CFArrayRef, CFDictionaryRef, CFStringRef, CFTypeRef, CFURLRef, FSCatalogInfo, FSCatalogInfoBitmap, FSRef, FSSpec, FSVolumeInfoBitmap, FSVolumeInfo, FSVolumeRefNum, GetVolParmsInfoBuffer, HFSUniStr255, IconRef, ItemCount, OSErr, OSStatus, OSType, LSSharedFileListRef, LSSharedFileListItemRef

class LazyCoreServices(LazyFramework):

    def __init__(self):
        super(LazyCoreServices, self).__init__()
        self._dllname = u'CoreServices'
        self._func_defs = {}

        def F(name, ret = None, args = [], errcheck = OSStatusCheck):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}
            if errcheck:
                self._func_defs[name]['errcheck'] = errcheck

        def C(name, const_type):
            self._const_defs[name] = const_type

        F('FSGetVolumeInfo', OSErr, [FSVolumeRefNum,
         ItemCount,
         POINTER(FSVolumeRefNum),
         FSVolumeInfoBitmap,
         POINTER(FSVolumeInfo),
         POINTER(HFSUniStr255),
         POINTER(FSRef)])
        F('FSGetVolumeParms', OSStatus, [FSVolumeRefNum, POINTER(GetVolParmsInfoBuffer), ByteCount])
        F('GetMacOSStatusErrorString', c_char_p, [OSStatus], errcheck=None)
        F('GetMacOSStatusCommentString', c_char_p, [OSStatus], errcheck=None)
        F('FSRefMakePath', OSStatus, [POINTER(FSRef), c_char_p, c_uint32])
        F('FSPathMakeRef', OSStatus, [c_char_p, POINTER(FSRef), POINTER(Boolean)])
        F('FSGetCatalogInfo', OSErr, [POINTER(FSRef),
         FSCatalogInfoBitmap,
         POINTER(FSCatalogInfo),
         POINTER(HFSUniStr255),
         POINTER(FSSpec),
         POINTER(FSRef)])
        F('FSSetCatalogInfo', OSErr, [POINTER(FSRef), FSCatalogInfoBitmap, POINTER(FSCatalogInfo)])
        F('FSIsAliasFile', OSErr, [POINTER(FSRef), POINTER(Boolean), POINTER(Boolean)])
        F('FSDetermineIfRefIsEnclosedByFolder', OSErr, [FSVolumeRefNum,
         OSType,
         POINTER(FSRef),
         POINTER(Boolean)])
        F('LSSharedFileListCreate', LSSharedFileListRef, [CFAllocatorRef, CFStringRef, CFTypeRef], errcheck=None)
        F('LSSharedFileListInsertItemURL', LSSharedFileListItemRef, [LSSharedFileListRef,
         LSSharedFileListItemRef,
         CFStringRef,
         IconRef,
         CFURLRef,
         CFDictionaryRef,
         CFArrayRef], errcheck=None)
        F('LSSharedFileListCopySnapshot', CFArrayRef, [LSSharedFileListRef, POINTER(c_uint32)], errcheck=None)
        F('LSSharedFileListItemResolve', OSStatus, [LSSharedFileListItemRef,
         c_uint32,
         POINTER(CFURLRef),
         POINTER(FSRef)])
        F('LSSharedFileListItemRemove', OSStatus, [LSSharedFileListRef, LSSharedFileListItemRef])
        C('kLSSharedFileListItemLast', LSSharedFileListItemRef)
        C('kLSSharedFileListItemBeforeFirst', LSSharedFileListItemRef)
        C('kLSSharedFileListFavoriteItems', LSSharedFileListItemRef)
        C('kLSSharedFileListSessionLoginItems', LSSharedFileListItemRef)


CoreServices = FakeDLL(LazyCoreServices)

class OSStatusError(Exception):

    def __init__(self, err):
        super(OSStatusError, self).__init__(err)
        self.errno = err
        self.errno_tup = None

    def __str__(self):
        try:
            return '[OSStatus %d] %s: %s)' % self.errno_tup
        except Exception:
            if not self.errno_tup:
                try:
                    self.errno_tup = (self.errno, CoreServices.GetMacOSStatusErrorString(self.errno), CoreServices.GetMacOSStatusCommentString(self.errno))
                    return '[OSStatus %d] %s: %s)' % self.errno_tup
                except Exception:
                    pass

            try:
                return '[OSStatus %d]' % self.errno
            except Exception:
                return '[OSStatus]'

    __repr__ = __str__


def OSStatusCheck(result, func, args):
    if result == errNone:
        return
    raise OSStatusError(result)
