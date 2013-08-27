#Embedded file name: ui/cocoa/custom_bubble.py
from AppKit import NSAnimation, NSAnimationLinear, NSAnimationNonblocking, NSBackingStoreBuffered, NSBezierPath, NSBorderlessWindowMask, NSButtonCell, NSColor, NSCompositeSourceOver, NSFont, NSImageOnly, NSLineBreakByTruncatingMiddle, NSMomentaryChangeButton, NSMutableParagraphStyle, NSNonactivatingPanelMask, NSObject, NSPanel, NSParagraphStyleAttributeName, NSScreen, NSShadowAttributeName, NSShadow, NSShadowlessSquareBezelStyle, NSStatusWindowLevel, NSStringDrawingUsesLineFragmentOrigin, NSStringDrawingUsesFontLeading, NSWindowController
from Foundation import NSHeight, NSInsetRect, NSMakeRange, NSMakeRect, NSMinY, NSRect, NSZeroRect
from objc import NO, YES, typedSelector
from PyObjCTools import AppHelper
import math
from Queue import Empty, Queue
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.trace import TRACE
from ui.cocoa.constants import Colors, Images
from ui.cocoa.util import guarded, edit_text_view, save_graphics_state
from ui.cocoa.dropbox_controls import FlippedButton, FlippedTextView, FlippedView

class BubbleCloseButtonCell(NSButtonCell):

    @guarded('v@:@{_NSRect={_NSPoint=ff}{_NSSize=ff}}@')
    def drawImage_withFrame_inView_(self, image, frame, view):
        image.drawInRect_fromRect_operation_fraction_(self.imageRectForBounds_(frame), NSZeroRect, NSCompositeSourceOver, 1.0)


class BubbleCloseButton(FlippedButton):

    def __new__(cls, frame):
        return BubbleCloseButton.alloc().initWithFrame_(frame)

    @classmethod
    def cellClass(cls):
        return BubbleCloseButtonCell

    @guarded('@24@0:4{_NSRect={_NSPoint=ff}{_NSSize=ff}}8')
    def initWithFrame_(self, frame):
        self = super(BubbleCloseButton, self).initWithFrame_(frame)
        if not self:
            return None
        closebox_img = Images.Closebox
        closebox_img.setFlipped_(YES)
        closebox_img_pressed = Images.CloseboxPressed
        closebox_img_pressed.setFlipped_(YES)
        self.setBezelStyle_(NSShadowlessSquareBezelStyle)
        self.setBordered_(NO)
        self.setButtonType_(NSMomentaryChangeButton)
        self.setImagePosition_(NSImageOnly)
        self.setImage_(closebox_img)
        self.setAlternateImage_(closebox_img_pressed)
        return self


class BubbleTextView(FlippedTextView):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, frame):
        return BubbleTextView.alloc().initWithFrame_(frame)

    @assert_message_queue
    def initWithFrame_(self, frame):
        self = super(BubbleTextView, self).initWithFrame_(frame)
        return self

    @classmethod
    def createWithText_width_color_isBold_shadow_(cls, text, width, color, is_bold, shadow):
        return cls.createWithText_width_color_isBold_size_shadow_truncate_(text, width, color, is_bold, 13, shadow, True)

    @classmethod
    def createWithText_width_color_isBold_size_shadow_truncate_(cls, text, width, color, is_bold, size, shadow, truncate):
        text_view = BubbleTextView(NSRect((0, 0), (width, 0)))
        text_view.setDrawsBackground_(NO)
        text_view.setEditable_(NO)
        text_view.setSelectable_(NO)
        with edit_text_view(text_view) as storage:
            storage.mutableString().setString_(text)
            if is_bold:
                storage.setFont_(NSFont.boldSystemFontOfSize_(size))
            else:
                storage.setFont_(NSFont.systemFontOfSize_(size))
            storage.setForegroundColor_(color)
            whole_range = NSMakeRange(0, len(text))
            if shadow:
                storage.addAttribute_value_range_(NSShadowAttributeName, shadow, whole_range)
            dps = NSMutableParagraphStyle.defaultParagraphStyle().mutableCopy()
            dps.setLineSpacing_(2)
            if truncate:
                dps.setLineBreakMode_(NSLineBreakByTruncatingMiddle)
            storage.addAttribute_value_range_(NSParagraphStyleAttributeName, dps, whole_range)
            bounds = storage.boundingRectWithSize_options_((0, 0), NSStringDrawingUsesLineFragmentOrigin | NSStringDrawingUsesFontLeading)
        text_view.layoutManager().glyphRangeForTextContainer_(text_view.textContainer())
        size = text_view.layoutManager().usedRectForTextContainer_(text_view.textContainer()).size
        text_view.setFrameSize_(size)
        return text_view


