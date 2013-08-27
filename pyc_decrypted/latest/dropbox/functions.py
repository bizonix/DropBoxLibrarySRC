#Embedded file name: dropbox/functions.py
from __future__ import absolute_import
import base64
import time
import re
import functools
import fnmatch
import sys
import os
import socket
import errno
import threading
import heapq
import stat
import itertools
import contextlib
import gzip
import struct
import cPickle as pickle
import ctypes
from UserDict import DictMixin
from Crypto.Random import random
from dropbox.dbexceptions import TimeoutError, EOFError
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.dirtraverse import DirectoryModifiedError
from dropbox.read_write_lock import RWLock
_UCS4_PYTHON = len(u'\U00010800') == 1
_SURROGATE_PAIR_EXPR = re.compile(u'[\ud800-\udfff]')
_SURROGATE_PAIR_EXPR_WIDE = re.compile(u'[\U00010000-\U0010ffff]') if _UCS4_PYTHON else _SURROGATE_PAIR_EXPR
_IS_WIN = sys.platform.startswith('win')

def is_four_byte_unicode(t):
    return _SURROGATE_PAIR_EXPR.search(t) or _SURROGATE_PAIR_EXPR_WIDE.search(t)


def lenient_decode(s):
    if isinstance(s, str):
        return s.decode('mbcs' if _IS_WIN else 'utf8', 'replace')
    else:
        return s


def run_iterable_in_c(iterable):
    any(itertools.ifilterfalse(None, iterable))


def loop_delete(directory, remove, dirmodifiederror = DirectoryModifiedError):
    while True:
        traverse_again = False
        try:
            for dirent in directory:
                try:
                    traverse_again = remove(dirent) or traverse_again
                except Exception:
                    unhandled_exc_handler()

        except dirmodifiederror:
            traverse_again = True
        except Exception:
            unhandled_exc_handler()

        if traverse_again:
            directory.reset()
        else:
            break


def locked(lock):

    def cons(fn):

        def new_fn(*n, **kw):
            with lock:
                fn(*n, **kw)

        return new_fn

    return cons


def natural_sort_key(filename):

    def try_int(s):
        try:
            return int(s)
        except Exception:
            return s.lower()

    return [ try_int(group) for group in re.findall('(\\d+|\\D+)', filename) ]


def natural_sort_cmp(a, b):
    return cmp(natural_sort_key(a), natural_sort_key(b))


def path_eq(p1, p2):
    p1 = os.path.normpath(unicode(p1))
    p2 = os.path.normpath(unicode(p2))
    if not sys.platform.startswith('linux'):
        p1 = p1.lower()
        p2 = p2.lower()
    return p1 == p2


def path_is_parent(parent, path):
    parent = os.path.normpath(unicode(parent))
    path = os.path.normpath(unicode(path))
    if not sys.platform.startswith('linux'):
        parent = parent.lower()
        path = path.lower()
    return os.path.join(path, '').startswith(os.path.join(parent, ''))


_charclass = u'[^<>:"/\\\\|?* ]'
_shortpath_re = re.compile(u'(\\\\|^)%s{3,6}~[0-9](\\.%s{1,3})?(\\\\|$)' % (_charclass, _charclass))

def is_short_path(local_path):
    assert type(local_path) is unicode
    return _shortpath_re.search(local_path) is not None


RECONSTRUCT_TEMP_FILE_PREFIX = '.dbtmp-'
IGNORED_FILES = set(('desktop.ini', 'thumbs.db', '.ds_store', 'icon\r', '.dropbox', '.dropbox.attr'))
_UNWATCHED_FILE_PATTERNS_RE = [ re.compile(fnmatch.translate(pat)) for pat in ('~$*',
 '~*.tmp',
 '.~*',
 RECONSTRUCT_TEMP_FILE_PREFIX + '*') ]
_TEMP_FILE_PATTERNS_RE = [re.compile('^[0-9a-fA-F]{8}(\\.tmp)*$')] if _IS_WIN else []
_TEMP_AND_UNWATCHED_RE = _TEMP_FILE_PATTERNS_RE + _UNWATCHED_FILE_PATTERNS_RE

