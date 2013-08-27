#Embedded file name: arch/win32/photouploader/install.py
import ctypes
import os
import shutil
import subprocess32 as subprocess
import sys
import win32con
import build_number
import PhotoUploaderLib
from _winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, REG_SZ, SetValue
from comtypes import BSTR
from comtypes.client import CreateObject
from comtypes.GUID import GUID
from win32com.shell import shellcon
from build_number import BUILD_KEY
from dropbox.event import report
from dropbox.functions import handle_exceptions
from dropbox.i18n import trans
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.win32.version import WINDOWS_VERSION
from pynt.constants import ERROR_ACCESS_DENIED, KEY_ALL_ACCESS, KEY_READ, KEY_WOW64_64KEY
from pynt.helpers.com import register_tlb, unregister_tlb
from pynt.helpers.general import windows_error
from pynt.helpers.registry import create_registry_key, delete_registry_tree, delete_regkey_if_empty, enum_registry_values, has_values, hkey_to_str, read_registry_value, registry_key, safe_delete_regkey, safe_delete_regvalue, set_registry_value
from ui.wxpython.dialogs import ElevationDialog
from .autoplay_defaults import set_old_default_autoplay
from .autoplay_event_handler import AutoplayEventHandler
from .autoplay_proxy import DropboxAutoplayProxy, DropboxAutoplayProxyImpl
from .constants import AUTOPLAY_KEY, DROPBOX_AUTOPLAY_CLSID, DROPBOX_AUTOPLAY_PROGID, DROPBOX_AUTOPLAY_VERNO, DROPBOX_AUTOPLAY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROXY_CLSID, DROPBOX_AUTOPLAY_PROXY_PROGID, DROPBOX_AUTOPLAY_PROXY_VERNO, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME, DROPBOX_DATA_CALLBACK_CLSID, DROPBOX_DATA_CALLBACK_PROGID, DROPBOX_DATA_CALLBACK_VERNO, DROPBOX_DATA_CALLBACK_DESC, USE_PHOTOUPLOADER, USE_WIA, USE_PROXY, VOLUME_EVENTS
from .portable_device import IWiaDevMgr
from .wiacallback import DropboxWiaDataCallback
from ..constants import photo_update_name
from ..internal import get_user_folder_path, is_admin, ShellExecuteW
INSTALL_PHOTO_ON_RESTART = 'install_photo_on_restart'

@handle_exceptions
def check_install_photo(app):
    if not USE_PHOTOUPLOADER:
        return
    should_install = app.config.get(INSTALL_PHOTO_ON_RESTART, False)
    TRACE('Install photo components flag: %r, is_update %r', should_install, app.is_update)
    if app.is_update or app.is_first_run:
        installed = is_photouploader_installed()
        TRACE('should_install: %r, winver: %r, photo feature already installed %r', should_install, WINDOWS_VERSION, installed)
        if not USE_PROXY or is_admin():
            report('photo-install', data={'step': 'nsis-install-%s' % ('succeeded' if installed else 'failed')})
        if app.is_update:
            if USE_PROXY and not installed:
                TRACE('Setting install_photo_on_restart flag to true')
                app.config[INSTALL_PHOTO_ON_RESTART] = True
                report('photo-install', data={'step': 'marked-install-on-restart'})
    elif should_install:
        TRACE('Requesting UAC elevation to do photo install')
        elevate_dlg = ElevationDialog(None, title='Dropbox elevation request', message='Dropbox needs permission to update.')
        dlg_result = elevate_dlg.show_modal()
        TRACE('Turning off the install photo on restart flag')
        del app.config[INSTALL_PHOTO_ON_RESTART]
        if dlg_result != elevate_dlg.ELEVATION_DLG_OK:
            report('photo-install', data={'step': 'update-denied'})
            TRACE('!! User declined to allow UAC elevation. Dialog result: %r (if canceled, expect 1 or -1)', dlg_result)
            return
        run_photo_update(app)


if not hasattr(build_number, 'frozen'):
    g_photo_uploader_installed = False
