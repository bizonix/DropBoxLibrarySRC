#Embedded file name: arch/posix_common/util.py
import os
import errno
import statvfs
import stat
import sys
import shutil
import signal
from socket import socketpair
import build_number
from dropbox.trace import TRACE, unhandled_exc_handler

def get_disk_free_space(local_path):
    search = local_path
    while True:
        try:
            volume_stat = os.statvfs(search)
            return volume_stat[statvfs.F_BAVAIL] * volume_stat[statvfs.F_FRSIZE]
        except Exception:
            oldsearch = search
            search = os.path.dirname(search)
            if search == oldsearch:
                return 0


def paths_on_same_device(path1, path2):
    return os.stat(os.path.abspath(path1))[stat.ST_DEV] == os.stat(os.path.abspath(path2))[stat.ST_DEV]


def kill_pid(pid):
    os.kill(pid, signal.SIGKILL)


def encode_command_line_arg(arg):
    assert isinstance(arg, unicode), 'Expected command line arg %r to be unicode' % (arg,)
    return arg.encode('utf-8')


def decode_command_line_args(argv):
    return [ arg.decode('utf-8') for arg in argv ]


def handle_extra_command_line_args(*n, **kw):
    pass
