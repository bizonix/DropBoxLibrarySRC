#Embedded file name: dropbox/idlehands.py
from __future__ import with_statement, absolute_import
import threading
import time
import sys
from pprint import pprint
from dropbox.threadutils import StoppableThread
from dropbox.native_threading import NativeCondition
from dropbox.trace import unhandled_exc_handler, report_bad_assumption
DEFAULT_POLL_SECONDS = 60
TS_DELTA_SECONDS = 3
DEBUG = False

class IdleHandler(StoppableThread):

    def __init__(self, idletracker):
        super(IdleHandler, self).__init__(name='IDLEHANDLER')
        self.cond = NativeCondition()
        self.cb_map = {}
        self.last_active_ts = None
        self.idletracker = idletracker
        self.poll_seconds = DEFAULT_POLL_SECONDS
        self.callbacks_started = False

    def set_wakeup_event(self):
        with self.cond:
            self.cond.notify()

    def set_poll_seconds(self, seconds):
        assert seconds > 0, 'seconds arg must be positive'
        self.poll_seconds = int(seconds)

    def add(self, wait_seconds, callback):
        with self.cond:
            assert wait_seconds > 0, 'wait_seconds must be positive'
            wait_seconds = int(wait_seconds)
            self.cb_map[callback] = (wait_seconds, False)

    def remove(self, callback):
        with self.cond:
            if callback in self.cb_map:
                try:
                    del self.cb_map[callback]
                except KeyError:
                    pass

    def run(self):
        if not self.idletracker.is_trackable():
            return False
        while not self.stopped():
            with self.cond:
                self.cond.wait(timeout=self.poll_seconds)
                try:
                    idle_for = self.idletracker.seconds_idle()
                except:
                    unhandled_exc_handler()
                    report_bad_assumption('seconds_idle failed. client used to be trackable.')
                    return False

                active_ts = int(time.time()) - idle_for
                if not self.last_active_ts:
                    self.last_active_ts = active_ts
                if DEBUG:
                    print 'idle_for', idle_for, 'started?', self.callbacks_started
                    pprint(self.cb_map)
                    print 'delta', active_ts - self.last_active_ts
                if self.callbacks_started and active_ts - self.last_active_ts > TS_DELTA_SECONDS:
                    self.last_active_ts = active_ts
                    for callback, (wait_seconds, called) in self.cb_map.items():
                        self.cb_map[callback] = (wait_seconds, False)

                    self.callbacks_started = False
                to_be_run = []
                for callback, (wait_seconds, ran) in self.cb_map.items():
                    if not ran and idle_for >= wait_seconds:
                        to_be_run.append((callback, wait_seconds))

            for callback, wait_seconds in to_be_run:
                self.callbacks_started = True
                self.cb_map[callback] = (wait_seconds, True)
                try:
                    callback()
                except:
                    unhandled_exc_handler()

                if DEBUG:
                    print 'callback', '<' * 30
