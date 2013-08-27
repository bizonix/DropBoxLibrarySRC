#Embedded file name: dropbox/file_cache/file_cache.py
import base64
import contextlib
import itertools
import operator
import pprint
import sqlite3
import sys
import threading
import time
import cPickle as pickle
from collections import defaultdict
from client_api.hashing import DROPBOX_HASH_LENGTH
from dropbox import sqlite3_helpers
from dropbox.attrs import Attributes, CorruptedAttributeError, FrozenAttributes, copy_file_tag_gid_v3, has_file_tag_gid_v3, unfreeze_attr_dict
from dropbox.callbacks import Handler
from dropbox.client_prof import SimpleTimer
from dropbox.fastdetails import FastDetails
from dropbox.functions import handle_exceptions_ex, to_signed_64_bit, to_unsigned_64_bit, frozendict, migrate_db_schema, migrate_db_get_table_entries, batch
from dropbox.low_functions import head, propagate_none
from dropbox.sqlite3_helpers import CorruptedDBError, sqlite3_get_table_entries, just_the_first, row_factory, sqlite_escape, dict_like_row
from dropbox.server_path import ServerPath, NsRelativePath, NsRelativePathFast, server_path_ns_rel_unicode, server_path_ns_unicode, server_path_rel_unicode, server_path_join_unicode, server_path_basename_unicode, server_path_dirname_unicode
from dropbox.trace import DEVELOPER_WARNING, TRACE, assert_, report_bad_assumption, unhandled_exc_handler
from .constants import EXTRA_PENDING_DETAILS_COL, IS_CONFLICTED_COL, IS_GUID_CONFLICTED_COL, LOCAL_ATTRS_COL, LOCAL_BLOCKLIST_COL, LOCAL_CTIME_COL, LOCAL_DIR_COL, LOCAL_FILENAME_COL, LOCAL_GUID_COL, LOCAL_MACHINE_GUID_COL, LOCAL_HOST_ID_COL, LOCAL_MTIME_COL, LOCAL_SIZE_COL, LOCAL_SJID_COL, LOCAL_TIMESTAMP_COL, LOCAL_GUID_SYNCED_GUID_REV_COL, MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT, PARENT_GUID_SYNCED_SJID_COL, PARENT_GUID_SYNCED_SERVER_PATH_COL, PARENT_PATH_COL, RECONSTRUCT_UNRECONSTRUCTABLE_CODE, RECONSTRUCT_SHORTCUT_CODE, RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE, RECONSTRUCT_SUCCESS_CODE, SERVER_PATH_COL, UPDATED_ATTRS_COL, UPDATED_BLOCKLIST_COL, UPDATED_DIR_COL, UPDATED_FILENAME_COL, UPDATED_GUID_COL, UPDATED_GUID_REV_COL, UPDATED_MTIME_COL, UPDATED_HOST_ID_COL, UPDATED_SIZE_COL, UPDATED_SJID_COL, UPDATED_TIMESTAMP_COL, UPLOAD_SUCCESS_CODE, UPLOAD_IGNORED_CODE, UPLOAD_CONFLICT_CODE, UPLOAD_DIRECTORY_NOT_EMPTY_CODE, UPLOAD_QUOTA_CODE, UPLOAD_NO_ACCESS_CODE, UPLOAD_GUID_CONFLICT_CODE, UNRECONSTRUCTABLE_COL
from .commit_holding import CommitHoldingLogic
from .directory_holding import DirectoryHoldingAddLogic, DirectoryHoldingDeleteLogic
from .exceptions import _ReallyBadDatabaseError, FileJournalEntryDoesNotExist, NamespaceNotMountedError
from .guid_holding import GUIDHoldingLogic
from .memory_caches import NamespaceMountTable
from .memory_cache_backend_wrapper import MemoryCacheBackendWrapper
from .sqlite_backend import SQLiteBackend, FileJournalRowLogic, _SQL_VARS, CONFIG_ATTRS_DATA_PLATS, CONFIG_ATTRS_WHITELIST, CONFIG_FILETYPE, CONFIG_SELECTIVE_SYNC_IGNORE_LIST, CONFIG_VERSION
from .types import ExtraPendingDetails
from .util import check_db_entries, is_valid_filejournal_entry, is_valid_sjid, local_details_from_entry, make_conflicted, server_hash_for_row, updated_details_from_entry, why_isnt_valid_filejournal_entry

def _FastDetails_factory_updated(cursor, ent):
    return FastDetails(blocklist=ent[0], mtime=ent[1], size=ent[2], dir=ent[3], attrs=ent[4], sjid=ent[5], server_path=ServerPath(ServerPath(ent[6], lowered=True), ent[7]), host_id=ent[8], ts=ent[9])


class DBMountTransitionQueuer(object):

    def __init__(self, file_cache):
        self.file_cache = file_cache
        self._pre_mount_remove_updated = []
        self._pre_mount_remove_pending = []
        self._to_add_pending = []
        self._to_add_updated = []
        self.to_add_pending = self._to_add_pending.append
        self.to_add_updated = self._to_add_updated.append

    def pre_mount_remove_updated(self, spl):
        self._pre_mount_remove_updated.append(spl)

    def pre_mount_remove_pending(self, spl):
        self._pre_mount_remove_pending.append(spl)

    def run_pre_mount(self, trans):
        trans.pattached.discard_batch(self._pre_mount_remove_pending)
        trans.uattached.discard_batch(self._pre_mount_remove_updated)
        trans.changed_pending.extend((a.lower() for a in self._pre_mount_remove_pending))
        trans.changed_updated.extend((a.lower() for a in self._pre_mount_remove_updated))

    def run_adds(self, trans):
        for q, attached, filter_, changedl in [(self._to_add_pending,
          trans.pattached,
          trans._upload_filter,
          trans.changed_pending), (self._to_add_updated,
          trans.uattached,
          trans._reconstruct_filter,
          trans.changed_updated)]:
            to_add = []
            to_discard = []
            for a in q:
                rf = filter_(a)
                if rf is not None:
                    to_add.append((a, rf))
                else:
                    to_discard.append(a.server_path)

            attached.add_batch(to_add)
            attached.discard_batch(to_discard)
            changedl.extend((a.server_path.lower() for a in q))

    def run_removes(self, trans = None):
        pass


class NoOpDBMountTransitionQueuer(object):

    def pre_mount_remove_updated(self, spl):
        pass

    def pre_mount_remove_pending(self, spl):
        pass

    def to_add_pending(self, details):
        pass

    def to_add_updated(self, details):
        pass


def change_target_ns_checksum(cursor, server_path, from_target_ns, to_target_ns):
    with row_factory(cursor, dict_like_row):
        row = cursor.execute('SELECT * FROM file_journal WHERE server_path = ?', (server_path,)).fetchone()
        if row:
            toxor = server_hash_for_row(row, target_ns=from_target_ns) ^ server_hash_for_row(row, target_ns=to_target_ns)
            ns = server_path_ns_unicode(server_path)
            new_checksum = toxor ^ to_unsigned_64_bit(cursor.execute('SELECT checksum FROM namespace_map WHERE ns = ?', (ns,)).fetchone()[0])
            cursor.execute('UPDATE namespace_map SET checksum = ? WHERE ns = ?', (to_signed_64_bit(new_checksum), ns))


class DatabaseMountLogic(object):

    def __init__(self, fc, root_ns, rel, unmount_ns, is_destructive, to_mount_ns, prune_in = ()):
        assert_(lambda : not (is_destructive and unmount_ns and to_mount_ns), "Can't remount destructively")
        self.root_ns = root_ns
        self.rel = rel
        self.unmount_ns = unmount_ns
        self.is_destructive = is_destructive
        self.to_mount_ns = to_mount_ns
        self.prune_in = prune_in
        self.fc = fc

    def details(self):
        return (self.root_ns,
         self.rel,
         self.unmount_ns,
         self.is_destructive,
         self.to_mount_ns)

    def execute_da_sql(self, trans, the_queuer):
        cursor = trans.sqlite_cursor()
        mount_point = (u'%d:%s' % (self.root_ns, self.rel)).lower()
        if self.unmount_ns and self.to_mount_ns:
            mount_from = u'%d:/' % (self.unmount_ns,)
            mount_to = u'%d:/' % (self.to_mount_ns,)
            TRACE('Performing remount transition: %r -> %r', mount_from, mount_to)
        elif self.unmount_ns:
            mount_from = u'%d:/' % (self.unmount_ns,)
            mount_to = u'%s/' % (mount_point,)
            TRACE('Performing %sunmount transition: %r -> %r', 'destructive ' if self.is_destructive else '', mount_from, mount_to)
        else:
            assert self.to_mount_ns
            mount_from = u'%s/' % (mount_point,)
            mount_to = u'%d:/' % (self.to_mount_ns,)
            TRACE('Performing mount transition: %r -> %r', mount_from, mount_to)
        if self.to_mount_ns:
            cursor.execute('INSERT INTO namespace_map (ns, last_sjid, checksum, extra) VALUES (?, -1, 0, NULL)', (self.to_mount_ns,))
        change_target_ns_checksum(cursor, mount_point, self.unmount_ns, self.to_mount_ns)
        toret = self.fc._db_mount_transition(trans, mount_from, mount_to, the_queuer, destructive=self.is_destructive, prune_in=self.prune_in)
        if self.to_mount_ns and self.unmount_ns:
            cursor.execute('UPDATE mount_table SET target_ns = ? WHERE server_path = ?', (self.to_mount_ns, mount_point))
        elif self.to_mount_ns:
            cursor.execute('INSERT INTO mount_table (server_path, target_ns) VALUES (?, ?)', (mount_point, self.to_mount_ns))
        else:
            cursor.execute('DELETE FROM mount_table WHERE server_path = ?', (mount_point,))
        if self.unmount_ns:
            cursor.execute('DELETE FROM namespace_map WHERE ns = ?', (self.unmount_ns,))
        return toret


class NamespaceMovedMountLogic(object):

    def __init__(self, fc, root_ns, moved_ns, old_mount_point, new_mount_point):
        self.root_ns = root_ns
        self.moved_ns = moved_ns
        self.old_mount_point = old_mount_point.lower()
        self.new_mount_point = new_mount_point.lower()
        self.fc = fc

    def details(self):
        return (self.root_ns,
         self.moved_ns,
         self.old_mount_point,
         self.new_mount_point)

    def execute_da_sql(self, trans, the_queuer):
        TRACE('Mount point %r has moved: %d:%r -> %d:%r', self.moved_ns, self.root_ns, self.old_mount_point, self.root_ns, self.new_mount_point)
        cursor = trans.sqlite_cursor()
        namespace_path = u'%d:/' % (self.moved_ns,)
        old_mount_point_path = u'%d:%s/' % (self.root_ns, self.old_mount_point)
        num_statements = self.fc._db_mount_transition(trans, namespace_path, old_mount_point_path, the_queuer, destructive=True)
        cursor.execute('DELETE FROM namespace_map WHERE ns = ?', (self.moved_ns,))
        cursor.execute('DELETE FROM mount_table WHERE server_path = ?', (old_mount_point_path[:-1],))
        num_statements += 2
        namespace_path = u'%d:/' % (self.moved_ns,)
        new_mount_point_path = u'%d:%s/' % (self.root_ns, self.new_mount_point)
        num_statements += self.fc._db_mount_transition(trans, new_mount_point_path, namespace_path, the_queuer)
        cursor.execute('REPLACE INTO namespace_map (ns, last_sjid, checksum, extra) VALUES (?,-1,0,NULL)', (self.moved_ns,))
        cursor.execute('INSERT INTO mount_table (server_path, target_ns) VALUES (?, ?)', (new_mount_point_path[:-1], self.moved_ns))
        change_target_ns_checksum(cursor, old_mount_point_path[:-1], self.moved_ns, None)
        change_target_ns_checksum(cursor, new_mount_point_path[:-1], None, self.moved_ns)
        return num_statements + 2


class CommitHoldingCompat(object):

    def __init__(self, trans):
        self.trans = trans

    def _wrap_iterator(self, it):
        for ent in it:
            if ent[LOCAL_SJID_COL] is None:
                continue
            yield local_details_from_entry(ent)

    def get_local_details(self, sp_iterable):
        return self._wrap_iterator(self.trans.get_entries(sp_iterable))

    def get_local_children(self, server_directory_path):
        return self._wrap_iterator(self.trans.get_local_children(server_directory_path))

    def get_holds(self, server_paths):
        return self.trans.get_holds(server_paths)

    def delete_from_held(self, sp_iterable):
        return self.trans.delete_from_held(sp_iterable)

    def add_to_held(self, details_iterable):
        return self.trans.add_to_held(details_iterable)

    def get_held_descendants(self, server_path):
        return self.trans.get_held_descendants(server_path)

    def add_guid_references(self, details, server_paths):
        return self.trans.add_guid_references(details, server_paths)

    def delete_guid_references(self, server_paths):
        return self.trans.delete_guid_references(server_paths)

    def get_backward_references(self, server_path):
        return self.trans.get_backward_references(server_path)

    def entries_by_local_dropbox_guid_batch(self, guids):
        return self.trans.entries_by_local_dropbox_guid_batch(guids)


class SelectiveSyncDeleteQueue(object):

    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
        self.closed = False

    def __iter__(self):
        self.cursor.execute('SELECT * FROM root_relative_to_delete ORDER BY length(path) DESC')
        return self.cursor

    def close(self):
        if not self.closed:
            self.cursor.close()
            self.conn.execute('DROP TABLE root_relative_to_delete')
            self.closed = True

    def __del__(self):
        try:
            self.close()
        except:
            unhandled_exc_handler()


