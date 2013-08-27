#Embedded file name: dropbox/file_cache/util.py
from __future__ import absolute_import
import base64
import hashlib
import json
import struct
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, dropbox_hash
from dropbox.attrs import Attributes
from dropbox.fastdetails import FastDetails
from dropbox.functions import handle_exceptions_ex, is_four_byte_unicode
from dropbox.low_functions import add_inner_methods, add_inner_properties
from dropbox.nfcdetector import is_nfc
from dropbox.server_path import ServerPath, server_path_basename_unicode, server_path_dirname_unicode, server_path_is_root_unicode, server_path_join_unicode, server_path_ns_rel_unicode
from dropbox.trace import report_bad_assumption
from . import constants as c

@handle_exceptions_ex(should_raise=True)
def sqlite_to_fastdetails(sqlite_type):
    kw = json.loads(sqlite_type)
    attrs = kw.get('attrs')
    if attrs is not None:
        kw['attrs'] = Attributes.unmarshal(attrs)
    parent_attrs = kw.get('parent_attrs')
    if parent_attrs is not None:
        kw['parent_attrs'] = Attributes.unmarshal(parent_attrs)
    mr = kw.get('mount_request')
    if mr is not None:
        if type(mr) is list:
            kw['mount_request'] = tuple(mr)
    bl = kw.get('blocklist')
    if bl is not None:
        kw['blocklist'] = str(bl)
    kw['server_path'] = ServerPath(kw['server_path'])
    return FastDetails(**kw)


@handle_exceptions_ex(should_raise=True)
def fastdetails_to_sqlite(details):
    kw = dict(details)
    attrs = kw.get('attrs')
    if attrs is not None:
        kw['attrs'] = attrs.marshal()
    parent_attrs = kw.get('parent_attrs')
    if parent_attrs is not None:
        kw['parent_attrs'] = parent_attrs.marshal()
    kw['server_path'] = unicode(kw['server_path'])
    bl = kw.get('blocklist')
    if bl is not None and type(bl) is not str:
        raise Exception('Blocklist must be a string: %r' % bl)
    return json.dumps(kw)


@handle_exceptions_ex(should_raise=True)
def sqlite_to_serverpath(sqlite_type):
    return ServerPath(sqlite_type.decode('utf-8'))


@handle_exceptions_ex(should_raise=True)
def serverpath_to_sqlite(sp):
    return unicode(sp)


def sixty_four_bit_hash_string(the_str):
    return struct.unpack('<Q', hashlib.md5(the_str).digest()[:8])[0]


def hash_attr_dict(attr_dict):
    current_hash = 0
    for plat, plat_xattrs in attr_dict.iteritems():
        for key, value in plat_xattrs.iteritems():
            try:
                data_str = base64.b64decode(str(value['data']))
            except KeyError:
                size = value['size']
                blocklist = value['blocklist']
            else:
                size = len(data_str)
                blocklist = ','.join([ dropbox_hash(data_str[i:i + DROPBOX_MAX_BLOCK_SIZE]) for i in xrange(0, size, DROPBOX_MAX_BLOCK_SIZE) ])

            current_hash ^= sixty_four_bit_hash_string('%s%s%s%s' % (str(plat),
             str(key),
             size,
             str(blocklist)))

    return current_hash


def server_hash(ns, rel, blocklist, size, attr_dict, sjid, is_dir, target_ns):
    the_str = '%s%s%s%s%s%s%s%s' % (ns,
     rel.encode('utf8'),
     str(blocklist),
     size,
     hash_attr_dict(attr_dict),
     sjid,
     is_dir,
     target_ns)
    return sixty_four_bit_hash_string(the_str)


def is_invalid_path_upload_code(code):
    return code == c.UPLOAD_INVALID_PATH_CODE or code.startswith('extended_')


def create_extended_upload_code(desc):
    return 'extended_%s' % desc


