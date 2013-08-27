#Embedded file name: dropbox/debugging.py
from __future__ import absolute_import
import random as insecure_random
import ctypes
import threading
import time
from dropbox.trace import TRACE

def trace_calls(f):

    def inner(*n, **kw):
        assert TRACE is not inner
        id = insecure_random.random()
        TRACE('{%r} %s(%r, %r)' % (id,
         f.__name__,
         n,
         kw))
        incoming = time.time()
        ret = f(*n, **kw)
        TRACE('{%r} %s() --> %r (took %r)' % (id,
         f.__name__,
         ret,
         time.time() - incoming))
        return ret

    return inner


template_repr_local = threading.local()

def template_repr(self, template, *fields):
    if not hasattr(template_repr_local, 'excluded_ids'):
        template_repr_local.excluded_ids = set()
    the_id = id(self)
    if the_id not in template_repr_local.excluded_ids:
        template_repr_local.excluded_ids.add(the_id)
        try:
            return template % {'module': self.__class__.__module__,
             'name': self.__class__.__name__,
             'inner': ' '.join(('%s=%r' % (attr, getattr(self, attr, '<NOTSET>')) for attr in fields)),
             'id': the_id}
        finally:
            template_repr_local.excluded_ids.remove(the_id)

    else:
        return template % {'module': self.__class__.__module__,
         'name': self.__class__.__name__,
         'inner': '...',
         'id': the_id}


def easy_repr(self, *fields):
    return template_repr(self, '<%(module)s.%(name)s %(inner)s at %(id)#x>', *fields)


def keyword_repr(self, *fields):
    return template_repr(self, '%(module)s.%(name)s(%(inner)s)', *fields)


class ReprStructure(ctypes.Structure):

    def __repr__(self):
        return keyword_repr(self, *(ent[0] for ent in self._fields_))
