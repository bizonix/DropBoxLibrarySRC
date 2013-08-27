#Embedded file name: arch/win32/startup.py
from __future__ import absolute_import
import ctypes
from ctypes.wintypes import UINT, DWORD, FILETIME, ULONG
import os
import pprint
import subprocess32 as subprocess
import sys
import threading
import time
import win32process
import win32profile
import win32security
import win32event
import win32api
import win32gui
import win32con
from win32com.shell import shell, shellcon
import winerror
import ntsecuritycon
import pywintypes
import pynt
from pynt.constants import HKEY_CURRENT_USER, RM_SHUTDOWN_TYPE_FORCE
from pynt.dlls import advapi32, kernel32, shell32
from pynt.dlls.rstrtmgr import rstrtmgr
from pynt.helpers.registry import create_registry_key, read_registry_value, registry_key
from pynt.helpers.general import windows_error
from pynt.types import RM_UNIQUE_PROCESS
import build_number
from build_number import BUILD_KEY, BRANCH
from contextlib import contextmanager
from hashlib import md5
from dropbox.db_thread import db_thread
from dropbox.event import report
from dropbox.fileutils import check_perms, safe_remove
from dropbox.functions import handle_exceptions
from dropbox.globals import dropbox_globals
from dropbox.i18n import trans
from dropbox.sync_engine_arch.win._lib_import_logic import rollback
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.win32.psapi import PROCESS_MEMORY_COUNTERS, GetProcessMemoryInfo, EnumProcesses
from dropbox.win32.kernel32 import GetLastError
from dropbox.win32.version import WIN8, VISTA, WINXP, WIN2K, WINDOWS_VERSION
from .network_interfaces import generate_adapter_info
from .photouploader.install import check_install_photo
from .internal import RegQueryValueExW, is_admin, is_uac_enabled, get_volumes, GetSystemWow64Directory, create_shortcut, add_shortcut_to_user_location, remove_shortcut_from_user_location, check_nsis_tracing, reset_nsis_tracing, get_installpath, win_strerror, tcp_parameters
from .tray_fix import promote_icon
from .util import hard_exit, is_x64, launch_folder, disable_x64_fs_redirection, FOLDER_INFOTIP, revert_x64_fs_redirection, path_is_remote
SHORTCUT_ICON_OFFSET = 0

def can_migrate_installation():
    TRACE('Checking profiles for multiple linked users')
    try:
        default_profdir = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, -1, 0)
        default_appdata = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, -1, 0)
        my_profdir = os.getenv('USERPROFILE')
        sys_profdir = win32profile.GetProfilesDirectory()
        TRACE('System profile dir: %r Default appdata: %r Profile: %r' % (sys_profdir, default_appdata, default_profdir))
        assert os.path.dirname(default_profdir) == sys_profdir, 'Default profile %r not subdir of %r' % (default_profdir, sys_profdir)
        default_profdir += os.path.sep
        assert default_appdata.startswith(default_profdir), 'Default profile appdata %r not subdir of %r' % (default_appdata, default_profdir)
        appdata_suffix = default_appdata[len(default_profdir):]
        count = 0
        for username in os.listdir(sys_profdir):
            profile_path = os.path.join(sys_profdir, username)
            if not os.path.isdir(profile_path):
                continue
            db_path = os.path.join(profile_path, appdata_suffix, BUILD_KEY)
            if db_path.startswith(default_profdir):
                continue
            TRACE('Looking at %r (%r, parent attrs %x)' % (username, db_path, win32api.GetFileAttributes(profile_path)))
            if os.path.exists(db_path):
                count += 1
                TRACE('Found Dropbox dir (%d total)' % count)
            if count > 1:
                break

        if count > 1:
            TRACE("Migrate check complete (don't migrate)")
            return False
    except Exception:
        unhandled_exc_handler()

    TRACE('Migrate check complete (ok)')
    return True


@handle_exceptions
def install_early_in_boot(app):
    pass


