#Embedded file name: pymac/helpers/interfaces.py
import ctypes
import socket
import sys
from ctypes import cast
from ctypes import pointer, POINTER, c_uint
from ..constants import IFF_BROADCAST
from ..dlls import libc
from ..types import sockaddr_in, sockaddr, ifaddrs

def get_socket_ip(sa):
    addr = None
    if sa and sa.contents:
        family = sa.contents.sa_family
        if family == socket.AF_INET:
            x = cast(sa, POINTER(sockaddr_in)).contents
            addr = socket.inet_ntop(family, x.sin_addr)
    return addr


def get_interface_data(ifaddr):
    if ifaddr.contents.ifa_addr is None:
        return
    addr = get_socket_ip(ifaddr.contents.ifa_addr)
    if addr is None:
        return
    netmask_addr = get_socket_ip(ifaddr.contents.ifa_netmask)
    interface_data = {'name': ifaddr.contents.ifa_name,
     'addr': addr,
     'netmask': netmask_addr}
    if ifaddr.contents.ifa_flags & IFF_BROADCAST:
        broadcast_addr = get_socket_ip(ifaddr.contents.ifa_dstaddr)
        interface_data['broadcast'] = broadcast_addr
    return interface_data


def generate_ipaddresses():
    addrlist = None
    try:
        addrlist = POINTER(ifaddrs)()
        libc.getifaddrs(ctypes.byref(addrlist))
        ifaddr = addrlist
        while ifaddr and ifaddr.contents:
            ipAddr = get_interface_data(ifaddr)
            if ipAddr is not None:
                yield ipAddr
            ifaddr = ifaddr.contents.ifa_next

    finally:
        if addrlist:
            libc.freeifaddrs(addrlist)
