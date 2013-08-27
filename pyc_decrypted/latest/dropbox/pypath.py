#Embedded file name: dropbox/pypath.py
from __future__ import absolute_import
import threading
import itertools
import ctypes
from weakref import WeakKeyDictionary, ref

class ServerPath(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('__dirname', 'basename', '__hash', '__weakref__', 'ns', '__len', '__lowered')
    _map_lock = threading.Lock()
    _map = WeakKeyDictionary()

    @classmethod
    def __low_new(cls, dirname, basename, ns, lowered):
        if basename in (u'.', u'..') or u'/' in basename:
            raise ValueError('Invalid basename: %r' % (basename,))
        self = object.__new__(cls)
        self.__dirname = dirname
        self.__lowered = lowered
        self.basename = basename
        self.ns = ns
        if not dirname:
            _s = u'%d:/' % (ns,)
            self.__hash = hash(_s)
            self.__len = len(_s)
        else:
            self.__hash = ctypes.c_long(1000003 * self.__dirname.__hash).value ^ hash(self.basename)
            self.__hash = -2 if self.__hash == -1 else self.__hash
            self.__len = dirname.__len + len(self.basename) + (1 if dirname.__dirname else 0)
        with cls._map_lock:
            try:
                already_exists = cls._map[self]
            except KeyError:
                cls._map[self] = ref(self)
                return self

            return already_exists()

    @classmethod
    def __from_ns_pieces(cls, ns, pieces, lower_elt):
        old_dir = cls.__low_new(None, '', ns, lower_elt)
        if pieces[1] or len(pieces) != 2:
            for i in xrange(1, len(pieces)):
                old_dir = cls.__low_new(old_dir, pieces[i], ns, lower_elt)

        return old_dir

    def __new__(cls, possible_dirname, *children, **kw):
        lower_elt = -1 if kw.get('lowered') else None
        if type(possible_dirname) is unicode:
            pieces = possible_dirname.split(u'/')
            if pieces[0][-1] != u':':
                raise ValueError('Bad Path: %r' % (possible_dirname,))
            old_dir = cls.__from_ns_pieces(long(pieces[0][:-1]), pieces, lower_elt)
            ns = old_dir.ns
        elif type(possible_dirname) is ServerPath:
            old_dir = possible_dirname
            ns = old_dir.ns
        else:
            try:
                ns = possible_dirname.ns
                pieces = possible_dirname.rel.split(u'/')
            except:
                try:
                    ns = possible_dirname[0]
                    assert len(possible_dirname) == 2
                    pieces = possible_dirname[1].split(u'/')
                except:
                    pieces = unicode(possible_dirname).split(u'/')
                    ns = long(pieces[0][:-1])
                    if pieces[0][-1] != u':':
                        raise ValueError('Bad path: %r' % (possible_dirname,))

            old_dir = cls.__from_ns_pieces(ns, pieces, lower_elt)
        for child in children:
            old_dir = cls.__low_new(old_dir, unicode(child), ns, lower_elt)

        return old_dir

    @classmethod
    def from_ns_rel(cls, ns, rel, lowered = False):
        if not rel.startswith(u'/'):
            raise ValueError('Bad rel: %r' % (rel,))
        return cls.__from_ns_pieces(ns, rel.split(u'/'), -1 if lowered else None)

    def is_parent_of(self, child):
        curobj = child
        while True:
            if self.__len >= curobj.__len:
                break
            curobj = curobj.__dirname
            if not curobj:
                break
            elif curobj is self:
                return True

    def join(self, *children, **kw):
        lower_elt = -1 if kw.get('lowered') else None
        old_dir = self
        ns = self.ns
        for child in children:
            old_dir = self.__low_new(old_dir, unicode(child), ns, lower_elt)

        return old_dir

    def __unicode__(self):
        if not self.__dirname:
            return u'%d:/' % (self.ns,)
        tojoin = [self.basename]
        curobj = self.__dirname
        while curobj:
            if not curobj.__dirname:
                tojoin.append(u'%d:/' % (self.ns,))
                break
            else:
                tojoin.append(u'/')
                tojoin.append(curobj.basename)
            curobj = curobj.__dirname

        tojoin.reverse()
        return ''.join(tojoin)

    def lower(self):
        if not self.__dirname or self.__lowered is -1:
            return self
        elif self.__lowered:
            return self.__lowered
        else:
            plowered = ServerPath(self.__dirname.lower(), self.basename.lower(), lowered=True)
            if plowered is self:
                self.__lowered = -1
                return self
            self.__lowered = plowered
            return plowered

    def __repr__(self):
        return 'ServerPath(%r)' % (unicode(self),)

    def __hash__(self):
        return self.__hash

    def __len__(self):
        return self.__len

    def __nonzero__(self):
        return True

    @property
    def is_root(self):
        return not self.__dirname

    @property
    def dirname(self):
        blh = self.__dirname
        if blh:
            return blh
        return self

    def ns_rel(self):
        if not self.__dirname:
            return (self.ns, u'/')
        return (self.ns, self.rel)

    @property
    def rel(self):
        if not self.__dirname:
            return u'/'
        tojoin = []
        curobj = self
        while True:
            p = curobj.__dirname
            if not p:
                break
            else:
                tojoin.append(curobj.basename)
                tojoin.append(u'/')
                curobj = p

        tojoin.reverse()
        return u''.join(tojoin)

    def __eq__(self, other):
        if self is other:
            return True
        if type(other) is not ServerPath:
            try:
                return self.ns == other.ns and self.rel == other.rel
            except AttributeError:
                return NotImplemented

        else:
            if self.ns != other.ns:
                return False
            if self.__len != other.__len:
                return False
            cur1 = self
            cur2 = other
            while True:
                if not cur1.__dirname:
                    return not cur2.__dirname
                if not cur2.__dirname:
                    return False
                if len(cur1.basename) != len(cur2.basename) or cur1.basename != cur2.basename:
                    return False
                cur1 = cur1.__dirname
                cur2 = cur2.__dirname

            assert False, 'not reached'

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if self is other:
            return 0
        if type(other) is not ServerPath:
            try:
                ret = cmp(self.ns, other.ns)
                if ret:
                    return ret
                return cmp(self.rel, other.rel)
            except AttributeError:
                return object.__cmp__(self, other)

        ret = cmp(self.ns, other.ns)
        if ret:
            return ret
        a_go_back = -1
        b_go_back = -1
        cur1 = self
        cur2 = other
        while True:
            if cur1 is not None:
                cur1 = cur1.__dirname
                a_go_back += 1
                if cur2 is not None:
                    cur2 = cur2.__dirname
                    b_go_back += 1
            elif cur2 is not None:
                cur2 = cur2.__dirname
                b_go_back += 1
            else:
                break

        while True:
            cur1 = self
            for j in xrange(0, a_go_back):
                cur1 = cur1.__dirname

            cur2 = other
            for j in xrange(0, b_go_back):
                cur2 = cur2.__dirname

            ret = cmp(cur1.basename, cur2.basename)
            if ret:
                return ret
            if not (a_go_back and b_go_back):
                break
            a_go_back -= 1
            b_go_back -= 1

        return cmp(a_go_back, b_go_back)
