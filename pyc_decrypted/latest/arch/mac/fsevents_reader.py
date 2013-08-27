#Embedded file name: arch/mac/fsevents_reader.py
from __future__ import absolute_import
import os
import stat
import time
import threading
from pymac.dlls import FSEvent, Core
from pymac.types import CFStringRef, FSEventStreamCallback
from pymac.helpers.core import releasing, python_to_property
from pymac.constants import kCFAllocatorDefault, kCFRunLoopRunFinished, kFSEventStreamCreateFlagWatchRoot, kFSEventStreamEventFlagHistoryDone, kFSEventStreamEventFlagKernelDropped, kFSEventStreamEventFlagMustScanSubDirs, kFSEventStreamEventFlagRootChanged, kFSEventStreamEventFlagUserDropped
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.directoryevent import DirectoryEvent
from dropbox.threadutils import StoppableThread
from dropbox.native_queue import Queue, Empty
from dropbox.fileevents import RootDeletedError, FileEvents
from dropbox.functions import is_case_insensitive_path
from .directory_reader_helper import RescanMixin
DEBUG = False

class FSEventThread(StoppableThread):

    def __init__(self):
        super(FSEventThread, self).__init__(name='FSEventThread')
        self.dataEvent = threading.Event()
        self.loop = None
        self.lock = threading.Lock()
        self.watchstream = []

    def run(self):
        with self.lock:
            self.loop = Core.CFRunLoopGetCurrent()
        for watch, path, stream in self.watchstream:
            watch.schedule(path, stream)

        while not self.stopped():
            Core.CFRunLoopRun()
            if not self.stopped():
                self.dataEvent.wait()
                self.dataEvent.clear()

        TRACE('Stopping...')

    def new_watch(self):
        self.dataEvent.set()

    def set_wakeup_event(self):
        self.dataEvent.set()
        if self.loop:
            Core.CFRunLoopStop(self.loop)


