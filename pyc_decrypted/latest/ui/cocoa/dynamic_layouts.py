#Embedded file name: ui/cocoa/dynamic_layouts.py
import math
import re
from objc import Category, NO, objc_object, YES
from Foundation import NSHeight, NSMakeRange, NSMakeRect, NSMaxX, NSMaxY, NSMidX, NSMidY, NSMinX, NSMinY, NSPoint, NSRect, NSSize, NSWidth, NSZeroRect
from AppKit import NSAttributedString, NSBezierPath, NSBox, NSBoxSeparator, NSButton, NSButtonCell, NSCenterTextAlignment, NSControl, NSDatePicker, NSFont, NSFontAttributeName, NSForegroundColorAttributeName, NSHelpButtonBezelStyle, NSLinkAttributeName, NSMatrix, NSMomentaryPushInButton, NSMutableAttributedString, NSMutableParagraphStyle, NSParagraphStyleAttributeName, NSPopUpButton, NSProgressIndicator, NSProgressIndicatorSpinningStyle, NSRadioButton, NSRadioModeMatrix, NSRegularControlSize, NSRoundedBezelStyle, NSSearchField, NSSecureTextField, NSSmallControlSize, NSStepper, NSStringDrawingUsesLineFragmentOrigin, NSSwitchButton, NSTextField, NSURL, NSView, NSWindow
from ctypes import cdll, c_int32
from ctypes.util import find_library
from dropbox.gui import event_handler
from dropbox.mac.version import MAC_VERSION, TIGER
from dropbox.trace import TRACE, unhandled_exc_handler
from .constants import Colors, ENTER_KEY
NEARBY_CONTROL_BORDER = 8
CONTENT_BORDER = 20
INFINITE_DIMENSION = 10000.0
CHECKBOX_HEIGHT = 14
CHECKBOX_VERTICAL_SPACING = 4
BUTTON_HEIGHT = 20
BUTTON_LEFT_ALIGNMENT_OFFSET = -4
BUTTON_TO_HELP_BUTTON_ADJUSTMENT = 4
BUTTON_TO_HELP_BUTTON_ADJUSTMENT_FLIPPED = 3
STATICTEXT_TO_BUTTON_BASELINE_ADJUSTMENT = 10
STATICTEXT_TO_HELPBUTTON_BASELINE_ADJUSTMENT = 8
STATICTEXT_TO_DROPDOWN_BASELINE_ADJUSTMENT = 6
LABEL_PADDING = 8
BOTTOM_BUTTON_BORDER = 6
HORIZ_BUTTON_BORDER = 17
HORIZ_BUTTON_SPACING = 2

