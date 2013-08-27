#Embedded file name: dropbox/client/databases.py
import sys
import os
import time
import base64
import sqlite3
import shutil
import tempfile
import threading
import cPickle as pickle
from contextlib import closing, contextmanager
from client_api.connection_hub import HTTP404Error
import arch
from dropbox import sqlite3_helpers
from dropbox.client.config import ConfigDict
from dropbox.client.db_exception import handle_corrupted_db
from dropbox.client.mapreduce import BAD_CONFIG_KEY
from dropbox.file_cache.file_cache import FileCache
from dropbox.file_cache.sqlite_backend import SQLiteBackend
from dropbox.fileutils import safe_remove, tempfilename, umkstemp
from dropbox.functions import migrate_db_get_table_entries
from dropbox.ideal_tracker.ideal_tracker import IdealTracker
from dropbox.server_path import server_path_ns_unicode
from dropbox.trace import unhandled_exc_handler, TRACE, report_bad_assumption, add_exception_handler, remove_exception_handler
_CONFIG_FILENAME = u'config.db'
_CONFIG_ENC_FILENAME = u'config.dbx'
_FILE_CACHE_FILENAME_TEMPLATE = u'filecache%d.db'
_FILE_CACHE_FILENAME = u'filecache.db'
_FILE_CACHE_ENC_FILENAME = u'filecache.dbx'
_PENDING_DATABASE_PREFIX = u'PENDING_'
_UPDATED_DATABASE_PREFIX = u'UPDATED_'
_IDEAL_TRACKER_ENC_FILENAME = u'idealtracker.dbx'
CONFIG_SCHEMA_VERSION_1 = 1
CONFIG_SCHEMA_VERSION = 2

def clear_appdata_for_unlink(clear_unlink_cookie = False, except_for = frozenset(), database_dir = None):
    TRACE('Unlinking...')
    didnt_delete = []
    did_delete = []
    database_dir = database_dir or arch.constants.appdata_path
    try:
        files = os.listdir(database_dir)
    except Exception:
        unhandled_exc_handler()
    else:
        rm_files = (u'aggregation.dbx', u'cache', u'config.db', u'config.dbx', u'dropbox.db', u'filecache.db', u'filecache.dbx', u'filecache1.db', u'filecache2.db', u'host.db', u'ignore.db', u'migrate.db', u'moving', u'notifications.dbx', u'sigstore.db', u'sigstore.dbx', u'photo.dbx')
        if clear_unlink_cookie:
            rm_files += (u'unlink.db',)
        for fn in files:
            fnl = fn.lower()
            if fnl not in rm_files or fnl in except_for:
                continue
            path = os.path.join(database_dir, fn)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    safe_remove(path)
            except Exception:
                unhandled_exc_handler()
            finally:
                (didnt_delete if os.path.exists(path) else did_delete).append(fn)

    TRACE('did delete: %r', did_delete)
    TRACE("didn't delete: %r", didnt_delete)
    return (did_delete, didnt_delete)


def safe_move(src, dst, must_delete_src = True):
    if must_delete_src:
        raise NotImplementedError('must_delete_src=True')
    if os.path.isdir(src):
        raise Exception('Attempt to move a directory')
    try:
        os.rename(src, dst)
    except OSError:
        shutil.copy2(src, dst)
        safe_remove(src)


def cleanup_corrupt_databases(database_dir):
    safe_remove(os.path.join(database_dir, _CONFIG_ENC_FILENAME))
    safe_remove(os.path.join(database_dir, _FILE_CACHE_ENC_FILENAME))


@contextmanager
def new_config_file(database_dir, keystore):
    with tempfilename(dir=database_dir) as enc_tmp:
        with closing(ConfigDict(enc_tmp, keystore=keystore)) as new_enc_config:
            yield new_enc_config
            new_enc_config['config_schema_version'] = CONFIG_SCHEMA_VERSION
        with tempfilename(dir=database_dir) as tmp:
            with closing(ConfigDict(tmp)) as new_config:
                new_config['config_schema_version'] = CONFIG_SCHEMA_VERSION
            if arch.constants.platform == 'win':
                safe_remove(os.path.join(database_dir, _CONFIG_FILENAME))
                safe_remove(os.path.join(database_dir, _CONFIG_ENC_FILENAME))
            safe_move(enc_tmp, os.path.join(database_dir, _CONFIG_ENC_FILENAME), False)
            safe_move(tmp, os.path.join(database_dir, _CONFIG_FILENAME), False)


