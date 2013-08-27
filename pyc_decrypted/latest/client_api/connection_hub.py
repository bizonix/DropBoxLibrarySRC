#Embedded file name: client_api/connection_hub.py
import httplib
import itertools
import json
import re
import socket
import ssl
import sys
import threading
import time
import urllib
import build_number
from dropbox.event import TimedEvent
from dropbox.throttle import Throttle
from .http_authentication import parse_proxy_authentication
from .kv_connection import KVHTTPConnection, KVHTTPSConnection
try:
    from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
except ImportError:

    def TRACE(string, *n):
        print string % n


    import traceback

    def unhandled_exc_handler(*n, **kw):
        traceback.print_exc()


    def report_bad_assumption(*n, **kw):
        pass


USER_AGENT_HEAD = 'DropboxDesktopClient/%s' % build_number.VERSION
USER_AGENT_OPT_FMT = '(%(platform)s; %(version)s; %(architecture)s; %(locale)s)'
IMPORTANT_METHODS = ('close_changeset', 'commit', 'commit_batch', 'list', 'list_xattrs', 'register_host', 'retrieve', 'retrieve_batch', 'store', 'store_batch', 'subscribe')

class DropboxServerError(Exception):
    pass


class DropboxResponseClientError(DropboxServerError):
    pass


class DropboxResponseServerError(DropboxServerError):
    pass


class HTTP400Error(DropboxResponseClientError):
    pass


class HTTP401Error(DropboxResponseClientError):
    pass


class HTTP403Error(DropboxResponseClientError):
    pass


class HTTP404Error(DropboxResponseClientError):
    pass


class HTTP500Error(DropboxResponseServerError):
    pass


class HTTP502Error(DropboxResponseServerError):
    pass


class HTTP503Error(DropboxResponseServerError):
    pass


class HTTP504Error(DropboxResponseServerError):
    pass


class RequestCancelledError(Exception):
    pass


def is_fatal_ssl_error(e):
    if isinstance(e, ssl.CertificateError):
        return True
    if not isinstance(e, ssl.SSLError):
        return False
    try:
        errno, msg = e.args[:2]
    except Exception:
        errno, msg = socket.SSL_ERROR_SSL, ''

    return not ('timed out' in msg or errno in (socket.SSL_ERROR_WANT_READ,
     socket.SSL_ERROR_WANT_WRITE,
     socket.SSL_ERROR_WANT_CONNECT,
     socket.SSL_ERROR_SYSCALL,
     socket.SSL_ERROR_ZERO_RETURN))


