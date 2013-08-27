#Embedded file name: arch/win32/tray_fix.py
import os
import string
import sys
import pywintypes
import win32api
import win32con
import win32gui
from win32com.shell import shellcon
from dropbox.trace import TRACE, report_bad_assumption
from dropbox.win32.version import VISTA, WIN2K, WIN2K3, WIN7, WIN8, WINXP, WINDOWS_VERSION
from .internal import get_user_folder_path
SUPPORTED_PLATFORMS = (WINXP,
 WIN2K3,
 VISTA,
 WIN7,
 WIN8)
GUID_FOLDER_PLATFORMS = (WIN7, WIN8)
if WINDOWS_VERSION in (WINXP, WIN2K3):
    TRAYNOTIFY_KEY = 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TrayNotify'
elif WINDOWS_VERSION in (VISTA, WIN7, WIN8):
    TRAYNOTIFY_KEY = 'Software\\Classes\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion\\TrayNotify'
SHOW_ICON_AND_NOTIFICATIONS = '\x02'
FLAG_OFFSET = 528
if WINDOWS_VERSION in GUID_FOLDER_PLATFORMS:
    WIN7_GUID_MAP = {}
    guid_map_template = {shellcon.CSIDL_WINDOWS: u'{S38OS404-1Q43-42S2-9305-67QR0O28SP23}',
     shellcon.CSIDL_SYSTEM: u'{Q65231O0-O2S1-4857-N4PR-N8R7P6RN7Q27}',
     shellcon.CSIDL_PROGRAM_FILES: u'{7P5N40RS-N0SO-4OSP-874N-P0S2R0O9SN8R}'}
    for flag in guid_map_template:
        path = get_user_folder_path(flag, fallback_to_default=True)
        WIN7_GUID_MAP[path] = guid_map_template[flag]

class UnsupportedPlatformError(Exception):
    pass


class MissingEntryError(Exception):
    pass


def rot13_char(c):
    if c in string.uppercase:
        pivot = 'M'
    elif c in string.lowercase:
        pivot = 'm'
    else:
        pivot = None
    if pivot is not None:
        if c > pivot:
            return chr(ord(c) - 13)
        else:
            return chr(ord(c) + 13)
    else:
        return c


def rot13_utf16_encode(s):
    return u''.join((rot13_char(c) for c in s)).encode('utf16')[2:]


def get_encoded_path(executable):
    if not isinstance(executable, unicode):
        executable = executable.decode('mbcs')
    executable = os.path.normpath(executable)
    if WINDOWS_VERSION in GUID_FOLDER_PLATFORMS:
        for folder in WIN7_GUID_MAP:
            if executable.lower().startswith(os.path.normpath(folder).lower() + '\\'):
                encoded_executable = WIN7_GUID_MAP[folder].encode('utf16')[2:] + rot13_utf16_encode(executable[len(folder):])
                break
        else:
            encoded_executable = rot13_utf16_encode(executable)

    else:
        encoded_executable = executable.encode('utf16')[2:]
    return encoded_executable


def load_icon_streams():
    hkey = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, TRAYNOTIFY_KEY, 0, win32con.KEY_READ | win32con.KEY_WOW64_64KEY)
    try:
        icon_streams = win32api.RegQueryValueEx(hkey, 'IconStreams')
    finally:
        win32api.RegCloseKey(hkey)

    assert icon_streams[1] == win32con.REG_BINARY, 'IconStreams is not of type REG_BINARY? Aborting'
    TRACE('Loaded icon streams registry key.')
    return icon_streams[0]


def save_icon_streams(icon_streams):
    hkey = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, TRAYNOTIFY_KEY, 0, win32con.KEY_ALL_ACCESS | win32con.KEY_WOW64_64KEY)
    try:
        win32api.RegSetValueEx(hkey, 'IconStreams', 0, win32con.REG_BINARY, icon_streams)
        TRACE('Saved icon streams registry key.')
    finally:
        win32api.RegCloseKey(hkey)


def locate_entry(icon_streams, executable):
    encoded = get_encoded_path(executable)
    encoded = encoded[2:]
    index = icon_streams.find(encoded)
    if index >= 0:
        index -= 2
    TRACE('Found entry at offset: %s', index)
    return index


def modify_entry(icon_streams, index):
    assert index > 0, 'Invalid offset.'
    local_offset = index + FLAG_OFFSET
    TRACE('Modified entry flag at offset [%s, %s]', index, local_offset)
    return icon_streams[:local_offset] + SHOW_ICON_AND_NOTIFICATIONS + icon_streams[local_offset + 1:]


def check_entry(icon_streams, index):
    assert index > 0, 'Invalid offset.'
    local_offset = index + FLAG_OFFSET
    return icon_streams[local_offset:local_offset + 1] == SHOW_ICON_AND_NOTIFICATIONS


def promote_icon(executable = sys.executable):
    TRACE('Promoting icon in tray ...')
    if WINDOWS_VERSION in (WIN2K,):
        TRACE('Skipping tray icon promotion on Windows 2000.')
        return
    if WINDOWS_VERSION not in SUPPORTED_PLATFORMS:
        raise UnsupportedPlatformError('Platform not supported: %r' % WINDOWS_VERSION)
    data = load_icon_streams()
    entry_index = locate_entry(data, executable)
    if entry_index < 0:
        raise MissingEntryError('Key exists, but entry could not be found!')
    if check_entry(data, entry_index):
        TRACE('Entry checks out!')
        return
    save_icon_streams(modify_entry(data, entry_index))