def why_isnt_valid_filejournal_entry(ent):
    try:
        if ent.get(c.IS_CONFLICTED_COL) and (ent[c.LOCAL_SJID_COL] is None or ent[c.LOCAL_SJID_COL] != 0):
            return "Can't be conflicted and not pending! %r %r" % (ent.get(c.IS_CONFLICTED_COL), ent[c.LOCAL_SJID_COL])
        for path_desc, path in (('server_path', ent[c.SERVER_PATH_COL]), ('parent_path', ent[c.PARENT_PATH_COL])):
            if not path:
                return 'Empty %s' % path_desc
            if path[-1] == u' ' or path.find(u' /') >= 0:
                return '%s has whitespace component' % path_desc
            if path.find(u'\\') >= 0:
                return '%s contains \\ character' % path_desc
            if not is_nfc(path):
                return '%s is not nfc' % path_desc
            if is_four_byte_unicode(path):
                return '%s is high unicode' % path_desc
            if path.lower() != path:
                return '%s is not lowered: %r' % (path_desc, path)

        if server_path_is_root_unicode(ent[c.SERVER_PATH_COL]):
            return 'Root entry in database'
        if server_path_dirname_unicode(ent[c.SERVER_PATH_COL]) != ent[c.PARENT_PATH_COL]:
            return "Parent_path doesn't match server_path: %r vs %r" % (ent[c.PARENT_PATH_COL], ent[c.SERVER_PATH_COL])
        if not server_path_basename_unicode(ent[c.SERVER_PATH_COL]):
            return 'File without a basename in server path'
        if ent[c.UPDATED_SJID_COL] is None and ent[c.LOCAL_SJID_COL] is None:
            return 'Both updated_sjid and local_sjid are NULL'
        if ent[c.UPDATED_SJID_COL] > 1 and ent[c.LOCAL_SJID_COL] > 1 and ent[c.UPDATED_SJID_COL] <= ent[c.LOCAL_SJID_COL]:
            return 'Updated sjid is less than or equal to local_sjid: %r vs %r' % (ent[c.UPDATED_SJID_COL], ent[c.LOCAL_SJID_COL])
        if ent[c.LOCAL_DIR_COL] not in (None, 0, 1):
            return 'Invalid local_dir: %r' % (ent[c.LOCAL_DIR_COL],)
        if ent[c.UPDATED_DIR_COL] not in (None, 0, 1):
            return 'Invalid updated_dir: %r' % (ent[c.UPDATED_DIR_COL],)
        if ent[c.UPDATED_SJID_COL] is not None:
            if ent[c.UPDATED_SIZE_COL] < 0 and ent[c.UPDATED_BLOCKLIST_COL]:
                return 'Deleted remote file but it had blocklists: %r' % (ent[c.UPDATED_BLOCKLIST_COL],)
            if ent[c.UPDATED_SIZE_COL] < 0 and ent[c.UPDATED_ATTRS_COL]:
                return 'Deleted remote file but it had attrs: %r' % (ent[c.UPDATED_ATTRS_COL],)
            if ent[c.UPDATED_SJID_COL] < 1:
                return 'Invalid updated_sjid: %r' % (ent[c.UPDATED_SJID_COL],)
            if not ent[c.UPDATED_FILENAME_COL]:
                return 'Empty updated_filename for updated entry: %r' % (ent[c.SERVER_PATH_COL],)
            if not is_nfc(ent[c.UPDATED_FILENAME_COL]):
                return 'Updated filename is not nfc'
            if is_four_byte_unicode(ent[c.UPDATED_FILENAME_COL]):
                return 'Updated filename is four byte unicode'
            if server_path_basename_unicode(ent[c.SERVER_PATH_COL]) != ent[c.UPDATED_FILENAME_COL].lower():
                return "Local filename doesn't match server_path: %r vs %r" % (ent[c.LOCAL_FILENAME_COL], ent[c.SERVER_PATH_COL])
            if ent[c.UPDATED_ATTRS_COL].data_plats:
                return 'Updated attrs had readable, or a data_plat: %r' % (ent[c.UPDATED_ATTRS_COL],)
            if ent[c.UPDATED_SIZE_COL] < 0 and ent[c.UPDATED_BLOCKLIST_COL]:
                return 'Deleted updated file but it had blocklists: %r' % (ent[c.UPDATED_BLOCKLIST_COL],)
            if ent[c.UPDATED_SIZE_COL] > 0 and not ent[c.UPDATED_BLOCKLIST_COL]:
                return 'Non-zero updated size but empty blocklist %r' % (ent[c.UPDATED_BLOCKLIST_COL],)
            if ent[c.UPDATED_SIZE_COL] < 0 and ent[c.UPDATED_ATTRS_COL]:
                return 'Deleted updated file but it had attrs: %r' % (ent[c.UPDATED_ATTRS_COL],)
            if ent[c.UPDATED_SIZE_COL] < 0 and ent[c.UPDATED_DIR_COL]:
                return 'Deleted updated file but is a directory'
            if not all((ns_dict for attr_ns, ns_dict in ent[c.UPDATED_ATTRS_COL].attr_dict.iteritems())):
                return 'Empty remote attr dict! %r' % (ent[c.UPDATED_ATTRS_COL].attr_dict,)
            if ent[c.SERVER_PATH_COL] != server_path_join_unicode(ent[c.PARENT_PATH_COL], ent[c.UPDATED_FILENAME_COL].lower()):
                return "Updated filename doesn't match server_path: %r vs %r" % (ent[c.UPDATED_FILENAME_COL], ent[c.SERVER_PATH_COL])
        elif any((ent[key] is not None for key in [c.UPDATED_ATTRS_COL,
         c.UPDATED_BLOCKLIST_COL,
         c.UPDATED_DIR_COL,
         c.UPDATED_FILENAME_COL,
         c.UPDATED_MTIME_COL,
         c.UPDATED_SIZE_COL,
         c.UPDATED_SJID_COL])):
            return 'updated_sjid was None yet we had other cols'
        if ent[c.LOCAL_SJID_COL] is not None:
            if not ent[c.LOCAL_FILENAME_COL]:
                return 'Empty local_filename for updated entry: %r' % (ent[c.SERVER_PATH_COL],)
            if not is_nfc(ent[c.LOCAL_FILENAME_COL]):
                return 'Local filename is not nfc'
            if is_four_byte_unicode(ent[c.LOCAL_FILENAME_COL]):
                return 'Updated filename is four byte unicode'
            if server_path_basename_unicode(ent[c.SERVER_PATH_COL]) != ent[c.LOCAL_FILENAME_COL].lower():
                return "Local filename doesn't match server_path: %r vs %r" % (ent[c.LOCAL_FILENAME_COL], ent[c.SERVER_PATH_COL])
            if not all((ns_dict for attr_ns, ns_dict in ent[c.LOCAL_ATTRS_COL].attr_dict.iteritems())):
                return 'Empty local attr dict! %r' % (ent[c.LOCAL_ATTRS_COL].attr_dict,)
            if ent[c.LOCAL_SIZE_COL] < 0 and ent[c.LOCAL_BLOCKLIST_COL]:
                return 'Deleted local file but it had blocklists: %r' % (ent[c.LOCAL_BLOCKLIST_COL],)
            if ent[c.LOCAL_SIZE_COL] > 0 and not ent[c.LOCAL_BLOCKLIST_COL]:
                return 'Non-zero local size but empty blocklist %r' % (ent[c.LOCAL_BLOCKLIST_COL],)
            if ent[c.LOCAL_SIZE_COL] < 0 and ent[c.LOCAL_ATTRS_COL]:
                return 'Deleted local file but it had attrs: %r' % (ent[c.LOCAL_ATTRS_COL],)
            if ent[c.LOCAL_SIZE_COL] < 0 and ent[c.LOCAL_DIR_COL]:
                return 'Deleted local file but is a directory'
            if ent[c.LOCAL_ATTRS_COL] is None:
                return 'local_attrs is NULL when local_sjid is not'
            if ent[c.LOCAL_BLOCKLIST_COL] is None:
                return 'local_blocklist is NULL when local_sjid is not'
            extra = ent[c.EXTRA_PENDING_DETAILS_COL]
            if ent[c.LOCAL_SJID_COL] == 0:
                if not extra:
                    return 'extra_pending_details is NULL yet local_sjid indicates a pending entry: %r' % (ent[c.LOCAL_SJID_COL],)
                p = extra['parent']
                if p:
                    if type(p['sjid']) not in (int, long) or p['sjid'] < 0:
                        return "Bad sjid in extra_pending_details['parent']: %r" % (p['sjid'],)
                    if p['attrs'] is None:
                        return 'We had a parent entry but attrs was NULL??'
                    if not all((ns_dict for attr_ns, ns_dict in p['attrs'].attr_dict.iteritems())):
                        return 'Empty parent attr dict! %r' % (p['attrs'].attr_dict,)
                    if p['blocklist'] is None:
                        return 'We had a parent entry but blocklist was NULL??'
                if extra['mount_request'] is not None and extra['mount_request'] <= 0:
                    return 'Invalid mount_request: %r' % (extra['mount_request'],)
            elif ent[c.LOCAL_SJID_COL] > 0:
                if extra:
                    return 'extra_pending_details is: %r yet local_sjid indicates an active entry: %r' % (ent[c.EXTRA_PENDING_DETAILS_COL], ent[c.LOCAL_SJID_COL])
                if ent[c.LOCAL_SIZE_COL] < 0:
                    return 'File was deleted but also active'
            else:
                return 'Negative local_sjid! %r' % (ent[c.LOCAL_SJID_COL],)
        else:
            if any((ent[key] is not None for key in [c.LOCAL_ATTRS_COL,
             c.LOCAL_BLOCKLIST_COL,
             c.LOCAL_DIR_COL,
             c.LOCAL_FILENAME_COL,
             c.LOCAL_MTIME_COL,
             c.LOCAL_SIZE_COL,
             c.LOCAL_SJID_COL])):
                return 'local_sjid was None yet we had other cols'
            if ent[c.LOCAL_CTIME_COL] is not None:
                return 'local_ctime is not None even though local_sjid is None'
            if ent[c.EXTRA_PENDING_DETAILS_COL] is not None:
                return 'extra pending details is not None even though local_sjid is None'
        ns = server_path_ns_rel_unicode(ent[c.SERVER_PATH_COL])[0]
        if ent[c.UPDATED_SJID_COL] is not None and ent[c.UPDATED_SJID_COL] != 1 and not is_valid_sjid(ns, ent[c.UPDATED_SJID_COL]):
            report_bad_assumption('Bad sjid %r from server for ns %r' % (ent[c.UPDATED_SJID_COL], ns))
        if ent[c.LOCAL_SJID_COL] is not None and ent[c.LOCAL_SJID_COL] > 1 and not is_valid_sjid(ns, ent[c.LOCAL_SJID_COL]):
            report_bad_assumption('Bad sjid %r from server for ns %r' % (ent[c.LOCAL_SJID_COL], ns))
        if not (ent.get(c.UPDATED_HOST_ID_COL) is None or ent[c.UPDATED_SJID_COL] > 1):
            return 'Had an updated host id but did not have a valid updated sjid'
        if not (ent.get(c.LOCAL_HOST_ID_COL) is None or ent[c.LOCAL_SJID_COL] > 1):
            return ('Had an local host id but did not have a valid updated sjid!',)
        if not (ent.get(c.UPDATED_TIMESTAMP_COL) is None or ent[c.UPDATED_SJID_COL] > 1):
            return 'Had an updated timestamp but did not have a valid updated sjid'
        if not (ent.get(c.LOCAL_TIMESTAMP_COL) is None or ent[c.LOCAL_SJID_COL] > 1):
            return ('Had a local timestamp but did not have a valid updated sjid!',)
        if not (ent.get(c.LOCAL_GUID_COL) is None or ent.get(c.LOCAL_MACHINE_GUID_COL) is not None):
            return 'Had a local guid but no machine guid!'
        if not (ent.get(c.UPDATED_GUID_COL) is None or ent.get(c.UPDATED_GUID_REV_COL) is not None):
            return 'Had an updated guid without a guid rev!'
        if ent.get(c.LOCAL_GUID_COL) is not None and ent[c.LOCAL_SJID_COL] is not None and ent[c.LOCAL_SJID_COL] > 1 and ent.get(c.LOCAL_GUID_SYNCED_GUID_REV_COL) is None:
            return 'Had a local guid but no guid rev'
    except (IndexError, KeyError) as e:
        return 'Database row was missing column: %s' % (e,)


