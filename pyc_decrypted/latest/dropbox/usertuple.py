#Embedded file name: dropbox/usertuple.py
from __future__ import absolute_import
import threading
from weakref import WeakValueDictionary
from dropbox.seqtools import seqslice
_map_lock = threading.Lock()
_map = WeakValueDictionary()

def _user_tuple_len(self):
    return len(self.__slots__)


def _user_tuple_getitem(self, key):
    try:
        return seqslice(self, *key.indices(len(self)))
    except AttributeError:
        return getattr(self, self.__slots__[key])


def _user_tuple_iter(self):
    for i in self.__slots__:
        yield getattr(self, i)


def _user_tuple_eq(self, other):
    l = len(self)
    return type(self) is type(other) and len(other) == l and all((self[i] == other[i] for i in xrange(l)))


def _user_tuple_ne(self, other):
    l = len(self)
    return type(self) is not type(other) or len(other) != l or any((self[i] != other[i] for i in xrange(l)))


def _user_tuple_repr(self):
    return '%s.UserTuple(%s)' % (self.__module__, ','.join([ repr(i) for i in self ]))


def _user_tuple_hash(self):
    l = len(self) << 1
    mult = 1000003
    x = 3430008
    for elt in self:
        x = (x ^ hash(elt)) * mult
        mult += 82520 + l

    x += 97531
    if x == -1:
        x = -2
    return x


def UserTuple(*args):
    nargs = len(args)
    try:
        the_type = _map[nargs]
    except KeyError:
        with _map_lock:
            try:
                the_type = _map[nargs]
            except KeyError:
                the_type = type('%d-tuple' % nargs, (object,), {'__len__': _user_tuple_len,
                 '__getitem__': _user_tuple_getitem,
                 '__iter__': _user_tuple_iter,
                 '__hash__': _user_tuple_hash,
                 '__eq__': _user_tuple_eq,
                 '__ne__': _user_tuple_ne,
                 '__repr__': _user_tuple_repr,
                 '__slots__': [ 'slot_%d' % n for n in xrange(nargs) ],
                 '__use_advanced_allocator__': 1048576})
                _map[nargs] = the_type

    toret = the_type()
    for i, a in enumerate(args):
        setattr(toret, the_type.__slots__[i], a)

    return toret
