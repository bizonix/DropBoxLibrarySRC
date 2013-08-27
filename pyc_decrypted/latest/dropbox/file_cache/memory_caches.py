#Embedded file name: dropbox/file_cache/memory_caches.py
from __future__ import absolute_import
import contextlib
import errno
import functools
import itertools
import operator
import os
import sqlite3
import sys
import threading
import time
from collections import MutableMapping
from contextlib import contextmanager
from dropbox.callbacks import Handler
from dropbox.fastdetails import FastDetails
from dropbox.functions import handle_exceptions_ex, null_context
from dropbox.low_functions import add_inner_methods, add_inner_properties, const, curry, head, propagate_none
from dropbox.server_path import ServerPath, is_server_path
from dropbox.sqlite3_helpers import MAIN_DB_NAME, SqliteConnectionHub, archive_database, create_tables, enable_converters, just_the_first, row_factory, sqlite3_get_table_entries, unique_in_memory_database_uri
from dropbox.trace import TRACE, assert_, report_bad_assumption, unhandled_exc_handler
from .constants import MOUNT_REQUEST_UNMOUNT, MOUNT_REQUEST_MOUNT, UPLOAD_QUOTA_CODE
from .util import sqlite_to_fastdetails, fastdetails_to_sqlite, sqlite_to_serverpath, serverpath_to_sqlite

class NamespaceMountTable(object):

    def __init__(self):
        self.mounts = {}

    def copy(self):
        a = object.__new__(self.__class__)
        a.mounts = dict(self.mounts)
        return a

    def __nonzero__(self):
        return bool(self.mounts)

    def __repr__(self):
        return repr(self.mounts)

    def mount_points(self):
        return self.mounts.iteritems()

    def child_mount_points(self, ns_rel_path, lower = True):
        ns_rel_path_lowered = ns_rel_path.lower() if lower else ns_rel_path
        assert ns_rel_path_lowered[-1] != '/'
        for rel_path, other_ns in self.mounts.iteritems():
            if rel_path.startswith(ns_rel_path_lowered + '/'):
                yield (rel_path, other_ns)

    def mount(self, ns_rel_path, ns, lower = True):
        ns_rel_path_lowered = ns_rel_path.lower() if lower else ns_rel_path
        assert ns_rel_path_lowered not in self.mounts
        self.mounts[ns_rel_path_lowered] = ns

    def unmount(self, ns_rel_path, lower = True):
        ns_rel_path_lowered = ns_rel_path.lower() if lower else ns_rel_path
        del self.mounts[ns_rel_path_lowered]

    def is_mount_point(self, ns_rel_path, lower = True):
        ns_rel_path_lowered = ns_rel_path.lower() if lower else ns_rel_path
        try:
            return self.mounts[ns_rel_path_lowered]
        except KeyError:
            return None

    def ns_is_mounted(self, ns):
        for rel_path, other_ns in self.mounts.iteritems():
            if other_ns == ns:
                return rel_path

    def translate_relative_path(self, root_ns, rel_path, lower = True, add_slash = False):
        rel_path_lowered = rel_path.lower() if lower else rel_path
        rel_path_slash = os.path.join(rel_path_lowered, u'') if add_slash else rel_path_lowered
        for rel_mount_point, ns in self.mounts.iteritems():
            if rel_path_slash.startswith(rel_mount_point + '/'):
                new_rel_base = os.path.join(rel_path, u'') if add_slash else rel_path
                return ServerPath.from_ns_rel(ns, new_rel_base[len(rel_mount_point):])

        return ServerPath.from_ns_rel(root_ns, rel_path)


def locked_queue_map(cls):

    class LockedFileSet(cls):

        def __init__(self, *n, **kw):
            cls.__init__(self, *n, **kw)
            if hasattr(self, 'lock'):
                raise Exception('Super class uses lock!')
            self.lock = threading.RLock()

        def l(fn):

            @functools.wraps(fn)
            def wrapped(self, *n, **kw):
                with self:
                    return fn(self, *n, **kw)

            return wrapped

        add = l(cls.add_unlocked)
        add_batch = l(cls.add_batch_unlocked)
        set_active = l(cls.set_active_unlocked)
        retry = l(cls.retry_unlocked)
        remove = l(cls.remove_unlocked)
        checked_remove = l(cls.checked_remove_unlocked)
        clear = l(cls.clear_unlocked)
        copy = l(cls.copy_unlocked)
        clear_retry_map = l(cls.clear_retry_map_unlocked)
        to_pop_time = l(cls.to_pop_time_unlocked)
        get = l(cls.get_unlocked)
        get_active = l(cls.get_active_unlocked)
        get_batch = l(cls.get_batch_unlocked)
        get_failure_counts = l(cls.get_failure_counts_unlocked)
        get_only_file = l(cls.get_only_file_unlocked)
        get_status = l(cls.get_status_unlocked)
        is_active = l(cls.is_active_unlocked)
        is_unactive = l(cls.is_unactive_unlocked)
        is_waiting = l(cls.is_waiting_unlocked)
        is_failing = l(cls.is_failing_unlocked)
        ready_time = l(cls.ready_time_unlocked)
        active_count = l(cls.active_count_unlocked)
        counts = l(cls.counts_unlocked)

        def __enter__(self):
            self.lock.__enter__()
            try:
                enter = cls.__enter__
            except AttributeError:
                pass
            else:
                return enter(self)

        def __exit__(self, *n, **kw):
            try:
                exit_ = cls.__exit__
            except AttributeError:
                pass
            else:
                exit_(self, *n, **kw)

            self.lock.__exit__(*n, **kw)

        __contains__ = l(cls.__contains__)
        __len__ = l(cls.__len__)
        __getitem__ = l(cls.__getitem__)

        def __iter__(self):
            with self.lock:
                for i in super(LockedFileSet, self).__iter__():
                    yield i

        __eq__ = l(cls.__eq__)

        def cas(self, key, old_data, new_data):
            with self:
                real_old = self.get_unlocked(key)
                if real_old == old_data:
                    if new_data is None:
                        self.remove_unlocked(key)
                    else:
                        self.add_unlocked(new_data)
                return real_old

        del l

    return LockedFileSet


