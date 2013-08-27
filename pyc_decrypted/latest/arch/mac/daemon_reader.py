#Embedded file name: arch/mac/daemon_reader.py
from __future__ import absolute_import
import os
import socket
import time
import posix
import threading
import subprocess32 as subprocess
import signal
import errno
import unicodedata
import fcntl
import re
from dropbox.db_thread import db_thread
from dropbox.dbexceptions import TimeoutError
from dropbox.directoryevent import DirectoryEvent
from dropbox.fastwalk_bridge import fastwalk_with_exception_handling
from dropbox.fileevents import EventsDroppedError, FileEvents, MetaWatchFailure, RootDeletedError
from dropbox.functions import desanitize, is_case_insensitive_path, verify_file_perms_helper
from dropbox.globals import dropbox_globals
from dropbox.mac.helper_installer import HELPERS_DIR, install_dropbox_helpers_with_fallback
from dropbox.mac.internal import binaries_ready, BINARIES_READY_TIMEOUT
from dropbox.native_event import AutoResetEvent
from dropbox.native_queue import Queue, Empty
from dropbox.nfcdetector import is_nfc
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.ultimatesymlinkresolver import UltimateSymlinkResolver
bad_path_re = re.compile('(^\\./)|(^\\.\\./)|(/\\./)|(/\\.\\./)|(/\\.$)|(/\\.\\.$)|(/$)')