class NSAttributedString(Category(NSAttributedString)):

    @classmethod
    def hyperlinkFromString_withURL_font_(cls, string, url, font = None):
        attr_str = NSMutableAttributedString.alloc().initWithString_(string)
        r = NSMakeRange(0, attr_str.length())
        if font is None:
            font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        attr_str.beginEditing()
        attr_str.addAttribute_value_range_(NSLinkAttributeName, url, r)
        attr_str.addAttribute_value_range_(NSForegroundColorAttributeName, Colors.link, r)
        attr_str.addAttribute_value_range_(NSFontAttributeName, font, r)
        attr_str.endEditing()
        return attr_str

    @classmethod
    def linkify(cls, string, font = None, color = None):
        link_re = re.compile('<a href="([^"]*)">([^<]*)</a>')
        parts = re.split('(<a href="[^"]*">[^<]*</a>)', string)
        attr_str = NSMutableAttributedString.alloc().init()
        for part in parts:
            m = link_re.match(part)
            if m is not None:
                u = NSURL.URLWithString_(m.groups()[0])
                inner_str = NSAttributedString.hyperlinkFromString_withURL_font_(m.groups()[1], u, font)
                attr_str.appendAttributedString_(inner_str)
            else:
                inner_str = NSAttributedString.createForControlWithString_font_color_(part, font, color)
                attr_str.appendAttributedString_(inner_str)

        return attr_str

    @classmethod
    def boldify(cls, string, font = None, bold_font = None, color = None, center = False, line_height = None):
        link_re = re.compile('<b>([^<]*)</b>')
        parts = re.split('(<b>[^<]*</b>)', string)
        attr_str = NSMutableAttributedString.alloc().init()
        font = font or NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        bold_font = bold_font or NSFont.boldSystemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        for part in parts:
            m = link_re.match(part)
            if m is not None:
                u = m.groups()[0]
                inner_str = NSAttributedString.createForControlWithString_font_color_(u, bold_font, color)
                attr_str.appendAttributedString_(inner_str)
            else:
                inner_str = NSAttributedString.createForControlWithString_font_color_(part, font, color)
                attr_str.appendAttributedString_(inner_str)

        if center or line_height is not None:
            style = NSMutableParagraphStyle.defaultParagraphStyle().mutableCopyWithZone_(None)
            if center:
                style.setAlignment_(NSCenterTextAlignment)
            if line_height is not None:
                style.setMinimumLineHeight_(line_height)
                style.setMaximumLineHeight_(line_height)
            r = NSMakeRange(0, attr_str.length())
            attr_str.addAttribute_value_range_(NSParagraphStyleAttributeName, style, r)
        return attr_str

    @classmethod
    def createForControlWithString_font_color_(cls, val, font = None, color = None):
        if font is None:
            font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        attrs = {NSFontAttributeName: font}
        if color:
            attrs[NSForegroundColorAttributeName] = color
        attr_str = NSAttributedString.alloc().initWithString_attributes_(val, attrs)
        return attr_str


class NSBox(Category(NSBox)):

    def verticalPadding(self):
        return 8

    def verticalTitleAdjustment(self):
        return 12


class NSBezierPath(Category(NSBezierPath)):

    @classmethod
    def bezierPathWithRoundedRect_radius_(cls, r, radius):
        bp = NSBezierPath.alloc().init()
        bp.moveToPoint_((NSMaxX(r), NSMidY(r)))
        bp.appendBezierPathWithArcFromPoint_toPoint_radius_((NSMaxX(r), NSMaxY(r)), (NSMidX(r), NSMaxY(r)), radius)
        bp.appendBezierPathWithArcFromPoint_toPoint_radius_((NSMinX(r), NSMaxY(r)), (NSMinX(r), NSMidY(r)), radius)
        bp.appendBezierPathWithArcFromPoint_toPoint_radius_((NSMinX(r), NSMinY(r)), (NSMidX(r), NSMinY(r)), radius)
        bp.appendBezierPathWithArcFromPoint_toPoint_radius_((NSMaxX(r), NSMinY(r)), (NSMaxX(r), NSMidY(r)), radius)
        bp.closePath()
        return bp


class DropboxHorizontalLine(NSBox):

    def verticalPadding(self):
        return 12

    def horizontalPadding(self):
        return 12

    def __new__(cls, width):
        return cls.alloc().initForParentWidth_(width)

    def initForParentWidth_(self, width):
        self = super(DropboxHorizontalLine, self).initWithFrame_(NSRect((0, 0), (width - self.horizontalPadding() * 2, 1)))
        if self is None:
            return
        self.setBoxType_(NSBoxSeparator)
        return self


