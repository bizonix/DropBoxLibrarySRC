#Embedded file name: arch/mac/dmg_starter.py
import errno
import filecmp
import os
import subprocess32 as subprocess
import tempfile
from pipes import quote as shell_quote
from AppKit import NSAutoreleasePool, NSWorkspace
from build_number import BUILD_KEY
from dropbox.i18n import safe_activate_translation, trans
from dropbox.mac.version import LEOPARD, MAC_VERSION, TIGER
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
import pymac.helpers.disk
VOLUMES_DIR = u'/Volumes'
get_all_login_matches = None
if MAC_VERSION > TIGER:
    try:
        from pymac.helpers.shared_file_list import get_all_login_matches
    except Exception:
        unhandled_exc_handler(True)

def dmg_target_volume():
    return os.path.join(VOLUMES_DIR, u'%s Installer' % (BUILD_KEY,))


def is_on_installer(path):
    try:
        mount_point = pymac.helpers.disk.get_mount_point_for_path(path)
        if not mount_point.startswith(dmg_target_volume()):
            return False
        if mount_point == '/' or not pymac.helpers.disk.is_ejectable(mount_point):
            return False
    except Exception:
        unhandled_exc_handler()
        return False

    return True


def find_previous_installation():
    if not get_all_login_matches:
        return None
    matches = get_all_login_matches('%s.app' % (BUILD_KEY,), unhandled_exc_handler)
    for match in reversed(matches):
        if os.path.exists(match) and not pymac.helpers.disk.is_in_trash(match):
            return os.path.dirname(match)


def decide_dmg_action(curr_instance_path, default_app_folder_path, give_us_permissions_cb, kill_other_instances = None, skip_mount_point_check = False):
    TRACE('starting decide_dmg_action %s, %s, %s, %s', curr_instance_path, default_app_folder_path, give_us_permissions_cb, kill_other_instances)
    curr_instance_path = curr_instance_path.rstrip('/')
    if not skip_mount_point_check:
        if not is_on_installer(curr_instance_path):
            return
    prev_installation = find_previous_installation()
    if prev_installation and not is_on_installer(prev_installation):
        app_folder_path = prev_installation
    else:
        app_folder_path = default_app_folder_path
    TRACE('find_previous_installation() returned %r, installing into %r', prev_installation, app_folder_path)
    app_target = os.path.join(app_folder_path, u'%s.app' % (BUILD_KEY,))
    launch_exe = os.path.join(app_target, u'Contents', u'MacOS', BUILD_KEY)
    launch_args = [launch_exe, u'/firstrunupdatemanual' if os.path.exists(app_target) else u'/firstrun']
    if kill_other_instances:
        kill_other_instances()
    did_exist_previously = os.path.exists(app_target)
    handle, temp_file_path = tempfile.mkstemp()
    try:
        os.close(handle)
    except Exception:
        unhandled_exc_handler()

    noqtn = '--noqtn' if MAC_VERSION >= LEOPARD else ''
    try:
        with open(temp_file_path, 'w') as temp_file:
            script = u'#!/bin/bash\n/bin/rm -rf %(app_target)s\n[ ! -e %(app_target)s ] && /usr/bin/ditto %(noqtn)s %(curr_instance_path)s %(app_target)s\n'
            script %= dict(app_target=shell_quote(app_target), curr_instance_path=shell_quote(curr_instance_path), noqtn=noqtn)
            script = script.encode('utf-8')
            temp_file.write(script)
        success = False
        try:
            proc = subprocess.Popen(['/bin/sh', temp_file_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            stdout, stderr = proc.communicate()
            returncode = proc.returncode
            if stdout:
                TRACE('installer script stdout: %s' % (stdout,))
            if stderr:
                TRACE('installer script stderr: %s' % (stderr,))
            proc.stdout.close()
            proc.stderr.close()
            TRACE('installer script returncode: %s', returncode)
            success = _plist_identical(curr_instance_path, app_target)
        except OSError as e:
            if did_exist_previously and not os.path.exists(app_target):
                report_bad_assumption('In first pass, double-click install deleted old installation at %s but failed to install new one', app_target)
            if e.errno != errno.EACCES:
                raise

        if not success:
            try:
                if not give_us_permissions_cb:
                    return
                safe_activate_translation()
                msg = trans(u'Please enter your computer admin password for Dropbox to finish installing.')
                retval, output = give_us_permissions_cb('/bin/sh', [temp_file_path], msg + u'\n\n')
                if output:
                    TRACE('installer script with elevated permissions output: %s', output)
                TRACE('installer script with elevated permissions returned %s', retval)
                if not retval:
                    return
            except Exception:
                unhandled_exc_handler()
                return

    finally:
        try:
            os.unlink(temp_file_path)
        except Exception:
            unhandled_exc_handler()

    pool = NSAutoreleasePool.alloc().init()
    try:
        ws = NSWorkspace.sharedWorkspace()
        ws.noteFileSystemChanged_(app_target)
    except Exception:
        pass
    finally:
        del pool

    return launch_args


def _plist_identical(d1, d2):
    p1 = os.path.join(d1, u'Contents', u'Info.plist')
    p2 = os.path.join(d2, u'Contents', u'Info.plist')
    if not os.path.exists(p1) or not os.path.exists(p2):
        return False
    try:
        return filecmp.cmp(p1, p2, shallow=False)
    except EnvironmentError:
        return False
