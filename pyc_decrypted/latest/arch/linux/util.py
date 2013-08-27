#Embedded file name: arch/linux/util.py
from __future__ import absolute_import
import sys
import os
import signal
import socket
import struct
import subprocess32 as subprocess
import Queue
import locale
import time
import shutil
import threading
import platform
import fcntl
import errno
import functools
import cPickle as pickle
import tempfile
from ..posix_common.util import get_disk_free_space, paths_on_same_device, socketpair, kill_pid, kill_pid, encode_command_line_arg, decode_command_line_args, handle_extra_command_line_args
from dropbox.xattrs import xattr
from dropbox.linux_libc import exit, syscall, openlog, LOG_PID, LOG_DAEMON, LOG_NOTICE, LOG_ERR, posix_fadvise, POSIX_FADV_SEQUENTIAL, syslog as libc_syslog
from .control_thread import ControlThread
from .internal import executable, get_contents_root, run_as_root
from dropbox.callbacks import watchable
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.globals import dropbox_globals
from dropbox.url_info import dropbox_url_info
from dropbox.dbexceptions import TagFolderError, TimeoutError, InterruptError
from dropbox.server_path import ServerPath, server_path_ns_rel, server_path_basename, server_path_is_root
from dropbox.db_thread import db_thread
from dropbox.functions import natural_sort_cmp as natural_basename_sort_cmp
from dropbox.i18n import trans
import dropbox.fsutil as fsutil
from .network_interfaces import generate_ipaddresses
from .proxy_watch import ProxyWatch
import build_number
from build_number import BUILD_KEY
_ct = None

def start_control_thread(app):
    global _ct
    _ct = db_thread(ControlThread)(app)
    _ct.start()
    app.linux_control_thread = _ct


def copy_text_to_clipboard(text):
    if _ct is not None and _ct.isAlive():
        _ct.ifaces_request(u'copy_to_clipboard', {u'text': [text]})


try:
    openlog(BUILD_KEY, LOG_PID, LOG_DAEMON)
except Exception:
    unhandled_exc_handler(False)

    def syslog(s, level = LOG_NOTICE):
        try:
            sys.stderr.writelines((s, '\n'))
        except Exception:
            unhandled_exc_handler()


else:

    def syslog(s, level = LOG_NOTICE):
        try:
            libc_syslog(level, s, None)
        except Exception:
            unhandled_exc_handler()

        try:
            sys.stderr.writelines((s, '\n'))
        except Exception:
            unhandled_exc_handler()


@watchable
def hard_exit(exit_code = 0, flush = True):
    from dropbox.client.high_trace import force_flush
    try:
        TRACE('Hard exiting with code %d' % exit_code)
    except Exception:
        pass

    try:
        if flush:
            force_flush()
    except Exception:
        unhandled_exc_handler()

    try:
        if _ct is not None and _ct.isAlive():
            _ct.kill_servers()
            _ct.ifaces_request(u'dropbox_quit', {})
            time.sleep(0.1)
    except Exception:
        unhandled_exc_handler(False)

    exit(exit_code)


def thread_id():
    return syscall(186 if is_x64() else 224)


def sample_process(temp_fn):
    return ''


def raise_application():
    pass


named_pipe_inqueue = Queue.Queue()
named_pipe_outqueue = Queue.Queue()

class NamedPipe(object):

    def __init__(self, app):
        self.app = app
        self.chaining = False

        def activate_chaining(value):
            TRACE('Now passing messages through')
            self.chaining = value

        app.mbox.on_secondary_link.add_handler(activate_chaining)

    def get_message(self, block = True, timeout = None):
        try:
            a = named_pipe_inqueue.get(block, timeout)
            if a is None:
                raise InterruptError()
            path, reqtype = a
            extra = {}
            return (None,
             path,
             reqtype,
             extra)
        except Queue.Empty:
            raise TimeoutError()

    def break_block(self):
        named_pipe_inqueue.put(None)

    def respond(self, context, ret):
        named_pipe_outqueue.put(ret)

    def complete_request(self, context):
        pass

    def chain_message(self, content, reqtype, path):
        return self.app.mbox.chain(content, reqtype, path)


code2str = [u'unwatched',
 u'up to date',
 u'syncing',
 u'unsyncable',
 u'selsync']

def icon_code(code):
    try:
        return code2str[code]
    except Exception:
        return code2str[0]


def running_dropbox_instances():
    return running_instances('dropbox')


def running_instances(process_name):
    try:
        elts = os.listdir('/proc')
        myuid = os.geteuid()
        mypid = os.getpid()
    except Exception:
        unhandled_exc_handler()
        return

    for name in elts:
        try:
            pid = int(name)
        except ValueError:
            continue

        if pid == mypid:
            continue
        try:
            a = os.stat(os.path.join('/proc', name))
        except OSError as e:
            if e.errno != errno.ENOENT:
                unhandled_exc_handler()
            continue

        if a.st_uid != myuid:
            continue
        try:
            if os.readlink('/proc/%d/exe' % pid).endswith('/' + process_name):
                yield pid
        except OSError as e:
            if e.errno != errno.EACCES:
                unhandled_exc_handler()
            continue
        except Exception:
            unhandled_exc_handler()
            continue


