#Embedded file name: dropbox/dirtraverse_win32.py
from __future__ import absolute_import
import sys
import ctypes
import os
from ctypes.wintypes import HANDLE
import win32file
from win32file import FILE_ATTRIBUTE_DIRECTORY, INVALID_HANDLE_VALUE
from winerror import ERROR_NO_MORE_FILES, ERROR_PATH_NOT_FOUND, ERROR_FILE_NOT_FOUND
from winnt import FILE_ATTRIBUTE_REPARSE_POINT
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR
from dropbox.win32.kernel32 import FindFirstFileExW, FindNextFileW, FindClose, WIN32_FIND_DATAW, FindExInfoBasic, FindExInfoStandard, FindExSearchNameMatch, FIND_FIRST_EX_LARGE_FETCH, GetLastError
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.debugging import easy_repr
from dropbox.dirtraverse_common import _DirectoryAbstract
from dropbox.win32.version import WIN7, WINDOWS_VERSION
WIN32_REPARSE_TAG_DFS = 'dfs'
WIN32_REPARSE_TAG_DFSR = 'dfsr'
WIN32_REPARSE_TAG_HSM = 'hsm'
WIN32_REPARSE_TAG_MOUNT_POINT = 'mount-point'
WIN32_REPARSE_TAG_RESERVED_ONE = 'reserved-one'
WIN32_REPARSE_TAG_RESERVED_RANGE = 'reserved-range'
WIN32_REPARSE_TAG_RESERVED_ZERO = 'reserved-zero'
WIN32_REPARSE_TAG_SIS = 'sis'
WIN32_REPARSE_TAG_SYMLINK = 'symlink'
WIN32_REPARSE_TAGS = (WIN32_REPARSE_TAG_DFS,
 WIN32_REPARSE_TAG_DFSR,
 WIN32_REPARSE_TAG_HSM,
 WIN32_REPARSE_TAG_MOUNT_POINT,
 WIN32_REPARSE_TAG_RESERVED_ONE,
 WIN32_REPARSE_TAG_RESERVED_RANGE,
 WIN32_REPARSE_TAG_RESERVED_ZERO,
 WIN32_REPARSE_TAG_SIS,
 WIN32_REPARSE_TAG_SYMLINK)

def win32_reparse_tag_to_human_readable(reparse_tag):
    return reparse_tag.replace('-', ' ')


GET_TAG = {2147483658L: WIN32_REPARSE_TAG_DFS,
 2147483666L: WIN32_REPARSE_TAG_DFSR,
 3221225476L: WIN32_REPARSE_TAG_HSM,
 2684354563L: WIN32_REPARSE_TAG_MOUNT_POINT,
 1: WIN32_REPARSE_TAG_RESERVED_ONE,
 1: WIN32_REPARSE_TAG_RESERVED_RANGE,
 0: WIN32_REPARSE_TAG_RESERVED_ZERO,
 2147483655L: WIN32_REPARSE_TAG_SIS,
 2684354572L: WIN32_REPARSE_TAG_SYMLINK}
CTYPES_INVALID_HANDLE_VALUE = HANDLE(INVALID_HANDLE_VALUE).value

class _DirectoryEntry(object):
    __slots__ = ['name',
     'size',
     'mtime',
     'win32_reparse_type',
     'win32_file_attributes']

    def __init__(self, file_name, size, mtime, win32_reparse_type, win32_file_attributes):
        self.name = file_name
        self.size = size
        self.mtime = mtime
        self.win32_reparse_type = win32_reparse_type
        self.win32_file_attributes = win32_file_attributes

    @property
    def type(self):
        if self.win32_file_attributes & FILE_ATTRIBUTE_DIRECTORY:
            return FILE_TYPE_DIRECTORY
        return FILE_TYPE_REGULAR

    def __repr__(self):
        return '_DirectoryEntry(%r, %r, %r, %r, %r)' % (self.name,
         self.size,
         self.mtime,
         self.win32_reparse_type,
         self.win32_file_attributes)


class Directory(_DirectoryAbstract):

    def __repr__(self):
        return easy_repr(self, 'path', 'search_handle', 'file_data', 'first_file')

    def __init__(self, path, **kw):
        assert type(path) is unicode
        self.path = path
        self.file_data = WIN32_FIND_DATAW()
        search_string = os.path.join(path, u'*.*')
        self.first_file = True
        self.search_handle = FindFirstFileExW(search_string, FindExInfoBasic if WINDOWS_VERSION >= WIN7 else FindExInfoStandard, ctypes.byref(self.file_data), FindExSearchNameMatch, None, FIND_FIRST_EX_LARGE_FETCH if WINDOWS_VERSION >= WIN7 else 0)
        if self.search_handle == CTYPES_INVALID_HANDLE_VALUE:
            err = GetLastError()
            self.search_handle = None
            if err == ERROR_FILE_NOT_FOUND or err == ERROR_PATH_NOT_FOUND:
                self.first_file = None
            else:
                raise Exception('FindFirstFileExW(%r, ..) --> %d' % (search_string, err))

    def close(self):
        if self.search_handle:
            if not FindClose(self.search_handle):
                raise Exception('FindClose() --> %r' % (GetLastError(),))
            self.search_handle = None

    def reset(self):
        self.close()
        self.__init__(self.path)

    def debug_trace_path_info(self):
        try:
            exists = os.path.exists(self.path)
            TRACE('!! exists=%r' % (exists,))
        except Exception:
            unhandled_exc_handler()
            TRACE("!! couldn't check exists for %r" % (self.path,))

        try:
            contents = os.listdir(self.path)
            TRACE('!! contents=%r' % (contents,))
        except Exception:
            unhandled_exc_handler()
            TRACE("!! couldn't check contents for %r" % (self.path,))

        try:
            the_stat = os.stat(self.path)
            TRACE('!! the_stat=%r' % (the_stat,))
        except Exception:
            unhandled_exc_handler()
            TRACE("!! couldn't check the_stat for %r" % (self.path,))

        try:
            attrib = win32file.GetFileAttributesW(self.path)
            TRACE('!! attrib=%r' % (attrib,))
        except Exception:
            unhandled_exc_handler()
            TRACE("!! couldn't check attrib for %r" % (self.path,))

    def one_entry(self):
        if not FindNextFileW(self.search_handle, ctypes.byref(self.file_data)):
            err = GetLastError()
            if err != ERROR_NO_MORE_FILES:
                self.debug_trace_path_info()
                raise Exception('FindNextFileW(%r, %r) --> %d' % (self.search_handle, self.file_data, err))
            self.first_file = None
            return False
        return True

    def file_time_to_unix_time(self, file_time):
        win_time = file_time.dwHighDateTime << 32 | file_time.dwLowDateTime
        return (win_time - 116444736000000000L) / 10000000.0

    def readdir(self):
        if self.first_file is None:
            return
        if self.first_file == False:
            if not self.one_entry():
                return
        else:
            self.first_file = False
        while self.file_data.cFileName in (u'.', u'..'):
            if not self.one_entry():
                return

        reparse_type = None
        if self.file_data.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT != 0:
            tag = self.file_data.dwReserved0
            if tag in GET_TAG:
                reparse_type = GET_TAG[tag]
        return _DirectoryEntry(self.file_data.cFileName, self.file_data.nFileSizeHigh << 32 | self.file_data.nFileSizeLow, self.file_time_to_unix_time(self.file_data.ftLastWriteTime), reparse_type, self.file_data.dwFileAttributes)
