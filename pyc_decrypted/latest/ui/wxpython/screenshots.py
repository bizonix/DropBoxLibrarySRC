#Embedded file name: ui/wxpython/screenshots.py
import wx
from dropbox.client.multiaccount.constants import Roles
from dropbox.client.screenshots import ScreenshotsController
from dropbox.gui import event_handler, message_sender
from ui.common.constants import ResizeMethod
from ui.common.preferences import pref_strings
from ui.common.screenshots import ScreenshotsStrings
from ui.images import wximages as Images
from ui.wxpython.constants import platform, Colors
from ui.wxpython.dialogs import WxSplashDialog
from ui.wxpython.util import resize_image

class WxScreenshotsSplashFrame(WxSplashDialog):
    HEADER_BORDER = 35
    HEADER_SIZE = 18
    HEADER_PADDING = 27
    SUBHEADER_SIZE = 10
    SUBHEADER_PADDING = 11
    BUTTONS_HORIZONTAL_PADDING = 10
    SUBHEADER_MAX_WIDTH = 500
    BUTTONS_PADDING = 20
    WINDOW_SIZE = (570, 450)
    OPEN_BOLD_TAG = '<b>'
    CLOSE_BOLD_TAG = '</b>'
    SCREENSHOT_SIZE = (233, 145)
    SCREENSHOT_POSITION = (0, 17)

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, file_path, title, always_cb, never_cb, close_cb, mbox_selector):
        self.always_cb = always_cb
        self.never_cb = never_cb
        self.close_cb = close_cb
        self.mbox_selector = mbox_selector
        self.screenshot = wx.Image(unicode(file_path))
        self.resized_screenshot = resize_image(self.screenshot, self.SCREENSHOT_SIZE, ResizeMethod.CROP)
        self.screenshot = None
        callbacks = ((wx.ID_YES,
          ScreenshotsStrings.always_move_screenshots,
          self.OnYes,
          True),)
        left_callbacks = ((wx.ID_NO,
          ScreenshotsStrings.never_move_screenshots,
          self.OnNo,
          False),)
        super(WxScreenshotsSplashFrame, self).__init__(title=title, image=Images.ScreenshotsBox, header=ScreenshotsStrings.quota_heading, subheader=ScreenshotsStrings.splash_message_for_win, left_callbacks=left_callbacks, callbacks=callbacks, background=Images.SplashGradientBackground.GetBitmap(), header_color=Colors.screenshots_header_font, mbox_selector=mbox_selector)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _init_image(self, parent):
        image = super(WxScreenshotsSplashFrame, self)._init_image(parent)
        self.SCREENSHOT_GLOBAL_POSITION = ((self.WINDOW_SIZE[0] - self._image.Image.GetSize().GetWidth()) / 2 + self.SCREENSHOT_POSITION[0], self.HEADER_BORDER + self.SCREENSHOT_POSITION[1])
        wx.StaticBitmap(parent, -1, self.resized_screenshot.ConvertToBitmap(), self.SCREENSHOT_GLOBAL_POSITION)
        return image

    def _init_subheader(self, parent):
        subheader_font = platform.get_tour_font(parent, self.SUBHEADER_SIZE)
        subheader_font.SetWeight(wx.FONTWEIGHT_NORMAL)
        subheader_font_bold = platform.get_tour_font(parent, self.SUBHEADER_SIZE)
        subheader_font_bold.SetWeight(wx.FONTWEIGHT_BOLD)
        start_char = 0
        str = ScreenshotsStrings.splash_message_for_win
        bold_ranges = []
        while start_char < len(str):
            open_char = str.find(self.OPEN_BOLD_TAG, start_char)
            if open_char == -1:
                break
            str = str[:open_char] + str[open_char + len(self.OPEN_BOLD_TAG):]
            close_char = str.find(self.CLOSE_BOLD_TAG, open_char)
            if close_char == -1:
                break
            str = str[:close_char] + str[close_char + len(self.CLOSE_BOLD_TAG):]
            start_char = close_char
            bold_ranges.append((open_char, close_char))

        default_attr = wx.TextAttr()
        default_attr.SetTextColour(Colors.screenshots_subheader_font)
        default_attr.SetFont(subheader_font)
        style = wx.BORDER_NONE | wx.TE_MULTILINE | wx.TE_CENTRE | wx.TE_READONLY | wx.TE_NO_VSCROLL | wx.TE_RICH2
        subheader = wx.TextCtrl(parent, style=style)
        subheader.SetDefaultStyle(default_attr)
        subheader.AppendText(str)
        bold_attr = wx.TextAttr()
        bold_attr.SetTextColour(Colors.screenshots_subheader_font)
        bold_attr.SetFont(subheader_font_bold)
        for range in bold_ranges:
            subheader.SetStyle(range[0], range[1], bold_attr)

        return subheader

    def OnNo(self, e):
        if self.never_cb:
            self.never_cb()
        self.Destroy()

    def OnYes(self, e):
        role = None
        if self.always_cb:
            if self.mbox_choice:
                index = self.mbox_choice.GetCurrentSelection()
                role = self.mbox_selector.translate_index(index)
            self.always_cb(role=role)
        self.Destroy()

    def OnClose(self, e = None):
        if self.close_cb:
            self.close_cb()
        self.Destroy()


