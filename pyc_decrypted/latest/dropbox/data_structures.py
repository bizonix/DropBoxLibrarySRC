#Embedded file name: dropbox/data_structures.py
from __future__ import absolute_import
import heapq
from UserDict import DictMixin
from dropbox.low_functions import identity
from dropbox.trace import unhandled_exc_handler

class RefCountedSet(dict):

    def ref(self, what):
        self[what] = self.get(what, 0) + 1

    def deref(self, what):
        try:
            old_count = self[what]
        except KeyError:
            return True

        if old_count <= 1:
            del self[what]
            return True
        else:
            self[what] = old_count - 1
            return False


class SetDict(dict):

    def set_add_callback(self, cb):
        self.add_cb = cb

    def set_del_callback(self, cb):
        self.del_cb = cb

    def copy(self):
        return SetDict(((a, set(b)) for a, b in self))

    def add(self, k, what):
        if k not in self:
            self[k] = set([what])
            if getattr(self, 'add_cb', None):
                try:
                    self.add_cb(k, what)
                except Exception:
                    unhandled_exc_handler()

        else:
            self[k].add(what)

    def remove(self, k, what):
        if k in self:
            v = self[k]
            v.remove(what)
            if not v:
                if getattr(self, 'del_cb', None):
                    try:
                        self.del_cb(k)
                    except Exception:
                        unhandled_exc_handler()

                del self[k]

    def clear(self):
        for k in self.keys():
            for v in list(self[k]):
                self.remove(k, v)


TESTING = False
DEBUGGING = True

class ManyToMany(object):

    def __low_init__(self, a_to_b, b_to_a):
        self.a_to_b = a_to_b
        self.b_to_a = b_to_a
        self.inside = False

    def __init__(self, left_callbacks = None, right_callbacks = None):
        a_to_b = SetDict()
        if left_callbacks:
            a_to_b.set_add_callback(left_callbacks[0])
            a_to_b.set_del_callback(left_callbacks[1])
        b_to_a = SetDict()
        if right_callbacks:
            b_to_a.set_add_callback(right_callbacks[0])
            b_to_a.set_del_callback(right_callbacks[1])
        self.__low_init__(a_to_b, b_to_a)

    def __repr__(self):
        return '<ManyToMany a_to_b=%r, b_to_a=%r>' % (self.a_to_b, self.b_to_a)

    def _invariant(self):
        for k, v in self.a_to_b.iteritems():
            for v1 in v:
                if k not in self.b_to_a[v1]:
                    raise Exception('Extra pair in a_to_b: %r %r' % (k, v1))

        for k, v in self.b_to_a.iteritems():
            for v1 in v:
                if k not in self.a_to_b[v1]:
                    raise Exception('Extra pair in b_to_a: %r %r' % (k, v1))

    def inv(fn):

        def new_fn(self, *n, **kw):
            if DEBUGGING:
                if self.inside:
                    raise Exception('this object is not re-entrant!')
                self.inside = True
            if TESTING:
                self._invariant()
            try:
                return fn(self, *n, **kw)
            finally:
                if TESTING:
                    self._invariant()
                if DEBUGGING:
                    self.inside = False

        return new_fn

    def copy(self, left_callbacks = None, right_callbacks = None):
        a_to_b = self.a_to_b.copy()
        if left_callbacks:
            a_to_b.set_add_callback(left_callbacks[0])
            a_to_b.set_del_callback(left_callbacks[1])
        b_to_a = self.b_to_a.copy()
        if right_callbacks:
            b_to_a.set_add_callback(right_callbacks[0])
            b_to_a.set_del_callback(right_callbacks[1])
        self.__low_init__(a_to_b, b_to_a)

    def left_keys(self):
        return self.a_to_b.keys()

    @inv
    def add(self, a, b):
        self.a_to_b.add(a, b)
        self.b_to_a.add(b, a)

    @inv
    def remove(self, a, b):
        self.a_to_b.remove(a, b)
        self.b_to_a.remove(b, a)

    @inv
    def remove_left(self, a):
        try:
            to_ret = self.a_to_b[a]
        except KeyError:
            to_ret = ()
        else:
            for b in to_ret:
                self.b_to_a.remove(b, a)

            del self.a_to_b[a]

        return to_ret

    @inv
    def remove_right(self, b):
        if b in self.b_to_a:
            toret = self.b_to_a[b]
            for a in toret:
                self.a_to_b.remove(a, b)

            del self.b_to_a[b]
        else:
            toret = ()
        return toret

    def in_left(self, k):
        return k in self.a_to_b

    def in_right(self, k):
        return k in self.b_to_a

    @inv
    def clear(self):
        self.a_to_b.clear()
        self.b_to_a.clear()


