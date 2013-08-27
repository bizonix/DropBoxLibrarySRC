#Embedded file name: dropbox/sync_engine/p2p/protocol.py
from __future__ import absolute_import
import ctypes
import socket
import time
import zlib
import dropsyncore as asyncore
import json
import POW
import select
import struct
import sys
from socket import ntohs, htons
from Crypto.Random import random
import arch
from dropbox.globals import dropbox_globals
from dropbox.url_info import dropbox_url_info
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.network import is_in_local_network
from .crypto import CryptoData
from .faststr import AppendString
HASTIMEOUT = 2.0
GETTIMEOUT = 20.0
NOREADTIMEOUT = 5.0
MAXRECONNECTS = 5
MAXRECONNTIMEFRAME = 200.0
SSL_BUFSIZE = 16384
PINGTIMEOUT = 60.0
PINGINTERVAL = 30.0
NAMESPACETIMEOUT = 500.0
HASBLACKLISTTIME = 60
GETBLACKLISTTIME = 600
hash_cache = dict()
cbdict = dict()
_FORCE_TLSv1 = False

def set_force_tlsv1(val):
    global _FORCE_TLSv1
    if _FORCE_TLSv1 != val:
        TRACE('Changing force TLSv1 setting from %s to %s', _FORCE_TLSv1, val)
        _FORCE_TLSv1 = val
        return True
    return False


class WrongCertException(Exception):
    pass


class ConnTimeoutException(Exception):
    pass


class StalledReadException(Exception):
    pass


class HASTakesTooLong(Exception):
    pass


class BothHASandGETError(Exception):
    pass


class SSLVerifyFailed(Exception):
    pass


class GETTakesTooLong(Exception):
    pass


class GETFailError(Exception):
    pass


class MyTrace(object):
    name = 'UNKNOWN'

    def setName(self, name):
        self.name = name

    def TRACE(self, msg):
        TRACE('%s: %s' % (self.name, msg))


class IntProtocol(asyncore.dispatcher):

    def __init__(self, *args, **kwargs):
        asyncore.dispatcher.__init__(self, *args, **kwargs)
        self.inbuf = AppendString()
        self.outbuf = AppendString()
        self.cmdlen = 0
        self.cmdbuf = []
        self.override = False

    def handle_error(self):
        self.handle_close()
        unhandled_exc_handler()

    def getData(self):
        self.inbuf += self.recv(SSL_BUFSIZE)

    def intsend(self, *args, **kwargs):
        if not kwargs.get('raw'):
            cmd = json.dumps(args)
        else:
            cmd = args[0]
        self.outbuf += struct.pack('!I', len(cmd))
        self.outbuf += cmd

    def writable(self):
        return len(self.outbuf) > 0

    def needMoreData(self):
        pass

    def intprocess(self):
        self.getData()
        while True:
            if self.cmdlen < 1:
                if len(self.inbuf) >= 4:
                    self.cmdlen = struct.unpack('!I', self.inbuf.getbuf(4))[0]
                else:
                    return
            if len(self.inbuf) < self.cmdlen:
                self.needMoreData()
                return
            data = self.inbuf.getbuf(self.cmdlen)
            self.cmdlen = 0
            self.cmdbuf.append(data)
            if len(self.inbuf) < 1:
                break