class BubbleView(FlippedView):
    CORNER_RADIUS = 9
    TOP_LEFT_PADDING = 12
    INNER_PADDING = 14
    WIDTH = 320
    UNINDENTED_TEXT_WIDTH = WIDTH - 2 * INNER_PADDING - TOP_LEFT_PADDING
    BORDER_WIDTH = 3
    BORDER_HOVER_WIDTH = 3
    SHADOW_OFFSET = -2
    SHADOW_BLUR = 2

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls):
        return BubbleView.alloc().init()

    @assert_message_queue
    def init(self):
        self = super(BubbleView, self).initWithFrame_(NSZeroRect)
        self._bg_color = Colors.notification_background
        self._text_color = Colors.white
        self._border_color = Colors.notification_border
        self._border_hover_color = Colors.notification_border_hover
        self.mouse_inside = False
        self._tr_tag = None
        self._close_box_tr_tag = None
        self._box_icon = Images.BoxGrowl
        self._box_icon.setFlipped_(YES)
        self._indent_body_text = True
        self._text_left = self.TOP_LEFT_PADDING + self.INNER_PADDING + self._box_icon.size().width + 4
        self._text_right = self.WIDTH - self.INNER_PADDING
        self._close_button = BubbleCloseButton(NSMakeRect(0, 2, 30, 30))
        self._title_view = None
        self._text_view = None
        return self

    @guarded('v@:*')
    def setCaption_(self, caption):
        if self._title_view:
            self._title_view.removeFromSuperview()
        self._title_view = BubbleTextView.createWithText_width_color_isBold_shadow_(caption, self._text_right - self._text_left, self._text_color, True, self._get_shadow())
        self.addSubview_(self._title_view)
        self.sizeToFit()

    @guarded('v@:*')
    def setMessage_(self, message):
        if self._text_view:
            self._text_view.removeFromSuperview()
        width = self._text_right - self._text_left if self._indent_body_text else self.UNINDENTED_TEXT_WIDTH
        self._text_view = BubbleTextView.createWithText_width_color_isBold_size_shadow_truncate_(message, width, self._text_color, False, 12, self._get_shadow(), False)
        self.addSubview_(self._text_view)
        self.sizeToFit()

    def _get_background_rect(self):
        b = NSInsetRect(self.bounds(), 4, 4)
        b.origin.x += self.TOP_LEFT_PADDING
        b.origin.y += self.TOP_LEFT_PADDING
        b.size.width -= self.TOP_LEFT_PADDING
        b.size.height -= self.TOP_LEFT_PADDING
        return b

    def _draw_border(self, bg_path, border_size):
        shaded_bounds = self._get_background_rect()
        border_rect = NSInsetRect(shaded_bounds, -border_size, -border_size)
        border_path = NSBezierPath.bezierPathWithRoundedRect_radius_(border_rect, self.CORNER_RADIUS)
        with save_graphics_state() as gs:
            clip_path = bg_path.bezierPathByReversingPath()
            clip_path.appendBezierPath_(border_path)
            clip_path.addClip()
            if self.mouse_inside:
                self._border_hover_color.setFill()
            else:
                self._border_color.setFill()
            border_path.setLineWidth_(border_size * 2)
            border_path.fill()

    def _get_shadow(self):
        shadow = NSShadow.alloc().init()
        shadow.setShadowOffset_((self.SHADOW_OFFSET, self.SHADOW_OFFSET))
        shadow.setShadowBlurRadius_(self.SHADOW_BLUR)
        shadow.setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(0, 0.45))
        return shadow

    def isOpaque(self):
        return NO

    @event_handler
    def drawRect_(self, rect):
        shaded_bounds = self._get_background_rect()
        bg_path = NSBezierPath.bezierPathWithRoundedRect_radius_(shaded_bounds, self.CORNER_RADIUS)
        with save_graphics_state() as context:
            self._bg_color.setFill()
            self._border_color.setStroke()
            bg_path.fill()
            if self.mouse_inside:
                self._draw_border(bg_path, self.BORDER_HOVER_WIDTH)
            else:
                self._draw_border(bg_path, self.BORDER_WIDTH)
        self._box_icon.drawAtPoint_fromRect_operation_fraction_((self.TOP_LEFT_PADDING + self.INNER_PADDING, self.TOP_LEFT_PADDING + self.INNER_PADDING), NSZeroRect, NSCompositeSourceOver, 1.0)
        self.window().invalidateShadow()
        super(BubbleView, self).drawRect_(rect)

    @guarded('v@:')
    def sizeToFit(self):
        height = self.TOP_LEFT_PADDING + self.INNER_PADDING
        if self._title_view:
            box_height = self._box_icon.size().height
            title_view_height = NSHeight(self._title_view.frame())
            delta = int((box_height - title_view_height) / 2 - 1)
            self._title_view.setFrameOrigin_((self._text_left, height + delta))
            top_padding = NSMinY(self._title_view.frame()) - self.TOP_LEFT_PADDING
            height += max(self._box_icon.size().height, NSHeight(self._title_view.frame()))
        else:
            top_padding = self.INNER_PADDING
        height += 2
        if self._text_view:
            if self._indent_body_text:
                self._text_view.setFrameOrigin_((self._text_left, height))
            else:
                self._text_view.setFrameOrigin_((self.TOP_LEFT_PADDING + self.INNER_PADDING, height))
            height += self._text_view.frame().size.height
        height += top_padding
        r = NSMakeRect(0, 0, self.WIDTH, height)
        self.setFrame_(r)
        if self._tr_tag:
            self.removeTrackingRect_(self._tr_tag)
        loc = self.convertPoint_fromView_(self.window().mouseLocationOutsideOfEventStream(), None)
        inside = self.mouse_inRect_(loc, self._get_background_rect())
        if inside:
            self.setCloseBoxVisible_(YES)
            self.mouse_inside = True
            self.setNeedsDisplay_(YES)
        self._tr_tag = self.addTrackingRect_owner_userData_assumeInside_(self._get_background_rect(), self, 0, inside)

    @guarded('v@:@')
    def handleCloseButton_(self, event):
        self.mouse_inside = False
        self.window().windowController().close()

    @guarded('v@:B')
    def setCloseBoxVisible_(self, flag):
        if flag:
            self._close_button.setTarget_(self)
            self._close_button.setAction_(self.handleCloseButton_)
            self._close_box_tr_tag = self.addTrackingRect_owner_userData_assumeInside_(self._close_button.frame(), self, 0, NO)
            self.addSubview_(self._close_button)
        else:
            if self._close_box_tr_tag:
                self.removeTrackingRect_(self._close_box_tr_tag)
            self._close_button.removeFromSuperview()

    @event_handler
    def mouseEntered_(self, event):
        TRACE('ENTERED: %r', event.locationInWindow())
        if not self.mouse_inside:
            self.setCloseBoxVisible_(YES)
            self.mouse_inside = True
            self.setNeedsDisplay_(YES)

    @event_handler
    def mouseExited_(self, event):
        TRACE('EXITED: %r', event.locationInWindow())
        event_location = event.locationInWindow()
        local_point = self.convertPoint_fromView_(event_location, None)
        in_close_box = self.mouse_inRect_(local_point, self._close_button.frame())
        in_own_box = self.mouse_inRect_(local_point, self._get_background_rect())
        TRACE('in_close_box: %s', in_close_box)
        TRACE('in_own_box: %s', in_own_box)
        if not in_close_box and not in_own_box and self.mouse_inside:
            self.setCloseBoxVisible_(NO)
            self.mouse_inside = False
            self.setNeedsDisplay_(YES)
            if self.window().should_close_on_exit:
                self.window().windowController().close()

    @event_handler
    def mouseUp_(self, event):
        event_location = event.locationInWindow()
        local_point = self.convertPoint_fromView_(event_location, None)
        in_close_box = self.mouse_inRect_(local_point, self._close_button.frame())
        in_own_box = self.mouse_inRect_(local_point, self._get_background_rect())
        if in_own_box and not in_close_box:
            self.window().handleClick()


