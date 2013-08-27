#Embedded file name: dropbox/ideal_tracker/ideal_tracker.py
import collections
import threading
from dropbox.trace import TRACE
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.platform import platform
from dropbox import fsutil
from .identifiers import Identifier
from .sqlite_backend import IdealTrackerBackend
from .util import ROOT_IDEAL, ROOT_IDEAL_ID, Ideal, IdealID

class IdealTracker(object):

    def __init__(self, database_file = None, **kw):
        if platform == 'win':
            raise Exception('!! Ideals are currently not supported on Windows. Use ObjectIDs instead')
        self.backend = IdealTrackerBackend(database_file, **kw)
        self.lock = threading.RLock()
        self.sync_engine = None

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine

    def _with_lock(fn):

        def wrapper(self, *args, **kwargs):
            with self.lock:
                return fn(self, *args, **kwargs)

        return wrapper

    @_with_lock
    def handle_fs_events(self, events):
        if not isinstance(events, collections.Iterable):
            return
        for evt in events:
            self.handle_fs_event(evt)

    @_with_lock
    def handle_fs_event(self, event):
        TRACE('IdealTracker handling %r', event)
        local_path = self.sync_engine.fs.make_path(event.path)
        if event.type == event.TYPE_CREATE:
            self._handle_create(local_path, is_rename=False)
        elif event.type == event.TYPE_RENAME_TO:
            self._handle_create(local_path, is_rename=True)
        elif event.type == event.TYPE_DELETE:
            self._handle_delete(local_path, is_rename=False)
        elif event.type == event.TYPE_RENAME_FROM:
            self._handle_delete(local_path, is_rename=True)
        else:
            self.update(local_path)

    MAX_RENAME_FROM_ACTIVE_TIME = 15.0
    MAX_CREATE_PERSIST_IDEAL_TIME = 15.0

    @_with_lock
    def _handle_create(self, local_path, is_rename = False):
        TRACE('IdealTracker creating %r with rename=%r', local_path, is_rename)
        if not fsutil.is_exists(self.sync_engine.fs, local_path):
            return
        is_dir = fsutil.is_directory(self.sync_engine.fs, local_path)
        parent_path = local_path.dirname
        name = local_path.basename
        parent_ideal = self.get_ideal_by_path(parent_path, True)
        identifier = Identifier.get(local_path, create=True)
        if is_rename:
            old_ideal = self.backend.get_ideal_by_identifier(identifier)
            TRACE('Found old ideal: %r', old_ideal)
            if old_ideal is not None:
                link_id_to_move = None
                last_unlink = self.backend.get_last_unlink_by_child(old_ideal.id)
                active_links = self.backend.get_links_by_child(old_ideal.id)
                broken_link_ids = []
                for link in active_links:
                    parent_path = self.any_path_for_ideal(link.parent_ideal_id)
                    path_through_link = parent_path.join(link.child_name)
                    if not fsutil.is_exists(self.sync_engine.fs, path_through_link):
                        broken_link_ids.append(link.id)

                TRACE('Broken active links: %r', broken_link_ids)
                if len(broken_link_ids) == 1:
                    link_id_to_move = broken_link_ids[0]
                elif len(broken_link_ids) > 1:
                    link_id_to_move = None
                elif last_unlink and get_monotonic_time_seconds() - last_unlink.unlink_time < self.MAX_RENAME_FROM_ACTIVE_TIME:
                    TRACE('Found %r unlinked recently', last_unlink)
                    link_id_to_move = last_unlink.id
                if link_id_to_move is None:
                    self.backend.create_link(parent_ideal.id, name, old_ideal.id)
                else:
                    self.backend.move_link(link_id_to_move, parent_ideal.id, name, old_ideal.id)
            else:
                self.backend.create_ideal(is_dir, parent_ideal.id, name, identifier)
        else:
            self.backend.unlink_by_name(parent_ideal.id, name)
            ideal_to_steal = None
            if not is_dir:
                last_unlink = self.backend.get_last_unlink_by_name(parent_ideal.id, name)
                if last_unlink and get_monotonic_time_seconds() - last_unlink.unlink_time < self.MAX_CREATE_PERSIST_IDEAL_TIME:
                    potential_ideal = self.backend.get_ideal(last_unlink.child_ideal_id)
                    if not potential_ideal.is_dir:
                        ideal_to_steal = potential_ideal
            if ideal_to_steal is not None:
                self._update_ideal_identifier(ideal_to_steal, identifier)
                self.backend.create_link(parent_ideal.id, name, ideal_to_steal.id)
            else:
                self.backend.create_ideal(is_dir, parent_ideal.id, name, identifier)

    def _update_ideal_identifier(self, ideal, identifier):
        links = self.backend.get_links_by_child(ideal.id)
        for link in links:
            parent_path = self.any_path_for_ideal(link.parent_ideal_id)
            link_path = parent_path.join(link.child_name)
            link_path_identifier = Identifier.get(link_path)
            if link_path_identifier != identifier:
                self.backend.unlink_by_id(link.id)

        self.backend.update_ideal(ideal.id, identifier)

    @_with_lock
    def _handle_delete(self, local_path, is_rename = False):
        parent_path = local_path.dirname
        name = local_path.basename
        parent_ideal = self.get_ideal_by_path(parent_path)
        if parent_ideal is not None:
            self.backend.unlink_by_name(parent_ideal.id, name)
            TRACE('Unlinked %r', local_path)

    @_with_lock
    def any_path_for_ideal(self, ideal, used_link_ids = None):
        if isinstance(ideal, Ideal):
            cur_ideal_id = ideal.id
        elif isinstance(ideal, IdealID):
            cur_ideal_id = ideal
        else:
            raise TypeError('_any_path_for_ideal expected Ideal or IdealID, got %r' % ideal)
        if cur_ideal_id == ROOT_IDEAL_ID:
            return self.sync_engine.fs.make_path(u'/')
        if used_link_ids is None:
            used_link_ids = set()
        links = self.backend.get_links_by_child(cur_ideal_id)
        for link in links:
            if link.id not in used_link_ids:
                used_link_ids.add(link.id)
                path = self.any_path_for_ideal(link.parent_ideal_id, used_link_ids)
                if path is not None:
                    return path.join(link.child_name)

    @_with_lock
    def handle_reindex_file(self, local_path, ideal_cache = None):
        TRACE('Updating IdealTracker for %r', local_path)
        parent_path = local_path.dirname
        name = local_path.basename
        if not fsutil.is_exists(self.sync_engine.fs, local_path):
            parent_ideal = self.get_ideal_by_path(parent_path, force=False)
            if parent_ideal is not None:
                self.backend.unlink_by_name(parent_ideal.id, name)
            return
        is_dir = fsutil.is_directory(self.sync_engine.fs, local_path)
        if ideal_cache and parent_path in ideal_cache:
            parent_ideal = ideal_cache[parent_path]
        else:
            parent_ideal = self.get_ideal_by_path(parent_path, force=True)
            if ideal_cache is not None:
                ideal_cache[parent_path] = parent_ideal
        ideal_to_link = None
        identifier = Identifier.get(local_path)
        if not is_dir:
            old_link = self.backend.get_link_by_name(parent_ideal.id, name)
            if old_link is not None:
                ideal_to_link = self.backend.get_ideal(old_link.child_ideal_id)
                if ideal_to_link.identifier == identifier:
                    return
        if ideal_to_link is None:
            matching_ideal = self.backend.get_ideal_by_identifier(identifier)
            if matching_ideal is not None:
                last_unlink = self.backend.get_last_unlink_by_child(matching_ideal.id)
                if self.any_path_for_ideal(matching_ideal) or last_unlink and get_monotonic_time_seconds() - last_unlink.unlink_time < 86400.0:
                    ideal_to_link = matching_ideal
        if ideal_to_link is None:
            self.backend.create_ideal(is_dir, parent_ideal.id, name, identifier)
        else:
            if identifier != ideal_to_link.identifier:
                self._update_ideal_identifier(ideal_to_link, identifier)
            self.backend.create_link(parent_ideal.id, name, ideal_to_link.id)

    @_with_lock
    def get_ideal_by_path(self, local_path, force = False):
        TRACE('Getting ideal for %r, force=%r', local_path, force)
        if local_path.is_root:
            return ROOT_IDEAL
        cur_ideal = ROOT_IDEAL_ID
        path_components = local_path.split()
        for comp in path_components:
            if not comp:
                continue
            cur_ideal = self.backend.get_child_id_by_name(cur_ideal, comp)

        if not force or cur_ideal is not None:
            return cur_ideal and self.backend.get_ideal(cur_ideal)
        cur_ideal = ROOT_IDEAL_ID
        cur_path = self.sync_engine.fs.make_path(u'/')
        for comp in path_components:
            if not comp:
                continue
            next_ideal = self.backend.get_child_id_by_name(cur_ideal, comp)
            next_path = cur_path.join(comp)
            if next_ideal is None:
                if not fsutil.is_exists(self.sync_engine.fs, next_path):
                    return
                is_dir = fsutil.is_directory(self.sync_engine.fs, next_path)
                next_identifier = Identifier.get(next_path)
                existing_ideal = self.backend.get_ideal_by_identifier(next_identifier)
                if existing_ideal is not None and self.any_path_for_ideal(existing_ideal) is not None:
                    self.backend.create_link(cur_ideal, comp, existing_ideal.id)
                    next_ideal = existing_ideal.id
                else:
                    next_ideal = self.backend.create_ideal(is_dir, parent=cur_ideal, name=comp, identifier=next_identifier)
            cur_ideal = next_ideal
            cur_path = next_path

        return self.backend.get_ideal(cur_ideal)

    def get_ideals_batch(self, paths, force = False):
        return {path:self.get_ideal(path, force) for path in paths}

    @_with_lock
    def update(self, local_path):
        ideal = self.get_ideal_by_path(local_path, True)
        if ideal is None:
            return
        identifier = Identifier.get(local_path, True)
        if identifier is not None and identifier != ideal.identifier:
            TRACE('Updating Ideal identifier for %r from %r to %r', local_path, ideal.identifier, identifier)
            self.backend.update_ideal(ideal.id, identifier)

    def _print_mapping(self, path):
        if isinstance(path, basestring):
            path = self.sync_engine.fs.make_path(path)
        ideal = self.get_ideal_by_path(path)
        TRACE('%r maps to %r', path, ideal)