def reinitialize_databases(config, database_dir, key = None):
    clear_appdata_for_unlink(except_for=set((u'config.dbx',)), database_dir=database_dir)
    with config as db_config:
        db_config.clear()
        db_config['config_schema_version'] = CONFIG_SCHEMA_VERSION
        if key:
            db_config.connection.teresa(key)
    with tempfilename(dir=database_dir) as tmp:
        with closing(ConfigDict(tmp)) as new_config:
            new_config['config_schema_version'] = CONFIG_SCHEMA_VERSION
        if arch.constants.platform == 'win':
            safe_remove(os.path.join(database_dir, _CONFIG_FILENAME))
        safe_move(tmp, os.path.join(database_dir, _CONFIG_FILENAME), False)


_config_migration_happened = [False]
_filecache_migration_happened = [False]

def _check_migration_config(database_dir, keystore):
    if _filecache_migration_happened[0]:
        raise Exception('Called filecache migration code before config migration code')
    _config_migration_happened[0] = True
    config_enc_path = os.path.join(database_dir, _CONFIG_ENC_FILENAME)
    config_db_path = os.path.join(database_dir, _CONFIG_FILENAME)
    dropbox_db_path = os.path.join(database_dir, u'dropbox.db')
    migrate_db_path = os.path.join(database_dir, u'migrate.db')
    if os.path.exists(config_db_path) and any((os.path.exists(p) for p in (dropbox_db_path, migrate_db_path))):
        TRACE('New config databases and old config databases existed... User has been jumping between versions, resetting state')
        for p in (config_db_path,
         config_enc_path,
         dropbox_db_path,
         migrate_db_path):
            safe_remove(p)

    if os.path.exists(dropbox_db_path):
        TRACE('Attempting to import %r from %r into %r', ConfigDict, dropbox_db_path, config_enc_path)
        try:
            with new_config_file(database_dir, keystore) as new_config:
                with closing(sqlite3_helpers.connect(dropbox_db_path)) as old_conn:
                    num_rows_imported = new_config.import_from_dropbox_db(old_conn)
                if 'email' in new_config and 'dropbox_path' not in new_config:
                    new_config['dropbox_path'] = arch.constants.seven_default_dropbox_path
        except Exception:
            unhandled_exc_handler()
            TRACE('Failed to migrate from %r!', dropbox_db_path)
            safe_remove(dropbox_db_path)
        else:
            safe_remove(migrate_db_path)
            TRACE('... successfully migrated %r entries', num_rows_imported)

    if os.path.exists(migrate_db_path):
        TRACE('Attempting to import %r from %r into %r', ConfigDict, migrate_db_path, config_enc_path)
        try:
            with new_config_file(database_dir, keystore) as new_config:
                with open(migrate_db_path, 'rb') as f:
                    num_rows_imported = new_config.import_from_migrate_db(f)
                    if 'email' in new_config and 'dropbox_path' not in new_config:
                        new_config['dropbox_path'] = arch.constants.seven_default_dropbox_path
        except Exception:
            TRACE('Failed to migrate from %r!', migrate_db_path)
            unhandled_exc_handler()
            safe_remove(migrate_db_path)
        else:
            safe_remove(dropbox_db_path)
            TRACE('... successfully migrated %r entries', num_rows_imported)

    try:
        if os.path.exists(config_db_path):
            with closing(ConfigDict(config_db_path)) as config:
                version = config.get('config_schema_version')
                if version == CONFIG_SCHEMA_VERSION:
                    if not os.path.exists(config_enc_path):
                        raise Exception('Missing config.dbx file!')
                    with closing(ConfigDict(config_enc_path, keystore=keystore)) as config_enc:
                        enc_version = config_enc.get('config_schema_version')
                        if enc_version != CONFIG_SCHEMA_VERSION:
                            raise Exception('Bad schema for config.dbx file!')
                elif version == CONFIG_SCHEMA_VERSION_1 or version is None:
                    if version is None:
                        report_bad_assumption('Version was None while importing from config.db')
                    TRACE('Attempting to import %r from %r into %r', ConfigDict, config_db_path, config_enc_path)
                    with new_config_file(database_dir, keystore) as new_config:
                        new_config.update(config)
                        config.close()
                    safe_remove(os.path.join(database_dir, _FILE_CACHE_ENC_FILENAME))
                    TRACE('... successfully migrated')
                    safe_remove(migrate_db_path)
                    safe_remove(dropbox_db_path)
                else:
                    raise Exception('Unknown version %s' % version)
        elif os.path.exists(config_enc_path):
            with closing(ConfigDict(config_enc_path, keystore=keystore)) as enc_config:
                config_version = enc_config.get('config_schema_version')
                if config_version is None:
                    report_bad_assumption('This client suffered from the config.clear() bug')
                elif config_version != CONFIG_SCHEMA_VERSION_1:
                    raise Exception('Bad version in config.dbx file: %r' % config_version)
                with new_config_file(database_dir, keystore) as new_config:
                    new_config.update(enc_config)
                    enc_config.close()
    except Exception as e:
        if isinstance(e, sqlite3.DatabaseError) and e.message == 'file is encrypted or is not a database':
            keystore.report_error(BAD_CONFIG_KEY)
        unhandled_exc_handler()
        TRACE('Failed to migrate or read from %r!', config_db_path)
        safe_remove(config_db_path)
        safe_remove(config_enc_path)

    if not os.path.exists(config_db_path):
        with new_config_file(database_dir, keystore):
            TRACE('Creating new empty config file')


