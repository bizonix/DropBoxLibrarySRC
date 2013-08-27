#Embedded file name: arch/mac/proxy_watch.py
from __future__ import absolute_import
from ctypes import byref, c_void_p
from dropbox.gui import event_handler
from dropbox.trace import TRACE
from pymac.dlls import Core, SystemConfiguration
from pymac.helpers.core import CFString, releasing
from pymac.types import SCDynamicStoreCallback, SCDynamicStoreContext

class ProxyWatch(object):

    def on_proxy_change(self, store, changedKeys, info):
        if self.callback:
            self.callback()

    def __init__(self):
        self.loop_mode = Core.kCFRunLoopDefaultMode
        self.registry_name = CFString.from_python(u'Dropbox')
        self.local_callback = SCDynamicStoreCallback(self.on_proxy_change)
        self.callback = self.systemDynamicStore = None

    def register_callback(self, function):
        self.callback = function

    @event_handler
    def setup_callback(self):
        context = SCDynamicStoreContext()
        context.version = 0
        context.info = context.retain = context.release = context.copyDescription = None
        self.systemDynamicStore = SystemConfiguration.SCDynamicStoreCreate(None, self.registry_name.get_ref(), self.local_callback, byref(context))
        with releasing(SystemConfiguration.SCDynamicStoreKeyCreateProxies(None)) as proxiesKey:
            with releasing(Core.CFArrayCreate(None, c_void_p(proxiesKey), 1, None)) as keyArray:
                SystemConfiguration.SCDynamicStoreSetNotificationKeys(self.systemDynamicStore, keyArray, None)
        with releasing(SystemConfiguration.SCDynamicStoreCreateRunLoopSource(None, self.systemDynamicStore, 0)) as storeRLSource:
            Core.CFRunLoopAddSource(Core.CFRunLoopGetCurrent(), storeRLSource, self.loop_mode)
        TRACE('ProxyWatch Callback Setup for OSX')

    def teardown_callback(self):
        self.callback = None
        if self.systemDynamicStore:
            with SystemConfiguration.SCDynamicStoreCreateRunLoopSource(None, self.systemDynamicStore, 0) as rls:
                Core.CFRunLoopSourceInvalidate(rls)
            Core.CFRelease(self.systemDynamicStore)
        TRACE('ProxyWatch Callback Tore Down for OSX')
