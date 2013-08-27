#Embedded file name: dropbox/xattrs.py
from __future__ import with_statement, absolute_import
import errno
import os
import sys
from UserDict import DictMixin
from ctypes import create_string_buffer
from dropbox.functions import safe_str
from dropbox.low_functions import Closeable, add_inner_methods, add_inner_properties
from dropbox.misc import protect_closed
from dropbox.sync_engine_file_system.util import CAN_READ, CAN_WRITE, convert_errno_to_ioerror
from dropbox.xattrs_posix import c_fgetxattr, fsetxattr, flistxattr, fremovexattr, ENOATTR_LIST

def _fgetxattr_high(callable):
    for i in xrange(100):
        try:
            size = callable(None, 0)
            p = create_string_buffer(size)
            ret = callable(p, size)
        except OSError as e:
            if e.errno == errno.ERANGE:
                continue
            raise
        else:
            toret = p.raw
            if len(toret) == ret:
                return toret
            return toret[:ret]

    else:
        raise OSError(errno.ERANGE, os.strerror(errno.ERANGE))


def _fgetxattr_high_linux(fd, item):

    def callable(buf, len):
        return c_fgetxattr(fd, item, buf, len, 0, 0)

    return _fgetxattr_high(callable)


class xattr(object, DictMixin):

    def __init__(self, fd):
        self.fd = fd

    @classmethod
    def from_path(cls, path):
        return cls(os.open(path, os.O_RDONLY))

    @protect_closed
    def fileno(self):
        return self.fd

    def dup(self):
        return type(self)(os.dup(self.fileno()))

    @protect_closed
    def __getitem__(self, item):
        try:
            return _fgetxattr_high_linux(self.fd, item)
        except OSError as e:
            if e.errno in ENOATTR_LIST:
                raise KeyError(item)
            raise

    @protect_closed
    def __setitem__(self, item, value):
        item = safe_str(item)
        fsetxattr(self.fd, item, value, 0)

    def __delitem__(self, item):
        item = safe_str(item)
        try:
            self.remove(item)
        except OSError as e:
            if e.errno in ENOATTR_LIST:
                raise KeyError(item)
            raise

    @protect_closed
    def keys(self):
        return flistxattr(self.fd)

    @protect_closed
    def remove(self, item):
        fremovexattr(self.fileno(), item)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    @property
    def closed(self):
        return self.fd is None

    def __del__(self):
        self.close()


def _fgetxattr_high_linux_str(fd, item):
    try:
        with convert_errno_to_ioerror():
            return _fgetxattr_high_linux(fd, item)
    except IOError as e:
        if e.errno in ENOATTR_LIST:
            return ''
        raise


class _XAttrFileLinux(Closeable):

    def __init__(self, fd, item, mode):
        try:
            if mode[-1] == 'b':
                mode = mode[:-1]
            self.fd = None
            self.can_read = CAN_READ[mode]
            self.can_write = CAN_WRITE[mode]
            self.item = item
            self.offset = 0
            if mode[0] == 'a':
                raise NotImplementedError()
            if mode[0] == 'r':
                try:
                    _fgetxattr_high_linux(fd, item)
                except OSError as e:
                    if e.errno in ENOATTR_LIST:
                        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), item)
                    else:
                        raise

            if mode[0] == 'w':
                try:
                    fsetxattr(fd, self.item, '', 0)
                except OSError as e:
                    if e.errno not in (errno.ERANGE, errno.EINVAL):
                        raise

        except:
            os.close(fd)
            raise

        self.fd = fd

    @protect_closed
    def read(self, amt = None):
        if not self.can_read:
            raise IOError(errno.EBADF, os.strerror(errno.EBADF))
        ret = _fgetxattr_high_linux_str(self.fd, self.item)
        toret = ret[self.offset:] if amt is None else ret[self.offset:self.offset + amt]
        self.offset += len(toret)
        return toret

    @protect_closed
    def tell(self):
        return self.offset

    @protect_closed
    def write(self, data):
        if not self.can_write:
            raise IOError(errno.EBADF, os.strerror(errno.EBADF))
        ret = _fgetxattr_high_linux_str(self.fd, self.item)
        if len(ret) < self.offset:
            ret = '%s%s' % (ret, '\x00' * (self.offset - len(ret)))
        ret = ''.join([ret if len(ret) == self.offset else ret[:self.offset], data, ret[self.offset + len(data):]])
        with convert_errno_to_ioerror():
            fsetxattr(self.fd, self.item, ret, 0)
        self.offset += len(data)

    @protect_closed
    def seek(self, where, whence = os.SEEK_SET):
        if whence == os.SEEK_END:
            self.read()
            self.offset += where
        elif whence == os.SEEK_SET:
            self.offset = where
        else:
            raise NotImplementedError()

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    @property
    def name(self):
        return self.item

    @property
    def closed(self):
        return self.fd is None

    def __del__(self):
        self.close()


@add_inner_methods('write', 'seek', 'tell', 'close', inner_name='linux_xattr')

@add_inner_properties('name', 'closed', inner_name='linux_xattr')

class _XAttrFileMac(Closeable):

    def __init__(self, fd, item, mode):
        self.fd = fd
        self.item = item
        self.can_read = CAN_READ[mode]
        self.linux_xattr = _XAttrFileLinux(fd, item, mode)

    def read(self, amt = None):
        if self.item == 'com.apple.ResourceFork':
            if not self.can_read:
                raise IOError(errno.EBADF, os.strerror(errno.EBADF))
            offset = self.linux_xattr.tell()
            try:
                with convert_errno_to_ioerror():
                    if amt is None:

                        def _callable(buf, len):
                            return c_fgetxattr(self.fd, self.item, buf, len, offset, 0)

                        toret = _fgetxattr_high(_callable)
                    else:
                        was_there = c_fgetxattr(self.fd, self.item, None, 0, offset, 0)
                        if was_there < amt:
                            amt = was_there
                        b = create_string_buffer(amt)
                        was_there = c_fgetxattr(self.fd, self.item, b, amt, offset, 0)
                        toret = b.raw
                        if amt != was_there:
                            toret = toret[:was_there]
            except IOError as e:
                if e.errno in ENOATTR_LIST:
                    toret = ''
                else:
                    raise

            self.linux_xattr.seek(len(toret) + offset)
            return toret
        else:
            return self.linux_xattr.read(amt)


if sys.platform.startswith('linux'):
    XAttrFile = _XAttrFileLinux
elif sys.platform.startswith('darwin'):
    XAttrFile = _XAttrFileMac
