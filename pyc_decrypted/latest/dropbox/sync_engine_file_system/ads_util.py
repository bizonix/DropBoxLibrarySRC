#Embedded file name: dropbox/sync_engine_file_system/ads_util.py
import errno
from dropbox.misc import protect_closed
from .abstract_attributes_handle import AbstractAttributesHandle
from .exceptions import create_io_error
from .util import convert_errno_to_ioerror
_DROPBOX_ATTR_STREAM = 'com.dropbox.attributes'

class XAttrAttributesHandleWin(AbstractAttributesHandle):

    def __init__(self, fs, path):
        self.fs = fs
        self.path = path
        self._closed = False

    @property
    def closed(self):
        return self._closed

    def close(self):
        self._closed = True

    @protect_closed
    def open(self, plat):
        raise create_io_error(errno.ENOENT, filename=plat)

    def _preserved_fname(self):
        return '%s:%s' % (unicode(self.path), _DROPBOX_ATTR_STREAM)

    @protect_closed
    def open_preserved(self, mode = 'r'):
        try:
            with convert_errno_to_ioerror():
                return self.fs.open(self._preserved_fname(), mode)
        except IOError as e:
            if e.errno == errno.EINVAL:
                raise create_io_error(errno.ENOENT, 'Preserved attributes not found', self._preserved_fname())
            raise

    @protect_closed
    def readplat(self):
        return None

    @protect_closed
    def remove_preserved(self):
        try:
            with convert_errno_to_ioerror():
                return self.fs.remove(self._preserved_fname())
        except IOError as e:
            if e.errno == errno.EINVAL:
                raise create_io_error(errno.ENOENT, 'Preserved attributes not found', self._preserved_fname())
            raise

    @protect_closed
    def reset(self):
        pass
