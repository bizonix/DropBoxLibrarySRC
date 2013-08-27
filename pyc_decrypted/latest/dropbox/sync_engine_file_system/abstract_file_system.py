#Embedded file name: dropbox/sync_engine_file_system/abstract_file_system.py
from dropbox.misc import LineReaderMixin
from dropbox.low_functions import Closeable

class AbstractDirectory(Closeable):

    def readdir(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        toret = self.readdir()
        if toret is None:
            raise StopIteration()
        return toret


class AbstractFile(Closeable, LineReaderMixin):

    def close(self):
        raise NotImplementedError()

    @property
    def closed(self):
        raise NotImplementedError()

    def flush(self):
        raise NotImplementedError()

    def read(self, size = None):
        raise NotImplementedError()

    def seek(self, offset, whence = 0):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()

    def tell(self):
        raise NotImplementedError()

    def truncate(self):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()

    def datasync(self):
        return self.sync()


class AbstractFileSystem(Closeable):

    def indexing_attributes(self, path, resolve_link = True, write_machine_guid = False):
        raise NotImplementedError()

    def make_path(self, string_path):
        raise NotImplementedError()

    def mkdir(self, path):
        raise NotImplementedError()

    def open(self, path, mode = 'r', **kw):
        raise NotImplementedError()

    def open_attributes(self, path):
        raise NotImplementedError()

    def opendir(self, path, **kw):
        raise NotImplementedError()

    def realpath(self, path):
        raise NotImplementedError()

    def remove(self, path):
        raise NotImplementedError()

    def rename(self, src, dst):
        raise NotImplementedError()

    def rmdir(self, path):
        raise NotImplementedError()

    def set_file_mtime(self, path, modification_time):
        raise NotImplementedError()

    def get_disk_free_space(self, path):
        raise NotImplementedError()

    def supported_attributes(self, path = None):
        raise NotImplementedError()

    def supports_extension(self, ext_name):
        raise NotImplementedError()
