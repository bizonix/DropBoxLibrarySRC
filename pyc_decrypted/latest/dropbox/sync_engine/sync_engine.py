#Embedded file name: dropbox/sync_engine/sync_engine.py
import contextlib
import errno
import functools
import itertools
import operator
import os
import pprint
import shutil
import socket
import sys
import threading
import time
import unicodedata
from client_api.dropbox_connection import DropboxServerError
from client_api.hashing import DROPBOX_HASH_LENGTH, DROPBOX_MAX_BLOCK_SIZE, dropbox_hash, is_valid_blocklist
from dropbox.metadata.metadata import metadata_plats
from dropbox.attrs import Attributes, FrozenAttributes, get_attrs_blocklist
from dropbox.bubble import BubbleKind, Bubble
from dropbox.callbacks import Handler
from dropbox.client_prof import SimpleTimer
from dropbox.dbexceptions import LowDiskSpaceError, RequestDataOversizeError
from dropbox.db_thread import db_thread
from dropbox.directoryevent import DirectoryEvent
from dropbox.event import report_aggregate_event, TimedEvent
from dropbox.fastdetails import FastDetails
from dropbox.features import feature_enabled
from dropbox.functions import batch, frozendict, is_four_byte_unicode, is_temp_file, is_watched_filename, loop_delete, null_context, split_extension
from dropbox.globals import dropbox_globals
from dropbox.i18n import trans
from dropbox.lock_ordering import NonRecursiveLock
from dropbox.low_functions import RuntimeMixin, add_inner_methods, identity
from dropbox.native_event import AutoResetEvent
from dropbox.nfcdetector import is_nfc
from dropbox.read_write_lock import RWLock
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption, assert_
from dropbox.client.deleted_file_cache import DeletedFileCache
import dropbox.fsutil as fsutil
from dropbox.file_cache.exceptions import InvalidDatabaseError, NamespaceNotMountedError
from dropbox.file_cache import RECONSTRUCT_BAD_LOCAL_DETAILS_CODE, RECONSTRUCT_BUSY_CODE, RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE, RECONSTRUCT_HASHES_NOT_READY_CODE, RECONSTRUCT_LOW_DISK_SPACE_CODE, RECONSTRUCT_NO_HASHES_CODE, RECONSTRUCT_NO_PARENT_FOLDER_CODE, RECONSTRUCT_PERMISSION_DENIED_CODE, RECONSTRUCT_READ_ONLY_FS_CODE, RECONSTRUCT_SUCCESS_CODE, RECONSTRUCT_UNRECONSTRUCTABLE_CODE, RECONSTRUCT_UNKNOWN_CODE, MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT, UPLOAD_QUOTA_CODE, UPLOAD_NO_ACCESS_CODE, UPLOAD_CONFLICT_CODE, UPLOAD_NEED_BLOCKS_CODE, UPLOAD_NEED_BLOCKS_HASHING_CODE, UPLOAD_INVALID_PATH_CODE, create_extended_upload_code, is_invalid_path_upload_code
from dropbox.server_path import server_path_ns_rel_unicode, server_path_ns_unicode, ServerPath, NsRelativePathFast, NsRelativePathMemory
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR, IGNORE_BAD_SYMLINK_CODE, IGNORE_CACHE_PATH_CODE, IGNORE_DROPBOX_WRITE_CODE, IGNORE_FOUR_BYTE_UNICODE_CODE, IGNORE_INVALID_FILENAME_CODE, IGNORE_INVALID_NFC_CODE, IGNORE_INVALID_NFD_CODE, IGNORE_NOT_REGULAR_FILE_CODE, IGNORE_SELECTIVE_SYNC_CODE, IGNORE_UNKNOWN_CODE, IGNORE_UNWATCHED_CODE, IGNORE_WHITESPACE_PATH_CODE
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError, FileSystemError, NotADirectoryError, FileExistsError
import arch
from .attrs_handler import AttributesHandler
from .case_filter import case_filter
from .constants import HASH_ACCESS, HASH_BUSY, HASH_DELETED, HASH_DROP, HASH_SUCCESS, HASH_UNKNOWN, FileSyncStatus
from .download import ListThread, HashDownloadThread
from .hashing import HashThread, _hash_file, _hash_dir
from .hash_queues import HashDetails, ToHashFileSet, UpdatedHashQueue, UploadHashQueue
from .mac_finder_comment_attr_wrapper import mac_finder_comment_file_system
from .move_dropbox import move as move_dropbox
from .posix_attrs_wrapper import executable_attribute_file_system
from .p2p.main import P2PThread, P2PState
from .reconstruct import ReconstructThread, _actually_reconstruct, _delete_dir_and_unwatched, _reconstruct, reconstruct_error_from_exception
from .reindex import ReindexThread, reindex_no_start_lock, ReindexDetails, ReindexQueue
from .server_local_mapper import ServerLocalMapper
from .sync_engine_util import SyncEngineStoppedError, add_sig_and_check, block_cache_contents, BlockContentsNotFoundError, BlockContentsBadDataError, BlockContentsError
from .sync_memory_caches import WriteIgnoreMap, PathCache
from .upload import UploadThread, HashUploadThread
_FILE_BUSY_HASH_RETRY_INTERVAL = 5

class ExecutableAttributeWrappedArch(RuntimeMixin):

    def __init__(self, arch):
        super(ExecutableAttributeWrappedArch, self).__init__(arch)
        self.file_system = mac_finder_comment_file_system(executable_attribute_file_system(arch.file_system))


START = 'start'
STOP = 'stop'
LIST = 'list'
HASH = 'hash'
RUNNING = 'running'
STOPPING = 'stopping'
STOPPED = 'stopped'
START_STOP_STATES = [RUNNING, STOPPING, STOPPED]

@add_inner_methods('deleted_details', 'get_upload_failures', 'get_reconstruct_failures', 'get_upload_count', 'get_reconstruct_count', 'get_conflict_count', 'get_upload_filename', 'get_reconstruct_filename', 'upload_ready_time', 'reconstruct_ready_time', 'is_uploading', 'is_reconstructing', 'is_conflicted', 'is_uploadable', 'is_reconstructable', 'last_revisions', 'filter_unsynced_sjids', 'get_all_tracked_namespaces', 'get_server_dir_children', 'server_dir_exists', 'root_relative_server_path', 'mount_relative_server_path', 'get_mount_points', 'get_num_local_files', 'update_ctime_on_files', 'target_ns', 'mounted_at', '_ignore_set_should_ignore', 'get_directory_ignore_set', 'get_attrs_whitelist', 'get_local_details_batch', 'is_over_quota', 'add_remote_file_event_callback', 'remove_remote_file_event_callback', 'add_synced_files_callback', 'remove_synced_files_callback', 'add_mount_callback', 'remove_mount_callback', 'find_blocklist_in_dir', dropbox_have_locally='block_exists', inner_name='cache')

@add_inner_methods(hash_ready_time='ready_time', get_hash_failure_counts='get_failure_counts', get_hash_count='__len__', get_hashable='get_active', get_hashable_count='active_count', inner_name='to_hash')

@add_inner_methods(add_change_directory_ignore_callback='add_handler', remove_change_directory_ignore_callback='remove_handler', handle_change_directory_ignore='run_handlers', inner_name='directory_ignore_set_handler')

@add_inner_methods(add_reconstruct_run_callback='add_handler', remove_reconstruct_run_callback='remove_handler', handle_reconstruct_run='run_handlers', inner_name='reconstruct_run_handler')

@add_inner_methods(add_priority_hint='add_priority_hint', inner_name='upload_hash_queue')