def ensure_latest_version():
    pass


def get_rss():
    try:
        c = PROCESS_MEMORY_COUNTERS()
        if not GetProcessMemoryInfo(win32api.GetCurrentProcess(), ctypes.byref(c), ctypes.sizeof(c)):
            win_errno = GetLastError()
            raise WindowsError(win_errno, win_strerror(win_errno))
        else:
            return c.WorkingSetSize
    except Exception:
        unhandled_exc_handler()

    return -1


@handle_exceptions
def enable_debug_privileges():
    htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), ntsecuritycon.TOKEN_ADJUST_PRIVILEGES | ntsecuritycon.TOKEN_QUERY)
    id = win32security.LookupPrivilegeValue(None, ntsecuritycon.SE_DEBUG_NAME)
    newPrivileges = [(id, ntsecuritycon.SE_PRIVILEGE_ENABLED)]
    win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)


_SHELL_WINDOW_CLASS = 'Shell_TrayWnd'

@contextmanager
def explorer_stopped():
    tray_hwnd = win32gui.FindWindowEx(0, 0, _SHELL_WINDOW_CLASS, '')
    if not tray_hwnd:
        raise Exception("Explorer was not running, can't proceed.")
    manager_handle = DWORD()
    session_key = ctypes.create_unicode_buffer(256)
    sink = FILETIME()
    use_rstrtmgr = True
    if WINDOWS_VERSION >= WIN8:
        use_rstrtmgr = False
    else:
        try:
            rstrtmgr.RmStartSession(ctypes.pointer(manager_handle), 0, session_key)
        except NotImplementedError:
            TRACE('RestartManager dll cannot be found, fall back to old method.')
            use_rstrtmgr = False

    if not use_rstrtmgr:
        TRACE("Can't use Restart Manager, so killing the tray instead.")
        win32gui.PostMessage(tray_hwnd, win32con.WM_QUIT, 0, 0)
        time.sleep(2)
        try:
            yield
        finally:
            kill_process_by_name('explorer.exe')

        return
    TRACE('Using Restart Manager to restart Windows Explorer')
    explorer_pid = win32process.GetWindowThreadProcessId(tray_hwnd)[1]
    explorer_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, explorer_pid)
    try:
        processes = (RM_UNIQUE_PROCESS * 1)()
        processes[0].dwProcessId = explorer_pid
        result = kernel32.kernel32.GetProcessTimes(explorer_handle.handle, ctypes.byref(processes[0].ProcessStartTime), ctypes.byref(sink), ctypes.byref(sink), ctypes.byref(sink))
        if not result:
            raise windows_error(result)
        rstrtmgr.RmRegisterResources(manager_handle, UINT(0), None, UINT(1), processes, UINT(0), None)
        rstrtmgr.RmShutdown(manager_handle, ULONG(RM_SHUTDOWN_TYPE_FORCE), None)
        try:
            yield
        finally:
            rstrtmgr.RmRestart(manager_handle, DWORD(0), None)

    finally:
        win32api.CloseHandle(explorer_handle)
        rstrtmgr.RmEndSession(manager_handle)


def kill_process_by_pid(pid, timeout = 5000):
    try:
        h = win32api.OpenProcess(win32con.PROCESS_TERMINATE | win32con.SYNCHRONIZE, 0, pid)
        try:
            win32process.TerminateProcess(h, 0)
            if timeout > 0:
                win32event.WaitForSingleObject(h, timeout)
        finally:
            win32api.CloseHandle(h)

    except pywintypes.error as e:
        if e.args[0] != 87:
            raise


