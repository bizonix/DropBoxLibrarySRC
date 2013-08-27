#Embedded file name: dropbox/client/high_trace.py
from __future__ import absolute_import
import base64
import errno
import getpass
import itertools
import os
import re
import sys
import threading
import time
import traceback
import uuid
import zlib
from cStringIO import StringIO
from hashlib import md5
import POW
import build_number
from dropbox.callbacks import Handler
from dropbox.fileutils import safe_remove
from dropbox.keystore import KeyStore
from dropbox.native_queue import Queue, Empty
from dropbox.platform import platform
from dropbox.preferences import OPT_PHOTO
from dropbox.threadutils import StoppableThread
from dropbox.trace_printer import generate_high_trace_printer
from trace_report import make_report, MAX_REPORT_LENGTH
import arch
import dropbox.trace
if platform == 'win':
    from dropbox.dirtraverse_win32 import WIN32_REPARSE_TAGS, win32_reparse_tag_to_human_readable
TRACE = dropbox.trace.TRACE
WARNING = dropbox.trace.WARNING
unhandled_exc_handler = dropbox.trace.unhandled_exc_handler
report_bad_assumption = dropbox.trace.report_bad_assumption
EMPHASIS_PREFIX = u'!!'
SECONDS_PER_DAY = 24 * 60 * 60

class _TraceSegment(object):
    __slots__ = ('emphasis', 'threadname', 'segment', '_preformatted')

    def __init__(self, tn, seg, emphasis = False):
        self.threadname = tn
        self.segment = seg
        self.emphasis = emphasis or seg.startswith(EMPHASIS_PREFIX)

    def __str__(self):
        try:
            return self._preformatted
        except AttributeError:
            self._preformatted = '| %s: %s\n' % (self.threadname, self.segment)
            return self._preformatted


class HighTrace(object):

    def __init__(self):
        self.h = Handler(recursive=False, handle_exc=traceback.print_exc)
        self.add_handler = self.h.add_handler
        self.remove_handler = self.h.remove_handler
        self.l = threading.RLock()

    def __call__(self, x):
        tn = threading.currentThread().getName().ljust(13)
        try:
            if type(x) is str:
                x = x.decode('utf-8')
            elif type(x) is not unicode:
                x = unicode(x)
        except Exception:
            x = u'repred:%s' % repr(x)

        try:
            emphasis = x.startswith(EMPHASIS_PREFIX)
        except Exception:
            emphasis = False

        lines = x.encode('ascii', 'backslashreplace').replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if emphasis:
            with self.l:
                for seg in lines:
                    self.h.run_handlers(_TraceSegment(tn, seg, emphasis))

        else:
            for seg in lines:
                with self.l:
                    self.h.run_handlers(_TraceSegment(tn, seg, emphasis))


generate_local_output_fn = None
if platform == 'win':
    import win32api

    def generate_local_output_fn_win():

        def local_output(ts):
            return win32api.OutputDebugString(str(ts))

        return local_output


    generate_local_output_fn = generate_local_output_fn_win
else:

    def generate_local_output_fn_posix():
        supports_color = sys.stderr.isatty() and os.environ.get('TERM') not in ('dumb', None)
        notyet_local_output = generate_high_trace_printer(print_color=supports_color, print_name=True, print_time=True)

        def local_output(ts):
            return notyet_local_output(ts.threadname, ts.segment)

        return local_output


    generate_local_output_fn = generate_local_output_fn_posix

def do_once(fn):
    lock = threading.Lock()
    have_run = [False]

    def newfn(*n, **kw):
        if have_run[0]:
            return
        with lock:
            if have_run[0]:
                return
            try:
                return fn(*n, **kw)
            finally:
                have_run[0] = True

    return newfn


class LtraceThread(threading.Thread):

    def __init__(self):
        super(LtraceThread, self).__init__()
        self.q = Queue()
        self.setDaemon(True)
        self.local_output = generate_local_output_fn()
        self._start = do_once(self.start)

    def run(self):
        while True:
            self.local_output(self.q.get())

    def trace(self, ts):
        self._start()
        self.q.put(ts)


