#Embedded file name: dropbox/sync_engine_file_system/pythonos.py
from __future__ import absolute_import
from __future__ import with_statement
import errno
import os
import time
from dropbox.functions import is_case_insensitive_path
from dropbox.low_functions import add_inner_methods, add_inner_properties
from .abstract_file_system import AbstractFile, AbstractFileSystem
from .util import convert_os_error_dec, convert_errno_to_ioerror, mode_map

@add_inner_methods('close', 'flush', 'read', 'seek', 'tell', 'truncate', 'write')

@add_inner_properties('closed')

class PythonFile(AbstractFile):

    def __init__(self, f):
        self.inner = f

    def sync(self):
        self.flush()
        with convert_errno_to_ioerror():
            os.fsync(self.inner.fileno())


class FileSystem(AbstractFileSystem):

    def __init__(self, make_path):
        self._make_path = make_path

    def make_path(self, *n, **kw):
        return self._make_path(*n, **kw)

    def is_case_insensitive_directory(self, path):
        return is_case_insensitive_path(unicode(path))

    @convert_os_error_dec
    def mkdir(self, path):
        os.mkdir(unicode(path))

    @convert_os_error_dec
    def rmdir(self, path):
        os.rmdir(unicode(path))

    @convert_os_error_dec
    def open(self, path, mode = 'r', **kw):
        if mode not in mode_map:
            raise ValueError('Opening file %r with an invalid mode (%r)' % (path, mode))
        return PythonFile(open(unicode(path), mode=mode + 'b'))

    def supported_attributes(self, path = None):
        return ()

    def supports_extension(self, ext):
        return os.name == 'posix' and ext == 'posix' or os.name in ('posix', 'nt') and ext == 'fdopen'

    @convert_os_error_dec
    def fdopen(self, *n):
        return PythonFile(os.fdopen(*n))

    @convert_os_error_dec
    def posix_symlink(self, symdata_, path):
        return os.symlink(symdata_, unicode(path))

    @convert_os_error_dec
    def posix_readlink(self, path):
        return os.readlink(unicode(path))

    @convert_os_error_dec
    def posix_chmod(self, path, mode):
        return os.chmod(unicode(path), mode)

    @convert_os_error_dec
    def get_disk_free_space(self, path):
        st = os.statvfs(unicode(path))
        return st.f_bavail * st.f_frsize

    @convert_os_error_dec
    def remove(self, path):
        return os.remove(unicode(path))

    @convert_os_error_dec
    def rename(self, src, dst):
        _dst = unicode(dst)
        _src = unicode(src)
        try:
            return os.rename(_src, _dst)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(_dst)
                os.rename(_src, _dst)
            else:
                raise

    def realpath(self, path):
        return self.make_path(os.path.realpath(unicode(path)))

    @convert_os_error_dec
    def set_file_mtime(self, path, mtime):
        os.utime(unicode(path), (time.time(), mtime))

    @convert_os_error_dec
    def unlink(self, path):
        os.unlink(unicode(path))

    def splitext(self, path):
        return os.path.splitext(unicode(path))