def kill_process_by_name(target, other_users = False):
    ret = True
    target = target.lower()
    if other_users:
        enable_debug_privileges()
    if WINDOWS_VERSION == WIN2K:

        def get_processname(h):
            return win32process.GetModuleFileNameEx(h, 0)

    else:

        def get_processname(h):
            p = ctypes.create_unicode_buffer(2048)
            ret = ctypes.windll.psapi.GetProcessImageFileNameW(int(h), ctypes.byref(p), 2048)
            assert ret > 0, 'GetProcessImageFileNameW failed (%d)' % win32api.GetLastError()
            return p.value

    mypid = win32process.GetCurrentProcessId()
    for pid in EnumProcesses():
        try:
            if pid == mypid:
                continue
            try:
                h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 0, pid)
            except pywintypes.error as e:
                if e.args[0] in (5, 87):
                    continue
                raise

            h_kill = None
            try:
                processname = get_processname(h)
                if processname.lower().endswith('\\' + target):
                    TRACE('Killing process %r (pid %s)', processname, pid)
                    try:
                        h_kill = win32api.OpenProcess(win32con.PROCESS_TERMINATE | win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 0, pid)
                    except pywintypes.error as e:
                        if e.args[0] in (5, 87):
                            continue
                        raise

                    try:
                        win32process.TerminateProcess(h_kill, 0)
                    except Exception:
                        ret = False
                        unhandled_exc_handler()

            finally:
                win32api.CloseHandle(h)
                if h_kill:
                    win32api.CloseHandle(h_kill)

        except Exception:
            TRACE('While examining %d:' % pid)
            unhandled_exc_handler()

    return ret


_mutex = None

def limit_to_one_instance(appdata_path, path_to_reveal = None):
    global _mutex
    should_exit = False
    if not _mutex:
        try:
            _mutex = win32event.CreateMutex(None, 0, 'dropbox_' + md5(appdata_path.encode('utf8')).hexdigest()[:8])
            hi = win32api.GetLastError()
            TRACE('LIMIT_TO_ONE_INSTANCE: GetLastError2: %d, appdata_path: %r' % (hi, appdata_path))
            if hi == winerror.ERROR_ALREADY_EXISTS:
                should_exit = True
        except Exception:
            TRACE('Dropbox is already running')
            unhandled_exc_handler()
            should_exit = True

    if should_exit:
        try:
            if path_to_reveal is not None:
                TRACE('path_to_reveal was set, showing: %r' % (path_to_reveal,))
                launch_folder(path_to_reveal)
        except Exception:
            unhandled_exc_handler()

        hard_exit(0)


def register_dll(dll_name, should_register = True, disable_x64_fs_redirection_bool = False):
    redir_disabled = False
    old_value = None
    try:
        if disable_x64_fs_redirection_bool:
            old_value = disable_x64_fs_redirection()
            redir_disabled = True
        args = [u'%s\\regsvr32.exe' % win32api.GetSystemDirectory(), u'/s', dll_name]
        if not should_register:
            args[1:1] = [u'/u']
        subprocess.call(args)
    except Exception:
        unhandled_exc_handler()
    finally:
        if redir_disabled:
            revert_x64_fs_redirection(old_value)


@handle_exceptions
def check_shell_extension(dll_name):
    TRACE('Verifying shell extension %s' % dll_name)
    shellext_dll = os.path.join(get_installpath(), dll_name)
    if os.path.exists(shellext_dll):
        info = win32api.GetFileVersionInfo(shellext_dll, '\\')
        most, least = info['FileVersionMS'], info['FileVersionLS']
        try:
            sig = hex(info['Signature'])
        except KeyError:
            sig = 'None'
        except Exception:
            unhandled_exc_handler()
            sig = '<error>'

        TRACE('Found %s: %s.%s.%s.%s signature %s', dll_name, win32api.HIWORD(most), win32api.LOWORD(most), win32api.HIWORD(least), win32api.LOWORD(least), sig)
    else:
        TRACE('Shell extension %s not found' % dll_name)


@handle_exceptions
def first_run(is_update = False, parent_pid = None, parent_dir = None):
    if is_update:
        remove_from_startup_items()


def remove_from_startup_items():
    remove_shortcut_from_user_location(shellcon.CSIDL_STARTUP)


