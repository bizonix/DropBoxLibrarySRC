#Embedded file name: dropbox/client/deleted_file_cache.py
import base64
import datetime
import errno
import re
import time
from Crypto.Random import get_random_bytes
import arch
from client_api.hashing import DROPBOX_HASH_LENGTH
from dropbox.client.background_worker import on_background_thread
from dropbox.sqlite3_helpers import VersionedSqlite3Cache, locked_and_handled
from dropbox.functions import split_extension
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.path import server_path_basename
import dropbox.fsutil as fsutil
from dropbox.fastwalk import fastwalk_with_exception_handling
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError, PermissionDeniedError

class DuplicateEntryError(Exception):
    pass


class DeletedFileCache(VersionedSqlite3Cache):
    MAX_DAYS = 3
    MTIME_MULT = 1000000000
    _USER_VERSION = 3

    def __init__(self, filename, cache_path, arch, **kw):
        self.tables = ['blocks', 'files']
        self.cache_path = cache_path
        self.last_prune = None
        self.migrations = [self.migrate_0_to_3, self.migrate_1_to_2, self.migrate_2_to_3]
        self.arch = arch
        self.fs = arch.file_system
        super(DeletedFileCache, self).__init__(unicode(filename), **kw)

    def migrate_0_to_3(self, cursor):
        TRACE('DeletedFileCache: Migrate 0->3')
        cursor.execute('CREATE TABLE blocks (hash BYTETEXT NOT NULL, file_id INT NOT NULL, i INT NOT NULL)')
        cursor.execute('CREATE TABLE files (file_id INTEGER PRIMARY KEY NOT NULL, cache_path TEXT UNIQUE NOT NULL, origin_path TEXT NOT NULL, date_added TEXT NOT NULL, origin_ns INT, size INT NOT NULL, mtime INT NOT NULL)')
        cursor.execute('CREATE TRIGGER block_cleanup DELETE ON files BEGIN DELETE FROM blocks WHERE file_id = old.file_id; END')
        cursor.execute('CREATE INDEX bh ON blocks (hash)')
        cursor.execute('CREATE INDEX cpath ON files (cache_path)')
        cursor.execute('CREATE INDEX blocks_file_id on blocks (file_id)')
        cursor.execute('PRAGMA user_version = 3')
        for day in self.valid_days():
            try:
                self._migrate_from_dir(cursor, day)
            except Exception:
                unhandled_exc_handler()

    def migrate_1_to_2(self, cursor):
        TRACE('DeletedFileCache: Migrate 1->2')
        cursor.execute('DELETE FROM blocks WHERE file_id IN (SELECT blocks.file_id FROM blocks LEFT OUTER JOIN files ON blocks.file_id = files.file_id WHERE files.cache_path is NULL)')
        cursor.execute('PRAGMA user_version = 2')

    def migrate_2_to_3(self, cursor):
        TRACE('DeletedFileCache: Migrate 2->3')
        cursor.execute('PRAGMA user_version = 3')
        on_background_thread(self._migrate_add_block_file_id_index)()

    @locked_and_handled()
    def _migrate_add_block_file_id_index(self):
        TRACE('DeletedFileCache: adding index on blocks.file_id')
        with self.connhub.cursor() as cursor:
            cursor.execute('CREATE INDEX blocks_file_id on blocks (file_id)')

    def _check_too_big(self):
        free_space = arch.util.get_disk_free_space(unicode(self.cache_path))
        with self.connhub.cursor() as cursor:
            cursor.execute('SELECT SUM(size) FROM files')
            cache_size = cursor.fetchone()[0] or 0
            max_size = (cache_size + free_space) * 0.1
            max_size = max(max_size, 10485760)
            max_size = min(max_size, 10737418240L)
            TRACE('Deleted file cache: size %d MB, limit %d MB', cache_size / 1048576, max_size / 1048576)
            if cache_size < max_size:
                return
            cursor.execute('SELECT file_id, cache_path, size FROM files ORDER BY date_added, -size')
            removed_file_ids = []
            for file_id, cache_path, size in cursor:
                cache_size -= size
                fsutil.safe_remove(self.fs, cache_path)
                removed_file_ids.append((file_id,))
                if cache_size < max_size:
                    break

            cursor.executemany('DELETE FROM files WHERE file_id = ?', removed_file_ids)
            TRACE('Removed %d files from deleted file cache', len(removed_file_ids))

    @classmethod
    def valid_days(cls):
        return [ unicode((datetime.date.today() - datetime.timedelta(x)).strftime('%Y-%m-%d')) for x in xrange(cls.MAX_DAYS) ]

    def _insert_entry(self, cursor, local_filename, old_filename, date_added, ns, size, mtime, blocklist):
        cursor.execute('SELECT cache_path FROM files WHERE cache_path = ? ', (unicode(local_filename),))
        row = cursor.fetchone()
        if row:
            raise DuplicateEntryError(local_filename)
        cursor.execute('INSERT INTO files(cache_path, origin_path, date_added, origin_ns, size, mtime)VALUES (?, ?, ?, ?, ?, ?)', (unicode(local_filename),
         unicode(old_filename),
         date_added,
         ns,
         size,
         int(mtime * self.MTIME_MULT)))
        file_id = cursor.lastrowid
        if blocklist:
            for i, h in enumerate(blocklist.split(',')):
                assert len(h) == DROPBOX_HASH_LENGTH
                cursor.execute('INSERT INTO blocks (hash, file_id, i) VALUES (?, ?, ?)', (h, file_id, i))

    def _migrate_from_dir(self, cursor, day):
        entries_fn = self.cache_path.join(day).join(u'entries.log')
        origins_fn = self.cache_path.join(day).join(u'origins.log')
        if not fsutil.is_exists(self.fs, entries_fn):
            return
        with self.fs.open(entries_fn, 'r') as f:
            j = 0
            for line in f:
                try:
                    fn, server_path, mtime, size, blocklist = line.strip().split('|')
                    fn = base64.decodestring(fn).decode('utf8')
                    server_path = base64.decodestring(server_path).decode('utf8')
                    fn = unicode(self.cache_path.join(day, fn))
                    mtime = float(mtime)
                    size = int(size)
                    self._insert_entry(cursor, local_filename=fn, old_filename='*migrated*', date_added=day, ns=None, size=size, mtime=mtime, blocklist=blocklist)
                    j += 1
                except DuplicateEntryError as e:
                    TRACE('Duplicate Entry: %r', e.message)
                except Exception:
                    unhandled_exc_handler()

            TRACE('DELETED: Migrated %s entries from %r' % (j, day))
        fsutil.safe_remove(self.fs, entries_fn)
        fsutil.safe_remove(self.fs, origins_fn)

    def _get_base_path(self):
        base_path = self.cache_path.join(datetime.date.today().strftime('%Y-%m-%d'))
        if not fsutil.is_exists(self.fs, base_path):
            fsutil.makedirs(self.fs, base_path)
        return base_path

    def get_filename(self, server_path, mtime, size, blocklist):
        fn, ext = split_extension(server_path_basename(server_path))
        uniq_id = get_random_bytes(16).encode('hex')
        return self._get_base_path().join_nfc_components(u'%s (deleted %s)%s' % (fn[:64], uniq_id, ext))

    def add_data(self, h, data):
        fn = self._get_base_path().join(unicode(h))
        try:
            with self.fs.open(fn, 'r') as f:
                if f.read() == data:
                    return
        except EnvironmentError as e:
            if e.errno != errno.ENOENT:
                unhandled_exc_handler()

        with self.fs.open(fn, 'w') as f:
            f.write(data)
        self.add_entry(fn, fn, None, len(data), h)

    @locked_and_handled()
    def add_entry(self, local_filename, old_filename, server_path, size, blocklist):
        try:
            mtime = self.fs.indexing_attributes(local_filename).mtime
        except EnvironmentError:
            mtime = 0
            unhandled_exc_handler()
        except Exception:
            mtime = 0
            unhandled_exc_handler()

        path, fn = local_filename.dirname, local_filename.basename
        with self.connhub.cursor() as cursor:
            try:
                self._insert_entry(cursor, local_filename, old_filename, datetime.date.today().strftime('%Y-%m-%d'), server_path and server_path.ns, size, mtime, blocklist)
            except DuplicateEntryError:
                unhandled_exc_handler()

    @locked_and_handled()
    def delete_entry(self, local_path):
        with self.connhub.cursor() as cursor:
            cursor.execute('DELETE FROM files WHERE cache_path = ?', (unicode(local_path),))
        try:
            self.fs.remove(local_path)
        except FileNotFoundError:
            pass
        except Exception:
            unhandled_exc_handler()

    @locked_and_handled()
    def who_has(self, h):
        with self.connhub.cursor() as cursor:
            cursor.execute('SELECT files.cache_path, blocks.i FROM blocks LEFT OUTER JOIN files ON blocks.file_id = files.file_id WHERE blocks.hash = ?', (h,))
            return [ (self.arch.make_path(cache_path) if cache_path else cache_path, i) for cache_path, i in cursor ]

    @locked_and_handled()
    def file_touched(self, lp):
        try:
            mtime = int(self.fs.indexing_attributes(lp).mtime * self.MTIME_MULT)
        except EnvironmentError:
            return
        except Exception:
            unhandled_exc_handler()
            return

        with self.connhub.cursor() as cursor:
            cursor.execute('SELECT file_id, origin_path FROM files WHERE cache_path = ? AND mtime != ?', (unicode(lp), mtime))
            row = cursor.fetchone()
            if not row:
                return
            file_id, origin = row
            TRACE('deleted file %r modified - used to be at %r' % (lp, origin))
            cursor.execute('DELETE FROM files WHERE file_id = ?', (file_id,))
            if origin:
                return self.arch.make_path(origin)
            return origin

    @locked_and_handled()
    def prune(self, always = False):
        if always or datetime.date.today() != self.last_prune:
            start = time.time()
            TRACE('Pruning deleted file cache...')
            with self.connhub.cursor() as cursor:
                valid_days = self.valid_days()
                cursor.execute("DELETE FROM files WHERE date_added <= DATE('now', 'localtime', '-%d days')" % (self.MAX_DAYS,))
            try:
                valid_days = set(self.valid_days())
                valid_camera_import_days = set([ 'camera-import-%s' % u for u in valid_days ])
                deleted_files = []
                deleted_dirs = []
                dir_iter = fastwalk_with_exception_handling(self.fs, self.cache_path, case_insensitive=False)
                try:
                    dirpath, ents = dir_iter.next()
                except StopIteration:
                    dirpath, ents = None, []

                for dirent in ents:
                    try:
                        _type = dirent.type
                    except AttributeError:
                        _type = self.fs.indexing_attributes(dirpath.join(dirent.name), resolve_link=False)

                    if _type == FILE_TYPE_DIRECTORY:
                        if dirent.name in valid_camera_import_days or dirent.name in valid_days:
                            continue
                        regex = '^\\d+-\\d+-\\d+$|^camera-import-\\d+-\\d+-\\d+$'
                        if re.match(regex, dirent.name):
                            deleted_dirs.append(dirpath.join(dirent.name))
                    elif dirent.name.startswith('~'):
                        deleted_files.append(dirpath.join(dirent.name))
                    elif dirent.name.lower().startswith('dropbox-upgrade-'):
                        try:
                            from build_number.global_bn import BRANCH, BUILD_NUMBER
                            m = re.match('dropbox-upgrade-(\\d+)\\.(\\d+)\\.(\\d+).*', dirent.name.lower())
                            if m:
                                file_build = tuple(map(int, m.groups()))
                                if file_build <= (BRANCH[0], BRANCH[1], BUILD_NUMBER):
                                    deleted_files.append(dirpath.join(dirent.name))
                        except Exception:
                            unhandled_exc_handler()

                for path in deleted_dirs:
                    try:
                        TRACE('DELETED: Clearing cache directory %r', path)
                        fsutil.rmtree(self.fs, path, ignore_errors=True)
                    except Exception:
                        unhandled_exc_handler()

                for path in deleted_files:
                    try:
                        self.fs.remove(path)
                    except PermissionDeniedError:
                        if arch.constants.platform != 'win':
                            unhandled_exc_handler()
                        else:
                            TRACE('DELETED: File in use %r', path)
                    except FileNotFoundError:
                        pass
                    except Exception:
                        unhandled_exc_handler()

                if deleted_files:
                    TRACE('DELETED: Cleared %s files in cache' % len(deleted_files))
            except Exception:
                unhandled_exc_handler()
            else:
                TRACE('Pruning deleted file cache took %f seconds' % (time.time() - start,))

            self.last_prune = datetime.date.today()
        self._check_too_big()
