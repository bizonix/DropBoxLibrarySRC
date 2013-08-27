#Embedded file name: ui/cocoa/xui/__init__.py
import objc
from AppKit import NSURL, NSUserDefaults
from Foundation import NSObject, NSMakePoint
from Cocoa import NSBundle, NSEvent, NSFont, NSLeftMouseDown, NSMenu, NSPointInRect, NSTrackingArea, NSTrackingMouseEnteredAndExited, NSTrackingMouseMoved, NSTrackingActiveAlways
from PyObjCTools import AppHelper
from WebKit import WebCacheModelDocumentViewer, WebDragDestinationActionNone, WebDragSourceActionNone, WebView
import build_number
from dropbox.event import report
from dropbox.functions import handle_exceptions
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.mac.version import MAC_VERSION, MOUNTAIN_LION, SNOW_LEOPARD
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from ui.cocoa.dropbox_menu import DropboxNSMenu
from ui.cocoa.util import CocoaSettings
from ui.cocoa.xui.javascript import inject_object, register_global_context, unregister_global_context
from ui.common.xui import XUIHost, XUIJavaScriptError
import ctypes.macholib.dyld
import os.path

@handle_exceptions
def report_webkit_version():
    path = ctypes.macholib.dyld.framework_find('JavaScriptCore')
    if not path:
        return
    bundle = NSBundle.bundleWithPath_(os.path.dirname(path))
    if bundle is None:
        return
    version = bundle.infoDictionary()['CFBundleVersion']
    report('webkit-version', version=version)


class WebViewDelegate(NSObject):

    def initWithHost_(self, host):
        self = super(WebViewDelegate, self).init()
        if self is None:
            return
        self.host = host
        self.globalContext = None
        return self

    @event_handler
    def dealloc(self):
        if self.globalContext is not None:
            unregister_global_context(self.globalContext)
            self.globalContext = None
        super(WebViewDelegate, self).dealloc()

    @objc.typedSelector('v@:@@@')
    @event_handler
    def webView_didClearWindowObject_forFrame_(self, sender, wso, frame):
        TRACE('Established JavaScript context for frame: %r', frame)
        try:
            if self.globalContext is not None:
                unregister_global_context(self.globalContext)
                self.globalContext = None
            self.globalContext = frame.globalContext().pointerAsInteger
            register_global_context(self.globalContext)
            inject_object(self.globalContext, self.host.controller._OBJECT_NAME, self.host.controller)
        except Exception:
            self.host.failed = True
            unhandled_exc_handler()

    @event_handler
    def webView_didFinishLoadForFrame_(self, sender, frame):
        TRACE('Finished loading frame: %r', frame)
        if not CocoaSettings.is_accelerated_compositing_supported():
            try:
                self.host.setCSSAnimationsSuspended_(objc.YES)
            except AttributeError:
                pass
            except Exception:
                unhandled_exc_handler()

    @event_handler
    def webView_didFailProvisionalLoadWithError_forFrame_(self, sender, error, frame):
        _message = 'Failed to load before committed, host failing: %r' % unicode(error)
        report_bad_assumption(_message)
        self.host.failed = True

    @event_handler
    def webView_didFailLoadWithError_forFrame_(self, sender, error, frame):
        _message = 'Failed to load before committed, host failing: %r' % unicode(error)
        report_bad_assumption(_message)
        self.host.failed = True

    @objc.typedSelector('v@:@@')
    @event_handler
    def webView_addMessageToConsole_(self, sender, message, *args):
        if message is None:
            return
        if 'MessageLevel' in message and 'MessageSource' in message:
            level = message.get('MessageLevel')
            if level != 'ErrorMessageLevel':
                return
            source = message.get('MessageSource')
            if source != 'JSMessageSource':
                return
        TRACE('!! Host failing due to uncaught JavaScript error.')
        self.failed = True
        raise XUIJavaScriptError(repr((message,) + args))

    @event_handler
    def webView_dragDestinationActionMaskForDraggingInfo_(self, sender, draggingInfo):
        return WebDragDestinationActionNone

    @event_handler
    def webView_dragSourceActionMaskForPoint_(self, sender, point):
        return WebDragSourceActionNone

    @event_handler
    def webView_contextMenuItemsForElement_defaultMenuItems_(self, sender, element, defaultMenuItems):
        if not hasattr(build_number, 'frozen'):
            return defaultMenuItems

    @event_handler
    def webView_decidePolicyForNavigationAction_request_frame_decisionListener_(self, sender, actionInformation, request, frame, listener):
        if not request.URL().absoluteString().startswith('about:xui'):
            TRACE('!! Failing host after request to navigate to: %r', request)
            listener.ignore()
            self.host.failed = True
        else:
            listener.use()

    @event_handler
    def webView_decidePolicyForNewWindowAction_request_newFrameName_decisionListener_(self, sender, actionInformation, request, frameName, listener):
        TRACE('!! Disallowing a request to open window to: %r', request)
        listener.ignore()

    @event_handler
    def webView_decidePolicyForMIMEType_request_frame_decisionListener_(self, sender, mimeType, request, frame, listener):
        TRACE('!! Disallowing a request to navigate to mime type: %r at %r', mimeType, request)
        listener.ignore()


