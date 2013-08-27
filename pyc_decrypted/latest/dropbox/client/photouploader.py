#Embedded file name: dropbox/client/photouploader.py
import errno
import functools
import os
import threading
import time
import arch
from dropbox.client.photo_constants import CU_QUOTA_UNEARNED
from dropbox.client.photodb import PhotoDb, SYNC_STATUS_DELETED, SYNC_STATUS_DELETED_WAITING, SYNC_STATUS_PENDING, SYNC_STATUS_REPORT_CU_HASH
from dropbox.client.photoimporter import DEFAULT_UPLOAD_LOCATION
from dropbox.build_common import get_build_number
from dropbox.functions import batch, handle_exceptions
from dropbox.native_event import AutoResetEvent
from dropbox.native_threading import NativeCondition
from dropbox.path import ServerPath
from dropbox.threadutils import StoppableThread
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.sync_engine.sync_engine import START, STOP, LIST, HASH

class Proxy(object):

    def do_your_thing(self, *args, **kwargs):
        proxy = arch.photouploader.get_proxy()
        proxy.do_your_thing(*args, **kwargs)


class CuDataFreshnessTracker(object):
    FRESHNESS_REQUIRED = 10
    MAX_TIME_TO_WAIT = 10

    def __init__(self, app):
        self._last_seen = 0
        self.app = app

    def freshen(self):
        self._last_seen = time.time()

    def is_sufficiently_fresh(self):
        return self._last_seen >= time.time() - self.FRESHNESS_REQUIRED

    @handle_exceptions
    def wait_for_list_results(self, event, expected_completion_time):
        if self.is_sufficiently_fresh():
            return
        time_left = expected_completion_time - time.time()
        if time_left <= 0:
            TRACE('Took longer than %s seconds before calling wait_for_list_results(); proceeding', self.MAX_TIME_TO_WAIT)
            return
        event.wait(timeout=time_left)
        if not self.is_sufficiently_fresh():
            TRACE('Waited %s seconds for list call out of total execution time of %s; proceeding', time_left, self.MAX_TIME_TO_WAIT)

    @handle_exceptions
    def demand_freshness(self):
        if self.is_sufficiently_fresh():
            return None
        event = AutoResetEvent()
        too_late = time.time() + self.MAX_TIME_TO_WAIT
        thread = threading.Thread(target=self._force_list_call, name='CUDATA_REFRESHER', args=(event,))
        thread.setDaemon(True)
        thread.start()
        return functools.partial(self.wait_for_list_results, event, too_late)

    def _force_list_call(self, event):
        try:
            sync_engine = self.app.sync_engine
            ret = sync_engine.conn.list(get_build_number(), sync_engine.last_revisions(), sync_engine.get_last_resync_time())
            self.app.photo_uploader.handle_list(ret)
        except Exception:
            unhandled_exc_handler()
        finally:
            event.set()


