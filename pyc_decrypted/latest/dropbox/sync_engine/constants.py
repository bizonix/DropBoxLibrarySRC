#Embedded file name: dropbox/sync_engine/constants.py
HASH_ACCESS = 'access'
HASH_BUSY = 'busy'
HASH_DELETED = 'deleted'
HASH_DROP = 'drop'
HASH_SUCCESS = 'success'
HASH_UNKNOWN = 'unknown'

class FileSyncStatus(object):
    UNWATCHED = 0
    UP_TO_DATE = 1
    SYNCING = 2
    UNSYNCABLE = 3
    SELECTIVE_SYNC = 4
