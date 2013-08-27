#Embedded file name: dropbox/sync_engine/exceptions.py


class ReconstructError(Exception):
    pass


class ReconstructCodeError(ReconstructError):

    def __init__(self, code):
        self.code = code


class UnreconstructableError(ReconstructError):
    pass


class PredictableError(ReconstructError):
    pass


class CustomPermissionError(ReconstructError):
    pass


class NoParentFolderError(ReconstructError):
    pass


class BusyFileError(ReconstructError):
    pass


class ShortcutFileError(ReconstructError):
    pass


class BadLocalDetailsError(ReconstructError):

    def __init__(self, local_path, server_path, l_mtime, l_size, l_isdir, l_machine_guid, st_mtime, st_size, st_isdir, st_machine_guid):
        self.local_path = local_path
        self.str = 'Expected different local file details, %r:%r (mtime=%r,size=%r,isdir=%r,machine_guid=%r) vs statted (mtime=%r,size=%r,isdir=%r,machine_guid=%r)' % (local_path,
         server_path,
         l_mtime,
         l_size,
         l_isdir,
         l_machine_guid,
         st_mtime,
         st_size,
         st_isdir,
         st_machine_guid)

    def __str__(self):
        return self.str

    def __repr__(self):
        return self.str


class NoLocalDetailsError(BadLocalDetailsError):

    def __init__(self, local_path, server_path, l_mtime, l_size):
        self.local_path = local_path
        self.str = 'Expected local file details but SyncEngine had no record %r:%r, filesystem mtime:size %r:%r' % (local_path,
         server_path,
         l_mtime,
         l_size)

    def __str__(self):
        return self.str


class UnmountedPathError(Exception):
    pass
