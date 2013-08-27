#Embedded file name: arch/win32/locked_files.py
from __future__ import absolute_import
import win32api
import win32file
import win32security
import win32con
locked_file_privileges = False

class LockedFile(object):

    def __init__(self, handle):
        self.handle = handle
        self.context = 0
        self.buffer = None

    def read(self, bytes = 4194304):
        hr, buf, context = win32file.BackupRead(self.handle, bytes, self.buffer, 0, 0, self.context)
        self.buffer, self.context = buf, context
        return str(buf)

    def close(self):
        win32api.CloseHandle(self.handle)


def open_locked(path):
    h = win32file.CreateFile(path, win32con.READ_CONTROL, 0, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS, None)
    return LockedFile(h)


def set_privilege(priv):
    flags = win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
    htoken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), flags)
    id = win32security.LookupPrivilegeValue(None, priv)
    win32security.AdjustTokenPrivileges(htoken, 0, [(id, win32security.SE_PRIVILEGE_ENABLED)])


def init_backup_privileges():
    set_privilege(win32security.SE_BACKUP_NAME)
    set_privilege(win32security.SE_RESTORE_NAME)


if __name__ == '__main__':
    import traceback
    try:
        from hashlib import md5
        init_backup_privileges()
        f = open_locked('c:\\python24\\test.doc')
        print md5(f.read()).hexdigest()
        f.close()
    except:
        traceback.print_exc()
