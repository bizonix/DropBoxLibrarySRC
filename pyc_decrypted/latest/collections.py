#Embedded file name: collections.py
__all__ = ['Counter',
 'deque',
 'defaultdict',
 'namedtuple',
 'OrderedDict']
from _abcoll import *
import _abcoll
__all__ += _abcoll.__all__
from _collections import deque, defaultdict
from operator import itemgetter as _itemgetter
from keyword import iskeyword as _iskeyword
import sys as _sys
import heapq as _heapq
from itertools import repeat as _repeat, chain as _chain, starmap as _starmap
try:
    from thread import get_ident as _get_ident
except ImportError:
    from dummy_thread import get_ident as _get_ident

class OrderedDict(dict):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__root
        except AttributeError:
            self.__root = root = []
            root[:] = [root, root, None]
            self.__map = {}

        self.__update(*args, **kwds)

    def __setitem__(self, key, value, PREV = 0, NEXT = 1, dict_setitem = dict.__setitem__):
        if key not in self:
            root = self.__root
            last = root[PREV]
            last[NEXT] = root[PREV] = self.__map[key] = [last, root, key]
        dict_setitem(self, key, value)

    def __delitem__(self, key, PREV = 0, NEXT = 1, dict_delitem = dict.__delitem__):
        dict_delitem(self, key)
        link_prev, link_next, key = self.__map.pop(key)
        link_prev[NEXT] = link_next
        link_next[PREV] = link_prev

    def __iter__(self):
        NEXT, KEY = (1, 2)
        root = self.__root
        curr = root[NEXT]
        while curr is not root:
            yield curr[KEY]
            curr = curr[NEXT]

    def __reversed__(self):
        PREV, KEY = (0, 2)
        root = self.__root
        curr = root[PREV]
        while curr is not root:
            yield curr[KEY]
            curr = curr[PREV]

    def clear(self):
        for node in self.__map.itervalues():
            del node[:]

        root = self.__root
        root[:] = [root, root, None]
        self.__map.clear()
        dict.clear(self)

    def keys(self):
        return list(self)

    def values(self):
        return [ self[key] for key in self ]

    def items(self):
        return [ (key, self[key]) for key in self ]

    def iterkeys(self):
        return iter(self)

    def itervalues(self):
        for k in self:
            yield self[k]

    def iteritems(self):
        for k in self:
            yield (k, self[k])

    update = MutableMapping.update
    __update = update
    __marker = object()

    def pop(self, key, default = __marker):
        if key in self:
            result = self[key]
            del self[key]
            return result
        if default is self.__marker:
            raise KeyError(key)
        return default

    def setdefault(self, key, default = None):
        if key in self:
            return self[key]
        self[key] = default
        return default

    def popitem(self, last = True):
        if not self:
            raise KeyError('dictionary is empty')
        key = next(reversed(self) if last else iter(self))
        value = self.pop(key)
        return (key, value)

    def __repr__(self, _repr_running = {}):
        call_key = (id(self), _get_ident())
        if call_key in _repr_running:
            return '...'
        _repr_running[call_key] = 1
        try:
            if not self:
                return '%s()' % (self.__class__.__name__,)
            return '%s(%r)' % (self.__class__.__name__, self.items())
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        items = [ [k, self[k]] for k in self ]
        inst_dict = vars(self).copy()
        for k in vars(OrderedDict()):
            inst_dict.pop(k, None)

        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return (self.__class__, (items,))

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value = None):
        self = cls()
        for key in iterable:
            self[key] = value

        return self

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self) == len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

    def viewkeys(self):
        return KeysView(self)

    def viewvalues(self):
        return ValuesView(self)

    def viewitems(self):
        return ItemsView(self)


def namedtuple(typename, field_names, verbose = False, rename = False):
    if isinstance(field_names, basestring):
        field_names = field_names.replace(',', ' ').split()
    field_names = tuple(map(str, field_names))
    if rename:
        names = list(field_names)
        seen = set()
        for i, name in enumerate(names):
            if not all((c.isalnum() or c == '_' for c in name)) or _iskeyword(name) or not name or name[0].isdigit() or name.startswith('_') or name in seen:
                names[i] = '_%d' % i
            seen.add(name)

        field_names = tuple(names)
    for name in (typename,) + field_names:
        if not all((c.isalnum() or c == '_' for c in name)):
            raise ValueError('Type names and field names can only contain alphanumeric characters and underscores: %r' % name)
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a keyword: %r' % name)
        if name[0].isdigit():
            raise ValueError('Type names and field names cannot start with a number: %r' % name)

    seen_names = set()
    for name in field_names:
        if name.startswith('_') and not rename:
            raise ValueError('Field names cannot start with an underscore: %r' % name)
        if name in seen_names:
            raise ValueError('Encountered duplicate field name: %r' % name)
        seen_names.add(name)

    numfields = len(field_names)
    argtxt = repr(field_names).replace("'", '')[1:-1]
    reprtxt = ', '.join(('%s=%%r' % name for name in field_names))
    template = "class %(typename)s(tuple):\n        '%(typename)s(%(argtxt)s)' \n\n        __slots__ = () \n\n        _fields = %(field_names)r \n\n        def __new__(_cls, %(argtxt)s):\n            'Create new instance of %(typename)s(%(argtxt)s)'\n            return _tuple.__new__(_cls, (%(argtxt)s)) \n\n        @classmethod\n        def _make(cls, iterable, new=tuple.__new__, len=len):\n            'Make a new %(typename)s object from a sequence or iterable'\n            result = new(cls, iterable)\n            if len(result) != %(numfields)d:\n                raise TypeError('Expected %(numfields)d arguments, got %%d' %% len(result))\n            return result \n\n        def __repr__(self):\n            'Return a nicely formatted representation string'\n            return '%(typename)s(%(reprtxt)s)' %% self \n\n        def _asdict(self):\n            'Return a new OrderedDict which maps field names to their values'\n            return OrderedDict(zip(self._fields, self)) \n\n        __dict__ = property(_asdict) \n\n        def _replace(_self, **kwds):\n            'Return a new %(typename)s object replacing specified fields with new values'\n            result = _self._make(map(kwds.pop, %(field_names)r, _self))\n            if kwds:\n                raise ValueError('Got unexpected field names: %%r' %% kwds.keys())\n            return result \n\n        def __getnewargs__(self):\n            'Return self as a plain tuple.  Used by copy and pickle.'\n            return tuple(self) \n\n" % locals()
    for i, name in enumerate(field_names):
        template += "        %s = _property(_itemgetter(%d), doc='Alias for field number %d')\n" % (name, i, i)

    if verbose:
        print template
    namespace = dict(_itemgetter=_itemgetter, __name__='namedtuple_%s' % typename, OrderedDict=OrderedDict, _property=property, _tuple=tuple)
    try:
        exec template in namespace
    except SyntaxError as e:
        raise SyntaxError(e.message + ':\n' + template)

    result = namespace[typename]
    try:
        result.__module__ = _sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return result


