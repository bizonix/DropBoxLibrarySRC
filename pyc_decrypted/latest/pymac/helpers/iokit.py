#Embedded file name: pymac/helpers/iokit.py
from __future__ import absolute_import
from ctypes import byref
from re import compile as re_compile
from ..dlls import Core, IOKit
from ..constants import kCFAllocatorDefault, kIOPlatformSerialNumberKey, kIOMasterPortDefault, kNilOptions
from .core import CFString, CFDictionary, releasing

def get_serial_number():
    service = IOKit.IOServiceGetMatchingService(None, IOKit.IOServiceMatching('IOPlatformExpertDevice'))
    if not service:
        raise Exception('Unable to get Expert Device Service')
    try:
        a = CFString.from_python(kIOPlatformSerialNumberKey)
        with releasing(IOKit.IORegistryEntryCreateCFProperty(service, a.get_ref(), kCFAllocatorDefault, 0)) as serial_number:
            if not serial_number:
                raise Exception('Serial Number not found')
            return CFString.to_unicode(serial_number)
    finally:
        IOKit.IOObjectRelease(service)


def get_property_dict_from_path(path):
    service = IOKit.IORegistryEntryFromPath(kIOMasterPortDefault, path)
    if not service:
        raise Exception('Unable to find service %r' % path)
    try:
        properties = Core.CFDictionaryCreate(kCFAllocatorDefault, None, None, 0, None, None)
        IOKit.IORegistryEntryCreateCFProperties(service, byref(properties), kCFAllocatorDefault, kNilOptions)
        return CFDictionary(properties, take_ownership=True)
    except Exception:
        if properties:
            Core.CFRelease(properties)
        return
    finally:
        IOKit.IOObjectRelease(service)


find_usb_regex = re_compile('(.*/AppleUSB(E|O)HCI/.*?)/')

def find_usb_device_path(ioregpath):
    res = find_usb_regex.match(ioregpath)
    if res:
        return res.group(1)
    else:
        return None
