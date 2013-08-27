#Embedded file name: ui/cocoa/camera.py
from __future__ import absolute_import
import functools
import time
from AppKit import NSApp, NSAlertDefaultReturn, NSAlertAlternateReturn, NSBackingStoreBuffered, NSBezierPath, NSColor, NSCompositeSourceOver, NSFloatingWindowLevel, NSFont, NSImage, NSImageAlignCenter, NSProgressIndicator, NSProgressIndicatorBarStyle, NSRunAlertPanel, NSScaleToFit, NSTextField, NSTitledWindowMask, NSWindow, NSWindowController
from Foundation import NSHeight, NSInsetRect, NSMakeRect, NSRect, NSZeroRect
from objc import NO, YES, typedSelector
from PyObjCTools import AppHelper
from ..common.camera import CameraUI, CameraStrings, photos_and_albums_message, rect_to_centered_square
from ..common.misc import MiscStrings
from .constants import Colors, ENTER_KEY, ESCAPE_KEY, Images
from dropbox.preferences import OPT_IMPORTED_IPHOTOS_ONCE
from .dropbox_controls import FlippedView
from .panel import ShadowedImage
from .splash import get_splash_screen, InnerSplashScreenView, SplashScreen
from .util import protected_action_method, save_graphics_state
from dropbox.gui import assert_message_queue, message_sender
from dropbox.i18n import format_number
from dropbox.trace import unhandled_exc_handler, TRACE

class CameraSplashScreen(object):

    @assert_message_queue
    def __init__(self, device, start_cb, cancel_cb, never_cb, never_text, always_text):
        right_button = (functools.partial(start_cb, device), CameraStrings.splash_start_button, None)
        lefter_right_button = (functools.partial(cancel_cb, device), CameraStrings.splash_cancel_button, ESCAPE_KEY)
        left_button = (functools.partial(never_cb, device), never_text, None)
        self.splash = get_splash_screen(splash_title=CameraStrings.splash_title, right_button=right_button, lefter_right_button=lefter_right_button, left_button=left_button, checkbox_text=always_text, header=CameraStrings.splash_heading, subheader=CameraStrings.splash_subheading, image=Images.CameraSplashDrawing)
        if self.splash is None:
            return
        self.show_window = self.splash.show_window
        self.close_window = self.splash.close_window

    def disable_never(self):
        if self.splash.left_button:
            self.splash.left_button.setEnabled_(False)
            self.splash.left_button.setToolTip_(CameraStrings.splash_always_import_disabled)

    def disable_always(self):
        if self.splash.inner.checkbox:
            self.splash.inner.checkbox.setState_(False)
            self.splash.inner.checkbox.setEnabled_(False)
            self.splash.inner.checkbox.setToolTip_(CameraStrings.splash_always_import_disabled)

    def uncheck_always(self):
        if self.splash.inner.checkbox:
            self.splash.inner.checkbox.setState_(False)


class QuotaSplashScreen(object):

    @assert_message_queue
    def __init__(self, upgrade_dropbox_cb, cancel_cb, cancel_text, left_button_cb, never_text, files_imported_text, quota_message, close_cb):
        right_button = (upgrade_dropbox_cb, CameraStrings.quota_more_space_button, None)
        lefter_right_button = (cancel_cb, cancel_text, ESCAPE_KEY)
        left_button = (left_button_cb, never_text, None)
        self.splash = get_splash_screen(splash_title=CameraStrings.splash_title, right_button=right_button, lefter_right_button=lefter_right_button, left_button=left_button, left_label=files_imported_text, header=CameraStrings.quota_heading, subheader=quota_message, image=Images.CameraQuotaSplash, close_cb=functools.partial(close_cb, self))
        if self.splash is None:
            return
        self.show_window = self.splash.show_window


