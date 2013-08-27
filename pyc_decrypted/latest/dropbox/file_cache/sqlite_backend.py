#Embedded file name: dropbox/file_cache/sqlite_backend.py
from __future__ import absolute_import
from Crypto.Random import get_random_bytes
import contextlib
import functools
import itertools
import operator
import pprint
import sqlite3
import time
import cPickle as pickle
from collections import defaultdict
from client_api.hashing import DROPBOX_HASH_LENGTH
from client_api.dropbox_connection import HTTP404Error
from dropbox.attrs import Attributes
from dropbox.functions import frozendict, handle_exceptions_ex, to_signed_64_bit, to_unsigned_64_bit
from dropbox.low_functions import compose, container, propagate_none, wrap_tuple
from dropbox.path import server_path_dirname_unicode, server_path_ns_unicode
from dropbox.platform import platform
from dropbox.sqlite3_helpers import Cursor, MAIN_DB_NAME, SqliteConnectionHub, archive_database, create_tables, dict_like_row, enable_converters, from_db_type, just_the_first, row_factory, sqlite3_get_table_entries, sqlite_escape, to_db_type, unique_in_memory_database_uri, using_row_factory
from dropbox.trace import TRACE, assert_, is_debugging, report_bad_assumption, unhandled_exc_handler
from dropbox.server_path import ServerPath
from .constants import EXTRA_PENDING_DETAILS_COL, IS_CONFLICTED_COL, IS_GUID_CONFLICTED_COL, LOCAL_ATTRS_COL, LOCAL_BLOCKLIST_COL, LOCAL_CTIME_COL, LOCAL_DIR_COL, LOCAL_FILENAME_COL, LOCAL_GUID_COL, LOCAL_GUID_SYNCED_SJID_COL, LOCAL_GUID_SYNCED_GUID_REV_COL, LOCAL_HOST_ID_COL, LOCAL_MACHINE_GUID_COL, LOCAL_MTIME_COL, LOCAL_SIZE_COL, LOCAL_SJID_COL, LOCAL_TIMESTAMP_COL, PARENT_GUID_SYNCED_SERVER_PATH_COL, PARENT_GUID_SYNCED_SJID_COL, PARENT_PATH_COL, SERVER_PATH_COL, UNRECONSTRUCTABLE_COL, UPDATED_ATTRS_COL, UPDATED_BLOCKLIST_COL, UPDATED_DIR_COL, UPDATED_FILENAME_COL, UPDATED_GUID_COL, UPDATED_GUID_REV_COL, UPDATED_HOST_ID_COL, UPDATED_MTIME_COL, UPDATED_SJID_COL, UPDATED_SIZE_COL, UPDATED_TIMESTAMP_COL
from .types import ExtraPendingDetails, ExtraPendingDetailsVersion1
from .util import FlushBefore, check_db_entries, is_valid_filejournal_entry, make_conflicted, server_hash_for_row, serverpath_to_sqlite, sqlite_to_serverpath, why_isnt_valid_filejournal_entry
FILE_JOURNAL_TABLE_NAME = 'file_journal'
FJID_COL = 'id'
HOST_ID_TABLE_NAME = 'host_id'
HOST_ID_NS_ID_COL = 'ns_id'
HOST_ID_SJID_COL = 'sjid'
HOST_ID_HOST_ID_COL = 'host_id'
TIMESTAMP_TABLE_NAME = 'timestamp'
TIMESTAMP_NS_ID_COL = 'ns_id'
TIMESTAMP_SJID_COL = 'sjid'
TIMESTAMP_TIMESTAMP_COL = 'timestamp'
CONFLICTED_TABLE_NAME = 'conflicted'
CONFLICTED_SERVER_PATH_COL = 'con_server_path'
UNRECONSTRUCTABLE_TABLE_NAME = 'unreconstructable'
UNRECONSTRUCTABLE_SERVER_PATH_COL = 'unrecon_server_path'
GUID_JOURNAL_TABLE_NAME = 'guid_journal'
GUID_JOURNAL_GUID_COL = 'guid'
GUID_JOURNAL_MACHINE_GUID_COL = 'machine_guid'
GUID_JOURNAL_SYNCED_GUID_REV_COL = 'synced_guid_rev'
GUID_JOURNAL_SYNCED_SERVER_PATH_COL = 'synced_server_path'
GUID_JOURNAL_SYNCED_SJID_COL = 'synced_sjid'
FILE_JOURNAL_GUID_TABLE_NAME = 'file_journal_guid'
FILE_JOURNAL_GUID_SERVER_PATH_COL = 'server_path'
FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL = 'local_machine_guid'
FILE_JOURNAL_GUID_UPDATED_GUID_COL = 'updated_guid'
FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL = 'updated_guid_rev'
FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL = 'is_guid_conflicted'
DIRECTORY_HOLD_TABLE_NAME = 'directory_hold'
DIRECTORY_HOLD_SERVER_PATH_COL = 'server_path'
DIRECTORY_HOLD_DETAILS_COL = 'details'
GUID_REFERENCES_TABLE_NAME = 'guid_back_references'
GUID_REFERENCES_ID_COL = 'id'
GUID_REFERENCES_SERVER_PATH_COL = 'server_path'
GUID_REFERENCES_DETAILS_SERVER_PATH_COL = 'details_server_path'
GUID_REFERENCES_DETAILS_COL = 'details'
CONFIG_ATTRS = 'attrs'
CONFIG_ATTRS_DATA_PLATS = 'attrs_data_plats'
CONFIG_ATTRS_WHITELIST = 'attrs_whitelist'
CONFIG_FILETYPE = 'filetype'
CONFIG_SELECTIVE_SYNC_IGNORE_LIST = 'selective_sync_ignore_list'
CONFIG_VERSION = 'version'
_SQL_VARS = dict(EXTRA_PENDING_DETAILS_COL=EXTRA_PENDING_DETAILS_COL, IS_CONFLICTED_COL=IS_CONFLICTED_COL, IS_GUID_CONFLICTED_COL=IS_GUID_CONFLICTED_COL, LOCAL_ATTRS_COL=LOCAL_ATTRS_COL, LOCAL_BLOCKLIST_COL=LOCAL_BLOCKLIST_COL, LOCAL_CTIME_COL=LOCAL_CTIME_COL, LOCAL_DIR_COL=LOCAL_DIR_COL, LOCAL_FILENAME_COL=LOCAL_FILENAME_COL, LOCAL_GUID_COL=LOCAL_GUID_COL, LOCAL_GUID_SYNCED_SJID_COL=LOCAL_GUID_SYNCED_SJID_COL, LOCAL_GUID_SYNCED_GUID_REV_COL=LOCAL_GUID_SYNCED_GUID_REV_COL, LOCAL_HOST_ID_COL=LOCAL_HOST_ID_COL, LOCAL_MACHINE_GUID_COL=LOCAL_MACHINE_GUID_COL, LOCAL_MTIME_COL=LOCAL_MTIME_COL, LOCAL_SIZE_COL=LOCAL_SIZE_COL, LOCAL_SJID_COL=LOCAL_SJID_COL, LOCAL_TIMESTAMP_COL=LOCAL_TIMESTAMP_COL, PARENT_GUID_SYNCED_SERVER_PATH_COL=PARENT_GUID_SYNCED_SERVER_PATH_COL, PARENT_GUID_SYNCED_SJID_COL=PARENT_GUID_SYNCED_SJID_COL, PARENT_PATH_COL=PARENT_PATH_COL, SERVER_PATH_COL=SERVER_PATH_COL, UNRECONSTRUCTABLE_COL=UNRECONSTRUCTABLE_COL, UPDATED_ATTRS_COL=UPDATED_ATTRS_COL, UPDATED_BLOCKLIST_COL=UPDATED_BLOCKLIST_COL, UPDATED_DIR_COL=UPDATED_DIR_COL, UPDATED_FILENAME_COL=UPDATED_FILENAME_COL, UPDATED_GUID_COL=UPDATED_GUID_COL, UPDATED_GUID_REV_COL=UPDATED_GUID_REV_COL, UPDATED_HOST_ID_COL=UPDATED_HOST_ID_COL, UPDATED_MTIME_COL=UPDATED_MTIME_COL, UPDATED_SJID_COL=UPDATED_SJID_COL, UPDATED_SIZE_COL=UPDATED_SIZE_COL, UPDATED_TIMESTAMP_COL=UPDATED_TIMESTAMP_COL, FILE_JOURNAL_TABLE_NAME=FILE_JOURNAL_TABLE_NAME, FJID_COL=FJID_COL, HOST_ID_TABLE_NAME=HOST_ID_TABLE_NAME, HOST_ID_NS_ID_COL=HOST_ID_NS_ID_COL, HOST_ID_SJID_COL=HOST_ID_SJID_COL, HOST_ID_HOST_ID_COL=HOST_ID_HOST_ID_COL, TIMESTAMP_TABLE_NAME=TIMESTAMP_TABLE_NAME, TIMESTAMP_NS_ID_COL=TIMESTAMP_NS_ID_COL, TIMESTAMP_SJID_COL=TIMESTAMP_SJID_COL, TIMESTAMP_TIMESTAMP_COL=TIMESTAMP_TIMESTAMP_COL, CONFLICTED_TABLE_NAME=CONFLICTED_TABLE_NAME, CONFLICTED_SERVER_PATH_COL=CONFLICTED_SERVER_PATH_COL, UNRECONSTRUCTABLE_TABLE_NAME=UNRECONSTRUCTABLE_TABLE_NAME, UNRECONSTRUCTABLE_SERVER_PATH_COL=UNRECONSTRUCTABLE_SERVER_PATH_COL, GUID_JOURNAL_TABLE_NAME=GUID_JOURNAL_TABLE_NAME, GUID_JOURNAL_GUID_COL=GUID_JOURNAL_GUID_COL, GUID_JOURNAL_MACHINE_GUID_COL=GUID_JOURNAL_MACHINE_GUID_COL, GUID_JOURNAL_SYNCED_GUID_REV_COL=GUID_JOURNAL_SYNCED_GUID_REV_COL, GUID_JOURNAL_SYNCED_SERVER_PATH_COL=GUID_JOURNAL_SYNCED_SERVER_PATH_COL, GUID_JOURNAL_SYNCED_SJID_COL=GUID_JOURNAL_SYNCED_SJID_COL, FILE_JOURNAL_GUID_TABLE_NAME=FILE_JOURNAL_GUID_TABLE_NAME, FILE_JOURNAL_GUID_SERVER_PATH_COL=FILE_JOURNAL_GUID_SERVER_PATH_COL, FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL=FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL, FILE_JOURNAL_GUID_UPDATED_GUID_COL=FILE_JOURNAL_GUID_UPDATED_GUID_COL, FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL=FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL, FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL=FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL, DIRECTORY_HOLD_TABLE_NAME=DIRECTORY_HOLD_TABLE_NAME, DIRECTORY_HOLD_SERVER_PATH_COL=DIRECTORY_HOLD_SERVER_PATH_COL, DIRECTORY_HOLD_DETAILS_COL=DIRECTORY_HOLD_DETAILS_COL, GUID_REFERENCES_TABLE_NAME=GUID_REFERENCES_TABLE_NAME, GUID_REFERENCES_ID_COL=GUID_REFERENCES_ID_COL, GUID_REFERENCES_SERVER_PATH_COL=GUID_REFERENCES_SERVER_PATH_COL, GUID_REFERENCES_DETAILS_SERVER_PATH_COL=GUID_REFERENCES_DETAILS_SERVER_PATH_COL, GUID_REFERENCES_DETAILS_COL=GUID_REFERENCES_DETAILS_COL)

