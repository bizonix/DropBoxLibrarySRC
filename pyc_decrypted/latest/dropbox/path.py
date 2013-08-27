#Embedded file name: dropbox/path.py
from __future__ import absolute_import
import math
import ctypes

def is_server_path_unicode(sp):
    try:
        return sp[:sp.index(u':/')].isdigit()
    except:
        return False


def server_path_is_root_unicode(sp):
    return sp[:-2].isdigit() and sp[-2:] == u':/'


def server_path_basename_unicode(sp):
    return sp[sp.rfind(u'/') + 1:]


def server_path_dirname_unicode(sp):
    sp = sp[:sp.rfind(u'/')]
    if sp[-1] == u':' and sp[:-1].isdigit():
        return sp + u'/'
    return sp


def server_path_ns_rel_unicode(sp):
    ns, rel = sp.split(u':', 1)
    return (long(ns), rel)


def server_path_ns_unicode(sp):
    return long(sp.split(u':', 1)[0])


def server_path_rel_unicode(sp):
    return sp.split(u':', 1)[1]


def server_path_join_unicode(a, *p):
    assert type(a) is unicode
    path = a
    for b in p:
        assert type(b) is unicode
        if b.startswith('/'):
            path = b
        elif path == '' or path.endswith('/'):
            path += b
        else:
            path += '/' + b

    return path


def is_server_path(sp):
    return type(sp) is ServerPath


def server_path_is_root(sp):
    return sp.is_root


def server_path_basename(sp):
    return sp.basename


def server_path_dirname(sp):
    return sp.dirname


def server_path_ns_rel(sp):
    return sp.ns_rel()


def server_path_ns(sp):
    return sp.ns


def server_path_rel(sp):
    return sp.rel


def server_path_join(sp, *children):
    return sp.join(*children)


def server_path_is_parent_of(sp, child):
    return sp.is_parent_of(child)


try:
    from fastpath import ServerPath
except ImportError:
    from dropbox.pypath import ServerPath

NsRelativePathMemory = ServerPath.from_ns_rel

class NsRelativePathFast(object):
    __slots__ = ('ns', 'rel')

    def __init__(self, ns, rel):
        self.ns = ns
        if not rel.startswith(u'/'):
            raise ValueError('Bad value relative path: %r!' % (rel,))
        self.rel = rel

    def __len__(self):
        return len(self.rel) + 2 + int(math.log10(self.ns)) + 1

    @property
    def is_root(self):
        return self.rel == u'/'

    def basename(self):
        if self.rel == u'/':
            return self.rel
        else:
            return self.rel[self.rel.rindex(u'/'):]

    def lower(self):
        return NsRelativePathFast(self.ns, self.rel.lower())

    def __unicode__(self):
        return u'%d:%s' % (self.ns, self.rel)

    def __repr__(self):
        return u'NsRelativePathFast(%r)' % (unicode(self),)

    def __hash__(self):
        if not self.is_root:
            hashes = map(hash, self.rel.split(u'/'))
            hashes[0] = hash('%d:/' % (self.ns,))
        else:
            hashes = [hash('%d:/' % (self.ns,))]
        toret = 0
        for i in hashes:
            toret = ctypes.c_long(1000003 * toret).value ^ i
            toret = -2 if toret == -1 else toret

        return toret

    def __cmp__(self, other):
        try:
            ret = cmp(self.ns, other.ns)
            if ret:
                return ret
            return cmp(self.rel, other.rel)
        except AttributeError:
            return object.__cmp__(self, other)


NsRelativePath = NsRelativePathMemory

def get_parent_paths(server_path):
    parents = []
    server_path = server_path.dirname
    while not server_path.is_root:
        parents.append(server_path)
        server_path = server_path.dirname

    return parents
