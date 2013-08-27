#Embedded file name: arch/win32/internal.py
from __future__ import absolute_import
import struct
import ctypes
import pprint
import traceback
import threading
import time
import os
import sys
import pywintypes
import win32con
import win32api
import win32event
import mmapfile
from win32com.shell import shell, shellcon
import win32security
from contextlib import contextmanager
import comtypes
from comtypes.shelllink import ShellLink
from comtypes.client import CreateObject
from comtypes.persist import IPersistFile
from ctypes import c_int, c_wchar_p, c_wchar, c_long
from ctypes.wintypes import HKEY, HWND, HDC, HINSTANCE, HANDLE, HRESULT, BYTE, DWORD, LPCWSTR, LPWSTR, LONG, UINT
from dropbox.features import current_feature_args
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.win32.kernel32 import FindFirstVolumeW, FindNextVolumeW, FindVolumeClose, GetLastError, win_strerror, SwitchToThread, GetVolumePathNamesForVolumeNameW
from dropbox.win32.version import WINDOWS_VERSION, WINXP
import build_number
from build_number import BUILD_KEY
from pynt.helpers.registry import registry_key, read_registry_value
from win32file import INVALID_HANDLE_VALUE
HTHEME = HANDLE
S_OK = 0

class RegKeyCouldntGetError(Exception):
    pass


class RegKeyCouldntSetError(Exception):
    pass


class RegKeyCouldntDeleteError(Exception):
    pass


ShellExecuteW = ctypes.windll.shell32.ShellExecuteW
ShellExecuteW.argtypes = [HWND,
 LPCWSTR,
 LPCWSTR,
 LPCWSTR,
 LPCWSTR,
 c_int]
ShellExecuteW.restype = HINSTANCE
GetDC = ctypes.windll.user32.GetDC
GetDC.argtypes = [HWND]
GetDC.restype = HDC
GetDeviceCaps = ctypes.windll.gdi32.GetDeviceCaps
GetDeviceCaps.argtypes = [HDC, c_int]
GetDeviceCaps.restype = c_int
ReleaseDC = ctypes.windll.user32.ReleaseDC
ReleaseDC.argtypes = [HWND, HDC]
ReleaseDC.restype = c_int
cached_installpath = None

def get_installpath():
    global cached_installpath
    if cached_installpath is None:
        configuration = get_registry(InstallPath=None)
        installpath = configuration['InstallPath']
        if installpath is None:
            TRACE('No installpath in HKCU, checking HKLM')
            default_installpath = win32api.GetModuleFileName(0).rsplit('\\', 1)[0]
            configuration = get_registry(win32con.HKEY_LOCAL_MACHINE, InstallPath=default_installpath)
            installpath = configuration['InstallPath']
        cached_installpath = os.path.normpath(installpath.decode('mbcs'))
    return cached_installpath


def executable(opts = ()):
    opts = list(opts) + current_feature_args()
    if hasattr(build_number, 'frozen'):
        ex = sys.executable
        cmd = [ex] + list(opts)
    else:
        cmd = [sys.executable, os.path.join('bin', 'dropbox')] + list(opts) + ['--key=%s' % BUILD_KEY]
    return cmd


CTYPES_INVALID_HANDLE_VALUE = HANDLE(INVALID_HANDLE_VALUE).value
FILE_SYSTEM_FLAGS = (('FILE_CASE_PRESERVED_NAMES', 2),
 ('FILE_CASE_SENSITIVE_SEARCH', 1),
 ('FILE_FILE_COMPRESSION', 16),
 ('FILE_NAMED_STREAMS', 262144),
 ('FILE_PERSISTENT_ACLS', 8),
 ('FILE_READ_ONLY_VOLUME', 524288),
 ('FILE_SEQUENTIAL_WRITE_ONCE', 1048576),
 ('FILE_SUPPORTS_ENCRYPTION', 131072),
 ('FILE_SUPPORTS_EXTENDED_ATTRIBUTES', 8388608),
 ('FILE_SUPPORTS_HARD_LINKS', 4194304),
 ('FILE_SUPPORTS_OBJECT_IDS', 65536),
 ('FILE_SUPPORTS_OPEN_BY_FILE_ID', 16777216),
 ('FILE_SUPPORTS_REPARSE_POINTS', 128),
 ('FILE_SUPPORTS_SPARSE_FILES', 64),
 ('FILE_SUPPORTS_TRANSACTIONS', 2097152),
 ('FILE_SUPPORTS_USN_JOURNAL', 33554432),
 ('FILE_UNICODE_ON_DISK', 4),
 ('FILE_VOLUME_IS_COMPRESSED', 32768),
 ('FILE_VOLUME_QUOTAS', 32))

