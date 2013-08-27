#Embedded file name: arch/mac/util.py
from __future__ import absolute_import
import errno
import fcntl
import os
import platform
import re
import select
import signal
import socket
import struct
import subprocess32 as subprocess
import sys
import time
import unicodedata
import zlib
from itertools import islice, chain
from AppKit import NSAutoreleasePool, NSString
import MacOS
from Carbon.Icn import ReadIconFromFSRef
from Carbon.Files import fsRdWrPerm
from Carbon.Res import FSCreateResFile, FSOpenResFile, Handle, UseResFile, Get1Resource, CloseResFile
import Carbon.Icons
from Foundation import NSCaseInsensitiveSearch, NSNumericSearch
from Foundation import NSLog
from dropbox.attrs import get_attr_data
from dropbox.callbacks import watchable
from dropbox.dbexceptions import TimeoutError, InterruptError
from dropbox.functions import natural_sort_cmp
from dropbox.i18n import trans
from dropbox.mac.version import MAC_VERSION
from dropbox.trace import TRACE, unhandled_exc_handler
import dropbox.fsutil as fsutil
import build_number
from build_number import BUILD_KEY
from dropbox.xattrs import xattr
from ..posix_common.util import get_disk_free_space, paths_on_same_device, socketpair, encode_command_line_arg, decode_command_line_args, handle_extra_command_line_args
from .constants import appdata_path
from .dmg_starter import is_on_installer
from .gui_prefs import set_folders_for_photo_display
from dropbox.mac.internal import executable, get_app_path, get_contents_root, is_intel, open_folder_in_finder, osa_send_piped, select_file_in_finder, select_files_in_finder, show_finder_popup
from pymac.constants import LOG_NOTICE, LOG_PID, LOG_DAEMON
from pymac.helpers.core import is_alias_file
from pymac.helpers.finder import FinderInfoEditor
from pymac.helpers.task_info import get_cpu_timer
from pymac.helpers.process import find_instances
from pymac.dlls import libc
from pymac.helpers.interfaces import generate_ipaddresses
from .proxy_watch import ProxyWatch
try:
    libc.openlog(BUILD_KEY, LOG_PID, LOG_DAEMON)
except Exception:
    unhandled_exc_handler(False)

    def syslog(the_string, level = LOG_NOTICE):
        try:
            NSLog(the_string)
        except Exception:
            unhandled_exc_handler()


else:

    def syslog(the_string, level = LOG_NOTICE):
        try:
            NSLog(the_string)
        except Exception:
            unhandled_exc_handler()

        try:
            libc.syslog(level, the_string, None)
        except Exception:
            unhandled_exc_handler()


def sample_process(temp_fn):
    subprocess.call(['/usr/bin/sample',
     '%s' % os.getpid(),
     '5',
     '10',
     '-file',
     temp_fn])
    try:
        with open(temp_fn, 'rb') as f:
            return f.read(4194304)
    finally:
        os.remove(temp_fn)


def natural_basename_sort_cmp(bn1, bn2):
    pool = NSAutoreleasePool.alloc().init()
    try:
        return NSString.compare_options_(bn1, bn2, NSCaseInsensitiveSearch | NSNumericSearch)
    except Exception:
        unhandled_exc_handler()
        return natural_sort_cmp(bn1, bn2)
    finally:
        del pool


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
        unhandled_exc_handler(False)

    os._exit(exit_code)


def thread_id():
    return '%x' % libc.mach_thread_self()


def icon_code(state):
    if state is 0:
        return ''
    iconfile = u'emblem-dropbox-%s.icns' % {1: 'uptodate',
     2: 'syncing',
     3: 'unsyncable',
     4: 'selsync'}.get(state, '')
    root_path = hasattr(build_number, 'frozen') and u'%s/Resources' % get_contents_root() or u'%s/images/emblems' % os.getcwd()
    iconfile = u'/'.join((root_path, iconfile))
    return iconfile


