#Embedded file name: dropbox/ideal_tracker/identifiers.py
import base64
import os
import os.path
import struct
from pylinux import statvfs
from dropbox.platform import platform

class Identifier(object):

    @staticmethod
    def get(path, create = False):
        return FSInodeIdentifier.get(path)

    @staticmethod
    def create(path):
        return FSInodeIdentifier.get(path)


class FSInodeIdentifier(object):
    if platform == 'linux':
        USE_STATVFS = True
    elif platform == 'mac':
        USE_STATVFS = False

    @staticmethod
    def get(path):
        try:
            st_info = os.stat(unicode(path))
            inode = st_info.st_ino
            if FSInodeIdentifier.USE_STATVFS:
                vfs_info = statvfs(unicode(path))
                fs_id = vfs_info.f_fsid
            else:
                fs_id = st_info.st_dev
        except OSError:
            return None

        data = struct.pack('!QQ', fs_id, inode)
        return unicode(base64.urlsafe_b64encode(data)).rstrip(u'=')
