#Embedded file name: dropbox/url_info.py
from __future__ import absolute_import
import webbrowser
import urllib
import multiprocessing
import os
from Crypto.Random import random
from webbrowser import _iscommand, register, BackgroundBrowser
from dropbox.debugging import easy_repr
from dropbox.i18n import get_requested_code
from dropbox.language_data import SYSTEM_LANG_CODE
from dropbox.monotonic_time import get_monotonic_time
from dropbox.platform import platform
from dropbox.trace import unhandled_exc_handler, TRACE
from build_number import BUILD_KEY, USABILITY
if _iscommand('x-www-browser'):
    register('x-www-browser', None, BackgroundBrowser('x-www-browser'))
browser_launcher = webbrowser
if platform == 'win':
    from pynt.dlls.shlwapi import shlwapi
    from pynt.constants import S_FALSE
    from ctypes import create_unicode_buffer, byref
    from ctypes.wintypes import LPCWSTR, DWORD
    import subprocess32 as subprocess

    def open_url(full_url):
        outsize = DWORD(0)
        assname = 'http'
        try:
            shlwapi.AssocQueryStringW(0, 1, LPCWSTR(assname), None, None, byref(outsize))
        except WindowsError as e:
            if e.winerror != S_FALSE:
                raise

        outval = create_unicode_buffer(outsize.value)
        shlwapi.AssocQueryStringW(0, 1, LPCWSTR(assname), None, outval, byref(outsize))
        command = outval.value
        TRACE('Got browser command "%r"', command)
        if '%1' in command:
            command = command.replace('%1', full_url)
        else:
            command += ' "' + full_url + '"'
        TRACE('Executing %r', command)
        subprocess.Popen(command.encode('mbcs'))


    class BrowserLauncher(object):
        open = staticmethod(open_url)
        open_new = staticmethod(open_url)


    browser_launcher = BrowserLauncher
elif platform == 'mac':
    from Foundation import NSURL, NSAutoreleasePool
    from LaunchServices import LSGetApplicationForURL, kLSRolesAll
    from webbrowser import MacOSXOSAScript

    class DefaultMacBrowser(MacOSXOSAScript):

        def __init__(self):
            self._name = None

        def open(self, url, new = 0, autoraise = True):
            pool = NSAutoreleasePool.alloc().init()
            try:
                fake_url = NSURL.URLWithString_('http:')
                os_status, app_ref, appurl = LSGetApplicationForURL(fake_url, kLSRolesAll, None, None)
                if os_status != 0:
                    raise Exception('No browser default?')
                self._name = app_ref.as_pathname().encode('utf-8')
            finally:
                del pool

            return super(DefaultMacBrowser, self).open(url, new, autoraise)


    register('MacOSDefault', None, DefaultMacBrowser(), -1)
elif platform == 'linux' and os.environ.get('DISPLAY'):
    if 'GNOME_DESKTOP_SESSION_ID' in os.environ and _iscommand('gvfs-open'):
        register('gvfs-open', None, BackgroundBrowser('gvfs-open'), -1)
    if _iscommand('xdg-open'):
        register('xdg-open', None, BackgroundBrowser('xdg-open'), -1)

