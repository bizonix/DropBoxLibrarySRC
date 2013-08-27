#Embedded file name: dropbox/file_cache/memory_cache_backend_wrapper.py
import contextlib
import functools
import itertools
import operator
from dropbox.attrs import FrozenAttributes
from dropbox.fastdetails import FastDetails
from dropbox.functions import batch
from dropbox.low_functions import add_inner_methods, add_inner_properties, compose, propagate_none
from dropbox.server_path import ServerPath
from dropbox.trace import TRACE
from . import constants as c
from .exceptions import InvalidDatabaseError
from .memory_caches import PendingFileSetWithFailure, UpdatedFileSetWithFailure
from .util import FlushBefore, updated_details_from_entry, why_isnt_valid_filejournal_entry
DEFAULT_QUEUE_BATCH_SIZE = 200

def details_from_file_entry(ent, should_be_synced = True):
    if should_be_synced and ent[c.LOCAL_SJID_COL] <= 1:
        raise Exception('Not a synced file entry: %r' % ent)
    sp = ServerPath(ServerPath(ent[c.PARENT_PATH_COL], lowered=True), ent[c.LOCAL_FILENAME_COL])
    return FastDetails(server_path=sp, sjid=ent[c.LOCAL_SJID_COL], blocklist=ent[c.LOCAL_BLOCKLIST_COL], size=ent[c.LOCAL_SIZE_COL], mtime=ent[c.LOCAL_MTIME_COL], dir=ent[c.LOCAL_DIR_COL], attrs=ent[c.LOCAL_ATTRS_COL], machine_guid=ent[c.LOCAL_MACHINE_GUID_COL], host_id=ent.get(c.LOCAL_HOST_ID_COL), ts=ent.get(c.LOCAL_TIMESTAMP_COL))


def is_pending_entry(entry):
    return entry[c.LOCAL_SJID_COL] is not None and not entry[c.LOCAL_SJID_COL] and not entry[c.IS_CONFLICTED_COL] and not entry[c.IS_GUID_CONFLICTED_COL]


def is_updated_entry_ignoring_guid_pending(entry):
    return not is_pending_entry(entry) and (not entry[c.IS_GUID_CONFLICTED_COL] or entry[c.LOCAL_GUID_COL] == entry[c.UPDATED_GUID_COL]) and entry[c.UPDATED_SJID_COL] is not None and not entry[c.UNRECONSTRUCTABLE_COL]


def _modify_sync_queues(trans_wrapper, trans, pattached, to_add_pending, to_remove_pending, pending_guids_removed, uattached, to_add_updated, to_remove_updated, changed_pending = None, changed_updated = None):
    pending_guids = trans.get_pending_guids((d.guid for d in to_add_updated if d.guid is not None), constructor=set)

    def new_reconstruct_filter(d):
        if d.guid in pending_guids:
            return None
        return trans_wrapper._reconstruct_filter(d)

    pending_loop_vars = (pattached,
     to_remove_pending,
     to_add_pending,
     changed_pending,
     trans_wrapper._upload_filter)
    updated_loop_vars = (uattached,
     to_remove_updated,
     to_add_updated,
     changed_updated,
     new_reconstruct_filter)
    for q, remove_l, add_l, changed_l, filt in [pending_loop_vars, updated_loop_vars]:
        q.discard_batch(remove_l, lower=False)
        new_to_discard = []
        new_to_add = []
        for deets in add_l:
            uf = filt(deets)
            if uf is not None:
                new_to_add.append((deets, uf))
            else:
                new_to_discard.append(deets.server_path)

        q.add_batch(new_to_add)
        q.discard_batch(new_to_discard)
        if changed_l is not None:
            changed_l.extend(remove_l)
            get_lowered_sp = compose(operator.methodcaller('lower'), operator.attrgetter('server_path'))
            changed_l.extend(itertools.imap(get_lowered_sp, add_l))

    uattached.discard_by_guid_batch((d.guid for d in to_add_pending if d.guid is not None))
    to_add = []
    for entry in trans.entries_by_remote_dropbox_guid_batch(pending_guids_removed):
        deets = is_updated_entry_ignoring_guid_pending(entry) and updated_details_from_entry(entry)
        if deets:
            uf = filt(deets)
            if uf is not None:
                to_add.append((deets, uf))

    uattached.add_batch(to_add)


