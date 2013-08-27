#Embedded file name: dropbox/keystore/keystore_posix.py
from __future__ import absolute_import
from Crypto.Random import get_random_bytes as _get_random_bytes
import base64
import errno
import fcntl
import hashlib
import hmac
import os
import json
import threading
import POW
from ._exceptions import KeychainMissingItem
from dropbox.trace import unhandled_exc_handler, TRACE
CIPHER_TYPE = POW.AES_128_CBC

class KeyStoreFileBacked(object):

    def __init__(self, appdata_path, instance_id = None):
        self._instance_id = instance_id
        self._appdata_path = appdata_path
        self._s = self.id2s(self.unique_id(self._appdata_path))
        self._i = 'l\x078\x014$sX\x03\xffri3\x13aQ'
        self._h = '\x8f\xf4\xf2\xbb\xad\xe9G\xea\x1f\xdfim\x80[5>'
        self._lock = threading.Lock()
        self._f = os.path.join(self._appdata_path, u'hostkeys')
        self._dict = None

    def id2s(self, _id):
        return hashlib.md5('ia9%sX' % _id + 'a|ui20').digest()

    @classmethod
    def _my_stat_repr(cls, fn):
        try:
            st = os.stat(fn)
            return 'StatResult(mtime=%r, inode=%r, size=%r)' % (st.st_mtime, st.st_ino, st.st_size)
        except OSError as e:
            if e.errno == errno.ENOENT:
                return 'ENOENT'
            raise

    def _load_dict(self):
        if self._dict is not None:
            return
        try:
            TRACE('Loading %r: %s', self._f, self._my_stat_repr(self._f))
        except Exception:
            unhandled_exc_handler()

        raw_payload = ''
        try:
            try:
                with open(self._f) as f:
                    data = f.read()
            except IOError as e:
                if e.errno == errno.ENOENT:
                    self._dict = {}
                    return
                raise

            version, raw_payload = self.unversionify_payload(data, {0: self._h})
            payload, needs_migrate = self.unobfuscate(raw_payload)
            self._dict = json.loads(payload)
        except Exception as e:
            unhandled_exc_handler(trace_locals=False)
            raise KeychainMissingItem(e, raw_payload)

        if needs_migrate:
            TRACE('Migrating keystore file.')
            self._save_dict()

    def _save_dict(self):
        payload = json.dumps(self._dict)
        payload = self.obfuscate(payload)
        data = self.versionify_payload(0, payload, self._h)
        newfile = self._f + u'.new'
        with open(newfile, 'w') as f:
            f.write(data)
        os.rename(newfile, self._f)
        try:
            TRACE('New info of %r: %s', self._f, self._my_stat_repr(self._f))
        except Exception:
            unhandled_exc_handler()

    def store_key(self, name, data):
        with self._lock:
            if self._dict is None:
                self._dict = {}
            self._dict[name] = base64.encodestring(data)
            self._save_dict()

    def get_key(self, name):
        with self._lock:
            self._load_dict()
            return base64.decodestring(self._dict[name])

    def obfuscate(self, data):
        encryptor = POW.Symmetric(CIPHER_TYPE)
        encryptor.encryptInit(self._s, self._i)
        return encryptor.update(data) + encryptor.final()

    def _unobfuscate_low(self, data, key):
        decryptor = POW.Symmetric(CIPHER_TYPE)
        decryptor.decryptInit(key, self._i)
        return decryptor.update(data) + decryptor.final()

    def unobfuscate(self, data):
        return (self._unobfuscate_low(data, self._s), False)

    def store_versioned_key(self, name, version, payload, hmac_key):
        self.store_key(name, self.versionify_payload(version, payload, hmac_key))
        return (version, payload)

    def versionify_payload(self, version, payload, hmac_key):
        payload = chr(version) + payload
        return payload + hmac.new(hmac_key, payload).digest()

    def unversionify_payload(self, data, hmac_keys):
        version = ord(data[0])
        if version not in hmac_keys:
            raise Exception('Parsing error, bad version')
        hm = hmac.new(hmac_keys[version])
        ds = hm.digest_size
        if len(data) <= ds:
            raise Exception('Bad digest size')
        stored_hm = data[-ds:]
        payload = data[:-ds]
        hm.update(payload)
        if hm.digest() != stored_hm:
            raise Exception('Bad digest')
        return (version, payload[1:])

    def get_versioned_key(self, name, hmac_keys):
        data = self.get_key(name)
        if not data:
            raise Exception('No Data')
        return self.unversionify_payload(data, hmac_keys)

    get_random_bytes = staticmethod(_get_random_bytes)

    def migrate_key_to(self, *args, **kwargs):
        return False