class FailureData(object):
    __slots__ = ('reason', 'retry_interval')

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)


def server_path_wrap(fn):

    @functools.wraps(fn)
    def wrapped(self, server_path, *n, **kw):
        assert_(lambda : is_server_path(server_path))
        lower = kw.pop('lower', True)
        return fn(self, (server_path.lower() if lower else server_path), *n, **kw)

    return wrapped


def server_path_timed_queue_map(cls):

    class ServerPathTimedQueueMap(cls):

        def __contains__(self, server_path):
            assert_(lambda : is_server_path(server_path))
            return cls.__contains__(self, server_path.lower())

        def __getitem__(self, server_path):
            assert_(lambda : is_server_path(server_path))
            return cls.__getitem__(self, server_path.lower())

    return ServerPathTimedQueueMap


INT64_MAX = 2 ** 63 - 1
FILE_SET_TABLE_NAME = 'file_set'

def normalize_iter_to_list(iter_):
    try:
        iter_[-1]
    except TypeError:
        return list(iter_)
    except IndexError:
        return []

    return iter_


@add_inner_properties('KEY_COLUMN_DEF', 'VALUE_COLUMN_DEF', '_all_cols', '_public_to_pop', 'error_callbacks', 'add_error_callback', 'remove_error_callback', 'name', 'on_retry', 'add_retry_handler', 'remove_retry_handler', 'on_key_mod', 'add_keymod_handler', 'remove_keymod_handler', inner_name='pending')

@add_inner_methods('__enter__', '__exit__', inner_name='pending')

