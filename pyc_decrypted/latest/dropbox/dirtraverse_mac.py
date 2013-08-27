#Embedded file name: dropbox/dirtraverse_mac.py
from __future__ import with_statement, absolute_import
import ctypes
import errno
import os
import sys
from dropbox.dirtraverse_common import _DirectoryAbstract, DirectoryModifiedError
from dropbox.debugging import ReprStructure, easy_repr
from dropbox.dirtraverse_posix import Directory as DirectoryPosix, _libc
from dropbox.mac.version import MAC_VERSION, TIGER
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR, FILE_TYPE_POSIX_BLOCK_DEVICE, FILE_TYPE_POSIX_CHARACTER_DEVICE, FILE_TYPE_POSIX_FIFO, FILE_TYPE_POSIX_SYMLINK, FILE_TYPE_POSIX_SOCKET
from dropbox.trace import unhandled_exc_handler

class Attrlist(ReprStructure):
    _fields_ = (('bitmapcount', ctypes.c_ushort),
     ('reserved', ctypes.c_uint16),
     ('commonattr', ctypes.c_uint32),
     ('volattr', ctypes.c_uint32),
     ('dirattr', ctypes.c_uint32),
     ('fileattr', ctypes.c_uint32),
     ('forkattr', ctypes.c_uint32))


Attrlist_p = ctypes.POINTER(Attrlist)

class Timespec(ReprStructure):
    _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]


for func_name, restype, argtypes in (('getdirentriesattr', ctypes.c_int, (ctypes.c_int,
   Attrlist_p,
   ctypes.c_void_p,
   ctypes.c_size_t,
   ctypes.POINTER(ctypes.c_long),
   ctypes.POINTER(ctypes.c_long),
   ctypes.POINTER(ctypes.c_long),
   ctypes.c_ulong)), ('getattrlist', ctypes.c_int, (ctypes.c_char_p,
   Attrlist_p,
   ctypes.c_void_p,
   ctypes.c_size_t,
   ctypes.c_ulong))):
    try:
        func = ctypes.CFUNCTYPE(restype, use_errno=True, *argtypes)((func_name, _libc))
        setattr(_libc, func_name, func)
    except Exception:
        unhandled_exc_handler()

_mac_native_to_logical = {1: FILE_TYPE_REGULAR,
 2: FILE_TYPE_DIRECTORY,
 3: FILE_TYPE_POSIX_BLOCK_DEVICE,
 4: FILE_TYPE_POSIX_CHARACTER_DEVICE,
 5: FILE_TYPE_POSIX_SYMLINK,
 6: FILE_TYPE_POSIX_SOCKET,
 7: FILE_TYPE_POSIX_FIFO}
ATTR_BIT_MAP_COUNT = 5
ATTR_CMN_NAME = 1
ATTR_CMN_OBJTYPE = 8
ATTR_CMN_OBJID = 32
ATTR_CMN_MODTIME = 1024
ATTR_CMN_CHGTIME = 2048
ATTR_FILE_LINKCOUNT = 1
ATTR_FILE_TOTALSIZE = 2
ATTR_FILE_ALLOCSIZE = 4
ATTR_FILE_DATALENGTH = 512
ATTR_VOL_INFO = 2147483648L
ATTR_VOL_CAPABILITIES = 131072
ATTR_VOL_ATTRIBUTES = 1073741824
VOL_CAPABILITIES_INTERFACES = 1
VOL_CAP_INT_READDIRATTR = 8
off_t = ctypes.c_int64

class FInfoAttrBuf(ReprStructure):
    _fields_ = (('length', ctypes.c_uint32),
     ('name_offset', ctypes.c_int32),
     ('name_length', ctypes.c_uint32),
     ('ftype', ctypes.c_uint32),
     ('objno', ctypes.c_uint32),
     ('generation', ctypes.c_uint32),
     ('mtime', Timespec),
     ('ctime', Timespec),
     ('size', off_t))


class VolCapabilitiesAttr(ReprStructure):
    _fields_ = (('capabilities', ctypes.c_uint32 * 4), ('valid', ctypes.c_uint32 * 4))