def check_db_entries(entries):
    for newent in entries:
        why = why_isnt_valid_filejournal_entry(newent)
        assert not why, 'Invalid filejournal entry!: %s %r' % (why, newent)

    return True


def server_hash_for_row(row, target_ns = None):
    tohash = None
    if row[c.LOCAL_SJID_COL] is not None:
        if row[c.LOCAL_SJID_COL] == 0 and row[c.EXTRA_PENDING_DETAILS_COL]['parent']:
            tohash = row[c.EXTRA_PENDING_DETAILS_COL]['parent']
        elif row[c.LOCAL_SJID_COL] > 1:
            tohash = {'sjid': row[c.LOCAL_SJID_COL],
             'blocklist': row[c.LOCAL_BLOCKLIST_COL],
             'size': row[c.LOCAL_SIZE_COL],
             'dir': row[c.LOCAL_DIR_COL],
             'attrs': row[c.LOCAL_ATTRS_COL]}
    if row[c.UPDATED_SJID_COL] is not None and (not tohash or row[c.UPDATED_SJID_COL] > tohash['sjid']):
        tohash = {'sjid': row[c.UPDATED_SJID_COL],
         'blocklist': row[c.UPDATED_BLOCKLIST_COL],
         'size': row[c.UPDATED_SIZE_COL],
         'dir': row[c.UPDATED_DIR_COL],
         'attrs': row[c.UPDATED_ATTRS_COL]}
    if not tohash:
        return 0
    ns, rel = server_path_ns_rel_unicode(row[c.SERVER_PATH_COL])
    return server_hash(ns, rel, tohash['blocklist'], tohash['size'], tohash['attrs'].attr_dict, tohash['sjid'], tohash['dir'], target_ns or 0)