class PhotoUploader(StoppableThread):
    ROTATION_TYPE_NONE = 'None'
    ROTATION_TYPE_V1 = 'V1'

    def __init__(self, app, path, *n, **kw):
        kw['name'] = 'PHOTOUPLOADER'
        super(PhotoUploader, self).__init__(*n, **kw)
        self.app = app
        self.conn = app.conn
        self.photodb = PhotoDb(os.path.join(path, 'photo.dbx') if path else None, keystore=self.app.keystore)
        self.location = self.photodb.get_config('location')
        self.cu_quota_unearned = max(0, self.photodb.get_config(CU_QUOTA_UNEARNED, 0) or 0)
        self.se = None
        self.app.conn.list_argument_handler.add_handler(self.handle_list_call)
        self.app.ui_kit.add_sync_engine_handler(self.handle_set_sync_engine)
        self.cbs = {START: self.handle_start,
         STOP: lambda : None,
         LIST: self.handle_list,
         HASH: self.handle_hash}
        self.rotation_type = self.ROTATION_TYPE_NONE
        self.exists = self.photodb.exists
        self.freshness_tracker = CuDataFreshnessTracker(self.app)
        self.demand_freshness = self.freshness_tracker.demand_freshness
        self.wakeup_cond = NativeCondition()
        self.deletes = []

    def add_photo(self, details):
        rr_server_path = self.root_relative_server_path(self.se.local_to_server(details.path))
        self.se.dirty_file(details.path)
        self.photodb.add_photo(details.blocklist, rr_server_path, details.cu_hash_8, details.cu_hash_full, details.size, details.mtime)

    @handle_exceptions
    def add_seen_photos(self, *args, **kwargs):
        self.photodb.add_seen_photos(*args, **kwargs)

    @handle_exceptions
    def handle_set_sync_engine(self, sync_engine):
        self.se = sync_engine
        self.root_relative_server_path = self.se.root_relative_server_path
        sync_engine.add_synced_files_callback(self.handle_new_synced_files)
        sync_engine.callbacks.add_handler(self.handle_sync_engine_cb)
        if self.location is None:
            self.location = DEFAULT_UPLOAD_LOCATION
        else:
            self.se.register_tag('camerauploads', self.location)

    @handle_exceptions
    def handle_sync_engine_cb(self, op, *n, **kw):
        try:
            cb = self.cbs[op]
        except KeyError:
            unhandled_exc_handler()
        else:
            cb(*n)

    @handle_exceptions
    def handle_start(self):
        self.reindex()

    @handle_exceptions
    def handle_list(self, ret):
        self.rotation_type = ret.get('cu_rotation_type', self.ROTATION_TYPE_NONE)
        cu_data = ret.get('cu_data')
        if cu_data:
            cu_hashes_full = cu_data.get('cu_hashes_full', [])
            last_cu_id = cu_data.get('last_cu_id', None)
            if cu_hashes_full or last_cu_id is not None:
                TRACE('Photouploader: Adding %d new cu_hashes and/or last_cu_id %r!', len(cu_hashes_full), last_cu_id)
                self.photodb.add_server_photos(cu_hashes_full, last_cu_id)
            location = cu_data.get('location')
            if location:
                self.location = location
                self.photodb.set_config('location', location)
                self.se.register_tag('camerauploads', location)
            cu_quota_unearned = cu_data.get('cu_quota_unearned', None)
            if cu_quota_unearned is not None:
                self.cu_quota_unearned = max(0, cu_quota_unearned)
                self.photodb.set_config(CU_QUOTA_UNEARNED, cu_quota_unearned)
        try:
            self.freshness_tracker.freshen()
        except Exception:
            unhandled_exc_handler()

        if not self.photodb.has_pending():
            return
        last_revisions = self.se.last_revisions()
        for namespace in last_revisions.keys():
            self.photodb.prune_by_sjid(ns=namespace, high_sjid=last_revisions[namespace])

        commit_delete_info = []
        commit_delete_photos = []
        if 'list' in ret:
            for ents in batch(ret['list'], 500):
                for ent in ents:
                    if ret.get('dict_return'):
                        sjid = ent['client_sjid']
                        server_path = u'%s:%s' % (ent['ns_id'], ent['path'])
                        blocklist = ent['blocklist']
                        attrs = ent['attrs']
                    else:
                        sjid, server_path, blocklist, size, mtime, dir_, attrs = ent
                    photo = self.photodb.find_imported(blocklist=blocklist)
                    if photo:
                        TRACE('Photouploader: Photo in photodb was changed: %r', photo)
                        if photo.sync_status == SYNC_STATUS_DELETED or photo.sync_status == SYNC_STATUS_DELETED_WAITING:
                            sp = ServerPath(server_path)
                            if photo.server_path.dirname.lower() == self.root_relative_server_path(sp).dirname.lower():
                                if photo.sync_status == SYNC_STATUS_DELETED_WAITING and photo.sjid != sjid:
                                    report_bad_assumption("DELETED_WAITING sjid doesn't match sjid of listed photo")
                                TRACE('Scheduling commit delete of %r', photo)
                                commit_delete_photos.append(photo)
                                commit_delete_info.append({'ns_id': sp.ns,
                                 'path': sp.rel,
                                 'parent_blocklist': blocklist,
                                 'blocklist': '',
                                 'size': -1,
                                 'mtime': -1,
                                 'is_dir': False,
                                 'parent_attrs': attrs,
                                 'attrs': {},
                                 'target_ns': None})
                                ret['list'].remove(ent)
                            else:
                                TRACE('File we want to commit-delete is in a different directory! Path: %r. No op', self.se.server_to_local(sp))

            if commit_delete_photos:
                self.add_delete(commit_delete_photos, commit_delete_info)
                self.set_wakeup_event()

    @handle_exceptions
    def commit_delete(self, photos, commit_info):
        try:
            TRACE('Photouploader: Committing manual delete: [ %s ]' % '\n  '.join([ '%r' % x for x in commit_info ]))
            ret = self.conn.commit_batch(commit_info)
            if not len(ret['results']) == len(commit_info):
                raise Exception('Bad commit results: %r' % (ret['results'],))
        except Exception:
            unhandled_exc_handler()
            TRACE('Photouploader: commit_delete failed! Trying again 60 seconds!')
            self.add_delete(photos, commit_info)
        else:
            try:
                photos_to_report = [ photo for photo in photos if photo.sync_status == SYNC_STATUS_DELETED ]
                self.photodb.update_status(photos_to_report, SYNC_STATUS_REPORT_CU_HASH)
                self.set_wakeup_event()
                photos_to_remove = [ photo for photo in photos if photo.sync_status == SYNC_STATUS_DELETED_WAITING ]
                self.photodb.add_server_photos((photo.cu_hash_full for photo in photos_to_remove))
                self.photodb.delete(photos_to_remove)
            except Exception:
                unhandled_exc_handler()

    @handle_exceptions
    def handle_list_call(self, args):
        args['last_cu_id'] = self.photodb.last_cu_id

    @handle_exceptions
    def handle_hash(self, changed_files):
        if not self.photodb.has_pending():
            return
        changed_photos = []
        for details in changed_files:
            rr_server_path = self.root_relative_server_path(details.server_path)
            photo = self.photodb.find_imported(server_path=rr_server_path)
            if photo and photo.sync_status == SYNC_STATUS_PENDING and details.blocklist != photo.blocklist:
                TRACE('Photouploader: Photo %r with blocklist %s has new blocklist %s. Marking original as deleted', photo.server_path, photo.blocklist, details.blocklist)
                changed_photos.append(photo)

        if changed_photos:
            self.photodb.update_status(changed_photos, SYNC_STATUS_DELETED)
            self.set_wakeup_event()

    @handle_exceptions
    def handle_new_synced_files(self, new_synced_files):
        if not self.photodb.has_pending():
            return
        photos = []
        nses = {}
        sjids = {}
        for deets in new_synced_files:
            photo = self.photodb.find_imported(blocklist=deets.blocklist)
            if photo:
                rr_server_path = self.root_relative_server_path(deets.server_path)
                if photo.server_path.lower() == rr_server_path.lower() and photo.sync_status == SYNC_STATUS_PENDING:
                    TRACE('Photouploader: %r uploaded.  Scheduling report_cu_hash', photo.server_path)
                    photos.append(photo)
                    nses[photo.blocklist] = deets.server_path.ns
                    sjids[photo.blocklist] = deets.sjid
                else:
                    TRACE('Synced file matches pending blocklist, but status/path was wrong.  Photo:%r, rr_server_path: %r', photo, rr_server_path)

        if photos:
            self.photodb.update_status(photos, SYNC_STATUS_REPORT_CU_HASH, nses=nses, sjids=sjids)
            self.set_wakeup_event()

    @handle_exceptions
    def complete_photos(self):
        try:
            photos = {}
            for photo in self.photodb.pending():
                if photo.sync_status in (SYNC_STATUS_REPORT_CU_HASH, SYNC_STATUS_DELETED):
                    photos[photo.cu_hash_full] = photo

            if not photos:
                return
            TRACE('Photouploader: Reporting %d cu_hashes to server', len(photos))
            hashes = [ (photo.cu_hash_8, photo.cu_hash_full, photo.sjid) for photo in photos.itervalues() ]
            sizes = [ photo.size for photo in photos.itervalues() ]
            ret = self.conn.report_cu_hashes(hashes, sizes)
            exists = ret.get('exists', [])
            to_commit_delete = []
            sjids = {}
            nses = {}
            for item in exists:
                cu_hash_full = item['cu_hash_full']
                photo = photos[cu_hash_full]
                TRACE('Photouploader: attempted to commit existing cu_hash: %r', photo)
                if photo and photo.sync_status == SYNC_STATUS_DELETED and item['sjid']:
                    TRACE('Photouploader: Conflict, must commit a delete for cu_hash_full %r, blocklist %r, %r:%r', cu_hash_full, photo.blocklist, item['ns_id'], item['sjid'])
                    to_commit_delete.append(photo)
                    nses[photo.blocklist] = item['ns_id']
                    sjids[photo.blocklist] = item['sjid']
                    del photos[cu_hash_full]

            if to_commit_delete:
                self.photodb.update_status(to_commit_delete, SYNC_STATUS_DELETED_WAITING, nses, sjids)
            self.photodb.add_server_photos((photo.cu_hash_full for photo in photos.itervalues()))
            self.photodb.delete(photos.itervalues())
        except Exception:
            unhandled_exc_handler()
            TRACE('Photouploader: complete_photos failed!  Will try again in 60 seconds!')

    def reindex(self):
        if not self.photodb.has_pending():
            return
        try:
            photos = self.photodb.pending()
            if photos:
                changed_photos = []
                for photo in photos:
                    TRACE('Photouploader: Reindex - photo in photodb.pending: %r', photo)
                    if photo.sync_status == SYNC_STATUS_PENDING:
                        full_path = unicode(self.se.server_to_local(photo.server_path))
                        try:
                            os.stat(full_path)
                        except OSError as e:
                            if e.errno == errno.ENOENT:
                                TRACE('Photouploader: Photo %r was deleted or renamed, blocklist %s', full_path, photo.blocklist)
                                changed_photos.append(photo)
                            else:
                                unhandled_exc_handler()

                if changed_photos:
                    self.photodb.update_status(changed_photos, SYNC_STATUS_DELETED)
                self.set_wakeup_event()
        except Exception:
            unhandled_exc_handler()

    def add_delete(self, photos, info):
        with self.wakeup_cond:
            self.deletes.append((photos, info))

    def set_wakeup_event(self):
        self.wakeup_cond.notify()

    def run(self):
        timeout = None
        while not self.stopped():
            with self.wakeup_cond:
                self.wakeup_cond.wait(60 if self.deletes else None)
                deletes_snap, self.deletes = self.deletes, []
            for photos, info in deletes_snap:
                self.commit_delete(photos, info)

            if self.photodb.has_pending():
                self.complete_photos()
