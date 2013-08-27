#Embedded file name: dropbox/trace.py
from __future__ import absolute_import
import contextlib
import functools
import hashlib
import os
import sys
import tempfile
import threading
import traceback
from pprint import pformat
import build_number
from trace_report import make_report
from dropbox.callbacks import Handler
_magic_trace_key_is_set = None

def magic_trace_key_is_set():
    global _magic_trace_key_is_set
    if _magic_trace_key_is_set is None:
        dbdev = os.getenv('DBDEV') or ''
        dbdev_hash = hashlib.sha256(dbdev).hexdigest()
        _magic_trace_key_is_set = dbdev_hash == 'e27eae61e774b19f4053361e523c771a92e838026da42c60e6b097d9cb2bc825'
    return _magic_trace_key_is_set


_debugging_features_enabled = None

def debugging_features_are_enabled():
    return not build_number.is_frozen() or magic_trace_key_is_set()


_trace_handler = Handler(recursive=False, handle_exc=traceback.print_exc)
run_trace_handlers = _trace_handler.run_handlers
add_trace_handler = _trace_handler.add_handler
remove_trace_handler = _trace_handler.remove_handler
_exception_handler = Handler(recursive=True, handle_exc=traceback.print_exc)
run_exception_handlers = _exception_handler.run_handlers
add_exception_handler = _exception_handler.add_handler
remove_exception_handler = _exception_handler.remove_handler
_event_handler = Handler(recursive=True, handle_exc=traceback.print_exc)
run_event_handlers = _event_handler.run_handlers
add_event_handler = _event_handler.add_handler
remove_event_handler = _event_handler.remove_handler
EVENT = run_event_handlers

def TRACE(string, *n):
    if n:
        try:
            string %= n
        except Exception:
            trace_stack()

    return run_trace_handlers(string)


_three_nuns = (None, None, None)

def unhandled_exc_handler(run_handlers = True, exc_info = None, **kw):
    if exc_info is None:
        exc_info = sys.exc_info()
        if exc_info == _three_nuns:
            try:
                assert False, 'Called unhandled_exc_handler not in a exception: \n%s' % (''.join(traceback.format_stack()[:-1]),)
            except Exception:
                exc_info = sys.exc_info()
                run_handlers = True

    report, hash = kw.get('report_and_hash') or make_report(exc_info)
    TRACE('\n'.join(('!! %s' % x for x in ['Exception (hash=%s):' % hash] + report.split('\n'))))
    if run_handlers:
        run_exception_handlers(*exc_info, **kw)


def watched(eff):

    def intwatched(*n, **kw):
        try:
            return eff(*n, **kw)
        except Exception:
            TRACE('A THREAD DIED***********************************: ')
            unhandled_exc_handler()

    return intwatched


def trace_stack():
    TRACE('\n'.join(('!! %s' % x for x in ''.join(traceback.format_stack()).split('\n'))))


def trace_locals(_locals):
    try:
        for k, v in _locals.iteritems():
            try:
                TRACE('!! %s : %s,' % (k, pformat(v)[:1000]))
            except Exception:
                TRACE('!! %s : <bad repr>,' % k)

    except Exception:
        try:
            TRACE('!! trace_locals: error iterating on %r', _locals)
        except Exception:
            TRACE('!! trace_locals: <bad repr>')


class BadAssumptionError(Exception):
    pass


def report_bad_assumption(the_str, *n, **kw):
    full_stack = kw.get('full_stack')
    try:
        if n:
            the_str %= n
    except Exception:
        unhandled_exc_handler(trace_locals=kw.get('trace_locals', True))

    try:
        raise BadAssumptionError(the_str)
    except Exception:
        _list = ['Traceback (most recent call last):\n']
        if full_stack:
            stack = traceback.format_stack()[:-2]
        else:
            stack = [traceback.format_stack()[-2]]
        _list.extend(stack)
        _list.append('BadAssumptionError(%r)' % (the_str,))
        report = ''.join(_list)
        tohash = ''.join(stack).replace('\\', '/')
        _hash = hashlib.md5(tohash.replace('.py"', '.pyc"') if sys.platform.startswith('linux') else tohash).hexdigest()
        unhandled_exc_handler(frame_for_locals=sys.exc_info()[2].tb_frame.f_back, report_and_hash=(report, _hash), trace_locals=kw.get('trace_locals', True))


