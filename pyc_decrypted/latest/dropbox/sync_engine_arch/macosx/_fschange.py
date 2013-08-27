#Embedded file name: dropbox/sync_engine_arch/macosx/_fschange.py
from __future__ import absolute_import
import base64
import datetime
import errno
import re
import subprocess32 as subprocess
import threading
import time
import zlib
from hashlib import md5
from Foundation import NSAutoreleasePool
from dropbox import fsutil
from dropbox.fastwalk import fastwalk
from dropbox.features import feature_enabled
from dropbox.mac.finder import FinderController, FinderRestartError, INJECTED_CURRENT_VERSION, INJECTED_OTHER_VERSION, cleanup_old_plugins, paths_open_in_finder, restart
from dropbox.mac.helper_installer import HELPERS_DIR, install_dropbox_helpers_with_fallback
from dropbox.mac.version import LEOPARD, MAC_VERSION, MAVERICKS, MOUNTAIN_LION, SNOW_LEOPARD, TIGER
from dropbox.mac.internal import binaries_ready, BINARIES_READY_TIMEOUT, find_finder_pid
from dropbox.native_threading import NativeCondition
from dropbox.threadutils import StoppableThread
from dropbox.trace import report_bad_assumption, unhandled_exc_handler, TRACE
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_POSIX_SYMLINK
from pymac.helpers.process import get_process_arch
MAX_BATCHED_EVENTS = 250
SLOW_BATCH_SLEEP = 0
TIME_BETWEEN_FINDER_POLL = 4
POTENTIAL_FINDER_RESTART_TIMEOUT = 1

def fill_pending(touchset, pending):
    while touchset and len(pending) < MAX_BATCHED_EVENTS:
        pending.add(touchset.pop())


def _datetime_from_crash_log_filename(filename):
    ts = filename.split('_')[1].split('-')
    return datetime.datetime(int(ts[0]), int(ts[1]), int(ts[2]), int(ts[3][:2]), int(ts[3][2:4]), int(ts[3][4:6]))


if MAC_VERSION >= SNOW_LEOPARD:
    BUNDLE_NAME = 'DropboxBundle.bundle'
else:
    BUNDLE_NAME = 'DropboxPlugin.plugin'

def finder_crashes(fs, folders_to_check = None):
    if MAC_VERSION < LEOPARD:
        return
    if folders_to_check is None:
        folders_to_check = [fsutil.expanduser(fs, u'~/Library/Logs/CrashReporter'), fs.make_path(u'/Library/Logs/CrashReporter')]
    for container in folders_to_check:
        try:
            try:
                filenames = fsutil.listdir(fs, container)
            except EnvironmentError as e:
                if e.errno == errno.ENOENT:
                    continue
                raise

            for fn in filenames:
                if fn.startswith(u'Finder') and fn.endswith(u'.crash'):
                    yield (container, fn)

        except Exception:
            unhandled_exc_handler()


def most_recent_known_finder_crash(fs, folders_to_check = None):
    most_recent = None
    for container, fn in finder_crashes(fs, folders_to_check):
        most_recent = max(fn, most_recent)

    if most_recent:
        return _datetime_from_crash_log_filename(most_recent)


class AlreadyInjectedError(Exception):
    pass


def restart_finder_and_log(app):
    try:
        restart()
    except FinderRestartError as e:
        unhandled_exc_handler()
        app.event.report('finder_restart', step='failed', error=e.__class__.__name__)
        return False
    except Exception as e:
        TRACE('Problem restarting Finder %r', e)
        app.event.report('finder_restart', step='failed', error=e.__class__.__name__)
        return False

    app.event.report('finder_restart', step='done')
    return True


def integrate_with_finder(fs, app, finder_controller, last_injected_pids = None):
    trust_binaries = binaries_ready.wait(timeout=BINARIES_READY_TIMEOUT)
    if not trust_binaries:
        TRACE('Not trusting Finder Integration')
        return
    finder_pid = find_finder_pid()
    if finder_pid is None:
        TRACE("Finder isn't running....")
        return
    injection_state = finder_controller.get_injection_state()
    if injection_state == INJECTED_CURRENT_VERSION:
        TRACE('Already injected with correct version.')
        if last_injected_pids is not None:
            last_injected_pids.append((finder_pid, datetime.datetime.now()))
        return
    if injection_state == INJECTED_OTHER_VERSION:
        if not restart_finder_and_log(app):
            return
    info = {'FinderLoadBundle': {'user': 'root',
                          'mode': 2377},
     BUNDLE_NAME: {}}
    if not install_dropbox_helpers_with_fallback(info):
        TRACE("Couldn't install %r", info.keys())
        return
    try:
        cleanup_old_plugins(HELPERS_DIR)
    except Exception:
        unhandled_exc_handler()

    try:
        inject_finder_bundle(fs, last_injected_pids)
    except AlreadyInjectedError:
        if True:
            if last_injected_pids is not None:
                last_injected_pids.append((finder_pid, datetime.datetime.now()))
            return
        if MAC_VERSION >= SNOW_LEOPARD:
            if not restart_finder_and_log(app):
                return
            inject_finder_bundle(fs, last_injected_pids)


