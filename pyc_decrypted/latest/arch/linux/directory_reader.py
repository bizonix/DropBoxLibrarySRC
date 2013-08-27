#Embedded file name: arch/linux/directory_reader.py
from __future__ import absolute_import
import os
import fcntl
import termios
import array
import struct
import time
import sys
import select
import stat
import errno
from dropbox.bubble import Bubble, BubbleKind
from dropbox.fastwalk_bridge import fastwalk_with_exception_handling
from dropbox.dirtraverse import Directory, FILE_TYPE_POSIX_SYMLINK
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.dbexceptions import TimeoutError
from dropbox.directoryevent import DirectoryEvent
from dropbox.fileevents import SimpleMetaDirectoryWatchManager, EventsDroppedError, RootDeletedError, FileEvents
from dropbox.i18n import trans
from dropbox.linux_libc import inotify_init, inotify_add_watch, inotify_rm_watch
from .util import syslog, LOG_ERR
INCREASE_USER_INSTANCES_COMMAND = 'echo fs.inotify.max_user_instances=256 | sudo tee -a /etc/sysctl.conf; sudo sysctl -p'
INCREASE_USER_WATCHES_COMMAND = 'echo fs.inotify.max_user_watches=100000 | sudo tee -a /etc/sysctl.conf; sudo sysctl -p'

class InotifyEvent():
    __slots__ = ('wd', 'mask', 'cookie', 'name')
    __use_advanced_allocator__ = 1048576

    def __repr__(self):
        return 'InotifyEvent(wd=%r, mask=%r, cookie=%r, name=%r)' % (self.wd,
         self.mask,
         self.cookie,
         self.name)


class Inotify(object):
    EV_MASKS = zip(['IN_ACCESS',
     'IN_MODIFY',
     'IN_ATTRIB',
     'IN_CLOSE_WRITE',
     'IN_CLOSE_NOWRITE',
     'IN_OPEN',
     'IN_MOVED_FROM',
     'IN_MOVED_TO',
     'IN_CREATE',
     'IN_DELETE',
     'IN_DELETE_SELF',
     'IN_MOVE_SELF'], [ 1 << i for i in xrange(12) ]) + [('IN_IGNORED', 32768),
     ('IN_ISDIR', 1073741824),
     ('IN_Q_OVERFLOW', 16384),
     ('IN_UNMOUNT', 8192),
     ('IN_DONT_FOLLOW', 33554432),
     ('IN_MASK_ADD', 536870912),
     ('IN_ONESHOT', 2147483648L),
     ('IN_ONLYDIR', 16777216)]

    @classmethod
    def masks(cls, mask):
        return (k for k, v in cls.EV_MASKS if mask & v)

    def __init__(self, bubble_callback):
        self.bubble_callback = bubble_callback
        try:
            self.inotify_fd = inotify_init()
        except OSError as e:
            if e.errno == errno.EMFILE:
                d = dict(command=INCREASE_USER_INSTANCES_COMMAND)
                self.bubble_callback(Bubble(BubbleKind.UNABLE_TO_MONITOR_FILESYSTEM, trans(u'Please run "%(command)s" and restart Dropbox to fix the problem.') % d, trans(u"Dropbox can't monitor the filesystem")))
                syslog('Unable to monitor entire Dropbox folder hierarchy.' + ' ' + 'Please run "%(command)s" and restart Dropbox to fix the problem.' % d, level=LOG_ERR)
            raise

    def close(self):
        if hasattr(self, 'inotify_fd') and self.inotify_fd >= 0:
            os.close(self.inotify_fd)
            self.inotify_fd = -1

    def __del__(self):
        try:
            self.close()
        except:
            unhandled_exc_handler()

    def add_watch(self, name, mask):
        assert type(name) == str
        assert type(mask) == int
        try:
            return inotify_add_watch(self.inotify_fd, name, mask)
        except OSError as e:
            if e.errno == errno.ENOSPC:
                d = dict(command=INCREASE_USER_WATCHES_COMMAND)
                self.bubble_callback(Bubble(BubbleKind.UNABLE_TO_MONITOR_FILESYSTEM, trans(u'Please run "%(command)s" and restart Dropbox to fix the problem.') % d, trans(u"Dropbox can't monitor the filesystem")))
                syslog('Unable to monitor entire Dropbox folder hierarchy.' + ' ' + 'Please run "%(command)s" and restart Dropbox to fix the problem.' % d, level=LOG_ERR)
            raise

    def rm_watch(self, wd):
        assert type(wd) == int
        inotify_rm_watch(self.inotify_fd, wd)

    def get_events(self, block = True, timeout = None):
        realtimeout = timeout if block else 0
        while True:
            try:
                if realtimeout is not None and realtimeout < 0:
                    raise TimeoutError()
                start = time.time()
                a, b, c = select.select([self.inotify_fd], [], [], realtimeout)
                if len(a) == 0:
                    raise TimeoutError()
                else:
                    break
            except select.error as e:
                if e[0] == errno.EINTR:
                    took = time.time() - start
                    if realtimeout is not None:
                        realtimeout -= took
                else:
                    raise

        buf = array.array('i', [0])
        if -1 == fcntl.ioctl(self.inotify_fd, termios.FIONREAD, buf, True):
            raise u'Ioctl error'
        while True:
            try:
                data = os.read(self.inotify_fd, buf[0])
                break
            except OSError as e:
                if e.errno != errno.EINTR:
                    raise

        off = 0
        total = len(data)
        while total - off >= 16:
            ev = InotifyEvent()
            b = off + 16
            ev.wd, ev.mask, ev.cookie, alen = struct.unpack('iIII', data[off:b])
            try:
                ev.name = data[b:data.index('\x00', b, b + alen)]
            except:
                ev.name = data[b:b + alen]

            yield ev
            off += 16 + alen