def snippet(text, maxchars = 30):
    if len(text) <= maxchars:
        return text
    else:
        dot_pos = text.rfind('.')
        if dot_pos > 0:
            ext = text[dot_pos:]
            maxchars = maxchars - len(ext)
        else:
            dot_pos = len(text)
            ext = ''
        maxchars = maxchars - 3
        left = int(maxchars * 3 / 4)
        right_count = maxchars - left
        right = dot_pos - right_count
        pre = text[:left]
        post = text[right:dot_pos]
        return pre + '...' + post + ext


def is_watched_local_path(local_path):
    return is_watched_filename(os.path.basename(local_path), os.path.isdir(local_path))


def random_string(length):
    return base64.b64encode(os.urandom(length))[:length]


def is_temp_file(filename):
    fn = os.path.basename(filename)
    return any((obj.match(fn) for obj in _TEMP_AND_UNWATCHED_RE))


def is_watched_filename(filename, isdir = False):
    if isdir:
        return True
    filename = filename.lower()
    if filename in IGNORED_FILES:
        return False
    return all((obj.match(filename) is None for obj in _UNWATCHED_FILE_PATTERNS_RE))


def get_mtime_size(st):
    is_dir = stat.S_ISDIR(st.st_mode)
    return (long(st.st_mtime),
     0 if is_dir else st.st_size,
     is_dir,
     long(st.st_ctime) if not _IS_WIN else None)


dsre = re.compile('\\\\(.)')

def desanitize(str, unescape_map = None):
    assert isinstance(str, unicode), 'offending string: %s' % (str,)
    if str.find(u'\\') == -1:
        return str
    if unescape_map is None:
        unescape_map = {u'n': u'\n',
         u't': u'\t'}
    unescape_map[u'\\'] = u'\\'

    def un(match):
        c = match.group(1)
        try:
            return unescape_map[c]
        except KeyError:
            return match.group(0)

    return dsre.sub(un, str)


def sanitize(str, escape_map = {u'\t': u't',
 u'\n': u'n'}):
    assert isinstance(str, unicode), 'offending string: %s' % (str,)
    str = str.replace(u'\\', u'\\\\')
    for k, v in escape_map.iteritems():
        str = str.replace(k, '\\' + v)

    return str


def get_arg(param):
    try:
        i = sys.argv.index(param)
    except Exception:
        raise Exception('no param')

    if i == len(sys.argv):
        raise Exception('no arg')
    return sys.argv[i + 1]


class frozendict(dict):
    singleton = None
    singleton_lock = threading.Lock()

    def __new__(cls, *args, **kw):
        if cls is not frozendict:
            result = super(frozendict, cls).__new__(cls, *args, **kw)
            super(frozendict, result).__init__(*args, **kw)
            return result
        if args or kw:
            if len(args) == 1 and type(args[0]) is frozendict:
                toret = args[0]
                return toret
            result = super(frozendict, cls).__new__(cls, *args, **kw)
            super(frozendict, result).__init__(*args, **kw)
            if result:
                return result
        if frozendict.singleton is None:
            with frozendict.singleton_lock:
                if frozendict.singleton is None:
                    frozendict.singleton = super(frozendict, cls).__new__(cls)
                    super(frozendict, frozendict.singleton).__init__()
        return frozendict.singleton

    def __init__(self, *n, **kw):
        pass

    def _blocked_attribute(self, *n, **kw):
        raise RuntimeError('A frozendict cannot be modified.')

    __delitem__ = __setitem__ = clear = _blocked_attribute
    pop = popitem = setdefault = update = _blocked_attribute

    def __repr__(self):
        return 'frozendict(%s)' % super(frozendict, self).__repr__()

    def __hash__(self):
        return hash(frozenset(self))