def add_to_startup_items():
    add_shortcut_to_user_location(shellcon.CSIDL_STARTUP, '/systemstartup')


can_configure_startupitem = True

@handle_exceptions
def reroll_startup_items(prefs):
    if prefs.app.mbox.is_secondary:
        TRACE('secondary client; leaving startup items alone')
        return
    TRACE('rerolling startup items')
    if prefs['startupitem']:
        add_to_startup_items()
    else:
        remove_from_startup_items()


needs_shell_touch_on_reindex = True

def initial_link_show_dropbox(dropbox_folder):
    launch_folder(dropbox_folder)


@handle_exceptions
def switch_sidebar_link(dropbox_folder, ignore_missing = False, old_link = None):
    if WINDOWS_VERSION < WINXP:
        return
    shortcut_dirs = []
    shortcut_dirs.append(shell.SHGetFolderPath(0, shellcon.CSIDL_SENDTO, None, 0))
    if WINDOWS_VERSION >= VISTA:
        profile_dir = shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, None, 0)
        shortcut_dirs.append(os.path.join(profile_dir, 'Links'))
    for target_dir in shortcut_dirs:
        if not os.path.isdir(target_dir):
            TRACE("User's %r directory does not exist!", target_dir)
            continue
        shortcut_path = os.path.join(target_dir, BUILD_KEY + '.lnk')
        if os.path.exists(shortcut_path) or ignore_missing:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            icon_fn = os.path.join(get_installpath(), '%s.exe' % (BUILD_KEY,))
            create_shortcut(shortcut_path, dropbox_folder, description=trans(FOLDER_INFOTIP), icon_location=(icon_fn, -SHORTCUT_ICON_OFFSET))


def pre_appdata_use_startup(appdata_path):
    check_nsis_tracing()
    TRACE('DBGVIEWCLEAR')
    pynt.trace.set_trace(TRACE)
    advapi32.advapi32.init()
    kernel32.kernel32.init()
    shell32.shell32.init()
    with create_registry_key(HKEY_CURRENT_USER, u'SOFTWARE\\%s' % BUILD_KEY) as hkey, created:
        if hkey:
            if created:
                TRACE('Created Dropbox registry key')
            else:
                TRACE('Successfully opened Dropbox registry key')
        else:
            TRACE('!! Failed to create Dropbox registry key')
    check_perms(appdata_path, first_time=True, report=True)
    try:
        if path_is_remote(appdata_path):
            report_bad_assumption('Appdata is on a remote filesystem! (%r)', appdata_path)
    except Exception:
        unhandled_exc_handler()

    safe_remove(os.path.join(appdata_path, 'bin', 'Python25.dll'))
    return True


def pre_network_startup(app):
    TRACE('OS Version: %r' % (win32api.GetVersionEx(1),))
    TRACE('Admin: %r UAC: %r' % (is_admin(), is_uac_enabled()))
    reset_nsis_tracing()
    try:
        TRACE('ProfileType: %d', win32profile.GetProfileType())
    except Exception:
        unhandled_exc_handler()

    TRACE('Volume information:')
    try:
        TRACE(pprint.pformat(get_volumes()))
    except Exception:
        unhandled_exc_handler()

    TRACE('Network information:')
    try:
        for nic in generate_adapter_info():
            TRACE('\t%s %s %s', nic.description, nic.adapterName, nic.ipAddressList.ipAddress)

    except Exception:
        unhandled_exc_handler()

    TRACE('Shell information:')
    try:
        shells = get_shell()
        TRACE(pprint.pformat(shells))
        for k, v in shells.iteritems():
            if v and v.lower() != u'explorer.exe':
                TRACE('!! Weird shell: %r', v)
                report_bad_assumption('User running weird shell: %r' % v)

    except Exception:
        unhandled_exc_handler()

    TRACE('TCP Parameters:')
    try:
        params = tcp_parameters()
        if params:
            for k, v in params:
                TRACE('\t%r: %r', k, v)

        else:
            TRACE('\tNone')
    except Exception:
        unhandled_exc_handler()