def is_valid_filejournal_entry(ent):
    return not why_isnt_valid_filejournal_entry(ent)


def local_details_from_entry(ent):
    sp = ServerPath(ServerPath(ent[c.PARENT_PATH_COL], lowered=True), ent[c.LOCAL_FILENAME_COL])
    return FastDetails(server_path=sp, mtime=ent[c.LOCAL_MTIME_COL], size=ent[c.LOCAL_SIZE_COL], dir=ent[c.LOCAL_DIR_COL], attrs=ent[c.LOCAL_ATTRS_COL], ctime=ent[c.LOCAL_CTIME_COL], blocklist=ent[c.LOCAL_BLOCKLIST_COL], sjid=ent[c.LOCAL_SJID_COL], guid=ent.get(c.LOCAL_GUID_COL), guid_rev=ent.get(c.LOCAL_GUID_SYNCED_GUID_REV_COL), machine_guid=ent.get(c.LOCAL_MACHINE_GUID_COL))


def updated_details_from_entry(row):
    return FastDetails(blocklist=row[c.UPDATED_BLOCKLIST_COL], size=row[c.UPDATED_SIZE_COL], mtime=row[c.UPDATED_MTIME_COL], dir=row[c.UPDATED_DIR_COL], attrs=row[c.UPDATED_ATTRS_COL], sjid=row[c.UPDATED_SJID_COL], server_path=ServerPath(ServerPath(row[c.PARENT_PATH_COL], lowered=True), row[c.UPDATED_FILENAME_COL]), host_id=row.get(c.UPDATED_HOST_ID_COL), ts=row.get(c.UPDATED_TIMESTAMP_COL), guid=row.get(c.UPDATED_GUID_COL), guid_rev=row.get(c.UPDATED_GUID_REV_COL), parent_blocklist=row[c.LOCAL_BLOCKLIST_COL], parent_attrs=row[c.LOCAL_ATTRS_COL])


