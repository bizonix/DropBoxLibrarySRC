#Embedded file name: dropbox/dispatch.py
from __future__ import absolute_import
import sys
from threading import Thread, Event, RLock
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.native_event import AutoResetEvent
from heapq import heappush, heappop
from itertools import count
import time

class TaskError(Exception):
    pass


class TaskTimeoutError(TaskError):
    pass


class TaskRunningError(TaskError):
    pass


class TaskBadStateError(TaskError):
    pass


class Worker(Thread):

    def __init__(self, group = None, name = None):
        Thread.__init__(self, group=group, name=name, target=self._run)
        self.setDaemon(True)
        self.activity_event = AutoResetEvent()
        self.work_items = []
        self.lock = RLock()
        self.counter = count()
        self._should_run = True
        self.start()

    def dispatch(self, action, on_complete = None, trace_unhandled_exc = True):
        return self.dispatch_at(time.time(), action, on_complete, trace_unhandled_exc)

    def delay(self, delta, action, on_complete = None, trace_unhandled_exc = True):
        return self.dispatch_at(time.time() + delta, action, on_complete, trace_unhandled_exc)

    def dispatch_at(self, time, action, on_complete = None, trace_unhandled_exc = True):
        if not callable(action):
            raise TypeError('action must be callable()')
        t = ActionTask(action, on_complete=on_complete, trace_unhandled_exc=trace_unhandled_exc)
        with self.lock:
            priority = time
            count = next(self.counter)
            entry = (priority, count, t)
            heappush(self.work_items, entry)
            if entry == self.work_items[0]:
                self.activity_event.set()
        return t

    def stop(self):
        TRACE('Stopping dispatch worker')
        self._should_run = False
        self.activity_event.set()

    def _run(self):
        TRACE('Starting dispatch worker')
        wait_time = None
        while self._should_run:
            try:
                if wait_time is None:
                    self.activity_event.wait()
                elif wait_time > 0:
                    self.activity_event.wait(timeout=wait_time)
                with self.lock:
                    if self.work_items and self.work_items[0][0] <= time.time():
                        priority, count, work = heappop(self.work_items)
                    else:
                        priority, count, work = (None, None, None)
                if work:
                    work()
                with self.lock:
                    wait_time = None
                    if self.work_items and self.work_items[0][0]:
                        wait_time = self.work_items[0][0] - time.time()
            except Exception:
                unhandled_exc_handler()

        TRACE('Finished dispatch worker')


class Task(object):

    def __init__(self, on_complete = None, trace_unhandled_exc = True):
        self._error = None
        self._value = None
        self._is_success = False
        self._is_complete = False
        self._completion = Event()
        self._lock = RLock()
        self._on_complete = on_complete
        self._trace_unhandled_exc = trace_unhandled_exc

    @property
    def error(self):
        if not self._completion.isSet():
            raise TaskRunningError('Task is not yet complete')
        elif self._is_success:
            raise TaskBadStateError('Task succeeded')
        else:
            return self._error

    @property
    def value(self):
        if not self._completion.isSet():
            raise TaskRunningError('Task is not yet complete')
        elif not self._is_success:
            raise TaskBadStateError('Task failed')
        else:
            return self._value

    @property
    def is_complete(self):
        return self._completion.isSet()

    @property
    def is_success(self):
        if not self._completion.isSet():
            raise TaskRunningError('Task is not yet complete')
        else:
            return self._is_success

    @property
    def is_fail(self):
        if not self._completion.isSet():
            raise TaskRunningError('Task is not yet complete')
        else:
            return not self._is_success

    def on_complete(self, continuation):
        with self._lock:
            self._on_complete = continuation
            call_sync = self._completion.isSet()
        if call_sync:
            continuation(self)

    def wait(self, timeout = None):
        self._completion.wait(timeout)
        return self._completion.isSet()

    def wait_value(self, timeout = None):
        if self._completion.isSet() or self.wait(timeout):
            if self._is_success:
                return self._value
            raise self._error[0], self._error[1], self._error[2]
        else:
            raise TaskTimeoutError()

    def _work(self):
        raise NotImplementedError('Derived tasks must override the _work method')

    def _complete(self, success):
        self._is_success = success
        if not success:
            self._error = sys.exc_info()
            if self._trace_unhandled_exc:
                unhandled_exc_handler(exc_info=self._error)
        with self._lock:
            self._completion.set()
            cont = self._on_complete
        if cont:
            try:
                cont(self)
            except Exception:
                unhandled_exc_handler()

    def __call__(self):
        try:
            self._value = self._work()
        except Exception:
            self._complete(False)
        else:
            self._complete(True)


class ActionTask(Task):

    def __init__(self, action, *args, **kwargs):
        super(ActionTask, self).__init__(*args, **kwargs)
        self.action = action

    def _work(self):
        return self.action()