class ConnectionPool(IntProtocol, MyTrace):
    MAX_PEERS_PER_REQUEST = 20

    def __init__(self, status, discovery, sock, p2p_state, map = None, version = None):
        self.setName('ConnectionPool')
        self.status = status
        IntProtocol.__init__(self, sock=sock, map=map)
        self.p2p_state = p2p_state
        self.map = map
        self.namespaces = {}
        self.blacklist = {}
        self.waitingHAS = {}
        self.waitingGET = {}
        self.connectsPerPeer = {}
        self.scheduled_for_ns = {}
        self.currently_connecting_for_ns = {}
        self.active_namespaces = {}
        self.version = version
        self.discovery = discovery
        self.discovery.subscribe(self.newPeer)
        self.server = None

    def blacklistClientFor(self, client, seconds):
        self.blacklist[client.host_int] = time.time() + seconds

    def closeAllConnections(self):
        for key, nsconns in self.namespaces.items():
            for c in list(nsconns):
                c.close()
                c.handle_close()

    def getPeerAndConnCount(self):
        peers = set()
        totalConns = 0
        for key, nsconns in self.namespaces.items():
            for c in list(nsconns):
                peers.add(c.host_int)
                totalConns += 1

        return {'peer_count': len(peers),
         'total_connections': totalConns}

    def handle_read(self):
        self.intprocess()
        self.processCommands()

    def handle_write(self):
        try:
            totalSent = 0
            while len(self.outbuf) > 0:
                sent = self.socket.send(self.outbuf.getbuf(SSL_BUFSIZE, keep=True))
                totalSent += sent
                if sys.platform.startswith('win'):
                    try:
                        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                    except Exception:
                        unhandled_exc_handler()

                self.outbuf.getbuf(sent)

        except Exception as e:
            self.TRACE('IntProtocol sending too fast. Buffer full: %s' % (e,))
            unhandled_exc_handler()

    def processCommands(self):
        while self.cmdbuf:
            cmd = self.cmdbuf.pop(0)
            cmd = json.loads(cmd)
            if cmd[0] == 'GET':
                targetHash = cmd[1]
                targetNamespaces = [ int(x) for x in cmd[2] ]
                callback = cbdict[cmd[3]]
                for ns in targetNamespaces:
                    self.active_namespaces[ns] = time.time()

                fail = True
                if not targetNamespaces:
                    targetNamespaces = []
                for tns in targetNamespaces:
                    tconns = self.namespaces.get(tns)
                    if tconns:
                        now = time.time()
                        if len(tconns) > self.MAX_PEERS_PER_REQUEST:
                            tconns = random.sample(list(tconns), self.MAX_PEERS_PER_REQUEST)
                        for c in tconns:
                            fail = False
                            self.TRACE('Asking %s for hash %s.' % (c, targetHash))
                            c.requestHash(targetHash, callback)
                            askedClients = self.waitingHAS.get(targetHash, (None, None, 0))[2] + 1
                            self.waitingHAS[targetHash] = (now, targetNamespaces, askedClients)

                if fail:
                    self.TRACE('Found no suitable p2p connection.')
                    self.intsend('GETFAIL', targetHash)

    def newConn(self, client):
        self.TRACE('connectionpool got new peerconnection to %s' % (client,))
        if not self.namespaces.get(client.namespace):
            self.namespaces[client.namespace] = set()
        self.namespaces[client.namespace].add(client)

    def versionsMatch(self, otherVersion):
        if self.version[0] == otherVersion[0] and self.version[1] == otherVersion[1]:
            return True
        return False

    def newPeer(self, msg):
        ip = msg['recv_addr']
        port = msg['port']
        want_announce = False
        if self.status.is_true('connecting'):
            return want_announce
        if not self.p2p_state.p2p_enabled:
            return want_announce
        if self.versionsMatch(msg['version']) and msg.get('host_int') and msg.get('host_int') != dropbox_url_info.host_int:
            for namespace in frozenset(msg['namespaces']).intersection(frozenset(self.p2p_state.sync_engine.get_all_tracked_namespaces())):
                already_known = not self.isNewpeer(msg, namespace)
                if not already_known:
                    self.TRACE('found a NEWPEER: %s %s %s %s' % (ip,
                     port,
                     namespace,
                     msg))
                    now = time.time()
                    key = (ip, port, namespace)
                    blackTimeout = self.blacklist.get(msg.get('host_int'), 0)
                    if time.time() < blackTimeout:
                        self.TRACE('Peer %s blacklisted till %d. Not connecting.' % (key, blackTimeout))
                        continue
                    if not self.connectsPerPeer.get(key):
                        self.connectsPerPeer[key] = []
                    self.connectsPerPeer[key].append(now)
                    self.connectsPerPeer[key] = [ x for x in self.connectsPerPeer[key] if now - x < MAXRECONNTIMEFRAME ]
                    if len(self.connectsPerPeer[key]) >= MAXRECONNECTS:
                        self.TRACE('Multiple (%d) reconnects to same peer %s - not reconnecting' % (len(self.connectsPerPeer[key]), key))
                        continue
                    client = P2PClient(msg['host_int'], ip, port, p2p_state=self.p2p_state, namespace=namespace, map=self.map, pool=self)
                    self.scheduleConn(client)
                    want_announce = True

        return want_announce

    def isNewpeer(self, msg, namespace):
        for client in self.namespaces.get(namespace, []):
            if client.host_int == msg.get('host_int'):
                return False

        for client in self.scheduled_for_ns.get(namespace, []):
            if client.host_int == msg.get('host_int'):
                return False

        for client in self.currently_connecting_for_ns.get(namespace, []):
            if client.host_int == msg.get('host_int'):
                return False

        return True

    def scheduleConn(self, client):
        if client not in self.currently_connecting_for_ns.get(client.namespace, set()):
            nsschedule = self.scheduled_for_ns.setdefault(client.namespace, set())
            nsschedule.add(client)

    def notify(self, conn, cmd):
        if cmd[0] == 'HASREPLY':
            if cmd[2]:
                if cmd[1] in self.waitingHAS:
                    now = time.time()
                    self.TRACE('GOT HASREPLY! Requesting the data from peer!')
                    del self.waitingHAS[cmd[1]]
                    self.waitingGET[cmd[1]] = (now, conn)
                    conn.getHash(cmd[1])
                else:
                    self.TRACE('Ignoring surplus HAS %s %s' % (cmd[0], cmd[1]))
            else:
                tmp = self.waitingHAS.get(cmd[1])
                if tmp:
                    self.waitingHAS[cmd[1]] = (tmp[0], tmp[1], tmp[2] - 1)
                    self.TRACE('RECEIVED HASREPLY NO! %s' % (self.waitingHAS[cmd[1]],))
                    if self.waitingHAS[cmd[1]][2] <= 0:
                        self.TRACE('No peers have the requested Hash in HAS. Failing P2P for this hash.')
                        del self.waitingHAS[cmd[1]]
                        self.intsend('HASFAIL', cmd[1])
                else:
                    self.TRACE('Ignoring surplus HAS %s %s (fail)' % (cmd[0], cmd[1]))
        elif cmd[0] == 'GETREPLY':
            if cmd[1] in self.waitingGET:
                try:
                    del self.waitingGET[cmd[1]]
                except Exception:
                    pass

                self.TRACE('Client %s got data for ConnectionPool: %s %s %d' % (conn,
                 cmd[0],
                 cmd[1],
                 len(cmd[2])))
                self.intsend(cmd[0], cmd[1])
                hash_cache[cmd[1]] = cmd[2]
            else:
                self.TRACE('Ignoring surplus GETREPLY for %s %s' % (cmd[0], cmd[1]))
        elif cmd[0] == 'GETFAIL':
            try:
                del self.waitingGET[cmd[1]]
                self.intsend(cmd)
            except Exception:
                unhandled_exc_handler()

            try:
                raise GETFailError('GETFail %s' % (cmd,))
            except Exception:
                unhandled_exc_handler()

        elif cmd[0] == 'HASFAIL':
            try:
                del self.waitingHAS[cmd[1]]
                self.intsend(cmd)
            except Exception:
                unhandled_exc_handler()

        else:
            try:
                raise Exception('Unhandled pool notification %s received.' % (cmd[0],))
            except Exception:
                unhandled_exc_handler()

    def clientDied(self, client):
        try:
            self.namespaces[client.namespace].remove(client)
        except Exception:
            self.TRACE('tried to remove dead client in clientDied')

    def registerServer(self, server):
        self.server = server

    def maybeTimeout(self, forcefail = False):
        now = time.time()
        both = self.waitingHAS.keys() + self.waitingGET.keys()
        for hval in both:
            hastime, targetNamespaces, clientsAsked = self.waitingHAS.get(hval, (None, None, 0))
            gettime, GETclient = self.waitingGET.get(hval, (None, None))
            if hastime and gettime:
                try:
                    raise BothHASandGETError('SHOULD NOT HAPPEN: both HAS and GET active for hash %s' % (hval,))
                except Exception:
                    unhandled_exc_handler()

            hightime = max(hastime, gettime)
            if hastime and (now - hightime > HASTIMEOUT or forcefail):
                try:
                    raise HASTakesTooLong('TIMING OUT P2P REQUEST WITH NO TIMELY HAS RESPONSE %f' % (now - hightime,))
                except Exception:
                    unhandled_exc_handler()

                for tns in targetNamespaces:
                    for client in list(self.namespaces.setdefault(tns, set())):
                        client.dieAndBlacklistFor(HASBLACKLISTTIME)

                try:
                    del self.waitingHAS[hval]
                except Exception:
                    unhandled_exc_handler()

                try:
                    self.intsend('HASFAIL', hval)
                except Exception:
                    unhandled_exc_handler()

            elif gettime and (now - hightime > GETTIMEOUT or forcefail):
                try:
                    raise GETTakesTooLong('TIMING OUT P2P REQUEST WITH NO TIMELY GET RESPONSE %f' % (now - hightime,))
                except Exception:
                    unhandled_exc_handler()

                GETclient.dieAndBlacklistFor(GETBLACKLISTTIME)
                try:
                    del self.waitingGET[hval]
                except Exception:
                    unhandled_exc_handler()

                try:
                    self.intsend('GETFAIL', hval)
                except Exception:
                    unhandled_exc_handler()

    def pulse(self):
        forcefail = False
        if not self.p2p_state.p2p_enabled:
            forcefail = True
            self.scheduled_for_ns = {}
            self.currently_connecting_for_ns = {}
        self.maybeTimeout(forcefail=forcefail)
        for ns in list(self.active_namespaces.keys()):
            if time.time() - self.active_namespaces[ns] > NAMESPACETIMEOUT:
                self.TRACE('Namespace %d timed out.' % ns)
                del self.active_namespaces[ns]
                continue
            chces = tuple(self.scheduled_for_ns.get(ns, []))
            if chces:
                client = random.choice(chces)
                self.scheduled_for_ns[ns].remove(client)
                self.currently_connecting_for_ns.setdefault(ns, set())
                self.currently_connecting_for_ns[ns].add(client)
                if not self.p2p_state.p2p_enabled:
                    self.TRACE('P2P Disabled. Not Connecting.')
                else:
                    client.startConnecting()

        for ns in self.namespaces.values():
            for client in list(ns):
                client.pulse()

        if self.server:
            self.server.pulse()
        if len(self.waitingHAS) or len(self.waitingGET):
            return True
        else:
            return False


