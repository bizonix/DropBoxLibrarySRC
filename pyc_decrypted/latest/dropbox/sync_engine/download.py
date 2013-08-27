#Embedded file name: dropbox/sync_engine/download.py
from __future__ import absolute_import
import pprint
import time
import base64
import os
import zlib
import json
import cStringIO
from Crypto.Random import random
import build_number
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, dropbox_hash
from dropbox.trace import unhandled_exc_handler, TRACE, report_bad_assumption, EVENT, debugging_features_are_enabled
from dropbox.build_common import get_build_number, get_platform
from dropbox.low_functions import container
from dropbox.path import server_path_ns
from dropbox.functions import lrudict, miniblocklist
from dropbox.features import feature_enabled
from dropbox.callbacks import Handler
from dropbox.threadutils import StoppableThread
from dropbox.native_event import AutoResetEvent
from dropbox import fsutil
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError
from .p2p.api import peerget
from .sync_engine_util import SyncEngineStoppedError, BlockContentsError
import dropbox.librsync
import dropbox.native_threading
_hash2usecount = lrudict(cache_size=500)
_sent_bad_assumption = False

def _use_fake_block_dir(sync_engine):
    if not debugging_features_are_enabled():
        return
    fake_block = os.getenv('FAKE_BLOCK')
    if fake_block is None:
        return
    try:
        return sync_engine.arch.make_path(fake_block)
    except Exception:
        unhandled_exc_handler()
        return


def retrieve_hashes(sync_engine, hash2info, should_stop):
    ret = []
    fake_block_dir = _use_fake_block_dir(sync_engine)
    if fake_block_dir is not None:
        for _hash in hash2info.iterkeys():
            fn = fake_block_dir.join(_hash)
            try:
                with sync_engine.fs.open(fn) as f:
                    ret.append((_hash, f.read()))
            except FileNotFoundError:
                pass
            except Exception:
                unhandled_exc_handler()

        if ret:
            return (ret, True, 0)
    if sync_engine.p2p_state.p2p_enabled:
        raw_transfer = 0
        min_file_size = sync_engine.p2p_min_nonbatch_file_size
        for _hash, info in hash2info.iteritems():
            size = getattr(info, 'size', None)
            if size is not None and size < min_file_size:
                TRACE('Not fetching hash %s over P2P because the file is small (%d < %d)', _hash, info.size, min_file_size)
                continue
            nses = getattr(info, 'namespaces', ())
            if nses:

                def p2p_cb(raw_size, time_delta):
                    sync_engine.status.set_lan_sync(True)
                    sync_engine.status.download_status.note_data(raw_size, time_delta)

                t_start = time.time()
                s = peerget(sync_engine, _hash, nses, cb=p2p_cb)
                raw_transfer += time.time() - t_start
                if s:
                    ret.append((_hash, s))

        if ret:
            return (ret, False, raw_transfer)
    sync_engine.status.set_lan_sync(False)
    if len(hash2info) == 1:
        _hash = hash2info.keys()[0]
        info = hash2info[_hash]
        t_start = time.time()
        data = sync_engine.conn.retrieve(_hash, getattr(info, 'parent', None), getattr(info, 'sig', None), cb=sync_engine.status.download_status.note_data, stop_cb=should_stop)
        raw_transfer = time.time() - t_start
        return ([(_hash, data)], True, raw_transfer)
    else:
        t_start = time.time()
        limits = getattr(sync_engine, 'server_limits', {})
        num_connections = limits.get('download_hash_batch_parallel_connections', 1)
        if num_connections > 1:
            response = sync_engine.conn.retrieve_batch_parallel(hash2info, num_connections, limits.get('download_hash_batch_max_size', DROPBOX_MAX_BLOCK_SIZE), cb=sync_engine.status.download_status.note_data, stop_cb=should_stop)
        else:
            response = sync_engine.conn.retrieve_batch(hash2info, cb=sync_engine.status.download_status.note_data, stop_cb=should_stop)
        buf = cStringIO.StringIO(response)
        raw_transfer = time.time() - t_start
        ret = []
        try:
            while True:
                head = buf.readline()
                if not head:
                    break
                head = json.loads(head)
                ret.append((head['hash'], buf.read(head['len'])))

        except Exception:
            unhandled_exc_handler()

        return (ret, True, raw_transfer)


