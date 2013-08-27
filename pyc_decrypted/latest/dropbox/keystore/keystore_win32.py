#Embedded file name: dropbox/keystore/keystore_win32.py
from __future__ import absolute_import
import hmac
import struct
from ctypes import byref
from Crypto.Random import get_random_bytes as _get_random_bytes
from pynt.constants import CRYPT_NEWKEYSET, CRYPT_SILENT, CRYPT_VERIFYCONTEXT, HKEY_CURRENT_USER, PROV_RSA_FULL, REG_BINARY
from pynt.dlls.advapi32 import advapi32
from pynt.helpers.crypt import protect_data, unprotect_data
from pynt.helpers.registry import create_registry_key, read_registry_value, safe_delete_regkey, set_registry_value
from pynt.types import HCRYPTPROV
from dropbox.trace import TRACE, unhandled_exc_handler
from ._exceptions import KeychainMissingItem, KeystoreRegKeyError
from build_number import BUILD_KEY

class KeyStore(object):

    def __init__(self, appdata_path = None, instance_id = None):
        self._hprov = HCRYPTPROV(0)
        self._instance_id = instance_id
        succ = advapi32.CryptAcquireContextW(byref(self._hprov), None, None, PROV_RSA_FULL, CRYPT_SILENT | CRYPT_VERIFYCONTEXT)
        if not succ:
            TRACE('Error calling CryptAcquireContextW. Trying to create.')
            succ = advapi32.CryptAcquireContextW(byref(self._hprov), None, None, PROV_RSA_FULL, CRYPT_NEWKEYSET, CRYPT_SILENT | CRYPT_VERIFYCONTEXT)
            if not succ:
                TRACE("!! Error calling CryptAcquireContextW. Couldn't create.")

    def __del__(self):
        if self._hprov.value:
            advapi32.CryptReleaseContext(self._hprov, 0)

    get_random_bytes = staticmethod(_get_random_bytes)

    @property
    def key_suffix(self):
        if self._instance_id:
            return unicode(self._instance_id)
        return u''

    def store_versioned_key(self, name, version, payload, hmac_key):
        return self._store_versioned_key(name, version, payload, hmac_key, key_suffix=self.key_suffix)

    def _store_versioned_key(self, name, version, payload, hmac_key, key_suffix):
        protected_data = protect_data(payload, hmac_key)
        protected_payload = struct.pack('BL', version, len(protected_data)) + protected_data
        protected_payload += hmac.new(hmac_key, protected_payload).digest()
        success = False
        with create_registry_key(HKEY_CURRENT_USER, u'SOFTWARE\\%s\\ks' % BUILD_KEY + key_suffix, restrict_to_current_user=True) as hkey, created:
            if hkey:
                success = set_registry_value(hkey, name, REG_BINARY, protected_payload)
        if not success:
            raise KeystoreRegKeyError('Failed to create keystore regkey!')
        return (version, payload)

    def get_versioned_key(self, name, hmac_keys):
        with create_registry_key(HKEY_CURRENT_USER, u'SOFTWARE\\%s\\ks' % BUILD_KEY + self.key_suffix, restrict_to_current_user=True) as hkey, created:
            if hkey:
                hmaced_payload = read_registry_value(hkey, name)
                version, payload_len = struct.unpack_from('BL', hmaced_payload)
                hmac_size = len(hmaced_payload) - payload_len - 8
                v, l, payload, h = struct.unpack('BL%ds%ds' % (payload_len, hmac_size), hmaced_payload)
            else:
                raise KeyError('Key not found')
        try:
            hm_key = hmac_keys[v]
        except KeyError:
            raise KeychainMissingItem('Parsing error, bad version')

        hm = hmac.new(hm_key)
        if hm.digest_size != len(h):
            raise KeychainMissingItem('Bad digest size')
        hm.update(hmaced_payload[:-hm.digest_size])
        if hm.digest() != h:
            raise KeychainMissingItem('Bad digest')
        try:
            unprotected_payload = unprotect_data(payload, hm_key)
        except Exception as e:
            unhandled_exc_handler()
            raise KeychainMissingItem(e)

        return (v, unprotected_payload)

    def migrate_key_to(self, name, version, payload, hmac_keys, migrate_to_instance_id):
        ret = False
        try:
            self._store_versioned_key(name, version, payload, hmac_keys[version], key_suffix=unicode(migrate_to_instance_id))
        except Exception:
            unhandled_exc_handler()
        else:
            ret = True
            safe_delete_regkey(HKEY_CURRENT_USER, u'SOFTWARE\\%s\\ks' % BUILD_KEY + self.key_suffix)

        return ret
