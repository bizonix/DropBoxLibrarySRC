#Embedded file name: dropbox/client/photodb.py
from dropbox.debugging import easy_repr
from dropbox.sqlite3_helpers import SqliteConnectionHub, VersionedSqlite3Cache, from_db_type, locked_and_handled, to_db_type, enable_converters
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.path import ServerPath
from .photo_constants import DEVICE_DEFAULTS_SET, FIRST_USE, LAST_CU_ID
SYNC_STATUS_PENDING = 0
SYNC_STATUS_REPORT_CU_HASH = 1
SYNC_STATUS_DELETED = 2
SYNC_STATUS_DELETED_WAITING = 3

class PendingPhoto(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('blocklist', 'server_path', 'cu_hash_8', 'cu_hash_full', 'size', 'mtime', 'sync_status', 'ns', 'sjid')

    def __init__(self, server_path, blocklist, cu_hash_8, cu_hash_full, size, mtime, sync_status, ns = None, sjid = None):
        self.blocklist = blocklist
        self.server_path = ServerPath(server_path)
        self.cu_hash_8 = cu_hash_8
        self.cu_hash_full = cu_hash_full
        self.size = size
        self.mtime = mtime
        self.sync_status = sync_status
        self.ns = ns
        self.sjid = sjid

    def __repr__(self):
        return easy_repr(self, *self.__slots__)

    def __eq__(self, other):
        return all((getattr(self, at) == getattr(other, at) for at in self.__slots__))


class DuplicatePhotoException(Exception):

    def __init__(self, path = None, blocklist = None):
        self.path = path
        self.blocklist = blocklist

    def __repr__(self):
        return easy_repr(self, 'path', 'blocklist')


class PhotoDb(VersionedSqlite3Cache):
    PROMPT_ALWAYS, SILENT, DISABLED, PROMPT_NO_ALWAYS = range(4)
    PROMPT = set([PROMPT_ALWAYS, PROMPT_NO_ALWAYS])
    _USER_VERSION = 10

    @classmethod
    def _sqlite_init(cls):
        enable_converters([('BYTETEXT', str)])

    def __init__(self, filename = None, **kw):
        self.tables = ['photo_cache',
         'config',
         'devices',
         'seen_photos',
         'new_imported_photos']
        self.migrations = [self.migrate_0_to_10,
         self.migrate_1_to_2,
         self.migrate_2_to_3,
         self.migrate_3_to_4,
         self.migrate_4_to_5,
         self.migrate_5_to_6,
         self.migrate_6_to_7,
         self.migrate_7_to_8,
         self.migrate_8_to_9,
         self.migrate_9_to_10]
        enable_converters([('BYTETEXT', str)])
        super(PhotoDb, self).__init__(filename, **kw)

    def migrate_0_to_10(self, cursor):
        TRACE('Photouploader: Migrate 0->10')
        cursor.execute('CREATE TABLE config (key TEXT PRIMARY KEY NOT NULL, value BLOB)')
        cursor.execute('CREATE TABLE new_imported_photos (blocklist BYTETEXT PRIMARY KEY NOT NULL, server_path TEXT NOT NULL, cu_hash_8 TEXT NOT NULL, cu_hash_full TEXT NOT NULL, size INTEGER, mtime INTEGER, sync_status INTEGER NOT NULL, ns INTEGER, sjid INTEGER)')
        cursor.execute('CREATE TABLE photo_cache (cu_hash_full BYTETEXT PRIMARY KEY NOT NULL)')
        cursor.execute('CREATE TABLE devices (id INTEGER PRIMARY KEY NOT NULL,uid BYTETEXT NOT NULL UNIQUE,last_import INTEGER,setting INTEGER NOT NULL)')
        cursor.execute('CREATE TABLE seen_photos (device_id INTEGER NOT NULL,name TEXT NOT NULL,mtime TIMESTAMP NOT NULL)')
        cursor.execute('CREATE INDEX dev ON seen_photos (device_id)')
        cursor.execute('CREATE TABLE iphoto_cgids_mapping (iphoto_album_guid BYTETEXT PRIMARY KEY NOT NULL,server_collection_gid BYTETEXT NOT NULL UNIQUE)')
        cursor.execute('CREATE TABLE iphoto_dirs_by_event_id (iphoto_event_id INTEGER PRIMARY KEY NOT NULL,local_dir_path TEXT NOT NULL)')
        cursor.execute('INSERT INTO config (key, value) VALUES (?, ?)', (FIRST_USE, to_db_type(True)))
        cursor.execute('PRAGMA user_version = 10')

    def migrate_1_to_2(self, cursor):
        TRACE('Photouploader: Migrate 1->2')
        cursor.execute('ALTER TABLE seen_photos RENAME TO seen_photos_temp')
        cursor.execute('CREATE TABLE seen_photos (device_id INTEGER NOT NULL,name BYTETEXT NOT NULL,mtime TIMESTAMP NOT NULL)')
        cursor.execute('INSERT INTO seen_photos(device_id, name, mtime) SELECT device, name, mtime FROM seen_photos_temp')
        cursor.execute('DROP TABLE seen_photos_temp')
        cursor.execute('CREATE INDEX dev ON seen_photos (device_id)')
        cursor.execute('VACUUM')
        cursor.execute('PRAGMA user_version = 2')

    def migrate_2_to_3(self, cursor):
        TRACE('Photouploader: Migrate 2->3')
        cursor.execute('DROP TABLE new_imported_photos')
        cursor.execute('CREATE TABLE new_imported_photos (blocklist BYTETEXT PRIMARY KEY NOT NULL, server_path TEXT NOT NULL, cu_hash_8 TEXT NOT NULL, cu_hash_full TEXT NOT NULL, size INTEGER, mtime INTEGER, sync_status INTEGER NOT NULL, ns INTEGER, sjid INTEGER)')
        cursor.execute('DROP TABLE photo_cache')
        cursor.execute('CREATE TABLE photo_cache (cu_hash_full BYTETEXT PRIMARY KEY NOT NULL)')
        cursor.execute("UPDATE config set key='last_cu_id' WHERE key='last_cr_id'")
        cursor.execute('VACUUM')
        cursor.execute('PRAGMA user_version = 3')

    def migrate_3_to_4(self, cursor):
        TRACE('Photouploader: Migrate 3->4')
        cursor.execute("DELETE from config WHERE key='last_cu_id'")
        cursor.execute('PRAGMA user_version = 4')

    def migrate_4_to_5(self, cursor):
        TRACE('Photouploader: Migrate 4->5')
        cursor.execute('ALTER TABLE seen_photos RENAME TO seen_photos_temp')
        cursor.execute('DROP INDEX dev')
        cursor.execute('CREATE TABLE seen_photos (device_id INTEGER NOT NULL,name TEXT NOT NULL,mtime TIMESTAMP NOT NULL)')
        cursor.execute('CREATE INDEX dev ON seen_photos (device_id)')
        cursor.execute('INSERT INTO seen_photos(device_id, name, mtime) SELECT device_id, name, mtime FROM seen_photos_temp')
        cursor.execute('DROP TABLE seen_photos_temp')
        cursor.execute('PRAGMA user_version = 5')

    def migrate_5_to_6(self, cursor):
        TRACE('Photouploader: Migrate 5->6')
        cursor.execute('ALTER TABLE devices RENAME TO devices_temp')
        cursor.execute('CREATE TABLE devices (id INTEGER PRIMARY KEY NOT NULL,uid BYTETEXT NOT NULL UNIQUE,last_import INTEGER,setting INTEGER NOT NULL)')
        cursor.execute('INSERT INTO devices(id, uid, setting) SELECT id, uid, setting FROM devices_temp')
        cursor.execute('DROP TABLE devices_temp')
        cursor.execute('PRAGMA user_version = 6')

    def migrate_6_to_7(self, cursor):
        TRACE('Photouploader: Migrate 6->7')
        ids = set(cursor.execute('SELECT id FROM devices'))
        if len(ids) == 0:
            cursor.execute('INSERT INTO config (key, value) VALUES (?, ?)', (FIRST_USE, to_db_type(True)))
        cursor.execute('PRAGMA user_version = 7')

    def migrate_7_to_8(self, cursor):
        TRACE('Photouploader: Migrate 7->8')
        cursor.execute('CREATE TABLE iphoto_cgids_mapping (iphoto_album_guid BYTETEXT PRIMARY KEY NOT NULL,server_collection_gid BYTETEXT NOT NULL UNIQUE)')
        cursor.execute('PRAGMA user_version = 8')

    def migrate_8_to_9(self, cursor):
        TRACE('Photouploader: Migrate 8->9')
        cursor.execute('CREATE TABLE iphoto_event_dirs_mapping (iphoto_event_id INTEGER PRIMARY KEY NOT NULL,local_dir_path TEXT NOT NULL)')
        cursor.execute('PRAGMA user_version = 9')

    def migrate_9_to_10(self, cursor):
        TRACE('Photouploader: Migrate 9->10')
        cursor.execute('DROP TABLE IF EXISTS iphoto_event_dirs_mapping')
        cursor.execute('CREATE TABLE IF NOT EXISTS iphoto_dirs_by_event_id (iphoto_event_id INTEGER PRIMARY KEY NOT NULL,local_dir_path TEXT NOT NULL)')
        cursor.execute('PRAGMA user_version = 10')

    def _load_data(self):
        self.by_blocklist = {}
        self.by_path = {}
        conn = self.connhub.conn()
        try:
            self.last_cu_id = self.get_config_key(LAST_CU_ID, conn)
        except KeyError:
            self.last_cu_id = -2

        for row in conn.execute('SELECT server_path, blocklist, cu_hash_8, cu_hash_full, size, mtime, sync_status, ns, sjid FROM new_imported_photos'):
            photo = PendingPhoto(*row)
            self.by_blocklist[photo.blocklist] = photo
            self.by_path[photo.server_path] = photo

    @locked_and_handled()
    def clear_device_settings(self):
        with self.connhub.conn() as conn:
            conn.execute('DELETE from devices')
            conn.execute('VACUUM')

    @locked_and_handled()
    def device_setting(self, uid):
        if uid is None:
            return self.PROMPT_ALWAYS
        setting = self.connhub.conn().execute('SELECT setting FROM devices WHERE uid=?', (uid,)).fetchone()
        if setting is not None:
            return setting[0]
        return self.PROMPT_ALWAYS

    def device_disabled(self, uid):
        return self.device_setting(uid) == self.DISABLED

    @locked_and_handled()
    def add_device(self, uid, setting = PROMPT_ALWAYS):
        if uid is None:
            return
        with self.connhub.conn() as conn:
            conn.execute('INSERT OR REPLACE INTO devices (id, last_import, uid, setting) VALUES ((SELECT id from devices where uid = ?), (SELECT last_import from devices where uid = ?), ?, ?)', (uid,
             uid,
             uid,
             setting))

    @locked_and_handled()
    def device_exists(self, uid):
        if uid is None:
            return False
        with self.connhub.conn() as conn:
            try:
                self._get_device_id_by_uid(uid, conn)
            except KeyError:
                return False

            return True

    def _get_device_id_by_uid(self, device_uid, conn):
        device_id = conn.execute('SELECT id FROM devices WHERE uid=?', (device_uid,)).fetchone()
        if not device_id:
            raise KeyError(device_uid)
        return device_id[0]

    @locked_and_handled()
    def get_device_last_import(self, uid):
        if uid is None:
            return
        last_import = self.connhub.conn().execute('SELECT last_import FROM devices WHERE uid=?', (uid,)).fetchone()
        if last_import is not None:
            return last_import[0]

    @locked_and_handled()
    def set_device_last_import(self, uid, last_import):
        if uid is None:
            return
        with self.connhub.conn() as conn:
            device_id = self._get_device_id_by_uid(uid, conn)
            conn.execute('UPDATE devices SET last_import=? WHERE id=?', (last_import, device_id))

    @locked_and_handled()
    def add_seen_photos(self, device_uid, name_mtime_iter):
        if device_uid is None:
            return
        with self.connhub.conn() as conn:
            device_id = self._get_device_id_by_uid(device_uid, conn)
            conn.executemany('INSERT INTO seen_photos (device_id, name, mtime) VALUES (%d, ?, ?)' % device_id, name_mtime_iter)

    @locked_and_handled()
    def get_seen_photos(self, device_uid):
        if device_uid is None:
            return set()
        conn = self.connhub.conn()
        device_id = self._get_device_id_by_uid(device_uid, conn)
        return set(conn.execute('SELECT name, mtime FROM seen_photos WHERE device_id=?', (device_id,)))

    @locked_and_handled()
    def del_seen_photos(self, device_uid, name_mtime_iter):
        if device_uid is None:
            return
        with self.connhub.conn() as conn:
            device_id = self._get_device_id_by_uid(device_uid, conn)
            conn.executemany('DELETE FROM seen_photos WHERE device_id=%d and name=? and mtime=?' % device_id, name_mtime_iter)

    @locked_and_handled()
    def pending(self):
        return self.by_path.values()

    @locked_and_handled()
    def has_pending(self):
        return bool(self.by_path)

    @locked_and_handled()
    def get_pending_size(self):
        return sum((photo.size for photo in self.by_path.itervalues() if photo.sync_status == SYNC_STATUS_PENDING))

    @locked_and_handled()
    def find_imported(self, blocklist = None, server_path = None):
        assert not (blocklist and server_path)
        if blocklist:
            return self.by_blocklist.get(blocklist)
        if server_path:
            return self.by_path.get(server_path)

    @locked_and_handled(retry=False, retval=False)
    def exists(self, cu_hash_full):
        assert len(cu_hash_full) == 32
        conn = self.connhub.conn()
        if conn.execute('SELECT cu_hash_full FROM new_imported_photos WHERE cu_hash_full=?', (cu_hash_full,)).fetchone():
            return True
        if conn.execute('SELECT * FROM photo_cache WHERE cu_hash_full=?', (cu_hash_full,)).fetchone():
            return True
        return False

    @locked_and_handled()
    def add_server_photos(self, cu_hashes_full, last_cu_id = None):
        with self.connhub.cursor() as cursor:
            if cu_hashes_full:
                cursor.executemany('INSERT OR REPLACE INTO photo_cache (cu_hash_full) VALUES (?)', ((cu_hash_full,) for cu_hash_full in cu_hashes_full))
            if last_cu_id and last_cu_id != self.last_cu_id:
                self.set_config_key(LAST_CU_ID, int(last_cu_id), cursor)
                self.last_cu_id = last_cu_id

    @locked_and_handled()
    def num_imported(self):
        conn = self.connhub.conn()
        num = conn.execute('SELECT count(*) FROM photo_cache').fetchone()[0]
        num += conn.execute('SELECT count(*) FROM new_imported_photos').fetchone()[0]
        return num

    @locked_and_handled()
    def has_imported(self):
        if self.last_cu_id > 0:
            return True
        conn = self.connhub.conn()
        if conn.execute('SELECT count(*) FROM photo_cache').fetchone()[0]:
            return True
        if conn.execute('SELECT count(*) FROM new_imported_photos').fetchone()[0]:
            return True
        return False

    @locked_and_handled()
    def has_imported_from_device(self, device_id):
        conn = self.connhub.conn()
        if conn.execute('SELECT count(*) FROM photo_cache where ').fetchone()[0]:
            return True
        if conn.execute('SELECT count(*) FROM new_imported_photos').fetchone()[0]:
            return True
        return False

    @locked_and_handled()
    def add_photo(self, blocklist, rr_server_path, cu_hash_8, cu_hash_full, size, mtime):
        if rr_server_path in self.by_path:
            raise DuplicatePhotoException(path=rr_server_path)
        if blocklist in self.by_blocklist:
            raise DuplicatePhotoException(blocklist=blocklist)
        photo = PendingPhoto(server_path=rr_server_path, blocklist=blocklist, cu_hash_8=cu_hash_8, cu_hash_full=cu_hash_full, size=size, mtime=mtime, sync_status=SYNC_STATUS_PENDING)
        with self.connhub.cursor() as cursor:
            TRACE('Photouploader: Adding %r to new_imported_photos', photo)
            cursor.execute('INSERT INTO new_imported_photos (blocklist, server_path, cu_hash_8, cu_hash_full, size, mtime, sync_status) VALUES (?, ?, ?, ?, ?, ?, ?)', (blocklist,
             unicode(rr_server_path),
             cu_hash_8,
             cu_hash_full,
             size,
             mtime,
             SYNC_STATUS_PENDING))
        self.by_blocklist[photo.blocklist] = photo
        self.by_path[photo.server_path] = photo
        return photo

    @locked_and_handled(retry=False, retval=None)
    def delete(self, photos):
        if photos:
            photos = list(photos)
            with self.connhub.cursor() as cursor:
                cursor.executemany('DELETE FROM new_imported_photos WHERE blocklist=?', ((photo.blocklist,) for photo in photos))
                if cursor.rowcount:
                    TRACE('Photouploader: Deleted %d rows from new_imported_photos', cursor.rowcount)
            for photo in photos:
                try:
                    TRACE('Photouploader: Deleting %r from pending photos', photo)
                    del self.by_blocklist[photo.blocklist]
                    del self.by_path[photo.server_path]
                except KeyError:
                    unhandled_exc_handler()

    @locked_and_handled(retry=False, retval=None)
    def prune_by_sjid(self, ns, high_sjid):
        with self.connhub.cursor() as cursor:
            cursor.execute('DELETE FROM new_imported_photos WHERE sync_status=? and ns=? and sjid<=?', (SYNC_STATUS_DELETED_WAITING, ns, high_sjid))
            if cursor.rowcount:
                TRACE('Photouploader: Pruned %d rows from new_imported_photos, ns=%r, high_sjid=%r', cursor.rowcount, ns, high_sjid)
        del_me = [ photo for photo in self.by_path.itervalues() if photo.sync_status == SYNC_STATUS_DELETED_WAITING and photo.ns == ns and photo.sjid <= high_sjid ]
        for photo in del_me:
            try:
                del self.by_blocklist[photo.blocklist]
                del self.by_path[photo.server_path]
            except KeyError:
                unhandled_exc_handler()

    @locked_and_handled(retry=False, retval=None)
    def update_status(self, photos, status, nses = None, sjids = None):
        if photos:
            photos = list(photos)
            if nses and sjids:
                with self.connhub.cursor() as cursor:
                    cursor.executemany('UPDATE new_imported_photos SET ns=?, sjid=?, sync_status=? WHERE blocklist=?', ((nses[photo.blocklist],
                     sjids[photo.blocklist],
                     status,
                     photo.blocklist) for photo in photos))
                for photo in photos:
                    if photo.ns:
                        report_bad_assumption('Setting pending photo ns when it already has an ns')
                    photo.ns = nses[photo.blocklist]
                    photo.sjid = sjids[photo.blocklist]
                    photo.sync_status = status

            else:
                with self.connhub.cursor() as cursor:
                    cursor.executemany('UPDATE new_imported_photos SET sync_status=? WHERE blocklist=?', ((status, photo.blocklist) for photo in photos))
                for photo in photos:
                    photo.sync_status = status

    @locked_and_handled()
    def save_iphoto_album_server_cgid_mapping(self, server_id_by_iphoto_id):
        with self.connhub.cursor() as cursor:
            cursor.executemany('INSERT INTO iphoto_cgids_mapping (iphoto_album_guid, server_collection_gid) VALUES (?, ?)', server_id_by_iphoto_id.iteritems())

    @locked_and_handled()
    def get_iphoto_album_server_cgid_mapping(self):
        conn = self.connhub.conn()
        return dict(conn.execute('SELECT iphoto_album_guid, server_collection_gid FROM iphoto_cgids_mapping'))

    @locked_and_handled()
    def clear_iphoto_album_server_cgid_mapping(self):
        with self.connhub.cursor() as cursor:
            cursor.execute('DELETE FROM iphoto_cgids_mapping')

    @locked_and_handled()
    def save_iphoto_event_dirname_by_id(self, event_id, event_dirname):
        with self.connhub.cursor() as cursor:
            cursor.execute('INSERT INTO  iphoto_dirs_by_event_id (iphoto_event_id, local_dir_path) VALUES (?, ?)', (event_id, event_dirname))

    @locked_and_handled()
    def get_iphoto_event_dirname_by_id(self):
        conn = self.connhub.conn()
        return dict(conn.execute('SELECT iphoto_event_id, local_dir_path FROM iphoto_dirs_by_event_id'))

    @locked_and_handled()
    def get_config(self, key, default = None):
        try:
            return self.get_config_key(key, self.connhub.conn())
        except KeyError:
            return default

    @locked_and_handled()
    def set_config(self, key, value):
        with self.connhub.cursor() as cursor:
            return self.set_config_key(key, value, cursor)

    @locked_and_handled()
    def del_config(self, key, default = None):
        with self.connhub.cursor() as cursor:
            self.del_config_key(key, cursor)

    @locked_and_handled()
    def update_device_defaults_set(self, new_defaults_set):
        TRACE("Adding new devices we've defaulted to Dropbox: %r", new_defaults_set)
        with self.connhub.cursor() as cursor:
            try:
                defaults_set = self.get_config_key(DEVICE_DEFAULTS_SET, cursor)
            except KeyError:
                defaults_set = []

            defaults_set.extend(new_defaults_set)
            self.set_config_key(DEVICE_DEFAULTS_SET, defaults_set, cursor)

    @staticmethod
    def get_config_key(key, cursor):
        row = cursor.execute('SELECT value FROM config WHERE key=?', (key,)).fetchone()
        if row:
            return from_db_type(row[0])
        raise KeyError(key)

    @staticmethod
    def set_config_key(key, value, cursor):
        cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, to_db_type(value)))

    @staticmethod
    def del_config_key(key, cursor):
        cursor.execute('DELETE FROM config WHERE key=?', (key,))
