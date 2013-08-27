#Embedded file name: ui/cocoa/splash.py
from AppKit import NSApp, NSAttributedString, NSBackingStoreBuffered, NSButton, NSCenterTextAlignment, NSClosableWindowMask, NSFloatingWindowLevel, NSFont, NSNormalWindowLevel, NSPopUpButton, NSRegularControlSize, NSSwitchButton, NSTextField, NSTitledWindowMask, NSView, NSWindow
from Foundation import NSHeight, NSMinYEdge, NSPoint, NSRect, NSSize, NSWidth, NSZeroRect
from objc import NO, YES, typedSelector
from PyObjCTools import AppHelper
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.preferences import OPT_IMPORTED_IPHOTOS_ONCE
from dropbox.trace import unhandled_exc_handler
from dropbox.mac.version import MAC_VERSION, LEOPARD
from ui.cocoa.constants import Images, ENTER_KEY, Colors
from ui.cocoa.dropbox_controls import BackgroundImageView, FlippedView, NonBlurryImageView, DropboxSheetErrorFactory
from ui.cocoa.dynamic_layouts import CONTENT_BORDER
from ui.cocoa.util import protected_action_method
from ui.common.camera import CameraStrings
from ui.common.misc import MiscStrings

class InnerSplashScreenView(FlippedView):
    HEADER_SIZE = 24
    SUBHEADER_SIZE = 16
    CHECKBOX_SIZE = 13
    BORDER = 40
    IMAGE_PADDING = 0
    HEADER_PADDING = 24
    SUBHEADER_PADDING = 8
    FINE_PRINT_SIZE = 13
    FINE_PRINT_PADDING = 11
    VIEW_SIZE = (570, 400)
    HEADER_COLOR = Colors.camera_font
    SUBHEADER_COLOR = Colors.camera_font
    BOLD_HEADER = True
    SUBHEADER_LINE_HEIGHT = 25
    CHOICE_SELECTOR_PADDING = 13

    @assert_message_queue
    def __new__(cls, checkbox_text, header, subheader, image, fine_print = None, choice_selector = None):
        return cls.alloc().init(cls, checkbox_text, header, subheader, image, fine_print, choice_selector)

    @assert_message_queue
    def init(self, cls, checkbox_text, header, subheader, image, fine_print, choice_selector):
        self = super(cls, self).initWithFrame_(NSRect((0, 0), self.VIEW_SIZE))
        if self is None:
            return self
        self.checkbox_text = checkbox_text
        self.fine_print = fine_print
        self.header = header
        self.subheader = subheader
        self.image = image
        self.choice_selector = choice_selector
        self.layout()
        return self

    @typedSelector('v@:')
    @assert_message_queue
    def layout(self):
        height = self.BORDER + self.IMAGE_PADDING
        width = self.VIEW_SIZE[0] - self.BORDER * 2
        image = NonBlurryImageView.alloc().initWithFrame_(NSZeroRect)
        image.setImage_(self.image)
        image.setFrameSize_(self.image.size())
        self.addSubview_(image)
        image.setFrameOrigin_((0, height))
        image.centerHorizontallyInSuperview()
        height += NSHeight(image.frame()) + self.HEADER_PADDING
        label1 = NSTextField.createLabelWithText_font_maxWidth_origin_(self.header, NSFont.boldSystemFontOfSize_(self.HEADER_SIZE) if self.BOLD_HEADER else NSFont.systemFontOfSize_(self.HEADER_SIZE), width, NSPoint(0, height))
        self.addSubview_(label1)
        label1.centerHorizontallyInSuperview()
        label1.setTextColor_(self.HEADER_COLOR)
        height += NSHeight(label1.frame()) + self.SUBHEADER_PADDING
        label2 = NSTextField.createLabelWithText_font_maxWidth_origin_(NSAttributedString.boldify(self.subheader, font=NSFont.systemFontOfSize_(self.SUBHEADER_SIZE), bold_font=NSFont.boldSystemFontOfSize_(self.SUBHEADER_SIZE), center=True, line_height=self.SUBHEADER_LINE_HEIGHT), NSFont.systemFontOfSize_(self.SUBHEADER_SIZE), width, NSPoint(0, height))
        self.addSubview_(label2)
        label2.setAlignment_(NSCenterTextAlignment)
        label2.setTextColor_(self.SUBHEADER_COLOR)
        label2.balancedWrapToWidth_(width)
        label2.centerHorizontallyInSuperview()
        if self.checkbox_text:
            checkbox = NSButton.alloc().initWithFrame_(NSZeroRect)
            self.addSubview_(checkbox)
            checkbox.setButtonType_(NSSwitchButton)
            checkbox.setAttributedTitle_(NSAttributedString.boldify(self.checkbox_text, font=NSFont.systemFontOfSize_(self.CHECKBOX_SIZE), bold_font=NSFont.boldSystemFontOfSize_(self.CHECKBOX_SIZE)))
            checkbox.setTextColor_(Colors.camera_font)
            checkbox.sizeToFit()
            if NSWidth(checkbox.frame()) > width:
                checkbox.setAttributedTitle_(CameraStrings.splash_always_import_no_name)
                checkbox.setTextColor_(Colors.camera_font)
                checkbox.sizeToFit()
            checkbox.setState_(True)
            checkbox.centerHorizontallyInSuperview()
            checkbox.alignBottomInSuperview(self.BORDER - checkbox.flippedBaselineOffset())
            self.checkbox = checkbox
        else:
            self.checkbox = None
        height += NSHeight(label2.frame()) + self.FINE_PRINT_PADDING
        if self.fine_print:
            fine_print = NSTextField.createLabelWithText_font_maxWidth_origin_(self.fine_print, NSFont.systemFontOfSize_(self.FINE_PRINT_SIZE), width, NSPoint(0, height))
            self.addSubview_(fine_print)
            fine_print.setAlignment_(NSCenterTextAlignment)
            fine_print.setTextColor_(Colors.fine_print)
            fine_print.balancedWrapToWidth_(width)
            fine_print.centerHorizontallyInSuperview()
            self.fine_print_label = fine_print
        else:
            self.fine_print_label = None
        self.combo = None
        if self.choice_selector:
            subview = NSView.alloc().initWithFrame_(NSZeroRect)
            combo_descriptor = NSTextField.createLabelWithText_(NSAttributedString.boldify(self.choice_selector.text, font=NSFont.systemFontOfSize_(NSRegularControlSize), bold_font=NSFont.boldSystemFontOfSize_(NSRegularControlSize)))
            combo_descriptor.setTextColor_(self.SUBHEADER_COLOR)
            subview.addSubview_(combo_descriptor)
            combo = NSPopUpButton.createNormalPopUpButtonWithChoices_default_(self.choice_selector.selections, self.choice_selector.default_index)
            combo.sizeToFit()
            subview.addSubview_(combo)
            descriptor_frame = combo_descriptor.frame()
            half = combo.frame().size.height / 2.0
            descriptor_half = descriptor_frame.size.height / 2.0
            combo_descriptor.setFrameOrigin_(NSPoint(descriptor_frame.origin.x, half - descriptor_half + 2.0))
            combo.setFrameOrigin_(NSPoint(descriptor_frame.origin.x + descriptor_frame.size.width, 0))
            subview.setFrameSize_((combo.frame().size.width + descriptor_frame.size.width, combo.frame().size.height))
            self.addSubview_(subview)
            subview.centerHorizontallyInSuperview()
            subview.alignBottomInSuperview(CONTENT_BORDER + self.CHOICE_SELECTOR_PADDING)
            self.combo = combo