def _patch_broken_xattrs(fc, server_conn):
    thr = threading.currentThread()
    if hasattr(thr, 'stopped') and hasattr(thr, 'sleep'):
        stopped = thr.stopped
        sleep = thr.sleep
    else:

        def stopped():
            return False

        sleep = time.sleep
    last_revision = dict(((ns, -1) for ns in fc.get_all_tracked_namespaces()))
    if not last_revision:
        report_bad_assumption('Empty last revision before doing list_xattrs???')
        return
    while not stopped():
        try:
            ret = server_conn.list_xattrs(last_revision)
        except HTTP404Error:
            return
        except Exception:
            unhandled_exc_handler()
            sleep(10)
            continue

        if ret.get('resync', False):
            raise Exception('Server requested we abort this import')

        def feed_into_patch():
            for listed_ent in ret['list']:
                ns = server_path_ns_unicode(listed_ent['path'])
                if listed_ent['sjid'] > last_revision[ns]:
                    last_revision[ns] = listed_ent['sjid']
                yield listed_ent

        fc.patch_broken_xattrs(feed_into_patch())
        if not ret.get('more_results', False):
            return


def file_cache_get_sjid(path, root_ns):
    with closing(FileCache.create_database_connection(path)) as old_conn:
        if old_conn.execute("SELECT value FROM config WHERE key='filetype'").fetchone()[0] != FileCache.FILETYPE:
            raise Exception('Not a valid filecache database.')
        version = old_conn.execute("SELECT value FROM config WHERE key='version'").fetchone()[0]
        if version >= 3:
            return (old_conn.execute('SELECT last_sjid FROM namespace_map WHERE ns=?', (root_ns,)).fetchone()[0], True)
        raise Exception('Unsupported filecache version %d' % version)


def file_cache2_get_sjid(path, root_ns):
    with closing(FileCache.create_database_connection(path)) as old_conn:
        return (old_conn.execute('SELECT last_sjid FROM namespace_map WHERE ns=?', (root_ns,)).fetchone()[0], True)


def file_cache1_get_sjid(path, root_ns):
    with closing(FileCache.connect_to_version_123_database(path)) as old_conn:
        return (old_conn.execute('SELECT last_sjid FROM last_revision WHERE ns=?', (root_ns,)).fetchone()[0], True)


def dropbox_db_get_sjid(path, root_ns):
    with closing(sqlite3_helpers.connect(path)) as old_conn:
        return (pickle.loads(base64.b64decode(old_conn.execute('select value from config where key=?', ('last_revision',)).fetchone()[0]))[root_ns], True)


def migrate_db_get_sjid(path, root_ns):
    with open(path, 'rb') as f:
        for obj in migrate_db_get_table_entries(f, 'Config'):
            if obj['key'] == 'last_revision':
                return (obj['value'][root_ns], True)

    raise Exception('no root_ns in migration db!')


