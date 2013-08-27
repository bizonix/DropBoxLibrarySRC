#Embedded file name: arch/mac/filelevel_fsevents_reader.py
from __future__ import absolute_import
import os
import threading
import time
from dropbox.mac.version import MAC_VERSION, MOUNTAIN_LION
from pymac.constants import kCFAllocatorDefault, kCFRunLoopRunFinished, kFSEventStreamCreateFlagFileEvents, kFSEventStreamCreateFlagWatchRoot, kFSEventStreamEventFlagHistoryDone, kFSEventStreamEventFlagItemChangeOwner, kFSEventStreamEventFlagItemCreated, kFSEventStreamEventFlagItemFinderInfoMod, kFSEventStreamEventFlagItemInodeMetaMod, kFSEventStreamEventFlagItemIsFile, kFSEventStreamEventFlagItemIsDir, kFSEventStreamEventFlagItemIsSymlink, kFSEventStreamEventFlagItemModified, kFSEventStreamEventFlagItemRemoved, kFSEventStreamEventFlagItemRenamed, kFSEventStreamEventFlagItemXattrMod, kFSEventStreamEventFlagKernelDropped, kFSEventStreamEventFlagMustScanSubDirs, kFSEventStreamEventFlagNone, kFSEventStreamEventFlagRootChanged, kFSEventStreamEventFlagUserDropped
from pymac.dlls import Core, FSEvent
from pymac.helpers.core import python_to_property, releasing
from pymac.types import FSEventStreamCallback
from dropbox.directoryevent import DirectoryEvent
from dropbox.fileevents import RootDeletedError, FileEvents
from dropbox.native_queue import Queue, Empty
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, unhandled_exc_handler
assert MAC_VERSION >= MOUNTAIN_LION, 'File-level FSevents requires Mountain Lion to operate bug-free'
FILE_TYPE_MASK = kFSEventStreamEventFlagItemIsDir | kFSEventStreamEventFlagItemIsFile | kFSEventStreamEventFlagItemIsSymlink
FILE_MODIFIED_MASK = kFSEventStreamEventFlagItemModified | kFSEventStreamEventFlagItemXattrMod | kFSEventStreamEventFlagItemChangeOwner | kFSEventStreamEventFlagItemFinderInfoMod
FILE_POSS_CREATED_MASK = kFSEventStreamEventFlagItemInodeMetaMod | kFSEventStreamEventFlagItemCreated | kFSEventStreamEventFlagItemRenamed
FILE_POSS_DELETED_MASK = kFSEventStreamEventFlagItemInodeMetaMod | kFSEventStreamEventFlagItemRemoved | kFSEventStreamEventFlagItemRenamed
DEBUG = False

class FSEventThread(StoppableThread):

    def __init__(self):
        super(FSEventThread, self).__init__(name='FSEventThread')
        self._dataEvent = threading.Event()
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
                self._dataEvent.wait()
                self._dataEvent.clear()

        TRACE('Stopping...')

    def new_watch(self):
        self._dataEvent.set()

    def set_wakeup_event(self):
        self._dataEvent.set()
        if self.loop:
            Core.CFRunLoopStop(self.loop)


