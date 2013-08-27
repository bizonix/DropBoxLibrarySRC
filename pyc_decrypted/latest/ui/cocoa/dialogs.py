#Embedded file name: ui/cocoa/dialogs.py
import objc
from Cocoa import NSApp, NSAttributedString, NSBackingStoreBuffered, NSBoldFontMask, NSButton, NSColor, NSDictionary, NSFontAttributeName, NSFontManager, NSImageView, NSMakeRect, NSMakeSize, NSRoundedBezelStyle, NSStringDrawingUsesLineFragmentOrigin, NSTextView, NSTitledWindowMask, NSWindow
from PyObjCTools import AppHelper
from dropbox.gui import assert_message_queue, message_sender, SafeValue
from ui.cocoa.util import get_main_screen_rect, get_origin_of_centered_window
dialog_windows = []

class DialogWindow(NSWindow):
    WINDOW_WIDTH = 430
    TEXT_WIDTH = 300
    TEXT_PADDING = 20
    BUTTON_HEIGHT = 30
    BUTTON_WIDTH = 120
    ICON_SIZE = 70
    WINDOW_MIN_HEIGHT = 100
    BUTTON_PADDING = 10

    @objc.typedSelector('@@:@@@')
    @assert_message_queue
    def initWithCaption_message_buttons_(self, caption, message, buttons):
        assert buttons and buttons.count
        mask = NSTitledWindowMask
        text_starting_x = self.WINDOW_WIDTH - self.TEXT_WIDTH - self.TEXT_PADDING
        title_view = NSTextView.alloc().init()
        title_view.setString_(caption)
        title_view.setDrawsBackground_(objc.NO)
        title_view.setBackgroundColor_(NSColor.clearColor())
        font = title_view.font()
        font_manager = NSFontManager.sharedFontManager()
        newFont = font_manager.fontWithFamily_traits_weight_size_(font.familyName(), NSBoldFontMask, 0, font.pointSize() + 1)
        title_view.textStorage().setFont_(newFont)
        attributes = NSDictionary.dictionaryWithObjectsAndKeys_(title_view.font(), NSFontAttributeName, None)
        attrString = NSAttributedString.alloc().initWithString_attributes_(title_view.string(), attributes)
        rect = attrString.boundingRectWithSize_options_(NSMakeSize(self.TEXT_WIDTH, 0), NSStringDrawingUsesLineFragmentOrigin)
        title_height = rect.size.height
        message_view = NSTextView.alloc().init()
        message_view.setString_(message)
        message_view.setDrawsBackground_(objc.NO)
        message_view.setBackgroundColor_(NSColor.clearColor())
        attributes = NSDictionary.dictionaryWithObjectsAndKeys_(message_view.font(), NSFontAttributeName, None)
        attrString = NSAttributedString.alloc().initWithString_attributes_(message_view.string(), attributes)
        rect = attrString.boundingRectWithSize_options_(NSMakeSize(self.TEXT_WIDTH, 0), NSStringDrawingUsesLineFragmentOrigin)
        message_height = rect.size.height
        height = title_height + message_height + 3 * self.TEXT_PADDING + self.BUTTON_HEIGHT
        if self.WINDOW_MIN_HEIGHT > height:
            height = self.WINDOW_MIN_HEIGHT
        screen_rect = get_main_screen_rect()
        center_of_screen = get_origin_of_centered_window(screen_rect, NSMakeSize(self.WINDOW_WIDTH, height))
        title_frame = NSMakeRect(text_starting_x, height - title_height - self.TEXT_PADDING, self.TEXT_WIDTH, title_height)
        title_view.setFrame_(title_frame)
        message_view.setFrame_(NSMakeRect(text_starting_x, title_frame.origin.y - message_height - 5, self.TEXT_WIDTH, message_height))
        rect = NSMakeRect(center_of_screen.x, center_of_screen.y, self.WINDOW_WIDTH, height)
        self.safeValue = SafeValue()
        self = super(DialogWindow, self).initWithContentRect_styleMask_backing_defer_(rect, mask, NSBackingStoreBuffered, objc.NO)
        i = 0
        for btnStr in buttons:
            but_frame = NSMakeRect(self.WINDOW_WIDTH - (self.BUTTON_PADDING + (i + 1) * self.BUTTON_WIDTH), self.BUTTON_PADDING, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
            but = NSButton.alloc().initWithFrame_(but_frame)
            but.setTitle_(btnStr)
            self.contentView().addSubview_(but)
            but.setBezelStyle_(NSRoundedBezelStyle)
            but.setTarget_(self)
            but.setAction_(objc.selector(self.buttonClicked_, signature='v@:@'))
            but.setTag_(i)
            i += 1

        app_image = NSApp.applicationIconImage()
        image_view_frame = NSMakeRect((text_starting_x - self.ICON_SIZE) * 0.5, height - self.ICON_SIZE - self.TEXT_PADDING, self.ICON_SIZE, self.ICON_SIZE)
        image_view = NSImageView.alloc().initWithFrame_(image_view_frame)
        image_view.setImage_(app_image)
        self.contentView().addSubview_(image_view)
        title_view.setEditable_(objc.NO)
        self.contentView().addSubview_(title_view)
        message_view.setEditable_(objc.NO)
        self.contentView().addSubview_(message_view)
        NSApp().activateIgnoringOtherApps_(True)
        return self

    def show(self):
        self.makeKeyAndOrderFront_(None)
        dialog_windows.append(self)

    def buttonClicked_(self, sender):
        self.safeValue.set(sender.tag())
        self.orderOut_(None)
        dialog_windows.remove(self)


@message_sender(AppHelper.callAfter, block=True)
def showAlertDialogWithCaption_message_andButtons_(caption = None, message = None, buttons = None):
    the_alert = DialogWindow.alloc().initWithCaption_message_buttons_(caption, message, buttons)
    the_alert.show()
    return the_alert.safeValue
