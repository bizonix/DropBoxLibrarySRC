#Embedded file name: dropbox/keystore/keystore_mac.py
from __future__ import absolute_import
import POW
import json
import os
import struct
from Crypto.Random import get_random_bytes as _get_random_bytes
from errno import ENOENT
import build_number
from pymac.helpers.disk import get_volume_uuid
from pymac.helpers.iokit import get_serial_number
from pymac.helpers.security import KeychainItem
from client_api.hashing import dropbox_hash
from dropbox.trace import unhandled_exc_handler, report_bad_assumption, TRACE
from dropbox.fileutils import safe_remove
from .keystore_posix import KeyStoreFileBacked

class KeyStore(KeyStoreFileBacked):

    def __init__(self, appdata_path = None, instance_id = None):
        super(KeyStore, self).__init__(appdata_path, instance_id)
        user_file = os.path.join(appdata_path, u'user.id')
        try:
            with open(user_file, 'r') as f:
                username = f.read().strip()
            if username:
                CLIENT_KEY_NAME = u'Client'
                item = KeychainItem.find(u'%s %s' % (build_number.BUILD_KEY, CLIENT_KEY_NAME), username)
                try:
                    self.get_key(CLIENT_KEY_NAME)
                except KeyError:
                    TRACE('KEYSTORE: Migrating from Keychain')
                    self.store_key(CLIENT_KEY_NAME, item.value)
                finally:
                    item.delete()

            safe_remove(user_file)
        except IOError as e:
            if e.errno != ENOENT:
                unhandled_exc_handler()
                safe_remove(user_file)
        except Exception:
            unhandled_exc_handler()
            safe_remove(user_file)

    def unique_id(self, path, old = False):
        inode = os.stat(path).st_ino
        try:
            uuid = get_volume_uuid(path)
        except Exception:
            unhandled_exc_handler()
            uuid = ''

        if old:
            serial = get_serial_number()
            if not serial:
                report_bad_assumption('No serial number on this machine!')
            TRACE('KEYSTORE: OLD unique_id = %r %s %s %s', path, dropbox_hash('%d' % inode), dropbox_hash('%s' % uuid), dropbox_hash('%s' % serial))
            return '%d_%s_%s' % (inode, uuid, serial)
        TRACE('KEYSTORE: unique_id = %r %s %s', path, dropbox_hash('%d' % inode), dropbox_hash('%s' % uuid))
        return '%d_%s' % (inode, uuid)

    def unobfuscate(self, data):
        try:
            t, needs_migrate = super(KeyStore, self).unobfuscate(data)

            def no(*n, **kw):
                pass

            json.loads(t, object_hook=no)
            return (t, needs_migrate)
        except (POW.SSLError, ValueError):
            unhandled_exc_handler(trace_locals=False)
            s = self.id2s(self.unique_id(self._appdata_path, old=True))
            return (self._unobfuscate_low(data, s), True)

    get_random_bytes = staticmethod(_get_random_bytes)