def add_download_info(se, hash2info):
    global _sent_bad_assumption
    cache_path = se.verify_cache_path()
    se.verify_disk_space(cache_path, 4194304)
    blow_me_away = []
    try:
        for _hash in hash2info:
            try:
                if se.have_locally_hard(_hash):
                    se.got_hash(_hash)
                    blow_me_away.append(_hash)
                    continue
                if not _sent_bad_assumption:
                    hash_download_count = _hash2usecount.get(_hash, 0)
                    if hash_download_count >= 10:
                        report_bad_assumption('The hash %r has been downloaded %d times in one session.', _hash, hash_download_count)
                        _sent_bad_assumption = True
                info = hash2info[_hash]
                server_paths = getattr(info, 'server_paths', ())
                info.namespaces = set((server_path_ns(sp) for sp in server_paths))
                info.fn = cache_path.join(_hash)
                info.sig = None
                info.orig = None
                if not hasattr(info, 'parent'):
                    info.parent = None
                with se.fs.open(info.fn, 'w'):
                    pass
                fsutil.safe_remove(se.fs, info.fn)
                TRACE('GETTING HASH %s for %s and %s', _hash, server_paths, info.namespaces)
            except Exception:
                unhandled_exc_handler()
                se.set_download_error(_hash)
                blow_me_away.append(_hash)
                continue

    finally:
        for _hash in blow_me_away:
            del hash2info[_hash]


def handle_retrieve_ret(sync_engine, hash2info, done, ret, t_start, raw_transfer, is_compressed = True):
    if not ret:
        return

    def verify_downloaded_hash(decompressed, _hash):
        if dropbox_hash(decompressed) != _hash:
            raise Exception('Downloaded _hash does not equal requested _hash! %r' % (_hash,))
        if len(decompressed) > DROPBOX_MAX_BLOCK_SIZE:
            raise Exception('Downloaded _hash size is larger than 4MB!')

    note = []
    raw_size = 0
    for _hash, data in ret:
        info = hash2info[_hash]
        parent = info.parent
        raw_size += len(data)
        if not is_compressed:
            decompressed = data
            verify_downloaded_hash(decompressed, _hash)
            compressed = zlib.compress(decompressed)
        elif data == '':
            assert parent, "Server returned '' but we have no parent?"
            try:
                try:
                    sig = sync_engine.get_block_sig(parent)
                except KeyError:
                    info.orig = orig = sync_engine.contents(parent)
                    sig = dropbox.librsync.sig(orig)

                info.sig = base64.encodestring(sig)
                sync_engine.status.download_status.cancel_intermediate_transfer()
            except Exception:
                TRACE('Failed to handle differential request on %s (parent %s)', _hash, parent)
                unhandled_exc_handler()
                info.sig = None
                info.parent = None

            continue
        elif parent:
            try:
                orig = info.orig or sync_engine.contents(parent)
                TRACE('Downloaded diff (%s bytes) %s -> %s', len(data), parent, _hash)
                decompressed = dropbox.librsync.patch(orig, zlib.decompress(data))
                verify_downloaded_hash(decompressed, _hash)
                compressed = zlib.compress(decompressed)
            except Exception as e:
                TRACE('Failed to handle differential request on %s (parent %s)', _hash, parent)
                if not isinstance(e, BlockContentsError):
                    unhandled_exc_handler()
                sync_engine.status.download_status.cancel_intermediate_transfer()
                info.parent = None
                info.sig = None
                continue

        elif info.sig:
            report_bad_assumption('Called retrieve with sig but no parent.')
            info.sig = None
            continue
        else:
            decompressed = zlib.decompress(data)
            verify_downloaded_hash(decompressed, _hash)
            compressed = data
        TRACE('Saving _hash %s to %s', _hash, info.fn)
        fake_block_dir = _use_fake_block_dir(sync_engine)
        if fake_block_dir is not None:
            fn = fake_block_dir.join(_hash)
            with sync_engine.fs.open(fn, 'w') as f:
                f.write(compressed)
        with sync_engine.fs.open(info.fn, 'w') as f:
            f.write(compressed)
        sync_engine.got_hash(_hash)
        EVENT('get_hash', miniblocklist(_hash), miniblocklist(parent), bool(parent))
        done.append(_hash)
        note.append((len(decompressed), len(data)))
        del hash2info[_hash]

    total_time = time.time() - t_start
    if not is_compressed:
        try:
            kib = raw_size / 1024.0 / raw_transfer
        except ZeroDivisionError:
            kib = 'DIVBYZERO'

        TRACE('Raw hash transfer took %r seconds for %r bytes ~ %rKiB/s', raw_transfer, raw_size, kib)
        sync_engine.status.download_status.note_data(0, total_time - raw_transfer)
    if note:
        sync_engine.status.download_status.note_hashes(note, total_time)


