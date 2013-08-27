#Embedded file name: dropbox/lock_ordering.py
from __future__ import absolute_import
import gc
import itertools
import os
import pprint
import threading
import time
import traceback
from collections import defaultdict
from dropbox.myweakref import MyWeakKeyDictionary
from dropbox.trace import TRACE
BROKEN_LOCK_TRACING = False

class _OrderedLock(object):

    def __init__(self, tracker, plock, acquire_methods, release_methods, fname, line_no):
        self.plock = plock
        self.tracker = tracker
        self.fname = fname
        self.line_no = line_no
        for maker, methods in ((self.make_acquirer, acquire_methods), (self.make_releaser, release_methods)):
            for method_name in methods:
                setattr(self, method_name, maker(method_name))

        self.default_acquire = getattr(self, acquire_methods[0])
        self.default_release = getattr(self, release_methods[0])

    def make_acquirer(self, method_name):

        def acquirer(*n, **kw):
            t = self.tracker
            try:
                pld = t.local.previous_locks_dict
                pl = t.local.previous_locks
                pls = t.local.previous_lock_sites
                st = t.local.stop_tracking
            except AttributeError:
                pld = t.local.previous_locks_dict = defaultdict(int)
                pl = t.local.previous_locks = []
                pls = t.local.previous_lock_sites = []
                st = t.local.stop_tracking = None

            if BROKEN_LOCK_TRACING and (self.fname, self.line_no) in t.broken_lock_pairs:
                key = (self.fname, self.line_no)
                for lock, tb in zip(pl, pls):
                    if (lock.fname, lock.line_no) in t.broken_lock_pairs[key]:
                        TRACE('Broken lock pair: (%r %r, %r %r)', *(lock,
                         ''.join(tb),
                         self,
                         ''.join(traceback.format_stack())))

            error_tuple = None
            if not st and pl and self not in pld:
                with t.parent_child_lock:
                    pcm = t.parent_child_map
                    cpm = t.child_parent_map
                    pchild_set = pcm.setdefault(self, MyWeakKeyDictionary(lock=t.parent_child_lock))
                    cpm.setdefault(self, MyWeakKeyDictionary(lock=t.parent_child_lock))
                    if any((cp in pchild_set for cp in pl)):
                        for cp in pl:
                            if cp in pchild_set:
                                break

                        error_string = 'Locks taken in invalid order!\n%r (id: %r)\n\ntaken after:\n%r (id %r)\n\nin:\n%s\n\nlock attempted children:\n%s\n'
                        error_string %= (self,
                         id(self),
                         cp,
                         id(cp),
                         pprint.pformat(pl),
                         pprint.pformat(pchild_set.keys()))
                        error_tuple = (self, cp, error_string)
                    else:
                        immediate_parent = pl[-1]
                        start_top = immediate_parent not in cpm[self]
                        start_bottom = self not in pcm[immediate_parent]
                        if start_top or start_bottom:
                            gc.disable()
                            try:
                                if start_top:
                                    for parent in itertools.chain((immediate_parent,), cpm[immediate_parent].iterkeys()):
                                        pcm[parent].update(itertools.chain(((self, 1),), pcm[self].iteritems()))

                                if start_bottom:
                                    for child in itertools.chain((self,), pcm[self].iterkeys()):
                                        cpm[child].update(itertools.chain(((immediate_parent, 1),), cpm[immediate_parent].iteritems()))

                            finally:
                                gc.enable()

            else:
                with t.parent_child_lock:
                    t.parent_child_map.setdefault(self, MyWeakKeyDictionary(lock=t.parent_child_lock))
                    t.child_parent_map.setdefault(self, MyWeakKeyDictionary(lock=t.parent_child_lock))
            if error_tuple:
                t.action(*error_tuple)
                t.local.stop_tracking = self
            rc = getattr(self.plock, method_name)(*n, **kw)
            if rc:
                pl.append(self)
                if BROKEN_LOCK_TRACING:
                    pls.append(traceback.format_stack())
                pld[self] += 1
            return rc

        return acquirer

    def make_releaser(self, method_name):

        def releaser(*n, **kw):
            getattr(self.plock, method_name)(*n, **kw)
            l = self.tracker.local
            if l.stop_tracking is self:
                l.stop_tracking = None
            assert self is l.previous_locks[-1], 'Popped lock %r is not %r' % (l.previous_locks[-1], self)
            l.previous_locks.pop()
            if BROKEN_LOCK_TRACING:
                l.previous_lock_sites.pop()
            l.previous_locks_dict[self] -= 1
            if not l.previous_locks_dict[self]:
                del l.previous_locks_dict[self]

        return releaser

    def __enter__(self):
        self.default_acquire()

    def __exit__(self, *n, **kw):
        self.default_release()

    def __getattr__(self, name):
        return getattr(self.plock, name)

    def __repr__(self):
        return '<OrderedLock %r>' % (self.plock,)


