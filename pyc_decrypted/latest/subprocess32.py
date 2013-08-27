#Embedded file name: subprocess32.py
import sys
mswindows = sys.platform == 'win32'
import os
import exceptions
import types
import time
import traceback
import gc
import signal

class CalledProcessError(Exception):

    def __init__(self, returncode, cmd, output = None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)


class TimeoutExpired(Exception):

    def __init__(self, cmd, output = None):
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return "Command '%s' timed out after %s seconds" % (self.cmd, self.timeout)


if mswindows:
    import threading
    import msvcrt
    import _subprocess

    class STARTUPINFO:
        dwFlags = 0
        hStdInput = None
        hStdOutput = None
        hStdError = None
        wShowWindow = 0


    class pywintypes:
        error = IOError


else:
    import select
    _has_poll = hasattr(select, 'poll')
    import errno
    import fcntl
    import pickle
    try:
        import _posixsubprocess
    except ImportError:
        _posixsubprocess = None
        import warnings
        warnings.warn('The _posixsubprocess module is not being used. Child process reliability may suffer if your program uses threads.', RuntimeWarning)

    _PIPE_BUF = getattr(select, 'PIPE_BUF', 512)
    _FD_CLOEXEC = getattr(fcntl, 'FD_CLOEXEC', 1)

    def _set_cloexec(fd, cloexec):
        old = fcntl.fcntl(fd, fcntl.F_GETFD)
        if cloexec:
            fcntl.fcntl(fd, fcntl.F_SETFD, old | _FD_CLOEXEC)
        else:
            fcntl.fcntl(fd, fcntl.F_SETFD, old & ~_FD_CLOEXEC)


    if _posixsubprocess:
        _create_pipe = _posixsubprocess.cloexec_pipe
    else:

        def _create_pipe():
            fds = os.pipe()
            _set_cloexec(fds[0], True)
            _set_cloexec(fds[1], True)
            return fds


__all__ = ['Popen',
 'PIPE',
 'STDOUT',
 'call',
 'check_call',
 'check_output',
 'CalledProcessError']
if mswindows:
    from _subprocess import CREATE_NEW_CONSOLE, CREATE_NEW_PROCESS_GROUP, STD_INPUT_HANDLE, STD_OUTPUT_HANDLE, STD_ERROR_HANDLE, SW_HIDE, STARTF_USESTDHANDLES, STARTF_USESHOWWINDOW
    __all__.extend(['CREATE_NEW_CONSOLE',
     'CREATE_NEW_PROCESS_GROUP',
     'STD_INPUT_HANDLE',
     'STD_OUTPUT_HANDLE',
     'STD_ERROR_HANDLE',
     'SW_HIDE',
     'STARTF_USESTDHANDLES',
     'STARTF_USESHOWWINDOW'])
try:
    MAXFD = os.sysconf('SC_OPEN_MAX')
except:
    MAXFD = 256

_active = []

def _cleanup():
    for inst in _active[:]:
        res = inst._internal_poll(_deadstate=sys.maxint)
        if res is not None:
            try:
                _active.remove(inst)
            except ValueError:
                pass


PIPE = -1
STDOUT = -2

def _eintr_retry_call(func, *args):
    while True:
        try:
            return func(*args)
        except (OSError, IOError) as e:
            if e.errno == errno.EINTR:
                continue
            raise


def _get_exec_path(env = None):
    if env is None:
        env = os.environ
    return env.get('PATH', os.defpath).split(os.pathsep)


if hasattr(os, 'get_exec_path'):
    _get_exec_path = os.get_exec_path

def call(*popenargs, **kwargs):
    timeout = kwargs.pop('timeout', None)
    p = Popen(*popenargs, **kwargs)
    try:
        return p.wait(timeout=timeout)
    except TimeoutExpired:
        p.kill()
        p.wait()
        raise


def check_call(*popenargs, **kwargs):
    retcode = call(*popenargs, **kwargs)
    if retcode:
        cmd = kwargs.get('args')
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd)
    return 0