class SQLiteFileSetLogic(object):
    _cur_time = None

    def __init__(self, pending, dbname, curs):
        self.pending = pending
        self.dbname = dbname
        self.cursor = curs
        self.sql_vars = self._sql_vars()

    def _table_name(self):
        return '%s.%s' % (self.dbname, FILE_SET_TABLE_NAME)

    def _sql_vars(self, **kw):
        kw.update(dict(KEY_COL=self.KEY_COLUMN_DEF[0], VAL_COL=self.VALUE_COLUMN_DEF[0], FILE_SET_TABLE_NAME=self._table_name(), FILE_SET_BASE_TABLE_NAME=FILE_SET_TABLE_NAME))
        return kw

    def _get_full_row(self, l_server_path):
        with row_factory(self.cursor, sqlite3.Row):
            sql = '\nSELECT\ndetails, public_to_pop(to_pop) as to_pop,\nfailure_interval, failure_reason\nFROM %(FILE_SET_TABLE_NAME)s WHERE\n%(KEY_COL)s = ?' % self.sql_vars
            self.cursor.execute(sql, (l_server_path,))
            return self.cursor.fetchone()

    def _get_row(self, l_server_path):
        row = self._get_full_row(l_server_path)
        if row is None:
            return
        return (row['details'], row['to_pop'])

    def _update_cur_time(fn):

        @functools.wraps(fn)
        def wrapped(self, *n, **kw):
            self._cur_time = time.time()
            return fn(self, *n, **kw)

        return wrapped

    _sql_method = _update_cur_time

    def checked_remove(self, key_to_old_data):
        with self:
            current_data = self.get_batch(key_to_old_data.keys(), lower=False)
            to_remove = []
            for hash_details in current_data:
                key = self.get_key(hash_details)
                old_data = key_to_old_data.get(key)
                if old_data == hash_details:
                    to_remove.append(key)

            self.discard_batch(to_remove, lower=False)

    @_sql_method
    def discard_batch(self, server_paths_, lower = True):
        server_paths = normalize_iter_to_list(server_paths_)
        if not server_paths:
            return
        KEY_COL = self.sql_vars['KEY_COL']
        VAL_COL = self.sql_vars['VAL_COL']
        TABLE_NAME = self.sql_vars['FILE_SET_TABLE_NAME']
        if lower:
            iter_ = lambda : itertools.imap(operator.methodcaller('lower'), server_paths)
        else:
            iter_ = lambda : server_paths
        desired_columns = [KEY_COL,
         VAL_COL,
         'public_to_pop(to_pop) as to_pop',
         'failure_reason']
        old_ents = sqlite3_get_table_entries(self.cursor, TABLE_NAME, KEY_COL, iter_(), desired_columns=desired_columns)
        sp2ent = dict(((row[KEY_COL], row) for row in old_ents))
        sql = '\nDELETE FROM %(FILE_SET_TABLE_NAME)s WHERE %(KEY_COL)s = ?\n' % self.sql_vars
        self.cursor.executemany(sql, ((sp,) for sp in iter_()))
        to_ret = []
        for sp in iter_():
            try:
                old = sp2ent[sp]
            except KeyError:
                continue

            TRACE('%s: Removed %r, to_pop: %r', self.name, old[VAL_COL], old['to_pop'])
            self.on_key_mod(sp, (old[VAL_COL], old['to_pop']), None)
            if old['failure_reason']:
                self.error_callbacks.run_handlers('remove', old['failure_reason'], server_path=sp)
            to_ret.append(old)

        return to_ret

    def get_batch(self, sps_, lower = True):
        KEY_COL = self.sql_vars['KEY_COL']
        VAL_COL = self.sql_vars['VAL_COL']
        TABLE_NAME = self.sql_vars['FILE_SET_TABLE_NAME']
        sps = itertools.imap(operator.methodcaller('lower'), sps_) if lower else sps_
        ret = sqlite3_get_table_entries(self.cursor, TABLE_NAME, KEY_COL, sps, row_factory=just_the_first, desired_columns=[VAL_COL])
        return list(ret)

    def get_key(self, d):
        return self.pending.KEY_COLUMN_DEF[2](d, None)

    def add_batch(self, to_add_):
        to_add = normalize_iter_to_list(to_add_)
        if not to_add:
            return
        KEY_COL = self.sql_vars['KEY_COL']
        VAL_COL = self.sql_vars['VAL_COL']
        TABLE_NAME = self.sql_vars['FILE_SET_TABLE_NAME']
        old_ents = sqlite3_get_table_entries(self.cursor, TABLE_NAME, KEY_COL, (self.get_key(d) for d, _ in to_add), desired_columns=[KEY_COL, VAL_COL, 'public_to_pop(to_pop) as to_pop'])
        sp2ent = dict(((row[KEY_COL], (row[VAL_COL], row['to_pop'])) for row in old_ents))
        insert_columns = ','.join((v[0] for v in self._all_cols()))

        def map_(*n):
            return tuple((v[2](*n) for v in self._all_cols()))

        sql = ('REPLACE INTO %s ' + '(%s) VALUES ' + '(%s)') % (TABLE_NAME, insert_columns, ','.join(itertools.repeat('?', len(self._all_cols()))))
        self.cursor.executemany(sql, (map_(*n) for n in to_add))
        to_ret = []
        for d, to_pop in to_add:
            l_server_path = self.get_key(d)
            try:
                old = sp2ent[l_server_path]
            except KeyError:
                TRACE('%s: Added %r, to_pop=%r', self.name, d, to_pop)
                old = None
            else:
                TRACE('%s: Updated to (%r, to_pop=%r) was (%r, to_pop=%r)', self.name, d, to_pop, *old)

            self.on_key_mod(l_server_path, old, (d, to_pop))
            to_ret.append(old)

        return to_ret

    def clear(self):
        TABLE_NAME = self.sql_vars['FILE_SET_TABLE_NAME']
        self.cursor.execute('DELETE FROM %s.delete_t' % (self.dbname,))
        try:
            self.cursor.execute('\nINSERT INTO %s.delete_t (to_pop, details)\nSELECT to_pop, details FROM %s' % (self.dbname, TABLE_NAME))
            self.cursor.execute('DELETE FROM %s' % (TABLE_NAME,))
            with row_factory(self.cursor, None):
                self.cursor.execute('SELECT details, public_to_pop(to_pop) FROM %s.delete_t' % (self.dbname,))
                for details, to_pop in self.cursor:
                    self.on_key_mod(self.get_key(details), (details, to_pop), None)

            TRACE('%s: Cleared out everything', self.name)
        finally:
            self.cursor.execute('DELETE FROM %s.delete_t' % (self.dbname,))

    def add(self, details, to_pop = 0):
        return self.add_batch([(details, to_pop)])[0]

    def remove(self, l_server_path):
        ret = self.discard_batch([l_server_path], lower=False)
        if not ret:
            raise KeyError("Don't have %r" % l_server_path)
        return ret[0]

    def set_active(self, l_server_path, is_active):
        TRACE('%s: Setting %r to %r', self.name, l_server_path, 'active' if is_active else 'inactive')
        old = self._get_row(l_server_path)
        if old is None:
            return
        new_to_pop = 0 if is_active else INT64_MAX
        public_new_to_pop = self._public_to_pop(new_to_pop)
        if old[1] == public_new_to_pop:
            return
        sql = '\nUPDATE %(FILE_SET_TABLE_NAME)s SET to_pop = ? WHERE %(KEY_COL)s = ?\n' % self.sql_vars
        self.cursor.execute(sql, (new_to_pop, l_server_path))
        self.on_key_mod(l_server_path, old, (old[0], public_new_to_pop))

    def retry(self, l_server_path, reason, interval = None):
        row = self._get_full_row(l_server_path)
        if row is None or row['to_pop']:
            report_bad_assumption("Item %r wasn't active in memory cache %r, did mount_transition happen?" % (l_server_path, self.name))
            return
        old_interval = row['failure_interval']
        if interval is None:
            new_interval = 5 if old_interval is None else min(old_interval * 2, 3600)
            if not (new_interval < 1000 or old_interval is not None and old_interval >= 1000):
                if reason != UPLOAD_QUOTA_CODE:
                    report_bad_assumption('Entry continuously rejected (%r) %r' % (row['details'], old_interval))
        else:
            try:
                new_interval = interval(old_interval)
            except TypeError:
                new_interval = interval

        TRACE('%s: Retrying %r in %r seconds because %s', self.name, row['details'], new_interval, reason)
        new_to_pop = new_interval + time.time()
        sql = '\nUPDATE %(FILE_SET_TABLE_NAME)s SET\nto_pop = ?, failure_reason = ?, failure_interval = ?\nWHERE %(KEY_COL)s = ?\n' % self.sql_vars
        self.cursor.execute(sql, (new_to_pop,
         reason,
         new_interval,
         l_server_path))
        self.on_key_mod(l_server_path, (row['details'], row['to_pop']), (row['details'], new_to_pop))
        self.on_retry(l_server_path, reason)
        self.error_callbacks.run_handlers('retry', reason=reason, server_path=l_server_path, details=self.get(l_server_path), retry_interval=new_interval)
        return new_interval

    def clear_retry_map(self, reason):
        sql = '\nUPDATE %(FILE_SET_TABLE_NAME)s SET\nfailure_reason = NULL,\nfailure_interval = NULL,\nto_pop = 0\nWHERE failure_reason = ?'
        sql %= self.sql_vars
        self.cursor.execute(sql, (reason,))
        count = self.cursor.rowcount
        TRACE("Cleared %s '%s' retry entries", count, reason)
        self.error_callbacks.run_handlers('clear_retry')
        return count

    @_sql_method
    def get_active(self, *n, **kw):
        return self.get_active_subclass(*n, **kw)

    def get_active_subclass(self, *n, **kw):
        raise NotImplementedError('subclasses must implement this!')

    def to_pop_time(self, l_server_path):
        with row_factory(self.cursor, just_the_first):
            sql = '\nSELECT public_to_pop(to_pop) FROM %(FILE_SET_TABLE_NAME)s WHERE server_path = ?\n'
            sql %= self.sql_vars
            self.cursor.execute(sql, (l_server_path,))
            return self.cursor.fetchone()

    def iteritems(self):
        with row_factory(self.cursor, None):
            sql = 'SELECT %(KEY_COL)s, details FROM %(FILE_SET_TABLE_NAME)s'
            sql %= self.sql_vars
            self.cursor.execute(sql)
            for elt in self.cursor:
                yield elt

    def get_size(self):
        sql = 'SELECT COUNT(*) FROM %(FILE_SET_TABLE_NAME)s'
        sql %= self.sql_vars
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    def get_only_file(self):
        if self.get_size() != 1:
            return None
        return head(self.iteritems())[1]

    def get(self, l_server_path):
        sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE %(KEY_COL)s = ?\n' % self.sql_vars
        self.cursor.execute(sql, (l_server_path,))
        return propagate_none(operator.itemgetter(0), self.cursor.fetchone())

    def get_failure_counts(self, constructor = None):
        sql = '\nSELECT failure_reason, count(*) FROM %(FILE_SET_TABLE_NAME)s\nWHERE failure_reason IS NOT NULL\nGROUP BY failure_reason\n' % self.sql_vars
        self.cursor.execute(sql)
        if constructor is None:
            constructor = functools.partial(map, tuple)
        return constructor(self.cursor)

    @_sql_method
    def get_status(self, l_server_path):
        sql = "\nSELECT IFNULL(\nCASE to_pop BETWEEN ? AND ?\n WHEN 1 THEN failure_reason\n ELSE NULL END, 'in progress')\nFROM %(FILE_SET_TABLE_NAME)s WHERE\n%(KEY_COL)s = ?\n" % self.sql_vars
        with row_factory(self.cursor, just_the_first):
            self.cursor.execute(sql, (self._cur_time + 1, INT64_MAX - 1, l_server_path))
            return self.cursor.fetchone()

    @_sql_method
    def is_active(self, l_server_path):
        sql = '\nSELECT EXISTS(\nSELECT 1 FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop <= ? AND\n%(KEY_COL)s = ?)\n' % self.sql_vars
        self.cursor.execute(sql, (self._cur_time, l_server_path))
        return self.cursor.fetchone()[0]

    @_sql_method
    def is_unactive(self, l_server_path):
        sql = '\nSELECT EXISTS(\nSELECT 1 FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop = ? AND\n%(KEY_COL)s = ?)\n' % self.sql_vars
        self.cursor.execute(sql, (INT64_MAX, l_server_path))
        return self.cursor.fetchone()[0]

    @_sql_method
    def is_waiting(self, l_server_path):
        sql = '\nSELECT EXISTS(\nSELECT 1 FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop BETWEEN ? AND ? AND\n%(KEY_COL)s = ?)\n' % self.sql_vars
        self.cursor.execute(sql, (self._cur_time + 1, INT64_MAX - 1, l_server_path))
        return self.cursor.fetchone()[0]

    @_sql_method
    def is_failing(self, l_server_path):
        sql = '\nSELECT EXISTS(\nSELECT 1 FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop BETWEEN ? AND ? AND\nfailure_reason IS NOT NULL AND\n%(KEY_COL)s = ?)\n' % self.sql_vars
        self.cursor.execute(sql, (self._cur_time + 1, INT64_MAX - 1, l_server_path))
        return self.cursor.fetchone()[0]

    @_sql_method
    def ready_time(self):
        sql = '\nSELECT MIN(to_pop) FROM %(FILE_SET_TABLE_NAME)s\n'
        sql %= self.sql_vars
        self.cursor.execute(sql)
        min_to_pop = self.cursor.fetchone()[0]
        assert_(lambda : min_to_pop is None or min_to_pop >= 0, 'Min to pop was negative? %r', min_to_pop)
        if min_to_pop is None or min_to_pop == INT64_MAX:
            return
        elif not min_to_pop:
            return time.time()
        else:
            return min_to_pop

    @_sql_method
    def active_count(self):
        sql = '\nSELECT COUNT(*) FROM %(FILE_SET_TABLE_NAME)s WHERE to_pop <= ?\n'
        sql %= self.sql_vars
        self.cursor.execute(sql, (self._cur_time,))
        return self.cursor.fetchone()[0]

    @_sql_method
    def counts(self):
        sql = "\nSELECT (CASE to_pop WHEN ? THEN 'inactive' ELSE\n          (CASE to_pop <= ? WHEN 1 THEN 'active' ELSE 'waiting' END)\n        END) as label,\n       COUNT(*) the_count FROM %(FILE_SET_TABLE_NAME)s\nGROUP BY label\n"
        sql %= self.sql_vars
        self.cursor.execute(sql, (INT64_MAX, self._cur_time))
        res = dict(self.cursor.fetchall())
        return (res.get('active', 0), res.get('waiting', 0), res.get('inactive', 0))

    @_sql_method
    def is_equal_to_db(self, other_dbname):
        clause = ' AND '.join((('a.%s = b.%s' % (column_name, column_name) if 'NOT NULL' in type_name_constraint else '(a.%s IS NULL AND b.%s IS NULL OR a.%s = b.%s)' % (column_name,
         column_name,
         column_name,
         column_name)) for column_name, type_name_constraint, _ in self._all_cols()))
        sql = '\nSELECT MIN(%(MIN_CLAUSE)s) FROM\n%(FILE_SET_TABLE_NAME)s AS a\nLEFT JOIN %(OTHER_DB_NAME)s.%(FILE_SET_BASE_TABLE_NAME)s AS b\nON a.%(KEY_COL)s = b.%(KEY_COL)s\n'
        sql_vars = dict(self.sql_vars)
        sql_vars.update(dict(MIN_CLAUSE=clause, OTHER_DB_NAME=other_dbname))
        sql %= sql_vars
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]

    @_sql_method
    def _dump(self, file = sys.stdout):
        with row_factory(self.cursor, sqlite3.Row):
            self.cursor.execute('SELECT * FROM %(FILE_SET_TABLE_NAME)s' % self.sql_vars)
            for r in self.cursor:
                print >> file, repr(dict(r))