class NSButton(Category(NSButton)):

    def verticalPadding(self):
        if self.bezelStyle() == 0:
            return 6
        else:
            return 8

    def baselineOffset(self):
        if self.bezelStyle() == NSHelpButtonBezelStyle:
            return 4
        return 0

    def flippedBaselineOffset(self):
        return 5

    def insetRect(self):
        if self.bezelStyle() == NSHelpButtonBezelStyle:
            return NSMakeRect(-3, -4, -6, -5)
        if self.bezelStyle() == NSRoundedBezelStyle:
            return NSMakeRect(-3, -8, -12, -12)
        return NSZeroRect

    def setTextColor_(self, textColor):
        attr_str = NSMutableAttributedString.alloc().initWithAttributedString_(self.attributedTitle())
        r = NSMakeRange(0, attr_str.length())
        attr_str.addAttribute_value_range_(NSForegroundColorAttributeName, textColor, r)
        attr_str.fixAttributesInRange_(r)
        self.setAttributedTitle_(attr_str)

    def sizeToFitWithPadding(self):
        self.sizeToFit()
        new_frame = self.frame()
        new_frame.size.width = max(96, NSWidth(new_frame) + 12)
        self.setFrame_(new_frame)

    @classmethod
    def createNormalRoundButtonWithTitle_(cls, title):
        return cls.createNormalRoundButtonWithTitle_default_(title, False)

    @classmethod
    def createNormalRoundButtonWithTitle_default_(cls, title, default):
        return cls.createNormalRoundButtonWithTitle_default_origin_(title, default, (0, 0))

    @classmethod
    def createNormalRoundButtonWithTitle_default_origin_(cls, title, default, origin):
        if isinstance(cls, objc_object):
            cls = cls.__class__
        button = cls.alloc().initWithFrame_(NSRect(origin, (0, 0)))
        button.setBezelStyle_(NSRoundedBezelStyle)
        button.setButtonType_(NSMomentaryPushInButton)
        button.setFont_(NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize)))
        if default:
            button.setKeyEquivalent_(ENTER_KEY)
        button.setTitle_(title)
        button.sizeToFitWithPadding()
        return button

    @classmethod
    def createNormalCheckboxWithTitle_(cls, title):
        return cls.createNormalCheckboxWithTitle_origin_(title, (0, 0))

    @classmethod
    def createNormalCheckboxWithTitle_origin_(cls, title, origin):
        if isinstance(cls, objc_object):
            cls = cls.__class__
        button = cls.alloc().initWithFrame_(NSRect(origin, (0, 0)))
        button.setButtonType_(NSSwitchButton)
        button.setFont_(NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize)))
        button.setAttributedTitle_(NSAttributedString.linkify(title))
        button.sizeToFit()
        return button

    @classmethod
    def createRadioButtonWithTitle_tag_origin_(cls, title, tag, origin):
        if isinstance(cls, objc_object):
            cls = cls.__class__
        button = cls.alloc().initWithFrame_(NSRect(origin, (0, 0)))
        button.setButtonType_(NSRadioButton)
        button.cell().setControlSize_(NSRegularControlSize)
        button.setFont_(NSFont.fontWithName_size_(button.cell().font().fontName(), NSFont.systemFontSize()))
        button.setTitle_(title)
        if tag is not None:
            button.setTag_(tag)
        button.sizeToFit()
        return button

    def placeLeftOfButton_(self, button):
        button_frame = button.frame()
        self.setFrameOrigin_(NSPoint(button_frame.origin.x - NSWidth(self.frame()), button_frame.origin.y))


class NSControl(Category(NSControl)):

    def placeRelativeToLabel_(self, label):
        label_frame = label.frame()
        if label.isFlipped():
            bl_offset = 0
            if hasattr(self, 'flippedBaselineOffset'):
                bl_offset = self.flippedBaselineOffset()
            self.setFrameOrigin_(NSPoint(NSMaxX(label_frame) + LABEL_PADDING + self.insetRect().origin.x, label_frame.origin.y - bl_offset))
        else:
            bl_offset = 0
            if hasattr(self, 'baselineOffset'):
                bl_offset = self.baselineOffset()
            self.setFrameOrigin_(NSPoint(label_frame.origin.x + NSWidth(label_frame) + LABEL_PADDING + self.insetRect().origin.x, label_frame.origin.y + NSHeight(label_frame) - NSHeight(self.frame()) + bl_offset))

    def nextControlY(self):
        return NSMaxY(self.frame()) + self.verticalPadding()


class NSDatePicker(Category(NSDatePicker)):

    def verticalPadding(self):
        return 8

    def baselineOffset(self):
        return 3


