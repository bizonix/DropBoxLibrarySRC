#Embedded file name: dropbox/dirtraverse_posix.py
from __future__ import absolute_import
import ctypes
import sys
import itertools
import os
import errno
import functools
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR, FILE_TYPE_POSIX_BLOCK_DEVICE, FILE_TYPE_POSIX_CHARACTER_DEVICE, FILE_TYPE_POSIX_FIFO, FILE_TYPE_POSIX_SYMLINK, FILE_TYPE_POSIX_SOCKET
from dropbox.trace import unhandled_exc_handler
from dropbox.debugging import easy_repr
from dropbox.dirtraverse_common import _DirectoryAbstract
_is_linux = sys.platform.startswith('linux')

class _DirectoryEntry(object):
    __slots__ = ('file_id', 'name', 'type')

    def __init__(self, name, inode, _type = None):
        self.name = name
        self.file_id = inode
        if _type is not None:
            self.type = _type

    def __repr__(self):
        return easy_repr(self, 'name', 'file_id', 'type')


_libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))

class Dirent(ctypes.Structure):
    if _is_linux:
        _fields_ = (('d_ino', ctypes.c_ulong),
         ('d_off', ctypes.c_long),
         ('d_reclen', ctypes.c_ushort),
         ('d_type', ctypes.c_ubyte),
         ('d_name', ctypes.c_char * 256))
    else:
        _fields_ = (('d_ino', ctypes.c_uint32),
         ('d_reclen', ctypes.c_uint16),
         ('d_type', ctypes.c_uint8),
         ('d_namlen', ctypes.c_uint8),
         ('d_name', ctypes.c_char * 256))


DIR_p = ctypes.c_void_p
Dirent_p = ctypes.POINTER(Dirent)
Dirent_pp = ctypes.POINTER(Dirent_p)
_native_to_logical = {1: FILE_TYPE_POSIX_FIFO,
 2: FILE_TYPE_POSIX_CHARACTER_DEVICE,
 4: FILE_TYPE_DIRECTORY,
 6: FILE_TYPE_POSIX_BLOCK_DEVICE,
 8: FILE_TYPE_REGULAR,
 10: FILE_TYPE_POSIX_SYMLINK,
 12: FILE_TYPE_POSIX_SOCKET}
for func_name, restype, argtypes in itertools.chain((('opendir', DIR_p, (ctypes.c_char_p,)),
 ('readdir_r', ctypes.c_int, (DIR_p, Dirent_p, Dirent_pp)),
 ('closedir', ctypes.c_int, (DIR_p,)),
 ('rewinddir', ctypes.c_int, (DIR_p,))), (('fdopendir', DIR_p, (ctypes.c_int,)),) if _is_linux else ()):
    try:
        func = ctypes.CFUNCTYPE(restype, use_errno=True, *argtypes)((func_name, _libc))
        setattr(_libc, func_name, func)
    except Exception:
        unhandled_exc_handler()

if _is_linux and not hasattr(os, 'O_NOATIME'):
    os.O_NOATIME = 262144

class Directory(_DirectoryAbstract):
    __slots__ = ('dirp', 'my_dirent', 'my_dirent_p', 'arg_is_unicode', 'path')

    def __init__(self, path, no_atime = False, **kw):
        arg_is_unicode = isinstance(path, unicode)
        if _is_linux and no_atime:
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOCTTY | os.O_NOATIME)
            except OSError as e:
                if e.errno == errno.EPERM:
                    fd = os.open(path, os.O_RDONLY | os.O_NOCTTY)
                else:
                    raise

            self.dirp = _libc.fdopendir(fd)
            if not self.dirp:
                try:
                    os.close(fd)
                except OSError:
                    unhandled_exc_handler()

                e = ctypes.get_errno()
                raise OSError(e, os.strerror(e), path)
        else:
            self.dirp = _libc.opendir(path.encode(sys.getfilesystemencoding()) if arg_is_unicode else path)
            if not self.dirp:
                e = ctypes.get_errno()
                raise OSError(e, os.strerror(e), path)
        self.path = path
        self.my_dirent = Dirent()
        self.my_dirent_p = Dirent_p()
        self.arg_is_unicode = arg_is_unicode
        self.reset = functools.partial(_libc.rewinddir, self.dirp)

    def close(self):
        try:
            dirp = self.dirp
        except AttributeError:
            pass
        else:
            if dirp:
                ret = _libc.closedir(dirp)
                if ret < 0:
                    e = ctypes.get_errno()
                    raise OSError(e, os.strerror(e))
                self.dirp = None

    def readdir(self):
        while True:
            ret = _libc.readdir_r(self.dirp, ctypes.byref(self.my_dirent), ctypes.byref(self.my_dirent_p))
            if ret > 0:
                raise OSError(ret, os.strerror(ret))
            if not self.my_dirent_p:
                return None
            name = self.my_dirent.d_name
            if name == '.' or name == '..':
                continue
            if self.arg_is_unicode:
                try:
                    name = name.decode(sys.getfilesystemencoding())
                except UnicodeDecodeError:
                    pass

            return _DirectoryEntry(name, self.my_dirent.d_ino, _native_to_logical.get(self.my_dirent.d_type))