def row_extract_l_server_path(d, to_pop):
    return d.server_path.lower()


def row_extract_to_pop(d, to_pop):
    if to_pop < 0:
        return INT64_MAX
    return to_pop


def row_extract_details(d, to_pop):
    return d


def row_extract_ns(d, to_pop):
    return d.server_path.ns


def row_extract_mount_request_sort_key(details, to_pop):
    mrt = getattr(details, 'mount_request', None)
    if mrt is None:
        mr = 2
    else:
        try:
            mr = mrt[0]
        except Exception:
            unhandled_exc_handler()
            mr = 2
        else:
            if mr == MOUNT_REQUEST_UNMOUNT:
                mr = 0
            elif mr == MOUNT_REQUEST_MOUNT:
                mr = 1
            else:
                mr = 2

    return mr


def row_extract_create_tries(details, to_pop):
    return getattr(details, 'create_tries', 0)


def row_extract_delete_sort_key(details, to_pop):
    return (-1 if details.size < 0 else 1) * len(details.server_path)


def row_extract_local_guid(d, to_pop):
    return getattr(d, 'local_guid', None)


def row_extract_guid(d, to_pop):
    return getattr(d, 'guid', None)


def row_extract_parent_guid(d, to_pop):
    return getattr(d, 'parent_guid', None)


