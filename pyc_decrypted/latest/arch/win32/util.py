#Embedded file name: arch/win32/util.py
from __future__ import absolute_import
import ctypes
import errno
import locale
import os
import platform
import socket
import struct
import tempfile
import threading
import zlib
import ntsecuritycon
import win32con
import pywintypes
import win32pipe
import win32event
import win32process
import win32file
import win32gui
import win32api
import win32ts
import win32clipboard
import win32security
import winerror
import winioctlcon
from win32com.shell import shellcon
from win32service import CloseServiceHandle, EnumServicesStatus, OpenSCManager, SERVICE_RUNNING, SC_MANAGER_ENUMERATE_SERVICE
import comtypes
from comtypes.client import CreateObject
from ctypes.wintypes import UINT, LPCWSTR, BOOL, DWORD, HANDLE, LARGE_INTEGER, LPWSTR, WCHAR, c_int, byref
import build_number
from build_number import BUILD_KEY
from .network_interfaces import generate_ipaddresses
from dropbox.callbacks import watchable
from dropbox.dbexceptions import InterruptError
from dropbox.decrypt_ctrace import decrypt_ctrace
from dropbox.functions import natural_sort_cmp
from dropbox.globals import dropbox_globals
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.win32.version import VISTA, WINDOWS_VERSION, WINDOWS_VERSION_STRING, WINXP
from dropbox.win32_util import find_media_type
from pynt.helpers.shell import open_folder_and_select_items, shell_get_known_folder_path
from pynt.dlls.kernel32 import kernel32
from pynt.dlls.shell32 import shell32
from pynt.types import SHFILEOPSTRUCTW
from pynt.constants import FOLDERID_Downloads
from .constants import appdata_path, default_dropbox_path, default_dropbox_folder_name
from .internal import is_admin, tcp_parameters, get_user_folder_path, get_user_folder_path_from_reg, is_uac_enabled, ShellExecuteW, uses_com, add_shortcut_to_user_location, executable, get_registry, set_registry, get_installpath, get_volumes
from .proxy_watch import ProxyWatch
_ = lambda x: x
FOLDER_INFOTIP = _(u'A secure home for all your photos, documents, and videos.')
del _
MEGABYTE = 1048576
PIPE_REJECT_REMOTE_CLIENTS = 8
DRIVE_SEPARATOR = ':'

def raise_application():
    pass


