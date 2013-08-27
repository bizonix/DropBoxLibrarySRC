#Embedded file name: dropbox/fd_leak_debugging.py
from __future__ import absolute_import
import os
import subprocess32 as subprocess
import time
import threading
from dropbox.platform import platform
from dropbox.trace import report_bad_assumption, TRACE
RATELIMIT_MIN_DELAY = 7200
_metawatch_module_name_lock = threading.Lock()
_metawatch_module_name = None

def notify_metawatch_change(metawatch):
    global _metawatch_module_name
    with _metawatch_module_name_lock:
        _metawatch_module_name = metawatch.__class__.__module__ if metawatch is not None else None


_last_report_time_lock = threading.Lock()
_last_report_time = None

def debug_fd_leak(threshold = 200):
    global _last_report_time
    if platform == 'mac':
        cmd = ['lsof',
         '-n',
         '-P',
         '-p',
         str(os.getpid())]
    elif platform == 'linux':
        cmd = ['ls', '-l', '/proc/%d/fd/' % os.getpid()]
    else:
        return
    r, w = os.pipe()
    os.close(r)
    os.close(w)
    fd_num = min(r, w)
    if fd_num <= threshold:
        return
    with _metawatch_module_name_lock:
        metawatch_module_name = _metawatch_module_name
    now = time.time()
    with _last_report_time_lock:
        if _last_report_time is not None and now < _last_report_time:
            _last_report_time = None
        if _last_report_time is not None and now - _last_report_time < RATELIMIT_MIN_DELAY:
            return
        _last_report_time = now
    if metawatch_module_name == 'arch.mac.directory_reader':
        report_bad_assumption('Got a filedescriptor number greater than %d: %d (metawatch is from %s - Mac kqueue)', threshold, r, metawatch_module_name)
    elif metawatch_module_name == 'arch.mac.daemon_reader':
        report_bad_assumption('Got a filedescriptor number greater than %d: %d (metawatch is from %s - Mac dbfseventsd)', threshold, r, metawatch_module_name)
    elif metawatch_module_name == 'arch.mac.fsevents_reader':
        report_bad_assumption('Got a filedescriptor number greater than %d: %d (metawatch is from %s - Mac FSEvents)', threshold, r, metawatch_module_name)
    elif metawatch_module_name == 'arch.linux.directory_reader':
        report_bad_assumption('Got a filedescriptor number greater than %d: %d (metawatch is from %s - Linux Inotify)', threshold, r, metawatch_module_name)
    elif metawatch_module_name == 'arch.win32.directory_reader':
        report_bad_assumption('Got a filedescriptor number greater than %d: %d (metawatch is from %s - Win32 ReadDirectoryChangesW)', threshold, r, metawatch_module_name)
    else:
        report_bad_assumption('Got a filedescriptor number greater than %d: %d (metawatch is from %s - ???)', threshold, r, metawatch_module_name)
    TRACE('!! debug_fd_leak: Executing command to get filedescriptor info: %r', cmd)
    try:
        output, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
        for line in output.rstrip().split('\n'):
            TRACE('!! debug_fd_leak:  Output: %s', line)

        TRACE('!! debug_fd_leak:  Output ended.')
    except Exception as e:
        TRACE('!! debug_fd_leak:  Failed: %r', e)
