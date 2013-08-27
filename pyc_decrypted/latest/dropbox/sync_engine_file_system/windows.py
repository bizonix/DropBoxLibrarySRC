#Embedded file name: dropbox/sync_engine_file_system/windows.py
from __future__ import with_statement, absolute_import
import base64
import errno
import functools
import os
import struct
import sys
from unicodedata import normalize
import pywintypes
import win32api
import win32con
import win32file
import winerror
from pynt.helpers import fileapi
from pynt.constants import ERROR_UNABLE_TO_MOVE_REPLACEMENT, ERROR_UNABLE_TO_MOVE_REPLACEMENT_2, ERROR_UNABLE_TO_REMOVE_REPLACED, ERROR_SYMLINK_NOT_SUPPORTED
from dropbox.nfcdetector import is_nfc
from dropbox import fsutil
from dropbox.features import feature_enabled
from dropbox.misc import protect_closed
from dropbox.trace import TRACE, assert_, report_bad_assumption, unhandled_exc_handler
from .abstract_file_system import AbstractFile
from .ads_util import XAttrAttributesHandleWin
from .constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR
from .exceptions import create_file_system_error, create_io_error
from .local_path import AbstractLocalPath
from .pythonos import FileSystem as PythonFileSystem
from .util import FileSystemDirectory, IndexingAttributes, convert_error, convert_os_error, convert_os_error_dec
from .windows_error import windows_error_to_errno
mode_flag_map = {'r': (win32con.GENERIC_READ, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_DELETE | win32con.FILE_SHARE_WRITE, win32con.OPEN_EXISTING),
 'r+': (win32con.GENERIC_READ | win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ, win32con.OPEN_EXISTING),
 'w': (win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ, win32con.CREATE_ALWAYS),
 'w+': (win32con.GENERIC_READ | win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ, win32con.CREATE_ALWAYS),
 'a': (win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ, win32con.OPEN_ALWAYS),
 'a+': (win32con.GENERIC_READ | win32con.GENERIC_WRITE, win32con.FILE_SHARE_READ, win32con.OPEN_ALWAYS)}
NT_PATH_PREFIX = u'\\\\?\\'
NT_SHARED_PATH_PREFIX = u'\\\\?\\UNC\\'
UNC_PATH_PREFIX = u'\\\\'

def get_real_file_path(suspected_symlink):
    handle = fileapi.create_file(suspected_symlink, fileapi.GENERIC_READ, 0, fileapi.OPEN_EXISTING, 0)
    try:
        return fileapi.get_final_path_name_by_handle(handle, 0)[4:]
    finally:
        fileapi.close_handle(handle)


def is_escaped_nt_path(path):
    return unicode(path).startswith(NT_PATH_PREFIX)


def nt_escape_path(path):
    assert isinstance(path, unicode)
    assert not is_escaped_nt_path(path)
    if path.startswith(UNC_PATH_PREFIX):
        return NT_SHARED_PATH_PREFIX + path[len(UNC_PATH_PREFIX):]
    else:
        return NT_PATH_PREFIX + path


def nt_unescape_path(path):
    assert isinstance(path, unicode)
    assert is_escaped_nt_path(path)
    if path.startswith(NT_SHARED_PATH_PREFIX):
        return UNC_PATH_PREFIX + path[len(NT_SHARED_PATH_PREFIX):]
    else:
        return path[len(NT_PATH_PREFIX):]


def is_drive_letter(char):
    d = ord(char)
    return 65 <= d <= 90 or 97 <= d <= 122


def is_root_without_slash(path):
    p = unicode(path)
    return len(p) == 6 and is_escaped_nt_path(p) and is_drive_letter(p[4]) and p[5] == u':' or len(p) == 2 and is_drive_letter(p[0]) and p[1] == ':'


