#Embedded file name: dropbox/client/gandalf.py
from __future__ import with_statement
import build_number
import os
from Crypto.Random import random
from dropbox.callbacks import Handler
from dropbox.db_thread import db_thread
from dropbox.native_event import AutoResetEvent
from dropbox.read_write_lock import RWLock
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, unhandled_exc_handler

class Gandalf(object):

    def __init__(self, dropbox_app):
        self.dropbox_app = dropbox_app
        self.features = {}
        self.logged = {}
        self.logged_allows = {}
        self.lock = RWLock()
        self.got_features = False
        self.enable_nonpresent_features = not (hasattr(build_number, 'frozen') or os.getenv('DB_USE_REAL_GANDALF'))
        self._info_received_callbacks = Handler(recursive=False, handle_exc=unhandled_exc_handler)
        self.gandalf_thread = db_thread(GandalfThread)(self, dropbox_app)

    def start(self):
        self.gandalf_thread.start()

    def stop(self):
        self.gandalf_thread.signal_stop()

    def handle_info(self, ret):
        self.lock.acquire_write()
        try:
            if not self.got_features:
                TRACE('Gandalf: got features: %r', ret)
                self.got_features = True
            self.features = ret
        finally:
            self.lock.release_write()

        self._info_received_callbacks.run_handlers()
        self._info_received_callbacks.clear()

    def info_received(self, callback = None):
        if self.got_features:
            return True
        else:
            if callback:
                self._info_received_callbacks.add_handler(callback)
            return False

    def allows(self, feature):
        cols = None
        with self.lock:
            is_allowed = feature in self.features or self.enable_nonpresent_features
            TRACE('Gandalf: allows() check for feature %s returning %r', feature, is_allowed)
            if hasattr(build_number, 'frozen'):
                if feature in self.features:
                    experiment_version, version, variant = self.features[feature]
                else:
                    experiment_version, version, variant = (None, None, None)
                if feature not in self.logged_allows or self.logged_allows[feature] != is_allowed:
                    self.logged_allows[feature] = is_allowed
                    cols = {'is_allowed': is_allowed,
                     'experiment_version': experiment_version,
                     'name': feature,
                     'version': version}
        if cols:
            self.dropbox_app.event.report('gandalf_allows', cols)
        return is_allowed

    def get_variant(self, feature):
        do_log = False
        with self.lock:
            if feature not in self.features:
                TRACE('Gandalf: feature %s not found', feature)
                return
            experiment_version, version, variant = self.features[feature]
            if hasattr(build_number, 'frozen') and (feature not in self.logged or self.logged[feature] != (experiment_version, version, variant)):
                if feature in self.logged:
                    TRACE('Gandalf: feature %s changed (experiment_version, version, variant) to %r', feature, (experiment_version, version, variant))
                self.logged[feature] = (experiment_version, version, variant)
                do_log = True
        TRACE('Gandalf: variant check for feature %s returning %r', feature, variant)
        if do_log:
            cols = {'name': feature,
             'experiment_version': experiment_version,
             'version': version,
             'variant': variant}
            self.dropbox_app.event.report('gandalf_variant', cols)
        return variant


class GandalfThread(StoppableThread):

    def __init__(self, gandalf, dropbox_app, *n, **kw):
        kw['name'] = 'GANDALF'
        super(GandalfThread, self).__init__(*n, **kw)
        self.gandalf = gandalf
        self.dropbox_app = dropbox_app
        self.setDaemon(True)
        self.bangp = AutoResetEvent()

    def set_wakeup_event(self):
        self.bangp.set()

    def run(self):
        TRACE('Gandalf thread starting.')
        while not self.stopped():
            try:
                ret = self.dropbox_app.conn.gandalf_get_variants()
                if ret['ret'] != 'ok':
                    TRACE('gandalf_get_variants returned some form of error! %r', ret)
                else:
                    self.gandalf.handle_info(ret['features'])
            except Exception:
                unhandled_exc_handler()

            wait_period = random.randint(10800 / 4, 18000 / 4)
            self.bangp.wait(wait_period)

        TRACE('Stopping...')
