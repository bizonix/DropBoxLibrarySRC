#Embedded file name: dropbox/client/status.py
from __future__ import absolute_import
import functools
import threading
from collections import OrderedDict
from dropbox.callbacks import Handler
from dropbox.debugging import easy_repr
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.common.progress import ACTION_DOWNLOADING, ACTION_INDEXING, ACTION_UPLOADING, get_summary_label, TransferStatus, BaseTransferStatus
from ui.common.status import format_failure_label, StatusStrings

class StatusController(object):
    LABEL_IMPORTING = 'importing'
    LABEL_UPDATING = 'updating'
    LABEL_MIGRATING = 'migrating'
    LABEL_MOVING = 'moving'
    LABEL_PAUSING = 'pausing'
    LABEL_PAUSED = 'paused'
    LABEL_STARTING = 'starting'
    LABEL_INITIALIZING = 'initializing'
    LABEL_PRELINK = 'waiting_for_link'
    LABEL_REINDEXING = 'reindexing'
    LABEL_SELSYNC = 'selsync'
    LABEL_LISTING = 'listing'
    LABEL_LOW_DISK_SPACE = 'low_disk_space'
    LABEL_CANT_MOUNT = 'cant_mount_dropbox'
    LABEL_SSL_ERROR = 'ssl_error'
    LABEL_CONNECTING = 'connecting'
    LABEL_SYNCING = 'syncing'
    LABEL_HASH_STATUS = 'hash_status'
    LABEL_HASH_FAILURE = 'hash_failure'
    LABEL_DOWNLOAD_STATUS = 'download_status'
    LABEL_DOWNLOAD_FAILURE = 'download_failure'
    LABEL_UPLOAD_STATUS = 'upload_status'
    LABEL_UPLOAD_FAILURE = 'upload_failure'
    LABEL_BLANK = 'nil'
    TRANSFER_LABELS = set((LABEL_HASH_STATUS,
     LABEL_HASH_FAILURE,
     LABEL_DOWNLOAD_STATUS,
     LABEL_DOWNLOAD_FAILURE,
     LABEL_UPLOAD_STATUS,
     LABEL_UPLOAD_FAILURE))
    ALL_LABELS = (LABEL_IMPORTING,
     LABEL_UPDATING,
     LABEL_MIGRATING,
     LABEL_MOVING,
     LABEL_PAUSING,
     LABEL_PAUSED,
     LABEL_STARTING,
     LABEL_INITIALIZING,
     LABEL_PRELINK,
     LABEL_REINDEXING,
     LABEL_SELSYNC,
     LABEL_LISTING,
     LABEL_LOW_DISK_SPACE,
     LABEL_CANT_MOUNT,
     LABEL_SSL_ERROR,
     LABEL_CONNECTING,
     LABEL_SYNCING,
     LABEL_HASH_STATUS,
     LABEL_HASH_FAILURE,
     LABEL_DOWNLOAD_STATUS,
     LABEL_DOWNLOAD_FAILURE,
     LABEL_UPLOAD_STATUS,
     LABEL_UPLOAD_FAILURE)

    def __repr__(self):
        return easy_repr(self, 'status_labels', 'status_callbacks', 'upload_status', 'download_status', 'hash_status')

    def __init__(self, dropbox_app):
        self.dropbox_app = dropbox_app
        self.lock = threading.RLock()
        self.lansync = False
        self.selsync = False
        self.initial_hash = False
        self._linked = False
        self._mounted = False
        self.status_labels = OrderedDict()
        self.secondary_status_labels = OrderedDict()
        self._clear_labels()
        self._clear_secondary_labels()
        self.status_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.add_status_callback = self.status_callbacks.add_handler
        _init_transfer_status = functools.partial(TransferStatus, self.transfer_status_update, self.lock)
        self.upload_status = _init_transfer_status(ACTION_UPLOADING)
        self.download_status = _init_transfer_status(ACTION_DOWNLOADING)
        self.hash_status = _init_transfer_status(ACTION_INDEXING)
        self.secondary_upload_status = None
        self.secondary_download_status = None
        self.secondary_hash_status = None
        self.allow_secondary_status = False
        self.dropbox_app.mbox.on_secondary_link.add_handler(self.on_secondary_link)

    def on_secondary_link(self, linked):
        if linked:
            self.allow_secondary_status = True
        else:
            self.allow_secondary_status = False
        self._clear_secondary_labels()
        with self.lock:
            self.secondary_upload_status = None
            self.secondary_download_status = None
            self.secondary_hash_status = None
        self.status_callbacks.run_handlers()

    def transfer_status_update(self, *args, **kwargs):
        if self.dropbox_app.mbox.is_secondary:
            hash_status, upload_status, download_status = self.get_transfer_statuses_serialized()
            self.dropbox_app.mbox.primary.set_secondary_transfer_status(hash_status=hash_status, upload_status=upload_status, download_status=download_status)
        self.status_callbacks.run_handlers(*args, **kwargs)

    def get_transfer_statuses_serialized(self):
        return (BaseTransferStatus(other_transfer_status=status) for status in (self.hash_status, self.upload_status, self.download_status))

    def _clear_labels(self):
        with self.lock:
            for label in self.ALL_LABELS:
                self.status_labels[label] = False

    def _clear_secondary_labels(self):
        with self.lock:
            for label in self.ALL_LABELS:
                self.secondary_status_labels[label] = False

    def is_true(self, status):
        with self.lock:
            return any((bool(self.status_labels.get(status)), bool(self.secondary_status_labels.get(status))))

    def set_secondary_transfer_status(self, upload_status, download_status, hash_status):
        with self.lock:
            self.secondary_upload_status = upload_status
            self.secondary_download_status = download_status
            self.secondary_hash_status = hash_status
            if self.secondary_download_status.file_count or self.secondary_upload_status.file_count or self.secondary_hash_status.file_count:
                TRACE('Received transfer statuses from secondary client!\n%r\n%r\n%r', self.secondary_download_status, self.secondary_upload_status, self.secondary_hash_status)
        self.status_callbacks.run_handlers()

    def try_set_status_label(self, label, state, clear_previous = False, fail_if_set = None, fail_if_not_set = None):
        return self.set_status_labels(_clear_previous=clear_previous, _fail_if_set=fail_if_set, _fail_if_not_set=fail_if_not_set, **{label: state})

    def set_status_labels(self, _clear_previous = False, _fail_if_set = None, _fail_if_not_set = None, set_secondary = False, **labels_and_states):
        changed = False
        with self.lock:
            if _clear_previous:
                TRACE('Clearing %sstatus labels', 'secondary ' if set_secondary else '')
                self._clear_secondary_labels() if set_secondary else self._clear_labels()
            if _fail_if_set and any((bool(self.status_labels.get(state)) for state in _fail_if_set)):
                return False
            if _fail_if_not_set and not all((bool(self.status_labels.get(state)) for state in _fail_if_not_set)):
                return False
            status_labels_to_set = self.secondary_status_labels if set_secondary else self.status_labels
            for label, state in labels_and_states.iteritems():
                if state != bool(status_labels_to_set.get(label)):
                    changed = True
                    if state:
                        TRACE("Setting %sstatus label: '%s'", 'secondary ' if set_secondary else '', label)
                        status_labels_to_set[label] = True
                    else:
                        TRACE("Clearing %sstatus label: '%s'", 'secondary ' if set_secondary else '', label)
                        status_labels_to_set[label] = False

            self.dropbox_app.mbox.set_status_label(_clear_previous=_clear_previous, **labels_and_states)
        if changed:
            self.status_callbacks.run_handlers()
        return True

    def set_status_label(self, label, state, clear_previous = False):
        assert label != self.LABEL_BLANK, 'Should not set the blank label.'
        self.set_status_labels(_clear_previous=clear_previous, **{label: state})

    def is_mounted(self):
        return self._mounted

    def set_mounted(self, value):
        changed = False
        with self.lock:
            if value != self._mounted:
                self._mounted = value
                changed = True
        if changed:
            self.status_callbacks.run_handlers()

    def is_linked(self):
        return self._linked

    def set_linked(self, value):
        changed = False
        with self.lock:
            if value != self._linked:
                self._linked = value
                changed = True
        if changed:
            self.status_callbacks.run_handlers()

    def set_initial_selective_sync(self, on):
        changed = False
        with self.lock:
            if on != self.selsync:
                self.selsync = on
                changed = True
        if changed:
            self.status_callbacks.run_handlers()

    def set_lan_sync(self, on):
        changed = False
        with self.lock:
            if on != self.lansync:
                self.lansync = on
                changed = True
        if changed:
            self.status_callbacks.run_handlers()

    def set_initial_hash(self, on):
        changed = False
        with self.lock:
            if on != self.initial_hash:
                self.initial_hash = on
                changed = True
        if changed:
            self.status_callbacks.run_handlers()

    def last_hash_done(self):
        return max(self.upload_status.last_hash_done, self.download_status.last_hash_done)

    @classmethod
    def _get_label(cls, label):
        assert label != cls.LABEL_SYNCING, 'Should not be obtained from here.'
        return getattr(StatusStrings, label)

    def _get_combined_statuses(self):
        if self.allow_secondary_status and self.secondary_hash_status and self.secondary_upload_status and self.secondary_upload_status:
            assert self.hash_status.verb == self.secondary_hash_status.verb and self.upload_status.verb == self.secondary_upload_status.verb and self.download_status.verb == self.secondary_download_status.verb

            def merge_samples(left, right):
                left, right = left or {}, right or {}
                return {k:left.get(k, []) + right.get(k, []) for k in set(left) | set(right)}

            hash, upload, download = [ TransferStatus(lock=p.lock, trigger_update=p.trigger_update, verb=p.verb, cant_sync=p.cant_sync or s.cant_sync, failures=(p.failures or 0) + (s.failures or 0), file_count=(p.file_count or 0) + (s.file_count or 0), total_size=(p.total_size or 0) + (s.total_size or 0), remaining=(p.remaining or 0) + (s.remaining or 0), speed=(p.speed or 0) + (s.speed or 0), speed_samples=merge_samples(p.speed_samples, s.speed_samples), hash_speed=(p.hash_speed or 0) + (s.hash_speed or 0)) for p, s in ((self.hash_status, self.secondary_hash_status), (self.upload_status, self.secondary_upload_status), (self.download_status, self.secondary_download_status)) ]
        else:
            hash, upload, download = [self.hash_status, self.upload_status, self.download_status]
        return (hash, upload, download)

    def _get_labels(self):
        labels = OrderedDict()

        def _mark_label(label):
            labels[label] = self._get_label(label)

        if self.status_labels.get(self.LABEL_IMPORTING):
            _mark_label(self.LABEL_IMPORTING)
        for label in (self.LABEL_UPDATING,
         self.LABEL_MIGRATING,
         self.LABEL_MOVING,
         self.LABEL_PAUSED,
         self.LABEL_PAUSING):
            if self.status_labels.get(label):
                _mark_label(label)
                return labels

        if self.status_labels.get(self.LABEL_STARTING):
            _mark_label(self.LABEL_STARTING)
            if self.selsync and self.status_labels.get(self.LABEL_LISTING):
                _mark_label(self.LABEL_LISTING)
            return labels
        combined_hash, combined_upload, combined_download = self._get_combined_statuses()
        hash_status, hash_files, hash_remaining = combined_hash.get_label()
        upload_status, upload_files, upload_remaining = combined_upload.get_label()
        download_status, download_files, download_remaining = combined_download.get_label(self.lansync)
        for label, is_true in self.status_labels.iteritems():
            if label in self.TRANSFER_LABELS or not is_true:
                continue
            _mark_label(label)

        if hash_status or upload_status or download_status:
            labels[self.LABEL_SYNCING] = get_summary_label((hash_remaining, upload_remaining, download_remaining), (hash_files, upload_files, download_files))
        if hash_status:
            if not (self.hash_status.cant_sync and self.hash_status.failures is not None and self.hash_status.failures == self.hash_status.file_count == 1):
                labels[self.LABEL_HASH_STATUS] = hash_status
            if self.hash_status.cant_sync:
                labels[self.LABEL_HASH_FAILURE] = format_failure_label(*self.hash_status.cant_sync)
        if upload_status:
            labels[self.LABEL_UPLOAD_STATUS] = upload_status
            if self.upload_status.cant_sync:
                labels[self.LABEL_UPLOAD_FAILURE] = format_failure_label(*self.upload_status.cant_sync)
        if download_status and not self.initial_hash:
            labels[self.LABEL_DOWNLOAD_STATUS] = download_status
            if self.download_status.cant_sync:
                labels[self.LABEL_DOWNLOAD_FAILURE] = format_failure_label(*self.download_status.cant_sync)
        return labels

    def get_labels(self):
        with self.lock:
            labels = self._get_labels()
            if labels:
                return labels
            if self._linked:
                return {self.LABEL_BLANK: self._get_label(self.LABEL_BLANK)}
            return {self.LABEL_CONNECTING: self._get_label(self.LABEL_CONNECTING)}