def row_extract_previous_guid_sjid(d, to_pop):
    return getattr(d, 'previous_guid_sjid', None)


def row_extract_derived_guid(d, to_pop):
    return getattr(d, 'derived_guid', None)


class SQLiteFileSetWithFailure(MutableMapping):
    KEY_COLUMN_DEF = ('server_path', 'SERVERPATH', row_extract_l_server_path)
    VALUE_COLUMN_DEF = ('details', 'FASTDETAILS NOT NULL', row_extract_details)
    DEFAULT_COLUMN_DEFS = [('to_pop', 'INTEGER NOT NULL', row_extract_to_pop), ('failure_reason', 'TEXT', const(None)), ('failure_interval', 'INTEGER', const(None))]
    DEFAULT_INDEX_DEFS = []
    EXTRA_COLUMN_DEFS = []
    EXTRA_INDEX_DEFS = []
    EXTRA_TABLE_CONSTRAINTS = []
    LOGIC_CLASS = SQLiteFileSetLogic

    @classmethod
    def _post_create(cls, conn):
        conn.execute('PRAGMA journal_mode=MEMORY')
        conn.execute('PRAGMA synchronous=OFF')
        cls._add_db_functions(conn)

    @classmethod
    def _add_db_functions(cls, conn):
        try:
            conn.execute('SELECT has_pending_file_set_functions(0)')
        except sqlite3.OperationalError:
            has_pending_file_set_functions = lambda _: _
            conn.create_function('public_to_pop', 1, cls._public_to_pop)
            conn.create_function('details_with_guid', 2, cls._details_with_guid)
            conn.create_function('has_pending_file_set_functions', 1, has_pending_file_set_functions)

    @staticmethod
    @curry(propagate_none)
    @handle_exceptions_ex(should_raise=True)
    def _public_to_pop(db_to_pop):
        if db_to_pop == INT64_MAX:
            return -1
        elif db_to_pop <= time.time():
            return 0
        else:
            return db_to_pop

    @classmethod
    @handle_exceptions_ex(should_raise=True)
    def _details_with_guid(cls, details, guid):
        return fastdetails_to_sqlite(sqlite_to_fastdetails(details).copy(guid=guid))

    @classmethod
    def _sqlite_init(cls):
        enable_converters([('FASTDETAILS', sqlite_to_fastdetails), ('SERVERPATH', sqlite_to_serverpath)], adapters=[(FastDetails, fastdetails_to_sqlite), (ServerPath, serverpath_to_sqlite)])

    def _all_cols(self):
        return [self.KEY_COLUMN_DEF, self.VALUE_COLUMN_DEF] + self.DEFAULT_COLUMN_DEFS + self.EXTRA_COLUMN_DEFS

    def on_key_mod(self, *n, **kw):
        return self._on_key_mod(self, *n, **kw)

    def __init__(self, name, path):
        self.connhub = None
        self.name = name
        _on_key_mod_handler = Handler(handle_exc=unhandled_exc_handler)
        self._on_key_mod = _on_key_mod_handler.run_handlers
        self.add_keymod_handler = _on_key_mod_handler.add_handler
        self.remove_keymod_handler = _on_key_mod_handler.remove_handler
        _on_retry_handler = Handler(handle_exc=unhandled_exc_handler)
        self.on_retry = _on_retry_handler.run_handlers
        self.add_retry_handler = _on_retry_handler.add_handler
        self.remove_retry_handler = _on_retry_handler.remove_handler
        self.error_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_error_callback = self.error_callbacks.add_handler
        self.remove_error_callback = self.error_callbacks.remove_handler
        if path is None:
            path = unique_in_memory_database_uri()
        self._sqlite_init()
        self.connhub = SqliteConnectionHub(path, isolation_level=None, post_create=self._post_create, detect_types=sqlite3.PARSE_DECLTYPES, trevor=os.urandom(16))
        try:
            self._create_tables()
        except:
            self.close()
            raise

    def _create_tables(self, force = False):
        table_defs = [(FILE_SET_TABLE_NAME,
          self._all_cols(),
          ['PRIMARY KEY (%s)' % (self.KEY_COLUMN_DEF[0],)] + self.EXTRA_TABLE_CONSTRAINTS,
          self.DEFAULT_INDEX_DEFS + self.EXTRA_INDEX_DEFS), ('delete_t',
          [('to_pop', 'INTEGER NOT NULL'), self.VALUE_COLUMN_DEF],
          [],
          [])]
        with self._wcursor() as cursor:
            create_tables(cursor, table_defs, force=force)

    @contextmanager
    def _wcursor(self):
        with contextlib.closing(self.connhub.conn().cursor()) as curs:
            yield curs

    @contextlib.contextmanager
    def _attach_trans(self, other = None):
        with self._wcursor() as cursor:
            with null_context() if other is None else other.attach_to(cursor) as other_curs:
                with self.connhub.conn():
                    cursor.execute('BEGIN TRANSACTION')
                    yield (cursor, other_curs)

    def _import(self, other):
        with self._attach_trans(other) as cursor, other_curs:
            archive_database(cursor, MAIN_DB_NAME, other_curs.dbname)

    def copy_unlocked(self, newpath = None):
        new_db = type(self)(newpath)
        new_db._import(self)
        return new_db

    def __metaclass__(name, bases, dict_):

        def create_fn(name):

            def wrapped(self, *n, **kw):
                with self._attach_trans() as cursor, _:
                    db_logic = self.LOGIC_CLASS(self, MAIN_DB_NAME, cursor)
                    return getattr(db_logic, name)(*n, **kw)

            return wrapped

        for meth_name in ['_dump',
         'active_count',
         'add',
         'add_batch',
         'checked_remove',
         'clear',
         'clear_retry_map',
         'counts',
         'get',
         'get_batch',
         'get_active',
         'get_failure_counts',
         'get_only_file',
         'get_size',
         'get_status',
         'is_active',
         'is_failing',
         'is_unactive',
         'is_waiting',
         'ready_time',
         'remove',
         'retry',
         'set_active',
         'to_pop_time']:
            new_meth_name = '%s_unlocked' % (meth_name,)
            assert new_meth_name not in dict_
            new_fn = create_fn(meth_name)
            new_fn.__name__ = new_meth_name
            dict_[new_meth_name] = new_fn

        return type(name, bases, dict_)

    @contextmanager
    def attach_to(self, curs, name = None):
        with self.connhub.attach_to(curs, name=name) as real_name:
            self._add_db_functions(curs.connection)
            yield self.LOGIC_CLASS(self, real_name, curs)

    def close(self):
        if self.connhub is None:
            return
        self.connhub.close()
        self.connhub = None

    def __len__(self):
        return self.get_size_unlocked()

    @handle_exceptions_ex(should_raise=True)
    def __del__(self):
        self.close()

    def __iter__(self):
        with self._attach_trans() as cursor, _:
            cursor.execute('BEGIN TRANSACTION')
            db_logic = self.LOGIC_CLASS(self, MAIN_DB_NAME, cursor)
            for key, _ in db_logic.iteritems():
                yield key

    def __contains__(self, l_server_path):
        return bool(self.get_unlocked(l_server_path))

    def __getitem__(self, l_server_path):
        ret = self.get_unlocked(l_server_path)
        if ret is None:
            raise KeyError()
        return ret

    def __setitem__(self, k, v):
        raise NotImplementedError("Doesn't make sense for this class")

    def __delitem__(self, k):
        raise NotImplementedError("Doesn't make sense for this class")

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        with self._attach_trans(other) as cursor, other_curs:
            db_logic = self.LOGIC_CLASS(self, MAIN_DB_NAME, cursor)
            return db_logic.is_equal_to_db(other_curs.dbname)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<%s.%s name=%r uri=%r>' % (self.__module__,
         type(self).__name__,
         self.name,
         self.connhub.n[0])


