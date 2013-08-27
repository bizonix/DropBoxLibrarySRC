#Embedded file name: dropbox/client/sigstore.py
import threading
import os
import base64
from dropbox.sqlite3_helpers import SqliteConnectionHub, Sqlite3Cache, locked_and_handled
from dropbox.functions import batch, migrate_db_get_table_entries
from dropbox.trace import unhandled_exc_handler

class HashInfoContainer(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('hash', 'sig', 'size')

    def __init__(self, *args, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return ''.join(['HashInfoContainer(', ','.join([ '%s=%r' % (k, getattr(self, k)) for k in self.__slots__ if hasattr(self, k) ]), ')'])


def post_create(conn):
    conn.text_factory = str


class SigStore(Sqlite3Cache):

    def __init__(self, filename = None, max_size_mb = None, **kw):
        Sqlite3Cache.__init__(self, filename, **kw)
        self.tables = ['sigstore']
        self.max_size = max_size_mb * 1024 * 1024 if max_size_mb else None
        self.disk_err_count = 0
        try:
            self._load_db()
        except Exception:
            self.rebuild()

    def _load_db(self):
        self.connhub = SqliteConnectionHub((self.filename or ':memory:'), post_create=post_create, **self.kw)
        conn = self.connhub.conn()
        cursor = conn.cursor()
        self.pagesize = cursor.execute('PRAGMA page_size').fetchone()[0]
        cursor.execute('CREATE TABLE IF NOT EXISTS sigstore (hash TEXT PRIMARY KEY NOT NULL, sig BLOB NOT NULL, size INTEGER NOT NULL, held INTEGER)')

    @locked_and_handled(retry=False, retval=None, track_disk_err=True)
    def clear(self):
        with self.connhub.conn() as conn:
            conn.execute('DELETE FROM sigstore')

    @locked_and_handled(track_disk_err=True)
    def get(self, hash):
        row = self.connhub.conn().execute('SELECT sig FROM sigstore WHERE hash=?', [hash]).fetchone()
        if row:
            return str(row[0])
        raise KeyError(hash)

    @locked_and_handled(retry=False, retval=False, track_disk_err=True)
    def __contains__(self, _hash):
        return bool(self.connhub.conn().execute('SELECT count(*) FROM sigstore WHERE hash=?', [_hash]).fetchone()[0])

    @locked_and_handled(track_disk_err=True)
    def set(self, _hash, sig, size):
        self._call_with_cursor(self._set_internal, ((_hash, sig, size),))

    @locked_and_handled(track_disk_err=True)
    def set_batch(self, sig_iterable):
        return self._call_with_cursor(self._set_internal, sig_iterable)

    @locked_and_handled(track_disk_err=True)
    def set_if_new(self, _hash, sig, size):
        return self._call_with_cursor(self._set_if_new_internal, _hash, sig, size)

    @locked_and_handled(retry=False, retval=0, track_disk_err=True)
    def delete(self, hash_iterable, formatted = False):
        return self._call_with_cursor(self._delete_internal, hash_iterable, formatted)

    @locked_and_handled(track_disk_err=True)
    def get_all(self, handler):
        with self.connhub.conn() as conn:
            c = conn.execute('SELECT hash, sig, size FROM sigstore')
            try:
                return handler(c)
            finally:
                c.close()

    @locked_and_handled(retry=False, track_disk_err=True)
    def hold(self, hash_list, formatted = False):
        if self.max_size:
            with self.connhub.conn() as conn:
                conn.cursor().executemany('UPDATE sigstore SET held = 1 WHERE hash = ?', hash_list if formatted else ((hash,) for hash in hash_list))

    def _call_with_cursor(self, f, *args):
        with self.connhub.conn() as conn:
            return f(conn.cursor(), *args)

    def _set_internal(self, cursor, sig_iterable):
        iterable_len = [0]

        def feed_into_sigtore():
            for _hash, sig, size in sig_iterable:
                iterable_len[0] += 1
                if sig:
                    yield (_hash, buffer(sig), size)

        cursor.executemany('INSERT OR REPLACE INTO sigstore (hash, sig, size) VALUES (?, ?, ?)', feed_into_sigtore())
        if self.max_size:
            if self.filename:
                size = os.stat(self.filename).st_size
            else:
                size = cursor.execute('PRAGMA page_count').fetchone()[0] * self.pagesize
            if size > self.max_size:
                cursor.execute('DELETE FROM sigstore WHERE hash in (SELECT hash FROM sigstore WHERE held IS NULL LIMIT %d)' % (iterable_len[0] * 5))
                cursor.execute('VACUUM')
        return iterable_len[0]

    def _set_if_new_internal(self, cursor, _hash, sig, size):
        row = cursor.execute('SELECT * FROM sigstore WHERE hash=?', [_hash]).fetchone()
        if not row:
            self._set_internal(cursor, ((_hash, sig, size),))
            return None
        else:
            return HashInfoContainer(hash=str(row[0]), sig=str(row[1]), size=long(row[2]))

    def _delete_internal(self, cursor, hash_iterable, formatted):
        cursor.executemany('DELETE FROM sigstore WHERE hash = ? ', hash_iterable if formatted else ((hash,) for hash in hash_iterable))
        return max(0, cursor.rowcount)

    def _import(self, block_cache_iterable, ref_checker = None):
        sigs_imported = 0
        sigs_pruned = 0
        with self.lock:
            with self.connhub.conn() as conn:
                cursor = conn.cursor()
                if ref_checker:
                    check_live_hashes = None

                    def feed_into_sigstore(ents):
                        for ent in ents:
                            check_live_hashes.append(ent[0])
                            yield ent

                    for ents in batch(block_cache_iterable, 200):
                        check_live_hashes = []
                        try:
                            sigs_imported += self._set_internal(cursor, feed_into_sigstore(ents))
                        except Exception:
                            unhandled_exc_handler()

                        try:
                            hwr = frozenset(ref_checker(check_live_hashes))
                            sigs_pruned += self._delete_internal(cursor, ((_hash,) for _hash in check_live_hashes if _hash not in hwr), True)
                        except Exception:
                            unhandled_exc_handler()

                else:
                    for ents in batch(block_cache_iterable, 200):
                        try:
                            sigs_imported += self._set_internal(cursor, ents)
                        except Exception:
                            unhandled_exc_handler()

        return (sigs_imported, sigs_pruned)

    def import_from_dropbox_db(self, old_conn, ref_checker = None):

        def feed_into_import():
            old_factory = old_conn.text_factory
            old_conn.text_factory = str
            try:
                for ent in old_conn.execute('SELECT hash, sig, size FROM block_cache'):
                    try:
                        yield (str(ent[0]), str(base64.decodestring(ent[1])), long(ent[2]))
                    except Exception:
                        unhandled_exc_handler()

            finally:
                old_conn.text_factory = old_factory

        return self._import(feed_into_import(), ref_checker=ref_checker)

    def import_from_migrate_db(self, fo, ref_checker = None):

        def feed_into_import():
            for ent in migrate_db_get_table_entries(fo, 'BlockCache'):
                try:
                    yield (str(ent['hash']), str(ent['sig']), long(ent['size']))
                except Exception:
                    unhandled_exc_handler()

        return self._import(feed_into_import(), ref_checker=ref_checker)