class AttributeSet(ReprStructure):
    _fields_ = (('commonattr', ctypes.c_uint32),
     ('volattr', ctypes.c_uint32),
     ('dirattr', ctypes.c_uint32),
     ('fileattr', ctypes.c_uint32),
     ('forkattr', ctypes.c_uint32))


class VolAttributesAttr(ReprStructure):
    _fields_ = (('validattr', AttributeSet), ('nativeattr', AttributeSet))


class DirectoryMacNotSupported(Exception):
    pass


class _DirectoryEntry(object):

    def __init__(self, name, type_, size, mtime, inode, ctime):
        self.name = name
        if type_ is not None:
            self.type = type_
        if size is not None:
            self.size = size
        self.mtime = mtime
        self.file_id = inode
        self.ctime = ctime

    def __repr__(self):
        return easy_repr(self, 'name', 'type', 'size', 'mtime', 'file_id', 'ctime')


BUF_SIZE = 16384
PER_CALL = BUF_SIZE / (ctypes.sizeof(FInfoAttrBuf) + 256)

class DirectoryMac(_DirectoryAbstract):

    def __init__(self, path, no_atime = False, **kw):
        self.dirfd = os.open(path, os.O_RDONLY)
        self.arg_is_unicode = isinstance(path, unicode)
        self.path = path
        self.attr_list = Attrlist()
        self.attr_list.bitmapcount = ATTR_BIT_MAP_COUNT
        self.attr_list.commonattr = ATTR_CMN_NAME | ATTR_CMN_OBJTYPE | ATTR_CMN_OBJID | ATTR_CMN_MODTIME | ATTR_CMN_CHGTIME
        self.attr_list.fileattr = ATTR_FILE_DATALENGTH
        self.attr_buf = ctypes.create_string_buffer(BUF_SIZE)
        self.junk = ctypes.c_long()
        self.state = ctypes.c_long()
        self.count = ctypes.c_long()
        self.state_valid = False
        self._getdirentries()
        self._next = self.lowiter().next

    def _getdirentries(self):
        old_state = self.state.value
        self.count.value = PER_CALL
        self.err = _libc.getdirentriesattr(self.dirfd, ctypes.byref(self.attr_list), self.attr_buf, len(self.attr_buf), ctypes.byref(self.count), ctypes.byref(self.junk), ctypes.byref(self.state), 0)
        if self.err < 0:
            e = ctypes.get_errno()
            if e == errno.ENOTSUP:
                raise DirectoryMacNotSupported()
            raise OSError(e, os.strerror(e))
        if self.state_valid and old_state != self.state.value:

            def _raise():
                raise DirectoryModifiedError()

            self._next = _raise
            _raise()
        self.state_valid = True

    def reset(self):
        os.lseek(self.dirfd, 0, 0)
        self.state_valid = False
        self._getdirentries()
        self._next = self.lowiter().next

    def readdir(self):
        try:
            return self.next()
        except StopIteration:
            return None

    def next(self):
        return self._next()

    def lowiter(self):
        while self.err >= 0:
            cur = ctypes.addressof(self.attr_buf)
            this_entry = FInfoAttrBuf.from_address(cur)
            for i in xrange(self.count.value):
                if self.dirfd is None:
                    raise Exception('closed!')
                name = ctypes.string_at(cur + this_entry.name_offset + 4, this_entry.name_length - 1)
                if self.arg_is_unicode:
                    try:
                        name = name.decode(sys.getfilesystemencoding())
                    except UnicodeDecodeError:
                        pass

                t = _mac_native_to_logical.get(this_entry.ftype)
                yield _DirectoryEntry(name, t, this_entry.size if t == FILE_TYPE_REGULAR else None, this_entry.mtime.tv_sec, this_entry.objno, this_entry.ctime.tv_sec)
                cur += this_entry.length
                this_entry = FInfoAttrBuf.from_address(cur)

            if self.err == 1:
                break
            self._getdirentries()

    def close(self):
        try:
            dirfd = self.dirfd
        except AttributeError:
            pass
        else:
            if dirfd is not None:
                os.close(dirfd)
                self.dirfd = None


if MAC_VERSION <= TIGER:
    Directory = DirectoryPosix
else:

    def Directory(*n, **kw):
        try:
            return DirectoryMac(*n, **kw)
        except DirectoryMacNotSupported:
            return DirectoryPosix(*n, **kw)