class NamedPipe(object):

    def __init__(self, app):
        self.app = app
        self.pipe = os.pipe()
        self.pollobj = select.poll()
        self.pollobj.register(self.pipe[0], select.POLLIN)
        self.magic = 50627488
        self.seq = None
        self.sockets = {}
        self.ls = None
        self.chaining = False
        self.chain_sock = None
        self.port_index = 0
        self.bind(0)

    def bind(self, index):
        if index >= 5:
            raise ValueError('Too many instances of Dropbox running')
        if self.ls:
            try:
                del self.sockets[self.ls.fileno()]
            except KeyError:
                pass

            self.pollobj.unregister(self.ls)
            self.ls.close()
            self.ls = None
        self.ls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.ls.bind(self.get_bind_address(index))
            TRACE('Bound socket %s', self.ls)
        except socket.error as e:
            try:
                self.ls.close()
            except Exception:
                pass

            if e[0] == errno.EADDRINUSE:
                self.ls = None
                return self.bind(index + 1)
            raise

        self.pollobj.register(self.ls, select.POLLIN)
        self.ls.listen(5)
        self.sockets[self.ls.fileno()] = self.ls
        self.chaining = False
        self.port_index = index
        if index:
            sock = socket.socket()
            sock.connect(self.get_bind_address(self.port_index - 1))
            ret = self.send_pipe_message(sock, 0, 5, u'')
            TRACE("Chain request returned %r (we're at index %d)" % (ret, index))
        else:
            TRACE('Bound to main port')

    def get_bind_address(self, index):
        return ('127.0.0.1', 25663 + os.getuid() % 1000 + index)

    def send_pipe_message(self, sock, seq, reqtype, path):
        msg = struct.pack('!LLLL', self.magic, seq, reqtype, len(path))
        msg += path.encode('utf16')[2:]
        sock.send(msg)
        received = ''
        while len(received) < 12:
            s = sock.recv(12 - len(received))
            if not s:
                raise ValueError('Connection closed by other side')
            received += s

        magic, in_seq, length = struct.unpack('!LLL', received)
        assert magic == self.magic, 'Expected magic %x (got %x)' % (magic, self.magic)
        assert seq == in_seq, 'Expected seq %x (got %x)' % (seq, in_seq)
        return sock.recv(length).decode('utf8')

    def chain_message(self, context, reqtype, path):

        def connect_chain_socket(self):
            if not self.chain_sock:
                self.chain_sock = socket.socket()
                try:
                    self.chain_sock.connect(self.get_bind_address(self.port_index + 1))
                except socket.error:
                    self.chaining = False
                    self.chain_sock = None
                    raise

        if not self.chain_sock:
            connect_chain_socket(self)
        try:
            return self.send_pipe_message(self.chain_sock, 0, reqtype, path)
        except socket.error:
            self.chain_sock = None
            connect_chain_socket(self)
            return self.send_pipe_message(self.chain_sock, 0, reqtype, path)

    def break_block(self):
        os.write(self.pipe[1], 'd')

    def kill_socket(self, s):
        try:
            self.pollobj.unregister(s)
            TRACE('Killed connection %r', s)
            del self.sockets[s.fileno()]
        except Exception:
            pass

        try:
            s.close()
        except Exception:
            pass

    def get_message(self, block = True, timeout = None):
        if block:
            if timeout is None:
                tov = None
            else:
                assert timeout >= 0
                tov = int(timeout * 1000)
        else:
            tov = 0
        while True:
            s = None
            if tov != None and tov < 0:
                raise TimeoutError()
            start = time.time()
            slist = self.pollobj.poll(tov)
            _after = time.time()
            if not slist:
                raise TimeoutError()
            if tov != None:
                tov = tov - int((_after - start) * 1000)
            try:
                for fd, eventmask in slist:
                    if fd == self.pipe[0]:
                        os.read(fd, 1)
                        raise InterruptError()
                    s = self.sockets.get(fd, None)
                    if not s:
                        os.close(fd)
                        continue
                    if eventmask & (select.POLLERR | select.POLLHUP | select.POLLNVAL):
                        TRACE('Bad socket event, killing: 0x%x', eventmask)
                        self.kill_socket(s)
                        continue
                    if not eventmask & select.POLLIN:
                        continue
                    if s == self.ls:
                        new_s, where = self.ls.accept()
                        new_s.settimeout(1)
                        TRACE('Accepted connection (%r, %r)', new_s, where)
                        self.pollobj.register(new_s, select.POLLIN)
                        self.sockets[new_s.fileno()] = new_s
                        continue

                    def recvall(s, total):
                        blah = []
                        while total:
                            ret = s.recv(total)
                            if not ret:
                                raise Exception('EOF')
                            blah.append(ret)
                            total -= len(blah[-1])

                        return ''.join(blah)

                    msg = recvall(s, 16)
                    if len(msg) != 16:
                        raise IOError('Wrong msg length (%s, %d bytes)' % (repr(msg), len(msg)))
                    magic, seq, reqtype, length = struct.unpack('!iiii', msg)
                    if self.magic is None:
                        self.magic = magic
                    else:
                        assert magic == self.magic, 'wrong magic %x, expected %x' % (magic, self.magic)
                    self.seq = long(seq)
                    msg = recvall(s, length * 2) if length else ''
                    path = unicodedata.normalize('NFD', msg.decode('utf16'))
                    extra = {}
                    return (s,
                     path,
                     reqtype,
                     extra)

            except Exception:
                unhandled_exc_handler(False)
                if s:
                    self.kill_socket(s)
                raise IOError('Error connecting pipe!')

    def respond(self, context, ret):
        payload = unicode(ret).encode('utf8')
        tosend = ''.join((struct.pack('!III', self.magic, self.seq, len(payload)), payload))
        try:
            context.send(tosend)
        except Exception:
            a = sys.exc_info()
            try:
                try:
                    if context:
                        self.kill_socket(context)
                except Exception:
                    unhandled_exc_handler()

                raise a[0], a[1], a[2]
            finally:
                del a

    def complete_request(self, context):
        pass


