#Embedded file name: arch/mac/startup.py
from __future__ import absolute_import
import threading
import subprocess32 as subprocess
import os
import signal
import shutil
import resource
import fcntl
import pwd
from plistlib import readPlist
from xml.parsers.expat import ExpatError
from Foundation import NSUserDefaults, NSString
import build_number
from build_number import BUILD_KEY
import pymac
from pymac.dlls import Carbon, preload_dlls
from pymac.helpers.authorization import AuthorizationCanceled, request_authorization_from_user_and_run
from pymac.helpers.disk import get_volume_desc
from pymac.helpers.process import find_instances, get_process_argv
from pymac.helpers.task_info import get_basic_task_info
from pymac.types import ProcessSerialNumber
from dropbox.dirtraverse import Directory
from dropbox.fastwalk_bridge import fastwalk_strict
from dropbox.functions import loop_delete
from dropbox.globals import dropbox_globals
from dropbox.i18n import trans
from dropbox.mac.helper_installer import verify_helper_installer, install_dropbox_helper_installer
from dropbox.mac.internal import get_contents_root, osa_send_piped, binaries_ready, post_linked_yet, get_app_path
from dropbox.mac.version import LEOPARD, MAC_VERSION, SNOW_LEOPARD, TIGER
from dropbox.trace import unhandled_exc_handler, TRACE, report_bad_assumption
from distutils.version import LooseVersion
import arch
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY
from ..posix_common.util import kill_pid
from .constants import get_alt_install_path
from .dmg_starter import decide_dmg_action, dmg_target_volume, is_on_installer
from .util import kill_other_instances, hard_exit, get_drives
import dropbox.native_threading
add_path_to_shared_list = None
get_all_login_matches = None
remove_path_from_shared_list = None
SFL_FAVORITES = None
SFL_LOGIN = None

def print_shared_list(list_type):
    return 'print_shared_list(%s) not implemented' % (list_type,)


def check_other_version():
    alt_install_path = get_alt_install_path()
    alt_install_plist_path = os.path.join(alt_install_path, u'Contents', u'Info.plist')
    if os.path.exists(alt_install_plist_path):
        try:
            plist = readPlist(alt_install_plist_path)
            try:
                version = plist['CFBundleVersion'].strip()
                TRACE('Found version %s in %s', version, alt_install_path)
                if LooseVersion(version) > LooseVersion(build_number.VERSION):
                    return alt_install_path
            except KeyError:
                return None

        except ExpatError:
            return None


def ensure_latest_version():
    alt_path = check_other_version()
    if not alt_path:
        return
    launch_exe = os.path.join(alt_path, u'Contents', u'MacOS', BUILD_KEY)
    launch_args = [launch_exe, u'/newerversion'] + os.sys.argv[2:]
    TRACE('launching newer version from alt path. Command: %s', launch_args)
    subprocess.check_call(launch_args, close_fds=True)
    raise Exception('The newer version exited without killing us')


if MAC_VERSION > TIGER:
    try:
        from pymac.helpers.shared_file_list import add_path_to_shared_list, get_all_login_matches, print_shared_list, remove_path_from_shared_list, SFL_FAVORITES, SFL_LOGIN
    except Exception:
        unhandled_exc_handler(True)

def get_rss():
    try:
        return get_basic_task_info(os.getpid()).resident_size
    except Exception:
        unhandled_exc_handler()
        return -1


def install_early_in_boot(app):
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    dropbox.native_threading.configure_wakeup_thread()
    if hasattr(build_number, 'frozen'):
        cmd = None
        try:
            cmd = decide_dmg_action(get_app_path(), u'/Applications', _get_permissions_from_user, kill_other_instances=kill_other_instances)
            TRACE('command is %s', cmd)
            if cmd is None:
                target_volume = dmg_target_volume()
                try:
                    _unmount_dmg(target_volume)
                except Exception:
                    unhandled_exc_handler()

                return
            TRACE('Run from dmg; executing %s directly' % cmd)
            subprocess.Popen(cmd, close_fds=True)
        except Exception:
            unhandled_exc_handler()
            try:
                import EasyDialogs
                EasyDialogs.Message(u'There was an error installing Dropbox; try dragging Dropbox into your Applications folder.')
            except Exception:
                pass

        hard_exit()