def get_shell():
    shells = {}
    with registry_key(win32con.HKEY_CURRENT_USER, u'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon') as hkey:
        try:
            shells['USER'] = read_registry_value(hkey, u'Shell')
        except (TypeError, KeyError):
            shells['USER'] = None
        except Exception:
            unhandled_exc_handler()

    with registry_key(win32con.HKEY_LOCAL_MACHINE, u'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon') as hkey:
        try:
            shells['MACHINE'] = read_registry_value(hkey, u'Shell')
        except (TypeError, KeyError):
            shells['MACHINE'] = None
        except Exception:
            unhandled_exc_handler()

    return shells


def recheck_shell_extensions():
    ret = False
    if getattr(build_number, 'DROPBOXEXT_VERSION'):
        TRACE('Checking shell extensions:')
        for shellext in ('DropboxExt.dll',
         'DropboxExt64.dll',
         'DropboxExt.%s.dll' % build_number.DROPBOXEXT_VERSION,
         'DropboxExt64.%s.dll' % build_number.DROPBOXEXT_VERSION):
            try:
                if os.path.exists(os.path.join(get_installpath(), shellext)):
                    check_shell_extension(shellext)
            except Exception:
                unhandled_exc_handler()

        shellext32 = os.path.join(get_installpath(), 'DropboxExt.%s.dll' % build_number.DROPBOXEXT_VERSION)
        shellext64 = os.path.join(get_installpath(), 'DropboxExt64.%s.dll' % build_number.DROPBOXEXT_VERSION)
        to_register_lst = [shellext64, shellext32] if is_x64() else [shellext32]

        def assert_properly_registered(the_shellext):
            assert os.path.exists(the_shellext), 'No %s exists!' % the_shellext
            TRACE('found shellext at %s' % the_shellext)
            if is_x64() and '64' in the_shellext:
                hkey = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, 'SOFTWARE\\Classes\\CLSID\\{FB314ED9-A251-47B7-93E1-CDD82E34AF8B}\\InProcServer32', 0, win32con.KEY_READ | win32con.KEY_WOW64_64KEY)
                try:
                    value, val_typ = RegQueryValueExW(hkey, '')
                    assert val_typ == win32con.REG_SZ, 'key exists but is wrong type??'
                    if the_shellext.lower() != value.lower():
                        raise Exception('currently registered 64-Bit shell extension is wrong: %r, really want %r' % (value, the_shellext))
                finally:
                    win32api.RegCloseKey(hkey)

            hkey = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, 'SOFTWARE\\Classes\\CLSID\\{FB314ED9-A251-47B7-93E1-CDD82E34AF8B}\\InProcServer32', 0, win32con.KEY_READ)
            try:
                value, val_typ = RegQueryValueExW(hkey, '')
                assert val_typ == win32con.REG_SZ, 'key exists but is wrong type??'
                if the_shellext.lower() != value.lower():
                    if is_x64():
                        if '.64' in value:
                            raise Exception('on 64bit machine, 64-bit shell extension data in 32-bit registry: %r, really want %r' % (value, the_shellext))
                    else:
                        raise Exception('currently registered 32-bit shell extension is wrong: %r, really want %r' % (value, the_shellext))
            finally:
                win32api.RegCloseKey(hkey)

        for to_register in to_register_lst:
            try:
                assert_properly_registered(to_register)
            except Exception:
                unhandled_exc_handler(False)
                try:
                    TRACE('Re-registering shell extension')
                    ret = True
                    if is_x64() and '64' in to_register:
                        windir = GetSystemWow64Directory()
                    else:
                        windir = win32api.GetSystemDirectory()
                    regsvr32_path = os.path.join(windir, 'regsvr32.exe')
                    TRACE('Registering shell extension %r' % to_register)
                    p = subprocess.Popen([regsvr32_path.encode('mbcs'), '/S', to_register.encode('mbcs')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p.stdin.close()
                    TRACE('regsvr32 returned %r' % p.wait())
                    TRACE('regsvr32 stdout:\n%s' % p.stdout.read())
                    TRACE('regsvr32 stderr:\n%s' % p.stderr.read())
                    assert_properly_registered(to_register)
                except Exception:
                    unhandled_exc_handler(True)
                    TRACE('reregistration failed!')
                else:
                    TRACE('reregistration succeeded')

            else:
                TRACE('Shell extension %s checks out fine' % to_register)

    return ret


def post_init_startup(app):
    pass


MAX_PROMOTION_TRIES = 5

def _fix_explorer(should_promote = False):
    with explorer_stopped():
        if not should_promote:
            return
        promote_icon()


@handle_exceptions
def fix_explorer(app, freshly_linked):
    should_fix = False
    if freshly_linked:
        TRACE('Fixing Explorer because we are freshly linked.')
        should_fix = True
    if app.system_startup:
        TRACE('Fixing Explorer because we are starting up with the system.')
        should_fix = True
    if app.is_first_run and (not app.is_update or app.is_manual_update):
        TRACE('Fixing Explorer because we are started by the installer.')
        should_fix = True
    if not should_fix:
        TRACE('Not fixing explorer ...')
        return
    needs_restart = False
    if app.should_restart_explorer:
        TRACE('NSIS wants us to restart Explorer.')
        needs_restart = True
    if recheck_shell_extensions():
        TRACE('The shell extension check wants us to restart Explorer.')
        needs_restart = True
    is_promoted = app.config.get('tray_promoted', False)
    num_failures = app.config.get('tray_promotion_failures', 0)
    should_promote = not is_promoted and num_failures < MAX_PROMOTION_TRIES
    if should_promote:
        TRACE('The tray icon is misplaced, we want to restart Explorer.')
        needs_restart = True
    if not needs_restart:
        TRACE("We don't need to restart Explorer.")
        return
    try:
        _fix_explorer(should_promote)
    except Exception:
        unhandled_exc_handler()
        num_failures += 1
        app.config['tray_promotion_failures'] = num_failures
        app.config['tray_promoted'] = False
        report('tray_icon_promotion', success=False, failures=num_failures)
    else:
        app.config['tray_promoted'] = True
        report('tray_icon_promotion', success=True)


def post_link_startup(app, freshly_linked):
    check_install_photo(app)
    fix_explorer(app, freshly_linked)


def post_tour_startup(app, freshly_linked):
    pass


def wait_wx_preconditions():
    return True


def unlink(unlink_cookie, is_uninstall):
    if not is_uninstall or not unlink_cookie:
        return
    try:
        libraries_moved = unlink_cookie.get('libraries_moved', None)
        if libraries_moved:
            TRACE('Prompting user to rollback their libraries')
            msg = trans(u'Would you like Dropbox to move your libraries (%s) back to their original locations?') % ', '.join(libraries_moved.keys())
            dlg_result = win32gui.MessageBox(None, msg, u'Dropbox', win32con.MB_YESNO | win32con.MB_DEFBUTTON1 | win32con.MB_ICONQUESTION)
            success = False
            while not success and dlg_result in (win32con.IDYES, win32con.IDRETRY):
                TRACE('User requested we move their libraries back to original locations!')
                success = rollback(libraries_moved)
                if not success:
                    msg = trans(u"The following libraries (%s) couldn't be moved, possibly because files inside are being used. Please close all other applications and try again.")
                    msg %= ', '.join(libraries_moved.keys())
                    dlg_result = win32gui.MessageBox(None, msg, u'Dropbox', win32con.MB_RETRYCANCEL | win32con.MB_ICONWARNING)

    except Exception:
        unhandled_exc_handler()
