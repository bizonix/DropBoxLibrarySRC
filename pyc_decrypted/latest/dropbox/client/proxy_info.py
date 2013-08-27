#Embedded file name: dropbox/client/proxy_info.py
import urlparse
import urllib
from threading import Lock
import types
import client_api.socks as socks
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.i18n import trans
import arch
from dropbox.preferences import AUTO_PROXY, MANUAL_PROXY, NO_PROXY, SOCKS4, SOCKS5

class ProxyInfo(object):

    def __init__(self, proxy_type, proxy_host, proxy_port, proxy_rdns = True, proxy_user = None, proxy_pass = None):
        self.proxy_type, self.proxy_host, self.proxy_port, self.proxy_rdns, self.proxy_user, self.proxy_pass = (proxy_type,
         proxy_host,
         proxy_port,
         proxy_rdns,
         proxy_user,
         proxy_pass)

    def __str__(self):
        obfuscated = '*' * len(self.proxy_pass or '')
        return 'type=%r, host=%r, port=%r, rdns=%r, user=%r, pass=%r' % (self.proxy_type,
         self.proxy_host,
         self.proxy_port,
         self.proxy_rdns,
         self.proxy_user,
         obfuscated)

    def astuple(self):
        return (self.proxy_type,
         self.proxy_host,
         self.proxy_port,
         self.proxy_rdns,
         self.proxy_user,
         self.proxy_pass)

    def isgood(self):
        return self.proxy_host and self.proxy_port


class MetaProxyInfo(object):

    def __init__(self, prefs, bad_proxy_notification_callback = None, is_dev = False):
        self.prefs = prefs
        self.bad_proxy_notification_callback = bad_proxy_notification_callback
        self.bubbled_about_proxy_settings_yet = False
        self._has_successfully_connected_once = False
        self.is_dev = is_dev
        self.error_bubble_lock = Lock()

    def fetch_proxies(self):
        prefs = self.prefs
        try:
            mode = prefs['proxy_mode']
        except Exception:
            TRACE("Couldn't load proxy info from preferences")
            unhandled_exc_handler()
            return None

        if mode == NO_PROXY:
            return None
        if mode == AUTO_PROXY:
            info = urllib.getproxies()
            if info and 'http' in info:
                try:
                    parsed = urlparse.urlparse(info['http'])
                    _type, hostname, port = socks.PROXY_TYPE_HTTP, parsed.hostname, parsed.port
                except Exception:
                    unhandled_exc_handler()
                    return None

            elif info and 'socks' in info:
                _type = socks.PROXY_TYPE_SOCKS4
                try:
                    split = info['socks'].split('//')[1].split(':', 1)
                    if len(split) == 1:
                        hostname = split[0]
                        port = 1080
                    else:
                        hostname, port = split
                        port = int(port)
                except (ValueError, IndexError):
                    return None

            else:
                return None
            return ProxyInfo(_type, hostname, port)
        if prefs['proxy_type'] == SOCKS4:
            args = [socks.PROXY_TYPE_SOCKS4]
        elif prefs['proxy_type'] == SOCKS5:
            args = [socks.PROXY_TYPE_SOCKS5]
        else:
            args = [socks.PROXY_TYPE_HTTP]
        try:

            def tsiu(a):
                if type(a) is unicode:
                    return a.encode('utf-8')
                return a

            args += [tsiu(prefs['proxy_server']), int(prefs['proxy_port'])]
            opt_args = {}
            if prefs['proxy_requires_auth']:
                opt_args['proxy_user'] = tsiu(prefs['proxy_username'])
                opt_args['proxy_pass'] = tsiu(prefs['proxy_password'])
            return ProxyInfo(*args, **opt_args)
        except Exception:
            unhandled_exc_handler()
            return None

    def try_to_fix_proxy_settings(self, e = None):
        with self.error_bubble_lock:
            TRACE('proxy trouble? %r' % e)
            prefs = self.prefs
            if not (self.bubbled_about_proxy_settings_yet or self._has_successfully_connected_once):
                if prefs['proxy_mode'] == AUTO_PROXY:
                    TRACE('Connection problems.')
                elif prefs['proxy_mode'] == MANUAL_PROXY:
                    if e:
                        try:
                            exc_msg = hasattr(e, 'value') and e.value[1] or e[1]
                            if not isinstance(exc_msg, types.UnicodeType):
                                exc_msg = exc_msg.decode('utf8')
                        except Exception:
                            exc_msg = u'Connection failed'

                        if isinstance(e, socks.HTTPError):
                            usr_msg = 'HTTP: '
                        if isinstance(e, socks.HTTPAuthenticationNeededError):
                            usr_msg = 'HTTP: '
                            exc_msg = u'Invalid username/password'
                        elif isinstance(e, socks.Socks4Error):
                            usr_msg = 'SOCKS4: '
                        elif isinstance(e, socks.Socks5Error):
                            usr_msg = 'SOCKS5: '
                        elif isinstance(e, socks.Socks5AuthError):
                            usr_msg = trans(u'SOCKS5 Authentication: ')
                        else:
                            usr_msg = ''
                        if hasattr(e, 'value'):
                            e = e.value
                        if arch.constants.platform == 'win':
                            if e[0] == 10049:
                                usr_msg += trans(u'The server you entered is blank or invalid. Did you forget to enter a server?')
                            if e[0] == 11001:
                                usr_msg += trans(u"The server entered doesn't exist or your computer is having trouble connecting to the Internet.")
                        elif arch.constants.platform == 'mac':
                            if e[0] == 64:
                                usr_msg += trans(u"There's no proxy running on that server.")
                            elif e[0] == 8:
                                usr_msg += trans(u"The server entered doesn't exist or your computer is having trouble connecting to the Internet.")
                        if self.is_dev:
                            usr_msg += u'\n\n(%s - %s)' % (e[0], exc_msg.capitalize())
                    TRACE('Connection problems w/ manual proxy; requesting fix from user')
                    if self.bad_proxy_notification_callback:
                        self.bad_proxy_notification_callback(usr_msg)
                self.bubbled_about_proxy_settings_yet = True
                prefs.add_pref_callback('proxy_.*', self.rebubble_if_user_made_bad_changes)

    def has_successfully_connected_once(self):
        self._has_successfully_connected_once = True

    def rebubble_if_user_made_bad_changes(self, prefs):
        self.bubbled_about_proxy_settings_yet = False
