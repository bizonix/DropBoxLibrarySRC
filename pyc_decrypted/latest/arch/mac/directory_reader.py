#Embedded file name: arch/mac/directory_reader.py
from __future__ import absolute_import
import errno
import os
import select
import time
from dropbox.directoryevent import DirectoryEvent
from dropbox.fileevents import NoWorkingWatchError, RootDeletedError, FileEvents
from dropbox.functions import is_case_insensitive_path
from dropbox.mac.version import MAC_VERSION, LEOPARD, MOUNTAIN_LION
from dropbox.trace import TRACE, unhandled_exc_handler
from .directory_reader_helper import RescanMixin
from arch.mac.daemon_reader import MetaDirectoryWatch as DBFSEventMetaDirectoryWatch

class DirectoryWatch(RescanMixin):
    RESCAN_TIME = 60

    def __init__(self, path, recurse = FileEvents.RECURSE_ALL, **kwargs):
        self.path_map = {}
        self.fd_map = {}
        self.kq = select.kqueue()
        self.dir = None
        self.root = path
        self.path = path
        try:
            self.case_insensitive = is_case_insensitive_path(self.path)
        except Exception:
            unhandled_exc_handler()
            self.case_insensitive = True

        self.recurse = recurse
        self.isdir = os.path.isdir(self.path)
        self.add_subdir(self.path, no_trace=True)
        if self.isdir:
            self.next_rescan = time.time() + self.RESCAN_TIME
        else:
            self.next_rescan = None

    def add_subdir(self, path, no_trace = False):
        if path in self.path_map:
            return
        if not no_trace:
            TRACE('Adding directory %s' % path)
        dirfd = os.open(path, 32768)
        event = select.kevent(dirfd, select.KQ_FILTER_VNODE, select.KQ_EV_ADD | select.KQ_EV_CLEAR | select.KQ_EV_ENABLE, fflags=select.KQ_NOTE_ATTRIB | select.KQ_NOTE_DELETE | select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_RENAME, data=dirfd)
        self.kq.control([event], 0)
        self.path_map[path] = (dict(), dict(), dirfd)
        self.fd_map[dirfd] = path
        self.rescan(path, no_trace=True)

    def close(self):
        self.kq.close()

    def del_subdir(self, path):
        for k in self.path_map.keys():
            if k == path or k.startswith(path + os.path.sep):
                dirs, files, dirfd = self.path_map[k]
                event = select.kevent(dirfd, select.KQ_FILTER_VNODE, select.KQ_EV_DELETE)
                self.kq.control([event], 0)
                os.close(dirfd)
                del self.fd_map[dirfd]
                del self.path_map[k]
                TRACE('Deleting %r from dir map' % path)

    def get_events(self, block = True, timeout = None):
        timeout = timeout if block else 0
        ret = []
        evts = self.kq.control([], 1, timeout)
        for e in evts:
            if e.ident in self.fd_map:
                path = self.fd_map[e.ident]
                if e.fflags & (select.KQ_NOTE_DELETE | select.KQ_NOTE_RENAME):
                    if e.fflags & select.KQ_NOTE_DELETE and path in self.path_map and os.path.isdir(path):
                        self.del_subdir(path)
                        dirs, files, dirfd = self.path_map[os.path.dirname(os.path.normpath(path))]
                        del dirs[os.path.basename(os.path.normpath(path))]
                    if path == self.path:
                        raise RootDeletedError
                    while True:
                        idx = path.rfind(os.path.sep)
                        if idx == -1:
                            path = self.root
                            break
                        path = path[:idx]
                        if path in self.path_map:
                            break

                if not self.isdir or self.recurse == FileEvents.RECURSE_NONE:
                    updated = set([path])
                    deleted = changed = set()
                else:
                    updated, deleted, changed = self.rescan(path)
                if updated or deleted or changed:
                    TRACE('Updated: %r Deleted: %r Changed:%r' % (updated, deleted, changed))
                ret = [ DirectoryEvent(os.path.join(path, x)) for x in deleted.union(updated) ] + [ DirectoryEvent(os.path.join(path, x), DirectoryEvent.TYPE_ATTR_ONLY) for x in changed ]

        if self.next_rescan and time.time() > self.next_rescan:
            updated, deleted, changed = self.rescan(self.root, True)
            self.next_rescan = time.time() + self.RESCAN_TIME
            if len(updated) or len(deleted) or len(changed):
                TRACE('Rescan: Updated: %r Deleted: %r Changed: %r' % (updated, deleted, changed))
            ret.extend([ DirectoryEvent(os.path.join(self.root, x)) for x in deleted.union(updated) ] + [ DirectoryEvent(os.path.join(self.root, x), DirectoryEvent.TYPE_ATTR_ONLY) for x in changed ])
        return ret