class lrudict(DictMixin):

    def __init__(self, subdict = None, notify_prune_fn = None, cache_size = 3000):
        self.lru_heap = []
        self.time = 0
        self.cache_size = cache_size
        self.need_to_heapify = False
        self.notify_prune_fn = notify_prune_fn
        self.subdict = {} if subdict is None else subdict
        self.keys = self.subdict.keys

    def clear(self):
        self.subdict = {}
        self.keys = self.subdict.keys
        self.lru_heap = []

    def __contains__(self, key):
        return key in self.subdict

    def __iter__(self):
        return iter(self.subdict)

    def iteritems(self):
        for i, v in self.subdict.iteritems():
            yield (i, v[2])

    def __delitem__(self, key):
        del self.subdict[key]
        for i, item in enumerate(self.lru_heap):
            if item[1] == key:
                break
        else:
            assert False

        del self.lru_heap[i]

    def __getitem__(self, key):
        obj = self.subdict[key]
        obj[0] = self.time
        self.need_to_heapify = True
        self.time += 1
        return obj[2]

    def __setitem__(self, key, value):
        if key in self.subdict:
            obj = self.subdict[key]
            obj[2] = value
            obj[0] = self.time
            self.need_to_heapify = True
        else:
            obj = [self.time, key, value]
            if self.need_to_heapify:
                heapq.heapify(self.lru_heap)
                self.need_to_heapify = False
            if len(self.lru_heap) == self.cache_size:
                a = heapq.heappop(self.lru_heap)
                if self.notify_prune_fn is not None:
                    self.notify_prune_fn(a[1])
                del self.subdict[a[1]]
            self.subdict[key] = obj
            heapq.heappush(self.lru_heap, obj)
        self.time += 1

    def lruitem(self):
        if self.need_to_heapify:
            heapq.heapify(self.lru_heap)
            self.need_to_heapify = False
        k = self.lru_heap[0][1]
        return (k, self.subdict[k][2])

    def __repr__(self):
        return '%s.lrudict(subdict=dict(%r), cache_size=%r)' % (self.__module__, list(self.iteritems()), self.cache_size)


class Memoizer(object):

    def __init__(self, fn, invalidate_data_fn = None, cache_size = 3000):
        self.fn = fn
        self.invalidate_data_fn = invalidate_data_fn
        self.value_cache = lrudict(cache_size=cache_size)

    def __call__(self, *n, **kw):
        args = tuple(n)
        invalidate_kw = kw.get('invalidate_kw', frozendict())
        retrieve_kw = kw.get('retrieve_kw', frozendict())
        new_val = None if self.invalidate_data_fn is None else self.invalidate_data_fn(*n, **invalidate_kw)
        if args in self.value_cache:
            ret, old_val = self.value_cache[args]
            if old_val != new_val:
                ret = self.fn(*n, **retrieve_kw)
                self.value_cache[args] = (ret, new_val)
        else:
            ret = self.fn(*n, **retrieve_kw)
            self.value_cache[args] = (ret, new_val)
        return ret


class SocketLineReader(object):

    def __init__(self, sock):
        self.bufs = []
        self.serv = sock

    def readline(self, block = True, timeout = None):
        data = ''.join(self.bufs)
        npos = data.find('\n')
        if npos == -1:
            self.bufs = [data]
        else:
            self.bufs = [data[npos + 1:]]
            return data[:npos + 1]
        realtimeout = timeout if block else 0
        while True:
            if realtimeout is not None and realtimeout < 0:
                raise TimeoutError()
            self.serv.settimeout(realtimeout)
            start = time.time()
            try:
                data = self.serv.recv(4096)
            except Exception as e:
                if isinstance(e, socket.timeout) or hasattr(e, 'args') and e.args and e.args[0] == errno.EAGAIN:
                    raise TimeoutError()
                else:
                    raise

            took = time.time() - start
            if realtimeout is not None:
                realtimeout -= took
            if data == '':
                raise EOFError()
            npos = data.find('\n')
            if npos == -1:
                self.bufs.append(data)
            else:
                self.bufs.append(data[:npos + 1])
                line = ''.join(self.bufs)
                self.bufs = [data[npos + 1:]]
                return line


