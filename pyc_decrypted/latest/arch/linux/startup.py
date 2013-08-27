#Embedded file name: arch/linux/startup.py
from __future__ import absolute_import
import errno
import fcntl
import os
import pwd
import shutil
import signal
import subprocess32 as subprocess
import sys
import threading
import tempfile
from .constants import appdata_path, update_root
from .internal import get_contents_root
from .util import hard_exit, kill_other_instances, launch_folder, start_control_thread
from ..posix_common.util import kill_pid
import arch
import build_number
from build_number import BUILD_KEY
from dropbox.trace import unhandled_exc_handler, TRACE
from distutils.version import LooseVersion

def install_early_in_boot(app):
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def get_rss():
    try:
        with open('/proc/self/stat') as statfile:
            return long(statfile.readline().split()[23]) * 4096
    except Exception:
        return -1


def check_other_version():
    home_install_path_version = os.path.join(update_root, u'VERSION')
    if os.path.exists(home_install_path_version):
        with open(home_install_path_version) as f:
            version = f.read().strip()
        if LooseVersion(version) > LooseVersion(build_number.VERSION):
            return update_root


def ensure_latest_version():
    other_location = check_other_version()
    if not other_location:
        return
    dropbox_exe = os.path.join(other_location, u'dropboxd').encode(sys.getfilesystemencoding())
    cmd = [dropbox_exe, '/newerversion'] + sys.argv[1:]
    subprocess.check_call(cmd, close_fds=True, cwd=u'/')
    raise Exception('The newer version exited without killing us')


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
                        TRACE('WARNING! pidfile exists but is garbled (will blow over it and continue): %r' % s)
                    else:
                        if pid == os.getpid():
                            return
                        try:
                            yes = os.readlink('/proc/%d/exe' % pid).endswith('/dropbox')
                        except OSError as e:
                            if e.errno != errno.ENOENT:
                                unhandled_exc_handler()
                            yes = False

                        if not (hasattr(build_number, 'frozen') or yes):
                            try:
                                with open('/proc/%d/cmdline' % pid) as f2:
                                    foo = f2.read()
                                    yes = os.path.join('bin', 'dropbox') in foo and 'python' in foo
                            except IOError as e:
                                if e.errno != errno.ENOENT:
                                    unhandled_exc_handler()

                        if yes:
                            get_out()
                f.seek(0)
                f.truncate()
                f.write('%d' % os.getpid())
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    except Exception:
        unhandled_exc_handler()


def pre_appdata_use_startup(_appdata_path):
    return arch.fixperms.check_and_fix_permissions(_appdata_path)


def pre_network_startup(app):
    try:
        start_control_thread(app)
    except Exception:
        unhandled_exc_handler()

    TRACE('filesystem encoding: ' + sys.getfilesystemencoding())
    TRACE('default encoding: ' + sys.getdefaultencoding())
    try:
        with open('/proc/mounts') as f:
            TRACE('mount information: \n%s', f.read())
    except Exception:
        unhandled_exc_handler()

    try:
        TRACE('username = %s, uid = %s, euid = %s', pwd.getpwuid(os.getuid())[0], os.getuid(), os.geteuid())
    except Exception:
        unhandled_exc_handler()


