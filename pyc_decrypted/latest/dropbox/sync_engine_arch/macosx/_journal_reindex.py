#Embedded file name: dropbox/sync_engine_arch/macosx/_journal_reindex.py
import datetime
import json
import os
import time
from pymac.constants import kCFAllocatorDefault, kFSEventStreamCreateFlagWatchRoot, kFSEventStreamEventFlagEventIdsWrapped, kFSEventStreamEventFlagHistoryDone, kFSEventStreamEventFlagKernelDropped, kFSEventStreamEventFlagMustScanSubDirs, kFSEventStreamEventFlagItemIsDir, kFSEventStreamEventFlagItemIsSymlink, kFSEventStreamEventFlagRootChanged, kFSEventStreamEventFlagMount
from pymac.dlls import FSEvent, Core
from pymac.helpers.core import releasing, python_to_property
from pymac.helpers.fsevents import fsevent_uuid_for_path
from pymac.types import FSEventStreamCallback
from dropbox.fastwalk_bridge import fastwalk_with_exception_handling
from dropbox.sync_engine_file_system.constants import FILE_TYPE_POSIX_SYMLINK
from dropbox.mac.version import MAC_VERSION, TIGER
from dropbox.trace import TRACE, unhandled_exc_handler

class JournalFailure(Exception):
    pass


def path_has_symlink_mount(path):
    walker = fastwalk_with_exception_handling(path, follow_symlinks=False)
    for dirpath, ents in walker:
        if os.path.ismount(dirpath):
            TRACE('Found mount point %r', dirpath)
            return True
        for dirent in ents:
            if dirent.type == FILE_TYPE_POSIX_SYMLINK:
                return True

    return False


