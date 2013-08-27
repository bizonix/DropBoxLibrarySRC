#Embedded file name: dropbox/threadutils.py
from __future__ import absolute_import
import functools
import threading
from dropbox.native_queue import Queue
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.gui import message_sender, spawn_thread_with_name

class ThreadPool(object):
    sentinel = object()

    def __init__(self, name, num_threads, max_queue_size = 0):
        self.name = name
        self.work_queue = Queue(maxsize=max_queue_size)
        self.workers = [ threading.Thread(target=self._process_work) for _ in xrange(num_threads) ]
        for i, worker in enumerate(self.workers):
            worker.daemon = True
            worker.name = '%s-worker-%s' % (name, i)
            worker.start()

    def add_work(self, f, *args, **kwargs):
        self.work_queue.put(lambda : f(*args, **kwargs))

    def wait_for_completion(self, shutdown = True):
        if shutdown:
            for worker in self.workers:
                self.work_queue.put(self.sentinel)

        self.work_queue.join()

    def _process_work(self):
        while True:
            work = self.work_queue.get()
            try:
                if work is self.sentinel:
                    break
                else:
                    work()
            except SystemExit:
                pass
            except Exception:
                unhandled_exc_handler()
            finally:
                self.work_queue.task_done()


class StoppableThread(threading.Thread):

    def __init__(self, *n, **kw):
        super(StoppableThread, self).__init__(*n, **kw)
        self._stop = False
        self._lock = threading.Lock()

    def signal_stop(self):
        with self._lock:
            self._stop = True
        self.set_wakeup_event()

    def stopped(self):
        with self._lock:
            return self._stop

    def set_wakeup_event(self):
        raise NotImplementedError


@message_sender(spawn_thread_with_name('MURDERER'))
def stop_all_threads():
    threads_to_join = set()
    main_thread = None

    def maybe_stop(thr):
        if hasattr(thr, 'signal_stop') and hasattr(thr.signal_stop, '__call__'):
            TRACE('Stopping %s', thr.getName())
            try:
                thr.signal_stop()
            except Exception:
                unhandled_exc_handler()
            else:
                threads_to_join.add(thr)

    def safe_join(thr):
        TRACE('Joining %s', thr.getName())
        try:
            thr.join()
        except Exception:
            unhandled_exc_handler()

    for thr in threading.enumerate():
        if thr.getName() != 'MainThread':
            maybe_stop(thr)
        else:
            main_thread = thr

    for thr in threads_to_join:
        safe_join(thr)

    maybe_stop(main_thread)
    safe_join(main_thread)


def inherit_parent_thread_name(func):
    owner_name = threading.current_thread().name

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        prev_name = threading.current_thread().name
        threading.current_thread().name = owner_name
        try:
            return func(*args, **kwargs)
        finally:
            threading.current_thread().name = prev_name

    return wrapper