class HTTPConnectionHub(object):

    def __init__(self, server_list, secure = True, timeout = None, on_connect = None, set_status_label = None, throttle_settings = None, meta_proxy_info = None, name = None, locale = None, response_preprocessor = None, event_reporter = None, user_agent_dict = None):
        self.throttle = Throttle()
        self.server_list, self.timeout = server_list, timeout
        self.meta_proxy_info = meta_proxy_info
        self.threadingLocal = threading.local()
        self.is_https = secure
        self.on_connect = on_connect
        self.dont_retry = False
        self.offline = True
        self.chillout = 0
        self.last_call = time.time()
        self.set_status_label = set_status_label
        self.throttle_settings = throttle_settings
        self.auth_details = None
        self.name = name
        self.locale = locale
        self.response_preprocessor = response_preprocessor
        self.event_reporter = event_reporter
        self.set_user_agent(user_agent_dict)

    def set_user_agent(self, user_agent_dict):
        self.user_agent = USER_AGENT_HEAD
        if user_agent_dict:
            user_agent_dict = dict(user_agent_dict)
            user_agent_dict['locale'] = self.locale
            self.user_agent += ' ' + USER_AGENT_OPT_FMT % user_agent_dict

    def __repr__(self):
        return 'HTTPConnectionHub(%s, %r, secure=%r, timeout=%r, on_connect=%r, set_status_label=%r, throttle_settings=%r)' % (self.name,
         self.server_list,
         self.is_https,
         self.timeout,
         self.on_connect,
         self.set_status_label,
         self.throttle_settings)

    def my_on_connect(self, sock):
        if self.throttle_settings is not None:
            self.throttle_settings(self.throttle)
        if callable(self.on_connect):
            self.on_connect(sock)

    def set_offline(self, offline, is_ssl_error = False):
        self.offline = offline
        if self.set_status_label is not None:
            if offline:
                if is_ssl_error:
                    self.set_status_label('connecting', False)
                    self.set_status_label('ssl_error', True)
                else:
                    self.set_status_label('connecting', True)
                    self.set_status_label('ssl_error', False)
            else:
                self.set_status_label('connecting', False)
                self.set_status_label('ssl_error', False)

    def disconnect(self):
        try:
            if getattr(self.threadingLocal, 'conn', None) is not None:
                self.threadingLocal.conn.close()
        except Exception:
            unhandled_exc_handler(False)

        self.threadingLocal.conn = None

    def connect(self, event):
        if not getattr(self.threadingLocal, 'conn', None):
            if not getattr(self.threadingLocal, 'servers', None):
                self.threadingLocal.servers = itertools.cycle(self.server_list)
            try:
                self.threadingLocal.conn = (self.is_https and KVHTTPSConnection or KVHTTPConnection)(self.threadingLocal.servers, timeout=self.timeout, on_connect=self.my_on_connect, meta_proxy_info=self.meta_proxy_info)
                TRACE('Explicit connect:')
                self.threadingLocal.conn.connect(self.auth_details, event=event)
                self.set_offline(False)
            except Exception as e:
                self.set_offline(True, is_fatal_ssl_error(e))
                TRACE('!! Connect failed: %r%r', type(e), e.args)
                raise

        event.update(server=self.threadingLocal.conn.host)

    def update_chillout(self, newval):
        self.chillout = float(newval)
        TRACE('%s requested backoff of %.2f sec' % (self.name, float(newval)))

    def wait_for_chillout(self, url = None):
        tosleep = self.chillout + self.last_call - time.time()
        while tosleep > 0.05:
            if tosleep > 1800 and url in IMPORTANT_METHODS:
                report_bad_assumption('Server is asking us to sleep more than thirty minutes on an important method: %r' % (tosleep,))
            TRACE('%s Sleeping (chillout) for %.2f more sec as requested by server' % (self.name, tosleep))
            time.sleep(min(tosleep, 30))
            tosleep = self.chillout + self.last_call - time.time()

        self.chillout = 0

    def force_no_retries(self):
        self.dont_retry = True

    def request(self, url, data = None, headers = None, is_json = True, max_tries = 6, ul_datacb = None, dl_datacb = None, allow_proxy_retry = True, dl_datacb2 = None, stop_cb = None, redact_data = False, backoff_period = 15, max_backoff_period = 120, do_backoff = False, chillout = True, num_streams = 1):
        if chillout:
            self.wait_for_chillout(url)
        HTTPConnectionHub.parse_operation(url)
        if type(data) is dict and not headers:
            headers = {'Content-type': 'application/x-www-form-urlencoded',
             'Connection': 'keep-alive'}
            data = urllib.urlencode(data)
        if not headers:
            headers = {'Connection': 'keep-alive'}
        if self.locale:
            headers['X-Dropbox-Locale'] = str(self.locale)
        headers['User-Agent'] = self.user_agent
        last_exception = None
        num_tries = 0
        try:
            while num_tries < max_tries:
                num_tries += 1
                event = TimedEvent(url=url, request_bytes=len(data) if data else None)
                try:
                    self.connect(event)
                    with event.timed_event('request'):
                        self.throttle.request(self.threadingLocal.conn, url, data, headers, cb=ul_datacb, stop_cb=stop_cb, num_streams=num_streams)
                    event.info('ul_throttle_bps', self.throttle.get_upload_speed())
                    ret = self._read_response(url, data, is_json, dl_datacb, dl_datacb2, allow_proxy_retry, redact_data, event, num_streams=num_streams)
                    event.event('total')
                    if self.event_reporter:
                        self.event_reporter.report_client_timing(event.report)
                    return ret
                except (DropboxResponseServerError,
                 httplib.HTTPException,
                 socket.error,
                 ssl.SSLError,
                 ssl.CertificateError) as e:
                    last_exception = sys.exc_info()
                    self.disconnect()
                    if self.dont_retry:
                        TRACE('!! dont_retry is set. re-raising: %r%r', type(e), e.args)
                        raise
                    TRACE("!! Reconnecting (here's why): %r%r", type(e), e.args)
                    if num_tries == 1:
                        TRACE('First request failed. Going to do a retry without backing off')
                        continue
                    if not do_backoff:
                        raise
                    if num_tries < max_tries:
                        TRACE('Request failed. Going to sleep for %s seconds before retrying request', backoff_period)
                        time.sleep(backoff_period)
                        backoff_period = min(max_backoff_period, backoff_period * 2)
                except Exception:
                    self.disconnect()
                    if stop_cb:
                        stop_cb()
                    raise

            if last_exception is not None:
                raise last_exception[0], last_exception[1], last_exception[2]
        finally:
            if last_exception is not None:
                del last_exception

    def _read_response(self, url, data, is_json, dl_datacb, dl_datacb2, allow_proxy_retry, redact_data, event, num_streams = 1):
        r = self.threadingLocal.conn.getresponse()
        event.event('response_start')
        event.info('request_id', r.msg.getheader('X-Dropbox-Request-Id'))
        event.info('server_response_time', r.msg.getheader('X-Server-Response-Time'))
        try:
            try:
                if self.response_preprocessor:
                    self.response_preprocessor(r)
            except Exception:
                unhandled_exc_handler()

            if r.status == 407 and allow_proxy_retry:
                self.auth_details = parse_proxy_authentication(['Proxy-Authenticate: %s' % r.getheader('proxy-authenticate')])
                allow_proxy_retry = False
                raise httplib.BadStatusLine('Proxy authorization required')
            if r.status != 200:
                try:
                    self.set_offline(True)
                except Exception:
                    unhandled_exc_handler()

                if data:
                    if redact_data:
                        data = '[redacted]'
                    elif len(data) > 200:
                        cut_point = data.find('application/octet-stream')
                        if cut_point != -1:
                            data = data[:max(200, cut_point)] + '...'
                        elif len(data) > 4000:
                            data = data[:4000] + '...'
                if r.status == 500:
                    raise HTTP500Error('Bad return status %d (url %r) (data %r) (host %r)' % (r.status,
                     url,
                     data,
                     self.server_list), r.status)
                elif r.status == 502:
                    raise HTTP502Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                elif r.status == 503:
                    raise HTTP503Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                elif r.status == 504:
                    raise HTTP504Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                elif r.status == 400:
                    raise HTTP400Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                elif r.status == 403:
                    raise HTTP403Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                elif r.status == 404:
                    raise HTTP404Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                elif r.status == 401:
                    raise HTTP401Error('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
                else:
                    raise DropboxResponseServerError('Bad return status %d (url %r) (data %r)' % (r.status, url, data), r.status)
            s = self.throttle.read(r, dl_datacb, data_cb=dl_datacb2, num_streams=num_streams)
            event.event('response_end')
            event.info('dl_throttle_bps', self.throttle.get_download_speed())
            event.info('response_bytes', len(s))
        finally:
            r.close()

        self.set_offline(False)
        self.last_call = time.time()
        if not is_json:
            return s
        try:
            return json.loads(s.decode('utf8'))
        except Exception:
            TRACE("Bad JSON: '%s'" % s)
            raise

    _url_op_regex = re.compile('([^?]*)\\??.*')

    @staticmethod
    def parse_operation(url):
        op = HTTPConnectionHub._url_op_regex.match(url)
        if op:
            return op.group(1)
        return ''