@handle_exceptions_ex(should_raise=True)
def _db_extract_ns_id(server_path):
    return propagate_none(compose(int, server_path_ns_unicode, unicode), server_path)


@handle_exceptions_ex(should_raise=True)
def _db_parent_guid(epd):
    if epd:
        parent = ExtraPendingDetails.unmarshal(epd).parent
        if parent is not None:
            return propagate_none(str, parent.get('guid'))


@handle_exceptions_ex(should_raise=True)
def _db_parent_guid_rev(epd):
    if epd:
        parent = ExtraPendingDetails.unmarshal(epd).parent
        if parent is not None:
            return propagate_none(str, parent.get('guid_rev'))


def _entries_debugging(entries_iterable):
    for ent in entries_iterable:
        assert_(lambda : is_valid_filejournal_entry(ent), 'Invalid file_journal entry!: %r %r', why_isnt_valid_filejournal_entry(ent), ent)
        yield ent


class FileJournalRowLogic(object):
    IS_NORMAL = 0
    IS_PARENT = 4398046511104L
    IS_ATTRS = 8796093022208L
    FILE_DETAIL_COLS = ('sjid', 'blocklist', 'size', 'mtime', 'dir', 'attrs', 'filename')
    LOCAL_FILE_DETAIL_COLS = [ 'local_%s' % k for k in FILE_DETAIL_COLS ]
    UPDATED_FILE_DETAIL_COLS = [ 'updated_%s' % k for k in FILE_DETAIL_COLS ]
    INSERT_SQL = 'INSERT INTO file_journal (' + ','.join(itertools.chain([SERVER_PATH_COL,
     PARENT_PATH_COL,
     LOCAL_CTIME_COL,
     EXTRA_PENDING_DETAILS_COL], LOCAL_FILE_DETAIL_COLS, UPDATED_FILE_DETAIL_COLS)) + ') VALUES (' + ':server_path,:parent_path,:local_ctime,' + ':extra_pending_details,' + ','.join((':local_%s' % key for key in FILE_DETAIL_COLS)) + ',' + ','.join((':updated_%s' % key for key in FILE_DETAIL_COLS)) + ')'
    UPDATE_SQL = 'UPDATE file_journal SET ' + ','.join(('%s = :%s' % (col, col) for col in itertools.chain(LOCAL_FILE_DETAIL_COLS, UPDATED_FILE_DETAIL_COLS))) + ',extra_pending_details = :extra_pending_details ,local_ctime = :local_ctime WHERE server_path = :server_path'
    DELETE_SQL = 'DELETE FROM file_journal WHERE id = ?'
    RECOMMENDED_BATCH_SIZE = 500

    def __init__(self, mount_points):
        self.to_remove_hash_ref = set()
        self.to_add_hash_ref = set()
        self.to_insert = []
        self.to_update = []
        self.to_delete = []
        self.ns_data_map = defaultdict(int)
        self.mount_table = frozendict(((unicode(sp), target_ns) for sp, target_ns in mount_points))
        self.host_ids_to_insert = {}
        self.host_ids_to_delete = set()
        self.timestamps_to_insert = {}
        self.timestamps_to_delete = set()
        self.server_paths_inserting = set()
        self.new_sp_to_local_guid = []
        self.dead_sp_to_local_guid = []
        self.new_conflicted = []
        self.dead_conflicted = []
        self.new_unreconstructable = []
        self.dead_unreconstructable = []
        self.new_guid_mapping = []

    def _create_accessor(col):

        @staticmethod
        def fn(row):
            try:
                return row[col]
            except (KeyError, IndexError):
                return None

        return fn

    _get_local_machine_guid = _create_accessor(LOCAL_MACHINE_GUID_COL)
    _get_updated_guid = _create_accessor(UPDATED_GUID_COL)
    _get_updated_host_id = _create_accessor(UPDATED_HOST_ID_COL)
    _get_local_host_id = _create_accessor(LOCAL_HOST_ID_COL)
    _get_updated_timestamp = _create_accessor(UPDATED_TIMESTAMP_COL)
    _get_local_timestamp = _create_accessor(LOCAL_TIMESTAMP_COL)
    del _create_accessor

    def __len__(self):
        return sum((len(a) for a in (self.to_insert,
         self.to_update,
         self.to_delete,
         self.to_add_hash_ref,
         self.to_remove_hash_ref,
         self.host_ids_to_insert,
         self.host_ids_to_delete,
         self.timestamps_to_insert,
         self.timestamps_to_delete)))

    @classmethod
    def new_ent(cls, server_path):
        assert_(lambda : server_path == server_path.lower(), 'Input path must be lowered! %r', server_path)
        ent = {SERVER_PATH_COL: server_path,
         PARENT_PATH_COL: server_path_dirname_unicode(server_path),
         LOCAL_CTIME_COL: None,
         EXTRA_PENDING_DETAILS_COL: None,
         UPDATED_HOST_ID_COL: None,
         LOCAL_HOST_ID_COL: None,
         UPDATED_TIMESTAMP_COL: None,
         LOCAL_TIMESTAMP_COL: None,
         LOCAL_MACHINE_GUID_COL: None,
         UNRECONSTRUCTABLE_COL: False,
         IS_CONFLICTED_COL: False,
         IS_GUID_CONFLICTED_COL: False,
         LOCAL_GUID_SYNCED_SJID_COL: None,
         LOCAL_GUID_COL: None,
         UPDATED_GUID_COL: None,
         UPDATED_GUID_REV_COL: None}
        ent.update(((key, None) for key in cls.LOCAL_FILE_DETAIL_COLS))
        ent.update(((key, None) for key in cls.UPDATED_FILE_DETAIL_COLS))
        return ent

    @classmethod
    def clear_updated_details(cls, ent):
        ent[UPDATED_HOST_ID_COL] = None
        ent[UPDATED_TIMESTAMP_COL] = None
        ent.update(((key, None) for key in cls.UPDATED_FILE_DETAIL_COLS))

    @classmethod
    def set_updated_details(cls, ent, deets):
        ent[UPDATED_HOST_ID_COL] = getattr(deets, 'host_id', None)
        ent[UPDATED_TIMESTAMP_COL] = getattr(deets, 'ts', None)
        ent[UPDATED_FILENAME_COL] = deets.server_path.basename
        ent[UPDATED_GUID_COL] = getattr(deets, 'guid', None)
        ent[UPDATED_GUID_REV_COL] = getattr(deets, 'guid_rev', None)
        for i, key in enumerate(cls.FILE_DETAIL_COLS):
            if key == 'filename':
                continue
            dbkey = cls.UPDATED_FILE_DETAIL_COLS[i]
            ent[dbkey] = getattr(deets, key)

    @classmethod
    def clear_local_details(cls, ent):
        ent.update(((k, None) for k in FileJournalRowLogic.LOCAL_FILE_DETAIL_COLS))
        ent[LOCAL_GUID_COL] = None
        ent[LOCAL_MACHINE_GUID_COL] = None
        ent[LOCAL_CTIME_COL] = None
        ent[EXTRA_PENDING_DETAILS_COL] = None
        ent[LOCAL_HOST_ID_COL] = None
        ent[LOCAL_TIMESTAMP_COL] = None

    @classmethod
    def set_pending_details(cls, ent, deets, remote_guid = None, remote_guid_parent_rev = None):
        mount_request = getattr(deets, 'mount_request', None)
        if ent[LOCAL_SJID_COL] is not None:
            if ent[LOCAL_SJID_COL] > 1:
                new_pending_details = ExtraPendingDetails(parent={'sjid': ent[LOCAL_SJID_COL],
                 'host_id': ent.get(LOCAL_HOST_ID_COL),
                 'ts': ent.get(LOCAL_TIMESTAMP_COL),
                 'blocklist': ent[LOCAL_BLOCKLIST_COL],
                 'size': ent[LOCAL_SIZE_COL],
                 'dir': ent[LOCAL_DIR_COL],
                 'attrs': ent[LOCAL_ATTRS_COL],
                 'guid': ent.get(LOCAL_GUID_COL),
                 'guid_rev': ent.get(LOCAL_GUID_SYNCED_GUID_REV_COL)}, mount_request=mount_request)
            else:
                extra = ent[EXTRA_PENDING_DETAILS_COL]
                if extra:
                    new_pending_details = extra.copy(mount_request=mount_request)
                else:
                    assert_(lambda : ent[LOCAL_SJID_COL] == 1, 'if extra was none this had to be a ignored local file! %r', ent)
                    new_pending_details = ExtraPendingDetails(mount_request=mount_request)
        else:
            new_pending_details = ExtraPendingDetails(mount_request=mount_request)
        ent[LOCAL_SJID_COL] = 0
        ent[LOCAL_CTIME_COL] = deets.ctime
        ent[LOCAL_FILENAME_COL] = deets.server_path.basename
        ent[EXTRA_PENDING_DETAILS_COL] = new_pending_details
        ent[LOCAL_HOST_ID_COL] = None
        ent[LOCAL_TIMESTAMP_COL] = None
        ent[LOCAL_MACHINE_GUID_COL] = deets.machine_guid
        ent[LOCAL_GUID_COL] = remote_guid
        ent[LOCAL_GUID_SYNCED_GUID_REV_COL] = remote_guid_parent_rev
        ent[IS_CONFLICTED_COL] = False
        ent[IS_GUID_CONFLICTED_COL] = False
        for attr_key, db_key in itertools.izip(cls.FILE_DETAIL_COLS, cls.LOCAL_FILE_DETAIL_COLS):
            if db_key in (LOCAL_FILENAME_COL, LOCAL_SJID_COL):
                continue
            ent[db_key] = getattr(deets, attr_key)

    @classmethod
    def move_updated_to_local(cls, newent):
        for i, k in enumerate(cls.FILE_DETAIL_COLS):
            if k == 'filename':
                continue
            local_name = cls.LOCAL_FILE_DETAIL_COLS[i]
            updated_name = cls.UPDATED_FILE_DETAIL_COLS[i]
            newent[local_name] = newent[updated_name]
            newent[updated_name] = None

        newent[LOCAL_GUID_COL] = newent.get(UPDATED_GUID_COL)
        newent[LOCAL_GUID_SYNCED_GUID_REV_COL] = newent.get(UPDATED_GUID_REV_COL)
        newent[UPDATED_GUID_COL] = None
        newent[UPDATED_GUID_REV_COL] = None
        newent[EXTRA_PENDING_DETAILS_COL] = None
        newent[LOCAL_MACHINE_GUID_COL] = None
        newent[LOCAL_CTIME_COL] = 0
        newent[LOCAL_HOST_ID_COL] = newent.get(UPDATED_HOST_ID_COL)
        newent[UPDATED_HOST_ID_COL] = None
        newent[LOCAL_TIMESTAMP_COL] = newent.get(UPDATED_TIMESTAMP_COL)
        newent[UPDATED_TIMESTAMP_COL] = None
        if newent[LOCAL_FILENAME_COL] is None:
            newent[LOCAL_FILENAME_COL] = newent[UPDATED_FILENAME_COL]
        newent[UPDATED_FILENAME_COL] = None

    def _assert_hash(self, _hash):
        assert_(lambda : type(_hash) is str, 'Hash is not a str! %r', _hash)
        assert_(lambda : len(_hash) == DROPBOX_HASH_LENGTH, 'Hash is not the correct length! %r', _hash)

    def _add_hash_ref(self, _hash, server_path, how):
        self._assert_hash(_hash)
        toadd = (how, _hash, server_path)
        try:
            self.to_remove_hash_ref.remove(toadd)
        except KeyError:
            self.to_add_hash_ref.add(toadd)

    def _remove_hash_ref(self, _hash, server_path, how):
        self._assert_hash(_hash)
        toadd = (how, _hash, server_path)
        try:
            self.to_add_hash_ref.remove(toadd)
        except KeyError:
            self.to_remove_hash_ref.add(toadd)

    def hashes_added(self):
        return self.new_hashes

    def hashes_removed(self):
        return self.dead_hashes

    def __repr__(self):
        return 'FileJournalRowLogic(to_add_hash_ref=%s, to_remove_hash_ref=%s)' % (pprint.pformat(self.to_add_hash_ref), pprint.pformat(self.to_remove_hash_ref))

    @classmethod
    def _modify_block_refs(cls, single, row):
        if row[LOCAL_BLOCKLIST_COL]:
            for i, _hash in enumerate(row[LOCAL_BLOCKLIST_COL].split(',')):
                single(_hash, row[SERVER_PATH_COL], i)

        if row[LOCAL_ATTRS_COL]:
            for _hash, ref in row[LOCAL_ATTRS_COL].get_blockrefs():
                single(_hash, row[SERVER_PATH_COL], cls.IS_ATTRS | ref)

        extra = row[EXTRA_PENDING_DETAILS_COL]
        if extra:
            parent_details = extra['parent']
            if parent_details:
                if parent_details['blocklist']:
                    for i, _hash in enumerate(parent_details['blocklist'].split(',')):
                        single(_hash, row[SERVER_PATH_COL], cls.IS_PARENT | i)

                if parent_details['attrs']:
                    for _hash, ref in parent_details['attrs'].get_blockrefs():
                        single(_hash, row[SERVER_PATH_COL], cls.IS_ATTRS | cls.IS_PARENT | ref)

    @classmethod
    def check_row(cls, row):
        assert_(lambda : check_db_entries([row]), 'Bad row! %r', row)
        if row[UPDATED_BLOCKLIST_COL] is not None and type(row[UPDATED_BLOCKLIST_COL]) is not str:
            report_bad_assumption('Updated blocklist is not str!! %r' % (row,))
            row[UPDATED_BLOCKLIST_COL] = str(row[UPDATED_BLOCKLIST_COL])
        if row[LOCAL_BLOCKLIST_COL] is not None and type(row[LOCAL_BLOCKLIST_COL]) is not str:
            report_bad_assumption('Local blocklist is not str!! %r' % (row,))
            row[LOCAL_BLOCKLIST_COL] = str(row[LOCAL_BLOCKLIST_COL])

    def _remove_host_id_refs(self, row):
        ns = server_path_ns_unicode(row[SERVER_PATH_COL])
        for host_id_extract, sjid_col in ((self._get_updated_host_id, UPDATED_SJID_COL), (self._get_local_host_id, LOCAL_SJID_COL)):
            old_host_id = host_id_extract(row)
            if old_host_id is not None:
                self.host_ids_to_delete.add((ns, row[sjid_col]))

    def _add_host_id_refs(self, row):
        ns = server_path_ns_unicode(row[SERVER_PATH_COL])
        for host_id_extract, sjid_col in ((self._get_updated_host_id, UPDATED_SJID_COL), (self._get_local_host_id, LOCAL_SJID_COL)):
            new_host_id = host_id_extract(row)
            if new_host_id is not None:
                self.host_ids_to_insert[ns, row[sjid_col]] = new_host_id

    def _remove_timestamp_refs(self, row):
        ns = server_path_ns_unicode(row[SERVER_PATH_COL])
        for timestamp_extract, sjid_col in ((self._get_updated_timestamp, UPDATED_SJID_COL), (self._get_local_timestamp, LOCAL_SJID_COL)):
            old_timestamp = timestamp_extract(row)
            if old_timestamp is not None:
                self.timestamps_to_delete.add((ns, row[sjid_col]))

    def _add_timestamp_refs(self, row):
        ns = server_path_ns_unicode(row[SERVER_PATH_COL])
        for timestamp_extract, sjid_col in ((self._get_updated_timestamp, UPDATED_SJID_COL), (self._get_local_timestamp, LOCAL_SJID_COL)):
            new_timestamp = timestamp_extract(row)
            if new_timestamp is not None:
                self.timestamps_to_insert[ns, row[sjid_col]] = new_timestamp

    def _remove_guid_refs(self, row):
        self.dead_sp_to_local_guid.append((row[SERVER_PATH_COL],))

    def _add_guid_refs(self, row):
        local_machine_guid = self._get_local_machine_guid(row)
        updated_guid = self._get_updated_guid(row)
        updated_guid_rev = row.get(UPDATED_GUID_REV_COL)
        is_guid_conflicted = row.get(IS_GUID_CONFLICTED_COL, False)
        self.new_sp_to_local_guid.append({FILE_JOURNAL_GUID_SERVER_PATH_COL: row[SERVER_PATH_COL],
         FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL: local_machine_guid,
         FILE_JOURNAL_GUID_UPDATED_GUID_COL: updated_guid,
         FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL: updated_guid_rev,
         FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL: is_guid_conflicted})
        if row.get(LOCAL_GUID_COL) is not None and row[LOCAL_SJID_COL] >= 1:
            self.new_guid_mapping.append({GUID_JOURNAL_GUID_COL: row[LOCAL_GUID_COL],
             GUID_JOURNAL_MACHINE_GUID_COL: row[LOCAL_MACHINE_GUID_COL],
             GUID_JOURNAL_SYNCED_GUID_REV_COL: row[LOCAL_GUID_SYNCED_GUID_REV_COL],
             GUID_JOURNAL_SYNCED_SERVER_PATH_COL: row[SERVER_PATH_COL],
             GUID_JOURNAL_SYNCED_SJID_COL: row[LOCAL_SJID_COL]})

    def _with_db_name(self, table_name):
        return '%s.%s' % (MAIN_DB_NAME, table_name)

    def update_entry(self, old_row, new_row):
        assert_(lambda : old_row[SERVER_PATH_COL] == new_row[SERVER_PATH_COL], 'Updating row but server paths are not equal!!! %r vs %r', old_row, new_row)
        self.check_row(old_row)
        self.check_row(new_row)
        self._modify_block_refs(self._remove_hash_ref, old_row)
        self._modify_block_refs(self._add_hash_ref, new_row)
        target_ns = self.mount_table.get(old_row[SERVER_PATH_COL])
        self.ns_data_map[server_path_ns_unicode(old_row[SERVER_PATH_COL])] ^= server_hash_for_row(old_row, target_ns=target_ns) ^ server_hash_for_row(new_row, target_ns=target_ns)
        self.to_update.append(new_row)
        self._remove_guid_refs(old_row)
        self._add_guid_refs(new_row)
        self._remove_host_id_refs(old_row)
        self._add_host_id_refs(new_row)
        self._remove_timestamp_refs(old_row)
        self._add_timestamp_refs(new_row)
        if bool(old_row.get(IS_CONFLICTED_COL)) != bool(new_row.get(IS_CONFLICTED_COL)):
            if new_row.get(IS_CONFLICTED_COL):
                self.new_conflicted.append(old_row[SERVER_PATH_COL])
            else:
                self.dead_conflicted.append(old_row[SERVER_PATH_COL])
        if bool(old_row.get(UNRECONSTRUCTABLE_COL)) != bool(new_row.get(UNRECONSTRUCTABLE_COL)):
            if new_row.get(UNRECONSTRUCTABLE_COL):
                self.new_unreconstructable.append(old_row[SERVER_PATH_COL])
            else:
                self.dead_unreconstructable.append(old_row[SERVER_PATH_COL])
        return self

    def delete_entry(self, old_row):
        self.check_row(old_row)
        self._modify_block_refs(self._remove_hash_ref, old_row)
        target_ns = self.mount_table.get(old_row[SERVER_PATH_COL])
        cs = server_hash_for_row(old_row, target_ns=target_ns)
        self.ns_data_map[server_path_ns_unicode(old_row[SERVER_PATH_COL])] ^= cs
        self.to_delete.append((old_row['id'],))
        self._remove_guid_refs(old_row)
        self._remove_host_id_refs(old_row)
        self._remove_timestamp_refs(old_row)
        self.server_paths_inserting.discard(old_row[SERVER_PATH_COL])
        if old_row.get(IS_CONFLICTED_COL):
            self.dead_conflicted.append(old_row[SERVER_PATH_COL])
        if old_row.get(UNRECONSTRUCTABLE_COL):
            self.dead_unreconstructable.append(old_row[SERVER_PATH_COL])
        return self

    def insert_entry(self, new_row):
        assert_(lambda : new_row[SERVER_PATH_COL] not in self.server_paths_inserting, 'Tried to insert the same path twice! %r', new_row)
        self.check_row(new_row)
        self._modify_block_refs(self._add_hash_ref, new_row)
        target_ns = self.mount_table.get(new_row[SERVER_PATH_COL])
        self.ns_data_map[server_path_ns_unicode(new_row[SERVER_PATH_COL])] ^= server_hash_for_row(new_row, target_ns=target_ns)
        self.to_insert.append(new_row)
        self._add_guid_refs(new_row)
        self._add_host_id_refs(new_row)
        self._add_timestamp_refs(new_row)
        self.server_paths_inserting.add(new_row[SERVER_PATH_COL])
        if new_row.get(IS_CONFLICTED_COL):
            self.new_conflicted.append(new_row[SERVER_PATH_COL])
        if new_row.get(UNRECONSTRUCTABLE_COL):
            self.new_unreconstructable.append(new_row[SERVER_PATH_COL])
        return self

    def execute_da_sql(self, cursor):
        num_statements = 0
        if self.ns_data_map:
            ndm = dict((a for a in self.ns_data_map.iteritems() if a[1]))
            to_update = [ (to_signed_64_bit(to_unsigned_64_bit(ent['checksum']) ^ ndm.pop(ent['ns'])), ent['ns']) for ent in sqlite3_get_table_entries(cursor, 'namespace_map', 'ns', ndm.keys()) ]
            cursor.executemany('INSERT INTO namespace_map (ns, checksum, last_sjid, extra) VALUES (?, ?, -1, NULL)', ((ns, to_signed_64_bit(cs)) for ns, cs in ndm.iteritems()))
            cursor.executemany('UPDATE namespace_map SET checksum = ? WHERE ns = ?', to_update)
        if self.to_update:
            if False and is_debugging():
                for elt in self.to_update:
                    cursor.execute(self.UPDATE_SQL, elt)

            else:
                cursor.executemany(self.UPDATE_SQL, self.to_update)
            num_statements += cursor.rowcount
        if self.to_insert:
            if False and is_debugging():
                for elt in self.to_insert:
                    cursor.execute(self.INSERT_SQL, elt)

            else:
                cursor.executemany(self.INSERT_SQL, self.to_insert)
            num_statements += cursor.rowcount
        if self.to_add_hash_ref:
            with row_factory(cursor, just_the_first):
                max_id = cursor.execute('select max(id) from block_cache').fetchone() or 0
                if is_debugging():
                    for a in self.to_add_hash_ref:
                        cursor.execute('INSERT OR IGNORE INTO block_cache (hash) VALUES (?)', (a[1],))
                        num_statements += cursor.rowcount

                else:
                    cursor.executemany('INSERT OR IGNORE INTO block_cache (hash) VALUES (?)', ((a[1],) for a in self.to_add_hash_ref))
                    num_statements += cursor.rowcount
                self.new_hashes = frozenset(cursor.execute('SELECT hash FROM block_cache WHERE id > ?', (max_id,)))
            if is_debugging():
                for a in self.to_add_hash_ref:
                    cursor.execute('INSERT INTO block_ref (hash_id, fj_id, how) SELECT block_cache.id, file_journal.id, ? FROM block_cache, file_journal WHERE block_cache.hash = ? AND file_journal.server_path = ?', a)
                    num_statements += cursor.rowcount

            else:
                cursor.executemany('INSERT INTO block_ref (hash_id, fj_id, how) SELECT block_cache.id, file_journal.id, ? FROM block_cache, file_journal WHERE block_cache.hash = ? AND file_journal.server_path = ?', self.to_add_hash_ref)
                num_statements += cursor.rowcount
        else:
            self.new_hashes = frozenset()
        if self.to_remove_hash_ref:
            cursor.executemany('DELETE FROM block_ref WHERE how = ? AND hash_id = (select id from block_cache where hash = ?) AND fj_id = (select id from file_journal where server_path = ?)', self.to_remove_hash_ref)
            num_statements += cursor.rowcount
            with row_factory(cursor, just_the_first):
                self.dead_hashes = frozenset(cursor.execute('SELECT block_cache.hash FROM block_cache WHERE NOT EXISTS (SELECT 1 FROM block_ref WHERE block_ref.hash_id = block_cache.id)'))
            cursor.execute('DELETE FROM block_cache WHERE NOT EXISTS (SELECT 1 FROM block_ref WHERE block_ref.hash_id = block_cache.id)')
            num_statements += cursor.rowcount
        else:
            self.dead_hashes = frozenset()
        if self.to_delete:
            cursor.executemany(self.DELETE_SQL, self.to_delete)
            num_statements += cursor.rowcount
        if self.host_ids_to_delete:
            cursor.executemany('DELETE FROM host_id WHERE ns_id = ? AND sjid = ?', self.host_ids_to_delete)
            num_statements += cursor.rowcount
        if self.host_ids_to_insert:
            cursor.executemany('INSERT OR IGNORE INTO host_id (ns_id, sjid, host_id) VALUES (?, ?, ?)', ((ns_id, sjid, host_id) for (ns_id, sjid), host_id in self.host_ids_to_insert.iteritems()))
            num_statements += cursor.rowcount
        if self.timestamps_to_delete:
            cursor.executemany('DELETE FROM timestamp WHERE ns_id = ? AND sjid = ?', self.timestamps_to_delete)
            num_statements += cursor.rowcount
        if self.timestamps_to_insert:
            cursor.executemany('INSERT OR IGNORE INTO timestamp (ns_id, sjid, timestamp) VALUES (?, ?, ?)', ((ns_id, sjid, timestamp) for (ns_id, sjid), timestamp in self.timestamps_to_insert.iteritems()))
            num_statements += cursor.rowcount
        if self.dead_sp_to_local_guid:
            cursor.executemany('DELETE FROM %s WHERE %s = ?' % (self._with_db_name(FILE_JOURNAL_GUID_TABLE_NAME), FILE_JOURNAL_GUID_SERVER_PATH_COL), self.dead_sp_to_local_guid)
            num_statements += cursor.rowcount
        if self.new_sp_to_local_guid:
            sql = '\nINSERT INTO %(FILE_JOURNAL_GUID_TABLE_NAME)s\n(\n%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s,\n%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s,\n%(FILE_JOURNAL_GUID_UPDATED_GUID_COL)s,\n%(FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL)s,\n%(FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL)s\n)\nVALUES\n(\n:%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s,\n:%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s,\n:%(FILE_JOURNAL_GUID_UPDATED_GUID_COL)s,\n:%(FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL)s,\n:%(FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL)s\n)\n'
            sql %= _SQL_VARS
            cursor.executemany(sql, self.new_sp_to_local_guid)
            num_statements += cursor.rowcount
        if self.new_guid_mapping:
            sql = '\nINSERT OR REPLACE INTO %(GUID_JOURNAL_TABLE_NAME)s\n(%(GUID_JOURNAL_GUID_COL)s,\n %(GUID_JOURNAL_MACHINE_GUID_COL)s,\n %(GUID_JOURNAL_SYNCED_SERVER_PATH_COL)s,\n %(GUID_JOURNAL_SYNCED_SJID_COL)s,\n %(GUID_JOURNAL_SYNCED_GUID_REV_COL)s)\nVALUES\n(:%(GUID_JOURNAL_GUID_COL)s,\n :%(GUID_JOURNAL_MACHINE_GUID_COL)s,\n :%(GUID_JOURNAL_SYNCED_SERVER_PATH_COL)s,\n :%(GUID_JOURNAL_SYNCED_SJID_COL)s,\n :%(GUID_JOURNAL_SYNCED_GUID_REV_COL)s)\n'
            sql %= _SQL_VARS
            cursor.executemany(sql, self.new_guid_mapping)
        if self.dead_conflicted:
            cursor.executemany('DELETE FROM conflicted WHERE con_server_path = ?', wrap_tuple(self.dead_conflicted))
        if self.new_conflicted:
            cursor.executemany('INSERT OR IGNORE INTO conflicted (con_server_path) VALUES (?)', wrap_tuple(self.new_conflicted))
        if self.dead_unreconstructable:
            cursor.executemany('DELETE FROM unreconstructable WHERE unrecon_server_path = ?', wrap_tuple(self.dead_unreconstructable))
        if self.new_unreconstructable:
            cursor.executemany('INSERT OR IGNORE INTO unreconstructable (unrecon_server_path) VALUES (?)', wrap_tuple(self.new_unreconstructable))
        return num_statements


