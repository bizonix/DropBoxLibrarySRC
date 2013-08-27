#Embedded file name: dropbox/file_cache/exceptions.py


class _ReallyBadDatabaseError(Exception):
    pass


class FileJournalEntryDoesNotExist(Exception):
    pass


class NamespaceNotMountedError(Exception):
    pass


class InvalidDatabaseError(Exception):
    pass
