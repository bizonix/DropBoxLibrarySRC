#Embedded file name: dropbox/native_queue.py
from __future__ import absolute_import
from time import time as _time
from collections import deque
from dropbox.native_threading import NativeCondition, NativeMutex

class Empty(Exception):
    pass


class Full(Exception):
    pass


class Queue(object):

    def __init__(self, maxsize = 0):
        self._init(maxsize)
        self.mutex = NativeMutex()
        self.not_empty = NativeCondition(self.mutex)
        self.not_full = NativeCondition(self.mutex)
        self.unfinished_tasks = 0
        self.all_tasks_done = NativeCondition(self.mutex)

    def clear(self):
        with self.mutex:
            self.queue.clear()
            self.not_full.notify()

    def get_all_and_clear(self):
        with self.mutex:
            ret = list(self.queue)
            self.queue.clear()
            self.not_full.notify()
        return ret

    def qsize(self):
        with self.mutex:
            return self._qsize()

    def empty(self):
        with self.mutex:
            return self._empty()

    def full(self):
        with self.mutex:
            return self._full()

    def task_done(self):
        with self.all_tasks_done:
            self.unfinished_tasks -= 1
            if self.unfinished_tasks < 0:
                self.unfinished_tasks += 1
                raise ValueError('task_done() called too many times')
            elif self.unfinished_tasks == 0:
                self.remaining_tasks = 0
                self.all_tasks_done.notifyAll()

    def join(self):
        with self.all_tasks_done:
            while self.unfinished_tasks:
                self.all_tasks_done.wait()

    def put(self, item, block = True, timeout = None):
        with self.not_full:
            if not block:
                if self._full():
                    raise Full
            elif timeout is None:
                while self._full():
                    self.not_full.wait()

            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = _time() + timeout
                while self._full():
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Full
                    self.not_full.wait(remaining)

            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def put_nowait(self, item):
        return self.put(item, False)

    def get(self, block = True, timeout = None):
        with self.not_empty:
            if not block:
                if self._empty():
                    raise Empty
            elif timeout is None:
                while self._empty():
                    self.not_empty.wait()

            else:
                if timeout < 0:
                    raise ValueError("'timeout' must be a positive number")
                endtime = _time() + timeout
                while self._empty():
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)

            item = self._get()
            self.not_full.notify()
            return item

    def get_nowait(self):
        return self.get(False)

    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = deque()

    def _qsize(self):
        return len(self.queue)

    def _empty(self):
        return not self.queue

    def _full(self):
        return self.maxsize > 0 and len(self.queue) == self.maxsize

    def _put(self, item):
        self.queue.append(item)

    def _get(self):
        return self.queue.popleft()
