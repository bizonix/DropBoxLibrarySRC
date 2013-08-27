#Embedded file name: dropbox/sqlite3_helpers.py
from __future__ import absolute_import
import errno
import itertools
import os
import threading
import sqlite3
import sys
import time
import cPickle as pickle
from contextlib import contextmanager
from functools import wraps
from weakref import WeakKeyDictionary
from dropbox.fatal_db_exception import do_fatal_db_error_restart
from dropbox.functions import random_string
from dropbox.fsutil import is_file_not_found_exception
from dropbox.trace import TRACE, assert_, trace_stack, unhandled_exc_handler

class CorruptedDBError(Exception):
    pass


class FatalDBError(Exception):
    pass


POSSIBLE_CORRUPTED_DB = (CorruptedDBError,
 sqlite3.DatabaseError,
 sqlite3.IntegrityError,
 sqlite3.OperationalError)
DISK_IO_ERROR_THRESHOLD = 5
MAIN_DB_NAME = 'main'

def get_sqlite_exc_message(exc_info):
    exc_type, exc_val, exc_tb = exc_info
    if exc_type in (sqlite3.DatabaseError, sqlite3.OperationalError, sqlite3.IntegrityError):
        if isinstance(exc_val, str):
            return exc_val
        try:
            return exc_val.message
        except Exception:
            TRACE('Strange exc value: %r' % exc_val)
            unhandled_exc_handler()
            return None

    else:
        return None


def enable_converters(converters, adapters = ()):
    for name, fn in converters:
        if name in sqlite3.converters:
            assert_(lambda : sqlite3.converters[name] == fn, 'Someone is conflicting with converting: %r, %s vs %r', name, sqlite3.converters[name], fn)
        sqlite3.register_converter(name, fn)

    for type_, fn in adapters:
        k = (type_, sqlite3.PrepareProtocol)
        if k in sqlite3.adapters:
            assert_(lambda : sqlite3.adapters[k] == fn, 'Someone is conflicted with adapting: %r %r', type_, fn)
        sqlite3.register_adapter(type_, fn)


_tracing_sql = False

def set_tracing_sql(tracing):
    global _tracing_sql
    _tracing_sql = tracing


class Cursor(sqlite3.Cursor):

    def execute(self, sql, *n, **kw):
        if _tracing_sql:
            TRACE('SQL: %s', sql)
        return super(Cursor, self).execute(sql, *n, **kw)

    def executemany(self, sql, *n, **kw):
        if _tracing_sql:
            TRACE('SQL: %s', sql)
        return super(Cursor, self).executemany(sql, *n, **kw)


class Connection(sqlite3.Connection):

    def cursor(self, cursorClass = None):
        if cursorClass is None:
            cursorClass = Cursor
        return super(Connection, self).cursor(cursorClass)

    def commit(self, *n, **kw):
        if _tracing_sql:
            TRACE('SQL: COMMIT')
        return super(Connection, self).commit(*n, **kw)

    def rollback(self, *n, **kw):
        if _tracing_sql:
            TRACE('SQL: ROLLBACK')
        return super(Connection, self).rollback(*n, **kw)


def connect(*n, **kw):
    kw.setdefault('factory', Connection)
    return sqlite3.connect(*n, **kw)


def _for_testing(*n, **kw):
    pass


