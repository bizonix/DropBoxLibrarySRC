#Embedded file name: dropbox/network.py
from __future__ import absolute_import
import socket
import struct
from dropbox.trace import unhandled_exc_handler, TRACE
ONESEVENTWOPARTS = [ str(x) for x in xrange(16, 32) ]

def is_in_local_network(addr, interfaces):
    targetaddrint = struct.unpack('I', socket.inet_aton(addr))[0]
    local = False
    for netdata in interfaces:
        try:
            netmask = netdata.get('netmask')
            if not netmask:
                if addr.startswith('192.168.'):
                    netmask = '255.255.0.0'
                if addr.startswith('10.'):
                    netmask = '255.0.0.0'
                if addr.startswith('169.254.'):
                    netmask = '255.255.0.0'
                if addr.startswith('172.'):
                    part = addr[4:6]
                    if part in ONESEVENTWOPARTS:
                        netmask = '255.240.0.0'
            if not (netmask and netdata.get('addr')):
                continue
            netmaskint = struct.unpack('I', socket.inet_aton(netmask))[0]
            netaddrint = struct.unpack('I', socket.inet_aton(netdata['addr']))[0]
            if netmaskint & netaddrint == netmaskint & targetaddrint:
                local = True
        except:
            unhandled_exc_handler()

    return local
