#Embedded file name: dropbox/client/preferences.py
from __future__ import absolute_import
import contextlib
import re
import unicodedata
from hashlib import md5
from threading import Lock
import POW
from dropbox.trace import unhandled_exc_handler, TRACE, report_bad_assumption
import dropbox.i18n
from dropbox.preferences import AUTO_PROXY, OPT_BUBBLES, OPT_CAMERA_UPLOAD_WINDOWS, OPT_LANG, OPT_LEOPARD, OPT_PHOTO, OPT_PHOTO_PRIMARY, OPT_P2P, OPT_STARTUP, OPT_SCREENSHOTS, OPT_IMPORTED_IPHOTOS_ONCE, HTTP
from dropbox.client.screenshots import ScreenshotsController
import arch
CIPHER_TYPE = POW.AES_128_CBC

class UserCurrentlyEditingPreferencesError(Exception):
    pass


class PrefController(object):

    def __init__(self, config):
        self._config = config
        self.editing_prefs_lock = Lock()
        self.pref_callbacks = []
        self.pref_callbacks_lock = Lock()
        self.single_access_blacklist = []

    def encode_on_write(self, d):
        return d

    def parse_on_read(self, d):
        return d

    def __getitem__(self, k):
        if k not in self.single_access_blacklist:
            try:
                single = {k: self._config[k]}
            except KeyError:
                single = {}

            return self.parse_on_read(single)[k]
        else:
            return self.get_unlocked()[k]

    def get_unlocked(self):
        return self.parse_on_read(dict(self._config.items()))

    @contextlib.contextmanager
    def update_prefs_context_manager(self):
        if not self.editing_prefs_lock.acquire(False):
            raise UserCurrentlyEditingPreferencesError()
        try:
            yield
        finally:
            self.editing_prefs_lock.release()

    def update(self, dct):
        dct = self.encode_on_write(dct)
        TRACE('Config update from preferences: %r', dct)
        for key in dct:
            assert '\n' not in key, 'Pref keys should not have newline chars, for matching simplicity: %r' % key

        to_call_keys = set()
        for k in dct:
            if k not in self._config or self._config[k] != dct[k]:
                to_call_keys.add(k)

        with self.update_prefs_context_manager():
            self._config.update(dct)
        to_call = set()
        with self.pref_callbacks_lock:
            for key_re, callback in self.pref_callbacks:
                for key_dct in to_call_keys:
                    if key_re.match(key_dct):
                        TRACE('Want to call %r for pref key %r' % (callback, key_dct))
                        to_call.add(callback)

        for callback in to_call:
            try:
                callback(self)
            except Exception:
                unhandled_exc_handler()

    def add_pref_callback(self, key_re_template, callback):
        compiled = re.compile('^%s$' % key_re_template)
        with self.pref_callbacks_lock:
            self.pref_callbacks.append((compiled, callback))

    def remove_pref_callback(self, key_re_template, callback):
        compiled = re.compile('^%s$' % key_re_template)
        with self.pref_callbacks_lock:
            indices_to_remove = []
            for i, (regexp, cb) in enumerate(self.pref_callbacks):
                if cb == callback and regexp == compiled:
                    indices_to_remove.append(i)

            if len(indices_to_remove):
                indices_to_remove.reverse()
                for i in indices_to_remove:
                    self.pref_callbacks.pop(i)