class SyncEngine(object):
    MIN_FREE_SPACE = 100 * 1024 * 1024

    @staticmethod
    def _sort_key_to_hash(details):
        return details.order

    def is_exists(self, fs_path):
        return fsutil.is_exists(self.fs, fs_path)

    def is_directory(self, fs_path):
        return fsutil.is_directory(self.fs, fs_path)

    def is_regular(self, fs_path):
        return fsutil.is_regular(self.fs, fs_path)

    def is_symlink(self, fs_path):
        return fsutil.is_symlink(self.fs, fs_path)

    def is_file_type(self, fs_path, fs_node_type, resolve_link = True):
        return fsutil.is_file_type(self.fs, fs_path, fs_node_type, resolve_link=resolve_link)

    def makedirs(self, fs_path):
        return fsutil.makedirs(self.fs, fs_path)

    def safe_move(self, src, dst):
        return fsutil.safe_move(self.fs, src, dst)

    _perm2mode = {'exec': 73,
     'write': 146,
     'read': 292}

    def verify_file_perms(self, local_file, perm, st = None):
        if st is None:
            st = self.fs.indexing_attributes(local_file)
        try:
            st.mode
        except AttributeError:
            return True

        return fsutil.posix_verify_file_parms(self.fs, local_file, perm, st=st)

    def verify_cache_path(self):
        try:
            self.makedirs(self.cache_path)
        except FileExistsError:
            pass

        try:
            self.arch.hide_folder(self.cache_path)
        except Exception:
            unhandled_exc_handler()

        return self.cache_path

    def mount_dropbox_folder(self, unicode_dropbox_folder, dfc_path = None, _already_have_start_stop_lock = False):
        context = null_context() if _already_have_start_stop_lock else self.start_stop_lock
        with context:
            if not self.stopped:
                raise Exception("Can't change dropbox path while sync engine is started!")
            self.dropbox_folder = self.arch.make_path(unicode_dropbox_folder)
            try:
                self.case_sensitive = not self.fs.is_case_insensitive_directory(self.dropbox_folder)
            except:
                unhandled_exc_handler()
                self.case_sensitive = sys.platform.startswith('linux')

            TRACE('---------------- Dropbox Folder %r is %scase insensitive!! ---------------', self.dropbox_folder, 'not ' if self.case_sensitive else '')
            self.cache_path = self.dropbox_folder.join(u'.dropbox.cache')
            self.cache_path_l = self.normalized_local_path(self.cache_path)
            try:
                self.verify_cache_path()
            except:
                unhandled_exc_handler()

            dfc_path = dfc_path or self.appdata_path
            dfc_db = dfc_path.join(u'deleted.dbx')
            old_dfc_db = self.cache_path.join(u'deleted.dbx')
            if not fsutil.is_regular(self.fs, dfc_db) and fsutil.is_regular(self.fs, old_dfc_db):
                TRACE("DeletedFileCache db 'deleted.dbx' found inside cache folder; moving it to appdata folder: %r -> %r", old_dfc_db, dfc_db)
                shutil.move(unicode(old_dfc_db), unicode(dfc_db))
            dfc_args = dict(filename=unicode(dfc_db), cache_path=self.cache_path, arch=self.arch)
            if self.keystore:
                dfc_args.update(keystore=self.keystore)
            self.deleted_file_cache = DeletedFileCache(**dfc_args)
            self.server_local_mapper = ServerLocalMapper({self.main_root_ns: self.dropbox_folder}, self.cache, self.fs)
            self.path_cache.set_server_local_mapper(self.server_local_mapper)
            self.local_to_server = self.server_local_mapper.local_to_server
            self.server_to_local = functools.partial(self.server_local_mapper.server_to_local, ignore_case=not self.case_sensitive)
            self.convert_local = self.server_local_mapper.convert_local
            if self.recently_changed:
                self.recently_changed.set_sync_engine(self)
            self._update_attrs(None, None)

    @property
    def fs(self):
        return self.arch.file_system

    def __init__(self, arch, root_ns, host_int, config, pref_controller, file_cache, sigstore, ideal_tracker, file_events, status, conn, bubble_context, keystore, desktop_login, event, ui_kit, notification_controller, recently_changed, appdata_path, server_params, freshly_linked = False, deleted_file_cache = None):
        self.arch = ExecutableAttributeWrappedArch(arch)
        self.appdata_path = appdata_path and self.fs.make_path(appdata_path)
        self.folder_tagger = arch.folder_tagger
        self.start_stop_lock = NonRecursiveLock(RWLock(), acquire_methods=('acquire_read', 'acquire_write'), release_methods=('release_read', 'release_write'))
        self._running_state = STOPPED
        self._running_state_lock = threading.Lock()
        self._running_state_callbacks = dict(((state, Handler(recursive=False, handle_exc=unhandled_exc_handler)) for state in START_STOP_STATES))
        self._caches_populated = False
        self.main_root_ns = root_ns
        self.root_nses = (root_ns,)
        self.writes_to_ignore = WriteIgnoreMap()
        self.config = config
        self.special_folders = {}
        self.deprecated_paths = []
        self.host_int = host_int
        self.desktop_login = desktop_login
        self.ideal_tracker = ideal_tracker
        if self.ideal_tracker is not None:
            self.ideal_tracker.set_sync_engine(self)
        self.deleted_file_cache = deleted_file_cache
        self.pref_controller = pref_controller
        self.gandalf = None
        self.event = event
        self.is_first_list = False
        try:
            file_cache.add_root_ns(root_ns)
        except:
            unhandled_exc_handler()
            file_cache.clear()
            file_cache.add_root_ns(root_ns)

        if len(file_cache.get_root_namespaces()) != 1:
            report_bad_assumption('More than one root_ns in file_cache!')
            file_cache.clear()
            file_cache.add_root_ns(root_ns)
        sync_engine = self

        def to_hash_mod_entry(self, the_key, old_entry_tuple, new_entry_tuple):
            if sync_engine.dropbox_folder is None:
                return
            if not old_entry_tuple:
                try:
                    sync_engine.path_cache.mark_changed(local_path=new_entry_tuple[0].local_path)
                except:
                    unhandled_exc_handler()

            elif not new_entry_tuple:
                try:
                    sync_engine.path_cache.mark_active(local_path=old_entry_tuple[0].local_path)
                except:
                    unhandled_exc_handler()

            else:
                return

        self.reindex_queue = ReindexQueue()
        self.to_hash = ToHashFileSet(self, file_cache)
        self.to_hash.add_keymod_handler(to_hash_mod_entry)
        self.blocked_events = set()
        self.to_event_later = set()
        self.dropbox_folder = None
        self.case_sensitive = None
        self.cache_path = None
        self.server_local_mapper = None
        self.initial_list_bool = False
        self.initial_list_lock = threading.RLock()
        self.initial_hash_bool = False
        self.initial_hash_lock = threading.RLock()
        self.initial_reindex_bool = False
        self.initial_reindex_lock = threading.RLock()
        self.upload_event = AutoResetEvent()
        self.reconstruct_event = AutoResetEvent()
        self.hash_event = AutoResetEvent()
        self.hash_upload_event = AutoResetEvent()
        self.hash_download_event = AutoResetEvent()
        self.bubble_context = bubble_context
        self.ui_kit = ui_kit
        self.status = status
        self.conn = conn
        self.recently_changed = recently_changed
        self.freshly_linked = freshly_linked
        self.sigstore = sigstore
        self.cache = file_cache
        self.path_cache = PathCache(self.arch)
        self.attr_handler = AttributesHandler(self.arch, event, self.cache.get_attrs_whitelist())
        self.keystore = keystore
        self.perf_logged = False
        self.perf_tracker = TimedEvent()

        def the_cb(the_map, the_key, old_entry_tuple, new_entry_tuple):
            if self.dropbox_folder is None:
                return
            if not old_entry_tuple:
                try:
                    sync_engine.path_cache.mark_changed(root_relative=sync_engine.cache.root_relative_server_path(new_entry_tuple[0].server_path, ctor=NsRelativePathMemory, ignore_case=not self.case_sensitive))
                except Exception:
                    unhandled_exc_handler()

            elif not new_entry_tuple:
                try:
                    sync_engine.path_cache.mark_active(root_relative=sync_engine.cache.root_relative_server_path(old_entry_tuple[0].server_path, ctor=NsRelativePathMemory, ignore_case=not self.case_sensitive))
                except Exception:
                    unhandled_exc_handler()

        self.cache.add_upload_keymod_handler(the_cb)
        self.cache.add_reconstruct_keymod_handler(the_cb)
        self.create_tries_map = {}

        def create_tries_cb(the_map, the_key, old_entry_tuple, new_entry_tuple):
            if not new_entry_tuple:
                try:
                    del self.create_tries_map[the_key]
                except KeyError:
                    pass

        self.cache.add_reconstruct_keymod_handler(create_tries_cb)

        def reconstruct_retry_cb(key, reason):
            if reason == RECONSTRUCT_NO_PARENT_FOLDER_CODE:
                self.create_tries_map[key] = self.create_tries_map.get(key, 0) + 1

        self.cache.add_reconstruct_retry_handler(reconstruct_retry_cb)
        self._default_server_local_mappers()
        self.to_hash.add_error_callback(self._to_hash_error_callback)
        self.cache.add_upload_error_callback(self._pending_error_callback)
        self.cache.add_reconstruct_error_callback(self._updated_error_callback)
        self.updated_hash_queue = UpdatedHashQueue(self.cache.set_reconstruct_active)
        self.upload_hash_queue = UploadHashQueue(self.cache.set_upload_active)
        self.cache.add_upload_changed_callback(self.upload_hash_queue.no_hashes_needed)
        self.cache.add_reconstruct_changed_callback(self.updated_hash_queue.no_hashes_needed)
        self.add_synced_files_callback(self.upload_hash_queue.synced_files_callback)
        self.add_synced_files_callback(self.updated_hash_queue.synced_files_callback)
        self.in_use, self.quota = (0, 0)
        self.max_upload_count = 200
        self.max_list_batch_count = 100
        self.p2p_min_nonbatch_file_size = 0
        self.server_supports_attrs = False
        self.server_limits = {}

        def block_ref_changes(hashes_added, hashes_removed):
            sigstore.delete(hashes_removed)

        self.cache.add_block_reference_callback(block_ref_changes)
        self.get_block_sig = self.sigstore.get
        self.file_events = file_events
        self._initial_list_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self._initial_hash_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self._initial_reindex_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self._handle_list(server_params)
        self.p2p_state = P2PState(config, status, pref_controller, host_int, self)
        try:
            self.p2p_state.update_active_namespaces(self.cache.get_all_tracked_namespaces())
        except:
            unhandled_exc_handler()

        self.threads_to_wait_on = frozenset((ReconstructThread,
         HashThread,
         HashUploadThread,
         UploadThread,
         ReindexThread))
        self.threads = dict(((db_thread(klass)(self), [klass, False, None]) for klass in (HashThread,
         HashUploadThread,
         HashDownloadThread,
         UploadThread,
         ReconstructThread,
         ReindexThread,
         P2PThread)))
        list_thread = db_thread(ListThread)(self, notification_controller)
        self.threads[list_thread] = [ListThread, False, None]
        for t, v in self.threads.iteritems():
            v[2] = t

        self.add_list_callback = list_thread.add_list_callback
        self.remove_list_callback = list_thread.remove_list_callback
        self.cache.add_mount_callback(self._mount_callback_not_running)
        self.add_list_callback(self.p2p_state._handle_list)
        self.add_list_callback(self._handle_list)
        self.reconstruct_run_handler = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.directory_ignore_set_handler = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        for thr in self.threads:
            thr.start()

    def local_case_filenames(self, local_path):
        return fsutil.local_case_filenames(self.fs, local_path)

    def normalized_local_path(self, local_path):
        if self.case_sensitive is None:
            raise Exception('Dropbox folder not mounted yet!')
        if self.case_sensitive:
            return local_path
        return local_path.lower()

    def local_to_root_relative(self, local_path, ctor = None):
        return self.server_local_mapper.convert_local(local_path, ctor=ctor)

    def get_hash_filename(self):
        try:
            p = self.to_hash.get_only_file()
        except Exception:
            unhandled_exc_handler()
            return None

        if p:
            return p.local_path.basename

    def get_reconstruct_create_tries(self, l_server_path):
        return self.create_tries_map.get(l_server_path, 0)

    def set_config_key(self, key, value):
        self.cache.set_config_key(key, value)

    def get_config_key(self, key):
        return self.cache.get_config_key(key)

    def remove_config_key(self, key):
        self.cache.remove_config_key(key)

    def _wants_dict_list(self):
        return True

    def _default_server_local_mappers(self):

        def df(*n, **kw):
            raise NamespaceNotMountedError

        self.local_to_server = self.server_to_local = df

    def get_max_inline_attr_size(self):
        return self.attr_handler.get_max_inline_attr_size()

    def _set_cant_sync(self, status_to_update, basename, reason):
        status_to_update.set_cant_sync(basename, reason)

    def _updated_error_callback(self, method, reason = None, server_path = None, details = None, retry_interval = None):
        if method != 'retry':
            return
        if not details:
            return
        if reason in (RECONSTRUCT_LOW_DISK_SPACE_CODE,
         RECONSTRUCT_PERMISSION_DENIED_CODE,
         RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE,
         RECONSTRUCT_BUSY_CODE,
         RECONSTRUCT_READ_ONLY_FS_CODE):
            self._set_cant_sync(self.status.download_status, details.server_path.basename, reason)

    def _pending_error_callback(self, method, reason = None, server_path = None, details = None, retry_interval = None):
        if method != 'retry':
            return
        if not details:
            return
        basename = details.server_path.basename
        upload_status = self.status.upload_status
        if reason == UPLOAD_QUOTA_CODE:
            self._set_cant_sync(upload_status, basename, UPLOAD_QUOTA_CODE)
        elif is_invalid_path_upload_code(reason):
            self._set_cant_sync(upload_status, basename, UPLOAD_INVALID_PATH_CODE)

    def _to_hash_error_callback(self, method, reason = None, server_path = None, details = None, retry_interval = None):
        if method != 'retry':
            return
        if not details:
            return
        local_path = details.local_path
        fn = local_path.basename
        hash_status = self.status.hash_status
        if reason == HASH_ACCESS:
            TRACE('Access denied on file "%r".', local_path)
            self._set_cant_sync(hash_status, fn, HASH_ACCESS)
        elif reason == HASH_BUSY:
            self._set_cant_sync(hash_status, fn, HASH_BUSY)

    def get_queue_stats(self):
        toret = self.cache.get_queue_stats()
        with self.to_hash:
            hash_active_count, hash_waiting_count, hash_inactive_count = self.to_hash.counts()
            toret['hash'] = {'total_count': len(self.to_hash),
             'active_count': hash_active_count,
             'waiting_count': hash_waiting_count,
             'inactive_count': hash_inactive_count,
             'failure_counts': self.to_hash.get_failure_counts(constructor=dict)}
            return toret

    def set_gandalf(self, gandalf):
        self.gandalf = gandalf

    def iterate_hashes_details(self, details):
        for hashes, parents in ((details.blocklist.split(',') if details.blocklist else (), details.parent_blocklist.split(',') if getattr(details, 'parent_blocklist', '') else ()), (self.attr_handler.get_downloadable_blocklist(self.server_to_local(details.server_path), details.attrs), ())):
            for i, _hash in enumerate(hashes):
                try:
                    parent_hash = parents[i]
                except IndexError:
                    parent_hash = None

                yield (_hash, parent_hash)

    def _get_db_state(self, lp):
        sp = self.local_to_server(lp)
        server_lp = self.server_to_local(sp, local_case_only=True)
        ld = self.cache.get_local_details_batch((sp,))
        size = -1 if not ld else ld[0].size
        return (server_lp, size)

    def _case_filter_local_paths(self, deets_iter, exists, dirname, key = identity):
        if self.case_sensitive:
            return case_filter(self._get_db_state, deets_iter, key=key, handle_conflict=self._handle_lower_case_conflict, exists=exists, dirname=dirname)
        else:
            return (('watched', d) for d in deets_iter)

    hash_details_local_key = operator.attrgetter('local_path')
    hash_details_dirname = operator.attrgetter('dirname')

    def get_hashable_with_attrs_deets(self):
        with self.start_stop_lock:
            if not self.running:
                raise SyncEngineStoppedError()
            self.update_status_ui()
            with self.cache.write_lock():
                with self.set_event_on_state_change():
                    hashable = []
                    while not hashable:
                        in_hash_queue = self.to_hash.get_active(lim=2 * self.max_upload_count)
                        if not in_hash_queue:
                            return ((), frozendict(), {})
                        to_batch = []
                        to_kill = []
                        for result, deets in self._case_filter_local_paths(in_hash_queue, exists=self.is_exists, dirname=self.hash_details_dirname, key=self.hash_details_local_key):
                            lp = deets.local_path
                            local_key = self.normalized_local_path(lp)
                            kill = False
                            if self._ignore_set_should_ignore(self.server_local_mapper.convert_local(lp, ctor=NsRelativePathFast)):
                                TRACE('SELECTIVE_SYNC: ignore %r', lp)
                                kill = True
                            elif result == 'ignored':
                                TRACE('Case filter ignored: %r', lp)
                                kill = True
                            elif not is_watched_filename(lp.basename, self.is_directory(lp)):
                                TRACE('Ignoring unwatched file: %r', lp)
                                to_batch.append(self.local_to_server(lp).lower())
                                kill = True
                            if kill:
                                to_kill.append((local_key, deets))
                            else:
                                hashable.append(deets)

                        deletes_to_commit = [ self.deleted_details(self.cache.root_relative_server_path(ent.server_path.lower(), ctor=NsRelativePathMemory)) for ent in self.cache.get_local_details_batch(to_batch, lower=False) if ent.size >= 0 ]
                        self._set_pending_and_clear_blockrefs(deletes_to_commit, [])
                        self.to_hash.checked_remove(dict(to_kill))

                    spl2local = dict(((self.local_to_server(hash_deets.local_path).lower(), hash_deets.local_path) for hash_deets in hashable if hash_deets.attrs))
                    lp2info = dict(((spl2local[ent.server_path.lower()], ent) for ent in self.cache.get_local_details_batch(spl2local, lower=False) if ent.size >= 0))
                    attrs_whitelist = self.cache.get_attrs_whitelist()
                    return (hashable, lp2info, attrs_whitelist)

    def update_status_ui(self):
        COUNT_FTN = {'download': self.get_reconstruct_count,
         'hash': self.get_hash_count,
         'upload': self.get_upload_count}
        FAILURE_FTN = {'hash': lambda : self.to_hash.counts()[1]}
        LAST_FILENAME_FTN = {'download': self.get_reconstruct_filename,
         'hash': self.get_hash_filename,
         'upload': self.get_upload_filename}
        SIZE_FTN = {'download': self.download_queue_size,
         'upload': self.upload_queue_size}
        STATUS_OBJECTS = {'download': self.status.download_status,
         'hash': self.status.hash_status,
         'upload': self.status.upload_status}
        with self.cache.read_lock():
            for status_type in COUNT_FTN.keys():
                try:
                    status_object = STATUS_OBJECTS[status_type]
                    count = COUNT_FTN[status_type]()
                    last_filename = LAST_FILENAME_FTN[status_type]()
                    try:
                        size_ftn = SIZE_FTN[status_type]
                    except KeyError:
                        size = num_hashes = None
                    else:
                        size, num_hashes = size_ftn()

                    try:
                        failure_ftn = FAILURE_FTN[status_type]
                    except KeyError:
                        failures = None
                    else:
                        failures = failure_ftn()

                    status_object.set_file_count(count, size, num_hashes, last_filename=last_filename, failures=failures)
                except Exception:
                    unhandled_exc_handler()

    @staticmethod
    def root_relative_parent(child):
        if child == u'/':
            return u'/'
        else:
            found = child.rindex(u'/')
            if found == 0:
                return u'/'
            return child[:found]

    def hashing_status(self, server_path, local_path = None):
        if not local_path:
            local_path = self.server_to_local(server_path)
        else:
            local_path = self.normalized_local_path(local_path)
        with self.to_hash:
            exists = self.to_hash.get(local_path)
            if exists:
                a = self.to_hash.is_failing(local_path)
                if not a:
                    return 'in progress'
                return a
            return

    def commit_info_print(self, x):
        if type(x) is dict:
            return '%s:%r (%s bytes, target_ns: %r)' % (x['ns_id'],
             x['path'],
             x['size'],
             x['target_ns'])
        else:
            return '%s:%r (%s bytes)' % (x[0], x[1], x[4])

    def commit_info_from_details(self, details, target_ns = None):
        ns, rel = details.server_path.ns_rel()
        if self.server_supports_attrs:
            if target_ns is None:
                target_ns = self.target_ns(details.server_path)
            if details.size >= 0:
                toupdate = [ (plat, None) for plat in self.attr_handler.whitelist if plat not in details.attrs.attr_dict and plat not in details.attrs.data_plats ]
                if toupdate:
                    attr_dict = dict(details.attrs.attr_dict)
                    attr_dict.update(toupdate)
                else:
                    attr_dict = details.attrs.attr_dict
            else:
                attr_dict = frozendict()
            pa = getattr(details, 'parent_attrs', None)
            if pa is not None:
                pa = pa.attr_dict
            toret = {'ns_id': ns,
             'path': rel,
             'parent_blocklist': getattr(details, 'parent_blocklist', None),
             'blocklist': details.blocklist,
             'size': details.size,
             'mtime': details.mtime,
             'is_dir': bool(details.dir),
             'parent_attrs': pa,
             'attrs': attr_dict,
             'target_ns': target_ns}
            if feature_enabled('fileids'):
                guid = getattr(details, 'guid', None)
                guid_rev = getattr(details, 'parent_guid_rev', None)
                assert guid_rev is None and guid is None or guid_rev is not None and guid is not None, "Can't have guid without guid rev: %r %r" % (guid, guid_rev)
                toret['file_id_gid'] = guid
                toret['file_id_rev'] = guid_rev
            return toret
        else:
            return (ns,
             rel,
             getattr(details, 'parent_blocklist', None),
             details.blocklist,
             details.size,
             details.mtime,
             details.dir)

    def convert_file_journal_entry(self, ent):
        path = self.server_local_mapper.convert_root_relative(NsRelativePathFast(*server_path_ns_rel_unicode(ent[1])), lowered=not self.case_sensitive)
        deets = ReindexDetails(fj_id=ent[0], dir=ent[2], size=ent[3], mtime=ent[4], ctime=ent[5], attrs=ent[6], filename=ent[7], machine_guid=ent[8])
        return (path, deets)

    def get_all_local_details_under_relative_root_iterator(self, root, handler = None):
        return itertools.imap(self.convert_file_journal_entry, self.cache.get_all_local_details_under_relative_root_iterator(self.server_local_mapper.convert_local(root), case_sensitive=self.case_sensitive))

    def get_immediate_local_details_under_relative_root(self, root, path):

        def handler(elts):
            return [ self.convert_file_journal_entry(elt) for elt in elts ]

        root_relative = self.server_local_mapper.convert_local(path)
        return self.cache.get_immediate_local_details_under_relative_root(root_relative, handler=handler, case_sensitive=self.case_sensitive)

    def add_cache_error_callbacks(self, callback):
        self.to_hash.add_error_callback(callback)

    def remove_cache_error_callbacks(self, callback):
        self.to_hash.remove_error_callback(callback)

    def _handle_reconstruct_helper(self, hashes_added, hashes_removed):
        for _hash in hashes_added:
            self.r_hashes_to_prune.discard(_hash)

    def _handle_hash_helper(self, hashes_added, hashes_removed):
        for _hash in hashes_added:
            self.h_hashes_to_prune.discard(_hash)

    def _prune_sigstore_hashes(self, hashes_to_prune):
        TRACE('Pruning %d hashes mistakenly added to the sigstore' % (len(hashes_to_prune),))
        try:
            hashes_with_references = self.cache.hashes_with_references(hashes_to_prune)
            self.sigstore.delete((_hash for _hash in hashes_to_prune if _hash not in hashes_with_references))
        except:
            unhandled_exc_handler()

    @staticmethod
    def _access_interval_fn(old):
        if old is None:
            return 1
        return min(2 * old, 1800)

    def _set_pending_and_clear_blockrefs(self, batch_list, hashes_to_prune):
        if not batch_list:
            return
        self.h_hashes_to_prune = hashes_to_prune
        self.cache.add_block_reference_callback(self._handle_hash_helper)
        try:
            self.cache.set_pending_hash_batch(batch_list)
        except:
            exc = sys.exc_info()
            try:
                if self.h_hashes_to_prune:
                    try:
                        self.sigstore.delete(self.h_hashes_to_prune)
                    except:
                        unhandled_exc_handler()

                raise exc[0], exc[1], exc[2]
            finally:
                del exc

        else:
            if self.h_hashes_to_prune:
                self._prune_sigstore_hashes(self.h_hashes_to_prune)
        finally:
            self.cache.remove_block_reference_callback(self._handle_hash_helper)
            self.h_hashes_to_prune = None

    def handle_hash_results(self, pending, hashes_to_prune):
        with self.start_stop_lock:
            with self.set_event_on_state_change():
                if not self.running:
                    return
                batch_list = []
                droplist = []
                retry_list = []
                cur_whitelist_hash = self.attr_handler.get_whitelist_hash()
                for ent, deets, item, recurse, whitelist_hash in pending:
                    local_path = deets.local_path
                    to_hash_key = self.normalized_local_path(local_path)
                    if deets != self.to_hash.get(to_hash_key):
                        TRACE('File %r has changed since we hashed it, ignoring...', local_path)
                        continue
                    if whitelist_hash != cur_whitelist_hash:
                        TRACE('Whitelist has changed since we hashed %r, ignoring...', local_path)
                        continue
                    hash_result = ent if type(ent) is str else ent[0]
                    root_relative_path = self.local_to_root_relative(local_path, ctor=NsRelativePathMemory)
                    if hash_result == HASH_DELETED:
                        batch_list.append(self.deleted_details(root_relative_path))
                        droplist.append((to_hash_key, deets))
                    elif hash_result in [HASH_ACCESS, HASH_UNKNOWN]:
                        retry_list.append((deets,
                         to_hash_key,
                         hash_result,
                         self._access_interval_fn))
                    elif hash_result == HASH_BUSY:
                        retry_list.append((deets,
                         to_hash_key,
                         hash_result,
                         _FILE_BUSY_HASH_RETRY_INTERVAL))
                    elif hash_result == HASH_DROP:
                        droplist.append((to_hash_key, deets))
                    elif hash_result == HASH_SUCCESS:
                        batch_list.append(ent[1].copy(server_path=root_relative_path))
                        droplist.append((to_hash_key, deets))
                    else:
                        report_bad_assumption('Unhandled hash_result: %r' % (hash_result,))
                        droplist.append((to_hash_key, deets))

                with self.cache.write_lock():
                    self._set_pending_and_clear_blockrefs(batch_list, hashes_to_prune)
                self.to_hash.checked_remove(dict(droplist))
                for args in retry_list:
                    with self.to_hash:
                        if args[0] == self.to_hash.get(args[1]):
                            self.to_hash.retry(*args[1:])

        self.callbacks.run_handlers(HASH, batch_list)

    def _prune_downloaded_hashes(self, hashes):
        try:
            deleted_hashes = [0]
            total_hashes = [0]

            def loop_delete_helper(dirent):
                fn = dirent.name
                if len(fn) == DROPBOX_HASH_LENGTH and fn.replace(u'-', u'a').replace(u'_', u'a').isalnum():
                    total_hashes[0] += 1
                    if hashes is None or fn in hashes:
                        self.fs.remove(self.cache_path.join(fn))
                        deleted_hashes[0] += 1
                        return True

            with self.fs.opendir(self.cache_path) as _dir:
                loop_delete(_dir, loop_delete_helper)
            if total_hashes[0]:
                TRACE('Pruned %r of %r downloaded hashes', deleted_hashes[0], total_hashes[0])
        except:
            unhandled_exc_handler()

    def get_root_namespaces(self):
        toret = self.cache.get_root_namespaces()
        assert_(lambda : len(toret) == 1, 'More than one root namespace??')
        return toret

    def _is_monitored(self, local_path, local_path_lowered = None):
        _child = self.normalized_local_path(local_path)
        _parent = self.normalized_local_path(self.dropbox_folder)
        return _parent.is_parent_of(_child)

    def is_monitored(self, local_path, local_path_lowered = None):
        return self._is_monitored(self.arch.make_path(local_path), local_path_lowered)

    def is_dirty(self, server_path):
        lp = self.server_to_local(server_path)
        return self.to_hash.get(self.normalized_local_path(lp))

    def transfer_thread_func(self, the_thread, need_transfer_event, transfer_done_event, hash_transfer_func, waiting_cb = None):
        sync_engine = self
        if need_transfer_event is sync_engine.hash_download_event:
            status_object = sync_engine.status.download_status
            get_size_totals = sync_engine.download_queue_size
        else:
            status_object = sync_engine.status.upload_status
            get_size_totals = sync_engine.upload_queue_size
        initted = False
        while not the_thread.stopped():
            try:
                if not sync_engine.check_if_running(need_transfer_event.set):
                    sync_engine.set_thread_is_running(False)
                    status_object.set_file_count(None, 0, 0)
                    initted = False
                    with SimpleTimer('HashUploadThread slept in transfer_thread_func'):
                        need_transfer_event.wait()
                    continue
                sync_engine.set_thread_is_running(True)
                if not initted:
                    if need_transfer_event is sync_engine.hash_download_event:
                        if not sync_engine.check_if_initial_hash_is_done(need_transfer_event.set):
                            TRACE('Waiting for hash reindex event...')
                            need_transfer_event.wait()
                            continue
                    TRACE('Starting...')
                    initted = True
                bytes, count = get_size_totals()
                if not count:
                    if not the_thread.stopped() and sync_engine.running:
                        TRACE('Waiting for new blocks')
                        status_object.set_file_count(None, 0, 0)
                        with SimpleTimer('HashUploadThread slept in transfer_thread_func waiting for blocks'):
                            need_transfer_event.wait()
                    continue
                status_object.set_file_count(None, bytes, count)
                try:
                    with SimpleTimer('Ran upload_hash_set'):
                        ret = hash_transfer_func(the_thread, need_transfer_event)
                except Exception:
                    exc = sys.exc_info()
                    try:
                        try:
                            status_object.cancel_intermediate_transfer()
                        except Exception:
                            unhandled_exc_handler()

                        raise exc[0], exc[1], exc[2]
                    finally:
                        del exc

                TRACE('Done transferring hashes: %s', ret)
                transfer_done_event.set()
            except LowDiskSpaceError:
                TRACE('Low disk space, sleeping for a minute')
                time.sleep(60)
            except SyncEngineStoppedError:
                pass
            except (socket.error, DropboxServerError):
                unhandled_exc_handler(False)
                try:
                    status_object.reset_transfer_speed()
                except Exception:
                    unhandled_exc_handler()

                time.sleep(1)
            except Exception:
                unhandled_exc_handler()
                need_transfer_event.wait(1)

    def _upload_hash_thread(self, the_thread, upload_hash_set):
        self.transfer_thread_func(the_thread, self.hash_upload_event, self.upload_event, upload_hash_set)

    def _download_hash_thread(self, the_thread, download_hash_set):
        self.transfer_thread_func(the_thread, self.hash_download_event, self.reconstruct_event, download_hash_set)

    def get_uploadable(self):
        return self.cache.get_uploadable(lim=self.max_upload_count, priority_nses=self.root_nses)

    def get_reconstructable(self):
        return self.cache.get_reconstructable(lim=500, priority_nses=self.root_nses, partition=True)

    def get_disk_free_space(self, local_path):
        search = local_path
        while True:
            try:
                return self.fs.get_disk_free_space(search)
            except Exception:
                if search.is_root:
                    raise
                search = search.dirname

    def verify_disk_space(self, local_path, min_space = 0):
        try:
            free_space = self.get_disk_free_space(local_path)
        except KeyError:
            ret = False
        except Exception:
            unhandled_exc_handler()
            ret = False
        else:
            ret = free_space < min_space + self.MIN_FREE_SPACE

        self.status.set_status_label('low_disk_space', ret)
        if ret:
            raise LowDiskSpaceError(free_space, min_space + self.MIN_FREE_SPACE)

    def get_space_used(self):
        return fsutil.get_directory_usage(self.fs, self.dropbox_folder)

    def get_dropbox_file_count(self):
        return fsutil.get_directory_count(self.fs, self.dropbox_folder, count_dirs=True)

    def get_last_resync_time(self):
        return self.config.get('last_resync')

    def debug_output(self):
        with self.path_cache.lock:
            TRACE(u'path_cache (%d items): [ %s ]', len(self.path_cache.pending_count), ',\n    '.join([ repr(x) for x in itertools.islice(self.path_cache.pending_count.iterkeys(), 50) ]))

    def register_tag(self, tag, server_path):
        TRACE('Registering tag %r to path %r', tag, server_path)
        self.special_folders[tag] = (server_path, server_path.lower())

    def init_tags(self, ret):
        if isinstance(ret.get('ui_flags'), dict):
            potential_special_folders = (('public', u'/Public'),)
            for tag, path in potential_special_folders:
                if ret['ui_flags'].get('support_%s_folder' % tag, True):
                    self.register_tag(tag, path)
                elif tag in self.special_folders:
                    del self.special_folders[tag]

            self.deprecated_paths = [('photos', u'/Photos')]
            for tag, path in self.deprecated_paths:
                TRACE('Registering deprecated tag %r for path %r', tag, path)

    def _handle_list(self, ret):
        try:
            try:
                in_use, quota = ret['in_use'], ret['quota']
            except KeyError:
                pass
            else:
                if in_use < self.in_use or quota > self.quota:
                    if self.cache.quota_changed():
                        TRACE('Quota changed! in_use: %r vs %r, quota: %r vs %r', in_use, self.in_use, quota, self.quota)
                        self.upload_event.set()
                self.in_use, self.quota = in_use, quota

        except:
            unhandled_exc_handler()

        if isinstance(ret.get('ui_flags'), dict):
            try:
                self.max_upload_count = int(ret['ui_flags'].get('max_upload_count', self.max_upload_count))
                self.max_list_batch_count = int(ret['ui_flags'].get('max_list_batch_count', self.max_list_batch_count))
            except:
                unhandled_exc_handler()

            try:
                self.p2p_min_nonbatch_file_size = int(ret['ui_flags'].get('p2p_min_nonbatch_file_size', 200000))
            except:
                unhandled_exc_handler()

        self.init_tags(ret)
        if 'sandboxes' in ret:
            try:
                old_sandboxes = self.config.get('sandboxes', [])
                try:
                    s_old_sandboxes = set(old_sandboxes)
                except Exception:
                    self.config['sandboxes'] = []
                    s_old_sandboxes = set()

                new_sandboxes = list(set(ret['sandboxes']) | s_old_sandboxes)
                self.config['sandboxes'] = new_sandboxes
                for ns in set(new_sandboxes) - s_old_sandboxes:
                    sp = self.cache.mounted_at(ns)
                    if sp:
                        TRACE('Retagging application %r at %r', ns, sp)
                        try:
                            self._tag_folder(server_path=sp, tag='sandbox', ns=ns, retag=True)
                        except:
                            unhandled_exc_handler()

            except:
                unhandled_exc_handler()

        try:
            self.update_attrs(ret.get('attrs'), ret.get('max_inline_attr_size'))
        except:
            unhandled_exc_handler()

        if 'resync' in ret:
            try:
                TRACE('handle_list got command to resync!')
                self.queue_resync(ret['resync'])
            except:
                unhandled_exc_handler()

        try:
            self.server_limits = ret['limits']
        except KeyError:
            pass

        if 'list' in ret:
            self.callbacks.run_handlers(LIST, ret)
            last_revisions = self.cache.last_revisions()
            ns_set = frozenset(last_revisions)
            if last_revisions.get(self.main_root_ns) == -1:
                self.is_first_list = True
            self.handle_raw_list(ret['list'], dict_return=ret.get('dict_return'))
            if ns_set == frozenset(self.cache.get_all_tracked_namespaces()) and not ret.get('more_results') and not self.check_if_initial_list_is_done():
                TRACE('First list complete; letting other threads start')
                self.signal_initial_list_done()
                self.is_first_list = False
        if 'send_checksums' in ret:
            try:
                self.conn.send_checksums(self.cache.get_namespace_checksums_and_last_sjid())
            except:
                unhandled_exc_handler()

    def handle_raw_list(self, the_list, stop_callback = None, dict_return = False):
        try:
            for ents in batch(the_list, self.max_list_batch_count):
                if stop_callback and stop_callback():
                    return
                server_file_map = []
                server_file_set = set()
                for ent in ents:
                    if dict_return:
                        sjid = ent['client_sjid']
                        server_path = u'%s:%s' % (ent['ns_id'], ent['path'])
                        blocklist = ent['blocklist']
                        size = ent['size']
                        mtime = ent['mtime']
                        dir_ = ent['is_dir']
                        attrs = ent['attrs']
                        mount_request = ent.get('target_ns')
                        ts = ent.get('ts')
                        if feature_enabled('fileids'):
                            guid = ent.get('file_id_gid')
                            guid_rev = ent.get('file_id_rev')
                    else:
                        sjid, server_path, blocklist, size, mtime, dir_, attrs = ent
                        ts = None
                        mount_request = -dir_ if dir_ < 0 else None
                    if mount_request is not None:
                        dir_ = 1
                    if size < 0:
                        dir_ = 0
                    blocklist = str(blocklist)
                    if not is_nfc(server_path):
                        report_bad_assumption("Server path from server isn't NFC! %r", server_path)
                        continue
                    elif is_four_byte_unicode(server_path):
                        report_bad_assumption('Server path from is four byte unicode! %r', server_path)
                        continue
                    elif server_path[-1] == u' ' or server_path.find(u' /') >= 0:
                        report_bad_assumption('Server path from server ends in trailing white space! %r', server_path)
                        continue
                    elif server_path.find(u'\\') >= 0:
                        report_bad_assumption("Server path from server contained ''character! %r", server_path)
                        continue
                    elif not is_valid_blocklist(blocklist):
                        report_bad_assumption('Invalid blocklist for path %r from server: %r, ignoring entry', server_path, blocklist)
                        continue
                    try:
                        sp = ServerPath(server_path)
                    except ValueError:
                        report_bad_assumption('Invalid ServerPath for path %r', server_path)
                        continue

                    if size >= 0 and not is_watched_filename(sp.basename, dir_):
                        report_bad_assumption("Server path from server isn't watched! %r", server_path)
                        continue
                    if server_path in server_file_set:
                        raise Exception('Returned set contains duplicate %r' % (server_path,))
                    details = {'sjid': sjid,
                     'server_path': sp,
                     'blocklist': blocklist,
                     'size': size,
                     'mtime': mtime,
                     'dir': dir_,
                     'mount_request': mount_request,
                     'attrs': Attributes(attrs) if attrs else FrozenAttributes(),
                     'ts': ts}
                    if dict_return and feature_enabled('fileids'):
                        details['guid'] = guid
                        details['guid_rev'] = guid_rev
                    if dict_return:
                        try:
                            details['host_id'] = ent['host_id']
                        except KeyError:
                            pass

                    deets = FastDetails(**details)
                    server_file_map.append(deets)
                    server_file_set.add(server_path)

                with self.start_stop_lock:
                    with self.set_event_on_state_change():
                        TRACE('Updated: [ %s ]' % ',\n    '.join((self.rep_details(v) for v in server_file_map)))
                        self.cache.set_updated_batch(server_file_map)

        except Exception:
            unhandled_exc_handler()

    def reset_sjids(self, *n, **kw):
        return self.cache.reset_sjids(*n, **kw)

    def handle_list_dirs(self, the_list, stop_callback = None, update_last_sjid = False):
        root_ns_string = u'%d:/' % (self.main_root_ns,)
        last_sjid_map = {}
        try:
            _sorter = the_list.sort
        except AttributeError:
            the_list = sorted(the_list, key=lambda x: (0 if x['path'].startswith(root_ns_string) else server_path_ns_unicode(x['path']), len(x['path'])))
        else:
            _sorter()

        for ents in batch(the_list, self.max_list_batch_count):
            if stop_callback and stop_callback():
                return
            server_file_map = []
            for listed_ent in ents:
                if listed_ent['size'] < 0 or not listed_ent['dir'] or listed_ent['blocklist']:
                    report_bad_assumption('Bad entry from list_dirs(): %r', listed_ent)
                    continue
                server_path = listed_ent['path']
                if not is_nfc(server_path):
                    report_bad_assumption("Server path from server isn't NFC! %r", server_path)
                    continue
                elif is_four_byte_unicode(server_path):
                    report_bad_assumption('Server path from is four byte unicode! %r', server_path)
                    continue
                elif server_path[-1] == u' ' or server_path.find(u' /') >= 0:
                    report_bad_assumption('Server path from server ends in trailing white space! %r', server_path)
                    continue
                elif server_path.find(u'\\') >= 0:
                    report_bad_assumption("Server path from server contained '' character! %r", server_path)
                    continue
                sp = ServerPath(server_path)
                size, _dir, attrs = listed_ent['size'], listed_ent['dir'], listed_ent['attrs']
                if _dir < 0:
                    mount_request = -_dir
                    _dir = 1
                else:
                    mount_request = None
                if listed_ent['sjid'] > last_sjid_map.get(sp.ns, -1):
                    last_sjid_map[sp.ns] = listed_ent['sjid']
                server_file_map.append(FastDetails(sjid=listed_ent['sjid'], server_path=sp, blocklist='', size=size, mtime=listed_ent['mtime'], dir=_dir, mount_request=mount_request, attrs=Attributes(attrs) if attrs else FrozenAttributes()))

            with self.start_stop_lock:
                with self.set_event_on_state_change():
                    self.cache.set_updated_batch(server_file_map, update_last_sjid=update_last_sjid)

        return last_sjid_map

    @staticmethod
    def rep_details(item):
        if item.size == -1:
            detail_string = '(delete)'
        elif item.dir:
            mr = getattr(item, 'mount_request', None)
            detail_string = '(dir, mtime %s)' % item.mtime if not mr else '(mount %d)' % (mr,)
        else:
            detail_string = '(%s bytes%s, mtime %s)' % (item.size, '' if item.size == 0 else ', blocklist %s' % item.blocklist, item.mtime)
        return 'sjid %s: %r %s' % (item.sjid, item.server_path, detail_string)

    def _retag_special_folders(self):
        count = 0
        try:
            self._tag_folder(local_path=self.dropbox_folder, tag='dropbox')
            count += 1
        except:
            unhandled_exc_handler()

        for tag, (relpath, _) in self.special_folders.iteritems():
            fp = self.server_to_local(ServerPath.from_ns_rel(self.main_root_ns, relpath))
            TRACE('Tagging Folder %r to %r', fp, tag)
            try:
                self._tag_folder(local_path=fp, tag=tag)
                count += 1
            except FileNotFoundError:
                TRACE("Couldn't find special folder: %r, not tagging...", fp)
            except Exception:
                unhandled_exc_handler()

        for a in self.cache.get_mount_points():
            if self._ignore_set_should_ignore(self.cache.root_relative_server_path(a[0], ctor=NsRelativePathFast)):
                continue
            lp = self.server_to_local(a[0])
            try:
                TRACE('Tagging Folder %r to %r', lp, a[1])
                self._tag_folder(local_path=lp, tag='shared', ns=a[1])
                count += 1
            except FileNotFoundError:
                TRACE("Couldn't find special folder: %r, not tagging...", lp)
            except Exception:
                unhandled_exc_handler()

        for dep_tag, dep_path in self.deprecated_paths:
            sp = ServerPath.from_ns_rel(self.main_root_ns, dep_path)
            taginfo = self.get_tag_info(server_path=sp)
            tag = None
            ns = None
            if taginfo:
                tag, ns = taginfo
            if tag and tag != dep_tag or ns:
                TRACE('Not untagging folder %r for deprecated tag %r since its current tag is %r and ns is %r', dep_path, dep_tag, tag, ns)
                continue
            lp = self.server_to_local(sp)
            TRACE('Untagging folder %r from tag %r', lp, dep_tag)
            try:
                self._untag_folder(local_path=lp, preserve_nsfile=True)
            except Exception:
                unhandled_exc_handler()

        return count

    def _mount_callback_not_running(self, *n, **kw):
        try:
            self.p2p_state.update_active_namespaces(self.cache.get_all_tracked_namespaces())
        except Exception:
            unhandled_exc_handler()

    def _mount_callback(self, server_path, from_ns, is_destructive, to_ns):
        try:
            self.p2p_state.update_active_namespaces(self.cache.get_all_tracked_namespaces())
        except Exception:
            unhandled_exc_handler()

        if self._ignore_set_should_ignore(self.cache.root_relative_server_path(server_path, ctor=NsRelativePathFast)):
            return
        local_path = None
        if from_ns and to_ns:
            pass
        elif not self.is_first_list:
            if from_ns:
                local_path = self.server_to_local(server_path)
                if from_ns in self.config.get('sandboxes', []):
                    self.ui_kit.show_bubble(Bubble(BubbleKind.UNLINKED_APPLICATION, trans(u'The app folder "%(app_folder_name)s" was removed from your Dropbox.') % {'app_folder_name': local_path.basename}, trans(u'Unlinked Application')))
                elif is_destructive:
                    self.ui_kit.show_bubble(Bubble(BubbleKind.SHARED_FOLDER_REMOVED, trans(u'The shared folder "%(folder_name)s" was removed from your Dropbox.') % {'folder_name': local_path.basename}, trans(u'Shared Folder Removed')))
                else:
                    self.ui_kit.show_bubble(Bubble(BubbleKind.LEFT_SHARED_FOLDER, trans(u'You have left the shared folder "%(folder_name)s".') % {'folder_name': local_path.basename}, trans(u'Left Shared Folder')))
            if to_ns:
                if not local_path:
                    local_path = self.server_to_local(server_path)
                if to_ns in self.config.get('sandboxes', []):
                    msg_args = {'app_folder_name': local_path.basename}
                    msg_passive = trans(u'The app folder "%(app_folder_name)s" was created in your Dropbox.') % msg_args
                    msg = trans(u'The app folder "%(app_folder_name)s" was created in your Dropbox (click to view).') % msg_args
                    self.ui_kit.show_bubble(Bubble(BubbleKind.LINKED_APPLICATION, msg, trans(u'Linked Application'), self.bubble_context, self.bubble_context.make_sp_context_ref(server_path, True), msg_passive=msg_passive))
                else:
                    msg_args = {'folder_name': local_path.basename}
                    msg_passive = trans(u'The shared folder "%(folder_name)s" is now in your Dropbox.') % msg_args
                    msg = trans(u'The shared folder "%(folder_name)s" is now in your Dropbox (click to view).') % msg_args
                    self.ui_kit.show_bubble(Bubble(BubbleKind.JOINED_SHARED_FOLDER, msg, trans(u'Joined Shared Folder'), self.bubble_context, self.bubble_context.make_sp_context_ref(server_path, True), msg_passive=msg_passive))
        if not self.is_reconstructable(server_path):
            try:
                if to_ns:
                    self._tag_folder(tag='shared', server_path=server_path, ns=to_ns, resolve_conflict=True)
                elif from_ns:
                    if not is_destructive:
                        self._untag_folder(server_path=server_path)
            except:
                unhandled_exc_handler()

    def _untag_folder(self, server_path = None, local_path = None, preserve_nsfile = False):
        assert server_path or local_path
        if local_path is None:
            local_path = self.server_to_local(server_path)
        self.folder_tagger.untag_folder(local_path, preserve_nsfile=preserve_nsfile)
        self.arch.shell_touch(local_path)

    def get_tag_info(self, server_path = None, tag = None, ns = None):
        if tag is None:
            if ns is None:
                spl = server_path.lower()
                ns = self.target_ns(spl, lower=False)
            if ns:
                tag = 'shared'
            else:
                for _tag, (_, relpath_lower) in self.special_folders.iteritems():
                    if spl == ServerPath.from_ns_rel(self.main_root_ns, relpath_lower):
                        tag = _tag
                        break

        if tag is None:
            return
        if tag == 'shared':
            if ns is None:
                spl = server_path.lower()
                ns = self.target_ns(spl, lower=False)
            if ns in self.config.get('sandboxes', []):
                tag = 'sandbox'
        return (tag, ns)

    def _tag_folder(self, server_path = None, tag = None, ns = None, local_path = None, retag = False, resolve_conflict = False):
        assert server_path or local_path and tag
        if local_path is None:
            local_path = self.server_to_local(server_path)
        tag_info = self.get_tag_info(server_path, tag, ns)
        if not tag_info:
            return
        tag, ns = tag_info
        if retag:
            try:
                if self.folder_tagger.get_folder_ns(local_path) != ns:
                    return
            except Exception:
                unhandled_exc_handler()
                return

        if resolve_conflict:
            dot_dropbox_path = local_path.join(u'.dropbox')
            try:
                ia = self.fs.indexing_attributes(dot_dropbox_path)
            except FileNotFoundError:
                pass
            else:
                if ia.type == FILE_TYPE_DIRECTORY:
                    try:
                        self._resolve_conflict(dot_dropbox_path, u'.dropbox', trans(u'Conflicted Copy'))
                    except:
                        unhandled_exc_handler()

        self.arch.folder_tagger.tag_folder(local_path, tag, ns)
        self.arch.shell_touch(local_path)

    def tag_folder_if_special(self, server_path, local_path, resolve_conflict = False):
        self._tag_folder(server_path=server_path, local_path=local_path, resolve_conflict=resolve_conflict)

    def signal_initial_list_done(self):
        TRACE('Signaling initial list is done!')
        with self.initial_list_lock:
            self.initial_list_bool = True
        self._initial_list_callbacks.run_handlers()
        self._initial_list_callbacks.clear()

    def check_if_initial_list_is_done(self, callback = None):
        with self.initial_list_lock:
            if self.initial_list_bool:
                return True
            if callback:
                self._initial_list_callbacks.add_handler(callback)
            return False

    def signal_initial_reindex_done(self):
        with self.initial_reindex_lock:
            self.initial_reindex_bool = True
        self._initial_reindex_callbacks.run_handlers()
        self._initial_reindex_callbacks.clear()

    def check_if_initial_reindex_is_done(self, callback = None):
        with self.initial_reindex_lock:
            if self.initial_reindex_bool:
                return True
            if callback:
                self._initial_reindex_callbacks.add_handler(callback)
            return False

    def signal_initial_hash_done(self):
        self.status.set_initial_hash(False)
        with self.initial_hash_lock:
            TRACE('Signaling initial hash is done!')
            self.initial_hash_bool = True
        self._initial_hash_callbacks.run_handlers()
        self._initial_hash_callbacks.clear()

    def check_if_initial_hash_is_done(self, callback = None):
        with self.initial_hash_lock:
            if self.initial_hash_bool:
                return True
            if callback:
                self._initial_hash_callbacks.add_handler(callback)
            return False

    def attrs_data_plats(self):
        platforms = set(self.fs.supported_attributes(self.dropbox_folder))
        return platforms

    def get_metadata(self, file_path, whitelist):
        toret = {}
        return toret

    def _handle_update_attrs_rehash(self, to_rehash_iter):
        self._dirty_files_no_start_lock((DirectoryEvent(self.server_to_local(x)) for x in to_rehash_iter), recurse=0)

    def _update_attrs(self, new_whitelist, new_max_inline_attr_size):
        if new_whitelist is not None:
            self.server_supports_attrs = True
        readable_plats = self.attrs_data_plats() if self.dropbox_folder else None
        if new_whitelist is not None:
            self.attr_handler.update(new_whitelist)
        if new_max_inline_attr_size is not None:
            self.attr_handler.update_attr_size(new_max_inline_attr_size)
        should_reindex = self.cache.update_attrs_parameters(readable_plats, new_whitelist)
        if should_reindex:
            TRACE('Readable attrs have changed. Reindexing... \nNew plats: %s\nNew whitelist:%s' % (pprint.pformat(readable_plats), pprint.pformat(new_whitelist)))
            self._queue_reindex()

    def update_attrs(self, new_whitelist, new_max_inline_attr_size):
        with self.start_stop_lock:
            with self.set_event_on_state_change():
                self._update_attrs(new_whitelist, new_max_inline_attr_size)

    def _queue_reindex(self, path = None):
        path_to_reindex = self.dropbox_folder if path is None else path
        TRACE('Queueing a reindex on %r...', path_to_reindex)
        self.reindex_queue.put(path_to_reindex)

    def is_changed(self, u_local_path):
        if not self.running:
            return FileSyncStatus.UNWATCHED
        local_path = self.arch.make_path(u_local_path)
        local_key = self.normalized_local_path(local_path)
        if local_key != self.normalized_local_path(self.dropbox_folder):
            val = self._should_ignore(local_path)
            if val and val != IGNORE_DROPBOX_WRITE_CODE:
                if val == IGNORE_UNWATCHED_CODE:
                    return FileSyncStatus.UNWATCHED
                if val == IGNORE_SELECTIVE_SYNC_CODE:
                    return FileSyncStatus.SELECTIVE_SYNC
                return FileSyncStatus.UNSYNCABLE
        else:
            if self.path_cache:
                return FileSyncStatus.SYNCING
            return FileSyncStatus.UP_TO_DATE
        if self.to_hash.is_failing(local_key):
            return FileSyncStatus.UNSYNCABLE
        try:
            if self.path_cache.is_changed(local_path=local_path):
                _status = self.cache.uploading_status(self.local_to_server(local_path))
                if _status and _status != 'in progress':
                    return FileSyncStatus.UNSYNCABLE
                return FileSyncStatus.SYNCING
            return FileSyncStatus.UP_TO_DATE
        except:
            unhandled_exc_handler()
            return FileSyncStatus.UNWATCHED

    def _stat_fail_ignore(self, local_path, e):
        if hasattr(e, 'winerror'):
            if e.winerror == 123:
                return IGNORE_INVALID_FILENAME_CODE
        else:
            if e.errno in (errno.ENAMETOOLONG, errno.EINVAL):
                return IGNORE_INVALID_FILENAME_CODE
            if e.errno == errno.ELOOP:
                return IGNORE_BAD_SYMLINK_CODE
        if e.errno in (errno.ENOENT, errno.ENOTDIR) and self.writes_to_ignore.should_ignore(unicode(local_path), -1, -1, False):
            return IGNORE_DROPBOX_WRITE_CODE
        return False

    def _stat_succeed_ignore(self, local_path, st):
        isdir = st.type == FILE_TYPE_DIRECTORY
        if not (isdir or st.type == FILE_TYPE_REGULAR):
            return IGNORE_NOT_REGULAR_FILE_CODE
        if self.writes_to_ignore.should_ignore(unicode(local_path), st.mtime, st.size, st.type == FILE_TYPE_DIRECTORY, st.ctime, machine_guid=st.machine_guid):
            return IGNORE_DROPBOX_WRITE_CODE
        return False

    def _should_ignore(self, local_path, stl = None):
        lp = self.normalized_local_path(local_path)
        if not self._is_monitored(lp):
            return IGNORE_UNWATCHED_CODE
        if lp == self.cache_path_l or self.cache_path_l.is_parent_of(lp):
            return IGNORE_CACHE_PATH_CODE
        ret = self.arch.should_ignore(local_path)
        if ret:
            return ret
        if self._ignore_set_should_ignore(self.server_local_mapper.convert_local(local_path, ctor=NsRelativePathFast)):
            return IGNORE_SELECTIVE_SYNC_CODE
        checker = lp
        while not checker.is_root and self._is_monitored(checker):
            if checker.basename[-1] == u' ':
                return IGNORE_WHITESPACE_PATH_CODE
            checker = checker.dirname

        if is_four_byte_unicode(unicode(local_path)):
            return IGNORE_FOUR_BYTE_UNICODE_CODE
        try:
            st = self.fs.indexing_attributes(local_path)
        except FileSystemError as e:
            val = self._stat_fail_ignore(local_path, e)
            if val:
                return val
        except Exception:
            unhandled_exc_handler()
            return IGNORE_UNKNOWN_CODE
        else:
            if stl:
                stl[0] = st
            val = self._stat_succeed_ignore(local_path, st)
            if val:
                return val

        return False

    def _resolve_conflict(self, old_local_path, filename, reason, attempt_move = False, dirname = None):
        if not dirname:
            dirname = old_local_path.dirname
        if attempt_move:
            newpath = dirname.join(filename)
            if not self.is_exists(newpath):
                try:
                    self.safe_move(old_local_path, newpath)
                    return newpath
                except Exception as e:
                    if isinstance(e, EnvironmentError):
                        if not hasattr(e, 'filename') or e.filename is None:
                            e.filename = newpath
                    raise e, None, sys.exc_info()[2]

        base, ext = split_extension(filename)
        for n in xrange(10000):
            new_fmt = '(%s%s)' % (reason, u' (%s)' % n if n else u'')
            new_filename = u'%s %s%s' % (base, new_fmt, ext)
            newpath = dirname.join_nfc_components(new_filename)
            if self.is_exists(newpath):
                continue
            try:
                self.arch.check_filename(newpath, is_delete=False, is_dir=False)
            except Exception as e:
                TRACE('Conflict path was not a valid filename: %r', e)
                raise

            if self.is_exists(old_local_path):
                try:
                    self.fs.rename(old_local_path, newpath)
                except Exception as e:
                    if isinstance(e, EnvironmentError):
                        if not hasattr(e, 'filename') or e.filename is None:
                            e.filename = newpath
                    raise e, None, sys.exc_info()[2]

            return newpath

        raise OverflowError

    def _handle_trailing_white_space(self, local_path):
        TRACE('handling white space conflict %r' % local_path)
        newname = local_path.basename.rstrip()
        if newname == local_path.basename:
            return
        attempt_move = True
        if not newname:
            attempt_move = False
        try:
            self._resolve_conflict(local_path, newname, trans(u'White Space Conflict'), attempt_move=attempt_move)
        except Exception:
            unhandled_exc_handler()

    def _handle_non_normalized_unicode_filename(self, local_path, head, tail, form):
        TRACE('handling non %r conflict %r', form, local_path)
        newbase = unicodedata.normalize(form, tail)
        if head.join(newbase) == local_path:
            return
        try:
            self._resolve_conflict(local_path, newbase, trans(u'Unicode Encoding Conflict'), attempt_move=True)
        except Exception:
            unhandled_exc_handler()

    def get_conflict_reason(self, server_path, ns = None):
        if server_path is not None:
            ns = server_path.ns
        display_name = dropbox_globals['displayname'] if ns == dropbox_globals['root_ns'] else dropbox_globals['userdisplayname']
        reason = trans(u"%(display_name)s's conflicted copy") % dict(display_name=display_name)
        reason += ' ' + time.strftime('%Y-%m-%d').decode('ascii')
        return reason

    def _dirty_files_ignore_helper(self, lp, evt, stl = None):
        val = self._should_ignore(lp, stl=stl)
        if val:
            TRACE('Ignoring %r (%s)', lp, val)
            if val == IGNORE_WHITESPACE_PATH_CODE and lp.basename[-1] == ' ':
                try:
                    self._handle_trailing_white_space(lp)
                except Exception:
                    unhandled_exc_handler()

            elif val in (IGNORE_INVALID_NFC_CODE, IGNORE_INVALID_NFD_CODE):
                proper_form = 'NFC' if val == IGNORE_INVALID_NFC_CODE else 'NFD'
                try:
                    self._handle_non_normalized_unicode_filename(lp, lp.dirname, lp.basename, proper_form)
                except Exception:
                    unhandled_exc_handler()

            return True

    def _handle_lower_case_conflict(self, oldpath, existing_path):
        TRACE('handling case conflict %r vs %r', oldpath, existing_path)
        try:
            self._resolve_conflict(oldpath, existing_path.basename, trans(u'Case Conflict'))
        except Exception:
            unhandled_exc_handler()

    _pending_count = 0

    def _dirty_files_unlocked(self, local_path_iter, recurse = -1, dont_invalidate = False, to_pop = 0):
        initial_pending_count = self._pending_count
        try:
            exceptional_type = local_path_iter.type
        except AttributeError:
            pass
        else:
            if exceptional_type == DirectoryEvent.TYPE_DROPPED_EVENTS:
                TRACE('Dropped file events detected.')
                self._queue_reindex()
            elif exceptional_type == DirectoryEvent.TYPE_WATCH_ERROR:

                def do_restart():
                    try:
                        self.stop()
                    except Exception:
                        unhandled_exc_handler()
                    else:
                        try:
                            self.start()
                        except Exception:
                            unhandled_exc_handler()

                threading.Thread(target=do_restart, name='RESTART').start()
            elif exceptional_type == DirectoryEvent.TYPE_WATCH_REMOVED:
                report_bad_assumption('Root was removed, restarting Dropbox')
                arch.util.restart()
                return
            return

        batch_deets = []
        batch_paths = []
        for evt in local_path_iter:
            try:
                ulp, evtype = evt.path, evt.type
            except AttributeError:
                ulp, evtype = evt, DirectoryEvent.TYPE_UNKNOWN

            try:
                ulp.dirname
            except AttributeError:
                lp = self.arch.make_path(ulp)
            else:
                lp = ulp
                ulp = unicode(lp)

            local_key = self.normalized_local_path(lp)
            if local_key in self.blocked_events:
                TRACE('Blocking file event for %r, reconstructing...', lp)
                self.to_event_later.add(evt)
                continue
            if self.cache_path.is_parent_of(lp):
                try:
                    origin = self.deleted_file_cache.file_touched(lp)
                    if origin:
                        reason = self.get_conflict_reason(None, ns=self.main_root_ns)
                        self._resolve_conflict(lp, origin.basename, reason, dirname=origin.dirname)
                        continue
                except Exception:
                    unhandled_exc_handler()

            stl = [None]
            if self._dirty_files_ignore_helper(lp, evt, stl=stl):
                continue
            st = stl[0]
            try:
                self._dwatcher(lp)
            except Exception:
                pass

            batch_deets.append((local_key, lp, evtype))
            batch_paths.append(local_key)

        all_deets = {self.normalized_local_path(d.local_path):d for d in self.to_hash.get_batch(batch_paths, lower=False)}
        batch = {}
        for local_key, lp, evtype in batch_deets:
            cur_hash_deets = all_deets.get(local_key)
            if cur_hash_deets and not cur_hash_deets.attrs and evtype == DirectoryEvent.TYPE_ATTR_ONLY:
                evtype = DirectoryEvent.TYPE_UNKNOWN
            if dont_invalidate and cur_hash_deets and not (cur_hash_deets.attrs and evtype != DirectoryEvent.TYPE_ATTR_ONLY):
                TRACE("%r already in TO_HASH, won't invalidate", lp)
            else:
                this_batch_deets = batch.get(lp)
                if this_batch_deets is not None:
                    if not (this_batch_deets[0].attrs and evtype != DirectoryEvent.TYPE_ATTR_ONLY):
                        continue
                    else:
                        del batch[lp]
                to_add = HashDetails(recurse=recurse, order=self._pending_count, local_path=lp, attrs=evtype == DirectoryEvent.TYPE_ATTR_ONLY)
                cur_to_pop = 5 + time.time() if is_temp_file(unicode(lp)) and st else (2 + time.time() if st and st.type != FILE_TYPE_DIRECTORY and not st.size and time.time() - st.mtime < 2 else (to_pop + time.time() if to_pop else 0))
                batch[lp] = (to_add, cur_to_pop)
                self._pending_count += 1

        self.to_hash.add_batch(batch.values())
        self.perf_tracker.event('to_hash_batched')
        return self._pending_count - initial_pending_count

    def _dirty_files_no_start_lock(self, *n, **kw):
        assert_(self.start_stop_lock.locked)
        if not self.running:
            return
        try:
            with self.to_hash:
                return self._dirty_files_unlocked(*n, **kw)
        finally:
            if self.get_hash_count():
                if not self.hash_event.is_set():
                    TRACE('Setting hash event!')
                self.hash_event.set()

    def dirty_files(self, *n, **kw):
        with self.start_stop_lock:
            return self._dirty_files_no_start_lock(*n, **kw)

    def dirty_file(self, local_path, **kw):
        return self.dirty_files([local_path], **kw)

    def _reconstruct_can_go(self, server_path, details):
        spl = server_path.lower()
        assert_(lambda : not self.cache.is_uploading(spl, lower=False) and self.cache.is_reconstructable(spl, lower=False) and self.cache.get_reconstructing(spl, lower=False) == details, 'State of FileCache changed during reconstruct! %r %r %r', self.cache.is_uploading(spl, lower=False), self.cache.is_reconstructable(spl, lower=False), self.cache.get_reconstructing(spl, lower=False), details)
        lp = self.server_local_mapper.server_to_local(server_path, ignore_case=not self.case_sensitive)
        local_key = lp if self.case_sensitive else lp.lower()
        with self.to_hash:
            if self.to_hash.get(local_key):
                return False
            self.blocked_events.add(local_key)
        try:
            local_details = self.cache.get_local_details_batch((spl,), lower=False)[0]
        except IndexError:
            local_details = None

        return (lp, local_details)

    def _ignore_change(self, local_path, mtime, size, is_dir, ctime = None, machine_guid = None):
        self.writes_to_ignore.ignore(unicode(local_path), mtime, size, is_dir, ctime=ctime, machine_guid=machine_guid)

    def _hacked_get_contents(self, _hash):
        s = self.contents(_hash, _already_have_sync_engine_lock=True, _already_have_file_cache_lock=True)
        add_sig_and_check(self.r_hashes_to_prune, self.sigstore, _hash, s)
        return s

    def _is_unreconstructable(self, details):
        lp = self.server_local_mapper.server_to_local(details.server_path)
        lpl = self.normalized_local_path(lp)
        if lpl == self.cache_path_l or self.cache_path.is_parent_of(lpl):
            TRACE('Not reconstructing %r, Cache Path', lpl)
            return True
        try:
            self.arch.check_filename(lp, details.size < 0, details.dir)
        except Exception as e:
            TRACE('Not reconstructing: %r', e)
            unhandled_exc_handler(False)
            return True

        return False

    def _eager_should_not_reconstruct(self, details, to_commit = None):
        try:
            if self._is_unreconstructable(details):
                if to_commit is not None:
                    to_commit.append((RECONSTRUCT_UNRECONSTRUCTABLE_CODE, details))
                return True
        except Exception:
            unhandled_exc_handler()

        try:
            hashes_waiting = []
            for _hash, parent_hash in self.iterate_hashes_details(details):
                if not self.have_locally(_hash):
                    hashes_waiting.append((_hash, parent_hash))

            if hashes_waiting:
                if to_commit is not None:
                    for _hash, parent in hashes_waiting:
                        try:
                            self._set_waiting_on(details.server_path, _hash, parent, details.size, details.blocklist)
                        except Exception:
                            unhandled_exc_handler()

                return True
        except Exception:
            unhandled_exc_handler()

        return False

    def _errstr_to_log_event_name(self, errstr):
        sanitized = errstr.replace(' ', '-').replace('_', '-')
        return '%s-error' % sanitized

    def _reconstruct_all(self, res):
        TRACE('Updated: %d', len(res))
        to_commit = []
        to_dirty = []
        ctx = self.reconstruct_ctx
        self.reconstruct_ctx = (to_commit, to_dirty)
        for details in res:
            should_not_reconstruct = self._eager_should_not_reconstruct(details, to_commit)
            if should_not_reconstruct:
                TRACE("Advisory checks show that we shouldn't reconstruct %r", details.server_path)
                continue
            try:
                success_ctx = _reconstruct(self, details, self.r_hashes_to_prune, self._hacked_get_contents, ctx, self.mtime_size_map)
            except SyncEngineStoppedError:
                break
            except Exception as e:
                errstr = reconstruct_error_from_exception(self.fs, e)
                event_name = self._errstr_to_log_event_name(errstr)
                to_report = {event_name: 1}
                to_report[errstr] = 1
                report_aggregate_event(event_name, to_report)
                if errstr in (RECONSTRUCT_UNKNOWN_CODE,
                 RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE,
                 RECONSTRUCT_BAD_LOCAL_DETAILS_CODE,
                 RECONSTRUCT_UNRECONSTRUCTABLE_CODE,
                 RECONSTRUCT_PERMISSION_DENIED_CODE):
                    unhandled_exc_handler()
                TRACE('Failed to reconstruct (%s %s) %r (%r)', errstr, str(e), details.server_path, details)
                if errstr == RECONSTRUCT_BAD_LOCAL_DETAILS_CODE:
                    to_dirty.append(e.local_path)
                    to_commit.append((errstr, details))
                elif errstr == RECONSTRUCT_NO_HASHES_CODE:
                    TRACE('Checking to see which hashes of %r were bad...', details.server_path)
                    to_download = []
                    for _hash, parent_hash in self.iterate_hashes_details(details):
                        if not self.have_locally_hard(_hash, _already_have_file_cache_lock=True, _already_have_sync_engine_lock=True):
                            TRACE("Didn't have %r for %r", _hash, details.server_path)
                            to_download.append((_hash, parent_hash))

                    if not to_download:
                        to_commit.append((RECONSTRUCT_HASHES_NOT_READY_CODE, details))
                    else:
                        for _hash, parent in to_download:
                            try:
                                self._set_waiting_on(details.server_path, _hash, parent, details.size, details.blocklist)
                            except Exception:
                                unhandled_exc_handler()

                else:
                    to_commit.append((errstr, details))
            else:
                TRACE('Finished reconstructing: %s, success details: %r', self.rep_details(details), success_ctx)
                to_commit.append(((RECONSTRUCT_SUCCESS_CODE, success_ctx), details))

        self.handle_reconstruct_run(to_commit)
        return to_commit

    def perform_reconstruct(self, *n, **kw):
        with self.start_stop_lock:
            if not self.running:
                return
            return self.__perform_reconstruct(*n, **kw)

    def __perform_reconstruct(self, ctx):
        TRACE('Reconstruct run...')
        self.status.set_status_labels(low_disk_space=False)
        self.update_status_ui()
        hashes_to_prune = set()
        mtime_size_map = _actually_reconstruct(self, self.cache.get_reconstructable(lim=50, priority_nses=self.root_nses), hashes_to_prune)
        if not mtime_size_map and self.status.is_true('low_disk_space'):
            return
        with self.cache.write_lock():
            with self.set_event_on_state_change():
                if not self.cache.get_reconstructable_count():
                    return
                self.reconstruct_ctx = ctx
                self.mtime_size_map = mtime_size_map
                self.r_hashes_to_prune = hashes_to_prune
                self.cache.add_block_reference_callback(self._handle_reconstruct_helper)
                try:
                    self.cache.perform_reconstruct(self._reconstruct_all, lim=50, priority_nses=self.root_nses)
                except:
                    exc = sys.exc_info()
                    try:
                        if self.r_hashes_to_prune:
                            try:
                                self.sigstore.delete(self.r_hashes_to_prune)
                            except:
                                unhandled_exc_handler()

                        raise exc[0], exc[1], exc[2]
                    finally:
                        del exc

                else:
                    if self.r_hashes_to_prune:
                        self._prune_sigstore_hashes(self.r_hashes_to_prune)
                finally:
                    to_commit, to_dirty = self.reconstruct_ctx
                    if self.blocked_events:
                        self.blocked_events = set()
                        if self.to_event_later:
                            try:
                                self._dirty_files_no_start_lock(self.to_event_later)
                            except:
                                unhandled_exc_handler()
                            finally:
                                self.writes_to_ignore.clear()
                                self.to_event_later = set()

                        else:
                            self.writes_to_ignore.clear()
                    if to_dirty:
                        try:
                            self._dirty_files_no_start_lock(to_dirty)
                        except:
                            unhandled_exc_handler()

                    self.cache.remove_block_reference_callback(self._handle_reconstruct_helper)
                    self.reconstruct_ctx = None
                    self.mtime_size_map = None
                    self.r_hashes_to_prune = None

                hashes_to_prune_local = set(itertools.chain(*(itertools.chain(self.attr_handler.get_downloadable_blocklist(self.server_to_local(details.server_path), details.attrs), details.blocklist.split(',')) for result, details in to_commit if hasattr(result, '__getitem__') and result[0] == 'success'))) if self.get_reconstruct_count() else None
        self._prune_downloaded_hashes(hashes_to_prune_local)

    def _upload(self, res):
        res = iter(res)
        try:
            first_res = res.next()
        except StopIteration:
            TRACE('Given empty set to commit')
            return []

        if getattr(first_res, 'mount_request', None):
            details = first_res
            mount_type, target_ns = details.mount_request
            if mount_type == MOUNT_REQUEST_UNMOUNT:
                TRACE('Deleting mount point %r -> %s', details.server_path, target_ns)
                if details.server_path.ns != self.main_root_ns:
                    ret = {'sjid': UPLOAD_NO_ACCESS_CODE}
                else:
                    ret = self.conn.change_mount(target_ns, details.server_path.rel, None)
                if ret['sjid'] == UPLOAD_CONFLICT_CODE:
                    report_bad_assumption('Conflict on an unmount request, resyncing: %r :%r!' % (details.server_path, details.mount_request))
                    self.queue_resync()
                try:
                    rsjid = long(ret['sjid'])
                except (ValueError, KeyError):
                    pass
                else:
                    if rsjid > 1:
                        try:
                            rr_path = None
                            with self.config as config:
                                m_attempts = config.get('mount_attempts', frozendict())
                                try:
                                    rr_path, last_attempt = m_attempts[target_ns]
                                except (ValueError, TypeError, KeyError):
                                    pass
                                else:
                                    del m_attempts[target_ns]
                                    config['mount_attempts'] = m_attempts

                            if rr_path:
                                local_path = self.server_local_mapper.convert_root_relative(NsRelativePathFast(*server_path_ns_rel_unicode(rr_path)))
                                self._dirty_files_no_start_lock([local_path])
                        except:
                            unhandled_exc_handler()

                return ((ret['sjid'], details),)
            if mount_type == MOUNT_REQUEST_MOUNT:
                TRACE('Adding mount point %r -> %s', details.server_path, target_ns)
                if details.server_path.ns != self.main_root_ns:
                    ret = {'sjid': UPLOAD_NO_ACCESS_CODE}
                    try:
                        self._untag_folder(server_path=details.server_path, preserve_nsfile=True)
                    except:
                        unhandled_exc_handler()

                else:
                    ret = self.conn.change_mount(target_ns, None, details.server_path.rel)
                    if ret['sjid'] == UPLOAD_CONFLICT_CODE:
                        ret['sjid'] = UPLOAD_NO_ACCESS_CODE
                if ret['sjid'] == UPLOAD_NO_ACCESS_CODE:
                    try:
                        self._untag_folder(server_path=details.server_path, preserve_nsfile=True)
                    except:
                        unhandled_exc_handler()

                    try:
                        rr = unicode(self.cache.root_relative_server_path(details.server_path, ignore_case=False))
                        with self.config as config:
                            m_attempts = config.get('mount_attempts') or {}
                            m_attempts[target_ns] = (rr, time.time())
                            config['mount_attempts'] = m_attempts
                    except:
                        unhandled_exc_handler()

                return ((ret['sjid'], details),)
        commit_info = []
        res2 = []
        ts = time.time()
        for details in itertools.chain([first_res], res):
            if getattr(details, 'mount_request', None):
                report_bad_assumption("Can't do commit_batch on changes to mount points! %r", details)
                continue
            res2.append(details)
            commit_info.append(self.commit_info_from_details(details))

        TRACE('Committing (%r, %d entries):\n[ %s ]', self.upload_ctx.changeset_map, len(commit_info), ',\n    '.join([ self.commit_info_print(x) for x in commit_info ]))
        ts = time.time()
        file_ids_on = feature_enabled('fileids')
        with SimpleTimer('commit_batch called from _upload()'):
            ret = self.conn.commit_batch(commit_info, self.upload_ctx.changeset_map, False, extended_ret=True, allow_guid_sjid_hack=file_ids_on, return_file_ids=file_ids_on)
        if len(ret['results']) != len(commit_info):
            raise Exception('Bad commit results: %r' % (ret['results'],))
        TRACE('Commit batch took %r for %d files', time.time() - ts, len(commit_info))
        TRACE('... Results: %r', ret['results'])
        if 'changeset_id' in ret:
            self.upload_ctx.changeset_map = dict(((long(x), long(y)) for x, y in ret['changeset_id'].iteritems()))
        need_blocks = frozenset(ret.get('need_blocks', ()))
        results = ret['results']

        def feed_into_handle_commit():
            files_with_dirty_attrs = []
            for tup in itertools.izip(results, res2):
                if tup[0] == UPLOAD_NEED_BLOCKS_CODE:
                    deets = tup[1]
                    if self.is_dirty(deets.server_path):
                        yield (UPLOAD_NEED_BLOCKS_HASHING_CODE, deets)
                    else:
                        regular_blocklist = deets.blocklist.split(',') if deets.blocklist else ()
                        if need_blocks:
                            target_fn = self.server_to_local(deets.server_path)
                            if self.attr_handler.try_remove_preserved_blocks(target_fn, need_blocks):
                                files_with_dirty_attrs.append(target_fn)
                        attrs_blocklist = get_attrs_blocklist(deets.attrs)
                        if not (regular_blocklist or attrs_blocklist):
                            report_bad_assumption("We got a 'nb' result even though this file had empty blocklists?? %r" % (deets,))
                        blocks_needed = [ (_hash, parent_hash) for _hash, parent_hash in self.iterate_hashes_details(deets) if _hash in need_blocks ]
                        if not blocks_needed:
                            report_bad_assumption("We got a 'nb' result but none of the blocks in our blocklist were actually needed")
                            yield (create_extended_upload_code('bad_nb'), deets)
                        else:
                            for _hash, parent_hash in blocks_needed:
                                try:
                                    self._set_upload_waiting_on(deets.server_path, _hash, parent_hash, deets.size, deets.blocklist)
                                except Exception:
                                    unhandled_exc_handler()

                else:
                    yield tup

            if files_with_dirty_attrs:
                self._dirty_files_no_start_lock(files_with_dirty_attrs)

        return feed_into_handle_commit()

    def perform_upload(self, *n, **kw):
        with self.start_stop_lock:
            if not self.running:
                return
            return self._perform_upload(*n, **kw)

    def _perform_upload(self, ctx):
        self.update_status_ui()
        self.conn.get_conn_for_url('commit_batch').wait_for_chillout('commit_batch')
        with self.cache.write_lock():
            with self.set_event_on_state_change():
                if not self.cache.get_uploadable_count():
                    return
                self.upload_ctx = ctx
                file_limit = self.max_upload_count or 16
                try:
                    while True:
                        try:
                            self.cache.perform_upload(self._upload, lim=file_limit, priority_nses=self.root_nses)
                            break
                        except RequestDataOversizeError as ex:
                            if file_limit == 1:
                                report_bad_assumption('Commit batch failed with client-side RequestDataOversizeError and a file_limit of 1. This is a programming error.')
                                raise
                            else:
                                if ex.item_count is not None:
                                    file_limit = ex.item_count
                                file_limit = max(1, file_limit / 2)
                                TRACE('Decreasing file limit to %d and trying request again...', file_limit)

                finally:
                    self.upload_ctx = None

    def queue_resync(self, resync_timestamp = None):
        if resync_timestamp is None:
            resync_timestamp = int(time.time())
        if resync_timestamp == self.config.get('last_resync'):
            TRACE('Ignoring resync request for %s (already complete)', resync_timestamp)
            return
        report_bad_assumption('Resyncing the client!')
        self.config['last_resync'] = resync_timestamp
        arch.util.restart()

    def reset_sync_state(self):
        TRACE('Resetting all sync state...')
        with self.cache.write_lock():
            self.updated_hash_queue.clear()
            self.upload_hash_queue.clear()
        root_nses = self.cache.get_root_namespaces()
        self.cache.clear()
        for root_ns in root_nses:
            self.cache.add_root_ns(root_ns)

    def _check_resync(self):
        if self.config.get('last_resync') == self.config.get('last_resync_done'):
            return
        TRACE('Soft resync starting. (timestamp %s)', self.get_last_resync_time())
        try:
            self.reset_sync_state()
        except:
            TRACE('Soft resync failed!')
            unhandled_exc_handler()
        else:
            TRACE('Soft resync succeeded!')
            self.config['last_resync_done'] = self.get_last_resync_time()

    def wait_for_directory_watch(self):
        if not self.dirty_watch:
            return
        while True:
            error = False
            try:
                self.dirty_watch_ready.wait()
            except:
                unhandled_exc_handler()
                error = True
            else:
                if not self.is_directory(self.dropbox_folder):
                    self.file_events.remove_watch(self.dirty_watch)
                    error = True
                    if not self.is_exists(self.dropbox_folder):
                        report_bad_assumption('Root was removed before watch added, restarting Dropbox')
                        arch.util.restart()
                        return
                else:
                    break

            if error:
                self.status.set_status_labels(starting=False, cant_mount_dropbox=True)
                time.sleep(60)
                self.status.set_status_labels(starting=True, cant_mount_dropbox=False)
                self.dirty_watch, self.dirty_watch_ready = self.file_events.add_watch_async(unicode(self.dropbox_folder), functools.partial(self.dirty_files, to_pop=self.arch.hash_wait_time))

    def get_system_time_tuple(self):
        self.start_os_time = sum(os.times()[:2])
        utime, stime = os.times()[:2]
        return (time.time(), utime, stime)

    def _start(self):
        stopped_bang = AutoResetEvent()
        if not self.check_if_stopped(stopped_bang.set, already_locked=True):
            self.start_stop_lock.release_write()
            try:
                stopped_bang.wait()
            finally:
                self.start_stop_lock.acquire_write()

        if self.running:
            report_bad_assumption('Multiple simultaneous start calls, ignoring because we are already running')
            return
        TRACE('Starting sync engine')
        if not self.dropbox_folder:
            raise Exception('Dropbox folder has not yet been initted!')
        self._check_resync()
        if not self.is_exists(self.dropbox_folder):
            report_bad_assumption('Root was removed before watch added, restarting Dropbox')
            arch.util.restart()
            return
        try:
            t_start = time.time()
            tagged = self._retag_special_folders()
            TRACE('Took %f seconds to tag %d special folders' % (time.time() - t_start, tagged))
        except:
            unhandled_exc_handler()

        TRACE('Attributes whitelist: \n%s', pprint.pformat(self.attr_handler.whitelist))
        self.status.set_initial_hash(True)
        self.start_times = self.get_system_time_tuple()
        self.dirty_watch, self.dirty_watch_ready = self.file_events.add_watch_async(unicode(self.dropbox_folder), functools.partial(self.dirty_files, to_pop=self.arch.hash_wait_time))
        if not self._caches_populated:
            self.cache.remove_mount_callback(self._mount_callback_not_running)
            self.cache.add_mount_callback(self._mount_callback)
            try:
                self.cache.refilter_queues()
            except InvalidDatabaseError:
                unhandled_exc_handler()
                self.reset_sync_state()

            self._caches_populated = True
        self.running_state = RUNNING
        self._running_state_callbacks[RUNNING].run_handlers()
        self._running_state_callbacks[RUNNING].clear()
        self.callbacks.run_handlers(START)

    def start(self, _already_have_start_stop_lock = False):
        if not _already_have_start_stop_lock:
            self.start_stop_lock.acquire_write()
        try:
            self._start()
        except:
            report_bad_assumption('Exception while starting sync engine?')
            raise
        finally:
            if not _already_have_start_stop_lock:
                self.start_stop_lock.release_write()

        try:
            self.clear_shell_state(timeout=0)
        except Exception:
            unhandled_exc_handler()

    def clear_shell_state(self, timeout = 2):
        self.arch.clear_shell_state(self.dropbox_folder, timeout)

    def restart(self, _already_have_start_stop_lock = False):
        self.stop(_already_have_start_stop_lock=_already_have_start_stop_lock, _restart=True)

    def close(self, do_join = True, timeout = None):
        _t = time.time()
        self.stop(do_join=do_join, timeout=timeout)
        if timeout is None:
            timeout -= time.time() - _t
        for t in self.threads:
            TRACE('Calling stop on %r', t)
            t.signal_stop()
            TRACE('Signaled %r!', t)
            if do_join:
                _t = time.time()
                t.join(max(0, timeout))
                if timeout is not None:
                    if timeout < 0:
                        raise Exception('Timeout reached!')
                    timeout -= time.time() - _t

    def stop(self, do_join = True, clear_caches = False, _already_have_start_stop_lock = False, _restart = False, shell_touch = True, timeout = None):
        if not self.running:
            return False
        self.running_state = STOPPING
        if not _already_have_start_stop_lock:
            self.start_stop_lock.acquire_write()
        self.start_stop_lock.release_write()
        try:
            TRACE('Stopping sync engine')
            started = time.time()
            for thr in self.threads:
                TRACE('Calling wakeup for %s', thr.getName())
                try:
                    thr.set_wakeup_event()
                except:
                    unhandled_exc_handler()

            if do_join:
                TRACE('Trying to wait on all running threads that matter to stop')
                while not frozenset((klass for klass, running, inst in self.threads.itervalues() if not running)).issuperset(self.threads_to_wait_on):
                    TRACE('%r are still running' % [ thr.getName() for thr, (klass, running, inst) in self.threads.iteritems() if running ])
                    if timeout is not None and timeout < 0:
                        raise Exception('Timeout reached!')
                    time.sleep(0.25)
                    if timeout is not None:
                        timeout -= 0.25

                still_running = [ thr.getName() for thr, (klass, running, inst) in self.threads.iteritems() if running ]
                if still_running:
                    TRACE("%r are still running, but it's ok to move on now:", still_running)
            watch_is_closed = threading.Event()
            self.file_events.remove_watch(self.dirty_watch, on_close=watch_is_closed.set)
            if do_join:
                watch_is_closed.wait(max(0, timeout))
                if timeout is not None and timeout < 0:
                    raise Exception('Timeout Reached!')
        except:
            self.start_stop_lock.acquire_write()
            try:
                self.running_state = STOPPED
                self._running_state_callbacks[STOPPED].run_handlers()
                self._running_state_callbacks[STOPPED].clear()
            finally:
                self.start_stop_lock.release_write()

            unhandled_exc_handler()
            report_bad_assumption('Exception while stopping sync engine?')
            return False

        try:
            self.start_stop_lock.acquire_write()
            try:
                assert self.running_state == STOPPING, "We don't seem to be stopping anymore??"
                self.to_hash.clear()
                self.reindex_queue.clear()
                if clear_caches and self._caches_populated:
                    self.cache.clear_queues()
                    self.cache.remove_mount_callback(self._mount_callback)
                    self.cache.add_mount_callback(self._mount_callback_not_running)
                    self._caches_populated = False
                with self.initial_hash_lock:
                    self.initial_hash_bool = False
                with self.initial_reindex_lock:
                    self.initial_reindex_bool = False
                stop_took = time.time() - started
                if stop_took >= 30:
                    report_bad_assumption('Stopping sync engine took more than 30 seconds: %r' % (stop_took,))
                self.running_state = STOPPED
                self._running_state_callbacks[STOPPED].run_handlers()
                self._running_state_callbacks[STOPPED].clear()
                self.callbacks.run_handlers(STOP)
                if _restart:
                    self._start()
            finally:
                if not _already_have_start_stop_lock:
                    self.start_stop_lock.release_write()

        except:
            unhandled_exc_handler()
            report_bad_assumption('Exception while stopping sync engine?')

        try:
            if shell_touch:
                self.clear_shell_state(timeout=0)
        except:
            unhandled_exc_handler()

        return True

    @property
    def running(self):
        with self._running_state_lock:
            return self._running_state == RUNNING

    @property
    def stopped(self):
        with self._running_state_lock:
            return self._running_state == STOPPED

    def get_running_state(self):
        return self._running_state

    def set_running_state(self, value):
        with self._running_state_lock:
            self._running_state = value

    running_state = property(get_running_state, set_running_state)

    def set_thread_is_running(self, val):
        self.threads[threading.currentThread()][1] = val

    def _check_for_running_state(self, *n, **kw):
        with self.start_stop_lock:
            return self._check_for_running_state_unlocked(*n, **kw)

    def _check_for_running_state_unlocked(self, state, callback = None):
        assert self.start_stop_lock.locked(), 'sync_engine.start_stop_lock must be locked when calling check_for_running_state'
        with self._running_state_lock:
            if self._running_state == state:
                return True
            if callback:
                self._running_state_callbacks[state].add_handler(callback)
            return False

    def check_if_running(self, callback = None, already_locked = False):
        check_fn = self._check_for_running_state_unlocked if already_locked else self._check_for_running_state
        return check_fn(RUNNING, callback)

    def check_if_stopped(self, callback = None, already_locked = False):
        check_fn = self._check_for_running_state_unlocked if already_locked else self._check_for_running_state
        return check_fn(STOPPED, callback)

    def block_cache_have_locally(self, _hash):
        assert len(_hash) == DROPBOX_HASH_LENGTH
        return self.is_exists(self.cache_path.join(unicode(_hash)))

    def dfc_have_locally(self, _hash):
        return self.deleted_file_cache.who_has(_hash)

    def have_locally(self, _hash):
        assert len(_hash) == DROPBOX_HASH_LENGTH
        if self.block_cache_have_locally(_hash):
            TRACE('Block cache says we have %r locally', _hash)
            return True
        if self.dfc_have_locally(_hash):
            TRACE('Deleted files cache says we have %r locally', _hash)
            return True
        if self.dropbox_have_locally(_hash):
            TRACE('Block ref cache says we have %r locally', _hash)
            return True

    def have_locally_hard(self, _hash, _already_have_sync_engine_lock = False, _already_have_file_cache_lock = False):
        assert len(_hash) == DROPBOX_HASH_LENGTH
        try:
            self.contents(_hash, _already_have_file_cache_lock=_already_have_file_cache_lock, _already_have_sync_engine_lock=_already_have_sync_engine_lock)
        except BlockContentsError:
            return False
        except:
            unhandled_exc_handler()
            return False

        return True

    def _load_block(self, local_path, seek_pos, _hash, attr):
        TRACE('Recovering block %s from %r:%r', _hash, local_path, seek_pos)
        if seek_pos & 8796093022208L:
            assert attr, 'High bit in seek_pos set but no attrs passed! %r' % local_path
            plat, key, i = attr.get_location(seek_pos)
            if plat in metadata_plats():
                d = self.get_metadata(local_path, {plat: {key: {}}})
                s = d[plat][key][i * DROPBOX_MAX_BLOCK_SIZE:(i + 1) * DROPBOX_MAX_BLOCK_SIZE]
            else:
                s = self.attr_handler.get_attribute_block(attr, local_path, seek_pos)
        else:
            with self.fs.open(local_path) as f:
                with SimpleTimer('disk IO in _load_block', cumulative=True):
                    f.seek(seek_pos * DROPBOX_MAX_BLOCK_SIZE)
                    s = f.read(DROPBOX_MAX_BLOCK_SIZE)
        read_hash = dropbox_hash(s)
        TRACE('Read %s bytes (hash %s)', len(s), read_hash)
        if read_hash != _hash:
            raise BlockContentsBadDataError('Contents of %r@%s-%s do not match hash %s' % (local_path,
             seek_pos,
             seek_pos + len(s),
             _hash))
        return s

    def dropbox_contents(self, _hash, ns = None, _already_have_file_cache_lock = False, _already_have_sync_engine_lock = False):

        def dirty_file(local_path, *n, **kw):
            if _already_have_sync_engine_lock:
                return self._dirty_files_no_start_lock([local_path], *n, **kw)
            else:
                return self.dirty_files([local_path], *n, **kw)

        return self._dropbox_contents_internal(_hash, ns=ns, on_dirty=dirty_file, _already_have_file_cache_lock=_already_have_file_cache_lock)

    def _dropbox_contents_internal(self, _hash, ns = None, on_dirty = None, _already_have_file_cache_lock = False):
        with SimpleTimer('self.cache.who_has', cumulative=True):
            who_has = self.cache.who_has(_hash, ns=ns, lim=10)
        for server_path, seek_pos, attr in who_has:
            try:
                with SimpleTimer('self.server_to_local()', cumulative=True):
                    local_path = self.server_to_local(server_path)
            except NamespaceNotMountedError:
                continue
            except:
                unhandled_exc_handler()
                continue

            try:
                with SimpleTimer('_load_block', cumulative=True):
                    return self._load_block(local_path, seek_pos, _hash, attr)
            except EnvironmentError as e:
                unhandled_exc_handler(e.errno != errno.ENOENT)
            except (KeyError, BlockContentsError):
                unhandled_exc_handler(False)
            except Exception:
                unhandled_exc_handler()

            if self.cache.verify_backward_hash_reference_consistency(server_path, repair=not _already_have_file_cache_lock, lower=False):
                TRACE('Requeuing file %r' % local_path)
                if on_dirty:
                    on_dirty(local_path, dont_invalidate=True)
            else:
                report_bad_assumption("Hash reference wasn't consistent: %r:%r:%r" % (_hash, server_path, seek_pos))

        raise BlockContentsNotFoundError('Contents of %s not available' % (_hash,))

    def dfc_contents(self, _hash):
        assert len(_hash) == DROPBOX_HASH_LENGTH
        for local_path, seek_pos in self.deleted_file_cache.who_has(_hash):
            try:
                return self._load_block(local_path, seek_pos, _hash, None)
            except IOError:
                unhandled_exc_handler(False)
            except:
                unhandled_exc_handler()

            self.deleted_file_cache.delete_entry(local_path)

        raise BlockContentsNotFoundError('Contents of %s not available' % (_hash,))

    def block_cache_contents(self, _hash):
        return block_cache_contents(self.fs, self.cache_path, _hash)

    def contents(self, _hash, _already_have_sync_engine_lock = False, _already_have_file_cache_lock = False):
        assert len(_hash) == DROPBOX_HASH_LENGTH
        try:
            with SimpleTimer('block_cache_contents', cumulative=True):
                return self.block_cache_contents(_hash)
        except BlockContentsError:
            pass
        except Exception:
            unhandled_exc_handler()

        try:
            with SimpleTimer('dropbox_contents', cumulative=True):
                return self.dropbox_contents(_hash, _already_have_file_cache_lock=_already_have_file_cache_lock, _already_have_sync_engine_lock=_already_have_sync_engine_lock)
        except BlockContentsError:
            pass
        except Exception:
            unhandled_exc_handler()

        return self.dfc_contents(_hash)

    def change_directory_ignore_set(self, *n, **kw):
        self.status.set_status_label('selsync', True)
        try:
            with self.start_stop_lock:
                return self._change_directory_ignore_set(*n, **kw)
        finally:
            self.status.set_status_label('selsync', False)

    def change_directory_ignore_set_lite(self, new_directory_ignore_set):
        with self.start_stop_lock:
            with self.cache.write_lock():
                self.cache.change_directory_ignore_set(new_directory_ignore_set, case_sensitive=self.case_sensitive, queue=False).close()
                self.handle_change_directory_ignore(new_directory_ignore_set)

    def _change_directory_ignore_set(self, new_directory_ignore_set, queue = True):
        assert_(lambda : all((a == a.lower() and type(a) is unicode for a in new_directory_ignore_set)))
        if not self.dropbox_folder:
            raise Exception('Dropbox folder has not yet been initted!')
        new_directory_ignore_set = frozenset(new_directory_ignore_set)

        def handle_dirty_files(local_path_batch, *n, **kw):
            hashes_to_prune = set()
            to_flush = []
            block_handler = functools.partial(add_sig_and_check, hashes_to_prune, self.sigstore)
            attrs_whitelist = self.cache.get_attrs_whitelist()
            for result, _lp in self._case_filter_local_paths((lpa for lpa in local_path_batch if not self._should_ignore(lpa)), exists=self.is_exists, dirname=self.hash_details_dirname):
                if result == 'ignored':
                    continue
                lp = _lp
                try:
                    st = self.fs.indexing_attributes(lp, write_machine_guid=True)
                except FileNotFoundError:
                    unhandled_exc_handler(False)
                except FileSystemError:
                    to_flush.append(self.deleted_details(self.server_local_mapper.convert_local(_lp)))
                except Exception:
                    unhandled_exc_handler()
                else:
                    try:
                        if not is_watched_filename(lp.basename, st.type == FILE_TYPE_DIRECTORY):
                            TRACE('Ignoring unwatched file: %r', lp)
                            continue
                        ret = _hash_dir(self, lp, st, block_handler, attrs_whitelist) if st.type == FILE_TYPE_DIRECTORY else _hash_file(self, lp, st, block_handler, attrs_whitelist, False)
                    except Exception:
                        unhandled_exc_handler()
                    else:
                        hash_result = ret if type(ret) is str else ret[0]
                        if hash_result == HASH_DELETED:
                            to_flush.append(self.deleted_details(self.server_local_mapper.convert_local(lp)))
                        elif hash_result == HASH_SUCCESS:
                            deets = ret[1].copy(server_path=self.server_local_mapper.convert_local(lp))
                            to_flush.append(deets)

            try:
                self._set_pending_and_clear_blockrefs(to_flush, hashes_to_prune)
            except:
                unhandled_exc_handler()

        def handle_dirty_events(local_path_batch):
            return handle_dirty_files((lp.path for lp in local_path_batch))

        def run_reindex(new_ignores):
            for rr in new_ignores:
                sp = self.cache.mount_relative_server_path(NsRelativePathFast(*server_path_ns_rel_unicode(rr)))
                _lp = self.server_to_local(sp)
                lp = _lp
                local_deets = self.cache.get_local_details_batch((sp,))
                is_dirty = False
                try:
                    st = self.fs.indexing_attributes(lp)
                except FileNotFoundError:
                    if local_deets:
                        is_dirty = True
                except Exception:
                    unhandled_exc_handler()
                    if local_deets:
                        is_dirty = True
                else:
                    if not local_deets:
                        is_dirty = True
                    elif st.type == FILE_TYPE_DIRECTORY:
                        if not local_deets[0].dir:
                            is_dirty = True
                    elif local_deets[0].dir or long(st.mtime) != local_deets[0].mtime or long(st.size) != local_deets[0].size or st.machine_guid != local_deets[0].machine_guid:
                        is_dirty = True

                if is_dirty:
                    handle_dirty_files((_lp,))
                try:
                    reindex_no_start_lock(self, self.dropbox_folder, _lp, handle_dirty_events, ctime_update=False)
                except FileNotFoundError:
                    pass
                except Exception:
                    unhandled_exc_handler()

        with self.cache.read_lock():
            new_ignores, new_unignores = self.cache.compute_ignore_changes(self.cache.get_directory_ignore_set(), new_directory_ignore_set)
            run_reindex(new_ignores)
            unsynced_exists = any((self.cache.unsynced_local_files_exist_under(self.cache.mount_relative_server_path(NsRelativePathFast(*server_path_ns_rel_unicode(rr)))) for rr in new_ignores))
        if unsynced_exists and not self.check_if_initial_list_is_done():
            ev = threading.Event()
            if not self.check_if_initial_list_is_done(ev.set):
                ev.wait()
        dirs_to_dirty = []
        with self.cache.write_lock():
            with self.set_event_on_state_change():
                new_ignores, new_unignores = self.cache.compute_ignore_changes(self.cache.get_directory_ignore_set(), new_directory_ignore_set)
                run_reindex(new_ignores)
                mv_failures = []
                for rr in new_unignores:
                    lp = self.server_to_local(self.cache.mount_relative_server_path(NsRelativePathFast(*server_path_ns_rel_unicode(rr))))
                    dirname, basename = lp.dirname, lp.basename
                    if not basename:
                        continue
                    basenamel = basename.lower()
                    if self.cache.server_dir_exists(ServerPath(rr), True):
                        try:
                            to_rename = [ name for name in fsutil.listdir(self.fs, dirname) if name.lower() == basenamel ]
                        except (NotADirectoryError, FileNotFoundError):
                            to_rename = ()
                        except Exception:
                            unhandled_exc_handler()
                            to_rename = ()

                        for rename in to_rename:
                            try:
                                local_path = dirname.join(rename)
                                self._resolve_conflict(local_path, rename, trans(u'Selective Sync Conflict'))
                            except Exception:
                                mv_failures.append(rr)

                    else:
                        dirs_to_dirty.extend(self.local_case_filenames(lp))

                if mv_failures:
                    TRACE('some unignores failed: %r' % (mv_failures,))
                    new_directory_ignore_set = frozenset(list(new_directory_ignore_set) + mv_failures)
                delete_handle = self.cache.change_directory_ignore_set(new_directory_ignore_set, case_sensitive=self.case_sensitive, queue=queue)
                self._dirty_files_no_start_lock((DirectoryEvent(x) for x in dirs_to_dirty))
                try:
                    self.handle_change_directory_ignore(new_directory_ignore_set)
                    delete_failures = 0
                    delete_successes = 0
                    for root_relative_path, mtime, size, blocklist, isdir, machine_guid in delete_handle:
                        ns_rel = NsRelativePathFast(*server_path_ns_rel_unicode(root_relative_path))
                        lp = self.server_local_mapper.convert_root_relative(ns_rel)
                        sp = self.cache.mount_relative_server_path(ns_rel)
                        deleted_fn = self.deleted_file_cache.get_filename(sp, mtime, size, blocklist) if not isdir else None
                        fail = True
                        try:
                            st = self.fs.indexing_attributes(lp)
                        except FileNotFoundError:
                            TRACE('Strange. %r was already deleted', lp)
                        except Exception:
                            unhandled_exc_handler()
                        else:
                            if (st.type == FILE_TYPE_DIRECTORY) != isdir or not isdir and (long(st.mtime) != mtime or long(st.size) != size or st.machine_guid != machine_guid):
                                report_bad_assumption('SELECTIVE SYNC: Synced file %r changed while sync engine was stopped, not deleting' % (lp,))
                            else:
                                try:
                                    if isdir:
                                        _delete_dir_and_unwatched(lp, self)
                                        self.arch.shell_touch(lp.dirname)
                                    elif all((self.dfc_have_locally(_hash) for _hash in blocklist.split(','))):
                                        try:
                                            self.fs.remove(lp)
                                        except FileNotFoundError:
                                            pass

                                    else:
                                        try:
                                            self.fs.remove(deleted_fn)
                                            TRACE('?? Deleted file %r already exists in cache?' % (deleted_fn,))
                                        except FileNotFoundError:
                                            pass
                                        except Exception as e:
                                            unhandled_exc_handler(isinstance(e, FileSystemError))

                                        try:
                                            self.safe_move(lp, deleted_fn)
                                        except Exception:
                                            unhandled_exc_handler(False)
                                            try:
                                                self.fs.remove(lp)
                                            except FileNotFoundError as e:
                                                pass

                                        else:
                                            self.deleted_file_cache.add_entry(deleted_fn, lp, sp, size, blocklist)

                                except:
                                    unhandled_exc_handler(False)
                                else:
                                    fail = False

                        if fail:
                            self.arch.shell_touch(lp)
                            delete_failures += 1
                        else:
                            delete_successes += 1

                    TRACE('SELECTIVE_SYNC: Deleted %d files successfully, %d failed', delete_successes, delete_failures)
                finally:
                    delete_handle.close()

                return mv_failures

    def move(self, new_path, warn, progress_callback = None, error_callback = None):
        return move_dropbox(self.fs.make_path(new_path), self, warn, progress_callback=progress_callback, error_callback=error_callback)

    def _set_waiting_on(self, server_path, hash_, parent = None, size = None, blocklist = None):
        with self.cache.write_lock():
            if hash_:
                self.updated_hash_queue.set_missing(server_path, hash_, parent, size, blocklist)
            else:
                self.updated_hash_queue.no_hashes_needed(server_path)

    def _set_upload_waiting_on(self, server_path, hash_, parent = None, size = None, blocklist = None):
        self.upload_hash_queue.set_missing(server_path, hash_, parent, size, blocklist)

    def got_hash(self, hash_):
        with self.cache.write_lock():
            self.updated_hash_queue.got_hash(hash_)

    def hash_uploaded(self, hash_):
        with self.cache.write_lock():
            self.upload_hash_queue.got_hash(hash_)

    def set_upload_error(self, hash_):
        self.upload_hash_queue.set_error(hash_)

    def set_download_error(self, hash_):
        self.updated_hash_queue.set_error(hash_)

    def next_needed_hash(self, **kw):
        return self.updated_hash_queue.next_needed_hash(**kw)

    def next_hash_batch_to_download(self, **kw):
        return self.updated_hash_queue.next_needed_hash_batch(max_hashes=self.server_limits.get('download_hash_batch_max', 1), max_size=self.server_limits.get('download_hash_batch_max_size', DROPBOX_MAX_BLOCK_SIZE), **kw)

    def next_hash_batch_to_upload(self, **kw):
        return self.upload_hash_queue.next_needed_hash_batch(max_hashes=self.server_limits.get('upload_hash_batch_max', 1), max_size=self.server_limits.get('upload_hash_batch_max_size', DROPBOX_MAX_BLOCK_SIZE), **kw)

    def hashes_to_upload(self):
        return self.upload_hash_queue.needed_hashes()

    def download_queue_size(self):
        return self.updated_hash_queue.get_size_totals()

    def upload_queue_size(self):
        return self.upload_hash_queue.get_size_totals()

    def commit_waiting_for_upload(self, server_path):
        return self.upload_hash_queue.is_waiting(server_path)

    @contextlib.contextmanager
    def set_event_on_state_change(self):
        assert self.start_stop_lock.locked()
        events_and_retry_fns = {'hash': (self.hash_event, self.hash_ready_time),
         'reconstruct': (self.reconstruct_event, self.cache.reconstruct_ready_time),
         'upload': (self.upload_event, self.cache.upload_ready_time),
         'hash download': (self.hash_download_event, self.updated_hash_queue.next_needed_hash_time),
         'hash upload': (self.hash_upload_event, self.upload_hash_queue.next_needed_hash_time)}
        events_to_retry_times = {}
        for event_name, (_, fn) in events_and_retry_fns.iteritems():
            events_to_retry_times[event_name] = None
            try:
                events_to_retry_times[event_name] = fn()
            except Exception:
                unhandled_exc_handler()

        try:
            yield
        finally:
            if not self.running:
                return
            for event_name, (event, fn) in events_and_retry_fns.iteritems():
                new_retry_time = None
                try:
                    new_retry_time = fn()
                except Exception:
                    unhandled_exc_handler()

                if not new_retry_time:
                    continue
                if not events_to_retry_times[event_name] or new_retry_time < events_to_retry_times[event_name]:
                    if not event.is_set():
                        TRACE('Setting %s event!', event_name)
                    event.set()

            self.update_status_ui()

    def get_queue_counts(self):
        return (self.get_hashable_count(),
         self.cache.get_uploadable_count(),
         self.cache.get_reconstructable_count(),
         self.upload_queue_size()[1],
         self.download_queue_size()[1])
