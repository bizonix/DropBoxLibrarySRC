#Embedded file name: dropbox/fileevents.py
from __future__ import absolute_import
import threading
import collections
import sys
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.threadutils import StoppableThread
from dropbox.dbexceptions import TimeoutError
from dropbox.directoryevent import DirectoryEvent
from dropbox.gui import SafeValue
import dropbox.fd_leak_debugging

class EventsDroppedError(Exception):
    pass


class RootDeletedError(Exception):
    pass


class UnrecoverableWatchError(Exception):
    pass


class NoWorkingWatchError(Exception):
    pass


class MetaWatchFailure(Exception):
    pass


class SimpleMetaDirectoryWatchManager(object):

    def __init__(self, MetaWatch):
        self.cur = None
        self.val = MetaWatch

    def next(self, reason = None):
        if self.cur is None:
            self.cur = self.val
            try:
                return self.val()
            except:
                unhandled_exc_handler()

        raise NoWorkingWatchError()


class FileEvents(StoppableThread):

    def __init__(self, metawatchmgr, **kwargs):
        super(FileEvents, self).__init__(name='FILEEVENTS')
        self.metawatchmgr = metawatchmgr
        self.metawatch = None
        self.arguments = kwargs
        self.lock = threading.Lock()
        self.async_watch_lock = threading.Lock()
        self.maxid = 1
        self.id2watchcb = {}
        self.path2watch = {}
        self.watch2cbs = collections.defaultdict(list)
        self.watches_to_close = []
        self.watches_to_create = collections.deque()
        self.configured = False
        self.ideal_tracker = None

    def set_wakeup_event(self):
        if self.metawatch:
            self.metawatch.set_wakeup_event()

    def set_ideal_tracker(self, ideal_tracker):
        self.ideal_tracker = ideal_tracker

    RECURSE_ALL = -1
    RECURSE_NONE = 0
    RECURSE_ONE = 1

    def _add_watch_at_index(self, path, cb, recurse, id):
        try:
            watch = self.path2watch[path, recurse]
        except KeyError:
            watch = self.DirectoryWatch(path, recurse=recurse, **self.arguments)
            self.path2watch[watch.path, watch.recurse] = watch

        self.watch2cbs[watch].append(cb)
        self.id2watchcb[id] = (watch, cb)

    def add_watch_async(self, path, cb, recurse = RECURSE_ALL):
        assert recurse in (self.RECURSE_ALL, self.RECURSE_NONE, self.RECURSE_ONE)
        done = SafeValue()
        with self.async_watch_lock:
            self.watches_to_create.append((path,
             cb,
             recurse,
             done,
             self.maxid))
            id = self.maxid
            self.maxid += 1
        self.set_wakeup_event()
        return (id, done)

    def add_watch(self, path, cb, recurse = RECURSE_ALL):
        watchid, done = self.add_watch_async(path, cb, recurse)
        done.wait()
        return watchid

    def remove_watch(self, watch_id, on_close = None):
        try:
            with self.lock:
                try:
                    watch, cb = self.id2watchcb[watch_id]
                except KeyError:
                    return

                self.watch2cbs[watch].remove(cb)
                del self.id2watchcb[watch_id]
                if not self.watch2cbs[watch]:
                    del self.path2watch[watch.path, watch.recurse]
                    del self.watch2cbs[watch]
                    self.watches_to_close.append((watch, on_close))
        except:
            unhandled_exc_handler()
        finally:
            self.set_wakeup_event()

    def switch_metawatch(self, reason = None):
        assert self.metawatch
        with self.lock:
            self.set_wakeup_event()
            oldwatchlist = self.id2watchcb.items()
            self.metawatch = self.metawatchmgr.next(reason)
            self.configured = False
            self.DirectoryWatch = self.metawatch.DirectoryWatch
            self.id2watchcb.clear()
            self.path2watch.clear()
            self.watch2cbs.clear()
            for id, (watch, cb) in oldwatchlist:
                self._add_watch_at_index(watch.path, cb, watch.recurse, id)
                self.watches_to_close.append((watch, None))

            TRACE('Switched metawatch to %r', self.metawatch)
            dropbox.fd_leak_debugging.notify_metawatch_change(self.metawatch)
        for id, (watch, cb) in oldwatchlist:
            try:
                TRACE('switch_metawatch: signalling DirectoryEvent.TYPE_DROPPED_EVENTS')
                cb(DirectoryEvent(watch.path, DirectoryEvent.TYPE_DROPPED_EVENTS))
            except:
                unhandled_exc_handler()

    def _get_ids(self, watch):
        with self.lock:
            return [ id for id, (w, cb) in self.id2watchcb.iteritems() if w == watch ]

    def run(self):
        TRACE(u'Starting...')
        while not self.stopped():
            with self.lock:
                if not self.metawatch:
                    self.metawatch = self.metawatchmgr.next()
                    dropbox.fd_leak_debugging.notify_metawatch_change(self.metawatch)
                    self.DirectoryWatch = self.metawatch.DirectoryWatch
                    TRACE('Using %r' % self.metawatch)
                if not self.configured:
                    self.metawatch.configure()
                    self.configured = True
                for watch, cb in self.watches_to_close:
                    watch.close()
                    if cb:
                        try:
                            cb()
                        except:
                            unhandled_exc_handler()

                self.watches_to_close = []
                while True:
                    with self.async_watch_lock:
                        try:
                            path, cb, recurse, done, id = self.watches_to_create.popleft()
                        except IndexError:
                            break

                    try:
                        self._add_watch_at_index(path, cb, recurse, id)
                        done.set(True)
                    except Exception as e:
                        done.set_exception(e, exc_info=sys.exc_info())

                watches = self.watch2cbs.keys()
                metawatch = self.metawatch
            try:
                ready = metawatch.wait(watches)
            except MetaWatchFailure:
                self.switch_metawatch()
                continue

            for watch in ready:
                ids_to_remove = []
                try:
                    events = list(watch.get_events(block=False))
                except TimeoutError:
                    continue
                except EventsDroppedError:
                    TRACE('!! File events dropped')
                    events = DirectoryEvent(watch.path, DirectoryEvent.TYPE_DROPPED_EVENTS)
                except RootDeletedError:
                    events = DirectoryEvent(watch.path, DirectoryEvent.TYPE_WATCH_REMOVED)
                    ids_to_remove = self._get_ids(watch)
                except UnrecoverableWatchError:
                    events = DirectoryEvent(watch.path, DirectoryEvent.TYPE_WATCH_ERROR)
                    ids_to_remove = self._get_ids(watch)
                except:
                    unhandled_exc_handler()
                    continue

                if not events:
                    continue
                try:
                    if self.ideal_tracker is not None:
                        TRACE('Sending events to IdealTracker')
                        self.ideal_tracker.handle_fs_events(events)
                except Exception:
                    unhandled_exc_handler()

                with self.lock:
                    cbs = list(self.watch2cbs[watch]) if watch in self.watch2cbs else []
                for id in ids_to_remove:
                    self.remove_watch(id)

                for cb in cbs:
                    try:
                        cb(events)
                    except:
                        unhandled_exc_handler()

        with self.lock:
            for watch, cb in self.watches_to_close:
                watch.close()
                try:
                    cb()
                except:
                    unhandled_exc_handler()

            for watch in self.watch2cbs.keys():
                watch.close()

        del self.metawatch
        TRACE('Stopping...')
