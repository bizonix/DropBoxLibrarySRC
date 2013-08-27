#Embedded file name: dropbox/sync_engine/upload.py
from __future__ import absolute_import
from Crypto.Random import random
import time
import zlib
from collections import defaultdict
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE
from dropbox.client_prof import SimpleTimer
from dropbox.functions import miniblocklist
from dropbox.path import server_path_ns
from dropbox.threadutils import StoppableThread
from dropbox.trace import unhandled_exc_handler, TRACE, EVENT
from .sync_engine_util import SyncEngineStoppedError, BlockContentsError
import dropbox.librsync

class PatchLargerException(Exception):
    pass


def store_hashes(sync_engine, hash2info, hash_to_ns_id_to_blocklists, should_stop):
    if len(hash2info) == 1:
        _hash = hash2info.keys()[0]
        info = hash2info[_hash]
        ret = sync_engine.conn.store(_hash, info.data, info.parent, ns_id_to_blocklists=hash_to_ns_id_to_blocklists[_hash] if _hash in hash_to_ns_id_to_blocklists else None, already_compressed=True, cb=sync_engine.status.upload_status.note_data, stop_cb=should_stop)
        return ((_hash, ret),)
    limits = getattr(sync_engine, 'server_limits', {})
    num_connections = limits.get('upload_hash_batch_parallel_connections', 1)
    if num_connections > 1:
        with SimpleTimer('blocked on store_batch_parallel'):
            return sync_engine.conn.store_batch_parallel(hash2info, num_connections, limits.get('upload_hash_batch_max_size', DROPBOX_MAX_BLOCK_SIZE), already_compressed=True, cb=sync_engine.status.upload_status.note_data, stop_cb=should_stop)
    else:
        return sync_engine.conn.store_batch(hash2info, already_compressed=True, cb=sync_engine.status.upload_status.note_data, stop_cb=should_stop)


def add_upload_info(self, hash2info):
    blow_me_away = []
    try:
        for _hash in hash2info:
            try:
                with SimpleTimer('self.se.contents', cumulative=True):
                    contents = self.se.contents(_hash)
            except Exception as e:
                if not isinstance(e, BlockContentsError):
                    unhandled_exc_handler()
                TRACE('Hash %s no longer available', _hash)
                blow_me_away.append(_hash)
                continue

            info = hash2info[_hash]
            with SimpleTimer('zlib.compress', cumulative=True):
                compressed_contents = zlib.compress(contents)
            info.is_diff = False
            if info.parent:
                try:
                    TRACE('Comparing %s to %s', _hash, info.parent)
                    with SimpleTimer('librsync.delta', cumulative=True):
                        patch = dropbox.librsync.delta(self.se.get_block_sig(info.parent), contents)
                        patch = zlib.compress(patch)
                    if len(patch) > len(compressed_contents):
                        TRACE('Patch (%d bytes) larger than original file (%d)', len(patch), len(compressed_contents))
                        info.is_diff = 'not_bigger'
                        raise PatchLargerException('patch larger than original file')
                    TRACE('Sending patch (%d bytes) as opposed to original file (%d)', len(patch), len(compressed_contents))
                    file_data = patch
                    info.is_diff = True
                except (PatchLargerException, KeyError):
                    file_data = compressed_contents
                    info.parent = None
                except Exception:
                    unhandled_exc_handler()
                    file_data = compressed_contents
                    info.parent = None
                    info.is_diff = 'exception'

            else:
                file_data = compressed_contents
            if info.is_diff:
                TRACE('Sending _hash %s (%d bytes compressed patch)', _hash, len(file_data))
            else:
                TRACE('Sending _hash %s (%d bytes vs %d bytes uncompressed)', _hash, len(file_data), len(contents))
            info.data = file_data
            info.compressed_contents = compressed_contents
            info.contents_len = len(contents)

    finally:
        for _hash in blow_me_away:
            self.se.hash_uploaded(_hash)
            del hash2info[_hash]


def upload_hash_batch(sync_engine, hash2info, hash_to_ns_id_to_blocklists, done, should_stop):
    try:
        count = 0
        t_start = time.time()
        while hash2info and count < 2:
            with SimpleTimer('store_hashes'):
                ret = store_hashes(sync_engine, hash2info, hash_to_ns_id_to_blocklists, should_stop)
            t = (time.time() - t_start) / len(ret)
            with SimpleTimer('Loop to mark hash as uploaded', cumulative=True):
                for _hash, ret2 in ret:
                    item = hash2info[_hash]
                    if ret2['ret'] == 'ok':
                        sync_engine.hash_uploaded(_hash)
                        TRACE('Hash %s saved %s', _hash, ret2)
                        EVENT('store_hash', miniblocklist(_hash), miniblocklist(item.parent), item.is_diff)
                        sync_engine.status.upload_status.note_hash(item.contents_len, len(item.data), t)
                        t_start += t
                        del hash2info[_hash]
                        done.append(_hash)
                    elif ret2['ret'] == 'send_entire':
                        sync_engine.status.upload_status.cancel_intermediate_transfer()
                        TRACE('Being asked to send entire file for %s', _hash)
                        item.data = item.compressed_contents
                        item.parent = None
                    else:
                        raise Exception('on Upload ret = %r' % ret2)

            count += 1

    except Exception:
        sync_engine.status.upload_status.cancel_intermediate_transfer()
        for _hash in hash2info:
            sync_engine.set_upload_error(_hash)

        raise