def flush_first(fn):

    @functools.wraps(fn)
    def wrapped(self, *n, **kw):
        self.flush()
        return fn(self, *n, **kw)

    return wrapped


@add_inner_methods('_upgrade_4_to_5', 'add_guid_references', 'add_to_held', 'clear_held', 'conflicted_get_active', 'conflicted_get_count', 'delete_from_held', 'delete_guid_references', 'do_magic_shared_folder_query', 'entries_by_local_dropbox_guid_batch', 'entries_by_remote_dropbox_guid_batch', 'entry_with_target_ns', 'get_attrs_data_plats', 'get_attrs_whitelist', 'get_backward_references', 'get_config_key', 'get_directory_ignore_set', 'get_entries', 'get_held_descendants', 'get_holds', 'get_local_children', 'get_mount_points', 'get_tracked_namespaces', 'get_version', 'has_local_children_not_going_to_be_deleted', 'has_server_children_not_going_to_be_deleted', 'last_revisions', 'map_machine_guids', 'remove_config_key', 'reset_local_ctimes', 'set_config_key', decorator=flush_first, inner_name='trans')

class MemoryCacheTransactionWrapper(object):

    def __init__(self, backend_wrapper):
        self.backend_wrapper = backend_wrapper
        self.currently_flushing = False

    def __metaclass__(name, bases, dict_):
        for name_prefix, q_attr in [('upload', 'pattached'), ('reconstruct', 'uattached')]:

            def fn_creator(q_attr, name):

                @flush_first
                def wrapped(self, *n, **kw):
                    return getattr(getattr(self, q_attr), name)(*n, **kw)

                return wrapped

            for external_name, internal_name in [('%s_clear_retry_map', 'clear_retry_map'),
             ('%s_is_failing', 'is_failing'),
             ('%s_ready_time', 'ready_time'),
             ('%s_retry', 'retry'),
             ('%sing_status', 'get_status'),
             ('_only_for_testing_dequeue_%s', 'remove'),
             ('add_%s_error_callback', 'add_error_callback'),
             ('add_%s_keymod_handler', 'add_keymod_handler'),
             ('add_%s_retry_handler', 'add_retry_handler'),
             ('get_%s_count', 'get_size'),
             ('get_%s_failure_counts', 'get_failure_counts'),
             ('get_%s_failures', 'get_failures'),
             ('get_%s_only_file', 'get_only_file'),
             ('get_%sable', 'get_active'),
             ('get_%sable_count', 'active_count'),
             ('get_%sing', 'get'),
             ('get_%sing_unlocked', 'get'),
             ('get_full_%s_counts', 'counts'),
             ('is_%sable', 'is_active'),
             ('is_%sing', 'get'),
             ('set_%s_active', 'set_active'),
             ('_add_%sable', 'add')]:
                new_name = external_name % (name_prefix,)
                assert new_name not in dict_
                new_fn = fn_creator(q_attr, internal_name)
                new_fn.__name__ = new_name
                dict_[new_name] = new_fn

        return type(name, bases, dict_)

    def _reconstruct_filter(self, details):
        rel_path = self.backend_wrapper.fc._root_relative_server_path_unlocked(details.server_path, trans=self)
        if self.backend_wrapper.fc._ignore_set_should_ignore(rel_path):
            TRACE('Selective Sync not reconstructing: %r', details.server_path)
            return None
        return 0

    def _upload_filter(self, details):
        rel_path = self.backend_wrapper.fc._root_relative_server_path_unlocked(details.server_path, trans=self)
        if self.backend_wrapper.fc._ignore_set_should_ignore(rel_path):
            TRACE('Selective Sync not committing: %r', details.server_path)
            return None
        return 0

    def sqlite_cursor(self):
        return FlushBefore(self, self.trans.sqlite_cursor())

    def _flush(self):
        _modify_sync_queues(self, self.trans, self.pattached, self.to_add_pending, self.to_remove_pending, self.pending_guids_removed, self.uattached, self.to_add_updated, self.to_remove_updated, self.changed_pending, self.changed_updated)
        self.new_synced_files.extend(self.current_synced_files)
        self._reset_flush_state()

    def _reset_flush_state(self):
        self.current_synced_files = []
        self.to_add_pending = []
        self.to_remove_pending = []
        self.to_add_updated = []
        self.to_remove_updated = []
        self.pending_guids_removed = set()

    @contextlib.contextmanager
    def transaction(self):
        self._reset_flush_state()
        self.changed_pending = []
        self.changed_updated = []
        self.new_synced_files = []
        pattacher = self.backend_wrapper.pending.attach_to(self.backend_wrapper.sqlite_cursor())
        uattacher = self.backend_wrapper.updated.attach_to(self.backend_wrapper.sqlite_cursor())
        with pattacher as pattached:
            with uattacher as uattached:
                with self.backend_wrapper.backend.transaction() as trans:
                    self.pattached = pattached
                    self.uattached = uattached
                    self.trans = trans
                    self.hashes_added = set()
                    self.hashes_removed = set()
                    try:
                        yield self
                        self.flush()
                        hashes_added = self.hashes_added
                        hashes_removed = self.hashes_removed
                        self.backend_wrapper.fc.dispatch_block_reference_changes(None, hash_references_added=hashes_added, hash_references_removed=hashes_removed)
                        if self.new_synced_files:
                            self.backend_wrapper.fc.synced_callbacks.run_handlers(self.new_synced_files)
                        for sp in self.changed_updated:
                            self.backend_wrapper.fc.changed_reconstruct_callbacks.run_handlers(sp)

                        for sp in self.changed_pending:
                            self.backend_wrapper.fc.changed_upload_callbacks.run_handlers(sp)

                    finally:
                        self.trans = None
                        self.uattached = None
                        self.pattached = None
                        self.hashes_added = None
                        self.hashes_removed = None

    def _is_updated(self, entry):
        return is_updated_entry_ignoring_guid_pending(entry) and updated_details_from_entry(entry)

    def _is_pending(self, entry):
        return is_pending_entry(entry) and self.backend_wrapper.fc._pending_details_from_ent(entry)

    def _synced_sjid(self, entry):
        return entry[c.LOCAL_SJID_COL] is not None and entry[c.LOCAL_SJID_COL] > 1 and entry[c.LOCAL_SJID_COL]

    def _update_caches(self, old_entry, new_entry):
        old_updated = propagate_none(self._is_updated, old_entry)
        old_pending = propagate_none(self._is_pending, old_entry)
        new_updated = propagate_none(self._is_updated, new_entry)
        new_pending = propagate_none(self._is_pending, new_entry)
        if old_pending != new_pending:
            if new_pending:
                self.to_add_pending.append(new_pending)
            elif old_pending:
                sp = ServerPath(old_entry[c.SERVER_PATH_COL], lowered=True)
                self.pending_guids_removed.add(old_pending.guid)
                self.to_remove_pending.append(sp)
        if old_updated != new_updated:
            if new_updated:
                self.to_add_updated.append(new_updated)
            elif old_updated:
                sp = ServerPath(old_entry[c.SERVER_PATH_COL], lowered=True)
                self.to_remove_updated.append(sp)

    def flush(self):
        self.currently_flushing = True
        try:
            fjrl = getattr(self.trans, 'fjrl', None)
            self.trans.flush()
            if fjrl is not None:
                hashes_actually_added = fjrl.hashes_added() - self.hashes_removed
                hashes_actually_removed = fjrl.hashes_removed() - self.hashes_added
                self.hashes_added |= hashes_actually_added
                self.hashes_added -= fjrl.hashes_removed()
                self.hashes_removed |= hashes_actually_removed
                self.hashes_removed -= fjrl.hashes_added()
            self._flush()
        finally:
            self.currently_flushing = False

    def update_entry(self, old_entry, new_entry):
        if self.currently_flushing:
            raise Exception("Can't add flush state while flushing")
        self.trans.update_entry(old_entry, new_entry)
        new_sjid = self._synced_sjid(new_entry)
        if new_sjid and self._synced_sjid(old_entry) != new_sjid:
            d = details_from_file_entry(new_entry)
            self.current_synced_files.append(d)
        self._update_caches(old_entry, new_entry)

    def delete_entry(self, old_entry):
        if self.currently_flushing:
            raise Exception("Can't add flush state while flushing")
        self.trans.delete_entry(old_entry)
        d = details_from_file_entry(old_entry, should_be_synced=False)
        self.current_synced_files.append(d.copy(blocklist='', size=-1, dir=0, attrs=FrozenAttributes()))
        self._update_caches(old_entry, None)

    def insert_entry(self, new_entry):
        if self.currently_flushing:
            raise Exception("Can't add flush state while flushing")
        self.trans.insert_entry(new_entry)
        self._update_caches(None, new_entry)

    def update_last_revision(self, ns_id, sj_id):
        if self.currently_flushing:
            raise Exception("Can't add flush state while flushing")
        self.trans.update_last_revision(ns_id, sj_id)

    @flush_first
    def clear_queues(self):
        self.trans.reset_transient_state()
        self.pattached.clear()
        self.uattached.clear()

    @flush_first
    def refilter_queues(self):
        self.clear_queues()
        for rows in batch(self.trans.get_unsynced_entries(), DEFAULT_QUEUE_BATCH_SIZE):
            to_add_pending = []
            to_add_updated = []
            for row in rows:
                msg = why_isnt_valid_filejournal_entry(row)
                if msg:
                    raise InvalidDatabaseError(msg)
                if is_pending_entry(row):
                    to_add_pending.append(self.backend_wrapper.fc._pending_details_from_ent(row))
                elif is_updated_entry_ignoring_guid_pending(row):
                    to_add_updated.append(updated_details_from_entry(row))

            _modify_sync_queues(self, self.trans, self.pattached, to_add_pending, [], [], self.uattached, to_add_updated, [])

    @flush_first
    def clear(self):
        self.trans.clear()
        self.pattached.clear()
        self.uattached.clear()

    @flush_first
    def move_entries_with_new_writable_attrs_to_reconstruct(self):
        entries = self.trans.move_entries_with_new_writable_attrs_to_reconstruct()
        for rows in batch(entries, DEFAULT_QUEUE_BATCH_SIZE):
            to_add_updated = [ updated_details_from_entry(row) for row in rows if is_updated_entry_ignoring_guid_pending(row) ]
            _modify_sync_queues(self, self.trans, self.pattached, [], [], [], self.uattached, to_add_updated, [])


