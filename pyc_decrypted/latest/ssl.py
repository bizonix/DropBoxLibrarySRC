#Embedded file name: ssl.py
import textwrap
import _ssl
from _ssl import OPENSSL_VERSION_NUMBER, OPENSSL_VERSION_INFO, OPENSSL_VERSION
from _ssl import SSLError
from _ssl import CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
from _ssl import RAND_status, RAND_egd, RAND_add
from _ssl import SSL_ERROR_ZERO_RETURN, SSL_ERROR_WANT_READ, SSL_ERROR_WANT_WRITE, SSL_ERROR_WANT_X509_LOOKUP, SSL_ERROR_SYSCALL, SSL_ERROR_SSL, SSL_ERROR_WANT_CONNECT, SSL_ERROR_EOF, SSL_ERROR_INVALID_ERROR_CODE
from _ssl import PROTOCOL_SSLv3, PROTOCOL_SSLv23, PROTOCOL_TLSv1
_PROTOCOL_NAMES = {PROTOCOL_TLSv1: 'TLSv1',
 PROTOCOL_SSLv23: 'SSLv23',
 PROTOCOL_SSLv3: 'SSLv3'}
try:
    from _ssl import PROTOCOL_SSLv2
    _SSLv2_IF_EXISTS = PROTOCOL_SSLv2
except ImportError:
    _SSLv2_IF_EXISTS = None
else:
    _PROTOCOL_NAMES[PROTOCOL_SSLv2] = 'SSLv2'

from socket import socket, _fileobject, _delegate_methods, error as socket_error
from socket import getnameinfo as _getnameinfo
import base64
import errno
_DEFAULT_CIPHERS = 'DEFAULT:!aNULL:!eNULL:!LOW:!EXPORT:!SSLv2'

class SSLSocket(socket):

    def __init__(self, sock, keyfile = None, certfile = None, server_side = False, cert_reqs = CERT_NONE, ssl_version = PROTOCOL_SSLv23, ca_certs = None, do_handshake_on_connect = True, suppress_ragged_eofs = True, ciphers = None, ca_certs_string = None):
        socket.__init__(self, _sock=sock._sock)
        for attr in _delegate_methods:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

        if ciphers is None and ssl_version != _SSLv2_IF_EXISTS:
            ciphers = _DEFAULT_CIPHERS
        if certfile and not keyfile:
            keyfile = certfile
        try:
            socket.getpeername(self)
        except socket_error as e:
            if e.errno != errno.ENOTCONN:
                raise
            self._connected = False
            self._sslobj = None
        else:
            self._connected = True
            self._sslobj = _ssl.sslwrap(self._sock, server_side, keyfile, certfile, cert_reqs, ssl_version, ca_certs, ciphers, ca_certs_string)
            if do_handshake_on_connect:
                self.do_handshake()

        self.keyfile = keyfile
        self.certfile = certfile
        self.cert_reqs = cert_reqs
        self.ssl_version = ssl_version
        self.ca_certs = ca_certs
        self.ca_certs_string = ca_certs_string
        self.ciphers = ciphers
        self.do_handshake_on_connect = do_handshake_on_connect
        self.suppress_ragged_eofs = suppress_ragged_eofs
        self._makefile_refs = 0

    def read(self, len = 1024):
        try:
            return self._sslobj.read(len)
        except SSLError as x:
            if x.args[0] == SSL_ERROR_EOF and self.suppress_ragged_eofs:
                return ''
            raise

    def write(self, data):
        return self._sslobj.write(data)

    def getpeercert(self, binary_form = False):
        return self._sslobj.peer_certificate(binary_form)

    def cipher(self):
        if not self._sslobj:
            return None
        else:
            return self._sslobj.cipher()

    def send(self, data, flags = 0):
        if self._sslobj:
            if flags != 0:
                raise ValueError('non-zero flags not allowed in calls to send() on %s' % self.__class__)
            while True:
                try:
                    v = self._sslobj.write(data)
                except SSLError as x:
                    if x.args[0] == SSL_ERROR_WANT_READ:
                        return 0
                    if x.args[0] == SSL_ERROR_WANT_WRITE:
                        return 0
                    raise
                else:
                    return v

        else:
            return self._sock.send(data, flags)

    def sendto(self, data, flags_or_addr, addr = None):
        if self._sslobj:
            raise ValueError('sendto not allowed on instances of %s' % self.__class__)
        else:
            if addr is None:
                return self._sock.sendto(data, flags_or_addr)
            return self._sock.sendto(data, flags_or_addr, addr)

    def sendall(self, data, flags = 0):
        if self._sslobj:
            if flags != 0:
                raise ValueError('non-zero flags not allowed in calls to sendall() on %s' % self.__class__)
            amount = len(data)
            count = 0
            while count < amount:
                v = self.send(data[count:])
                count += v

            return amount
        else:
            return socket.sendall(self, data, flags)

    def recv(self, buflen = 1024, flags = 0):
        if self._sslobj:
            if flags != 0:
                raise ValueError('non-zero flags not allowed in calls to recv() on %s' % self.__class__)
            return self.read(buflen)
        else:
            return self._sock.recv(buflen, flags)

    def recv_into(self, buffer, nbytes = None, flags = 0):
        if buffer and nbytes is None:
            nbytes = len(buffer)
        elif nbytes is None:
            nbytes = 1024
        if self._sslobj:
            if flags != 0:
                raise ValueError('non-zero flags not allowed in calls to recv_into() on %s' % self.__class__)
            tmp_buffer = self.read(nbytes)
            v = len(tmp_buffer)
            buffer[:v] = tmp_buffer
            return v
        else:
            return self._sock.recv_into(buffer, nbytes, flags)

    def recvfrom(self, buflen = 1024, flags = 0):
        if self._sslobj:
            raise ValueError('recvfrom not allowed on instances of %s' % self.__class__)
        else:
            return self._sock.recvfrom(buflen, flags)

    def recvfrom_into(self, buffer, nbytes = None, flags = 0):
        if self._sslobj:
            raise ValueError('recvfrom_into not allowed on instances of %s' % self.__class__)
        else:
            return self._sock.recvfrom_into(buffer, nbytes, flags)

    def pending(self):
        if self._sslobj:
            return self._sslobj.pending()
        else:
            return 0

    def unwrap(self):
        if self._sslobj:
            s = self._sslobj.shutdown()
            self._sslobj = None
            return s
        raise ValueError('No SSL wrapper around ' + str(self))

    def shutdown(self, how):
        self._sslobj = None
        socket.shutdown(self, how)

    def close(self):
        if self._makefile_refs < 1:
            self._sslobj = None
            socket.close(self)
        else:
            self._makefile_refs -= 1

    def do_handshake(self):
        self._sslobj.do_handshake()

    def _real_connect(self, addr, return_errno):
        if self._connected:
            raise ValueError('attempt to connect already-connected SSLSocket!')
        self._sslobj = _ssl.sslwrap(self._sock, False, self.keyfile, self.certfile, self.cert_reqs, self.ssl_version, self.ca_certs, self.ciphers, self.ca_certs_string)
        try:
            socket.connect(self, addr)
            if self.do_handshake_on_connect:
                self.do_handshake()
        except socket_error as e:
            if return_errno:
                return e.errno
            self._sslobj = None
            raise e

        self._connected = True
        return 0

    def connect(self, addr):
        self._real_connect(addr, False)

    def connect_ex(self, addr):
        return self._real_connect(addr, True)

    def accept(self):
        newsock, addr = socket.accept(self)
        return (SSLSocket(newsock, keyfile=self.keyfile, certfile=self.certfile, server_side=True, cert_reqs=self.cert_reqs, ssl_version=self.ssl_version, ca_certs=self.ca_certs, ciphers=self.ciphers, ca_certs_string=self.ca_certs_string, do_handshake_on_connect=self.do_handshake_on_connect, suppress_ragged_eofs=self.suppress_ragged_eofs), addr)

    def makefile(self, mode = 'r', bufsize = -1):
        self._makefile_refs += 1
        return _fileobject(self, mode, bufsize, close=True)