class DropboxPrefController(PrefController):

    def __init__(self, *n, **kw):
        self.app = kw.pop('app', None)
        super(DropboxPrefController, self).__init__(*n, **kw)
        self.default_state = {'throttle_upload_speed': 10.0,
         'throttle_upload_style': 1,
         'throttle_download_speed': 50.0,
         'throttle_download_style': 0,
         'proxy_mode': AUTO_PROXY,
         'proxy_type': HTTP,
         'proxy_server': '',
         'proxy_port': 8080,
         'proxy_requires_auth': False,
         'proxy_username': '',
         'proxy_password': '',
         'dropbox_path': self.app.default_dropbox_path,
         'network_drive': False,
         OPT_STARTUP: True,
         OPT_BUBBLES: True,
         OPT_P2P: arch.util.enable_p2p_default(),
         OPT_LEOPARD: False,
         OPT_PHOTO: None,
         OPT_PHOTO_PRIMARY: True,
         OPT_SCREENSHOTS: ScreenshotsController.STATE_UNKNOWN,
         'selsync_advanced_view_hint': False,
         OPT_LANG: dropbox.i18n.get_default_code_for_prefs(),
         OPT_CAMERA_UPLOAD_WINDOWS: 0,
         OPT_IMPORTED_IPHOTOS_ONCE: False}
        self.single_access_blacklist = ['proxy_password']
        for migration in (arch.util.startup_pref_migration, self.historical_key_migration, self.type_safety_migration):
            try:
                unlocked_no_parse = dict(self._config.items())
                migrated, to_delete = migration(unlocked_no_parse)
                TRACE('Potentially migrating preferences due to %r', migration)
                if to_delete:
                    TRACE('deleting keys: %r' % (to_delete,))
                    for key in to_delete:
                        del self._config[key]

                if migrated:
                    TRACE('updating keys: %r' % (migrated,))
                    self._config.update(migrated)
            except Exception:
                unhandled_exc_handler()

    def get_config_for_secondary(self):
        config = self.get_unlocked()
        return {k:config[k] for k in ('proxy_mode',
         'proxy_type',
         'proxy_server',
         'proxy_port',
         'proxy_requires_auth',
         'proxy_username',
         'proxy_password',
         OPT_P2P,
         OPT_LANG,
         OPT_PHOTO,
         OPT_PHOTO_PRIMARY)}

    @staticmethod
    def numeric_unequiv(a, b):
        return (isinstance(a, int) or isinstance(a, float) or isinstance(a, long)) and not (isinstance(b, int) or isinstance(b, float) or isinstance(b, long))

    @staticmethod
    def string_unequiv(a, b):
        return isinstance(a, basestring) and not isinstance(b, basestring)

    def type_safety_migration(self, d):
        migrated = {}
        to_delete = set()
        for k in self.default_state:
            if k in d and (self.numeric_unequiv(self.default_state[k], d[k]) or self.string_unequiv(self.default_state[k], d[k])):
                to_delete.add(k)
                report_bad_assumption('Type of loaded pref key %r is not equivalent to type in default state: %r (%r) != %r (%r)' % (k,
                 d[k],
                 type(d[k]),
                 self.default_state[k],
                 type(self.default_state[k])))

        return (migrated, to_delete)

    def historical_key_migration(self, d):
        migrated = {}
        to_delete = set()
        if 'max_download_kBs' in d:
            if d['max_download_kBs'] <= 0:
                migrated['throttle_download_style'] = 0
            else:
                migrated['throttle_download_style'] = 2
                migrated['throttle_download_speed'] = d['max_download_kBs']
            to_delete.add('max_download_kBs')
        if 'max_upload_kBs' in d:
            if d['max_upload_kBs'] < 0:
                migrated['throttle_upload_style'] = 1
            elif d['max_upload_kBs'] == 0:
                migrated['throttle_upload_style'] = 0
            else:
                migrated['throttle_upload_style'] = 2
                migrated['throttle_upload_speed'] = d['max_upload_kBs']
            to_delete.add('max_upload_kBs')
        if 'throttle_upload_speed' in d:
            if d['throttle_upload_speed'] <= 0:
                migrated['throttle_upload_speed'] = 0.001
        if 'throttle_download_speed' in d:
            if d['throttle_download_speed'] <= 0:
                migrated['throttle_download_speed'] = 0.001
        return (migrated, to_delete)

    def encode_on_write(self, d):
        if 'proxy_password' in d:
            if 'proxy_username' in d and 'proxy_server' in d:
                encryptor = POW.Symmetric(CIPHER_TYPE)
                encryptor.encryptInit(md5(d['proxy_username']).digest(), md5(d['proxy_server']).digest()[:16])
                d['shadowed_proxy_password'] = encryptor.update(d.pop('proxy_password')) + encryptor.final()
            else:
                del d['proxy_password']
        return d

    def parse_on_read(self, d):
        if 'shadowed_proxy_password' in d:
            if 'proxy_username' in d and 'proxy_server' in d:
                decryptor = POW.Symmetric(CIPHER_TYPE)
                decryptor.decryptInit(md5(d['proxy_username']).digest(), md5(d['proxy_server']).digest()[:16])
                d['proxy_password'] = decryptor.update(d.pop('shadowed_proxy_password')) + decryptor.final()
            else:
                TRACE("hmm, user's config table was in a slightly messed up state.. shouldn't have shadowed_proxy_password without proxy_username and proxy_server")
                del d['shadowed_proxy_password']
        d = dict(((k, d.get(k, self.default_state[k])) for k in self.default_state))
        d['dropbox_path'] = unicodedata.normalize(arch.constants.local_form, d['dropbox_path'])
        return d
