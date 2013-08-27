#Embedded file name: dropbox/directoryevent.py
from __future__ import absolute_import

class DirectoryEvent(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ['path', 'type']
    TYPE_UNKNOWN = 0
    TYPE_ATTR_ONLY = 1
    TYPE_DROPPED_EVENTS = 2
    TYPE_WATCH_REMOVED = 3
    TYPE_WATCH_ERROR = 4
    TYPE_CREATE = 5
    TYPE_DELETE = 6
    TYPE_RENAME_TO = 7
    TYPE_RENAME_FROM = 8

    def __init__(self, path, t = TYPE_UNKNOWN):
        self.path = path
        self.type = t

    TYPE_TO_STR = {TYPE_UNKNOWN: 'unknown',
     TYPE_ATTR_ONLY: 'attr_only',
     TYPE_DROPPED_EVENTS: 'dropped_events',
     TYPE_WATCH_REMOVED: 'watch_removed',
     TYPE_WATCH_ERROR: 'watch_error',
     TYPE_CREATE: 'create',
     TYPE_DELETE: 'delete',
     TYPE_RENAME_TO: 'rename_to',
     TYPE_RENAME_FROM: 'rename_from'}

    def __repr__(self):
        return 'DirectoryEvent(%r, %s)' % (self.path, self.TYPE_TO_STR[self.type])

    def __eq__(self, other):
        return self.path == other.path and self.type == other.type

    def __ne__(self, other):
        return self.path != other.path or self.type != other.type