class WrappingNSButtonCell(NSButtonCell):

    def init(self):
        self.max_width = 0
        self.baseline = 0
        return super(WrappingNSButtonCell, self).init()

    def cellSize(self):
        orig_size = super(WrappingNSButtonCell, self).cellSize()
        if self.max_width:
            max_text_width = self.max_width - self.image().size().width - 4
            text_rect = self.attributedTitle().boundingRectWithSize_options_(NSSize(max_text_width, 0), NSStringDrawingUsesLineFragmentOrigin)
            ret = NSSize(int(math.ceil(NSWidth(text_rect))) + 4 + self.image().size().width, max(NSHeight(text_rect), self.image().size().height))
            self.baseline = (ret.height - orig_size.height) / 2
            return ret
        return orig_size

    @event_handler
    def drawTitle_withFrame_inView_(self, title, frame, view):
        if self.max_width:
            title.drawWithRect_options_(frame, NSStringDrawingUsesLineFragmentOrigin)
            return frame
        else:
            return super(WrappingNSButtonCell, self).drawTitle_withFrame_inView_(title, frame, view)

    @event_handler
    def drawImage_withFrame_inView_(self, image, frame, view):
        if self.max_width and self.baseline:
            frame = NSRect((frame.origin.x, frame.origin.y - self.baseline), (frame.size.width, frame.size.height))
        return super(WrappingNSButtonCell, self).drawImage_withFrame_inView_(image, frame, view)

    def setMaxWidth_(self, max_width):
        self.max_width = max_width


class NSMatrix(Category(NSMatrix)):

    def verticalPadding(self):
        return 12

    def baselineOffset(self):
        return 0

    @classmethod
    def createRadioGroup_(cls, choices):
        return NSMatrix.createRadioGroup_verticalSpacing_maxWidth_(choices, 4, None)

    @classmethod
    def createRadioGroup_verticalSpacing_maxWidth_(cls, choices, vertical_spacing, max_width):
        matrix = NSMatrix.alloc().initWithFrame_mode_cellClass_numberOfRows_numberOfColumns_(NSZeroRect, NSRadioModeMatrix, WrappingNSButtonCell, 0, 1)
        matrix.setIntercellSpacing_(NSSize(2, vertical_spacing))
        cell_font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        for x, text in enumerate(choices):
            cell = matrix.makeCellAtRow_column_(x, 1)
            cell.setLineBreakMode_(0)
            cell.setWraps_(YES)
            cell.setTitle_(text)
            cell.setButtonType_(NSRadioButton)
            cell.setFont_(cell_font)
            cell.setTag_(x)
            cell.setMaxWidth_(max_width)
            matrix.addRowWithCells_([cell])

        matrix.selectCellAtRow_column_(1, 1)
        matrix.sizeToFit()
        return matrix


class NSPopUpButton(Category(NSPopUpButton)):

    def insetRect(self):
        return NSZeroRect

    def verticalPadding(self):
        return 16

    def flippedBaselineOffset(self):
        return 3

    def baselineOffset(self):
        return 6

    @classmethod
    def createNormalPopUpButtonWithChoices_default_(cls, choices, default):
        return NSPopUpButton.createNormalPopUpButtonWithChoices_default_origin_(choices, default, (0, 0))

    @classmethod
    def createNormalPopUpButtonWithChoices_default_origin_(cls, choices, default, origin):
        choice = NSPopUpButton.alloc().initWithFrame_(NSRect(origin, (0, 0)))
        choice.addItemsWithTitles_(choices)
        choice.selectItemAtIndex_(default)
        choice.sizeToFit()
        return choice


class NSProgressIndicator(Category(NSProgressIndicator)):

    @classmethod
    def createSmallSpinner(cls):
        pi = NSProgressIndicator.alloc().initWithFrame_(NSZeroRect)
        pi.setStyle_(NSProgressIndicatorSpinningStyle)
        pi.setControlSize_(NSSmallControlSize)
        pi.setIndeterminate_(YES)
        pi.sizeToFit()
        return pi


