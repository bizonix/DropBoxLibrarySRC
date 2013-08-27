#Embedded file name: ui/cocoa/tray_popup.py
import objc
from AppKit import NSApplication, NSBackingStoreBuffered, NSBorderlessWindowMask, NSColor, NSHUDWindowMask, NSNonactivatingPanelMask, NSNotificationCenter, NSPanel, NSScreen, NSStatusWindowLevel, NSUtilityWindowMask, NSWindowCollectionBehaviorCanJoinAllSpaces
from Cocoa import NSEvent, NSMouseMoved, NSMakePoint
from Foundation import NSMakeRect, NSInsetRect, NSIntersectionRect, NSRect
from PyObjCTools import AppHelper
from WebKit import WebViewProgressFinishedNotification
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.mac.version import LION, MAC_VERSION, SNOW_LEOPARD
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.cocoa.util import screen_from_point, get_main_screen_rect
from ui.cocoa.xui import WebViewXUIHost

class TrayPopupView(WebViewXUIHost):
    SHADOW_MARGIN_SIZE = 20

    @objc.namedSelector('setHeight:', 'v@:l')
    @assert_message_queue
    def set_height(self, height):
        height += self.SHADOW_MARGIN_SIZE
        self.window().moveToAnchor_withHeight_(height=height)

    @objc.namedSelector('isVisible', signature='B@:')
    @assert_message_queue
    def is_visible(self):
        if not self.window():
            return False
        return self.window().isVisible()


