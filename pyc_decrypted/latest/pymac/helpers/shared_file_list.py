#Embedded file name: pymac/helpers/shared_file_list.py
from __future__ import absolute_import
import os
from ctypes import byref, c_uint32, create_string_buffer
from .core import CFString, releasing, CFArray
from ..constants import dirNFErr, errFSNotAFolder, fnfErr, kCFAllocatorDefault, kCFURLPOSIXPathStyle, kLSSharedFileListNoUserInteraction, kLSSharedFileListDoNotMountVolumes, nsvErr, paramErr
from ..dlls import Core, CoreServices
from ..dlls.CoreServices import OSStatusError
from ..types import CFStringRef, CFURLRef
SFL_FAVORITES = 'favorites'
SFL_LOGIN = 'login'
SUPPORTED_LISTS = (SFL_FAVORITES, SFL_LOGIN)

def kLSSharedFileList_for_list(list_type):
    if list_type == SFL_FAVORITES:
        return CoreServices.kLSSharedFileListFavoriteItems
    if list_type == SFL_LOGIN:
        return CoreServices.kLSSharedFileListSessionLoginItems
    assert False, '%s not in SUPPORTED_LISTS' % (list_type,)


def add_path_to_shared_list(path, list_type, first = False):
    assert type(path) is unicode
    assert list_type in SUPPORTED_LISTS
    path_cfstr = CFString.from_python(path)
    basename_cfstr = CFString.from_python(os.path.basename(path))
    isdir = 1 if os.path.isdir(path) else 0
    with releasing(Core.CFURLCreateWithFileSystemPath(kCFAllocatorDefault, path_cfstr.get_ref(), kCFURLPOSIXPathStyle, isdir)) as path_url:
        with releasing(CoreServices.LSSharedFileListCreate(kCFAllocatorDefault, kLSSharedFileList_for_list(list_type), None)) as the_list:
            pos = CoreServices.kLSSharedFileListItemBeforeFirst if first else CoreServices.kLSSharedFileListItemLast
            with releasing(CoreServices.LSSharedFileListInsertItemURL(the_list, pos, basename_cfstr.get_ref(), None, path_url, None, None)):
                pass


def remove_path_from_shared_list(path_test, list_type, unhandled_exc_handler = None):
    assert list_type in SUPPORTED_LISTS
    with releasing(CoreServices.LSSharedFileListCreate(kCFAllocatorDefault, kLSSharedFileList_for_list(list_type), None)) as the_list:
        snapshot_seed = c_uint32()
        with releasing(CoreServices.LSSharedFileListCopySnapshot(the_list, byref(snapshot_seed))) as snapshot:
            path_buffer = create_string_buffer(1024)
            for item_ref in CFArray(snapshot).refs():
                try:
                    with releasing(CFURLRef()) as item_url:
                        try:
                            CoreServices.LSSharedFileListItemResolve(item_ref, kLSSharedFileListDoNotMountVolumes | kLSSharedFileListNoUserInteraction, byref(item_url), None)
                        except OSStatusError as e:
                            if e.errno in (errFSNotAFolder,
                             nsvErr,
                             fnfErr,
                             dirNFErr):
                                continue
                            raise

                        if not Core.CFURLGetFileSystemRepresentation(item_url, 1, path_buffer, len(path_buffer)):
                            raise Exception('Unable to get representation of %r' % item_url)
                    item_path = path_buffer.value.decode('utf8')
                    if path_test(item_path):
                        try:
                            CoreServices.LSSharedFileListItemRemove(the_list, item_ref)
                        except OSStatusError as e:
                            if e.errno == paramErr:
                                continue
                            raise

                except Exception:
                    if unhandled_exc_handler:
                        unhandled_exc_handler()
                    else:
                        raise


def print_shared_list(list_type):
    assert list_type in SUPPORTED_LISTS
    items = []

    def trace_path(path):
        items.append('item_path is %r' % path)
        return False

    remove_path_from_shared_list(trace_path, list_type)
    items.append('')
    return '\n'.join(items)


def get_all_login_matches(app_name, unhandled_exc_handler = None):
    matches = []
    app_name = '/' + app_name

    def capture_path(path):
        try:
            if path.endswith(app_name):
                matches.append(path)
        except Exception:
            if unhandled_exc_handler:
                unhandled_exc_handler()

        return False

    try:
        remove_path_from_shared_list(capture_path, SFL_LOGIN)
    except Exception:
        if unhandled_exc_handler:
            unhandled_exc_handler()

    return matches


def print_all_lists():
    print 'Favourites are:'
    print print_shared_list(SFL_FAVORITES)
    print
    print 'Login Items are:'
    print print_shared_list(SFL_LOGIN)