def server_path_file_set_logic(cls):
    new_dict = {meth:server_path_wrap(getattr(cls, meth)) for meth in ['get',
     'get_status',
     'is_active',
     'is_failing',
     'is_unactive',
     'is_waiting',
     'remove',
     'retry',
     'set_active',
     'to_pop_time']}
    return type(cls.__name__, (cls,), new_dict)


@server_path_file_set_logic

class PendingFileSetLogic(SQLiteFileSetLogic):

    def modify_guid_mapping_batch(self, new_mappings):
        new_mappings = list(new_mappings)
        if not new_mappings:
            return
        self.cursor.execute('DELETE FROM modify_t')
        try:
            self.cursor.executemany('\nINSERT INTO modify_t (pending_id, guid)\nSELECT rowid, guid FROM file_set AS one WHERE\nlocal_guid = ? AND (guid is NULL OR guid != ?)\n', new_mappings)
            self.cursor.executemany('\nUPDATE %(FILE_SET_TABLE_NAME) SET\nguid = ?,\ndetails = details_with_guid(details, ?)\nWHERE\nlocal_guid = ? AND (guid IS NULL OR guid != ?)' % self.sql_vars, ((guid,
             guid,
             local_guid,
             guid) for local_guid, guid in new_mappings if local_guid is not None and guid is not None))
            self.cursor.execute('\nSELECT\nmodify_t.guid as old_guid,\n%(FILE_SET_TABLE_NAME)s.details,\npublic_to_pop(%(FILE_SET_TABLE_NAME)s.to_pop)\nFROM modify_t LEFT JOIN %(FILE_SET_TABLE_NAME)s ON\nmodify_t.pending_id = %(FILE_SET_TABLE_NAME)s.rowid' % self.sql_vars)
            for old_guid, new_details, to_pop in self.cursor:
                old_details = new_details.copy(guid=old_guid)
                self.on_key_mod(new_details.server_path.lower(), (old_details, to_pop), (new_details, to_pop))

        finally:
            self.cursor.execute('DELETE FROM modify_t')

    def get_active_subclass(self, lim = None, priority_nses = ()):
        if lim is not None and lim < 0:
            raise RuntimeError('Invalid limit passed: %r' % lim)
        with row_factory(self.cursor, just_the_first):
            sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop <= ? AND mount_request_sort_key IN (0, 1)\nORDER BY to_pop, ns, mount_request_sort_key LIMIT 1\n'
            sql %= self.sql_vars
            self.cursor.execute(sql, (self._cur_time,))
            deets = self.cursor.fetchall()
            if deets:
                return deets
            sql_lim = -1 if lim is None else lim
            for ns in priority_nses:
                sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE to_pop <= ? AND ns = ?\nORDER BY to_pop, ns, mount_request_sort_key, delete_sort_key ASC\nLIMIT ?\n'
                sql %= self.sql_vars
                self.cursor.execute(sql, (self._cur_time, ns, sql_lim))
                res = self.cursor.fetchall()
                if res:
                    return res
            else:
                sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop <= :cur_time AND\nns = (\n    SELECT ns FROM %(FILE_SET_TABLE_NAME)s WHERE to_pop <= :cur_time\n    ORDER BY to_pop, ns, mount_request_sort_key, delete_sort_key ASC\n    LIMIT 1\n)\nORDER BY to_pop, ns, mount_request_sort_key, delete_sort_key ASC\nLIMIT :lim\n'
                sql %= self.sql_vars
                self.cursor.execute(sql, dict(cur_time=self._cur_time, lim=sql_lim))
                return self.cursor.fetchall()


