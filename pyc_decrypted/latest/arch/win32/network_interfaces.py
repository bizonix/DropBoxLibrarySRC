#Embedded file name: arch/win32/network_interfaces.py
import struct
import socket
import winerror
import win32api
from ctypes import Structure, windll, sizeof, POINTER, byref, c_ulong, c_uint, c_ubyte, c_char, c_char_p, create_string_buffer, addressof
from ctypes.wintypes import DWORD, BYTE, BOOL, ULONG
MAX_ADAPTER_DESCRIPTION_LENGTH = 128
MAX_ADAPTER_NAME_LENGTH = 256
MAX_ADAPTER_ADDRESS_LENGTH = 8

class IP_ADDR_STRING(Structure):
    pass


LP_IP_ADDR_STRING = POINTER(IP_ADDR_STRING)
IP_ADDR_STRING._fields_ = [('next', LP_IP_ADDR_STRING),
 ('ipAddress', c_char * 16),
 ('ipMask', c_char * 16),
 ('context', DWORD)]

class IP_ADAPTER_INFO(Structure):
    pass


LP_IP_ADAPTER_INFO = POINTER(IP_ADAPTER_INFO)
IP_ADAPTER_INFO._fields_ = [('next', LP_IP_ADAPTER_INFO),
 ('comboIndex', DWORD),
 ('adapterName', c_char * (MAX_ADAPTER_NAME_LENGTH + 4)),
 ('description', c_char * (MAX_ADAPTER_DESCRIPTION_LENGTH + 4)),
 ('addressLength', c_uint),
 ('address', BYTE * MAX_ADAPTER_ADDRESS_LENGTH),
 ('index', DWORD),
 ('type', c_uint),
 ('dhcpEnabled', c_uint),
 ('currentIpAddress', LP_IP_ADDR_STRING),
 ('ipAddressList', IP_ADDR_STRING),
 ('gatewayList', IP_ADDR_STRING),
 ('dhcpServer', IP_ADDR_STRING),
 ('haveWins', BOOL),
 ('primaryWinsServer', IP_ADDR_STRING),
 ('secondaryWinsServer', IP_ADDR_STRING),
 ('leaseObtained', c_ulong),
 ('leaseExpires', c_ulong)]
_GetAdaptersInfo = windll.iphlpapi.GetAdaptersInfo
_GetAdaptersInfo.restype = DWORD
_GetAdaptersInfo.argtypes = [c_char_p, POINTER(ULONG)]

def string_for_relevant_error(rc):
    for e in ('ERROR_INVALID_DATA', 'ERROR_INVALID_PARAMETER', 'ERROR_NO_DATA', 'ERROR_NOT_SUPPORTED'):
        if rc == getattr(winerror, e):
            return e

    return win32api.FormatMessage(rc)


def GetAdaptersInfo():
    adapterInfo = create_string_buffer(sizeof(IP_ADAPTER_INFO))
    buflen = ULONG(sizeof(adapterInfo))
    rc = _GetAdaptersInfo(adapterInfo, byref(buflen))
    assert rc in (winerror.ERROR_SUCCESS, winerror.ERROR_BUFFER_OVERFLOW), '_GetAdaptersInfo failed! --> %d (%s)' % (rc, string_for_relevant_error(rc))
    i = 0
    while rc == winerror.ERROR_BUFFER_OVERFLOW and i < 5:
        adapterInfo = create_string_buffer(buflen.value)
        rc = _GetAdaptersInfo(adapterInfo, byref(buflen))
        i += 1

    assert rc == winerror.ERROR_SUCCESS, '_GetAdaptersInfo failed! --> %d (%s)' % (rc, string_for_relevant_error(rc))
    return adapterInfo


def generate_adapter_info():
    try:
        adapterInfoBuf = GetAdaptersInfo()
    except:
        from dropbox.trace import unhandled_exc_handler
        unhandled_exc_handler()
        raise StopIteration
    else:
        if sizeof(adapterInfoBuf) < sizeof(IP_ADAPTER_INFO):
            raise StopIteration
        adapterInfo = IP_ADAPTER_INFO.from_address(addressof(adapterInfoBuf))
        while adapterInfo:
            yield adapterInfo
            if adapterInfo.next:
                adapterInfo = adapterInfo.next.contents
            else:
                adapterInfo = None


def generate_ipaddresses():
    for adapterInfo in generate_adapter_info():
        adNode = adapterInfo.ipAddressList
        while adNode:
            ipAddr = {'addr': adNode.ipAddress,
             'netmask': adNode.ipMask}
            if ipAddr.get('addr') and ipAddr.get('netmask'):
                ipAddr['broadcast'] = socket.inet_ntoa(struct.pack('I', (struct.unpack('I', socket.inet_aton(ipAddr['addr']))[0] | ~struct.unpack('I', socket.inet_aton(ipAddr['netmask']))[0]) & 4294967295L))
                ipAddr['datasource'] = 'ctypeswrapper'
                yield ipAddr
            if adNode.next:
                adNode = adNode.next.contents
            else:
                adNode = None


if __name__ == '__main__':
    print list(generate_ipaddresses())