def filecache_version_1_2_data_plats(dropbox_dir):
    if arch.constants.platform not in ('mac', 'linux'):
        platforms = ()
    else:
        platforms = set(('posix',))
        if dropbox_dir and arch.util.fs_supports_attrs(dropbox_dir):
            platforms.add(arch.constants.platform)
    return platforms


def _check_migration_filecache(database_dir, status_controller, server_conn, config, sigstore, root_ns, keystore):
    _filecache_migration_happened[0] = True
    dropbox_dir = config.get('dropbox_path')
    config_attrs_whitelist = config.get('attrs')
    file_cache_path = os.path.join(database_dir, _FILE_CACHE_ENC_FILENAME)

    def migrate_file_cache_2(path):
        tmp, tmp2 = (None, None)
        try:
            f, tmp = umkstemp(dir=database_dir)
            os.close(f)
            f, tmp2 = umkstemp(dir=database_dir)
            os.close(f)
            shutil.copy(path, tmp)
            with closing(FileCache.connect_to_version_123_database(tmp)) as old_conn:
                FileCache.import_from_filecache_2(old_conn, filecache_version_1_2_data_plats(dropbox_dir), config_attrs_whitelist or {}, server_conn=server_conn)
            with closing(FileCache(tmp)) as old_fc:
                old_fc.copy(tmp2, keystore=keystore).close()
            safe_move(tmp2, file_cache_path, False)
            TRACE('... successfully migrated')
            safe_remove(path)
        except Exception:
            e = sys.exc_info()
            try:
                try:
                    for _f in (tmp, tmp2):
                        if _f:
                            safe_remove(_f)

                except Exception:
                    unhandled_exc_handler()

                raise e[0], e[1], e[2]
            finally:
                del e

    def migrate_file_cache_1(filecache1_path):
        f, tmp = umkstemp(dir=database_dir)
        os.close(f)
        try:
            with closing(FileCache.connect_to_version_123_database(filecache1_path)) as old_conn:
                with closing(FileCache(tmp, keystore=keystore)) as fc:
                    num_rows_imported = fc.import_from_filecache_1(old_conn, filecache_version_1_2_data_plats(dropbox_dir), not config.get('already_fixed_up_attrs_larger_than_255', False), config_attrs_whitelist or {}, server_conn=server_conn)
                    try:
                        del config['already_fixed_up_attrs_larger_than_255']
                    except Exception:
                        unhandled_exc_handler()

                    _patch_broken_xattrs(fc, server_conn)
            safe_move(tmp, file_cache_path, False)
            TRACE('... successfully migrated %r entries', num_rows_imported)
            safe_remove(filecache1_path)
        except Exception:
            safe_remove(tmp)
            raise

    def migrate_dropbox_db(dropbox_db_path):
        f, tmp = umkstemp(dir=database_dir)
        os.close(f)
        try:
            with closing(sqlite3_helpers.connect(dropbox_db_path)) as old_conn:
                with closing(FileCache(tmp, keystore=keystore)) as fc:
                    num_rows_imported = fc.import_from_dropbox_db(old_conn, server_conn=server_conn)
                    TRACE('... successfully migrated %r entries', num_rows_imported)
                    _patch_broken_xattrs(fc, server_conn)
                    TRACE('Attempting to import block signatures from %r...', dropbox_db_path)
                    try:
                        sig_counts = sigstore.import_from_dropbox_db(old_conn, ref_checker=fc.hashes_with_references)
                    except Exception:
                        TRACE('Failed to import block sigs from %r!', dropbox_db_path)
                        unhandled_exc_handler()
                    else:
                        TRACE('Successfully imported %d block signatures, %d of which were pruned out', *sig_counts)

            safe_move(tmp, file_cache_path, False)
            TRACE('... successfully migrated %r entries', num_rows_imported)
            safe_remove(dropbox_db_path)
        except Exception:
            safe_remove(tmp)
            raise

    def migrate_migrate_db(migrate_db_path):
        f, tmp = umkstemp(dir=database_dir)
        os.close(f)
        try:
            with open(migrate_db_path, 'rb') as f:
                with closing(FileCache(tmp, keystore=keystore)) as fc:
                    num_rows_imported = fc.import_from_migrate_db(f, server_conn=server_conn)
                    TRACE('... successfully migrated %r entries', num_rows_imported)
                    _patch_broken_xattrs(fc, server_conn)
                    TRACE('Attempting to import block signatures from %r...', migrate_db_path)
                    try:
                        sig_counts = sigstore.import_from_migrate_db(f, ref_checker=fc.hashes_with_references)
                    except Exception:
                        TRACE('Failed to import block sigs from %r!', migrate_db_path)
                        unhandled_exc_handler()
                    else:
                        TRACE('Successfully imported %d block signatures, %d of which were pruned out', *sig_counts)

            safe_move(tmp, file_cache_path, False)
            TRACE('... successfully migrated %r entries', num_rows_imported)
            safe_remove(migrate_db_path)
        except Exception:
            safe_remove(tmp)
            raise

    def migrate_file_cache(path):
        data_plats = filecache_version_1_2_data_plats(dropbox_dir)
        SQLiteBackend.migrate_path(path, None, data_plats, server_conn)
        with closing(FileCache(path)) as old_fc:
            old_fc.copy(file_cache_path, keystore=keystore).close()
        TRACE('... successfully migrated')
        safe_remove(path)

    def file_cache_enc_get_sjid(path, root_ns):
        with closing(FileCache.create_database_connection(path, trevor=keystore.get_database_key(0))) as old_conn:
            if old_conn.execute("SELECT value FROM config WHERE key='filetype'").fetchone()[0] != FileCache.FILETYPE:
                raise Exception('Not a valid filecache database.')
            version = old_conn.execute("SELECT value FROM config WHERE key='version'").fetchone()[0]
            if version >= 3:
                return (old_conn.execute('SELECT last_sjid FROM namespace_map WHERE ns=?', (root_ns,)).fetchone()[0], version != FileCache.VERSION)
            raise Exception('Unsupported filecache version %d' % version)

    def migrate_file_cache_enc(path):
        data_plats = filecache_version_1_2_data_plats(dropbox_dir)
        return SQLiteBackend.migrate_path(path, keystore, data_plats, server_conn)

    migrations = [(_FILE_CACHE_ENC_FILENAME, file_cache_enc_get_sjid, migrate_file_cache_enc),
     (_FILE_CACHE_FILENAME, file_cache_get_sjid, migrate_file_cache),
     (_FILE_CACHE_FILENAME_TEMPLATE % (2,), file_cache2_get_sjid, migrate_file_cache_2),
     (_FILE_CACHE_FILENAME_TEMPLATE % (1,), file_cache1_get_sjid, migrate_file_cache_1),
     (u'dropbox.db', dropbox_db_get_sjid, migrate_dropbox_db),
     (u'migrate.db', migrate_db_get_sjid, migrate_migrate_db)]
    runme = (-2, None)
    for filename, get_sjid, migrate in migrations:
        fullpath = os.path.join(database_dir, filename)
        if os.path.exists(fullpath):
            try:
                sjid, need_migrate = get_sjid(fullpath, root_ns)
            except Exception:
                unhandled_exc_handler()
                sjid = -2

            if sjid > runme[0]:
                if len(runme) > 2:
                    safe_remove(runme[2])
                runme = (sjid, migrate if need_migrate else None, fullpath)
            else:
                TRACE('Bad SJID: %r vs %r killing this database %r', sjid, runme[0], fullpath)
                safe_remove(fullpath)

    if runme[1]:
        _, migrate, fullpath = runme
        if status_controller:
            status_controller.set_status_label('migrating', True)
        TRACE('Attempting to import %r from %r into %r', FileCache, fullpath, _FILE_CACHE_ENC_FILENAME)
        try:
            migrate(fullpath)
        except Exception:
            TRACE('!! Failed to migrate from %r!', fullpath)
            unhandled_exc_handler()
            safe_remove(file_cache_path)
            safe_remove(fullpath)
        finally:
            if status_controller:
                status_controller.set_status_label('migrating', False)

    try:
        del config['attrs']
    except KeyError:
        pass
    except Exception:
        unhandled_exc_handler()

    return runme[1]