def is_valid_time_limited_cookie(cookie):
    try:
        try:
            t_when = int(cookie[:8], 16) ^ 1686035233
        except ValueError:
            return False

        if abs(time.time() - t_when) < SECONDS_PER_DAY * 2:
            if md5(cookie[:8] + 'traceme').hexdigest()[:6] == cookie[8:]:
                return True
    except Exception:
        unhandled_exc_handler()

    return False


def limited_support_cookie_is_set():
    dbdev = os.getenv('DBDEV')
    return dbdev and is_valid_time_limited_cookie(dbdev)


def create_trace_to_file(path):
    trace_file = open(path, 'w', 1)
    trace_file_lock = threading.Lock()

    def trace_to_file(x):
        line = str(x)
        try:
            with trace_file_lock:
                trace_file.write(line)
        except Exception:
            traceback.print_exc()

    return trace_to_file


def track_magic():
    if build_number.is_frozen():
        if dropbox.trace.magic_trace_key_is_set():
            report_bad_assumption('User is using DBDEV magic', trace_locals=False)
        elif limited_support_cookie_is_set():
            report_bad_assumption('User is using time-limited cookie', trace_locals=False)


class DropboxLog(object):
    MAX_LOG_SIZE = 900000
    MAX_LOGDIR_SIZE = 10485760
    FLUSH_INTERVAL = 305
    UNSENT_EXCEPTION_FLUSH_INTERVAL = 900
    VERSION = 1
    K = (110093462787613230683718604167952238607764759689169662460905861963450470184595270635535853784586268485739648520915575469728859495177822842042021261706874596521068953372362104883780132437534139972150872401307998419446355601480229878625132515974025662413269540355057640674127294875668480774843418327296008691399L, 5)

    def __init__(self, app, t_start):
        self.app = app
        self.cache_dir = app.appdata_path
        self.log_dir = os.path.join(self.cache_dir, u'l')
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.ts = int(time.time())
        self.buf = StringIO()
        self.buf_lock = threading.Lock()
        self.fn = None
        self.next_unsent_exception_flush = None
        self.t_start = t_start
        self._klock = threading.Lock()
        self.get_random_bytes = KeyStore(appdata_path=u'/tmp').get_random_bytes
        self.generate_session_key()

    def encrypt_blob(self, blob, timestamp):
        with self._klock:
            header = self.header
            log_key = self.log_key
        contents = zlib.compress(blob)
        contents += md5(contents).digest()
        cipher = POW.Symmetric(POW.AES_128_CBC)
        iv = md5('%08x' % timestamp).digest()[:16]
        assert len(iv) == 16, 'IV is not a valid length for AES_128_CBC'
        cipher.encryptInit(log_key, iv)
        return 'Dropboxy%04d%04d%s%s' % (self.VERSION,
         len(header),
         header,
         cipher.update(contents) + cipher.final())

    def sample_process(self):
        ret = arch.util.sample_process(os.path.join(self.cache_dir, 's%08x' % int(time.time())))
        ret = base64.b64encode(zlib.compress(ret))
        for j in range(0, len(ret), 200):
            TRACE('SAMPLE:: %s' % ret[j:j + 200])

    def generate_session_key(self):
        bytes = self.get_random_bytes(32)
        _k = POW.rsaFromBN(self.K[0], self.K[1])
        log_key = md5(bytes).digest()
        header = _k.publicEncrypt(log_key)
        with self._klock:
            self.header = header
            self.log_key = log_key

    def get_active_log_files(self, load_contents = False):
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except Exception:
                unhandled_exc_handler()
                return

        for x in os.listdir(self.log_dir):
            try:
                if len(x) == 8:
                    try:
                        full_path = os.path.join(self.log_dir, x)
                    except UnicodeError:
                        full_path = os.path.join(self.log_dir.encode(sys.getfilesystemencoding()), x)

                    if load_contents:
                        with open(full_path, 'rb') as f:
                            contents = f.read()
                        yield (full_path, contents)
                    else:
                        yield full_path
            except Exception:
                unhandled_exc_handler()

    def get_all_log_files_in_mtime_order(self):
        existing_log_files = []
        for full_path in itertools.chain(self.get_active_log_files(load_contents=False), arch.util.get_shellext_logs(load_contents=False)):
            try:
                existing_log_files.append((full_path, os.stat(full_path)))
            except Exception as e:
                if platform == 'win' and isinstance(e, WindowsError) and e.winerror in (32, 5):
                    TRACE('Not getting logfile %r because %r', full_path, e)
                    continue
                unhandled_exc_handler()
                try:
                    os.remove(full_path)
                except Exception:
                    unhandled_exc_handler()

        existing_log_files.sort(key=lambda x: x[1].st_mtime)
        for log_file in existing_log_files:
            yield log_file

    def rotate(self):
        total_log_size = 0
        for fn, the_stat in self.get_all_log_files_in_mtime_order():
            if total_log_size > self.MAX_LOGDIR_SIZE:
                try:
                    os.remove(fn)
                except Exception:
                    unhandled_exc_handler()

            else:
                total_log_size += the_stat.st_size

    def delete_all_traces(self):
        for fn, the_stat in self.get_all_log_files_in_mtime_order():
            try:
                os.remove(fn)
            except Exception:
                unhandled_exc_handler()

    def delete_all_old_version_traces(self):
        if getattr(self.app, 'config') is None:
            return False
        if self.app.config.get('trace_version', None) == self.VERSION:
            return True
        for fn, the_stat in self.get_all_log_files_in_mtime_order():
            try:
                with open(fn, 'rb') as f:
                    if f.read(8) == 'Dropboxy' and int(f.read(4)) == self.VERSION:
                        continue
            except Exception:
                pass

            safe_remove(fn)

        self.app.config['trace_version'] = self.VERSION
        return True

    def _should_flush(self):
        return self.buf.tell() > 900000

    def flush(self, force = False):
        old_ts = self.ts
        with self.buf_lock:
            if not force and not self._should_flush():
                return
            ciphertext = self.encrypt_blob(self.buf.getvalue(), old_ts)
            self.buf.close()
            self.buf = StringIO()
        self.ts = int(time.time())
        fn = os.path.join(self.log_dir, '%08x' % old_ts)
        try:
            with open(fn, 'wb') as f:
                f.write(ciphertext)
        except Exception as e:
            if not isinstance(e, IOError):
                unhandled_exc_handler()
            try:
                os.remove(fn)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    unhandled_exc_handler()
            except Exception:
                unhandled_exc_handler()

            TRACE('No disk space; sending traces immediately')
            try:
                ret = self.app.conn.send_trace(old_ts, ciphertext, None)
                if ret.get('drop_traces'):
                    self.delete_all_traces()
            except Exception:
                unhandled_exc_handler(False)

    def report_unsent_exceptions(self, force = False):
        if not force and self.next_unsent_exception_flush and self.next_unsent_exception_flush > time.time():
            return
        self.next_unsent_exception_flush = time.time() + self.UNSENT_EXCEPTION_FLUSH_INTERVAL
        if not getattr(self.app, 'conn', None):
            return
        with _unsent_exceptions_lock():
            to_report = [ (report,
             hash,
             exception_count,
             tag) for hash, (exception_count, report, tag) in _unsent_exceptions.iteritems() if exception_count ]
        if to_report:
            TRACE('Trying to send up %d exceptions', len(to_report))
        for report, hash, exception_count, tag in to_report:
            TRACE(u'Reporting unsent exception %r (count %d)', report[:100], exception_count)
            try:
                ret = self.app.conn.report_exception(report, hash, exception_count, tag=tag)
            except Exception:
                unhandled_exc_handler(False)
                break
            else:
                with _unsent_exceptions_lock():
                    if exception_count == _unsent_exceptions[hash][0]:
                        _unsent_exceptions[hash] = (0, '', None)
                if ret.get('drop_traces'):
                    self.delete_all_traces()
                elif isinstance(ret['ret'], list) or isinstance(ret['ret'], tuple) and ret['ret'][0] == 'send_trace':
                    try:
                        send_trace_log(*ret['ret'][1:])
                    except Exception:
                        unhandled_exc_handler()

    def send_ds_store(self):
        if platform == 'mac' and self.app.ui_flags.get('send_DS_Store_on_suspicious_Finder_crash'):
            try:
                last_known = self.app.config.get('most_recent_finder_crash_for_ds_store', 0)
                try:
                    path = self.app.config['dropbox_path']
                except KeyError:
                    return

                from dropbox.sync_engine_arch.mac._fschange import send_us_DS_Store_on_Finder_crash
                most_recent = send_us_DS_Store_on_Finder_crash(self.app.sync_engine.fs, path, last_known)
                if most_recent != last_known:
                    self.app.config['most_recent_finder_crash_for_ds_store'] = most_recent
            except Exception:
                unhandled_exc_handler()

    def send_finder_crashes(self):
        if platform == 'mac':
            try:
                last_timestamp = self.app.config.get('last_finder_crash_log_sent', 0)
                if self.send_apple_crash_log('dbfseventsd', last_timestamp):
                    report_bad_assumption('dbfseventsd crash!')
                if self.send_apple_crash_log('finder', last_timestamp):
                    report_bad_assumption('Finder Crash!')
                self.app.config['last_finder_crash_log_sent'] = int(time.time())
            except Exception:
                unhandled_exc_handler()

    def send_all(self, latest = None, related_exception = None):
        if build_number.BUILD_KEY != 'Dropbox' and re.search('^[^\\.]+\\.dropbox\\.com$', self.app.conn.host) is not None:
            WARNING("Not sending traces because BUILD_KEY is not Dropbox and we're sending to prod: %r, %r", build_number.BUILD_KEY, self.app.conn.host)
            return
        if not self.app.conn:
            return
        self.send_finder_crashes()
        self.flush(force=True)
        total_size = 0
        for rel_exc, fn, contents in itertools.chain(((related_exception, logs[0], logs[1]) for logs in self.get_active_log_files(load_contents=True)), ((logs[2], logs[0], logs[1]) for logs in arch.util.get_shellext_logs(load_contents=True))):
            try:
                ts = int(fn[-8:], 16)
            except ValueError:
                continue

            if latest and latest >= ts:
                continue
            TRACE('Sending trace %d (%r)', ts, fn)
            try:
                ret = self.app.conn.send_trace(ts, contents, rel_exc)
            except Exception:
                unhandled_exc_handler(False)
                break
            else:
                total_size += len(contents)
                if ret.get('drop_traces'):
                    self.delete_all_traces()
                    break
                try:
                    if rel_exc in arch.util.shellext_log_types:
                        arch.util.cleanup_shellext_log(fn)
                    else:
                        os.remove(fn)
                except Exception:
                    unhandled_exc_handler()

        self.rotate()
        TRACE('Done sending traces (%.1f kB sent)', total_size / 1024.0)

    def paths_in_folder(self, folder, process_name, last_timestamp):
        toret = []
        for f in os.listdir(folder):
            if f.lower().startswith(process_name + '_') and f.endswith('.crash'):
                newf = os.path.join(folder, f)
                try:
                    st = os.stat(newf)
                except Exception:
                    unhandled_exc_handler()
                    continue

                try:
                    _t = st.st_birthtime
                except AttributeError:
                    _t = st.st_mtime

                if _t > last_timestamp:
                    toret.append(newf)

        return toret

    def send_apple_crash_log(self, process_name, last_timestamp):
        assert process_name == process_name.lower()
        log_list = []
        for path in (os.path.expanduser('~/Library/Logs/CrashReporter'), '/Library/Logs/CrashReporter'):
            try:
                log_list += self.paths_in_folder(path, process_name, last_timestamp)
            except EnvironmentError as e:
                if e.errno not in (errno.ENOENT, errno.EACCES):
                    unhandled_exc_handler()
            except Exception:
                unhandled_exc_handler()

        if not log_list:
            return
        TRACE('New %s crash logs to send: %r', process_name, log_list)
        for log in log_list:
            try:
                st = os.stat(log)
                try:
                    _t = st.st_birthtime
                except AttributeError:
                    _t = st.st_mtime

                log_time = int(_t)
                with open(log, 'rb') as f:
                    try:
                        ret = self.app.conn.send_trace(log_time, self.encrypt_blob(f.read(), log_time), process_name + '_crash')
                    except Exception:
                        unhandled_exc_handler(False)
                        break

                    if ret.get('drop_traces'):
                        self.delete_all_traces()
            except OSError as e:
                if e.errno != errno.EACCES:
                    unhandled_exc_handler()
            except Exception:
                unhandled_exc_handler()

        return log_list

    def trace(self, ts, x):
        ts = int((ts - self.t_start) * 1000)
        x = '%8s.%03d %s' % (ts / 1000, ts % 1000, x)
        with self.buf_lock:
            try:
                self.buf.write(x)
            except Exception:
                self.buf = StringIO()

            return self._should_flush()


