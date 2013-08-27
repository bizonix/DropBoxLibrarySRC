#Embedded file name: dropbox/client/config.py
import base64
import UserDict
import contextlib
import threading
import cPickle as pickle
from dropbox.trace import unhandled_exc_handler, TRACE, report_bad_assumption
from dropbox.sqlite3_helpers import Cursor, SqliteConnectionHub, from_db_type, to_db_type
from dropbox.functions import migrate_db_get_table_entries

def post_create(conn):
    conn.text_factory = unicode


class DBConfig(Cursor, UserDict.DictMixin):
    INSERT_STATEMENT = 'INSERT OR REPLACE INTO config VALUES (?, ?)'

    def create_tables(self, force = False):
        self.execute('CREATE TABLE %sconfig (key TEXT PRIMARY KEY NOT NULL, value BLOB)' % ('' if force else 'IF NOT EXISTS '))

    def __getitem__(self, key):
        assert isinstance(key, basestring)
        row = self.execute('SELECT value FROM config WHERE key=?', (key,)).fetchone()
        if row:
            try:
                return from_db_type(row[0])
            except Exception:
                unhandled_exc_handler()
                raise KeyError(key)

        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        assert isinstance(key, basestring)
        self.execute(self.INSERT_STATEMENT, (key, to_db_type(value)))

    def __delitem__(self, key):
        assert isinstance(key, basestring)
        self.execute('DELETE FROM config WHERE key=?', (key,))
        if not self.rowcount:
            raise KeyError(key)

    def __len__(self):
        return self.execute('SELECT count(*) FROM config').fetchone()[0]

    def __contains__(self, key):
        if not isinstance(key, basestring):
            return False
        row = self.execute('SELECT 1 FROM config WHERE key=?', (key,)).fetchone()
        return bool(row and row[0])

    def iterkeys(self):
        return iter((row[0] for row in self.connection.cursor(DBConfig).execute('SELECT key FROM config').cursor_iter()))

    def itervalues(self):
        for row in self.connection.cursor(DBConfig).execute('SELECT value FROM config').cursor_iter():
            try:
                toret = from_db_type(row[0])
            except Exception:
                unhandled_exc_handler()
            else:
                yield toret

    def iteritems(self):
        for row in self.connection.cursor(DBConfig).execute('SELECT key, value FROM config').cursor_iter():
            try:
                toret = from_db_type(row[1])
            except Exception:
                unhandled_exc_handler()
            else:
                yield (row[0], toret)

    __iter__ = iterkeys

    def cursor_iter(self):
        try:
            while True:
                yield self.next()

        except StopIteration:
            pass

    def keys(self):
        return list(self.iterkeys())

    def values(self):
        return list(self.itervalues())

    def update(self, other):
        try:
            iitems = other.iteritems()
        except:
            try:
                iitems = ((k, other[k]) for k in other.keys())
            except:
                iitems = other

        self.executemany(self.INSERT_STATEMENT, ((key, to_db_type(value)) for key, value in iitems))

    def clear(self):
        self.execute('DELETE FROM config')


class ConfigDict(object, UserDict.DictMixin):

    def __init__(self, filename = None, **kw):
        self.lock = threading.RLock()
        self.lock_count = 0
        self.connhub = SqliteConnectionHub((filename or ':memory:'), post_create=post_create, isolation_level=None, **kw)
        try:
            self.__cursor().create_tables()
        except Exception:
            self.close()
            raise

    def __del__(self):
        try:
            self.close()
        except:
            unhandled_exc_handler()

    def close(self):
        self.connhub.close()

    def __cursor(self):
        return self.connhub.conn().cursor(DBConfig)

    def __enter__(self):
        self.lock.acquire()
        if not self.lock_count:
            self.__cursor_in_use = self.__cursor()
            self.__cursor_in_use.execute('BEGIN TRANSACTION')
        self.lock_count += 1
        return self.__cursor_in_use

    def __exit__(self, *exc_info):
        self.lock_count -= 1
        if not self.lock_count:
            try:
                if exc_info[0]:
                    self.connhub.conn().rollback()
                else:
                    self.connhub.conn().commit()
            except Exception:
                unhandled_exc_handler()

            try:
                self.__cursor_in_use.close()
            except Exception:
                unhandled_exc_handler()

            self.__cursor_in_use = None
        self.lock.release()

    def __getitem__(self, key):
        with self as db_config:
            return db_config[key]

    def __setitem__(self, key, value):
        with self as db_config:
            db_config[key] = value

    def update(self, other):
        with self as db_config:
            db_config.update(other)

    def __delitem__(self, key):
        with self as db_config:
            try:
                del db_config[key]
            except KeyError:
                pass

    def __len__(self):
        with self as db_config:
            return len(db_config)

    def iterkeys(self):
        with contextlib.closing(self.__cursor()) as c:
            for i in c.iterkeys():
                yield i

    def iteritems(self):
        with contextlib.closing(self.__cursor()) as c:
            for i in c.iteritems():
                yield i

    def itervalues(self):
        with contextlib.closing(self.__cursor()) as c:
            for i in c.itervalues():
                yield i

    __iter__ = iterkeys

    def keys(self):
        with self as db_config:
            return db_config.keys()

    def values(self):
        with self as db_config:
            return db_config.values()

    def items(self):
        with self as db_config:
            return db_config.items()

    def __contains__(self, key):
        with self as db_config:
            return key in db_config

    def clear(self):
        with self as db_config:
            db_config.clear()

    def copy(self, path, **kw):
        toret = type(self)(path, **kw)
        with self as old_db_config:
            toret.update(old_db_config)
        return toret

    def __import(self, old_config_iter):

        def new_config_data():
            for obj in old_config_iter:
                key = obj['key']
                if key in ('last_revision', 'recently_changed', 'recently_changed2', 'schema_version'):
                    continue
                yield (key, obj['value'])

            yield ('check_user_xattr', True)

        with self as db_config:
            db_config.clear()
            db_config.update(new_config_data())
            return db_config.rowcount

    def import_from_dropbox_db(self, old_conn):

        def yield_to_import():
            for key, val in old_conn.execute('select key, value from config'):
                if val is None:
                    if key in ('proxy_server', 'proxy_username', 'proxy_password'):
                        val = ''
                    else:
                        report_bad_assumption('Warning, None value in config DB: %r' % (key,))
                        continue
                else:
                    try:
                        val = pickle.loads(base64.b64decode(val))
                    except:
                        try:
                            TRACE("Couldn't import key, val: (%r, %r)" % (key, val))
                        except:
                            pass

                        unhandled_exc_handler()
                        continue

                yield {'key': key,
                 'value': val}

        return self.__import(yield_to_import())

    def import_from_migrate_db(self, fo):
        return self.__import(migrate_db_get_table_entries(fo, 'Config'))
