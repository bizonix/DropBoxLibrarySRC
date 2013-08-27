#Embedded file name: dropbox/sync_engine_file_system/local_path.py
import itertools
from dropbox.low_functions import compose
from dropbox.nfcdetector import is_nfc
from dropbox.trace import assert_, DEVELOPER_WARNING
from .exceptions import BadPathComponentError, InvalidPathError

class AbstractLocalPath(object):
    __slots__ = ('p',)

    def __init__(self):
        raise NotImplementedError()

    def __getstate__(self):
        return self.p

    def __setstate__(self, p):
        self.p = p

    @classmethod
    def _from_path_string(cls, path):
        if not isinstance(path, unicode):
            raise ValueError('Path must be unicode: %r' % (path,))
        self = cls.__new__(cls)
        self.p = path
        return self

    @classmethod
    def _join_validate(cls, comp):
        return None

    def add_dropbox_ns_relative_path(self, ns_relative_path):
        if not is_nfc(ns_relative_path):
            raise Exception('Dropbox paths must be in NFC! %r' % (ns_relative_path,))
        return self.join_nfc_components(*ns_relative_path.split('/')[1:])

    def to_dropbox_ns_relative(self, parent_local_path):
        if not parent_local_path.lower().is_parent_of(self.lower()):
            raise Exception('Does not make sense to convert to dropbox ns relative ' + 'if `parent_local_path` is not a prefix directory')
        to_remove = int(unicode(parent_local_path).endswith(self.SEPARATOR))
        assert_(lambda : bool(to_remove) == bool(parent_local_path.is_root), 'to_remove should only be set if the parent_local_path is a root: %r', parent_local_path)
        return unicode(self)[len(parent_local_path) - to_remove:].replace(self.SEPARATOR, u'/')

    def append(self, ext):
        other = self.__class__.__new__(self.__class__)
        other.p = u'%s%s' % (self.p, unicode(ext))
        return other

    @property
    def is_root(self):
        raise NotImplementedError()

    @property
    def dirname(self):
        raise NotImplementedError()

    @property
    def basename(self):
        if self.is_root:
            return u''
        else:
            return self.p.rsplit(self.SEPARATOR, 1)[1]

    def join(self, *children):
        if children:

            def check_child(c):
                if self.SEPARATOR in c:
                    raise BadPathComponentError('cannot have separator in a path component: %r' % (c,))
                if not c:
                    raise BadPathComponentError('cannot have an empty child! %r' % (children,))
                if not isinstance(c, unicode):
                    raise BadPathComponentError('components must be unicode')
                res = self._join_validate(c)
                if res:
                    raise BadPathComponentError('%s: %r' % (res, c))
                return c

            p = u'%s%s%s' % (self.p, u'' if self.p == self.SEPARATOR else self.SEPARATOR, self.SEPARATOR.join(itertools.imap(compose(check_child, unicode), children)))
        else:
            p = self.p
        return self._from_path_string(p)

    def split(self):
        return self.p.split(self.SEPARATOR)

    join_nfc_components = join

    def lower(self):
        return self._from_path_string(self.p.lower())

    def upper(self):
        return self._from_path_string(self.p.upper())

    def is_parent_of(self, child):
        if self.is_root:
            return not child.is_root
        else:
            return child.p.startswith(self.p + self.SEPARATOR)

    def startswith(self, parent):
        return parent.is_parent_of(self) or parent == self

    def __unicode__(self):
        return self.p

    def __repr__(self):
        return 'OSPath(%r)' % self.p

    def __len__(self):
        return len(self.p)

    def __hash__(self):
        return hash(self.p)

    def __eq__(self, other):
        try:
            return self.p == other.p
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __conform__(self, protocol):
        return unicode(self)


class AbstractPosixPath(AbstractLocalPath):

    @classmethod
    def _join_validate(cls, comp):
        if comp in (u'.', u'..'):
            return "Cannot use '.' or '..' as path components"

    @classmethod
    def root_path(cls):
        return cls._from_path_string(cls.SEPARATOR)

    @classmethod
    def from_path_string(cls, path):
        if not path.startswith(cls.SEPARATOR):
            raise InvalidPathError('Path %r does not start with %r' % (path, cls.SEPARATOR))
        if path == cls.SEPARATOR:
            return cls.root_path()
        if path.endswith(cls.SEPARATOR):
            DEVELOPER_WARNING('Path %r ends in separator, correcting automatically but you should really try to avoid this.', path)
            path = path[:-len(cls.SEPARATOR)]
        return cls.root_path().join(*path.split(cls.SEPARATOR)[1:])

    @property
    def dirname(self):
        if self.is_root:
            return self
        parent, child = unicode(self).rsplit(self.SEPARATOR, 1)
        return self._from_path_string(parent if parent else self.SEPARATOR)

    @property
    def is_root(self):
        return unicode(self) == self.SEPARATOR