class P2PServer(asyncore.dispatcher, MyTrace):

    def __init__(self, p2p_state, sync_engine, map = None, pool = None):
        self.setName('P2PServer')
        asyncore.dispatcher.__init__(self, map=map)
        self.p2p_state = p2p_state
        self.map = map
        self.pool = pool
        self.handlers = set()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.dying = False
        self.sync_engine = sync_engine
        port = dropbox_url_info.p2p_port
        fail = True
        while fail:
            if port - dropbox_url_info.p2p_port > 100:
                break
            try:
                self.bind(('', port))
            except Exception:
                port += 1
            else:
                fail = False
                dropbox_url_info.p2p_port = port
                self.listen(150)
                self.TRACE('Now listening on P2P Port %d' % port)
                self.pool.registerServer(self)

        self.cryptodata = CryptoData(force_tlsv1=_FORCE_TLSv1)

    def want_die(self):
        self.dying = True

    def check_death(self):
        if self.dying:
            self.TRACE('dying as per request.')
            self.pool.server = None
            self.dying = False
            self.close()
            for handler in self.handlers:
                handler.close()

            return True
        else:
            return False

    def handle_error(self):
        unhandled_exc_handler()
        self.handle_close()

    def handle_accept(self):
        conn, addrport = self.accept()
        ips = list(arch.util.generate_ipaddresses())
        try:
            assert ips, 'Generate addresses is failing?'
        except Exception:
            unhandled_exc_handler()
        else:
            try:
                assert is_in_local_network(addrport[0], ips)
            except Exception:
                TRACE('is_in_local_network fails for %s and %s' % (addrport[0], ips))
                unhandled_exc_handler()
                conn.close()
                return

        csock = self.cryptodata.tradeSockForCryptoSock(conn)
        self.TRACE('Connection from %s' % (addrport,))
        handler = P2PServerHandler(csock, addrport, self, self.p2p_state, map=self.map, pool=self.pool, oldsock=conn)

    def handle_close(self):
        self.close()

    def handle_read(self):
        pass

    def handle_write(self):
        pass

    def handle_connect(self):
        pass

    def writable(self):
        return 0

    def readable(self):
        return self.accepting

    def pulse(self):
        for handler in list(self.handlers):
            handler.pulse()

    def registerHandler(self, handler):
        self.handlers.add(handler)

    def unregisterHandler(self, handler):
        try:
            self.handlers.remove(handler)
        except Exception:
            pass