class PerLineWrapper(object):
    VERSION = 1

    def __init__(self, sender):
        self._sender = sender
        self.get_random_bytes = KeyStore(appdata_path='/tmp').get_random_bytes
        self.generate_session_key()
        self._header_sent = False

    def generate_session_key(self):
        bytes = self.get_random_bytes(32)
        _k = POW.rsaFromBN(DropboxLog.K[0], DropboxLog.K[1])
        self.log_key = md5(bytes).digest()
        self.header = _k.publicEncrypt(self.log_key)
        self.iv = md5(self.log_key).digest()[:16]

    def send_header(self):
        self._header_sent = True
        h = base64.b64encode(self.header)
        msg = 'NEWKEY: %04d%04d%s' % (self.VERSION, len(h), h)
        self._sender(msg)

    def send_line(self, line):
        if not self._header_sent:
            self.send_header()
        self._sender(self.encrypt_blob(str(line)))

    def encrypt_blob(self, line):
        line = line + md5(line).digest()
        cipher = POW.Symmetric(POW.AES_128_CBC)
        cipher.encryptInit(self.log_key, self.iv)
        output = base64.b64encode(cipher.update(line) + cipher.final())
        return 'TRACE: %04d%04d%s' % (self.VERSION, len(output), output)


def line_encrypter(sender):
    return PerLineWrapper(sender).send_line


