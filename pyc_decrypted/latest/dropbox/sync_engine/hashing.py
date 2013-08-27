#Embedded file name: dropbox/sync_engine/hashing.py
from __future__ import absolute_import
import errno
import sys
import time
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, dropbox_hash
from dropbox.attrs import attr_dict_from_whitelist, unfreeze_attr_dict
from dropbox.fastdetails import FastDetails
from dropbox.features import feature_enabled
from dropbox.threadutils import StoppableThread
from dropbox.functions import paths_only_parents, frozendict
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.usertuple import UserTuple
from dropbox.metadata.metadata import metadata_plats
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY
from dropbox.sync_engine_file_system.exceptions import FileSystemError, FileNotFoundError
from .constants import HASH_ACCESS, HASH_BUSY, HASH_DELETED, HASH_DROP, HASH_SUCCESS, HASH_UNKNOWN
from .sync_engine_util import add_sig_and_check, SyncEngineStoppedError

def _oserror_to_hash_result(e):
    try:
        windows_errno = e.winerror
    except AttributeError:
        if e.errno in (errno.ENOENT, errno.ENOTDIR):
            return HASH_DELETED
        if e.errno in (errno.EPERM, errno.EACCES):
            return HASH_ACCESS
    else:
        if windows_errno in (32, 33, 170):
            return HASH_BUSY
        if windows_errno in (2, 3):
            return HASH_DELETED
        if windows_errno == 5:
            return HASH_ACCESS

    return HASH_UNKNOWN


def _get_attributes(sync_engine, local_path, block_handler, whitelist):
    attrs = sync_engine.attr_handler.read_attributes(local_path, block_handler=block_handler)
    metadata = frozendict() if sync_engine.is_directory(local_path) else sync_engine.get_metadata(local_path, whitelist)
    if metadata:
        new_data_plats = set(attrs.data_plats) | set(metadata_plats())
        formatted = dict(((k, attr_dict_from_whitelist(metadata[k], k, whitelist)) for k, val in metadata.iteritems()))
        attr_dict = unfreeze_attr_dict(attrs.attr_dict)
        attr_dict.update(formatted)
        attrs = attrs.copy(attr_dict=attr_dict, data_plats=new_data_plats)
    if not all((ns_dict for ns, ns_dict in attrs.attr_dict.iteritems())):
        report_bad_assumption('Read_attributes is returning a bad attr_dict: %r', attrs)
        attrs = attrs.copy(attr_dict=dict(((ns, ns_dict) for ns, ns_dict in attrs.attr_dict.iteritems() if ns_dict)))
    return attrs


def _check_times(sync_engine, st, local_path):
    try:
        _st = sync_engine.fs.indexing_attributes(local_path)
    except FileSystemError as e:
        exc = sys.exc_info()
        try:
            result = _oserror_to_hash_result(e)
            if result == HASH_UNKNOWN:
                unhandled_exc_handler(exc_info=exc)
            return result
        finally:
            del exc

    if abs(st.mtime - _st.mtime) >= 0.001:
        return HASH_BUSY
    if abs(getattr(st, 'ctime', 0) - getattr(_st, 'ctime', 0)) >= 0.001:
        return HASH_BUSY
    if feature_enabled('fileids') and st.machine_guid != _st.machine_guid:
        TRACE('_check_times detected local machine guid mismatch on path %r: %r vs %r', unicode(local_path), st.machine_guid, _st.machine_guid)
        return HASH_BUSY


def _hash_file(sync_engine, local_path, st, block_handler, whitelist, check_stopped = True):
    TRACE('Hashing file %r', local_path)
    new_blocklist = []
    total_size = 0
    try:
        with sync_engine.fs.open(local_path, 'r', sequential=True) as f:
            while True:
                if check_stopped and not sync_engine.running:
                    raise SyncEngineStoppedError
                ret = _check_times(sync_engine, st, local_path)
                if ret:
                    return ret
                s_arr = []
                block_read = 0
                while DROPBOX_MAX_BLOCK_SIZE != block_read:
                    s = f.read(DROPBOX_MAX_BLOCK_SIZE - block_read)
                    if not s:
                        break
                    s_arr.append(s)
                    block_read += len(s)

                s = ''.join(s_arr)
                if s:
                    sha1_digest = dropbox_hash(s)
                    new_blocklist.append(sha1_digest)
                    total_size += len(s)
                    if block_handler:
                        block_handler(sha1_digest, s)
                if len(s) != DROPBOX_MAX_BLOCK_SIZE:
                    break

    except (IOError, FileSystemError) as e:
        exc = sys.exc_info()
        try:
            result = _oserror_to_hash_result(e)
            if result == HASH_UNKNOWN:
                unhandled_exc_handler(exc_info=exc)
            return result
        finally:
            del exc

    blocklist_string = ','.join(new_blocklist)
    try:
        attrs = _get_attributes(sync_engine, local_path, block_handler, whitelist)
    except FileNotFoundError:
        return HASH_DELETED

    ret = _check_times(sync_engine, st, local_path)
    if ret:
        return ret
    if total_size != st.size:
        report_bad_assumption("Weird... total size read isn't equal to statted size %r vs %r" % (total_size, st.size))
    return (HASH_SUCCESS, FastDetails(blocklist=blocklist_string, mtime=long(st.mtime), size=total_size, dir=0, attrs=attrs, ctime=long(getattr(st, 'ctime', 0)), machine_guid=st.machine_guid))