def kill_other_instances():
    for pid in find_instances(BUILD_KEY, unhandled_exc_handler=unhandled_exc_handler):
        try:
            TRACE('Killing %s' % pid)
            os.kill(pid, signal.SIGKILL)
        except Exception:
            unhandled_exc_handler()


def get_clean_env():
    env = dict(os.environ)
    env['PATH'] = '/sbin:/bin'
    return env


def get_drives():
    try:
        output = subprocess.Popen(['mount', '-v'], stdout=subprocess.PIPE, env=get_clean_env()).communicate()[0]
        r = re.compile('^/dev/(?P<dev>\\S+)\\son\\s(?P<volume>.+)\\s\\((?P<opts>[^(]+)\\)$', re.M)
        return [ (vol,
         [opts.split(', ')[0]],
         '/dev/' + dev,
         None) for dev, vol, opts in r.findall(output) ]
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


def launch_folder(full_path, cleanup = False):
    if not cleanup:
        subprocess.call(['open',
         '-a',
         'Finder',
         full_path], close_fds=True)
    else:
        open_folder_in_finder(full_path, cleanup)


def launch_app(full_path):
    subprocess.call(['open', full_path], close_fds=True)


def clear_fs_bits(full_path):
    pass


def is_x64():
    return False


def path_makes_invalid_dropbox_parent(path):
    if path[0] != '"' or path[-1] != '"':
        newpath = ''
        last_c = ''
        for c in path:
            if c == ' ' and last_c != '\\':
                newpath += '\\ '
            else:
                newpath += c
            last_c = c

        path = newpath
    try:
        info = subprocess.Popen('diskutil info %s' % path, shell=True, stdout=subprocess.PIPE)
        info = info.communicate()[0]
        TRACE('diskutil told us: %s' % info)
    except Exception:
        unhandled_exc_handler()
        return False

    try:
        read_only = info.split('Read Only:')[1].split('\n')[0].strip().lower() == 'yes'
    except Exception:
        read_only = False

    if read_only:
        return 'Target folder is on read-only media'
    return False