def load_dropbox_config(database_dir, keystore, default_dropbox_folder_name = None, seven_default_dropbox = None):
    default_dropbox_folder_name = default_dropbox_folder_name or arch.constants.default_dropbox_folder_name
    seven_default_dropbox_path = seven_default_dropbox or arch.constants.seven_default_dropbox_path
    database_dir = unicode(database_dir)
    remove_exception_handler(handle_corrupted_db)
    try:
        _check_migration_config(database_dir, keystore)
    except Exception:
        unhandled_exc_handler()

    add_exception_handler(handle_corrupted_db)
    config_path = os.path.join(database_dir, _CONFIG_ENC_FILENAME)
    config_db_path = os.path.join(database_dir, _CONFIG_FILENAME)
    TRACE('Using Configuration %r', config_path)
    try:
        new_config = ConfigDict(config_path, keystore=keystore)
        if new_config['config_schema_version'] != CONFIG_SCHEMA_VERSION:
            raise Exception('Database is not current schema version')
    except Exception:
        unhandled_exc_handler()
        safe_remove(config_path)
        safe_remove(config_db_path)
        with new_config_file(database_dir, keystore):
            TRACE('Exception while loading config, clearing file and trying again')
        new_config = ConfigDict(config_path, keystore=keystore)

    try:
        db_path = new_config['dropbox_path']
    except KeyError:
        pass
    except Exception:
        unhandled_exc_handler()
    else:
        try:
            if db_path == default_dropbox_folder_name:
                new_config['dropbox_path'] = seven_default_dropbox_path
        except Exception:
            unhandled_exc_handler()

    return new_config