def _hash_attr_only_check(local_path, st, deet):
    return st.type != FILE_TYPE_DIRECTORY and deet.mtime == long(st.mtime) and deet.size == (0 if deet.dir else long(st.size)) and st.machine_guid == deet.machine_guid


def _hash_attr_only(sync_engine, local_path, st, deet, block_handler, whitelist):
    TRACE('Hashing attributes for %r', local_path)
    try:
        attrs = _get_attributes(sync_engine, local_path, block_handler, whitelist)
    except (IOError, FileSystemError) as e:
        exc = sys.exc_info()
        try:
            result = _oserror_to_hash_result(e)
            if result == HASH_UNKNOWN:
                unhandled_exc_handler(exc_info=exc)
            return result
        finally:
            del exc

    ret = _check_times(sync_engine, st, local_path)
    if ret:
        return ret
    return (HASH_SUCCESS, FastDetails(blocklist=deet.blocklist, mtime=long(st.mtime), size=deet.size, dir=deet.dir, attrs=attrs, ctime=long(st.ctime), machine_guid=st.machine_guid))


def _hash_dir(sync_engine, local_path, st, block_handler, whitelist):
    TRACE('Hashing directory %r', local_path)
    try:
        attrs = _get_attributes(sync_engine, local_path, block_handler, whitelist)
    except (IOError, FileSystemError) as e:
        exc = sys.exc_info()
        try:
            result = _oserror_to_hash_result(e)
            if result == HASH_UNKNOWN:
                unhandled_exc_handler(exc_info=exc)
            return result
        finally:
            del exc

    try:
        ns = sync_engine.folder_tagger.get_folder_ns(local_path)
    except Exception:
        unhandled_exc_handler()
        ns = None

    if ns is not None:
        TRACE('Folder %r had ns %r', local_path, ns)
    ret = _check_times(sync_engine, st, local_path)
    if ret:
        return ret
    toret = FastDetails(blocklist='', mtime=long(st.mtime), size=0, dir=1, attrs=attrs, ctime=long(st.ctime), mount_request=ns, machine_guid=st.machine_guid)
    return (HASH_SUCCESS, toret)


def _flush_pending(self, pending):
    assert pending
    TRACE('Flushing %d file at %0.3f', len(pending), time.time())
    reindex_list = []
    maybe_reindex = []
    for hash_tuple in pending:
        ret = hash_tuple[0]
        local_path = hash_tuple[2]
        recurse = hash_tuple[3]
        if hasattr(ret, '__getitem__') and ret[0] == HASH_SUCCESS and ret[1].dir == 1 and recurse:
            reindex_list.append(local_path)
        if ret == HASH_DELETED or hasattr(ret, '__getitem__') and ret[0] == HASH_SUCCESS and not ret[1].dir:
            maybe_reindex.append(local_path)

    if maybe_reindex:
        with self.se.cache.read_lock():
            spl2lp = dict(((self.se.local_to_server(lp).lower(), lp) for lp in maybe_reindex))
            spl2deets = dict(((ent.server_path.lower(), ent) for ent in self.se.cache.get_local_details_batch(spl2lp.keys(), lower=False)))
            for spl, ent in spl2deets.iteritems():
                if ent.dir != 1:
                    continue
                reindex_list.append(spl2lp[spl])

    if reindex_list:
        reindex_list.sort()
        for local_path in paths_only_parents(reindex_list, key=unicode):
            self.se._queue_reindex(local_path)

    self.se.handle_hash_results(pending, self.hashes_to_prune)


def sum_failures(ite):
    return sum((it[1] for it in ite))


