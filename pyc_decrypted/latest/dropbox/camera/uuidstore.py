#Embedded file name: dropbox/camera/uuidstore.py
import errno
import hmac
import struct
import uuid
import os
from hashlib import md5
import dropbox.platform
from dropbox.camera.fromfiledevice import ReadFromFile
from dropbox.functions import can_write_file
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
MAGIC = 2765596145L
VERSION = 1
HEADER = struct.pack('!LL', MAGIC, VERSION)
HEADERLEN = len(HEADER)
ENTRYLEN = 48
MAX_STORE_LENGTH = 1048576
HMAC_KEY = '52\xdd\x14M\xcf.\x03\xe6\xeb\xf7D\x7fw\xfe5'
DEVICE_ID_FOLDER = u'MISC'
DEVICE_ID_PATH = u'.dropbox.device'
WIN_ERROR_WRITE_PROTECT = 19
WIN_ERROR_IO_DEVICE = 1117

def user_id_to_key(user_id):
    return md5(str(user_id)).digest()


def new_uuid():
    return uuid.uuid4()


class UUIDStore(object):

    def __init__(self):
        self._uuids = {}
        self._dirty = False

    def has_user(self, user_id):
        return user_id_to_key(user_id) in self._uuids

    def get(self, user_id):
        return self._get_or_generate_uuid(user_id)

    def _get_or_generate_uuid(self, user_id):
        key = user_id_to_key(user_id)
        try:
            toret = self._uuids[key]
        except KeyError:
            toret = new_uuid()
            self._uuids[key] = toret
            self._dirty = True

        return str(toret)


def compute_hmac(payload, hmac_key = HMAC_KEY):
    return hmac.new(hmac_key, payload).digest()


if dropbox.platform.platform == 'win':
    import win32file
    import win32con

    def set_hidden(path):
        try:
            attrs = win32file.GetFileAttributesW(path)
            win32file.SetFileAttributesW(path, attrs | win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        except Exception:
            unhandled_exc_handler()


    def clear_hidden(path):
        try:
            win32file.SetFileAttributesW(path, 0)
        except Exception:
            pass


else:

    def set_hidden(path):
        pass


    def clear_hidden(path):
        pass


class MalformedUUIDStore(Exception):
    pass


class SDCardUUIDStore(UUIDStore):

    def __init__(self, root, alternate_paths = None, nest_in_subdir = True):
        super(SDCardUUIDStore, self).__init__()
        self.dont_touch = False
        self.parent_path = os.path.join(root, DEVICE_ID_FOLDER) if nest_in_subdir else root
        self.path = os.path.join(self.parent_path, DEVICE_ID_PATH)
        self.alternate_paths = None
        if alternate_paths:
            self.alternate_paths = [ os.path.join(path, DEVICE_ID_PATH) for path in alternate_paths ]
        keys_loaded = False
        if self.alternate_paths:
            paths = [self.path] + self.alternate_paths
        else:
            paths = [self.path]
        for path in paths:
            try:
                keys_loaded = self._load_keys(path)
            except MalformedUUIDStore:
                self.dont_touch = True
            except IOError as e:
                if e.errno == errno.EACCES:
                    self.dont_touch = True
                else:
                    raise

            if keys_loaded:
                if self.alternate_paths and path in self.alternate_paths:
                    try:
                        self._save_keys()
                        os.remove(path)
                    except Exception:
                        unhandled_exc_handler()

                break

    def is_writable(self):
        return can_write_file(self.path)

    def read_file_object(self, fobj):
        fobj.seek(0, 2)
        if fobj.tell() > MAX_STORE_LENGTH:
            raise MalformedUUIDStore('UUIDStore file is too big to be valid')
        fobj.seek(0, 0)
        data = fobj.read(HEADERLEN)
        if len(data) != HEADERLEN:
            raise MalformedUUIDStore('No header found')
        magic, version = struct.unpack('!LL', data)
        if MAGIC != magic:
            raise MalformedUUIDStore('Bad secret')
        if VERSION != version:
            raise MalformedUUIDStore('Version mismatch')
        data = fobj.read(ENTRYLEN)
        while len(data) == ENTRYLEN:
            key, uuidbytes, hmac_digest = struct.unpack('!16s16s16s', data)
            data = fobj.read(ENTRYLEN)
            if not compute_hmac(key + uuidbytes) == hmac_digest:
                continue
            self._uuids[key] = uuid.UUID(bytes=uuidbytes)

    def write_file_object(self, fobj):
        fobj.write(HEADER)
        for key, uuid in self._uuids.iteritems():
            payload = struct.pack('!16s16s', key, uuid.bytes)
            fobj.write(struct.pack('!32s16s', payload, compute_hmac(payload)))

    def _load_keys(self, path):
        if path is None:
            return False
        try:
            with open(path, 'rb') as f:
                self.read_file_object(f)
            return True
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
        except MalformedUUIDStore:
            raise

        return False

    def _save_keys(self):
        if not self.path:
            return
        try:
            if not os.path.exists(self.parent_path):
                try:
                    os.makedirs(self.parent_path)
                except Exception as e:
                    if e.errno != errno.EEXIST:
                        raise

            clear_hidden(self.path)
            with open(self.path, 'wb') as f:
                self.write_file_object(f)
            set_hidden(self.path)
        except IOError:
            raise

    def get_only(self, user_id):
        return str(self._uuids[user_id_to_key(user_id)])

    def get(self, user_id):
        if self.dont_touch:
            return None
        if not self.has_user(user_id) and not self.is_writable():
            return None
        uuid = self._get_or_generate_uuid(user_id)
        if self._dirty:
            try:
                self._save_keys()
                self._dirty = False
            except Exception as e:
                if e.errno in (errno.EROFS, errno.EACCES, errno.EPERM) or hasattr(e, 'winerror') and e.winerror in (WIN_ERROR_WRITE_PROTECT, WIN_ERROR_IO_DEVICE):
                    return None
                raise

        return uuid


class SDCardDevice(ReadFromFile):

    def __init__(self, _id, user_id):
        super(SDCardDevice, self).__init__(_id)
        self._uid_store = None
        self._user_id = user_id
        self.uid = None

    def init_uuid_store(self, root, alternate_paths = None, nest_in_subdir = True):
        self._uid_store = SDCardUUIDStore(root, alternate_paths, nest_in_subdir)
        try:
            if self._uid_store.has_user(self._user_id):
                self.uid = self._uid_store.get(self._user_id)
                TRACE('Found existing uuid %r for this (device, user) pair' % self.uid)
        except Exception:
            unhandled_exc_handler()

    def is_trackable(self):
        return self._uid_store is not None and self._uid_store.is_writable()

    def establish_uid(self):
        if not self._uid_store:
            report_bad_assumption('No uuid store object was created for this device!!')
            return
        try:
            had_uid = self.uid is not None
            self.uid = self._uid_store.get(self._user_id)
            if not had_uid:
                TRACE('Made new uuid %r for device' % self.uid)
        except Exception:
            self.uid = None
            TRACE('Failed to create or retrieve uuid for device!')
            unhandled_exc_handler()