class SQLiteBackendCursor(Cursor):
    VERSION = 6
    FILETYPE = u'FileCache'
    TABLE_DEFS = []
    TABLE_DEFS.append((FILE_JOURNAL_TABLE_NAME,
     [('id', 'INTEGER PRIMARY KEY NOT NULL'),
      (SERVER_PATH_COL, 'TEXT NOT NULL UNIQUE'),
      (PARENT_PATH_COL, 'TEXT NOT NULL '),
      (EXTRA_PENDING_DETAILS_COL, 'PENDINGDETAILS2'),
      (LOCAL_SJID_COL, 'INTEGER'),
      (LOCAL_FILENAME_COL, 'TEXT'),
      (LOCAL_BLOCKLIST_COL, 'BYTETEXT'),
      (LOCAL_SIZE_COL, 'INTEGER'),
      (LOCAL_MTIME_COL, 'INTEGER'),
      (LOCAL_CTIME_COL, 'INTEGER'),
      (LOCAL_DIR_COL, 'INTEGER'),
      (LOCAL_ATTRS_COL, 'ATTRIBUTETEXT'),
      (UPDATED_SJID_COL, 'INTEGER'),
      (UPDATED_FILENAME_COL, 'TEXT'),
      (UPDATED_BLOCKLIST_COL, 'BYTETEXT'),
      (UPDATED_SIZE_COL, 'INTEGER'),
      (UPDATED_MTIME_COL, 'INTEGER'),
      (UPDATED_DIR_COL, 'INTEGER'),
      (UPDATED_ATTRS_COL, 'ATTRIBUTETEXT')],
     [],
     [('sp', [SERVER_PATH_COL]), ('ul', [UPDATED_SJID_COL, LOCAL_SJID_COL]), ('pp', [PARENT_PATH_COL])]))
    TABLE_DEFS.append(('namespace_map',
     [('ns', 'INTEGER PRIMARY KEY NOT NULL'),
      ('last_sjid', 'INTEGER NOT NULL'),
      ('checksum', 'INTEGER NOT NULL'),
      ('extra', 'BYTETEXT')],
     [],
     []))
    TABLE_DEFS.append(('mount_table',
     [('server_path', 'TEXT PRIMARY KEY NOT NULL'), ('target_ns', 'INTEGER UNIQUE NOT NULL')],
     [],
     []))
    TABLE_DEFS.append(('block_ref',
     [('hash_id', 'INTEGER NOT NULL'), ('fj_id', 'INTEGER NOT NULL'), ('how', 'INTEGER NOT NULL')],
     ['PRIMARY KEY (hash_id, fj_id, how)'],
     []))
    TABLE_DEFS.append(('block_cache',
     [('id', 'INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL'), ('hash', 'BYTETEXT NOT NULL UNIQUE')],
     [],
     [('hash', ['hash'])]))
    TABLE_DEFS.append(('config',
     [('key', 'TEXT PRIMARY KEY NOT NULL'), ('value', 'BLOB')],
     [],
     []))
    TABLE_DEFS.append((HOST_ID_TABLE_NAME,
     [(HOST_ID_NS_ID_COL, 'INTEGER NOT NULL'), (HOST_ID_SJID_COL, 'INTEGER NOT NULL'), (HOST_ID_HOST_ID_COL, 'INTEGER NOT NULL')],
     ['PRIMARY KEY (%s, %s)' % (HOST_ID_NS_ID_COL, HOST_ID_SJID_COL)],
     []))
    TABLE_DEFS.append((TIMESTAMP_TABLE_NAME,
     [(TIMESTAMP_NS_ID_COL, 'INTEGER NOT NULL'), (TIMESTAMP_SJID_COL, 'INTEGER NOT NULL'), (TIMESTAMP_TIMESTAMP_COL, 'INTEGER NOT NULL')],
     ['PRIMARY KEY (%s, %s)' % (TIMESTAMP_NS_ID_COL, TIMESTAMP_SJID_COL)],
     []))
    TABLE_DEFS.append((CONFLICTED_TABLE_NAME,
     [(CONFLICTED_SERVER_PATH_COL, 'TEXT PRIMARY KEY NOT NULL')],
     [],
     []))
    TABLE_DEFS.append(('unreconstructable',
     [('unrecon_server_path', 'TEXT PRIMARY KEY NOT NULL')],
     [],
     []))
    TABLE_DEFS.append((FILE_JOURNAL_GUID_TABLE_NAME,
     [(FILE_JOURNAL_GUID_SERVER_PATH_COL, 'TEXT PRIMARY KEY NOT NULL'),
      (FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL, 'BYTETEXT UNIQUE'),
      (FILE_JOURNAL_GUID_UPDATED_GUID_COL, 'BYTETEXT'),
      (FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL, 'INTEGER'),
      (FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL, 'INTEGER')],
     [],
     []))
    TABLE_DEFS.append((GUID_JOURNAL_TABLE_NAME,
     [(GUID_JOURNAL_GUID_COL, 'BYTETEXT PRIMARY KEY NOT NULL'),
      (GUID_JOURNAL_MACHINE_GUID_COL, 'BYTETEXT UNIQUE'),
      (GUID_JOURNAL_SYNCED_GUID_REV_COL, 'INTEGER'),
      (GUID_JOURNAL_SYNCED_SERVER_PATH_COL, 'TEXT'),
      (GUID_JOURNAL_SYNCED_SJID_COL, 'INTEGER')],
     [],
     []))
    TABLE_DEFS.append((DIRECTORY_HOLD_TABLE_NAME,
     [(DIRECTORY_HOLD_SERVER_PATH_COL, 'SERVERPATH PRIMARY KEY'), (DIRECTORY_HOLD_DETAILS_COL, 'FASTDETAILS NOT NULL')],
     [],
     []))
    TABLE_DEFS.append((GUID_REFERENCES_TABLE_NAME,
     [(GUID_REFERENCES_ID_COL, 'INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL'),
      (GUID_REFERENCES_SERVER_PATH_COL, 'SERVERPATH NOT NULL'),
      (GUID_REFERENCES_DETAILS_SERVER_PATH_COL, 'SERVERPATH NOT NULL'),
      (GUID_REFERENCES_DETAILS_COL, 'FASTDETAILS NOT NULL')],
     [],
     [('server_path_i', [GUID_REFERENCES_SERVER_PATH_COL])]))

    def __init__(self, *n, **kw):
        super(SQLiteBackendCursor, self).__init__(*n, **kw)
        self.in_trans = False
        self.modified = False

    def set_default_config_state(self):
        self.set_config_key(CONFIG_ATTRS_DATA_PLATS, [])
        self.set_config_key(CONFIG_ATTRS_WHITELIST, {})
        self.set_config_key(CONFIG_FILETYPE, self.FILETYPE)
        self.set_config_key(CONFIG_VERSION, self.VERSION)

    def create_tables(self, force = True):
        create_tables(self, self.TABLE_DEFS, force=force)

    def init_tables(self, force = True):
        self.reset_transient_state()
        try:
            self.get_config_key(CONFIG_FILETYPE)
            self.get_config_key(CONFIG_VERSION)
            self.get_config_key(CONFIG_ATTRS_WHITELIST)
            self.get_config_key(CONFIG_ATTRS_DATA_PLATS)
            if force:
                raise Exception('version was set')
        except KeyError:
            self.set_default_config_state()

    def drop_tables(self, force = True):
        force_str = '' if force else 'IF EXISTS '
        for table_name, _, _, _ in self.TABLE_DEFS:
            self.execute('DROP TABLE %s %s' % (force_str, table_name))

    def clear(self):
        for t in self.TABLE_DEFS:
            self.execute('DELETE FROM %s' % t[0])

        self.set_default_config_state()

    _obj = object()

    def get_config_key(self, key, default = _obj):
        row = self.execute('SELECT value FROM config WHERE key=?', (key,)).fetchone()
        if row:
            return from_db_type(row[0])
        if default is self._obj:
            raise KeyError(key)
        else:
            return default

    def set_config_key(self, key, value):
        self.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', (key, to_db_type(value)))

    def remove_config_key(self, key):
        sql = '\nDELETE FROM config WHERE key = ?\n'
        self.execute(sql, (key,))

    _STANDARD_TABLE_NAMES = dict(FJNAME='one', H1='h1', H2='h2', TS1='ts1', TS2='ts2', SP='sp', GJ='gj', GJ2='gj2')
    A = 'file_journal AS %(FJNAME)s '
    _GET_ENTRIES_TABLE_NAME_META = '\nLEFT OUTER JOIN %(HOST_ID_TABLE_NAME)s as %%(H1)s ON\n(extract_ns_id(%%(FJNAME)s.%(SERVER_PATH_COL)s) =\n %%(H1)s.%(HOST_ID_NS_ID_COL)s AND\n %%(FJNAME)s.%(UPDATED_SJID_COL)s =\n %%(H1)s.%(HOST_ID_SJID_COL)s)\nLEFT OUTER JOIN %(HOST_ID_TABLE_NAME)s as %%(H2)s ON\n(extract_ns_id(%%(FJNAME)s.%(SERVER_PATH_COL)s) =\n %%(H2)s.%(HOST_ID_NS_ID_COL)s AND\n %%(FJNAME)s.%(LOCAL_SJID_COL)s =\n %%(H2)s.%(HOST_ID_SJID_COL)s)\nLEFT OUTER JOIN %(TIMESTAMP_TABLE_NAME)s as %%(TS1)s ON\n(extract_ns_id(%%(FJNAME)s.%(SERVER_PATH_COL)s) =\n %%(TS1)s.%(TIMESTAMP_NS_ID_COL)s AND\n %%(FJNAME)s.%(UPDATED_SJID_COL)s =\n %%(TS1)s.%(TIMESTAMP_SJID_COL)s)\nLEFT OUTER JOIN %(TIMESTAMP_TABLE_NAME)s as %%(TS2)s ON\n(extract_ns_id(%%(FJNAME)s.%(SERVER_PATH_COL)s) =\n %%(TS2)s.%(TIMESTAMP_NS_ID_COL)s AND\n %%(FJNAME)s.%(LOCAL_SJID_COL)s =\n %%(TS2)s.%(TIMESTAMP_SJID_COL)s)\nLEFT OUTER JOIN %(FILE_JOURNAL_GUID_TABLE_NAME)s as %%(SP)s ON\n(%%(FJNAME)s.%(SERVER_PATH_COL)s =\n %%(SP)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s)\nLEFT OUTER JOIN %(GUID_JOURNAL_TABLE_NAME)s as %%(GJ)s ON\n(%%(SP)s.%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s =\n %%(GJ)s.%(GUID_JOURNAL_MACHINE_GUID_COL)s)\nLEFT OUTER JOIN %(GUID_JOURNAL_TABLE_NAME)s as %%(GJ2)s ON\n(parent_guid(%%(FJNAME)s.%(EXTRA_PENDING_DETAILS_COL)s) =\n %%(GJ2)s.%(GUID_JOURNAL_GUID_COL)s)\n' % _SQL_VARS
    _GET_ENTRIES_TABLE_NAME = (A + _GET_ENTRIES_TABLE_NAME_META) % _STANDARD_TABLE_NAMES
    _ENTRY_COLUMNS = ['FJID_COL',
     'SERVER_PATH_COL',
     'PARENT_PATH_COL',
     'LOCAL_ATTRS_COL',
     'LOCAL_BLOCKLIST_COL',
     'LOCAL_CTIME_COL',
     'LOCAL_DIR_COL',
     'LOCAL_FILENAME_COL',
     'LOCAL_MTIME_COL',
     'LOCAL_SIZE_COL',
     'LOCAL_SJID_COL',
     'UPDATED_ATTRS_COL',
     'UPDATED_BLOCKLIST_COL',
     'UPDATED_DIR_COL',
     'UPDATED_FILENAME_COL',
     'UPDATED_MTIME_COL',
     'UPDATED_SIZE_COL',
     'UPDATED_SJID_COL',
     'EXTRA_PENDING_DETAILS_COL',
     'UPDATED_HOST_ID_COL',
     'LOCAL_HOST_ID_COL',
     'UPDATED_TIMESTAMP_COL',
     'LOCAL_TIMESTAMP_COL',
     'LOCAL_MACHINE_GUID_COL',
     'UPDATED_GUID_COL',
     'UPDATED_GUID_REV_COL',
     'IS_CONFLICTED_COL',
     'UNRECONSTRUCTABLE_COL',
     'LOCAL_GUID_COL',
     'LOCAL_GUID_SYNCED_GUID_REV_COL',
     'LOCAL_GUID_SYNCED_SJID_COL',
     'PARENT_GUID_SYNCED_SJID_COL',
     'PARENT_GUID_SYNCED_SERVER_PATH_COL',
     'IS_GUID_CONFLICTED_COL']
    _GET_ENTRIES_COLUMNS_META = '\n%%(FJNAME)s.%(FJID_COL)s as %%(FJID_COL)s,\n%%(FJNAME)s.%(SERVER_PATH_COL)s as %%(SERVER_PATH_COL)s,\n%%(FJNAME)s.%(PARENT_PATH_COL)s as %%(PARENT_PATH_COL)s,\n%%(FJNAME)s.%(LOCAL_ATTRS_COL)s as %%(LOCAL_ATTRS_COL)s,\n%%(FJNAME)s.%(LOCAL_BLOCKLIST_COL)s as %%(LOCAL_BLOCKLIST_COL)s,\n%%(FJNAME)s.%(LOCAL_CTIME_COL)s as %%(LOCAL_CTIME_COL)s,\n%%(FJNAME)s.%(LOCAL_DIR_COL)s as %%(LOCAL_DIR_COL)s,\n%%(FJNAME)s.%(LOCAL_FILENAME_COL)s as %%(LOCAL_FILENAME_COL)s,\n%%(FJNAME)s.%(LOCAL_MTIME_COL)s as %%(LOCAL_MTIME_COL)s,\n%%(FJNAME)s.%(LOCAL_SIZE_COL)s as %%(LOCAL_SIZE_COL)s,\n%%(FJNAME)s.%(LOCAL_SJID_COL)s as %%(LOCAL_SJID_COL)s,\n%%(FJNAME)s.%(UPDATED_ATTRS_COL)s as %%(UPDATED_ATTRS_COL)s,\n%%(FJNAME)s.%(UPDATED_BLOCKLIST_COL)s as %%(UPDATED_BLOCKLIST_COL)s,\n%%(FJNAME)s.%(UPDATED_DIR_COL)s as %%(UPDATED_DIR_COL)s,\n%%(FJNAME)s.%(UPDATED_FILENAME_COL)s as %%(UPDATED_FILENAME_COL)s,\n%%(FJNAME)s.%(UPDATED_MTIME_COL)s as %%(UPDATED_MTIME_COL)s,\n%%(FJNAME)s.%(UPDATED_SIZE_COL)s as %%(UPDATED_SIZE_COL)s,\n%%(FJNAME)s.%(UPDATED_SJID_COL)s as %%(UPDATED_SJID_COL)s,\n%%(FJNAME)s.%(EXTRA_PENDING_DETAILS_COL)s as %%(EXTRA_PENDING_DETAILS_COL)s,\n%%(H1)s.%(HOST_ID_HOST_ID_COL)s as %%(UPDATED_HOST_ID_COL)s,\n%%(H2)s.%(HOST_ID_HOST_ID_COL)s as %%(LOCAL_HOST_ID_COL)s,\n%%(TS1)s.%(TIMESTAMP_TIMESTAMP_COL)s as %%(UPDATED_TIMESTAMP_COL)s,\n%%(TS2)s.%(TIMESTAMP_TIMESTAMP_COL)s as %%(LOCAL_TIMESTAMP_COL)s,\n%%(SP)s.%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s as %%(LOCAL_MACHINE_GUID_COL)s,\n%%(SP)s.%(FILE_JOURNAL_GUID_UPDATED_GUID_COL)s as %%(UPDATED_GUID_COL)s,\n%%(SP)s.%(FILE_JOURNAL_GUID_UPDATED_GUID_REV_COL)s as %%(UPDATED_GUID_REV_COL)s,\nEXISTS(SELECT 1 FROM %(CONFLICTED_TABLE_NAME)s WHERE\n       %(CONFLICTED_TABLE_NAME)s.%(CONFLICTED_SERVER_PATH_COL)s =\n       %%(FJNAME)s.%(SERVER_PATH_COL)s) as %%(IS_CONFLICTED_COL)s,\nEXISTS(SELECT 1 FROM %(UNRECONSTRUCTABLE_TABLE_NAME)s WHERE\n       %(UNRECONSTRUCTABLE_TABLE_NAME)s.%(UNRECONSTRUCTABLE_SERVER_PATH_COL)s =\n       %%(FJNAME)s.%(SERVER_PATH_COL)s) as %%(UNRECONSTRUCTABLE_COL)s,\n%%(GJ)s.%(GUID_JOURNAL_GUID_COL)s as %%(LOCAL_GUID_COL)s,\n%%(GJ)s.%(GUID_JOURNAL_SYNCED_GUID_REV_COL)s as %%(LOCAL_GUID_SYNCED_GUID_REV_COL)s,\n%%(GJ)s.%(GUID_JOURNAL_SYNCED_SJID_COL)s as %%(LOCAL_GUID_SYNCED_SJID_COL)s,\n%%(GJ2)s.%(GUID_JOURNAL_SYNCED_SJID_COL)s as %%(PARENT_GUID_SYNCED_SJID_COL)s,\n%%(GJ2)s.%(GUID_JOURNAL_SYNCED_SERVER_PATH_COL)s as %%(PARENT_GUID_SYNCED_SERVER_PATH_COL)s,\n%%(SP)s.%(FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL)s as %%(IS_GUID_CONFLICTED_COL)s\n' % _SQL_VARS
    _replace = dict(_STANDARD_TABLE_NAMES)
    _replace.update(globals())
    _GET_ENTRIES_COLUMNS = _GET_ENTRIES_COLUMNS_META % _replace
    _SP_COLUMN = 'one.%s' % (SERVER_PATH_COL,)

    def sqlite_cursor(self):
        return FlushBefore(self, self.connection.cursor())

    def _get_entries(self, server_paths_iterable):
        new_curs = self.sqlite_cursor()
        return sqlite3_get_table_entries(new_curs, self._GET_ENTRIES_TABLE_NAME, self._SP_COLUMN, itertools.imap(unicode, server_paths_iterable), row_factory=dict_like_row, desired_columns=self._GET_ENTRIES_COLUMNS)

    def flush_before(fn):

        @functools.wraps(fn)
        def flush_wrapper(self, *n, **kw):
            self.flush()
            return fn(self, *n, **kw)

        return flush_wrapper

    @flush_before
    def get_entries(self, server_paths_iterable, lower = True):
        if lower:
            iter_ = itertools.imap(operator.methodcaller('lower'), server_paths_iterable)
        else:
            iter_ = server_paths_iterable
        if is_debugging():
            if not lower:
                paths = list(iter_)
                assert_(lambda : all((a == a.lower() for a in paths)), 'not all server paths are lowered!! %r', paths)
            else:
                paths = iter_
            return _entries_debugging(self._get_entries(paths))
        else:
            return self._get_entries(iter_)

    @flush_before
    @using_row_factory(dict_like_row)
    def conflicted_get_active(self):
        self.execute('\nSELECT file_journal.* FROM\nconflicted LEFT JOIN file_journal ON\nconflicted.con_server_path = file_journal.server_path\nWHERE file_journal.local_size >= 0\n')
        return [ make_conflicted(ent) for ent in self ]

    @flush_before
    @using_row_factory(None)
    def conflicted_get_count(self):
        self.execute('\nSELECT COUNT(*) FROM conflicted WHERE\nEXISTS(SELECT 1 FROM file_journal WHERE\n       server_path = con_server_path AND\n       local_size >= 0)\n')
        return self.fetchone()[0]

    @flush_before
    @using_row_factory(dict_like_row)
    def conflicted_get_entry(self, server_path, lower = True):
        self.execute('\nSELECT * FROM file_journal WHERE\nserver_path = ? AND\nlocal_size IS NOT NULL AND local_size >= 0 AND\nEXISTS(SELECT 1 FROM conflicted WHERE con_server_path = server_path)', (unicode(server_path.lower() if lower else server_path),))
        return propagate_none(make_conflicted, self.fetchone())

    @using_row_factory(None)
    def _last_revisions(self):
        return dict(self.execute('SELECT ns, last_sjid FROM namespace_map'))

    last_revisions = flush_before(_last_revisions)

    @using_row_factory(None)
    def _get_mount_points(self):
        return [ (ServerPath(sp, lowered=True), target_ns) for sp, target_ns in self.execute('SELECT server_path, target_ns FROM mount_table') ]

    get_mount_points = flush_before(_get_mount_points)

    @flush_before
    def map_machine_guids(self, machine_guids):
        toret = sqlite3_get_table_entries(self, GUID_JOURNAL_TABLE_NAME, GUID_JOURNAL_MACHINE_GUID_COL, (mguid for mguid in machine_guids if mguid is not None))

        def to_guid_obj(ent):
            return container(guid=ent[GUID_JOURNAL_GUID_COL], machine_guid=ent[GUID_JOURNAL_MACHINE_GUID_COL], synced_server_path=ent[GUID_JOURNAL_SYNCED_SERVER_PATH_COL], synced_sjid=ent[GUID_JOURNAL_SYNCED_SJID_COL], synced_guid_rev=ent[GUID_JOURNAL_SYNCED_GUID_REV_COL])

        return dict(((ent[GUID_JOURNAL_MACHINE_GUID_COL], to_guid_obj(ent)) for ent in toret))

    @flush_before
    @using_row_factory(dict_like_row)
    def entry_with_target_ns(self, target_ns):
        self.execute('\nSELECT * FROM file_journal WHERE\nserver_path = (SELECT server_path FROM mount_table WHERE target_ns = ?)', (target_ns,))
        return self.fetchone()

    @flush_before
    @using_row_factory(dict_like_row)
    def get_local_children(self, sp, lower = True):
        self.execute('\nSELECT * FROM file_journal WHERE\nparent_path = ?', (unicode(sp.lower() if lower else sp),))
        return self.fetchall()

    @flush_before
    @using_row_factory(None)
    def has_local_children_not_going_to_be_deleted(self, sp, lower = True):
        self.execute("\nSELECT EXISTS(\nSELECT 1 FROM file_journal WHERE\nparent_path = translate_mount_points_to_ns_roots(?) AND\n/* not being remotely queued for delete\n  !!!: i don't think this condition makes sense (or ever triggers)\n  because if this directory was being queued for delete\n  no child should exist on the server */\n(\nupdated_sjid IS NULL OR updated_size >= 0 OR\nselective_sync_is_ignored_unlocked(server_path) OR\nEXISTS(SELECT 1 FROM unreconstructable where unrecon_server_path = server_path) OR\n(local_sjid IS NOT NULL AND local_sjid = 0 AND\n NOT EXISTS(SELECT 1 FROM conflicted WHERE con_server_path = server_path))\n) AND\n/* exist locally */\nlocal_sjid IS NOT NULL AND\nlocal_size >= 0\n)", (sp.lower() if lower else sp,))
        return self.fetchone()[0]

    @flush_before
    @using_row_factory(None)
    def has_server_children_not_going_to_be_deleted(self, sp, lower = True):
        self.execute('\nSELECT EXISTS(\nSELECT 1 FROM file_journal WHERE\nparent_path = translate_mount_points_to_ns_roots(?) AND\n\n/* not going to be deleted */\n(local_sjid IS NULL OR\n (local_sjid = 0 AND\n  (selective_sync_is_ignored_unlocked(server_path) OR\n   EXISTS(SELECT 1 FROM conflicted WHERE con_server_path = server_path) OR\n   local_size >= 0))) AND\n(\n/* verify it exists on server */\n/* all these cases pick through the row to find the server state */\n(updated_sjid IS NULL AND local_sjid IS NOT NULL AND local_sjid == 0 AND parent_size(extra_pending_details) >= 0) OR\n(updated_sjid IS NULL AND local_sjid IS NOT NULL AND local_sjid > 1 AND local_size >= 0) OR\n\n(updated_sjid IS NOT NULL AND local_sjid IS NULL AND updated_sjid > 1 AND updated_size >= 0) OR\n\n(updated_sjid IS NOT NULL AND local_sjid IS NOT NULL AND updated_sjid > 1 AND local_sjid > 1 AND updated_sjid >= local_sjid AND updated_size >= 0) OR\n(updated_sjid IS NOT NULL AND local_sjid IS NOT NULL AND updated_sjid > 1 AND local_sjid > 1 AND local_sjid > updated_sjid AND local_size >= 0) OR\n\n(updated_sjid IS NOT NULL AND local_sjid IS NOT NULL AND updated_sjid > 1 AND local_sjid = 0 AND (NOT has_parent(extra_pending_details) OR updated_sjid >= parent_sjid(extra_pending_details)) AND updated_size >= 0) OR\n(updated_sjid IS NOT NULL AND local_sjid IS NOT NULL AND updated_sjid > 1 AND local_sjid = 0 AND has_parent(extra_pending_details) AND parent_sjid(extra_pending_details) > updated_sjid AND parent_size(extra_pending_details) >= 0)\n)\n)', (unicode(sp.lower() if lower else sp),))
        return self.fetchone()[0]

    def _with_db_name(self, table_name):
        return '%s.%s' % (MAIN_DB_NAME, table_name)

    def get_holds(self, server_paths, lower = True):
        if lower:
            server_paths = itertools.imap(operator.methodcaller('lower'), server_paths)
        return list(sqlite3_get_table_entries(self, self._with_db_name(DIRECTORY_HOLD_TABLE_NAME), DIRECTORY_HOLD_SERVER_PATH_COL, server_paths, desired_columns=[DIRECTORY_HOLD_DETAILS_COL], row_factory=just_the_first))

    def delete_from_held(self, server_paths, lower = True):
        if lower:
            server_paths = itertools.imap(operator.methodcaller('lower'), server_paths)
        self.executemany('\nDELETE FROM %(table_name)s WHERE\n%(server_path_col)s = ?' % dict(table_name=self._with_db_name(DIRECTORY_HOLD_TABLE_NAME), server_path_col=DIRECTORY_HOLD_SERVER_PATH_COL), ((sp.lower(),) for sp in server_paths))

    def add_to_held(self, details):
        self.executemany('\nINSERT OR REPLACE INTO %(table_name)s (%(server_path_col)s, %(details_col)s)\nVALUES (?, ?)\n' % dict(table_name=self._with_db_name(DIRECTORY_HOLD_TABLE_NAME), server_path_col=DIRECTORY_HOLD_SERVER_PATH_COL, details_col=DIRECTORY_HOLD_DETAILS_COL), ((d.server_path.lower(), d) for d in details))

    @using_row_factory(just_the_first)
    def get_held_descendants(self, server_path, lower = True):
        if lower:
            server_path = server_path.lower()
        self.execute("\nSELECT %(server_path_col)s FROM %(table_name)s WHERE\n%(server_path_col)s LIKE ? ESCAPE '\\'\n" % dict(server_path_col=DIRECTORY_HOLD_SERVER_PATH_COL, table_name=self._with_db_name(DIRECTORY_HOLD_TABLE_NAME)), (sqlite_escape(unicode(server_path)) + u'%',))
        return self.fetchall()

    def clear_held(self):
        self.execute('DELETE FROM %s' % self._with_db_name(DIRECTORY_HOLD_TABLE_NAME))

    def add_guid_references(self, details, guid_to_sp):
        self.executemany('\nINSERT INTO %(table_name)s (%(server_path_col)s, %(details_server_path_col)s, %(details_col)s)\nVALUES (?, ?, ?)\n' % dict(table_name=self._with_db_name(GUID_REFERENCES_TABLE_NAME), server_path_col=GUID_REFERENCES_SERVER_PATH_COL, details_server_path_col=GUID_REFERENCES_DETAILS_SERVER_PATH_COL, details_col=GUID_REFERENCES_DETAILS_COL), ((guid_to_sp[d.guid], d.server_path.lower(), d) for d in details if hasattr(d, 'guid') and d.guid in guid_to_sp))

    def delete_guid_references(self, server_paths):
        self.executemany('\nDELETE FROM %(table_name)s WHERE\n%(details_server_path_col)s = ?\n' % dict(table_name=self._with_db_name(GUID_REFERENCES_TABLE_NAME), details_server_path_col=GUID_REFERENCES_DETAILS_SERVER_PATH_COL), ((sp.lower(),) for sp in server_paths))

    def get_backward_references(self, server_path, lower = True):
        if lower:
            server_path = server_path.lower()
        return list(sqlite3_get_table_entries(self, self._with_db_name(GUID_REFERENCES_TABLE_NAME), GUID_REFERENCES_SERVER_PATH_COL, [server_path], desired_columns=[GUID_REFERENCES_DETAILS_COL], row_factory=just_the_first))

    @flush_before
    def entries_by_local_dropbox_guid_batch(self, guids):
        table_name = '\n%(GUID_JOURNAL_TABLE_NAME)s\nLEFT OUTER JOIN %(FILE_JOURNAL_GUID_TABLE_NAME)s ON\n(%(GUID_JOURNAL_TABLE_NAME)s.%(GUID_JOURNAL_MACHINE_GUID_COL)s =\n %(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s)\n'
        col = '%(GUID_JOURNAL_TABLE_NAME)s.%(GUID_JOURNAL_GUID_COL)s'
        desired_column = '%(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s'
        condition = '\n%(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s\nIS NOT NULL\n'
        table_name %= _SQL_VARS
        col %= _SQL_VARS
        desired_column %= _SQL_VARS
        condition %= _SQL_VARS
        server_paths = sqlite3_get_table_entries(self, table_name, col, guids, row_factory=just_the_first, desired_columns=[desired_column], extra_conditions=condition)
        return self.get_entries(server_paths, lower=False)

    @flush_before
    def entries_by_remote_dropbox_guid_batch(self, guids):
        server_paths = sqlite3_get_table_entries(self, self._with_db_name(FILE_JOURNAL_GUID_TABLE_NAME), FILE_JOURNAL_GUID_UPDATED_GUID_COL, guids, row_factory=just_the_first, desired_columns=[FILE_JOURNAL_GUID_SERVER_PATH_COL])
        return self.get_entries(server_paths, lower=False)

    @flush_before
    def get_pending_guids(self, guids, constructor = None):
        if constructor is None:
            constructor = list
        sql_table = '\n%(GUID_JOURNAL_TABLE_NAME)s\nLEFT OUTER JOIN %(FILE_JOURNAL_GUID_TABLE_NAME)s ON\n(%(GUID_JOURNAL_TABLE_NAME)s.%(GUID_JOURNAL_MACHINE_GUID_COL)s =\n %(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_LOCAL_MACHINE_GUID_COL)s)\nLEFT OUTER JOIN %(FILE_JOURNAL_TABLE_NAME)s ON\n(%(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_SERVER_PATH_COL)s =\n %(FILE_JOURNAL_TABLE_NAME)s.%(SERVER_PATH_COL)s)\n'
        guid_col = '%s.%s' % (GUID_JOURNAL_TABLE_NAME, GUID_JOURNAL_GUID_COL)
        conditions = '\nCOALESCE(%(FILE_JOURNAL_TABLE_NAME)s.%(LOCAL_SJID_COL)s, 1) = 0 AND\nNOT EXISTS(SELECT 1 FROM %(CONFLICTED_TABLE_NAME)s WHERE\n           %(CONFLICTED_TABLE_NAME)s.%(CONFLICTED_SERVER_PATH_COL)s =\n           %(FILE_JOURNAL_TABLE_NAME)s.%(SERVER_PATH_COL)s) AND\nCOALESCE(%(FILE_JOURNAL_GUID_TABLE_NAME)s.%(FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL)s, 0) = 0\n'
        sql_table %= _SQL_VARS
        conditions %= _SQL_VARS
        return constructor(sqlite3_get_table_entries(self, sql_table, guid_col, guids, row_factory=just_the_first, desired_columns=[guid_col], extra_conditions=conditions))

    @flush_before
    def reset_transient_state(self):
        self.execute('DELETE FROM conflicted')
        self.execute('DELETE FROM unreconstructable')
        sql = '\nUPDATE %(FILE_JOURNAL_GUID_TABLE_NAME)s\nSET %(FILE_JOURNAL_GUID_IS_GUID_CONFLICTED_COL)s = 0\n'
        self.execute(sql % _SQL_VARS)

    @flush_before
    def get_unsynced_entries(self):
        sql = '\nSELECT %(COLUMNS)s FROM %(TABLE_NAME)s WHERE\n(%(LOCAL_SJID_COL)s IS NOT NULL AND %(LOCAL_SJID_COL)s = 0) OR\n%(UPDATED_SJID_COL)s IS NOT NULL AND\nnot selective_sync_is_ignored_unlocked(%(SERVER_PATH_COL)s)\n'
        c = self.sqlite_cursor()
        c.row_factory = dict_like_row
        return c.execute(sql % dict(COLUMNS=self._GET_ENTRIES_COLUMNS, TABLE_NAME=self._GET_ENTRIES_TABLE_NAME, LOCAL_SJID_COL=LOCAL_SJID_COL, UPDATED_SJID_COL=UPDATED_SJID_COL, SERVER_PATH_COL=self._SP_COLUMN))

    @flush_before
    def reset_local_ctimes(self):
        sql = '\nUPDATE file_journal SET local_ctime = 0 WHERE\nlocal_size >= 0 AND local_sjid IS NOT NULL\n'
        self.execute(sql)
        c = self.sqlite_cursor()

        def sp_factory(cursor, ent):
            return ServerPath(ent[0], lowered=True)

        c.row_factory = sp_factory
        sql = '\nSELECT server_path from file_journal WHERE\nlocal_ctime = 0 AND local_size >= 0 AND local_sjid IS NOT NULL\n'
        return c.execute(sql)

    @flush_before
    def move_entries_with_new_writable_attrs_to_reconstruct(self):
        sql = '\nUPDATE file_journal SET local_sjid = 1, updated_sjid = local_sjid,\nupdated_dir = local_dir, updated_size = local_size,\nupdated_filename = local_filename, updated_blocklist = local_blocklist,\nupdated_attrs = no_data_plat(local_attrs), updated_mtime = local_mtime\nWHERE local_sjid > 1 AND has_new_writable_attrs(local_attrs) AND\nupdated_sjid IS NULL\n'
        self.execute(sql)
        sql = '\nSELECT %(COLUMNS)s FROM %(TABLE_NAME)s WHERE\none.local_sjid = 1 AND one.updated_sjid > 1 AND\nhas_new_writable_attrs(one.updated_attrs)\n'
        c = self.sqlite_cursor()
        c.row_factory = dict_like_row
        return c.execute(sql % dict(COLUMNS=self._GET_ENTRIES_COLUMNS, TABLE_NAME=self._GET_ENTRIES_TABLE_NAME))

    @flush_before
    def get_directory_ignore_set(self):
        try:
            return frozenset(self.get_config_key(CONFIG_SELECTIVE_SYNC_IGNORE_LIST))
        except KeyError:
            return ()

    @flush_before
    def get_attrs_whitelist(self):
        return self.get_config_key(CONFIG_ATTRS_WHITELIST)

    @flush_before
    def get_attrs_data_plats(self):
        return self.get_config_key(CONFIG_ATTRS_DATA_PLATS)

    @flush_before
    def do_magic_shared_folder_query(self, server_path, to_root):
        server_path = unicode(server_path.lower())
        to_root = unicode(to_root.lower())
        if server_path.endswith(u'/'):
            raise Exception('server path ends with slash: %r' % (server_path,))
        if to_root.endswith(u'/'):
            raise Exception('to_root ends with slash: %r' % (to_root,))
        sql = "\nSELECT %(COLUMNS1)s, %(COLUMNS2)s\nFROM %(TABLE_NAME1)s\nLEFT OUTER JOIN file_journal AS %(FJNAME2)s ON\nrebase_server_path(%(FJNAME1)s.%(SERVER_PATH_COL)s, :from_root, :to_root) =\n%(FJNAME2)s.%(SERVER_PATH_COL)s\n%(TABLE_NAME2)s\nWHERE\n%(FJNAME1)s.%(SERVER_PATH_COL)s LIKE :from_root_like ESCAPE '\\'\nORDER BY length(%(FJNAME1)s.%(SERVER_PATH_COL)s) DESC\n"
        second_table_dict = dict(FJNAME='two', H1='h12', H2='h22', TS1='ts12', TS2='ts22', SP='sp2', GJ='gj22', GJ2='gj222')
        for column in self._ENTRY_COLUMNS:
            second_table_dict[column] = 'two_' + globals()[column]

        sql %= dict(COLUMNS1=self._GET_ENTRIES_COLUMNS, COLUMNS2=self._GET_ENTRIES_COLUMNS_META % second_table_dict, TABLE_NAME1=self._GET_ENTRIES_TABLE_NAME, TABLE_NAME2=self._GET_ENTRIES_TABLE_NAME_META % second_table_dict, FJNAME1='one', FJNAME2='two', SERVER_PATH_COL=SERVER_PATH_COL)
        c = self.sqlite_cursor()
        c.row_factory = dict_like_row
        c.execute(sql, dict(from_root=server_path, from_root_like=sqlite_escape(unicode(server_path)) + '/%', to_root=to_root))
        for row in c:
            row1 = {globals()[a]:row.get(globals()[a]) for a in self._ENTRY_COLUMNS}
            row2 = {globals()[a]:row.get('two_' + globals()[a]) for a in self._ENTRY_COLUMNS}
            yield (row1, row2 if row2[SERVER_PATH_COL] is not None else None)

    @flush_before
    def get_version(self):
        return self.get_config_key(CONFIG_VERSION)

    @flush_before
    def get_tracked_namespaces(self):
        with row_factory(self, just_the_first):
            return self.execute('SELECT ns FROM namespace_map').fetchall()

    @flush_before
    def _upgrade_3_to_4(self, data_plats, attrs_whitelist):
        self.set_config_key('attrs_whitelist', dict(attrs_whitelist))
        self.set_config_key('attrs_data_plats', list(data_plats))
        self.set_config_key(CONFIG_VERSION, self.VERSION)

    @flush_before
    def _upgrade_4_to_5(self, server_conn = None):
        self.create_tables(force=False)
        self.set_config_key(CONFIG_VERSION, self.VERSION)
        if platform == 'win':
            TRACE('Migration: Updating local_ctime column in file_journal')
            self.execute('UPDATE file_journal SET local_ctime = local_mtime WHERE local_ctime != 0')
        if server_conn is None:
            raise Exception('Need server conn!')
        last_revision = {ns:-1 for ns in self.get_tracked_namespaces()}
        while True:
            try:
                ret = server_conn.list_guids(last_revision)
            except HTTP404Error:
                return
            except Exception:
                unhandled_exc_handler()
                time.sleep(10)
                continue

            def stream_events():
                for listed_ent in ret['list']:
                    ns = server_path_ns_unicode(listed_ent['path'])
                    if listed_ent['sjid'] > last_revision[ns]:
                        last_revision[ns] = listed_ent['sjid']
                    yield listed_ent

            sp_to_server_ent = {e['path'].lower():e for e in stream_events()}
            for read_ent in self.get_entries(sp_to_server_ent, lower=False):
                ent = dict(read_ent)
                server_ent = sp_to_server_ent[ent[SERVER_PATH_COL]]
                if ent[LOCAL_SJID_COL] == server_ent['sjid']:
                    ent[LOCAL_MACHINE_GUID_COL] = get_random_bytes(16).encode('hex')
                    ent[LOCAL_GUID_COL] = server_ent['guid']
                    ent[LOCAL_GUID_SYNCED_GUID_REV_COL] = server_ent['guid_rev']
                elif ent[LOCAL_SJID_COL] == 0 and ent[EXTRA_PENDING_DETAILS_COL].parent is not None and ent[EXTRA_PENDING_DETAILS_COL].parent.get('sjid') == server_ent['sjid']:
                    ent[EXTRA_PENDING_DETAILS_COL].parent['guid'] = server_ent['guid']
                    ent[EXTRA_PENDING_DETAILS_COL].parent['guid_rev'] = server_ent['guid_rev']
                elif ent[UPDATED_SJID_COL] == server_ent['sjid']:
                    ent[UPDATED_GUID_COL] = server_ent['guid']
                    ent[UPDATED_GUID_REV_COL] = server_ent['guid_rev']
                else:
                    continue
                self.update_entry(read_ent, ent)

            if not ret.get('more_results', False):
                return

    @flush_before
    def _upgrade_5_to_6(self):
        self.create_tables(force=False)
        self.set_config_key(CONFIG_VERSION, self.VERSION)

    del flush_before

    def _begin(self):
        if self.in_trans:
            raise Exception('Already in a transaction')
        self._new_last_revisions = {}
        self.in_trans = True

    def only_trans(fn):

        @functools.wraps(fn)
        def new_fn(self, *n, **kw):
            if not self.in_trans:
                raise NotImplementedError('Can only call update_entry in a transaction')
            if not hasattr(self, 'fjrl'):
                self.fjrl = FileJournalRowLogic(self._get_mount_points())
            return fn(self, *n, **kw)

        return new_fn

    @only_trans
    def update_entry(self, old_entry, new_entry):
        self.modified = True
        self.fjrl.update_entry(old_entry, new_entry)

    @only_trans
    def delete_entry(self, old_entry):
        self.modified = True
        self.fjrl.delete_entry(old_entry)

    @only_trans
    def insert_entry(self, new_entry):
        self.modified = True
        self.fjrl.insert_entry(new_entry)

    @only_trans
    def update_last_revision(self, ns_id, sj_id):
        self.modified = True
        if self._new_last_revisions.get(ns_id, -1) < sj_id:
            self._new_last_revisions[ns_id] = sj_id

    def _finish(self):
        if not self.in_trans:
            raise Exception('Not in a transaction!')
        if hasattr(self, 'fjrl'):
            self.fjrl.execute_da_sql(self)
            del self.fjrl
        if self._new_last_revisions:
            self.executemany('INSERT OR IGNORE INTO namespace_map (ns, last_sjid, checksum, extra) VALUES (?, ?, 0, NULL)', self._new_last_revisions.iteritems())
            sql = '\nUPDATE namespace_map SET last_sjid = MAX(:last_sjid, last_sjid) WHERE ns = :ns\n'
            self.executemany(sql, (dict(ns=ns, last_sjid=last_sjid) for ns, last_sjid in self._new_last_revisions.iteritems()))
        del self._new_last_revisions
        self.in_trans = False

    def _test_finish(self):
        pass

    def flush(self):
        if not self.in_trans:
            return
        self._finish()
        self._begin()