class RtraceThread(StoppableThread):

    def __init__(self, app, t_start):
        super(RtraceThread, self).__init__(name='RTRACE')
        self.rtrace_queue = Queue()
        self.flush_event = threading.Event()
        self.app = app
        self.log = DropboxLog(self.app, t_start)

    def set_wakeup_event(self):
        self.rtrace_queue.put(('nothing',))

    def sample_process(self):
        self.rtrace_queue.put(('sample_process',))

    def send_trace_log(self, latest = None, related_exception = None):
        TRACE('App internal request to send trace logs')
        self.rtrace_queue.put(('send_trace_log', latest, related_exception))
        try:
            self.app.formatted_trace.run()
        except Exception:
            unhandled_exc_handler()

    def send_ds_store(self, latest = None, related_exception = None):
        self.rtrace_queue.put(('send_ds_store',))

    def send_finder_crashes(self, latest = None, related_exception = None):
        self.rtrace_queue.put(('send_finder_crashes',))

    def force_flush(self, wait = 4):
        self.flush_event.clear()
        self.rtrace_queue.put(('flush', True))
        self.flush_event.wait(wait)

    def report_unsent_exceptions(self, in_a_bit = False):
        self.rtrace_queue.put(('report_unsent', in_a_bit))

    def trace(self, ts):
        if self.log.trace(time.time(), str(ts)):
            self.rtrace_queue.put(('flush', False))

    def set_conn(self, conn):
        pass

    def run(self):
        self.watch_queue()
        TRACE('Stopping...')

    def watch_queue(self):
        log = self.log
        delete_old_versions = True
        next_report = None
        while not self.stopped():
            if next_report is not None:
                slp = next_report - time.time()
                x = ('report_unsent', False)
                if slp > 0:
                    try:
                        x = self.rtrace_queue.get(block=True, timeout=slp)
                    except Empty:
                        pass

            else:
                x = self.rtrace_queue.get()
            if delete_old_versions:
                delete_old_versions = not log.delete_all_old_version_traces()
            try:
                cmd, args = x[0], x[1:]
                if cmd == 'trace':
                    if log.trace(args[0], args[1]):
                        log.flush()
                        log.rotate()
                elif cmd == 'flush':
                    try:
                        log.flush(force=args[0])
                        log.rotate()
                        log.report_unsent_exceptions(force=args[0])
                    finally:
                        self.flush_event.set()

                elif cmd == 'send_trace_log':
                    log.send_all(*args)
                elif cmd == 'send_finder_crashes':
                    log.send_finder_crashes(*args)
                elif cmd == 'sample_process':
                    log.sample_process()
                elif cmd == 'send_ds_store':
                    log.send_ds_store()
                elif cmd == 'report_unsent':
                    if args[0] == True:
                        if next_report is None:
                            next_report = time.time() + 180
                        continue
                    try:
                        log.report_unsent_exceptions(force=True)
                    except Exception:
                        unhandled_exc_handler()
                        next_report = time.time() + 180
                    else:
                        next_report = None

                elif cmd == 'nothing':
                    pass
                else:
                    report_bad_assumption('no handler for cmd %s, args %s', cmd, args)
            except Exception:
                unhandled_exc_handler()

        log.flush()


