#Embedded file name: dropbox/client/multiaccount/instance_database.py
import arch
import os
from dropbox.client.mapreduce import attempt_keystore_migration, DBKeyStore
from dropbox.fileutils import safe_move, safe_remove, tempfilename
from dropbox.sqlite3_helpers import dict_like_row, locked_and_handled, VersionedSqlite3Cache
from dropbox.trace import TRACE, unhandled_exc_handler

class MasterConfig(object):

    def __init__(self, directory):
        if directory is None:
            directory = arch.constants.instance_config_path
        self.directory = directory
        self.check_directory(self.directory)

    def check_directory(self, path):
        try:
            os.mkdir(path)
        except OSError as exn:
            if exn.errno == 17:
                pass


class InstanceDB(VersionedSqlite3Cache):
    _USER_VERSION = 1

    def __init__(self, filename, **kwargs):
        self.tables = ['instance']
        self.migrations = [self.migrate_0_to_1]
        self.filename = filename
        self.disk_err_count = 0
        super(InstanceDB, self).__init__(filename, **kwargs)

    def migrate_0_to_1(self, cursor):
        TRACE('%s: Migrating 0->1', self.__class__.__name__)
        cursor.execute('\n                       CREATE TABLE instance (\n                           id INTEGER PRIMARY KEY AUTOINCREMENT,\n                           active INTEGER NOT NULL DEFAULT 1,\n                           master INTEGER NOT NULL DEFAULT 0,\n                           appdata_path TEXT,\n                           default_dropbox_path TEXT,\n                           default_dropbox_folder_name TEXT,\n                           business_name TEXT\n                       )\n                       ')
        cursor.execute('PRAGMA user_version = 1')

    def _load_data(self):
        self.get_or_create_master()

    @locked_and_handled(track_disk_err=True)
    def get_or_create_master(self):
        with self.connhub.cursor() as cursor:
            master_query = 'SELECT * from instance where active = 1 and master = 1'
            master = cursor.execute(master_query).fetchone()
            if not master:
                master_tuple = (None,
                 True,
                 True,
                 arch.constants.appdata_path,
                 arch.constants.default_dropbox_path,
                 arch.constants.default_dropbox_folder_name,
                 None)
                cursor.execute('INSERT INTO instance VALUES (?, ?, ?, ?, ?, ?, ?)', master_tuple)
                master = cursor.execute(master_query).fetchone()
            return master

    @locked_and_handled(track_disk_err=True)
    def get_slave_rows(self):
        with self.connhub.cursor() as cursor:
            return cursor.execute('SELECT * from instance where active = 1 and master = 0').fetchall()

    @locked_and_handled(track_disk_err=True)
    def set_inactive_by_id(self, instance_id):
        with self.connhub.cursor() as cursor:
            query = 'UPDATE instance SET active = 0 WHERE active = 1 and id = ?'
            return cursor.execute(query, (instance_id,)).fetchall()

    @locked_and_handled(track_disk_err=True)
    def promote_slave_to_master(self, instance_id):
        with self.connhub.cursor() as cursor:
            query = 'UPDATE instance SET master = 1 WHERE active = 1 and id = ?'
            return cursor.execute(query, (instance_id,)).fetchall()

    @locked_and_handled(track_disk_err=True)
    def update_dropbox_name(self, instance_id, dropbox_name, dropbox_path):
        with self.connhub.cursor() as cursor:
            query = '\n            UPDATE instance\n            SET default_dropbox_folder_name = ?,\n                default_dropbox_path = ?\n            WHERE id = ?\n            '
            return cursor.execute(query, (dropbox_name, dropbox_path, instance_id))

    @locked_and_handled(track_disk_err=True)
    def insert_slave(self):
        with self.connhub.cursor() as cursor:
            slave_tuple = (None,
             True,
             False,
             None,
             None,
             None,
             None)
            cursor.execute('INSERT INTO instance VALUES (?, ?, ?, ?, ?, ?, ?)', slave_tuple)
            slave_id = cursor.lastrowid
            suffixed = lambda s: '%s (%s)' % (s, slave_id)
            appdata_path = arch.constants.appdata_path + str(slave_id)
            default_dropbox_path = suffixed(arch.constants.default_dropbox_path)
            default_dropbox_folder_name = suffixed(arch.constants.default_dropbox_folder_name)
            query = '\n                    UPDATE instance\n                    SET appdata_path = ?,\n                        default_dropbox_path = ?,\n                        default_dropbox_folder_name = ?\n                    WHERE id = ?\n                    '
            subst = (appdata_path,
             default_dropbox_path,
             default_dropbox_folder_name,
             slave_id)
            cursor.execute(query, subst)
            return self._get_row_unlocked(slave_id, cursor)

    def _get_row_unlocked(self, instance_id, cursor):
        return cursor.execute('SELECT * from instance where id = ?', (instance_id,)).fetchone()

    @locked_and_handled(track_disk_err=True)
    def get_row(self, instance_id):
        with self.connhub.cursor() as cursor:
            return self._get_row_unlocked(instance_id, cursor)


def _instance_db_row_text_factory(conn):
    conn.text_factory = unicode
    conn.row_factory = dict_like_row


class InstanceConfig(MasterConfig):
    _INSTANCE_DB_FILENAME = 'instance.dbx'

    def __init__(self, app, directory = None):
        super(InstanceConfig, self).__init__(directory)
        self.filename = os.path.join(self.directory, self._INSTANCE_DB_FILENAME)
        if not os.path.exists(self.filename):
            if arch.constants.platform == 'win':
                attempt_keystore_migration(app, self.directory, migrate_to_instance_id=1)
            self.keystore = DBKeyStore(self.directory)
            self.create_db()
        else:
            self.keystore = DBKeyStore(self.directory)
        self.instance_db = InstanceDB(self.filename, keystore=self.keystore, post_create=_instance_db_row_text_factory)

    def clear(self):
        try:
            safe_remove(self.filename)
        except Exception:
            unhandled_exc_handler()

    def create_db(self):
        with tempfilename(dir=self.directory) as tmp:
            tmp_config = InstanceDB(tmp, keystore=self.keystore, post_create=_instance_db_row_text_factory)
            tmp_config.close()
            if arch.constants.platform == 'win':
                safe_remove(self.filename)
            safe_move(tmp, self.filename)

    def get_slave_row(self, create_if_not_exists = False):
        slave_rows = self.instance_db.get_slave_rows()
        slave_row = None
        if slave_rows:
            assert len(slave_rows) == 1, 'expected a slave row: %r' % slave_rows
            slave_row = slave_rows.pop()
        elif create_if_not_exists:
            slave_row = self.instance_db.insert_slave()
        return slave_row
