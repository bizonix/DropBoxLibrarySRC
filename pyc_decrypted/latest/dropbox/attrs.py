#Embedded file name: dropbox/attrs.py
from __future__ import absolute_import
import base64
import itertools
import json
import os
import threading
import zlib
from cStringIO import StringIO
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, dropbox_hash
from dropbox.metadata.utils import split_metadata_key
from dropbox.functions import frozendict
from dropbox.low_functions import safe_navigate
from dropbox.trace import unhandled_exc_handler
BLOCKABLE_INLINE_CUT_OFF = 0
BLOCKABLE_DEFAULT = BLOCKABLE_BLOCKLIST_IF_TOO_LARGE = 1
BLOCKABLE_BLOCKLIST_ALWAYS = 2
FILE_TAG_PLAT = u'dropbox_tag'
FILE_TAG_GID_V3_ATTR = u'file_tag_gid_v3'

class CorruptedAttributeError(Exception):
    pass


class AllowAllWhitelist(object):

    def __getitem__(self, key):
        return AllowAllWhitelist()

    def __contains__(self, key):
        return True


def get_attrs_blocklist(attr):
    l = []
    for plat, plat_attrs in attr.attr_dict.iteritems():
        for k, v in plat_attrs.iteritems():
            try:
                bl = v['blocklist']
            except KeyError:
                pass
            else:
                if bl:
                    l.extend(str(bl).split(','))

    return l


def is_attrs_subset(attrs_a, attrs_b):
    for plat_key, plat_dict in attrs_a.attr_dict.iteritems():
        try:
            attrs_b_plat_dict = attrs_b.attr_dict[plat_key]
        except KeyError:
            return False

        for attr_key, attr_value in plat_dict.iteritems():
            try:
                attrs_b_attr_value = attrs_b_plat_dict[attr_key]
            except KeyError:
                return False

            if attrs_b_attr_value != attr_value:
                return False

    return True


def unserialize_attr_dict(buf):
    if buf:
        return json.loads(zlib.decompress(buf))
    else:
        return {}


def serialize_attr_dict(attr, data_plats, only = ()):
    if data_plats is None:
        sp = frozenset(only)
    else:
        sp = attr.get_serialized_platforms(data_plats, give_set=True)
    return serialize_attr_dict_only(attr.attr_dict, sp)


def serialize_attr_dict_only(attr_dict, only):
    buf = dict(attr_dict)
    for plat_key in attr_dict.iterkeys():
        if plat_key not in only:
            del buf[plat_key]

    if buf:
        return zlib.compress(json.dumps(buf))


def attr_dict_filter_whitelist(attrs_dict, whitelist):
    if not whitelist:
        return attrs_dict
    return dict(((plat, dict(((k, v) for k, v in plat_attrs.iteritems() if k in whitelist[plat]))) for plat, plat_attrs in attrs_dict.iteritems() if plat in whitelist))


def convert_attr_data(raw_attr_fh, max_inline_attr_size = None, block_handler = None, blockable = BLOCKABLE_DEFAULT):
    raw_attr_fh.seek(0, os.SEEK_END)
    attr_length = raw_attr_fh.tell()
    raw_attr_fh.seek(0, os.SEEK_SET)
    if blockable == BLOCKABLE_BLOCKLIST_ALWAYS or blockable == BLOCKABLE_BLOCKLIST_IF_TOO_LARGE and max_inline_attr_size is not None and attr_length > max_inline_attr_size:
        blocklist = []
        real_length = 0
        while True:
            block = raw_attr_fh.read(DROPBOX_MAX_BLOCK_SIZE)
            if not block:
                break
            real_length += len(block)
            sha1_digest = dropbox_hash(block)
            blocklist.append(sha1_digest)
            if block_handler:
                block_handler(sha1_digest, block)

        if real_length != attr_length:
            raise Exception('Attr length changed while reading!')
        return dict(blocklist=','.join(blocklist), size=real_length)
    else:
        if max_inline_attr_size is None:
            attr_data = raw_attr_fh.read()
        else:
            attr_data = raw_attr_fh.read(max_inline_attr_size)
        return dict(data=base64.b64encode(attr_data))