class NSSecureTextField(Category(NSSecureTextField)):

    @classmethod
    def createNormalSecureTextField(cls):
        return NSSecureTextField.createNormalSecureTextFieldWithFont_(None)

    @classmethod
    def createNormalSecureTextFieldWithFont_(cls, font):
        return cls.createNormalSecureTextFieldWithFont_initialValue_placeholder_(font, '', None)

    @classmethod
    def createNormalSecureTextFieldWithFont_initialValue_placeholder_(cls, font, initialValue = '', placeholder = None):
        if font is None:
            font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        tf = NSSecureTextField.alloc().initWithFrame_(NSZeroRect)
        tf.setBezeled_(YES)
        tf.setDrawsBackground_(YES)
        tf.setEditable_(YES)
        tf.setFont_(font)
        tf.setRefusesFirstResponder_(NO)
        tf.setSelectable_(YES)
        tf.setStringValue_(initialValue)
        if placeholder is not None:
            tf.cell().setPlaceholderString_(placeholder)
        tf.sizeToFit()
        return tf


class NSSearchField(Category(NSSearchField)):

    def horizontalPadding(self):
        return 8

    @classmethod
    def createSearchFieldWithWidth_(cls, width):
        sf = NSSearchField.alloc().initWithFrame_(NSZeroRect)
        sf.sizeToFit()
        f = sf.frame()
        f.size.width = width
        sf.setFrame_(f)
        return sf


class NSStepper(Category(NSStepper)):

    def baselineOffset(self):
        return 4

    def horizontalPadding(self):
        return LABEL_PADDING


class NSTextField(Category(NSTextField)):

    def horizontalPadding(self):
        return LABEL_PADDING

    def verticalPadding(self):
        return 10

    def baselineOffset(self):
        if self.drawsBackground():
            return 2
        return 0

    def placeButtonToRight(self, button):
        padding = 4
        button.sizeToFitWithPadding()
        my_frame = self.frame()
        button_origin = NSPoint(my_frame.origin.x + my_frame.size.width + padding, my_frame.origin.y - STATICTEXT_TO_BUTTON_BASELINE_ADJUSTMENT)
        button.setFrameOrigin_(button_origin)
        return NSSize(my_frame.size.width + padding + button.frame().size.width, max(my_frame.size.height + STATICTEXT_TO_BUTTON_BASELINE_ADJUSTMENT, button.frame().size.height))

    def placeDropdownToRight(self, dropdown):
        padding = 4
        dropdown.sizeToFitWithPadding()
        my_frame = self.frame()
        dropdown_origin = NSPoint(my_frame.origin.x + my_frame.size.width + padding, my_frame.origin.y - STATICTEXT_TO_DROPDOWN_BASELINE_ADJUSTMENT)
        dropdown.setFrameOrigin_(dropdown_origin)
        return NSSize(my_frame.size.width + padding + dropdown.frame().size.width, max(my_frame.size.height + STATICTEXT_TO_DROPDOWN_BASELINE_ADJUSTMENT, dropdown.frame().size.height))

    def sizeForWidth_(self, width):
        infinite_height_frame = self.frame()
        infinite_height_frame.size.width = width - infinite_height_frame.origin.x
        infinite_height_frame.size.height = INFINITE_DIMENSION
        return self.cell().cellSizeForBounds_(infinite_height_frame)

    def wrapToWidth_(self, width):
        proper_size = self.sizeForWidth_(width)
        self.setFrameSize_(proper_size)
        return proper_size

    def balancedWrapToWidth_(self, width):
        largest_size = self.sizeForWidth_(INFINITE_DIMENSION)
        cur_size = self.sizeForWidth_(width)
        if cur_size.height > largest_size.height:
            lo = 0
            hi = width
            last = cur_size.height
            while lo <= hi:
                mid = lo + (hi - lo) // 2
                cur_size = self.sizeForWidth_(mid)
                if cur_size.height > last:
                    lo = mid + 1
                else:
                    width = mid
                    hi = mid - 1

        return self.wrapToWidth_(width)

    @classmethod
    def createLabelWithText_(cls, text):
        font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        return NSTextField.createLabelWithText_font_(text, font)

    @classmethod
    def createLabelWithText_origin_(cls, text, origin):
        font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        return NSTextField.createLabelWithText_font_maxWidth_origin_(text, font, None, origin)

    @classmethod
    def createLabelWithText_font_(cls, text, font):
        return NSTextField.createLabelWithText_font_maxWidth_(text, font, None)

    @classmethod
    def createLabelWithText_maxWidth_(cls, text, max_width):
        font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        return NSTextField.createLabelWithText_font_maxWidth_(text, font, max_width)

    @classmethod
    def createLabelWithText_font_maxWidth_(cls, text, font, max_width = None):
        return NSTextField.createLabelWithText_font_maxWidth_origin_(text, font, max_width, (0, 0))

    @classmethod
    def createLabelWithText_font_maxWidth_origin_(cls, text, font, max_width = None, origin = (0, 0)):
        label = NSTextField.alloc().initWithFrame_(NSRect(origin, (0, 0)))
        label.setAllowsEditingTextAttributes_(YES)
        label.setBezeled_(NO)
        label.setDrawsBackground_(NO)
        label.setEditable_(NO)
        label.setFont_(font)
        label.setSelectable_(NO)
        label.setStringValue_(text)
        label.sizeToFit()
        if max_width is not None:
            max_size = NSSize(max_width, 0)
            attrs, r = label.attributedStringValue().attributesAtIndex_effectiveRange_(0, None)
            text_rect = label.stringValue().boundingRectWithSize_options_attributes_(max_size, NSStringDrawingUsesLineFragmentOrigin, attrs)
            label.cell().setWraps_(YES)
            label.setFrameSize_((int(math.ceil(NSWidth(text_rect))) + 4, NSHeight(text_rect)))
        return label

    @classmethod
    def createNormalTextField(cls):
        f = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
        return cls.createNormalTextFieldWithFont_(f)

    @classmethod
    def createNormalTextFieldWithFont_(cls, font):
        return cls.createNormalTextFieldWithFont_initialValue_placeholder_(font, '', None)

    @classmethod
    def createNormalTextFieldWithFont_initialValue_placeholder_(cls, font, initialValue = '', placeholder = None):
        tf = NSTextField.alloc().initWithFrame_(NSZeroRect)
        tf.setBezeled_(YES)
        tf.setDrawsBackground_(YES)
        tf.setEditable_(YES)
        tf.setFont_(font)
        tf.setRefusesFirstResponder_(NO)
        tf.setSelectable_(YES)
        tf.setStringValue_(initialValue)
        if placeholder is not None:
            tf.cell().setPlaceholderString_(placeholder)
        tf.sizeToFit()
        return tf

    def placeRelativeToControl_(self, control):
        bl_offset = 0
        if hasattr(control, 'baselineOffset'):
            bl_offset = control.baselineOffset()
        self.setFrameOrigin_(NSPoint(control.frame().origin.x - NSWidth(self.frame()) - LABEL_PADDING, control.frame().origin.y + bl_offset))


