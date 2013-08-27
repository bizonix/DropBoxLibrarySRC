#Embedded file name: arch/win32/directory_reader.py
from __future__ import absolute_import
import os
import threading
import time
import contextlib
import win32file
import win32con
import win32api
import win32event
import ntsecuritycon
import pywintypes
from dropbox.dbexceptions import TimeoutError
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.globals import dropbox_globals
from dropbox.functions import is_short_path
from dropbox.directoryevent import DirectoryEvent
from dropbox.fileevents import SimpleMetaDirectoryWatchManager, UnrecoverableWatchError, EventsDroppedError, RootDeletedError, FileEvents
from .util import path_is_remote

class DirectoryWatch(object):
    EV_CREATED, EV_DELETED, EV_UPDATED, EV_MOVE_FROM, EV_MOVE_TO = range(1, 6)
    __actions_map = {EV_CREATED: 'Created',
     EV_DELETED: 'Deleted',
     EV_UPDATED: 'Updated',
     EV_MOVE_FROM: 'Renamed from something',
     EV_MOVE_TO: 'Renamed to something'}

    def __init__(self, path, recurse = FileEvents.RECURSE_ALL, **kwargs):
        self.ov = pywintypes.OVERLAPPED()
        self.ov.hEvent = win32event.CreateEvent(None, 1, 0, None)
        self.buf = win32file.AllocateReadBuffer(65536 if path_is_remote(path) else 262144)
        self.requestsent = False
        self.path = path
        self.recurse = recurse
        self.isdir = os.path.isdir(self.path)
        self.dir = self.path if self.isdir else os.path.split(self.path)[0]
        self.has_error = False
        self.hDir = win32file.CreateFileW(self.dir, ntsecuritycon.FILE_LIST_DIRECTORY, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE, None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS | win32con.FILE_FLAG_OVERLAPPED, None)
        self.send_request()

    def close(self):
        try:
            win32file.CloseHandle(self.ov.hEvent)
        except:
            unhandled_exc_handler()

        try:
            win32file.CloseHandle(self.hDir)
        except:
            unhandled_exc_handler()

    def send_request(self):
        if not self.requestsent:
            ret = win32file.ReadDirectoryChangesW(self.hDir, self.buf, self.recurse == FileEvents.RECURSE_ALL and self.isdir, win32con.FILE_NOTIFY_CHANGE_FILE_NAME | win32con.FILE_NOTIFY_CHANGE_DIR_NAME | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES | win32con.FILE_NOTIFY_CHANGE_SIZE | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE | win32con.FILE_NOTIFY_CHANGE_SECURITY, self.ov)
            if ret is not None:
                raise Exception('problem')
            self.requestsent = True

    def get_events(self, block = True, timeout = None):
        while True:
            assert block or timeout is None
            if self.has_error:
                raise self.has_error
            self.send_request()
            if block:
                if timeout is None:
                    tov = win32event.INFINITE
                else:
                    tov = int(timeout * 1000)
            else:
                tov = 0
            start = time.time()
            ret = win32event.WaitForSingleObject(self.ov.hEvent, tov)
            if ret == win32event.WAIT_OBJECT_0:
                win32event.ResetEvent(self.ov.hEvent)
                if timeout is not None:
                    took = time.time() - start
                    timeout -= took
                self.requestsent = False
                try:
                    nbytes = win32file.GetOverlappedResult(self.hDir, self.ov, True)
                except pywintypes.error as e:
                    if e[0] == 64:
                        raise UnrecoverableWatchError
                    else:
                        raise

                if nbytes == 0:
                    TRACE('ReadDirectoryChangesW buffer overflowed (filesystem events dropped)')
                    raise EventsDroppedError
                toret = []
                for action, fn in win32file.FILE_NOTIFY_INFORMATION(self.buf, nbytes):
                    full_filename = os.path.join(self.dir, fn)
                    if action == DirectoryWatch.EV_UPDATED and os.path.isdir(full_filename):
                        TRACE('%s %r (dir)', DirectoryWatch.__actions_map.get(action, 'Unknown'), full_filename)
                        continue
                    if is_short_path(full_filename):
                        TRACE('possible short path %r' % full_filename)
                        if action in (DirectoryWatch.EV_DELETED, DirectoryWatch.EV_MOVE_FROM):
                            full_filename, basename = os.path.split(full_filename)
                            if is_short_path(basename):
                                basename = None
                                action = DirectoryWatch.EV_UPDATED
                            l_is_83_path = is_short_path(full_filename)
                        else:
                            basename = None
                            l_is_83_path = True
                        stop_continue = False
                        while l_is_83_path:
                            try:
                                full_filename = win32api.GetLongPathNameW(full_filename)
                            except pywintypes.error as e:
                                if e[0] in (2, 3, 5, 18, 32):
                                    if action in (DirectoryWatch.EV_DELETED, DirectoryWatch.EV_MOVE_FROM):
                                        basename = None
                                        action = DirectoryWatch.EV_UPDATED
                                    full_filename = os.path.dirname(full_filename)
                                else:
                                    unhandled_exc_handler()
                                    TRACE('GetLongPathNameW failed... Skipping this file %r' % full_filename)
                                    stop_continue = True
                                    break
                                l_is_83_path = is_short_path(full_filename)
                            else:
                                break

                        if stop_continue:
                            continue
                        if basename:
                            full_filename = os.path.join(full_filename, basename)
                    if (not self.isdir or self.recurse == FileEvents.RECURSE_NONE) and full_filename != self.path:
                        continue
                    if full_filename == self.path:
                        if action in (DirectoryWatch.EV_DELETED, DirectoryWatch.EV_MOVE_FROM):
                            raise RootDeletedError
                        if action == DirectoryWatch.EV_UPDATED and self.isdir:
                            TRACE('Faking EventsDroppedError to trigger a reindex')
                            raise EventsDroppedError
                    TRACE('%s %r', DirectoryWatch.__actions_map.get(action, 'Unknown'), full_filename)
                    evt = DirectoryEvent(full_filename)
                    if action == DirectoryWatch.EV_CREATED:
                        evt.type = evt.TYPE_CREATE
                    elif action == DirectoryWatch.EV_DELETED:
                        evt.type = evt.TYPE_DELETE
                    elif action == DirectoryWatch.EV_MOVE_FROM:
                        evt.type = evt.TYPE_RENAME_FROM
                    elif action == DirectoryWatch.EV_MOVE_TO:
                        evt.type = evt.TYPE_RENAME_TO
                    toret.append(evt)

                if toret:
                    return toret
                if timeout is not None and timeout < 0:
                    raise TimeoutError()
                else:
                    continue
            else:
                raise TimeoutError() if ret == win32event.WAIT_TIMEOUT else Exception('badness')


