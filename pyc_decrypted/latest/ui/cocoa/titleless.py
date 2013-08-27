#Embedded file name: ui/cocoa/titleless.py
import objc
import os
import build_number
from Cocoa import NSBackingStoreBuffered, NSImage, NSImageView, NSMakeRect, NSMaxX, NSMinX, NSPointInRect, NSScaleNone, NSTitledWindowMask, NSTrackingActiveAlways, NSTrackingArea, NSTrackingMouseEnteredAndExited, NSTrackingMouseMoved, NSView, NSViewHeightSizable, NSViewWidthSizable, NSWindow, NSWindowCloseButton, NSWindowMiniaturizeButton, NSWindowZoomButton
from dropbox.mac.internal import get_resources_dir
from dropbox.gui import assert_message_queue, event_handler, message_sender
from PyObjCTools import AppHelper

class TitlelessHostView(NSView):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, frame):
        return TitlelessHostView.alloc().initWithFrame_(frame)

    @objc.typedSelector('@@:@{_NSRect={_NSPoint=ff}{_NSSize=ff}}@')
    @assert_message_queue
    def initWithFrame_window_(self, frame, window):
        self = super(TitlelessHostView, self).initWithFrame_(frame)
        if self is None:
            return
        self.trackingArea = None
        resources_dir = get_resources_dir() if hasattr(build_number, 'frozen') else u'images/setupwizard/mac'
        overlay_path = os.path.join(resources_dir, 'traffic-light.tiff')
        self.customLights = []
        self.closeLight = None
        for b in window.controlButtons:
            pos = self.convertPoint_fromView_(b.frame().origin, b.superview())
            image = NSImage.alloc().initWithContentsOfFile_(overlay_path)
            imageview = NSImageView.alloc().initWithFrame_(NSMakeRect(pos.x, pos.y - 1, b.frame().size.width, b.frame().size.height))
            imageview.setImage_(image)
            self.addSubview_(imageview)
            self.customLights.append(imageview)
            if b != window.closeButton:
                imageview.setAlphaValue_(0.3)
            else:
                self.closeLight = imageview

        return self

    def hitTest_(self, point):
        return None

    @objc.typedSelector('v@:')
    @event_handler
    def updateTrackingAreas(self):
        window = self.window()
        if window is None:
            return
        if self.trackingArea is not None:
            self.removeTrackingArea_(self.trackingArea)
        options = NSTrackingMouseEnteredAndExited | NSTrackingMouseMoved | NSTrackingActiveAlways
        self.trackingArea = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(self.bounds(), options, self, None)
        mouseLocation = self.window().mouseLocationOutsideOfEventStream()
        mouseLocation = self.convertPoint_fromView_(mouseLocation, None)
        if NSPointInRect(mouseLocation, self.bounds()):
            self.mouseEntered_(None)
        else:
            self.mouseExited_(None)
        self.addTrackingArea_(self.trackingArea)

    def acceptsFirstMouse_(self, point):
        return objc.YES

    @event_handler
    def mouseEntered_(self, event):
        self.window().closeButton.setHidden_(objc.NO)
        self.closeLight.setHidden_(objc.YES)

    @event_handler
    def mouseExited_(self, event):
        self.window().closeButton.setHidden_(objc.YES)
        self.closeLight.setHidden_(objc.NO)


class TitlelessWindow(NSWindow):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, contentRect, styleMask, view):
        return TitlelessWindow.alloc().initWithContentRect_styleMask_view_(contentRect, styleMask, view)

    @objc.typedSelector('@@:@{_NSRect={_NSPoint=ff}{_NSSize=ff}}@@')
    @assert_message_queue
    def initWithContentRect_styleMask_view_(self, contentRect, styleMask, view):
        assert styleMask & NSTitledWindowMask, 'Titleless windows must be titled.'
        self = super(TitlelessWindow, self).initWithContentRect_styleMask_backing_defer_(contentRect, styleMask, NSBackingStoreBuffered, objc.NO)
        if self is None:
            return
        self.setReleasedWhenClosed_(objc.NO)
        self.controlButtons = [self.standardWindowButton_(NSWindowCloseButton), self.standardWindowButton_(NSWindowMiniaturizeButton), self.standardWindowButton_(NSWindowZoomButton)]
        self.closeButton, self.miniaturizeButton, self.zoomButton = self.controlButtons
        contentViewFrame = self.contentView().frame()
        frameRect = self.frameRectForContentRect_(contentRect)
        titleBarHeight = frameRect.size.height - contentRect.size.height
        contentViewFrame.size.height += titleBarHeight
        self.setContentView_(view)
        view.setFrame_(contentViewFrame)
        self.contentView().superview().addSubview_(self.closeButton)
        hoverRectForTrafficLights = self.closeButton.frame()
        hoverRectForTrafficLights.size.width = NSMaxX(self.zoomButton.frame()) - NSMinX(hoverRectForTrafficLights)
        titlelessView = TitlelessHostView.alloc().initWithFrame_window_(hoverRectForTrafficLights, self)
        self.contentView().superview().addSubview_(titlelessView)
        view.updateTrackingAreas()
        titlelessView.updateTrackingAreas()
        return self
