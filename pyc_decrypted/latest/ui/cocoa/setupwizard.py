#Embedded file name: ui/cocoa/setupwizard.py
from __future__ import absolute_import
import math
import os
from objc import YES, NO, typedSelector
from AppKit import NSAlertAlternateReturn, NSBackingStoreBuffered, NSBeginAlertSheet, NSBox, NSButton, NSApp, NSCalendar, NSClosableWindowMask, NSDatePicker, NSFloatingWindowLevel, NSFont, NSLeftTextAlignment, NSLineBreakByWordWrapping, NSMatrix, NSMenuItem, NSNormalWindowLevel, NSPopUpButton, NSRegularControlSize, NSSecureTextField, NSSmallControlSize, NSStringDrawingUsesLineFragmentOrigin, NSTextField, NSTitledWindowMask, NSWindow, NSYearMonthDatePickerElementFlag
from Foundation import NSDate, NSGregorianCalendar, NSInsetRect, NSHeight, NSMakeRect, NSMonthCalendarUnit, NSPoint, NSSize, NSRect, NSWidth, NSYearCalendarUnit, NSZeroRect
from PyObjCTools import AppHelper
from Quartz import NSBezierPath
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from .constants import Colors
from .dropbox_controls import BackgroundImageView, CheckboxWithLink, CreditCardTypeView, CocoaDropboxLocationChanger, DropboxLocationSheetMixin, FancyRadioGroup as FancyRadioGroupView, FancyRadioView, FlagPopUpButton, HelpButton as HelpButtonControl, ImageView, PlanView, TextFieldWithLink
from .selective_sync import SelectiveSyncLauncher
from .util import protected_action_method, save_graphics_state
from ..common.misc import MiscStrings
from ..common.setupwizard import Button, CenteredMultiControlLine, Checkbox, Choice, CreditCardType, Date, ExampleText, FancyRadioGroup, FlagChoice, HelpButton, HorizSpacer, Image, LocationChanger, MultiControlLine, MultiControlLineSimple, PlanChoices, RadioGroup, SelectiveSync, SetupWizardStrings, SetupWizardWindowBase, Spacer, TextInput, TextBlock
FLAG_WIDTH = 16
LABEL_PADDING = 8
STATUS_LABEL_HEIGHT = 17
WIZARD_BOX_PADDING = 12
LEFT_SIDE_IMAGE_OFFSET_FROM_TOP = 40 - WIZARD_BOX_PADDING - 6

class SetupWizardBox(NSBox):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, frame):
        return SetupWizardBox.alloc().initWithFrame_(frame)

    @typedSelector(NSBox.performKeyEquivalent_.signature)
    def performKeyEquivalent_(self, event):
        return super(SetupWizardBox, self).performKeyEquivalent_(event)

    @message_sender(AppHelper.callAfter, block=True)
    def initWithFrame_(self, frame):
        self = super(SetupWizardBox, self).initWithFrame_(frame)
        if self:
            self._set_defaults()
        self._title_size = None
        return self

    @typedSelector('v@:')
    @assert_message_queue
    def _set_defaults(self):
        self._inner_padding = WIZARD_BOX_PADDING
        self.titleCell().setLineBreakMode_(NSLineBreakByWordWrapping)
        self.setTitleFont_(NSFont.boldSystemFontOfSize_(14))
        self.titleCell().setTextColor_(Colors.black)
        self.titleCell().setAlignment_(NSLeftTextAlignment)
        self.setBackgroundColor_(Colors.setup_wizard_background)
        self.setBorderColor_(Colors.setup_wizard_border)
        self._resize_content_view()

    @typedSelector('v@:')
    @assert_message_queue
    def _resize_content_view(self):
        cv = self.contentView()
        dx, dy = self.contentViewMargins()
        new_cv_frame = NSInsetRect(self.bg_rect, dx + self._inner_padding, dy + self._inner_padding)
        cv.setFrame_(new_cv_frame)
        cv.setBoundsSize_(new_cv_frame.size)

    @typedSelector('v@:@')
    @assert_message_queue
    def setBackgroundColor_(self, new_color):
        self.background_color = new_color
        self.setNeedsDisplay_(YES)

    @typedSelector('v@:@')
    @assert_message_queue
    def setBorderColor_(self, new_color):
        self.border_color = new_color
        self.setNeedsDisplay_(YES)

    @typedSelector('v@:@')
    @assert_message_queue
    def setTitle_(self, title):
        if title is not None:
            super(SetupWizardBox, self).setTitle_(title)
            self._title_size = None
            self._resize_content_view()

    @typedSelector('v@:@')
    @assert_message_queue
    def setTitleFont_(self, font):
        super(SetupWizardBox, self).setTitleFont_(font)
        self._title_size = None
        self._resize_content_view()

    @property
    @typedSelector('v@:@')
    @assert_message_queue
    def title_size(self):
        bounds = self.bounds()
        if self._title_size is None:
            max_text_width = bounds.size.width - 10
            text_rect = self.titleCell().attributedStringValue().boundingRectWithSize_options_(NSSize(max_text_width, 0), NSStringDrawingUsesLineFragmentOrigin)
            self._title_size = text_rect.size
        return self._title_size

    @property
    @typedSelector('v@')
    @assert_message_queue
    def bg_rect(self):
        bounds = self.bounds()
        return NSMakeRect(bounds.origin.x, bounds.origin.y, bounds.size.width - 1, bounds.size.height - self.title_size.height - 5)

    @protected_action_method
    def drawRect_(self, rect):
        bounds = self.bounds()
        title_rect = NSMakeRect(bounds.origin.x, bounds.origin.y + NSHeight(bounds) - self.title_size.height, math.ceil(self.title_size.width) + 10, self.title_size.height)
        self.titleCell().drawInteriorWithFrame_inView_(title_rect, self)
        bgpath = NSBezierPath.bezierPathWithRect_(self.bg_rect)
        with save_graphics_state() as graphics_context:
            self.background_color.set()
            bgpath.fill()
            graphics_context.setShouldAntialias_(NO)
            self.border_color.set()
            bgpath.stroke()