def _hash_thread(self):
    sync_engine = self.se
    initted = False
    while not self.stopped():
        try:
            if not self.se.check_if_running(sync_engine.hash_event.set):
                self.se.set_thread_is_running(False)
                initted = False
                TRACE('SyncEngine has stopped, waiting...')
                sync_engine.hash_event.wait()
                continue
            self.se.set_thread_is_running(True)
            if not initted:
                TRACE('Hashing thread starting.')
                pending = []
                self.hashes_to_prune = set()
                to_hash = ()
                to_hash_index = 0
                waiting_for_initial_index_completion = True
                initted = True
            if to_hash_index == len(to_hash):
                if pending:
                    _flush_pending(self, pending)
                    self.hashes_to_prune = set()
                    pending = []
                new_to_hash, local_deet_map, attrs_whitelist = sync_engine.get_hashable_with_attrs_deets()
                whitelist_hash = sync_engine.attr_handler.get_whitelist_hash()
                if not new_to_hash:
                    if waiting_for_initial_index_completion and sync_engine.get_hash_count() == sync_engine.get_hash_failure_counts(sum_failures) and sync_engine.check_if_initial_reindex_is_done(sync_engine.hash_event.set):
                        current_times = sync_engine.get_system_time_tuple()
                        TRACE('End of initial index; Starting download thread!')
                        TRACE('Elapsed since start: %.2f sec (%.2f sec CPU time, %.2f user, %.2f system)' % (current_times[0] - self.se.start_times[0],
                         sum(current_times[1:3]) - sum(self.se.start_times[1:3]),
                         current_times[1] - self.se.start_times[1],
                         current_times[2] - self.se.start_times[2]))
                        sync_engine.signal_initial_hash_done()
                        waiting_for_initial_index_completion = False
                    ready_time = sync_engine.hash_ready_time()
                    timeout = None if ready_time is None else ready_time - time.time()
                    if timeout is None:
                        sync_engine.writes_to_ignore.prune_old_entries()
                        TRACE('Waiting indefinitely for new files')
                    elif timeout > 0:
                        TRACE('Waiting for %f seconds for new files' % timeout)
                    else:
                        timeout = 0
                    if waiting_for_initial_index_completion:
                        TRACE("... haven't yet signaled initial hash done to rest of SyncEngine")
                    sync_engine.hash_event.wait(timeout)
                    continue
                else:
                    to_hash = new_to_hash
                    to_hash_index = 0
                    TRACE('Got %d new files to hash' % (len(new_to_hash),))
                    del new_to_hash
            elif len(pending) >= sync_engine.max_upload_count:
                _flush_pending(self, pending)
                self.hashes_to_prune = set()
                pending = []
            deet = to_hash[to_hash_index]
            try:
                attrs_deets = local_deet_map[deet.local_path]
            except KeyError:
                attrs_deets = None

            to_hash_index += 1
            item = deet.local_path
            recurse = False
            try:
                st = sync_engine.fs.indexing_attributes(item, write_machine_guid=True)
            except FileSystemError as e:
                exc = sys.exc_info()
                try:
                    should_ignore = sync_engine._stat_fail_ignore(item, e)
                    if should_ignore:
                        TRACE('Ignoring hash result, failed: %r, %r', item, should_ignore)
                        ret = HASH_DROP
                    else:
                        ret = _oserror_to_hash_result(e)
                        if ret == HASH_UNKNOWN:
                            unhandled_exc_handler(exc_info=exc)
                finally:
                    del exc

            else:
                try:
                    should_ignore = sync_engine._stat_succeed_ignore(item, st)
                    if should_ignore:
                        TRACE('Ignoring hash result, succeed: %r, %r' % (item, should_ignore))
                        ret = HASH_DROP
                    elif attrs_deets and _hash_attr_only_check(item, st, attrs_deets):
                        ret = _hash_attr_only(self.se, item, st, attrs_deets, self.block_handler, attrs_whitelist)
                    elif st.type == FILE_TYPE_DIRECTORY:
                        ret = _hash_dir(self.se, item, st, self.block_handler, attrs_whitelist)
                        recurse = deet.recurse != 0
                    else:
                        ret = _hash_file(self.se, item, st, self.block_handler, attrs_whitelist)
                except:
                    unhandled_exc_handler()
                    ret = HASH_UNKNOWN

            TRACE('Hashed %r: %s', item, ret if type(ret) is str else 'ok')
            pending.append(UserTuple(ret, deet, item, recurse, whitelist_hash))
        except:
            unhandled_exc_handler()
            self.se.hash_event.wait(5)


class HashThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'HASH'
        super(HashThread, self).__init__(*n, **kw)
        self.se = sync_engine

    def set_wakeup_event(self):
        self.se.hash_event.set()

    def block_handler(self, *n):
        add_sig_and_check(self.hashes_to_prune, self.se.sigstore, *n)

    def run(self):
        _hash_thread(self)
        TRACE('Stopping...')