_rtrace_thread = None

def sample_process(*n, **kw):
    global _rtrace_thread
    if _rtrace_thread:
        _rtrace_thread.sample_process(*n, **kw)


def send_trace_log(*n, **kw):
    if _rtrace_thread:
        _rtrace_thread.send_trace_log(*n, **kw)


def send_ds_store(*n, **kw):
    if _rtrace_thread:
        _rtrace_thread.send_ds_store(*n, **kw)


def send_finder_crashes(*n, **kw):
    if _rtrace_thread:
        _rtrace_thread.send_finder_crashes(*n, **kw)


def force_flush(*n, **kw):
    if _rtrace_thread:
        _rtrace_thread.force_flush(*n, **kw)


def report_unsent_exceptions(*n, **kw):
    if _rtrace_thread:
        _rtrace_thread.report_unsent_exceptions(*n, **kw)


_high_tracer = None
_t_start = None

def add_high_trace_handler(handler):
    global _high_tracer
    if _high_tracer is None:
        raise Exception('Tracing system has not yet been started! Call install_global_trace_handlers() first before using this')
    _high_tracer.add_handler(handler)


def remove_high_trace_handler(handler):
    if _high_tracer is None:
        raise Exception('Tracing system has not yet been started! Call install_global_trace_handlers() first before using this')
    _high_tracer.remove_handler(handler)


