#Embedded file name: ui/wxpython/setupwizard2.py
from __future__ import absolute_import
from functools import partial
import wx
import wx.combo
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.trace import TRACE, unhandled_exc_handler
from ..common.misc import MiscStrings
from ..common.setupwizard import AdvancedPanelRadioGroup, Button, CenteredMultiControlLine, Checkbox, CheckboxLink, Choice, CreditCardType, Date, ExampleText, FancyRadioGroup, FlagChoice, Image, HelpButton, HorizSpacer, LocationChanger, FancyGauge, MultiControlLine, MultiControlLineSimple, PlanChoices, RadioGroup, SelectiveSync, SetupWizardStrings, SetupWizardWindowBase, Spacer, TextBlock, TextInput, WelcomePanel
from .constants import Colors, platform, GNOME
from .dialogs import DropboxModalDialog
from .dropbox_controls import AdvancedWizardRadioGroup, AutoTip, CreditCardTypePanel, DatePicker, DropboxFlagChoice, EVT_DATE_PICKER_CHANGED, FancyGaugePanel, PlanChoicesWidget, TransparentPanel, TransparentStaticBitmap, TransparentStaticText, WizardRadioGroup
from .background_panel import BackgroundPanel
from .location_changer import DropboxLocationChanger, EVT_DROPBOX_LOCATION_CHANGED, request_valid_dropbox_path_from_user
from .selective_sync import EVT_IGNORE_LIST_CHANGED, SelectiveSyncLauncher
from .static_link_text import StaticLinkText
from .util import wordwrap
from ui.images import wximages as Images
WINDOW_HEIGHT = 480
FORM_CONTENT_WIDTH = 480
TITLE_WIDTH = 500
WINDOW_WIDTH = 510
DEFAULT_BORDER = 10
_SHOULD_OVERRIDE_SYSTEM_COLORS = platform == GNOME

