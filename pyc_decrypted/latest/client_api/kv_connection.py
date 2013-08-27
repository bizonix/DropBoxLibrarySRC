#Embedded file name: client_api/kv_connection.py
import errno
import httplib
import http_authentication
import socket
import socks
import ssl
import sys
import time
from contextlib import contextmanager
import build_number
from dropbox.platform import platform
from dropbox.trace import TRACE, unhandled_exc_handler
if platform == 'linux':
    from pylinux import res_init
from . import root_certs
BUILD_KEY = build_number.BUILD_KEY
CONNECT_TIMEOUT = 10
EXPIRY_TIME = 60
TCP_SEND_BUFFER_SIZE = 131072

class ResponseWrapper(httplib.HTTPResponse):

    def setconn(self, conn):
        self.conn = conn

    def close(self):
        a = self.isclosed()
        httplib.HTTPResponse.close(self)
        if not a:
            try:
                self.conn.die_at(float(self.getheader('X-DB-Timeout')) + time.time())
            except (ValueError, TypeError):
                self.conn.die_at(EXPIRY_TIME + time.time())


TCP_SEND_BUFFER_SIZE = 131072

class FakeEvent(object):

    def __init__(self, **info):
        pass

    def info(self, name, value):
        pass

    def update(self, **info):
        pass

    def event(self, name):
        pass

    @contextmanager
    def timed_event(self, name):
        yield


class KVHTTPConnection(httplib.HTTPConnection):
    response_class = ResponseWrapper

    def __init__(self, servers, strict = None, timeout = None, on_connect = None, meta_proxy_info = None):
        self.servers = servers
        host, port = self.servers.next()
        assert type(host) is str and type(port) is int, 'Invalid host,port combination in server_list %r' % ((host, port),)
        httplib.HTTPConnection.__init__(self, host, port, strict)
        self.timeout = timeout
        self.on_connect = on_connect
        self.connection_dead_at = None
        self.current_resp = None
        self.meta_proxy_info = meta_proxy_info

    def connect(self, auth_details = None, event = FakeEvent()):
        try:
            self.host, self.port = self.servers.next()
            self.proxy_info = self.meta_proxy_info.fetch_proxies() if self.meta_proxy_info else None
            if self.proxy_info and self.proxy_info.isgood():
                TRACE('Using proxy info (HTTP): %s' % (self.proxy_info,))
                event.info('using_proxy', 'True')
                self.sock = socks.socksocket()
                self.sock.setproxy(*self.proxy_info.astuple())
                self.sock.use_connect_method = False
                if self.proxy_info.proxy_type == socks.PROXY_TYPE_HTTP:
                    self.sock.http_url_prefix = 'http://%s:%s' % (self.host, self.port)
                if auth_details:
                    self.sock.auth_details = auth_details
            else:
                self.sock = socket.socket()
            self.sock.settimeout(CONNECT_TIMEOUT)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TCP_SEND_BUFFER_SIZE)
            if sys.platform == 'darwin':
                self.sock.setsockopt(socket.SOL_SOCKET, 4130, 1)
            TRACE('Trying to connect to %s:%d (HTTP)' % (self.host, self.port))
            try:
                if platform == 'linux':
                    res_init()
            except OSError:
                unhandled_exc_handler()

            with event.timed_event('connect'):
                self.sock.connect((self.host, self.port))
            self.sock.settimeout(self.timeout)
            if callable(self.on_connect):
                self.on_connect(self.sock)
        except socks.HTTPAuthenticationNeededError as e:
            if e.value[1] and not auth_details:
                try:
                    ret = self.connect(e.value[1])
                except Exception:
                    raise
                else:
                    if callable(self.on_connect):
                        self.on_connect(self.sock)
                    return ret

            else:
                if self.meta_proxy_info:
                    self.meta_proxy_info.try_to_fix_proxy_settings(e)
                raise
        except socket.error as e:
            if self.meta_proxy_info:
                self.meta_proxy_info.try_to_fix_proxy_settings(e)
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass

            raise
        except Exception as e:
            if self.meta_proxy_info:
                self.meta_proxy_info.try_to_fix_proxy_settings(e)
            raise

        if self.proxy_info and self.proxy_info.isgood():
            if self.meta_proxy_info:
                self.meta_proxy_info.has_successfully_connected_once()

    def close(self):
        httplib.HTTPConnection.close(self)
        self.die_at(None)

    def hard_close(self):
        sock = getattr(self, 'sock', None)
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                if e[0] != errno.ENOTCONN and e[0] != errno.EBADF:
                    unhandled_exc_handler(False)

            _sock = getattr(sock, '_sock', None)
            if _sock:
                try:
                    _sock.close()
                except socket.error as e:
                    if e[0] != errno.EBADF:
                        unhandled_exc_handler(False)
                except Exception:
                    unhandled_exc_handler(False)

            try:
                sock.close()
            except Exception:
                unhandled_exc_handler(False)

        self.close()

    def die_at(self, dieat):
        self.connection_dead_at = dieat
        self.current_resp = None

    def expire(self):
        if self.connection_dead_at is not None and time.time() >= self.connection_dead_at:
            TRACE('Connection to %s:%s has expired, closing.', self.host, self.port)
            self.close()

    def getresponse(self):
        assert self.current_resp is None, 'A response is still in flight'
        self.current_resp = httplib.HTTPConnection.getresponse(self)
        self.current_resp.setconn(self)
        return self.current_resp

    def request(self, method, url, body = None, headers = {}):
        if self.current_resp is None:
            self.expire()
            self.die_at(None)
        if getattr(self.sock, 'http_url_prefix', None):
            url = self.sock.http_url_prefix + url
            if getattr(self.sock, 'auth_details', None):
                proxy_info = self.proxy_info.astuple()
                auth_type, details = self.sock.auth_details
                proxy_authorization_line = http_authentication.get_proxy_authorization_line(auth_type, details, method, url, proxy_info[4], proxy_info[5])
                header, val = proxy_authorization_line.split(': ', 1)
                headers[header] = val
        httplib.HTTPConnection.request(self, method, url, body, headers)