class DBFSEventThread(StoppableThread):

    def __init__(self):
        super(DBFSEventThread, self).__init__(name='DBFSEventThread')
        self.installed = False
        self.dbfseventsd_popen = None
        self.serv = None
        try:
            self.connect(just_started=False)
            TRACE('Connecting to a pre-existing dbfseventsd')
        except DirectoryWatch.FatalError:
            self.start_dbfseventsd()
            try:
                self.connect()
            except DirectoryWatch.FatalError:
                DirectoryWatch.FatalError.trace_debug_info()
                raise

        self.queuemap = {}
        self.lock = threading.Lock()
        self.dataEvent = AutoResetEvent()
        self.error = None
        self.rapid_dropped_count = 0
        self.last_start = time.time()
        try:
            del dropbox_globals['dbfseventsd_is_broken']
        except KeyError:
            pass

    def connect(self, just_started = True):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            if just_started:
                sock.settimeout(0.2)
                start = time.time()
            while True:
                try:
                    sock.connect('/.dbfseventsd')
                    break
                except Exception as e:
                    if not just_started or time.time() - start > 1.0:
                        self.killall_dbfseventsd()
                        dropbox_globals['dbfseventsd_is_broken'] = True
                        unhandled_exc_handler(False)
                        raise DirectoryWatch.FatalError('error connecting to /.dbfseventsd: %r' % (e,))
                    else:
                        time.sleep(0.2)

        except:
            sock.close()
            raise

        sock.settimeout(None)
        self.serv = sock
        TRACE('Connected to dbfseventsd!')

    def set_wakeup_event(self):
        self.close()

    def log(self):
        if self.dbfseventsd_popen:
            try:
                for line in self.dbfseventsd_popen.stderr:
                    TRACE('dbfseventsd: %s', line.strip())

            except IOError as e:
                if e.errno != errno.EAGAIN:
                    unhandled_exc_handler()
            except Exception:
                unhandled_exc_handler()

    def handle_drop(self, line, watch2q, kill_dbfseventsd = True):
        if not self.stopped():
            self.log()
            if self.last_start < time.time() - 10:
                self.rapid_dropped_count = 1
            else:
                self.rapid_dropped_count += 1
            if self.rapid_dropped_count >= 5:
                raise Exception('Too many dropped messages. Giving up on dbfseventsd')
            if kill_dbfseventsd:
                TRACE('dbfsevents dying because line = %r', line)
                self.close()
                self.start_dbfseventsd()
                self.connect()
            for _, q in watch2q:
                TRACE('dbfseventsd connection dropped')
                q.put(EventsDroppedError)

            self.dataEvent.set()

    def run(self):
        try:
            buf = ''
            while not self.stopped():
                self.log()
                recv = self.serv.recv(16384)
                with self.lock:
                    watch2q = self.queuemap.items()
                if recv == '':
                    self.handle_drop(recv, watch2q)
                    continue
                if buf:
                    buf += recv
                else:
                    buf = recv
                cur, _, buf = buf.rpartition('\n')
                if cur:
                    try:
                        lines = cur.decode('utf-8').split(u'\n')
                    except UnicodeDecodeError:
                        slines = cur.split('\n')
                        lines = []
                        for sline in slines:
                            try:
                                lines.append(sline.decode('utf-8'))
                            except UnicodeDecodeError:
                                TRACE('bad unicode line from dbfseventsd, line was: ' + repr(sline))

                    if lines:
                        try:
                            for watch, q in watch2q:
                                events = watch._process_events(lines)
                                if events:
                                    q.put(events)
                                    self.dataEvent.set()

                        except EventsDroppedError:
                            self.handle_drop('dropped', watch2q, kill_dbfseventsd=False)

        except Exception:
            self.log()
            unhandled_exc_handler()
            self.error = True

        self.dataEvent.set()
        self.close()
        TRACE('Stopping...')

    def register(self, watch, queue):
        with self.lock:
            self.queuemap[watch] = queue

    def unregister(self, watch):
        with self.lock:
            try:
                del self.queuemap[watch]
            except Exception:
                unhandled_exc_handler()

    @staticmethod
    def kill_pid(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError as e:
            if e.errno != errno.ESRCH:
                raise

    def killall_dbfseventsd(self):
        if self.dbfseventsd_popen is not None:
            self.log()
            pid = self.dbfseventsd_popen.pid
            self.dbfseventsd_popen = None
            TRACE('Killing dbfseventsd %d' % pid)
            try:
                self.kill_pid(pid)
                a = 0
                while (0, 0) == os.waitpid(pid, posix.WNOHANG) and a < 2:
                    time.sleep(0.1)
                    a += 0.1

            except Exception as e:
                if not isinstance(e, OSError):
                    unhandled_exc_handler()

    def close(self):
        if self.serv is not None:
            try:
                self.serv.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                if not isinstance(e, socket.error) or e[0] != errno.ENOTCONN:
                    unhandled_exc_handler()

            try:
                self.serv.close()
            except Exception:
                unhandled_exc_handler()

            self.serv = None
        self.killall_dbfseventsd()

    def install_dbfsevents(self):
        if self.installed:
            return
        if not binaries_ready.wait(timeout=BINARIES_READY_TIMEOUT):
            raise DirectoryWatch.FatalError('Not trusting dbfseventsd')
        dbfsevents_info = {'dbfseventsd': {'user': 'root',
                         'mode': 2377,
                         'kill': signal.SIGKILL}}
        if not install_dropbox_helpers_with_fallback(dbfsevents_info):
            raise DirectoryWatch.FatalError("Couldn't install dbfseventd")
        self.installed = True

    def start_dbfseventsd(self):
        self.install_dbfsevents()
        dbfseventsd_path = os.path.join(HELPERS_DIR, 'dbfseventsd')
        env = dict(os.environ)
        env['DBFSEVENTSD_ALARM'] = '3'
        self.dbfseventsd_popen = subprocess.Popen([dbfseventsd_path], close_fds=True, cwd=u'/', env=env, stderr=subprocess.PIPE)
        flags = fcntl.fcntl(self.dbfseventsd_popen.stderr, fcntl.F_GETFL)
        fcntl.fcntl(self.dbfseventsd_popen.stderr, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self.last_start = time.time()
        TRACE('Started up dbfseventsd (pid %d)', self.dbfseventsd_popen.pid)


class DirectoryWatch(object):

    class FatalError(Exception):

        @staticmethod
        def trace_debug_info():
            TRACE('!! Getting info on /.dbfseventsd ...')
            try:
                output = subprocess.check_output('ls -l /.dbfseventsd || true', stderr=subprocess.STDOUT, shell=True)
                for line in output.rstrip().split('\n'):
                    TRACE('!!  Output: %s', line)

            except Exception as e:
                TRACE('!!  Failed: %r', e)

            TRACE('!! Getting info on dbfseventsd processes ...')
            try:
                TRACE('!!  (Columns: user,group,pgid,ppid,pid,pcpu,command)')
                output = subprocess.check_output("ps -Ao 'user,group,pgid,ppid,pid,pcpu,command' | grep dbfseventsd | grep -v grep || true", stderr=subprocess.STDOUT, shell=True)
                for line in output.rstrip().split('\n'):
                    TRACE('!!  Output: %s', line)

            except Exception as e:
                TRACE('!!  Failed: %r', e)

    EventThread = None

    def __init__(self, path, recurse = FileEvents.RECURSE_ALL, **kwargs):
        if not DirectoryWatch.EventThread or DirectoryWatch.EventThread.stopped():
            DirectoryWatch.EventThread = DBFSEventThread()
            DirectoryWatch.EventThread.start()
        try:
            self.case_insensitive = is_case_insensitive_path(path)
        except Exception:
            unhandled_exc_handler()
            self.case_insensitive = True

        self.symlink_resolver = UltimateSymlinkResolver(case_insensitive=self.case_insensitive, debug=None, log=None)
        self.test_healthiness = []
        self.last_watch_time = {}
        self.last_watch_time_update = {}
        self.queue = Queue()
        newwatch = os.path.normpath(os.path.realpath(path))
        self.symlink_resolver.add_watch(newwatch, recurse)
        self.last_watch_time[newwatch] = 0
        self.path = path
        self.realpath = newwatch
        self.realpath_lt = os.path.join(newwatch.lower() if self.case_insensitive else newwatch, '')
        self.realPathFix = self.path != newwatch
        self.recurse = recurse
        try:
            uid = os.geteuid()
            groups = set(os.getgroups())
            while newwatch:
                if not verify_file_perms_helper(newwatch, perm_list=['exec', 'read'], uid=uid, groups=groups):
                    st = os.stat(newwatch)
                    report_bad_assumption('Bad permissions on directory %r %s', newwatch, oct(st.st_mode))
                if newwatch == u'/':
                    break
                newwatch = os.path.dirname(newwatch)

        except Exception:
            unhandled_exc_handler()

        self.events2funcs = {u'update': (DirectoryWatch.path_convert, self._handle_generic),
         u'stat': (DirectoryWatch.path_convert, self._handle_generic),
         u'xattr': (DirectoryWatch.path_convert, self._handle_generic),
         u'create': (DirectoryWatch.path_convert, self._handle_create),
         u'delete': (DirectoryWatch.path_convert, self._handle_delete),
         u'rename': (DirectoryWatch.path_convert_2, self._handle_rename),
         u'exchange': (DirectoryWatch.path_convert_2, self._handle_exchange),
         u'fork': (DirectoryWatch.path_convert_fork, self._handle_fork)}
        DirectoryWatch.EventThread.register(self, self.queue)

    def _process_events(self, events):
        ret = []
        for ev_string, path in self._process_events_helper(events):
            try:
                if ev_string in (u'broken_symlink', u'rename_from', u'delete') and self.realpath_lt.startswith(os.path.join(path.lower() if self.case_insensitive else path, '')):
                    return RootDeletedError
                for p2 in self.symlink_resolver.reverse_resolve_symlinks(path):
                    TRACE(u'%s %r', ev_string, p2)
                    if self.realPathFix and p2.startswith(self.realpath):
                        if self.realpath == p2:
                            p2 = self.path
                        elif self.path != p2:
                            p2 = os.path.join(self.path, p2[len(self.realpath) + 1:])
                    evt = DirectoryEvent(p2)
                    if ev_string in (u'xattr', u'stat', u'fork'):
                        evt.type = evt.TYPE_ATTR_ONLY
                    elif ev_string == u'create':
                        evt.type = evt.TYPE_CREATE
                    elif ev_string == u'delete':
                        evt.type = evt.TYPE_DELETE
                    elif ev_string == u'rename_to':
                        evt.type = evt.TYPE_RENAME_TO
                    elif ev_string == u'rename_from':
                        evt.type = evt.TYPE_RENAME_FROM
                    ret.append(evt)

            except Exception:
                unhandled_exc_handler()

        return ret

    def fixup_fork(self, path, inode):
        try:
            st = os.stat(path)
            if st.st_ino == inode:
                return path
        except OSError:
            pass

        try:
            for dirpath, ents in fastwalk_with_exception_handling(os.path.dirname(path), case_insensitive=self.case_insensitive):
                for dirent in ents:
                    if dirent.inode == inode:
                        return dirent.fullpath

                TRACE('Inode %d not found for path %r' % (inode, path))
                return None

        except OSError as e:
            if e.errno != errno.ENOENT:
                unhandled_exc_handler()
            return None

    def _handle_create(self, ev, path, ret):
        for x in self.symlink_resolver.file_created(path):
            ret.append((u'fixed_symlink', x))

        if ev:
            self._handle_generic(ev, path, ret)

    def _handle_delete(self, ev, path, ret):
        for x in self.symlink_resolver.file_deleted(path):
            ret.append((u'broken_symlink', x))

        if ev:
            self._handle_generic(ev, path, ret)

    def _handle_generic(self, ev, path, ret):
        ret.append((ev, path))

    def _handle_exchange(self, ev, values, ret):
        if values[0]:
            ret.append((u'exchange_from', values[0]))
        if values[1]:
            ret.append((u'exchange_to', values[1]))

    def _handle_fork(self, ev, values, ret):
        path = self.fixup_fork(values[0], values[1])
        if path:
            ret.append((ev, path))

    def _handle_rename(self, ev, values, ret):
        if values[0]:
            self._handle_delete(None, values[0], ret)
        if values[1]:
            self._handle_create(None, values[1], ret)
        if values[0]:
            ret.append((u'rename_from', values[0]))
        if values[1]:
            ret.append((u'rename_to', values[1]))

    def _process_events_helper(self, lines):
        ret = []
        for line in lines:
            if line == u'dropped':
                TRACE("dbfseventsd returned 'dropped'")
                raise EventsDroppedError
            ev, data = line.split(u'\t', 1)
            try:
                parser, handler = self.events2funcs[ev]
                handler(ev, parser(data), ret)
            except Exception:
                unhandled_exc_handler()

        return ret

    @staticmethod
    def path_convert(path):
        if bad_path_re.search(path):
            o_path = path
            path = os.path.normpath(o_path.encode('utf-8')).decode('utf-8')
        ret = desanitize(path)
        if is_nfc(ret):
            ret = unicodedata.normalize('NFD', ret)
        return ret

    @staticmethod
    def path_convert_2(data):
        return [ DirectoryWatch.path_convert(a) for a in data.split(u'\t', 1) ]

    @staticmethod
    def path_convert_fork(data):
        path, inode = data.split(u'\t', 1)
        return (DirectoryWatch.path_convert(path), int(inode))

    CHECK_INTERVAL = 1200
    WAIT_TIME = 3

    def get_events_fatal_check(self):
        while True:
            oldest_test = time.time()
            flag = False
            curtime = time.time()
            for watch, t in self.last_watch_time.iteritems():
                if curtime - t >= DirectoryWatch.CHECK_INTERVAL:
                    try:
                        fn = os.path.join(watch, '.~%s.tmp' % int(time.time()))
                        open(fn, 'w').close()
                        try:
                            os.remove(fn)
                        except OSError:
                            unhandled_exc_handler(False)

                        self.test_healthiness.append([watch, time.time() + DirectoryWatch.WAIT_TIME, fn.lower()])
                        del fn
                        self.last_watch_time_update[watch] = curtime
                        flag = True
                        TRACE('Checking healthiness of %r, %r' % (watch, curtime))
                    except Exception:
                        unhandled_exc_handler()

                else:
                    oldest_test = min(t, oldest_test)

            if flag:
                self.last_watch_time.update(self.last_watch_time_update)
                self.last_watch_time_update.clear()
            if len(self.test_healthiness) > 0:
                soonest_to_expire = min((elt[1] for elt in self.test_healthiness))
                try:
                    evs = list(self._process_events(DirectoryWatch._lines2events(self._multiget(True, max(0, soonest_to_expire - time.time())))))
                except TimeoutError:
                    dropbox_globals['dbfseventsd_is_broken'] = True
                    raise DirectoryWatch.FatalError()
                else:
                    self.test_healthiness = [ elt for elt in self.test_healthiness if not any((ev.path.lower() == elt[2] for ev in evs)) ]
                    if len(self.test_healthiness) > 0:
                        soonest_to_expire = min((elt[1] for elt in self.test_healthiness))
                        if soonest_to_expire <= time.time():
                            dropbox_globals['dbfseventsd_is_broken'] = True
                            raise DirectoryWatch.FatalError()
                    else:
                        TRACE('Dbfsevents is working!')
                    return evs

            else:
                try:
                    return list(self._process_events(DirectoryWatch._lines2events(self._multiget(True, oldest_test + DirectoryWatch.CHECK_INTERVAL - time.time()))))
                except TimeoutError:
                    continue

    def get_events(self, block = True, timeout = None):
        if block or timeout is not None:
            raise NotImplementedError()
        full_list = []
        while True:
            try:
                ret = self.queue.get(False)
            except Empty:
                break

            if ret == EventsDroppedError:
                raise EventsDroppedError
            elif ret == RootDeletedError:
                raise RootDeletedError
            else:
                full_list.extend(ret)

        return full_list

    def close(self):
        DirectoryWatch.EventThread.unregister(self)


class MetaDirectoryWatch(object):
    DirectoryWatch = DirectoryWatch

    def __init__(self):
        if not DirectoryWatch.EventThread or DirectoryWatch.EventThread.stopped():
            DirectoryWatch.EventThread = db_thread(DBFSEventThread)()
            DirectoryWatch.EventThread.start()

    def configure(self):
        pass

    def wait(self, watches):
        ready = [ w for w in watches if not w.queue.empty() ]
        if ready:
            return ready
        assert DirectoryWatch.EventThread
        DirectoryWatch.EventThread.dataEvent.wait()
        if DirectoryWatch.EventThread.error:
            DirectoryWatch.EventThread.dataEvent.set()
            raise MetaWatchFailure('Daemon Reader Thread Died.')
        return watches

    def set_wakeup_event(self):
        DirectoryWatch.EventThread.dataEvent.set()

    def __del__(self):
        if DirectoryWatch.EventThread:
            DirectoryWatch.EventThread.signal_stop()