class MetaDirectoryWatch(object):
    DirectoryWatch = DirectoryWatch

    def __init__(self):
        self.wakeupEvent = win32event.CreateEvent(None, 0, 0, None)

    def configure(self):
        pass

    def wait(self, watches):
        assert len(watches) + 1 <= win32event.MAXIMUM_WAIT_OBJECTS
        events = []
        ready = []
        timeout = win32event.INFINITE
        for watch in watches:
            try:
                watch.send_request()
            except Exception:
                unhandled_exc_handler()
                timeout = 0
                watch.has_error = UnrecoverableWatchError
                ready.append(watch)
            else:
                events.append(watch.ov.hEvent)

        ret = win32event.WaitForMultipleObjects(events + [self.wakeupEvent], 0, timeout) - win32event.WAIT_OBJECT_0
        while ret >= 0 and ret < len(watches):
            ready.append(watches[ret])
            watches = watches[ret + 1:]
            events = events[ret + 1:]
            if events:
                ret = win32event.WaitForMultipleObjects(events, 0, 0) - win32event.WAIT_OBJECT_0
            else:
                break

        return ready

    def set_wakeup_event(self):
        win32event.SetEvent(self.wakeupEvent)


class MetaDirectoryWatchManager(SimpleMetaDirectoryWatchManager):

    def __init__(self):
        super(MetaDirectoryWatchManager, self).__init__(MetaDirectoryWatch)