class SqliteConnectionHub(object):

    def __init__(self, *n, **kw):
        self.local = threading.local()
        self.n = n
        self.closed = False
        self._all_conns = WeakKeyDictionary()
        self.post_create = kw.pop('post_create', None)
        if kw.get('keystore', None) is not None and kw.get('trevor', None) is not None:
            raise ValueError("Can't set both keystore and trevor")
        if kw.get('keystore', None) is not None and not kw['keystore'].get_database_key():
            raise ValueError('Not a quackable keystore object')
        self.kw = kw
        if is_memory_database_uri(self.n[0]):
            TRACE('Creating in memory keepalive connection')
            self.in_memory_keepalive_conn = self.conn()

    def close(self):
        if not self.closed:
            self._close_all()
            self.closed = True

    def __del__(self):
        try:
            self.close()
        except Exception:
            unhandled_exc_handler()

    def _close_all(self, except_self = False):
        _c = self.conn() if except_self else None

        def call_close(c):
            c.close()

        self._do_all(call_close, except_self=except_self)
        self._all_conns.clear()
        self.local = threading.local()
        if _c is not None:
            self.local.conn = _c
            self._all_conns[_c] = id(_c)

    def _do_all(self, meth, except_self = False):
        _c = self.conn() if except_self else None
        try:
            for c in self._all_conns.keys():
                if c is _c:
                    continue
                try:
                    meth(c)
                except Exception:
                    unhandled_exc_handler()

        except Exception:
            unhandled_exc_handler()

    def _create_conn(self):
        kw = self.kw
        ks = kw.get('keystore')
        if ks is not None:
            kw = dict(kw)
            kw['trevor'] = ks.get_database_key()
        kw.pop('keystore', None)
        conn = connect(check_same_thread=False, *self.n, **kw)
        if self.post_create:
            self.post_create(conn)
        return conn

    def conn(self, refresh = False):
        if self.closed:
            raise Exception('Already closed!')
        try:
            conn = self.local.conn
        except AttributeError:
            pass
        else:
            if refresh:
                conn.close()
                del self.local.conn
            else:
                return conn

        self.local.conn = self._create_conn()
        self._all_conns[self.local.conn] = id(self.local.conn)
        return self.local.conn

    @contextmanager
    def cursor(self):
        with self.conn() as conn:
            yield conn.cursor()

    @contextmanager
    def attach_to(self, curs, name = None):
        if self.n[0] == ':memory:':
            raise Exception("You can't attach to an in-memory database!")
        try:
            ks = self.kw['keystore']
        except KeyError:
            trev = self.kw.get('trevor')
        else:
            trev = ks.get_database_key()

        def _attach(path, name, trev):
            if not is_memory_database_uri(path):
                try:
                    st = os.stat(path)
                except Exception as e:
                    if is_file_not_found_exception(e):
                        do_fatal_db_error_restart("CAN'T ATTACH TO MISSING DATABASE: %r" % (path,))
                    unhandled_exc_handler()
                else:
                    if not st.st_size:
                        do_fatal_db_error_restart("EMPTY SQL FILE CAN'T ATTACH!")
            _for_testing()
            curs.execute("ATTACH DATABASE ? as ? KEY X'%s'" % (trev.encode('hex') if trev is not None else '',), (path, name))

        if name is None:
            for i in xrange(5):
                name = 'a' + random_string(8).encode('hex')
                try:
                    _attach(self.n[0], name, trev)
                except sqlite3.OperationalError:
                    check_database_path_exists(self.n[0])
                    unhandled_exc_handler(i == 0)
                    trace_stack()
                    time.sleep(1)
                    continue
                except Exception:
                    unhandled_exc_handler(i == 0)
                    trace_stack()
                    time.sleep(1)
                    continue
                else:
                    break

            else:
                raise Exception("Couldn't pick a database name!")

        else:
            try:
                _attach(self.n[0], name, trev)
            except sqlite3.OperationalError:
                check_database_path_exists(self.n[0])
                raise

        try:
            yield name
        finally:
            try:
                curs.execute('DETACH DATABASE %s' % (name,))
            except Exception:
                unhandled_exc_handler()
                trace_stack()


def sqlite3_get_table_entries(cursor, table, checked_column, column_iterable, select_limit = 200, desired_columns = None, row_factory = sqlite3.Row, extra_conditions = None):
    if desired_columns is not None:
        if isinstance(desired_columns, basestring):
            desired_columns_literal = desired_columns
        else:
            desired_columns_literal = ', '.join(desired_columns)
    else:
        desired_columns_literal = '*'
    if extra_conditions is None:
        extra_conditions = ''
    else:
        extra_conditions = 'AND (%s)' % (extra_conditions,)
    over = select_limit * [None]
    stop = False
    with _row_factory(cursor, row_factory):
        the_iter = iter(column_iterable)
        while not stop:
            try:
                for i in xrange(select_limit):
                    over[i] = the_iter.next()

            except StopIteration:
                if i == 0:
                    break
                del over[i:]
                stop = True

            sql = 'SELECT %s FROM %s WHERE %s IN (%s) %s' % (desired_columns_literal,
             table,
             checked_column,
             ', '.join([ '?' for x in xrange(min(select_limit, len(over))) ]),
             extra_conditions)
            cursor.execute(sql, over)
            for row in cursor:
                yield row