def highlight_file(local_path):
    return select_file_in_finder(local_path)


def highlight_files(folder, local_paths, cleanup = False):
    return select_files_in_finder(local_paths, cleanup=cleanup)


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
            x['com.whatever']
        except KeyError:
            pass
        except OSError as e:
            if e.errno == errno.EOPNOTSUPP:
                return False

    except Exception:
        unhandled_exc_handler()

    return True


shellext_log_types = ('finder_shell_extension',)

def cleanup_shellext_log(full_path):
    os.remove(full_path)


def get_shellext_logs(load_contents = False):
    shellext_logs = os.path.join(appdata_path, u'finderplugin', u'l')
    if os.path.exists(shellext_logs):
        files = os.listdir(shellext_logs)
        for fn in files:
            if fn == 'new_trace':
                continue
            try:
                full_path = os.path.join(shellext_logs, fn)
                if load_contents:
                    with open(full_path, 'rb') as f:
                        contents = f.read()
                    yield (full_path, zlib.compress(contents), 'finder_shell_extension')
                else:
                    yield full_path
            except Exception:
                unhandled_exc_handler()

        if load_contents:
            try:
                open(os.path.join(shellext_logs, 'new_trace'), 'wb+').close()
            except Exception:
                unhandled_exc_handler()


get_comments_ascript = '\non run argv\nset acmt to {}\nrepeat with posixPath in argv\n    try\n        set pf to POSIX file posixPath\n        set a to pf as alias\n        tell application "Finder"\n            set end of acmt to comment of a\n        end tell\n        on error\n            set end of acmt to ""\n    end try\nend repeat\nreturn acmt\nend run\n'

def get_comments(local_path_iter):

    def batch(iterable, size):
        sourceiter = iter(iterable)
        while True:
            batchiter = islice(sourceiter, size)
            yield chain([batchiter.next()], batchiter)

    for local_path_batch in batch(local_path_iter, 200):
        files = list(local_path_batch)
        out, err = osa_send_piped(get_comments_ascript, parse_results=True, args=files)
        if err:
            raise Exception(err)
        assert len(out) == len(files)
        for f in out:
            yield f


set_comment_ascript = '\non run argv\nset posixPath to item 1 of argv\nset commentString to item 2 of argv\nset pf to POSIX file posixPath\nset a to pf as alias\ntell application "Finder"\n  set comment of a to ""\n  set comment of a to commentString\nend tell\nend run\n'

def set_comment(local_path, comment, timeout = None):
    return osa_send_piped(set_comment_ascript, parse_results=True, args=[local_path, comment], timeout=timeout)


def startup_pref_migration(pref_state):
    return ({}, set())


def _set_all_fds_cloexec():
    try:
        MAXFD = os.sysconf('SC_OPEN_MAX')
    except Exception:
        MAXFD = 256

    for i in xrange(3, MAXFD):
        try:
            fcntl.fcntl(i, fcntl.F_SETFD, 1)
        except Exception:
            pass


def _fallback_restart(argv):
    try:
        subprocess.Popen(argv)
    except Exception:
        unhandled_exc_handler()

    os._exit(0)


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
        childpid = os.fork()
    except Exception:
        unhandled_exc_handler()
        _fallback_restart(argv)
    else:
        if childpid:
            time.sleep(5)
            os._exit(0)
        else:
            if os.getppid() != 1:
                try:
                    os.kill(os.getppid(), signal.SIGKILL)
                except Exception:
                    pass

            _set_all_fds_cloexec()
            try:
                os.execv(argv[0], argv)
            except Exception:
                _fallback_restart(argv)


def hide_folder(path):
    pass


def set_hidden_and_read_only(path):
    pass


def get_free_space(folder):
    st = os.statvfs(folder)
    return st.f_bfree * st.f_bsize


def gethostname():
    host = socket.gethostname()
    host = re.sub('(.*).local', '\\1', host)
    return host


thread_yield = libc.sched_yield

def formatted_trace(info):
    pass