def get_clean_env():
    env = dict(os.environ)
    env['PATH'] = '/sbin:/bin'
    return env


def get_drives():
    try:
        output = subprocess.Popen(['mount', '-v'], stdout=subprocess.PIPE, env=get_clean_env()).communicate()[0]
        lines = [ l.split() for l in output.split('\n') ]
        return [ (m[2],
         [m[4]],
         m[0],
         None) for m in lines if m and m[0].startswith('/dev') ]
    except Exception:
        unhandled_exc_handler()
        return []


def get_running_services():
    procs = []
    try:
        output = subprocess.Popen(['/bin/ps', 'aux'], stdout=subprocess.PIPE).communicate()[0]
        for line in output.split('\n')[1:]:
            if not line:
                continue
            line = unicode(line, 'utf-8', errors='replace')
            procs.append(u' '.join(line.split()[10:]))

    except Exception:
        unhandled_exc_handler()

    return procs


def kill_other_instances():
    for pid in running_dropbox_instances():
        try:
            TRACE('Killing %s', pid)
            os.kill(pid, signal.SIGKILL)
        except Exception:
            unhandled_exc_handler()


def clear_fs_bits(full_path):
    pass


def is_x64():
    try:
        struct.unpack('L', '4444')
        return False
    except Exception:
        return True


def path_makes_invalid_dropbox_parent(path):
    return False


def _save_env_vars(names):
    return dict(((name, os.environ.get(name)) for name in names))


def _restore_env_vars(saved_vars):
    for name, value in saved_vars.items():
        os.environ.pop(name, None)
        if value is not None:
            os.environ[name] = value


def using_old_ld_library_path(func):

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        saved = _save_env_vars(('LD_LIBRARY_PATH', 'OLD_LD_LIBRARY_PATH'))
        try:
            _restore_env_vars({'LD_LIBRARY_PATH': os.environ.get('OLD_LD_LIBRARY_PATH')})
            return func(*args, **kwargs)
        finally:
            _restore_env_vars(saved)

    return wrapped


def _preexec_fn():
    _restore_env_vars({'LD_LIBRARY_PATH': os.environ.get('OLD_LD_LIBRARY_PATH')})


def _preexec_fn_lose_child():
    _preexec_fn()
    try:
        os.setsid()
    except Exception:
        unhandled_exc_handler()

    if os.fork():
        os._exit(0)


def launch_folder(full_path):
    have_nautilus = subprocess.Popen('which nautilus', shell=True, close_fds=True, preexec_fn=_preexec_fn).wait() == 0
    toopen = 'nautilus --no-desktop' if have_nautilus else 'xdg-open'
    if type(full_path) is unicode:
        try:
            full_path = full_path.encode(sys.getfilesystemencoding())
        except UnicodeEncodeError:
            full_path = full_path.encode('utf8')

    subprocess.Popen('%s "%s"' % (toopen, full_path.replace('"', '\\"')), shell=True, close_fds=True, preexec_fn=_preexec_fn_lose_child)


def highlight_file(local_path):
    launch_folder(os.path.dirname(local_path))


def highlight_files(folder, local_paths, cleanup = False):
    launch_folder(folder)


bubble_last_key_and_ctx = None
bubblelock = threading.Lock()

def bubble_external(app, message, caption, ctx_ref = None):
    global bubble_last_key_and_ctx
    assert isinstance(message, unicode), 'offending string: %s' % (message,)
    assert isinstance(caption, unicode), 'offending string: %s' % (caption,)
    if _ct is None or not _ct.isAlive():
        return
    args = {u'message': [message],
     u'caption': [caption]}
    if ctx_ref is not None:
        key = u'bubble%d' % ctx_ref

        def temp_cb(args):
            try:
                app.bubble_context.get_context_ref(int(ctx_ref)).thunk()
            except Exception:
                unhandled_exc_handler()

            return {}

        with bubblelock:
            if bubble_last_key_and_ctx is not None:
                try:
                    _ct.cs.remove_command(bubble_last_key_and_ctx[0])
                except Exception:
                    unhandled_exc_handler()

                try:
                    app.bubble_context.expire_context_ref(bubble_last_key_and_ctx[1])
                except Exception:
                    unhandled_exc_handler()

            _ct.cs.add_command(key, temp_cb)
            bubble_last_key_and_ctx = (key, ctx_ref)
        args[u'callback'] = [key]
    _ct.ifaces_request(u'bubble', args)


def refresh_tray_menu_external(menu):
    if _ct is None or not _ct.isAlive():
        return
    _ct.ifaces_request(u'refresh_tray_menu', {u'active': [u'true']})


def change_state_external(new_state):
    if _ct is None or not _ct.isAlive():
        return
    _ct.ifaces_request(u'change_state', {u'new_state': [unicode(new_state)]})


def get_platform_info():
    try:
        return list(platform.uname())
    except Exception:
        unhandled_exc_handler()
        return []


def enable_p2p_default():
    return True


