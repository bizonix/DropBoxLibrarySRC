#Embedded file name: dropbox/sync_engine/posix_attrs_wrapper.py
import errno
import itertools
import os
import stat
from dropbox import fsutil
from dropbox.low_functions import add_inner_methods, add_inner_properties
from dropbox.misc import protect_closed
from dropbox.sync_engine_file_system.abstract_attributes_handle import AbstractAttributesHandle, AbstractPlatformHandle
from dropbox.sync_engine_file_system.abstract_file_system import AbstractFile
from dropbox.sync_engine_file_system.constants import SEEK_CUR, SEEK_END, SEEK_SET
from dropbox.sync_engine_file_system.util import WrappedFileSystem
from dropbox.trace import WARNING
_POSIX_ATTR_PLAT = 'posix'
_EXECUTABLE_ATTR_KEY = 'executable'

def posix_file_is_executable(fs, path):
    ia = fs.indexing_attributes(path)
    return not stat.S_ISDIR(ia.posix_mode) and fsutil.posix_verify_file_perms(fs, path, 'exec', st=ia)


def posix_file_set_executable(fs, path, is_executable):
    ia = fs.indexing_attributes(path)
    mode = stat.S_IMODE(ia.posix_mode)
    if not is_executable:
        mode &= -74
    else:
        assert (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) >> 2 == stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH, "If this fails it means that stat.S_IRUSR doesn't bitshift correctly. That would mean the constants changed which would mean the POSIX spec changed."
        mode |= (mode & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)) >> 2
        if hasattr(os, 'geteuid') and ia.posix_uid == os.geteuid():
            mode |= stat.S_IXUSR
        elif hasattr(os, 'getgroups') and ia.posix_gid in os.getgroups():
            mode |= stat.S_IXGRP
        else:
            mode |= stat.S_IXOTH
    fs.posix_chmod(path, mode)


def executable_attribute_file_system(fs):
    if 'posix' in fs.supported_attributes():
        return fs
    if not fs.supports_extension('posix'):
        return fs
    if not (hasattr(os, 'geteuid') and hasattr(os, 'getgroups')):
        msg = ' OS does not have both the geteuid() and getgroups()\nfunctions... posix executable attribute will be degraded\n'
        WARNING(msg)
    return PosixAttrFS(fs)


class PosixAttrFS(WrappedFileSystem):

    def __init__(self, fs):
        assert 'posix' not in fs.supported_attributes()
        assert fs.supports_extension('posix')
        super(PosixAttrFS, self).__init__(fs)

    def supported_attributes(self, path = None):
        toret = list(self.fs.supported_attributes(path))
        toret.append(_POSIX_ATTR_PLAT)
        return toret

    def open_attributes(self, path):
        return PosixAttrAttributesHandle(self.fs, path, self.fs.open_attributes(path))


@add_inner_methods('open_preserved', 'remove_preserved', 'close')

@add_inner_properties('closed')

class PosixAttrAttributesHandle(AbstractAttributesHandle):

    def __init__(self, fs, path, inner):
        self.fs = fs
        self.path = path
        self.inner = inner
        self.reset()

    @protect_closed
    def open(self, plat):
        if plat == _POSIX_ATTR_PLAT:
            return PosixAttrPlatformHandle(self.fs, self.path)
        return self.inner.open(plat)

    @protect_closed
    def readplat(self):
        try:
            return next(self.curiter)
        except StopIteration:
            return None

    @protect_closed
    def remove(self, plat, key):
        if plat == _POSIX_ATTR_PLAT:
            if key != _EXECUTABLE_ATTR_KEY:
                raise IOError(errno.ENOENT)
            else:
                posix_file_set_executable(self.fs, self.path, False)
                return
        return self.inner.remove(plat, key)

    @protect_closed
    def reset(self):
        self.curiter = itertools.chain(self.inner, [_POSIX_ATTR_PLAT])


class PosixAttrPlatformHandle(AbstractPlatformHandle):

    def __init__(self, fs, path):
        self.fs = fs
        self.path = path
        self._closed = False
        self.reset()

    @property
    def closed(self):
        return self._closed

    @property
    def name(self):
        return _POSIX_ATTR_PLAT

    def close(self):
        self._closed = True

    @protect_closed
    def readattr(self):
        try:
            return next(self.curiter)
        except StopIteration:
            return None

    @protect_closed
    def open(self, key, mode = 'r'):
        if key != _EXECUTABLE_ATTR_KEY:
            raise IOError(errno.ENOENT, 'Key Not supported: %r' % key)
        return _ExecutableFile(self.fs, self.path)

    @protect_closed
    def reset(self):
        to_iter = []
        if posix_file_is_executable(self.fs, self.path):
            to_iter.append('executable')
        self.curiter = iter(to_iter)


class _ExecutableFile(AbstractFile):

    def __init__(self, fs, path):
        self.fs = fs
        self.path = path
        self.offset = 0
        self._closed = False

    @property
    def closed(self):
        return self._closed

    @property
    def name(self):
        return _EXECUTABLE_ATTR_KEY

    def close(self):
        self._closed = True

    @protect_closed
    def tell(self):
        return self.offset

    @protect_closed
    def read(self, amt = None):
        if self.offset >= 1:
            return ''
        toret = '1' if posix_file_is_executable(self.fs, self.path) else '0'
        self.offset += len(toret)
        return toret

    @protect_closed
    def write(self, data):
        if self.offset >= 1:
            return
        posix_file_set_executable(self.fs, self.path, data.startswith('1'))

    @protect_closed
    def seek(self, offset, whence = None):
        if whence is None:
            whence = SEEK_SET
        if whence == SEEK_CUR:
            self.offset += offset
        elif whence == SEEK_END:
            self.offset = 1 + offset
        elif whence == SEEK_SET:
            self.offset = offset
        else:
            raise IOError(errno.EINVAL, os.strerror(errno.EINVAL))
