#Embedded file name: dropbox/client/mapreduce.py
from __future__ import absolute_import
from collections import deque
from dropbox.keystore import KeyStore, KeychainAuthCanceled, KeychainAuthFailed, KeychainNeedsRepair, KeychainMissingItem, pbkdf2
from dropbox.trace import unhandled_exc_handler, report_bad_assumption, TRACE

class Version0(object):
    USER_HMAC_KEY = '\xd1\x14\xa5R\x12e_t\xbdw.7\xe6J\xee\x9b'
    APP_KEY = '\rc\x8c\t.\x8b\x82\xfcE(\x83\xf9_5[\x8e'
    APP_IV = '\xd8\x9bC\x1f\xb6\x1d\xde\x1a\xfd\xa4\xb7\xf9\xf4\xb8\r\x05'
    APP_ITER = 1066
    USER_KEYLEN = 16
    DB_KEYLEN = 16

    def new_user_key_and_hmac(self, ks):
        return (ks.get_random_bytes(self.USER_KEYLEN), self.USER_HMAC_KEY)

    def get_database_key(self, user_key):
        return pbkdf2(user_key, self.APP_KEY, self.APP_ITER, self.DB_KEYLEN)


CLIENT_KEY_NAME = u'Client'
BAD_CONFIG_KEY, BAD_UNLINK_COOKIE_KEY, MISSING_ITEM = xrange(3)

class DBKeyStore(object):

    def __init__(self, appdata_path, instance_id = None, create = True):
        self.parsers = {0: Version0()}
        self.hmac_keys = dict(((v, self.parsers[v].USER_HMAC_KEY) for v in self.parsers))
        self.ks = KeyStore(appdata_path, instance_id)
        self.max_version = 0
        self.errors = deque()
        if create:
            try:
                self.get_user_key()
                TRACE('KEYSTORE: Loaded previous user key')
            except KeyError:
                TRACE('KEYSTORE: creating new user key: Reason KeyError')
                self.new_user_key()
            except KeychainMissingItem:
                unhandled_exc_handler(trace_locals=False)
                self.report_error(MISSING_ITEM)
                TRACE('KEYSTORE: creating new user key: Reason KeychainMissingItem')
                self.new_user_key()
            except (KeychainAuthFailed, KeychainNeedsRepair, KeychainAuthCanceled):
                raise
            except Exception:
                unhandled_exc_handler()
                TRACE('KEYSTORE: creating new user key: Reason Exception')
                self.new_user_key()

        else:
            self.get_user_key()
            TRACE('KEYSTORE: Loaded previous user key')

    def new_user_key(self):
        parser = self.parsers[self.max_version]
        version, user_key = self.ks.store_versioned_key(CLIENT_KEY_NAME, self.max_version, *parser.new_user_key_and_hmac(self.ks))
        return (version, user_key)

    def get_user_key(self):
        version, user_key = self.ks.get_versioned_key(CLIENT_KEY_NAME, self.hmac_keys)
        return (version, user_key)

    def get_database_key(self, version = 0):
        if version:
            raise Exception('invalid version number')
        version, user_key = self.get_user_key()
        return self.parsers[version].get_database_key(user_key)

    def migrate_key_to(self, instance_id):
        version, user_key = self.ks.get_versioned_key(CLIENT_KEY_NAME, self.hmac_keys)
        return self.ks.migrate_key_to(CLIENT_KEY_NAME, version, user_key, self.hmac_keys, instance_id)

    def report_errors_to_server(self):
        ret = False
        while self.errors:
            error = self.errors.popleft()
            ret = True
            if error == BAD_CONFIG_KEY:
                report_bad_assumption('Bad decryption key for config file.')
            elif error == BAD_UNLINK_COOKIE_KEY:
                report_bad_assumption('Encrypted host id in cookie is undecryptable.')
            elif error == MISSING_ITEM:
                report_bad_assumption('Encryption key disappeared or is corrupted.')
            else:
                report_bad_assumption('Unknown sigstore error %r' % error)

        return ret

    def report_error(self, error):
        self.errors.append(error)


def attempt_keystore_migration(app, appdata_path, migrate_to_instance_id = 1):
    if app.mbox.is_secondary:
        return False
    else:
        TRACE('Attempting to migrate global keystore to instance keystore!')
        try:
            ks = DBKeyStore(appdata_path, instance_id=None, create=False)
        except Exception:
            unhandled_exc_handler()
            return False

        return ks.migrate_key_to(instance_id=migrate_to_instance_id)