class BubbleFader(NSAnimation):
    FORWARD = 1
    BACKWARD = -1

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, window, duration):
        return BubbleFader.alloc().initWithDuration_window_(window, duration)

    def initWithDuration_window_(self, window, duration):
        self = super(BubbleFader, self).initWithDuration_animationCurve_(duration, NSAnimationLinear)
        if not self:
            return self
        self.setAnimationBlockingMode_(NSAnimationNonblocking)
        self._direction = self.FORWARD
        self._window = window
        return self

    def reverse(self):
        self._direction *= -1

    @guarded('v@:f')
    def setCurrentProgress_(self, progress):
        a = 1 - math.exp(-4 * progress)
        if self._direction == self.FORWARD:
            min(self._window.setAlphaValue_(a), 1.0)
        else:
            max(self._window.setAlphaValue_(1 - a), 0.0)
        if progress >= 1:
            if self._direction == self.FORWARD:
                self._window.setAlphaValue_(1.0)
            else:
                self._window.setAlphaValue_(0.0)

    def window(self):
        return self._window

    def direction(self):
        return self._direction


class BubblePanel(NSPanel):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, app):
        return BubblePanel.alloc().initWithApp_(app)

    def initWithApp_(self, app):
        try:
            self = super(BubblePanel, self).initWithContentRect_styleMask_backing_defer_(NSZeroRect, NSBorderlessWindowMask | NSNonactivatingPanelMask, NSBackingStoreBuffered, YES)
        except:
            TRACE('!! %r -> %r type = %r', BubblePanel, self, type(self))
            raise

        if self is None:
            return
        self.setBackgroundColor_(NSColor.clearColor())
        self.setAlphaValue_(0.0)
        self.setHasShadow_(YES)
        self.setLevel_(NSStatusWindowLevel)
        self.useOptimizedDrawing_(YES)
        self.setOpaque_(NO)
        self.setSticky_(YES)
        self.setContentView_(BubbleView())
        self.sizeToFit()
        self._app = app
        self._ctx_ref = None
        self.should_close_on_exit = False
        return self

    @guarded('v@:')
    def sizeToFit(self):
        self.contentView().sizeToFit()
        inner_frame = self.contentView().frame()
        old_frame = self.frame()
        old_frame.size = inner_frame.size
        self.setFrame_display_animate_(old_frame, YES, YES)

    @guarded('v@:*')
    def setMessage_(self, message):
        self.contentView().setMessage_(message)
        self.sizeToFit()

    @guarded('v@:*')
    def setCaption_(self, caption):
        self.contentView().setCaption_(caption)
        self.sizeToFit()

    @guarded('v@:@')
    def setCtxRef_(self, ctx_ref):
        self._ctx_ref = ctx_ref

    @guarded('v@:')
    def place(self):
        main_screen_frame = NSScreen.mainScreen().frame()
        r = self.frame()
        r.origin.x = main_screen_frame.origin.x + main_screen_frame.size.width - r.size.width - 9
        r.origin.y = main_screen_frame.origin.y + main_screen_frame.size.height - r.size.height - 21
        self.setFrameOrigin_(r.origin)

    @guarded('v@:')
    def handleClick(self):
        if self._ctx_ref is not None:
            self._app.bubble_context.thunk_and_expire_context_ref(self._ctx_ref)
            self._ctx_ref = None
        self.contentView().mouse_inside = False
        self.windowController().close()

    @property
    def mouse_inside(self):
        return self.contentView().mouse_inside


