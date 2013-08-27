#Embedded file name: babel/localedata.py
from __future__ import absolute_import
import os
import pickle
import imp
try:
    import threading
except ImportError:
    import dummy_threading as threading

from UserDict import DictMixin
from .localedata2 import locales_available
__all__ = ['exists', 'list', 'load']
__docformat__ = 'restructuredtext en'
_cache = {}
_cache_lock = threading.RLock()

def exists(name):
    if name in _cache:
        return True
    else:
        try:
            __import__('babel.localedata2.%s' % name)
        except Exception:
            return False

        return True


_list = list

def list():
    return _list(locales_available)


def load(name, merge_inherited = True):
    _cache_lock.acquire()
    try:
        data = _cache.get(name)
        if not data:
            if name == 'root' or not merge_inherited:
                data = {}
            else:
                parts = name.split('_')
                if len(parts) == 1:
                    parent = 'root'
                else:
                    parent = '_'.join(parts[:-1])
                data = load(parent).copy()
            _s = getattr(__import__('babel.localedata2.%s' % name).localedata2, name).data
            if name != 'root' and merge_inherited:
                merge(data, pickle.loads(_s))
            else:
                data = pickle.loads(_s)
            _cache[name] = data
        return data
    finally:
        _cache_lock.release()


def merge(dict1, dict2):
    for key, val2 in dict2.items():
        if val2 is not None:
            val1 = dict1.get(key)
            if isinstance(val2, dict):
                if val1 is None:
                    val1 = {}
                if isinstance(val1, Alias):
                    val1 = (val1, val2)
                elif isinstance(val1, tuple):
                    alias, others = val1
                    others = others.copy()
                    merge(others, val2)
                    val1 = (alias, others)
                else:
                    val1 = val1.copy()
                    merge(val1, val2)
            else:
                val1 = val2
            dict1[key] = val1


class Alias(object):

    def __init__(self, keys):
        self.keys = tuple(keys)

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.keys)

    def resolve(self, data):
        base = data
        for key in self.keys:
            data = data[key]

        if isinstance(data, Alias):
            data = data.resolve(base)
        elif isinstance(data, tuple):
            alias, others = data
            data = alias.resolve(base)
        return data


class LocaleDataDict(DictMixin, dict):

    def __init__(self, data, base = None):
        dict.__init__(self, data)
        if base is None:
            base = data
        self.base = base

    def __getitem__(self, key):
        orig = val = dict.__getitem__(self, key)
        if isinstance(val, Alias):
            val = val.resolve(self.base)
        if isinstance(val, tuple):
            alias, others = val
            val = alias.resolve(self.base).copy()
            merge(val, others)
        if type(val) is dict:
            val = LocaleDataDict(val, base=self.base)
        if val is not orig:
            self[key] = val
        return val

    def copy(self):
        return LocaleDataDict(dict.copy(self), base=self.base)