class WebViewXUIHost(WebView, XUIHost):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, frame, controller):
        return WebViewXUIHost.alloc().initWithFrame_controller_(frame, controller)

    def initWithFrame_controller_(self, frame, controller):
        self = WebView.initWithFrame_frameName_groupName_(self, frame, controller.__xui_resource__ + '_main', None)
        if self is None:
            return
        self.setMaintainsBackForwardList_(objc.NO)
        self.setEditable_(objc.NO)
        self.setPreferencesIdentifier_('DropboxXUI')
        preferences = self.preferences()
        preferences.setAutosaves_(objc.NO)
        preferences.setPlugInsEnabled_(objc.NO)
        preferences.setJavaEnabled_(objc.NO)
        preferences.setJavaScriptCanOpenWindowsAutomatically_(objc.NO)
        preferences.setUserStyleSheetEnabled_(objc.NO)
        preferences.setCacheModel_(WebCacheModelDocumentViewer)
        preferences.setTabsToLinks_(objc.YES)
        report_webkit_version()
        if MAC_VERSION >= MOUNTAIN_LION:
            try:
                preferences.setSuppressesIncrementalRendering_(objc.YES)
            except AttributeError:
                pass
            except Exception:
                unhandled_exc_handler()

        if MAC_VERSION >= SNOW_LEOPARD:
            try:
                preferences.setAcceleratedCompositingEnabled_(CocoaSettings.is_accelerated_compositing_supported())
            except AttributeError:
                pass
            except Exception:
                unhandled_exc_handler()

        XUIHost.__init__(self, controller)
        self.theDelegate = WebViewDelegate.alloc().initWithHost_(self)
        self.setFrameLoadDelegate_(self.theDelegate)
        self.setUIDelegate_(self.theDelegate)
        self.setPolicyDelegate_(self.theDelegate)
        self.mainFrame().frameView().setAllowsScrolling_(objc.NO)
        data = controller._get_view_data().encode('utf-8')
        self.mainFrame().loadHTMLString_baseURL_(data, NSURL.URLWithString_('about:xui'))
        self.mainTrackingArea = None
        return self

    def setupTrackingArea(self):
        options = NSTrackingMouseEnteredAndExited | NSTrackingMouseMoved | NSTrackingActiveAlways
        self.mainTrackingArea = None
        self.mainTrackingArea = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(self.bounds(), options, self, None)
        self.addTrackingArea_(self.mainTrackingArea)

    @event_handler
    def updateTrackingAreas(self):
        self.removeTrackingArea_(self.mainTrackingArea)
        self.setupTrackingArea()
        super(WebViewXUIHost, self).updateTrackingAreas()

    @event_handler
    def mouseEntered_(self, event):
        self.window().setAcceptsMouseMovedEvents_(objc.YES)

    @event_handler
    def mouseExited_(self, event):
        self.window().setAcceptsMouseMovedEvents_(objc.NO)

    @event_handler
    def acceptsFirstResponder(self):
        return objc.YES

    @objc.typedSelector('v@:@ll')
    @assert_message_queue
    def show_context(self, options, x, y):
        y = self.frame().size.height - y
        menu = DropboxNSMenu.menuWithDropboxMenuDescriptor_(options)
        if MAC_VERSION >= SNOW_LEOPARD:
            menu.popUpMenuPositioningItem_atLocation_inView_(None, NSMakePoint(x, y), self)
            return
        fake_event = NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(NSLeftMouseDown, NSMakePoint(x, y), 0, 0, self.window().windowNumber(), None, 0, 0, 0)
        NSMenu.popUpContextMenu_withEvent_forView_withFont_(menu, fake_event, self, NSFont.systemFontOfSize_(12.75))