PHOTOUPLOADER_REGKEY = u'Software\\Classes\\%s\\CurVer' % DROPBOX_AUTOPLAY_PROGID
PROXIES_INSTALLED_KEY = u'SOFTWARE\\%s\\AutoplayProxy' % BUILD_KEY
PROXY_REGKEY = u'SOFTWARE\\Classes\\%s\\CurVer' % DROPBOX_AUTOPLAY_PROXY_PROGID

def is_photouploader_installed():
    global g_photo_uploader_installed
    try:
        if not hasattr(build_number, 'frozen'):
            return g_photo_uploader_installed
        if USE_PROXY and is_admin():
            proxy_key_found = False
            with registry_key(HKEY_LOCAL_MACHINE, PROXIES_INSTALLED_KEY, KEY_READ | KEY_WOW64_64KEY) as proxies_key:
                if proxies_key is None:
                    TRACE('No proxies key, returning false')
                    return False
                for value in enum_registry_values(proxies_key):
                    if value.lower() == os.path.dirname(sys.executable).decode('mbcs').lower():
                        TRACE('Found our executable path in the proxies key.')
                        proxy_key_found = True
                        break

            if proxy_key_found:
                verno = get_regclass_version(HKEY_LOCAL_MACHINE, PROXY_REGKEY, KEY_READ | KEY_WOW64_64KEY)
                if verno:
                    TRACE('Installed Dropbox.AutoplayProxyEventHandler is version %d, current version %d', verno, DROPBOX_AUTOPLAY_PROXY_VERNO)
                return verno == DROPBOX_AUTOPLAY_PROXY_VERNO
            else:
                TRACE('No entry in HKLM proxies key!  Returning False!')
                return False
        else:
            verno = get_regclass_version(HKEY_CURRENT_USER, PHOTOUPLOADER_REGKEY)
            if verno:
                TRACE('Installed Dropbox.AutoplayEventHandler is version %d, current version %d', verno, DROPBOX_AUTOPLAY_VERNO)
            return verno == DROPBOX_AUTOPLAY_VERNO
    except Exception:
        unhandled_exc_handler()

    return False


def get_regclass_version(hkey_which, curver_key, perms = KEY_READ):
    try:
        with registry_key(hkey_which, curver_key, perms) as ver_key:
            if ver_key is None:
                TRACE('No class key found for %s', curver_key)
                return
            verno = read_registry_value(ver_key, None)
        verno = int(verno.split('.')[-1])
        return verno
    except Exception:
        unhandled_exc_handler()
        return


def get_proxy_path():
    progfiles_path = get_user_folder_path(shellcon.CSIDL_PROGRAM_FILES, fallback_to_default=True)
    proxy_path = os.path.join(progfiles_path, u'Dropbox', u'DropboxProxy.exe')
    return proxy_path


OLD_PROXY_CMDS = (u'"%s"  /autoplayproxy /device_id:%%1 /event_id:%%2' % get_proxy_path(),)

def get_proxy_cmd():
    proxy_run_cmd = u'"%s" /autoplayproxy /wia /device_id:%%1 /event_id:%%2' % get_proxy_path()
    return proxy_run_cmd


def install_photo_components(as_admin, force = False):
    if not USE_PHOTOUPLOADER:
        TRACE('!! Photo uploads not supported on this version of Windows: %r', WINDOWS_VERSION)
        return
    installed = is_photouploader_installed()
    TRACE('winver: %r, is admin: %r, photo feature already installed: %r', WINDOWS_VERSION, is_admin(), installed)
    if installed and not force:
        TRACE('Photouploader is already installed')
        return
    TRACE('Installing photo components now')
    try:
        if USE_PROXY:
            install_with_proxy(as_admin)
        else:
            install_without_proxy()
    except Exception:
        unhandled_exc_handler()
        uninstall_photo_components(as_admin)
    else:
        TRACE('Photo uploader was installed successfully!')


