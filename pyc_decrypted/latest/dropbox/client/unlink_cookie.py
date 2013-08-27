#Embedded file name: dropbox/client/unlink_cookie.py
import os
import time
import json
import base64
import errno
import POW
import types
from hashlib import md5
from pprint import pformat
from dropbox.fileutils import safe_remove
from dropbox.preferences import OPT_LANG
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.client.high_trace import DropboxLog
from dropbox.client.mapreduce import BAD_UNLINK_COOKIE_KEY

class CorruptCookieError(Exception):
    pass


_salt = 's1d3fl4pz'
_COOKIE_NAME = u'unlink.db'
_HOSTDB_NAME = u'host.db'
_HOSTDBX_NAME = u'host.dbx'
UNLINK_COOKIE_PREFS = [OPT_LANG]

def write_host_dbx(host_int, dropbox_location, appdata_path):
    try:
        _k = POW.rsaFromBN(DropboxLog.K[0], DropboxLog.K[1])
        enc_host_int = base64.b64encode(_k.publicEncrypt(str(host_int)))
        assert len(enc_host_int) == 172
        lines = [enc_host_int, base64.b64encode(dropbox_location.encode('utf8'))]
        host_db_path = os.path.join(appdata_path, _HOSTDBX_NAME)
        with open(host_db_path, 'wb') as f:
            f.write('\n'.join(lines))
    except Exception:
        unhandled_exc_handler()


def write_safe_host_db(dropbox_location, appdata_path):
    try:
        with open(os.path.join(appdata_path, _HOSTDB_NAME), 'wb') as f:
            f.write('\n'.join(['0' * 40, base64.b64encode(dropbox_location.encode('utf8'))]))
    except Exception:
        unhandled_exc_handler()


def read_safe_host_db(appdata_path):
    try:
        with open(os.path.join(appdata_path, _HOSTDB_NAME), 'rb') as f:
            for i, line in enumerate(f):
                if i == 1:
                    return base64.b64decode(line).decode('utf8')

    except IOError as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
    except Exception:
        unhandled_exc_handler()


def _cookie_dict_from_config(config):
    GROUPS = [['host_id',
      'email',
      'root_ns',
      'dropbox_path'], [OPT_LANG], ['libraries_moved']]
    cookie_dict = {}
    for group in GROUPS:
        temp_dict = {}
        try:
            for key in group:
                tkey = 'path' if key == 'dropbox_path' else key
                temp_dict[tkey] = config[key]

        except KeyError:
            TRACE("Don't have the complete unlink cookie group for %r", group)
            continue

        cookie_dict.update(temp_dict)

    return cookie_dict


def write_unlink_cookie(sync_engine, keystore, **overrides):
    appdata_path = unicode(sync_engine.appdata_path)
    with sync_engine.config as config:
        cookie_dict = _cookie_dict_from_config(config)
    cookie_dict['unicode_rr_set'] = list(sync_engine.get_directory_ignore_set())
    toret = _write_cookie_dict(cookie_dict, keystore, appdata_path, overrides)
    cookie_path = cookie_dict.get('path')
    if cookie_path:
        if sync_engine.host_int:
            write_host_dbx(sync_engine.host_int, cookie_path, appdata_path)
        write_safe_host_db(cookie_path, appdata_path)
    return toret


def write_unlink_cookie_no_sync_engine(appdata_path, in_config = None, keystore = None, **overrides):
    TRACE("!! Can't write unlink cookie because we have no sync engine, just adding local overrides")
    cookie_dict = read_unlink_cookie(appdata_path, keystore)
    if not cookie_dict:
        TRACE("!! Don't have a sync engine, nor is there an old cookie; aborting writing any unlink cookie")
        return
    cookie_dict['unicode_rr_set'] = list(cookie_dict['unicode_rr_set'])
    if in_config:
        with in_config:
            cookie_from_config = _cookie_dict_from_config(in_config)
        cookie_dict.update(cookie_from_config)
    return _write_cookie_dict(cookie_dict, keystore, appdata_path, overrides)


def _write_cookie_dict(cookie_dict, keystore, appdata_path, overrides):
    cookie_dict.update(overrides)
    timestamp = '%08x' % int(time.time())
    if cookie_dict.get('host_id'):
        if keystore:
            encryptor = POW.Symmetric(POW.AES_128_CBC)
            pass_key = str(keystore.get_database_key())
            iv = md5(timestamp).digest()[:16]
            assert len(iv) == 16, 'IV is an inappropriate length for AES_128_CBC cipher'
            encryptor.encryptInit(pass_key, iv)
            cookie_dict['host_id'] = base64.b64encode(encryptor.update(cookie_dict['host_id']) + encryptor.final())
        else:
            report_bad_assumption('cookie with host_id but no keystore')
            del cookie_dict['host_id']
    data = json.dumps(cookie_dict)
    TRACE('Writing unlink cookie: %r ' % (data,))
    cipher = POW.Symmetric(POW.AES_128_CBC)
    cipher.encryptInit(md5(_salt).digest(), md5(timestamp).digest()[:16])
    encrypted = cipher.update(data) + cipher.final()
    cookie_path = os.path.join(appdata_path, _COOKIE_NAME)
    try:
        os.remove(cookie_path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
    except Exception:
        unhandled_exc_handler()

    for i in xrange(5):
        try:
            with open(cookie_path, 'wb') as f:
                f.write(timestamp)
                f.write(encrypted)
        except Exception:
            unhandled_exc_handler()
            time.sleep(0.1)
        else:
            break

    else:
        raise Exception("Couldn't write unlink cookie...")

    if 'path' in cookie_dict:
        cookie_path = cookie_dict['path']
        if not cookie_path or not isinstance(cookie_path, basestring):
            report_bad_assumption('Bad cookie_path in cookie_dict %r' % cookie_path)
    return cookie_dict


def read_unlink_cookie(appdata_path, keystore = None):
    cookie_path = os.path.join(appdata_path, _COOKIE_NAME)
    dropbox_location = read_safe_host_db(appdata_path)
    safe_remove(os.path.join(appdata_path, _HOSTDB_NAME))
    if dropbox_location:
        write_safe_host_db(dropbox_location, appdata_path)
    try:
        with open(cookie_path, 'rb') as f:
            timestamp = f.read(8)
            encrypted = ''
            while True:
                s = f.read()
                if not s:
                    break
                encrypted += s

    except IOError:
        TRACE('Unlink cookie not found')
        return
    except Exception:
        unhandled_exc_handler()

    try:
        cipher = POW.Symmetric(POW.AES_128_CBC)
        cipher.decryptInit(md5(_salt).digest(), md5(timestamp).digest()[:16])
        data = cipher.update(encrypted) + cipher.final()
        d = json.loads(data)
        TRACE('Read unlink cookie: %s', pformat(d))
        d['path'] = unicode(d['path'])
        d['unicode_rr_set'] = set((unicode(path) for path in d['unicode_rr_set']))
        if d.get('host_id') and len(d['host_id']) != 32:
            if keystore:
                try:
                    decryptor = POW.Symmetric(POW.AES_128_CBC)
                    my_pass = keystore.get_database_key()
                    iv = md5(timestamp).digest()[:16]
                    decryptor.decryptInit(my_pass, iv)
                    d['host_id'] = decryptor.update(base64.b64decode(d['host_id'])) + decryptor.final()
                except Exception:
                    keystore.report_error(BAD_UNLINK_COOKIE_KEY)
                    unhandled_exc_handler()
                    del d['host_id']

            else:
                del d['host_id']
        return d
    except Exception:
        raise CorruptCookieError()