def dropboxize_raw_attrs_dict(attrs_dict, whitelist = None, max_inline_attr_size = 4096, block_handler = None):
    new_dict = {}
    for plat, plat_attrs in attrs_dict.iteritems():
        new_plat_dict = {}
        if whitelist is not None:
            try:
                platform_whitelist = whitelist[plat]
            except KeyError:
                continue

            if not platform_whitelist:
                continue
        else:
            platform_whitelist = None
        for k, attr_data in plat_attrs.iteritems():
            base_key = split_metadata_key(k)
            if platform_whitelist is not None and base_key not in platform_whitelist:
                continue
            blockable = (platform_whitelist or {}).get(base_key, {}).get('blockable', BLOCKABLE_DEFAULT)
            new_plat_dict[k] = convert_attr_data(StringIO(attr_data), max_inline_attr_size=max_inline_attr_size, block_handler=block_handler, blockable=blockable)

        new_dict[plat] = new_plat_dict

    return new_dict


def attr_dict_from_whitelist(attr_handle, _platform, whitelist = None, max_inline_attr_size = 4096, block_handler = None):
    return dropboxize_raw_attrs_dict({_platform: attr_handle}, whitelist=whitelist, max_inline_attr_size=max_inline_attr_size, block_handler=block_handler).get(_platform, frozendict())


def get_attr_data(attr_data, get_contents = lambda : None):
    try:
        return base64.b64decode(attr_data['data'])
    except KeyError:
        blocklist = attr_data['blocklist']
        if not blocklist and not attr_data['size']:
            return ''
        else:
            return ''.join([ get_contents(x) for x in blocklist.split(',') ])


def convert_attr_dict(dict_constructor, attr_dict):
    return dict_constructor(((plat, dict_constructor(((key, dict_constructor(val)) for key, val in plat_attrs.iteritems())) if plat_attrs is not None else None) for plat, plat_attrs in attr_dict.iteritems()))


def make_frozen_attr_dict(attr_dict):
    return convert_attr_dict(frozendict, attr_dict)


def unfreeze_attr_dict(frozen_attr_dict):
    return convert_attr_dict(dict, frozen_attr_dict)


def has_file_tag_gid_v3(attrs):
    return safe_navigate(attrs.attr_dict, FILE_TAG_PLAT, FILE_TAG_GID_V3_ATTR)


def copy_file_tag_gid_v3(from_attrs, to_attrs):
    new_attr_dict = dict(to_attrs.attr_dict)
    file_tag_plat_dict = dict(new_attr_dict[FILE_TAG_PLAT])
    file_tag_plat_dict[FILE_TAG_GID_V3_ATTR] = from_attrs.attr_dict[FILE_TAG_PLAT][FILE_TAG_GID_V3_ATTR]
    new_attr_dict[FILE_TAG_PLAT] = file_tag_plat_dict
    return to_attrs.copy(attr_dict=new_attr_dict)