def absreadlink(path):
    dest = os.readlink(path)
    if not isinstance(dest, unicode) and isinstance(path, unicode):
        dest = dest.decode('utf-8')
    if not os.path.isabs(dest):
        dest = os.path.join(os.path.dirname(path), dest)
    return os.path.normpath(dest)


def getrealcasedpath(path):
    pathlist = []
    while path != u'/':
        parent, tail = os.path.split(path)
        for child in os.listdir(parent):
            if child.lower() == tail.lower():
                pathlist.append(child)
                break
        else:
            raise Exception('No real cased path exists! %r' % path)

        path = parent

    if pathlist:
        return os.path.sep + os.path.join(*reversed(pathlist))
    return os.path.sep


_perm2mode = {'exec': 73,
 'write': 146,
 'read': 292}

def verify_file_perms_helper(local_file, perm_list = [], st = None, uid = None, groups = None):
    if st is None:
        st = os.stat(local_file)
    if uid is None:
        uid = os.geteuid()
    ret = True
    if uid == 0:
        if 'exec' in perm_list:
            ret &= st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0
        return ret
    if st.st_uid == uid:
        check = stat.S_IRWXU
    elif st.st_gid in (groups if groups is not None else os.getgroups()):
        check = stat.S_IRWXG
    else:
        check = stat.S_IRWXO
    for perm in perm_list:
        ret &= st.st_mode & (check & _perm2mode[perm]) != 0

    return ret


def verify_file_perms(local_file, perm, st = None):
    if not _IS_WIN:
        if not st:
            st = os.stat(local_file)
        uid = os.geteuid()
        if uid == 0:
            if perm == 'exec':
                return st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0
            return True
        if st.st_uid == uid:
            check = stat.S_IRWXU
        elif st.st_gid in os.getgroups():
            check = stat.S_IRWXG
        else:
            check = stat.S_IRWXO
        return st.st_mode & (check & _perm2mode[perm]) != 0
    else:
        return True


def can_write_dir(path):
    if not path:
        return False
    if not os.path.exists(path):
        newpath = os.path.dirname(path)
        if newpath == path:
            return False
        return can_write_dir(os.path.dirname(path))
    test_file = 'test'
    while os.path.exists(os.path.join(path, test_file)):
        test_file += '_'

    test_path = os.path.join(path, test_file)
    try:
        open(test_path, 'w').close()
        os.remove(test_path)
    except IOError:
        return False

    return True


def can_write_file(path):
    if os.path.exists(path):
        try:
            open(path, 'a').close()
            return True
        except IOError:
            return False

    else:
        return can_write_dir(os.path.dirname(path))


def lock_object_methods(the_object, locked_methods, the_lock = None):
    if not the_lock:
        the_lock = threading.Lock()
    for name in locked_methods:
        elt = getattr(the_object, name)

        def rebind(elt):

            def new_method(*n, **kw):
                with the_lock:
                    return elt(*n, **kw)

            return new_method

        setattr(the_object, name, rebind(elt))

    return the_object


def miniblocklist(s):
    if s is None:
        s = 'None'
    return ','.join([ x[:4] for x in s.split(',') ])


def paths_only_parents(local_paths, lower = True, key = None):
    last_path = '<not a path>'
    for ent in local_paths:
        if key:
            local_path = key(ent)
        else:
            local_path = ent
        llocal_path = local_path.lower() if lower else local_path
        if not llocal_path.startswith(last_path):
            last_path = llocal_path + os.path.sep
            yield ent


def migrate_db_schema(migrate_db_file):
    migrate_db_file.seek(0)
    with contextlib.closing(gzip.GzipFile(fileobj=migrate_db_file)) as f:
        return struct.unpack('L', f.read(struct.calcsize('L')))[0] - 65536