def install_global_trace_handlers(allow_local_traces = True, flags = None, args = None):
    global _t_start
    global _high_tracer
    if _high_tracer is not None:
        assert _t_start is not None
        TRACE('!! Already enabled tracing system')
        return
    _t_start = time.time()
    _high_tracer = HighTrace()
    dropbox.trace.add_trace_handler(_high_tracer)
    if not build_number.is_frozen() or dropbox.trace.magic_trace_key_is_set() or limited_support_cookie_is_set():
        if allow_local_traces:
            _high_tracer.add_handler(LtraceThread().trace)
        if os.getenv('DBTRACEFILE'):
            try:
                fname = os.getenv('DBTRACEFILE')
                try:
                    if os.getenv('DBTRACE_TO_SEPARATE_FILES'):
                        suffix = ''
                        if flags and flags.get('--client', None):
                            suffix += '-' + flags.get('--client')
                        if args and len(args) > 1 and len(args[1]) > 0:
                            suffix += '-' + args[1].lower()[1:]
                        fname += suffix
                except Exception:
                    traceback.print_exc()

                new_handler = create_trace_to_file(fname)
            except Exception:
                traceback.print_exc()
            else:
                _high_tracer.add_handler(new_handler)


def start_trace_thread(app):
    global _rtrace_thread
    if _t_start is None:
        raise Exception('Tracing system has not been enabled yet. call install_global_trace_handlers() before calling this method.')
    assert _high_tracer is not None, '_t_start and _high_tracer should have been set together: %r:%r' % (_t_start, _high_tracer)
    if _rtrace_thread is not None:
        TRACE('!! Already started trace thread')
        return
    _rtrace_thread = RtraceThread(app, _t_start)
    _rtrace_thread.start()
    _high_tracer.add_handler(_rtrace_thread.trace)
    track_magic()