def inject_finder_bundle(fs, last_injected_pids):
    finder_pid = find_finder_pid()
    if finder_pid is None:
        TRACE("Finder isn't running....")
        return False
    arch_for_finderloadbundle = get_process_arch(finder_pid)
    TRACE('Finder (pid %d) running in %s mode' % (finder_pid, 'unknown' if not arch_for_finderloadbundle else arch_for_finderloadbundle))
    injector = u'FinderLoadBundle'
    injectee = '%s/%s' % (HELPERS_DIR.encode('utf8'), BUNDLE_NAME)
    args = [injectee, str(finder_pid)]
    try:
        cmd = []
        if arch_for_finderloadbundle and MAC_VERSION >= LEOPARD:
            cmd.extend(('/usr/bin/arch', '-%s' % arch_for_finderloadbundle))
        cmd.append(fsutil.join_path_string(fs, unicode(HELPERS_DIR), injector))
        cmd.extend(args)
        TRACE("about to call: '%s'" % ' '.join(cmd))
        if last_injected_pids is not None:
            last_injected_pids.append((finder_pid, datetime.datetime.now()))
        inj = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = inj.communicate()
        returncode = inj.returncode
        if returncode == errno.EEXIST:
            TRACE("We're already injected.")
            raise AlreadyInjectedError()
        if stdout:
            TRACE('%s stdout: %s' % (injector, stdout))
        if stderr:
            TRACE('%s stderr: %s' % (injector, stderr))
        inj.stdout.close()
        inj.stderr.close()
        if returncode:
            raise subprocess.CalledProcessError(returncode, cmd)
    except AlreadyInjectedError:
        raise
    except Exception:
        unhandled_exc_handler()
        try:
            injector_path = fsutil.join_path_string(fs, unicode(HELPERS_DIR), injector).encode('utf-8')
            TRACE('Hmm, failed injection? Here\'s the output of \'file "%s"\'', injector_path)
            inj = subprocess.Popen(['/usr/bin/file', injector_path], stdout=subprocess.PIPE)
            if not inj.wait():
                TRACE('%s', inj.stdout.read())
            inj.stdout.close()
        except Exception:
            unhandled_exc_handler()

    else:
        TRACE('inject returned 0!')


