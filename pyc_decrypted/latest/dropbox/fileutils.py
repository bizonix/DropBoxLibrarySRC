#Embedded file name: dropbox/fileutils.py
from __future__ import absolute_import
import contextlib
import errno
import shutil
import sys
import tempfile
import os
from dropbox.dirtraverse import Directory
from dropbox.fastwalk_bridge import fastwalk_with_exception_handling
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler, trace_stack
from dropbox.lock_ordering import NonRecursiveLock
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY

def check_perms(path, check_path = None, first_time = False, follow_symlinks = True, report = False):
    try:
        if not check_path:

            def access_check(path):
                required_perms = os.R_OK | os.W_OK
                return os.access(path, required_perms)

            check_path = access_check
        stat_fn = os.stat
        if not follow_symlinks:
            stat_fn = os.lstat
        try:
            stat_fn(path)
        except OSError as e:
            if first_time and e.errno is errno.ENOENT:
                TRACE("Data folder doesn't yet exist; assuming we can create it")
                return True
            else:
                unhandled_exc_handler()
                TRACE("!! Error accessing required file '%s': %r", path, e)
                return False

        have_perms = check_path(path)
        if not have_perms:
            ts = "!! Don't have sufficient permissions to %s" % path
            TRACE(ts)
            if report:
                report_bad_assumption(ts)
            return False
        try:
            with contextlib.closing(Directory(path)) as d:
                for dirent in d:
                    child_path = os.path.join(path, dirent.name)
                    if os.path.isdir(child_path):
                        if not check_perms(child_path, check_path=check_path, follow_symlinks=follow_symlinks, report=report):
                            return False
                    elif not check_path(child_path):
                        return False

        except Exception as e:
            TRACE('Exception iterating over the directory: %s' % e)
            unhandled_exc_handler()
            return False

        return True
    except Exception:
        unhandled_exc_handler()
        return False


def safe_remove(path):
    try:
        os.remove(path)
        return
    except OSError as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
            trace_stack()
        else:
            return
    except Exception:
        unhandled_exc_handler()
        trace_stack()

    try:
        with open(path, 'r+') as f:
            f.seek(0)
            f.truncate()
            f.flush()
            os.fsync(f.fileno())
    except (IOError, OSError) as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
    except Exception:
        trace_stack()
        unhandled_exc_handler()


def _posix_xdev_move(src, dst):
    try:
        os.rename(src, dst)
    except OSError as e:
        if e.errno == errno.EXDEV:
            shutil.copy2(src, dst)
            os.unlink(src)
        else:
            raise


def umkstemp(dir = None, **kw):
    if dir is not None:
        dir = dir.encode(sys.getfilesystemencoding())
    f, tmp = tempfile.mkstemp(dir=dir, **kw)
    return (f, tmp.decode(sys.getfilesystemencoding()))


@contextlib.contextmanager
def tempfilename(**kw):
    f, fn = umkstemp(**kw)
    try:
        os.close(f)
        yield fn
    finally:
        safe_remove(fn)


safe_move = os.rename if sys.platform.lower().startswith('win') else _posix_xdev_move
chdir_lock = NonRecursiveLock()

@contextlib.contextmanager
def safe_chdir(local_path):
    with chdir_lock:
        cwd = os.getcwd()
        TRACE('!!Changing working directory to %r', local_path)
        os.chdir(local_path)
        try:
            yield
        finally:
            os.chdir(cwd)
            TRACE('!!Changed working directory back to %r', cwd)