@locked_queue_map

@server_path_timed_queue_map

class PendingFileSetWithFailure(SQLiteFileSetWithFailure):
    EXTRA_COLUMN_DEFS = [('ns', 'INTEGER NOT NULL', row_extract_ns),
     ('mount_request_sort_key', 'INTEGER NOT NULL', row_extract_mount_request_sort_key),
     ('delete_sort_key', 'INTEGER NOT NULL', row_extract_delete_sort_key),
     ('local_guid', 'BYTETEXT', row_extract_local_guid),
     ('guid', 'BYTETEXT', row_extract_guid),
     ('previous_guid_sjid', 'INTEGER', row_extract_previous_guid_sjid),
     ('derived_guid', 'BYTETEXT', row_extract_derived_guid)]
    EXTRA_INDEX_DEFS = [('active_i', ['to_pop',
       'ns',
       'mount_request_sort_key',
       'delete_sort_key'])]
    LOGIC_CLASS = PendingFileSetLogic

    def __init__(self, *n, **kw):
        SQLiteFileSetWithFailure.__init__(self, 'PENDING', *n, **kw)

    def _create_tables(self, force = False):
        SQLiteFileSetWithFailure._create_tables(self, force=force)
        table_def = ('modify_t',
         [('pending_id', 'INTEGER NOT NULL'), ('guid', 'BYTETEXT')],
         [],
         [])
        with self._wcursor() as cursor:
            create_tables(cursor, [table_def], force=force)