def masks(mask):
    return (k for k, v in FILE_SYSTEM_FLAGS if mask & v)


def _get_rest_of_info(ub):
    try:
        info = win32api.GetVolumeInformation(ub.value)
        mm = list(masks(info[-2]))
    except Exception as e:
        if not isinstance(e, pywintypes.error) or e[0] != 21:
            unhandled_exc_handler(False)
        info = None
        mm = None

    ldw = DWORD()
    ub2 = ctypes.create_string_buffer(ctypes.sizeof(ctypes.c_wchar) * win32con.MAX_PATH * 5)
    if not GetVolumePathNamesForVolumeNameW(ub, ctypes.cast(ub2, LPWSTR), win32con.MAX_PATH * 5, ctypes.byref(ldw)):
        try:
            win_errno = GetLastError()
            raise WindowsError(win_errno, win_strerror(win_errno))
        except Exception:
            unhandled_exc_handler(False)

        aliases = None
    else:
        aliases = ub2.raw.decode('utf16')[:ldw.value].split(u'\x00')[:-2]
    return (ub.value,
     info,
     aliases,
     mm)


def get_volumes():
    ub = ctypes.create_unicode_buffer(win32con.MAX_PATH)
    hVol = FindFirstVolumeW(ub, win32con.MAX_PATH)
    if hVol == CTYPES_INVALID_HANDLE_VALUE:
        win_errno = GetLastError()
        raise WindowsError(win_errno, win_strerror(win_errno))
    toret = []
    try:
        toret.append(_get_rest_of_info(ub))
        while True:
            ret = FindNextVolumeW(hVol, ub, win32con.MAX_PATH)
            if not ret:
                break
            toret.append(_get_rest_of_info(ub))

        return toret
    finally:
        FindVolumeClose(hVol)


cached_dpi_mode = None

def get_dpi_mode():
    global cached_dpi_mode
    if cached_dpi_mode is None:
        hdc = GetDC(0)
        cached_dpi_mode = GetDeviceCaps(hdc, win32con.LOGPIXELSX)
        ReleaseDC(0, hdc)
    return cached_dpi_mode


def GetEnvironmentVariableW(lpName):
    max_env_size = 32767
    lpBuffer = ctypes.create_unicode_buffer(max_env_size)
    ret = ctypes.windll.kernel32.GetEnvironmentVariableW(LPCWSTR(unicode(lpName)), lpBuffer, DWORD(max_env_size))
    if ret:
        return lpBuffer.value


try:
    _GetSystemWow64DirectoryW = ctypes.windll.kernel32.GetSystemWow64DirectoryW
    _GetSystemWow64DirectoryW.argtypes = [LPWSTR, UINT]
    _GetSystemWow64DirectoryW.restype = UINT
except Exception:
    _GetSystemWow64DirectoryW = None

def GetSystemWow64Directory():
    if _GetSystemWow64DirectoryW is None:
        raise Exception('No GetSystemWow64DirectoryW!')
    ub = ctypes.create_unicode_buffer(win32con.MAX_PATH)
    _GetSystemWow64DirectoryW(ub, win32con.MAX_PATH)
    return ub.value


LPDWORD = ctypes.POINTER(DWORD)
_RegQueryValueExW = ctypes.windll.advapi32.RegQueryValueExW
_RegQueryValueExW.argtypes = [HKEY,
 LPCWSTR,
 LPDWORD,
 LPDWORD,
 ctypes.c_void_p,
 LPDWORD]
_RegQueryValueExW.restype = LONG

class RegQueryValueExWError(Exception):
    pass


def RegQueryValueExW(hkey, value_name):
    buf_size = DWORD(0)
    _RegQueryValueExW(hkey.handle, value_name, None, None, None, ctypes.byref(buf_size))
    buf = ctypes.create_unicode_buffer(buf_size.value)
    val_typ = DWORD()
    ret = _RegQueryValueExW(hkey.handle, value_name, None, ctypes.byref(val_typ), buf, ctypes.byref(buf_size))
    TRACE('_RegQueryValueExW(%r, %r, %r) -> %r, %r, %r, %r' % (hkey,
     value_name,
     None,
     val_typ.value,
     buf.value,
     buf_size.value,
     ret))
    if ret != 0:
        raise RegQueryValueExWError(ret)
    return (buf.value, val_typ.value)


