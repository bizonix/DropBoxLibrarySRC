#Embedded file name: ui/common/status.py
from __future__ import absolute_import
from dropbox.functions import snippet
from dropbox.file_cache.constants import RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE, RECONSTRUCT_LOW_DISK_SPACE_CODE, RECONSTRUCT_PERMISSION_DENIED_CODE, RECONSTRUCT_READ_ONLY_FS_CODE, RECONSTRUCT_UNKNOWN_CODE, UPLOAD_INVALID_PATH_CODE, UPLOAD_QUOTA_CODE
from dropbox.sync_engine.constants import HASH_ACCESS, HASH_BUSY
from dropbox.trace import unhandled_exc_handler
from ui.common.strings import UIStrings, DONT_TRANSLATE

class StatusStrings(UIStrings):
    _strings = dict(connecting=u'Connecting...', initializing=u'Starting...', pausing=u'Pausing...', moving=u'Moving Dropbox...', importing=u'Importing photos...', paused=(u'Syncing paused', 'abbreviation, meaning, syncing is currently paused. SHORT'), waiting_for_link=u'Waiting to be linked to a Dropbox account...', low_disk_space=u"Can't sync (not enough free disk space)", updating=u'Upgrading Dropbox...', cant_mount_dropbox=u"Can't access Dropbox folder", ssl_error=u"Can't establish secure internet connection", reindexing=u'Indexing...', listing=u'Downloading file list...', migrating=u'Upgrading database...', starting=u'Starting...', selsync=u'Applying selective sync settings...', uploading=u'Uploading', downloading=u'Downloading', indexing=u'Indexing', nil=u'Up to date', cant_sync_file=u'Can\'t sync "%(file)s"', cant_sync_access_denied=u'Can\'t sync "%(file)s" (access denied)', cant_sync_busy=u'Can\'t sync "%(file)s" (file is in use)', cant_sync_dir_not_empty=u'Can\'t sync "%(file)s" (this directory isn\'t empty)', cant_sync_low_disk=u'Can\'t sync "%(file)s" (low disk space)', cant_sync_permission_denied=u'Can\'t sync "%(file)s" (permission denied)', cant_sync_quota=u'Can\'t sync "%(file)s" (your Dropbox is out of space)', cant_sync_rejected_by_server=u'Can\'t sync "%(file)s"', cant_sync_ROFS=u'Can\'t sync "%(file)s" (your file system is read-only)', cant_sync_unknown=u'Can\'t sync "%(file)s"')
    _platform_overrides = dict(mac=dict(uploading=(u'\u25b2', DONT_TRANSLATE), downloading=(u'\u25bc', DONT_TRANSLATE), importing=u'Importing photos...'))


def format_failure_label(filename, reason):
    FAILURE_LABELS = {HASH_ACCESS: StatusStrings.cant_sync_access_denied,
     HASH_BUSY: StatusStrings.cant_sync_busy,
     RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE: StatusStrings.cant_sync_dir_not_empty,
     RECONSTRUCT_LOW_DISK_SPACE_CODE: StatusStrings.cant_sync_low_disk,
     RECONSTRUCT_PERMISSION_DENIED_CODE: StatusStrings.cant_sync_permission_denied,
     RECONSTRUCT_READ_ONLY_FS_CODE: StatusStrings.cant_sync_ROFS,
     RECONSTRUCT_UNKNOWN_CODE: StatusStrings.cant_sync_unknown,
     UPLOAD_INVALID_PATH_CODE: StatusStrings.cant_sync_rejected_by_server,
     UPLOAD_QUOTA_CODE: StatusStrings.cant_sync_quota}
    if not reason:
        template = StatusStrings.cant_sync_file
    else:
        try:
            template = FAILURE_LABELS[reason]
        except KeyError:
            unhandled_exc_handler()
            template = StatusStrings.cant_sync_unknown

    return template % {'file': snippet(filename)}