class TrayPopupWindow(NSPanel):
    SCREEN_WIDTH = 350
    BASE_HEIGHT = 50
    SCREEN_SIZE = (SCREEN_WIDTH, BASE_HEIGHT)
    objc.synthesize('menuDelegate', copy=False)

    @assert_message_queue
    def init(self, app, controller):
        rect = NSRect((0, 0), self.SCREEN_SIZE)
        mask = NSUtilityWindowMask | NSHUDWindowMask | NSNonactivatingPanelMask | NSBorderlessWindowMask
        self = NSPanel.initWithContentRect_styleMask_backing_defer_(self, rect, mask, NSBackingStoreBuffered, objc.NO)
        if self is None:
            return
        self.app = app
        self.controller = controller
        self.anchor = None
        self.targetHeight = self.BASE_HEIGHT
        self.offsetWidth = 0
        self.host = TrayPopupView.alloc().initWithFrame_controller_(rect, controller)
        self.host.setShouldUpdateWhileOffscreen_(objc.NO)
        self.host.setDrawsBackground_(objc.NO)
        self.setContentView_(self.host)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.frameHasLoaded_, WebViewProgressFinishedNotification, self.host)
        self.setFloatingPanel_(objc.NO)
        self.setBecomesKeyOnlyIfNeeded_(objc.YES)
        self.setWorksWhenModal_(objc.YES)
        self.setAlphaValue_(1.0)
        self.setOpaque_(objc.NO)
        self.setHasShadow_(objc.NO)
        self.useOptimizedDrawing_(objc.YES)
        self.setMovableByWindowBackground_(objc.NO)
        self.setBackgroundColor_(NSColor.clearColor())
        self.setDelegate_(self)
        self.setLevel_(NSStatusWindowLevel)
        collection_behavior = NSWindowCollectionBehaviorCanJoinAllSpaces
        try:
            if MAC_VERSION >= SNOW_LEOPARD:
                from AppKit import NSWindowCollectionBehaviorTransient
                collection_behavior |= NSWindowCollectionBehaviorTransient
            if MAC_VERSION >= LION:
                from AppKit import NSWindowCollectionBehaviorFullScreenAuxiliary
                collection_behavior |= NSWindowCollectionBehaviorFullScreenAuxiliary
        except Exception:
            unhandled_exc_handler()

        self.setCollectionBehavior_(collection_behavior)
        if MAC_VERSION >= LION:
            self.alphaAnimation = self.animationForKey_('alphaValue').copy()
            self.alphaAnimation.setDelegate_(self)
            self.alphaAnimation.setDuration_(1.0)
            self.setAnimations_({'alphaValue': self.alphaAnimation})
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def windowDidResignKey_(self, notification):
        self.hide()

    def animationDidStop(self):
        if self.alphaValue() == 0.0:
            self.orderOut_(None)

    @objc.typedSelector('v@:@')
    @event_handler
    def animationDidStop_(self, animation):
        self.animationDidStop()

    @objc.typedSelector('v@:@B')
    @event_handler
    def animationDidStop_finished_(self, animation, flag):
        self.animationDidStop()

    @event_handler
    def canBecomeKeyWindow(self):
        return objc.YES

    @event_handler
    def canBecomeMainWindow(self):
        return objc.NO

    @objc.typedSelector('v@:@')
    @event_handler
    def frameHasLoaded_(self, event):
        self.setAlphaValue_(0.01)
        self.makeKeyAndOrderFront_(None)
        self.orderOut_(None)
        self.setAlphaValue_(1.0)

    @objc.typedSelector('v@:@B')
    def moveToAnchor_withHeight_(self, anchor = None, height = None):
        refresh_anchor = False
        refresh_height = False
        if anchor is not None:
            refresh_anchor = True
            screen_frame = screen_from_point((anchor[0], anchor[1])).frame()
        else:
            screen_frame = get_main_screen_rect()
        if height is not None and self.frame().size.height != height:
            refresh_height = True
        if not (refresh_anchor or refresh_height):
            return
        if refresh_anchor:
            self.anchor = anchor
        if refresh_height:
            self.targetHeight = height
        if self.anchor is None:
            return
        ax, ay, aw, _ = self.anchor
        pw, ph = self.SCREEN_WIDTH, self.targetHeight
        popup_frame = NSMakeRect(ax - pw / 2.0 + aw / 2.0, ay - ph, pw, ph)
        original_frame = popup_frame
        new_offset_width = 0
        try:
            if screen_frame is not None:
                padded_frame = NSInsetRect(screen_frame, 15, 0)
                covered_area = NSIntersectionRect(padded_frame, popup_frame)
                offset_width = self.SCREEN_WIDTH - covered_area.size.width
                if popup_frame.origin.x > offset_width:
                    popup_frame.origin.x -= offset_width
                    new_offset_width = offset_width
        except Exception:
            unhandled_exc_handler()
            TRACE("Couldn't get the screen information from the OS, the popup may be cutoff.")

        TRACE('Moving to icon rect: %r, new frame: %r (original frame: %r)', anchor, popup_frame, original_frame)
        self.setFrame_display_(popup_frame, False)
        if self.offsetWidth != new_offset_width:
            self.offsetWidth = new_offset_width

    def hide(self):
        if self.menuDelegate():
            self.menuDelegate().menuDidClose_(None)
        if MAC_VERSION >= LION:
            self.alphaAnimation.setDuration_(0.15)
            self.animator().setAlphaValue_(0.0)
        else:
            self.orderOut_(None)

    def show(self):
        if self.menuDelegate():
            self.menuDelegate().menuWillOpen_(None)
        self.makeKeyAndOrderFront_(None)
        self.app.event.report('tray-popup')
        if MAC_VERSION >= LION:
            self.alphaAnimation.setDuration_(0.05)
            self.animator().setAlphaValue_(1.0)
        fake_event = NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(NSMouseMoved, NSMakePoint(0, 0), 0, 0, self.windowNumber(), None, 0, 0, 0)
        NSApplication.sharedApplication().postEvent_atStart_(fake_event, objc.YES)

    @objc.typedSelector('v@:{_NSRect={_NSPoint=ff}{_NSSize=ff}}')
    def showAnchoredToRect_(self, rect):
        assert not self.host.failed, 'Host has failed!'
        if self.isVisible():
            self.hide()
        else:
            self.controller.refresh()
            self.moveToAnchor_withHeight_(anchor=rect)
            self.show()