def is_admin():
    try:
        return shell.IsUserAnAdmin()
    except Exception:
        pass

    admin_sid = win32security.GetBinarySid('S-1-5-32-544')
    t = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    groups = win32security.GetTokenInformation(t, win32security.TokenGroups)
    return any((group_sid == admin_sid for group_sid, group_attr in groups))


def is_uac_enabled():
    try:
        hkey = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System', 0, win32con.KEY_READ)
        try:
            val, val_typ = win32api.RegQueryValueEx(hkey, 'EnableLUA')
            return val != 0
        finally:
            win32api.RegCloseKey(hkey)

    except Exception:
        return False


def get_registry(*hkey, **keys_and_default_values):
    if len(hkey) == 0:
        hkey = (win32con.HKEY_CURRENT_USER, 'SOFTWARE\\%s' % BUILD_KEY)
    elif len(hkey) == 1:
        hkey = (hkey[0], 'SOFTWARE\\%s' % BUILD_KEY)
    elif len(hkey) > 2:
        raise RegKeyCouldntGetError('Too many non-keyword arguments to get_registry')
    try:
        hkey = win32api.RegOpenKeyEx(hkey[0], hkey[1], 0, win32con.KEY_READ)
        TRACE('Opened %s key' % BUILD_KEY)
    except Exception:
        TRACE("Couldn't open %s key" % BUILD_KEY)
        unhandled_exc_handler(False)
        hkey = None

    if hkey:
        try:
            configuration = {}
            for key in keys_and_default_values:
                TRACE('Trying to read value for key: %s' % key)
                try:
                    value, val_typ = RegQueryValueExW(hkey, key)
                    configuration[key] = value
                    TRACE('Read value: %s' % value)
                except Exception:
                    TRACE(traceback.format_exc())
                    try:
                        raise RegKeyCouldntGetError(key)
                    except Exception:
                        unhandled_exc_handler(False)

                    configuration[key] = keys_and_default_values[key]
                    TRACE("Couldn't read value, using default")

        finally:
            win32api.RegCloseKey(hkey)

        TRACE('Closed %s key' % BUILD_KEY)
    else:
        configuration = keys_and_default_values
    TRACE('get_registry is returning: %s' % pprint.pformat(configuration))
    return configuration


def set_registry(*hkey, **keys_and_values):
    if len(hkey) == 0:
        hkey = (win32con.HKEY_CURRENT_USER, 'SOFTWARE\\%s' % BUILD_KEY)
    elif len(hkey) == 1:
        hkey = (hkey[0], 'SOFTWARE\\%s' % BUILD_KEY)
    elif len(hkey) > 2:
        raise RegKeyCouldntSetError('Too many non-keyword arguments to set_registry')
    try:
        hkey = win32api.RegOpenKeyEx(hkey[0], hkey[1], 0, win32con.KEY_ALL_ACCESS)
    except Exception:
        unhandled_exc_handler(False)
        hkey = None

    if hkey:
        try:
            for key in keys_and_values:
                try:
                    win32api.RegSetValueEx(hkey, key, 0, win32con.REG_SZ, keys_and_values[key])
                except Exception:
                    TRACE(traceback.format_exc())
                    try:
                        raise RegKeyCouldntSetError(key + ':' + keys_and_values[key])
                    except Exception:
                        unhandled_exc_handler(False)

        finally:
            win32api.RegCloseKey(hkey)


@contextmanager
def initialized_com(coinit = comtypes.COINIT_APARTMENTTHREADED):
    if threading.currentThread().getName() != 'MainThread':
        try:
            try:
                comtypes.CoInitializeEx(coinit)
            except Exception:
                unhandled_exc_handler()

            yield
        finally:
            try:
                comtypes.CoUninitialize()
            except Exception:
                unhandled_exc_handler()

    else:
        yield


def uses_com(f):

    def wrapper(*args, **kw):
        with initialized_com():
            return f(*args, **kw)

    return wrapper


CSIDL_FLAG_CREATE = 32768
relevant_reg_keys = {shellcon.CSIDL_PERSONAL: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'Personal'),
 shellcon.CSIDL_STARTUP: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'Startup'),
 shellcon.CSIDL_APPDATA: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'AppData'),
 shellcon.CSIDL_DESKTOP: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'Desktop'),
 shellcon.CSIDL_MYMUSIC: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'My Music'),
 shellcon.CSIDL_MYPICTURES: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'My Pictures'),
 shellcon.CSIDL_MYVIDEO: ('SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders', 'My Video')}