def migrate_db_get_table_entries(migrate_db_file, table):
    migrate_db_file.seek(0)
    Lsize = struct.calcsize('L')
    with contextlib.closing(gzip.GzipFile(fileobj=migrate_db_file)) as f:
        f.seek(Lsize)
        while True:
            num = f.read(Lsize)
            if not num:
                break
            table_name_len = struct.unpack('L', num)[0]
            assert table_name_len > 0 and table_name_len < 255
            table_name = f.read(table_name_len)
            count = struct.unpack('L', f.read(Lsize))[0]
            if table_name == table:
                for j in xrange(count):
                    yield pickle.loads(f.read(struct.unpack('L', f.read(Lsize))[0]))

            else:
                for j in xrange(count):
                    f.seek(struct.unpack('L', f.read(Lsize))[0] + f.tell())


class RepresentableContainer(object):

    def __repr__(self):
        return repr(self.__dict__)


def batch(iterable, size):
    sourceiter = iter(iterable)
    while True:
        batchiter = itertools.islice(sourceiter, size)
        yield itertools.chain((batchiter.next(),), batchiter)


def is_case_insensitive_path(root_path, return_file = False):
    if _IS_WIN:
        tmp_file = '~%dHI.tmp' % (random.randint(0, sys.maxint),)
    else:
        tmp_file = '.~%dHI' % (random.randint(0, sys.maxint),)
    orig_path = os.path.join(root_path, tmp_file)
    open(orig_path, 'w').close()
    try:
        does_exist = os.path.exists(os.path.join(root_path, tmp_file.lower()))
        if return_file:
            return (does_exist, orig_path)
        return does_exist
    finally:
        os.unlink(orig_path)


def function_address_of_builtin(bltin):
    if sys.version_info[:2] != (2, 5):
        raise Exception('Bad version of python')
    if type(bltin) is type(map):
        return ctypes.c_void_p.from_address(ctypes.c_void_p.from_address(id(bltin) + ctypes.sizeof(ctypes.c_size_t) + ctypes.sizeof(ctypes.c_void_p)).value + ctypes.sizeof(ctypes.c_void_p)).value
    if type(bltin) is type(file.read):
        return ctypes.c_void_p.from_address(ctypes.c_void_p.from_address(id(bltin) + ctypes.sizeof(ctypes.c_size_t) + ctypes.sizeof(ctypes.c_void_p) + ctypes.sizeof(ctypes.c_void_p) + ctypes.sizeof(ctypes.c_void_p)).value + ctypes.sizeof(ctypes.c_void_p)).value
    raise Exception('programming_error')


try:
    ctypes.pythonapi.PyBuffer_FromReadWriteObject.restype = ctypes.py_object
    ctypes.pythonapi.PyBuffer_FromReadWriteObject.argtypes = [ctypes.py_object, ctypes.c_size_t, ctypes.c_size_t]
    ctypes.pythonapi.PyObject_AsWriteBuffer.restype = ctypes.c_int
    ctypes.pythonapi.PyObject_AsWriteBuffer.argtypes = [ctypes.py_object, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)]
    ctypes.pythonapi.PyObject_AsReadBuffer.restype = ctypes.c_int
    ctypes.pythonapi.PyObject_AsReadBuffer.argtypes = [ctypes.py_object, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)]

    def rw_buffer(obj, offset = 0, size = None):
        if size is None:
            size = len(obj) - offset
        return ctypes.pythonapi.PyBuffer_FromReadWriteObject(obj, offset, size)


    def get_readable_pointer(buf):
        ptr = ctypes.c_void_p()
        size = ctypes.c_size_t()
        ctypes.pythonapi.PyObject_AsReadBuffer(buf, ctypes.byref(ptr), ctypes.byref(size))
        return (ptr.value, size.value)


    def get_writable_pointer(buf):
        ptr = ctypes.c_void_p()
        size = ctypes.c_size_t()
        ctypes.pythonapi.PyObject_AsWriteBuffer(buf, ctypes.byref(ptr), ctypes.byref(size))
        return (ptr.value, size.value)


except Exception:

    def rw_buffer(*n, **kw):
        raise Exception('bad version of python')


    def get_readable_pointer(*n, **kw):
        raise Exception('bad version of python')


    def get_writable_pointer(*n, **kw):
        raise Exception('bad version of python')


