#Embedded file name: ui/cocoa/util.py
from contextlib import contextmanager
from functools import wraps
import os
import sys
from AppKit import NSGraphicsContext, NSImage, NSScreen, NSApplication, NSMakePoint, NSMakeRect, NSMakeSize, NSCompositeSourceOver
from Foundation import NSPointInRect
from PyObjCTools import AppHelper
from objc import typedSelector
import build_number
from dropbox.gui import assert_message_queue, message_sender
from dropbox.i18n import get_current_code
from dropbox.language_data import DEFAULT_CODE, LOCALE_SPLITCHAR
from dropbox.mac.version import MAC_VERSION, MAVERICKS, LEOPARD, SNOW_LEOPARD
from dropbox.trace import unhandled_exc_handler, TRACE
from ..common.constants import ResizeMethod
from pymac.helpers.process import get_model_identifier

class CocoaSettings(object):
    _accelerated_compositing_supported = None

    @classmethod
    def is_accelerated_compositing_supported(cls):
        if cls._accelerated_compositing_supported is not None:
            return cls._accelerated_compositing_supported
        result = True
        if MAC_VERSION < LEOPARD:
            result = False
        elif MAC_VERSION <= SNOW_LEOPARD:
            result = False
        else:
            try:
                model = get_model_identifier()
                if model in ('MacBookPro6,1', 'MacBookPro6,2', 'MacBookPro7,1'):
                    result = False
            except Exception:
                unhandled_exc_handler()

        cls._accelerated_compositing_supported = result
        return cls._accelerated_compositing_supported


def get_image_dir(lang = None):
    if hasattr(build_number, 'frozen'):
        if not lang or lang == DEFAULT_CODE:
            lang = 'en'
        prefix = u'%s.lproj' % (lang,)
        executable = sys.executable.decode('utf8')
        return os.path.join(executable[:executable.rfind(u'/Contents') + 9], u'Resources', prefix)
    else:
        prefix = os.path.join('i18n', lang) if lang else ''
        return os.path.join(os.getcwdu(), prefix, u'images')


@message_sender(AppHelper.callAfter, block=True)
def load_image(image_name, lazy = False):
    code = get_current_code()
    degrade_options = [code, None]
    if LOCALE_SPLITCHAR in code:
        short = code.split(LOCALE_SPLITCHAR)[0]
        degrade_options.insert(1, short)
    for lang in degrade_options:
        image_dir = get_image_dir(lang)
        image_path = os.path.join(image_dir, image_name)
        if not os.path.exists(image_path):
            continue
        if lazy:
            return NSImage.alloc().initByReferencingFile_(image_path)
        return NSImage.alloc().initWithContentsOfFile_(image_path)

    raise AttributeError('!! Attempt to load missing image %r' % image_name)


def guarded(sig):

    def inner_guarded(fn):

        @typedSelector(sig)
        @wraps(fn)
        def wrapper(self, *n, **kw):
            try:
                m = assert_message_queue(fn)
                return m(self, *n, **kw)
            except Exception:
                TRACE('Crash in %s.%s' % (self.__class__.__name__, fn.__name__))
                unhandled_exc_handler()

        return wrapper

    return inner_guarded


def protected_action_method(action_method):

    @wraps(action_method)
    def wrapper(self, sender):
        try:
            m = assert_message_queue(action_method)
            return m(self, sender)
        except Exception:
            TRACE('Crash in %s.%s' % (self.__class__.__name__, action_method.__name__))
            unhandled_exc_handler()

    return wrapper


@contextmanager
def save_graphics_state():
    context = NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    try:
        yield context
    finally:
        context.restoreGraphicsState()


@contextmanager
def edit_attributed_string(attributed_string):
    try:
        attributed_string.beginEditing()
        yield attributed_string
    finally:
        attributed_string.endEditing()


@contextmanager
def edit_text_view(text_view):
    storage = text_view.textStorage()
    try:
        storage.beginEditing()
        yield storage
    finally:
        storage.endEditing()


def screen_from_point(point):
    screens = NSScreen.screens()
    for screen in screens:
        if NSPointInRect(point, screen.frame()):
            return screen

    return NSScreen.mainScreen()


def get_main_screen_rect():
    screen_frame = None
    try:
        if MAC_VERSION >= MAVERICKS:
            screen = NSScreen.mainScreen()
        else:
            screen = NSScreen.screens()[0]
        screen_frame = screen.frame()
    except Exception:
        unhandled_exc_handler()

    if screen_frame is None:
        TRACE("!! Couldn't get the screen information from the OS.")
    return screen_frame


def get_origin_of_centered_window(screen_frame, window_size):
    return NSMakePoint(screen_frame.origin.x + screen_frame.size.width / 2.0 - 0.5 * window_size.width, screen_frame.origin.y + screen_frame.size.height / 2.0 - 0.5 * window_size.height)


def resize_image(source_img, dimensions, method = ResizeMethod.FIT):
    assert source_img
    NSApplication.sharedApplication()
    initial_width = float(dimensions[0])
    initial_height = float(dimensions[1])
    width = source_img.bestRepresentationForDevice_(None).pixelsWide()
    height = source_img.bestRepresentationForDevice_(None).pixelsHigh()
    pixel_size = NSMakeSize(width, height)
    orig_size = source_img.size()
    width_ratio = initial_width / pixel_size[0]
    height_ratio = initial_height / pixel_size[1]
    if method == ResizeMethod.FIT:
        width_ratio = min(width_ratio, height_ratio)
        height_ratio = min(width_ratio, height_ratio)
    if method == ResizeMethod.CROP:
        width_ratio = max(width_ratio, height_ratio)
        height_ratio = max(width_ratio, height_ratio)
    resized_width = width * width_ratio
    resized_height = height * height_ratio
    crop_width = orig_size.width
    crop_height = orig_size.height
    if method is ResizeMethod.CROP:
        crop_width = initial_width / resized_width * orig_size.width
        crop_height = initial_height / resized_height * orig_size.height
    final_width = min(resized_width, initial_width)
    final_height = min(resized_height, initial_height)
    target_img = NSImage.alloc().initWithSize_(NSMakeSize(final_width, final_height))
    target_img.lockFocus()
    TRACE('Resized image sizes W=%r, H=%r', final_width, final_height)
    source_img.drawInRect_fromRect_operation_fraction_(NSMakeRect(0, 0, final_width, final_height), NSMakeRect((orig_size.width - crop_width) / 2, (orig_size.height - crop_height) / 2, crop_width, crop_height), NSCompositeSourceOver, 1.0)
    target_img.unlockFocus()
    return target_img
