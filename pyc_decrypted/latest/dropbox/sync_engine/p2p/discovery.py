#Embedded file name: dropbox/sync_engine/p2p/discovery.py
from __future__ import absolute_import
import traceback
import select
import socket
import time
import json
import errno
import arch
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.globals import dropbox_globals
from dropbox.network import is_in_local_network
from dropbox.url_info import dropbox_url_info
MSG_MAX_SEND_SIZE = 512
MSG_MAX_RECV_SIZE = 65536

class DiscoveryEngine(object):
    announcement_interval = 30.0

    def __init__(self):
        self._bind_addr = ('', dropbox_url_info.discovery_port)
        self._socket = self._init_socket(self._bind_addr)
        self._announcement_data = None
        self._next_announcement_time = 0.0
        self._subscribers = set()

    def set_announcement_data(self, version, port, host_int, namespaces_callback):
        assert isinstance(version, tuple) and len(version) == 2, 'version should be a 2-tuple; was: %r' % (version,)
        assert isinstance(host_int, (int, long)), 'host_int should be an integer; was: %r' % (host_int,)
        assert isinstance(port, int), 'port should be an integer; was: %r' % (port,)
        assert callable(namespaces_callback), 'namespaces_callback should be callable; was: %r' % (namespaces_callback,)
        self._announcement_data = dict(version=version, port=port, host_int=host_int)
        self._namespaces_callback = namespaces_callback
        TRACE('Discovery: Registered %r -> %r', self._announcement_data, self._namespaces_callback)
        self._announcement_data['displayname'] = ''

    def subscribe(self, callback):
        assert callable(callback), 'callback should be callable; was: %r' % (callback,)
        self._subscribers.add(callback)

    def pulse(self):
        now = get_monotonic_time_seconds()
        if now >= self._next_announcement_time:
            self._next_announcement_time = now + self.announcement_interval
            self._announce()
        self._handle_incoming_announcements()

    def _announce(self):
        self._announcement_data['namespaces'] = list((int(ns) for ns in self._namespaces_callback()))
        raw_msgs = self._encode_announcement(self._announcement_data)
        for raw_msg in raw_msgs:
            self._do_broadcast(raw_msg, dropbox_url_info.discovery_port)

        self._last_announcement_monotonic_time = get_monotonic_time_seconds()

    def _do_broadcast(self, raw_msg, port):
        try:
            self._socket.sendto(raw_msg, 0, ('<broadcast>', port))
        except:
            TRACE('failed to broadcast send to port %d' % (port,))
            unhandled_exc_handler()

        try:
            for addrdata in arch.util.generate_ipaddresses():
                baddr = addrdata.get('broadcast')
                if not baddr:
                    continue
                try:
                    self._socket.sendto(raw_msg, 0, (baddr, port))
                except Exception as e:
                    if isinstance(e, OSError) and e.errno == errno.EDESTADDRREQ:
                        TRACE('socket.sendto failed with EDESTADDRREQ addrdata=%r', addrdata)
                    else:
                        TRACE('failed to send to baddr %s port %d' % (baddr, port))
                        unhandled_exc_handler()

        except:
            unhandled_exc_handler()

    def _handle_incoming_announcements(self):
        while True:
            rlist = select.select((self._socket,), (), (), 0)[0]
            if self._socket not in rlist:
                break
            try:
                raw_msg, remote_addr = self._socket.recvfrom(MSG_MAX_RECV_SIZE)
            except:
                unhandled_exc_handler()
                report_bad_assumption('DiscoveryEngine.socket.recvfrom raised an exception - please notify dlitz')
                try:
                    self._socket.close()
                except:
                    unhandled_exc_handler()
                    report_bad_assumption('socket.close() failed after DiscoveryEngine.socket.recvfrom raised an exception - please notify dlitz')

                self._socket = self._init_socket(self._bind_addr)
                break

            ips = list(arch.util.generate_ipaddresses())
            if remote_addr is None:
                TRACE('recvfrom returned None as remote_addr, ips:%r', ips)
                continue
            if not ips:
                report_bad_assumption("generate_ipaddresses() didn't return anything - please notify dlitz")
            elif not is_in_local_network(remote_addr[0], ips):
                TRACE('is_in_local_network fails for %s and %s', remote_addr[0], ips)
                continue
            try:
                msg = self._parse_announcement(raw_msg)
            except:
                TRACE("can't parse received datagram - ignoring")
                unhandled_exc_handler()
                continue

            msg['updated'] = time.time()
            msg['recv_addr'] = remote_addr[0]
            for sub in list(self._subscribers):
                try:
                    sub(msg)
                except:
                    unhandled_exc_handler()

    def _parse_announcement(self, raw_msg):
        data = json.loads(raw_msg)
        if not isinstance(data, dict):
            raise TypeError('cannot parse: not a dict')
        msg = {}
        if 'host_int' in data:
            msg['host_int'] = int(data['host_int'])
        if 'port' in data:
            msg['port'] = int(data['port'])
        if 'version' in data:
            msg['version'] = tuple((int(x) for x in data['version']))
        if 'namespaces' in data:
            msg['namespaces'] = list((int(x) for x in data['namespaces']))
        return msg

    @staticmethod
    def _encode_announcement(out):
        candidates = [out]
        while candidates:
            candidate = candidates.pop()
            raw_msg = json.dumps(candidate)
            if len(raw_msg) <= MSG_MAX_SEND_SIZE:
                yield raw_msg
            else:
                n = len(candidate['namespaces'])
                assert n > 1, 'message was too long, even with only 1 namespace remaining'
                left = dict(candidate, namespaces=candidate['namespaces'][n // 2:])
                right = dict(candidate, namespaces=candidate['namespaces'][:n // 2])
                candidates.extend([left, right])

    def _init_socket(self, bind_addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            pass

        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except:
            pass

        try:
            s.bind(bind_addr)
        except:
            unhandled_exc_handler()
            report_bad_assumption('P2P UDP bind() failed.  please notify dlitz')

        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return s
