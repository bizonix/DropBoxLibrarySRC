#Embedded file name: ui/cocoa/tray_arrow.py
from __future__ import absolute_import
import functools
from objc import YES, NO, ivar
from AppKit import NSBackingStoreBuffered, NSBorderlessWindowMask, NSCompositeSourceOver, NSFloatingWindowLevel, NSRectFill, NSTimer, NSWindow, NSView
from Foundation import NSHeight, NSRect, NSWidth, NSZeroPoint
from dropbox.gui import assert_message_queue
from dropbox.trace import TRACE, unhandled_exc_handler
from ..common import tray_arrow
from .constants import Colors, Images
from .util import screen_from_point

class TrayArrowView(NSView):
    theImage = ivar('theImage')

    def __new__(cls, image):
        return TrayArrowView.alloc().initWithImage_(image)

    def initWithImage_(self, image):
        self.theImage = image
        self.theImage.retain()
        self = super(TrayArrowView, self).initWithFrame_(NSRect((0, 0), (self.theImage.size().width, self.theImage.size().height)))
        return self

    def dealloc(self):
        self.theImage.release()
        super(TrayArrowView, self).dealloc()

    def drawRect_(self, rect):
        try:
            Colors.clear.set()
            NSRectFill(self.frame())
            self.theImage.compositeToPoint_operation_(NSZeroPoint, NSCompositeSourceOver)
            self.window().invalidateShadow()
        except:
            unhandled_exc_handler()

    def mouseDown_(self, event):
        self.window().stop()


class TrayArrow(NSWindow):
    PERIOD_LENGTH = tray_arrow.PERIOD_LENGTH
    TICK_RATE = tray_arrow.TICK_RATE
    PADDING_FACTOR = tray_arrow.PADDING_FACTOR

    def __new__(cls, rect):
        TRACE('Creating Cocoa TrayArrow pointing at (%d,%d,%d,%d)' % rect)
        return TrayArrow.alloc().initDirectedAtPoint_(rect)

    def initDirectedAtPoint_(self, rect):
        self.pointing_at = rect
        self._tick = functools.partial(tray_arrow.tick, self)
        self.get_current_position = functools.partial(tray_arrow.get_current_position, self)
        self.determine_motion = functools.partial(tray_arrow.determine_motion, self)
        the_image = self.get_correct_image()
        self.determine_motion()
        window_rect = NSRect((self.startx, self.starty), (self.w, self.h))
        self = super(TrayArrow, self).initWithContentRect_styleMask_backing_defer_(window_rect, NSBorderlessWindowMask, NSBackingStoreBuffered, NO)
        if self is None:
            return
        self.setAlphaValue_(1.0)
        self.setOpaque_(NO)
        self.setHasShadow_(YES)
        self.setLevel_(NSFloatingWindowLevel)
        self.setReleasedWhenClosed_(NO)
        self.setContentView_(TrayArrowView(the_image))
        return self

    def get_correct_image(self):
        rx, ry, rw, rh = self.pointing_at
        screen_rect = screen_from_point((rx, ry)).frame()
        top_dist = NSHeight(screen_rect) - ry + screen_rect.origin.y
        bottom_dist = ry - screen_rect.origin.y
        left_dist = rx - screen_rect.origin.x
        right_dist = NSWidth(screen_rect) - rx + screen_rect.origin.x
        min_dist = min(top_dist, bottom_dist, left_dist, right_dist)
        if top_dist == min_dist:
            self.orientation = 0
            img = Images.TrayArrowUp
            motion_factor = -1
        elif left_dist == min_dist:
            self.orientation = 90
            img = Images.TrayArrowLeft
            motion_factor = 1
        elif bottom_dist == min_dist:
            self.orientation = 180
            img = Images.TrayArrowDown
            motion_factor = 1
        else:
            self.orientation = 270
            img = Images.TrayArrowRight
            motion_factor = -1
        self.h = img.size().height
        self.w = img.size().width
        self.range_of_motion = self.h / 6 * motion_factor
        if self.orientation == 0:
            self.y_factor = -(TrayArrow.PADDING_FACTOR * rh + self.h)
        elif self.orientation == 180:
            self.y_factor = TrayArrow.PADDING_FACTOR * rh + rh
        return img

    def start(self):
        assert_message_queue()
        self.t = 0
        self.orderFront_(None)
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(self.TICK_RATE, self, self.tick_, None, True)

    def stop(self):
        if self.timer:
            self.timer.invalidate()
            self.timer = None
        self.close()

    def place(self):
        self.setFrameOrigin_(self.get_current_position())

    def tick_(self, timer):
        self._tick(None)
