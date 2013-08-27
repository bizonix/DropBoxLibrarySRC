#Embedded file name: arch/win32/update.py
from __future__ import absolute_import
import os
import time
import ctypes
import win32api
import win32con
from build_number import BUILD_KEY
from dropbox.globals import dropbox_globals
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.build_common import get_build_number, get_platform
from .constants import appdata_path

def can_update():
    pass


EXTENSION = '.exe'

def update_to(fn, version, cache_path, report_func = None, host_id = None, **kw):
    TRACE('Running %r', fn)
    args = '/S'
    try:
        ctypes.windll.Shell32.ShellExecuteW(0, u'open', fn, unicode(args), cache_path, win32con.SW_HIDE)
    except Exception:
        unhandled_exc_handler()
        win32api.ShellExecute(0, 'open', fn, args, cache_path, win32con.SW_HIDE)

    time.sleep(900)
    raise Exception('Update did not complete in 15 min')
