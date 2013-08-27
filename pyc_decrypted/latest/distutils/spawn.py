#Embedded file name: distutils/spawn.py
__revision__ = '$Id$'
import sys
import os
from distutils.errors import DistutilsPlatformError, DistutilsExecError
from distutils import log

def spawn(cmd, search_path = 1, verbose = 0, dry_run = 0):
    if os.name == 'posix':
        _spawn_posix(cmd, search_path, dry_run=dry_run)
    elif os.name == 'nt':
        _spawn_nt(cmd, search_path, dry_run=dry_run)
    elif os.name == 'os2':
        _spawn_os2(cmd, search_path, dry_run=dry_run)
    else:
        raise DistutilsPlatformError, "don't know how to spawn programs on platform '%s'" % os.name


def _nt_quote_args(args):
    for i, arg in enumerate(args):
        if ' ' in arg:
            args[i] = '"%s"' % arg

    return args


def _spawn_nt(cmd, search_path = 1, verbose = 0, dry_run = 0):
    executable = cmd[0]
    cmd = _nt_quote_args(cmd)
    if search_path:
        executable = find_executable(executable) or executable
    log.info(' '.join([executable] + cmd[1:]))
    if not dry_run:
        try:
            rc = os.spawnv(os.P_WAIT, executable, cmd)
        except OSError as exc:
            raise DistutilsExecError, "command '%s' failed: %s" % (cmd[0], exc[-1])

        if rc != 0:
            raise DistutilsExecError, "command '%s' failed with exit status %d" % (cmd[0], rc)


def _spawn_os2(cmd, search_path = 1, verbose = 0, dry_run = 0):
    executable = cmd[0]
    if search_path:
        executable = find_executable(executable) or executable
    log.info(' '.join([executable] + cmd[1:]))
    if not dry_run:
        try:
            rc = os.spawnv(os.P_WAIT, executable, cmd)
        except OSError as exc:
            raise DistutilsExecError, "command '%s' failed: %s" % (cmd[0], exc[-1])

        if rc != 0:
            log.debug("command '%s' failed with exit status %d" % (cmd[0], rc))
            raise DistutilsExecError, "command '%s' failed with exit status %d" % (cmd[0], rc)


if sys.platform == 'darwin':
    from distutils import sysconfig
    _cfg_target = None
    _cfg_target_split = None

def _spawn_posix(cmd, search_path = 1, verbose = 0, dry_run = 0):
    global _cfg_target
    global _cfg_target_split
    log.info(' '.join(cmd))
    if dry_run:
        return
    exec_fn = search_path and os.execvp or os.execv
    exec_args = [cmd[0], cmd]
    if sys.platform == 'darwin':
        if _cfg_target is None:
            _cfg_target = sysconfig.get_config_var('MACOSX_DEPLOYMENT_TARGET') or ''
            if _cfg_target:
                _cfg_target_split = [ int(x) for x in _cfg_target.split('.') ]
        if _cfg_target:
            cur_target = os.environ.get('MACOSX_DEPLOYMENT_TARGET', _cfg_target)
            if _cfg_target_split > [ int(x) for x in cur_target.split('.') ]:
                my_msg = '$MACOSX_DEPLOYMENT_TARGET mismatch: now "%s" but "%s" during configure' % (cur_target, _cfg_target)
                raise DistutilsPlatformError(my_msg)
            env = dict(os.environ, MACOSX_DEPLOYMENT_TARGET=cur_target)
            exec_fn = search_path and os.execvpe or os.execve
            exec_args.append(env)
    pid = os.fork()
    if pid == 0:
        try:
            exec_fn(*exec_args)
        except OSError as e:
            sys.stderr.write('unable to execute %s: %s\n' % (cmd[0], e.strerror))
            os._exit(1)

        sys.stderr.write('unable to execute %s for unknown reasons' % cmd[0])
        os._exit(1)
    else:
        while 1:
            try:
                pid, status = os.waitpid(pid, 0)
            except OSError as exc:
                import errno
                if exc.errno == errno.EINTR:
                    continue
                raise DistutilsExecError, "command '%s' failed: %s" % (cmd[0], exc[-1])

            if os.WIFSIGNALED(status):
                raise DistutilsExecError, "command '%s' terminated by signal %d" % (cmd[0], os.WTERMSIG(status))
            elif os.WIFEXITED(status):
                exit_status = os.WEXITSTATUS(status)
                if exit_status == 0:
                    return
                raise DistutilsExecError, "command '%s' failed with exit status %d" % (cmd[0], exit_status)
            elif os.WIFSTOPPED(status):
                continue
            else:
                raise DistutilsExecError, "unknown error executing '%s': termination status %d" % (cmd[0], status)


def find_executable(executable, path = None):
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    base, ext = os.path.splitext(executable)
    if (sys.platform == 'win32' or os.name == 'os2') and ext != '.exe':
        executable = executable + '.exe'
    if not os.path.isfile(executable):
        for p in paths:
            f = os.path.join(p, executable)
            if os.path.isfile(f):
                return f

        return
    else:
        return executable