class WindowsPath(AbstractLocalPath):
    SEPARATOR = u'\\'

    @classmethod
    def _join_validate(cls, comp):
        if comp in (u'.', u'..'):
            return "Cannot use '.' or '..' as path components"

    @classmethod
    def from_path_string(cls, path):
        return cls._from_path_string(path)

    def to_dropbox_ns_relative(self, parent_local_path):
        toret = super(WindowsPath, self).to_dropbox_ns_relative(parent_local_path)
        if not is_nfc(toret):
            raise Exception('Cannot convert Non-NFC Windows path to Dropbox: %r %r' % (parent_local_path, toret))
        return toret

    def __repr__(self):
        return 'WindowsPath(%r)' % unicode(self)

    @property
    def dirname(self):
        if self.is_root:
            return self
        else:
            parent, child = unicode(self).rsplit(self.SEPARATOR, 1)
            if is_root_without_slash(parent):
                return self.from_path_string(parent + self.SEPARATOR)
            return self.from_path_string(parent)

    @property
    def is_root(self):
        return is_root_without_slash(self.p[:-1]) and unicode(self.p[-1]) == self.SEPARATOR


def create_pywin_error_converter(create_error):

    def pywin_error_to_error(e):
        if isinstance(e, pywintypes.error):
            try:
                message = e[2]
            except IndexError:
                message = None

            return create_error(windows_error_to_errno(e[0]), message=message)
        else:
            return e

    return pywin_error_to_error


def convert_pywin_error_fs_error():
    return convert_error(create_pywin_error_converter(create_file_system_error))


def convert_pywin_error_fs_error_dec(f):

    @functools.wraps(f)
    def wrapped(*n, **kw):
        with convert_pywin_error_fs_error():
            return f(*n, **kw)

    return wrapped


def convert_pywin_error_ioerror():
    return convert_error(create_pywin_error_converter(create_io_error))


def convert_pywin_error_ioerror_dec(f):

    @functools.wraps(f)
    def wrapped(*n, **kw):
        with convert_pywin_error_ioerror():
            return f(*n, **kw)

    return wrapped


class WindowsFile(AbstractFile):

    def __init__(self, path, mode, sequential = False, **kw):
        self.hFile = None
        self.name = unicode(path)
        if mode not in mode_flag_map:
            raise ValueError('Opening file %r with an invalid mode (%r)' % (self.name, mode))
        full_path = nt_escape_path(self.name)
        flags = mode_flag_map[mode]
        with convert_pywin_error_fs_error():
            self.hFile = win32file.CreateFileW(full_path, flags[0], flags[1], None, flags[2], win32con.FILE_FLAG_SEQUENTIAL_SCAN if sequential else 0, 0)
        self.appendMode = mode.startswith(u'a')
        self.read_only = mode == 'r'

    @property
    def closed(self):
        return self.hFile is None

    @convert_pywin_error_ioerror_dec
    @protect_closed
    def seek(self, offset, whence = os.SEEK_SET):
        move_method = None
        if whence == os.SEEK_SET:
            move_method = win32con.FILE_BEGIN
        elif whence == os.SEEK_END:
            move_method = win32con.FILE_END
        elif whence == os.SEEK_CUR:
            move_method = win32con.FILE_CURRENT
        else:
            raise IOError(errno.EINVAL, os.strerror(errno.EINVAL))
        win32file.SetFilePointer(self.hFile, offset, move_method)

    @convert_pywin_error_ioerror_dec
    @protect_closed
    def tell(self):
        return win32file.SetFilePointer(self.hFile, 0, 1)

    @convert_pywin_error_ioerror_dec
    @protect_closed
    def read(self, length = None):
        if length is None:
            toret = []
            while True:
                toadd = win32file.ReadFile(self.hFile, 4194304)[1]
                if not toadd:
                    break
                toret.append(toadd)

            return ''.join(toret)
        else:
            return win32file.ReadFile(self.hFile, length)[1]

    @convert_pywin_error_ioerror_dec
    @protect_closed
    def write(self, data):
        if self.appendMode:
            self.seek(0, os.SEEK_END)
        return win32file.WriteFile(self.hFile, data)[1]

    @convert_pywin_error_ioerror_dec
    def close(self):
        if self.hFile is not None:
            win32api.CloseHandle(self.hFile)
            self.hFile = None

    @convert_pywin_error_ioerror_dec
    @protect_closed
    def truncate(self):
        if self.read_only:
            raise IOError('Cannot truncate a read-only file')
        win32file.SetEndOfFile(self.hFile)

    def flush(self):
        pass

    @convert_pywin_error_ioerror_dec
    @protect_closed
    def sync(self):
        win32file.FlushFileBuffers(self.hFile)