relevant_env_vars = {shellcon.CSIDL_WINDOWS: ('%SYSTEMROOT%', '%windir%'),
 shellcon.CSIDL_APPDATA: ('%APPDATA%', '%appdata%'),
 shellcon.CSIDL_PROFILE: ('%USERPROFILE%', '%userprofile%')}
default_csidl_locs = {shellcon.CSIDL_WINDOWS: u'C:\\Windows',
 shellcon.CSIDL_SYSTEM: u'C:\\Windows\\System32',
 shellcon.CSIDL_PROGRAM_FILES: u'C:\\Program Files'}

def get_user_folder_path(flag, fallback_to_default = False):
    toret = None
    TRACE('getting user folder path: %r' % flag)
    try:
        toret = shell.SHGetFolderPath(0, flag | CSIDL_FLAG_CREATE, None, 0)
    except Exception:
        unhandled_exc_handler()

    if not toret:
        try:
            reg = relevant_reg_keys[flag]
        except KeyError:
            pass
        else:
            TRACE('!! Failed to get user path; trying registry')
            try:
                userprofile = GetEnvironmentVariableW('USERPROFILE')
                toret = get_registry(win32con.HKEY_CURRENT_USER, reg[0], **{reg[1]: None})[reg[1]].replace('%USERPROFILE%', userprofile)
            except Exception:
                TRACE('USERPROFILE is %r', userprofile)
                unhandled_exc_handler()

    if not toret:
        try:
            env_choices = relevant_env_vars[flag]
        except KeyError:
            pass
        else:
            TRACE('!! Failed to get user path; trying environment environment')
            for env in env_choices:
                try:
                    maybe = GetEnvironmentVariableW(env)
                    if maybe:
                        toret = maybe
                        break
                except Exception:
                    unhandled_exc_handler()

    if not toret and fallback_to_default:
        try:
            toret = default_csidl_locs[flag]
        except KeyError:
            pass

    if not toret:
        TRACE('!! Failed to get user path')
    return toret


def get_user_folder_path_from_reg(flag):
    toret = None
    TRACE('getting user folder path from registry: %r' % flag)
    try:
        reg = relevant_reg_keys[flag]
    except KeyError:
        pass
    else:
        try:
            userprofile = GetEnvironmentVariableW('USERPROFILE')
            toret = get_registry(win32con.HKEY_CURRENT_USER, reg[0], **{reg[1]: ''})[reg[1]].replace('%USERPROFILE%', userprofile)
        except Exception:
            unhandled_exc_handler()

    return toret


@uses_com
def create_shortcut(name, target, description = None, arguments = None, icon_location = None):
    shortcut = CreateObject(ShellLink)
    shortcut.SetPath(target)
    if description:
        shortcut.SetDescription(description)
    if arguments:
        shortcut.SetArguments(arguments)
    if icon_location:
        try:
            i_fn, i_offset = icon_location
            TRACE("setting %r's shortcut icon to %r, %r", name, i_fn, i_offset)
            shortcut.SetIconLocation(i_fn, i_offset)
        except Exception:
            unhandled_exc_handler()

    pf = shortcut.QueryInterface(IPersistFile)
    pf.Save(name, True)


def remove_shortcut_from_user_location(location):
    if hasattr(build_number, 'frozen'):
        folder = get_user_folder_path(location)
        item_path = os.path.join(folder, '%s.lnk' % BUILD_KEY)
        TRACE('removing shortcut from %s' % item_path)
        if os.path.exists(item_path):
            os.remove(item_path)


def add_shortcut_to_user_location(location, arguments = None):
    if hasattr(build_number, 'frozen'):
        folder = get_user_folder_path(location)
        if folder:
            item_path = os.path.join(folder, '%s.lnk' % BUILD_KEY)
            TRACE('Adding shortcut to %s' % item_path)
            if not os.path.exists(item_path):
                create_shortcut(item_path, executable()[0], u'%s - Sync your files online and across computers' % BUILD_KEY, arguments)
        else:
            TRACE("Couldn't add shortcut at %r with args: %r", location, arguments)