class ScreenshotsSplashScreen(object):

    def __init__(self, always_cb, never_cb, close_cb, file_path, mbox_selector = None):
        self.dialog = WxScreenshotsSplashFrame(file_path=file_path, title=ScreenshotsStrings.splash_title, always_cb=always_cb, never_cb=never_cb, close_cb=close_cb, mbox_selector=mbox_selector)

    def show(self):
        self.dialog.Show()


class ScreenshotsSelector(wx.Panel):

    def __init__(self, parent, app, has_own_borders, change_cb):
        super(ScreenshotsSelector, self).__init__(parent)
        self.has_own_borders = has_own_borders
        self.app = app
        self.mbox = app.mbox
        self.change_cb = change_cb
        if self.has_own_borders:
            i_box = wx.StaticBox(self, label=pref_strings.screenshots_label)
            self.i_sizer = wx.StaticBoxSizer(i_box, wx.VERTICAL)
        else:
            self.i_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.i_sizer)
        self.reset()

    def needs_refresh(self):
        return self.multi_account and not self.mbox.has_secondary or not self.multi_account and self.mbox.has_secondary

    def reset(self):
        self.multi_account = self.mbox.has_secondary
        self.i_sizer.Clear(True)
        screenshots_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = pref_strings.screenshots_multiaccount if self.multi_account else pref_strings.screenshots
        self.screenshots_box = wx.CheckBox(self, label=label)
        self.screenshots_box.Bind(wx.EVT_CHECKBOX, self.change_cb)
        screenshots_sizer.Add(self.screenshots_box, border=platform.radio_static_box_interior, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM)
        self.mbox_choice = None
        if self.multi_account:
            self.mbox_choice = wx.Choice(self, choices=[self.mbox.account_labels_plain_long.personal, self.mbox.account_labels_plain_long.business])
            self.mbox_choice.Bind(wx.EVT_CHOICE, self.change_cb)
            screenshots_sizer.Add(self.mbox_choice, flag=wx.ALIGN_CENTER)
        else:
            screenshots_sizer.AddSpacer(wx.Size(0, 0), proportion=1, flag=wx.EXPAND)
        self.i_sizer.Add(screenshots_sizer, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM)
        self.read(self.app.config)
        self.i_sizer.Layout()

    def enabled(self, value):
        self.screenshots_box.Enabled = value

    @event_handler
    def read(self, state):
        checkbox, role = ScreenshotsController.current_prefs_state(self.app)
        self.screenshots_box.SetValue(checkbox)
        self.mbox_checkbox_value = checkbox
        if self.mbox_choice:
            default = 1 if role == Roles.BUSINESS else 0
            self.mbox_choice.SetSelection(default)
            self.mbox_default = default

    @event_handler
    def save(self):
        checkbox_changed = self.mbox_checkbox_value != self.screenshots_box.GetValue()
        if not self.multi_account:
            if checkbox_changed:
                self.app.screenshots_controller.update_from_prefs_window(bool(self.screenshots_box.GetValue()), None)
        elif checkbox_changed or self.mbox_choice.GetCurrentSelection() != self.mbox_default:
            self.app.screenshots_controller.update_from_prefs_window(bool(self.screenshots_box.GetValue()), Roles.PERSONAL if self.mbox_choice.GetCurrentSelection() == 0 else Roles.BUSINESS)
            self.mbox_default = self.mbox_choice.GetCurrentSelection()
        self.mbox_checkbox_value = self.screenshots_box.GetValue()

    @event_handler
    def on_show(self):
        self.reset()
