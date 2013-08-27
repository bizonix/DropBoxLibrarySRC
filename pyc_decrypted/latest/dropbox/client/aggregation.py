#Embedded file name: dropbox/client/aggregation.py
import json
import os
import threading
import time
from itertools import islice
from dropbox.client.multiaccount.controller import MergedController
from dropbox.debugging import easy_repr
from dropbox.functions import handle_exceptions
from dropbox.path import ServerPath
from dropbox.sqlite3_helpers import VersionedSqlite3Cache, locked_and_handled
from dropbox.sync_engine.reconstruct import mute_attr_set
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from ui.common.aggregation import RecentlyChangedFile

class FileAggregationDatabase(VersionedSqlite3Cache):
    _USER_VERSION = 2
    _KEY_RECENT = 'recent'

    def __init__(self, app, filename, **kwargs):
        self.app = app
        self.tables = ['snapshot']
        self.migrations = [self.migrate_0_to_2, self.migrate_1_to_2]
        self.should_import = False
        super(FileAggregationDatabase, self).__init__(filename, **kwargs)

    def migrate_0_to_2(self, cursor):
        TRACE('%s: Migrating 0->2', self.__class__.__name__)
        cursor.execute('CREATE TABLE snapshot(key TEXT PRIMARY KEY NOT NULL,value BLOB NOT NULL)')
        cursor.execute('PRAGMA user_version = 2')
        self.should_import = True

    def migrate_1_to_2(self, cursor):
        TRACE('%s: Migrating 1->2', self.__class__.__name__)
        _old_key = 'recent'
        try:
            item = cursor.execute('SELECT value FROM snapshot WHERE key=?', (_old_key,)).fetchone()
            if item is None:
                cursor.execute('PRAGMA user_version = 2')
                return
            entries = []
            for server_path, timestamp in json.loads(item[0]):
                entries.append({'server_path': server_path,
                 'timestamp': timestamp,
                 'blocklist': None})

            cursor.execute('INSERT OR REPLACE INTO snapshot (key, value) VALUES (?, ?)', (self._KEY_RECENT, json.dumps(entries)))
        except Exception:
            unhandled_exc_handler()
            TRACE('!! Failed to recover snapshot data, dropping entries.')
            cursor.execute('DELETE FROM snapshot')

        cursor.execute('PRAGMA user_version = 2')

    @locked_and_handled()
    def save_recent_snapshot(self, snapshot):
        snapshot_dump = json.dumps(snapshot)
        with self.connhub.cursor() as cursor:
            cursor.execute('INSERT OR REPLACE INTO snapshot (key, value) VALUES (?, ?)', (self._KEY_RECENT, snapshot_dump))

    @locked_and_handled()
    def get_recent_snapshot(self):
        with self.connhub.cursor() as cursor:
            item = cursor.execute('SELECT value FROM snapshot WHERE key=?', (self._KEY_RECENT,)).fetchone()
            if item is None:
                return
            return json.loads(item[0])