def check_database_path_exists(path):
    try:
        st = os.stat(path)
    except OSError as e:
        if is_file_not_found_exception(e):
            TRACE('!! file no longer exists')
            do_fatal_db_error_restart('Database we are attaching to no longer exists')
    else:
        TRACE('Database exists: %r %r', path, st)


@contextmanager
def row_factory(cursor, row_factory):
    old_row_factory = cursor.row_factory
    cursor.row_factory = row_factory
    try:
        yield cursor
    finally:
        cursor.row_factory = old_row_factory


def using_row_factory(row_factory_):

    def take_new_fn(fn):

        def row_factory_wrapper(cursor, *n, **kw):
            with row_factory(cursor, row_factory_):
                return fn(cursor, *n, **kw)

        return row_factory_wrapper

    return take_new_fn


_row_factory = row_factory

def sqlite3_get_memory_statistics():
    try:
        return sqlite3.get_memory_statistics()
    except AttributeError:
        pass
    except Exception:
        unhandled_exc_handler()

    return (0, 0)


def to_db_type(value):
    if value is None or isinstance(value, (int,
     long,
     float,
     unicode)):
        return value
    else:
        return buffer(pickle.dumps(value))


def from_db_type(value):
    if isinstance(value, buffer):
        return pickle.loads(str(value))
    else:
        return value


def is_corrupted_db_exception(exc_type, exc_val, exc_tb, tables = None, **kw):
    if exc_type not in POSSIBLE_CORRUPTED_DB:
        return False
    elif exc_type is CorruptedDBError:
        return True
    tables = tables or []
    message = get_sqlite_exc_message((exc_type, exc_val, exc_tb))
    if exc_type == sqlite3.DatabaseError:
        return message in ('database disk image is malformed', 'file is encrypted or is not a database')
    elif exc_type == sqlite3.OperationalError:
        return message in ('auxiliary database format error', 'SQL logic error or missing database') + tuple(('no such table: %s' % table for table in tables))
    elif exc_type == sqlite3.IntegrityError:
        return message in ('datatype mismatch', 'constraint failed') or 'not unique' in message
    else:
        return False


class Sqlite3Cache(object):

    def __init__(self, filename = None, **kw):
        self.lock = threading.Lock()
        self.filename = filename
        self.connhub = None
        self.kw = kw
        self.disk_err_count = 0

    def rebuild(self):
        if self.connhub:
            self.connhub.conn().close()
        del self.connhub
        try:
            os.unlink(self.filename)
        except Exception as e:
            if not (isinstance(e, OSError) and e.errno == errno.ENOENT):
                unhandled_exc_handler()

        self._load_db()
        self.disk_err_count = 0

    def close(self):
        if self.connhub:
            self.connhub.close()


class VersionedSqlite3Cache(Sqlite3Cache):

    def __init__(self, filename = None, **kw):
        super(VersionedSqlite3Cache, self).__init__(filename, **kw)
        try:
            self._load_db()
        except Exception:
            trace_stack()
            unhandled_exc_handler(False)
            self.rebuild()

    def _load_db(self):
        assert self._USER_VERSION > 0, '_USER_VERSION must be greater than 0'
        self.connhub = SqliteConnectionHub((self.filename or ':memory:'), detect_types=sqlite3.PARSE_DECLTYPES, **self.kw)
        with self.connhub.cursor() as cursor:
            version = cursor.execute('PRAGMA user_version').fetchone()[0]
            TRACE('%s(version=%r)', self.__class__.__name__, version)
            while version != self._USER_VERSION:
                self.migrations[version](cursor)
                new_version = cursor.execute('PRAGMA user_version').fetchone()[0]
                TRACE('migrated to %s(version=%r)', self.__class__.__name__, new_version)
                if new_version == version:
                    raise Exception("Migration didn't progress anywhere")
                version = new_version

        self._load_data()

    def _load_data(self):
        pass


