#Embedded file name: arch/posix_common/fixperms.py
import os
import stat
import tempfile
import threading
import sys
from functools import partial
from re import match
from signal import signal, SIGUSR2
import arch
from dropbox.globals import dropbox_globals
from dropbox.fastwalk_bridge import fastwalk
from dropbox.fileutils import check_perms
from dropbox.gui import message_sender
from dropbox.i18n import safe_activate_translation, trans
from dropbox.trace import TRACE, unhandled_exc_handler
authorization = arch.authorization

def fix_perm_on_directory(path, required_perms = 'rwX'):
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write('#!/bin/bash\nchown %(uid)s "%(rootdir)s"\nchmod u+%(perms)s "%(rootdir)s"\necho Done' % dict(uid=os.getuid(), rootdir=path.encode(sys.getfilesystemencoding()), pid=os.getpid(), perms=required_perms))
        temp_file.flush()
        safe_activate_translation()
        msg = trans(u'Dropbox needs to change permissions for the Folder: %(folder_name)s') % {'folder_name': path}
        f = authorization.request_authorization_from_user_and_run('/bin/sh', [temp_file.name], msg + u'\n\n')
        if f:
            try:
                TRACE('Permission Fix for %r: %r', path, f.read())
            finally:
                try:
                    f.close()
                except Exception:
                    unhandled_exc_handler()


def fix_perms(path, timeout = 5, call_on_mt = None, validate_perms = check_perms, required_perms = 'rwX', follow_symlinks = False):
    try:
        assert match('[rwxX]+', required_perms)
        try:
            usr_chmod(required_perms, path)
        except Exception:
            unhandled_exc_handler()

        try:
            for curr_dir, files in fastwalk(path, follow_symlinks=follow_symlinks):
                for f in files:
                    fullpath = f.fullpath
                    try:
                        usr_chmod(required_perms, fullpath)
                        TRACE('changed perms on %s' % fullpath)
                    except Exception:
                        unhandled_exc_handler()

        except Exception:
            unhandled_exc_handler()

        if validate_perms(path):
            return True
        TRACE("!! Couldn't fix permissions for '%s'. Trying more forcefully.", path)
        permissions_ok = threading.Event()

        def install_sigusr2_handler():
            try:
                return signal(SIGUSR2, partial(_sigusr2_handler, permissions_ok))
            except Exception:
                TRACE('!! Failed to install SIGUSR2 handler')
                unhandled_exc_handler()
                return -1

        try:
            old_handler = message_sender(call_on_mt, block=True)(install_sigusr2_handler)() if call_on_mt else install_sigusr2_handler()
            TRACE('Installed SIGUSR2 handler')
        except Exception:
            TRACE('!! Failed to install SIGUSR2 handler')
            unhandled_exc_handler()
            return False

        if old_handler == -1:
            TRACE('!! Failed to install SIGUSR2 handler')
            return False
        temp_file_path = None
        try:
            fd, temp_file_path = tempfile.mkstemp()
            try:
                os.close(fd)
            except Exception:
                unhandled_exc_handler()

            with open(temp_file_path, 'w') as temp_file:
                temp_file.write('#!/bin/bash\nchown -R %(uid)s "%(rootdir)s"\nchmod -R u+%(perms)s "%(rootdir)s"\nkill -s USR2 %(pid)d' % dict(uid=os.getuid(), rootdir=path.encode(sys.getfilesystemencoding()), pid=os.getpid(), perms=required_perms))
            safe_activate_translation()
            msg = trans(u'Dropbox needs your permission to save settings to your computer.')
            f = authorization.request_authorization_from_user_and_run('/bin/sh', [temp_file_path], msg + u'\n\n')
            if f:
                try:
                    TRACE('Permission Fix: %r', f.read())
                finally:
                    try:
                        f.close()
                    except Exception:
                        unhandled_exc_handler()

            permissions_ok.wait(timeout=timeout)
            return permissions_ok.isSet()
        except Exception:
            TRACE('!! Error running privileged command')
            unhandled_exc_handler()
            return False
        finally:
            if temp_file_path:
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    unhandled_exc_handler()

            def restore_sigusr2_handler():
                try:
                    signal(SIGUSR2, old_handler)
                except Exception:
                    TRACE('!! Error restoring old SIGUSR2 handler')
                    unhandled_exc_handler()

            if call_on_mt:
                call_on_mt(restore_sigusr2_handler)
            else:
                restore_sigusr2_handler()

    except Exception:
        unhandled_exc_handler()
        return False


def _sigusr2_handler(permissions_ok, signum, frame):
    TRACE('Got SIGUSR2!')
    permissions_ok.set()


def check_and_fix_permissions(path, timeout = 5):
    try:
        if check_perms(path, first_time=True, follow_symlinks=True):
            return True
        validate_fn = partial(check_perms, follow_symlinks=True)
        return fix_perms(path, timeout=timeout, validate_perms=validate_fn, follow_symlinks=True)
    except Exception:
        unhandled_exc_handler()
        return False


def fix_whole_dropbox_permissions(call_on_mt, timeout = 30):
    if 'dropbox' not in dropbox_globals:
        TRACE("!! User hasn't picked their Dropbox location, so we can't fix permissions yet")
        return True
    path = dropbox_globals['dropbox']

    def check_rw_perms(path):
        required_perms = os.R_OK | os.W_OK
        if os.access(path, required_perms):
            try:
                mode = os.lstat(path)[stat.ST_MODE]
            except OSError:
                return False

            if mode & stat.S_IRUSR:
                if mode & stat.S_IWUSR:
                    return True
        return False

    if check_perms(path, check_path=check_rw_perms, first_time=True, follow_symlinks=False):
        return True
    validate_fn = partial(check_perms, check_path=check_rw_perms, follow_symlinks=False)
    return fix_perms(path, timeout=timeout, call_on_mt=call_on_mt, validate_perms=validate_fn, required_perms='rw', follow_symlinks=False)


def usr_chmod(mod_str, path):
    newmode = mode = os.lstat(path)[stat.ST_MODE]
    for char in mod_str:
        if char == 'r':
            newmode |= stat.S_IRUSR
        elif char == 'w':
            newmode |= stat.S_IWUSR
        elif char == 'x':
            newmode |= stat.S_IXUSR
        elif char == 'X':
            if stat.S_ISDIR(mode) or mode & stat.S_IXGRP or mode & stat.S_IXOTH:
                newmode |= stat.S_IXUSR

    os.chmod(path, newmode)