def get_gallery_import_splash(num_photos, num_albums, num_events, import_cb, never_cb, cancel_cb, show_quota_promo, app):
    right_button = (import_cb, CameraStrings.gallery_import_start_button, None)
    lefter_right_button = (cancel_cb, CameraStrings.gallery_import_later_button, ESCAPE_KEY)
    left_button = (never_cb, CameraStrings.gallery_import_never_button, None)
    if num_photos:
        subheader = CameraStrings.gallery_import_subheading % dict(photos_and_albums=photos_and_albums_message(num_photos, num_albums), num_events=num_events)
    else:
        subheader = CameraStrings.gallery_import_subheading_no_photos
    fine_print = CameraStrings.gallery_import_quota_notice if show_quota_promo else None
    inner_kwargs = dict(checkbox_text=None, header=CameraStrings.gallery_import_heading, subheader=subheader, image=Images.IPhoto, fine_print=fine_print)
    splash_kwargs = dict(splash_title=CameraStrings.gallery_import_title, right_button=right_button, lefter_right_button=lefter_right_button, left_button=left_button, close_cb=cancel_cb, background=Images.SplashGradientBackground, app=app)
    if app.mbox.is_dfb_user_without_linked_pair and not app.pref_controller[OPT_IMPORTED_IPHOTOS_ONCE]:
        splash_kwargs.update(dict(wrap_import_button_with_warning=True))
    if fine_print:
        inner = GalleryImportInnerSplashScreen(**inner_kwargs)
        splash = SplashScreen(inner=inner, **splash_kwargs)
    else:
        inner = GalleryImportNoBonusInnerSplashScreen(**inner_kwargs)
        splash = GalleryImportNoBonusSplashScreen(inner=inner, **splash_kwargs)
    return splash


class GalleryImportInnerSplashScreen(InnerSplashScreenView):
    IMAGE_PADDING = 6
    HEADER_PADDING = 26
    SUBHEADER_PADDING = 10
    HEADER_COLOR = Colors.photo_gallery_header
    SUBHEADER_COLOR = Colors.photo_gallery_subheader
    BOLD_HEADER = False
    SUBHEADER_LINE_HEIGHT = 24


class GalleryImportNoBonusInnerSplashScreen(InnerSplashScreenView):
    IMAGE_PADDING = 6
    HEADER_PADDING = 26
    SUBHEADER_PADDING = 10
    VIEW_SIZE = (570, 370)
    HEADER_COLOR = Colors.photo_gallery_header
    SUBHEADER_COLOR = Colors.photo_gallery_subheader
    BOLD_HEADER = False
    SUBHEADER_LINE_HEIGHT = 24


class GalleryImportNoBonusSplashScreen(SplashScreen):
    BOTTOM_BORDER = 52
    WINDOW_SIZE = (570, 420)


class CameraProgressWindow(NSWindow):

    @assert_message_queue
    def __new__(cls, ui):
        return CameraProgressWindow.alloc().initWithUI_(ui)

    @typedSelector('v@:@')
    @assert_message_queue
    def initWithUI_(self, ui):
        self = super(CameraProgressWindow, self).initWithContentRect_styleMask_backing_defer_(NSZeroRect, NSTitledWindowMask, NSBackingStoreBuffered, NO)
        self.setReleasedWhenClosed_(NO)
        self.setLevel_(NSFloatingWindowLevel)
        self.useOptimizedDrawing_(YES)
        self.setTitle_(CameraStrings.progress_title)
        v = CameraProgressView(ui)
        self.setContentView_(v)
        self.sizeToFit()
        self.center()
        return self

    @typedSelector('v@:')
    @assert_message_queue
    def sizeToFit(self):
        self.contentView().sizeToFit()
        old_frame = self.frame()
        new_frame = self.frameRectForContentRect_(self.contentView().frame())
        new_frame.origin = old_frame.origin
        delta_h = NSHeight(new_frame) - NSHeight(old_frame)
        new_frame.origin.y -= delta_h
        self.setFrame_display_animate_(new_frame, YES, YES)


class ThumbnailBoxView(ShadowedImage):
    BORDER_INSET = 2
    IMAGE_INSET = 6

    def initWithFrame_(self, frame):
        self = super(ThumbnailBoxView, self).initWithFrame_(frame)
        if not self:
            return
        self.border = False
        return self

    def setBorder_(self, border):
        self.border = border

    def drawRect_(self, rect):
        if not self.border:
            return super(ThumbnailBoxView, self).drawRect_(rect)
        with save_graphics_state():
            self._shadow.set()
            NSColor.whiteColor().set()
            NSBezierPath.bezierPathWithRect_(NSInsetRect(rect, self.BORDER_INSET, self.BORDER_INSET)).fill()
        size = self.image().size()
        self.image().drawInRect_fromRect_operation_fraction_(NSInsetRect(rect, self.IMAGE_INSET, self.IMAGE_INSET), NSMakeRect(*rect_to_centered_square(size.width, size.height)), NSCompositeSourceOver, 1.0)


