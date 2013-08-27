#Embedded file name: ui/wxpython/dialogs.py
from __future__ import absolute_import
import functools
import wx
import sys
from ..common.misc import MiscStrings
from dropbox.gui import message_sender, assert_message_queue
from ui.wxpython.constants import platform, Win32
from ui.images import wximages as Images
from .background_panel import BackgroundPanel
from .constants import Colors
from .dropbox_controls import ColorPanel, TransparentStaticBitmap, TransparentStaticText
from dropbox.trace import unhandled_exc_handler
from .static_link_text import StaticLinkText
if sys.platform.startswith('win'):
    from dropbox.win32.version import WINDOWS_VERSION, VISTA
    import win32gui

def make_line(parent):
    if sys.platform.startswith('win') and WINDOWS_VERSION < VISTA:
        line = wx.StaticLine(parent)
    else:
        line = wx.Panel(parent)
        line.SetBackgroundColour(Colors.line_windows)
        line.SetSize((1, 1))
    return line


BCM_SETSHIELD = 5644

class UACButton(wx.Button):

    def __init__(self, *n, **kw):
        super(UACButton, self).__init__(*n, **kw)
        win32gui.SendMessage(self.GetHandle(), BCM_SETSHIELD, None, True)
        self.calc_min()

    def calc_min(self):
        min_size = self.GetEffectiveMinSize()
        min_size.x += wx.SystemSettings.GetMetric(wx.SYS_SMALLICON_X)
        self.SetInitialSize(min_size)

    def SetLabel(self, label):
        ret = super(UACButton, self).SetLabel(label)
        self.calc_min()
        return ret


class DropboxModalDialog(wx.Dialog):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, *n, **kw):
        message = kw.pop('message')
        caption = kw.pop('caption', None)
        buttons = kw.pop('buttons', [])
        super(DropboxModalDialog, self).__init__(*n, **kw)
        if platform == Win32:
            self.panel = ColorPanel(self, color=wx.Color(255, 255, 255))
        else:
            self.panel = wx.Panel(self)
        platform.init()
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        bmp = wx.StaticBitmap(self.panel, bitmap=Images.BoxLarge.GetBitmap())
        if platform == Win32:
            bmp.SetBackgroundColour(wx.Color(255, 255, 255))
        self.hsizer.Add(bmp, flag=wx.ALL, border=platform.error_bitmap_border)
        self.txt_sizer = wx.BoxSizer(wx.VERTICAL)
        if caption is not None:
            captxt = wx.StaticText(self.panel, label=caption)
            if platform == Win32:
                captxt.SetBackgroundColour(wx.Color(255, 255, 255))
            captxt.Wrap(platform.error_dialog_width - bmp.GetSize().GetWidth() - platform.error_bitmap_border * 3)
            self.txt_sizer.Add(captxt, border=platform.error_bitmap_border, flag=wx.TOP)
            f = captxt.GetFont()
            f.SetWeight(wx.BOLD)
            captxt.SetFont(f)
        txt = StaticLinkText(self.panel, label=message)
        if platform == Win32:
            txt.SetBackgroundColour(wx.Color(255, 255, 255))
        elif caption is not None:
            txt.SetBackgroundColour(captxt.GetBackgroundColour())
        txt.Wrap(platform.error_dialog_width - bmp.GetSize().GetWidth() - platform.error_bitmap_border * 3)
        self.txt_sizer.Add(txt, border=platform.error_bitmap_border / 2, flag=wx.TOP)
        self.hsizer.Add(self.txt_sizer, border=platform.error_bitmap_border, flag=wx.RIGHT)
        self.vsizer.Add(self.hsizer, border=platform.error_bitmap_border, flag=wx.BOTTOM)
        self.buttonsizer = wx.FlexGridSizer(cols=len(buttons) + 1)
        self.buttonsizer.AddSpacer(wx.Size(0, 0))
        self.buttonsizer.AddGrowableCol(0)
        self.wx_buttons = [ wx.Button(self.panel, label=button) for button in buttons ]
        self.button_dict = {}
        for i, button in enumerate(self.wx_buttons):
            self.buttonsizer.Add(button, border=platform.button_horizontal_spacing, flag=wx.LEFT)
            self.button_dict[button.Id] = i
            button.Bind(wx.EVT_BUTTON, functools.partial(self.on_button_click, button.Id))

        max_height = max([ b.GetBestSize().GetHeight() for b in self.wx_buttons ])
        for b in self.wx_buttons:
            b.SetMinSize(wx.Size(-1, max_height))

        self.vsizer.Add(self.buttonsizer, flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=platform.outer_button_border)
        self.panel.SetSizerAndFit(self.vsizer)
        default = self.wx_buttons[-1]
        default.SetDefault()
        default.SetFocus()
        self.Fit()
        self.Center(wx.BOTH)
        self.Show(True)
        self.Raise()

    def on_button_click(self, _id, theEvent):
        self.EndModal(_id)

    @message_sender(wx.CallAfter, block=True)
    def show_modal(self):
        _id = super(DropboxModalDialog, self).ShowModal()
        if _id == wx.ID_CANCEL:
            return -1
        if _id not in self.button_dict:
            raise Exception('DropboxModalDialog: unknown id %r' % id)
        return self.button_dict[_id]