class FsChangeThread(StoppableThread):

    def __init__(self, dropbox_app, file_system):
        super(FsChangeThread, self).__init__(name='FSCHANGE')
        self.dropbox_app = dropbox_app
        self.fs = file_system
        self.fast_touch = set()
        self.slow_touch = set()
        self.touching = NativeCondition()
        self.paths_open_in_finder = set()
        self.last_check_on_paths_open = None
        self.should_shell_touch_tree = False
        self.should_wakeup = False
        self.should_request_finder_bundle_version = False
        self.touch_tree_event = threading.Event()
        self.last_injected_pids = []
        self.should_integrate_with_finder = False
        if feature_enabled('mavericks-finder-integration'):
            self.never_inject_again = not TIGER <= MAC_VERSION <= MAVERICKS
        else:
            self.never_inject_again = not TIGER <= MAC_VERSION <= MOUNTAIN_LION
        self.potential_finder_restart()

    def shell_touch(self, full_path):
        with self.touching:
            if full_path.dirname in self.paths_open_in_finder:
                self.fast_touch.add(full_path)
            else:
                self.slow_touch.add(full_path)
            self.touching.notify()

    def potential_finder_restart(self):
        with self.touching:
            should_inject = False
            if self.never_inject_again:
                pass
            elif self.dropbox_app.config.get('disable_finder_integration', False):
                pass
            elif self.dropbox_app.mbox.is_secondary:
                pass
            elif not self.last_injected_pids:
                should_inject = True
            else:
                finder_pid = find_finder_pid()
                if finder_pid is None:
                    TRACE("Finder isn't running....")
                elif len(self.last_injected_pids) < 5 and finder_pid != self.last_injected_pids[-1][0]:
                    new_most_recent_known = most_recent_known_finder_crash(self.fs)
                    if new_most_recent_known and new_most_recent_known > self.last_injected_pids[-1][1] and new_most_recent_known - self.last_injected_pids[-1][1] < datetime.timedelta(0, 20, 0):
                        TRACE('Crash, time started delta of %r, not reinjecting!', new_most_recent_known - self.last_injected_pids[-1][1])
                        self.never_inject_again = True
                    else:
                        should_inject = True
            if should_inject:
                self.should_integrate_with_finder = time.time()
                self.touching.notify()
            return should_inject

    def clear_shell_state(self, dropbox_path, timeout = 2):
        with self.touching:
            self.touch_tree_event.clear()
            self.should_shell_touch_tree = dropbox_path
            self.touching.notify()
        self.touch_tree_event.wait(timeout)

    def set_wakeup_event(self):
        with self.touching:
            self.should_wakeup = True
            self.touching.notify()

    def request_finder_bundle_version(self):
        with self.touching:
            self.should_request_finder_bundle_version = True
        self.set_wakeup_event()

    def run(self):
        last_send = time.time()
        last_finder_poll = 0
        finder_controller = None
        pending = set()
        while not self.stopped():
            pool = NSAutoreleasePool.alloc().init()
            if not finder_controller:
                finder_controller = FinderController()
                self.dropbox_app.add_quit_handler(finder_controller.clear_all)
            try:
                with self.touching:
                    while self.slow_touch and time.time() - last_send < SLOW_BATCH_SLEEP and not (self.should_wakeup or self.fast_touch or self.should_shell_touch_tree or self.should_integrate_with_finder or self.should_request_finder_bundle_version):
                        self.touching.wait(timeout=SLOW_BATCH_SLEEP - time.time() + last_send)

                    while not (self.should_wakeup or self.fast_touch or self.slow_touch or self.should_shell_touch_tree or self.should_integrate_with_finder or self.should_request_finder_bundle_version):
                        self.touching.wait()

                self.should_wakeup = False
                if self.stopped():
                    break
                fs = self.dropbox_app.sync_engine.fs
                if self.should_integrate_with_finder:
                    now = time.time()
                    while self.should_integrate_with_finder > now:
                        with self.touching:
                            self.touching.wait(self.should_integrate_with_finder - now)
                        now = time.time()

                    try:
                        integrate_with_finder(fs, self.dropbox_app, finder_controller, self.last_injected_pids)
                    except Exception:
                        unhandled_exc_handler()

                    self.should_integrate_with_finder = False
                    self.should_request_finder_bundle_version = True
                    self.should_shell_touch_tree = self.dropbox_app.sync_engine.dropbox_folder
                if self.should_request_finder_bundle_version:
                    self.should_request_finder_bundle_version = False
                    finder_controller.request_finder_bundle_version()
                    finder_controller.request_finder_bundle_version()
                if (self.should_shell_touch_tree and MAC_VERSION <= LEOPARD or self.fast_touch or self.slow_touch) and time.time() - last_finder_poll > TIME_BETWEEN_FINDER_POLL:
                    reported_paths_open_in_finder = set((fsutil.make_normalized_path(fs, path) for path in paths_open_in_finder()))
                    self.paths_open_in_finder = set()
                    for path in reported_paths_open_in_finder:
                        self.paths_open_in_finder.add(path)
                        if MAC_VERSION < SNOW_LEOPARD:
                            while not path.is_root:
                                path = path.dirname
                                self.paths_open_in_finder.add(path)

                    last_finder_poll = time.time()
                    TRACE('open paths: %r' % self.paths_open_in_finder)
                    with self.touching:
                        promoted = set([ to_touch for to_touch in self.slow_touch if to_touch.dirname in self.paths_open_in_finder ])
                        demoted = set([ to_touch for to_touch in self.fast_touch if to_touch.dirname not in self.paths_open_in_finder ])
                        self.slow_touch.difference_update(promoted)
                        self.fast_touch.update(promoted)
                        self.fast_touch.difference_update(demoted)
                        self.slow_touch.update(demoted)
                if self.should_shell_touch_tree:
                    if not finder_controller.touch_all():
                        dropbox_path = self.should_shell_touch_tree
                        TRACE('!! Failed to touch all paths, touching each path individually.')
                        if MAC_VERSION <= LEOPARD:
                            for dirpath, ents in fastwalk(fs, dropbox_path, follow_symlinks=False):
                                for dirent in ents:
                                    try:
                                        if dirent.type == FILE_TYPE_POSIX_SYMLINK:
                                            full_path = dirpath.join(dirent.name)
                                            st = fs.indexing_attributes(full_path)
                                            if st.type == FILE_TYPE_DIRECTORY:
                                                self.shell_touch(full_path)
                                        elif dirent.type == FILE_TYPE_DIRECTORY:
                                            self.shell_touch(dirpath.join(dirent.name))
                                    except Exception:
                                        unhandled_exc_handler()

                        else:
                            try:
                                with self.touching:
                                    for open_path in self.paths_open_in_finder:
                                        if dropbox_path.is_parent_of(open_path):
                                            self.fast_touch.add(open_path)

                                    self.touching.notify()
                            except Exception:
                                unhandled_exc_handler()

                    self.should_shell_touch_tree = False
                    self.touch_tree_event.set()
                    continue
                with self.touching:
                    if self.fast_touch:
                        fill_pending(self.fast_touch, pending)
                    if len(pending) < MAX_BATCHED_EVENTS:
                        fill_pending(self.slow_touch, pending)
                if not pending:
                    continue
                to_update = [ unicode(x) for x in pending if fsutil.is_exists(fs, x) ]
                t_start = time.time()
                finder_controller.touch(to_update)
                pending.clear()
                last_send = time.time()
                TRACE('Sent %s notifications in %s sec', len(to_update), last_send - t_start)
            except Exception:
                unhandled_exc_handler()
                time.sleep(1)
            finally:
                del pool