def fs_supports_attrs(directory):
    try:
        x = xattr.from_path(directory)
        try:
            x['user.myxattr']
        except KeyError:
            return True
        except OSError as e:
            if e.errno == errno.EOPNOTSUPP:
                return False
            raise
        else:
            return True

    except Exception:
        unhandled_exc_handler()

    return False


shellext_log_types = ()

def get_shellext_logs(load_contents = False):
    try:
        pass
    except Exception:
        yield


def startup_pref_migration(pref_state):
    return ({}, set())


def launch_new_dropbox(opts = ()):
    TRACE('Launching second Dropbox process with args %r', opts)
    argv = executable(opts)
    subprocess.Popen(argv)


@watchable
def restart(opts = (), flush = True):
    from dropbox.client.high_trace import force_flush
    try:
        TRACE('Restarting with args %r', opts)
    except Exception:
        pass

    try:
        if flush:
            force_flush()
    except Exception:
        unhandled_exc_handler(False)

    argv = executable(opts)
    try:
        MAXFD = os.sysconf('SC_OPEN_MAX')
    except Exception:
        MAXFD = 256

    for i in xrange(3, MAXFD):
        try:
            fcntl.fcntl(i, fcntl.F_SETFD, 1)
        except Exception:
            pass

    os.execv(argv[0], argv)


if not hasattr(os, 'O_NOATIME'):
    os.O_NOATIME = 262144

def hide_folder(path):
    pass


def set_hidden_and_read_only(path):
    pass


def get_cpu_timer():
    pid = os.getpid()
    tid = thread_id()
    statfile = open('/proc/%d/task/%d/stat' % (pid, tid), 'r')

    def timer(close = False):
        statfile.seek(0)
        stats = statfile.read().split()
        if close:
            statfile.close()
        return int(stats[13]) + int(stats[14])

    return timer


def get_free_space(folder):
    st = os.statvfs(folder)
    return st.f_bfree * st.f_bsize


def gethostname():
    raw = socket.gethostname()
    enc = locale.getpreferredencoding()
    try:
        h = raw.decode(enc)
    except UnicodeError:
        h = raw.decode(enc, 'replace')

    return h


def formatted_trace(info):
    pass


class NoSuchCommand(Exception):
    pass


def run_packagekit(inst):
    try:
        import dbus
        bus = dbus.SessionBus()
        proxy = bus.get_object('org.freedesktop.PackageKit', '/org/freedesktop/PackageKit')
        iface = dbus.Interface(proxy, 'org.freedesktop.PackageKit.Modify')
        iface.InstallPackageNames(dbus.UInt32(0), inst, '', timeout=3600)
    except dbus.exceptions.DBusException as e:
        if e.get_dbus_name() not in ('org.freedesktop.Packagekit.Modify.Cancelled', 'org.freedesktop.Packagekit.Modify.Forbidden'):
            raise


def run_synaptic(prompt, finish_msg, progress_msg, inst = [], rm = []):
    if not os.path.exists('/usr/sbin/synaptic'):
        raise NoSuchCommand()
    cmd = ['/usr/sbin/synaptic',
     '--hide-main-window',
     '--non-interactive',
     '--finish-str',
     finish_msg,
     '--progress-str',
     progress_msg]
    with tempfile.NamedTemporaryFile() as f:
        cmd.append('--set-selections-file')
        cmd.append(f.name)
        for s in inst:
            f.write('%s\tinstall\n' % s)

        for s in rm:
            f.write('%s\tdeinstall\n' % s)

        f.flush()
        return run_as_root(cmd, prompt)


def install_language_pack(code):
    inst = ['language-pack-gnome-%s' % code[0:2]]
    try:
        run_packagekit(inst)
    except Exception:
        unhandled_exc_handler()
        prompt = trans(u'Dropbox requires a language pack to support the language you have selected.  Type your password to allow Dropbox to install this language pack.')
        finish_msg = trans(u'The language pack was successfully installed.')
        progress_msg = trans(u'Installing language pack for selected language.')
        if run_synaptic(prompt, finish_msg, progress_msg, inst=inst) != 0:
            raise Exception('Unable to install')


def get_sanitized_executable_path():
    if not hasattr(build_number, 'frozen'):
        return 'dev'
    home_dir = os.path.expanduser('~/')
    if get_contents_root().startswith(home_dir):
        return 'home'
    return 'other'


def clean_tray():
    pass


def get_user_agent_dict():
    return {'platform': 'Linux',
     'version': platform.release(),
     'architecture': 'x64' if struct.calcsize('P') * 8 == 64 else 'i32'}


def check_move_blocked(paths, destination):
    return 0


def move_files(paths, destination, fs, highlight = True, highlight_limit = 10):
    items_to_show = []
    for path in paths:
        dest = os.path.join(destination, os.path.basename(path))
        fsutil.safe_move(fs, path, dest)
        items_to_show.append(dest)

    if highlight:
        if len(items_to_show) <= highlight_limit:
            highlight_files(destination, items_to_show)
        else:
            launch_folder(destination)


def is_shortcut_file(*args, **kwargs):
    return False