class SetupWizardWindow(NSWindow, SetupWizardWindowBase, DropboxLocationSheetMixin):
    BUTTON_PADDING_WIDTH = 12
    BOX_LEFT = 18

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, wizard):
        TRACE('Creating Cocoa SetupWizard')
        return SetupWizardWindow.alloc().init(wizard)

    @message_sender(AppHelper.callAfter, block=True)
    def init(self, wizard):
        self = super(SetupWizardWindow, self).initWithContentRect_styleMask_backing_defer_(NSRect((0, 0), (580, 500)), NSTitledWindowMask | NSClosableWindowMask, NSBackingStoreBuffered, NO)
        if self is not None:
            self._wizard = wizard
            self._dropbox_app = wizard.dropbox_app
            self.setReleasedWhenClosed_(NO)
            self.center()
            self.setLevel_(NSFloatingWindowLevel)
            self._system_font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
            self._small_system_font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSSmallControlSize))
            self.setTitle_(SetupWizardStrings.window_title)
            self._renderers = {Button: self._create_button,
             CenteredMultiControlLine: self._create_centered_multi_control_line,
             Checkbox: self._create_checkbox,
             Choice: self._create_choice,
             CreditCardType: self._create_credit_card_type,
             Date: self._create_date,
             ExampleText: self._create_example_text,
             FancyRadioGroup: self._create_fancy_radio_group,
             FlagChoice: self._create_flag_choice,
             HelpButton: self._create_help_button,
             Image: self._create_image,
             LocationChanger: self._create_location_changer,
             MultiControlLine: self._create_multi_control_line,
             MultiControlLineSimple: self._create_multi_control_line,
             TextBlock: self._create_text_block,
             TextInput: self._create_text_input,
             PlanChoices: self._create_plan_choices,
             RadioGroup: self._create_radio_group,
             SelectiveSync: self._create_selective_sync,
             Spacer: self._create_spacer}
            self._buttons = {}
        return self

    @typedSelector('v@:@')
    @event_handler
    def changeLocation_(self, sender):
        return self._changeLocation_(sender)

    @typedSelector('v@:@i@')
    @event_handler
    def openPanelDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        return self._openPanelDidEnd_returnCode_contextInfo_(sheet, returnCode, ctx)

    @property
    def width(self):
        return NSWidth(self.frame())

    @property
    def height(self):
        return NSHeight(self.frame())

    @property
    def next_button(self):
        return self._buttons.get(SetupWizardStrings.next_button, None)

    def disallow_covering(self):
        self.setLevel_(NSFloatingWindowLevel)

    def allow_covering(self):
        self.setLevel_(NSNormalWindowLevel)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def is_shown(self):
        return self.isVisible()

    @protected_action_method
    def clicked_(self, sender):
        if sender.title() in self.current_actions:
            action = self.current_actions[sender.title()]
            self._handle_action(action)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def show_window(self):
        self.makeKeyAndOrderFront_(None)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def _create_contents_and_fill(self):
        view = self._create_view()
        self.setContentView_(view)
        self.recalculateKeyViewLoop()
        self.selectNextKeyView_(self)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def _create_contents_and_replace(self):
        view = self._create_view()
        self._last_view = self.contentView()
        self.setContentView_(view)
        self.recalculateKeyViewLoop()
        self.selectNextKeyView_(self)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_button(self, form_item, val, form_view):
        TRACE("Creating button '%s'" % form_item.label)
        control = NSButton.createNormalRoundButtonWithTitle_(form_item.label)
        control.setAction_(self.buttonAction_)
        control.setTarget_(self)
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_(NSPoint(control.frame().origin.x, self._form_y_offset))
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_checkbox(self, form_item, val, form_view):
        control = CheckboxWithLink(form_item.label)
        control.setAction_(self.checkboxAction_)
        if val is not None:
            control.setIntValue_(val)
        if form_item.bottom_align:
            bottom = self._form_bottom
        else:
            self._form_y_offset -= NSHeight(control.frame())
            bottom = self._form_y_offset
        self._form_y_offset -= NSHeight(control.frame())
        if form_item.left_align:
            cp = control.frame().origin.x
        elif form_item.center:
            cp = min((self._in_box_form_width - NSWidth(control.frame())) / 2, self._in_box_form_width - NSWidth(control.frame()))
        else:
            cp = min(self._center_point, self._in_box_form_width - NSWidth(control.frame()))
        control.setFrameOrigin_(NSPoint(cp, bottom))
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_choice(self, form_item, val, form_view):
        control_label = NSTextField.createLabelWithText_font_(form_item.label, self._system_font)
        control = NSPopUpButton.createNormalPopUpButtonWithChoices_default_(form_item.choices, val)
        control.setAction_(self.popupAction_)
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_(NSPoint(self._center_point - 3, self._form_y_offset))
        if form_item.width != -1:
            f = control.frame()
            control.setFrameSize_((form_item.width, NSHeight(f)))
        control_label.placeRelativeToControl_(control)
        return (control, control_label)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_credit_card_type(self, form_item, val, form_view):
        control = CreditCardTypeView()
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_(NSPoint(self._center_point, self._form_y_offset))
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_date(self, form_item, val, form_view):
        gregorian = NSCalendar.alloc().initWithCalendarIdentifier_(NSGregorianCalendar)
        control_label = NSTextField.createLabelWithText_font_(form_item.label, self._system_font)
        control = NSDatePicker.alloc().initWithFrame_(NSZeroRect)
        control.setCalendar_(gregorian)
        control.setDatePickerElements_(NSYearMonthDatePickerElementFlag)
        control.setDrawsBackground_(YES)
        control.setDateValue_(NSDate.date())
        control.setMinDate_(NSDate.date())
        control.setMaxDate_(NSDate.dateWithString_('2029-12-31 23:59:59 +0600'))
        control.sizeToFit()
        control.setAction_(self.datePickerAction_)
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_(NSPoint(self._center_point, self._form_y_offset))
        control_label.placeRelativeToControl_(control)
        return (control, control_label)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_example_text(self, form_item, val, form_view):
        control = TextFieldWithLink(form_item.text, self._in_box_form_width, size_diff=-2)
        control.setTextColor_(Colors.example_text)
        x = control.frame().origin.x + self._in_box_x_offset
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_(NSPoint(x, self._form_y_offset))
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_flag_choice(self, form_item, val, form_view):
        control_label = NSTextField.createLabelWithText_font_(form_item.label, self._system_font)
        control = FlagPopUpButton(NSZeroRect, FLAG_WIDTH)
        control.sizeToFit()
        control.setAction_(self.popupAction_)
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_(NSPoint(self._center_point - 3, self._form_y_offset))
        if form_item.width != -1:
            f = control.frame()
            control.setFrameSize_((form_item.width, NSHeight(f)))
        control_label.placeRelativeToControl_(control)
        menu = control.menu()
        for choice in form_item.choices:
            img, name, phonecode = choice
            title = u'%s %s' % (name, phonecode)
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, '')
            if img:
                item.setImage_(img)
            menu.addItem_(item)

        control.selectItemAtIndex_(val)
        return (control, control_label)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_help_button(self, form_item, val, form_view):
        control = HelpButtonControl(form_item.hover_text, form_item.url)
        self._form_y_offset -= NSHeight(control.frame())
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_image(self, form_item, val, form_view):
        control = ImageView(form_item.image, form_item.label, form_item.border)
        if form_item.inline:
            self._form_y_offset -= NSHeight(control.frame())
            bottom = self._form_y_offset
        else:
            bottom = 4
        control.setFrameOrigin_(NSPoint(self._in_box_x_offset + self._in_box_form_width / 2 - NSWidth(control.frame()) / 2, bottom))
        return (control, None)

    @typedSelector('v@:@@@')
    def _create_location_changer(self, form_item, val, form_view):
        control = CocoaDropboxLocationChanger(self._wizard.dropbox_app, True)
        control.readOnOpen_withUrlInfo_andWidth_andSyncEngine_andAction_({'dropbox_path': val}, self._wizard.dropbox_app.dropbox_url_info, self._in_box_form_width - self._center_point * 2, None, self.locationChanger_)
        self._form_y_offset -= NSHeight(control.frame())
        self._location_changer_origin = NSPoint(self._center_point, self._form_y_offset)
        control.setFrameOrigin_(self._location_changer_origin)
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_multi_control_line(self, form_item, val, form_view, controls = None):
        last_control, last_label = (None, None)
        new_y = self._form_y_offset
        x_offset = 0
        if controls is None:
            controls = []
        for c in form_item.controls:
            if 'mac' in c.hide_on:
                continue
            old_y = self._form_y_offset
            if c.__class__ == HorizSpacer:
                x_offset += c.width
                continue
            next_control, next_label = self._create_form_item(c, form_view)
            if controls is not None:
                controls.append((next_control, next_label))
            if last_control is None and next_control:
                next_control.setFrameOrigin_((next_control.frame().origin.x + x_offset, next_control.frame().origin.y))
            if last_control is not None:
                padding = 0 if form_item.close_spacing else 8
                label_origin = NSPoint(last_control.frame().origin.x + NSWidth(last_control.frame()) + padding + x_offset, last_label.frame().origin.y if last_label else last_control.frame().origin.y)
                if next_label is not None:
                    next_label.setFrameOrigin_(label_origin)
                if next_control is not None:
                    bl_offset = 0
                    if hasattr(next_control, 'baselineOffset'):
                        bl_offset = next_control.baselineOffset()
                    width_offset = NSWidth(next_label.frame()) if next_label else 0
                    control_origin = NSPoint(label_origin.x + width_offset, label_origin.y - bl_offset)
                    next_control.setFrameOrigin_(control_origin)
            last_control, last_label = next_control, next_label
            x_offset = 0
            new_y = min(new_y, self._form_y_offset)
            self._form_y_offset = old_y

        for next_control, next_label in controls:
            if isinstance(next_control, NSButton):
                control_origin = NSPoint(next_control.frame().origin.x, next_control.frame().origin.y - 8)
                next_control.setFrameOrigin_(control_origin)

        self._form_y_offset = new_y
        return (None, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_centered_multi_control_line(self, form_item, val, form_view):
        controls = []
        self._create_multi_control_line(form_item, val, form_view, controls)
        width = self._in_box_form_width
        last_control, last_label = (None, None)
        for control, label in reversed(controls):
            if control is not None or label is not None:
                last_control = control
                last_label = label
                break

        if last_control is not None:
            controls_width = last_control.frame().origin.x + NSWidth(last_control.frame())
        elif last_label is not None:
            controls_width = last_label.frame().origin.x + NSWidth(last_label.frame())
        else:
            report_bad_assumption('No non-None UI elements at all in CenteredMultiControlLine')
            return (None, None)
        centered_x_offset = (width - controls_width) / 2 + form_item.offset
        for control, label in controls:
            if control is not None:
                control.setFrameOrigin_(NSPoint(control.frame().origin.x + centered_x_offset, control.frame().origin.y))
            if label is not None:
                label.setFrameOrigin_(NSPoint(label.frame().origin.x + centered_x_offset, label.frame().origin.y))

        return (None, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_plan_choices(self, form_item, val, form_view):
        plan_view = PlanView(form_view.bounds())
        first = True
        for i, choice in enumerate(form_item.choices):
            c = plan_view.addPlanChoice_i_(choice, i)
            if val is None and first:
                first = False
                c.selected = True
                setattr(self.current_panel, form_item.attr, choice)
            elif val == choice:
                c.selected = True
                setattr(self.current_panel, form_item.attr, choice)

        if val is not None:
            try:
                plan_view.setSelectedIndex_(int(val))
            except (ValueError, TypeError):
                plan_view.setSelected_(val)

        setattr(self.current_panel, form_item.attr, plan_view.selectedPlan)
        plan_view.setAction_(self.planViewAction_)
        plan_view.sizeToFit()
        plan_view.setFrameOrigin_((plan_view.frame().origin.x, NSHeight(form_view.bounds()) - NSHeight(plan_view.frame())))
        control = plan_view
        self._form_y_offset -= NSHeight(control.frame())
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_fancy_radio_group(self, form_item, val, form_view):
        control = FancyRadioGroupView(form_view.bounds())
        for choice in form_item.choices:
            v = FancyRadioView(choice, control, choice['image'], choice['label'], choice['sublabel'], choice['description'], None)
            control.addChoiceView_(v)

        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_((control.frame().origin.x, self._form_y_offset))
        if val is not None:
            try:
                control.setSelectedIndex_(int(val))
            except (ValueError, TypeError):
                control.setSelected_(val)

        setattr(self.current_panel, form_item.attr, control.selected().data)
        control.setAction_(self.fancyRadioGroupAction_)
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_radio_group(self, form_item, val, form_view):
        if form_item.vertical_spacing is not None:
            control = NSMatrix.createRadioGroup_verticalSpacing_maxWidth_(form_item.choices, form_item.vertical_spacing, form_item.max_width)
        else:
            control = NSMatrix.createRadioGroup_(form_item.choices)
        self._form_y_offset -= NSHeight(control.frame())
        if self.current_panel.advanced:
            control.setFrameOrigin_(NSPoint(self._center_point, self._form_y_offset))
        else:
            control.setFrameOrigin_(NSPoint(form_view.bounds().origin.x + NSWidth(form_view.bounds()) / 2.0 - NSWidth(control.frame()) / 2.0, self._form_y_offset))
        control.setAction_(self.radioGroupAction_)
        if val is not None:
            control.selectCellWithTag_(val)
        form_view.addSubview_(control)
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_text_block(self, form_item, val, form_view):
        w = self._in_box_form_width
        if not form_item.greedy:
            w = None
        control = TextFieldWithLink(form_item.text, w, center=form_item.center, bold=form_item.bold, size_diff=form_item.size_diff, line_height=form_item.line_height)
        if form_item.right_align:
            x = self._center_point + 225 - NSWidth(control.frame())
        else:
            x = control.frame().origin.x + self._in_box_x_offset
        if form_item.bottom_align:
            bottom = self._form_bottom
        else:
            self._form_y_offset -= NSHeight(control.frame())
            bottom = self._form_y_offset
        control.setFrameOrigin_(NSPoint(x, bottom))
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_text_input(self, form_item, val, form_view):
        if form_item.secure:
            control = NSSecureTextField.createNormalSecureTextFieldWithFont_initialValue_placeholder_(self._system_font, val, form_item.placeholder)
        else:
            control = NSTextField.createNormalTextFieldWithFont_initialValue_placeholder_(self._system_font, val, form_item.placeholder)
        setattr(self.current_panel, form_item.attr, val)
        control.setDelegate_(self)
        control_label = NSTextField.createLabelWithText_font_(form_item.label, self._system_font)
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrame_(NSMakeRect(self._center_point, self._form_y_offset, form_item.width, NSHeight(control.frame())))
        control_label.placeRelativeToControl_(control)
        if form_item.sublabel:
            sublabel = NSTextField.createLabelWithText_font_(form_item.sublabel, self._small_system_font)
            self._form_y_offset -= sublabel.frame().size.height
            sublabel.setFrameOrigin_(NSPoint(control.frame().origin.x - LABEL_PADDING - sublabel.frame().size.width, self._form_y_offset))
            form_view.addSubview_(sublabel)
        return (control, control_label)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_selective_sync(self, form_item, val, form_view):
        control = SelectiveSyncLauncher(self._wizard.dropbox_app, False, True)
        control.setAction_(self.selectiveSyncAction_)
        self._form_y_offset -= NSHeight(control.frame())
        control.setFrameOrigin_((self._in_box_form_width - NSWidth(control.frame()), self._form_y_offset))
        return (control, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_spacer(self, form_item, val, form_view):
        self._form_y_offset -= form_item.size
        return (None, None)

    @typedSelector('v@:@@@')
    @assert_message_queue
    def _create_form_item(self, form_item, form_view):
        control = None
        control_label = None
        if form_item.attr is not None:
            val = getattr(self.current_panel, form_item.attr, form_item.default_value)
        else:
            val = form_item.default_value
        if form_item.__class__ in self._renderers:
            control, control_label = self._renderers[form_item.__class__](form_item, val, form_view)
        if control and form_item.disabled:
            control.setEnabled_(NO)
        if hasattr(control, 'verticalPadding'):
            self._form_y_offset -= control.verticalPadding()
        if control is not None:
            form_view.addSubview_(control)
            self.current_controls[control] = form_item.attr
            if hasattr(control, 'action') and control.target() is None:
                control.sendAction_to_(control.action(), self)
        if control_label is not None:
            form_view.addSubview_(control_label)
            self.labels[form_item.attr] = control_label
        if self._first_control is None and control is not None and control.acceptsFirstResponder():
            self._first_control = control
            self.setInitialFirstResponder_(control)
        if self._first_item is None:
            self._first_item = control_label or control
        return (control, control_label)

    @typedSelector('v@:')
    @assert_message_queue
    def _create_view(self):
        self.current_actions = {}
        self.current_controls = {}
        self.labels = {}
        self._window_y_offset = 0
        view = BackgroundImageView(self.frame(), self.current_panel.background_image, bottom_align=True)
        if self.current_panel.buttons:
            self._add_buttons(self.current_panel.buttons, view)
        if self.current_panel.tour and self.current_panel.progress_text:
            prog = self._add_progress_text(self.current_panel.progress_text, view)
        self._in_box_x_offset = 0
        if self.current_panel.left_side_image:
            lsi = self.current_panel.left_side_image
            lsi_control = ImageView(lsi.image, lsi.label, lsi.border)
            lsi_box_width = lsi.image.size().width + 2 * self.current_panel.left_side_image_padding
            self._in_box_x_offset = lsi_box_width
        if self.current_panel.full_sized_form:
            r = NSRect((self.BOX_LEFT, self._window_y_offset), (self.width - 36, self.height - self._window_y_offset - 14 - 20 - 6))
            if self.current_panel.left_side_image:
                self._center_point = self._in_box_x_offset
            else:
                self._center_point = NSWidth(r) - 330 - 20
        else:
            r = NSRect((178, self._window_y_offset), (self.width - 178 - 17, self.height - self._window_y_offset - 14 - 20 - 6))
            self._center_point = NSWidth(r) - 200 - 40
        if self.current_panel.tour or self.current_panel.advanced:
            if not self.current_panel.left_side_image:
                self._center_point = 10
            self._form_bottom = 0
        else:
            self._form_bottom = 24
        self._form_box = SetupWizardBox(r)
        self._form_box.setTitle_(self.current_panel.title)
        form_view = self._form_box.contentView()
        self._form_y_offset = self._window_y_offset
        self._in_box_form_width = NSWidth(form_view.frame()) - self._in_box_x_offset
        if self.current_panel.form_contents:
            self._form_y_offset = NSHeight(form_view.frame()) - 1
            self._first_control = None
            self._first_item = None
            for form_item in self.current_panel.form_contents:
                if 'mac' in form_item.hide_on:
                    continue
                control, control_label = self._create_form_item(form_item, form_view)

            self._add_form_status_label(form_view)
        if self.current_panel.left_side_image:
            assert self._first_item is not None
            y = NSHeight(form_view.frame()) - NSHeight(lsi_control.frame()) - LEFT_SIDE_IMAGE_OFFSET_FROM_TOP
            x = max(0, self.current_panel.left_side_image_padding - 8)
            lsi_control.setFrameOrigin_((x, y))
            self._form_box.addSubview_(lsi_control)
        view.addSubview_(self._form_box)
        self.set_focus_on_control(self.current_panel.focus_attr)
        return view

    @typedSelector('v@:@@')
    @assert_message_queue
    def _add_progress_text(self, progress_text, view):
        prog = NSTextField.createLabelWithText_(progress_text)
        prog.setFrameOrigin_(NSPoint(self.BOX_LEFT, self._window_y_offset))
        view.addSubview_(prog)
        prog.alignBottomInSuperview()
        offset = -2
        prog.setFrameOrigin_(NSPoint(prog.frame().origin.x, prog.frame().origin.y - offset))
        return prog

    @typedSelector('v@:@@')
    @assert_message_queue
    def _add_buttons(self, buttons, view):
        self._buttons = {}
        button_x = self.width - self.BUTTON_PADDING_WIDTH
        first = True
        for title, action in reversed(buttons):
            button = NSButton.createNormalRoundButtonWithTitle_default_origin_(title, first, (button_x, self._window_y_offset))
            button.setAction_(self.clicked_)
            if action is not None:
                self.current_actions[title] = action
            else:
                button.setEnabled_(NO)
            first = False
            button_x -= NSWidth(button.frame())
            button.setFrameOrigin_(NSPoint(button_x, self._window_y_offset))
            view.addSubview_(button)
            button.alignBottomInSuperview()
            self._buttons[title] = button

        self._window_y_offset += 19
        self._window_y_offset += NSHeight(button.frame()) + button.verticalPadding()

    @typedSelector('v@:ss')
    @assert_message_queue
    def update_button_title(self, old_title, new_title):
        if old_title in self._buttons:
            b = self._buttons.pop(old_title)
            a = self.current_actions.pop(old_title, None)
            b.setTitle_(new_title)
            self._buttons[new_title] = b
            self.current_actions[new_title] = a

    def _add_form_status_label(self, form_view):
        self._form_status_label = TextFieldWithLink('X', max_width=self._in_box_form_width, center=True)
        self._form_status_label.setFont_(self._small_system_font)
        self._form_status_label.sizeToFit()
        self._form_status_label.setStringValue_('')
        self._form_status_label.setFrameOrigin_(NSPoint(50, STATUS_LABEL_HEIGHT - NSHeight(self._form_status_label.frame())))
        form_view.addSubview_(self._form_status_label)

    @typedSelector('v@:si')
    @message_sender(AppHelper.callAfter)
    def set_form_status(self, status, error = False):
        self._form_status_label.setStringValue_(status)
        self._form_status_label.sizeToFit()
        self._form_status_label.centerHorizontallyInSuperview()
        if error:
            self._form_status_label.setTextColor_(Colors.text_error)
        else:
            self._form_status_label.setTextColor_(Colors.black)
        self._form_status_label.superview().setNeedsDisplay_(YES)

    def select_all_in_control(self, attr):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.selectText_(self)
                break
        else:
            TRACE("!! Tried to select_all_in_control %r when it doesn't exist", attr)

    def set_example_text(self, attr, text, error = False):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.setTextColor_(Colors.text_error if error else Colors.black)
                control.setStringValue_(text)
                control.sizeToFit()
                control.superview().setNeedsDisplay_(YES)
                break
        else:
            TRACE("!! Tried to set_example_text_error %r when it doesn't exist", attr)

    @typedSelector('v@:@@')
    @message_sender(AppHelper.callAfter, block=True)
    def _mark_label_as_error(self, attr_name, is_error):
        assert attr_name in self.labels
        color = Colors.text_error if is_error else Colors.black
        self.labels[attr_name].setTextColor_(color)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def _update_next_button(self):
        if self.next_button and self.current_panel:
            self.next_button.setEnabled_(self.current_panel.form_is_valid)

    @typedSelector('v@:i')
    @message_sender(AppHelper.callAfter, block=True)
    def set_next_button_enabled(self, enabled):
        self.next_button.setEnabled_(enabled)

    def update_panel_attr(self, sender, val, quiet = False):
        if sender not in self.current_controls:
            TRACE('Received event from unregistered control: %r, %r', sender, self.current_controls)
            return
        setattr(self.current_panel, self.current_controls[sender], val)
        if not quiet:
            TRACE("Panel attribute '%r' changed. New value is '%r'" % (self.current_controls[sender], val))
        self.current_panel.form_item_changed(self.current_controls[sender], val)
        self._update_next_button()

    @protected_action_method
    def buttonAction_(self, sender):
        for item in self.current_panel.form_contents:
            if item.attr == self.current_controls[sender] and callable(item.action):
                item.action()
                return
            if hasattr(item, 'controls'):
                for c in item.controls:
                    if c.attr == self.current_controls[sender] and callable(c.action):
                        c.action()
                        return

    @protected_action_method
    def checkboxAction_(self, sender):
        val = bool(sender.intValue())
        self.update_panel_attr(sender, val)

    @protected_action_method
    def datePickerAction_(self, sender):
        date = sender.dateValue()
        gregorian = NSCalendar.alloc().initWithCalendarIdentifier_(NSGregorianCalendar)
        components = gregorian.components_fromDate_(NSYearCalendarUnit | NSMonthCalendarUnit, date)
        val = [components.month(), components.year()]
        self.update_panel_attr(sender, val)

    @protected_action_method
    def locationChanger_(self, sender):
        val = sender.targetPath
        form_view_frame = self._form_box.contentView().frame()
        sender.readOnOpen_withUrlInfo_andWidth_andSyncEngine_andAction_({'dropbox_path': val}, self._wizard.dropbox_app.dropbox_url_info, NSWidth(form_view_frame) - self._center_point, None, self.locationChanger_)
        sender.setFrameOrigin_(self._location_changer_origin)
        self.update_panel_attr(sender, val)

    @protected_action_method
    def fancyRadioGroupAction_(self, sender):
        val = sender.selected().data
        self.update_panel_attr(sender, val, quiet=True)

    @protected_action_method
    def planViewAction_(self, sender):
        val = sender.selectedPlan
        self.update_panel_attr(sender, val)

    @protected_action_method
    def popupAction_(self, sender):
        val = sender.indexOfSelectedItem()
        self.update_panel_attr(sender, val)

    @protected_action_method
    def radioGroupAction_(self, sender):
        val = sender.selectedCell().tag() if sender.selectedCell() is not None else None
        self.update_panel_attr(sender, val)

    @protected_action_method
    def selectiveSyncAction_(self, sender):
        val = sender.current_ignore_list
        self.update_panel_attr(sender, val)

    @protected_action_method
    def controlTextDidChange_(self, notification):
        control = notification.object()
        val = control.stringValue()
        self.update_panel_attr(control, val, True)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def raise_window(self):
        self.makeKeyAndOrderFront_(None)
        NSApp().activateIgnoringOtherApps_(True)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def disable_buttons(self):
        for button in self._buttons.itervalues():
            button.setEnabled_(NO)

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter, block=True)
    def enable_buttons(self):
        for button in self._buttons.itervalues():
            button.setEnabled_(YES)

    @protected_action_method
    def windowShouldClose_(self, sender):
        NSBeginAlertSheet(self._wizard.exit_prompt, self._wizard.exit_button, MiscStrings.cancel_button, None, self, self, self.acceptedSheet_returnCode_contextInfo_, None, 0, u'')
        return NO

    def wantsDropboxWindowMenuEvents(self):
        return YES

    @typedSelector('v@:@ii')
    def acceptedSheet_returnCode_contextInfo_(self, sheet, return_code, context_info):
        if return_code == NSAlertAlternateReturn:
            TRACE('User decided not to close the SetupWizard')
            return
        self._wizard.exit()

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter)
    def on_finish(self):
        self.current_panel.on_swap_out()
        self.close()

    @typedSelector('v@:@@')
    @message_sender(AppHelper.callAfter)
    def set_control_value(self, attr, value):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.setStringValue_(value)
                break
        else:
            TRACE("!! Tried to set control value %r when it doesn't exist", attr)

    @typedSelector('v@:@@')
    @message_sender(AppHelper.callAfter)
    def set_control_hidden(self, attr, value):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.setHidden_(value)
                break
        else:
            TRACE("!! Tried to hide/show %r when it doesn't exist", attr)

    @typedSelector('v@:@@')
    @message_sender(AppHelper.callAfter)
    def set_control_enabled(self, attr, value):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.setEnabled_(value)
                break
        else:
            TRACE("!! Tried to enable/disable %r when it doesn't exist", attr)

    @typedSelector('v@:@')
    @message_sender(AppHelper.callAfter)
    def set_focus_on_control(self, attr):
        if attr:
            try:
                for control, control_attr in self.current_controls.iteritems():
                    if attr == control_attr:
                        self.makeFirstResponder_(control)
                        break
                else:
                    TRACE("!! Tried to set focus on %r when it doesn't exist", attr)

            except Exception:
                unhandled_exc_handler()

    @typedSelector('v@:@@@')
    @message_sender(AppHelper.callAfter)
    def ask_yes_no(self, prompt, yes_button_text, no_button_text, expl_text = None, on_yes = None, on_no = None):
        TRACE("Asking user '%r'" % prompt)
        self._on_yes = on_yes
        self._on_no = on_no
        NSBeginAlertSheet(prompt, yes_button_text, no_button_text, None, self, self, self.askYesNoSheet_returnCode_contextInfo_, None, 0, '%@', expl_text if expl_text else '')

    @typedSelector('v@:@ii')
    def askYesNoSheet_returnCode_contextInfo_(self, sheet, return_code, context_info):
        if return_code == NSAlertAlternateReturn:
            if callable(self._on_no):
                self._on_no()
        elif callable(self._on_yes()):
            self._on_yes()
        del self._on_no
        del self._on_yes

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter)
    def choose_dropbox_location(self, on_location = None):
        self.initialSelection = os.path.dirname(self._wizard.dropbox_path)
        self.syncEngine = None
        self.window = lambda : self
        if callable(on_location):

            def callback(sender):
                on_location(sender.targetPath)

            self._action = callback
        else:
            self._action = None
        self.changeLocation_(self)