class P2PServerHandler(IntProtocol, MyTrace):

    def __init__(self, conn, addr, server, p2p_state, map = None, pool = None, oldsock = None):
        IntProtocol.__init__(self, sock=oldsock, map=map)
        self.p2p_state = p2p_state
        self.pool = pool
        self.csock = conn
        self.addr = addr
        self.setName('P2PServerHandler (%s)' % (self.addr,))
        self.server = server
        self.handshaked = False
        self.targetNS = None
        self.accepted = False
        self.connectedCert = None
        self.closed = False
        now = time.time()
        self.lastAnswer = now
        self.server.registerHandler(self)

    def handle_read(self):
        if not self.accepted:
            self.TRACE('TRYING TO SSL ACCEPT.')
            try:
                self.csock.accept()
            except POW.SSLWantError:
                return
            except Exception as e:
                unhandled_exc_handler()
                self.TRACE('accept error %s' % (e,))
                self.handle_close()

            verify_result = self.csock.getVerifyResult()
            self.TRACE('ssl verify result is %s' % (verify_result,))
            if verify_result != 18:
                try:
                    raise SSLVerifyFailed('Unexpected getVerifyResult return value: %d' % (verify_result,))
                except Exception:
                    self.handle_close()
                    unhandled_exc_handler()

                return
            try:
                clientCert = self.csock.peerCertificate()
                certPEM = clientCert.pemWrite()
                targetNSList = [ (ns, cert) for ns, (cert, pk, md) in self.p2p_state.ns_p2p_key_map().iteritems() if certPEM == cert ]
                if not targetNSList:
                    raise WrongCertException("got cert %s, i don't belong to namespace" % (certPEM,))
                self.connectedCert = targetNSList[0]
                self.targetNS = targetNSList[0][0]
            except Exception:
                self.TRACE('Problems with verifying the peer certificate.')
                self.handle_close()
                unhandled_exc_handler()
                return

            self.accepted = True
            self.setName('P2PServerHandler (%s/%d)' % (self.addr, self.targetNS))
            self.TRACE('ACCEPTED PEER')
            return
        try:
            self.doHandle()
        except Exception:
            self.handle_close()
            unhandled_exc_handler()
            raise

    def getData(self):
        pass

    def doHandle(self):
        try:
            data = self.csock.read(SSL_BUFSIZE)
            if len(data) < 1:
                self.TRACE('doHandle: no more data - connection closed')
                self.handle_close()
                return
            self.inbuf += data
        except POW.SSLWantError:
            return
        except Exception as e:
            unhandled_exc_handler()
            myerrno = -1
            try:
                myerrno = ctypes.get_errno()
            except Exception:
                pass

            self.TRACE('doHandle: recv error (e.g connection closed) %s - errno: %d' % (e, myerrno))
            self.handle_close()
            return

        if len(self.inbuf) < 1:
            self.TRACE('doHandle: empty inbuf, closing connection')
            self.handle_close()
            return
        self.intprocess()
        self.processCommands()

    def processCommands(self):
        if not self.cmdbuf:
            try:
                raise Exception('Empty command set - int protocol broken?')
            except Exception:
                unhandled_exc_handler()

        while self.cmdbuf:
            now = time.time()
            self.lastAnswer = now
            cmd = self.cmdbuf.pop(0)
            cmd = json.loads(cmd)
            if not self.handshaked:
                if cmd[0] == 'HELLO':
                    self.TRACE('Server received HELLO %s' % (cmd[1],))
                    if not (cmd[1][0] == self.pool.version[0] and cmd[1][1] == self.pool.version[1]):
                        self.TRACE('PROTOCOL VERSION DIFFERS - DISCONNECTING')
                        self.handle_close()
                        return
                    self.handshaked = cmd[1]
                    self.intsend('HOWDY', self.pool.version)
                continue
            if cmd[0] == 'HAS':
                hval = cmd[1]
                dohave = bool(self.server.sync_engine.dropbox_have_locally(hval, ns=self.targetNS))
                self.TRACE('replying to HAS %s %s!' % (hval, dohave))
                self.intsend('HASREPLY', hval, dohave)
            elif cmd[0] == 'GET':
                hval = cmd[1]
                self.TRACE('GET request for %s' % (hval,))
                dohave = self.server.sync_engine.dropbox_have_locally(hval, ns=self.targetNS)
                fail = False
                if not dohave:
                    fail = True
                else:
                    try:
                        data = self.server.sync_engine.dropbox_contents(hval, ns=self.targetNS)
                    except Exception as e:
                        self.TRACE('Getting or decompressing failed: %s %s' % (hval, e))
                        fail = True
                        unhandled_exc_handler()

                if not fail:
                    self.TRACE('replying to GET with data! (%s)' % (hval,))
                    self.intsend('GETREPLY', hval)
                    self.intsend(data, raw=True)
                else:
                    self.TRACE('Unable to handle GET Request: %s' % (hval,))
                    self.intsend('GETFAIL', hval)
            elif cmd[0] == 'PING':
                self.intsend('PONG')
            else:
                self.TRACE('Received unknown command %s' % (cmd,))

    def handle_write(self):
        if self.override:
            self.TRACE('override mode')
            self.override = False
            self.handle_read()
            return
        totalsent = 0
        try:
            while len(self.outbuf) > 0:
                block = self.outbuf.getoutputpart(SSL_BUFSIZE)
                if len(block) > 0:
                    sent = self.csock.write(str(block))
                    try:
                        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                    except Exception:
                        unhandled_exc_handler()

                    self.outbuf.consume(sent)
                    totalsent += sent
                if len(block) - sent > 0:
                    self.TRACE('COULDNT SEND ALL DATA!!!')

        except POW.SSLWantError as e:
            return
        except Exception as e:
            self.TRACE('Write Exception: %s' % (e,))
            self.handle_close()
            unhandled_exc_handler()
            return

        if len(self.outbuf) > 0:
            self.TRACE('server write buffer full? - sent less than in outbuf')

    def writable(self):
        return not self.closed and (len(self.outbuf) > 0 or self.override)

    def readable(self):
        return not self.closed

    def handle_expt(self):
        myerrno = ctypes.get_errno()
        try:
            raise Exception('expt exception in p2p server %d' % (myerrno,))
        except Exception:
            unhandled_exc_handler()

        self.handle_close()

    def handle_close(self):
        self.TRACE('closing connection and resetting state.')
        self.server.unregisterHandler(self)
        self.accepted = False
        self.close()
        self.closed = True

    def pulse(self):
        now = time.time()
        try:
            if self.connectedCert:
                outside_certtup = self.p2p_state.ns_p2p_key_map().get(self.connectedCert[0])
                if not outside_certtup or self.connectedCert[1] != outside_certtup[0]:
                    self.TRACE('CERT Changed for namespace %d - kicking client!' % self.connectedCert[0])
                    self.handle_close()
        except Exception:
            unhandled_exc_handler()

        if now - self.lastAnswer > 120:
            self.TRACE('Connection timed out. Closing.')
            self.handle_close()