def first_run(is_update = False, parent_pid = None, parent_dir = None):
    if not is_update:
        return
    newdir = parent_dir
    if not newdir and parent_pid is not None:
        try:
            exe = os.readlink('/proc/%d/exe' % parent_pid)
            newdir = os.path.normpath(os.path.join(exe, '..')).decode(sys.getfilesystemencoding())
        except Exception:
            unhandled_exc_handler()

    if not (newdir and os.access(newdir, os.W_OK)):
        newdir = os.path.expanduser('~/.dropbox-dist').decode(sys.getfilesystemencoding())
    curdir = get_contents_root()
    killed_parent = False
    rollback = False
    must_die = False
    olddir = None
    tmpdir = None
    try:
        if not os.path.exists(newdir):
            os.makedirs(newdir)
        olddir = tempfile.mkdtemp(prefix='.dropbox-dist-old-', dir=os.path.dirname(newdir).encode(sys.getfilesystemencoding())).decode(sys.getfilesystemencoding())
        tmpdir = tempfile.mkdtemp(prefix='.dropbox-dist-tmp-', dir=os.path.dirname(newdir).encode(sys.getfilesystemencoding())).decode(sys.getfilesystemencoding())
        for f in (olddir, tmpdir):
            os.chmod(f, 493)
            if os.path.exists(f):
                TRACE('Removing %r', f)
                shutil.rmtree(f, True)
            os.mkdir(f)
            os.rmdir(f)

        TRACE('Copying %r to %r', curdir, tmpdir)
        shutil.copytree(curdir, tmpdir, symlinks=True)
        os.mkdir(olddir)
        os.rmdir(olddir)
        if parent_pid is not None:
            try:
                os.kill(parent_pid, signal.SIGKILL)
                TRACE('killed parent %d', parent_pid)
                killed_parent = True
            except Exception:
                unhandled_exc_handler()

            try:
                assert os.getppid() == parent_pid, "getppid() and parent_pid don't match! %r vs %r" % (os.getppid(), parent_pid)
            except Exception:
                unhandled_exc_handler()

        kill_other_instances()
        killed_parent = True
        TRACE('Moving %r to %r', newdir, olddir)
        os.rename(newdir, olddir)
        rollback = True
        TRACE('Moving %r to %r', tmpdir, newdir)
        os.rename(tmpdir, newdir)
    except Exception:
        unhandled_exc_handler()
        if rollback:
            try:
                if os.path.exists(newdir):
                    TRACE('Removing %r', newdir)
                    shutil.rmtree(newdir, True)
            except Exception:
                unhandled_exc_handler()

            TRACE('Copying %r to %r', olddir, newdir)
            try:
                os.rename(olddir, newdir)
            except OSError:
                try:
                    shutil.copytree(olddir, newdir, True)
                except Exception:
                    unhandled_exc_handler()
                    TRACE("Couldn't roll back.  All hell has broken loose!")
                    hard_exit(-1)

        must_die = True
    finally:
        for f in (tmpdir, olddir):
            try:
                if f and os.path.exists(f):
                    TRACE('Removing %r', f)
                    shutil.rmtree(f, True)
            except Exception:
                unhandled_exc_handler()

    if killed_parent:
        try:
            lbk = BUILD_KEY.lower()
            a = os.path.join(newdir, u'%sd' % (lbk,)).encode(sys.getfilesystemencoding())
            TRACE('Starting %r', a)
            subprocess.Popen([a], close_fds=True, cwd=u'/')
        except Exception:
            unhandled_exc_handler()
        else:
            try:
                if os.path.exists(curdir):
                    TRACE('Removing %r', curdir)
                    shutil.rmtree(curdir)
            except Exception:
                unhandled_exc_handler()

            hard_exit(-1 if must_die else 0)

    if must_die:
        hard_exit(-1)


can_configure_startupitem = False

def reroll_startup_items(prefs):
    global can_configure_startupitem
    TRACE('rerolling startup items')
    if prefs.app.mbox.is_secondary:
        TRACE('secondary client; leaving startup items alone')
        return
    try:
        home_dir = os.path.expanduser('~')
        contents = os.listdir(home_dir)
        startupitem = prefs['startupitem']
        if startupitem:
            TRACE('Making sure we are a startup item')
        else:
            TRACE('Making sure we are NOT a startup item')
        if '.config' in contents:
            TRACE('~/.config exists...')
            autostart_dir = os.path.join(home_dir, '.config', 'autostart')
            autostart_link = os.path.join(autostart_dir, '%s.desktop' % BUILD_KEY.lower())
            if not startupitem:
                if os.path.exists(autostart_link):
                    os.remove(autostart_link)
                    TRACE('OK, removed desktop file at %r' % autostart_link)
            desktop_file_locs = ['/usr/local/share/applications/%s.desktop' % BUILD_KEY.lower(), '/usr/share/applications/%s.desktop' % BUILD_KEY.lower()]
            TRACE(repr(desktop_file_locs))
            for desktop_file in desktop_file_locs:
                if os.path.exists(desktop_file):
                    can_configure_startupitem = True
                    if startupitem:
                        if not os.path.exists(autostart_dir):
                            os.makedirs(autostart_dir)
                        shutil.copyfile(desktop_file, autostart_link)
                        TRACE('OK, copied desktop file from %s' % desktop_file)
                    break
            else:
                TRACE('no .desktop file???')

    except Exception:
        unhandled_exc_handler()


def initial_link_show_dropbox(dropbox_folder):
    launch_folder(dropbox_folder)


needs_shell_touch_on_reindex = True

def post_init_startup(app):
    pass


def post_link_startup(*args, **kwargs):
    pass


def post_tour_startup(app, freshly_linked):
    pass


def switch_sidebar_link(dropbox_folder, old_link = None, ignore_missing = None):
    pass


wx_preconditions_cond_var = threading.Condition()

def wait_wx_preconditions():
    previous_signal_stop = threading.currentThread().signal_stop
    try:
        should_stop = [False]

        def wakeup():
            should_stop[0] = True
            with wx_preconditions_cond_var:
                wx_preconditions_cond_var.notify()

        threading.currentThread().signal_stop = wakeup
        while not should_stop[0] and not os.environ.get('DISPLAY', ''):
            with wx_preconditions_cond_var:
                TRACE('waiting on cond var')
                wx_preconditions_cond_var.wait()

        if os.environ.get('DISPLAY', ''):
            TRACE('Loading WX with DISPLAY = %r' % os.environ['DISPLAY'])
            return True
        TRACE('main thread stopped, rss is at %r' % get_rss())
        return False
    finally:
        threading.currentThread().signal_stop = previous_signal_stop


kill_process_by_pid = kill_pid

def unlink(*args, **kwargs):
    pass
