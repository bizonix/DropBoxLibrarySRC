#Embedded file name: ui/cocoa/bubble.py
from __future__ import absolute_import
import threading
from Queue import Queue
import objc
from AppKit import NSAutoreleasePool, NSNumber, NSObject
from PyObjCTools import AppHelper
from build_number import BUILD_KEY
from dropbox.functions import handle_exceptions
from dropbox.gui import message_sender
from dropbox.mac.internal import get_frameworks_dir
from dropbox.mac.version import MAC_VERSION, MOUNTAIN_LION
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.cocoa.custom_bubble import BubbleWindowController

class Bubbler(object):

    def __init__(self, app):
        self._impl = None
        self._app = app

    @message_sender(AppHelper.callAfter, block=True)
    def init(self):
        bubblers = [DropboxGrowlBridge]
        if MAC_VERSION >= MOUNTAIN_LION:
            TRACE('Using NotificationCenter: (MAC_VERSION is %r)', MAC_VERSION)
            from ui.cocoa.notification_center import NotificationCenterBubbler
            bubblers.append(NotificationCenterBubbler)
        bubblers.append(BubbleWindowController)
        if not self._impl:
            for impl in bubblers:
                try:
                    TRACE('Bubbler init: Attempting to load %r', impl.__name__)
                    self._impl = impl(self._app)
                    TRACE('Bubbler init: %r loaded successfully', impl.__name__)
                    return
                except NotImplementedError:
                    TRACE('Bubbler init: %r load failed, trying next bubbler', impl.__name__)
                except Exception:
                    unhandled_exc_handler()

    def lazy_init(self):
        if self._impl:
            if not self._impl.still_running():
                TRACE('Previously loaded bubbler no longer running')
                self._impl = None
        if not self._impl:
            self.init()
        assert self._impl

    @handle_exceptions
    def render_bubble(self, bubble):
        assert bubble.has_no_ctxt_ref() or bubble.has_valid_ctxt_ref()
        self.lazy_init()
        self._impl.do_bubble(bubble.msg, bubble.caption, bubble.ctxt_ref)
        self._app.report_show_bubble(bubble)


class DropboxGrowlBridge(NSObject):

    def __new__(cls, app):
        return DropboxGrowlBridge.alloc().initWithApp_(app)

    def initWithApp_(self, app):
        self = super(DropboxGrowlBridge, self).init()
        if self is None:
            return
        self.app = app
        self.loaded_growl = threading.Event()
        self.growl_had_problems = True
        self.GrowlApplicationBridge = None
        self.growl_queue = Queue()
        self.load_growl()
        if self.growl_had_problems:
            TRACE('Growl load failed')
            raise NotImplementedError('Growl')
        return self

    def registrationDictionaryForGrowl(self):
        return {u'ApplicationName': unicode(BUILD_KEY),
         u'AllNotifications': [u'File Updates'],
         u'DefaultNotifications': [u'File Updates'],
         u'ApplicationId': unicode(BUILD_KEY)}

    def applicationNameForGrowl(self):
        return BUILD_KEY

    def growlNotificationWasClicked_(self, clickContextS):
        try:
            self.app.bubble_context.thunk_and_expire_context_ref(clickContextS)
        except Exception:
            unhandled_exc_handler()

    def growlNotificationTimedOut_(self, clickContextS):
        try:
            self.app.bubble_context.expire_context_ref(clickContextS)
        except Exception:
            unhandled_exc_handler()

    def still_running(self):
        return self.GrowlApplicationBridge.isGrowlRunning()

    def do_bubble(self, message, caption, ctx_ref):
        TRACE('DropboxGrowlBridge: Bubbling: %s', message)
        pool = NSAutoreleasePool.alloc().init()
        try:
            if ctx_ref is not None:
                ctx_ref = NSNumber.numberWithInt_(ctx_ref)
            self.GrowlApplicationBridge.notifyWithTitle_description_notificationName_iconData_priority_isSticky_clickContext_(unicode(caption), unicode(message), u'File Updates', None, 0, False, ctx_ref)
        finally:
            del pool

    def load_growl(self):
        if self.loaded_growl.isSet():
            return
        try:
            TRACE('Loading Growl...')
            pool = NSAutoreleasePool.alloc().init()
            if self.GrowlApplicationBridge is None:
                bundle_path = '%s/Growl.framework' % get_frameworks_dir()
                env = {}
                objc.loadBundle('GrowlApplicationBridge', env, bundle_path=bundle_path)
                self.GrowlApplicationBridge = env['GrowlApplicationBridge']
                installed = self.GrowlApplicationBridge.isGrowlInstalled()
                running = self.GrowlApplicationBridge.isGrowlRunning()
                TRACE('Growl is installed? %r; Growl is running? %r', installed, running)
            if running:
                TRACE('Initializing Growl Delegate')
                self.GrowlApplicationBridge.setGrowlDelegate_(self)
            else:
                return
        except Exception:
            unhandled_exc_handler()
            self.growl_had_problems = True
            TRACE('Growl had problems, tossing ability to notify out the window')
        else:
            self.growl_had_problems = False
            self.growlIsReady()

    def growlIsReady(self):
        TRACE('Growl is ready')
        self.loaded_growl.set()
        while not self.growl_queue.empty():
            self.do_bubble(*self.growl_queue.get())
