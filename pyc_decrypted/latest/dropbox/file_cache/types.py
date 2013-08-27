#Embedded file name: dropbox/file_cache/types.py
import json
from dropbox.attrs import Attributes
from dropbox.functions import handle_exceptions_ex

class ExtraPendingDetailsVersion1(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('mount_request', 'parent_blocklist', 'parent_attrs')

    def __init__(self, parent_blocklist = None, parent_attrs = None, mount_request = None):
        self.mount_request = mount_request
        self.parent_blocklist = parent_blocklist
        self.parent_attrs = parent_attrs

    def copy(self, **kw):
        return ExtraPendingDetails(parent_blocklist=kw.get('parent_blocklist', self.parent_blocklist), parent_attrs=kw.get('parent_attrs', self.parent_attrs), mount_request=kw.get('mount_request', self.mount_request))

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    @classmethod
    def unmarshal(cls, buf):
        d = json.loads(buf)
        pb = d.get('parent_blocklist')
        return ExtraPendingDetailsVersion1(parent_blocklist=pb if pb is None else str(pb), parent_attrs=None if d.get('parent_attrs') is None else Attributes.unmarshal(d['parent_attrs']), mount_request=d.get('mount_request'))

    def marshal(self):
        real_parent_attrs = None if self.parent_attrs is None else self.parent_attrs.marshal()
        return json.dumps({'parent_blocklist': self.parent_blocklist,
         'parent_attrs': real_parent_attrs,
         'mount_request': self.mount_request})

    @handle_exceptions_ex(should_raise=True)
    def __conform__(self, protocol):
        return self.marshal()

    def __repr__(self):
        return 'ExtraPendingDetails(%r, %r, %r)' % (self.parent_blocklist, self.parent_attrs, self.mount_request)


class ExtraPendingDetails(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('mount_request', 'parent', 'recommit')

    def __init__(self, parent = None, mount_request = None, recommit = None):
        self.mount_request = mount_request
        self.parent = parent
        self.recommit = recommit

    def copy(self, **kw):
        return ExtraPendingDetails(parent=kw.get('parent', self.parent), mount_request=kw.get('mount_request', self.mount_request), recommit=kw.get('recommit', self.recommit))

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    @classmethod
    def unmarshal(cls, buf):
        d = json.loads(buf)
        parent = d.get('parent')
        if parent:
            parent['attrs'] = Attributes.unmarshal(parent['attrs'])
            parent['blocklist'] = str(parent['blocklist'])
        mount_request = d.get('mount_request')
        recommit = d.get('recommit')
        return ExtraPendingDetails(parent=parent, mount_request=mount_request, recommit=recommit)

    @handle_exceptions_ex(should_raise=True)
    def __conform__(self, protocol):
        return self.marshal()

    def marshal(self):
        result = {}
        if self.parent is not None:
            parent = dict(self.parent)
            parent['attrs'] = parent['attrs'].marshal()
            result['parent'] = parent
        mount_request = self.mount_request
        if mount_request is not None:
            result['mount_request'] = mount_request
        recommit = self.recommit
        if recommit is not None:
            result['recommit'] = recommit
        return json.dumps(result)

    def __repr__(self):
        return 'ExtraPendingDetails(%r, %r%s)' % (self.parent, self.mount_request, ' recommit' if self.recommit else '')