def set_trace_conn(conn):
    if _rtrace_thread:
        _rtrace_thread.set_conn(conn)


__unsent_exceptions_lock = None

def _unsent_exceptions_lock():
    global __unsent_exceptions_lock
    if __unsent_exceptions_lock is None:
        __unsent_exceptions_lock = threading.RLock()
    return __unsent_exceptions_lock


_unsent_exceptions = {}

def report_exception(*exc_info, **kw):
    report, hash = kw.get('report_and_hash') or make_report(exc_info)
    if len(report) > MAX_REPORT_LENGTH:
        report = report[-MAX_REPORT_LENGTH:]
    tag = kw.get('tag')
    with _unsent_exceptions_lock():
        if hash not in _unsent_exceptions:
            if kw.get('trace_locals', True):
                try:
                    tb = exc_info[2]
                    if tb is not None:
                        while tb.tb_next:
                            tb = tb.tb_next

                        frame = kw.get('frame_for_locals') or tb.tb_frame
                        TRACE('!! locals of %s:' % frame.f_code.co_name)
                        dropbox.trace.trace_locals(frame.f_locals)
                except Exception:
                    TRACE(traceback.format_exception(*exc_info))

            _unsent_exceptions[hash] = (1, report, tag)
            report_unsent_exceptions()
        else:
            exception_count = _unsent_exceptions[hash][0] + 1
            _unsent_exceptions[hash] = (exception_count, report, tag)
            TRACE('Queuing exc %s for later delivery (count %d)', hash, exception_count)
            report_unsent_exceptions(in_a_bit=True)


dropbox.trace.add_exception_handler(report_exception)

def get_free_space_formatted(folder):
    try:
        bytes = arch.util.get_free_space(folder)
    except OSError as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
        return 'Unknown (%s)' % e.strerror
    except Exception as e:
        return 'Unknown (%r)' % e

    kb = bytes / 1024
    mb = kb / 1024
    gb = mb / 1024.0
    if gb > 1:
        return '%.1f G' % gb
    if mb > 1:
        return '%s M' % mb
    if kb > 1:
        return '%s K' % kb
    return '%s b' % bytes


def get_drive_info():
    drive_info = []
    for d, i, a, m in arch.util.get_drives():
        row = []
        row.append(d)
        if getattr(a, '__iter__', False):
            row.append(' OR '.join(a))
        else:
            row.append(a)
        if i:
            row.append(i[-1])
        else:
            row.append(None)
        if platform == 'win':
            drive_dir = row[1]
        else:
            drive_dir = row[0]
        row.append(get_free_space_formatted(drive_dir))
        drive_info.append(row)

    return drive_info


