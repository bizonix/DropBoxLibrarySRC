#Embedded file name: dropbox/ideal_tracker/sqlite_backend.py
from __future__ import absolute_import, with_statement
import contextlib
import sqlite3
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.sqlite3_helpers import SqliteConnectionHub, create_tables, unique_in_memory_database_uri
from dropbox.trace import TRACE
from .util import Ideal, IdealID, IdealLink, LinkID, to_text

class IdealLinkError(Exception):
    pass


class IdealTrackerBackend(object):
    TABLE_DEFS = []
    TABLE_DEFS.append(('ideal_nodes',
     [('id', 'TEXT PRIMARY KEY NOT NULL'),
      ('is_dir', 'INTEGER NOT NULL'),
      ('identifier', 'TEXT'),
      ('last_update', 'FLOAT NOT NULL')],
     [],
     [('i', ['identifier'])]))
    TABLE_DEFS.append(('ideal_links',
     [('id', 'TEXT'),
      ('parent_ideal_id', 'TEXT NOT NULL'),
      ('child_name', 'TEXT NOT NULL'),
      ('child_ideal_id', 'TEXT NOT NULL'),
      ('active', 'INTEGER NOT NULL'),
      ('unlink_time', 'FLOAT')],
     [],
     [('id', ['id']), ('pi', ['parent_ideal_id', 'active', 'child_name']), ('ci', ['child_ideal_id'])]))

    def __init__(self, database_file = None, **kw):
        if database_file is None:
            database_file = unique_in_memory_database_uri()
        TRACE('IdealTracker connecting to database %r' % database_file)
        self.connhub = SqliteConnectionHub(database_file, detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None, **kw)
        self.create_tables(force=False)

    def _with_cursor(fn):

        def wrapper(self, *args, **kwargs):
            with contextlib.closing(self.connhub.conn().cursor()) as curs:
                return fn(self, curs, *args, **kwargs)

        return wrapper

    @_with_cursor
    def create_tables(self, curs, force = True):
        create_tables(curs, self.TABLE_DEFS, force=force)

    @_with_cursor
    def get_ideal(self, curs, ideal_id):
        curs.execute('SELECT * FROM ideal_nodes WHERE id=?', (to_text(ideal_id),))
        ideal_data = curs.fetchone()
        return ideal_data and Ideal(*ideal_data)

    @_with_cursor
    def get_ideal_by_identifier(self, curs, identifier):
        if identifier is None:
            return
        curs.execute('SELECT * FROM ideal_nodes WHERE identifier=?\n                     ORDER BY last_update DESC', (identifier,))
        ideal_data = curs.fetchone()
        return ideal_data and Ideal(*ideal_data)

    @_with_cursor
    def get_children_ids(self, curs, ideal_id):
        res = curs.execute('SELECT child_name, child_ideal_id FROM ideal_links WHERE\n                           parent_ideal_id=? AND active=1', (to_text(ideal_id),))
        return {row[0]:IdealID(row[1]) for row in res}

    @_with_cursor
    def get_child_id_by_name(self, curs, ideal_id, name):
        if ideal_id is None:
            return
        curs.execute('SELECT child_ideal_id FROM ideal_links WHERE parent_ideal_id=? AND\n                     child_name=? AND active=1', (to_text(ideal_id), name))
        id_data = curs.fetchone()
        return id_data and IdealID(*id_data)

    @_with_cursor
    def get_link_by_name(self, curs, ideal_id, name):
        if ideal_id is None:
            return
        curs.execute('SELECT id, parent_ideal_id, child_name, child_ideal_id FROM ideal_links\n                     WHERE parent_ideal_id=? AND child_name=? AND active=1', (to_text(ideal_id), name))
        link_data = curs.fetchone()
        return link_data and IdealLink(*link_data)

    @_with_cursor
    def get_last_unlink_by_name(self, curs, ideal_id, name):
        if ideal_id is None:
            return
        curs.execute('SELECT id, parent_ideal_id, child_name, child_ideal_id, unlink_time FROM\n                     ideal_links WHERE parent_ideal_id=? AND child_name=? AND active=0 ORDER BY\n                     unlink_time DESC', (to_text(ideal_id), name))
        link_data = curs.fetchone()
        return link_data and IdealLink(*link_data)

    @_with_cursor
    def create_ideal(self, curs, is_dir, parent = None, name = None, identifier = None):
        ideal_id = IdealID()
        curs.execute('INSERT INTO ideal_nodes (id, is_dir, identifier,\n                     last_update) VALUES (?, ?, ?, ?)', (to_text(ideal_id),
         is_dir,
         identifier,
         get_monotonic_time_seconds()))
        if parent is not None and name is not None:
            self._unlink_by_name(curs, parent, name)
            curs.execute('INSERT INTO ideal_links (id, parent_ideal_id, child_name,\n                         child_ideal_id, active) VALUES (?, ?, ?, ?, 1)', (to_text(LinkID()),
             to_text(parent),
             name,
             to_text(ideal_id)))
        return ideal_id

    @_with_cursor
    def update_ideal(self, curs, ideal_id, identifier = None):
        curs.execute('UPDATE ideal_nodes SET identifier=?, last_update=?\n                     WHERE id=?', (identifier, get_monotonic_time_seconds(), to_text(ideal_id)))

    @_with_cursor
    def create_link(self, curs, parent_ideal_id, child_name, child_ideal_id):
        self._unlink_by_name(curs, parent_ideal_id, child_name)
        link_id = LinkID()
        curs.execute('INSERT INTO ideal_links (id, parent_ideal_id, child_name,\n                     child_ideal_id, active) VALUES (?, ?, ?, ?, 1)', (to_text(link_id),
         to_text(parent_ideal_id),
         child_name,
         to_text(child_ideal_id)))
        return link_id

    @_with_cursor
    def move_link(self, curs, link_id, parent_ideal_id, child_name, child_ideal_id):
        curs.execute('UPDATE ideal_links SET active=0, unlink_time=? WHERE id=?', (get_monotonic_time_seconds(), to_text(link_id)))
        self._unlink_by_name(curs, parent_ideal_id, child_name)
        curs.execute('INSERT INTO ideal_links (id, parent_ideal_id, child_name,\n                     child_ideal_id, active) VALUES (?, ?, ?, ?, 1)', (to_text(link_id),
         to_text(parent_ideal_id),
         child_name,
         to_text(child_ideal_id)))

    @_with_cursor
    def unlink_by_name(self, curs, parent_ideal_id, child_name):
        self._unlink_by_name(curs, parent_ideal_id, child_name)

    def _unlink_by_name(self, curs, parent_ideal_id, child_name):
        curs.execute('UPDATE ideal_links SET active=0, unlink_time=? WHERE\n                     parent_ideal_id=? AND child_name=? AND active=1', (get_monotonic_time_seconds(), to_text(parent_ideal_id), child_name))

    @_with_cursor
    def unlink_by_id(self, curs, link_id):
        curs.execute('UPDATE ideal_links SET active=0, unlink_time=? WHERE id=?', (get_monotonic_time_seconds(), to_text(link_id)))

    @_with_cursor
    def get_links_by_child(self, curs, child_ideal_id):
        curs.execute('SELECT id, parent_ideal_id, child_name, child_ideal_id FROM\n                     ideal_links WHERE child_ideal_id=? AND active=1', (to_text(child_ideal_id),))
        links = curs.fetchall()
        return [ IdealLink(*link_data) for link_data in links ]

    @_with_cursor
    def get_last_unlink_by_child(self, curs, child_ideal_id):
        curs.execute('SELECT id, parent_ideal_id, child_name, child_ideal_id, unlink_time FROM\n                     ideal_links WHERE child_ideal_id=? AND active=0 ORDER BY unlink_time\n                     DESC', (to_text(child_ideal_id),))
        link_data = curs.fetchone()
        return link_data and IdealLink(*link_data)
