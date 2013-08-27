#Embedded file name: dropbox/win32_util.py
from __future__ import absolute_import
import os
import win32file
from dropbox.trace import unhandled_exc_handler

def find_media_type(path):
    try:
        if path.startswith(u'\\\\'):
            return (win32file.DRIVE_REMOTE, path)
        typepath = path
        type_ = win32file.DRIVE_NO_ROOT_DIR
        oldpath = None
        while type_ == win32file.DRIVE_NO_ROOT_DIR:
            if oldpath == typepath:
                return (None, typepath)
            type_ = win32file.GetDriveTypeW(typepath)
            oldpath = typepath
            typepath = os.path.dirname(typepath)

        return (type_, typepath)
    except Exception:
        unhandled_exc_handler()
        return (None, None)