def _download_hash_batch(sync_engine, hash2info, done, should_stop = None):
    try:
        count = 0
        while hash2info and count < 5:
            t_start = time.time()
            ret, is_compressed, raw_transfer = retrieve_hashes(sync_engine, hash2info, should_stop)
            try:
                for _hash, _ in ret:
                    _hash2usecount[_hash] = _hash2usecount.get(_hash, 0) + 1

            except Exception:
                unhandled_exc_handler()

            handle_retrieve_ret(sync_engine, hash2info, done, ret, t_start, raw_transfer, is_compressed=is_compressed)
            count += 1

    finally:
        for _hash, info in hash2info.iteritems():
            sync_engine.set_download_error(_hash)

        sync_engine.status.download_status.cancel_intermediate_transfer()


def download_hash_batch(sync_engine, hash2info, done, should_stop = None):
    add_download_info(sync_engine, hash2info)
    return _download_hash_batch(sync_engine, hash2info, done, should_stop=should_stop)


def download_hash_set(self, need_transfer_event):
    sync_engine = self.se
    t_start = time.time()
    done = []
    while not self.stopped() and sync_engine.running and time.time() - t_start <= 10:
        hash2info = self.se.next_hash_batch_to_download(need_transfer_event=need_transfer_event)
        if not hash2info:
            TRACE('No more hashes needed')
            break
        download_hash_batch(self.se, hash2info, done, should_stop=self.should_stop)

    return done


def download_hash(sync_engine, _hash, parent = None, namespaces = None, should_stop = None):
    hash2info = {_hash: container(parent=parent, namespaces=namespaces)}
    done = []
    download_hash_batch(sync_engine, hash2info, done, should_stop)
    return sync_engine.contents(_hash)


class HashDownloadThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'DOWNLOAD_HASH'
        super(HashDownloadThread, self).__init__(*n, **kw)
        self.se = sync_engine

    def set_wakeup_event(self):
        self.se.hash_download_event.set()

    def should_stop(self):
        if not self.se.running:
            raise SyncEngineStoppedError

    def run(self):
        self.se._download_hash_thread(self, download_hash_set)
        TRACE('Stopping...')