class MetaDirectoryWatch(object):
    DirectoryWatch = DirectoryWatch

    def __init__(self):
        self.read, self.write = os.pipe()

    def wait(self, watches):
        fds = dict(((watch.kq, watch) for watch in watches))
        while True:
            try:
                timeout = None
                timeout_watch = None
                now = time.time()
                for watch in watches:
                    if watch.next_rescan and (timeout is None or watch.next_rescan < timeout):
                        timeout = watch.next_rescan
                        timeout_watch = watch

                l = fds.keys()
                l.append(self.read)
                a, b, c = select.select(l, [], [], max(0, timeout - now) if timeout else None)
                if len(a) == 0:
                    return [timeout_watch]
                if self.read in a:
                    os.read(self.read, 1)
                return [ fds[fd] for fd in a if fd != self.read ]
            except select.error as e:
                if e[0] != errno.EINTR:
                    raise

    def configure(self):
        pass

    def set_wakeup_event(self):
        if os.write(self.write, 'a') != 1:
            TRACE('WTF')


FSEventMetaDirectoryWatch = 'FSEventMetaDirectoryWatch'
if MAC_VERSION >= LEOPARD:
    try:
        from arch.mac.fsevents_reader import MetaDirectoryWatch as FSEventMetaDirectoryWatch
    except Exception:
        unhandled_exc_handler()
        TRACE('No support for FSEvents (import failed)')

else:
    TRACE('No support for FSEvents (OS X version too old)')
FileLevelFSEventMetaDirectoryWatch = 'FileLevelFSEventMetaDirectoryWatch'
if MAC_VERSION >= MOUNTAIN_LION:
    try:
        from arch.mac.filelevel_fsevents_reader import MetaDirectoryWatch as FileLevelFSEventMetaDirectoryWatch
    except Exception:
        unhandled_exc_handler()
        TRACE('No support for file-level FSEvents')

class MetaDirectoryWatchManager(object):

    def __init__(self):
        self.cur = None

    def next(self, reason = None):
        if self.cur is None:
            self.cur = DBFSEventMetaDirectoryWatch
            try:
                return DBFSEventMetaDirectoryWatch()
            except:
                unhandled_exc_handler()
                reason = 'PERM'

        if self.cur == DBFSEventMetaDirectoryWatch and reason in ('PERM', None):
            if FSEventMetaDirectoryWatch == 'FSEventMetaDirectoryWatch':
                reason = 'BROKEN'
            else:
                self.cur = FSEventMetaDirectoryWatch
                try:
                    return FSEventMetaDirectoryWatch()
                except:
                    unhandled_exc_handler()
                    reason = 'BROKEN'

        if self.cur in [DBFSEventMetaDirectoryWatch, FSEventMetaDirectoryWatch] and reason in ('BROKEN', None):
            self.cur = MetaDirectoryWatch
            try:
                return MetaDirectoryWatch()
            except:
                unhandled_exc_handler()
                reason = 'BROKEN'

        raise NoWorkingWatchError()