class DropboxURLInfo(object):

    def __init__(self, host, port, discovery_port, p2p_port):
        self.host = host
        self.port = port
        self.discovery_port = discovery_port
        self.p2p_port = p2p_port
        self.email = None
        self.root_ns = None
        self.uid = None
        self.host_int = None
        self._host_id = None
        self._server_time = None
        self._monotonic_time = None
        self._webserver = None
        self._metaserver = None
        self._pubserver = None

    def __repr__(self):
        return easy_repr(self, 'host', 'port', 'discovery_port', 'p2p_port', 'email', 'root_ns', 'uid', 'host_int', '_host_id', '_server_time', '_monotonic_time', '_webserver', '_metaserver', '_pubserver')

    def host_id(self):
        return self._host_id

    def update_host_id(self, host_id):
        self._host_id = host_id

    def update_from_ret(self, ret):
        if 'server_time' in ret:
            assert type(ret['server_time']) is int
            self._server_time = ret['server_time']
            self._monotonic_time = get_monotonic_time()
            TRACE('Monotonic time is %r', self._monotonic_time)
        if 'host_int' in ret:
            self.host_int = ret['host_int']
        if 'webserver' in ret:
            self._webserver = ret['webserver']
        if 'metaserver' in ret:
            self._metaserver = ret['metaserver']
        if 'pubserver' in ret:
            self._pubserver = ret['pubserver']
        if 'uid' in ret:
            self.uid = ret['uid']
        if 'root_ns' in ret:
            self.root_ns = ret['root_ns']
        if 'email' in ret and ret['email']:
            self.email = ret['email']

    def get_client_locale(self):
        try:
            code = get_requested_code()
        except Exception:
            unhandled_exc_handler()
            return None

        if code != SYSTEM_LANG_CODE:
            return code

    def _locale_query_piece(self):
        code = self.get_client_locale()
        if code is not None:
            return 'cl=%s' % (urllib.quote(code, safe=''),)
        return ''

    def construct_full_url(self, path = '/', query_pieces = None, host_prefix = None, with_locale = True):
        if not path.startswith('/'):
            path = '/' + path
        if not host_prefix:
            host_prefix = self._host_prefix()
        if query_pieces is None:
            query_pieces = []
        if with_locale:
            lqp = self._locale_query_piece()
            if lqp:
                query_pieces.append(lqp)
        ret = host_prefix + path
        if query_pieces:
            ret += ('&' if '?' in path else '?') + '&'.join(query_pieces)
        return ret

    def generate_public_link(self, path):
        path = unicode(path)
        public_root = '%s:/public/' % (self.root_ns,)
        if path.lower().startswith(public_root):
            return self.construct_full_url('/u/%s/%s' % (self.uid, urllib.quote(path[len(public_root):].encode('utf-8'))), host_prefix=self._public_host_prefix(), with_locale=False)
        raise Exception('no public link')

    def _host_prefix(self):
        if self._webserver is not None:
            return 'https://%s' % self._webserver
        elif self._metaserver is not None:
            return 'https://%s' % self._metaserver
        else:
            return 'http%s://%s%s' % ('s' if self.port == 443 else '', self.host, ':%d' % self.port if self.port not in (80, 443) else '')

    def _public_host_prefix(self):
        return 'https://%s' % self._pubserver

    def cli_link_url(self):
        if not self._host_id:
            raise Exception('Cannot yet generate link url')
        return self.construct_full_url('/cli_link', ['host_id=%s' % (self._host_id,)])

    def help_url(self, help_page):
        return self.construct_full_url('/c/help/%s' % (help_page,))

    if platform == 'linux':

        def launch_full_url(self, *args, **kwargs):
            import arch
            child = multiprocessing.Process(target=arch.util.using_old_ld_library_path(self._launch_full_url), args=args, kwargs=kwargs)
            child.daemon = True
            child.start()
            child.join()

    else:

        def launch_full_url(self, *args, **kwargs):
            self._launch_full_url(*args, **kwargs)

    def _launch_full_url(self, full_url, new_window = False):
        if new_window:
            browser_launcher.open_new(full_url)
        else:
            browser_launcher.open(full_url)

    @classmethod
    def init_from_build_info(cls, build_key, usability):
        boffset = 0
        api_host = None
        if build_key in ('Dropbox', 'DropboxTeam') and not usability:
            host = 'www.dropbox.com'
            api_host = [ ('client%d.dropbox.com' % i, 443) for i in xrange(100) ]
            random.shuffle(api_host)
        elif build_key.startswith('DropboxDev'):
            host = 'tarak.corp.dropbox.com'
            boffset -= 100
        elif build_key.startswith('DropboxAPI'):
            host = 'will-meta.getdropbox.com'
        elif build_key.startswith('DropboxBuild'):
            host = 'www.dropbox.com'
        elif build_key.startswith('DropboxId3'):
            host = os.getenv('DROPBOX_HOST')
            if not host:
                host = 'musicbox.corp.getdropbox.com'
        else:
            host = os.getenv('DROPBOX_HOST')
            if not host:
                host = 'www.dropbox.com'
        if not api_host:
            api_host = [(host, 443)]
        if build_key[-1].isdigit():
            p2p_port = 17501 + int(build_key[-1]) + boffset
        else:
            p2p_port = 17500 + boffset
        discovery_port = p2p_port
        port = 443
        toret = cls(host, port, discovery_port, p2p_port)
        toret.api_hosts = api_host
        return toret


dropbox_url_info = DropboxURLInfo.init_from_build_info(BUILD_KEY, USABILITY)
