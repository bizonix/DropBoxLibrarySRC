#Embedded file name: dropbox/sync_engine_file_system/abstract_attributes_handle.py
from dropbox.low_functions import Closeable

class AbstractAttributesHandle(Closeable):

    def close(self):
        raise NotImplementedError()

    @property
    def closed(self):
        raise NotImplementedError()

    def open(self, plat):
        raise NotImplementedError()

    def open_preserved(self, mode = 'r'):
        raise NotImplementedError()

    def readplat(self):
        raise NotImplementedError()

    def remove(self, plat, key):
        raise NotImplementedError()

    def remove_preserved(self, raise_if_not_found = False):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        toret = self.readplat()
        if toret is None:
            raise StopIteration()
        return toret


class AbstractPlatformHandle(Closeable):

    def close(self):
        raise NotImplementedError()

    @property
    def closed(self):
        raise NotImplementedError()

    @property
    def name(self):
        raise NotImplementedError()

    def open(self, key, mode = 'r'):
        raise NotImplementedError()

    def readattr(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        toret = self.readattr()
        if toret is None:
            raise StopIteration()
        return toret
