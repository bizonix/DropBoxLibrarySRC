#Embedded file name: dropbox/sync_engine_file_system/linux.py
from __future__ import with_statement, absolute_import
import errno
import os
import sys
from unicodedata import normalize
from dropbox.nfcdetector import is_nfc
from dropbox.linux_libc import posix_fadvise, POSIX_FADV_SEQUENTIAL
from dropbox.trace import report_bad_assumption, unhandled_exc_handler
from .local_path import AbstractPosixPath
from .posix import PosixFileSystem
from .pythonos import PythonFile
from .util import FileSystemDirectory, convert_os_error, convert_os_error_dec, convert_errno_to_ioerror, mode_string_to_flags
from .xattr_util import path_supports_xattrs, XAttrAttributesHandle
if not hasattr(os, 'O_NOATIME'):
    os.O_NOATIME = 262144

class LinuxPath(AbstractPosixPath):
    SEPARATOR = u'/'

    def to_dropbox_ns_relative(self, parent_local_path):
        toret = super(LinuxPath, self).to_dropbox_ns_relative(parent_local_path)
        if not is_nfc(toret):
            raise Exception('Cannot convert Non-NFC Linux path to Dropbox %r %r' % (parent_local_path, toret))
        return toret

    def __repr__(self):
        return 'LinuxPath(%r)' % unicode(self)


class LinuxFile(PythonFile):

    def datasync(self):
        self.flush()
        with convert_errno_to_ioerror():
            return os.fdatasync(self.inner.fileno())


class FileSystem(PosixFileSystem):
    MACHINE_GUID_XATTR_PREFIX = u'user.com.dropbox.local-id.'
    USE_STATVFS = True
    HAS_O_NOATIME = True

    def __init__(self):
        if not sys.platform.startswith('linux'):
            raise Exception('This only works on a linux system')
        super(FileSystem, self).__init__(LinuxPath.from_path_string)

    def opendir(self, _path, **_kw):
        return FileSystemDirectory(unicode(_path), **_kw)

    def open(self, _path, _mode = 'r', sequential = False, no_atime = False, **_kw):
        mode_flags = mode_string_to_flags(_mode)
        path = unicode(_path)
        with convert_os_error():
            try:
                fd = os.open(path, mode_flags | os.O_NOCTTY | (os.O_NOATIME if no_atime else 0))
            except OSError as e:
                if no_atime and e.errno == errno.EPERM:
                    fd = os.open(path, mode_flags | os.O_NOCTTY)
                else:
                    raise

        if sequential:
            try:
                posix_fadvise(fd, 0, 0, POSIX_FADV_SEQUENTIAL)
            except Exception:
                unhandled_exc_handler()

        with convert_os_error():
            f = os.fdopen(fd, _mode)
        return LinuxFile(f)

    def open_attributes(self, _path):
        return XAttrAttributesHandle(_path, 'linux', 'user.com.dropbox.attributes')

    def supported_attributes(self, path = None):
        if path is None:
            return ()
        elif path_supports_xattrs(path):
            return ('linux',)
        else:
            return ()

    def exchangedata(self, *n, **kw):
        raise OSError(errno.EOPNOTSUPP, 'exchangedata not supported on linux')