@add_inner_properties('connhub', 'sqlite_cursor', inner_name='backend')

class MemoryCacheBackendWrapper(object):

    def __low_init__(self, fc, pending, updated, backend):
        self.fc = fc
        self.pending = pending
        self.updated = updated
        self.backend = backend

    def __init__(self, pending_path, updated_path, fc, backend):
        pending_obj = PendingFileSetWithFailure(pending_path)
        try:
            updated_obj = UpdatedFileSetWithFailure(updated_path)
            try:
                self.__low_init__(fc, pending_obj, updated_obj, backend)
            except:
                updated_obj.close()
                raise

        except:
            pending_obj.close()
            raise

    @classmethod
    def _from_components(cls, fc, pending, updated, backend):
        a = cls.__new__(cls)
        a.__low_init__(fc, pending, updated, backend)
        return a

    def transaction(self):
        return MemoryCacheTransactionWrapper(self).transaction()

    def close(self):
        self.backend.close()
        self.pending.close()
        self.updated.close()

    def copy(self, fc, database_file, **kw):
        new_backend = self.backend.copy(fc, database_file, **kw)
        new_pending_database_file = kw.pop('pending_database_file', None)
        new_updated_database_file = kw.pop('updated_database_file', None)
        new_pending = self.pending.copy(new_pending_database_file)
        new_updated = self.updated.copy(new_updated_database_file)
        return MemoryCacheBackendWrapper._from_components(self.fc, new_pending, new_updated, new_backend)