class Attributes(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('data_plats', 'attr_dict')
    singleton_lock = threading.Lock()
    singletons = {}

    @classmethod
    def __low_new(cls, attr_dict = frozendict(), data_plats = frozenset()):
        toret = object.__new__(cls)
        object.__setattr__(toret, 'attr_dict', make_frozen_attr_dict(attr_dict))
        object.__setattr__(toret, 'data_plats', frozenset(data_plats))
        return toret

    @classmethod
    def __singleton(cls, key, attr_dict, data_plats):
        if Attributes.singletons.get(key) is None:
            with Attributes.singleton_lock:
                if Attributes.singletons.get(key) is None:
                    Attributes.singletons[key] = toret = cls.__low_new(attr_dict=attr_dict, data_plats=data_plats)
                else:
                    toret = Attributes.singletons[key]
        else:
            toret = Attributes.singletons[key]
        return toret

    def __new__(cls, attr_dict = frozendict(), data_plats = frozenset()):
        if not attr_dict and not data_plats:
            return cls.__singleton(cls, attr_dict, data_plats)
        if not attr_dict:
            data_plats = frozenset(data_plats)
            return cls.__singleton(data_plats, attr_dict, data_plats)
        return cls.__low_new(attr_dict=attr_dict, data_plats=data_plats)

    def __setattr__(self, k, v):
        raise Exception('Not Supported')

    def __repr__(self):
        return 'Attributes(%r,%r)' % (self.attr_dict, self.data_plats)

    def __eq__(self, other):
        return self is other or isinstance(other, Attributes) and self.attr_dict == other.attr_dict

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.attr_dict)

    def copy(self, **kw):
        return Attributes(attr_dict=kw.get('attr_dict', self.attr_dict), data_plats=kw.get('data_plats', self.data_plats))

    def marshal(self):
        if self.data_plats:
            d = dict(self.attr_dict)
            sk = d.keys()
            sk.sort()
            dpi = []
            dpl = []
            for dp in self.data_plats:
                if dp in self.attr_dict:
                    dpi.append(sk.index(dp))
                else:
                    dpl.append(dp)

            if dpi:
                d['__dpi'] = dpi
            if dpl:
                d['__dpl'] = dpl
        else:
            d = self.attr_dict
        return json.dumps(d)

    def __nonzero__(self):
        return bool(self.attr_dict)

    def __conform__(self, protocol):
        try:
            return self.marshal()
        except:
            unhandled_exc_handler()
            raise

    @staticmethod
    def unmarshal(buf):
        if not buf:
            raise Exception("Couldn't unmarshal empty buffer")
        if buf == '{}':
            return Attributes()
        try:
            d = json.loads(buf)
        except ValueError as ex:
            raise CorruptedAttributeError(ex.message)

        try:
            dpi = d.pop('__dpi')
        except KeyError:
            dpi = ()

        try:
            dpl = d.pop('__dpl')
        except KeyError:
            dpl = ()

        for k in [ k for k in d.iterkeys() if k == 'unwritten' or k.startswith('__') ]:
            del d[k]

        sk = d.keys()
        sk.sort()
        return Attributes(d, data_plats=frozenset(itertools.chain((sk[i] for i in dpi), dpl)))

    def get_serialized_platforms(self, platforms, give_set = False):
        apfdp = platforms
        if give_set:
            return set((plat for plat in self.attr_dict.iterkeys() if plat not in apfdp))
        else:
            return [ plat for plat in self.attr_dict.iterkeys() if plat not in apfdp ]

    def has_blockrefs(self):
        return bool(self.get_blockrefs())

    def get_blockrefs(self):
        if not self.data_plats:
            return ()
        platforms = self.attr_dict.keys()
        platforms.sort()
        valid_platforms = self.data_plats
        ret = []
        for plat_num, plat in enumerate(platforms):
            if plat not in valid_platforms:
                continue
            keys = self.attr_dict[plat].keys()
            keys.sort()
            for key_num, key in enumerate(keys):
                try:
                    bs = str(self.attr_dict[plat][key]['blocklist']).split(',')
                    for i, k in enumerate(bs):
                        ret.append((k, plat_num << 32 | key_num << 24 | i))

                except KeyError:
                    pass

        return ret

    def get_location(self, ref):
        plat_num = ref >> 32 & 255
        key_num = ref >> 24 & 255
        i = ref & 16777215
        platforms = self.attr_dict.keys()
        platforms.sort()
        plat = platforms[plat_num]
        keys = self.attr_dict[plat].keys()
        keys.sort()
        key = keys[key_num]
        return (plat, key, i)


FrozenAttributes = Attributes