def rebase_server_path(server_path, from_root, to_root):
    if to_root.endswith(u'/'):
        to_root = to_root[:-1]
    ender = unicode(server_path)[len(from_root):]
    if ender.startswith(u'/'):
        ender = ender[1:]
    toret = u'%s/%s' % (to_root, ender)
    return toret


class SQLiteBackend(object):
    VERSION = SQLiteBackendCursor.VERSION
    FILETYPE = SQLiteBackendCursor.FILETYPE

    @classmethod
    def _sqlite_init(cls):
        converters = [('ATTRIBUTETEXT', Attributes.unmarshal),
         ('PENDINGDETAILS', ExtraPendingDetailsVersion1.unmarshal),
         ('PENDINGDETAILS2', ExtraPendingDetails.unmarshal),
         ('BYTETEXT', str),
         ('SERVERPATH', sqlite_to_serverpath)]
        adapters = [(ServerPath, serverpath_to_sqlite)]
        enable_converters(converters, adapters=adapters)

    def sqlite_cursor(self):
        return self.connhub.conn().cursor()

    def create_database_functions(self, conn):
        conn.create_function('extract_ns_id', 1, _db_extract_ns_id)
        conn.create_function('parent_guid', 1, _db_parent_guid)
        conn.create_function('parent_guid_rev', 1, _db_parent_guid_rev)
        if self.fc is not None:
            conn.create_function('parent_dir', 1, self.fc._db_parent_dir)
            conn.create_function('parent_sjid', 1, self.fc._db_parent_sjid)
            conn.create_function('parent_size', 1, self.fc._db_parent_size)
            conn.create_function('has_parent', 1, self.fc._db_has_parent)
            conn.create_function('translate_mount_points_to_ns_roots', 1, self.fc._db_translate_mount_points_to_ns_roots)
            conn.create_function('no_data_plat', 1, self.fc._db_no_data_plat)
            conn.create_function('is_bad_attr', 1, self.fc._db_is_bad_attr)
            conn.create_function('make_good_attr', 1, self.fc._db_make_good_attr)
            conn.create_function('has_new_writable_attrs', 1, self.fc._db_has_new_writable_attrs)
            conn.create_function('root_relative_server_path', 3, self.fc._db_root_relative_server_path)
            conn.create_function('root_relative_server_path_case', 3, self.fc._db_root_relative_server_path_case)
            conn.create_function('empty_attrs_with_data_plats', 1, self.fc._db_empty_attrs_with_data_plats)
            conn.create_function('create_extra_pending_details', 9, self.fc._db_create_extra_pending_details)
            conn.create_function('selective_sync_is_ignored_unlocked', 1, self.fc._db_selective_sync_is_ignored)
            conn.create_function('rebase_server_path', 3, rebase_server_path)
        file_cache = self.fc

        class SqliteHashAggregate(object):

            def __init__(self):
                self.ns2cs = {}

            @handle_exceptions_ex(should_raise=True)
            def step(self, server_path, extra_pending_details, local_sjid, local_blocklist, local_size, local_dir, local_attrs, updated_sjid, updated_blocklist, updated_size, updated_dir, updated_attrs):
                ns = server_path_ns_unicode(server_path)
                row = {SERVER_PATH_COL: server_path,
                 EXTRA_PENDING_DETAILS_COL: ExtraPendingDetails.unmarshal(extra_pending_details) if extra_pending_details else None,
                 LOCAL_SJID_COL: local_sjid,
                 LOCAL_BLOCKLIST_COL: local_blocklist,
                 LOCAL_SIZE_COL: local_size,
                 LOCAL_DIR_COL: local_dir,
                 LOCAL_ATTRS_COL: None if local_attrs is None else Attributes.unmarshal(local_attrs),
                 UPDATED_SJID_COL: updated_sjid,
                 UPDATED_BLOCKLIST_COL: updated_blocklist,
                 UPDATED_SIZE_COL: updated_size,
                 UPDATED_DIR_COL: updated_dir,
                 UPDATED_ATTRS_COL: None if updated_attrs is None else Attributes.unmarshal(updated_attrs)}
                target_ns = file_cache._mount_table.get(server_path)
                hash_ = server_hash_for_row(row, target_ns=target_ns)
                self.ns2cs[ns] = self.ns2cs.get(ns, 0) ^ hash_

            @handle_exceptions_ex(should_raise=True)
            def finalize(self):
                return buffer(pickle.dumps(self.ns2cs))

        conn.create_aggregate('server_hash', 12, SqliteHashAggregate)

    @classmethod
    def cls_cursor(cls, conn):
        return conn.cursor(SQLiteBackendCursor)

    @classmethod
    def cls_get_config_key(cls, key, cursor):
        return cls.cls_cursor(cursor.connection).get_config_key(key)

    @classmethod
    def cls_set_config_key(cls, key, value, cursor):
        return cls.cls_cursor(cursor.connection).set_config_key(key, value)

    @classmethod
    def cls_get_mount_points(cls, cursor):
        return cls.cls_cursor(cursor.connection).get_mount_points()

    @classmethod
    def cls_last_revisions(cls, cursor):
        return cls.cls_cursor(cursor.connection).last_revisions()

    def __init__(self, fc, database_file, _check_latest = True, **kw):
        self._sqlite_init()
        self.fc = fc
        if database_file is None:
            database_file = unique_in_memory_database_uri()
        self.connhub = SqliteConnectionHub(database_file, detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None, post_create=self.create_database_functions, **kw)
        try:
            with self.transaction() as cursor:
                cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' and name='config'")
                if cursor.fetchone():
                    if cursor.get_config_key(CONFIG_FILETYPE, None) != self.FILETYPE:
                        raise Exception('Not a valid FileCache file')
                else:
                    cursor.execute("\n    SELECT 1 FROM sqlite_master WHERE type = 'table' and name != 'config'\n    ")
                    if cursor.fetchone():
                        raise Exception('Not a valid FileCache file (strange tables)')
                    cursor.create_tables(force=True)
                    cursor.init_tables(force=True)
                if _check_latest:
                    version = cursor.get_config_key(CONFIG_VERSION)
                    if version != self.VERSION:
                        raise Exception('filecache version %d != current (%d) ' % (version, self.VERSION))
        except:
            self.close()
            raise

    def _import(self, other):
        name = 'DB2'
        curs = self.sqlite_cursor()
        with other.attach_to(curs, name) as rname:
            with self.transaction() as trans:
                archive_database(trans.sqlite_cursor(), MAIN_DB_NAME, rname)
        return self

    @contextlib.contextmanager
    def attach_to(self, curs, name = None):
        with self.connhub.attach_to(curs, name=name) as name2:
            yield name2

    def copy(self, fc, database_file, **kw):
        return SQLiteBackend(fc, database_file, **kw)._import(self)

    def close(self):
        try:
            ch = self.connhub
        except AttributeError:
            pass
        else:
            ch.close()

    @classmethod
    def _get_entries(cls, cursor, server_paths_iterable):
        curs = cursor.connection.cursor(SQLiteBackendCursor)
        return curs.get_entries(server_paths_iterable, lower=False)

    @classmethod
    @contextlib.contextmanager
    def transaction_from_conn(cls, conn):
        st = time.time()
        with contextlib.closing(conn.cursor(SQLiteBackendCursor)) as curs:
            with conn:
                curs.execute('BEGIN TRANSACTION')
                curs._begin()
                yield curs
                curs._finish()
                curs._test_finish()
            modified = curs.modified
        if modified:
            TRACE('>> db transaction took %0.3f seconds', time.time() - st)

    def transaction(self):
        return self.transaction_from_conn(self.connhub.conn())

    @classmethod
    def migrate_path(cls, path, keystore, data_plats, server_conn, trevor = None):
        a = cls(None, path, _check_latest=False, keystore=keystore, trevor=trevor)
        try:
            with a.transaction() as trans:
                old_version = trans.get_version()
                if old_version < 3 or old_version > cls.VERSION:
                    raise Exception("Can't import from this version")
                TRACE('Attempting to import from FileCache version %r...', old_version)
                if old_version == 3:
                    config_attrs_whitelist = trans.get_config_key(CONFIG_ATTRS, None) or {}
                    TRACE('Upgrading from 3 to 4: %r, %r', data_plats, config_attrs_whitelist)
                    trans._upgrade_3_to_4(data_plats, config_attrs_whitelist)
                if old_version <= 4:
                    TRACE('Upgrading from 4 to 5')
                    trans._upgrade_4_to_5(server_conn)
                if old_version <= 5:
                    TRACE('Upgrading from 5 to 6')
                    trans._upgrade_5_to_6()
                if keystore is not None:
                    a.connhub.conn().teresa(keystore.get_database_key())
                TRACE('... successfully migrated')
        finally:
            a.close()