class P2PClient(IntProtocol, MyTrace):

    def __init__(self, host_int, ip, port, namespace, p2p_state, map = None, pool = None):
        self.namespace = namespace
        self.pool = pool
        self.host_int = host_int
        self.p2p_state = p2p_state
        self.map = map
        self.ip = ip
        self.port = port
        self.closed = False
        self.callback = None
        IntProtocol.__init__(self, map=map)
        self.startedConnecting = False
        self.creationTime = time.time()
        self.rawGET = None
        self.receiving_get_reply = False
        self.connectedCert = None

    def __str__(self):
        return self.name

    def dieAndBlacklistFor(self, seconds):
        self.TRACE('Blacklisting and disconnecting: %s' % (self,))
        self.pool.blacklistClientFor(self, seconds)
        self.handle_close()

    def startConnecting(self):
        assert not self.startedConnecting
        self.startedConnecting = True
        self.setName('P2PClient (%s:%d/%d, %d)' % (self.ip,
         self.port,
         self.namespace,
         self.host_int))
        self.TRACE('Connecting to %s' % (self.host_int,))
        try:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((self.ip, self.port))
        except Exception:
            unhandled_exc_handler()
            self.handle_close()
            return

        all_certs = self.p2p_state.ns_p2p_key_map()
        try:
            self.connectedCert = all_certs.get(self.namespace)
        except Exception:
            unhandled_exc_handler()
            self.connectedCert = None

        if not self.connectedCert:
            try:
                TRACE('!! No certdata for namespace: %r, %r', self.namespace, all_certs.keys())
            except Exception:
                unhandled_exc_handler()

            self.handle_close()
            return
        self.cryptodata = CryptoData(privPEM=self.connectedCert[1], certPEM=self.connectedCert[0], force_tlsv1=_FORCE_TLSv1)
        self.t_start = time.time()
        self.rly_connected = False
        self.handshaked = False
        self.csock = None
        self.closed = False
        self.rawGET = False
        self.lastRead = 0
        now = time.time()
        self.lastAnswer = now
        self.lastPing = now

    def requestHash(self, targetHash, cb):
        self.callback = cb
        if self.handshaked:
            self.intsend('HAS', targetHash)
        else:
            self.pool.notify(self, ('HASREPLY', targetHash, False))

    def getHash(self, _hash):
        self.intsend('GET', _hash)
        self.receiving_get_reply = True
        self.hashTotal = 0
        self.readStart = self.hashStart = time.time()
        self.waitingBytes = 0

    def getData(self):
        pass

    def handle_connect(self):
        try:
            if not self.csock:
                self.csock = self.cryptodata.tradeSockForCryptoSock(self.socket)
            self.csock.connect()
        except POW.SSLWantError:
            return
        except Exception:
            unhandled_exc_handler()
            raise

        self.TRACE('Connected!')
        self.setName('P2PClient+ (%s:%d/%d, %d)' % (self.ip,
         self.port,
         self.namespace,
         self.host_int))
        self.rly_connected = True
        self.intsend('HELLO', self.pool.version)

    def handle_close(self):
        try:
            self.pool.currently_connecting_for_ns[self.namespace].remove(self)
        except Exception:
            pass

        if self.closed:
            pass
        else:
            self.TRACE('client died (handle_close)')
            self.pool.clientDied(self)
            self.closed = True
            self.close()

    def handle_read(self):
        if not self.rly_connected:
            self.handle_connect()
            return
        allReplies = 0
        try:
            reply = None
            while True:
                reply = self.csock.read(SSL_BUFSIZE)
                if len(reply) == 0:
                    self.TRACE('client connection lost?')
                    self.handle_close()
                    return
                self.lastRead = time.time()
                allReplies += len(reply)
                self.inbuf += reply

        except POW.SSLWantError as e:
            if not len(self.inbuf):
                return
        except POW.SSLError as e:
            myerrno = ctypes.get_errno()
            self.TRACE('client connection lost exception %s - errno: %d' % (str(e), myerrno))
            raise

        if self.callback and self.receiving_get_reply:
            took = time.time() - self.readStart
            self.hashTotal += allReplies
            self.waitingBytes += allReplies
            if took >= 0.001:
                self.callback(self.waitingBytes, took)
                self.waitingBytes = 0
        self.intprocess()
        self.processCommands()

    def processCommands(self):
        while self.cmdbuf:
            now = time.time()
            self.lastAnswer = now
            if not self.handshaked:
                cmd = json.loads(self.cmdbuf.pop(0))
                if cmd[0] == 'HOWDY':
                    if not (cmd[1][0] == self.pool.version[0] and cmd[1][1] == self.pool.version[1]):
                        self.TRACE('PROTOCOL VERSION DIFFERS - DISCONNECTING')
                        self.handle_close()
                        return
                    self.setName('P2PClient! (%s:%d/%d, %d)' % (self.ip,
                     self.port,
                     self.namespace,
                     self.host_int))
                    self.TRACE('HANDSHAKE COMPLETE %s' % (cmd[1],))
                    self.handshaked = cmd[1]
                    self.pool.newConn(self)
                continue
            if not self.rawGET:
                cmd = json.loads(self.cmdbuf.pop(0))
            else:
                data = self.cmdbuf.pop(0)
                cmd = list(self.rawGET)
                cmd.append(data)
                self.rawGET = None
                self.receiving_get_reply = False
                curtime = time.time()
                if self.callback and self.waitingBytes:
                    self.callback(self.waitingBytes, curtime - self.readStart)
                timeTotal = curtime - self.hashStart
                self.pool.notify(self, cmd)
                return
            if cmd[0] == 'GETREPLY':
                self.rawGET = cmd
            elif cmd[0] == 'HASREPLY':
                self.pool.notify(self, cmd)
            elif cmd[0] == 'PONG':
                pass
            else:
                self.TRACE('unknown command: %s' % (cmd,))

        return False

    def readable(self):
        if self.receiving_get_reply and not self.waitingBytes:
            self.readStart = time.time()
        return self.connected and not self.closed

    def writable(self):
        return not self.closed and (self.override or not self.connected or len(self.outbuf) > 0 and self.rly_connected)

    def handle_write(self):
        if self.override:
            self.override = False
            self.handle_read()
            return
        if not self.rly_connected:
            return
        try:
            d = self.outbuf.getbuf(SSL_BUFSIZE, keep=True)
            sent = self.csock.write(d)
            try:
                self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                unhandled_exc_handler()

            ridof = self.outbuf.getbuf(sent)
        except POW.SSLWantError:
            return
        except Exception:
            unhandled_exc_handler()
            self.handle_close()

        if len(self.outbuf) > 0:
            self.TRACE('write data left in client outbuf - socket buffer full?')

    def handle_expt(self):
        myerrno = ctypes.get_errno()
        TRACE('expt exception in p2p client %d' % (myerrno,))
        self.handle_close()

    def pulse(self):
        now = time.time()
        try:
            try:
                cur_cert = self.p2p_state.ns_p2p_key_map().get(self.namespace)
            except Exception:
                unhandled_exc_handler()
                cur_cert = None

            if cur_cert != self.connectedCert:
                self.TRACE('CERT Changed for namespace %d - kicking client!' % self.namespace)
                self.handle_close()
                return
        except Exception:
            unhandled_exc_handler()

        if self.handshaked and now - self.lastAnswer >= PINGINTERVAL and now - self.lastPing >= PINGINTERVAL:
            self.lastPing = now
            self.intsend('PING')
        if now - self.lastAnswer > PINGTIMEOUT:
            try:
                raise ConnTimeoutException('Peer %s timed out!' % (self.host_int,))
            except Exception:
                unhandled_exc_handler()

            self.handle_close()
        if self.rawGET and now - self.lastRead >= NOREADTIMEOUT:
            try:
                raise StalledReadException('Trying to get data but none arrived in %f seconds.' % (now - self.lastRead,))
            except Exception:
                unhandled_exc_handler()

            self.handle_close()
            tmp = list(self.rawGET)
            tmp[0] = 'GETFAIL'
            self.pool.notify(self, tmp)