class Counter(dict):

    def __init__(self, iterable = None, **kwds):
        super(Counter, self).__init__()
        self.update(iterable, **kwds)

    def __missing__(self, key):
        return 0

    def most_common(self, n = None):
        if n is None:
            return sorted(self.iteritems(), key=_itemgetter(1), reverse=True)
        return _heapq.nlargest(n, self.iteritems(), key=_itemgetter(1))

    def elements(self):
        return _chain.from_iterable(_starmap(_repeat, self.iteritems()))

    @classmethod
    def fromkeys(cls, iterable, v = None):
        raise NotImplementedError('Counter.fromkeys() is undefined.  Use Counter(iterable) instead.')

    def update(self, iterable = None, **kwds):
        if iterable is not None:
            if isinstance(iterable, Mapping):
                if self:
                    self_get = self.get
                    for elem, count in iterable.iteritems():
                        self[elem] = self_get(elem, 0) + count

                else:
                    super(Counter, self).update(iterable)
            else:
                self_get = self.get
                for elem in iterable:
                    self[elem] = self_get(elem, 0) + 1

        if kwds:
            self.update(kwds)

    def subtract(self, iterable = None, **kwds):
        if iterable is not None:
            self_get = self.get
            if isinstance(iterable, Mapping):
                for elem, count in iterable.items():
                    self[elem] = self_get(elem, 0) - count

            else:
                for elem in iterable:
                    self[elem] = self_get(elem, 0) - 1

        if kwds:
            self.subtract(kwds)

    def copy(self):
        return self.__class__(self)

    def __reduce__(self):
        return (self.__class__, (dict(self),))

    def __delitem__(self, elem):
        if elem in self:
            super(Counter, self).__delitem__(elem)

    def __repr__(self):
        if not self:
            return '%s()' % self.__class__.__name__
        items = ', '.join(map('%r: %r'.__mod__, self.most_common()))
        return '%s({%s})' % (self.__class__.__name__, items)

    def __add__(self, other):
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            newcount = count + other[elem]
            if newcount > 0:
                result[elem] = newcount

        for elem, count in other.items():
            if elem not in self and count > 0:
                result[elem] = count

        return result

    def __sub__(self, other):
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            newcount = count - other[elem]
            if newcount > 0:
                result[elem] = newcount

        for elem, count in other.items():
            if elem not in self and count < 0:
                result[elem] = 0 - count

        return result

    def __or__(self, other):
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            other_count = other[elem]
            newcount = other_count if count < other_count else count
            if newcount > 0:
                result[elem] = newcount

        for elem, count in other.items():
            if elem not in self and count > 0:
                result[elem] = count

        return result

    def __and__(self, other):
        if not isinstance(other, Counter):
            return NotImplemented
        result = Counter()
        for elem, count in self.items():
            other_count = other[elem]
            newcount = count if count < other_count else other_count
            if newcount > 0:
                result[elem] = newcount

        return result


if __name__ == '__main__':
    from cPickle import loads, dumps
    Point = namedtuple('Point', 'x, y', True)
    p = Point(x=10, y=20)
    assert p == loads(dumps(p))

    class Point(namedtuple('Point', 'x y')):
        __slots__ = ()

        @property
        def hypot(self):
            return (self.x ** 2 + self.y ** 2) ** 0.5

        def __str__(self):
            return 'Point: x=%6.3f  y=%6.3f  hypot=%6.3f' % (self.x, self.y, self.hypot)


    for p in (Point(3, 4), Point(14, 5 / 7.0)):
        print p

    class Point(namedtuple('Point', 'x y')):
        __slots__ = ()
        _make = classmethod(tuple.__new__)

        def _replace(self, _map = map, **kwds):
            return self._make(_map(kwds.get, ('x', 'y'), self))


    print Point(11, 22)._replace(x=100)
    Point3D = namedtuple('Point3D', Point._fields + ('z',))
    print Point3D.__doc__
    import doctest
    TestResults = namedtuple('TestResults', 'failed attempted')
    print TestResults(*doctest.testmod())