class FileCache(object):
    VERSION = SQLiteBackend.VERSION
    FILETYPE = SQLiteBackend.FILETYPE

    def __init__(self, database_file, **kw):
        self.prevent_main_thread = False
        pending_database_path = kw.pop('pending_database_path', None)
        updated_database_path = kw.pop('updated_database_path', None)
        sqlite_backend = SQLiteBackend(self, database_file, **kw)
        try:
            backend = MemoryCacheBackendWrapper(pending_database_path, updated_database_path, self, sqlite_backend)
            sqlite_backend = None
            try:
                self.__low_init__(backend, {}, {})
                with self.write_lock() as trans:
                    self._load_db_state(trans, load_run_queues=False)
            except:
                backend.close()
                raise

        except:
            if sqlite_backend is not None:
                sqlite_backend.close()
            raise

    def __low_init__(self, backend, root_ns_to_mount_table, last_revision):
        self.backend = backend
        self.giant_lock = threading.RLock()
        self.lock_local = threading.local()
        self.root_ns_to_mount_table = root_ns_to_mount_table
        self.last_revision = last_revision
        self.connhub = self.backend.connhub
        self._setup_callbacks()

    @contextlib.contextmanager
    def write_lock(self):
        if self.prevent_main_thread and threading.current_thread().name == 'MainThread':
            DEVELOPER_WARNING("Don't grab file cache lock on the main thread!")
        with self.giant_lock:
            try:
                self.lock_local.write_count += 1
            except AttributeError:
                self.lock_local.write_count = 1

            try:
                if hasattr(self.lock_local, 'trans'):
                    if False:
                        DEVELOPER_WARNING("Recursively locking file cache... this currently works but don't do this, it makes file cache more complex and harder to maintain")
                    yield self.lock_local.trans
                else:
                    try:
                        with self.backend.transaction() as trans:
                            self.lock_local.trans = trans
                            yield self.lock_local.trans
                    finally:
                        try:
                            del self.lock_local.trans
                        except AttributeError:
                            pass

            finally:
                self.lock_local.write_count -= 1

    read_lock = write_lock

    @contextlib.contextmanager
    def _read_lock_cursor(self):
        with self.read_lock() as trans:
            yield trans.sqlite_cursor()

    def _is_write_locked(self):
        return getattr(self.lock_local, 'write_count', 0)

    _is_read_locked = _is_write_locked

    def _load_db_state(self, trans, load_run_queues = True):
        assert_(self._is_write_locked)
        self._load_root_nses(trans.sqlite_cursor())
        self._unicode_rr_set = trans.get_directory_ignore_set()
        if not isinstance(trans.get_attrs_whitelist(), dict):
            raise _ReallyBadDatabaseError('Bad attrs whitelist! %r', self.get_attrs_whitelist())
        if not isinstance(trans.get_attrs_data_plats(), list):
            raise _ReallyBadDatabaseError('Bad attrs data plats! %r', self.get_attrs_data_plats())
        if load_run_queues:
            raise Exception('Not supported')

    def __metaclass__(name, bases, dict_):

        def wrap_backend_method(method_name):

            def wrapped(self, *n, **kw):
                with self.write_lock() as trans:
                    return getattr(trans, method_name)(*n, **kw)

            wrapped.__name__ = method_name
            return wrapped

        for method in ['upload_ready_time',
         'reconstruct_ready_time',
         'get_upload_failures',
         'get_reconstruct_failures',
         'get_upload_failure_counts',
         'get_reconstruct_failure_counts',
         'get_uploadable',
         'get_reconstructable',
         'get_uploadable_count',
         'get_reconstructable_count',
         'get_upload_count',
         'get_reconstruct_count',
         'get_full_upload_counts',
         'get_full_reconstruct_counts',
         'is_uploading',
         'is_reconstructing',
         'is_reconstructable',
         'is_uploadable',
         'get_reconstructing',
         'get_uploading',
         'set_upload_active',
         'set_reconstruct_active',
         'add_upload_keymod_handler',
         'add_reconstruct_keymod_handler',
         'add_upload_retry_handler',
         'add_reconstruct_retry_handler',
         'reconstructing_status',
         'uploading_status',
         'upload_retry',
         'reconstruct_retry',
         'upload_clear_retry_map',
         '_only_for_testing_dequeue_upload',
         'add_upload_error_callback',
         'add_reconstruct_error_callback',
         '_add_uploadable',
         '_add_reconstructable']:
            assert method not in dict_
            dict_[method] = wrap_backend_method(method)

        return type(name, bases, dict_)

    def close(self):
        self.backend.close()

    @classmethod
    def create_database_connection(cls, database_file, **kw):
        return sqlite3_helpers.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES, **kw)

    def _setup_callbacks(self):
        self.block_reference_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_block_reference_callback = self.block_reference_callbacks.add_handler
        self.remove_block_reference_callback = self.block_reference_callbacks.remove_handler
        self.remote_files_event_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_remote_file_event_callback = self.remote_files_event_callbacks.add_handler
        self.remove_remote_file_event_callback = self.remote_files_event_callbacks.remove_handler
        self.mount_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_mount_callback = self.mount_callbacks.add_handler
        self.remove_mount_callback = self.mount_callbacks.remove_handler
        self.synced_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_synced_files_callback = self.synced_callbacks.add_handler
        self.remove_synced_files_callback = self.synced_callbacks.remove_handler
        self.changed_upload_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_upload_changed_callback = self.changed_upload_callbacks.add_handler
        self.changed_reconstruct_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_reconstruct_changed_callback = self.changed_reconstruct_callbacks.add_handler

    def get_conflicted(self):
        with self.read_lock() as trans:
            return trans.conflicted_get_active()

    def get_conflicted_count(self):
        with self.read_lock() as trans:
            return trans.conflicted_get_count()

    def is_conflicted(self, sp, lower = True):
        with self.read_lock() as trans:
            entries = list(trans.get_entries([sp], lower=lower))
            if not entries:
                return False
            ent, = entries
            is_conflicted = ent[IS_CONFLICTED_COL] or ent[IS_GUID_CONFLICTED_COL] and ent[LOCAL_GUID_COL] == ent[UPDATED_GUID_COL]
            if is_conflicted:
                return make_conflicted(ent)

    def get_upload_filename(self):
        with self.read_lock() as trans:
            try:
                p = trans.get_upload_only_file()
            except Exception:
                unhandled_exc_handler()
                return

            if p:
                return p.server_path.basename
            return

    def get_reconstruct_filename(self):
        with self.read_lock() as trans:
            try:
                p = trans.get_reconstruct_only_file()
            except Exception:
                unhandled_exc_handler()
                return

            if p:
                return p.server_path.basename
            return

    def get_queue_stats(self):
        with self.read_lock() as trans:
            upload_counts = trans.get_full_upload_counts()
            reconstruct_counts = trans.get_full_reconstruct_counts()
            return {'upload': {'total_count': sum(upload_counts),
                        'active_count': upload_counts[0],
                        'waiting_count': upload_counts[1],
                        'inactive_count': upload_counts[2],
                        'failure_counts': trans.get_upload_failure_counts(constructor=dict)},
             'reconstruct': {'total_count': sum(reconstruct_counts),
                             'active_count': reconstruct_counts[0],
                             'waiting_count': reconstruct_counts[1],
                             'inactive_count': reconstruct_counts[2],
                             'failure_counts': trans.get_reconstruct_failure_counts(constructor=dict)},
             'conflicted': {'total_count': trans.conflicted_get_count()}}

    def _ignore_set_should_ignore(self, rr_server_path):
        return self.__ignore_set_should_ignore_lc_uni(unicode(rr_server_path).lower())

    ignore_set_should_ignore = _ignore_set_should_ignore

    def __ignore_set_should_ignore_lc_uni(self, ul_rr_sp):
        return any((ul_rr_sp.startswith(ignored_path + u'/') or ul_rr_sp == ignored_path for ignored_path in self._unicode_rr_set))

    def get_version(self):
        with self.read_lock() as trans:
            return trans.get_version()

    def get_attrs_data_plats(self):
        with self.read_lock() as trans:
            return trans.get_attrs_data_plats()

    def get_attrs_whitelist(self):
        with self.read_lock() as trans:
            return trans.get_attrs_whitelist()

    def get_config_key(self, key):
        with self.read_lock() as trans:
            return trans.get_config_key(key)

    def set_config_key(self, key, value):
        with self.write_lock() as trans:
            trans.set_config_key(key, value)

    def remove_config_key(self, key):
        with self.write_lock() as trans:
            trans.remove_config_key(key)

    @classmethod
    def cls_set_config_key(cls, key, value, cursor):
        return SQLiteBackend.cls_set_config_key(key, value, cursor)

    @classmethod
    def cls_get_config_key(cls, key, cursor):
        return SQLiteBackend.cls_get_config_key(key, cursor)

    @classmethod
    def cls_get_version(cls, cursor = None, conn = None):
        if cursor is None:
            cursor = conn.cursor()
        return SQLiteBackend.cls_get_config_key(CONFIG_VERSION, cursor)

    def _import(self, new_curs, new_info_iter):
        num_imported_rows = 0
        mps = ()
        fjrl = FileJournalRowLogic(mps)
        for new_row in new_info_iter:
            why_bad_row = FileCache.why_isnt_valid_filejournal_entry(new_row)
            if why_bad_row:
                raise _ReallyBadDatabaseError('User has a bad row not importing database: %r' % (why_bad_row,))
            fjrl.insert_entry(new_row)
            if len(fjrl) == fjrl.RECOMMENDED_BATCH_SIZE:
                fjrl.execute_da_sql(new_curs)
                num_imported_rows += fjrl.RECOMMENDED_BATCH_SIZE
                fjrl = FileJournalRowLogic(mps)

        if fjrl:
            fjrl.execute_da_sql(new_curs)
            num_imported_rows += len(fjrl)
        return num_imported_rows

    @classmethod
    def _safe_decode_old_attrs(cls, attr_data):
        if not attr_data or attr_data == u'Vnt9CnAxCi4=' or attr_data == u'{}' or attr_data == u'Uyd7fScKcDAKLg==\n':
            return FrozenAttributes()
        try:
            return Attributes.unmarshal(attr_data)
        except:
            try:
                current = attr_data
                for i in xrange(10):
                    try:
                        current = pickle.loads(base64.decodestring(current))
                    except:
                        break

                else:
                    raise Exception('Decoded too many times!')

                return Attributes.unmarshal(current)
            except:
                unhandled_exc_handler()
                return FrozenAttributes()

    @classmethod
    def _convert_version_6_row(cls, old_row):
        new_row = None
        mount_at = None
        remote_mount = None
        if old_row['active_sjid'] and old_row['active_size'] >= 0:
            new_row = {SERVER_PATH_COL: old_row['server_path'],
             PARENT_PATH_COL: server_path_dirname_unicode(old_row['server_path']),
             EXTRA_PENDING_DETAILS_COL: None,
             LOCAL_SJID_COL: old_row['active_sjid'],
             LOCAL_BLOCKLIST_COL: str(old_row['active_blocklist']),
             LOCAL_SIZE_COL: old_row['active_size'],
             LOCAL_MTIME_COL: old_row['active_mtime'],
             LOCAL_DIR_COL: int(bool(old_row['active_dir'])),
             LOCAL_ATTRS_COL: cls._safe_decode_old_attrs(old_row['active_attrs']),
             LOCAL_FILENAME_COL: server_path_basename_unicode(old_row['active_server_path']),
             LOCAL_CTIME_COL: 0}
            FileJournalRowLogic.clear_updated_details(new_row)
            if old_row['active_dir'] < 0:
                mount_at = (old_row['server_path'], -old_row['active_dir'])
        if old_row['updated_sjid']:
            if old_row['updated_dir'] < 0:
                remote_mount = (3, -old_row['updated_dir'])
            elif old_row['updated_dir'] >= 0 and mount_at:
                remote_mount = (1 if old_row['updated_size'] < 0 else 2, mount_at[1])
            if not new_row:
                new_row = FileJournalRowLogic.new_ent(old_row['server_path'])
            new_row[UPDATED_BLOCKLIST_COL] = str(old_row['updated_blocklist'])
            for detail_name in ('sjid', 'size', 'mtime'):
                updated_name = 'updated_' + detail_name
                new_row[updated_name] = old_row[updated_name]

            new_row[UPDATED_DIR_COL] = 0 if old_row['updated_size'] < 0 or not old_row['updated_dir'] else 1
            new_row[UPDATED_ATTRS_COL] = cls._safe_decode_old_attrs(old_row['updated_attrs'])
            new_row[UPDATED_FILENAME_COL] = server_path_basename_unicode(old_row['updated_server_path'])
        if new_row:
            return (new_row, mount_at, remote_mount)

    @classmethod
    def _convert_version_3to5_row(cls, old_row):
        new_row = None
        mount_at = None
        remote_mount = None
        if old_row['active_sjid'] and old_row['active_size'] >= 0:
            sp = old_row['server_path'].lower()
            new_row = {SERVER_PATH_COL: sp,
             PARENT_PATH_COL: server_path_dirname_unicode(sp),
             EXTRA_PENDING_DETAILS_COL: None,
             LOCAL_SJID_COL: old_row['active_sjid'],
             LOCAL_BLOCKLIST_COL: str(old_row['active_blocklist']),
             LOCAL_SIZE_COL: old_row['active_size'],
             LOCAL_MTIME_COL: old_row['active_mtime'],
             LOCAL_DIR_COL: 1 if bool(old_row['active_dir']) else 0,
             LOCAL_ATTRS_COL: cls._safe_decode_old_attrs(old_row['active_attrs']),
             LOCAL_FILENAME_COL: server_path_basename_unicode(old_row['server_path']),
             LOCAL_CTIME_COL: 0}
            if new_row[LOCAL_ATTRS_COL]:
                for i, key in enumerate(FileJournalRowLogic.LOCAL_FILE_DETAIL_COLS):
                    new_row[FileJournalRowLogic.UPDATED_FILE_DETAIL_COLS[i]] = new_row[key]

                new_row[LOCAL_SJID_COL] = 1
                new_row[LOCAL_ATTRS_COL] = FrozenAttributes()
            else:
                for key in FileJournalRowLogic.UPDATED_FILE_DETAIL_COLS:
                    new_row[key] = None

            if old_row['active_dir'] < 0:
                mount_at = (old_row['server_path'], -old_row['active_dir'])
        if old_row['updated_sjid']:
            if old_row['updated_dir'] < 0:
                remote_mount = (3, -old_row['updated_dir'])
            elif old_row['updated_dir'] >= 0 and mount_at:
                remote_mount = (1 if old_row['updated_size'] < 0 else 2, mount_at[1])
            if old_row['updated_dir'] < 0:
                raise Exception("Can't import when updated_dir is a mount point right now")
            elif old_row['updated_dir'] >= 0 and mount_at:
                raise Exception("Can't import when updated_dir is an unmount and directory is locally mounted right now")
            if not new_row:
                sp = old_row['server_path'].lower()
                new_row = FileJournalRowLogic.new_ent(sp)
            new_row[UPDATED_BLOCKLIST_COL] = str(old_row['updated_blocklist'])
            for detail_name in ('sjid', 'size', 'mtime'):
                updated_name = 'updated_' + detail_name
                new_row[updated_name] = old_row[updated_name]

            new_row[UPDATED_DIR_COL] = 0 if old_row['updated_size'] < 0 else old_row['updated_dir']
            new_row[UPDATED_ATTRS_COL] = cls._safe_decode_old_attrs(old_row['updated_attrs'])
            new_row[UPDATED_FILENAME_COL] = server_path_basename_unicode(old_row['server_path'])
        if new_row:
            return (new_row, mount_at, remote_mount)

    @classmethod
    def connect_to_version_123_database(cls, database_file):
        return sqlite3_helpers.connect(database_file or ':memory:', detect_types=sqlite3.PARSE_DECLTYPES)

    @classmethod
    def import_from_filecache_2(cls, old_conn, data_plats, attrs_whitelist, server_conn = None):
        with SQLiteBackend.transaction_from_conn(old_conn) as trans:
            trans.create_tables(force=False)
            trans.set_config_key(CONFIG_ATTRS_DATA_PLATS, list(data_plats))
            trans.set_config_key(CONFIG_ATTRS_WHITELIST, dict(attrs_whitelist))
            trans.set_config_key(CONFIG_FILETYPE, FileCache.FILETYPE)
            trans.set_config_key(CONFIG_VERSION, FileCache.VERSION)
            trans._upgrade_4_to_5(server_conn)

    def import_from_filecache_1(self, old_conn, data_plats, fixup_small_attrs, attrs_whitelist, server_conn = None):
        old_curs = old_conn.cursor()

        def fix_attr_with_None_plats(attr):
            if 'posix' in data_plats and any(('blocklist' in v for k, v in attr.attr_dict.get('posix', frozendict()).iteritems() if k != 'executable')):
                data_plats2 = set(data_plats)
                data_plats2.remove('posix')
            else:
                data_plats2 = data_plats
            if all((plat_attrs is not None for plat_attrs in attr.attr_dict.itervalues())):
                return attr.copy(data_plats=data_plats2)
            new_attr_dict = dict(attr.attr_dict)
            for plat, plat_attrs in attr.attr_dict.iteritems():
                if plat_attrs is None:
                    del new_attr_dict[plat]

            return Attributes(attr_dict=new_attr_dict, data_plats=data_plats2)

        def is_bad_attr(attrs):
            try:
                return any((len(val.get('data', '')) > 340 for val in itertools.chain(*[ attrs.attr_dict.get(dp, frozendict()).itervalues() for dp in data_plats ])))
            except Exception:
                unhandled_exc_handler()
                return False

        def make_good_attr(attrs):
            try:
                attr_dict = unfreeze_attr_dict(attrs.attr_dict)
                for val in itertools.chain(*[ attr_dict.get(dp, frozendict()).itervalues() for dp in data_plats ]):
                    if len(val.get('data', '')) > 340:
                        val['data'] = val['data'][:340]

                return attrs.copy(attr_dict=attr_dict)
            except Exception:
                unhandled_exc_handler()
                return attrs

        def feed_into_import():
            old_curs.row_factory = dict_like_row
            for old_row in old_curs.execute('SELECT * FROM file_journal'):
                new_row = dict(old_row)
                extra = old_row[EXTRA_PENDING_DETAILS_COL]
                if extra:
                    if extra['parent_attrs'] is not None:
                        if extra['parent_blocklist'] is None:
                            raise _ReallyBadDatabaseError('User has a bad row not importing database: parent_attrs was not None but parent_blocklist was None')
                        if old_row[LOCAL_SJID_COL] >= 0:
                            raise _ReallyBadDatabaseError('User has a bad row not importing database: we had parent attrs but the sjid was 0')
                        pb = extra['parent_blocklist']
                        pa = fix_attr_with_None_plats(extra['parent_attrs'])
                        parent = {'sjid': -new_row[LOCAL_SJID_COL],
                         'dir': int(pb == '' and 'com.apple.ResourceFork' not in pa.attr_dict.get('mac', frozendict())),
                         'size': 0,
                         'blocklist': pb,
                         'attrs': pa}
                        new_row[LOCAL_SJID_COL] = 0
                    else:
                        if extra['parent_blocklist'] is not None:
                            raise _ReallyBadDatabaseError('User has a bad row not importing database: parent_attrs was None but parent_blocklist was not None')
                        if old_row[LOCAL_SJID_COL] != 0:
                            raise _ReallyBadDatabaseError('User has a bad row not importing database: no parent data yet local_sjid was != 0 ')
                        parent = None
                    new_row[EXTRA_PENDING_DETAILS_COL] = ExtraPendingDetails(mount_request=extra['mount_request'], parent=parent)
                if new_row[LOCAL_ATTRS_COL] is not None:
                    new_row[LOCAL_ATTRS_COL] = fix_attr_with_None_plats(new_row[LOCAL_ATTRS_COL])
                    if fixup_small_attrs and is_bad_attr(new_row[LOCAL_ATTRS_COL]):
                        new_row[LOCAL_ATTRS_COL] = make_good_attr(new_row[LOCAL_ATTRS_COL])
                        new_row[LOCAL_CTIME_COL] = 0
                yield new_row

        with self.write_lock() as trans:
            self.clear()
            try:
                curs = trans.sqlite_cursor()
                toret = self._import(curs, feed_into_import())
                old_curs.row_factory = None
                for ns, last_sjid in old_curs.execute('SELECT ns, last_sjid FROM last_revision'):
                    try:
                        curs.execute('INSERT INTO namespace_map (ns, last_sjid, checksum, extra) VALUES (?, ?, 0, NULL)', (ns, last_sjid))
                    except sqlite3.IntegrityError:
                        curs.execute('UPDATE namespace_map SET last_sjid = ? WHERE ns = ?', (last_sjid, ns))

                mt = old_curs.execute('SELECT server_path, target_ns FROM mount_table').fetchall()
                curs.executemany('INSERT INTO mount_table (server_path, target_ns) VALUES (?, ?)', mt)
                for sp, target_ns in mt:
                    change_target_ns_checksum(curs, sp, None, target_ns)

                self.cls_set_config_key(CONFIG_ATTRS_WHITELIST, dict(attrs_whitelist), curs)
                self.cls_set_config_key(CONFIG_ATTRS_DATA_PLATS, list(data_plats), curs)
                self._load_db_state(trans, load_run_queues=False)
                trans._upgrade_4_to_5(server_conn)
                return toret
            except:
                self.clear()
                raise

    def _old_schema_importer(self, iterator, converter, server_conn = None):
        remote_mounts = []
        batched_mount = []
        last_revision = {}

        def feed_into_import():
            for old_row in iterator:
                new_info = converter(old_row)
                if not new_info:
                    continue
                new_row, mount_at, remote_mount = new_info
                yield new_row
                ns = server_path_ns_unicode(new_row[SERVER_PATH_COL])
                if new_row[LOCAL_SJID_COL] is not None and new_row[LOCAL_SJID_COL] > 1 and last_revision.get(ns, -1) <= new_row[LOCAL_SJID_COL]:
                    last_revision[ns] = new_row[LOCAL_SJID_COL]
                if new_row[UPDATED_SJID_COL] is not None and last_revision.get(ns, -1) <= new_row[UPDATED_SJID_COL]:
                    last_revision[ns] = new_row[UPDATED_SJID_COL]
                if remote_mount:
                    remote_mounts.append((new_row, remote_mount))
                if mount_at:
                    batched_mount.append(mount_at)

        with self.write_lock() as trans:
            self.clear()
            try:
                curs = trans.sqlite_cursor()
                toret = self._import(curs, feed_into_import())
                if batched_mount:
                    curs.executemany('INSERT INTO mount_table (server_path, target_ns) VALUES (?, ?)', batched_mount)
                    for i in batched_mount:
                        change_target_ns_checksum(curs, i[0], None, i[1])
                        if i[1] not in last_revision:
                            last_revision[i[1]] = -1

                if last_revision:
                    for ns, last_sjid in last_revision.iteritems():
                        try:
                            curs.execute('INSERT INTO namespace_map (ns, last_sjid, checksum, extra) VALUES (?, ?, 0, NULL)', (ns, last_sjid))
                        except sqlite3.IntegrityError:
                            curs.execute('UPDATE namespace_map SET last_sjid = ? WHERE ns = ?', (last_sjid, ns))

                remote_mounts.sort(key=lambda x: x[0][UPDATED_SJID_COL])
                for new_row, remote_mount_info in remote_mounts:
                    kind, at_ns = remote_mount_info
                    root_ns, rel = server_path_ns_rel_unicode(new_row[SERVER_PATH_COL])
                    if kind in (1, 2):
                        ml = DatabaseMountLogic(self, root_ns, rel, at_ns, kind == 1, None)
                    elif kind == 3:
                        ml = DatabaseMountLogic(self, root_ns, rel, None, None, at_ns)
                    else:
                        assert False, 'Invalid mount kind!: %r' % (kind,)
                    ml.execute_da_sql(trans, NoOpDBMountTransitionQueuer())

                self._load_db_state(trans, load_run_queues=False)
                trans._upgrade_4_to_5(server_conn)
                return toret
            except:
                self.clear()
                raise

    def import_from_dropbox_db(self, old_conn, server_conn = None):
        old_curs = old_conn.cursor()
        old_curs.execute('select value from config where key = ?', ('schema_version',))
        schema_version = old_curs.fetchone()
        if schema_version:
            schema_version = pickle.loads(base64.decodestring(schema_version[0]))
        if schema_version == 6:
            converter = self._convert_version_6_row
        elif 3 <= schema_version < 5:
            converter = self._convert_version_3to5_row
        else:
            converter = None
        if not converter:
            return
        old_curs.row_factory = dict_like_row
        return self._old_schema_importer(old_curs.execute('SELECT * FROM file_journal'), converter, server_conn=server_conn)

    def import_from_migrate_db(self, fo, server_conn = None):
        incoming_schema = migrate_db_schema(fo)
        if incoming_schema == 6:
            converter = self._convert_version_6_row
        elif 3 <= incoming_schema <= 5:
            converter = self._convert_version_3to5_row
        else:
            converter = None
        if not converter:
            return
        return self._old_schema_importer(migrate_db_get_table_entries(fo, 'FileJournal'), converter, server_conn=server_conn)

    def patch_broken_xattrs(self, list_iter):
        with self.write_lock() as trans:
            new_curs = trans.sqlite_cursor()
            read_cursor = trans.sqlite_cursor()
            read_cursor.row_factory = dict_like_row
            mps = self.cls_db_get_mount_points(read_cursor)
            last_revisions = self.cls_db_last_revisions(read_cursor)
            fjrl = FileJournalRowLogic(mps)
            for ents in batch(list_iter, FileJournalRowLogic.RECOMMENDED_BATCH_SIZE):
                sp2ent = dict(((server_ent['path'].lower(), server_ent) for server_ent in ents))
                for db_ent in self._get_entries(read_cursor, sp2ent.keys()):
                    listed_ent = sp2ent.pop(db_ent[SERVER_PATH_COL])
                    new_ent = None
                    has_local = db_ent[LOCAL_SJID_COL] is not None
                    attrs_listed_ent = Attributes(listed_ent['attrs'])
                    if has_local and db_ent[LOCAL_SJID_COL] > 1 and db_ent[LOCAL_SJID_COL] == listed_ent['sjid'] and attrs_listed_ent != db_ent[LOCAL_ATTRS_COL]:
                        new_ent = dict(db_ent)
                        new_ent[LOCAL_ATTRS_COL] = attrs_listed_ent
                    elif has_local and db_ent[LOCAL_SJID_COL] == 0 and db_ent[EXTRA_PENDING_DETAILS_COL]['parent'] and db_ent[EXTRA_PENDING_DETAILS_COL]['parent']['sjid'] == listed_ent['sjid']:
                        curattrs = db_ent[EXTRA_PENDING_DETAILS_COL]['parent']['attrs']
                        if curattrs.attr_dict != listed_ent['attrs']:
                            new_ent = dict(db_ent)
                            new_ent[EXTRA_PENDING_DETAILS_COL] = db_ent[EXTRA_PENDING_DETAILS_COL].copy(parent={'sjid': listed_ent['sjid'],
                             'blocklist': str(listed_ent['blocklist']),
                             'size': listed_ent['size'],
                             'dir': listed_ent['dir'],
                             'attrs': curattrs.copy(attr_dict=listed_ent['attrs'])})
                    elif db_ent[UPDATED_SJID_COL] is not None and db_ent[UPDATED_SJID_COL] == listed_ent['sjid']:
                        new_ent = dict(db_ent)
                        new_ent[UPDATED_SJID_COL] = listed_ent['sjid']
                        new_ent[UPDATED_BLOCKLIST_COL] = str(listed_ent['blocklist'])
                        new_ent[UPDATED_SIZE_COL] = listed_ent['size']
                        new_ent[UPDATED_MTIME_COL] = listed_ent['mtime']
                        new_ent[UPDATED_DIR_COL] = 0 if listed_ent['size'] < 0 else (1 if listed_ent['dir'] < 0 else listed_ent['dir'])
                        new_ent[UPDATED_ATTRS_COL] = attrs_listed_ent
                        new_ent[UPDATED_FILENAME_COL] = server_path_basename_unicode(listed_ent['path'])
                    if new_ent:
                        fjrl.update_entry(db_ent, new_ent)

                if len(fjrl) >= FileJournalRowLogic.RECOMMENDED_BATCH_SIZE:
                    fjrl.execute_da_sql(new_curs)
                    fjrl = FileJournalRowLogic(mount_points=mps)
                for sp, listed_ent in sp2ent.iteritems():
                    if listed_ent['sjid'] > last_revisions[server_path_ns_unicode(sp)]:
                        continue
                    if listed_ent['dir'] < 0:
                        raise _ReallyBadDatabaseError("Missing attr row on shared folder, can't really resolve this...")
                    ent = FileJournalRowLogic.new_ent(sp)
                    ent[UPDATED_SJID_COL] = listed_ent['sjid']
                    ent[UPDATED_BLOCKLIST_COL] = str(listed_ent['blocklist'])
                    ent[UPDATED_SIZE_COL] = listed_ent['size']
                    ent[UPDATED_MTIME_COL] = listed_ent['mtime']
                    ent[UPDATED_DIR_COL] = 0 if listed_ent['size'] < 0 else (1 if listed_ent['dir'] < 0 else listed_ent['dir'])
                    ent[UPDATED_ATTRS_COL] = Attributes(listed_ent['attrs'])
                    ent[UPDATED_FILENAME_COL] = server_path_basename_unicode(listed_ent['path'])
                    fjrl.insert_entry(ent)
                    if len(fjrl) >= FileJournalRowLogic.RECOMMENDED_BATCH_SIZE:
                        fjrl.execute_da_sql(new_curs)
                        fjrl = FileJournalRowLogic(mount_points=mps)

            if fjrl:
                fjrl.execute_da_sql(new_curs)

    def _load_root_nses(self, curs):
        assert_(self._is_write_locked)
        assert_(lambda : not self.root_ns_to_mount_table and not self.last_revision)
        try:
            root_nses = curs.execute('SELECT ns FROM namespace_map WHERE NOT EXISTS (SELECT target_ns FROM mount_table WHERE target_ns = ns)').fetchall()
            for root_ns in root_nses:
                root_ns = root_ns[0]
                mount_table = self.root_ns_to_mount_table[root_ns] = NamespaceMountTable()
                last_revision_nses = [root_ns]
                curs.execute('SELECT server_path, target_ns FROM mount_table WHERE server_path LIKE ?', ('%d:/%%' % (root_ns,),))
                for server_path, target_ns in curs:
                    ns, rel = server_path_ns_rel_unicode(server_path)
                    old_mp = mount_table.ns_is_mounted(target_ns)
                    if old_mp:
                        raise _ReallyBadDatabaseError('Namespace %r is mounted twice??? %r and %r' % (target_ns, rel, old_mp))
                    mount_table.mount(rel, target_ns)
                    last_revision_nses.append(target_ns)

                for ent in sqlite3_get_table_entries(curs, 'namespace_map', 'ns', last_revision_nses):
                    self.last_revision[ent['ns']] = ent['last_sjid']

            TRACE('root_ns_to_mount_table = %r', self.root_ns_to_mount_table)
            TRACE('last_revision = %r', self.last_revision)
        except:
            self.root_ns_to_mount_table = {}
            self.last_revision = {}
            raise

    def add_root_ns(self, root_ns):
        with self.write_lock() as trans:
            if root_ns in self.last_revision:
                assert_(lambda : root_ns in self.root_ns_to_mount_table)
                return
            assert_(lambda : root_ns not in self.last_revision)
            curs = trans.sqlite_cursor()
            curs.execute('INSERT INTO namespace_map (ns, last_sjid, checksum, extra) VALUES (?, -1, 0, NULL)', (root_ns,))
            self.root_ns_to_mount_table[root_ns] = NamespaceMountTable()
            self.last_revision[root_ns] = -1

    @staticmethod
    def why_isnt_valid_filejournal_entry(ent):
        return why_isnt_valid_filejournal_entry(ent)

    @staticmethod
    def is_valid_sjid(ns, sjid):
        return is_valid_sjid(ns, sjid)

    @staticmethod
    def is_valid_filejournal_entry(ent):
        return is_valid_filejournal_entry(ent)

    @staticmethod
    def check_db_entries(entries):
        return check_db_entries(entries)

    @staticmethod
    def _sqlite_escape(st):
        return sqlite_escape(st)

    @classmethod
    def _get_entries(cls, cursor, server_paths_iterable):
        return SQLiteBackend._get_entries(cursor, server_paths_iterable)

    def _get_entry(self, cursor, server_path):
        try:
            return self._get_entries(cursor, (server_path,)).next()
        except StopIteration:
            raise FileJournalEntryDoesNotExist

    def is_over_quota(self, server_path):
        return self.uploading_status(server_path) == UPLOAD_QUOTA_CODE

    def _correct_cased_server_path(self, server_path_u, master_path_filename_map = None, lowered = False, local_only = False, trans = None):
        if not server_path_u[:-2].isdigit() or server_path_u[-2:] != u':/':
            ppaths = []
            parent = server_path_u
            parent_old = None
            if lowered:
                while parent != parent_old:
                    ppaths.append((parent, parent))
                    parent_old = parent
                    parent = server_path_dirname_unicode(parent)

            else:
                while parent != parent_old:
                    ppaths.append((parent, parent.lower()))
                    parent_old = parent
                    parent = server_path_dirname_unicode(parent)

            parent_path_filename_map = {} if master_path_filename_map is None else master_path_filename_map
            pp = id(ppaths[-1][1])
            to_get = [ a[1] for a in ppaths if a[1] not in parent_path_filename_map and id(a[1]) != pp ]
            if to_get:
                if trans is None:
                    ents = self._get_entries(self.connhub.conn().cursor(), to_get)
                else:
                    ents = trans.get_entries(to_get)
                for row in ents:
                    if row[LOCAL_FILENAME_COL] and row[LOCAL_SIZE_COL] >= 0:
                        parent_path_filename_map[row[SERVER_PATH_COL]] = row[LOCAL_FILENAME_COL]
                    elif not local_only and row[UPDATED_FILENAME_COL]:
                        parent_path_filename_map[row[SERVER_PATH_COL]] = row[UPDATED_FILENAME_COL]

            return u'/'.join([ parent_path_filename_map.get(spul) or server_path_basename_unicode(spu) for spu, spul in reversed(ppaths) ])
        else:
            return server_path_rel_unicode(server_path_u)

    def root_relative_server_path_powerful(self, server_path, correct_case = None, ctor = None, trans = None):
        try:
            ns, rel = server_path_ns_rel_unicode(server_path)
        except:
            ns, rel = server_path.ns_rel()

        if correct_case:
            rel = correct_case(unicode(server_path), trans=trans)
        if not ctor:
            ctor = NsRelativePath
        if ns not in self.root_ns_to_mount_table:
            for root_ns, mount_table in self.root_ns_to_mount_table.iteritems():
                rel_mount_point = mount_table.ns_is_mounted(ns)
                if rel_mount_point:
                    if correct_case:
                        rel_mount_point = correct_case(u'%d:%s' % (root_ns, rel_mount_point), trans=trans)
                    return ctor(root_ns, server_path_join_unicode(rel_mount_point, rel[1:]) if rel != u'/' else rel_mount_point)

            raise NamespaceNotMountedError("%r isn't locally mounted!" % server_path)
        else:
            return ctor(ns, rel)

    def __omg_really_secret_2(self, server_path_u, **kw):
        return self._correct_cased_server_path(server_path_u, local_only=True)

    def _root_relative_server_path_unlocked(self, server_path, ignore_case = True, ctor = None, local_case_only = False, trans = None):
        return self.root_relative_server_path_powerful(server_path, correct_case=self.__omg_really_secret_2 if local_case_only else (self._correct_cased_server_path if not ignore_case else None), ctor=ctor, trans=trans)

    def root_relative_server_path(self, *n, **kw):
        with self.read_lock() as trans:
            return self._root_relative_server_path_unlocked(trans=trans, *n, **kw)

    def mount_relative_server_path(self, root_relative_path):
        with self.read_lock():
            return self.root_ns_to_mount_table[root_relative_path.ns].translate_relative_path(root_relative_path.ns, root_relative_path.rel)

    def get_mount_points(self):
        with self.read_lock():
            toret = []
            for root_ns, mount_table in self.root_ns_to_mount_table.iteritems():
                toret.extend(((ServerPath.from_ns_rel(root_ns, rel_path, lowered=True), target_ns) for rel_path, target_ns in mount_table.mount_points()))

            return toret

    @classmethod
    def cls_db_get_mount_points(cls, cursor):
        return SQLiteBackend.cls_get_mount_points(cursor)

    def db_get_mount_points(self):
        with self._read_lock_cursor() as curs:
            return self.cls_db_get_mount_points(curs)

    def get_root_namespaces(self):
        with self.read_lock():
            return self.root_ns_to_mount_table.keys()

    def get_root_namespaces_db(self):
        with self._read_lock_cursor() as curs:
            curs.row_factory = just_the_first
            return curs.execute('SELECT ns FROM namespace_map WHERE NOT EXISTS (SELECT target_ns FROM mount_table WHERE target_ns = ns)').fetchall()

    def last_revisions(self):
        with self.read_lock():
            return self.last_revision.copy()

    def get_all_tracked_namespaces(self):
        with self.read_lock():
            return self.last_revision.keys()

    def get_all_tracked_namespaces_db(self):
        with self.read_lock() as trans:
            return trans.get_tracked_namespaces()

    @classmethod
    def cls_db_last_revisions(cls, curs):
        return SQLiteBackend.cls_last_revisions(curs)

    def db_last_revisions(self):
        with self.read_lock() as trans:
            return trans.last_revisions()

    @classmethod
    def cls_db_filter_unsynced_sjids(cls, cursor, sjids):
        if not sjids:
            return ()
        return frozenset(sqlite3_get_table_entries(cursor, 'file_journal', 'updated_sjid', sjids, desired_columns=('updated_sjid',), extra_conditions='local_sjid IS NULL', row_factory=just_the_first))

    def db_filter_unsynced_sjids(self, sjids):
        with self._read_lock_cursor() as cursor:
            return self.cls_db_filter_unsynced_sjids(cursor, sjids)

    def reset_sjids(self):
        TRACE('Resetting last sjid for every namespace...')
        with self.write_lock() as trans:
            curs = trans.sqlite_cursor()
            curs.execute('UPDATE namespace_map SET last_sjid = -1')
            for k in self.last_revision:
                self.last_revision[k] = -1

    def _mounted_at_internal(self, target_ns):
        for ns, mount_table in self.root_ns_to_mount_table.iteritems():
            rel = mount_table.ns_is_mounted(target_ns)
            if rel:
                return ServerPath.from_ns_rel(ns, rel)

    def get_namespace_checksums(self):
        with self._read_lock_cursor() as curs:
            return dict(((ns, to_unsigned_64_bit(checksum)) for ns, checksum in curs.execute('SELECT ns, checksum FROM namespace_map')))

    def get_namespace_checksums_and_last_sjid(self):
        with self._read_lock_cursor() as curs:
            return dict(((ns, {'checksum': to_unsigned_64_bit(checksum),
              'last_sjid': last_sjid}) for ns, checksum, last_sjid in curs.execute('SELECT ns, checksum, last_sjid FROM namespace_map')))

    def get_namespace_checksums_plow(self):
        with self._read_lock_cursor() as curs:
            self._mount_table = frozendict(((unicode(sp), target_ns) for sp, target_ns in self.cls_db_get_mount_points(curs)))
            curs.row_factory = just_the_first
            try:
                orig = dict(((ns, 0) for ns in curs.execute('SELECT ns FROM namespace_map')))
                orig.update(pickle.loads(str(curs.execute('SELECT server_hash(server_path, extra_pending_details, local_sjid, local_blocklist, local_size, local_dir, local_attrs, updated_sjid, updated_blocklist, updated_size, updated_dir, updated_attrs) from file_journal').fetchone() or pickle.dumps({}))))
                return orig
            finally:
                del self._mount_table

    def mounted_at(self, target_ns):
        with self.read_lock():
            return self._mounted_at_internal(target_ns)

    def target_ns(self, server_path, lower = True):
        with self.read_lock():
            return self._target_ns(server_path, lower=lower)

    def _under_root_sql_predicate(self, root_server_path, variable_where_clause = False):
        ns, rel = root_server_path.ns_rel()
        try:
            mount_table = self.root_ns_to_mount_table[ns]
        except KeyError:
            assert_(lambda : not root_server_path.is_root)
            tosearch = [u'%s/' % root_server_path.lower()]
        else:
            if rel == u'/':
                tosearch = [u'%d:/' % ns]
                for rel_path_lowered, target_ns in mount_table.mount_points():
                    tosearch.append(u'%d:/' % target_ns)

            else:
                rell = rel.lower()
                at_ns = mount_table.is_mount_point(rell, lower=False)
                if at_ns:
                    tosearch = [u'%d:/' % at_ns]
                else:
                    tosearch = [u'%s/' % root_server_path.lower()]
                    check = rell + u'/'
                    for rel_path_lowered, ns in mount_table.mount_points():
                        if rel_path_lowered.startswith(check):
                            tosearch.append(u'%d:/' % ns)

        server_path_col = '%(SERVER_PATH_COL)s' if variable_where_clause else 'server_path'
        return ('(%s)' % ' OR '.join([ "%s LIKE ? ESCAPE '\\'" % server_path_col for x in xrange(len(tosearch)) ]), [ FileCache._sqlite_escape(x) + '%' for x in tosearch ])

    def get_num_entries_under_root(self, root_server_path):
        with self._read_lock_cursor() as cursor:
            where_clause, binding_params = self._under_root_sql_predicate(root_server_path)
            cursor.execute('SELECT COUNT(*) FROM file_journal WHERE local_filename IS NOT NULL AND %s' % where_clause, binding_params)
            return cursor.fetchone()[0]

    _blank_sjid = {'sjid': 0}

    @staticmethod
    def _FastDetails_factory_local(cursor, ent):
        return FastDetails(blocklist=ent[0], mtime=ent[1], size=ent[2], dir=ent[3], attrs=ent[4], ctime=ent[5], sjid=ent[6] or -(ent[9]['parent'] or FileCache._blank_sjid)['sjid'], server_path=ServerPath(ServerPath(ent[7], lowered=True), ent[8]), machine_guid=ent[10])

    @staticmethod
    def _FastDetails_factory_local_with_mount_request(cursor, ent):
        if not ent[9] or not ent[9]['mount_request']:
            return FileCache._FastDetails_factory_local(cursor, ent)
        return FastDetails(blocklist=ent[0], mtime=ent[1], size=ent[2], dir=ent[3], attrs=ent[4], ctime=ent[5], sjid=ent[6] or -(ent[9]['parent'] or FileCache._blank_sjid)['sjid'], server_path=ServerPath(ServerPath(ent[7], lowered=True), ent[8]), mount_request=ent[9]['mount_request'], machine_guid=ent[10])

    @staticmethod
    def _FastDetails_factory_local_with_id(cursor, ent):
        return FastDetails(blocklist=ent[0], mtime=ent[1], size=ent[2], dir=ent[3], attrs=ent[4], ctime=ent[5], sjid=ent[6], server_path=ent[7], parent_blocklist=ent[8], mount_request=ent[9])

    def get_num_local_files(self):
        with self._read_lock_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM file_journal WHERE local_sjid IS NOT NULL AND local_size >= 0')
            return cursor.fetchone()[0]

    @staticmethod
    @handle_exceptions_ex(should_raise=True)
    def _db_no_data_plat(attrs_str):
        return Attributes(Attributes.unmarshal(attrs_str).attr_dict).marshal()

    def get_directory_ignore_set(self):
        with self.read_lock():
            return self._unicode_rr_set

    def get_directory_ignore_set_db(self):
        with self.read_lock() as trans:
            return trans.get_directory_ignore_set()

    @staticmethod
    def compute_ignore_changes(initial_directory_ignore_set, new_directory_ignore_set):
        return (frozenset((rr_sp for rr_sp in new_directory_ignore_set if rr_sp not in initial_directory_ignore_set and not any((rr_sp.startswith(initial_ignored + u'/') for initial_ignored in initial_directory_ignore_set)))), frozenset((rr_sp for rr_sp in initial_directory_ignore_set if rr_sp not in new_directory_ignore_set)))

    @staticmethod
    def _sweet_func(ns, rel):
        return u'%d:%s' % (ns, rel)

    @handle_exceptions_ex(should_raise=True)
    def _db_root_relative_server_path(self, uni_server_path, filename, lowered):
        return self._root_relative_server_path_unlocked(uni_server_path, ctor=self._sweet_func)

    def __omg_really_secret(self, server_path_u, **kw):
        return self._correct_cased_server_path(server_path_u, self.__rr_case_map, self.__rr_lowered)

    @handle_exceptions_ex(should_raise=True)
    def _db_root_relative_server_path_case(self, uni_server_path, filename, lowered):
        if filename and uni_server_path not in self.__rr_case_map:
            self.__rr_case_map[uni_server_path] = filename
            self.__rr_lowered = lowered
            try:
                return self.root_relative_server_path_powerful(uni_server_path, ctor=self._sweet_func, correct_case=self.__omg_really_secret)
            finally:
                del self.__rr_case_map[uni_server_path]
                del self.__rr_lowered

        else:
            self.__rr_lowered = lowered
            try:
                return self.root_relative_server_path_powerful(uni_server_path, ctor=self._sweet_func, correct_case=self.__omg_really_secret)
            finally:
                del self.__rr_lowered

    @staticmethod
    def _db_empty_attrs_with_data_plats(attrs_str):
        return Attributes(data_plats=Attributes.unmarshal(attrs_str).data_plats).marshal()

    @staticmethod
    @handle_exceptions_ex(should_raise=True)
    def _db_create_extra_pending_details(parent_sjid, parent_blocklist, parent_size, parent_dir, parent_attrs_str, mount_request, host_id, guid, guid_rev):
        return ExtraPendingDetails(mount_request=mount_request, parent={'sjid': parent_sjid,
         'host_id': host_id,
         'blocklist': parent_blocklist,
         'size': parent_size,
         'dir': parent_dir,
         'attrs': Attributes.unmarshal(parent_attrs_str),
         'guid': guid,
         'guid_rev': guid_rev}).marshal()

    def _get_pending_parent(self, server_path):
        with self._read_lock_cursor() as cursor:
            cursor.execute('SELECT extra_pending_details FROM file_journal WHERE server_path = ? AND local_sjid IS NOT NULL AND local_sjid = 0', (unicode(server_path).lower(),))
            ret = cursor.fetchone()
            if ret is None:
                return
            return ret[0]['parent']

    def _host_id_for_sjid(self, ns_id, sjid):
        with self._read_lock_cursor() as cursor:
            row = cursor.execute('SELECT host_id FROM host_id WHERE ns_id = ? AND sjid = ?', (ns_id, sjid)).fetchone()
            if row is not None:
                return row[0]
            return

    def _timestamp_for_sjid(self, ns_id, sjid):
        with self._read_lock_cursor() as cursor:
            row = cursor.execute('SELECT timestamp FROM timestamp WHERE ns_id = ? AND sjid = ?', (ns_id, sjid)).fetchone()
            if row is not None:
                return row[0]
            return

    def unsynced_local_files_exist_under(self, server_path, lower = True):
        with self._read_lock_cursor() as cursor:
            where_clause, binding_params = self._under_root_sql_predicate(server_path)
            where_clause = '((%s) OR server_path = ?)' % (where_clause,)
            binding_params += [unicode(server_path.lower())]
            return cursor.execute('SELECT EXISTS (SELECT 1 FROM file_journal WHERE (%s) AND local_sjid IS NOT NULL AND local_sjid <= 1)' % where_clause, binding_params).fetchone()[0]

    def change_directory_ignore_set(self, *n, **kw):
        with self.write_lock():
            return self._change_directory_ignore_set_unlocked(*n, **kw)

    def _change_directory_ignore_set_unlocked(self, new_directory_ignore_set, case_sensitive = False, queue = True):
        assert_(lambda : all((a == a.lower() and type(a) is unicode for a in new_directory_ignore_set)))

        @contextlib.contextmanager
        def after_transaction():
            yield
            self._unicode_rr_set = frozenset(new_directory_ignore_set)

        with after_transaction():
            with self.write_lock() as trans:
                cursor = trans.sqlite_cursor()
                read_cursor = cursor.connection.cursor()
                read_cursor2 = cursor.connection.cursor()
                read_cursor2.row_factory = dict_like_row
                cursor.execute('DROP TABLE IF EXISTS root_relative_to_delete')
                cursor.execute('\n                CREATE TEMPORARY TABLE root_relative_to_delete (\n                    path TEXT PRIMARY KEY DESC NOT NULL,\n                    mtime INTEGER NOT NULL,\n                    size INTEGER NOT NULL,\n                    blocklist BYTETEXT NOT NULL,\n                    dir INTEGER,\n                    machine_guid BYTETEXT UNIQUE\n                )\n                ')
                new_ignores, new_unignores = self.compute_ignore_changes(self._unicode_rr_set, new_directory_ignore_set)

                def remove_local_guid_refs(fj_where_clause, binding_params):
                    sql = '\nUPDATE %(FILE_JOURNAL_GUID_TABLE_NAME)s SET\n%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s = NULL,\n%(FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL)s = 0\nWHERE\n%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s IN (\n    SELECT %(SERVER_PATH_COL)s FROM %(FILE_JOURNAL_TABLE_NAME)s WHERE\n    %(where_clause)s\n)\n'
                    template = dict(where_clause=fj_where_clause)
                    template.update(_SQL_VARS)
                    cursor.execute(sql % template, binding_params)

                for rr in new_ignores:
                    root_server_path = self.mount_relative_server_path(NsRelativePathFast(*server_path_ns_rel_unicode(rr)))
                    where_clause, binding_params = self._under_root_sql_predicate(root_server_path, variable_where_clause=True)
                    where_clause %= dict(SERVER_PATH_COL='file_journal.server_path')
                    where_clause = '(((%s) OR file_journal.server_path = ?) AND local_sjid > 1)' % (where_clause,)
                    binding_params += [unicode(root_server_path.lower())]
                    self.__rr_case_map = {}
                    try:
                        sql = '\n                        INSERT INTO root_relative_to_delete\n                            (path, mtime, size, blocklist, dir, machine_guid)\n                        SELECT\n                            %s(server_path, local_filename, 1),\n                            local_mtime,\n                            local_size,\n                            local_blocklist,\n                            local_dir,\n                            local_machine_guid\n                        FROM file_journal LEFT JOIN file_journal_guid USING (server_path)\n                        WHERE %s\n                    ' % ('root_relative_server_path_case' if case_sensitive else 'root_relative_server_path', where_clause)
                        cursor.execute(sql, binding_params)
                    finally:
                        del self.__rr_case_map

                    cursor.execute('UPDATE block_ref SET how = how | (1<<42) WHERE EXISTS (SELECT 1 FROM file_journal WHERE  file_journal.id = block_ref.fj_id AND (%s))' % (where_clause,), binding_params)
                    sql = "\nUPDATE %(FILE_JOURNAL_TABLE_NAME)s SET\nlocal_size = -1, local_mtime = -1, local_ctime = -1, local_blocklist = '',\nlocal_attrs = empty_attrs_with_data_plats(local_attrs), local_sjid = 0, local_dir = 0,\nextra_pending_details = create_extra_pending_details(local_sjid, local_blocklist, local_size,\n    local_dir, local_attrs, NULL,\n    (SELECT host_id FROM host_id as h WHERE\n     h.ns_id = extract_ns_id(server_path) AND\n     h.sjid = local_sjid),\n     %(PARENT_GUID_SELECT_GUID)s,\n     %(PARENT_GUID_SELECT_GUID_REV)s\n)\nWHERE (%(where_clause)s)\n"
                    parent_guid_select = '\n(\n    SELECT %(DESIRED_COL)s FROM %(GUID_JOURNAL_TABLE_NAME)s WHERE\n    %(GUID_JOURNAL_MACHINE_GUID_COL)s = (\n        SELECT %(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s\n        FROM %(FILE_JOURNAL_GUID_TABLE_NAME)s WHERE\n        %(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s =\n        %(FILE_JOURNAL_TABLE_NAME)s.%(SERVER_PATH_COL)s\n    )\n)\n'

                    def p_select(col):
                        template = dict(DESIRED_COL=col)
                        template.update(_SQL_VARS)
                        return parent_guid_select % template

                    template = dict(PARENT_GUID_SELECT_GUID=p_select(_SQL_VARS['GUID_JOURNAL_GUID_COL']), PARENT_GUID_SELECT_GUID_REV=p_select(_SQL_VARS['GUID_JOURNAL_SYNCED_GUID_REV_COL']), where_clause=where_clause)
                    template.update(_SQL_VARS)
                    cursor.execute(sql % template, binding_params)
                    cursor.execute('\nUPDATE %(FILE_JOURNAL_GUID_TABLE_NAME)s SET\n%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s = NULL\nWHERE\n%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s IS NOT NULL AND\n%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s IN (\n    SELECT %(SERVER_PATH_COL)s FROM %(FILE_JOURNAL_TABLE_NAME)s WHERE\n    %(LOCAL_SIZE_COL)s < 0\n)\n' % _SQL_VARS)
                    to_del = read_cursor.execute('SELECT extract_ns_id(server_path),        parent_sjid(extra_pending_details) FROM file_journal WHERE local_sjid = 0')
                    cursor.executemany('DELETE FROM host_id WHERE ns_id = ? AND sjid = ?', to_del)

                for rr in new_unignores:
                    root_server_path = self.mount_relative_server_path(NsRelativePathFast(*server_path_ns_rel_unicode(rr)))
                    where_clause, binding_params = self._under_root_sql_predicate(root_server_path)
                    where_clause = '((%s) OR server_path = ?)' % (where_clause,)
                    binding_params += [unicode(root_server_path.lower())]
                    cursor.execute('DELETE FROM block_ref WHERE EXISTS (SELECT 1 FROM file_journal WHERE file_journal.id = block_ref.fj_id AND %s)' % (where_clause,), binding_params)
                    cursor.execute('DELETE FROM block_cache WHERE NOT EXISTS (SELECT 1 FROM block_ref WHERE block_ref.hash_id = block_cache.id)')
                    case_2_where_clause = '\nlocal_sjid IS NOT NULL AND\nlocal_sjid > 1 AND\nupdated_sjid is NULL AND (%s)' % (where_clause,)
                    cursor.execute('UPDATE file_journal SET local_sjid = NULL, local_dir = NULL, local_size = NULL, local_attrs = NULL, local_mtime = NULL, local_blocklist = NULL, local_filename = NULL, local_ctime = NULL, extra_pending_details = NULL, updated_filename = local_filename, updated_sjid = local_sjid, updated_dir = local_dir, updated_size = local_size, updated_attrs = no_data_plat(local_attrs), updated_mtime = local_mtime, updated_blocklist = local_blocklist WHERE %s' % (case_2_where_clause,), binding_params)
                    sql = '\nUPDATE %(FILE_JOURNAL_GUID_TABLE_NAME)s SET\n%(FILE_JOURNAL_GUID_UPDATED_GUID_COL)s = %(UPDATED_GUID_SELECT)s,\n%(FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL)s = %(UPDATED_GUID_REV_SELECT)s\nWHERE\n%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s IN (\n    SELECT %(SERVER_PATH_COL)s FROM %(FILE_JOURNAL_TABLE_NAME)s WHERE\n    %(where_clause)s\n)\n'
                    template = '\n(\n    SELECT %(DESIRED_COL)s FROM %(GUID_JOURNAL_TABLE_NAME)s WHERE\n    %(GUID_JOURNAL_MACHINE_GUID_COL)s = %(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s\n)\n'

                    def p_select2(col):
                        template_dict = dict(DESIRED_COL=col)
                        template_dict.update(_SQL_VARS)
                        return template % template_dict

                    template = dict(UPDATED_GUID_SELECT=p_select2(_SQL_VARS['GUID_JOURNAL_GUID_COL']), UPDATED_GUID_REV_SELECT=p_select2(_SQL_VARS['GUID_JOURNAL_SYNCED_GUID_REV_COL']), where_clause=case_2_where_clause)
                    template.update(_SQL_VARS)
                    sql %= template
                    cursor.execute(sql, binding_params)
                    case_3_where_clause = 'local_sjid IS NOT NULL AND local_sjid = 0 AND updated_sjid IS NULL AND (%s)' % (where_clause,)

                    def feed_into_execute(handle_parent):
                        read_cursor.execute('SELECT id, server_path, extra_pending_details FROM file_journal WHERE %s' % (case_3_where_clause,), binding_params)
                        for rid, server_path, extra_pending_details in read_cursor:
                            p = extra_pending_details['parent']
                            toyield = handle_parent(rid, server_path, p)
                            if toyield is not None:
                                yield toyield

                    def handle_parent_for_host_id(_, server_path, p):
                        if p is None:
                            return
                        host_id = p.get('host_id')
                        if host_id is None:
                            return
                        return (server_path_ns_unicode(server_path), p['sjid'], host_id)

                    cursor.executemany('INSERT OR IGNORE INTO host_id (ns_id, sjid, host_id) VALUES (?, ?, ?)', feed_into_execute(handle_parent_for_host_id))
                    sql = '\nUPDATE %(FILE_JOURNAL_GUID_TABLE_NAME)s SET\n%(FILE_JOURNAL_GUID_UPDATED_GUID_COL)s = %(SELECT_UPDATED_GUID)s,\n%(FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL)s = %(SELECT_UPDATED_GUID_REV)s\n'

                    def p_select3(func):
                        template = '\n(\n    SELECT %(FUNC)s(%(EXTRA_PENDING_DETAILS_COL)s) FROM %(FILE_JOURNAL_TABLE_NAME)s\n    WHERE %(where_clause)s AND\n    %(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s =\n    %(FILE_JOURNAL_TABLE_NAME)s.%(SERVER_PATH_COL)s\n)\n'
                        template_dict = dict(FUNC=func, where_clause=case_3_where_clause)
                        template_dict.update(_SQL_VARS)
                        return template % template_dict

                    template = dict(SELECT_UPDATED_GUID=p_select3('parent_guid'), SELECT_UPDATED_GUID_REV=p_select3('parent_guid_rev'))
                    template.update(_SQL_VARS)
                    sql %= template
                    cursor.execute(sql, binding_params + binding_params)

                    def handle_parent_for_file_journal(rid, _, p):
                        if p is None:
                            return
                        return (p['sjid'],
                         p['dir'],
                         p['size'],
                         Attributes(attr_dict=p['attrs'].attr_dict),
                         p['blocklist'],
                         rid)

                    cursor.executemany('UPDATE file_journal SET local_sjid = NULL, local_dir = NULL, local_size = NULL, local_attrs = NULL, local_mtime = NULL, local_blocklist = NULL, local_filename = NULL, local_ctime = NULL, extra_pending_details = NULL, updated_filename = local_filename, updated_sjid = ?, updated_dir = ?, updated_size = ?, updated_attrs = ?, updated_mtime = %d, updated_blocklist = ? WHERE id = ?' % (long(time.time()),), feed_into_execute(handle_parent_for_file_journal))
                    case_4_where_clause = 'updated_sjid IS NULL AND (%s)' % (where_clause,)
                    sql = '\nDELETE FROM %(FILE_JOURNAL_GUID_TABLE_NAME)s WHERE\n%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s IN (\nSELECT %(SERVER_PATH_COL)s FROM %(FILE_JOURNAL_TABLE_NAME)s WHERE\n%(where_clause)s\n)\n'
                    template = dict(where_clause=case_4_where_clause)
                    template.update(_SQL_VARS)
                    cursor.execute(sql % template, binding_params)
                    cursor.execute('DELETE FROM file_journal WHERE %s' % (case_4_where_clause,), binding_params)
                    case_5_where_clause = 'local_sjid IS NOT NULL AND updated_sjid IS NOT NULL AND (%s)' % (where_clause,)
                    cursor.execute('UPDATE file_journal SET local_sjid = NULL, local_dir = NULL, local_size = NULL, local_attrs = NULL, local_mtime = NULL, local_blocklist = NULL, local_filename = NULL, local_ctime = NULL, extra_pending_details = NULL WHERE %s' % case_5_where_clause, binding_params)
                    remove_local_guid_refs(where_clause, binding_params)

                trans.set_config_key(CONFIG_SELECTIVE_SYNC_IGNORE_LIST, list(new_directory_ignore_set))
                if queue:
                    old_rr_set = self._unicode_rr_set
                    self._unicode_rr_set = frozenset(new_directory_ignore_set)
                    try:
                        trans.refilter_queues()
                    finally:
                        self._unicode_rr_set = old_rr_set

                return SelectiveSyncDeleteQueue(cursor.connection)

    def get_all_local_details_under_relative_root_iterator(self, root_relative_server_path, case_sensitive = False):
        with self.write_lock() as trans:
            cursor = trans.sqlite_cursor()
            where_clause, binding_params = self._under_root_sql_predicate(self.mount_relative_server_path(root_relative_server_path))
            if case_sensitive:
                self.__rr_case_map = dict(cursor.execute('SELECT server_path, CASE local_filename WHEN NULL THEN updated_filename ELSE local_filename END from file_journal WHERE local_sjid IS NOT NULL AND local_dir == 1 AND local_size >= 0 AND %s' % where_clause, binding_params))
            try:
                guid_subquery = '\n                    SELECT %(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s\n                    FROM %(FILE_JOURNAL_GUID_TABLE_NAME)s\n                    WHERE %(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s = file_journal.server_path\n                ' % _SQL_VARS
                file_query = '\n                    SELECT\n                        id,\n                        root_relative_server_path%(case_suffix)s(server_path, local_filename, 1) as path,\n                        local_dir,\n                        local_size,\n                        local_mtime,\n                        local_ctime,\n                        local_attrs,\n                        local_filename,\n                        (%(guid_subquery)s)\n                    FROM file_journal\n                    WHERE\n                        local_sjid IS NOT NULL AND\n                        local_size >= 0 AND\n                        %(where_clause)s\n                    ORDER BY path\n                    COLLATE DIRTRAVERSE\n                ' % {'case_suffix': '_case' if case_sensitive else '',
                 'guid_subquery': guid_subquery,
                 'where_clause': where_clause}
                cursor.execute(file_query, binding_params)
                for entry in cursor:
                    yield entry

            finally:
                try:
                    del self.__rr_case_map
                except AttributeError:
                    pass

    def get_immediate_local_details_under_relative_root(self, server_path, handler = None, case_sensitive = False):
        if handler is None:
            handler = operator.methodcaller('fetchall')
        with self.write_lock() as trans:
            cursor = trans.sqlite_cursor()
            ns = self.root_ns_to_mount_table[server_path.ns].is_mount_point(server_path.rel)
            if ns is not None:
                parent_srv_path = ServerPath.from_ns_rel(ns, u'/')
            else:
                parent_srv_path = self.mount_relative_server_path(server_path)
            parent_path = unicode(parent_srv_path).lower()
            TRACE('parent path is %s', parent_path)
            where_clause = 'parent_path = ?'
            binding_params = [parent_path]
            if case_sensitive:
                self.__rr_case_map = {}
            try:
                file_query_sql = '\nSELECT id, %s(server_path, local_filename, 1), local_dir,\nlocal_size, local_mtime, local_ctime, local_attrs, local_filename, (%s)\nFROM file_journal\nWHERE local_sjid IS NOT NULL AND local_size >= 0 AND %s\n'
                sub_query_sql = '\nSELECT %(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s\nFROM %(FILE_JOURNAL_GUID_TABLE_NAME)s\nWHERE (%(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s =\nfile_journal.server_path)\n' % _SQL_VARS
                if case_sensitive:
                    query_args = ('root_relative_server_path_case', sub_query_sql, where_clause)
                else:
                    query_args = ('root_relative_server_path', sub_query_sql, where_clause)
                cursor.execute(file_query_sql % query_args, binding_params)
                return handler(cursor)
            finally:
                try:
                    del self.__rr_case_map
                except AttributeError:
                    pass

    def get_local_details_under(self, root_server_path, blocklist = None, handler = None):
        with self._read_lock_cursor() as cursor:
            where_clause, binding_params = self._under_root_sql_predicate(root_server_path)
            if blocklist:
                where_clause = '((%s) AND local_blocklist = ?)' % (where_clause,)
                binding_params += [blocklist]
            cursor.row_factory = self._FastDetails_factory_local_with_id
            cursor.execute('SELECT local_blocklist, local_mtime, local_size, local_dir, local_attrs,local_ctime, local_sjid, server_path, local_filename, id from file_journal WHERE local_sjid IS NOT NULL AND local_size >= 0 AND %s' % (where_clause,), binding_params)
            if handler:
                return handler(cursor)
            return cursor.fetchall()

    def find_blocklist_in_dir(self, blocklist, dir_server_path):
        all_deets = self.get_local_details_under(dir_server_path, blocklist=blocklist)
        for deets in all_deets:
            if self.root_relative_server_path(deets.server_path).dirname.lower() == dir_server_path.lower():
                return deets

    def get_local_details_batch(self, server_paths, lower = True):
        with self._read_lock_cursor() as cursor:
            return list(sqlite3_get_table_entries(cursor, 'file_journal LEFT JOIN file_journal_guid USING (server_path)', 'file_journal.server_path', (unicode(x).lower() for x in server_paths) if lower else (unicode(x) for x in server_paths), desired_columns=('file_journal.local_blocklist', 'file_journal.local_mtime', 'file_journal.local_size', 'file_journal.local_dir', 'file_journal.local_attrs', 'file_journal.local_ctime', 'file_journal.local_sjid', 'file_journal.parent_path', 'file_journal.local_filename', 'file_journal.extra_pending_details', 'file_journal_guid.local_machine_guid'), row_factory=self._FastDetails_factory_local, extra_conditions='local_sjid IS NOT NULL'))

    def get_all_local_details(self, lower = True):
        with self._read_lock_cursor() as cursor:
            cursor.row_factory = self._FastDetails_factory_local_with_mount_request
            cursor.execute('SELECT file_journal.local_blocklist,\n                                     file_journal.local_mtime,\n                                     file_journal.local_size,\n                                     file_journal.local_dir,\n                                     file_journal.local_attrs,\n                                     file_journal.local_ctime,\n                                     file_journal.local_sjid,\n                                     file_journal.parent_path,\n                                     file_journal.local_filename,\n                                     file_journal.extra_pending_details,\n                                     file_journal_guid.local_machine_guid\n                              FROM file_journal LEFT JOIN file_journal_guid USING (server_path)\n                              WHERE local_sjid IS NOT NULL AND local_size >= 0')
            return cursor.fetchall()

    def get_all_updated_details(self, lower = True):
        with self._read_lock_cursor() as cursor:
            cursor.row_factory = _FastDetails_factory_updated
            join_source = 'file_journal as f1 LEFT OUTER JOIN host_id as h1 ON extract_ns_id(f1.server_path) = h1.ns_id AND f1.updated_sjid = h1.sjid LEFT OUTER JOIN timestamp as ts1 ON extract_ns_id(f1.server_path) = ts1.ns_id AND f1.updated_sjid = ts1.sjid'
            cursor.execute('SELECT updated_blocklist, updated_mtime, updated_size, updated_dir, updated_attrs,updated_sjid, parent_path, updated_filename, h1.host_id, ts1.timestamp FROM %s WHERE updated_sjid IS NOT NULL AND updated_size >= 0' % (join_source,))
            return cursor.fetchall()

    def get_updated_details_batch(self, server_paths, lower = True):
        with self._read_lock_cursor() as cursor:
            desired_columns = (UPDATED_BLOCKLIST_COL,
             UPDATED_MTIME_COL,
             UPDATED_SIZE_COL,
             UPDATED_DIR_COL,
             UPDATED_ATTRS_COL,
             UPDATED_SJID_COL,
             PARENT_PATH_COL,
             UPDATED_FILENAME_COL,
             'h1.host_id',
             'ts1.timestamp')
            paths = (unicode(x).lower() for x in server_paths) if lower else itertools.imap(unicode, server_paths)
            factory = _FastDetails_factory_updated
            join_source = 'file_journal as f1 LEFT OUTER JOIN host_id as h1 ON extract_ns_id(f1.server_path) = h1.ns_id AND f1.updated_sjid = h1.sjid LEFT OUTER JOIN timestamp as ts1 ON extract_ns_id(f1.server_path) = ts1.ns_id AND f1.updated_sjid = ts1.sjid'
            return list(sqlite3_get_table_entries(cursor, join_source, 'server_path', paths, desired_columns=desired_columns, row_factory=factory, extra_conditions='updated_sjid IS NOT NULL'))

    def _translate_parent_path(self, server_path, lower = True):
        assert_(self._is_read_locked)
        ns, rel = server_path.ns_rel()
        try:
            mt = self.root_ns_to_mount_table[ns]
        except KeyError:
            return unicode(server_path)

        target_ns = mt.is_mount_point(rel, lower=lower)
        if target_ns:
            return u'%d:/' % target_ns
        else:
            return unicode(server_path)

    @staticmethod
    @handle_exceptions_ex(should_raise=True)
    def _db_parent_dir(epd):
        if epd:
            parent = ExtraPendingDetails.unmarshal(epd).parent
            if parent is not None:
                return propagate_none(int, parent.get('dir'))

    @staticmethod
    @handle_exceptions_ex(should_raise=True)
    def _db_parent_size(epd):
        if epd:
            parent = ExtraPendingDetails.unmarshal(epd).parent
            if parent is not None:
                return propagate_none(int, parent.get('size'))

    @staticmethod
    @handle_exceptions_ex(should_raise=True)
    def _db_parent_sjid(epd):
        if epd:
            parent = ExtraPendingDetails.unmarshal(epd).parent
            if parent is not None:
                return propagate_none(int, parent.get('sjid'))

    @staticmethod
    @handle_exceptions_ex(should_raise=True)
    def _db_has_parent(epd):
        if epd:
            return int(ExtraPendingDetails.unmarshal(epd).parent is not None)
        return 0

    @handle_exceptions_ex(should_raise=True)
    def _db_translate_mount_points_to_ns_roots(self, mp):
        ns, rel = mp.split(':', 1)
        mount_table = self.root_ns_to_mount_table.get(int(ns), None)
        if mount_table is not None:
            mount_ns = mount_table.is_mount_point(rel, lower=False)
            if mount_ns is not None:
                return u'%d:/' % mount_ns
        return mp

    def __uni_ctor(self, *n):
        return u'%d:%s' % n

    @handle_exceptions_ex(should_raise=True)
    def _db_selective_sync_is_ignored(self, sp):
        return self.__ignore_set_should_ignore_lc_uni(self.root_relative_server_path(sp, ctor=self.__uni_ctor))

    _dir_exists = '((%(ent)s.updated_sjid IS NULL AND %(ent)s.local_sjid IS NOT NULL AND %(ent)s.local_sjid == 0 AND parent_dir(%(ent)s.extra_pending_details) = 1) OR (%(ent)s.updated_sjid IS NULL AND %(ent)s.local_sjid IS NOT NULL AND %(ent)s.local_sjid > 1 AND %(ent)s.local_dir = 1) OR (%(ent)s.updated_sjid IS NOT NULL AND %(ent)s.local_sjid IS NULL AND %(ent)s.updated_sjid > 1 AND %(ent)s.updated_dir = 1) OR (%(ent)s.updated_sjid IS NOT NULL AND %(ent)s.local_sjid IS NOT NULL AND %(ent)s.updated_sjid > 1 AND %(ent)s.local_sjid > 1 AND %(ent)s.updated_sjid >= %(ent)s.local_sjid AND %(ent)s.updated_dir = 1) OR (%(ent)s.updated_sjid IS NOT NULL AND %(ent)s.local_sjid IS NOT NULL AND %(ent)s.updated_sjid > 1 AND %(ent)s.local_sjid > 1 AND %(ent)s.local_sjid > %(ent)s.updated_sjid AND %(ent)s.local_dir = 1) OR (%(ent)s.updated_sjid IS NOT NULL AND %(ent)s.local_sjid IS NOT NULL AND %(ent)s.updated_sjid > 1 AND %(ent)s.local_sjid = 0 AND (NOT has_parent(%(ent)s.extra_pending_details) OR %(ent)s.updated_sjid >= parent_sjid(%(ent)s.extra_pending_details)) AND %(ent)s.updated_dir = 1) OR (%(ent)s.updated_sjid IS NOT NULL AND %(ent)s.local_sjid IS NOT NULL AND %(ent)s.updated_sjid > 1 AND %(ent)s.local_sjid = 0 AND has_parent(%(ent)s.extra_pending_details) AND parent_sjid(%(ent)s.extra_pending_details) > %(ent)s.updated_sjid AND parent_dir(%(ent)s.extra_pending_details) = 1))'

    def get_server_dir_children(self, server_path, lower = True):
        if lower:
            server_path = server_path.lower()
        with self._read_lock_cursor() as cursor:
            return cursor.execute('SELECT (CASE WHEN one.local_filename IS NOT NULL THEN one.local_filename ELSE one.updated_filename END), EXISTS (SELECT 1 FROM file_journal AS two         WHERE         translate_mount_points_to_ns_roots(one.server_path) = two.parent_path AND         %s)FROM file_journal AS one WHERE one.parent_path = ? AND %s' % (self._dir_exists % {'ent': 'two'}, self._dir_exists % {'ent': 'one'}), (self._translate_parent_path(server_path, lower=False),)).fetchall()

    def server_dir_exists(self, server_path, lower = True):
        if lower:
            server_path = server_path.lower()
        with self._read_lock_cursor() as cursor:
            sql_to_execute = 'SELECT %s FROM file_journal WHERE server_path = ?' % (self._dir_exists % {'ent': 'file_journal'})
            sql_param = (server_path,)
            result = cursor.execute(sql_to_execute, sql_param).fetchone()
            return result and result[0]

    def size_of_dropbox(self):
        with self._read_lock_cursor() as cursor:
            return cursor.execute('SELECT SUM(CASE WHEN     updated_size IS NOT NULL THEN updated_size     ELSE (CASE WHEN           (local_size IS NOT NULL AND            local_sjid > 1) THEN local_size ELSE 0 END) END) FROM file_journal').fetchone()[0]

    def update_ctime_on_files(self, ctimeidlist):
        with self.write_lock() as trans:
            trans.sqlite_cursor().executemany('UPDATE file_journal SET local_ctime = ? WHERE id = ? and local_ctime < ?', ctimeidlist)

    def update_attrs_parameters(self, new_data_plats, new_whitelist):
        with self.write_lock() as trans:
            old_data_plats = frozenset(trans.get_config_key(CONFIG_ATTRS_DATA_PLATS))
            old_whitelist = trans.get_config_key(CONFIG_ATTRS_WHITELIST)
            if new_whitelist is None:
                new_whitelist = old_whitelist
            if new_data_plats is None:
                new_data_plats = old_data_plats
            new_data_plats = frozenset(new_data_plats)
            if old_data_plats != new_data_plats or old_whitelist != new_whitelist:
                TRACE('Old data plats, old_whitelist: %r %r', old_data_plats, old_whitelist)
                TRACE('New data plats, new_whitelist: %r %r', new_data_plats, new_whitelist)
            set_of_old_readable_plats = set()
            set_of_old_writable_plats = set()
            for plat, plat_attrs in old_whitelist.iteritems():
                if plat in old_data_plats:
                    for plat_key, attr_attrs in plat_attrs.iteritems():
                        toadd = (plat, plat_key)
                        set_of_old_readable_plats.add(toadd)
                        if 'derived' not in attr_attrs:
                            set_of_old_writable_plats.add(toadd)

            set_of_new_readable_plats = set()
            set_of_new_writable_plats = set()
            for plat, plat_attrs in new_whitelist.iteritems():
                if plat in new_data_plats:
                    for plat_key, attr_attrs in plat_attrs.iteritems():
                        toadd = (plat, plat_key)
                        set_of_new_readable_plats.add(toadd)
                        if 'derived' not in attr_attrs:
                            set_of_new_writable_plats.add(toadd)

            should_reindex = False
            if set_of_new_readable_plats - set_of_old_readable_plats:
                TRACE('Updating rows because readable attrs have changed')
                should_reindex = True
                trans.reset_local_ctimes()
            new_writable_attrs = set_of_new_writable_plats - set_of_old_writable_plats
            if new_writable_attrs:
                self.writable_attrs = defaultdict(set)
                for plat, plat_key in new_writable_attrs:
                    self.writable_attrs[plat].add(plat_key)

                trans.move_entries_with_new_writable_attrs_to_reconstruct()
            trans.set_config_key(CONFIG_ATTRS_DATA_PLATS, list(new_data_plats))
            trans.set_config_key(CONFIG_ATTRS_WHITELIST, dict(new_whitelist))
            return should_reindex

    @handle_exceptions_ex(return_value=False)
    def _db_has_new_writable_attrs(self, attrs_str):
        attr_dict = Attributes.unmarshal(attrs_str).attr_dict
        return any((any((k in plat_attrs for k in self.writable_attrs.get(plat, ()))) for plat, plat_attrs in attr_dict.iteritems()))

    @handle_exceptions_ex(return_value=False)
    def _db_is_bad_attr(self, attrs_str):
        attr_dict = Attributes.unmarshal(attrs_str).attr_dict
        return any((len(val.get('data', '')) > 340 for val in itertools.chain(*[ attr_dict.get(platform, frozendict()).itervalues() for platform in self._reset_attr_platforms ])))

    @handle_exceptions_ex(return_value_factory=lambda self, n: n)
    def _db_make_good_attr(self, attrs_str):
        attrs = Attributes.unmarshal(attrs_str)
        attr_dict = unfreeze_attr_dict(attrs.attr_dict)
        for platform in self._reset_attr_platforms:
            for key, val in attr_dict[platform].iteritems():
                if len(val.get('data', '')) > 340:
                    val['data'] = val['data'][:340]

        return attrs.copy(attr_dict=attr_dict).marshal()

    def reset_attrs_larger_than_255_on_files(self, platforms):
        self._reset_attr_platforms = platforms
        try:
            with self.write_lock() as trans:
                curs = trans.sqlite_cursor()
                curs.execute('UPDATE file_journal SET local_attrs = make_good_attr(local_attrs),' + 'local_ctime = 0 WHERE local_sjid IS NOT NULL AND is_bad_attr(local_attrs)')
        finally:
            self._reset_attr_platforms = None

    def quota_changed(self):
        return self.upload_clear_retry_map(UPLOAD_QUOTA_CODE)

    def tracked_ns(self, ns):
        with self.read_lock():
            return ns in self.root_ns_to_mount_table or any((mt.ns_is_mounted(ns) for mt in self.root_ns_to_mount_table.itervalues()))

    def refilter_queues(self):
        with self.write_lock() as trans:
            trans.refilter_queues()

    def clear_queues(self):
        with self.write_lock() as trans:
            trans.clear_queues()

    @classmethod
    def deleted_details(cls, server_path, **kw):
        return FastDetails(server_path=server_path, size=(-1), blocklist='', mtime=(-1), ctime=(-1), dir=0, machine_guid=None, attrs=FrozenAttributes(), **kw)

    @classmethod
    def directory_details(cls, server_path, **kw):
        if 'attrs' not in kw:
            kw['attrs'] = FrozenAttributes()
        if 'machine_guid' not in kw:
            kw['machine_guid'] = None
        if 'ctime' not in kw:
            kw['ctime'] = long(time.time())
        if 'mtime' not in kw:
            kw['mtime'] = kw['ctime']
        return FastDetails(server_path=server_path, size=0, dir=1, blocklist='', **kw)

    @staticmethod
    def is_consistent_updated(updated_details, file_journal_entry):
        if updated_details:
            if not file_journal_entry:
                return False
            if file_journal_entry[LOCAL_SJID_COL] is not None and file_journal_entry[LOCAL_SJID_COL] <= 0:
                pass
            if file_journal_entry[UPDATED_SJID_COL] is None:
                return False
            for key in FileJournalRowLogic.FILE_DETAIL_COLS:
                if key == 'filename':
                    if file_journal_entry[UPDATED_FILENAME_COL] != updated_details.server_path.basename:
                        return False
                elif file_journal_entry['updated_%s' % key] != getattr(updated_details, key):
                    return False

        return True

    @staticmethod
    def is_consistent_pending(pending_details, file_journal_entry):
        if not pending_details:
            return True
        if not file_journal_entry:
            return False
        if file_journal_entry[LOCAL_SJID_COL] is None:
            return False
        if file_journal_entry[LOCAL_SJID_COL] > 0:
            return False
        mr = getattr(pending_details, 'mount_request', None)
        if type(mr) is tuple:
            if mr[0] not in (MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT):
                return False
            if mr[0] == MOUNT_REQUEST_MOUNT and mr[1] != file_journal_entry[EXTRA_PENDING_DETAILS_COL]['mount_request']:
                return False
        elif mr is not None:
            return False
        return all((file_journal_entry[k] == (getattr(pending_details, FileJournalRowLogic.FILE_DETAIL_COLS[i], None) if k != LOCAL_FILENAME_COL else (pending_details.server_path.basename if pending_details.server_path else None)) for i, k in enumerate(FileJournalRowLogic.LOCAL_FILE_DETAIL_COLS) if k != LOCAL_SJID_COL))

    @classmethod
    def check_full_consistency(cls, currently_pending_details, currently_conflicted_details, currently_updated_details, ent):
        assert_(lambda : cls.is_consistent_updated(currently_updated_details, ent), 'Updated details and database out of sync: %r vs %r', currently_updated_details, dict(ent) if ent else ent)
        assert_(lambda : not (currently_pending_details and currently_conflicted_details), 'Both pending details and conflicted details exist! %r vs %r', currently_pending_details, currently_conflicted_details)
        assert_(lambda : cls.is_consistent_pending(currently_pending_details or currently_conflicted_details, ent), 'Pending details and database out of sync: %r vs %r', currently_pending_details or currently_conflicted_details, dict(ent) if ent else ent)

    @classmethod
    def _get_updated_host_id(cls, row):
        try:
            return row[UPDATED_HOST_ID_COL]
        except (KeyError, IndexError):
            return None

    @classmethod
    def _get_local_host_id(cls, row):
        try:
            return row[LOCAL_HOST_ID_COL]
        except (KeyError, IndexError):
            return None

    @classmethod
    def _get_updated_timestamp(cls, row):
        try:
            return row[UPDATED_TIMESTAMP_COL]
        except (KeyError, IndexError):
            return None

    @classmethod
    def _get_local_timestamp(cls, row):
        try:
            return row[LOCAL_TIMESTAMP_COL]
        except (KeyError, IndexError):
            return None

    @classmethod
    def _updated_details_from_ent(cls, row):
        return updated_details_from_entry(row)

    def _pending_details_from_ent(self, newent):
        sp = ServerPath(newent[PARENT_PATH_COL], lowered=True).join(newent[LOCAL_FILENAME_COL])
        mount_request = newent[EXTRA_PENDING_DETAILS_COL]['mount_request']
        mount_request = self._calc_mount_request(sp, mount_request)
        return FastDetails(server_path=sp, blocklist=newent[LOCAL_BLOCKLIST_COL], size=newent[LOCAL_SIZE_COL], mtime=newent[LOCAL_MTIME_COL], dir=newent[LOCAL_DIR_COL], attrs=newent[LOCAL_ATTRS_COL], mount_request=mount_request, parent_blocklist=(newent[EXTRA_PENDING_DETAILS_COL]['parent'] or frozendict()).get('blocklist'), parent_attrs=(newent[EXTRA_PENDING_DETAILS_COL]['parent'] or frozendict()).get('attrs'), machine_guid=newent[LOCAL_MACHINE_GUID_COL], guid=newent.get(LOCAL_GUID_COL), parent_guid_rev=newent.get(LOCAL_GUID_SYNCED_GUID_REV_COL))

    def _calc_mount_request(self, sp, mount_request, lower = True):
        is_mounted_at = self._target_ns(sp, lower=lower)
        if not mount_request and is_mounted_at:
            mr = (MOUNT_REQUEST_UNMOUNT, is_mounted_at)
        elif mount_request and mount_request != is_mounted_at:
            mr = (MOUNT_REQUEST_MOUNT, mount_request)
        else:
            mr = None
        return mr

    def _run_mount_request_fixup(self, trans, mount_logic):
        cursor = trans.sqlite_cursor()
        if type(mount_logic) is NamespaceMovedMountLogic:
            root_ns, moved_ns, old_mount_point, new_mount_point = mount_logic.details()
            spl = ServerPath.from_ns_rel(root_ns, old_mount_point.lower(), lowered=True)
            pending_deets = trans.pattached.get_batch([spl], lower=False)
            if pending_deets:
                pending_deets, = pending_deets
                row = cursor.execute('SELECT extra_pending_details FROM file_journal WHERE server_path = ?', (unicode(spl),)).fetchone()
                trans.pattached.add_batch([(pending_deets.copy(mount_request=self._calc_mount_request(spl, row[0]['mount_request'])), 0)])
            spl = ServerPath.from_ns_rel(root_ns, new_mount_point.lower(), lowered=True)
            pending_deets = trans.pattached.get_batch([spl], lower=False)
            if pending_deets:
                pending_deets, = pending_deets
                row = cursor.execute('SELECT extra_pending_details FROM file_journal WHERE server_path = ?', (unicode(spl),)).fetchone()
                trans.pattached.add_batch([(pending_deets.copy(mount_request=self._calc_mount_request(spl, row[0]['mount_request'])), 0)])
        else:
            root_ns, rel, unmount_ns, is_destructive, to_mount_ns = mount_logic.details()
            spl = ServerPath.from_ns_rel(root_ns, rel.lower(), lowered=True)
            pending_deets = trans.pattached.get_batch([spl], lower=False)
            if pending_deets:
                pending_deets, = pending_deets
                row = cursor.execute('SELECT extra_pending_details FROM file_journal WHERE server_path = ?', (unicode(spl),)).fetchone()
                trans.pattached.add_batch([(pending_deets.copy(mount_request=self._calc_mount_request(spl, row[0]['mount_request'])), 0)])

    def _change_memory_mount_tables(self, mount_logic):
        if type(mount_logic) is NamespaceMovedMountLogic:
            root_ns, moved_ns, old_mount_point, new_mount_point = mount_logic.details()
            mt = self.root_ns_to_mount_table[root_ns]
            self.last_revision[moved_ns] = -1
            mt.unmount(old_mount_point)
            mt.mount(new_mount_point, moved_ns)
            return ((ServerPath.from_ns_rel(root_ns, old_mount_point),
              moved_ns,
              True,
              None), (ServerPath.from_ns_rel(root_ns, new_mount_point),
              None,
              False,
              moved_ns))
        else:
            root_ns, rel, unmount_ns, is_destructive, to_mount_ns = mount_logic.details()
            mt = self.root_ns_to_mount_table[root_ns]
            TRACE('Changing mount tables: %r', mount_logic.details())
            if unmount_ns:
                TRACE('DELETING from self.last_revision, %r', unmount_ns)
                del self.last_revision[unmount_ns]
                mt.unmount(rel)
            if to_mount_ns:
                self.last_revision[to_mount_ns] = -1
                mt.mount(rel, to_mount_ns)
            return ((ServerPath.from_ns_rel(root_ns, rel),
              unmount_ns,
              is_destructive,
              to_mount_ns),)

    def _db_mount_transition(self, trans, from_root_lowered, to_root_lowered, queuers, destructive = False, prune_in = ()):
        num_statements = 0
        cursor = trans.sqlite_cursor()
        read_cursor = cursor.connection.cursor()
        read_cursor.row_factory = dict_like_row
        mps = self.cls_db_get_mount_points(read_cursor)
        entries = trans.do_magic_shared_folder_query(from_root_lowered[:-1], to_root_lowered[:-1])
        fjrl = FileJournalRowLogic(mps)
        directory_not_kill = set()
        for ent, current_new_row in entries:
            assert_(lambda : self.is_valid_filejournal_entry(ent), 'Invalid file journal entry! %s %r', self.why_isnt_valid_filejournal_entry(ent), ent)
            old_spl = ServerPath(ent[SERVER_PATH_COL], lowered=True)
            if ent[UPDATED_SJID_COL] is not None:
                queuers.pre_mount_remove_updated(old_spl)
            fjrl.delete_entry(ent)
            if ent[LOCAL_SJID_COL] is None:
                continue
            cs_sp = server_path_join_unicode(ent[PARENT_PATH_COL], ent[LOCAL_FILENAME_COL])
            new_spu = u'%s%s' % (to_root_lowered, cs_sp[len(from_root_lowered):])
            new_spul = new_spu.lower()
            new_pp = server_path_dirname_unicode(new_spul)
            new_row = FileJournalRowLogic.new_ent(new_spul)
            if ent[LOCAL_SIZE_COL] >= 0:
                FileJournalRowLogic.set_pending_details(new_row, FastDetails(attrs=ent[LOCAL_ATTRS_COL], blocklist=ent[LOCAL_BLOCKLIST_COL], ctime=ent[LOCAL_CTIME_COL], dir=ent[LOCAL_DIR_COL], machine_guid=ent[LOCAL_MACHINE_GUID_COL], mtime=ent[LOCAL_MTIME_COL], server_path=ServerPath(new_spu), size=ent[LOCAL_SIZE_COL]), remote_guid=ent[LOCAL_GUID_COL], remote_guid_parent_rev=ent[LOCAL_GUID_SYNCED_GUID_REV_COL])
            if current_new_row and current_new_row[LOCAL_SJID_COL] is not None:
                report_bad_assumption("'transition_to' row exists in database with local details! from: %r, to: %r" % (ent, dict(current_new_row)))
            if ent[LOCAL_SJID_COL] > 0:
                if not destructive or new_spul in directory_not_kill:
                    if not destructive:
                        directory_not_kill.add(new_pp)
                    extra_details = ExtraPendingDetails(recommit=True)
                    if current_new_row:
                        new_row.update({LOCAL_SJID_COL: 0,
                         EXTRA_PENDING_DETAILS_COL: extra_details,
                         LOCAL_HOST_ID_COL: None,
                         UPDATED_HOST_ID_COL: self._get_updated_host_id(current_new_row),
                         LOCAL_TIMESTAMP_COL: None,
                         UPDATED_TIMESTAMP_COL: self._get_updated_timestamp(current_new_row),
                         UPDATED_BLOCKLIST_COL: current_new_row[UPDATED_BLOCKLIST_COL],
                         UPDATED_SIZE_COL: current_new_row[UPDATED_SIZE_COL],
                         UPDATED_MTIME_COL: current_new_row[UPDATED_MTIME_COL],
                         UPDATED_DIR_COL: current_new_row[UPDATED_DIR_COL],
                         UPDATED_ATTRS_COL: current_new_row[UPDATED_ATTRS_COL],
                         UPDATED_SJID_COL: current_new_row[UPDATED_SJID_COL],
                         UPDATED_FILENAME_COL: current_new_row[UPDATED_FILENAME_COL],
                         UPDATED_GUID_COL: current_new_row[UPDATED_GUID_COL],
                         UPDATED_GUID_REV_COL: current_new_row[UPDATED_GUID_REV_COL]})
                    else:
                        new_row.update({LOCAL_SJID_COL: 0,
                         EXTRA_PENDING_DETAILS_COL: extra_details,
                         LOCAL_HOST_ID_COL: None,
                         UPDATED_HOST_ID_COL: None,
                         LOCAL_TIMESTAMP_COL: None,
                         UPDATED_TIMESTAMP_COL: None,
                         UPDATED_BLOCKLIST_COL: None,
                         UPDATED_SIZE_COL: None,
                         UPDATED_MTIME_COL: None,
                         UPDATED_DIR_COL: None,
                         UPDATED_ATTRS_COL: None,
                         UPDATED_SJID_COL: None,
                         UPDATED_FILENAME_COL: None})
                else:
                    new_row.update({UPDATED_BLOCKLIST_COL: '',
                     UPDATED_SIZE_COL: -1,
                     UPDATED_MTIME_COL: -1,
                     UPDATED_DIR_COL: 0,
                     UPDATED_ATTRS_COL: FrozenAttributes(),
                     UPDATED_SJID_COL: 1,
                     UPDATED_FILENAME_COL: ent[LOCAL_FILENAME_COL],
                     LOCAL_SJID_COL: 1,
                     LOCAL_HOST_ID_COL: None,
                     UPDATED_HOST_ID_COL: None,
                     LOCAL_TIMESTAMP_COL: None,
                     UPDATED_TIMESTAMP_COL: None,
                     EXTRA_PENDING_DETAILS_COL: None})
            else:
                queuers.pre_mount_remove_pending(old_spl)
                if ent[LOCAL_SIZE_COL] < 0:
                    if current_new_row:
                        assert_(lambda : new_row[LOCAL_BLOCKLIST_COL] is None)
                        new_row.update({UPDATED_HOST_ID_COL: self._get_updated_host_id(current_new_row),
                         UPDATED_TIMESTAMP_COL: self._get_updated_timestamp(current_new_row),
                         UPDATED_BLOCKLIST_COL: current_new_row[UPDATED_BLOCKLIST_COL],
                         UPDATED_SIZE_COL: current_new_row[UPDATED_SIZE_COL],
                         UPDATED_MTIME_COL: current_new_row[UPDATED_MTIME_COL],
                         UPDATED_DIR_COL: current_new_row[UPDATED_DIR_COL],
                         UPDATED_ATTRS_COL: current_new_row[UPDATED_ATTRS_COL],
                         UPDATED_SJID_COL: current_new_row[UPDATED_SJID_COL],
                         UPDATED_FILENAME_COL: current_new_row[UPDATED_FILENAME_COL],
                         UPDATED_GUID_COL: current_new_row[UPDATED_GUID_COL],
                         UPDATED_GUID_REV_COL: current_new_row[UPDATED_GUID_REV_COL],
                         LOCAL_SJID_COL: None,
                         LOCAL_HOST_ID_COL: None,
                         LOCAL_TIMESTAMP_COL: None,
                         EXTRA_PENDING_DETAILS_COL: None})
                    else:
                        new_row = None
                else:
                    if destructive:
                        directory_not_kill.add(new_pp)
                    extra_details = ent[EXTRA_PENDING_DETAILS_COL].copy(parent=None)
                    if current_new_row:
                        new_row.update({LOCAL_SJID_COL: 0,
                         EXTRA_PENDING_DETAILS_COL: extra_details,
                         UPDATED_HOST_ID_COL: self._get_updated_host_id(current_new_row),
                         UPDATED_TIMESTAMP_COL: self._get_updated_timestamp(current_new_row),
                         UPDATED_BLOCKLIST_COL: current_new_row[UPDATED_BLOCKLIST_COL],
                         UPDATED_SIZE_COL: current_new_row[UPDATED_SIZE_COL],
                         UPDATED_MTIME_COL: current_new_row[UPDATED_MTIME_COL],
                         UPDATED_DIR_COL: current_new_row[UPDATED_DIR_COL],
                         UPDATED_ATTRS_COL: current_new_row[UPDATED_ATTRS_COL],
                         UPDATED_SJID_COL: current_new_row[UPDATED_SJID_COL],
                         UPDATED_FILENAME_COL: current_new_row[UPDATED_FILENAME_COL],
                         UPDATED_GUID_COL: current_new_row[UPDATED_GUID_COL],
                         UPDATED_GUID_REV_COL: current_new_row[UPDATED_GUID_REV_COL]})
                    else:
                        new_row.update({LOCAL_SJID_COL: 0,
                         LOCAL_HOST_ID_COL: None,
                         UPDATED_HOST_ID_COL: None,
                         LOCAL_TIMESTAMP_COL: None,
                         UPDATED_TIMESTAMP_COL: None,
                         EXTRA_PENDING_DETAILS_COL: extra_details,
                         UPDATED_BLOCKLIST_COL: None,
                         UPDATED_SIZE_COL: None,
                         UPDATED_MTIME_COL: None,
                         UPDATED_DIR_COL: None,
                         UPDATED_ATTRS_COL: None,
                         UPDATED_SJID_COL: None,
                         UPDATED_FILENAME_COL: None})
            if new_row:
                if ent[LOCAL_SJID_COL] > 0 or ent[EXTRA_PENDING_DETAILS_COL].recommit:
                    for prune_spl in prune_in:
                        if prune_spl.is_parent_of(old_spl) or prune_spl == old_spl:
                            new_row.update({UPDATED_BLOCKLIST_COL: '',
                             UPDATED_SIZE_COL: -1,
                             UPDATED_MTIME_COL: -1,
                             UPDATED_DIR_COL: 0,
                             UPDATED_ATTRS_COL: FrozenAttributes(),
                             UPDATED_SJID_COL: 1,
                             UPDATED_FILENAME_COL: ent[LOCAL_FILENAME_COL],
                             LOCAL_SJID_COL: 1,
                             EXTRA_PENDING_DETAILS_COL: None})
                            break

                if new_row[LOCAL_SJID_COL] is not None and new_row[LOCAL_SJID_COL] == 0:
                    queuers.to_add_pending(self._pending_details_from_ent(new_row))
                elif new_row[UPDATED_SJID_COL]:
                    queuers.to_add_updated(self._updated_details_from_ent(new_row))
                if current_new_row:
                    fjrl.update_entry(current_new_row, new_row)
                else:
                    fjrl.insert_entry(new_row)
            elif current_new_row:
                fjrl.delete_entry(current_new_row)
            if len(fjrl) >= 500:
                num_statements += fjrl.execute_da_sql(cursor)
                fjrl = FileJournalRowLogic(mps)

        num_statements += fjrl.execute_da_sql(cursor)
        return num_statements

    def set_updated_batch(self, new_details, update_last_sjid = True):
        with self.write_lock() as trans:
            self.set_updated_batch_internal(trans, new_details, update_last_sjid=update_last_sjid)
        if update_last_sjid:
            self.remote_files_event_callbacks.run_handlers(new_details)

    def _process_mount_logic(self, trans, mount_logic):
        assert_(self._is_write_locked, 'you must have the giant lock when calling this.')
        trans.flush()
        if not mount_logic:
            report_bad_assumption('invalid mount logic in the extra queue')
            return
        the_queuer = DBMountTransitionQueuer(self)
        mount_logic.execute_da_sql(trans, the_queuer)
        the_queuer.run_pre_mount(trans)
        trans_ = self._change_memory_mount_tables(mount_logic)
        the_queuer.run_adds(trans)
        the_queuer.run_removes(trans)
        self._run_mount_request_fixup(trans, mount_logic)
        for a in trans_:
            self.mount_callbacks.run_handlers(*a)

        trans.flush()

    def _process_single_updated_entry(self, trans, ent, updated_details, update_last_sjid = True):
        if updated_details.sjid <= 1:
            report_bad_assumption('Invalid sjid from the server: %r %r' % (updated_details.sjid, updated_details.server_path))
            return False
        ciserver_path = updated_details.server_path.lower()
        ciserver_pathu = unicode(ciserver_path)
        ns, rel = ciserver_path.ns_rel()
        if ns not in self.last_revision:
            TRACE("!! Ignoring %r:%r because we aren't watching that namespace", updated_details.server_path, updated_details.sjid)
            return False
        if not self.is_valid_sjid(ns, updated_details.sjid):
            report_bad_assumption('Bad sjid %r for ns: %r' % (updated_details.sjid, ns))
        if update_last_sjid:
            trans.update_last_revision(ns, updated_details.sjid)
        if not ent:
            if updated_details.size >= 0:
                ent = FileJournalRowLogic.new_ent(ciserver_pathu)
                FileJournalRowLogic.set_updated_details(ent, updated_details)
                TRACE('Creating new entry for updated file %r:%r', updated_details, ent)
                trans.insert_entry(ent)
                return True
            else:
                TRACE('Ignoring entry for updated/deleted but not pre-existing file %r', updated_details)
                return False
        if ent[UPDATED_SJID_COL] is not None and ent[UPDATED_SJID_COL] >= updated_details.sjid:
            TRACE('File entry in local database is newer or the same as what the server has just given us: %r vs %r', updated_details, dict(ent))
            if ent[UPDATED_SJID_COL] == updated_details.sjid:
                updated_attrs = ent[UPDATED_ATTRS_COL]
                if updated_attrs != updated_details.attrs:
                    TRACE('Local updated entry had bad attrs... %r, local %r vs remote %r', updated_details.server_path, updated_attrs, updated_details.attrs)
                    if any((local_plat not in updated_details.attrs.attr_dict for local_plat in updated_attrs.attr_dict)):
                        report_bad_assumption("Entries in what we thought was the remote_attrs that weren't in remote_attrs for same sjid: %r, %r vs %r" % (updated_details.sjid, updated_attrs.attr_dict, updated_details.attrs.attr_dict))
                    newent = dict(ent)
                    newent[UPDATED_ATTRS_COL] = updated_details.attrs
                    trans.update_entry(ent, newent)
            else:
                report_bad_assumption('Server has sent out of order updated entries, previous: %r, now: %r' % (ent[UPDATED_SJID_COL], updated_details.sjid))
            return False
        if ent[LOCAL_SJID_COL] is not None and ent[LOCAL_SJID_COL] >= updated_details.sjid:
            newent = None
            if ent[LOCAL_SJID_COL] == updated_details.sjid:
                TRACE('Updated file %r (%r vs %r) is the same as local file', updated_details.server_path, updated_details.sjid, ent[LOCAL_SJID_COL])
                local_attrs = ent[LOCAL_ATTRS_COL]
                if local_attrs != updated_details.attrs:
                    if any((local_plat not in updated_details.attrs.attr_dict for local_plat in local_attrs.attr_dict)):
                        report_bad_assumption("Entries in local_attrs that weren't in remote_attrs for same sjid: %r, %r vs %r" % (updated_details.sjid, ent[LOCAL_ATTRS_COL].attr_dict, updated_details.attrs.attr_dict))
                    newent = dict(ent)
                    newent[LOCAL_ATTRS_COL] = updated_details.attrs.copy(data_plats=ent[LOCAL_ATTRS_COL].data_plats)
                host_id = getattr(updated_details, 'host_id', None)
                ent_host_id = self._get_updated_host_id(ent)
                assert_(lambda : ent_host_id is None or host_id is None or host_id == ent_host_id, 'host_id from server does not equal host_id in client %r vs %r, %r', host_id, ent_host_id, ent)
                if ent_host_id is None and host_id is not None:
                    newent = newent or dict(ent)
                    newent[LOCAL_HOST_ID_COL] = host_id
                timestamp = getattr(updated_details, 'ts', None)
                if timestamp is not None:
                    newent = newent or dict(ent)
                    newent[LOCAL_TIMESTAMP_COL] = timestamp
            elif ent[LOCAL_SJID_COL] > updated_details.sjid:
                TRACE('Updated file %r (%r vs %r) is older than local file', updated_details.server_path, updated_details.sjid, ent[LOCAL_SJID_COL])
            if ent[UPDATED_SJID_COL] is not None:
                report_bad_assumption('Server has sent out of order updated entries, previous: %r, now: %r' % (ent[LOCAL_SJID_COL], updated_details.sjid))
                newent = newent or dict(ent)
                FileJournalRowLogic.clear_updated_details(newent)
            if newent:
                trans.update_entry(ent, newent)
            return False
        if ent[LOCAL_SJID_COL] is None and updated_details.size < 0:
            trans.delete_entry(ent)
            TRACE('Remote file is deleted and was never reconstructed locally, skipping. %r', updated_details)
            return True
        compare_attrs_synced = ent[LOCAL_ATTRS_COL]
        if ent[LOCAL_SJID_COL] is not None and not ent[LOCAL_SJID_COL]:
            parent = propagate_none(lambda x: x.parent, ent.get(EXTRA_PENDING_DETAILS_COL))
            compare_attrs_synced = self.generate_attrs_for_compare(updated_details.attrs, compare_attrs_synced, first_local_edit=parent is None)
        if ent[LOCAL_SJID_COL] is not None and (ent[LOCAL_BLOCKLIST_COL],
         ent[LOCAL_SIZE_COL],
         ent[LOCAL_DIR_COL],
         ent[LOCAL_GUID_COL]) == (updated_details.blocklist,
         updated_details.size,
         updated_details.dir,
         getattr(updated_details, 'guid', None)) and compare_attrs_synced == updated_details.attrs:
            TRACE('Updated file %r is the same as local file (%r vs %r)', updated_details.server_path, updated_details, ent)
            if ent[LOCAL_SJID_COL] == 0 and ent[LOCAL_SIZE_COL] < 0:
                trans.delete_entry(ent)
                return True
            new_attrs = updated_details.attrs.copy(data_plats=compare_attrs_synced.data_plats)
            new_ent = dict(ent)
            new_ent[IS_CONFLICTED_COL] = False
            new_ent.update({LOCAL_ATTRS_COL: new_attrs,
             EXTRA_PENDING_DETAILS_COL: None,
             LOCAL_SJID_COL: updated_details.sjid,
             LOCAL_HOST_ID_COL: getattr(updated_details, 'host_id', None),
             LOCAL_TIMESTAMP_COL: getattr(updated_details, 'ts', None)})
            FileJournalRowLogic.clear_updated_details(new_ent)
            trans.update_entry(ent, new_ent)
            return True
        newent = dict(ent)
        FileJournalRowLogic.set_updated_details(newent, updated_details)
        trans.update_entry(ent, newent)
        return True

    def _process_updated_entries(self, trans, subset, update_last_sjid = True):
        server_path_iter = itertools.imap(operator.attrgetter('server_path'), subset)
        sp2info = dict(((ent[SERVER_PATH_COL], ent) for ent in trans.get_entries(server_path_iter)))
        assert_(lambda : trans.last_revisions() == self.last_revision, "backend doesn't match our internal cache: %r vs %r", trans.last_revisions(), self.last_revision)
        if not sp2info and all((updated_details.size < 0 for updated_details in subset)):
            if update_last_sjid:
                ns_to_max_sjids = defaultdict(lambda : -1)
                for updated_details in subset:
                    ns, _ = updated_details.server_path.ns_rel()
                    ns_to_max_sjids[ns] = max(ns_to_max_sjids[ns], updated_details.sjid)

                for ns, max_sjid in ns_to_max_sjids.iteritems():
                    trans.update_last_revision(ns, max_sjid)

            processed = [False] * len(subset)
        else:
            processed = []
            for updated_details in subset:
                ent = sp2info.get(unicode(updated_details.server_path.lower()))
                done = self._process_single_updated_entry(trans, ent, updated_details, update_last_sjid=update_last_sjid)
                processed.append(done)

        if update_last_sjid:
            self.last_revision = trans.last_revisions()
        return processed

    def set_updated_batch_internal(self, trans, new_details, update_last_sjid = True):
        details_in_sjid_order = new_details

        def _sort_key_updated_list(details):
            return (details.server_path.ns if details.server_path.ns not in self.root_ns_to_mount_table else sys.maxint, details.sjid)

        try:
            sort_method = details_in_sjid_order.sort
        except AttributeError:
            details_in_sjid_order = sorted(new_details, key=_sort_key_updated_list)
        else:
            sort_method(key=_sort_key_updated_list)

        cur_idx = 0
        ldiso = len(details_in_sjid_order)
        while cur_idx < ldiso:
            try:
                mount_logic = None
                required_unmounts = []
                for i in xrange(cur_idx, ldiso):
                    updated_details = details_in_sjid_order[i]
                    assert_(lambda : updated_details.dir in (0, 1), "'dir' attribute of input details had an invalite dir attribuite: %r", updated_details)
                    root_ns, rel = updated_details.server_path.ns_rel()
                    try:
                        mount_table = self.root_ns_to_mount_table[root_ns]
                    except KeyError:
                        pass
                    else:
                        at_ns = mount_table.is_mount_point(rel)
                        mount_request = getattr(updated_details, 'mount_request', None)
                        assert_(lambda : not mount_request or updated_details.dir, "Mount request on an entry that isn't a directory! %r", updated_details)
                        if at_ns == mount_request:
                            pass
                        elif at_ns and mount_request:
                            assert_(lambda : updated_details.dir)
                            mount_logic = DatabaseMountLogic(self, root_ns, rel, at_ns, False, mount_request)
                        elif at_ns:
                            if not updated_details.dir:
                                is_destructive = True
                            elif updated_details.dir == 1:
                                is_destructive = False
                            else:
                                report_bad_assumption('Hmm an unmount yet the details seem wrong: %r' % (updated_details,))
                            mount_logic = DatabaseMountLogic(self, root_ns, rel, at_ns, is_destructive, None)
                        elif mount_request:
                            current_mount_point = mount_table.ns_is_mounted(mount_request)
                            if current_mount_point:
                                row = trans.entry_with_target_ns(mount_request)
                                if row[UPDATED_SJID_COL] > 1:
                                    other_sjid = row[UPDATED_SJID_COL]
                                elif row[LOCAL_SJID_COL] > 1:
                                    other_sjid = row[LOCAL_SJID_COL]
                                elif row[LOCAL_SJID_COL] == 0 and row[EXTRA_PENDING_DETAILS_COL]['parent']:
                                    other_sjid = row[EXTRA_PENDING_DETAILS_COL]['parent']['sjid']
                                else:
                                    report_bad_assumption('Mounted path without server details!')
                                    other_sjid = None
                                if not other_sjid or updated_details.sjid > other_sjid:
                                    mount_logic = NamespaceMovedMountLogic(self, root_ns, mount_request, current_mount_point, rel)
                            else:
                                prune_list = []
                                for mount_rel, mount_ns in mount_table.child_mount_points(rel):
                                    prune_list.append(ServerPath.from_ns_rel(root_ns, mount_rel, lowered=True))
                                    required_unmounts.append(DatabaseMountLogic(self, root_ns, mount_rel, mount_ns, False, None))

                                mount_logic = DatabaseMountLogic(self, root_ns, rel, None, False, mount_request, prune_in=prune_list)

                    if mount_logic:
                        mount_at_idx = i
                        break
                else:
                    mount_at_idx = ldiso

                if cur_idx != mount_at_idx:
                    seq_of_details = details_in_sjid_order[cur_idx:mount_at_idx]
                    self._process_updated_entries(trans, seq_of_details, update_last_sjid=update_last_sjid)
                if not mount_logic:
                    assert_(lambda : mount_at_idx == ldiso, 'breaks in updated list are bad! %r vs %r', mount_at_idx, ldiso)
                    break
                for item in required_unmounts:
                    self._process_mount_logic(trans, item)

                cur_idx = mount_at_idx + 1
                processed = self._process_updated_entries(trans, [details_in_sjid_order[mount_at_idx]], update_last_sjid=update_last_sjid)[0]
                if processed:
                    self._process_mount_logic(trans, mount_logic)
            finally:
                TRACE('last_revision is now: %r', self.last_revision)

    def perform_upload(self, uploader, lim = None, priority_nses = (), retry_interval = None):
        with self.write_lock():
            uploadable = self.get_uploadable(lim=lim, priority_nses=priority_nses)
            self._handle_commit_results(uploader(uploadable), retry_interval=retry_interval)

    def handle_commit_results(self, results_and_details):
        with self.write_lock():
            report_bad_assumption('This method is deprecated and unsafe, please do not continue using this.')
            return self._handle_commit_results(results_and_details)

    def _handle_commit_results(self, results_and_details, retry_interval = None):
        server_path_map = {}
        possible_directory_not_empties = {}
        mount_logic = None
        for commit_result_name, extra, deets in self._normalize_commit_results(results_and_details):
            sp = deets.server_path
            currently_pending_details = self.get_uploading(sp)
            assert_(lambda : currently_pending_details == deets or commit_result_name == UPLOAD_SUCCESS_CODE and extra[3] is not None, 'Currently pending details have changed from what was committed! %r vs %r', currently_pending_details, deets)
            if commit_result_name == UPLOAD_SUCCESS_CODE:
                sjid, guid, guid_rev, mount_logic = extra
                deets = deets.copy(sjid=sjid, guid=guid, guid_rev=guid_rev)
            elif commit_result_name in (UPLOAD_CONFLICT_CODE, UPLOAD_IGNORED_CODE, UPLOAD_GUID_CONFLICT_CODE):
                deets = deets.copy(sjid=commit_result_name)
            if commit_result_name in [UPLOAD_SUCCESS_CODE,
             UPLOAD_CONFLICT_CODE,
             UPLOAD_IGNORED_CODE,
             UPLOAD_GUID_CONFLICT_CODE]:
                server_path_map[unicode(sp).lower()] = deets
            elif commit_result_name == UPLOAD_DIRECTORY_NOT_EMPTY_CODE:
                possible_directory_not_empties[sp.lower()] = deets
            else:
                if commit_result_name == UPLOAD_NO_ACCESS_CODE:
                    if getattr(deets, 'mount_request', (2,))[0] not in (MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT):
                        report_bad_assumption("'no access' without a mount request: %r" % (deets,))
                    else:
                        self._add_uploadable(currently_pending_details.copy(mount_request=None))
                try:
                    backoff_time = self.upload_retry(sp, commit_result_name, interval=retry_interval)
                except Exception:
                    unhandled_exc_handler()
                else:
                    TRACE('Commit for %r returned %s; backing off for %s sec', sp, commit_result_name, '%.1f' % backoff_time if backoff_time else 'n/a')

        assert_(lambda : mount_logic is None or len(server_path_map) == 1, 'Mounting but we had more than one thing to process?? %r %r', mount_logic, server_path_map)
        self._handle_conflict_and_successfuls(server_path_map, mount_logic, retry_interval=retry_interval)
        self._handle_directory_not_empties(possible_directory_not_empties, retry_interval=retry_interval)

    def _normalize_commit_results(self, results_and_details):
        for commit_result, deets in results_and_details:
            commit_result_name = commit_result[0] if hasattr(commit_result, '__getitem__') and not isinstance(commit_result, basestring) else commit_result
            commit_result_for_guid_off = None
            sjid = None
            guid = None
            guid_rev = None
            if type(commit_result_name) in (int, long):
                sjid = commit_result_name
                commit_result_name = UPLOAD_IGNORED_CODE if commit_result_name == -1 else UPLOAD_SUCCESS_CODE
                commit_result_for_guid_off = 1
            elif commit_result_name == UPLOAD_SUCCESS_CODE:
                sjid = commit_result[1]
                commit_result_for_guid_off = 2
            if commit_result_for_guid_off is not None:
                try:
                    guid = commit_result[commit_result_for_guid_off]
                    guid_rev = commit_result[commit_result_for_guid_off + 1]
                except (TypeError, IndexError):
                    assert_(lambda : guid is None, 'Guid in commit_result without guid_rev: %r', commit_result)

            mr = getattr(deets, 'mount_request', None)
            assert_(lambda : not mr or mr[0] in (MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT), 'mount_request must be in (%r, %r): %r %r %r', MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT, mr, commit_result_name, deets)
            sp = deets.server_path
            if commit_result_name == UPLOAD_IGNORED_CODE and mr:
                report_bad_assumption('Cannot ignore on a mount_request: %r :%r!' % (sp, deets.mount_request))
                continue
            if commit_result_name == UPLOAD_SUCCESS_CODE:
                assert_(lambda : FileCache.is_valid_sjid(sp.ns, sjid), 'Invalid sjid from server: %r %r!', sjid, sp)
                mount_logic = None
                if mr:
                    if mr[0] == 0:
                        details_to_commit = self.deleted_details(deets.server_path, sjid=sjid)
                        mount_logic = DatabaseMountLogic(self, deets.server_path.ns, deets.server_path.rel, mr[1], deets.size < 0, None)
                    else:
                        details_to_commit = FastDetails(server_path=deets.server_path, size=0, mtime=int(time.time()), ctime=int(time.time()), attrs=FrozenAttributes(), blocklist='', dir=1, mount_request=mr)
                        mount_logic = DatabaseMountLogic(self, deets.server_path.ns, deets.server_path.rel, None, False, mr[1])
                else:
                    details_to_commit = deets
                yield (commit_result_name, (sjid,
                  guid,
                  guid_rev,
                  mount_logic), details_to_commit)
            else:
                yield (commit_result_name, None, deets)

    def _handle_conflict_and_successfuls(self, server_path_map, mount_logic, retry_interval = None):
        assert_(lambda : mount_logic is None or len(server_path_map) == 1, "mount logic can only be set when we're processing a single entry! %r, %r", mount_logic, server_path_map)
        if not server_path_map:
            return
        with self.write_lock() as trans:
            processed = []
            updated_guids_to_remove = []
            for ent in trans.get_entries(server_path_map, lower=False):
                just_committed_details = server_path_map[ent[SERVER_PATH_COL]]
                fn = self._handle_conflicted_and_ignored if just_committed_details.sjid in (UPLOAD_CONFLICT_CODE, UPLOAD_IGNORED_CODE) else (self._handle_guid_conflicted if just_committed_details.sjid == UPLOAD_GUID_CONFLICT_CODE else self._pending_to_active_committed)
                fn(trans, just_committed_details, ent, processed, mount_logic, updated_guids_to_remove=updated_guids_to_remove)

            guid_to_d = {j.guid:j for j in updated_guids_to_remove if j.guid is not None}
            entries = trans.entries_by_remote_dropbox_guid_batch(guid_to_d)
            for ent in entries:
                d = guid_to_d[ent[UPDATED_GUID_COL]]
                assert_(lambda : ent[UPDATED_SJID_COL] is not None, 'Updated SJID should not be none if ' + 'Updated GUID is not None %r %r', ent, d)
                if ent[UPDATED_GUID_REV_COL] <= d.guid_rev:
                    TRACE('Clearing updated entry for guid %r, ' + 'because guid rev is newer: %r vs %r, %r, %r', d.guid, ent[UPDATED_GUID_REV_COL], d.guid_rev, ent, d)
                    if ent[LOCAL_SJID_COL] is not None:
                        new_ent = dict(ent)
                        FileJournalRowLogic.clear_updated_details(new_ent)
                        trans.update_entry(ent, new_ent)
                    else:
                        trans.delete_entry(ent)

            if processed[0] and mount_logic:
                self._process_mount_logic(trans, mount_logic)

    def _handle_conflicted_and_ignored(self, trans, just_committed_details, ent, processed, mount_logic, *n, **kw):
        assert_(lambda : not (ent[UPDATED_SJID_COL] is not None and (ent[UPDATED_BLOCKLIST_COL],
         ent[UPDATED_SIZE_COL],
         ent[UPDATED_DIR_COL],
         ent[UPDATED_ATTRS_COL]) == (just_committed_details.blocklist,
         just_committed_details.size,
         just_committed_details.dir,
         just_committed_details.attrs)), 'Conflicted or uncommitted file is the same as Updated %r, making active', just_committed_details.server_path)
        processed.append(True)
        if just_committed_details.size < 0:
            TRACE('Committed useless entry: %r', just_committed_details)
            if not ent[EXTRA_PENDING_DETAILS_COL]['parent']:
                if ent[UPDATED_SJID_COL] is None:
                    trans.delete_entry(ent)
                else:
                    new_ent = dict(ent)
                    FileJournalRowLogic.clear_local_details(new_ent)
                    trans.update_entry(ent, new_ent)
            else:
                new_ent = dict(ent)
                new_ent[IS_CONFLICTED_COL] = True
                trans.update_entry(ent, new_ent)
        elif just_committed_details.sjid == UPLOAD_IGNORED_CODE:
            if ent[UPDATED_SJID_COL]:
                report_bad_assumption('File was ignored by server yet we had an updated entry for it? %r:%r' % (just_committed_details, dict(ent)))
                new_ent = dict(ent)
                FileJournalRowLogic.clear_local_details(new_ent)
                trans.update_entry(ent, new_ent)
            else:
                trans.delete_entry(ent)
        elif just_committed_details.sjid == UPLOAD_CONFLICT_CODE:
            new_ent = dict(ent)
            new_ent[IS_CONFLICTED_COL] = True
            trans.update_entry(ent, new_ent)
        else:
            report_bad_assumption('Invalid sjid value %r for %r' % (just_committed_details.sjid, just_committed_details.server_path))

    def _handle_guid_conflicted(self, trans, just_commited_details, ent, processed, mount_logic, *n, **kw):
        new_ent = dict(ent)
        new_ent[IS_GUID_CONFLICTED_COL] = True
        trans.update_entry(ent, new_ent)
        processed.append(True)

    def _pending_to_active_committed(self, trans, just_committed_details, ent, processed, mount_logic, updated_guids_to_remove, *n, **kw):
        assert_(lambda : ent[LOCAL_SJID_COL] == 0, 'Local SJID changed while committing %r', ent)
        committed_details_are_equal = (ent[LOCAL_BLOCKLIST_COL],
         ent[LOCAL_SIZE_COL],
         ent[LOCAL_DIR_COL],
         ent[LOCAL_ATTRS_COL]) == (just_committed_details.blocklist,
         just_committed_details.size,
         just_committed_details.dir,
         just_committed_details.attrs)
        new_ent = dict(ent)
        if ent[UPDATED_SJID_COL] is not None and ent[UPDATED_SJID_COL] <= just_committed_details.sjid:
            TRACE('Clearing updated entry (updated sjid %s vs just_committed sjid %s)', ent[UPDATED_SJID_COL], just_committed_details.sjid)
            FileJournalRowLogic.clear_updated_details(new_ent)
        if just_committed_details.guid is not None:
            updated_guids_to_remove.append(just_committed_details)
        if committed_details_are_equal:
            if ent[LOCAL_SIZE_COL] < 0 and new_ent[UPDATED_SJID_COL] is None:
                trans.delete_entry(ent)
            else:
                new_ent[LOCAL_SJID_COL] = just_committed_details.sjid
                new_ent[EXTRA_PENDING_DETAILS_COL] = None
                if just_committed_details.guid is not None:
                    if just_committed_details.size >= 0:
                        new_ent[LOCAL_GUID_COL] = just_committed_details.guid
                        new_ent[LOCAL_GUID_SYNCED_GUID_REV_COL] = just_committed_details.guid_rev
                    else:
                        report_bad_assumption("Server sent down a GUID for a deleted file, that won't work %r", just_committed_details)
                trans.update_entry(ent, new_ent)
        else:
            assert_(lambda : mount_logic is not None, 'Different local details while committing! %r vs %r', ent, just_committed_details)
            parent_deets = {'sjid': just_committed_details.sjid,
             'blocklist': just_committed_details.blocklist,
             'size': just_committed_details.size,
             'dir': just_committed_details.dir,
             'attrs': just_committed_details.attrs}
            new_ent[EXTRA_PENDING_DETAILS_COL] = ExtraPendingDetails(parent=parent_deets, mount_request=new_ent[EXTRA_PENDING_DETAILS_COL]['mount_request'])
            trans.update_entry(ent, new_ent)
        processed.append(True)

    def _handle_directory_not_empties(self, possible_directory_not_empties, retry_interval = None):
        if not possible_directory_not_empties:
            return
        directories_to_instantiate = set()
        to_delay = set()
        with self.write_lock() as trans:
            for ent in trans.get_entries(possible_directory_not_empties, lower=False):
                spl = ServerPath(ent[SERVER_PATH_COL], lowered=True)
                if trans.has_server_children_not_going_to_be_deleted(ent[SERVER_PATH_COL]):
                    tostart = spl
                    while not tostart.is_root:
                        directories_to_instantiate.add(tostart)
                        to_delay.discard(tostart)
                        tostart = tostart.dirname

                elif spl not in directories_to_instantiate:
                    to_delay.add(spl)

            TRACE('Directories to instantiate %r', directories_to_instantiate)
            for ent in trans.get_entries(directories_to_instantiate, lower=False):
                should_process = True
                if ent[LOCAL_SJID_COL] is None or ent[LOCAL_SJID_COL] > 0:
                    TRACE("Path %r isn't pending, should be queued for reconstruction soon...", ent[SERVER_PATH_COL])
                    should_process = False
                elif ent[LOCAL_DIR_COL]:
                    TRACE('Path %r is already a directory locally...', ent[SERVER_PATH_COL])
                    should_process = False
                spl = ServerPath(ent[SERVER_PATH_COL], lowered=True)
                if should_process:
                    parent = ent[EXTRA_PENDING_DETAILS_COL]['parent']
                    if not (parent is not None and parent['dir'] or ent[UPDATED_SJID_COL] is not None and ent[UPDATED_DIR_COL]):
                        TRACE("We don't yet have server details for %r, waiting on server details...", ent[SERVER_PATH_COL])
                        should_process = False
                if not should_process:
                    if spl in possible_directory_not_empties:
                        to_delay.add(spl)
                    continue
                TRACE('Directory %r was not empty on the server and had remote children, requeing for reconstruction', ent[SERVER_PATH_COL])
                newent = dict(ent)
                if ent[LOCAL_SIZE_COL] < 0:
                    FileJournalRowLogic.clear_local_details(newent)
                else:
                    newent[IS_CONFLICTED_COL] = True
                if ent[UPDATED_SJID_COL] is None or ent[UPDATED_SJID_COL] <= 1:
                    if parent['size'] < 0:
                        report_bad_assumption('We got a directory_not_empty for something without any server state and that used to be deleted %r' % dict(ent))
                    newent[UPDATED_BLOCKLIST_COL] = parent['blocklist']
                    newent[UPDATED_SIZE_COL] = parent['size']
                    newent[UPDATED_DIR_COL] = parent['dir']
                    newent[UPDATED_FILENAME_COL] = ent[LOCAL_FILENAME_COL]
                    newent[UPDATED_SJID_COL] = parent['sjid']
                    newent[UPDATED_MTIME_COL] = long(time.time())
                    newent[UPDATED_ATTRS_COL] = parent['attrs'].copy(data_plats=())
                    newent[UPDATED_HOST_ID_COL] = parent.get('host_id')
                trans.update_entry(ent, newent)

        for spl in to_delay:
            try:
                self.upload_retry(spl, UPLOAD_DIRECTORY_NOT_EMPTY_CODE, lower=False, interval=retry_interval)
            except Exception:
                unhandled_exc_handler()

    def perform_reconstruct(self, reconstructor, lim = 50, priority_nses = ()):
        with self.write_lock():
            self._handle_reconstruct_results(reconstructor(self.get_reconstructable(lim=lim, priority_nses=priority_nses)))

    def handle_reconstruct_results(self, results_and_details):
        with self.write_lock():
            report_bad_assumption('This method is deprecated and unsafe, please do not continue using this.')
            return self._handle_reconstruct_results(results_and_details)

    def _handle_reconstruct_success(self, trans, ent, result, just_saved_details):
        assert_(lambda : ent[LOCAL_SJID_COL] == 1 or ent[UPDATED_SJID_COL] == 1 or just_saved_details.sjid > ent[LOCAL_SJID_COL], 'Local file is newer than updated file?? %r:%r', just_saved_details, dict(ent))
        assert_(lambda : result[0] == RECONSTRUCT_SUCCESS_CODE, 'bad result for main reconstruct result processsing loop %r', result)
        if just_saved_details.size < 0:
            trans.delete_entry(ent)
            return
        file_metadata = result[1]
        try:
            new_ctime = file_metadata.ctime
            new_mtime = file_metadata.mtime
            data_plats = file_metadata.data_plats
            actual_attrs = file_metadata.attrs
            new_machine_guid = file_metadata.machine_guid
        except AttributeError:
            new_ctime, new_mtime, data_plats = result[1]
            new_machine_guid = None
            actual_attrs = just_saved_details.attrs

        actual_local_details = [new_ctime,
         new_mtime,
         data_plats,
         actual_attrs]
        assert_(lambda : all((a is not None for a in actual_local_details)), 'Local details that were None were passed to handle_reconstruct_results: %r', actual_local_details)
        assert_(lambda : ent[UPDATED_GUID_COL] is None or new_machine_guid is not None, 'server gave file a guid but we did not get a machine guid back!')
        newent = dict(ent)
        newent[IS_CONFLICTED_COL] = False
        FileJournalRowLogic.move_updated_to_local(newent)
        newent[LOCAL_MACHINE_GUID_COL] = new_machine_guid
        newent[LOCAL_CTIME_COL] = new_ctime
        newent[LOCAL_MTIME_COL] = new_mtime
        newent[LOCAL_ATTRS_COL] = actual_attrs.copy(data_plats=data_plats)
        if newent[LOCAL_SJID_COL] == 1:
            if ent[LOCAL_SJID_COL] is not None and ent[LOCAL_SJID_COL] > 1:
                newent[EXTRA_PENDING_DETAILS_COL] = ExtraPendingDetails(mount_request=self._target_ns(just_saved_details.server_path), parent={'sjid': ent[LOCAL_SJID_COL],
                 'host_id': self._get_local_host_id(ent),
                 'ts': self._get_local_timestamp(ent),
                 'blocklist': ent[LOCAL_BLOCKLIST_COL],
                 'size': ent[LOCAL_SIZE_COL],
                 'dir': ent[LOCAL_DIR_COL],
                 'attrs': ent[LOCAL_ATTRS_COL]})
            else:
                newent[EXTRA_PENDING_DETAILS_COL] = ExtraPendingDetails(mount_request=self._target_ns(just_saved_details.server_path))
            newent[LOCAL_SJID_COL] = 0
            newent[LOCAL_HOST_ID_COL] = None
            newent[LOCAL_TIMESTAMP_COL] = None
        trans.update_entry(ent, newent)

    def _handle_reconstruct_results(self, results_and_details):
        server_path_map = {}
        possible_directory_not_empties = {}
        unreconstructables = []
        for result, details in results_and_details:
            spl = details.server_path.lower()
            currently_updated_details = self.get_reconstructing(spl, lower=False)
            assert_(lambda : details.sjid >= 1, 'Bad sjid on queued file to be reconstructed')
            assert_(lambda : currently_updated_details == details, 'Queued details changed during reconstruct! %r vs %r', currently_updated_details, details)
            result_name = result if isinstance(result, basestring) or not hasattr(result, '__getitem__') else result[0]
            if result_name == RECONSTRUCT_SUCCESS_CODE:
                server_path_map[unicode(spl)] = (result, details)
            elif result_name == RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE:
                possible_directory_not_empties[unicode(spl)] = (result, details)
            elif result_name in (RECONSTRUCT_UNRECONSTRUCTABLE_CODE, RECONSTRUCT_SHORTCUT_CODE):
                unreconstructables.append(spl)
            else:
                try:
                    self.reconstruct_retry(spl, result_name, 30, lower=False)
                except Exception:
                    unhandled_exc_handler()

        if server_path_map or unreconstructables:
            with self.write_lock() as trans:
                guid_conflicts_to_unmap = [ d.guid for _, d in server_path_map.itervalues() if getattr(d, 'guid', None) ]
                sps = list((ent[SERVER_PATH_COL] for ent in trans.entries_by_local_dropbox_guid_batch(guid_conflicts_to_unmap)))
                for ent in trans.get_entries(server_path_map):
                    result, just_saved_details = server_path_map[ent[SERVER_PATH_COL]]
                    self._handle_reconstruct_success(trans, ent, result, just_saved_details)

                for ent in trans.get_entries(unreconstructables):
                    new_ent = dict(ent)
                    new_ent[UNRECONSTRUCTABLE_COL] = True
                    trans.update_entry(ent, new_ent)

                for ent in trans.get_entries(sps):
                    new_ent = dict(ent)
                    new_ent[IS_GUID_CONFLICTED_COL] = False
                    trans.update_entry(ent, new_ent)

        self._reconstruct_handle_directory_not_empties(possible_directory_not_empties)

    def _reconstruct_handle_directory_not_empties(self, possible_directory_not_empties):
        if not possible_directory_not_empties:
            return
        directories_to_instantiate = set()
        to_delay = set()
        with self.write_lock() as trans:
            for ent in trans.get_entries(possible_directory_not_empties, lower=False):
                result, just_saved_details = possible_directory_not_empties[ent[SERVER_PATH_COL]]
                if ent[IS_CONFLICTED_COL]:
                    to_delay.append(ServerPath(ent[SERVER_PATH_COL], lower=True))
                    continue
                assert_(lambda : ent[UPDATED_SIZE_COL] < 0 or not ent[UPDATED_DIR_COL], 'We got a directory not empty return value from reconstruct but the directory was not requested to be deleted: %r', ent)
                assert_(lambda : ent[LOCAL_SJID_COL] == 1 or ent[UPDATED_SJID_COL] == 1 or just_saved_details.sjid > ent[LOCAL_SJID_COL], 'Local file is newer than updated file? %r:%r', just_saved_details, ent)
                spl = ServerPath(ent[SERVER_PATH_COL], lowered=True)
                if trans.has_local_children_not_going_to_be_deleted(ent[SERVER_PATH_COL]):
                    tostart = spl
                    while not tostart.is_root:
                        directories_to_instantiate.add(tostart)
                        to_delay.discard(tostart)
                        tostart = tostart.dirname

                elif spl not in directories_to_instantiate:
                    to_delay.add(spl)

            for ent in trans.get_entries(directories_to_instantiate, lower=False):
                uspl = ent[SERVER_PATH_COL]
                ciserver_path = ServerPath(uspl, lowered=True)
                assert_(lambda : self._target_ns(ciserver_path, lower=False) is None, 'File queued for deletion had a target ns? %r', ent)
                if ent[LOCAL_SJID_COL] is None or not ent[LOCAL_DIR_COL] or ent[LOCAL_SJID_COL] == 0:
                    if uspl in possible_directory_not_empties:
                        to_delay.add(ciserver_path)
                    continue
                if ent[UPDATED_DIR_COL] if ent[UPDATED_SJID_COL] is not None and ent[UPDATED_SJID_COL] > 1 and ent[UPDATED_SJID_COL] > ent[LOCAL_SJID_COL] else (ent[LOCAL_DIR_COL] if ent[LOCAL_SJID_COL] > 1 else False):
                    TRACE('Path is already a directory remotely %r', ent[SERVER_PATH_COL])
                    if uspl in possible_directory_not_empties:
                        to_delay.add(ciserver_path)
                    continue
                newent = dict(ent)
                newent[EXTRA_PENDING_DETAILS_COL] = ExtraPendingDetails(parent={'sjid': ent[LOCAL_SJID_COL],
                 'host_id': self._get_local_host_id(ent),
                 'ts': self._get_local_timestamp(ent),
                 'dir': ent[LOCAL_DIR_COL],
                 'size': ent[LOCAL_SIZE_COL],
                 'blocklist': ent[LOCAL_BLOCKLIST_COL],
                 'attrs': ent[LOCAL_ATTRS_COL]}) if ent[LOCAL_SJID_COL] > 1 else ExtraPendingDetails()
                newent[LOCAL_SJID_COL] = 0
                newent[LOCAL_HOST_ID_COL] = None
                newent[LOCAL_TIMESTAMP_COL] = None
                assert_(lambda : not ent.get(IS_CONFLICTED_COL), 'Since we gate against local_sjid == 0 above, file should not be conflicted: %r', ent)
                trans.update_entry(ent, newent)

        for spl in to_delay:
            try:
                self.reconstruct_retry(spl, 'directory_not_empty', 30, lower=False)
            except Exception:
                unhandled_exc_handler()

    @staticmethod
    def _get_server_path(details):
        return unicode(details.server_path).lower()

    @staticmethod
    def merge_locally_unreadable_for_compare(comparing_against, local_attrs):
        new_attr_dict = dict(local_attrs.attr_dict)
        for plat, plat_attrs in comparing_against.attr_dict.iteritems():
            if plat not in new_attr_dict and plat not in local_attrs.data_plats:
                new_attr_dict[plat] = plat_attrs

        return local_attrs.copy(attr_dict=new_attr_dict)

    @staticmethod
    def generate_attrs_for_compare(remote_attrs, local_attrs, first_local_edit):
        merged_local_attrs = FileCache.merge_locally_unreadable_for_compare(remote_attrs, local_attrs)
        if first_local_edit and has_file_tag_gid_v3(remote_attrs) and has_file_tag_gid_v3(merged_local_attrs):
            merged_local_attrs = copy_file_tag_gid_v3(remote_attrs, merged_local_attrs)
        return merged_local_attrs

    def _process_local_details(self, trans, details, db_info, guid_db_info):
        spl = details.server_path.lower()
        ns, rel = details.server_path.ns_rel()
        if guid_db_info is not None:
            remote_guid = guid_db_info.guid
            remote_guid_synced_guid_rev = guid_db_info.synced_guid_rev
        else:
            remote_guid = None
            remote_guid_synced_guid_rev = None
        conditions = [(not details.server_path.is_root, 'There should not be a namespace root entry in pending'),
         (details.server_path.basename, 'All commits should have a filename'),
         (details.size >= 0 or not details.attrs, 'Attrs on a delete'),
         (details.size > 0 or not details.blocklist, 'non-positive size yet non empty blocklist!'),
         (type(details.blocklist) is str, 'non string blocklist!'),
         (details.attrs is not None, 'None attrs type!!'),
         (details.size >= 0 or not details.dir, 'negative size with dir != 0'),
         (getattr(details, 'mount_request', None) is None or details.dir, 'mount request but dir != 1'),
         (details.machine_guid is None or len(details.machine_guid.decode('ascii', 'ignore')) == len(details.machine_guid), 'local_guid must be a str and ascii!'),
         (guid_db_info is None or guid_db_info.machine_guid == details.machine_guid, 'guid db info did not machine guid!')]
        for must_be_true, error_msg in conditions:
            if not must_be_true:
                raise Exception('%s %r' % (error_msg, details))

        mount_request = getattr(details, 'mount_request', None)
        is_mounted_at = self._target_ns(details.server_path)
        if db_info is None:
            if details.size < 0:
                TRACE('Deleted file %r without active counterpart; ignoring.', details.server_path)
                return
            update = FileJournalRowLogic.new_ent(unicode(spl))
        else:
            new_ent = None
            if is_mounted_at and mount_request is None and db_info[UPDATED_SJID_COL] and db_info[LOCAL_SJID_COL] is not None and db_info[LOCAL_SJID_COL] > 0 and db_info[LOCAL_DIR_COL] == 1:
                TRACE('Pending file is an unmount but updated is mounting, overriding %r %r %r %r', mount_request, is_mounted_at, db_info[UPDATED_SJID_COL], db_info[LOCAL_SJID_COL])
                report_bad_assumption('Overriding unmount due to pending mount.')
                mount_request = is_mounted_at
            if db_info[UPDATED_SJID_COL] is not None and db_info[UPDATED_SIZE_COL] == details.size and db_info[UPDATED_BLOCKLIST_COL] == details.blocklist and db_info[UPDATED_DIR_COL] == details.dir and db_info[UPDATED_GUID_COL] == remote_guid and db_info[UPDATED_ATTRS_COL] == self.generate_attrs_for_compare(db_info[UPDATED_ATTRS_COL], details.attrs, first_local_edit=db_info[LOCAL_SJID_COL] is None):
                TRACE('Pending file is the same as file being updated, %r, updated_attrs: %r', details, db_info[UPDATED_ATTRS_COL])
                if db_info[UPDATED_SJID_COL] == 1:
                    new_ent = dict(db_info)
                    FileJournalRowLogic.clear_updated_details(new_ent)
                else:
                    if db_info[UPDATED_SIZE_COL] < 0:
                        trans.delete_entry(db_info)
                    else:
                        update = dict(db_info)
                        FileJournalRowLogic.move_updated_to_local(update)
                        update[LOCAL_ATTRS_COL] = db_info[UPDATED_ATTRS_COL].copy(data_plats=details.attrs.data_plats)
                        update[LOCAL_CTIME_COL] = details.ctime
                        update[LOCAL_MTIME_COL] = details.mtime
                        update[LOCAL_FILENAME_COL] = details.server_path.basename
                        update[LOCAL_MACHINE_GUID_COL] = details.machine_guid
                        update[IS_CONFLICTED_COL] = False
                        trans.update_entry(db_info, update)
                    return
            if db_info[LOCAL_SJID_COL] is not None and db_info[LOCAL_SIZE_COL] == details.size and db_info[LOCAL_BLOCKLIST_COL] == details.blocklist and db_info[LOCAL_DIR_COL] == details.dir and db_info[LOCAL_GUID_COL] == remote_guid:
                if db_info[LOCAL_SJID_COL] != 0 and db_info[LOCAL_ATTRS_COL] == (self.merge_locally_unreadable_for_compare(db_info[LOCAL_ATTRS_COL], details.attrs) if db_info[LOCAL_SJID_COL] > 1 else details.attrs) and is_mounted_at == mount_request:
                    TRACE('Pending file %r is already local (%r %r)', details.server_path, details, dict(db_info))
                    fn = details.server_path.basename
                    if db_info[LOCAL_CTIME_COL] != details.ctime or db_info[LOCAL_MTIME_COL] != details.mtime or db_info[LOCAL_MACHINE_GUID_COL] != details.machine_guid or db_info[LOCAL_FILENAME_COL] != fn:
                        TRACE('... filename, mtime, or ctime changed: %r vs %r', (db_info[LOCAL_FILENAME_COL], db_info[LOCAL_MTIME_COL], db_info[LOCAL_CTIME_COL]), (fn, details.mtime, details.ctime))
                        new_ent = new_ent or dict(db_info)
                        new_ent[LOCAL_CTIME_COL] = details.ctime
                        new_ent[LOCAL_MTIME_COL] = details.mtime
                        new_ent[LOCAL_MACHINE_GUID_COL] = details.machine_guid
                        new_ent[LOCAL_FILENAME_COL] = fn
                        trans.update_entry(db_info, new_ent)
                    elif new_ent:
                        TRACE('... same as client-initiated reconstruct, killing updated details')
                        trans.update_entry(db_info, new_ent)
                    return
                if db_info[LOCAL_SJID_COL] == 0 and db_info[LOCAL_MTIME_COL] == details.mtime and db_info[LOCAL_CTIME_COL] == details.ctime and db_info[LOCAL_ATTRS_COL] == details.attrs and db_info[LOCAL_FILENAME_COL] == details.server_path.basename and db_info[LOCAL_MACHINE_GUID_COL] == details.machine_guid and db_info[EXTRA_PENDING_DETAILS_COL]['mount_request'] == mount_request:
                    TRACE('Pending file is already queued to be pending: %r', details.server_path)
                    if new_ent:
                        trans.update_entry(db_info, new_ent)
                    return
            p = propagate_none(lambda x: x.parent, db_info.get(EXTRA_PENDING_DETAILS_COL))
            if db_info[LOCAL_SJID_COL] == 0 and p is not None and (p.get('guid') is None or unicode(spl) == db_info[PARENT_GUID_SYNCED_SERVER_PATH_COL]) and (p.get('guid') is None or p['sjid'] == db_info[PARENT_GUID_SYNCED_SJID_COL]) and p['blocklist'] == details.blocklist and p['size'] == details.size and p['dir'] == details.dir and is_mounted_at == mount_request and p.get('guid') == remote_guid and p['attrs'] == self.merge_locally_unreadable_for_compare(p['attrs'], details.attrs):
                new_ent = new_ent or dict(db_info)
                new_ent[LOCAL_BLOCKLIST_COL] = p['blocklist']
                new_ent[LOCAL_SIZE_COL] = p['size']
                new_ent[LOCAL_DIR_COL] = p['dir']
                new_ent[LOCAL_SJID_COL] = p['sjid']
                new_ent[LOCAL_ATTRS_COL] = p['attrs']
                new_ent[LOCAL_MTIME_COL] = details.mtime
                new_ent[LOCAL_CTIME_COL] = details.ctime
                new_ent[LOCAL_FILENAME_COL] = details.server_path.basename
                new_ent[LOCAL_HOST_ID_COL] = p.get('host_id')
                new_ent[LOCAL_TIMESTAMP_COL] = p.get('ts')
                new_ent[LOCAL_GUID_COL] = p.get('guid')
                new_ent[LOCAL_GUID_SYNCED_GUID_REV_COL] = p.get('guid_rev')
                new_ent[EXTRA_PENDING_DETAILS_COL] = None
                new_ent[LOCAL_MACHINE_GUID_COL] = details.machine_guid
                new_ent[IS_CONFLICTED_COL] = False
                trans.update_entry(db_info, new_ent)
                TRACE('Pending file is the same as what was previously synced, setting back to synced %r', details.server_path)
                return
            update = new_ent or dict(db_info)
            if details.size < 0 and db_info[LOCAL_SJID_COL] is not None and db_info[LOCAL_SJID_COL] <= 1 and not (update[LOCAL_SJID_COL] == 0 and update[EXTRA_PENDING_DETAILS_COL]['parent']) and not (update[UPDATED_SJID_COL] is not None and update[UPDATED_SJID_COL] > 0):
                TRACE('Local file was never uploaded, has no server state and is now deleted, dropping row from database: %r', details.server_path)
                trans.delete_entry(db_info)
                return
            if db_info[LOCAL_SJID_COL] is None and details.size < 0:
                TRACE('Deleted file %r without active counterpart; ignoring.', details.server_path)
                if new_ent:
                    trans.delete_entry(db_info)
                return
        FileJournalRowLogic.set_pending_details(update, details, remote_guid=remote_guid, remote_guid_parent_rev=remote_guid_synced_guid_rev)
        if db_info is None:
            trans.insert_entry(update)
        else:
            trans.update_entry(db_info, update)

    def set_pending_hash_batch(self, seq_of_details__):
        with self.write_lock() as trans:
            new_seq = []
            for details in seq_of_details__:
                try:
                    details = details.copy(server_path=self.mount_relative_server_path(details.server_path))
                except KeyError:
                    report_bad_assumption('Non-root relative path in set_pending_hash_batch!')

                new_seq.append(details)

            backend = CommitHoldingCompat(trans)
            dhal = DirectoryHoldingAddLogic(backend, backend)
            dhdl = DirectoryHoldingDeleteLogic(backend, backend)
            ghl = GUIDHoldingLogic(backend, backend)
            chl = CommitHoldingLogic(backend, [dhal, dhdl, ghl])
            TRACE('Before holding details:\n%s', pprint.pformat(new_seq))
            seq_of_details = chl.filter(new_seq)
            TRACE('After holding details:\n%s', pprint.pformat(seq_of_details))
            _guids = (a.machine_guid for a in seq_of_details)
            machine_guid_to_remote_guid_info = trans.map_machine_guids(_guids).get
            _sps = itertools.imap(operator.attrgetter('server_path'), seq_of_details)
            try:
                sp2info = dict(((ServerPath(ent[SERVER_PATH_COL], lowered=True), ent) for ent in trans.get_entries(_sps)))
            except CorruptedAttributeError as ex:
                unhandled_exc_handler()
                raise CorruptedDBError(ex.message)

            for details in seq_of_details:
                db_info = sp2info.get(details.server_path.lower())
                remote_guid_info = machine_guid_to_remote_guid_info(details.machine_guid)
                self._process_local_details(trans, details, db_info, remote_guid_info)

    def dispatch_block_reference_changes(self, bcbl, hash_references_added = (), hash_references_removed = ()):
        if not hash_references_added:
            hash_references_added = bcbl.hashes_added() if bcbl else ()
        if not hash_references_removed:
            hash_references_removed = bcbl.hashes_removed() if bcbl else ()
        self.block_reference_callbacks.run_handlers(hash_references_added, hash_references_removed)

    def _target_ns(self, sp, lower = True):
        assert_(self._is_read_locked)
        ns, rel = sp.ns_rel()
        try:
            mt = self.root_ns_to_mount_table[ns]
        except KeyError:
            return None

        return mt.is_mount_point(rel, lower=lower)

    def copy(self, database_file, **kw):
        assert_(lambda : not self._is_write_locked())
        with self.giant_lock:
            file_cache = object.__new__(self.__class__)
            new_backend = self.backend.copy(file_cache, database_file, **kw)
            file_cache.__low_init__(new_backend, dict(((ns, mt.copy()) for ns, mt in self.root_ns_to_mount_table.iteritems())), dict(self.last_revision))
            return file_cache

    def clear(self):
        with self.write_lock() as trans:
            trans.clear()
            self.last_revision = {}
            self.root_ns_to_mount_table = {}

    def who_has(self, hash, ns = None, lim = None):
        assert_(lambda : len(hash) == DROPBOX_HASH_LENGTH, 'length of hash is bad %r vs %r', len(hash), DROPBOX_HASH_LENGTH)
        with self._read_lock_cursor() as cursor:
            with SimpleTimer('who_has, but inside the lock', cumulative=True):
                cursor.execute('SELECT file_journal.server_path, block_ref.how, file_journal.local_attrs FROM block_ref JOIN block_cache ON block_ref.hash_id = block_cache.id JOIN file_journal ON block_ref.fj_id = file_journal.id WHERE block_cache.hash = ? AND ((block_ref.how >> 42) & 1) == 0 %s %s' % (' AND file_journal.server_path LIKE ? ' if ns is not None else '', 'LIMIT %d' % (lim,) if lim else ''), (hash, '%d:/%%' % (ns,)) if ns is not None else (hash,))
                return [ (ServerPath(a[0], lowered=True), a[1], a[2]) for a in cursor ]

    def block_exists(self, _hash, ns = None):
        assert_(lambda : len(_hash) == DROPBOX_HASH_LENGTH, 'length of hash is bad %r vs %r', len(_hash), DROPBOX_HASH_LENGTH)
        with self._read_lock_cursor() as cursor:
            if ns is None:
                cursor.execute('SELECT 1 FROM block_ref JOIN block_cache ON block_ref.hash_id == block_cache.id WHERE block_cache.hash = ? AND ((block_ref.how >> 42) & 1) != 1 LIMIT 1', (_hash,))
            else:
                cursor.execute('SELECT 1 FROM block_ref JOIN block_cache ON block_ref.hash_id == block_cache.id JOIN file_journal ON block_ref.fj_id = file_journal.id WHERE block_cache.hash = ? AND ((block_ref.how >> 42) & 1) != 1 AND file_journal.server_path LIKE ? LIMIT 1', (_hash, '%d:/%%' % (ns,)))
            return cursor.fetchone()

    def hashes_with_references(self, hashes_sequence):
        with self._read_lock_cursor() as cursor:
            return frozenset(sqlite3_get_table_entries(cursor, 'block_cache', 'hash', hashes_sequence, desired_columns=('hash',), row_factory=just_the_first))

    def _get_block_references(self, cursor, uspl):
        try:
            ent = self._get_entry(cursor, uspl)
        except FileJournalEntryDoesNotExist:
            file_journal_references = frozenset()
        else:
            if ent[LOCAL_SJID_COL] is None:
                file_journal_references = frozenset()
            else:
                file_journal_references = set()
                IS_ATTRS = FileJournalRowLogic.IS_ATTRS
                IS_PARENT = FileJournalRowLogic.IS_PARENT
                if ent[LOCAL_BLOCKLIST_COL]:
                    for i, _hash in enumerate(ent[LOCAL_BLOCKLIST_COL].split(',')):
                        file_journal_references.add((_hash, uspl, i))

                if ent[LOCAL_ATTRS_COL]:
                    for _hash, ref in ent[LOCAL_ATTRS_COL].get_blockrefs():
                        file_journal_references.add((_hash, uspl, ref | IS_ATTRS))

                extra = ent[EXTRA_PENDING_DETAILS_COL]
                if extra:
                    p = extra['parent']
                    if p:
                        if p['blocklist']:
                            for i, _hash in enumerate(p['blocklist'].split(',')):
                                file_journal_references.add((_hash, uspl, i | IS_PARENT))

                        if p['attrs']:
                            for _hash, ref in p['attrs'].get_blockrefs():
                                file_journal_references.add((_hash, uspl, ref | IS_PARENT | IS_ATTRS))

        return file_journal_references

    def _kill_block_references(self, server_path, lower = True):
        if lower:
            server_path = server_path.lower()
        uspl_tup = (unicode(server_path),)
        with self.write_lock() as trans:
            cursor = trans.sqlite_cursor()
            cursor.execute('DELETE FROM block_ref WHERE fj_id = (SELECT id FROM file_journal WHERE server_path = ?)', uspl_tup)
            cursor.execute('DELETE FROM block_cache WHERE NOT EXISTS (SELECT 1 FROM block_ref WHERE block_ref.hash_id = block_cache.id)')

    def local_details_by_dropbox_guid(self, guid):
        with self.read_lock() as trans:
            entries = trans.entries_by_local_dropbox_guid_batch([guid])
            try:
                ent = head(entries)
            except IndexError:
                return

            return local_details_from_entry(ent)

    def verify_backward_hash_reference_consistency(self, server_path, repair = True, lower = True):
        with self._read_lock_cursor() as cursor:
            if lower:
                server_path = server_path.lower()
            uspl = unicode(server_path)
            uspl_tup = (uspl,)
            consistent = self._get_block_references(cursor, uspl) == set(cursor.execute('SELECT block_cache.hash, file_journal.server_path, block_ref.how FROM block_ref JOIN block_cache ON block_ref.hash_id == block_cache.id JOIN file_journal ON block_ref.fj_id == file_journal.id WHERE file_journal.server_path = ?', uspl_tup))
        if repair and not consistent:
            with self.write_lock() as trans:
                cursor = trans.sqlite_cursor()
                cursor.execute('DELETE FROM block_ref WHERE fj_id = (SELECT id FROM file_journal WHERE server_path = ?)', uspl_tup)
                cursor.execute('DELETE FROM block_cache WHERE NOT EXISTS (SELECT 1 FROM block_ref WHERE  block_ref.hash_id = block_cache.id)')
                cursor.row_factory = dict_like_row
                old_row = cursor.execute('SELECT * FROM file_journal WHERE server_path = ?', uspl_tup).fetchone()
                l = FileJournalRowLogic(trans.get_mount_points())
                l.delete_entry(dict(old_row))
                l.execute_da_sql(cursor)
                l = FileJournalRowLogic(trans.get_mount_points())
                l.insert_entry(dict(old_row))
                l.execute_da_sql(cursor)
        return consistent
