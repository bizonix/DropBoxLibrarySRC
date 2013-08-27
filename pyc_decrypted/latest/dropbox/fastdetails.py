#Embedded file name: dropbox/fastdetails.py
from __future__ import absolute_import
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY

class FastDetails(object):
    __use_advanced_allocator__ = 1048576
    __attrs__ = ('server_path', 'blocklist', 'parent_blocklist', 'attrs', 'parent_attrs', 'size', 'mtime', 'sjid', 'dir', 'ctime', 'ts', 'mount_request', 'machine_guid', 'guid', 'guid_rev')
    __slots__ = __attrs__ + ('__internal_dict',)

    def __init__(self, *args, **kw):
        self.__internal_setattr('_FastDetails__internal_dict', None)
        for k, v in kw.iteritems():
            if k == '__internal_dict':
                continue
            self.__internal_setattr(k, v)

    def __iter__(self, include_none = True):
        for k in FastDetails.__attrs__:
            try:
                val = getattr(self, k)
            except AttributeError:
                continue
            else:
                if include_none or val is not None:
                    yield (k, val)

        if self.__internal_dict is not None:
            for item in self.__internal_dict.iteritems():
                if include_none or item[1] is not None:
                    yield item

    EMPTY_DICT = {}

    def __eq__(self, other):
        for k in FastDetails.__attrs__:
            if getattr(self, k, None) != getattr(other, k, None):
                return False

        d1 = self.__internal_dict or self.EMPTY_DICT
        d2 = other.__internal_dict or self.EMPTY_DICT

        def len_wo_none(d):
            return sum((1 for v in d.itervalues() if v is not None))

        if len_wo_none(d1) != len_wo_none(d2):
            return False
        for k, v in d1.iteritems():
            if d2.get(k) != v:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self.__iter__(include_none=False)))

    def copy(self, exclude = (), **kw):
        new_kw = {}
        for k in FastDetails.__attrs__:
            if k in exclude:
                continue
            try:
                a = getattr(self, k)
            except AttributeError:
                pass
            else:
                new_kw[k] = a

        if self.__internal_dict:
            new_kw.update(((k, v) for k, v in self.__internal_dict.iteritems() if k not in exclude))
        new_kw.update(kw)
        return FastDetails(**new_kw)

    def __setattr__(self, k, v):
        raise TypeError('%r object does not support setting attributes' % (type(self).__name__,))

    def __internal_setattr(self, k, v):
        if k == 'host_id':
            k = 'ctime'
        try:
            return object.__setattr__(self, k, v)
        except AttributeError:
            d = self.__internal_dict
            if d is None:
                d = {}
                object.__setattr__(self, '_FastDetails__internal_dict', d)
            d[k] = v

    def __getattribute__(self, k):
        if k == 'host_id':
            k = 'ctime'
        return object.__getattribute__(self, k)

    def __getattr__(self, k):
        try:
            return self.__internal_dict[k]
        except (KeyError, TypeError):
            raise AttributeError('%r object has no attribute %r' % (type(self).__name__, k))

    def __repr__(self):
        return 'FastDetails(%s)' % ', '.join(('%s=%r' % t for t in self))