class FormattedTraceReporter(object):

    def __init__(self, buildno, conn, config, pref_controller):
        self.buildno = buildno
        self.conn = conn
        self.sync_engine = None
        self.config = config
        self.pref_controller = pref_controller
        self.drive_info = None
        self.symlink_tracker = None

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine

    def set_symlink_tracker(self, symlink_tracker):
        self.symlink_tracker = symlink_tracker

    def run(self):
        if not self.sync_engine:
            TRACE('no sync engine WTF?')
            return
        self.info = []
        try:
            self.info.append(([u'version: %s' % self.buildno], []))
            try:
                user = getpass.getuser().decode(sys.getfilesystemencoding())
            except Exception:
                user = repr(getpass.getuser())

            if platform == 'win':
                user += u' is %san admin' % (u'' if arch.util.is_admin() else u'not ')
            self.info.append(([u'User: ' + user], []))
            if platform == 'mac':
                try:
                    from pymac.helpers.process import get_model_identifier
                    self.info.append(([u'Macbook Model: ' + get_model_identifier()], []))
                except Exception:
                    unhandled_exc_handler()

            if uuid.getnode() == uuid.getnode():
                _uuid = ('%012x' % uuid.getnode()).upper()
                formatted = []
                for i in range(len(_uuid) / 2):
                    formatted.append(_uuid[2 * i:2 * (i + 1)] + ':')

                uuidnode = u''.join(formatted)[:-1]
            else:
                uuidnode = u'unknown'
            self.info.append(([u'uuid: ' + uuidnode], []))
            self.info.append(([u'Dropbox Folder', u'Case Sensitive'], [(unicode(self.sync_engine.dropbox_folder), unicode(getattr(self.sync_engine, 'case_sensitive', 'Unknown')))]))
            up_style = self.pref_controller['throttle_upload_style']
            if up_style == 0:
                up_style_str = 'unlimited'
            elif up_style == 1:
                up_style_str = 'automatic limit'
            elif up_style == 2:
                up_style_str = str(self.pref_controller['throttle_upload_speed']) + ' kB/s'
            else:
                up_style_str = 'Some messed-up invalid value.'
            down_style = self.pref_controller['throttle_download_style']
            if down_style == 0:
                down_style_str = 'unlimited'
            elif down_style == 1:
                down_style_str = 'automatic limit'
            elif down_style == 2:
                down_style_str = str(self.pref_controller['throttle_download_speed']) + ' kB/s'
            else:
                down_style_str = 'Some messed-up invalid value.'
            try:
                arch.util.formatted_trace(self.info)
            except Exception:
                unhandled_exc_handler()

            self.info.append(([u'Network Preferences', None], [('Upload:', up_style_str), ('Download:', down_style_str)]))
            self.info.append(([u'Mount Points', u'Namespace'], [ (unicode(p), ns) for p, ns in self.sync_engine.get_mount_points() ]))
            self.info.append(([u'Selective Sync Ignore List'], [ [unicode(path)] for path in self.sync_engine.get_directory_ignore_set() ]))
            if self.drive_info is None:
                self.drive_info = get_drive_info()
            self.info.append(([u'Drives',
              u'Location',
              u'File System',
              u'Free Space'], self.drive_info))
            camera_uploads_enabled = False
            if platform == 'win':
                camera_uploads_enabled = arch.photouploader.is_photouploader_installed()
            elif platform == 'mac':
                camera_uploads_enabled = self.pref_controller[OPT_PHOTO]
            self.info.append(([u'Camera uploads: %s' % ('enabled' if camera_uploads_enabled else 'not enabled')], []))
            try:
                if self.symlink_tracker is not None:
                    symlink_data = self.symlink_tracker.get_symlink_data(cached=True)
                    if self.symlink_tracker.is_unix:
                        symlink_header = ['Symlink Info', None]
                        invalid_inside = symlink_data['invalid-absolute-inside'] + symlink_data['invalid-relative-inside']
                        invalid_outside = symlink_data['invalid-absolute-outside'] + symlink_data['invalid-relative-outside']
                        symlink_content = [('Total count:', symlink_data['total']),
                         ('Invalid count:', invalid_inside + invalid_outside),
                         ('Number invalid to outside Dropbox folder:', invalid_outside),
                         ('Number invalid within Dropbox folder:', invalid_inside)]
                        self.info.append((symlink_header, symlink_content))
                        self.info.append((['Sample symlink', 'Target'], symlink_data['sample-paths']))
                    else:
                        symlink_header = ['Reparse Point Info', None]
                        symlink_content = [('Total reparse points:', sum((symlink_data[tag] for tag in WIN32_REPARSE_TAGS)))]
                        for tag in WIN32_REPARSE_TAGS:
                            if symlink_data[tag]:
                                human_string = win32_reparse_tag_to_human_readable(tag)
                                symlink_content.append(('Number of %s:' % human_string, symlink_data[tag]))

                        self.info.append((symlink_header, symlink_content))
                        self.info.append((['Sample reparse points', 'Reparse type'], symlink_data['sample-paths']))
            except Exception:
                unhandled_exc_handler()

            self.conn.report_formatted_trace(self.info)
        except Exception:
            unhandled_exc_handler()