def _just_raise(string):
    raise Exception(string)


class NonRecursiveLock(object):

    def __init__(self, base_lock = None, acquire_methods = ('acquire',), release_methods = ('release',)):
        self.lock = base_lock or threading.Lock()
        self.local = threading.local()
        for maker, method_names in ((self.make_acquirer, acquire_methods), (self.make_releaser, release_methods)):
            for method_name in method_names:
                setattr(self, method_name, maker(method_name))

        self.default_acquire = getattr(self, acquire_methods[0])
        self.default_release = getattr(self, release_methods[0])

    def locked(self):
        return self.lock.locked()

    def make_acquirer(self, method_name):

        def acquirer(*n, **kw):
            if getattr(self.local, 'locked', False):
                raise Exception('Cannot recursively acquire this lock')
            rc = getattr(self.lock, method_name)(*n, **kw)
            self.local.locked = rc
            return rc

        return acquirer

    def make_releaser(self, method_name):

        def releaser(*n, **kw):
            assert self.local.locked, 'Called release when locked was not locked'
            self.local.locked = False
            return getattr(self.lock, method_name)(*n, **kw)

        return releaser

    def __enter__(self):
        self.default_acquire()

    def __exit__(self, *n, **kw):
        self.default_release()

    def __getattr__(self, name):
        return getattr(self.lock, name)


class OrderedLockTracker(object):

    def __init__(self, action = None, default_lock_type = None):
        self.local = threading.local()
        self.parent_child_lock = threading.RLock()
        self.parent_child_map = MyWeakKeyDictionary(lock=self.parent_child_lock)
        self.child_parent_map = MyWeakKeyDictionary(lock=self.parent_child_lock)
        if not action:
            action = lambda a, b, msg: _just_raise(msg)
        self.action = action
        self.handling = False
        self.default_lock_type = default_lock_type
        if BROKEN_LOCK_TRACING:
            self.broken_lock_pairs = _make_lookup_table(_read_broken_locks())
        else:
            self.broken_lock_pairs = {}

    def allocate_lock(self, base_lock = None, acquire_methods = ('acquire',), release_methods = ('release',), fname = None, line_no = None):
        lock = base_lock or self.default_lock_type and self.default_lock_type() or threading.Lock()
        return _OrderedLock(self, lock, acquire_methods, release_methods, fname, line_no)


BROKEN_LOCK_FILE = '.dropbox.broken_locks'
DAYS_TO_KEEP = 1

def _get_lock_file_path(fname):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), fname)


def _read_broken_locks(fname = BROKEN_LOCK_FILE, days = DAYS_TO_KEEP):
    broken_locks = {}
    if os.path.exists(fname):
        abs_path = _get_lock_file_path(fname)
        with open(abs_path) as f:
            for line in f:
                f1, l1, f2, l2, ts = line.strip().split(':')
                if float(ts) < time.time() - days * 24 * 60 * 60:
                    continue
                broken_locks[f1, l1, f2, l2] = ts

    return broken_locks


def _write_broken_locks(broken_locks, fname = BROKEN_LOCK_FILE):
    abs_path = _get_lock_file_path(fname)
    with open(abs_path, 'w') as f:
        for (f1, l1, f2, l2), ts in broken_locks.iteritems():
            f.write(':'.join((str(x) for x in (f1,
             l1,
             f2,
             l2,
             ts))))


def _make_lookup_table(lock_list):
    broken_lock_pairs = defaultdict(set)
    for (f1, l1, f2, l2), ts in lock_list.iteritems():
        broken_lock_pairs[f1, l1].add((f2, l2))
        broken_lock_pairs[f2, l2].add((f1, l1))

    return broken_lock_pairs


def record_broken_locks_and_raise(lock1, lock2, msg):
    if BROKEN_LOCK_TRACING:
        broken_locks = _read_broken_locks()
        key = (lock1.fname,
         lock1.line_no,
         lock2.fname,
         lock2.line_no)
        try:
            del broken_locks[key]
        except KeyError:
            pass

        broken_locks[key] = time.time()
        _write_broken_locks(broken_locks)
    _just_raise(msg)