def locked_and_handled(retry = True, retval = None, track_disk_err = False):

    def _middleman(func):

        @wraps(func)
        def _runner(self, *args, **kwargs):
            with self.lock:
                try:
                    return func(self, *args, **kwargs)
                except POSSIBLE_CORRUPTED_DB:
                    exc_info = sys.exc_info()
                    try:
                        if track_disk_err and exc_info[0] == sqlite3.OperationalError and get_sqlite_exc_message(exc_info) == 'disk I/O error':
                            self.disk_err_count += 1
                        if self.filename and is_corrupted_db_exception(exc_info[0], exc_info[1], exc_info[2], tables=self.tables) or track_disk_err and self.disk_err_count > DISK_IO_ERROR_THRESHOLD:
                            TRACE('Database %s has become corrupted.  Rebuilding it' % self.filename)
                            unhandled_exc_handler(False, exc_info)
                            self.rebuild()
                        else:
                            raise exc_info[0], exc_info[1], exc_info[2]
                    finally:
                        del exc_info

                    if retry:
                        try:
                            return func(self, *args, **kwargs)
                        except POSSIBLE_CORRUPTED_DB:
                            exc_info = sys.exc_info()
                            try:
                                new_exc = Exception('Corrupted Database %s %s' % (self.filename, exc_info[1] or exc_info[0]))
                                raise new_exc.__class__, new_exc, exc_info[2]
                            finally:
                                del exc_info

                    else:
                        return retval

        return _runner

    return _middleman


def just_the_first(cursor, ent):
    return ent[0]


def archive_database(cursor, dest_name, src_name):
    read_cursor = cursor.connection.cursor()
    read_cursor.execute("SELECT name FROM %s.sqlite_master WHERE type='table'" % (src_name,))
    for table_name, in read_cursor:
        TRACE('Archiving %s.%s into %s', src_name, table_name, dest_name)
        cursor.execute('DELETE FROM %s.%s' % (dest_name, table_name))
        cursor.execute('INSERT INTO %s.%s SELECT * FROM %s.%s' % (dest_name,
         table_name,
         src_name,
         table_name))


def create_tables(cursor, table_defs, force = False):
    force_str = '' if force else 'IF NOT EXISTS'
    for table_name, table_columns, table_constraints, indexes in table_defs:
        tcolstr = ','.join(itertools.chain(('%s %s' % tuple(v[:2]) for v in table_columns), table_constraints))
        cursor.execute('CREATE TABLE %s %s (%s)' % (force_str, table_name, tcolstr))
        for index_name, index_columns in indexes:
            cursor.execute('CREATE INDEX %s %s ON %s (%s)' % (force_str,
             index_name,
             table_name,
             ','.join(index_columns)))


def unique_in_memory_database_uri():
    while True:
        database_file = 'file:%s?mode=memory&cache=shared' % (random_string(32).replace('/', ''),)
        con = sqlite3.connect(database_file)
        try:
            if not con.execute("select * from sqlite_master WHERE type='table'").fetchone():
                return database_file
        finally:
            con.close()


def is_memory_database_uri(uri):
    return uri == ':memory:' or uri.startswith('file:') and 'mode=memory' in uri


def sqlite_escape(st):
    return st.replace(u'\\', u'\\\\').replace(u'%', u'\\%').replace(u'_', u'\\_')


class dict_like_row(sqlite3.Row):
    __slots__ = []

    def get(self, k, default = None):
        try:
            return self[k]
        except (KeyError, IndexError):
            return default

    def __getattr__(self, k, default = None):
        return self.get(k, default)

    def __repr__(self):
        return '<dict_like_row %r>' % (dict(self),)