def check_output(*popenargs, **kwargs):
    timeout = kwargs.pop('timeout', None)
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = Popen(stdout=PIPE, *popenargs, **kwargs)
    try:
        output, unused_err = process.communicate(timeout=timeout)
    except TimeoutExpired:
        process.kill()
        output, unused_err = process.communicate()
        raise TimeoutExpired(process.args, output=output)

    retcode = process.poll()
    if retcode:
        raise CalledProcessError(retcode, process.args, output=output)
    return output


def list2cmdline(seq):
    result = []
    needquote = False
    for arg in seq:
        bs_buf = []
        if result:
            result.append(' ')
        needquote = ' ' in arg or '\t' in arg or not arg
        if needquote:
            result.append('"')
        for c in arg:
            if c == '\\':
                bs_buf.append(c)
            elif c == '"':
                result.append('\\' * len(bs_buf) * 2)
                bs_buf = []
                result.append('\\"')
            else:
                if bs_buf:
                    result.extend(bs_buf)
                    bs_buf = []
                result.append(c)

        if bs_buf:
            result.extend(bs_buf)
        if needquote:
            result.extend(bs_buf)
            result.append('"')

    return ''.join(result)


_PLATFORM_DEFAULT_CLOSE_FDS = object()

class Popen(object):

    def __init__(self, args, bufsize = 0, executable = None, stdin = None, stdout = None, stderr = None, preexec_fn = None, close_fds = _PLATFORM_DEFAULT_CLOSE_FDS, shell = False, cwd = None, env = None, universal_newlines = False, startupinfo = None, creationflags = 0, restore_signals = True, start_new_session = False, pass_fds = ()):
        _cleanup()
        self._child_created = False
        self._input = None
        self._communication_started = False
        if not isinstance(bufsize, (int, long)):
            raise TypeError('bufsize must be an integer')
        if mswindows:
            if preexec_fn is not None:
                raise ValueError('preexec_fn is not supported on Windows platforms')
            any_stdio_set = stdin is not None or stdout is not None or stderr is not None
            if close_fds is _PLATFORM_DEFAULT_CLOSE_FDS:
                if any_stdio_set:
                    close_fds = False
                else:
                    close_fds = True
            elif close_fds and any_stdio_set:
                raise ValueError('close_fds is not supported on Windows platforms if you redirect stdin/stdout/stderr')
        else:
            if close_fds is _PLATFORM_DEFAULT_CLOSE_FDS:
                close_fds = True
            if pass_fds and not close_fds:
                warnings.warn('pass_fds overriding close_fds.', RuntimeWarning)
                close_fds = True
            if startupinfo is not None:
                raise ValueError('startupinfo is only supported on Windows platforms')
            if creationflags != 0:
                raise ValueError('creationflags is only supported on Windows platforms')
        self.args = args
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.pid = None
        self.returncode = None
        self.universal_newlines = universal_newlines
        p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite = self._get_handles(stdin, stdout, stderr)
        self._execute_child(args, executable, preexec_fn, close_fds, pass_fds, cwd, env, universal_newlines, startupinfo, creationflags, shell, p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite, restore_signals, start_new_session)
        if mswindows:
            if p2cwrite != -1:
                p2cwrite = msvcrt.open_osfhandle(p2cwrite.Detach(), 0)
            if c2pread != -1:
                c2pread = msvcrt.open_osfhandle(c2pread.Detach(), 0)
            if errread != -1:
                errread = msvcrt.open_osfhandle(errread.Detach(), 0)
        if p2cwrite != -1:
            self.stdin = os.fdopen(p2cwrite, 'wb', bufsize)
        if c2pread != -1:
            if universal_newlines:
                self.stdout = os.fdopen(c2pread, 'rU', bufsize)
            else:
                self.stdout = os.fdopen(c2pread, 'rb', bufsize)
        if errread != -1:
            if universal_newlines:
                self.stderr = os.fdopen(errread, 'rU', bufsize)
            else:
                self.stderr = os.fdopen(errread, 'rb', bufsize)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()
        if self.stdin:
            self.stdin.close()
        self.wait()

    def _translate_newlines(self, data):
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')
        return data

    def __del__(self, _maxint = sys.maxint, _active = _active):
        if not getattr(self, '_child_created', False):
            return
        self._internal_poll(_deadstate=_maxint)
        if self.returncode is None and _active is not None:
            _active.append(self)

    def communicate(self, input = None, timeout = None):
        if self._communication_started and input:
            raise ValueError('Cannot send input after starting communication')
        if timeout is not None:
            endtime = time.time() + timeout
        else:
            endtime = None
        if endtime is None and not self._communication_started and [self.stdin, self.stdout, self.stderr].count(None) >= 2:
            stdout = None
            stderr = None
            if self.stdin:
                if input:
                    self.stdin.write(input)
                self.stdin.close()
            elif self.stdout:
                stdout = _eintr_retry_call(self.stdout.read)
                self.stdout.close()
            elif self.stderr:
                stderr = _eintr_retry_call(self.stderr.read)
                self.stderr.close()
            self.wait()
            return (stdout, stderr)
        try:
            stdout, stderr = self._communicate(input, endtime)
        finally:
            self._communication_started = True

        sts = self.wait(timeout=self._remaining_time(endtime))
        return (stdout, stderr)

    def poll(self):
        return self._internal_poll()

    def _remaining_time(self, endtime):
        if endtime is None:
            return
        else:
            return endtime - time.time()

    def _check_timeout(self, endtime):
        if endtime is None:
            return
        if time.time() > endtime:
            raise TimeoutExpired(self.args)

    if mswindows:

        def _get_handles(self, stdin, stdout, stderr):
            if stdin is None and stdout is None and stderr is None:
                return (-1, -1, -1, -1, -1, -1)
            p2cread, p2cwrite = (-1, -1)
            c2pread, c2pwrite = (-1, -1)
            errread, errwrite = (-1, -1)
            if stdin is None:
                p2cread = _subprocess.GetStdHandle(_subprocess.STD_INPUT_HANDLE)
                if p2cread is None:
                    p2cread, _ = _subprocess.CreatePipe(None, 0)
            elif stdin == PIPE:
                p2cread, p2cwrite = _subprocess.CreatePipe(None, 0)
            elif isinstance(stdin, int):
                p2cread = msvcrt.get_osfhandle(stdin)
            else:
                p2cread = msvcrt.get_osfhandle(stdin.fileno())
            p2cread = self._make_inheritable(p2cread)
            if stdout is None:
                c2pwrite = _subprocess.GetStdHandle(_subprocess.STD_OUTPUT_HANDLE)
                if c2pwrite is None:
                    _, c2pwrite = _subprocess.CreatePipe(None, 0)
            elif stdout == PIPE:
                c2pread, c2pwrite = _subprocess.CreatePipe(None, 0)
            elif isinstance(stdout, int):
                c2pwrite = msvcrt.get_osfhandle(stdout)
            else:
                c2pwrite = msvcrt.get_osfhandle(stdout.fileno())
            c2pwrite = self._make_inheritable(c2pwrite)
            if stderr is None:
                errwrite = _subprocess.GetStdHandle(_subprocess.STD_ERROR_HANDLE)
                if errwrite is None:
                    _, errwrite = _subprocess.CreatePipe(None, 0)
            elif stderr == PIPE:
                errread, errwrite = _subprocess.CreatePipe(None, 0)
            elif stderr == STDOUT:
                errwrite = c2pwrite
            elif isinstance(stderr, int):
                errwrite = msvcrt.get_osfhandle(stderr)
            else:
                errwrite = msvcrt.get_osfhandle(stderr.fileno())
            errwrite = self._make_inheritable(errwrite)
            return (p2cread,
             p2cwrite,
             c2pread,
             c2pwrite,
             errread,
             errwrite)

        def _make_inheritable(self, handle):
            return _subprocess.DuplicateHandle(_subprocess.GetCurrentProcess(), handle, _subprocess.GetCurrentProcess(), 0, 1, _subprocess.DUPLICATE_SAME_ACCESS)

        def _find_w9xpopen(self):
            w9xpopen = os.path.join(os.path.dirname(_subprocess.GetModuleFileName(0)), 'w9xpopen.exe')
            if not os.path.exists(w9xpopen):
                w9xpopen = os.path.join(os.path.dirname(sys.exec_prefix), 'w9xpopen.exe')
                if not os.path.exists(w9xpopen):
                    raise RuntimeError('Cannot locate w9xpopen.exe, which is needed for Popen to work with your shell or platform.')
            return w9xpopen

        def _execute_child(self, args, executable, preexec_fn, close_fds, pass_fds, cwd, env, universal_newlines, startupinfo, creationflags, shell, p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite, unused_restore_signals, unused_start_new_session):
            assert not pass_fds, 'pass_fds not supported on Windows.'
            if not isinstance(args, types.StringTypes):
                args = list2cmdline(args)
            if startupinfo is None:
                startupinfo = STARTUPINFO()
            if -1 not in (p2cread, c2pwrite, errwrite):
                startupinfo.dwFlags |= _subprocess.STARTF_USESTDHANDLES
                startupinfo.hStdInput = p2cread
                startupinfo.hStdOutput = c2pwrite
                startupinfo.hStdError = errwrite
            if shell:
                startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = _subprocess.SW_HIDE
                comspec = os.environ.get('COMSPEC', 'cmd.exe')
                args = comspec + ' /c ' + '"%s"' % args
                if _subprocess.GetVersion() >= 2147483648L or os.path.basename(comspec).lower() == 'command.com':
                    w9xpopen = self._find_w9xpopen()
                    args = '"%s" %s' % (w9xpopen, args)
                    creationflags |= _subprocess.CREATE_NEW_CONSOLE
            try:
                hp, ht, pid, tid = _subprocess.CreateProcess(executable, args, None, None, int(not close_fds), creationflags, env, cwd, startupinfo)
            except pywintypes.error as e:
                raise WindowsError(*e.args)
            finally:
                if p2cread != -1:
                    p2cread.Close()
                if c2pwrite != -1:
                    c2pwrite.Close()
                if errwrite != -1:
                    errwrite.Close()

            self._child_created = True
            self._handle = hp
            self.pid = pid
            ht.Close()

        def _internal_poll(self, _deadstate = None, _WaitForSingleObject = _subprocess.WaitForSingleObject, _WAIT_OBJECT_0 = _subprocess.WAIT_OBJECT_0, _GetExitCodeProcess = _subprocess.GetExitCodeProcess):
            if self.returncode is None:
                if _WaitForSingleObject(self._handle, 0) == _WAIT_OBJECT_0:
                    self.returncode = _GetExitCodeProcess(self._handle)
            return self.returncode

        def wait(self, timeout = None):
            if timeout is None:
                timeout = _subprocess.INFINITE
            else:
                timeout = int(timeout * 1000)
            if self.returncode is None:
                result = _subprocess.WaitForSingleObject(self._handle, timeout)
                if result == _subprocess.WAIT_TIMEOUT:
                    raise TimeoutExpired(self.args)
                self.returncode = _subprocess.GetExitCodeProcess(self._handle)
            return self.returncode

        def _readerthread(self, fh, buffer):
            buffer.append(fh.read())
            fh.close()

        def _communicate(self, input, endtime):
            if self.stdout and not hasattr(self, '_stdout_buff'):
                self._stdout_buff = []
                self.stdout_thread = threading.Thread(target=self._readerthread, args=(self.stdout, self._stdout_buff))
                self.stdout_thread.daemon = True
                self.stdout_thread.start()
            if self.stderr and not hasattr(self, '_stderr_buff'):
                self._stderr_buff = []
                self.stderr_thread = threading.Thread(target=self._readerthread, args=(self.stderr, self._stderr_buff))
                self.stderr_thread.daemon = True
                self.stderr_thread.start()
            if self.stdin:
                if input is not None:
                    self.stdin.write(input)
                self.stdin.close()
            if self.stdout is not None:
                self.stdout_thread.join(self._remaining_time(endtime))
                if self.stdout_thread.isAlive():
                    raise TimeoutExpired(self.args)
            if self.stderr is not None:
                self.stderr_thread.join(self._remaining_time(endtime))
                if self.stderr_thread.isAlive():
                    raise TimeoutExpired(self.args)
            stdout = None
            stderr = None
            if self.stdout:
                stdout = self._stdout_buff
                self.stdout.close()
            if self.stderr:
                stderr = self._stderr_buff
                self.stderr.close()
            if stdout is not None:
                stdout = stdout[0]
            if stderr is not None:
                stderr = stderr[0]
            if self.universal_newlines and hasattr(file, 'newlines'):
                if stdout:
                    stdout = self._translate_newlines(stdout)
                if stderr:
                    stderr = self._translate_newlines(stderr)
            return (stdout, stderr)

        def send_signal(self, sig):
            if sig == signal.SIGTERM:
                self.terminate()
            elif sig == signal.CTRL_C_EVENT:
                os.kill(self.pid, signal.CTRL_C_EVENT)
            elif sig == signal.CTRL_BREAK_EVENT:
                os.kill(self.pid, signal.CTRL_BREAK_EVENT)
            else:
                raise ValueError('Unsupported signal: %s' % sig)

        def terminate(self):
            _subprocess.TerminateProcess(self._handle, 1)

        kill = terminate
    else:

        def _get_handles(self, stdin, stdout, stderr):
            p2cread, p2cwrite = (-1, -1)
            c2pread, c2pwrite = (-1, -1)
            errread, errwrite = (-1, -1)
            if stdin is None:
                pass
            elif stdin == PIPE:
                p2cread, p2cwrite = _create_pipe()
            elif isinstance(stdin, int):
                p2cread = stdin
            else:
                p2cread = stdin.fileno()
            if stdout is None:
                pass
            elif stdout == PIPE:
                c2pread, c2pwrite = _create_pipe()
            elif isinstance(stdout, int):
                c2pwrite = stdout
            else:
                c2pwrite = stdout.fileno()
            if stderr is None:
                pass
            elif stderr == PIPE:
                errread, errwrite = _create_pipe()
            elif stderr == STDOUT:
                errwrite = c2pwrite
            elif isinstance(stderr, int):
                errwrite = stderr
            else:
                errwrite = stderr.fileno()
            return (p2cread,
             p2cwrite,
             c2pread,
             c2pwrite,
             errread,
             errwrite)

        if hasattr(os, 'closerange'):

            @staticmethod
            def _closerange(fd_low, fd_high):
                os.closerange(fd_low, fd_high)

        else:

            @staticmethod
            def _closerange(fd_low, fd_high):
                for fd in xrange(fd_low, fd_high):
                    while True:
                        try:
                            os.close(fd)
                        except (OSError, IOError) as e:
                            if e.errno == errno.EINTR:
                                continue
                            break

        def _close_fds(self, but):
            self._closerange(3, but)
            self._closerange(but + 1, MAXFD)

        def _close_all_but_a_sorted_few_fds(self, fds_to_keep):
            start_fd = 3
            for fd in fds_to_keep:
                if fd >= start_fd:
                    self._closerange(start_fd, fd)
                    start_fd = fd + 1

            if start_fd <= MAXFD:
                self._closerange(start_fd, MAXFD)

        def _execute_child(self, args, executable, preexec_fn, close_fds, pass_fds, cwd, env, universal_newlines, startupinfo, creationflags, shell, p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite, restore_signals, start_new_session):
            if isinstance(args, types.StringTypes):
                args = [args]
            else:
                args = list(args)
            if shell:
                args = ['/bin/sh', '-c'] + args
                if executable:
                    args[0] = executable
            if executable is None:
                executable = args[0]
            errpipe_read, errpipe_write = _create_pipe()
            try:
                try:
                    if _posixsubprocess:
                        fs_encoding = sys.getfilesystemencoding()

                        def fs_encode(s):
                            if isinstance(s, str):
                                return s
                            else:
                                return s.encode(fs_encoding, 'strict')

                        if env is not None:
                            env_list = [ fs_encode(k) + '=' + fs_encode(v) for k, v in env.items() ]
                        else:
                            env_list = None
                        if os.path.dirname(executable):
                            executable_list = (fs_encode(executable),)
                        else:
                            path_list = _get_exec_path(env)
                            executable_list = (os.path.join(dir, executable) for dir in path_list)
                            executable_list = tuple((fs_encode(exe) for exe in executable_list))
                        fds_to_keep = set(pass_fds)
                        fds_to_keep.add(errpipe_write)
                        self.pid = _posixsubprocess.fork_exec(args, executable_list, close_fds, sorted(fds_to_keep), cwd, env_list, p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite, errpipe_read, errpipe_write, restore_signals, start_new_session, preexec_fn)
                        self._child_created = True
                    else:
                        gc_was_enabled = gc.isenabled()
                        gc.disable()
                        try:
                            self.pid = os.fork()
                        except:
                            if gc_was_enabled:
                                gc.enable()
                            raise

                        self._child_created = True
                        if self.pid == 0:
                            try:
                                if p2cwrite != -1:
                                    os.close(p2cwrite)
                                if c2pread != -1:
                                    os.close(c2pread)
                                if errread != -1:
                                    os.close(errread)
                                os.close(errpipe_read)
                                if c2pwrite == 0:
                                    c2pwrite = os.dup(c2pwrite)
                                if errwrite == 0 or errwrite == 1:
                                    errwrite = os.dup(errwrite)

                                def _dup2(a, b):
                                    if a == b:
                                        _set_cloexec(a, False)
                                    elif a != -1:
                                        os.dup2(a, b)

                                _dup2(p2cread, 0)
                                _dup2(c2pwrite, 1)
                                _dup2(errwrite, 2)
                                closed = set()
                                for fd in [p2cread, c2pwrite, errwrite]:
                                    if fd > 2 and fd not in closed:
                                        os.close(fd)
                                        closed.add(fd)

                                if close_fds:
                                    if pass_fds:
                                        fds_to_keep = set(pass_fds)
                                        fds_to_keep.add(errpipe_write)
                                        self._close_all_but_a_sorted_few_fds(sorted(fds_to_keep))
                                    else:
                                        self._close_fds(but=errpipe_write)
                                if cwd is not None:
                                    os.chdir(cwd)
                                if restore_signals:
                                    signals = ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ')
                                    for sig in signals:
                                        if hasattr(signal, sig):
                                            signal.signal(getattr(signal, sig), signal.SIG_DFL)

                                if start_new_session and hasattr(os, 'setsid'):
                                    os.setsid()
                                if preexec_fn:
                                    preexec_fn()
                                if env is None:
                                    os.execvp(executable, args)
                                else:
                                    os.execvpe(executable, args, env)
                            except:
                                try:
                                    exc_type, exc_value = sys.exc_info()[:2]
                                    if isinstance(exc_value, OSError):
                                        errno_num = exc_value.errno
                                    else:
                                        errno_num = 0
                                    message = '%s:%x:%s' % (exc_type.__name__, errno_num, exc_value)
                                    os.write(errpipe_write, message)
                                except Exception:
                                    pass

                            os._exit(255)
                        if gc_was_enabled:
                            gc.enable()
                finally:
                    os.close(errpipe_write)

                if p2cread != -1 and p2cwrite != -1:
                    os.close(p2cread)
                if c2pwrite != -1 and c2pread != -1:
                    os.close(c2pwrite)
                if errwrite != -1 and errread != -1:
                    os.close(errwrite)
                data = ''
                while True:
                    part = _eintr_retry_call(os.read, errpipe_read, 50000)
                    data += part
                    if not part or len(data) > 50000:
                        break

            finally:
                os.close(errpipe_read)

            if data != '':
                try:
                    _eintr_retry_call(os.waitpid, self.pid, 0)
                except OSError as e:
                    if e.errno != errno.ECHILD:
                        raise

                try:
                    exception_name, hex_errno, err_msg = data.split(':', 2)
                except ValueError:
                    print 'Bad exception data:', repr(data)
                    exception_name = 'RuntimeError'
                    hex_errno = '0'
                    err_msg = 'Unknown'

                child_exception_type = getattr(exceptions, exception_name, RuntimeError)
                for fd in (p2cwrite, c2pread, errread):
                    if fd != -1:
                        os.close(fd)

                if issubclass(child_exception_type, OSError) and hex_errno:
                    errno_num = int(hex_errno, 16)
                    if errno_num != 0:
                        err_msg = os.strerror(errno_num)
                        if errno_num == errno.ENOENT:
                            err_msg += ': ' + repr(args[0])
                    raise child_exception_type(errno_num, err_msg)
                try:
                    exception = child_exception_type(err_msg)
                except Exception:
                    exception = RuntimeError('Could not re-raise %r exception from the child with error message %r' % (child_exception_type, err_msg))

                raise exception

        def _handle_exitstatus(self, sts, _WIFSIGNALED = os.WIFSIGNALED, _WTERMSIG = os.WTERMSIG, _WIFEXITED = os.WIFEXITED, _WEXITSTATUS = os.WEXITSTATUS):
            if _WIFSIGNALED(sts):
                self.returncode = -_WTERMSIG(sts)
            elif _WIFEXITED(sts):
                self.returncode = _WEXITSTATUS(sts)
            else:
                raise RuntimeError('Unknown child exit status!')

        def _internal_poll(self, _deadstate = None, _waitpid = os.waitpid, _WNOHANG = os.WNOHANG, _os_error = os.error):
            if self.returncode is None:
                try:
                    pid, sts = _waitpid(self.pid, _WNOHANG)
                    if pid == self.pid:
                        self._handle_exitstatus(sts)
                except _os_error:
                    if _deadstate is not None:
                        self.returncode = _deadstate

            return self.returncode

        def _try_wait(self, wait_flags):
            try:
                pid, sts = _eintr_retry_call(os.waitpid, self.pid, wait_flags)
            except OSError as e:
                if e.errno != errno.ECHILD:
                    raise
                pid = self.pid
                sts = 0

            return (pid, sts)

        def wait(self, timeout = None, endtime = None):
            if endtime is None and timeout is not None:
                endtime = time.time() + timeout
            if self.returncode is not None:
                return self.returncode
            if endtime is not None:
                delay = 0.0005
                while True:
                    pid, sts = self._try_wait(os.WNOHANG)
                    assert pid == self.pid or pid == 0
                    if pid == self.pid:
                        self._handle_exitstatus(sts)
                        break
                    remaining = self._remaining_time(endtime)
                    if remaining <= 0:
                        raise TimeoutExpired(self.args)
                    delay = min(delay * 2, remaining, 0.05)
                    time.sleep(delay)

            elif self.returncode is None:
                pid, sts = self._try_wait(0)
                self._handle_exitstatus(sts)
            return self.returncode

        def _communicate(self, input, endtime):
            if self.stdin and not self._communication_started:
                self.stdin.flush()
                if not input:
                    self.stdin.close()
            if _has_poll:
                stdout, stderr = self._communicate_with_poll(input, endtime)
            else:
                stdout, stderr = self._communicate_with_select(input, endtime)
            self.wait(timeout=self._remaining_time(endtime))
            if stdout is not None:
                stdout = ''.join(stdout)
            if stderr is not None:
                stderr = ''.join(stderr)
            if self.universal_newlines and hasattr(file, 'newlines'):
                if stdout:
                    stdout = self._translate_newlines(stdout)
                if stderr:
                    stderr = self._translate_newlines(stderr)
            return (stdout, stderr)

        def _communicate_with_poll(self, input, endtime):
            stdout = None
            stderr = None
            if not self._communication_started:
                self._fd2file = {}
            poller = select.poll()

            def register_and_append(file_obj, eventmask):
                poller.register(file_obj.fileno(), eventmask)
                self._fd2file[file_obj.fileno()] = file_obj

            def close_unregister_and_remove(fd):
                poller.unregister(fd)
                self._fd2file[fd].close()
                self._fd2file.pop(fd)

            if self.stdin and input:
                register_and_append(self.stdin, select.POLLOUT)
            if not self._communication_started:
                self._fd2output = {}
                if self.stdout:
                    self._fd2output[self.stdout.fileno()] = []
                if self.stderr:
                    self._fd2output[self.stderr.fileno()] = []
            select_POLLIN_POLLPRI = select.POLLIN | select.POLLPRI
            if self.stdout:
                register_and_append(self.stdout, select_POLLIN_POLLPRI)
                stdout = self._fd2output[self.stdout.fileno()]
            if self.stderr:
                register_and_append(self.stderr, select_POLLIN_POLLPRI)
                stderr = self._fd2output[self.stderr.fileno()]
            if self.stdin and self._input is None:
                self._input_offset = 0
                self._input = input
                if self.universal_newlines and isinstance(self._input, unicode):
                    self._input = self._input.encode(self.stdin.encoding or sys.getdefaultencoding())
            while self._fd2file:
                try:
                    ready = poller.poll(self._remaining_time(endtime))
                except select.error as e:
                    if e.args[0] == errno.EINTR:
                        continue
                    raise

                self._check_timeout(endtime)
                for fd, mode in ready:
                    if mode & select.POLLOUT:
                        chunk = self._input[self._input_offset:self._input_offset + _PIPE_BUF]
                        self._input_offset += os.write(fd, chunk)
                        if self._input_offset >= len(self._input):
                            close_unregister_and_remove(fd)
                    elif mode & select_POLLIN_POLLPRI:
                        data = os.read(fd, 4096)
                        if not data:
                            close_unregister_and_remove(fd)
                        self._fd2output[fd].append(data)
                    else:
                        close_unregister_and_remove(fd)

            return (stdout, stderr)

        def _communicate_with_select(self, input, endtime):
            if not self._communication_started:
                self._read_set = []
                self._write_set = []
                if self.stdin and input:
                    self._write_set.append(self.stdin)
                if self.stdout:
                    self._read_set.append(self.stdout)
                if self.stderr:
                    self._read_set.append(self.stderr)
            if self.stdin and self._input is None:
                self._input_offset = 0
                self._input = input
                if self.universal_newlines and isinstance(self._input, unicode):
                    self._input = self._input.encode(self.stdin.encoding or sys.getdefaultencoding())
            stdout = None
            stderr = None
            if self.stdout:
                if not self._communication_started:
                    self._stdout_buff = []
                stdout = self._stdout_buff
            if self.stderr:
                if not self._communication_started:
                    self._stderr_buff = []
                stderr = self._stderr_buff
            while self._read_set or self._write_set:
                try:
                    rlist, wlist, xlist = select.select(self._read_set, self._write_set, [], self._remaining_time(endtime))
                except select.error as e:
                    if e.args[0] == errno.EINTR:
                        continue
                    raise

                if not (rlist or wlist or xlist):
                    raise TimeoutExpired(self.args)
                self._check_timeout(endtime)
                if self.stdin in wlist:
                    chunk = self._input[self._input_offset:self._input_offset + _PIPE_BUF]
                    bytes_written = os.write(self.stdin.fileno(), chunk)
                    self._input_offset += bytes_written
                    if self._input_offset >= len(self._input):
                        self.stdin.close()
                        self._write_set.remove(self.stdin)
                if self.stdout in rlist:
                    data = os.read(self.stdout.fileno(), 1024)
                    if data == '':
                        self.stdout.close()
                        self._read_set.remove(self.stdout)
                    stdout.append(data)
                if self.stderr in rlist:
                    data = os.read(self.stderr.fileno(), 1024)
                    if data == '':
                        self.stderr.close()
                        self._read_set.remove(self.stderr)
                    stderr.append(data)

            return (stdout, stderr)

        def send_signal(self, sig):
            os.kill(self.pid, sig)

        def terminate(self):
            self.send_signal(signal.SIGTERM)

        def kill(self):
            self.send_signal(signal.SIGKILL)
