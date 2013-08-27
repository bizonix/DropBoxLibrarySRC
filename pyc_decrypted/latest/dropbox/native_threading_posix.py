#Embedded file name: dropbox/native_threading_posix.py
from __future__ import absolute_import
import threading, errno, ctypes, ctypes.util, time, signal
from dropbox.trace import unhandled_exc_handler
libpthread = ctypes.cdll.LoadLibrary(ctypes.util.find_library('pthread'))

class Timespec(ctypes.Structure):
    _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]


pthread_mutex_t_p = ctypes.c_void_p
pthread_mutexattr_t_p = ctypes.c_void_p
pthread_cond_t_p = ctypes.c_void_p
pthread_condattr_t_p = ctypes.c_void_p
struct_timespec_p = ctypes.POINTER(Timespec)
sm = (('mutex_init', ctypes.c_int, (pthread_mutex_t_p, pthread_mutexattr_t_p)),
 ('mutex_destroy', ctypes.c_int, (pthread_mutex_t_p, pthread_mutexattr_t_p)),
 ('mutex_lock', ctypes.c_int, (pthread_mutex_t_p,)),
 ('mutex_trylock', ctypes.c_int, (pthread_mutex_t_p,)),
 ('mutex_unlock', ctypes.c_int, (pthread_mutex_t_p,)),
 ('mutex_destroy', ctypes.c_int, (pthread_mutex_t_p,)),
 ('cond_init', ctypes.c_int, (pthread_cond_t_p, pthread_condattr_t_p)),
 ('cond_destroy', ctypes.c_int, (pthread_cond_t_p,)),
 ('cond_broadcast', ctypes.c_int, (pthread_cond_t_p,)),
 ('cond_signal', ctypes.c_int, (pthread_cond_t_p,)),
 ('cond_wait', ctypes.c_int, (pthread_cond_t_p, pthread_mutex_t_p)),
 ('cond_timedwait', ctypes.c_int, (pthread_cond_t_p, pthread_mutex_t_p, struct_timespec_p)),
 ('cond_destroy', ctypes.c_int, (pthread_cond_t_p,)),
 ('self', ctypes.c_long, ()),
 ('kill', ctypes.c_int, (ctypes.c_long, ctypes.c_int)))
for func_name, restype, argtypes in sm:
    func = getattr(libpthread, 'pthread_' + func_name)
    func.restype = restype
    func.argtypes = argtypes

_NATIVE_MUTEX_MAGIC = 4207853295L

class NativeMutex(object):
    MUTEX_BUFFER_LENGTH = 64
    NATIVE_MUTEX_MAGIC = _NATIVE_MUTEX_MAGIC

    def __init__(self, **kw):
        self.p = libpthread
        self._mutex = ctypes.create_string_buffer(NativeMutex.MUTEX_BUFFER_LENGTH)
        if self.p.pthread_mutex_init(self._mutex, None) != 0:
            raise Exception('toats messed up')

    def __del__(self):
        self.p.pthread_mutex_destroy(self._mutex)

    def acquire(self, blocking = 1):
        if blocking == 1:
            ret = self.p.pthread_mutex_lock(self._mutex)
            if ret != 0:
                raise Exception('toats messed up')
            else:
                return 1
        else:
            ret = self.p.pthread_mutex_trylock(self._mutex)
            if ret not in (errno.EBUSY, 0):
                raise Exception('toats messed up')
            if ret == 0:
                return 1
            return 0

    __enter__ = acquire

    def release(self):
        if self.p.pthread_mutex_unlock(self._mutex) != 0:
            raise Exception('toats messed up')

    def __exit__(self, t, v, tb):
        self.release()


class NativeCondition(object):
    COND_SIZE = 64

    def __init__(self, lock = None, **kw):
        self.p = libpthread
        self.__lock = NativeMutex() if lock is None else lock
        if self.__lock.NATIVE_MUTEX_MAGIC != _NATIVE_MUTEX_MAGIC:
            raise Exception('Can only use NativeCondition with NativeMutex (%r), instead got %r' % (NativeMutex, type(self.__lock)))
        self._cond = ctypes.create_string_buffer(NativeCondition.COND_SIZE)
        if self.p.pthread_cond_init(self._cond, None) != 0:
            raise Exception('toats messed up')
        self.acquire = self.__lock.acquire
        self.release = self.__lock.release

    def __del__(self):
        self.p.pthread_cond_destroy(self._cond)

    def __enter__(self):
        return self.__lock.__enter__()

    def __exit__(self, *args):
        return self.__lock.__exit__(*args)

    def wait(self, timeout = None):
        if timeout is None:
            if self.p.pthread_cond_wait(self._cond, self.__lock._mutex) != 0:
                raise Exception('toats messed up')
        else:
            timeout += time.time()
            timespec = Timespec()
            timespec.tv_sec = int(timeout)
            timespec.tv_nsec = int((timeout - int(timeout)) * 1000000000)
            ret = self.p.pthread_cond_timedwait(self._cond, self.__lock._mutex, ctypes.byref(timespec))
            if ret not in (0, errno.ETIMEDOUT):
                raise Exception('toats messed up')

    def notify(self, n = 1):
        for i in range(n):
            if self.p.pthread_cond_signal(self._cond) != 0:
                raise Exception('toats messed up')

    def notifyAll(self):
        if self.p.pthread_cond_broadcast(self._cond) != 0:
            raise Exception('toats messed up')


def configure_wakeup_thread():
    try:
        signal.signal(signal.SIGURG, lambda x, y: None)
    except:
        unhandled_exc_handler()


def wakeup_thread(tid):
    try:
        if tid and tid != thread_id():
            libpthread.pthread_kill(tid, signal.SIGURG)
    except:
        unhandled_exc_handler()


def thread_id():
    try:
        return libpthread.pthread_self()
    except:
        unhandled_exc_handler()
        return None


if __name__ == '__main__':
    a = NativeCondition()

    def yo():
        with a:
            while True:
                a.wait(0.5)
                print 'got notification %f' % time.time()


    threading.Thread(target=yo).start()
    while True:
        with a:
            print 'notifying %f' % time.time()
            a.notify()
        time.sleep(1)