def get_sanitized_executable_path():
    if not hasattr(build_number, 'frozen'):
        return 'dev'
    full_path = get_app_path()
    suffix = '/%s.app' % (BUILD_KEY,)
    path = full_path[:-len(suffix)]
    if full_path.startswith('/Applications/'):
        return '/Applications'
    if path.startswith('/Volumes/'):
        if is_on_installer(path):
            return 'DMG'
        return 'external'
    home_dir = os.path.expanduser('~/').decode(sys.getfilesystemencoding())
    if not path.startswith(home_dir):
        TRACE('Dropbox installed in an unusual place: %r', full_path)
        return 'other'
    subpath = path[len(home_dir):]
    slash_index = subpath.find('/')
    if slash_index >= 0:
        subpath = subpath[:slash_index]
    if subpath in ('Desktop', 'Downloads'):
        return subpath
    if subpath == 'Applications':
        return 'home/Applications'
    return 'home'


def clean_tray():
    pass


def get_python_arch():
    if not is_intel():
        return 'ppc'
    return ('x64' if struct.calcsize('P') * 8 == 64 else 'i32',)


def get_user_agent_dict():
    return {'platform': 'Macintosh',
     'version': '.'.join(map(str, MAC_VERSION._tuple)),
     'architecture': get_python_arch()}


def check_move_blocked(paths, destination):
    allowedCount = 0
    aliasCount = 0
    whitelist = set(['Desktop',
     'Downloads',
     'Documents',
     'Music',
     'Movies',
     'Pictures'])
    home_dir = os.path.expanduser('~/')
    for path in paths:
        if is_shortcut_file(path):
            aliasCount += 1
        elif not path.startswith('/Volumes/'):
            parent_dir = os.path.dirname(path)
            if parent_dir.startswith(home_dir):
                subpath = path[len(home_dir):]
                slash_index = subpath.find('/')
                if slash_index >= 0:
                    subpath = subpath[:slash_index]
                if subpath in whitelist:
                    allowedCount += 1

    if allowedCount:
        allowedCount += aliasCount
    return len(paths) - allowedCount


def move_files(paths, destination, fs, highlight = True, highlight_limit = 10):
    items_to_show = []
    for path in paths:
        if is_shortcut_file(path):
            continue
        basename = os.path.basename(path)
        dest = os.path.join(destination, basename)
        is_dir = fsutil.is_directory(fs, dest)
        if os.path.exists(dest):
            error_msg = ''
            buttons = [trans(u'Skip'), trans(u'Keep Both')]
            default = 1
            if is_dir:
                error_msg = trans(u'A folder named "%(name)s" already exists in this location. Do you still want to add the one you\'re moving?') % dict(name=basename)
            else:
                error_msg = trans(u'A file named "%(name)s" already exists in this location. Do you want to replace it with the one you\'re moving?') % dict(name=basename)
                buttons = buttons + [trans(u'Replace')]
                default = 2
            selected = show_finder_popup(trans(u'Move to Dropbox'), error_msg, buttons, default)
            if selected == 1:
                root, extension = os.path.splitext(dest)
                suffix = 1
                dest = root + ' ' + str(suffix) + extension
                while os.path.exists(dest):
                    suffix += 1
                    dest = root + ' ' + str(suffix) + extension

            elif selected != 2:
                dest = None
        if dest:
            fsutil.safe_move(fs, path, dest)
            items_to_show.append(dest)

    if highlight:
        if len(items_to_show) <= highlight_limit:
            highlight_files(destination, items_to_show)
        else:
            launch_folder(destination)


def is_shortcut_file(path, cache_path = None, file_attrs = None):
    if os.path.exists(path) and is_alias_file(path):
        return True
    if cache_path and is_alias_file(cache_path):
        return True
    if file_attrs:
        finderInfo = file_attrs.attr_dict.get('mac', {}).get('com.apple.FinderInfo', None)
        if finderInfo:
            data = get_attr_data(finderInfo, None)
            if 'alis' in str(data):
                return True
    return False