for ev_name, ev_num in Inotify.EV_MASKS:
    setattr(Inotify, ev_name, ev_num)

Inotify.IN_CLOSE = Inotify.IN_CLOSE_WRITE | Inotify.IN_CLOSE_NOWRITE
Inotify.IN_MOVE = Inotify.IN_MOVED_FROM | Inotify.IN_MOVED_TO

class DirectoryWatch(object):

    def __init__(self, path, recurse = FileEvents.RECURSE_ALL, app = None):
        self.path = path
        self.recurse = recurse

        def show_bubble(bubble):
            try:
                app.ui_kit.show_bubble(bubble)
            except:
                unhandled_exc_handler()

        self.inotify = Inotify(show_bubble)
        self.wd_to_path = {}
        self.path_to_wd = {}
        self.symlinkdirs = set()
        self.symlinkfiles = set()
        self.path_to_watch = path
        if self.recurse == FileEvents.RECURSE_NONE or not os.path.isdir(path):
            self.watch_single_dir(self.path_to_watch)
        elif self.recurse == FileEvents.RECURSE_ALL:
            self.watch_all_subdirs(self.path_to_watch)
        elif self.recurse == FileEvents.RECURSE_ONE:
            self.watch_dir(self.path_to_watch, isroot=True)

    def watch_all_subdirs(self, path, isroot = False):
        theiter = iter(fastwalk_with_exception_handling(path, no_atime=True, dont_follow_up_to=self.path_to_watch, case_insensitive=False))
        try:
            root_p, root_children = theiter.next()
        except StopIteration:
            return

        self.watch_dir(root_p, isroot=True, children=root_children)
        for path, children in theiter:
            try:
                self.watch_dir(path, children=children)
            except OSError as e:
                unhandled_exc_handler()
                if e.errno == errno.ENOSPC:
                    return
            except:
                unhandled_exc_handler()

    def watch_single_dir(self, fp):
        wd = self.inotify.add_watch(fp.encode(sys.getfilesystemencoding()), Inotify.IN_MODIFY | Inotify.IN_CLOSE_WRITE | Inotify.IN_DELETE | Inotify.IN_CREATE | Inotify.IN_DELETE_SELF | Inotify.IN_MOVE_SELF)
        self.symlinkfiles.add(fp)
        self.path_to_wd[fp] = wd
        self.wd_to_path[wd] = fp
        TRACE('Watching file: %r, with id: %s', fp, wd)

    def watch_symlinked_file(self, fp):
        wd = self.inotify.add_watch(fp.encode(sys.getfilesystemencoding()), Inotify.IN_MODIFY | Inotify.IN_CLOSE_WRITE | Inotify.IN_DELETE_SELF | Inotify.IN_MOVE_SELF | Inotify.IN_ATTRIB)
        self.symlinkfiles.add(fp)
        self.path_to_wd[fp] = wd
        self.wd_to_path[wd] = fp
        TRACE('Watching file: %r, with id: %s', fp, wd)

    def unwatch_symlinked_file(self, fp):
        fp = os.path.normpath(fp)
        TRACE('removing symlink file watch: %r', fp)
        wd = self.path_to_wd[fp]
        del self.path_to_wd[fp]
        if wd in self.wd_to_path:
            try:
                self.inotify.rm_watch(wd)
            except:
                pass

            del self.wd_to_path[wd]
        self.symlinkfiles.remove(fp)
        TRACE('wd was: %d', wd)

    def check_children_for_watching(self, path, children):
        for dirent in children:
            try:
                fp = os.path.join(path, dirent.name)
                if dirent.type == FILE_TYPE_POSIX_SYMLINK and stat.S_ISREG(os.stat(fp).st_mode):
                    if fp in self.symlinkdirs:
                        wd = self.path_to_wd[fp]
                        del self.path_to_wd[fp]
                        del self.wd_to_path[wd]
                        self.symlinkdirs.remove(fp)
                    self.watch_symlinked_file(fp)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    unhandled_exc_handler()
            except:
                unhandled_exc_handler()

    def watch_dir(self, path, isroot = False, children = None):
        islink = os.path.islink(path)
        wd = self.folder_is_being_watched(path)
        if wd:
            try:
                assert islink == (path in self.symlinkdirs), ("A watched folder is a link but we didn't think it was: %r:%r" if islink else 'A watched folder is a not link but we thought was: %r:%r') % (path, wd)
            except:
                unhandled_exc_handler()
                (self.symlinkdirs.add if islink else self.symlinkdirs.remove)(path)

            return
        adir = os.path.normpath(path)
        mask = Inotify.IN_MODIFY | Inotify.IN_CLOSE_WRITE | Inotify.IN_CREATE | Inotify.IN_DELETE | Inotify.IN_MOVE | Inotify.IN_ATTRIB | (Inotify.IN_DELETE_SELF | Inotify.IN_MOVE_SELF if isroot else 0)
        ret = self.inotify.add_watch(adir.encode(sys.getfilesystemencoding()), mask)
        TRACE('Watching: %r, with id: %s', adir, ret)
        if islink:
            self.symlinkdirs.add(adir)
        self.wd_to_path[ret] = adir
        self.path_to_wd[adir] = ret
        if not children:
            with Directory(path, no_atime=True) as children:
                self.check_children_for_watching(path, children)
        else:
            self.check_children_for_watching(path, children)

    def unwatch_dir(self, adir):
        dir = os.path.normpath(adir)
        TRACE('removing watch: %r', dir)
        self.symlinkdirs.discard(dir)
        assert dir in self.path_to_wd
        wd = self.path_to_wd[dir]
        if wd in self.wd_to_path:
            try:
                self.inotify.rm_watch(wd)
            except:
                pass

            del self.wd_to_path[wd]
        del self.path_to_wd[dir]
        TRACE('wd was: %d' % wd)

    def unwatch(self, fp):
        if fp in self.symlinkfiles:
            return self.unwatch_symlinked_file(fp)
        return self.unwatch_dir(fp)

    def folder_is_being_watched(self, adir):
        try:
            return self.path_to_wd[os.path.normpath(adir)]
        except KeyError:
            return None

    def get_events(self, block = True, timeout = None):
        toret = []
        timeout = timeout if block else 0
        while not toret:
            if timeout is not None and timeout < 0:
                raise TimeoutError()
            start = time.time()
            for ev in self.inotify.get_events(True, timeout):
                try:
                    if ev.mask & Inotify.IN_Q_OVERFLOW:
                        assert ev.wd == -1, 'Overflow event yet wd was not -1??? %r' % (ev,)
                        ppath = None
                        TRACE('inotify returned IN_Q_OVERFLOW (filesystem events dropped)')
                        raise EventsDroppedError
                    ppath = self.wd_to_path[ev.wd]
                except KeyError:
                    ppath = None
                    continue
                finally:
                    if ppath is None:
                        p = ''.join(('!wd ', repr(ev.name)))
                    elif ev.name == '':
                        p = ppath.encode('utf-8')
                    else:
                        p = ppath.encode('utf-8') + '/' + ev.name
                    TRACE('%s %r', ','.join(Inotify.masks(ev.mask)), p)

                if ev.mask & Inotify.IN_UNMOUNT:
                    raise RootDeletedError
                if ev.mask & Inotify.IN_IGNORED:
                    if ppath in self.symlinkfiles:
                        if ppath == self.path_to_watch:
                            raise RootDeletedError
                        self.unwatch_symlinked_file(ppath)
                        toret.append(DirectoryEvent(ppath))
                    elif ppath in self.symlinkdirs:
                        self.unwatch_dir(ppath)
                        check = ppath + u'/'
                        for subpath in self.path_to_wd.keys():
                            if subpath.startswith(check):
                                self.unwatch(subpath)

                        toret.append(DirectoryEvent(ppath))
                    else:
                        TRACE('We got an ignored event on a wd that we were still watching: %r' % (ev,))
                    continue
                if ev.name == '':
                    if ev.mask & (Inotify.IN_MOVE_SELF | Inotify.IN_DELETE_SELF):
                        if ppath == self.path_to_watch:
                            raise RootDeletedError
                        thepathu = ppath
                    elif ppath in self.symlinkfiles:
                        thepathu = ppath
                    else:
                        continue
                else:
                    try:
                        thepathu = os.path.join(ppath, ev.name.decode(sys.getfilesystemencoding()))
                    except UnicodeDecodeError:
                        TRACE('non filesystem-encoded path in dropbox: %s' % os.path.join(self.wd_to_path[ev.wd].encode(sys.getfilesystemencoding()), ev.name))
                        continue

                if ev.mask & (Inotify.IN_CREATE | Inotify.IN_MOVED_TO):
                    issymlink = os.path.islink(thepathu)
                    isdir = os.path.isdir(thepathu) if issymlink else ev.mask & Inotify.IN_ISDIR
                    try:
                        if isdir:
                            if self.recurse == FileEvents.RECURSE_ALL:
                                self.watch_all_subdirs(thepathu)
                        elif issymlink:
                            self.watch_symlinked_file(thepathu)
                    except:
                        unhandled_exc_handler(False)

                elif thepathu in self.path_to_wd and ev.mask & (Inotify.IN_MOVED_FROM | Inotify.IN_DELETE):
                    if thepathu in self.symlinkfiles:
                        self.unwatch_symlinked_file(thepathu)
                    else:
                        if self.folder_is_being_watched(thepathu):
                            self.unwatch_dir(thepathu)
                        check = thepathu + u'/'
                        for subpath in self.path_to_wd.keys():
                            if subpath.startswith(check):
                                self.unwatch(subpath)

                if self.recurse == FileEvents.RECURSE_NONE and ev.name:
                    toret.append(DirectoryEvent(ppath))
                    continue
                evt = DirectoryEvent(thepathu)
                if ev.mask & Inotify.IN_CREATE:
                    evt.type = evt.TYPE_CREATE
                if ev.mask & Inotify.IN_MOVED_TO:
                    evt.type = evt.TYPE_RENAME_TO
                if ev.mask & Inotify.IN_DELETE:
                    evt.type = evt.TYPE_DELETE
                if ev.mask & Inotify.IN_MOVED_FROM:
                    evt.type = evt.TYPE_RENAME_FROM
                toret.append(evt)

            took = time.time() - start
            if timeout is not None:
                timeout -= took

        return toret

    def close(self):
        if self.inotify:
            self.inotify.close()
            self.inotify = None


class MetaDirectoryWatch(object):
    DirectoryWatch = DirectoryWatch

    def __init__(self):
        self.read, self.write = os.pipe()

    def configure(self):
        pass

    def wait(self, watches):
        fds = dict(((watch.inotify.inotify_fd, watch) for watch in watches))
        while True:
            try:
                l = fds.keys()
                l.append(self.read)
                a, b, c = select.select(l, [], [], None)
                if len(a) == 0:
                    raise TimeoutError()
                if self.read in a:
                    os.read(self.read, 1)
                return [ fds[fd] for fd in a if fd != self.read ]
            except select.error as e:
                if e[0] != errno.EINTR:
                    raise

    def set_wakeup_event(self):
        if os.write(self.write, 'a') != 1:
            TRACE('WTF')


class MetaDirectoryWatchManager(SimpleMetaDirectoryWatchManager):

    def __init__(self):
        super(MetaDirectoryWatchManager, self).__init__(MetaDirectoryWatch)
