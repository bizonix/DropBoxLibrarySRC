#Embedded file name: dropbox/ideal_tracker/util.py
from __future__ import absolute_import
from Crypto.Random import get_random_bytes
from dropbox.monotonic_time import get_monotonic_time_seconds

class _GID(object):

    def __init__(self, data = None):
        if data is None:
            self.data = get_random_bytes(16)
        elif isinstance(data, IdealID):
            self.data = data.data
        elif len(data) == 16:
            self.data = bytes(data)
        elif len(data) == 32:
            self.data = data.decode('hex')
        else:
            raise Exception('Unknown IdealID format: %r' % data)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.data.encode('hex'))

    def __eq__(self, other):
        return self.data == other.data

    def __ne__(self, other):
        return self.data != other.data

    def __hash__(self):
        return hash(repr(self))


class IdealID(_GID):
    pass


class LinkID(_GID):
    pass


ROOT_IDEAL_ID = IdealID('00000000000000000000000000000000')

class Ideal(object):

    def __init__(self, ideal_id = None, is_dir = None, identifier = None, last_update = None):
        self.id = IdealID(ideal_id)
        assert is_dir is not None, 'Ideal requires is_dir'
        self.is_dir = is_dir
        self.identifier = identifier
        if last_update is None:
            self.last_update = get_monotonic_time_seconds()
        else:
            self.last_update = last_update

    def __repr__(self):
        return 'Ideal(%r, %r, %r, %r)' % (self.id,
         self.is_dir,
         self.identifier,
         self.last_update)


ROOT_IDEAL = Ideal(ROOT_IDEAL_ID, is_dir=1)

class IdealLink(object):

    def __init__(self, link_id = None, parent_ideal_id_data = None, child_name = None, child_ideal_id_data = None, unlink_time = None):
        self.id = LinkID(link_id)
        self.parent_ideal_id = IdealID(parent_ideal_id_data)
        self.child_name = child_name
        self.child_ideal_id = IdealID(child_ideal_id_data)
        self.unlink_time = unlink_time

    def __repr__(self):
        return 'IdealLink(id=%r, parent=%r, name=%r, child=%r, unlink_time=%r)' % (self.id,
         self.parent_ideal_id,
         self.child_name,
         self.child_ideal_id,
         self.unlink_time)


def to_text(id_data):
    if isinstance(id_data, _GID):
        id_data = id_data.data
    return id_data.encode('hex')
