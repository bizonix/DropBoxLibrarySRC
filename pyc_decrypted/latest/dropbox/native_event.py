#Embedded file name: dropbox/native_event.py
from __future__ import absolute_import
from dropbox.native_threading import NativeCondition

class AutoResetEvent(object):

    def __init__(self):
        self._cond = NativeCondition()
        self._is_set = False

    def set(self):
        with self._cond:
            self._is_set = True
            self._cond.notify()

    push = set

    def is_set(self):
        return self._is_set

    isSet = is_set

    def clear(self):
        return self.wait(0)

    def wait(self, timeout = None):
        with self._cond:
            if not self._is_set:
                self._cond.wait(timeout)
            signaled = self._is_set
            self._is_set = False
            return signaled
