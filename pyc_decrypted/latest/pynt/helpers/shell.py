#Embedded file name: pynt/helpers/shell.py
from __future__ import absolute_import
import os
from ctypes import byref, create_unicode_buffer, c_wchar_p
from ctypes.wintypes import MAX_PATH
from dropbox.win32.version import VISTA, WINDOWS_VERSION
from ..constants import CSIDL_FLAG_CREATE, S_OK
from ..types import PIDLIST, ABM_GETTASKBARPOS, APPBARDATA
from ..dlls.shell32 import shell32
from .general import windows_error

def get_folder_path(path_flag):
    raw_path = create_unicode_buffer(MAX_PATH)
    ret = shell32.SHGetFolderPathW(0, path_flag | CSIDL_FLAG_CREATE, 0, 0, raw_path)
    if ret != S_OK:
        return None
    else:
        return raw_path.value


def open_folder_and_select_items(folder, items):
    count = len(items)
    items_il = (PIDLIST * count)()
    folder_il = shell32.ILCreateFromPathW(folder)
    if not folder_il:
        raise windows_error()
    try:
        cur = 0
        for path in items:
            item = shell32.ILCreateFromPathW(path)
            if item:
                items_il[cur] = item
                cur += 1

        ret = shell32.SHOpenFolderAndSelectItems(folder_il, cur, items_il, 0)
        if ret:
            raise windows_error(ret)
    finally:
        shell32.ILFree(folder_il)
        for i in items_il:
            if i:
                shell32.ILFree(i)


def shell_get_known_folder_path(folder_id):
    pbuf = c_wchar_p()
    if WINDOWS_VERSION >= VISTA:
        ret = shell32.SHGetKnownFolderPath(byref(folder_id), 0, 0, byref(pbuf))
    else:
        pbuf = create_unicode_buffer(MAX_PATH)
        ret = shell32.SHGetFolderPathW(0, folder_id, 0, 0, pbuf)
    if ret != S_OK:
        raise windows_error(ret)
    path = pbuf.value
    normed = os.path.normpath(path)
    return normed


def shell_set_known_folder_path(folder_id, path):
    if WINDOWS_VERSION >= VISTA:
        ret = shell32.SHSetKnownFolderPath(byref(folder_id), 0, 0, path)
    else:
        ret = shell32.SHSetFolderPathW(folder_id, 0, 0, path)
    if ret != S_OK:
        raise windows_error(ret)


def get_taskbar_position():
    appbardata = APPBARDATA()
    if shell32.SHAppBarMessage(ABM_GETTASKBARPOS, byref(appbardata)) == 0:
        raise Exception('Failed to get taskbar position')
    return (appbardata.rc.left,
     appbardata.rc.top,
     appbardata.rc.right,
     appbardata.rc.bottom)