def _unmount_dmg(path):
    if not os.path.exists(path) or get_app_path().startswith(path):
        return
    mount_point = pymac.helpers.disk.get_mount_point_for_path(path)
    if mount_point != '/' and pymac.helpers.disk.is_ejectable(mount_point):
        TRACE('about to diskutil eject %s', mount_point)
        subprocess.Popen(['diskutil', 'eject', mount_point], stdout=subprocess.PIPE, stderr=open('/dev/null', 'wb'), close_fds=True)


def _get_permissions_from_user(cmd, argv, auth_text = None):
    output = None
    retval = False
    try:
        channel = request_authorization_from_user_and_run(cmd, argv, auth_text)
        retval = True
        if channel:
            try:
                output = channel.read()
            finally:
                try:
                    channel.close()
                except Exception:
                    unhandled_exc_handler()

    except AuthorizationCanceled:
        pass

    return (retval, output)


def remove_from_startup_items():
    should_add = False
    if hasattr(build_number, 'frozen'):
        remove_script = 'tell application "System Events" to delete every login item whose Path contains "%s.app"' % BUILD_KEY
        try:
            p = osa_send_piped(remove_script)
            TRACE('Removed existing startup item')
            should_add = True
        except Exception:
            unhandled_exc_handler()

    return should_add


startup_item_add_template = '\ntell application "System Events"\n  make new login item with properties { path: "%s", hidden:false } at end\nend tell\n'

def add_to_startup_items():
    if hasattr(build_number, 'frozen'):
        app_path = get_app_path()
        if is_on_installer(app_path):
            return
        if app_path == get_alt_install_path():
            return
        try:
            if get_all_login_matches:
                matches = get_all_login_matches('%s.app' % (BUILD_KEY,), unhandled_exc_handler)
                if matches == [app_path]:
                    return
                if matches:
                    remove_from_startup_items()
        except Exception:
            unhandled_exc_handler()

        if add_path_to_shared_list:
            try:
                add_path_to_shared_list(app_path, SFL_LOGIN)
                TRACE('added ourselves to startup items using add_path_to_shared_list')
            except Exception:
                unhandled_exc_handler()
            else:
                return

        try:
            osa_send_piped(startup_item_add_template % app_path.encode('utf-8'), async=True)
            TRACE('Added startup item via OSA script')
        except Exception:
            unhandled_exc_handler()


can_configure_startupitem = True

def reroll_startup_items(prefs):
    if prefs.app.mbox.is_secondary:
        TRACE('secondary client; leaving startup items alone')
        return
    TRACE('rerolling startup items')
    if MAC_VERSION >= SNOW_LEOPARD:
        try:
            TRACE('before: %s', print_shared_list(SFL_LOGIN))
        except Exception:
            unhandled_exc_handler()

    try:
        if prefs['startupitem']:
            add_to_startup_items()
        else:
            remove_from_startup_items()
    except Exception:
        unhandled_exc_handler()

    if MAC_VERSION >= SNOW_LEOPARD:
        try:
            TRACE('after rerolling: %s', print_shared_list(SFL_LOGIN))
        except Exception:
            unhandled_exc_handler()


needs_shell_touch_on_reindex = MAC_VERSION < SNOW_LEOPARD

def cleanup_app_files():
    if not hasattr(build_number, 'frozen'):
        return
    try:
        contents_path = get_contents_root()
        contents_dir = os.path.dirname(contents_path)

        def loop_delete_helper1(dirent):
            if dirent.name != 'Contents':
                fullpath = os.path.join(contents_dir, dirent.name)
                if dirent.type == 'directory':
                    shutil.rmtree(fullpath)
                else:
                    os.remove(fullpath)
                return True
            else:
                return False

        try:
            loop_delete(Directory(contents_dir), loop_delete_helper1)
        except Exception:
            unhandled_exc_handler()

        lst = os.path.join(contents_path, u'Dropbox-files.lst')
        if os.path.exists(lst):
            with open(lst) as f:
                files = set((os.path.normpath(os.path.join(contents_path, x.strip().decode('utf8'))) for x in f))

                def loop_delete_helper(dirent):
                    if dirent.fullpath not in files:
                        TRACE("Deleting %r because it doesn't belong.", dirent.fullpath)
                        if dirent.type == FILE_TYPE_DIRECTORY:
                            shutil.rmtree(dirent.fullpath)
                        else:
                            os.remove(dirent.fullpath)
                        return True
                    else:
                        return False

                for dir_to_explore, ents in fastwalk_strict(contents_path, follow_symlinks=False):
                    loop_delete(ents, loop_delete_helper)

            os.remove(lst)
    except Exception:
        unhandled_exc_handler()


