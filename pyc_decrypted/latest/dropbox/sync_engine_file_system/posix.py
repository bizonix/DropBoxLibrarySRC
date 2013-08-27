#Embedded file name: dropbox/sync_engine_file_system/posix.py
from dropbox import fsutil
from .posix_indexing_attributes_mixin import PosixIndexingAttributesMixin
from .pythonos import FileSystem

class PosixFileSystem(PosixIndexingAttributesMixin, FileSystem):

    def is_normal_file(self, path):
        return fsutil.posix_is_normal_file(self, path)