class SetupWizardWindow(wx.Frame, SetupWizardWindowBase):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, wizard):
        pre = wx.PreFrame()
        pre.Show(False)
        pre.Create(None, size=(WINDOW_WIDTH, WINDOW_HEIGHT), style=platform.simple_frame_style)
        self.PostCreate(pre)
        self._wizard = wizard
        self._done = False
        self.border = wx.BoxSizer(wx.HORIZONTAL)
        self.AutoLayout = True
        self.Sizer = self.border
        self.Title = SetupWizardStrings.window_title
        platform.frame_icon(self)
        self._renderers = {AdvancedPanelRadioGroup: self._create_advanced_panel_radio_group,
         Button: self._create_button,
         CenteredMultiControlLine: self._create_centered_multi_control_line,
         Checkbox: self._create_checkbox,
         CheckboxLink: self._create_checkbox_link,
         Choice: self._create_choice,
         CreditCardType: self._create_credit_card_type,
         Date: self._create_date,
         ExampleText: self._create_example_text,
         FancyRadioGroup: self._create_fancy_radio_group,
         FlagChoice: self._create_flag_choice,
         HelpButton: self._create_help_button,
         HorizSpacer: self._create_horiz_spacer,
         Image: self._create_image,
         LocationChanger: self._create_location_changer,
         MultiControlLine: self._create_multi_control_line,
         MultiControlLineSimple: self._create_multi_control_line_simple,
         TextBlock: self._create_text_block,
         TextInput: self._create_text_input,
         FancyGauge: self._create_fancy_gauge,
         PlanChoices: self._create_plan_choices,
         RadioGroup: self._create_radio_group,
         SelectiveSync: self._create_selective_sync,
         Spacer: self._create_spacer}
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self._buttons = {}

    @property
    def next_button(self):
        return self._buttons.get(SetupWizardStrings.next_button, None)

    @message_sender(wx.CallAfter, block=True)
    def is_shown(self):
        return self.IsShown()

    @message_sender(wx.CallAfter)
    def raise_window(self):
        self.Raise()

    def allow_covering(self):
        pass

    def disallow_covering(self):
        pass

    @message_sender(wx.CallAfter)
    def show_window(self):
        self.CenterOnScreen()
        self.Show(True)

    @message_sender(wx.CallAfter)
    def on_finish(self):
        self.current_panel.on_swap_out()
        self._done = True
        self.Close()

    @message_sender(wx.CallAfter)
    def update_button_title(self, old_title, new_title):
        if old_title in self._buttons:
            b = self._buttons.pop(old_title)
            a = self.current_actions.pop(old_title, None)
            b.Label = new_title
            self._buttons[new_title] = b
            self.current_actions[new_title] = a

    @message_sender(wx.CallAfter)
    def _create_contents_and_fill(self):
        panel = self._create_panel()
        panel.Show(True)
        self.current_contents = panel
        self.border.Add(panel, proportion=1, flag=wx.EXPAND)
        self.border.Layout()

    @message_sender(wx.CallAfter)
    def _create_contents_and_replace(self, block = True):
        self.Freeze()
        panel = self._create_panel()
        w, h = self.current_contents.Size
        panel.SetDimensions(0, 0, w, h)
        self.border.Replace(self.current_contents, panel)
        self.border.Layout()
        self.current_contents.Show(False)
        self.current_contents.Destroy()
        panel.Show(True)
        self.current_contents = panel
        self.Thaw()

    @assert_message_queue
    def set_control_value(self, attr, value):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.SetValue(value)

    @assert_message_queue
    def _send_fake_event(self, control, event_type):
        fake_event = wx.CommandEvent(event_type.typeId, control.Id)
        fake_event.EventObject = control
        wx.PostEvent(self, fake_event)

    @assert_message_queue
    def _bind_and_trigger(self, control, handler, event):
        self.Bind(event, handler, control)
        self._send_fake_event(control, event)

    @assert_message_queue
    def _create_advanced_panel_radio_group(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = AdvancedWizardRadioGroup(form_view, form_item.choices)
        old_row = self._row
        self._row = 1
        for i, ctls in enumerate(form_item.embedded_controls):
            for ctl in ctls:
                subctl, sublabel = self._create_form_item(ctl, control[i], control[i].subcontrol_sizer)
                if subctl:
                    control[i].setup_bindings(subctl)
                if sublabel:
                    control[i].setup_bindings(sublabel)
                self._row += 1

        self._row = old_row
        control.SetValue(val)
        self._bind_and_trigger(control, self.OnAdvancedPanelRadioGroup, wx.EVT_CHOICE)
        parent_sizer.Add(control, pos=(self._row, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
        return (control, None)

    @assert_message_queue
    def _create_button(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = wx.Button(form_view, label=form_item.label)
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        self.Bind(wx.EVT_BUTTON, self.OnButtonClicked, control)
        self.current_actions[form_item.label] = form_item.action
        if filling_multi_control_simple:
            parent_sizer.Add(control)
        else:
            parent_sizer.Add(control, pos=(self._row, 0), span=(1, 2))
        return (control, None)

    @assert_message_queue
    def _create_checkbox(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = wx.CheckBox(form_view, label=form_item.label)
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control.Value = val
        self._bind_and_trigger(control, self.OnCheckBox, wx.EVT_CHECKBOX)
        parent_sizer.Add(control, pos=(self._row, 0 if form_item.left_align else 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=DEFAULT_BORDER if form_item.left_align else 0)
        return (control, None)

    @assert_message_queue
    def _create_checkbox_link(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = wx.CheckBox(form_view, label='')
        platform.apply_tour_font(control)
        control.Value = val
        label = StaticLinkText(form_view, label=form_item.label, on_click=partial(self.OnCheckBoxLabelMouseUp, checkbox=control))
        platform.apply_tour_font(label)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(control, 0, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5)
        sizer.Add(label, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        self._bind_and_trigger(control, self.OnCheckBox, wx.EVT_CHECKBOX)
        parent_sizer.Add(sizer, span=(1, 2), pos=(self._row, 0), flag=wx.ALIGN_CENTER_HORIZONTAL)
        return (control, label)

    @assert_message_queue
    def _create_choice(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        label = TransparentStaticText(form_view, label=form_item.label)
        platform.apply_tour_font(label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control = wx.Choice(form_view, choices=form_item.choices, size=(form_item.width, -1))
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control.SetSelection(val)
        self._bind_and_trigger(control, self.OnChoice, wx.EVT_CHOICE)
        parent_sizer.Add(label, pos=(self._row, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        parent_sizer.Add(control, pos=(self._row, 1))
        return (control, label)

    @assert_message_queue
    def _create_credit_card_type(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = CreditCardTypePanel(form_view)
        parent_sizer.Add(control, pos=(self._row, 1))
        return (control, None)

    @assert_message_queue
    def _create_date(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        label = TransparentStaticText(form_view, label=form_item.label)
        platform.apply_tour_font(label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        f = platform.get_tour_font(self)
        control = DatePicker(form_view, f)
        control.SetValue(val)
        self._bind_and_trigger(control, self.OnDateChanged, EVT_DATE_PICKER_CHANGED)
        parent_sizer.Add(label, pos=(self._row, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        parent_sizer.Add(control, pos=(self._row, 1))
        return (control, label)

    @assert_message_queue
    def _create_example_text(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = TransparentStaticText(form_view, label=form_item.text)
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        font = control.GetFont()
        font.SetPointSize(font.GetPointSize() - 2)
        control.SetFont(font)
        control.ForegroundColour = Colors.example_text
        control.Wrap(FORM_CONTENT_WIDTH)
        if filling_multi_control_simple:
            parent_sizer.Add(control)
        else:
            parent_sizer.Add(control, pos=(self._row, 1), flag=wx.ALIGN_RIGHT)
        return (control, None)

    @assert_message_queue
    def _create_fancy_radio_group(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = WizardRadioGroup(form_view, form_item.choices)
        control.SetValue(val)
        self._bind_and_trigger(control, self.OnPlanChoice, wx.EVT_CHOICE)
        parent_sizer.Add(control, pos=(self._row, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
        return (control, None)

    @assert_message_queue
    def _create_flag_choice(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        label = TransparentStaticText(form_view, label=form_item.label)
        platform.apply_tour_font(label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control = DropboxFlagChoice(form_view, choices=form_item.choices, style=wx.CB_READONLY, size=(form_item.width, -1))
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control.SetSelection(form_item.default_value)
        self._bind_and_trigger(control, self.OnChoice, wx.EVT_COMBOBOX)
        if filling_multi_control_simple:
            parent_sizer.Add(control)
        else:
            parent_sizer.Add(label, pos=(self._row, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            parent_sizer.Add(control, pos=(self._row, 1))
        return (control, label)

    @assert_message_queue
    def _create_help_button(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = TransparentStaticBitmap(form_view, Images.Help)
        parent_sizer.Add(control, pos=(self._row, 1), flag=wx.ALIGN_CENTER)
        control.autotip = AutoTip(form_view, {control: form_item.hover_text})
        return (control, None)

    @assert_message_queue
    def _create_horiz_spacer(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = (form_item.width, 10)
        parent_sizer.Add(control)
        return (control, None)

    @assert_message_queue
    def _create_image(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if form_item.border:
            control = TransparentPanel(form_view, style=wx.SIMPLE_BORDER)
            bmp = TransparentStaticBitmap(control, form_item.image)
            vsizer = wx.BoxSizer(wx.VERTICAL)
            vsizer.Add(bmp)
            control.SetAutoLayout(True)
            control.SetSizerAndFit(vsizer)
        else:
            control = TransparentStaticBitmap(form_view, form_item.image)
        sizer.Add(control, flag=wx.ALIGN_CENTER)
        if form_item.label:
            label_sizer = wx.BoxSizer(wx.VERTICAL)
            label = TransparentStaticText(form_view, label=form_item.label)
            platform.apply_tour_font(label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
            label_sizer.Add((0, 2))
            label_sizer.Add(label)
            sizer.Add((5, 0))
            sizer.Add(label_sizer, flag=wx.ALIGN_CENTER)
        if filling_multi_control_simple:
            parent_sizer.Add(sizer)
        else:
            parent_sizer.Add(sizer, pos=(self._row, 0), span=(1, 2), flag=wx.ALIGN_CENTER)
        return (None, None)

    @assert_message_queue
    def _create_location_changer(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = DropboxLocationChanger(form_view, self._wizard.dropbox_app, False, False, True, platform.get_tour_font(self), override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control.SetValue(val)
        self._bind_and_trigger(control, self.OnDropboxLocationChanged, EVT_DROPBOX_LOCATION_CHANGED)
        parent_sizer.Add(control, pos=(self._row, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
        return (control, None)

    @assert_message_queue
    def choose_dropbox_location(self, on_location = None):
        loc = request_valid_dropbox_path_from_user(self._wizard.dropbox_app, self._wizard.dropbox_path, care_about_existing_dropbox=False, move=False, parent=None)
        if loc and callable(on_location):
            on_location(loc)

    @assert_message_queue
    def _create_multi_control_line_simple(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        sizer = wx.BoxSizer()
        for control in form_item.controls:
            self._create_form_item(control, form_view, sizer, filling_multi_control_simple=True)

        parent_sizer.Add(sizer, pos=(self._row, 0))
        return (None, None)

    @assert_message_queue
    def _create_centered_multi_control_line(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        sizer = wx.BoxSizer()
        for control in form_item.controls:
            self._create_form_item(control, form_view, sizer, filling_multi_control_simple=True)

        parent_sizer.Add(sizer, pos=(self._row, 0), span=(1, 2), flag=wx.ALIGN_CENTER)
        return (None, None)

    @assert_message_queue
    def _create_multi_control_line(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        final_column_zero_window = None
        final_column_zero_flag = 0
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        for i, control in enumerate(form_item.controls):
            self._create_form_item(control, form_view, parent_sizer)
            if i == 0:
                sizer_item = parent_sizer.FindItemAtPosition((self._row, 0))
                if sizer_item:
                    final_column_zero_window = sizer_item.Window
                    final_column_zero_flag = sizer_item.Flag
                    parent_sizer.Detach(final_column_zero_window)
                sizer_item = parent_sizer.FindItemAtPosition((self._row, 1))
                if sizer_item:
                    ctl = sizer_item.Window
                    parent_sizer.Detach(ctl)
                    sizer.Add(ctl, border=sizer_item.Border, flag=sizer_item.Flag)
            else:
                for x in (0, 1):
                    sizer.Add((parent_sizer.VGap, 0))
                    sizer_item = parent_sizer.FindItemAtPosition((self._row, x))
                    if sizer_item is None:
                        continue
                    ctl = sizer_item.Window
                    parent_sizer.Detach(ctl)
                    sizer.Add(ctl, border=sizer_item.Border, flag=sizer_item.Flag)

        parent_sizer.Add(final_column_zero_window, pos=(self._row, 0), flag=final_column_zero_flag)
        parent_sizer.Add(sizer, pos=(self._row, 1))
        return (None, None)

    @assert_message_queue
    def _create_plan_choices(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        sizer = wx.BoxSizer(wx.VERTICAL)
        base_font = platform.get_tour_font(self)
        control = PlanChoicesWidget(form_view, form_item.choices, base_font)
        control.SetValue(val)
        self._bind_and_trigger(control, self.OnPlanChoice, wx.EVT_CHOICE)
        sizer.Add(control, 0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=DEFAULT_BORDER)
        parent_sizer.Add(sizer, pos=(self._row, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
        return (control, None)

    @assert_message_queue
    def _create_radio_group(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        sizer = wx.BoxSizer(wx.VERTICAL)
        for i, choice in enumerate(form_item.choices):
            if form_item.max_width:
                choice = wordwrap(choice, form_item.max_width, wx.ClientDC(self), False)
            if i == 0:
                control = wx.RadioButton(form_view, -1, choice, style=wx.RB_GROUP)
                if self._first_control is None:
                    self._first_control = control
                    control.SetFocus()
            else:
                control = wx.RadioButton(form_view, -1, choice)
            platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
            control.index = i
            if i == val:
                control.Value = True
                self._send_fake_event(control, wx.EVT_RADIOBUTTON)
            else:
                control.Value = False
            sizer.Add(control)
            if form_item.vertical_spacing is not None:
                sizer.AddSpacer((0, form_item.vertical_spacing))
            self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton, control)
            self.current_controls[control] = form_item.attr

        parent_sizer.Add(sizer, pos=(self._row, 0), span=(1, 2), flag=wx.ALIGN_CENTER)
        return (None, None)

    @assert_message_queue
    def _create_selective_sync(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = SelectiveSyncLauncher(form_view, self._wizard.dropbox_app, False, False, True, platform.get_tour_font(self), True, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        control.SetValue(val)
        self._bind_and_trigger(control, self.OnIgnoreList, EVT_IGNORE_LIST_CHANGED)
        parent_sizer.Add(control, pos=(self._row, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL)
        return (control, None)

    @assert_message_queue
    def _create_spacer(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        parent_sizer.Add((0, form_item.size), pos=(self._row, 0), span=(1, 2))
        return (None, None)

    @assert_message_queue
    def _create_text_block(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        control = StaticLinkText(form_view, label=form_item.text, line_height=form_item.line_height)
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        font = control.GetFont()
        if form_item.bold:
            font.SetWeight(wx.FONTWEIGHT_BOLD)
        if form_item.size_diff:
            font.SetPointSize(font.GetPointSize() + form_item.size_diff)
        control.SetFont(font)
        if form_item.greedy:
            width = parent_sizer.GetMinSize()[0] if self.has_text_input_controls else FORM_CONTENT_WIDTH
            if self.current_panel.left_side_image:
                width -= self.current_panel.left_side_image.image.getBitmap().GetWidth() + self.current_panel.left_side_image_padding * 2
            control.Wrap(width, fixed_width=not form_item.center, center=form_item.center)
        else:
            control.Wrap(0)
        if form_item.right_align:
            alignment = wx.ALIGN_RIGHT
        elif self.current_panel.left_side_image:
            alignment = wx.ALIGN_LEFT
        else:
            alignment = wx.ALIGN_CENTER_HORIZONTAL
        if filling_multi_control_simple:
            parent_sizer.Add(control)
        else:
            parent_sizer.Add(control, pos=(self._row, 0), span=(1, 2), flag=alignment)
        return (control, None)

    @assert_message_queue
    def _create_text_input(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple):
        label = TransparentStaticText(form_view, label=form_item.label)
        platform.apply_tour_font(label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        if form_item.sublabel:
            sublabel = TransparentStaticText(form_view, label=form_item.sublabel)
            platform.apply_tour_font(sublabel, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
            font = sublabel.Font
            font.PointSize = 7
            sublabel.Font = font
            label_sizer = wx.BoxSizer(wx.VERTICAL)
            label_sizer.Add(label, flag=wx.ALIGN_RIGHT | wx.TOP, border=3)
            label_sizer.Add(sublabel, flag=wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT, border=2)
            to_add = label_sizer
            alignment = wx.ALIGN_RIGHT
        else:
            to_add = label
            alignment = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
        if filling_multi_control_simple:
            border = 0
            if form_item.label:
                border = 5
                alignment |= wx.RIGHT
            parent_sizer.Add(to_add, border=border, flag=alignment)
        else:
            parent_sizer.Add(to_add, pos=(self._row, 0), flag=alignment)
        style = wx.TE_PASSWORD if form_item.secure else 0
        control = wx.TextCtrl(form_view, value=val, size=(form_item.width, -1), style=style)
        if form_item.disabled:
            control.Disable()
        platform.apply_tour_font(control, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        self._bind_and_trigger(control, self.OnText, wx.EVT_TEXT)
        self._bind_and_trigger(control, self.OnChar, wx.EVT_CHAR)
        if platform == GNOME:
            b = 0
            if form_item.attr in ('zip', 'ccode'):
                b = 2
        else:
            b = 1
        if filling_multi_control_simple:
            parent_sizer.Add(control, border=1, flag=wx.TOP)
        else:
            parent_sizer.Add(control, pos=(self._row, 1), border=b, flag=wx.TOP)
        self.has_text_input_controls = True
        return (control, label)

    @assert_message_queue
    def _create_fancy_gauge(self, form_item, val, form_view, parent_sizer, filling_multi_control_simple = False):
        label = TransparentStaticText(form_view, form_item.label)
        platform.apply_tour_font(label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        alignment = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
        fancy_gauge = FancyGaugePanel(form_view, form_item.width, form_item.meters, colors=form_item.colors, skip=form_item.skip)
        if filling_multi_control_simple:
            parent_sizer.Add(label)
            parent_sizer.Add(fancy_gauge)
        else:
            parent_sizer.Add(label, pos=(self._row, 0), flag=alignment)
            parent_sizer.Add(fancy_gauge, pos=(self._row, 1))
        return (fancy_gauge, None)

    @assert_message_queue
    def _create_form_item(self, form_item, form_view, sizer = None, filling_multi_control_simple = False):
        control = None
        control_label = None
        if form_item.attr is not None:
            val = getattr(self.current_panel, form_item.attr, form_item.default_value)
        else:
            val = form_item.default_value
        if form_item.__class__ in self._renderers:
            sizer = sizer if sizer else form_view.Sizer
            control, control_label = self._renderers[form_item.__class__](form_item, val, form_view, sizer, filling_multi_control_simple=filling_multi_control_simple)
        else:
            TRACE("!! Not drawing a '%r' because there are no instructions how", form_item.__class__)
        if control is not None:
            self.current_controls[control] = form_item.attr
        if control and form_item.disabled and hasattr(control, 'Disable'):
            control.Disable()
        if control_label is not None:
            self.labels[form_item.attr] = control_label
        if self._first_control is None and control is not None and hasattr(control, 'SetFocus') and control.AcceptsFocus():
            self._first_control = control
            control.SetFocus()
            if hasattr(control, 'SelectAll'):
                control.SelectAll()
        return (control, control_label)

    @assert_message_queue
    def _create_panel(self):
        self.current_actions = {}
        self.current_controls = {}
        self.labels = {}
        panel = SetupWizardPanel(self, self.current_panel.background_image.GetBitmap(), self.current_panel.buttons, self.current_panel.progress_text if self.current_panel.tour else None)
        if self.current_panel.title and type(self.current_panel) is not WelcomePanel:
            title = TransparentStaticText(panel.background_panel, label=self.current_panel.title, style=wx.ALIGN_CENTER)
            platform.apply_tour_font(title, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
            title_font = title.Font
            title_font.SetWeight(wx.FONTWEIGHT_BOLD)
            title_font.SetPointSize(12)
            title.Font = title_font
            lines = title.BalancedWrap(TITLE_WIDTH)
            if self.current_panel.tour:
                panel.background_panel.Sizer.Add(title, flag=wx.ALIGN_CENTER | wx.TOP, border=19 // lines)
                panel.background_panel.Sizer.Add((0, DEFAULT_BORDER))
            else:
                panel.background_panel.Sizer.Add(title, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=19)
        if self.current_panel.left_side_image:
            panel.background_panel.Sizer.Add((0, self.current_panel.panel_title_lower_padding))
            grid_sizer = wx.GridBagSizer(hgap=0, vgap=0)
            middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
            img_sizer = wx.BoxSizer(wx.HORIZONTAL)
            img_control = TransparentPanel(panel.background_panel)
            img_vsizer = wx.BoxSizer(wx.VERTICAL)
            img_vsizer.Add(TransparentStaticBitmap(img_control, self.current_panel.left_side_image.image))
            img_control.SetAutoLayout(True)
            img_control.SetSizerAndFit(img_vsizer)
            img_sizer.Add(img_control, flag=wx.ALIGN_CENTER)
            middle_sizer.Add((self.current_panel.left_side_image_padding, 0))
            middle_sizer.Add(img_sizer, 0, flag=wx.ALIGN_CENTER_HORIZONTAL, border=0)
            middle_sizer.Add((self.current_panel.left_side_image_padding, 0))
            middle_sizer.Add(grid_sizer, 0, flag=wx.ALIGN_CENTER_VERTICAL, border=0)
            panel.background_panel.Sizer.Add(middle_sizer, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_LEFT)
        else:
            grid_sizer = wx.GridBagSizer(hgap=3, vgap=5)
            middle_sizer = wx.BoxSizer(wx.VERTICAL)
            middle_sizer.Add(grid_sizer, 1, flag=wx.ALIGN_CENTER_HORIZONTAL)
            panel.background_panel.Sizer.Add(middle_sizer, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)
        panel.background_panel.Sizer.AddStretchSpacer()
        self._status_label = TransparentStaticText(panel.background_panel, '', style=wx.ALIGN_CENTER)
        platform.apply_tour_font(self._status_label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        panel.background_panel.Sizer.Add(self._status_label, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.BOTTOM, border=DEFAULT_BORDER)
        self._row = 0
        self.has_text_input_controls = False
        if self.current_panel.form_contents:
            self._first_control = None
            for form_item in self.current_panel.form_contents:
                if 'win' not in form_item.hide_on:
                    control, control_label = self._create_form_item(form_item, panel.background_panel, grid_sizer)
                    if hasattr(form_item, 'bottom_align') and form_item.bottom_align:
                        sizer_item = grid_sizer.FindItemAtPosition((self._row, 0))
                        if sizer_item:
                            item = sizer_item.Window if sizer_item.Window else sizer_item.Sizer
                            flag = sizer_item.GetFlag()
                            if self.current_panel.tour:
                                index = 5
                                flag |= wx.BOTTOM
                                border = DEFAULT_BORDER
                            else:
                                border = 0
                                index = 3
                            grid_sizer.Detach(item)
                            panel.background_panel.Sizer.Insert(index, item, border=border, flag=flag)
                    self._row += 1

            self.set_focus_on_control(self.current_panel.focus_attr)
        return panel

    @message_sender(wx.CallAfter)
    def _mark_label_as_error(self, attr_name, is_error):
        assert attr_name in self.labels
        self.labels[attr_name].ForegroundColour = Colors.text_error if is_error else Colors.black
        self.labels[attr_name].Refresh()

    @message_sender(wx.CallAfter)
    def set_example_text(self, attr, text, error = False):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                break
        else:
            TRACE("!! Tried to enable/disable %r when it doesn't exist", attr)
            return

        control.ForegroundColour = Colors.text_error if error else Colors.black
        control.Label = text
        control.Wrap(FORM_CONTENT_WIDTH)
        control.Parent.Layout()

    @message_sender(wx.CallAfter)
    def set_form_status(self, status, error = False):
        self._status_label.ForegroundColour = Colors.text_error if error else Colors.black
        self._status_label.Label = status
        self._status_label.BalancedWrap(FORM_CONTENT_WIDTH)
        self._status_label.Parent.Layout()

    @message_sender(wx.CallAfter)
    def disable_buttons(self):
        for button in self._buttons.itervalues():
            button.Enabled = False

    @message_sender(wx.CallAfter)
    def enable_buttons(self):
        for button in self._buttons.itervalues():
            button.Enabled = True

    @message_sender(wx.CallAfter)
    def set_control_enabled(self, attr, value):
        for control, control_attr in self.current_controls.iteritems():
            if attr == control_attr:
                control.Enabled = value
                break
        else:
            TRACE("!! Tried to enable/disable %r when it doesn't exist", attr)

    @message_sender(wx.CallAfter)
    def select_all_in_control(self, attr):
        if attr:
            try:
                for control, control_attr in self.current_controls.iteritems():
                    if attr == control_attr:
                        control.SetSelection(-1, -1)
                        break
                else:
                    TRACE("!! Tried to select_all_in_control on %r when it doesn't exist", attr)

            except Exception:
                unhandled_exc_handler()

    @message_sender(wx.CallAfter)
    def set_focus_on_control(self, attr):
        if attr:
            try:
                for control, control_attr in self.current_controls.iteritems():
                    if attr == control_attr:
                        control.SetFocus()
                        break
                else:
                    TRACE("!! Tried to SetFocus on %r when it doesn't exist", attr)

            except Exception:
                unhandled_exc_handler()

    @message_sender(wx.CallAfter)
    def _update_next_button(self):
        if self.next_button and self.current_panel:
            self.next_button.Enabled = self.current_panel.form_is_valid

    @message_sender(wx.CallAfter)
    def ask_yes_no(self, prompt, yes_button_text, no_button_text, expl_text = None, on_yes = None, on_no = None):
        TRACE("Asking user '%s'", prompt)
        dlg = DropboxModalDialog(self, message=expl_text or prompt, title=prompt if expl_text else '', caption=prompt if expl_text else '', buttons=[no_button_text or MiscStrings.cancel_button, yes_button_text or MiscStrings.ok_button])
        ret = dlg.show_modal()
        if ret == 1:
            if callable(on_yes):
                on_yes()
        elif callable(on_no):
            on_no()

    @event_handler
    def OnClose(self, event):
        if not event.CanVeto() or self._done:
            self.Destroy()
            return
        if wx.MessageDialog(self, self._wizard.exit_prompt, self._wizard.exit_caption, style=wx.OK | wx.CANCEL | wx.ICON_ERROR).ShowModal() == wx.ID_OK:
            self._wizard.exit()
            self.Destroy()
        else:
            TRACE('Vetoing window close')
            event.Veto()

    @event_handler
    def OnAdvancedPanelRadioGroup(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val)

    @event_handler
    def OnChoice(self, event):
        if hasattr(event.EventObject, 'CurrentSelection'):
            val = event.EventObject.CurrentSelection
        else:
            val = event.EventObject.GetSelection()
        self.update_panel_attr(event.EventObject, val)

    @event_handler
    def OnDropboxLocationChanged(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val)

    @event_handler
    def OnButtonClicked(self, event):
        sender = event.EventObject
        if sender.LabelText in self.current_actions:
            action = self.current_actions[sender.LabelText]
            self._handle_action(action)

    @event_handler
    def OnCheckBox(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val)

    def OnCheckBoxLabelMouseUp(self, rect, checkbox):
        checkbox.SetValue(not checkbox.GetValue())
        self.update_panel_attr(checkbox, checkbox.GetValue())

    @event_handler
    def OnDateChanged(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val)

    @event_handler
    def OnIgnoreList(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val)

    @event_handler
    def OnRadioButton(self, event):
        val = event.EventObject.index
        self.update_panel_attr(event.EventObject, val)

    @event_handler
    def OnText(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val, True)

    @event_handler
    def OnChar(self, event):
        val = event.EventObject.Value
        self.update_panel_attr(event.EventObject, val, True)

    @event_handler
    def OnPlanChoice(self, event):
        event_object = event.EventObject
        self.update_panel_attr(event_object, event_object.Value)


class SetupWizardPanel(wx.Panel):

    def __init__(self, parent, background_image, buttons, progress_text):
        pre = wx.PrePanel()
        pre.SetWindowStyle(wx.TAB_TRAVERSAL)
        pre.Show(False)
        pre.Create(parent)
        self.PostCreate(pre)
        self.background_panel = BackgroundPanel(self, background_image)
        button_panel = ButtonPanel(self, buttons, parent, progress_text)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.background_panel, 1, flag=wx.EXPAND)
        vsizer.Add(wx.StaticLine(self), flag=wx.EXPAND | wx.TOP | wx.BOTTOM)
        vsizer.Add(button_panel, flag=wx.EXPAND)
        self.SetSizerAndFit(vsizer)


class ButtonPanel(wx.Panel):

    def __init__(self, parent, buttons, wizard_window, progress_text):
        super(ButtonPanel, self).__init__(parent=parent, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if progress_text:
            progress_text = wx.StaticText(self, label=progress_text)
            platform.apply_tour_font(progress_text)
            button_sizer.Add(progress_text, flag=wx.ALIGN_CENTER_VERTICAL)
        button_sizer.AddStretchSpacer()
        wizard_window._buttons = dict()
        for title, action in buttons:
            button = wx.Button(self, label=title)
            platform.apply_tour_font(button)
            wizard_window._buttons[title] = button
            wizard_window.Bind(wx.EVT_BUTTON, wizard_window.OnButtonClicked, button)
            if action is not None:
                wizard_window.current_actions[title] = action
            else:
                button.Enabled = False
            button_sizer.Add((platform.button_horizontal_spacing, 0))
            button_sizer.Add(button)

        button.SetDefault()
        button_border = wx.BoxSizer(wx.VERTICAL)
        button_border.Add(button_sizer, proportion=1, border=platform.outer_button_border, flag=wx.ALL | wx.EXPAND)
        self.SetSizerAndFit(button_border)
