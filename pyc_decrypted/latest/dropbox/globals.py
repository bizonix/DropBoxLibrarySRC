#Embedded file name: dropbox/globals.py
from __future__ import absolute_import
import time

def is_unicode(v):
    return isinstance(v, unicode)


class DropboxGlobals(dict):
    __conditions__ = {'dropbox': is_unicode}

    def __setitem__(self, k, v):
        if k in self.__conditions__:
            assert self.__conditions__[k](v), "Sorry, can't bring myself to set %r to %r" % (k, v)
        super(DropboxGlobals, self).__setitem__(k, v)

    def update(self, other):
        for k in other:
            if k in self.__conditions__:
                assert self.__conditions__[k](other[k]), "Sorry, can't bring myself to set %r to %r" % (k, other[k])

        super(DropboxGlobals, self).update(other)

    def setdefault(self, k, v = None):
        if k in self.__conditions__:
            assert self.__conditions__[k](v), "Sorry, can't bring myself to setdefault %r to %r" % (k, v)
        super(DropboxGlobals, self).setdefault(k, v)

    def __init__(self, *n, **kw):
        for k in kw:
            if k in self.__conditions__:
                assert self.__conditions__[k](kw[k]), 'Initial argument %r no good: %r' % (k, kw[k])

        super(DropboxGlobals, self).__init__(self, *n, **kw)


dropbox_globals = DropboxGlobals()
