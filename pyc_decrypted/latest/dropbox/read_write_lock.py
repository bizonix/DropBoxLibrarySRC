#Embedded file name: dropbox/read_write_lock.py
from __future__ import absolute_import
import threading
import functools

class LowRWLock(object):

    def __init__(self, base_lock_constructor, base_condition_constructor):
        self.base_lock = base_lock_constructor()
        self.base_condition_constructor = base_condition_constructor
        self.write_condition = base_condition_constructor(self.base_lock)
        self.read_condition = base_condition_constructor(self.base_lock)
        self.writer_request = False
        self.num_readers = 0

    def _acquire_read(self):
        while self.writer_request:
            self.write_condition.wait()

        self.num_readers += 1
        return True

    def acquire_read(self):
        with self.base_lock:
            return self._acquire_read()

    def _release_read(self):
        assert self.num_readers
        self.num_readers -= 1
        if not self.num_readers:
            self.read_condition.notifyAll()

    def release_read(self):
        with self.base_lock:
            self._release_read()

    def _acquire_write(self):
        while self.writer_request:
            self.write_condition.wait()

        self.writer_request = True
        while self.num_readers:
            self.read_condition.wait()

        return True

    def acquire_write(self, *n, **kw):
        with self.base_lock:
            return self._acquire_write(*n, **kw)

    def _release_write(self):
        assert not self.num_readers
        assert self.writer_request
        self.writer_request = False
        self.write_condition.notifyAll()

    def release_write(self, *n, **kw):
        with self.base_lock:
            return self._release_write(*n, **kw)

    release = release_read
    acquire = acquire_read
    __enter__ = acquire

    def __exit__(self, *n, **kw):
        self.release()

    def locked(self):
        with self.base_lock:
            return self.num_readers or self.writer_request


RWLock = functools.partial(LowRWLock, threading.Lock, threading.Condition)