UPDATED_FILE_SET_GUID_COL = 'guid'

@server_path_file_set_logic

class UpdatedFileSetLogic(SQLiteFileSetLogic):

    def discard_by_guid_batch(self, guids_):
        guids = list(guids_)
        if not guids:
            return
        KEY_COL = self.sql_vars['KEY_COL']
        TABLE_NAME = self.sql_vars['FILE_SET_TABLE_NAME']
        keys_to_discard = sqlite3_get_table_entries(self.cursor, TABLE_NAME, UPDATED_FILE_SET_GUID_COL, guids, desired_columns=[KEY_COL], row_factory=just_the_first)
        self.discard_batch(keys_to_discard, lower=False)

    def get_active_subclass(self, lim = None, priority_nses = (), partition = False):
        if lim is not None and lim < 0:
            raise RuntimeError('Bad limit: %r' % (lim,))
        for ns in priority_nses:
            sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE\nto_pop <= ? AND ns = ?\nORDER BY delete_sort_key LIMIT 1\n'
            sql %= self.sql_vars
            self.cursor.execute(sql, (self._cur_time, ns))
            deets = self.cursor.fetchone()
            if deets:
                break
        else:
            sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE to_pop <= ?\nORDER BY ns, delete_sort_key LIMIT 1\n'
            sql %= self.sql_vars
            self.cursor.execute(sql, (self._cur_time,))
            deets = self.cursor.fetchone()

        if not deets:
            return ()
        deets, = deets
        with row_factory(self.cursor, just_the_first):
            sql = '\nSELECT details FROM %(FILE_SET_TABLE_NAME)s WHERE to_pop <= ? AND ns = ?\n%(EXTRA_CONDITION)s\nORDER BY to_pop, ns, delete_sort_key ASC\nLIMIT ?\n'
            vars_ = dict(self.sql_vars)
            vars_.update(dict(EXTRA_CONDITION='AND delete_sort_key < 0' if deets.size < 0 and partition else ''))
            sql %= vars_
            self.cursor.execute(sql, (self._cur_time, deets.server_path.ns, -1 if lim is None else lim))
            return self.cursor.fetchall()


@locked_queue_map

@server_path_timed_queue_map

class UpdatedFileSetWithFailure(SQLiteFileSetWithFailure):
    EXTRA_COLUMN_DEFS = [('ns', 'INTEGER NOT NULL', row_extract_ns), ('delete_sort_key', 'INTEGER NOT NULL', row_extract_delete_sort_key), (UPDATED_FILE_SET_GUID_COL, 'BYTETEXT', row_extract_guid)]
    EXTRA_INDEX_DEFS = [('active_i', ['to_pop', 'ns', 'delete_sort_key']), ('by_guid', ['guid'])]
    LOGIC_CLASS = UpdatedFileSetLogic

    def __init__(self, *n, **kw):
        SQLiteFileSetWithFailure.__init__(self, 'UPDATED', *n, **kw)
