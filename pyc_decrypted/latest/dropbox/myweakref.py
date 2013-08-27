#Embedded file name: dropbox/myweakref.py
from __future__ import absolute_import
import UserDict
from _weakref import getweakrefcount, getweakrefs, ref, proxy, CallableProxyType, ProxyType, ReferenceType
from exceptions import ReferenceError
ProxyTypes = (ProxyType, CallableProxyType)

class MyWeakKeyDictionary(UserDict.UserDict):

    def __init__(self, dict = None, lock = None):
        self.data = {}

        def remove(k, selfref = ref(self)):
            self = selfref()
            if self is not None:
                if lock is not None:
                    with lock:
                        del self.data[k]
                else:
                    del self.data[k]

        self._remove = remove
        if dict is not None:
            self.update(dict)

    def __delitem__(self, key):
        del self.data[ref(key)]

    def __getitem__(self, key):
        return self.data[ref(key)]

    def __repr__(self):
        return '<WeakKeyDictionary at %s>' % id(self)

    def __setitem__(self, key, value):
        self.data[ref(key, self._remove)] = value

    def copy(self):
        new = MyWeakKeyDictionary()
        for key, value in self.data.iteritems():
            o = key()
            if o is not None:
                new[o] = value

        return new

    def get(self, key, default = None):
        return self.data.get(ref(key), default)

    def has_key(self, key):
        try:
            wr = ref(key)
        except TypeError:
            return 0

        return wr in self.data

    def __contains__(self, key):
        try:
            wr = ref(key)
        except TypeError:
            return 0

        return wr in self.data

    def items(self):
        L = []
        for key, value in self.data.items():
            o = key()
            if o is not None:
                L.append((o, value))

        return L

    def iteritems(self):
        for wr, value in self.data.iteritems():
            key = wr()
            if key is not None:
                yield (key, value)

    def iterkeyrefs(self):
        return self.data.iterkeys()

    def iterkeys(self):
        for wr in self.data.iterkeys():
            obj = wr()
            if obj is not None:
                yield obj

    def __iter__(self):
        return self.iterkeys()

    def itervalues(self):
        return self.data.itervalues()

    def keyrefs(self):
        return self.data.keys()

    def keys(self):
        L = []
        for wr in self.data.keys():
            o = wr()
            if o is not None:
                L.append(o)

        return L

    def popitem(self):
        while 1:
            key, value = self.data.popitem()
            o = key()
            if o is not None:
                return (o, value)

    def pop(self, key, *args):
        return self.data.pop(ref(key), *args)

    def setdefault(self, key, default = None):
        return self.data.setdefault(ref(key, self._remove), default)

    def update(self, dict = None, **kwargs):
        d = self.data
        if dict is not None:
            if not hasattr(dict, 'items'):
                dict = type({})(dict)
            for key, value in dict.items():
                d[ref(key, self._remove)] = value

        if len(kwargs):
            self.update(kwargs)