class RecentlyChangedAggregator(object):
    TIMELINE_SIZE = 3
    TIMELINE_CACHE_SIZE = 15

    def __repr__(self):
        return easy_repr(self, '_timeline')

    def __init__(self, app, path):
        self._app = app
        self._timeline = {}
        self._sync_engine = None
        self._lock = threading.Lock()
        self._loaded = False
        database_path = os.path.join(path, 'aggregation.dbx')
        self._db = FileAggregationDatabase(self._app, database_path)
        TRACE('Initialized %r.', self)

    def set_sync_engine(self, sync_engine):
        self._sync_engine = sync_engine
        if not self._loaded:
            self._load_timeline()
        self._sync_engine.add_synced_files_callback(self._handle_synced_files)

    @handle_exceptions
    def _import_recently_changed_config(self):
        TRACE('Importing recently changed files from config...')
        now = time.time()
        recently_changed = self._app.config.get('recently_changed3')
        if not recently_changed:
            return
        changed = False
        for path, is_dir in reversed(recently_changed):
            try:
                server_path = ServerPath(path)
                local_path = unicode(self._sync_engine.server_to_local(server_path))
                try:
                    timestamp = os.stat(local_path).st_mtime
                except OSError:
                    timestamp = now

                if is_dir is None:
                    is_delete = True
                    is_dir = False
                else:
                    is_delete = False
                    is_dir = bool(is_dir)
                self._create_entry(server_path, timestamp, is_dir=is_dir, is_delete=is_delete)
                changed = True
            except Exception:
                unhandled_exc_handler(False)
                continue

        if changed:
            self._save_timeline()

    @handle_exceptions
    def _load_timeline(self):
        TRACE('Loading recently changed timeline...')
        self._loaded = True
        if self._db.should_import:
            self._import_recently_changed_config()
            return
        snapshot = self._db.get_recent_snapshot()
        if snapshot is None:
            TRACE('No recently changed entries found!')
            return
        for entry in snapshot:
            self._create_entry(ServerPath(entry['server_path']), entry['timestamp'], blocklist=entry['blocklist'])

    @handle_exceptions
    def _save_timeline(self):
        TRACE('Saving recently changed timeline ...')
        serialized = [ {'server_path': unicode(entry.server_path),
         'timestamp': entry.timestamp,
         'blocklist': entry.blocklist} for entry in self._timeline.itervalues() ]
        self._db.save_recent_snapshot(serialized)

    @handle_exceptions
    def _create_entry(self, server_path, timestamp, attrs = None, blocklist = None, is_dir = False, is_delete = False):
        if is_dir:
            return
        if attrs is not None and mute_attr_set(attrs):
            return
        timeline_key = unicode(server_path.lower())
        if is_delete:
            if timeline_key in self._timeline:
                del self._timeline[timeline_key]
            return
        entry = RecentlyChangedFile(server_path, timestamp, blocklist)
        self._timeline[timeline_key] = entry
        if len(self._timeline) > self.TIMELINE_CACHE_SIZE:
            entries_to_delete = sorted(self._timeline.iteritems(), key=lambda (k, v): v.timestamp, reverse=True)
            entries_to_delete = entries_to_delete[self.TIMELINE_CACHE_SIZE:]
            for k, _ in entries_to_delete:
                del self._timeline[k]

    @handle_exceptions
    def _handle_synced_files(self, synced_files):
        if not self._loaded:
            return
        now = time.time()
        with self._lock:
            for details in synced_files:
                timestamp = getattr(details, 'ts', None)
                timestamp = timestamp if timestamp is not None else now
                self._create_entry(details.server_path, timestamp, attrs=details.attrs, blocklist=details.blocklist, is_dir=details.dir, is_delete=details.size < 0)

            if synced_files:
                self._save_timeline()

    def get_latest(self, count = TIMELINE_SIZE):
        generate = sorted(self._timeline.itervalues(), key=lambda v: v.timestamp, reverse=True)
        return list(islice(generate, count))


class MultiaccountRecentlyChanged(MergedController):
    TIMELINE_SIZE = 4

    def __init__(self, app):
        super(MultiaccountRecentlyChanged, self).__init__(app)
        if not app.recently_changed:
            report_bad_assumption('Multiaccount aggregator initialized without primary')
        self.primary = app.recently_changed
        self.secondary = app.mbox.recently_changed

    def get_latest(self, count = None):
        if self.show_primary and self.show_secondary:
            count = count or self.TIMELINE_SIZE
        else:
            count = count or self.primary.TIMELINE_SIZE
        changes = self.tag_and_merge(primary_method=self.primary.get_latest, secondary_method=self.secondary.get_latest, count=count)
        sorted_changes = sorted(changes, key=lambda v: v.timestamp, reverse=True)
        return sorted_changes[:count]
