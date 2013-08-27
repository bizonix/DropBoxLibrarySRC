#Embedded file name: pymac/helpers/disk.py
import os
from ctypes import byref, sizeof
from .core import CFDictionary, CFString, releasing
from ..dlls import Core, CoreServices, DiskArbitration, libc
from ..dlls.CoreServices import OSStatusError
from ..types import FSCatalogInfo, FSRef, FSVolumeRefNum, GetVolParmsInfoBuffer, HFSUniStr255, struct_statfs, Boolean
from ..constants import bIsEjectable, bIsOnExternalBus, bIsOnInternalBus, bIsRemovable, dirNFErr, kCFAllocatorDefault, kCFStringEncodingUTF8, kCFURLPOSIXPathStyle, kFSCatInfoNone, kFSCatInfoVolume, kFSInvalidVolumeRefNum, kFSVolInfoNone, kOnAppropriateDisk, kTrashFolderType, kTemporaryFolderType, kWhereToEmptyTrashFolderType, kTemporaryItemsInCacheDataFolderType, kChewableItemsFolderType, nsvErr

def get_mount_point_for_path(path):
    path = os.path.normpath(os.path.abspath(path))
    while True:
        if os.path.ismount(path) or path == '/':
            return path
        path = os.path.dirname(path)


def get_volume_desc(device_path):
    with releasing(DiskArbitration.DASessionCreate(kCFAllocatorDefault)) as sess:
        if not sess:
            raise Exception("Couldn't create DASession")
        with releasing(DiskArbitration.DADiskCreateFromBSDName(kCFAllocatorDefault, sess, device_path)) as disk:
            if not disk:
                raise Exception("Couldn't DADiskCreate")
            desc = DiskArbitration.DADiskCopyDescription(disk)
            if not desc:
                raise Exception("Couldn't DADiskCopyDescription")
            return CFDictionary(desc, take_ownership=True)


def get_volume_desc_for_mount_point(path):
    path = path.encode('utf-8')
    stat = struct_statfs()
    libc.statfs(path, byref(stat))
    return get_volume_desc(stat.f_mntfromname)


def get_volume_uuid(path):
    return get_volume_desc_for_mount_point(path)['DAVolumeUUID']


def is_ejectable(path):
    return get_volume_desc_for_mount_point(path)['DAMediaEjectable']


def is_removable_drive(volumeRefNum):
    volparms = GetVolParmsInfoBuffer()
    try:
        CoreServices.FSGetVolumeParms(volumeRefNum, byref(volparms), sizeof(volparms))
    except AttributeError:
        return False

    attrs = volparms.vMExtendedAttributes
    version = volparms.vMVersion
    return (version > 2 and attrs & bIsEjectable and attrs & bIsRemovable and (attrs & bIsOnExternalBus or attrs & bIsOnInternalBus)) != 0


def _get_path_from_fsref(fsref):
    with releasing(Core.CFURLCreateFromFSRef(kCFAllocatorDefault, byref(fsref))) as cfurlref:
        with releasing(Core.CFURLCopyFileSystemPath(cfurlref, kCFURLPOSIXPathStyle)) as cfstringref:
            return unicode(CFString(cfstringref))


def _get_string_from_hfsunistr255(string):
    with releasing(Core.CFStringCreateWithCharacters(kCFAllocatorDefault, string.unicode, string.length)) as cfstringref:
        return unicode(CFString(cfstringref))


def is_in_trash(path):
    ref = _path_to_fsref(path)
    result = Boolean(False)
    for location in (kTrashFolderType,
     kTemporaryFolderType,
     kWhereToEmptyTrashFolderType,
     kTemporaryItemsInCacheDataFolderType,
     kChewableItemsFolderType):
        try:
            CoreServices.FSDetermineIfRefIsEnclosedByFolder(kOnAppropriateDisk, location, byref(ref), byref(result))
        except OSStatusError as e:
            if e.errno != nsvErr:
                raise

        if result:
            return True

    return False


def get_all_removable_drives():
    toret = {}
    volumeIndex = 1
    while True:
        try:
            volumeRefNum = FSVolumeRefNum()
            name = HFSUniStr255()
            rootdir = FSRef()
            CoreServices.FSGetVolumeInfo(kFSInvalidVolumeRefNum, volumeIndex, byref(volumeRefNum), kFSVolInfoNone, None, byref(name), byref(rootdir))
            if is_removable_drive(volumeRefNum):
                path = _get_path_from_fsref(rootdir)
                toret[path] = _get_string_from_hfsunistr255(name)
            volumeIndex += 1
        except OSStatusError as e:
            if e.errno not in (dirNFErr, nsvErr):
                raise
            break
        except Exception:
            raise

    return toret


def _path_to_fsref(path):
    ref = FSRef()
    if not isinstance(path, str):
        path = path.encode('utf8')
    CoreServices.FSPathMakeRef(path, byref(ref), None)
    return ref


def is_path_removable_drive(path):
    ref = _path_to_fsref(path)
    catalog_info = FSCatalogInfo()
    CoreServices.FSGetCatalogInfo(byref(ref), kFSCatInfoVolume, byref(catalog_info), None, None, None)
    volumeRefNum = catalog_info.volume
    return is_removable_drive(volumeRefNum)


def drive_name_from_path(path):
    ref = _path_to_fsref(path)
    name = HFSUniStr255()
    CoreServices.FSGetCatalogInfo(byref(ref), kFSCatInfoNone, None, byref(name), None, None)
    return _get_string_from_hfsunistr255(name)
