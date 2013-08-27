#Embedded file name: dropbox/native_threading_win32.py
from __future__ import absolute_import
from threading import currentThread
import win32event
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.win32.kernel32 import GetLastError, CreateMutex, ReleaseMutex, CreateSemaphore, ReleaseSemaphore, CreateEvent, SetEvent, WaitForSingleObject, SignalObjectAndWait, CloseHandle

def debug(*n):
    return TRACE('*** ' + ' '.join((str(ni) for ni in n)))


class NativeThreadingException(Exception):

    def __init__(self, *n, **kw):
        debug('*** NativeThreadingException: %r, %r' % (n, kw))
        super(NativeThreadingException, self).__init__(*n, **kw)


_NATIVE_MUTEX_MAGIC = 4207853295L

class NativeMutex(object):
    NATIVE_MUTEX_MAGIC = _NATIVE_MUTEX_MAGIC

    def __init__(self):
        self._mutex = CreateMutex(None, False, None)
        if not self._mutex:
            try:
                raise NativeThreadingException(GetLastError(), 'CreateMutex failed')
            except:
                unhandled_exc_handler()
                raise

        self.ch = CloseHandle

    def acquire(self, blocking = 1):
        did_wait = WaitForSingleObject(self._mutex, win32event.INFINITE if blocking else 0)
        if did_wait == win32event.WAIT_FAILED:
            try:
                raise NativeThreadingException(GetLastError(), 'WaitForSingleObject failed')
            except:
                unhandled_exc_handler()
                raise

        elif not blocking:
            return did_wait != win32event.WAIT_TIMEOUT
        return True

    __enter__ = acquire

    def release(self):
        if not ReleaseMutex(self._mutex):
            try:
                raise NativeThreadingException(GetLastError(), 'ReleaseMutex failed')
            except:
                unhandled_exc_handler()
                raise

    def __exit__(self, t, v, tb):
        self.release()

    def __del__(self):
        if not self.ch(self._mutex):
            debug('Tried to close invalid handle: %r' % self._mutex)


class NativeCondition(object):

    def __init__(self, lock = None):
        self.__waiters_count = 0
        self.__waiters_count_lock = NativeMutex()
        self.__was_broadcast = False
        self.__sema = CreateSemaphore(None, 0, 2147483647, None)
        if not self.__sema:
            try:
                raise NativeThreadingException(GetLastError(), 'CreateSemaphore failed')
            except:
                unhandled_exc_handler()

        self.__waiters_done = CreateEvent(None, False, False, None)
        if not self.__waiters_done:
            try:
                raise NativeThreadingException(GetLastError(), 'CreateEvent failed')
            except:
                unhandled_exc_handler()

        self.__lock = NativeMutex() if lock is None else lock
        if self.__lock.NATIVE_MUTEX_MAGIC != _NATIVE_MUTEX_MAGIC:
            raise Exception('Can only use NativeCondition with NativeMutex')
        self.acquire = self.__lock.acquire
        self.release = self.__lock.release
        self.ch = CloseHandle

    def __enter__(self):
        self.__lock.__enter__()

    def __exit__(self, t, v, tb):
        self.__lock.__exit__(t, v, tb)

    def __del__(self):
        for hand in (self.__sema, self.__waiters_done):
            if not self.ch(hand):
                debug('Tried to close invalid handle: %r' % hand)

    def wait(self, timeout = None):
        with self.__waiters_count_lock:
            self.__waiters_count += 1
        last_waiter = False
        did_wait = SignalObjectAndWait(self.__lock._mutex, self.__sema, int(timeout * 1000) if timeout is not None else win32event.INFINITE, False)
        if did_wait == win32event.WAIT_FAILED:
            try:
                raise NativeThreadingException(GetLastError(), 'SignalObjectAndWait failed')
            except:
                unhandled_exc_handler()
                raise

        else:
            timed_out = did_wait == win32event.WAIT_TIMEOUT
        with self.__waiters_count_lock:
            self.__waiters_count -= 1
            last_waiter = self.__was_broadcast and self.__waiters_count == 0
        if last_waiter:
            did_wait = SignalObjectAndWait(self.__waiters_done, self.__lock._mutex, win32event.INFINITE, False)
            if did_wait == win32event.WAIT_FAILED:
                try:
                    raise NativeThreadingException(GetLastError(), 'SignalObjectAndWait failed')
                except:
                    unhandled_exc_handler()
                    raise

        else:
            did_wait = WaitForSingleObject(self.__lock._mutex, win32event.INFINITE)
            if did_wait == win32event.WAIT_FAILED:
                try:
                    raise NativeThreadingException(GetLastError(), 'WaitForSingleObject failed')
                except:
                    unhandled_exc_handler()
                    raise

        return timed_out

    def notify(self, n = 1):
        self.__waiters_count_lock.acquire()
        to_wake = n if n > -1 else self.__waiters_count
        first_iter = True
        while to_wake:
            if not first_iter:
                self.__waiters_count_lock.acquire()
            if not ReleaseSemaphore(self.__sema, 1, None):
                try:
                    raise NativeThreadingException(GetLastError(), 'ReleaseSemaphore failed')
                except:
                    unhandled_exc_handler()
                    raise

            self.__waiters_count_lock.release()
            to_wake -= 1
            first_iter = False

    def notifyAll(self):
        self.__waiters_count_lock.acquire()
        self.__was_broadcast = self.__waiters_count > 0
        if self.__was_broadcast:
            try:
                if not ReleaseSemaphore(self.__sema, self.__waiters_count, None):
                    try:
                        raise NativeThreadingException(GetLastError(), 'ReleaseSemaphore failed')
                    except:
                        unhandled_exc_handler()
                        raise

            finally:
                self.__waiters_count_lock.release()

            did_wait = WaitForSingleObject(self.__waiters_done, win32event.INFINITE)
            if did_wait == win32event.WAIT_FAILED:
                try:
                    raise NativeThreadingException(GetLastError(), 'WaitForSingleObject failed')
                except:
                    unhandled_exc_handler()
                    raise

            self.__was_broadcast = False
        else:
            self.__waiters_count_lock.release()


def configure_wakeup_thread():
    pass


def wakeup_thread(tid):
    pass


def thread_id():
    return None


if __name__ == '__main__':
    from threading import Thread
    from Crypto.Random import random
    import time
    import traceback
    a = NativeCondition()
    trace_lock = NativeMutex()

    def yo():
        try:
            while True:
                with a:
                    if a.wait(1):
                        print '%s: timed out at %f' % (currentThread().getName(), time.time())
                    else:
                        print '%s: got notification at %f' % (currentThread().getName(), time.time())

        except:
            with trace_lock:
                print 'some stuff happened in %r' % currentThread()
                traceback.print_exc()


    for i in range(10):
        yot = Thread(target=yo, name=str(i))
        yot.setDaemon(True)
        yot.start()

    while True:
        with a:
            th = random.randint(0, 9)
            print 'notifying %d threads at %f' % (th, time.time())
            a.notify(th)
        time.sleep(2)
