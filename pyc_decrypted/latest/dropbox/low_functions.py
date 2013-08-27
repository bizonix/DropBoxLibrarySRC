#Embedded file name: dropbox/low_functions.py
import collections
import itertools

def split_len(seq, length):
    return (seq[i:i + length] for i in range(0, len(seq), length))


class WrapCall(object):

    def __init__(self, obj, new_f):
        object.__setattr__(self, '_obj', obj)
        object.__setattr__(self, '_f', new_f)

    def __getattr__(self, name):
        return getattr(self._obj, name)

    def __setattr__(self, name, value):
        return setattr(self._obj, name, value)

    def __call__(self, *n, **kw):
        return self._f(*n, **kw)


def identity(x):
    return x


def const(c):

    def fn(*n, **kw):
        return c

    return fn


_obj = undefined = object()

def head(l, d = _obj):
    try:
        return iter(l).next()
    except StopIteration:
        if d is not _obj:
            return d
        raise IndexError()


def tail(l, d = _obj):
    try:
        return reversed(l).next()
    except StopIteration:
        if d is not _obj:
            return d
        raise IndexError()


class container(object):

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return 'container(%s)' % ','.join(('%s=%r' % (k, getattr(self, k)) for k in dir(self) if not k.startswith('_')))


class NullObject(object):

    def __getattr__(self, *n, **kw):
        return self

    def __call__(self, *n, **kw):
        pass


def compose(*n):

    def composed(x):
        for f in reversed(n):
            x = f(x)

        return x

    return composed


def propagate_none(fn, val):
    if val is not None:
        return fn(val)


def from_maybe(default, val):
    if val is None:
        return default
    return val


def curry(uncurried):

    def take_a(a):

        def take_b(b):
            return uncurried(a, b)

        return take_b

    return take_a


class RuntimeMixin(object):

    def __init__(self, inner):
        self.inner = inner

    def __getattr__(self, key):
        return getattr(self.inner, key)

    def __enter__(self, *n, **kw):
        return self.inner.__enter__(*n, **kw)

    def __exit__(self, *n, **kw):
        return self.inner.__exit__(*n, **kw)


class OverrideRepr(RuntimeMixin):

    def __init__(self, inner, new_repr):
        self.inner = inner
        self.repr = new_repr

    def __repr__(self):
        return self.repr


def wrap_tuple(iterable):
    return ((a,) for a in iterable)


def select(needle, haystack, key = None):
    if key is None:
        key = identity
    for item in haystack:
        if key(needle) == key(item):
            return item


def find(f, iterable):
    for item in iterable:
        if f(item):
            return item


def partition(f, iterable, lazy = False):
    iter1, iter2 = itertools.tee(iterable, 2)
    true, false = itertools.ifilter(f, iter1), itertools.ifilterfalse(f, iter2)
    if not lazy:
        true, false = list(true), list(false)
    return (true, false)


def group_by(f, iterable):
    result = collections.defaultdict(list)
    for item in iterable:
        result[f(item)].append(item)

    return result


def safe_navigate(dictionary, *keys):
    try:
        for key in keys:
            dictionary = dictionary[key]

        return dictionary
    except KeyError:
        return None


class Closeable(object):

    def __enter__(self):
        return self

    def __exit__(self, *n, **kw):
        self.close()

    def close(self):
        raise NotImplementedError


def add_inner_methods(*method_names, **kw):
    decorator = kw.pop('decorator', None)
    if decorator is None:
        decorator = identity
    inner_name = kw.pop('inner_name', None)
    if inner_name is None:
        inner_name = 'inner'

    def wrapper(cls):

        def make_inner_fn(name):

            def wrapped(self, *n, **kw):
                return getattr(getattr(self, inner_name), name)(*n, **kw)

            wrapped.__name__ = name
            return wrapped

        new_dict = {outer_meth_name:decorator(make_inner_fn(inner_meth_name)) for outer_meth_name, inner_meth_name in itertools.chain(((x, x) for x in method_names), kw.iteritems())}
        return type(cls.__name__, (cls,), new_dict)

    return wrapper


def add_inner_properties(*property_names, **kw):
    inner_name = kw.get('inner_name', None)
    if inner_name is None:
        inner_name = 'inner'

    def wrapper(cls):

        def make_inner_prop(name):

            def _get(self):
                return getattr(getattr(self, inner_name), name)

            def _put(self, val):
                return setattr(getattr(self, inner_name), name, val)

            return property(_get, _put)

        new_dict = {name:make_inner_prop(name) for name in property_names}
        return type(cls.__name__, (cls,), new_dict)

    return wrapper


def coerce_list(obj):
    if isinstance(obj, list):
        return obj
    else:
        return list(obj)