class CameraProgressView(FlippedView):
    THUMBNAIL_ORIGIN = (20, 15)
    THUMBNAIL_SIZE = (64, 64)
    THUMBNAIL_TIMEOUT = 2
    LABEL_ORIGIN = (102, 19)
    PROGRESS_ORIGIN = (102, 43)
    PROGRESS_SIZE = (388, 20)
    ESTIMATE_ORIGIN = (102, 67)
    SHADOW_OFFSET = (2.0, -2.0)
    SHADOW_BLUR = 3.0

    @assert_message_queue
    def __new__(cls, ui):
        return CameraProgressView.alloc().initWithUI_(ui)

    @typedSelector('v@:@')
    @assert_message_queue
    def initWithUI_(self, ui):
        self = super(CameraProgressView, self).initWithFrame_(NSMakeRect(0, 0, 508, 122))
        if self is None:
            return self
        self.ui = ui
        self._width = 508
        self.last_photo_time = 0
        self.layout()
        return self

    @typedSelector('v@:')
    @assert_message_queue
    def layout(self):
        self._thumbnail = ThumbnailBoxView.alloc().initWithFrame_(NSZeroRect)
        self._thumbnail.setImage_(Images.Box64)
        self._thumbnail.setImageAlignment_(NSImageAlignCenter)
        self._thumbnail.setImageScaling_(NSScaleToFit)
        self._thumbnail.setFrameSize_(self.THUMBNAIL_SIZE)
        self._thumbnail.setFrameOrigin_(self.THUMBNAIL_ORIGIN)
        self._thumbnail.setShadowOffset_(self.SHADOW_OFFSET)
        self._thumbnail.setShadowBlurRadius_(self.SHADOW_BLUR)
        self._thumbnail.setShadowColor_(NSColor.blackColor().colorWithAlphaComponent_(0.3))
        self._label = NSTextField.createLabelWithText_font_('', NSFont.boldSystemFontOfSize_(13))
        self._label.setFrameOrigin_(self.LABEL_ORIGIN)
        self._progress_bar = NSProgressIndicator.alloc().initWithFrame_(NSRect(self.PROGRESS_ORIGIN, self.PROGRESS_SIZE))
        self._progress_bar.setStyle_(NSProgressIndicatorBarStyle)
        self._progress_bar.setIndeterminate_(YES)
        self._progress_bar.setFrameOrigin_(self.PROGRESS_ORIGIN)
        self._estimate = NSTextField.createLabelWithText_font_('', NSFont.systemFontOfSize_(NSFont.smallSystemFontSize()))
        self._estimate.setFrameOrigin_(self.ESTIMATE_ORIGIN)
        self._hide_button = self.addNormalRoundButtonWithTitle_action_(MiscStrings.hide_button, self.handleHideButton_)
        self._hide_button.setKeyEquivalent_(ENTER_KEY)
        self._hide_button.alignRightInSuperview()
        self._hide_button.alignBottomInSuperview()
        self._cancel_button = self.addNormalRoundButtonWithTitle_action_(MiscStrings.cancel_button, self.handleCancelButton_)
        self._cancel_button.placeLeftOfButton_(self._hide_button)
        self.addSubview_(self._thumbnail)
        self.addSubview_(self._label)
        self.addSubview_(self._progress_bar)
        self.addSubview_(self._estimate)

        @message_sender(AppHelper.callAfter)
        def handleMessage(message):
            self._label.setStringValue_(message)
            self._label.sizeToFit()

        @message_sender(AppHelper.callAfter)
        def handleTotalBytes(total_bytes):
            self._progress_bar.setIndeterminate_(YES if total_bytes == 0 else NO)
            self._progress_bar.setMinValue_(0.0)
            self._progress_bar.setMaxValue_(total_bytes)
            self._progress_bar.setDoubleValue_(self.ui.cur_bytes.get())

        @message_sender(AppHelper.callAfter)
        def handleCurBytes(cur_bytes):
            self._progress_bar.setDoubleValue_(cur_bytes)
            self._estimate.setStringValue_(self.ui.get_remaining_message())
            self._estimate.sizeToFit()

        @message_sender(AppHelper.callAfter)
        def handleLastPhoto(path):
            if path:
                if time.time() - self.last_photo_time > self.THUMBNAIL_TIMEOUT:
                    image = NSImage.alloc().initByReferencingFile_(unicode(path))
                    if image.isValid():
                        self._thumbnail.setBorder_(True)
                        self._thumbnail.setImage_(image)
                        self.last_photo_time = time.time()
            else:
                self._thumbnail.setBorder_(False)
                self._thumbnail.setImage_(Images.Box64)

        handleMessage(self.ui.message.get())
        handleTotalBytes(self.ui.total_bytes.get())
        handleCurBytes(self.ui.cur_bytes.get())
        handleLastPhoto(self.ui.last_photo.get())
        self.ui.message.register(handleMessage)
        self.ui.total_bytes.register(handleTotalBytes)
        self.ui.cur_bytes.register(handleCurBytes)
        self.ui.last_photo.register(handleLastPhoto)

    @typedSelector('v@:')
    @assert_message_queue
    def sizeToFit(self):
        self.setFrame_(NSMakeRect(0, 0, self._width, 122))

    @protected_action_method
    def handleCancelButton_(self, event):
        self.ui.on_cancel()

    @protected_action_method
    def handleHideButton_(self, event):
        self.ui.progress_window_hide()