def load_dropbox_filecache(database_dir, status_controller, server_conn, config, sigstore, root_ns, keystore):
    database_dir = unicode(database_dir)
    remove_exception_handler(handle_corrupted_db)
    try:
        _check_migration_filecache(database_dir, status_controller, server_conn, config, sigstore, root_ns, keystore)
    except Exception:
        unhandled_exc_handler()

    add_exception_handler(handle_corrupted_db)
    try:
        for file_ in os.listdir(database_dir):
            if file_.startswith(_PENDING_DATABASE_PREFIX) or file_.startswith(_UPDATED_DATABASE_PREFIX):
                safe_remove(os.path.join(database_dir, file_))

    except Exception:
        unhandled_exc_handler()

    disable_on_disk_cache = config.get('disable_on_disk_cache', False)
    pending_path = None
    if not disable_on_disk_cache:
        try:
            fd, pending_path = tempfile.mkstemp(dir=database_dir, prefix=_PENDING_DATABASE_PREFIX)
            os.close(fd)
        except Exception:
            unhandled_exc_handler()

    updated_path = None
    if not disable_on_disk_cache:
        try:
            fd, updated_path = tempfile.mkstemp(dir=database_dir, prefix=_UPDATED_DATABASE_PREFIX)
            os.close(fd)
        except Exception:
            unhandled_exc_handler()

    file_cache_filename = os.path.join(database_dir, _FILE_CACHE_ENC_FILENAME)
    TRACE('Using filecache db: %r', file_cache_filename)
    TRACE('Using pending db: %r', pending_path)
    TRACE('Using updated db: %r', updated_path)
    try:
        return FileCache(file_cache_filename, keystore=keystore, pending_database_path=pending_path, updated_database_path=updated_path)
    except Exception:
        unhandled_exc_handler()
        TRACE('Exception while loading file_cache, clearing file and trying again')
        safe_remove(file_cache_filename)
        safe_remove(pending_path)
        safe_remove(updated_path)
        return FileCache(file_cache_filename, keystore=keystore, pending_database_path=pending_path, updated_database_path=updated_path)


def load_dropbox_ideal_tracker(database_dir):
    database_dir = unicode(database_dir)
    ideal_tracker_filename = os.path.join(database_dir, _IDEAL_TRACKER_ENC_FILENAME)
    TRACE('Using idealtracker db: %r', ideal_tracker_filename)
    try:
        return IdealTracker(ideal_tracker_filename)
    except Exception:
        unhandled_exc_handler()
        TRACE('Exception while loading ideal_tracker, clearing file and trying again')
        safe_remove(ideal_tracker_filename)
        return IdealTracker(ideal_tracker_filename)
