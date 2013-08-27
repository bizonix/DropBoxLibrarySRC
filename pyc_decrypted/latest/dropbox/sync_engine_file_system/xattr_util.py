#Embedded file name: dropbox/sync_engine_file_system/xattr_util.py
from __future__ import with_statement, absolute_import
import errno
import os
from dropbox.misc import protect_closed
from dropbox.xattrs import XAttrFile, xattr
from .abstract_attributes_handle import AbstractAttributesHandle, AbstractPlatformHandle
from .util import convert_errno_to_ioerror, convert_os_error
from .exceptions import create_io_error

class _PlatformHandle(AbstractPlatformHandle):

    def __init__(self, xattr, plat):
        with convert_errno_to_ioerror():
            self.xattr = xattr.dup()
        self.platform = plat
        self.reset()

    @property
    def name(self):
        return self.platform

    @protect_closed
    def reset(self):
        self.curiter = iter(self.xattr)

    @protect_closed
    def open(self, key, mode = 'r'):
        with convert_errno_to_ioerror():
            fd = os.dup(self.xattr.fileno())
            return XAttrFile(fd, key, mode)

    @protect_closed
    def close(self):
        self.xattr.close()

    @property
    def closed(self):
        return self.xattr.closed

    @protect_closed
    def readattr(self):
        try:
            return self.curiter.next()
        except StopIteration:
            return None


class XAttrAttributesHandle(AbstractAttributesHandle):

    def __init__(self, path, plat, preserved_name):
        with convert_os_error():
            self._xattr = xattr.from_path(unicode(path))
        self._supported_plats = (plat,)
        self.preserved_name = preserved_name
        self.reset()

    @property
    def closed(self):
        return self._xattr.closed

    @protect_closed
    def reset(self):
        self.curiter = iter(self._supported_plats)

    @protect_closed
    def readplat(self):
        try:
            return self.curiter.next()
        except StopIteration:
            return None

    @protect_closed
    def open(self, plat):
        if plat != self._supported_plats[0]:
            raise create_io_error(errno.ENOENT, filename=plat)
        return _PlatformHandle(self._xattr, plat)

    @protect_closed
    def open_preserved(self, mode = 'r'):
        try:
            with convert_errno_to_ioerror():
                fd = os.dup(self._xattr.fileno())
                return XAttrFile(fd, self.preserved_name, mode)
        except IOError as e:
            if e.errno == errno.ENOTSUP:
                raise IOError(errno.ENOENT, 'Preserved attributes not found')
            raise

    @protect_closed
    def remove(self, plat, key):
        if plat != self._supported_plats[0]:
            raise create_io_error(errno.ENOENT, filename=plat)
        with convert_errno_to_ioerror():
            self._xattr.remove(key)

    @protect_closed
    def remove_preserved(self, raise_if_not_found = False):
        try:
            with convert_errno_to_ioerror():
                del self._xattr[self.preserved_name]
        except KeyError:
            if raise_if_not_found:
                raise
        except IOError as e:
            if e.errno == errno.ENOTSUP:
                if raise_if_not_found:
                    raise create_io_error(errno.ENOENT, 'Preserved attributes not found', filename=self.preserved_name)
            else:
                raise

    def close(self):
        self._xattr.close()


def path_supports_xattrs(path, test = 'user.myxattr'):
    x = xattr.from_path(unicode(path))
    try:
        x[test]
    except KeyError:
        pass
    except OSError as e:
        if e.errno == errno.EOPNOTSUPP:
            return False
        raise

    return True