_secret_obj = object()

class DictQueue(object, DictMixin):

    def __low_init__(self, key_to_ent, queue, key_fn):
        self.key_to_ent = key_to_ent
        self.queue = queue
        self.key_fn = key_fn

    def __init__(self, key_fn = identity):
        self.__low_init__({}, [], key_fn)

    def copy(self):
        new_dict_queue = type(self)(key_fn=self.key_fn)
        new_dict_queue.update(self)
        return new_dict_queue

    def __contains__(self, elt):
        return elt in self.key_to_ent

    def __repr__(self):
        return repr(self.queue)

    def __len__(self):
        return len(self.key_to_ent)

    def __nonzero__(self):
        return bool(self.key_to_ent)

    def __iter__(self):
        return iter(self.key_to_ent)

    def keys(self):
        return self.key_to_ent.keys()

    def iteritems(self):
        for k, v in self.key_to_ent.iteritems():
            yield (k, v[1])

    def __delitem__(self, k):
        ent = self.key_to_ent[k]
        val = ent[1]
        ent[1] = _secret_obj
        del self.key_to_ent[k]

    def __getitem__(self, k):
        return self.key_to_ent[k][1]

    def __setitem__(self, k, v):
        if k in self.key_to_ent:
            ent = self.key_to_ent[k]
            ent[1] = _secret_obj
        newent = [self.key_fn(v), v]
        self.key_to_ent[k] = newent
        heapq.heappush(self.queue, newent)

    def inorder(self):
        popped_items = []
        try:
            while self.queue:
                first = self.queue[0]
                if first[1] is _secret_obj:
                    heapq.heappop(self.queue)
                    continue
                yield first[1]
                if self.queue[0] is not first:
                    raise Exception('Item added to DictQueue while iterating.')
                if first is not _secret_obj:
                    popped_items.append(heapq.heappop(self.queue))

        finally:
            if popped_items:
                if not self.queue:
                    self.queue = popped_items
                else:
                    self.queue = popped_items + self.queue
                    heapq.heapify(self.queue)

    def peek(self, lim = 0, while_fn = None):
        if lim == 1:
            while self.queue and self.queue[0][1] is _secret_obj:
                heapq.heappop(self.queue)

            return self.queue[0][1]
        if not self.queue:
            return ()
        if not lim:
            toret = []
            while self.queue:
                first = self.queue[0]
                if first[1] is _secret_obj:
                    heapq.heappop(self.queue)
                    continue
                if while_fn and not while_fn(first[1]):
                    break
                toret.append(heapq.heappop(self.queue))

        else:
            toret = [None] * lim
            i = 0
            while i < lim and self.queue:
                first = self.queue[0]
                if first[1] is _secret_obj:
                    heapq.heappop(self.queue)
                    continue
                if while_fn and not while_fn(first[1]):
                    break
                toret[i] = heapq.heappop(self.queue)
                i += 1

            if i < lim:
                del toret[i:]
        for j in xrange(len(toret)):
            elt = toret[j]
            heapq.heappush(self.queue, elt)
            toret[j] = elt[1]

        return toret


class SlotDict(object):

    def __init__(self, *args, **kwargs):
        if args:
            for key, value in args[0].items():
                setattr(self, key, value)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def getvalues(self, *args):
        return (getattr(self, y) for y in args)

    def __iter__(self):
        return ((key, getattr(self, key)) for key in self.__slots__)

    def __hash__(self):
        return hash(tuple([ getattr(self, key, None) for key in self.__slots__ ]))

    def get(self, key, default = None):
        try:
            return getattr(self, key)
        except:
            return default