def install_without_proxy():
    TRACE('Installing photouploader without proxy (Windows 7+)')
    remove_regkeys()
    register_class(HKEY_CURRENT_USER, AutoplayEventHandler, DROPBOX_AUTOPLAY_CLSID, DROPBOX_AUTOPLAY_PROGID, DROPBOX_AUTOPLAY_VERNO, u'Dropbox Autoplay COM Server', u'%s /autoplay' % sys.executable.decode('mbcs'))
    register_drop_target(HKEY_CURRENT_USER, DROPBOX_AUTOPLAY_CLSID, DROPBOX_AUTOPLAY_PROGID)
    add_autoplay_regkeys(HKEY_CURRENT_USER, DROPBOX_AUTOPLAY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROGID, sys.executable)
    add_wpd_regkeys(HKEY_CURRENT_USER, DROPBOX_AUTOPLAY_HANDLER_NAME)
    TRACE('Registering tlb for user for autoplay')
    register_tlb(sys.executable, this_user_only=True)


def install_with_proxy(as_admin):
    if as_admin:
        TRACE('Running with administrator privileges, possibly impersonating other user')
        verno = get_regclass_version(HKEY_LOCAL_MACHINE, PROXY_REGKEY, KEY_READ | KEY_WOW64_64KEY)
        if verno and verno < DROPBOX_AUTOPLAY_PROXY_VERNO:
            uninstall_proxy()
        TRACE('Installing photouploader with proxy (for XP/Vista)')
        proxy_path = get_proxy_path()
        register_class(HKEY_LOCAL_MACHINE, DropboxAutoplayProxy, DROPBOX_AUTOPLAY_PROXY_CLSID, DROPBOX_AUTOPLAY_PROXY_PROGID, DROPBOX_AUTOPLAY_PROXY_VERNO, u'Dropbox Autoplay Proxy COM Server', u'%s /autoplayproxy' % get_proxy_path())
        register_drop_target(HKEY_LOCAL_MACHINE, DROPBOX_AUTOPLAY_PROXY_CLSID, DROPBOX_AUTOPLAY_PROXY_PROGID)
        with create_registry_key(HKEY_LOCAL_MACHINE, PROXIES_INSTALLED_KEY, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as key, _:
            TRACE("Recording this user's Dropbox installation at %r", sys.executable)
            if not key or not set_registry_value(key, os.path.dirname(sys.executable).decode('mbcs'), REG_SZ, u''):
                raise Exception('Registry error: failed to record in HKLM AutoplayProxy')
        copy_proxy_binaries()
        add_autoplay_regkeys(HKEY_LOCAL_MACHINE, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROXY_PROGID, proxy_path)
        TRACE('Registering tlb for all users for autoplay')
        register_tlb(proxy_path, this_user_only=False)
        if not USE_WIA:
            add_wpd_regkeys(HKEY_LOCAL_MACHINE, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME)
        else:
            register_for_wia()
    else:
        TRACE('Running as the user')
        remove_regkeys()
        register_class(HKEY_CURRENT_USER, AutoplayEventHandler, DROPBOX_AUTOPLAY_CLSID, DROPBOX_AUTOPLAY_PROGID, DROPBOX_AUTOPLAY_VERNO, u'Dropbox Autoplay COM Server', u'%s /autoplay' % sys.executable.decode('mbcs'))
        register_drop_target(HKEY_CURRENT_USER, DROPBOX_AUTOPLAY_CLSID, DROPBOX_AUTOPLAY_PROGID)
        if USE_WIA:
            register_class(HKEY_CURRENT_USER, DropboxWiaDataCallback, DROPBOX_DATA_CALLBACK_CLSID, DROPBOX_DATA_CALLBACK_PROGID, DROPBOX_DATA_CALLBACK_VERNO, DROPBOX_DATA_CALLBACK_DESC, u'%s /wiacallback' % sys.executable.decode('mbcs'))


def register_for_wia():
    proxy_path = get_proxy_path()
    try:
        pWiaDevMgr = CreateObject(progid='WiaDevMgr', interface=IWiaDevMgr)
        proxy_cmd = get_proxy_cmd()
        TRACE('Registering us for WIA events with cmdline to run = %r', proxy_cmd)
        WIA_REGISTER_EVENT_CALLBACK = 1
        WIA_EVENT_DEVICE_CONNECTED = GUID('{A28BBADE-64B6-11D2-A231-00C04FA31809}')
        import_string = trans(u'Import photos and videos to Dropbox')
        pWiaDevMgr.RegisterEventCallbackProgram(WIA_REGISTER_EVENT_CALLBACK, None, WIA_EVENT_DEVICE_CONNECTED, BSTR(proxy_cmd), BSTR(BUILD_KEY), BSTR(import_string), BSTR(proxy_path + ',0'))
    except Exception:
        if os.path.exists(proxy_path):
            TRACE('!! Elevation succeeded, failed to register WIA events!  We will not receive USB camera events!')
        else:
            TRACE('!! Failed to register for WIA events! Elevation may have been denied')
        raise


DROPBOX_INVOKE_VERB = u'import'

def register_class(hkey, cls, co_clsid, co_progid, co_verno, co_desc, server_path, permissions = KEY_ALL_ACCESS | KEY_WOW64_64KEY):
    root = u'Software\\Classes'
    entries = [(u'\\CLSID\\%s' % co_clsid, co_desc),
     (u'\\CLSID\\%s\\LocalServer32' % co_clsid, server_path),
     (u'\\CLSID\\%s\\ProgID' % co_clsid, u'%s.%d' % (co_progid, co_verno)),
     (u'\\CLSID\\%s\\Typelib' % co_clsid, cls._reg_typelib_[0]),
     (u'\\CLSID\\%s\\VersionIndependentProgID' % co_clsid, co_progid),
     (u'\\%s.%d' % (co_progid, co_verno), co_desc),
     (u'\\%s.%d\\CLSID' % (co_progid, co_verno), co_clsid),
     (u'\\%s' % co_progid, co_desc),
     (u'\\%s\\CLSID' % co_progid, co_clsid),
     (u'\\%s\\CurVer' % co_progid, u'%s.%d' % (co_progid, co_verno))]
    for reg_key, reg_value in entries:
        full_key = u'%s%s' % (root, reg_key)
        TRACE('Creating value [%s\\%s] %s', hkey_to_str(hkey), full_key, reg_value)
        with create_registry_key(hkey, full_key, permissions) as key, _:
            if not key or not set_registry_value(key, u'', REG_SZ, reg_value):
                raise Exception('Registry error: failed to register the %s class' % co_progid)


def register_drop_target(hkey, co_clsid, co_progid):
    key_name = u'Software\\Classes\\%s\\shell\\%s\\DropTarget' % (co_progid, DROPBOX_INVOKE_VERB)
    with create_registry_key(hkey, key_name, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as key, _:
        value_name = u'CLSID'
        TRACE('Setting value %s %s to %r', key_name, value_name, co_clsid)
        if not key or not set_registry_value(key, value_name, REG_SZ, co_clsid):
            raise Exception('Registry error: failed to register %s for DropTarget' % co_progid)


def copy_proxy_binaries():
    proxy_path = get_proxy_path()
    proxy_dir = os.path.dirname(proxy_path)
    if not os.path.exists(proxy_dir):
        os.makedirs(proxy_dir)
    shutil.copy2(sys.executable, proxy_path)
    msvc_name = 'Microsoft.VC90.CRT'
    dropbox_dir = os.path.dirname(sys.executable)
    msvc_dir = os.path.join(proxy_dir, msvc_name)
    if not os.path.exists(msvc_dir):
        os.makedirs(msvc_dir)
    for path_components in [(msvc_name, 'msvcm90.dll'),
     (msvc_name, 'msvcr90.dll'),
     (msvc_name, 'msvcp90.dll'),
     ('icudt.dll',),
     ('libcef.dll',),
     ('wxmsw28uh_vc.dll',)]:
        from_path = os.path.join(dropbox_dir, *path_components)
        to_path = os.path.join(proxy_dir, *path_components)
        shutil.copy2(from_path, to_path)


WPD_EVENTS = (u'Function\\{23F05BBC-15DE-4C2A-A55B-A9AF5CE412EF}', u'Source\\{9261B03C-3D78-4519-85E3-02C5E1F50BB9}', u'Source\\{EF2107D5-A52A-4243-A26B-62D4176D7603}')

def add_autoplay_regkeys(hk_which, handler_name, progid, binary):
    for event_name in VOLUME_EVENTS:
        keyname = u'%s\\EventHandlers\\%s' % (AUTOPLAY_KEY, event_name)
        TRACE('Adding %r %r %r', hkey_to_str(hk_which), keyname, handler_name)
        with create_registry_key(hk_which, keyname, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as pynt_key, _:
            if not pynt_key or not set_registry_value(pynt_key, handler_name, REG_SZ, u''):
                raise Exception('Registry error: Failed to add Dropbox as autoplay handler for %s' % event_name)

    root = u'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\AutoplayHandlers\\EventHandlersDefaultSelection'
    for event in VOLUME_EVENTS:
        TRACE('Creating value %r %r', u'%s\\%s' % (root, event), handler_name)
        SetValue(HKEY_CURRENT_USER, u'%s\\%s' % (root, event), REG_SZ, handler_name)

    keyname = u'%s\\Handlers\\%s' % (AUTOPLAY_KEY, handler_name)
    TRACE('Populating %r %r', hkey_to_str(hk_which), keyname)
    with create_registry_key(hk_which, keyname, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as pynt_key, _:
        if not pynt_key:
            raise Exception('Registry error: Failed to create %s' % keyname)
        AUTOPLAY_ACTION = trans(u'Import photos and videos')
        values = [(u'Action', AUTOPLAY_ACTION),
         (u'DefaultIcon', binary),
         (u'Provider', BUILD_KEY),
         (u'ProgID', progid),
         (u'InvokeProgId', progid),
         (u'InvokeVerb', DROPBOX_INVOKE_VERB)]
        for valuename, value in values:
            if not set_registry_value(pynt_key, valuename, REG_SZ, value):
                raise Exception('Registry error: Failed to populate Dropbox AutoplayHandler key')


def add_wpd_regkeys(hk_which, handler_name):
    for event_guid in WPD_EVENTS:
        keyname = u'%s\\EventHandlers\\WPD\\%s' % (AUTOPLAY_KEY, event_guid)
        with create_registry_key(hk_which, keyname, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as pynt_key, _:
            TRACE('Adding %r %r %r', hkey_to_str(hk_which), keyname, handler_name)
            if not pynt_key or not set_registry_value(pynt_key, handler_name, REG_SZ, u''):
                raise Exception('Registry error: Failed to register Dropbox for WPD events')


@handle_exceptions
def remove_regkeys():
    keys = [u'Software\\Classes\\CLSID\\%s' % DROPBOX_AUTOPLAY_CLSID,
     u'Software\\Classes\\%s' % DROPBOX_AUTOPLAY_PROGID,
     u'Software\\Classes\\CLSID\\%s' % DROPBOX_DATA_CALLBACK_CLSID,
     u'Software\\Classes\\%s' % DROPBOX_DATA_CALLBACK_PROGID]
    keys.extend((u'Software\\Classes\\%s.%d' % (DROPBOX_AUTOPLAY_PROGID, verno) for verno in xrange(1, DROPBOX_AUTOPLAY_VERNO + 1)))
    keys.extend((u'Software\\Classes\\%s.%d' % (DROPBOX_DATA_CALLBACK_PROGID, verno) for verno in xrange(1, DROPBOX_DATA_CALLBACK_VERNO + 1)))
    for keyname in keys:
        try:
            TRACE('Removing %r %r', 'HKCU', keyname)
            delete_registry_tree(HKEY_CURRENT_USER, keyname)
        except Exception:
            unhandled_exc_handler()

    remove_autoplay_regkeys(hk_which=HKEY_CURRENT_USER, handler_name=DROPBOX_AUTOPLAY_HANDLER_NAME, delete_all_the_keys=True)


@handle_exceptions
def run_photo_update(app):
    global g_photo_uploader_installed
    if not hasattr(build_number, 'frozen'):
        g_photo_uploader_installed = True
        return
    report('photo-install', data={'step': 'launching-update'})
    args = ''
    filename = os.path.join(os.path.dirname(sys.executable), '%s%s.exe' % (BUILD_KEY, photo_update_name))
    ret = 1
    try:
        ret = subprocess.call(filename + ' ' + args)
        TRACE('subprocess.call of Dropbox%s returned %r', photo_update_name, ret)
    except Exception:
        unhandled_exc_handler()
        ret = ctypes.windll.Shell32.ShellExecuteW(0, u'open', unicode(filename), unicode(args), os.path.dirname(unicode(filename)), win32con.SW_HIDE)
        TRACE('ShellExecuteW of Dropbox%s %r', photo_update_name, ret)
        if ret > 32:
            ret = 0
        else:
            raise windows_error(ret)
    finally:
        success = ret == 0
        report('photo-install', data={'step': 'update-exe-launch-%s' % ('succeeded' if success else 'failed')})
        installed = is_photouploader_installed()
        report('photo-install', data={'step': 'photo-install-%s' % ('succeeded' if installed else 'failed')})


def remove_autoplay_regkeys(hk_which, handler_name, delete_all_the_keys):
    for event_name in VOLUME_EVENTS:
        safe_delete_regvalue(hk_which, u'%s\\EventHandlers\\%s' % (AUTOPLAY_KEY, event_name), handler_name, delete_key=delete_all_the_keys, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)

    for event_guid in WPD_EVENTS:
        safe_delete_regvalue(hk_which, u'%s\\EventHandlers\\WPD\\%s' % (AUTOPLAY_KEY, event_guid), handler_name, delete_key=delete_all_the_keys, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)

    keyname = u'%s\\Handlers\\%s' % (AUTOPLAY_KEY, handler_name)
    TRACE('Removing %r %r', hkey_to_str(hk_which), keyname)
    delete_registry_tree(hk_which, keyname, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)
    if delete_all_the_keys:
        wpd_event_keys = [u'%s\\EventHandlers\\WPD\\Function' % AUTOPLAY_KEY,
         u'%s\\EventHandlers\\WPD\\Source' % AUTOPLAY_KEY,
         u'%s\\EventHandlers\\WPD' % AUTOPLAY_KEY,
         u'%s\\EventHandlers' % AUTOPLAY_KEY]
        for wpd_event_key in wpd_event_keys:
            TRACE('Cleaning up if empty: %r %r', hkey_to_str(hk_which), wpd_event_key)
            safe_delete_regkey(hk_which, wpd_event_key, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)

        keyname = u'%s\\Handlers' % AUTOPLAY_KEY
        TRACE('Cleaning up if empty: %r %r', hkey_to_str(hk_which), keyname)
        delete_regkey_if_empty(key=hk_which, subkey=keyname, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)


@handle_exceptions
def uninstall_photo_components(as_admin):
    if not USE_PHOTOUPLOADER:
        return
    if not USE_PROXY:
        remove_regkeys()
        try:
            TRACE('Removing all Dropbox autoplay default entries')
            set_old_default_autoplay(old_handlers={})
        except Exception:
            unhandled_exc_handler()

        TRACE('Unregistering tlb for user for autoplay')
        try:
            str_lib_id, major_version_number, minor_version_number = PhotoUploaderLib.Library._reg_typelib_
            unregister_tlb(str_lib_id, major_version_number, minor_version_number, this_user_only=True)
        except Exception:
            unhandled_exc_handler()

    elif as_admin:
        TRACE("Deleting our executable's entry in HKLM\\Dropbox\\AutoplayProxy")
        safe_delete_regvalue(HKEY_LOCAL_MACHINE, PROXIES_INSTALLED_KEY, os.path.dirname(sys.executable).decode('mbcs'), permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)
        TRACE('Checking to see if the autoplay proxy needs to be uninstalled')
        with registry_key(HKEY_LOCAL_MACHINE, PROXIES_INSTALLED_KEY, KEY_ALL_ACCESS | KEY_WOW64_64KEY) as proxies_key:
            if proxies_key is None:
                TRACE('%r %r was not present. Skipping proxy uninstall', 'HKLM', PROXIES_INSTALLED_KEY)
                return
            if not has_values(proxies_key):
                uninstall_proxy()
    else:
        remove_regkeys()


@handle_exceptions
def uninstall_proxy():
    TRACE('Cleaning up autoplay proxy')
    if USE_WIA:
        unregister_for_wia()
    TRACE('Removing proxy regkeys')
    remove_autoplay_regkeys(hk_which=HKEY_LOCAL_MACHINE, handler_name=DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME, delete_all_the_keys=False)
    keys = [PROXIES_INSTALLED_KEY,
     u'SOFTWARE\\Dropbox',
     u'Software\\Classes\\CLSID\\%s' % DROPBOX_AUTOPLAY_PROXY_CLSID,
     u'Software\\Classes\\%s' % DROPBOX_AUTOPLAY_PROXY_PROGID]
    keys.extend((u'Software\\Classes\\%s.%d' % (DROPBOX_AUTOPLAY_PROXY_PROGID, verno) for verno in xrange(1, DROPBOX_AUTOPLAY_PROXY_VERNO + 1)))
    for keyname in keys:
        ret = delete_registry_tree(HKEY_LOCAL_MACHINE, keyname, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY)
        TRACE('del_reg_tree of %r %r returned %r', HKEY_LOCAL_MACHINE, keyname, ret)

    str_lib_id, major_version_number, minor_version_number = PhotoUploaderLib.Library._reg_typelib_
    TRACE('Unregistering tlb for all users')
    unregister_tlb(str_lib_id, major_version_number, minor_version_number, this_user_only=False)
    proxy_path = get_proxy_path()
    TRACE('Deleting the proxy binary from %r', proxy_path)
    try:
        shutil.rmtree(os.path.dirname(proxy_path))
    except WindowsError as e:
        if e.winerror == ERROR_ACCESS_DENIED:
            TRACE('!! This file needs to get deleted on reboot!')
            unhandled_exc_handler()
    except Exception:
        unhandled_exc_handler()


@handle_exceptions
def unregister_for_wia():
    pWiaDevMgr = CreateObject(progid='WiaDevMgr', interface=IWiaDevMgr)
    TRACE('Unregistering us for WIA events')
    WIA_UNREGISTER_EVENT_CALLBACK = 2
    WIA_EVENT_DEVICE_CONNECTED = GUID('{A28BBADE-64B6-11D2-A231-00C04FA31809}')
    proxy_path = get_proxy_path() + ',0'
    proxy_cmd = get_proxy_cmd()
    try:
        pWiaDevMgr.RegisterEventCallbackProgram(WIA_UNREGISTER_EVENT_CALLBACK, None, WIA_EVENT_DEVICE_CONNECTED, BSTR(proxy_cmd), BSTR(BUILD_KEY), BSTR(''), BSTR(proxy_path))
    except Exception:
        unhandled_exc_handler()
    else:
        TRACE('Wia unregistration succeeded!')

    try:
        pWiaDevMgr.RegisterEventCallbackCLSID(WIA_UNREGISTER_EVENT_CALLBACK, None, WIA_EVENT_DEVICE_CONNECTED, ctypes.byref(DropboxAutoplayProxyImpl._reg_clsid_), BSTR(BUILD_KEY), BSTR(''), BSTR(proxy_path))
    except Exception:
        pass
    else:
        TRACE('Successfully uninstalled old WIA event callback CLSID')

    for old_cmd in OLD_PROXY_CMDS:
        try:
            pWiaDevMgr.RegisterEventCallbackProgram(WIA_UNREGISTER_EVENT_CALLBACK, None, WIA_EVENT_DEVICE_CONNECTED, BSTR(old_cmd), BSTR(BUILD_KEY), BSTR(''), BSTR(proxy_path))
        except Exception:
            pass
        else:
            TRACE('Uninstalled old WIA event callback %r', old_cmd)
