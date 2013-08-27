#Embedded file name: dropbox/client/desktop_login.py
import functools
import os
import tempfile
import time
import urllib
from Crypto.Random import get_random_bytes
from Crypto.Util.strxor import strxor
from ui.common.misc import MiscStrings
from dropbox.dispatch import Worker
from dropbox.native_event import AutoResetEvent
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from binascii import b2a_hex
from threading import Lock
login_page_template = '\n<!DOCTYPE html>\n<!-- the following line is required for our script to run in IE -->\n<!-- saved from url=(0023)https://www.dropbox.com -->\n<html>\n<head>\n    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n    <script type="text/javascript">\n        (function () {\n            "use strict";\n            function go() {\n                var c = \'%(file_nonce)s\';\n                var b = window.location.hash.substr(1);\n                window.location.hash = \'\';\n                var a = \'\';\n                if (c.length !== b.length || (c.length %% 2) !== 0) {\n                    a = \'**\' + c; // XXX - See note2 above\n                } else {\n                    // hex-decode and xor\n                    for (var i = 0; i !== c.length; i += 2) {\n                        a += String.fromCharCode(parseInt(c.slice(i, i + 2), 16) ^ parseInt(b.slice(i, i + 2), 16));\n                    }\n                }\n                var n = document.getElementById(\'n\');\n                n.setAttribute(\'value\', a);\n                document.desktop_login.submit();\n                setTimeout(function() { window.location = "%(default_web_url)s"; }, %(page_timeout)s);\n            }\n            window.onload = go;\n        })();\n    </script>\n    <style type="text/css">\n        div.center {\n            text-align: center;\n            margin: 40px 0;\n        }\n        img {\n            margin: auto;\n        }\n        body {\n            font-family: Sans-Serif;\n            font-size: 14pt;\n            padding: 80px 0;\n        }\n    </style>\n    <title>Dropbox</title>\n</head>\n<body>\n<form name="desktop_login" action="%(desktop_login_url)s" method="post">\n    <input type="hidden" name="i" value="%(host_int)s">\n    <input id=\'n\' type="hidden" name="n" value="">\n    <input type="hidden" name="u" value="%(redirect_url)s">\n    <input type="hidden" name="c" value="%(client_locale)s">\n    <noscript>\n        <div class="center">\n            <meta id="meta-refresh" http-equiv="refresh" content="2;URL=\'%(fallback_login_url)s\'">\n            <p>%(noscript_text)s</p>\n            <a href="%(fallback_login_url)s">%(signin_text)s</a>\n        </div>\n    </noscript>\n</form>\n</body>\n</html>\n'

class DesktopLoginPrefetch(StoppableThread):

    def __init__(self, app):
        super(DesktopLoginPrefetch, self).__init__(name='DESKTOP_LOGIN_PREFETCH')
        self.app = app
        self._lock = Lock()
        self._event = AutoResetEvent()
        self._nonces = {}
        self._used = {}
        self._expected_fresh_count = None

    def start(self):
        super(DesktopLoginPrefetch, self).start()

    def set_wakeup_event(self):
        self._event.set()

    def use_nonce(self, lifetime):
        with self._lock:
            try:
                fresh_nonce = self._next_nonce()
                if fresh_nonce:
                    self._used[fresh_nonce] = lifetime
                return fresh_nonce
            finally:
                self._event.set()

    def _next_nonce(self):
        if self._nonces:
            nonce = sorted(self._nonces, key=self._nonces.get)[0]
            del self._nonces[nonce]
            return nonce
        else:
            return None

    def _nonces_expiring_within(self, seconds):
        cur_time = time.time()
        ret = dict(((n, t) for n, t in self._nonces.iteritems() if t <= cur_time + seconds))
        return ret

    def run(self):
        try:
            TRACE('Starting...')
            while not self.stopped():
                with self._lock:
                    expiring = self._nonces_expiring_within(2 * DesktopLogin.LINK_LIFETIME_SECONDS)
                    used = self._used
                    self._used = {}
                    fresh_count = len(self._nonces) - len(expiring)
                invalidate_all = self._expected_fresh_count is None
                if invalidate_all or used or expiring or fresh_count < self._expected_fresh_count:
                    try:
                        expiring = dict(((n, 0) for n, t in expiring.iteritems()))
                        TRACE('Prefetching: invalidate_all:%s; expiring:%s; used:%s; fresh_count:%s; expected_fresh_count:%s', invalidate_all, len(expiring), len(used), fresh_count, self._expected_fresh_count)
                        resp = self.app.conn.desktop_login_sync(dict(used.items() + expiring.items()), invalidate_all)
                        fresh_nonces = resp['nonces']
                    except Exception:
                        unhandled_exc_handler()
                    else:
                        if not len(fresh_nonces):
                            report_bad_assumption("Didn't get any nonces on prefetch! Trying to invalidate and re-sync nonces.")
                            self._expected_fresh_count = None
                            with self._lock:
                                self._nonces = {}
                            self._event.set()
                        else:
                            if self._expected_fresh_count is None:
                                self._expected_fresh_count = len(fresh_nonces)
                            with self._lock:
                                for n in expiring:
                                    del self._nonces[n]

                                self._nonces = dict(self._nonces.items() + fresh_nonces.items())
                            TRACE('Got %s new nonces. %s total fresh nonces.', len(fresh_nonces), len(self._nonces))
                self._event.wait(timeout=DesktopLogin.LINK_LIFETIME_SECONDS)

        except Exception:
            unhandled_exc_handler()

        TRACE('Stopped.')