def print_path_perms(path):
    ret = repr(path) + '\n'
    try:
        ret += 'real_path=%r\n' % (os.path.realpath(path),)
    except Exception:
        pass

    try:
        st = os.stat(path)
        ret += '\tmode=%s\tuid=%d\tgid=%d\n' % (oct(st.st_mode), st.st_uid, st.st_gid)
    except Exception:
        ret += '\tnot found\n'

    try:
        st = os.stat(os.path.dirname(path))
        ret += 'parent\tmode=%s\tuid=%d\tgid=%d' % (oct(st.st_mode), st.st_uid, st.st_gid)
    except Exception:
        ret += 'parent\tnot found'

    return ret


def get_extra_trace_info(appdata_path, dropbox_path):
    unix = sys.platform.startswith('linux') or sys.platform.startswith('darwin')

    def get_user_name(effective_user = False):
        import pwd
        return repr(pwd.getpwuid(os.geteuid() if effective_user else os.getuid()))

    def get_grp_name(effective_group = False):
        import grp
        return repr(grp.getgrgid(os.getegid() if effective_group else os.getgid()))

    d = [('pid', os.getpid)]
    if unix:
        d.extend([('ppid', os.getppid),
         ('uid', os.getuid),
         ('user_info', get_user_name),
         ('effective_user_info', functools.partial(get_user_name, effective_user=True)),
         ('euid', os.geteuid),
         ('gid', os.getgid),
         ('egid', os.getegid),
         ('group_info', get_grp_name),
         ('effective_group_info', functools.partial(get_grp_name, effective_group=True))])
    d.extend([('appdata', functools.partial(print_path_perms, appdata_path)), ('dropbox_path', functools.partial(print_path_perms, dropbox_path)), ('HOME', functools.partial(os.environ.get, 'HOME'))])
    if not unix:
        d.extend([('TMP', functools.partial(os.environ.get, 'TMP')), ('TEMP', functools.partial(os.environ.get, 'TEMP'))])
    d.append(('tempdir', functools.partial(print_path_perms, tempfile.gettempdir())))
    ret = []
    for name, f in d:
        try:
            val = unicode(f()).encode('utf-8')
        except Exception:
            val = 'failed'

        ret.append('%s:\t%s' % (name, val))

    return '\n'.join(ret)


def reraise_exc_handler():
    exc = sys.exc_info()
    raise exc[0], exc[1], exc[2]


_is_debugging = True

def set_debugging(bool_):
    global _is_debugging
    _is_debugging = bool_


def is_debugging():
    return _is_debugging


def assert_(predicate, *n):
    try:
        str_ = n[0]
    except IndexError:
        str_ = ''

    if _is_debugging:
        assert predicate(), str_ % n[1:]
    else:
        try:
            if not predicate():
                report_bad_assumption(str_ % n[1:])
        except Exception:
            unhandled_exc_handler()


def DEVELOPER_WARNING(str_, *n):
    if not build_number.is_frozen():
        TRACE(('!! %s (use trace_stack() to figure out where this is happening)' % str_), *n)


def WARNING(str_, *n):
    TRACE(('!! ' + str_), *n)


def trace_threads():
    for frame in sys._current_frames().values():
        TRACE('!! **** %r ********', frame)
        TRACE('\n'.join(('!! %s' % x for x in ''.join(traceback.format_stack(frame)).split('\n'))))


def thread_tracebacks():
    ti = {thread.ident:thread for thread in threading.enumerate()}
    for tid, frame in sys._current_frames().iteritems():
        print ''
        print '#### %s ####' % ti[tid].name
        traceback.print_stack(frame)
        print ''


@contextlib.contextmanager
def trace_before_after(message):
    TRACE(message + ' (before)')
    yield
    TRACE(message + ' (after)')