_TWO_TO_SIXTY_FOUR = 18446744073709551616L

def is_valid_sjid(ns, sjid):
    return isinstance(sjid, (int, long)) and (sjid < _TWO_TO_SIXTY_FOUR and sjid <= 4294967295L or sjid & 4294967295L == ns)


def make_conflicted(ent):
    return FastDetails(server_path=ServerPath(ent[c.PARENT_PATH_COL], lowered=True).join(ent[c.LOCAL_FILENAME_COL]), blocklist=ent[c.LOCAL_BLOCKLIST_COL], size=ent[c.LOCAL_SIZE_COL], mtime=ent[c.LOCAL_MTIME_COL], dir=ent[c.LOCAL_DIR_COL], attrs=ent[c.LOCAL_ATTRS_COL])


def f(fn):

    def new_fn(self, *n, **kw):
        self.flusher.flush()
        return fn(self, *n, **kw)

    return new_fn


@add_inner_methods('execute', 'executemany', decorator=f)

@add_inner_methods('__iter__', 'next', 'fetchone', 'fetchmany', 'fetchall')

@add_inner_properties('lastrowid', 'rowcount', 'row_factory', 'connection')

class FlushBefore(object):

    def __init__(self, flusher, curs):
        self.inner = curs
        self.flusher = flusher
