#Embedded file name: ui/cocoa/screenshots.py
import AppKit
from dropbox.gui import assert_message_queue
from .splash import SplashScreen, InnerSplashScreenView
from .util import resize_image
from ..common.screenshots import ScreenshotsStrings
from ..common.constants import ResizeMethod
from .constants import Images, ENTER_KEY, ESCAPE_KEY, Colors

class ScreenshotsInnerSplashScreenView(InnerSplashScreenView):
    HEADER_SIZE = 24
    SUBHEADER_SIZE = 16
    CHECKBOX_SIZE = 13
    BORDER = 35
    HEADER_PADDING = 30
    SUBHEADER_PADDING = 9
    FINE_PRINT_SIZE = 13
    FINE_PRINT_PADDING = 0
    VIEW_SIZE = (570, 370)
    HEADER_COLOR = Colors.screenshots_header_font
    SUBHEADER_COLOR = Colors.screenshots_subheader_font
    BOLD_HEADER = False

    @assert_message_queue
    def __new__(cls, *args, **kwargs):
        if kwargs.get('choice_selector'):
            cls.VIEW_SIZE = (570, 392)
            cls.HEADER_PADDING = 22
        return super(ScreenshotsInnerSplashScreenView, cls).__new__(cls, *args, **kwargs)


class ScreenshotsDialog(SplashScreen):
    BOTTOM_BORDER = 52
    WINDOW_SIZE = (570, 420)

    @assert_message_queue
    def __new__(cls, *args, **kwargs):
        if kwargs.get('choice_selector'):
            cls.WINDOW_SIZE = (570, 452)
        return super(ScreenshotsDialog, cls).__new__(cls, *args, **kwargs)


def get_screenshots_splash_screen(splash_title, right_button, lefter_right_button, left_button, checkbox_text = None, left_label = None, close_cb = None, background = None, *args, **kwargs):
    inner = ScreenshotsInnerSplashScreenView(checkbox_text, *args, **kwargs)
    splash_screen = ScreenshotsDialog(splash_title, right_button, lefter_right_button, left_button, inner, checkbox_text, left_label, close_cb, background, *args, **kwargs)
    return splash_screen


class ScreenshotsSplashScreen(object):
    SCREENSHOT_SIZE = (233, 144)

    def __init__(self, always_cb, never_cb, close_cb, file_path, mbox_selector):
        source_img = AppKit.NSImage.alloc().initByReferencingFile_(file_path)
        if not source_img:
            close_cb()
            return
        screenshot = resize_image(source_img, self.SCREENSHOT_SIZE, ResizeMethod.CROP)
        static_image = Images.ScreenshotsBox
        image = create_splash_screen_image(screenshot, static_image)
        quota_message = ScreenshotsStrings.splash_message

        def translated_cb(cb):

            def f(index = None):
                if mbox_selector:
                    cb(role=mbox_selector.translate_index(index))
                else:
                    cb()

            return f

        right_button = (translated_cb(always_cb), ScreenshotsStrings.always_move_screenshots, ENTER_KEY)
        left_button = (never_cb, ScreenshotsStrings.never_move_screenshots, ESCAPE_KEY)
        self.splash = get_screenshots_splash_screen(splash_title=ScreenshotsStrings.splash_title, right_button=right_button, lefter_right_button=None, left_button=left_button, left_label='', header=ScreenshotsStrings.quota_heading, subheader=quota_message, image=image, close_cb=close_cb, choice_selector=mbox_selector, background=Images.SplashGradientBackground)
        self.show_window = self.splash.show_window


def create_splash_screen_image(screenshot, img):
    screenshot_position = (3, 10)
    try:
        img.lockFocus()
        AppKit.NSGraphicsContext.currentContext().setImageInterpolation_(AppKit.NSImageInterpolationHigh)
        destRect = (screenshot_position, screenshot.size())
        srcRect = ((0, 0), screenshot.size())
        screenshot.drawInRect_fromRect_operation_fraction_(destRect, srcRect, AppKit.NSCompositeSourceOver, 1.0)
    finally:
        img.unlockFocus()

    return img