def _output_dbdebug_string(s):
    s = str(s)
    mm = mmapfile.mmapfile(None, 'DBNSIS_BUFFER', 4096, 0, 4096)
    buffer_event = win32event.OpenEvent(win32con.SYNCHRONIZE, 0, 'DBNSIS_BUFFER_READY')
    data_event = win32event.OpenEvent(win32con.EVENT_MODIFY_STATE, 0, 'DBNSIS_DATA_READY')
    win32event.WaitForSingleObject(buffer_event, 10000)
    mm.seek(0)
    frag = struct.pack('L', win32api.GetCurrentProcessId()) + s.rstrip()[:2000].encode('utf16')[2:] + '\x00\x00'
    mm.write(frag)
    mm.flush()
    win32event.SetEvent(data_event)


_tracer = None

def check_nsis_tracing():
    global _tracer
    try:
        win32event.OpenEvent(win32con.SYNCHRONIZE, 0, 'DBNSIS_BUFFER_READY')
    except pywintypes.error as e:
        if e[0] != 2:
            TRACE("Couldn't access NSIS buffer")
            unhandled_exc_handler()
    except Exception:
        unhandled_exc_handler()
    else:
        from dropbox.client.high_trace import add_high_trace_handler, line_encrypter
        if _tracer is None:
            _tracer = line_encrypter(_output_dbdebug_string)
        add_high_trace_handler(_tracer)


def reset_nsis_tracing():
    time.sleep(0.5)
    from dropbox.client.high_trace import remove_high_trace_handler
    remove_high_trace_handler(_tracer)


def lfHeight_to_pointsize(lfHeight):
    hdc = GetDC(0)
    point_size = -72 * lfHeight / GetDeviceCaps(hdc, win32con.LOGPIXELSY)
    ReleaseDC(0, hdc)
    return point_size


def pointsize_to_lfHeight(point):
    hdc = GetDC(0)
    lfHeight = -point * GetDeviceCaps(hdc, win32con.LOGPIXELSY) / 72
    ReleaseDC(0, hdc)
    return lfHeight


if WINDOWS_VERSION >= WINXP:
    try:
        OpenThemeData = ctypes.windll.uxtheme.OpenThemeData
        OpenThemeData.argtypes = [HWND, c_wchar_p]
        OpenThemeData.restype = HTHEME
        CloseThemeData = ctypes.windll.uxtheme.CloseThemeData
        CloseThemeData.argtypes = [HTHEME]
        CloseThemeData.restype = HRESULT
        TMT_CAPTIONFONT = 801
        TMT_SMALLCAPTIONFONT = 802
        TMT_MENUFONT = 803
        TMT_STATUSFONT = 804
        TMT_MSGBOXFONT = 805
        TMT_ICONTITLEFONT = 806

        class LOGFONTW(ctypes.Structure):
            _fields_ = [('lfHeight', c_long),
             ('lfWidth', c_long),
             ('lfEscapement', c_long),
             ('lfOrientation', c_long),
             ('lfWeight', c_long),
             ('lfItalic', BYTE),
             ('lfUnderline', BYTE),
             ('lfStrikeOut', BYTE),
             ('lfCharSet', BYTE),
             ('lfOutPrecision', BYTE),
             ('lfClipPrecision', BYTE),
             ('lfQuality', BYTE),
             ('lfPitchAndFamily', BYTE),
             ('lfFaceName', c_wchar * win32con.LF_FACESIZE)]


        GetThemeSysFont = ctypes.windll.uxtheme.GetThemeSysFont
        GetThemeSysFont.argtypes = [HTHEME, c_int, ctypes.POINTER(LOGFONTW)]
        GetThemeSysFont.restype = HRESULT

        def font_for_hwnd(hwnd, font):
            htheme = OpenThemeData(hwnd, 'Window')
            try:
                lf = LOGFONTW()
                err = GetThemeSysFont(htheme, font, ctypes.byref(lf))
                assert err == S_OK, 'GetThemeSysFont failed! %r' % err
                return lf
            finally:
                try:
                    if htheme:
                        CloseThemeData(htheme)
                except Exception:
                    unhandled_exc_handler()


    except Exception:
        unhandled_exc_handler()

thread_yield = SwitchToThread

def tcp_parameters():
    toret = []
    subkey = u'SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters'
    with registry_key(win32con.HKEY_LOCAL_MACHINE, subkey) as hkey:
        if hkey:
            for _t in (u'Tcp1323Opts', u'GlobalMaxTcpWindowSize', u'TcpWindowSize', u'EnablePMTUDiscovery'):
                try:
                    v = read_registry_value(hkey, _t)
                except KeyError:
                    continue
                except Exception:
                    unhandled_exc_handler()
                else:
                    toret.append((_t, v))

    return toret