class ElevationDialog(DropboxModalDialog):
    ELEVATION_DLG_OK = 0
    ELEVATION_DLG_CANCEL = 1

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, *n, **kw):
        kw['buttons'] = [MiscStrings.continue_button, MiscStrings.cancel_button]
        super(ElevationDialog, self).__init__(*n, **kw)
        win32gui.SendMessage(self.wx_buttons[0].GetHandle(), BCM_SETSHIELD, None, True)
        uac_button = self.wx_buttons[0]
        try:
            min_size = uac_button.GetEffectiveMinSize()
            min_size.x += wx.SystemSettings.GetMetric(wx.SYS_SMALLICON_X)
            uac_button.SetInitialSize(min_size)
            self.buttonsizer.Layout()
        except Exception:
            unhandled_exc_handler()

        uac_button.SetDefault()
        uac_button.SetFocus()


class WxSplashDialog(wx.Dialog):
    WINDOW_SIZE = (576, 470)
    HEADER_BORDER = 40
    HEADER_SIZE = 18
    HEADER_PADDING = 16
    SUBHEADER_SIZE = 12
    SUBHEADER_PADDING = 14
    SUBHEADER_MAX_WIDTH = 500
    CHOICE_WINDOW_SIZE = (576, 485)
    CHOICE_PADDING = 8

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, title, image, header, subheader, callbacks, left_callbacks = None, progress_text = None, background = None, header_color = None, mbox_selector = None):
        self._image = image
        self._header = header
        self._subheader = subheader
        self._callbacks = callbacks
        self._left_callbacks = left_callbacks
        self._progress_text = progress_text
        self._background_image = background or Images.CameraBackground.GetBitmap()
        self.header_color = header_color or Colors.camera_font
        self.mbox_selector = mbox_selector
        pre = wx.PreDialog()
        pre.Show(False)
        pre.Create(None, size=self.WINDOW_SIZE if not mbox_selector else self.CHOICE_WINDOW_SIZE, style=platform.simple_frame_style | wx.TAB_TRAVERSAL | wx.STAY_ON_TOP)
        self.PostCreate(pre)
        self.SetDoubleBuffered(True)
        self.SetTitle(title)
        platform.frame_icon(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.content_panel = self._init_content(self)
        sizer.Add(self.content_panel, proportion=1, flag=wx.EXPAND)
        self.button_panel = self._init_buttons(self)
        sizer.Add(self.button_panel, flag=wx.EXPAND | wx.BOTTOM)
        self.SetSizer(sizer)
        self.CenterOnScreen()

    @assert_message_queue
    def _init_buttons(self, parent):
        button_panel = WxSplashButtonPanel(parent, self._callbacks, self._left_callbacks, self._progress_text)
        return button_panel

    @assert_message_queue
    def _init_content(self, parent):
        content_panel = BackgroundPanel(parent, self._background_image)
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        self._init_elems(content_panel, content_sizer)
        content_panel.SetSizerAndFit(content_sizer)
        return content_panel

    @assert_message_queue
    def _init_elems(self, parent, sizer):
        sizer.Add((0, self.HEADER_BORDER))
        header_image = self._init_image(parent)
        sizer.Add(header_image, flag=wx.CENTER)
        sizer.Add((0, self.HEADER_PADDING))
        header_label = self._init_header(parent)
        sizer.Add(header_label, flag=wx.CENTER)
        sizer.Add((0, self.SUBHEADER_PADDING))
        subheader = self._init_subheader(parent)
        sizer.Add(subheader, flag=wx.CENTER | wx.EXPAND | wx.LEFT | wx.RIGHT, border=(self.WINDOW_SIZE[0] - self.SUBHEADER_MAX_WIDTH) / 2)
        self.mbox_choice = None
        if self.mbox_selector:
            row = wx.BoxSizer(wx.HORIZONTAL)
            description = wx.StaticText(parent, label=self.mbox_selector.text)
            row.Add(description, flag=wx.ALIGN_CENTER)
            selector = wx.Choice(parent, choices=self.mbox_selector.selections)
            selector.SetSelection(self.mbox_selector.default_index)
            row.Add((2, 0))
            row.Add(selector, flag=wx.ALIGN_CENTER)
            self.mbox_choice = selector
            sizer.Add((0, self.CHOICE_PADDING))
            sizer.Add(row, flag=wx.ALIGN_CENTER)
        sizer.Layout()

    def _init_image(self, parent):
        header_image = TransparentStaticBitmap(parent, self._image)
        return header_image

    def _init_header(self, parent):
        header_font = platform.get_tour_font(parent, self.HEADER_SIZE)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header_label = wx.StaticText(parent, label=self._header)
        header_label.SetForegroundColour(self.header_color)
        header_label.SetFont(header_font)
        return header_label

    def _init_subheader(self, parent):
        subheader_font = platform.get_tour_font(parent, self.SUBHEADER_SIZE)
        subheader_font.SetWeight(wx.FONTWEIGHT_NORMAL)
        subheader_label = TransparentStaticText(parent, style=wx.ALIGN_CENTRE, label=self._subheader)
        subheader_label.SetForegroundColour(Colors.camera_font)
        subheader_label.SetFont(subheader_font)
        subheader_label.Wrap(self.SUBHEADER_MAX_WIDTH)
        return subheader_label


class WxSplashButtonPanel(wx.Panel):
    HORIZONTAL_SPACING = 8
    OUTER_HORIZONTAL_BORDER = 14
    OUTER_VERTICAL_BORDER = 10

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, buttons, left_buttons = None, progress_text = None):
        super(WxSplashButtonPanel, self).__init__(parent=parent, style=wx.TAB_TRAVERSAL)
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if left_buttons:
            assert not progress_text
            for identifier, title, action, focus in left_buttons:
                button = wx.Button(self, id=identifier, label=title)
                platform.apply_tour_font(button)
                if action is not None:
                    button.Bind(wx.EVT_BUTTON, action, button)
                else:
                    button.SetEnabled(False)
                if focus:
                    button.SetFocus()
                button_sizer.Add(button, border=self.OUTER_VERTICAL_BORDER, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)

        elif progress_text:
            progress_text = wx.StaticText(self, label=progress_text)
            platform.apply_tour_font(progress_text)
            button_sizer.Add(progress_text, flag=wx.ALIGN_CENTER_VERTICAL)
        button_sizer.AddStretchSpacer()
        for identifier, title, action, focus in buttons:
            button_sizer.Add((self.HORIZONTAL_SPACING, 0))
            button = wx.Button(self, id=identifier, label=title)
            platform.apply_tour_font(button)
            if action is not None:
                button.Bind(wx.EVT_BUTTON, action, button)
            else:
                button.SetEnabled(False)
            if focus:
                button.SetFocus()
            button_sizer.Add(button, border=self.OUTER_VERTICAL_BORDER, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)

        button_border = wx.BoxSizer(wx.VERTICAL)
        line = make_line(self)
        button_border.Add(line, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)
        button_border.Add(button_sizer, proportion=1, border=self.OUTER_HORIZONTAL_BORDER, flag=wx.LEFT | wx.RIGHT | wx.EXPAND)
        self.SetSizerAndFit(button_border)