class KVHTTPSConnection(httplib.HTTPSConnection):
    response_class = ResponseWrapper

    def __init__(self, servers, key_file = None, cert_file = None, strict = None, timeout = None, on_connect = None, meta_proxy_info = None):
        self.servers = servers
        host, port = self.servers.next()
        assert type(host) is str and type(port) is int, 'Invalid host,port combination in server_list %r' % ((host, port),)
        httplib.HTTPSConnection.__init__(self, host, port=port, key_file=key_file, cert_file=cert_file, strict=strict)
        self.timeout = timeout
        self.on_connect = on_connect
        self.connection_dead_at = None
        self.current_resp = None
        self.meta_proxy_info = meta_proxy_info

    def request(self, method, url, body = None, headers = {}):
        method = method.encode('ascii')
        url = url.encode('ascii')
        safe_headers = {}
        for k, v in headers.iteritems():
            if isinstance(k, basestring):
                k = k.encode('utf-8')
            else:
                k = str(k)
            if isinstance(v, basestring):
                v = v.encode('utf-8')
            else:
                v = str(v)
            safe_headers[k] = v

        if self.current_resp is None:
            self.expire()
            self.die_at(None)
        return httplib.HTTPSConnection.request(self, method, url, body, safe_headers)

    def hard_close(self):
        sock = getattr(self, 'sock', None)
        if sock:
            sock = sock._sock
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except socket.error as e:
                if e[0] != errno.ENOTCONN and e[0] != errno.EBADF:
                    unhandled_exc_handler(False)

            _sock = getattr(sock, '_sock', None)
            if _sock:
                try:
                    _sock.close()
                except socket.error as e:
                    if e[0] != errno.EBADF:
                        unhandled_exc_handler(False)
                except Exception:
                    unhandled_exc_handler(False)

            try:
                sock.close()
            except Exception:
                unhandled_exc_handler(False)

        self.close()

    def close(self):
        httplib.HTTPSConnection.close(self)
        self.die_at(None)

    def die_at(self, dieat):
        self.connection_dead_at = dieat
        self.current_resp = None

    def expire(self):
        if self.connection_dead_at is not None and time.time() >= self.connection_dead_at:
            TRACE('Connection to %s:%s has expired, closing.', self.host, self.port)
            self.close()

    def getresponse(self):
        assert self.current_resp is None, 'A response is still in flight'
        self.current_resp = httplib.HTTPSConnection.getresponse(self)
        self.current_resp.setconn(self)
        return self.current_resp

    def connect(self, auth_details = None, event = FakeEvent()):
        try:
            self.host, self.port = self.servers.next()
            self.proxy_info = self.meta_proxy_info.fetch_proxies() if self.meta_proxy_info else None
            if self.proxy_info and self.proxy_info.isgood():
                TRACE('Using proxy info (HTTPS): %s' % (self.proxy_info,))
                event.info('using_proxy', 'True')
                sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM, 0)
                sock.setproxy(*self.proxy_info.astuple())
                if auth_details:
                    sock.auth_details = auth_details
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECT_TIMEOUT)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TCP_SEND_BUFFER_SIZE)
            if sys.platform == 'darwin':
                sock.setsockopt(socket.SOL_SOCKET, 4130, 1)
            TRACE('Trying to connect to %s:%d (HTTPS)' % (self.host, self.port))
            try:
                if platform == 'linux':
                    res_init()
            except OSError:
                unhandled_exc_handler()

            with event.timed_event('connect'):
                sock.connect((self.host, self.port))
            try:
                sock.settimeout(self.timeout)
                with event.timed_event('handshake'):
                    sock = ssl.wrap_socket(sock, keyfile=self.key_file, certfile=self.cert_file, ssl_version=ssl.PROTOCOL_TLSv1, ciphers='HIGH:!eNULL:!aNULL:!SSLv2', cert_reqs=ssl.CERT_REQUIRED, ca_certs_string=root_certs.root_certs)
                    cert = sock.getpeercert(binary_form=False)
                    ssl.match_hostname(cert, self.host)
                TRACE('TLS secure channel established with %s', self.host)
                self.sock = sock
                if callable(self.on_connect):
                    self.on_connect(self.sock)
            except:
                exc = sys.exc_info()
                try:
                    try:
                        sock.close()
                        self.sock = None
                    except Exception as e:
                        TRACE('Error closing socket after failed SSL negotiation (this is probably fine): %r', e)

                    raise exc[0], exc[1], exc[2]
                finally:
                    del exc

        except socks.HTTPAuthenticationNeededError as e:
            if e.value[1] and not auth_details:
                try:
                    ret = self.connect(e.value[1])
                except Exception:
                    raise
                else:
                    if callable(self.on_connect):
                        self.on_connect(self.sock)
                    return ret

            else:
                if self.meta_proxy_info:
                    self.meta_proxy_info.try_to_fix_proxy_settings(e)
                raise
        except Exception as e:
            if self.meta_proxy_info:
                self.meta_proxy_info.try_to_fix_proxy_settings(e)
            raise

        if self.proxy_info and self.proxy_info.isgood():
            if self.meta_proxy_info:
                self.meta_proxy_info.has_successfully_connected_once()

    def send(self, data):
        if self.sock is None:
            if self.auto_open:
                self.connect()
            else:
                raise httplib.NotConnected()
        if self.debuglevel > 0:
            print 'send:', repr(data)
        return self.sock.write(data)
