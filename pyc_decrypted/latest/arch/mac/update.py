#Embedded file name: arch/mac/update.py
from __future__ import absolute_import
import contextlib
import os
import shutil
import subprocess32 as subprocess
import sys
import tarfile
import time
import tempfile
from build_number import BUILD_KEY
from dropbox.functions import can_write_file
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.mac.internal import get_contents_root
from .constants import get_alt_install_path
from .util import encode_command_line_arg

class PermissionError(Exception):
    pass


def get_fs_encoding():
    try:
        fs_encoding = sys.getfilesystemencoding()
    except Exception:
        unhandled_exc_handler()
        fs_encoding = 'utf8'

    return fs_encoding


def get_update_root():
    fs_encoding = get_fs_encoding()
    contents_root = os.path.normpath(get_contents_root().encode(fs_encoding)).decode(fs_encoding)
    if not os.access(contents_root, os.W_OK) or not os.access(os.path.dirname(contents_root), os.W_OK):
        alt_install_path = get_alt_install_path()
        contents_root = os.path.join(alt_install_path, u'Contents')
    return contents_root


def can_update():
    contents_root = get_update_root()
    TRACE('Checking can_update for location: %s', contents_root)
    if not os.path.exists(contents_root):
        if not can_write_file(contents_root):
            raise PermissionError(contents_root)
    elif not os.access(contents_root, os.W_OK) or not os.access(os.path.dirname(contents_root), os.W_OK):
        raise PermissionError(contents_root)


EXTENSION = '.tar.bz2'

def extract(fn, contents_root, report_func):
    fs_encoding = get_fs_encoding()
    if not os.path.exists(contents_root):
        os.makedirs(contents_root)
    try:
        if report_func:
            report_func('plat_mac_started_read_tarfile')
    except Exception:
        unhandled_exc_handler()

    TRACE('extract(): Reading tarfile %r', fn)
    app_dir = os.path.dirname(contents_root)
    new_contents_root = None
    try:
        new_contents_root = tempfile.mkdtemp(dir=app_dir.encode(fs_encoding)).decode(fs_encoding)
        os.chmod(new_contents_root, 493)
    except Exception:
        unhandled_exc_handler()
        if new_contents_root:
            shutil.rmtree(new_contents_root, ignore_errors=True)
        new_contents_root = os.path.join(app_dir, u'NewContents')
        if os.path.isdir(new_contents_root):
            shutil.rmtree(new_contents_root)
        elif os.path.exists(new_contents_root):
            os.remove(new_contents_root)
        os.mkdir(new_contents_root)
        os.chmod(new_contents_root, 493)

    try:
        with contextlib.closing(tarfile.open(fn, 'r:bz2')) as tf:
            tf.errorlevel = 1
            try:
                if report_func:
                    report_func('plat_mac_started_extraction')
            except Exception:
                unhandled_exc_handler()

            TRACE('extract(): Starting extraction')
            tf.extractall(new_contents_root.encode(fs_encoding))
    except Exception:
        ex = sys.exc_info()
        try:
            try:
                shutil.rmtree(new_contents_root)
            except Exception:
                unhandled_exc_handler()

            raise ex[0], ex[1], ex[2]
        finally:
            del ex

    rollback_dir = os.path.join(app_dir, u'rollback')
    if os.path.isdir(rollback_dir):
        shutil.rmtree(rollback_dir)
    elif os.path.exists(rollback_dir):
        os.remove(rollback_dir)
    TRACE('extract(): renaming %r to %r', contents_root, rollback_dir)
    os.rename(contents_root, rollback_dir)
    try:
        TRACE('extract(): renaming %r to %r', new_contents_root, contents_root)
        os.rename(new_contents_root, contents_root)
    except Exception:
        ex = sys.exc_info()
        try:
            try:
                os.rename(rollback_dir, contents_root)
            except Exception:
                unhandled_exc_handler()

            try:
                shutil.rmtree(new_contents_root)
            except Exception:
                unhandled_exc_handler()

            raise ex[0], ex[1], ex[2]
        finally:
            del ex

    def to_rollback():
        try:
            TRACE('rollback(): renaming %r to %r', contents_root, new_contents_root)
            os.rename(contents_root, new_contents_root)
            TRACE('rollback(): renaming %r to %r', rollback_dir, contents_root)
            os.rename(rollback_dir, contents_root)
            TRACE('rollback(): rmtree %r', new_contents_root)
            shutil.rmtree(new_contents_root)
        except Exception:
            unhandled_exc_handler()

    return to_rollback


def update_with_archive(fn, report_func = None, dbkeyname = None):
    contents_root = get_update_root()
    torollback = extract(fn, contents_root, report_func)
    try:
        if report_func:
            report_func('restart_new_client')
    except Exception:
        unhandled_exc_handler()

    try:
        cmd = [encode_command_line_arg(os.path.join(contents_root, u'MacOS/%s' % BUILD_KEY)), '/firstrunupdate', str(os.getpid())]
        TRACE('Executing %r', cmd)
        subprocess.call(cmd, close_fds=True, cwd=u'/')
        time.sleep(300)
        raise Exception('Update did not start in 5 min')
    except Exception:
        torollback()
        raise


def update_to(fn, version, cache_path, report_func = None, host_id = None, dbkeyname = None):
    TRACE('Extracting %r', fn)
    update_with_archive(fn, report_func=report_func, dbkeyname=dbkeyname)