class CocoaCameraUI(CameraUI):
    _MAX_FILE_SELECT = 50

    def __init__(self, **kw):
        super(CocoaCameraUI, self).__init__(**kw)
        self.window_controller = None
        self.call_later = AppHelper.callLater
        self.sel_sync = False
        self.open_quota_splashes = set()

    @message_sender(AppHelper.callAfter, block=True)
    def ask_user(self, device, start_cb, cancel_cb, never_cb, old_action, always_state, never_ever):
        never_text = self.generate_never_text(never_ever, old_action)
        if device.name or device.model:
            always_text = CameraStrings.splash_always_import % dict(name=device.name or device.model)
        else:
            always_text = CameraStrings.splash_always_import_no_name
        splash = CameraSplashScreen(device, start_cb, cancel_cb, never_cb, never_text, always_text)
        if not device.is_trackable():
            if not old_action:
                splash.disable_never()
            splash.disable_always()
        if always_state is False:
            splash.uncheck_always()
        splash.show_window()
        return splash.close_window

    @message_sender(AppHelper.callAfter)
    def progress_window_show(self):
        self.showing_bubbles = False
        if not self.window_controller:
            self.window_controller = NSWindowController.alloc().initWithWindow_(CameraProgressWindow(self))
        self.window_controller.showWindow_(None)
        NSApp().activateIgnoringOtherApps_(True)

    @message_sender(AppHelper.callAfter)
    def progress_window_hide(self):
        if self.window_controller:
            self.window_controller.close()
        self.showing_bubbles = True

    @message_sender(AppHelper.callAfter, block=True)
    def out_of_space_show(self, upgrade_cb, cancel_cb, cancel_text, never_cb, never_text, quota_message, files_imported_label = None):

        def close_cb(quota_splash):
            try:
                self.open_quota_splashes.remove(quota_splash)
            except Exception:
                unhandled_exc_handler()

        splash = QuotaSplashScreen(upgrade_cb, cancel_cb, cancel_text, never_cb, never_text, files_imported_label, quota_message, close_cb)
        self.open_quota_splashes.add(splash)
        splash.show_window()

    @message_sender(AppHelper.callAfter)
    def prompt_sel_sync(self, on_enable, on_disable, on_cancel):
        if self.sel_sync:
            return
        self.sel_sync = True
        try:
            NSApp().activateIgnoringOtherApps_(True)
            ret = NSRunAlertPanel(CameraStrings.sel_sync_question, CameraStrings.sel_sync_message, CameraStrings.sel_sync_enable, CameraStrings.sel_sync_disable, CameraStrings.sel_sync_cancel)
            if ret == NSAlertDefaultReturn:
                on_enable()
            elif ret == NSAlertAlternateReturn:
                on_disable()
            else:
                on_cancel()
        finally:
            self.sel_sync = False

    def _can_select_paths(self, paths):
        return len(paths) <= self._MAX_FILE_SELECT

    @message_sender(AppHelper.callAfter)
    def error_dialog(self, caption, message = '', okay_caption = None):
        if okay_caption is None:
            okay_caption = MiscStrings.ok_button
        NSApp().activateIgnoringOtherApps_(True)
        NSRunAlertPanel(caption, message, okay_caption, None, None)