is_first_run_update = False

def first_run(is_update = False, parent_pid = None, parent_dir = None):
    global is_first_run_update
    if parent_pid is not None:
        try:
            if os.getppid() != parent_pid:
                report_bad_assumption("getppid() %d and parent_pid %d don't match!", os.getppid(), parent_pid)
        except Exception:
            unhandled_exc_handler()

        try:
            os.kill(parent_pid, signal.SIGKILL)
            TRACE('killed parent %d' % parent_pid)
        except Exception:
            unhandled_exc_handler()

    kill_other_instances()
    if is_update:
        try:
            os.chmod(get_contents_root(), 493)
        except Exception:
            unhandled_exc_handler()

    is_first_run_update = is_update


def update_and_fix_binaries_if_needed(freshly_linked = False):
    if not verify_helper_installer():
        if is_first_run_update:
            authorization_text = trans(u'Please enter your computer password for Dropbox to successfully update.')
        else:
            authorization_text = trans(u'Please enter your computer password for Dropbox to work properly.')
        authorization_text += u'\n\n'
        if not install_dropbox_helper_installer(auth_text=authorization_text, keep_focus=freshly_linked):
            TRACE('No Dropbox Helper was installed.  Not verifying binaries.')
            binaries_ready.set(False)
            return
    binaries_ready.set(True)


sidebar_add_template = '\nset pbox to "%s"\nset box to POSIX file pbox\ntell application "Finder"\n  activate\n  set result1 to reveal folder box\n  tell application "System Events"\n    set result2 to result1 as string\n    keystroke "t" using command down\n    set result2 to "done"\n  end tell\n  copy result2 to stdout\nend tell\n'

def switch_sidebar_link(dropbox_folder, old_link = None, ignore_missing = None):
    if os.path.dirname(dropbox_folder) == u'/Volumes':
        return
    if add_path_to_shared_list:
        try:
            if remove_path_from_shared_list is not None:
                basename = os.path.basename(dropbox_folder)

                def path_fn(item_path):
                    will_remove = basename == os.path.basename(item_path)
                    TRACE('Found %s on the sidebar, %sremoving...', item_path, '' if will_remove else 'not ')
                    return will_remove

                remove_path_from_shared_list(path_fn, SFL_FAVORITES, unhandled_exc_handler=unhandled_exc_handler)
        except Exception:
            unhandled_exc_handler()

        try:
            TRACE('Adding %s to the sidebar', dropbox_folder)
            add_path_to_shared_list(dropbox_folder, SFL_FAVORITES, first=True)
            return
        except Exception:
            unhandled_exc_handler()

    osa_send_piped(sidebar_add_template % dropbox_folder.encode('utf-8'), async=True)


def initial_link_show_dropbox(dropbox_folder):
    show_dropbox_template = '\nset pbox to "%s"\nset box to POSIX file pbox\ntell application "Finder"\n  activate\n  if (count of Finder windows) < 1 then\n    set the_window to make new Finder window\n  end if\n  set the target of the front Finder window to box\nend tell\n'
    osa_send_piped(show_dropbox_template % dropbox_folder.encode('utf-8'), async=True)


def pre_appdata_use_startup(appdata_path):
    preload_dlls(unhandled_exc_handler)
    try:
        DOMAIN = NSString.alloc().initWithString_('com.apple.LaunchServices')
        KEYS = (NSString.alloc().initWithString_('LSArchitecturesForX86_64'), NSString.alloc().initWithString_('LSArchitecturesForX86_64v2'))
        APP = NSString.alloc().initWithString_('com.getdropbox.dropbox')
        UserDefaults = NSUserDefaults.standardUserDefaults()
        launchServices = UserDefaults.persistentDomainForName_(DOMAIN)
        if launchServices:
            for key in KEYS:
                apps = launchServices.objectForKey_(key)
                if apps and apps.get(APP):
                    apps.removeObjectForKey_(APP)
                    UserDefaults.setObject_forKey_(apps, key)
                    UserDefaults.setPersistentDomain_forName_(launchServices, DOMAIN)
                    UserDefaults.synchronize()
                    report_bad_assumption("User had 'Open using Rosetta' set.")

    except Exception:
        unhandled_exc_handler()

    if MAC_VERSION <= LEOPARD:
        try:
            psn = ProcessSerialNumber()
            Carbon.GetCurrentProcess(psn)
            TRACE('On Leopard or lower: PSN is %r', (psn.lowLongOfPSN, psn.highLongOfPSN))
        except Exception:
            unhandled_exc_handler()

    return arch.fixperms.check_and_fix_permissions(appdata_path)


