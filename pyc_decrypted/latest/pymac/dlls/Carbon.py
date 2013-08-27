#Embedded file name: pymac/dlls/Carbon.py
from __future__ import absolute_import
from ctypes import POINTER
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework
from ..types import CFStringRef, ICACompletion, ICACopyObjectDataPB, ICACopyObjectPropertyDictionaryPB, ICADownloadFilePB, ICAError, ICAGetDeviceListPB, OSErr, ProcessSerialNumber
from .CoreServices import OSStatusCheck

class LazyCarbon(LazyFramework):

    def __init__(self):
        super(LazyCarbon, self).__init__()
        self._dllname = u'Carbon'
        self._func_defs = {}

        def F(name, ret = None, args = [], errcheck = OSStatusCheck):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args,
             'errcheck': errcheck}

        def C(name, const_type):
            self._const_defs[name] = const_type

        F('ICACopyObjectPropertyDictionary', ICAError, [POINTER(ICACopyObjectPropertyDictionaryPB), ICACompletion])
        F('ICADownloadFile', ICAError, [POINTER(ICADownloadFilePB), ICACompletion])
        F('ICACopyObjectData', ICAError, [POINTER(ICACopyObjectDataPB), ICACompletion])
        F('ICAGetDeviceList', ICAError, [POINTER(ICAGetDeviceListPB), ICACompletion])
        C('kICANotificationTypeObjectAdded', CFStringRef)
        C('kICANotificationTypeObjectRemoved', CFStringRef)
        C('kICANotificationTypeObjectInfoChanged', CFStringRef)
        C('kICANotificationTypeDeviceAdded', CFStringRef)
        C('kICANotificationTypeDeviceRemoved', CFStringRef)
        C('kICANotificationTypeDeviceInfoChanged', CFStringRef)
        C('kICANotificationTypeStoreAdded', CFStringRef)
        C('kICANotificationTypeStoreRemoved', CFStringRef)
        C('kICANotificationTypeDeviceConnectionProgress', CFStringRef)
        F('GetCurrentProcess', OSErr, [POINTER(ProcessSerialNumber)])


Carbon = FakeDLL(LazyCarbon)