class DirectoryWatch(object):

    class _TimeoutError(Exception):
        pass

    EventThread = None

    def __init__(self, path, recurse = FileEvents.RECURSE_ALL, read_interval = 0.1, **kwargs):
        if not DirectoryWatch.EventThread or DirectoryWatch.EventThread.stopped():
            DirectoryWatch.EventThread = FSEventThread()
            DirectoryWatch.EventThread.start()
        self._stream2path = {}
        self._path2stream = {}
        self.queue = Queue()
        if path.endswith('/'):
            path = path.rstrip('/') or '/'
        self.path = path
        self.recurse = recurse
        self._c_fsevents_callback = FSEventStreamCallback(self._fsevents_callback)
        self._register_path(self.path)

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

    def _register_path(self, path):
        if path in self._path2stream:
            return
        with releasing(python_to_property([path])) as cfArray:
            fsstream = FSEvent.FSEventStreamCreate(kCFAllocatorDefault, self._c_fsevents_callback, None, cfArray, FSEvent.FSEventsGetCurrentEventId(), 0.1, kFSEventStreamCreateFlagWatchRoot | kFSEventStreamCreateFlagFileEvents)
        self.schedule(path, fsstream)

    def schedule(self, path, fsstream):
        with DirectoryWatch.EventThread.lock:
            if DirectoryWatch.EventThread.loop is None:
                DirectoryWatch.EventThread.watchstream.append((self, path, fsstream))
                return
        FSEvent.FSEventStreamScheduleWithRunLoop(fsstream, DirectoryWatch.EventThread.loop, Core.kCFRunLoopDefaultMode)
        if not FSEvent.FSEventStreamStart(fsstream):
            FSEvent.FSEventStreamInvalidate(fsstream)
            FSEvent.FSEventStreamRelease(fsstream)
            raise Exception('Failed to start stream')
        self._path2stream[path] = fsstream
        self._stream2path[fsstream] = (path, os.path.realpath(path))
        self.EventThread.new_watch()

    def _unregister_path(self, path):
        try:
            fsstream = self._path2stream[path]
            FSEvent.FSEventStreamStop(fsstream)
            FSEvent.FSEventStreamInvalidate(fsstream)
            FSEvent.FSEventStreamRelease(fsstream)
            del self._path2stream[path]
            del self._stream2path[fsstream]
        except KeyError:
            unhandled_exc_handler(False)

    def close(self):
        for path in self._path2stream.keys():
            self._unregister_path(path)

    def _fsevents_callback(self, streamRef, info, numEvents, paths, eventFlags, eventId):
        try:
            ret = []
            events = [None] * numEvents
            streamroot, realstreamroot = self._stream2path[streamRef]
            for x in xrange(numEvents):
                events[x] = (streamroot + paths[x].decode('utf-8')[len(realstreamroot):], eventFlags[x])

            events.sort()
            if DEBUG:
                pretty = ', '.join([ '(%r, 0x%x)' % event for event in events ])
                TRACE('Events: %s', pretty)
            for path, flags in events:
                if self.recurse == FileEvents.RECURSE_NONE:
                    if path != self.path:
                        continue
                elif self.recurse == FileEvents.RECURSE_ONE:
                    if path != self.path and os.path.dirname(path) != self.path:
                        continue
                updated, deleted, changed = set(), set(), set()
                if flags == kFSEventStreamEventFlagNone:
                    updated.add(path)
                elif flags & kFSEventStreamEventFlagRootChanged:
                    deleted.add(streamroot)
                elif flags & kFSEventStreamEventFlagMustScanSubDirs:
                    where = ''
                    if flags & kFSEventStreamEventFlagUserDropped:
                        where += ' userspace'
                    if flags & kFSEventStreamEventFlagKernelDropped:
                        where += ' kernel'
                    TRACE('kFSEventStreamEventFlagMustScanSubDirs!! where:%s', where)
                    ret.append(DirectoryEvent(path, DirectoryEvent.TYPE_DROPPED_EVENTS))
                    continue
                elif flags & kFSEventStreamEventFlagHistoryDone:
                    continue
                else:
                    changes_flags = flags & ~FILE_TYPE_MASK
                    if flags & kFSEventStreamEventFlagItemIsSymlink:
                        raise Exception("Can't handle symlink")
                    if changes_flags & FILE_POSS_DELETED_MASK:
                        deleted.add(path)
                    elif changes_flags & FILE_POSS_CREATED_MASK:
                        updated.add(path)
                    elif changes_flags & FILE_MODIFIED_MASK:
                        changed.add(path)
                if self.path in deleted:
                    self.queue.put(RootDeletedError)
                    continue
                ret += [ DirectoryEvent(x) for x in deleted.union(updated) ]
                ret += [ DirectoryEvent(x, DirectoryEvent.TYPE_ATTR_ONLY) for x in changed ]

            for event in ret:
                self.queue.put(event)

        except Exception:
            unhandled_exc_handler()


class MetaDirectoryWatch(object):
    DirectoryWatch = DirectoryWatch

    def __init__(self):
        self.loop = None
        self.lock = threading.Lock()
        self._dataEvent = threading.Event()
        self.watchstream = []
        DirectoryWatch.EventThread = self

    def configure(self):
        with self.lock:
            self.loop = Core.CFRetain(Core.CFRunLoopGetCurrent())
        for watch, path, stream in self.watchstream:
            assert 'WHAT THE FUCK WHERE did self.watchstream get modified?'
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
            self._dataEvent.wait()
            self._dataEvent.clear()
        return [ w for w in watches if not w.queue.empty() ]

    def new_watch(self):
        self._dataEvent.set()

    def set_wakeup_event(self):
        self._dataEvent.set()
        with self.lock:
            if self.loop:
                Core.CFRunLoopStop(self.loop)
