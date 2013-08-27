#Embedded file name: dropbox/sync_engine/hash_queues.py
from __future__ import absolute_import
import collections
import dropbox.fsutil as fsutil
import os
import json
import sqlite3
import tempfile
import threading
from client_api.hashing import DROPBOX_HASH_LENGTH, DROPBOX_MAX_BLOCK_SIZE
from dropbox.client_prof import SimpleTimer
from dropbox.data_structures import ManyToMany, DictQueue, SlotDict
from dropbox.file_cache.memory_caches import SQLiteFileSetLogic, SQLiteFileSetWithFailure, locked_queue_map
from dropbox.functions import handle_exceptions_ex
from dropbox.low_functions import identity
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.server_path import ServerPath
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.sqlite3_helpers import enable_converters, just_the_first, row_factory
INT64_MAX = 9223372036854775807L
_HASH_DATABASE_PREFIX = u'TO_HASH_'

class HashDetails(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('recurse', 'order', 'local_path', 'attrs')

    def __init__(self, *args, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return ''.join(['HashDetails(', ','.join([ '%s=%r' % (k, getattr(self, k)) for k in self.__slots__ if hasattr(self, k) ]), ')'])

    def __eq__(self, othr):
        return self is othr or isinstance(othr, HashDetails) and (self.recurse,
         self.order,
         self.local_path,
         self.attrs) == (othr.recurse,
         othr.order,
         othr.local_path,
         othr.attrs)

    def __ne__(self, othr):
        return not self.__eq__(othr)

    @handle_exceptions_ex(should_raise=True)
    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            to_dump = {}
            for name in ['recurse', 'order', 'attrs']:
                if hasattr(self, name):
                    to_dump[name] = getattr(self, name)

            if hasattr(self, 'local_path'):
                to_dump['local_path'] = unicode(self.local_path)
            return json.dumps(to_dump)


def row_extract_details(d, to_pop):
    return d


def row_extract_order(d, to_pop):
    return d.order


class HashPriorityMap(DictQueue):

    def __init__(self, key_fn = identity):
        DictQueue.__init__(self, key_fn=key_fn)
        self.total_size = 0

    def copy(self):
        copied = DictQueue.copy(self)
        copied.total_size = self.total_size
        return copied

    def add(self, k, v):
        if k not in self:
            self.total_size += min(v[1], DROPBOX_MAX_BLOCK_SIZE)
            self[k] = (v, k)

    def remove(self, k):
        try:
            v, k = self[k]
        except KeyError:
            return None

        self.total_size -= min(v[1], DROPBOX_MAX_BLOCK_SIZE)
        del self[k]
        return v

    def clear(self):
        DictQueue.clear(self)
        self.total_size = 0

    def get_totals(self):
        return (self.total_size, len(self))


class HashPrioritizer(object):

    class PriorityHint(SlotDict):
        __slots__ = ['hint_added_monotime', 'synced_monotime']

        def __repr__(self):
            return '%s(%r)' % (type(self).__name__, dict(self))

    PRIORITY_HINT_LINGER_TIME = 3600
    PRIORITY_HINT_MAX_LIFETIME = 86400

    def __init__(self, hash_to_waiting_files):
        self._priority_hints = {}
        self._hash_to_waiting_files = hash_to_waiting_files

    def clear(self):
        self._priority_hints.clear()

    def add_priority_hint(self, server_path):
        ciserver_path = server_path.lower()
        TRACE('Adding priority hint: %r', unicode(ciserver_path))
        self._priority_hints[ciserver_path] = self.PriorityHint(hint_added_monotime=get_monotonic_time_seconds(), synced_monotime=None)
        self._prune_priority_hints()
        if len(self._priority_hints) > 200:
            report_bad_assumption('large number of priority hints added: count is %d', len(self._priority_hints), full_stack=True)

    def _prune_priority_hints(self):
        now = get_monotonic_time_seconds()
        expired = []
        for ciserver_path, hint in self._priority_hints.iteritems():
            if self._hint_expired(hint, now):
                expired.append(ciserver_path)

        for ciserver_path in expired:
            TRACE('Removing expired priority hint: %r', unicode(ciserver_path))
            del self._priority_hints[ciserver_path]

    def _hint_expired(self, hint, now):
        if hint.hint_added_monotime + self.PRIORITY_HINT_MAX_LIFETIME < now:
            return True
        if hint.synced_monotime is not None and hint.synced_monotime + self.PRIORITY_HINT_LINGER_TIME < now:
            return True
        return False

    def sort_key(self, v):
        info, hash_ = v
        try:
            server_paths = self._hash_to_waiting_files.a_to_b[hash_]
        except Exception:
            unhandled_exc_handler()
            return v

        pri = 0
        now = get_monotonic_time_seconds()
        for server_path in server_paths:
            ciserver_path = server_path.lower()
            hint = self._priority_hints.get(ciserver_path)
            if not hint:
                continue
            elif not self._hint_expired(hint, now):
                pri = -1
                break

        return (info.retry_time,
         pri,
         info.size,
         info.file_hash,
         info.is_first,
         info.parent)

    def synced_files_callback(self, details_list):
        now = get_monotonic_time_seconds()
        for deets in details_list:
            ciserver_path = deets.server_path.lower()
            hint = self._priority_hints.get(ciserver_path)
            if hint is None:
                continue
            if hint.synced_monotime is None:
                hint.synced_monotime = now

        self._prune_priority_hints()


class NeededHash(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ['hash',
     'size',
     'server_paths',
     'is_first',
     'parent',
     'data',
     'is_diff',
     'compressed_contents',
     'contents_len',
     'ns_id_to_blocklists',
     'namespaces',
     'fn',
     'sig',
     'orig']

    def __init__(self, hash, size, server_paths, is_first, parent):
        self.hash = hash
        self.size = size
        self.is_first = is_first
        self.server_paths = frozenset(server_paths or ())
        self.parent = parent

    def get(self, k, default = None):
        return getattr(self, k, default)

    def __repr__(self):
        toret = ['NeededHash(']
        middle = ','.join([ '%s=%r' % (k, getattr(self, k)) for k in self.__slots__ if k != '__dict__' and hasattr(self, k) ])
        if middle:
            toret.append(middle)
        toret.append(')')
        return ''.join(toret)


HashInfoTuple = collections.namedtuple('HashInfoTuple', 'retry_time, size, file_hash, is_first, parent')

class HashTransferQueue(object):

    def __init__(self, lock, file_now_waiting_cb, file_done_waiting_cb):
        self.lock = lock
        self.hash_to_waiting_files = ManyToMany(right_callbacks=(file_now_waiting_cb, file_done_waiting_cb))
        self._hash_prioritizer = HashPrioritizer(hash_to_waiting_files=self.hash_to_waiting_files)
        self._needed_hashes = HashPriorityMap(key_fn=self._hash_prioritizer.sort_key)

    def __repr__(self):
        return '<HashTransferQueue hash_to_waiting_files=%r, needed_hashes=%r>' % (self.hash_to_waiting_files, self._needed_hashes)

    def clear_needed_hashes(self):
        with self.lock:
            self.hash_to_waiting_files.clear()
            self._needed_hashes.clear()
            self._hash_prioritizer.clear()

    clear = clear_needed_hashes

    def got_hash(self, hash):
        with self.lock:
            self.hash_to_waiting_files.remove_left(hash)
            self._needed_hashes.remove(hash)

    def _no_hashes_needed_unlocked(self, server_path):
        ciserver_path = server_path.lower()
        hashes_referred_to = self.hash_to_waiting_files.remove_right(ciserver_path)
        for _hash in hashes_referred_to:
            if not self.hash_to_waiting_files.in_left(_hash):
                self._needed_hashes.remove(_hash)

    def no_hashes_needed(self, server_path):
        with self.lock:
            self._no_hashes_needed_unlocked(server_path)

    def _set_missing_unlocked(self, server_path, file_hash, parent, size, blocklist, is_first = 0):
        if len(file_hash) != DROPBOX_HASH_LENGTH:
            raise Exception('Invalid hash %r' % file_hash)
        if parent is not None and len(parent) != DROPBOX_HASH_LENGTH:
            raise Exception('Invalid parent hash %r' % parent)
        if type(size) not in (int, long):
            raise Exception('Invalid size %r' % size)
        if not isinstance(server_path, ServerPath):
            report_bad_assumption('set_missing expected ServerPath; got %r', type(server_path), full_stack=True)
        ciserver_path = server_path.lower()
        self.hash_to_waiting_files.add(file_hash, ciserver_path)
        if file_hash not in self._needed_hashes:
            self._needed_hashes.add(file_hash, HashInfoTuple(0, size, hash(blocklist), is_first, parent))

    def set_missing(self, *args, **kwargs):
        with self.lock:
            self._set_missing_unlocked(*args, **kwargs)

    def set_error(self, hash, delay = 30):
        with self.lock:
            ret = self._needed_hashes.remove(hash)
            if ret:
                TRACE('Error transferring hash %s; delaying for %.1f sec' % (hash, delay))
                self._needed_hashes.add(hash, ret._replace(retry_time=get_monotonic_time_seconds() + delay))

    def needed_hashes(self):
        return self.hash_to_waiting_files.left_keys()

    def next_needed_hash_time(self):
        try:
            retry_time = self._needed_hashes.peek(lim=1)[0][0]
        except Exception:
            return None

        if retry_time:
            return retry_time
        else:
            return get_monotonic_time_seconds()

    def next_needed_hash_batch(self, max_hashes = 1, max_size = DROPBOX_MAX_BLOCK_SIZE, need_transfer_event = None):
        ret = {}
        while not ret:
            error_wait = None
            total_size = 0
            with self.lock:
                for (retry_time, size, file_hash, is_first, parent), hash in self._needed_hashes.inorder():
                    hash_size = min(size, DROPBOX_MAX_BLOCK_SIZE)
                    if not self.hash_to_waiting_files.in_left(hash):
                        self._needed_hashes.remove(hash)
                        TRACE('Skipping hash: %r, not needed any longer', hash)
                        continue
                    ct = get_monotonic_time_seconds()
                    if retry_time and retry_time > ct:
                        if need_transfer_event is not None:
                            delta = retry_time - ct
                            error_wait = delta if error_wait is None else min(error_wait, delta)
                            TRACE('Hash still has error timeout; skipping (error_wait = %f)', error_wait)
                            continue
                    if ret and total_size + hash_size > max_size:
                        break
                    ret[hash] = nh = NeededHash(hash=hash, size=size, server_paths=self.hash_to_waiting_files.a_to_b.get(hash), is_first=is_first, parent=parent)
                    TRACE('Next needed hash: %s (needed by %r)' % (hash, nh.server_paths or '???'))
                    total_size += hash_size
                    if len(ret) == max_hashes:
                        break

            if not ret and error_wait is not None:
                with SimpleTimer('HashUploadThread sleeping in next_needed_hash_batch error_wait=%f', error_wait):
                    need_transfer_event.wait(error_wait)
            else:
                return ret

    def next_needed_hash(self):
        ret = self.next_needed_hash_batch()
        if ret:
            return ret.keys()[0]

    def get_size_totals(self):
        with self.lock:
            return self._needed_hashes.get_totals()

    def is_waiting(self, server_path, blocklist = None):
        with self.lock:
            ciserver_path = server_path.lower()
            return self.hash_to_waiting_files.in_right(ciserver_path)

    def add_priority_hint(self, server_path):
        with self.lock:
            self._hash_prioritizer.add_priority_hint(server_path)
            ciserver_path = server_path.lower()
            hashes_referred_to = self.hash_to_waiting_files.b_to_a.get(ciserver_path, ())
            for hash_ in hashes_referred_to:
                v = self._needed_hashes.remove(hash_)
                self._needed_hashes.add(hash_, v)

    def synced_files_callback(self, details_list):
        with self.lock:
            self._hash_prioritizer.synced_files_callback(details_list)


class UpdatedHashQueue(HashTransferQueue):

    def __init__(self, set_active):

        def file_now_waiting_cb(server_path, hash):
            set_active(server_path, False)

        def file_done_waiting_cb(server_path):
            set_active(server_path, True)

        HashTransferQueue.__init__(self, threading.RLock(), file_now_waiting_cb, file_done_waiting_cb)


class UploadHashQueue(HashTransferQueue):

    def __init__(self, set_active):

        def file_now_waiting_cb(server_path, hash):
            set_active(server_path, False)

        def file_done_waiting_cb(server_path):
            set_active(server_path, True)

        HashTransferQueue.__init__(self, threading.RLock(), file_now_waiting_cb, file_done_waiting_cb)

    def set_missing(self, server_path, hash_, parent, size, blocklist):
        is_first = 1 if blocklist and blocklist.startswith(hash_) else 0
        return HashTransferQueue.set_missing(self, server_path, hash_, parent, size, blocklist, is_first)


class HashFileSetLogic(SQLiteFileSetLogic):

    def get_active_subclass(self, lim = None):
        if lim is not None and lim < 0:
            raise RuntimeError('Bad limit: %r' % (lim,))
        with row_factory(self.cursor, just_the_first):
            sql = '\n            SELECT %(VALUE_COL)s FROM file_set WHERE to_pop <= ?\n            ORDER BY hash_order_sort_key ASC\n            LIMIT ?\n            ' % dict(VALUE_COL=self.VALUE_COLUMN_DEF[0])
            bindparams = (self._cur_time, -1 if lim is None else lim)
            self.cursor.execute(sql, bindparams)
            return self.cursor.fetchall()


@locked_queue_map

class ToHashFileSet(SQLiteFileSetWithFailure):
    EXTRA_COLUMN_DEFS = [('hash_order_sort_key', 'INTEGER NOT NULL', row_extract_order)]
    EXTRA_INDEX_DEFS = [('active_i', ['to_pop', 'hash_order_sort_key'])]
    LOGIC_CLASS = HashFileSetLogic

    @handle_exceptions_ex(should_raise=True)
    def sqlite_to_fs_path(self, sqlite_type):
        return self.fs.make_path(sqlite_type.decode('utf-8'))

    @handle_exceptions_ex(should_raise=True)
    def sqlite_to_hash_details(self, sqlite_type):
        d = json.loads(sqlite_type)
        if 'local_path' in d:
            d['local_path'] = self.fs.make_path(d['local_path'])
        return HashDetails(**d)

    def _sqlite_init(self):
        enable_converters([(self.fs_path_sqlite_type, self.sqlite_to_fs_path), (self.hash_details_sqlite_type, self.sqlite_to_hash_details)])

    def row_extract_local_key(self, d, to_pop):
        if self.se.case_sensitive:
            return d.local_path
        return d.local_path.lower()

    def __init__(self, sync_engine, file_cache):
        self.se = sync_engine
        self.fs = sync_engine.fs
        self.fs_path_sqlite_type = 'FSPATH_' + str(id(self.fs))
        self.hash_details_sqlite_type = 'HASHDETAILS_' + str(id(self.fs))
        self.KEY_COLUMN_DEF = ('local_path', self.fs_path_sqlite_type, self.row_extract_local_key)
        self.VALUE_COLUMN_DEF = ('details', '%s NOT NULL' % (self.hash_details_sqlite_type,), row_extract_details)
        database_dir = sync_engine.arch.APPDATA_PATH
        hash_set_path = None
        try:
            disable_on_disk_cache = sync_engine.config.get('disable_on_disk_cache', False)
            if database_dir is not None and not disable_on_disk_cache:
                for file_ in fsutil.listdir(self.fs, database_dir):
                    if file_.startswith(_HASH_DATABASE_PREFIX):
                        fsutil.safe_remove(self.fs, database_dir.join(file_))

                fd, hash_set_path = tempfile.mkstemp(dir=unicode(database_dir), prefix=_HASH_DATABASE_PREFIX)
                os.close(fd)
        except Exception:
            unhandled_exc_handler()

        with file_cache.write_lock() as trans:
            trans.clear_held()
        SQLiteFileSetWithFailure.__init__(self, name='TO_HASH', path=hash_set_path)