class NSView(Category(NSView)):

    def insetRect(self):
        return NSZeroRect

    def alignRightInSuperview(self, offset = CONTENT_BORDER):
        parent_bounds = self.superview().bounds()
        self.setFrameOrigin_(NSPoint(parent_bounds.origin.x + NSWidth(parent_bounds) - NSWidth(self.frame()) - offset - self.insetRect().origin.x, self.frame().origin.y))

    def alignLeftInSuperview(self, offset = CONTENT_BORDER):
        parent_bounds = self.superview().bounds()
        self.setFrameOrigin_(NSPoint(parent_bounds.origin.x + offset + self.insetRect().origin.x, self.frame().origin.y))

    def alignRightToOffset_(self, offset):
        self.setFrameOrigin_(NSPoint(offset - NSWidth(self.frame()) - self.insetRect().origin.x, self.frame().origin.y))

    def alignLeftToOffset_(self, offset):
        self.setFrameOrigin_(NSPoint(offset + self.insetRect().origin.x, self.frame().origin.y))

    def offsetFrame_(self, offset):
        f = self.frame()
        self.setFrameOrigin_(NSPoint(f.origin.x + offset.x, f.origin.y + offset.y))

    def alignBottomInSuperview(self, offset = CONTENT_BORDER):
        parent_bounds = self.superview().bounds()
        if not self.superview().isFlipped():
            self.setFrameOrigin_(NSPoint(self.frame().origin.x, parent_bounds.origin.y + offset + self.insetRect().origin.y))
        else:
            self.setFrameOrigin_(NSPoint(self.frame().origin.x, parent_bounds.origin.y + NSHeight(parent_bounds) - offset - NSHeight(self.frame()) - self.insetRect().origin.y))

    def addNormalRoundButtonWithTitle_action_(self, title, action):
        button = NSButton.createNormalRoundButtonWithTitle_(title)
        button.setTarget_(self)
        button.setAction_(action)
        self.addSubview_(button)
        return button

    def addNormalTextFieldWithLabel_(self, text):
        label = NSTextField.createLabelWithText_(text)
        self.addSubview_(label)
        return label

    def centerInSuperview(self):
        if self.superview():
            self.centerHorizontallyInSuperview()
            self.centerVerticallyInSuperview()

    def centerHorizontallyInSuperview(self):
        parent_bounds = self.superview().bounds()
        self.setFrameOrigin_(NSPoint(parent_bounds.origin.x + NSWidth(parent_bounds) / 2.0 - NSWidth(self.frame()) / 2.0, self.frame().origin.y))

    def centerVerticallyInSuperview(self):
        parent_bounds = self.superview().bounds()
        self.setFrameOrigin_(NSPoint(self.frame().origin.x, parent_bounds.origin.y + NSHeight(parent_bounds) / 2.0 - NSHeight(self.frame()) / 2.0))


