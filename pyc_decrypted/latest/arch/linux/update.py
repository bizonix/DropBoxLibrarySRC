#Embedded file name: arch/linux/update.py
from __future__ import absolute_import
import contextlib
import subprocess32 as subprocess
import shutil
import os
import time
import tarfile
import tempfile
import sys
from dropbox.functions import can_write_file
from dropbox.trace import unhandled_exc_handler, TRACE
from .constants import update_root
from .util import running_dropbox_instances, encode_command_line_arg

class PermissionError(Exception):
    pass


def can_update():
    TRACE('Checking can_update for location: %s', update_root)
    if not os.path.exists(update_root):
        if not can_write_file(update_root):
            raise PermissionError(update_root)
    elif not os.access(update_root, os.W_OK) or not os.access(os.path.dirname(update_root), os.W_OK):
        raise PermissionError(update_root)


EXTENSION = '.tar.gz'

def update_with_archive(fn, report_func = None):
    newdir = tempfile.mkdtemp(prefix='.dropbox-dist-new-').decode(sys.getfilesystemencoding())
    try:
        try:
            if report_func:
                report_func('plat_linux_started_read_tarfile')
        except Exception:
            unhandled_exc_handler()

        TRACE('tarfile opening')
        with contextlib.closing(tarfile.open(fn, 'r:gz')) as tf:
            TRACE('extracting all')
            try:
                if report_func:
                    report_func('plat_linux_started_extraction')
            except Exception:
                unhandled_exc_handler()

            if os.path.exists(newdir):
                shutil.rmtree(newdir)
            os.mkdir(newdir)
            tf.extractall(newdir.encode(sys.getfilesystemencoding()))
        try:
            if report_func:
                report_func('restart_new_client')
        except Exception:
            unhandled_exc_handler()

        cmd = [os.path.join(newdir, u'.dropbox-dist/dropboxd').encode(sys.getfilesystemencoding()),
         '/firstrunupdate',
         str(os.getpid()),
         encode_command_line_arg(update_root)]
        TRACE('Executing %r', cmd)
        subprocess.call(cmd, close_fds=True, cwd=u'/')
        time.sleep(900)
        raise Exception('Update did not start in 15 min')
    except Exception:
        exc = sys.exc_info()
        try:
            try:
                TRACE('our pid: %r, our user: %r, other instances: %r', os.getpid(), os.environ.get('USER'), tuple(running_dropbox_instances()))
            except Exception:
                unhandled_exc_handler()

            raise exc[0], exc[1], exc[2]
        finally:
            del exc

    return True


def update_to(fn, version, cache_path, report_func = None, host_id = None, **kw):
    TRACE('Extracting %r', fn)
    update_with_archive(fn, report_func=report_func)