class BubbleWindowController(NSWindowController):
    POPUP_DURATION = 5

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, app):
        return cls.alloc().initWithApp_(app)

    def initWithApp_(self, app):
        self._window = BubblePanel(app)
        self = super(BubbleWindowController, self).initWithWindow_(self._window)
        if self is None:
            return
        self._app = app
        self._q = Queue()
        self._window_showing = False
        self._fader = BubbleFader(self._window, 0.3)
        self._fader.setDelegate_(self)
        return self

    @guarded('v@:')
    def close(self):
        NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(self, self.close, None)
        if self._window.mouse_inside:
            self._window.should_close_on_exit = True
            return
        self._fader.startAnimation()

    @guarded('v@:')
    def cancelPendingClose(self):
        TRACE('Cancelling scheduled window close')
        self.cancelPreviousPerformRequestsWithTarget_selector_object_(self, self.close, None)

    @guarded('v@:@')
    @assert_message_queue
    def animationDidEnd_(self, animation):
        d = animation.direction()
        animation.reverse()
        if d == animation.FORWARD:
            self.performSelector_withObject_afterDelay_(self.close, None, self.POPUP_DURATION)
        else:
            super(BubbleWindowController, self).close()
            self._window_showing = False
            try:
                message, caption, ctx_ref = self._q.get(False)
                self.do_bubble(message, caption, ctx_ref)
            except Empty:
                pass

    def still_running(self):
        return True

    @typedSelector('v@:**@')
    @message_sender(AppHelper.callAfter)
    def do_bubble(self, message, caption, ctx_ref = None):
        if self._window_showing:
            TRACE('Queuing bubble: %s', message)
            self._q.put_nowait((message, caption, ctx_ref))
            return
        TRACE('BubbleWindowController: Bubbling: %s', message)
        self._window_showing = True
        self._window.setCaption_(caption)
        self._window.setMessage_(message)
        self._window.setCtxRef_(ctx_ref)
        self._window.place()
        self._window.makeKeyAndOrderFront_(self)
        self._window.should_close_on_exit = False
        self._fader.startAnimation()