def limit_to_one_instance(appdata_path, path_to_reveal = None):
    pidfile = os.path.join(appdata_path, 'dropbox.pid')

    def get_out():
        try:
            print 'Another instance of Dropbox (%s) is running!' % pid
        except Exception:
            unhandled_exc_handler(False)
        finally:
            hard_exit(-1)

    try:
        with open(pidfile, 'a+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0)
                s = f.read()
                if s:
                    try:
                        pid = int(s)
                    except Exception:
                        unhandled_exc_handler()
                        TRACE('!! Pidfile exists but is garbled: %r' % s)
                        if list(find_instances(BUILD_KEY, unhandled_exc_handler=unhandled_exc_handler)):
                            TRACE("Garbled pidfile and another running process, don't continue booting")
                            get_out()
                    else:
                        if pid == os.getpid():
                            return
                        if pid in list(find_instances(BUILD_KEY, unhandled_exc_handler=unhandled_exc_handler)):
                            get_out()
                        if not hasattr(build_number, 'frozen'):
                            try:
                                argv = get_process_argv(pid)
                            except Exception:
                                if pid in find_instances(unhandled_exc_handler=unhandled_exc_handler):
                                    get_out()
                            else:
                                if 'Python' in argv[0] and any((os.path.join('bin', 'dropbox') in elt for elt in argv[1:])):
                                    get_out()
                f.seek(0)
                f.truncate()
                f.write('%d' % os.getpid())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    except Exception:
        unhandled_exc_handler()


def pre_network_startup(app):
    cleanup_app_files()
    try:
        curmax, maxmax = resource.getrlimit(resource.RLIMIT_NOFILE)
        newmax = min(maxmax, dropbox_globals.get('max_fds', 10000))
        TRACE('Setting max file descriptors to %s', newmax)
        resource.setrlimit(resource.RLIMIT_NOFILE, (newmax, maxmax))
    except Exception:
        unhandled_exc_handler(False)

    try:
        info = subprocess.Popen('mount', stdout=subprocess.PIPE)
        info = info.communicate()[0]
        TRACE('raw mount information:\n%s', info)
    except Exception:
        unhandled_exc_handler()

    try:
        TRACE('DADiskDescription for mounted drives:')
        GB = 1073741824.0
        for mount_point, _, device_path, _ in get_drives():
            try:
                TRACE('%s at %s\n%r', device_path, mount_point, get_volume_desc(device_path))
            except Exception:
                unhandled_exc_handler(False)

            try:
                st = os.statvfs(mount_point)
                TRACE('size = %.2fGB free = %.2fGB\n', st.f_blocks * st.f_frsize / GB, st.f_bfree * st.f_frsize / GB)
            except Exception:
                unhandled_exc_handler(False)

    except Exception:
        unhandled_exc_handler(False)

    try:
        TRACE('username = %s, uid = %s, euid = %s', pwd.getpwuid(os.getuid())[0], os.getuid(), os.geteuid())
    except Exception:
        unhandled_exc_handler()


def run_binary_fix(ui_kit, freshly_linked):
    threading.Thread(target=update_and_fix_binaries_if_needed, name='BINARY_FIX', args=[freshly_linked]).start()


def post_init_startup(app):
    pass


def post_link_startup(app, *args, **kwargs):
    if not app.mbox.is_secondary:
        try:
            assert not (hasattr(build_number, 'frozen') and list(find_instances(BUILD_KEY))), "This really shouldn't be happening - user is probably running multiple Dropboxen."
        except Exception:
            unhandled_exc_handler()

    post_linked_yet.set()


def post_tour_startup(app, freshly_linked):
    run_binary_fix(app.ui_kit, freshly_linked)


kill_process_by_pid = kill_pid

def unlink(*args, **kwargs):
    pass