def copy_buffers(dest_buffer, src_buffer):
    dest_ptr, dest_size = get_writable_pointer(dest_buffer)
    src_ptr, src_size = get_readable_pointer(src_buffer)
    amt_copied = min(dest_size, src_size)
    ctypes.memmove(dest_ptr, src_ptr, amt_copied)
    return amt_copied


def safe_str(obj, encoding = 'utf-8'):
    try:
        return str(obj)
    except UnicodeEncodeError:
        return unicode(obj).encode(encoding)


_two_to_32 = 4294967296L
_two_to_31 = _two_to_32 / 2

def _generate_conversion_functions(width):
    _two_to_64 = 1 << width
    _two_to_63 = _two_to_64 >> 1

    def to_signed(num):
        assert 0 <= num < _two_to_64, 'Number is out the correct range: %r [0, %r)' % (num, _two_to_64)
        if num >= _two_to_63:
            return num - _two_to_64
        else:
            return num

    def to_unsigned(num):
        assert -_two_to_63 <= num < _two_to_64, 'Number is out the correct range: %r, [%r, %r]' % (num, -_two_to_63, _two_to_64)
        if num < 0:
            return num + _two_to_64
        else:
            return num

    return (to_signed, to_unsigned)


to_signed_64_bit, to_unsigned_64_bit = _generate_conversion_functions(64)
to_signed_32_bit, to_unsigned_32_bit = _generate_conversion_functions(32)

class SynchronizedObject(object):

    def __init__(self, obj, shared_lock_methods = (), exclusive_lock_methods = ()):
        self._obj = obj
        self._lock = _lock = RWLock()

        def locked_object_call(methname):

            def f(*n, **kw):
                with self._lock:
                    return getattr(self._obj, methname)(*n, **kw)

            return f

        def locked_object_call_ex(methname):

            def f(*n, **kw):
                self._lock.acquire_write()
                try:
                    return getattr(self._obj, methname)(*n, **kw)
                finally:
                    self._lock.release_write()

            return f

        for methods, dec in ((shared_lock_methods, locked_object_call), (exclusive_lock_methods, locked_object_call_ex)):
            for meth in methods:
                setattr(self, meth, dec(meth))

    def __getattr__(self, name):
        return getattr(self._obj, name)


LockedBinaryFile = functools.partial(SynchronizedObject, exclusive_lock_methods=('readinto', 'read', 'tell', 'write', 'truncate', 'flush', 'close', 'seek'))

def handle_exceptions_ex(should_raise = False, return_value = None, return_value_factory = None):

    def trans(f):

        @functools.wraps(f)
        def newfn(*n, **kw):
            try:
                return f(*n, **kw)
            except Exception:
                unhandled_exc_handler()
                if should_raise:
                    raise
                elif return_value_factory is not None:
                    return return_value_factory(*n, **kw)
                else:
                    return return_value

        return newfn

    return trans


handle_exceptions = handle_exceptions_ex()
convert_to_twos_complement = to_unsigned_32_bit

def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False

    return not isinstance(obj, basestring)


def split_extension(fn):
    if '.' not in fn:
        return (fn, '')
    fn, ext = fn.rsplit('.', 1)
    return (fn, '.%s' % ext)


def instance_method_decorator(dec):

    def fn_that_takes_a_fn(next_fn):

        def new_fn(self, *n, **kw):
            return dec(functools.partial(next_fn, self))(*n, **kw)

        return new_fn

    return fn_that_takes_a_fn


class classproperty(object):

    def __init__(self, getter):
        self.getter = getter
        functools.update_wrapper(self, getter)

    def __get__(self, instance, instance_type):
        return self.getter(instance_type)


@contextlib.contextmanager
def null_context(toyield = None):
    yield toyield


def trace_call(fn):

    @functools.wraps(fn)
    def wrapped(*n, **kw):
        TRACE('%s: --> %r, %r', fn.__name__, n, kw)
        ret = fn(*n, **kw)
        TRACE('%s: <-- %r', fn.__name__, ret)
        return ret

    return wrapped