class ListThread(StoppableThread):

    def __init__(self, sync_engine, notification_controller, *n, **kw):
        kw['name'] = 'LIST'
        super(ListThread, self).__init__(*n, **kw)
        self.sync_engine = sync_engine
        self.notification_controller = notification_controller
        self.wakeup_bang = AutoResetEvent()
        self.thread_id = None
        self.skip_subscribe = True
        self._list_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_list_callback = self._list_callbacks.add_handler
        self.remove_list_callback = self._list_callbacks.remove_handler

    def set_wakeup_event(self):
        self.sync_engine.conn.abort_subscribe()
        dropbox.native_threading.wakeup_thread(self.thread_id)
        self.wakeup_bang.set()

    def reconnect_wakeup(self):
        dropbox.native_threading.wakeup_thread(self.thread_id)
        self.wakeup_bang.set()

    def loop(self):
        self.sync_engine.debug_output()
        last_revision = self.sync_engine.last_revisions()
        last_nid = self.notification_controller.last_nid()
        TRACE('Cursor state: [%r, %r]', last_revision, last_nid)
        ns_list = last_revision.keys()
        result = None
        if self.skip_subscribe:
            TRACE('Skipping notification server')
        else:
            TRACE('Waiting for notification server')
            self.sync_engine.status.set_status_label('listing', False)
            result = self.sync_engine.conn.subscribe(last_revision, last_nid)
            if self.stopped():
                return True
        if result is None:
            should_list = should_list_notifications = True
        else:
            should_list, should_list_notifications = 'list' in result, 'user' in result
        if should_list_notifications:
            TRACE('Listing notifications!')
            self.notification_controller.handle_ping()
        if should_list:
            self.sync_engine.status.set_status_label('listing', True)
            file_ids_on = feature_enabled('fileids')
            ret = self.sync_engine.conn.list(get_build_number(), last_revision, self.sync_engine.get_last_resync_time(), ns_p2p_key_map=self.sync_engine.p2p_state.ns_p2p_key_map_request(ns_list), need_sandboxes=self.sync_engine.config.get('sandboxes') is None, dict_return=self.sync_engine._wants_dict_list(), return_file_ids=file_ids_on)
            try:
                if 'update_to_dict' in ret:
                    _u_version = ret['update_to_dict']['version']
                else:
                    _u_version = ret['update_to'][0]
            except KeyError:
                pass
            except Exception:
                unhandled_exc_handler()
            else:
                try:
                    self.sync_engine.conn.record_upgrade_step(from_build_no=get_build_number(), to_build_no='%s-%s-%s' % (build_number.BUILD_KEY, get_platform(), _u_version), step='early_received_upgrade_signal')
                except Exception:
                    unhandled_exc_handler()

            TRACE('List returned:\n%s', pprint.pformat([ item for item in ret.iteritems() if item[0] != 'list' ]))
            self._list_callbacks.run_handlers(ret)
            next_list_first = ret.get('more_results')
            next_list_first = next_list_first or self.namespace_map_changed(ns_list)
            return next_list_first

    def namespace_map_changed(self, old_list):
        new_list = self.sync_engine.last_revisions().keys()
        if len(new_list) != len(old_list):
            return True
        new_list.sort()
        old_list.sort()
        if new_list != old_list:
            return True
        return False

    def run(self):
        self.thread_id = dropbox.native_threading.thread_id()
        self.sync_engine.conn.add_reconnect_wakeup(self.reconnect_wakeup)
        TRACE('List thread waiting to start...')
        while not self.stopped():
            if not self.sync_engine.check_if_running(self.wakeup_bang.set):
                self.wakeup_bang.wait()
            else:
                break

        try:
            TRACE('List thread starting')
            FAILURE_WAIT_PERIOD_BASE = 15
            ns_map1 = self.sync_engine.last_revisions()
            root_ns, last_sjid = ns_map1.popitem()
            if not ns_map1 and last_sjid == -1:
                self.sync_engine.is_first_list = True
                self.sync_engine.status.set_status_label('listing', True)
                try:
                    ns_map1 = {root_ns: -1}
                    failure_wait_period = FAILURE_WAIT_PERIOD_BASE
                    while not self.stopped():
                        try:
                            ret = self.sync_engine.conn.list_dirs(ns_map=ns_map1)
                            if self.stopped():
                                return
                            new_maxes = self.sync_engine.handle_list_dirs(ret.pop('list'), stop_callback=self.stopped, update_last_sjid=False)
                            old_ns_set = frozenset(ns_map1)
                            for ns, sjid in new_maxes.iteritems():
                                if sjid > ns_map1.get(ns, -1):
                                    ns_map1[ns] = sjid

                            if not ret.get('more_results') and old_ns_set == frozenset(ns_map1):
                                break
                        except Exception as e:
                            is_transient_error = self.sync_engine.conn.is_transient_error(e)
                            if is_transient_error:
                                TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                            else:
                                unhandled_exc_handler()
                            failure_wait_period = min(900, failure_wait_period * 2) if is_transient_error else FAILURE_WAIT_PERIOD_BASE
                            if not self.stopped():
                                time_to_wait = random.randint(failure_wait_period - failure_wait_period / 4, failure_wait_period + failure_wait_period / 4)
                                TRACE('Sleeping for %r seconds after failure', time_to_wait)
                                time.sleep(time_to_wait)
                        else:
                            failure_wait_period = FAILURE_WAIT_PERIOD_BASE

                finally:
                    self.sync_engine.status.set_status_label('listing', False)

            failure_wait_period = FAILURE_WAIT_PERIOD_BASE
            while not self.stopped():
                try:
                    self.skip_subscribe = self.loop()
                except Exception as e:
                    is_transient_error = self.sync_engine.conn.is_transient_error(e)
                    if is_transient_error:
                        TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                    else:
                        unhandled_exc_handler()
                    self.sync_engine.status.set_status_label('listing', False)
                    failure_wait_period = min(900, failure_wait_period * 2) if is_transient_error else FAILURE_WAIT_PERIOD_BASE
                    if not self.stopped():
                        time_to_wait = random.randint(failure_wait_period - failure_wait_period / 4, failure_wait_period + failure_wait_period / 4)
                        TRACE('Sleeping for %r seconds after failure', time_to_wait)
                        self.wakeup_bang.wait(time_to_wait)
                else:
                    failure_wait_period = FAILURE_WAIT_PERIOD_BASE

        finally:
            self.sync_engine.conn.remove_reconnect_wakeup(self.reconnect_wakeup)

        TRACE('Stopping...')