_REMOVE_CRASH_RE = re.compile('BTreeIterator::Next.*THFSPlusPropertyStore', re.DOTALL)
_CRASH_RE = re.compile('^Thread \\d+ Crashed:\n0 +com\\.apple\\.DesktopServices', re.MULTILINE)
_SUDSOFC_FINDER_PID = None

def send_us_DS_Store_on_Finder_crash(fs, dropbox_dir, last_known = 0, folders_to_check = None):
    global _SUDSOFC_FINDER_PID
    pid = find_finder_pid()
    if pid == _SUDSOFC_FINDER_PID:
        return last_known
    _SUDSOFC_FINDER_PID = pid
    crashes = []
    most_recent = None
    for container, fn in finder_crashes(fs, folders_to_check):
        most_recent = max(fn, most_recent)
        if not last_known or time.mktime(_datetime_from_crash_log_filename(fn).timetuple()) > last_known:
            crashes.append((container, fn))

    if not most_recent:
        return last_known
    most_recent = _datetime_from_crash_log_filename(most_recent)
    most_recent_secs = time.mktime(most_recent.timetuple())
    if last_known and last_known >= most_recent_secs:
        return last_known
    if not crashes:
        return most_recent_secs
    matched = 0
    to_remove = False
    ds_store_path = dropbox_dir.join('.DS_Store')
    try:
        for container, fn in crashes:
            try:
                full_path = container.join(fn)
                data = fs.open(full_path).read()
                if _CRASH_RE.search(data):
                    matched += 1
                if _REMOVE_CRASH_RE.search(data):
                    to_remove = True
            except Exception:
                unhandled_exc_handler()

    except Exception:
        unhandled_exc_handler()

    TRACE('found %s crashes from %r to %r; %s matched', len(crashes), time.ctime(last_known), time.ctime(most_recent_secs), matched)
    ds_store_data = ''
    if matched:
        try:
            with fs.open(ds_store_path) as f:
                ds_store_data = f.read()
        except Exception:
            unhandled_exc_handler(trace_locals=False)
            to_remove = True
            TRACE("couldn't read from %s", ds_store_path)

    removed = False
    try:
        if to_remove:
            fs.remove(ds_store_path)
            removed = True
    except Exception:
        unhandled_exc_handler(trace_locals=False)

    if ds_store_data:
        trace_ds_store_file(ds_store_data)
        report_bad_assumption('possible bad DS Store file%s; was output to traces' % (' (removed)' if removed else ''), trace_locals=False)
    return most_recent_secs


def trace_ds_store_file(data = None, path = None):
    try:
        if data is None and path is None:
            return
        if data and path:
            TRACE('trace_ds_store_file: both a path and data provided')
            return
        if path:
            with open(path, 'rb') as f:
                data = f.read()
        checksum = md5(data).hexdigest()
        output = base64.b64encode(zlib.compress(data, 9))
        TRACE('DS_Store data has length %s, md5 checksum %s; compressed, base64d to %s chars', len(data), checksum, len(output))
        for j in range(0, len(output), 200):
            TRACE('DS_STORE:: %s' % output[j:j + 200])

    except Exception:
        data_desc = repr(data)
        try:
            if data:
                data_desc = '%s bytes' % (len(data),)
        except Exception:
            pass

        TRACE('trace_ds_store_file failed: path=%r data=%s', path, data_desc)
        unhandled_exc_handler(trace_locals=False)
        return