def get_ns_ids_to_blocklists(self, hash2info):
    hash_to_ns_id_to_blocklists = defaultdict(lambda : defaultdict(list))
    for hash_, info in hash2info.iteritems():
        if info.is_first:
            for server_path in info.server_paths:
                with SimpleTimer('se.cache.get_uploading', cumulative=True):
                    pending_info = self.se.cache.get_uploading(server_path)
                if pending_info:
                    hash_to_ns_id_to_blocklists[hash_][server_path_ns(server_path)].append(pending_info.blocklist)

    return hash_to_ns_id_to_blocklists


def upload_hash_set(self, need_transfer_event):
    t_start = time.time()
    done = []
    while not self.stopped() and self.se.running and time.time() - t_start <= 15:
        with SimpleTimer('next_hash_batch_to_upload'):
            hash2info = self.se.next_hash_batch_to_upload(need_transfer_event=need_transfer_event)
        if not hash2info:
            break
        with SimpleTimer('add_upload_info'):
            add_upload_info(self, hash2info)
        with SimpleTimer('hash_to_ns_id_to_blocklists'):
            hash_to_ns_id_to_blocklists = get_ns_ids_to_blocklists(self, hash2info)
        with SimpleTimer('upload_hash_batch'):
            upload_hash_batch(self.se, hash2info, hash_to_ns_id_to_blocklists, done, should_stop=self.should_stop)

    return done


def upload_loop(self):
    with SimpleTimer('perform_upload'):
        self.se.perform_upload(self)
    if not self.se.get_upload_count():
        if self.changeset_map:
            if self.se.get_hash_count():
                TRACE('Waiting to close changesets (dirty queue still has files)')
            else:
                for ns_id, changeset_id in self.changeset_map.items():
                    TRACE('Closing changeset %s', changeset_id)
                    self.se.conn.close_changeset(changeset_id, ns_id)

                self.changeset_map = None
    if not self.stopped() and self.se.running:
        ready_time = self.se.upload_ready_time()
        if ready_time is not None:
            timeout = ready_time - time.time()
            if timeout > 0:
                TRACE('Waiting %f seconds for upload event', timeout)
                self.se.upload_event.wait(timeout)
        else:
            TRACE('Waiting for upload event')
            with SimpleTimer('Upload Thread fell asleep'):
                self.se.upload_event.wait()


def upload_thread(self):
    TRACE('This thread has started.')
    self.changeset_map = None
    initted = False
    FAILURE_WAIT_PERIOD_BASE = 15
    failure_wait_period = FAILURE_WAIT_PERIOD_BASE
    while not self.stopped():
        try:
            if not self.se.check_if_running(self.se.upload_event.set):
                self.se.set_thread_is_running(False)
                self.changeset_map = None
                initted = False
                TRACE('SyncEngine has stopped, waiting...')
                self.se.upload_event.wait()
                continue
            self.se.set_thread_is_running(True)
            if not initted:
                if not self.se.check_if_initial_list_is_done(self.se.upload_event.set):
                    TRACE('Waiting for initial list to finish')
                    self.se.upload_event.wait()
                    continue
                TRACE('Starting upload process')
                initted = True
            with SimpleTimer('upload_loop'):
                upload_loop(self)
        except Exception as e:
            is_transient_error = self.se.conn.is_transient_error(e)
            if is_transient_error:
                TRACE('!! Failed to communicate with server: %r %r%r', is_transient_error, type(e), e.args)
            else:
                unhandled_exc_handler()
            failure_wait_period = min(900, failure_wait_period * 2) if is_transient_error else FAILURE_WAIT_PERIOD_BASE
            if not self.stopped() and self.se.running:
                time_to_wait = random.randint(failure_wait_period - failure_wait_period / 4, failure_wait_period + failure_wait_period / 4)
                TRACE('Sleeping for %r seconds after failure', time_to_wait)
                self.se.upload_event.wait(time_to_wait)
        else:
            failure_wait_period = FAILURE_WAIT_PERIOD_BASE


class HashUploadThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'UPLOAD_HASH'
        super(HashUploadThread, self).__init__(*n, **kw)
        self.se = sync_engine

    def set_wakeup_event(self):
        self.se.hash_upload_event.set()

    def should_stop(self):
        if not self.se.running:
            raise SyncEngineStoppedError

    def run(self):
        self.se._upload_hash_thread(self, upload_hash_set)
        TRACE('Stopping...')


class UploadThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'UPLOAD'
        super(UploadThread, self).__init__(*n, **kw)
        self.se = sync_engine

    def set_wakeup_event(self):
        self.se.upload_event.set()

    def run(self):
        upload_thread(self)
        TRACE('Stopping...')