class DesktopLogin(object):
    LINK_LIFETIME_SECONDS = 60
    PAGE_TIMEOUT_MS = 30000

    def __init__(self, app):
        self.app = app
        self.worker = Worker(name='DESKTOP_LOGIN')
        self.prefetch = DesktopLoginPrefetch(app)
        self.started = False
        self.active_files = set()

    def start(self):
        if not self.started:
            self.prefetch.start()
            self.started = True

    def split_nonce(self, nonce):
        nonce = str(nonce)
        nonce_b = get_random_bytes(len(nonce))
        nonce_c = strxor(nonce, nonce_b)
        return (nonce_b, nonce_c)

    def login_and_redirect(self, url):
        TRACE("Attempting to launch URL: '%s'", url)
        nonce = self.prefetch.use_nonce(DesktopLogin.LINK_LIFETIME_SECONDS)
        nonce_b, nonce_c = self.split_nonce(nonce)
        host_int = self.app.dropbox_url_info.host_int
        if nonce is None or host_int is None or self.app.dropbox_url_info._host_id is None:
            TRACE("!! Couldn't create a desktop_login url %s", dict(have_nonce=True if nonce else False, host_int=host_int))
            target_url = self.app.dropbox_url_info.construct_full_url(path=url)
            self.app.dropbox_url_info.launch_full_url(target_url)
        else:
            self.worker.dispatch(functools.partial(self._launch_file_url, host_int, nonce_b, nonce_c, DesktopLogin.LINK_LIFETIME_SECONDS, url))

    def _launch_file_url(self, host_int, nonce_b, nonce_c, lifetime, url):
        try:
            file_nonce = nonce_c
            fname = None
            contents = login_page_template % dict(page_timeout=DesktopLogin.PAGE_TIMEOUT_MS, default_web_url=self.app.dropbox_url_info.construct_full_url(path='/home'), desktop_login_url=self.app.dropbox_url_info.construct_full_url(path='/desktop_login', with_locale=False), fallback_login_url=self.app.dropbox_url_info.construct_full_url(path='/login', query_pieces=['cont=/%s' % urllib.quote(url, safe='')]), host_int=host_int, file_nonce=b2a_hex(file_nonce), redirect_url=url, noscript_text=MiscStrings.desktop_login_noscript, signin_text=MiscStrings.desktop_login_signin, client_locale=self.app.dropbox_url_info.get_client_locale() or '')
            with tempfile.NamedTemporaryFile(mode='w', prefix='dbxl', suffix='.html', delete=False) as f:
                fname = f.name
                TRACE('Writing local login file %s', fname)
                f.write(contents.encode('utf-8'))
            furl = 'file:///%s#%s' % (urllib.pathname2url(fname).lstrip('/'), b2a_hex(nonce_b))
            self.active_files.add(fname)
        except Exception:
            unhandled_exc_handler()
            TRACE('!! Something bad happened while creating a file URL. Giving up and launching the URL directly.')
            self.app.dropbox_url_info.launch_full_url(self.app.dropbox_url_info.construct_full_url(url))
        else:
            TRACE('Launching URL %s', furl)
            self.app.dropbox_url_info.launch_full_url(furl)

        if fname and fname in self.active_files:
            self.worker.delay(DesktopLogin.LINK_LIFETIME_SECONDS, functools.partial(self._remove_file, fname))

    def _remove_file(self, fname):
        try:
            TRACE('Removing local login file %s', fname)
            os.remove(fname)
        finally:
            self.active_files.remove(fname)