class FileSystem(PythonFileSystem):

    def __init__(self):
        if not sys.platform.startswith('win'):
            raise Exception('This only works on a Windows system')
        super(FileSystem, self).__init__(WindowsPath.from_path_string)

    def open(self, _path, _mode = 'r', sequential = False, **_kw):
        return WindowsFile(_path, _mode, sequential, **_kw)

    def open_attributes(self, _path):
        return XAttrAttributesHandleWin(self, _path)

    def opendir(self, _path, **_kw):
        return FileSystemDirectory(unicode(_path), **_kw)

    @convert_os_error_dec
    def rename(self, src, dst):
        return fileapi.move_file_ex(unicode(src), unicode(dst), replace_existing=True)

    @convert_os_error_dec
    def win32_get_file_attributes(self, path, *n):
        return fileapi.get_file_attributes(unicode(path), *n)

    @convert_os_error_dec
    def win32_set_file_attributes(self, path, *n):
        return fileapi.set_file_attributes(unicode(path), *n)

    @convert_os_error_dec
    def win32_get_file_security(self, path, *n):
        return fileapi.get_file_security(unicode(path), *n)

    @convert_os_error_dec
    def win32_set_file_security(self, path, *n):
        return fileapi.set_file_security(unicode(path), *n)

    @convert_os_error_dec
    def win32_inherit_not_content_indexing(self, path):
        pattrs = self.win32_get_file_attributes(path.dirname)
        attrs = self.win32_get_file_attributes(path)
        if (attrs ^ pattrs) & fileapi.FILE_ATTRIBUTE_NOT_CONTENT_INDEXED:
            attrs ^= fileapi.FILE_ATTRIBUTE_NOT_CONTENT_INDEXED
        self.win32_set_file_attributes(path, attrs)

    @convert_os_error_dec
    def realpath(self, path):
        try:
            handle = fileapi.create_file(unicode(path), fileapi.GENERIC_READ, fileapi.FILE_SHARE_READ | fileapi.FILE_SHARE_WRITE | fileapi.FILE_SHARE_DELETE, fileapi.OPEN_EXISTING, fileapi.FILE_ATTRIBUTE_NORMAL | fileapi.FILE_FLAG_BACKUP_SEMANTICS)
            try:
                realpath = unicode(fileapi.get_final_path_name_by_handle(handle, 0))
                if is_escaped_nt_path(realpath):
                    realpath = nt_unescape_path(realpath)
                return self.make_path(realpath)
            finally:
                fileapi.close_handle(handle)

        except Exception:
            return super(FileSystem, self).realpath(path)

    @convert_pywin_error_fs_error_dec
    def get_disk_free_space(self, path):
        return win32file.GetDiskFreeSpaceEx(unicode(path))[0]

    @convert_pywin_error_fs_error_dec
    def set_file_time(self, fn, creation, access, modified):
        hFile = win32file.CreateFileW(unicode(fn), win32file.GENERIC_WRITE, win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_DELETE, None, win32file.OPEN_EXISTING, win32file.FILE_FLAG_BACKUP_SEMANTICS, 0)
        try:
            win32file.SetFileTime(hFile, None if creation is None else pywintypes.Time(creation), None if access is None else pywintypes.Time(access), None if modified is None else pywintypes.Time(modified))
        finally:
            win32file.CloseHandle(hFile)

    def _replace_file(self, dest, src, backup_file, temp_prefix):
        destu = unicode(dest)
        srcu = unicode(src)
        backup_fileu = unicode(backup_file)
        try:
            fileapi.replace_file(destu, srcu, 1, backup_fileu)
        except WindowsError as e:
            if e.winerror == ERROR_SYMLINK_NOT_SUPPORTED:
                real_dest_path = self.make_path(get_real_file_path(destu))
                real_dest_dir = real_dest_path.dirname
                with fsutil.tempfilename(self, dir=real_dest_dir, prefix=temp_prefix) as temp_src_file:
                    with fsutil.tempfilename(self, dir=real_dest_dir, prefix=temp_prefix) as temp_backup_file:
                        self.remove(temp_src_file)
                        self.remove(temp_backup_file)
                        fsutil.safe_move(self, src, temp_src_file)
                        fileapi.replace_file(unicode(real_dest_path), unicode(temp_src_file), 1, unicode(temp_backup_file))
                        fsutil.safe_move(self, temp_backup_file, backup_file)
            elif e.winerror in (ERROR_UNABLE_TO_MOVE_REPLACEMENT, ERROR_UNABLE_TO_REMOVE_REPLACED):
                raise create_file_system_error(errno.EOPNOTSUPP)
            elif e.winerror == ERROR_UNABLE_TO_MOVE_REPLACEMENT_2:
                try:
                    fsutil.safe_move(self, src, dest)
                except Exception:
                    report_bad_assumption('ERROR_UNABLE_TO_MOVE_REPLACEMENT_2 fails')
                    raise

            else:
                raise

    def exchangedata(self, src, dest, temp_prefix = ''):
        backup_file = src.append('.backup')
        self._replace_file(dest, src, backup_file, temp_prefix)
        try:
            fsutil.safe_move(self, backup_file, src)
        except Exception:
            unhandled_exc_handler()
            report_bad_assumption("Couldn't move backup file to temp file for reconstruct")

    @convert_pywin_error_fs_error_dec
    def is_normal_file(self, path):
        h = win32file.CreateFileW(unicode(path), win32con.READ_CONTROL, 0, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS, None)
        try:
            fi = win32file.GetFileInformationByHandle(h)
            return fi[7] == 1 and not fi[0] & 1024 and not fi[0] & 16
        finally:
            win32file.CloseHandle(h)

    def indexing_attributes(self, path, resolve_link = True, write_machine_guid = False):
        with convert_os_error():
            handle = fileapi.create_file(unicode(path), fileapi.READ_CONTROL, fileapi.FILE_SHARE_READ | fileapi.FILE_SHARE_DELETE | fileapi.FILE_SHARE_WRITE, fileapi.OPEN_EXISTING, fileapi.FILE_FLAG_BACKUP_SEMANTICS)
            try:
                info = fileapi.get_file_information_by_handle(handle)
                file_objectid_buffer = None
                if feature_enabled('fileids'):
                    try:
                        if write_machine_guid:
                            file_objectid_buffer = fileapi.create_or_get_object_id(handle)
                        else:
                            file_objectid_buffer = fileapi.get_object_id(handle)
                    except WindowsError as e:
                        if e.winerror == winerror.ERROR_INVALID_FUNCTION:
                            TRACE('Filesystem does not support object ids on path %r', path)
                        elif e.winerror == winerror.ERROR_FILE_NOT_FOUND and not write_machine_guid:
                            pass
                        else:
                            unhandled_exc_handler()

            finally:
                fileapi.close_handle(handle)

        file_type_ = FILE_TYPE_DIRECTORY if info.file_attributes & fileapi.FILE_ATTRIBUTE_DIRECTORY else FILE_TYPE_REGULAR
        if file_objectid_buffer is not None:
            binary_machine_guid = struct.pack('!B3xL16s', 3, info.volume_serial_number, str(file_objectid_buffer.object_id))
            machine_guid = unicode(base64.urlsafe_b64encode(binary_machine_guid)).rstrip(u'=')
        else:
            machine_guid = None
        return IndexingAttributes(atime=info.last_access_time, size=info.file_size, mtime=info.last_write_time, type=file_type_, volume_id=info.volume_serial_number, file_id=info.file_index, ctime=info.last_write_time, machine_guid=machine_guid)

    def supports_extension(self, ext):
        return super(FileSystem, self).supports_extension(ext) or ext in ('win32', 'exchangedata')