class SplashScreen(NSWindow):
    BOTTOM_BORDER = 52
    WINDOW_SIZE = (570, 450)

    @assert_message_queue
    def __new__(cls, splash_title, right_button, lefter_right_button, left_button, inner, checkbox_text = None, left_label = None, close_cb = None, background = None, wrap_import_button_with_warning = False, app = None, *args, **kwargs):
        return cls.alloc().init(splash_title, right_button, lefter_right_button, left_button, inner, checkbox_text, left_label, close_cb, background, wrap_import_button_with_warning, app, *args, **kwargs)

    @assert_message_queue
    def init(self, splash_title, right_button, lefter_right_button, left_button, inner, checkbox_text, left_label, close_cb, background, wrap_import_button_with_warning, app, *args, **kwargs):
        self = super(SplashScreen, self).initWithContentRect_styleMask_backing_defer_(NSRect((0, 0), self.WINDOW_SIZE), NSTitledWindowMask | NSClosableWindowMask, NSBackingStoreBuffered, NO)
        if self is None:
            return self
        self.background = background or Images.CameraBackground
        self.right_button_cb, self.right_button_text, self.right_button_key = right_button
        if wrap_import_button_with_warning:
            original_cb = self.right_button_cb

            def right_button_cb_with_dialog():
                if app.pref_controller[OPT_IMPORTED_IPHOTOS_ONCE]:
                    original_cb()
                else:
                    DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self, CameraStrings.gallery_import_dialog_caption, None, original_cb, lambda : None, MiscStrings.yes_button, MiscStrings.no_button)

            self.right_button_cb = right_button_cb_with_dialog
        if lefter_right_button:
            self.lefter_right_button_cb, self.lefter_right_button_text, self.lefter_right_button_key = lefter_right_button
        else:
            self.lefter_right_button_cb, self.lefter_right_button_text, self.lefter_right_button_key = (None, None, None)
        if left_button:
            self.left_button_cb, self.left_button_text, self.left_button_key = left_button
        else:
            self.left_button_cb, self.left_button_text, self.left_button_key = (None, None, None)
        self.inner = inner
        self.left_label = left_label
        self.checkbox_text = checkbox_text
        self.close_callback = close_cb
        self.setReleasedWhenClosed_(NO)
        self.center()
        self.setLevel_(NSNormalWindowLevel)
        self.setTitle_(splash_title)
        if MAC_VERSION >= LEOPARD:
            self.setContentBorderThickness_forEdge_(self.BOTTOM_BORDER, NSMinYEdge)
        self.layout()
        return self

    def layout(self):
        view = self.contentView()
        buttons = []
        right_button = view.addNormalRoundButtonWithTitle_action_(self.right_button_text, self.handleRightButton_)
        right_button.setKeyEquivalent_(ENTER_KEY if not self.right_button_key else self.right_button_key)
        offset = (self.BOTTOM_BORDER - (NSHeight(right_button.frame()) + NSHeight(right_button.insetRect()))) / 2
        right_button.alignRightInSuperview()
        right_button.alignBottomInSuperview(offset)
        buttons.append(right_button)
        self.left_button = None
        if self.left_button_text:
            left_button = view.addNormalRoundButtonWithTitle_action_(self.left_button_text, self.handleLeftButton_)
            left_button.alignLeftInSuperview()
            left_button.alignBottomInSuperview(offset)
            if self.left_button_key:
                left_button.setKeyEquivalent_(self.left_button_key)
            self.left_button = left_button
            buttons.append(left_button)
        elif self.left_label:
            left_label = NSTextField.createLabelWithText_(self.left_label)
            view.addSubview_(left_label)
            left_label.alignLeftInSuperview()
            left_label.alignBottomInSuperview(offset)
        if self.lefter_right_button_text:
            lefter_right_button = view.addNormalRoundButtonWithTitle_action_(self.lefter_right_button_text, self.handleLefterRightButton_)
            if self.lefter_right_button_key:
                lefter_right_button.setKeyEquivalent_(self.lefter_right_button_key)
            lefter_right_button.placeLeftOfButton_(right_button)
            buttons.append(lefter_right_button)
        for button in buttons:
            button.setTarget_(self)

        bg_image = BackgroundImageView(NSRect((0, self.BOTTOM_BORDER), (NSWidth(self.frame()), NSHeight(self.frame()) - self.BOTTOM_BORDER)), self.background, bottom_align=True)
        if (self.background.size().width, self.background.size().height) != self.WINDOW_SIZE:
            bg_image.setImageSize_(NSSize(self.WINDOW_SIZE[0], self.WINDOW_SIZE[1]))
        view.addSubview_(bg_image)
        view.addSubview_(self.inner)
        self.inner.alignBottomInSuperview(self.BOTTOM_BORDER)

    @typedSelector('c@:@')
    @event_handler
    def windowShouldClose_(self, sender):
        try:
            if self.close_callback:
                self.close_callback()
        except Exception:
            unhandled_exc_handler()

        return YES

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def show_window(self):
        self.setLevel_(NSFloatingWindowLevel)
        self.makeKeyAndOrderFront_(None)
        NSApp().activateIgnoringOtherApps_(True)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def close_window(self):
        self.close()
        return True

    @protected_action_method
    def handleLefterRightButton_(self, event):
        self.close()
        if self.lefter_right_button_cb:
            self.lefter_right_button_cb()

    @protected_action_method
    def handleLeftButton_(self, event):
        self.close()
        if self.left_button_cb:
            self.left_button_cb()

    @protected_action_method
    def handleRightButton_(self, event):
        self.close()
        combo_index = None
        if self.inner.combo:
            combo_index = self.inner.combo.indexOfSelectedItem()
        if self.checkbox_text:
            checkbox_state = bool(self.inner.checkbox.state())
            self.right_button_cb(checkbox_state)
        elif self.inner.combo:
            self.right_button_cb(index=combo_index)
        else:
            self.right_button_cb()


def get_splash_screen(splash_title, right_button, lefter_right_button, left_button, checkbox_text = None, left_label = None, close_cb = None, background = None, *args, **kwargs):
    inner = InnerSplashScreenView(checkbox_text, *args, **kwargs)
    splash_screen = SplashScreen(splash_title, right_button, lefter_right_button, left_button, inner, checkbox_text, left_label, close_cb, background, *args, **kwargs)
    return splash_screen