def copy_text_to_clipboard(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()


def syslog(*n, **kw):
    pass


def launch_new_dropbox(opts = ()):
    TRACE('Launching second Dropbox process with args %r', opts)
    _launch_new_dropbox(opts)


@watchable
def restart(opts = (), flush = True):
    from dropbox.client.high_trace import force_flush
    opts = ['/restart', str(win32process.GetCurrentProcessId())] + list(opts)
    try:
        TRACE('Restarting with args %r', opts)
    except Exception:
        pass

    try:
        if flush:
            force_flush()
    except Exception:
        unhandled_exc_handler(False)

    _launch_new_dropbox(opts)
    win32process.ExitProcess(0)


def _launch_new_dropbox(opts = ()):
    cmd = executable(list(opts))
    fn = cmd[0]
    args = ' '.join(cmd[1:])
    try:
        try:
            ShellExecuteW(0, u'open', fn, args, None, win32con.SW_SHOW)
        except Exception:
            unhandled_exc_handler()
            win32api.ShellExecute(0, 'open', fn.encode('mbcs'), args.encode('mbcs'), None, win32con.SW_SHOW)

    except Exception:
        unhandled_exc_handler()


def path_filter(local_path, server_path, active_details = None):
    return True


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

    win32process.ExitProcess(exit_code)


def thread_id():
    return win32api.GetCurrentThreadId()


def trace_local(x):
    thread_name = threading.currentThread().getName()
    if type(x) is str:
        x = x.decode('iso-8859-1')
    else:
        x = unicode(x)
    for seg in str(x.encode('ascii', 'backslashreplace')).replace('\r\n', '\n').replace('\r', '\n').replace('\x00', '').split('\n'):
        win32api.OutputDebugString('| %s(%s): %s' % (thread_name, win32api.GetCurrentThreadId(), seg))


get_drives = get_volumes

def get_running_services():
    try:
        handle = OpenSCManager(None, None, SC_MANAGER_ENUMERATE_SERVICE)
        try:
            return dict((s[:2] for s in EnumServicesStatus(handle) if s[2][1] & SERVICE_RUNNING))
        finally:
            CloseServiceHandle(handle)

    except Exception:
        unhandled_exc_handler()
        return {}


def icon_code(state):
    return u'%s' % state


class NamedPipe(object):
    DROPBOX_PIPE_NAME = u'\\\\.\\pipe\\DropboxPipe'
    MAGIC = 50627330

    def __init__(self, app):
        self.app = app
        TRACE('Creating named pipe')
        self.mutex = None
        self.overlapped = pywintypes.OVERLAPPED()
        self.overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
        if 'old_shell_extension' in dropbox_globals:
            pipe_prefix = self.DROPBOX_PIPE_NAME
        else:
            session_id = win32ts.ProcessIdToSessionId(win32api.GetCurrentProcessId())
            pipe_prefix = u'%s_%d' % (self.DROPBOX_PIPE_NAME, session_id)
        TRACE('Pipe Prefix: %s' % (pipe_prefix,))
        self.pipe_prefix = pipe_prefix
        self.pipe_index = None
        self.chaining = False
        self.bind(0)

    def pipe_exists(self, pipe_name):
        try:
            h = win32file.CreateFile(pipe_name, win32con.GENERIC_READ, 0, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_OVERLAPPED, None)
            h.Close()
            return True
        except Exception:
            return False

    def send_pipe_message(self, index, pid, tid, reqtype, path):
        TRACE('Sending Pipe Message: index: %s pid: %s tid: %s reqtype: %s path:%s' % (index,
         pid,
         tid,
         reqtype,
         path))
        msg = struct.pack('LLLL', self.MAGIC, pid, tid, reqtype)
        msg += (path + u'\x00').encode('utf16')[2:]
        return win32pipe.CallNamedPipe(self.get_pipe_name(index), msg, 16384, 2000)[4:].decode('utf16')

    def chain_message(self, context, reqtype, path):
        pid, tid = context
        return self.send_pipe_message(self.pipe_index + 1, pid, tid, reqtype, path)

    def get_pipe_name(self, index):
        return self.pipe_prefix + ('' if not index else '_%d' % index)

    def bind(self, index = 0):
        if index >= 5:
            raise ValueError('Too many instances of Dropbox running')
        pipe_name = self.get_pipe_name(index)
        if self.pipe_exists(pipe_name):
            return self.bind(index + 1)
        try:
            ph = win32process.GetCurrentProcess()
            th = win32security.OpenProcessToken(ph, win32security.TOKEN_ALL_ACCESS)
            info = win32security.GetTokenInformation(th, win32security.TokenGroups)
            for sid, group_id in info:
                if group_id & win32security.SE_GROUP_LOGON_ID == win32security.SE_GROUP_LOGON_ID:
                    logon_sid = sid
                    break
            else:
                raise Exception('No Logon Sid Found!')

            dacl = win32security.ACL()
            dacl.AddAccessAllowedAce(dacl.GetAclRevision(), win32con.GENERIC_ALL, logon_sid)
            network_sid = win32security.SID()
            network_sid.Initialize(ntsecuritycon.SECURITY_NT_AUTHORITY, 1)
            network_sid.SetSubAuthority(0, ntsecuritycon.SECURITY_NETWORK_RID)
            dacl.AddAccessDeniedAce(dacl.GetAclRevision(), win32con.GENERIC_ALL, network_sid)
            sd = win32security.SECURITY_DESCRIPTOR()
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            sa = win32security.SECURITY_ATTRIBUTES()
            sa.SECURITY_DESCRIPTOR = sd
        except Exception:
            unhandled_exc_handler()
            sa = None

        pipe_mode = win32con.PIPE_TYPE_MESSAGE
        if WINDOWS_VERSION >= VISTA:
            pipe_mode |= PIPE_REJECT_REMOTE_CLIENTS
        self.hPipe = win32pipe.CreateNamedPipe(pipe_name, win32con.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED, pipe_mode, win32con.PIPE_UNLIMITED_INSTANCES, 0, 0, 6000, sa)
        TRACE('Using pipe name %s' % pipe_name)
        self.pipe_index = index
        self.interrupt = False
        self.chaining = False
        if self.pipe_index > 0:
            ret = self.send_pipe_message(self.pipe_index - 1, win32api.GetCurrentProcessId(), win32api.GetCurrentThreadId(), 5, u'')
            TRACE('Chain request returned %r' % ret)

    def break_block(self):
        self.interrupt = True
        win32event.SetEvent(self.overlapped.hEvent)

    def get_message(self):
        while True:
            try:
                hr = win32pipe.ConnectNamedPipe(self.hPipe, self.overlapped)
            except pywintypes.error as details:
                if details[0] not in (109, 232):
                    unhandled_exc_handler()
                win32pipe.DisconnectNamedPipe(self.hPipe)
                continue

            if hr == winerror.ERROR_PIPE_CONNECTED:
                win32event.SetEvent(self.overlapped.hEvent)
            timeout = self.pipe_index > 0 and 6000 + self.pipe_index * 1000 or win32event.INFINITE
            waitHandles = (self.overlapped.hEvent,)
            rc = win32event.WaitForMultipleObjects(waitHandles, 0, timeout)
            if self.interrupt:
                self.interrupt = False
                raise InterruptError()
            if rc == win32event.WAIT_OBJECT_0:
                try:
                    hr, s = win32file.ReadFile(self.hPipe, 4016)
                    try:
                        return self._parse_shell_request(s)
                    except Exception as e:
                        TRACE('!! Failed to decode message from the shell extension')
                        unhandled_exc_handler()
                        win32pipe.DisconnectNamedPipe(self.hPipe)
                        continue

                except win32file.error as e:
                    if e[0] != 109:
                        unhandled_exc_handler()
                    win32pipe.DisconnectNamedPipe(self.hPipe)
                    continue

            elif rc == win32event.WAIT_TIMEOUT:
                if not self.pipe_exists(self.get_pipe_name(self.pipe_index - 1)):
                    self.bind(0)
                if self.pipe_index:
                    ret = self.send_pipe_message(self.pipe_index - 1, win32api.GetCurrentProcessId(), win32api.GetCurrentThreadId(), 5, u'')

        raise IOError('Could not read from pipe')

    @classmethod
    def _parse_shell_request(cls, s):
        magic, pid, tid, reqtype = struct.unpack('LLLL', s[:16])
        if magic != cls.MAGIC:
            raise ValueError('Expected magic constant %x (got %x)' % (cls.MAGIC, magic))
        ustr = s[16:].decode('utf-16-le').split(u'\x00')[:-1]
        path = ustr[0]
        extra = ustr[1:]
        extra = dict(((extra[i], extra[i + 1]) for i in xrange(0, len(extra) - 1, 2)))
        if reqtype == 1:
            if len(path) != 3 or path[1:3] != ':\\' or not path[0].isalpha():
                try:
                    path = win32api.GetLongPathNameW(path)
                except pywintypes.error as e:
                    if e[0] not in (2, 3, 5):
                        raise

        if u'_dllver' in extra:
            try:
                extra[u'_dllver'] = tuple((int(x) for x in extra[u'_dllver'].split(u'.')))
            except Exception:
                TRACE("!! Bogus _dllver couldn't be parsed: %r", extra[u'_dllver'])
                unhandled_exc_handler(False)
                del extra[u'_dllver']

        return ((pid, tid),
         path,
         reqtype,
         extra)

    def respond(self, context, ret):
        try:
            win32file.WriteFile(self.hPipe, ''.join((struct.pack('L', self.MAGIC), unicode(ret).encode('utf16')[2:])))
        except pywintypes.error as e:
            if e[0] == 232:
                unhandled_exc_handler(False)
            else:
                raise

    def complete_request(self, context):
        win32pipe.DisconnectNamedPipe(self.hPipe)


_StrCmpLogicalW = None

def natural_basename_sort_cmp(bn1, bn2):
    global _StrCmpLogicalW
    if _StrCmpLogicalW is None:
        try:
            _StrCmpLogicalW = ctypes.windll.shlwapi.StrCmpLogicalW
        except Exception as e:
            if not isinstance(e, AttributeError) or WINDOWS_VERSION >= WINXP:
                unhandled_exc_handler()
            _StrCmpLogicalW = natural_sort_cmp
        else:
            _StrCmpLogicalW.argtypes = [LPCWSTR, LPCWSTR]
            _StrCmpLogicalW.restype = ctypes.c_int

    return _StrCmpLogicalW(bn1, bn2)


def kill_other_instances():
    import startup
    startup.kill_process_by_name('%s.exe' % BUILD_KEY)


def launch_folder(full_path, cleanup = False):
    os.startfile(full_path + unicode(os.path.sep))


def clear_fs_bits(target_fn):
    try:
        win32file.SetFileAttributesW(target_fn, 0)
    except Exception:
        pass


def get_disk_free_space(local_path):
    search = local_path
    while True:
        try:
            return win32file.GetDiskFreeSpaceEx(search)[0]
        except pywintypes.error:
            oldsearch = search
            search = os.path.dirname(search)
            if oldsearch == search:
                unhandled_exc_handler()
                break

    return 0


def is_x64():
    ret = ctypes.c_ulong(0)
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.IsWow64Process(kernel32.GetCurrentProcess(), ctypes.byref(ret))
    except AttributeError:
        pass
    except Exception:
        unhandled_exc_handler(False)

    return bool(ret.value)


def disable_x64_fs_redirection():
    ret = ctypes.c_void_p()
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.Wow64DisableWow64FsRedirection(ctypes.byref(ret))
    except AttributeError:
        pass
    except Exception:
        unhandled_exc_handler(False)

    return ret.value


def revert_x64_fs_redirection(what):
    p = ctypes.c_void_p(what)
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.Wow64RevertWow64FsRedirection(p)
    except AttributeError:
        pass
    except Exception:
        unhandled_exc_handler(False)


def paths_on_same_device(path1, path2):
    return os.path.abspath(path1).split('\\', 1)[0].upper() == os.path.abspath(path2).split('\\', 1)[0].upper()


def path_is_remote(path):
    type_, _ = find_media_type(path)
    if type_ is None:
        return True
    return type_ == win32file.DRIVE_REMOTE


FILE_ATTRIBUTE_REPARSE_POINT = 1024

def highlight_file(local_path):
    if local_path:
        TRACE('Highlighting %r' % local_path)
        try:
            is_dir = os.path.isdir(local_path)
        except Exception:
            unhandled_exc_handler()
            is_dir = False

        try:
            if not is_dir:
                try:
                    ShellExecuteW(0, u'open', u'explorer.exe', u'/select,"%s"' % local_path, None, win32con.SW_SHOW)
                except Exception:
                    unhandled_exc_handler(True)

            else:
                launch_folder(local_path)
        except Exception:
            unhandled_exc_handler(True)


@uses_com
def highlight_files(path, files, cleanup = False):
    return open_folder_and_select_items(path, files)


MiniDumpNormal = 0
MiniDumpWithDataSegs = 1
MiniDumpWithFullMemory = 2
MiniDumpWithHandleData = 4
MiniDumpFilterMemory = 8
MiniDumpScanMemory = 16
MiniDumpWithUnloadedModules = 32
MiniDumpWithIndirectlyReferencedMemory = 64
MiniDumpFilterModulePaths = 128
MiniDumpWithProcessThreadData = 256
MiniDumpWithPrivateReadWriteMemory = 512
MiniDumpWithoutOptionalData = 1024
MiniDumpWithFullMemoryInfo = 2048
MiniDumpWithThreadInfo = 4096
MiniDumpWithCodeSegs = 8192

def sample_process(temp_fn, flags = MiniDumpWithHandleData | MiniDumpWithProcessThreadData | MiniDumpWithUnloadedModules):
    hDumpFile = win32file.CreateFile(temp_fn, win32file.GENERIC_WRITE, 0, None, win32file.CREATE_ALWAYS, 0, 0)
    ctypes.windll.dbghelp.MiniDumpWriteDump(win32process.GetCurrentProcess(), win32process.GetCurrentProcessId(), hDumpFile.handle, flags, 0, 0, 0)
    hDumpFile.Close()
    f = open(temp_fn, 'rb')
    ret = f.read(4 * MEGABYTE)
    f.close()
    os.remove(temp_fn)
    return ret


def get_platform_info():
    try:
        reported_uname = list(platform.uname())
        reported_uname[2] = WINDOWS_VERSION_STRING
        return reported_uname + ['x64:%r' % is_x64(), 'admin:%r' % is_admin(), 'uac:%r' % is_uac_enabled()]
    except Exception:
        unhandled_exc_handler()
        return []


def add_shortcut_to_desktop():
    add_shortcut_to_user_location(shellcon.CSIDL_DESKTOP, arguments='/home')


@uses_com
def enable_p2p_default():
    try:
        fwmgr = CreateObject('HNetCfg.FwMgr', dynamic=True)
        profile = fwmgr.LocalPolicy.CurrentProfile
        if profile.FirewallEnabled:
            uexec = executable()[0].decode('mbcs').lower()
            for app in profile.AuthorizedApplications:
                if app.ProcessImageFileName.lower() == uexec:
                    TRACE('Firewall Exception added for %r Enabled = %d' % (uexec, app.Enabled))
                    return app.Enabled

            TRACE('Firewall Exception not added for %r' % (uexec,))
            return False
        TRACE('Firewall Not Enabled')
        return True
    except comtypes.COMError as e:
        if e.hresult in (-2147023143, -2147352567):
            TRACE('Firewall Service Not Running')
            return True
        unhandled_exc_handler()
    except WindowsError as e:
        if e.winerror in (-2147023143, -2147352567):
            TRACE('Firewall Service Not Running')
            return True
        unhandled_exc_handler()
    except Exception:
        unhandled_exc_handler()

    return True


shellext_log_types = ('explorer_shell_extension', 'explorer_crash')

def cleanup_shellext_log(full_path):
    os.rename(full_path, u'%s_sent' % full_path)


def unreported_explorer_crash():
    shellext_crashes = os.path.join(appdata_path, u'shellext', u'dump')
    return os.path.exists(shellext_crashes) and bool(os.listdir(shellext_crashes))


def get_shellext_logs(load_contents = False):
    shellext_logs = os.path.join(appdata_path, u'shellext', u'l')
    shellext_crashes = os.path.join(appdata_path, u'shellext', u'dump')
    if load_contents:
        try:
            open(os.path.join(shellext_logs, 'new_trace'), 'wb+').close()
        except Exception:
            unhandled_exc_handler()

    for rel_exc, the_dir in (('explorer_shell_extension', shellext_logs), ('explorer_crash', shellext_crashes)):
        if os.path.exists(the_dir):
            for fn in os.listdir(the_dir):
                if fn == 'new_trace':
                    continue
                try:
                    full_path = os.path.join(the_dir, fn)
                    if full_path.endswith(u'_sent'):
                        try:
                            os.remove(full_path)
                        except WindowsError as e:
                            if e.winerror not in (32, 5):
                                unhandled_exc_handler()
                        except Exception:
                            unhandled_exc_handler()

                    elif load_contents:
                        if rel_exc == 'explorer_shell_extension':
                            contents = ''.join(decrypt_ctrace(full_path))
                            yield (full_path, zlib.compress(contents.decode('mbcs').encode('utf8')), 'explorer_shell_extension')
                        elif rel_exc == 'explorer_crash':
                            with open(full_path, 'rb') as f:
                                contents = f.read(4 * MEGABYTE)
                            yield (full_path, contents, 'explorer_crash')
                    else:
                        yield full_path
                except IOError as e:
                    if e.errno != errno.EACCES:
                        unhandled_exc_handler()
                except Exception:
                    unhandled_exc_handler()


def startup_pref_migration(pref_state):
    migrated = {}
    if pref_state.get('dropbox_path', default_dropbox_path) == default_dropbox_path:
        try:
            TRACE('Seeing if we need to migrate DropboxPath from registry')
            configuration = get_registry(DropboxPath=default_dropbox_path)
            regdropboxpath = unicode(configuration['DropboxPath'])
            if regdropboxpath.find('?') != -1:
                raise ValueError('MBCS conversion error')
        except Exception:
            unhandled_exc_handler()
        else:
            if default_dropbox_path != regdropboxpath and regdropboxpath:
                TRACE('Migrating DropboxPath: %r' % regdropboxpath)
                migrated['dropbox_path'] = regdropboxpath
                try:
                    set_registry(DropboxPath='')
                except Exception:
                    unhandled_exc_handler()

    return (migrated, set())


def kill_pid(pid):
    h = win32api.OpenProcess(win32con.PROCESS_TERMINATE | win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, 0, pid)
    try:
        win32process.TerminateProcess(h, 0)
    finally:
        win32api.CloseHandle(h)


def hide_folder(folder):
    attrs = win32file.GetFileAttributesW(folder)
    win32file.SetFileAttributesW(folder, attrs | win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)


def get_cpu_timer():
    raise RuntimeError('Cpu profiling not supported on this platform')


def fs_supports_attrs(directory):
    old_attrib = win32file.GetFileAttributesW(directory)
    try:
        clear_fs_bits(directory)
        a = '%s:%s' % (directory, 'user.myxattr')
        try:
            open(a, 'wb').close()
            TRACE('Directory %s supports extended attributes', directory)
        except IOError as e:
            if e.errno == errno.EINVAL and os.path.exists(directory):
                TRACE("Directory %s doesn't support extended attributes", directory)
                return False
            unhandled_exc_handler()
        else:
            os.unlink(a)

    except Exception:
        unhandled_exc_handler()
    finally:
        try:
            win32file.SetFileAttributesW(directory, old_attrib)
        except Exception:
            unhandled_exc_handler()

    return True


def get_free_space(folder):
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
    return free_bytes.value


def gethostname():
    raw = socket.gethostname()
    enc = locale.getpreferredencoding()
    try:
        h = raw.decode(enc)
    except UnicodeError:
        h = raw.decode(enc, 'replace')

    return h


def get_old_default_dropbox_directory():
    return os.path.join(get_user_folder_path(shellcon.CSIDL_PERSONAL), u'My %s' % (BUILD_KEY,))


def formatted_trace(info):
    info.append(([u'tcp parameter', u'value'], [ (unicode(k), unicode(v)) for k, v in tcp_parameters() ]))


def set_hidden(path):
    file_attrs = win32file.GetFileAttributesW(path)
    win32file.SetFileAttributesW(path, file_attrs | win32con.FILE_ATTRIBUTE_HIDDEN)


def is_junction_point(path):
    file_attrs = win32file.GetFileAttributesW(path)
    return bool(file_attrs & FILE_ATTRIBUTE_REPARSE_POINT)


def create_junction_point(src, target):
    IO_REPARSE_TAG_MOUNT_POINT = 2684354563L
    target = target.lstrip('\\??\\')
    target = target.lstrip('\\\\?\\')
    target = '\\??\\' + os.path.abspath(target)
    handle = win32file.CreateFileW(src, win32con.GENERIC_READ | win32con.GENERIC_WRITE, 0, None, win32con.OPEN_EXISTING, win32file.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OPEN_REPARSE_POINT, None)
    target_length = len(target) * ctypes.sizeof(WCHAR)
    targetFormatted = target.encode('utf-16le')
    buf_struct = struct.pack('LHHHHHH', IO_REPARSE_TAG_MOUNT_POINT, target_length + 12, 0, 0, target_length, target_length + 2, 0) + targetFormatted + '\x00\x00\x00\x00'
    win32file.DeviceIoControl(handle, winioctlcon.FSCTL_SET_REPARSE_POINT, buf_struct, None)
    win32file.CloseHandle(handle)


def encode_command_line_arg(arg):
    return arg


def decode_command_line_args(argv):
    command_line = kernel32.GetCommandLineW()
    if not command_line:
        return argv
    argc = c_int(0)
    argv_w = shell32.CommandLineToArgvW(command_line, byref(argc))
    try:
        if not argv_w:
            return argv
        if argc.value <= 0:
            return argv
        start = argc.value - len(argv)
        ret_args = argv_w[start:argc.value]
        return ret_args
    finally:
        kernel32.LocalFree(argv_w)


def is_shortcut_file(path, cache_path = None, file_attrs = None):
    _, ext = os.path.splitext(path)
    return ext.lower() == '.lnk'


def check_move_blocked(paths, destination):
    allowedCount = 0
    lnkCount = 0
    whitelist_csidls = [shellcon.CSIDL_DESKTOP,
     shellcon.CSIDL_PERSONAL,
     shellcon.CSIDL_MYMUSIC,
     shellcon.CSIDL_MYVIDEO,
     shellcon.CSIDL_MYPICTURES]
    whitelist = list((get_user_folder_path(whitelist_id) for whitelist_id in whitelist_csidls if whitelist_id is not None))
    if WINDOWS_VERSION >= VISTA:
        whitelist_folderids = [FOLDERID_Downloads]
        whitelist2 = list((shell_get_known_folder_path(whitelist_id) for whitelist_id in whitelist_folderids))
        whitelist.extend(whitelist2)
    else:
        whitelist_reg = list((get_user_folder_path_from_reg(whitelist_id) for whitelist_id in whitelist_csidls if whitelist_id is not None and whitelist_id not in whitelist))
        whitelist.extend(whitelist_reg)
    for path in paths:
        if is_shortcut_file(path):
            lnkCount += 1
        else:
            src_drive = path[0]
            dest_drive = destination[0]
            if src_drive == dest_drive:
                parent_dir = os.path.dirname(path)
                if parent_dir is not None:
                    for allowed in whitelist:
                        if allowed and parent_dir.startswith(allowed):
                            if WINDOWS_VERSION >= VISTA or path not in whitelist:
                                allowedCount += 1
                                break

    if allowedCount:
        allowedCount += lnkCount
    return len(paths) - allowedCount


def move_files(paths, destination, fs = None, highlight = True, highlight_limit = 10):
    src_drive = paths[0][0]
    should_move = paths[0][1] == ':' and all([ len(src) > 1 and src_drive == src[0] and src[1] == ':' for src in paths ]) and src_drive == destination[0] and destination[1] == ':'
    total_file_size = 0
    num_files = 0
    move_paths = []
    for path in paths:
        if is_shortcut_file(path):
            continue
        try:
            total_file_size += os.path.getsize(path)
            num_files += 1
            move_paths.append(path)
        except Exception as e:
            if e.errno != errno.ENOENT:
                unhandled_exc_handler()
            continue

    if num_files > 0:
        TRACE('Decided to %s files listed on command line', 'move' if should_move else 'copy')
        args = SHFILEOPSTRUCTW(wFunc=UINT(shellcon.FO_MOVE if should_move else shellcon.FO_COPY), pFrom=LPCWSTR(u'\x00'.join(move_paths) + '\x00'), pTo=LPCWSTR(destination), fFlags=shellcon.FOF_ALLOWUNDO, fAnyOperationsAborted=BOOL())
        result = shell32.SHFileOperationW(byref(args))
        if result == 0:
            if highlight:
                items_to_show = [ os.path.join(destination, os.path.basename(src)) for src in move_paths ]
                if len(items_to_show) <= highlight_limit:
                    highlight_files(destination, items_to_show)
                else:
                    launch_folder(destination)
            return (num_files, total_file_size)
        TRACE('SHFileOperationW failed with result %d', result)


def get_sanitized_executable_path():
    if not hasattr(build_number, 'frozen'):
        return 'dev'
    type_, typepath = find_media_type(appdata_path)
    TRACE('appdata path is %r, typepath is %r, type_ is %r', appdata_path, typepath, type_)
    if type_ == win32file.DRIVE_FIXED:
        return 'local'
    if type_ == win32file.DRIVE_REMOTE:
        return 'remote'
    if type_ == win32file.DRIVE_REMOVABLE:
        return 'removable'
    return 'other'


def clean_tray():

    def FW(hwnd_parent, window_class):
        return win32gui.FindWindowEx(hwnd_parent, 0, window_class, '')

    try:
        parent_hwnd = FW(FW(FW(None, 'Shell_TrayWnd'), 'TrayNotifyWnd'), 'SysPager')
        hwnd = 0
        while True:
            hwnd = win32gui.FindWindowEx(parent_hwnd, hwnd, 'ToolbarWindow32', None)
            if hwnd == 0:
                break
            r = win32gui.GetClientRect(hwnd)
            for x in xrange(0, r[2], 5):
                for y in xrange(0, r[3], 5):
                    win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, (y << 16) + x)

    except Exception:
        unhandled_exc_handler()


def get_user_agent_dict():
    return {'platform': 'Windows',
     'version': WINDOWS_VERSION.name() or 'Unknown',
     'architecture': 'x64' if struct.calcsize('P') * 8 == 64 else 'i32'}


def handle_extra_command_line_args(paths, path_to_dropbox):
    return move_files(paths, path_to_dropbox)