class JournalReindexer:

    def __init__(self, sync_engine, top_level, stats, path):
        self.stats = stats
        if MAC_VERSION <= TIGER:
            failure = 'Mac version too old'
            self._log_failure(failure)
            raise JournalFailure(failure)
        self.c_fsevents_callback = FSEventStreamCallback(self._fsevents_callback)
        self._changed_dirs = {}
        self.sync_engine = sync_engine
        self.top_level = top_level
        self.loop = None
        self.failed = False
        self.path = unicode(path)
        try:
            reindex_info = json.loads(sync_engine.get_config_key('reindex_info'))
        except KeyError:
            raise JournalFailure('No reindex info')

        reindex_date = datetime.datetime.fromtimestamp(reindex_info['last_reindex'])
        if datetime.datetime.now() - reindex_date > datetime.timedelta(days=15):
            raise JournalFailure('Reindex expired')
        total_dirs = reindex_info['num_dirs']
        self.max_dir_count = max(int(0.15 * total_dirs), 50)
        self.current_uuid = fsevent_uuid_for_path(self.path)
        if self.current_uuid is None:
            raise JournalFailure('No uuid available')
        try:
            saved_uuid = self._load_cursor()
            if saved_uuid != self.current_uuid:
                TRACE('UUID changed')
                raise KeyError
        except KeyError:
            latest_event = FSEvent.FSEventsGetCurrentEventId()

            def write_cursor():
                if not self.sync_engine.get_hash_count():
                    self.has_had_symlink_or_mount = path_has_symlink_mount(self.path)
                    self._store_cursor(latest_event)
                    TRACE('Initial cursor write')
                else:
                    TRACE('No file cursor written: unsyncable files')

            if self.sync_engine.check_if_initial_hash_is_done(callback=write_cursor):
                write_cursor()
            raise JournalFailure('No cursor and/or symlink data found')
        except Exception:
            unhandled_exc_handler()

    def _load_cursor(self):
        reindex_info = json.loads(self.sync_engine.get_config_key('reindex_cursor'))
        self.has_had_symlink_or_mount = reindex_info['has_had_symlink_or_mount']
        self.reindex_cursor = reindex_info['event_id']
        return reindex_info['uuid']

    def _store_cursor(self, event):
        json_string_cursor = json.dumps({'event_id': event,
         'uuid': self.current_uuid,
         'has_had_symlink_or_mount': self.has_had_symlink_or_mount})
        self.sync_engine.set_config_key('reindex_cursor', json_string_cursor)

    def can_journal(self, db_path):
        if self.has_had_symlink_or_mount:
            self._log_failure('symlink or mount')
            return False
        db_pathu = unicode(db_path)
        if db_pathu != os.path.realpath(db_pathu):
            self._log_failure('fake dropbox path')
            return False
        return True

    def _create_fsstream(self, path, event_id):
        TRACE('Creating stream with %r at event %d', path, event_id)
        with releasing(python_to_property([path])) as cfArray:
            fsstream = FSEvent.FSEventStreamCreate(kCFAllocatorDefault, self.c_fsevents_callback, None, cfArray, event_id, 0.1, kFSEventStreamCreateFlagWatchRoot)
            return fsstream

    def _stop_fsstream(self, fsstream):
        FSEvent.FSEventStreamStop(fsstream)
        FSEvent.FSEventStreamInvalidate(fsstream)
        FSEvent.FSEventStreamRelease(fsstream)
        Core.CFRunLoopStop(self.loop)

    def _history_done(self, event_id, fsstream):
        TRACE('Found changed directories: %r', self._changed_dirs)

        def write_cursor():
            if not self.sync_engine.get_hash_count():
                TRACE('Recording file system cursor')
                self._store_cursor(event_id)
            else:
                TRACE('No file cursor written: unhashable files')

        if self.sync_engine.check_if_initial_hash_is_done(callback=write_cursor):
            write_cursor()
        self._stop_fsstream(fsstream)

    def _log_failure(self, reason):
        if self.stats:
            self.stats['failed_reason'] = reason

    def start_reindex(self):
        fsstream = self._create_fsstream(self.path, self.reindex_cursor)
        self.loop = Core.CFRunLoopGetCurrent()
        FSEvent.FSEventStreamScheduleWithRunLoop(fsstream, self.loop, Core.kCFRunLoopDefaultMode)
        FSEvent.FSEventStreamStart(fsstream)
        TRACE('Journal starting at event %s', self.reindex_cursor)
        start_journal = time.time()
        Core.CFRunLoopRun()
        took = time.time() - start_journal
        TRACE('Journal ending with time %d', took)
        if self.stats:
            self.stats['journal_time'] = took
            self.stats['changed_dir_count'] = len(self._changed_dirs)
        if self.failed:
            raise JournalFailure(self.failed)
        return self._changed_dirs

    def reset(self):
        self.sync_engine.remove_config_key('reindex_cursor')

    def _manage_failure(self, fsstream, failure_warning):
        TRACE('Journaling failed during stream. Back to regular reindex')
        self.reset()
        self.failed = failure_warning
        self._log_failure(failure_warning)
        self._stop_fsstream(fsstream)
        raise JournalFailure(failure_warning)

    def _fsevents_callback(self, streamRef, info, numEvents, paths, eventFlags, eventId):
        try:
            events = ((paths[x].decode('utf-8'), eventFlags[x]) for x in xrange(numEvents))
            for path, flag in events:
                path = os.path.normpath(path)
                TRACE('Handling event for %r with flag %s', path, flag)
                if flag & kFSEventStreamEventFlagRootChanged:
                    TRACE('Dropbox folder path changed with flags %s', flag)
                    self._manage_failure(streamRef, 'Dropbox path modified')
                if flag & (kFSEventStreamEventFlagItemIsSymlink | kFSEventStreamEventFlagMount):
                    TRACE('Symlink or mount created')
                    self.has_had_symlink_or_mount = True
                elif flag & kFSEventStreamEventFlagItemIsDir:
                    if os.path.commonprefix([path, self.path]) != self.path:
                        TRACE('Dropbox folder path changed with flags %s', flag)
                        self._manage_failure(streamRef, 'Dropbox path modified')
                    elif path_has_symlink_mount(path):
                        TRACE('Symlink or mount added in')
                        self.has_had_symlink_or_mount = True
                if flag & kFSEventStreamEventFlagHistoryDone:
                    self._history_done(eventId.contents.value, streamRef)
                else:
                    path = os.path.normpath(path)
                    if path not in self._changed_dirs:
                        should_recurse = flag & kFSEventStreamEventFlagMustScanSubDirs
                        self._changed_dirs[path] = self._changed_dirs.get(path, False) or should_recurse
                        if len(self._changed_dirs) > self.max_dir_count:
                            self.failed = 'Greater than %d directories' % self.max_dir_count
                            self._manage_failure(streamRef, self.failed)
                    elif flag & kFSEventStreamEventFlagEventIdsWrapped:
                        self._manage_failure(streamRef, 'Event IDs wrapped')

        except JournalFailure:
            unhandled_exc_handler(False)
        except Exception:
            unhandled_exc_handler()
            self._manage_failure(streamRef, 'Unknown failure in stream')