class DirectoryWatch(RescanMixin):

    class NonFatalError(Exception):
        pass

    class EventsDroppedError(Exception):
        pass

    class _TimeoutError(Exception):
        pass

    EventThread = None

    def __init__(self, path, recurse = FileEvents.RECURSE_ALL, read_interval = 0.1, **kwargs):
        if not DirectoryWatch.EventThread or DirectoryWatch.EventThread.stopped():
            DirectoryWatch.EventThread = FSEventThread()
            DirectoryWatch.EventThread.start()
        self.path_map = {}
        self.stream2path = {}
        self.path2stream = {}
        self.link_paths = set()
        self.should_shell_touch = False
        self.queue = Queue()
        self.path = path
        try:
            self.case_insensitive = is_case_insensitive_path(self.path)
        except Exception:
            unhandled_exc_handler()
            self.case_insensitive = True

        self.recurse = recurse
        self.isdir = os.path.isdir(self.path)
        self.dir = self.path if self.isdir else os.path.split(self.path)[0]
        self.c_fsevents_callback = FSEventStreamCallback(self.fsevents_callback)
        self.register_path(self.dir)
        if self.isdir:
            self.add_subdir(self.path, no_trace=True)
        else:
            self.add_file(self.path)

    def get_events(self, block = True, timeout = None):
        count = 0
        while True:
            try:
                event = self.queue.get(False)
            except Empty:
                if count > 0:
                    break
                if not block or timeout is not None and timeout <= 0:
                    return
                start = time.time()
                try:
                    event = self.queue.get(block, timeout)
                except Empty:
                    raise DirectoryWatch._TimeoutError()

                took = time.time() - start
                if timeout is not None:
                    timeout -= took

            if event is RootDeletedError:
                raise RootDeletedError
            yield event
            count += 1

    def add_file(self, path):
        if path in self.path_map:
            return
        self.path_map[self.dir] = (dict(), dict())
        self.rescan(self.dir)

    def add_subdir(self, path, no_trace = False):
        if path in self.path_map:
            return
        try:
            lst = os.lstat(path)
            if stat.S_ISLNK(lst.st_mode):
                self.link_paths.add(path)
                self.register_path(path)
            if not no_trace:
                TRACE('Adding directory %s' % path.encode('utf-8'))
            self.path_map[path] = (dict(), dict())
            self.rescan(path, no_trace=no_trace)
        except OSError as e:
            if e.errno == 2:
                TRACE('attemping to add_subdir on an non-existant file %s, most likely a temp file' % path.encode('utf-8'))
            else:
                raise

    def del_subdir(self, path):
        if DEBUG:
            TRACE('del_subdir called on path %r' % path)
        for k in self.path_map.keys():
            if DEBUG:
                TRACE('key in path map %r' % k.encode('utf-8'))
            if k == path or k.startswith(path + os.path.sep):
                if k in self.link_paths:
                    self.unregister_path(path)
                    self.link_paths.remove(k)
                if k in self.path_map:
                    dirs, files = self.path_map[k]
                    del self.path_map[k]
                    TRACE('Deleting %r from dir map' % k.encode('utf-8'))

    def register_path(self, path):
        if path in self.path2stream:
            return
        with releasing(python_to_property([path])) as cfArray:
            fsstream = FSEvent.FSEventStreamCreate(kCFAllocatorDefault, self.c_fsevents_callback, None, cfArray, FSEvent.FSEventsGetCurrentEventId(), 0.1, kFSEventStreamCreateFlagWatchRoot)
        self.schedule(path, fsstream)

    def schedule(self, path, fsstream):
        with DirectoryWatch.EventThread.lock:
            if DirectoryWatch.EventThread.loop is None:
                DirectoryWatch.EventThread.watchstream.append((self, path, fsstream))
                return
        self.path2stream[path] = fsstream
        self.stream2path[fsstream] = (path, os.path.realpath(path))
        FSEvent.FSEventStreamScheduleWithRunLoop(fsstream, DirectoryWatch.EventThread.loop, Core.kCFRunLoopDefaultMode)
        if not FSEvent.FSEventStreamStart(fsstream):
            FSEvent.FSEventStreamInvalidate(fsstream)
            FSEvent.FSEventStreamRelease(fsstream)
            raise Exception('Failed to start stream')
        self.EventThread.new_watch()

    def unregister_path(self, path):
        try:
            fsstream = self.path2stream[path]
            FSEvent.FSEventStreamStop(fsstream)
            FSEvent.FSEventStreamInvalidate(fsstream)
            FSEvent.FSEventStreamRelease(fsstream)
            del self.path2stream[path]
            del self.stream2path[fsstream]
        except KeyError:
            unhandled_exc_handler(False)

    def close(self):
        for path in self.path2stream.keys():
            self.unregister_path(path)

    def fsevents_callback(self, streamRef, info, numEvents, paths, eventFlags, eventId):
        try:
            ret = []
            events = [None] * numEvents
            root, realroot = self.stream2path[streamRef]
            for x in xrange(numEvents):
                events[x] = (root + paths[x].decode('utf-8')[len(realroot):], eventFlags[x])

            events.sort()
            if DEBUG:
                TRACE('Events %r' % events)
            for path, flag in events:
                if flag & kFSEventStreamEventFlagRootChanged:
                    path = ''
                    updated, deleted, changed = set(), set([root]), set()
                elif flag & kFSEventStreamEventFlagMustScanSubDirs:
                    TRACE('kFSEventStreamEventFlagMustScanSubDirs!!')
                    path = root
                    updated, deleted, changed = self.rescan(root, True)
                elif flag & (kFSEventStreamEventFlagUserDropped | kFSEventStreamEventFlagKernelDropped):
                    TRACE('kFSEventStreamEventFlagKernelDropped or kFSEventStreamEventFlagUserDropped %d!!' % flag)
                    path = self.dir
                    updated, deleted, changed = self.rescan(self.dir, True)
                elif flag & kFSEventStreamEventFlagHistoryDone:
                    continue
                else:
                    if path[-1] == '/':
                        path = path[:-1]
                    if DEBUG:
                        TRACE('Callback found %r' % path)
                    updated, deleted, changed = self.rescan(path)
                    if DEBUG and (len(updated) or len(deleted) or len(changed)):
                        TRACE('Rescan: Updated: %r Deleted: %r Changed: %r' % (updated, deleted, changed))
                if self.path in deleted:
                    self.queue.put(RootDeletedError)
                    continue
                ret += [ DirectoryEvent(os.path.join(path, x)) for x in deleted.union(updated) ] + [ DirectoryEvent(os.path.join(path, x), DirectoryEvent.TYPE_ATTR_ONLY) for x in changed ]

            for event in ret:
                self.queue.put(event)

        except Exception:
            unhandled_exc_handler()


class MetaDirectoryWatch(object):
    DirectoryWatch = DirectoryWatch

    def __init__(self):
        self.loop = None
        self.lock = threading.Lock()
        self.dataEvent = threading.Event()
        self.watchstream = []
        DirectoryWatch.EventThread = self

    def configure(self):
        with self.lock:
            self.loop = Core.CFRetain(Core.CFRunLoopGetCurrent())
        for watch, path, stream in self.watchstream:
            watch.schedule(path, stream)

        self.watchstream = []

    def __del__(self):
        if self.loop:
            Core.CFRelease(self.loop)

    def stopped(self):
        return False

    def wait(self, watches):
        ret = Core.CFRunLoopRunInMode(Core.kCFRunLoopDefaultMode, 3000000000.0, True)
        if ret == kCFRunLoopRunFinished:
            self.dataEvent.wait()
            self.dataEvent.clear()
        return [ w for w in watches if not w.queue.empty() ]

    def new_watch(self):
        self.dataEvent.set()

    def set_wakeup_event(self):
        self.dataEvent.set()
        with self.lock:
            if self.loop:
                Core.CFRunLoopStop(self.loop)