def wrap_socket(sock, keyfile = None, certfile = None, server_side = False, cert_reqs = CERT_NONE, ssl_version = PROTOCOL_SSLv23, ca_certs = None, do_handshake_on_connect = True, suppress_ragged_eofs = True, ciphers = None, ca_certs_string = None):
    return SSLSocket(sock, keyfile=keyfile, certfile=certfile, server_side=server_side, cert_reqs=cert_reqs, ssl_version=ssl_version, ca_certs=ca_certs, do_handshake_on_connect=do_handshake_on_connect, suppress_ragged_eofs=suppress_ragged_eofs, ciphers=ciphers, ca_certs_string=ca_certs_string)


def cert_time_to_seconds(cert_time):
    import time
    return time.mktime(time.strptime(cert_time, '%b %d %H:%M:%S %Y GMT'))


PEM_HEADER = '-----BEGIN CERTIFICATE-----'
PEM_FOOTER = '-----END CERTIFICATE-----'

def DER_cert_to_PEM_cert(der_cert_bytes):
    if hasattr(base64, 'standard_b64encode'):
        f = base64.standard_b64encode(der_cert_bytes)
        return PEM_HEADER + '\n' + textwrap.fill(f, 64) + '\n' + PEM_FOOTER + '\n'
    else:
        return PEM_HEADER + '\n' + base64.encodestring(der_cert_bytes) + PEM_FOOTER + '\n'


def PEM_cert_to_DER_cert(pem_cert_string):
    if not pem_cert_string.startswith(PEM_HEADER):
        raise ValueError('Invalid PEM encoding; must start with %s' % PEM_HEADER)
    if not pem_cert_string.strip().endswith(PEM_FOOTER):
        raise ValueError('Invalid PEM encoding; must end with %s' % PEM_FOOTER)
    d = pem_cert_string.strip()[len(PEM_HEADER):-len(PEM_FOOTER)]
    return base64.decodestring(d)


def get_server_certificate(addr, ssl_version = PROTOCOL_SSLv3, ca_certs = None):
    host, port = addr
    if ca_certs is not None:
        cert_reqs = CERT_REQUIRED
    else:
        cert_reqs = CERT_NONE
    s = wrap_socket(socket(), ssl_version=ssl_version, cert_reqs=cert_reqs, ca_certs=ca_certs)
    s.connect(addr)
    dercert = s.getpeercert(True)
    s.close()
    return DER_cert_to_PEM_cert(dercert)


def get_protocol_name(protocol_code):
    return _PROTOCOL_NAMES.get(protocol_code, '<unknown>')


def sslwrap_simple(sock, keyfile = None, certfile = None):
    if hasattr(sock, '_sock'):
        sock = sock._sock
    ssl_sock = _ssl.sslwrap(sock, 0, keyfile, certfile, CERT_NONE, PROTOCOL_SSLv23, None)
    try:
        sock.getpeername()
    except socket_error:
        pass
    else:
        ssl_sock.do_handshake()

    return ssl_sock