class NSWindow(Category(NSWindow)):

    def setSticky_(self, flag):
        if MAC_VERSION <= TIGER:
            TRACE("Not changing stickiness; we're on 10.4 or earlier")
            return
        try:
            wid = self.windowNumber()
            TRACE("Trying to change window id %r's stickiness", wid)
            if wid > 0:
                cglib = cdll.LoadLibrary(find_library('ApplicationServices'))
                cid = cglib._CGSDefaultConnection()
                tags = (c_int32 * 2)(0, 0)
                if not cglib.CGSGetWindowTags(cid, wid, tags, 32):
                    tags[0] = tags[0] | 2048 if flag else tags[0] & 2048
                    cglib.CGSSetWindowTags(cid, wid, tags, 32)
        except Exception:
            unhandled_exc_handler()


class ManagedRadioButton(NSButton):

    def __new__(cls, frame, title, tag):
        return ManagedRadioButton.alloc().initWithFrame_title_tag_(frame, title, tag)

    def initWithFrame_title_tag_(self, frame, title, tag):
        self = super(ManagedRadioButton, self).initWithFrame_(frame)
        if self is not None:
            self.setButtonType_(NSRadioButton)
            self.cell().setControlSize_(NSRegularControlSize)
            self.setFont_(NSFont.fontWithName_size_(self.cell().font().fontName(), NSFont.systemFontSize()))
        self.setTitle_(title)
        if tag is not None:
            self.setTag_(tag)
        self.sizeToFit()
        return self

    def acceptsFirstResponder(self):
        return False

    def mouseDown_(self, event):
        if self.superview() is not None:
            self.superview().mouseDown_(event)

    def mouseUp_(self, event):
        if self.superview() is not None:
            self.superview().mouseUp_(event)


def help_button(x, y):
    button = NSButton.alloc().initWithFrame_(NSRect((x, y), (0, 0)))
    button.setTitle_('')
    button.setBezelStyle_(NSHelpButtonBezelStyle)
    button.cell().setControlSize_(NSRegularControlSize)
    button.sizeToFit()
    return button


def height_for_fixed_width(theControl, width):
    infinite_height_frame = theControl.frame()
    infinite_height_frame.size.width = width - infinite_height_frame.origin.x
    infinite_height_frame.size.height = INFINITE_DIMENSION
    proper_frame = theControl.cell().cellSizeForBounds_(infinite_height_frame)
    theControl.setFrame_(NSRect((infinite_height_frame.origin.x, infinite_height_frame.origin.y), (proper_frame.width, proper_frame.height)))
    return proper_frame.height


def align_center_to_offset(theControl, offset):
    new_frame = theControl.frame()
    new_frame.origin.x = offset - new_frame.size.width / 2.0
    theControl.setFrame_(new_frame)
