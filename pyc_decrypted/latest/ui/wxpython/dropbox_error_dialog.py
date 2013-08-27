#Embedded file name: ui/wxpython/dropbox_error_dialog.py
from __future__ import absolute_import
import sys
import threading
import wx
from dropbox.gui import event_handler, message_sender
import ui
from .constants import platform, Win32
from .dropbox_controls import ColorPanel
from .static_link_text import StaticLinkText
from ..common.misc import MiscStrings

class DropboxErrorDialog(wx.Frame):

    @event_handler
    def handle_cancel(self, theEvent):
        self.cancel_event.set()
        self.Show(False)
        if self.die_on_cancel:
            wx.GetApp().ExitMainLoop()

    def wait_for_cancel(self):
        return self.cancel_event.wait()

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, *n, **kw):
        self.message = kw.pop('message')
        ok_only = kw.pop('ok_only', False)
        if 'caption' in kw:
            self.caption = kw.pop('caption')
        else:
            self.caption = None
        if 'die_on_cancel' in kw:
            self.die_on_cancel = kw.pop('die_on_cancel')
        else:
            self.die_on_cancel = False
        kw['style'] = platform.simple_frame_style
        super(DropboxErrorDialog, self).__init__(*n, **kw)
        platform.frame_icon(self)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        if platform == Win32:
            self.panel = ColorPanel(self, color=wx.Color(255, 255, 255))
        else:
            self.panel = wx.Panel(self)
        platform.init()
        self.SetTitle(MiscStrings.dropbox_error)
        bmp = wx.StaticBitmap(self.panel, bitmap=ui.images.wximages.DropBang.GetBitmap())
        if platform == Win32:
            bmp.SetBackgroundColour(wx.Color(255, 255, 255))
        self.hsizer.Add(bmp, flag=wx.ALL, border=platform.error_bitmap_border)
        self.txt_sizer = wx.BoxSizer(wx.VERTICAL)
        if self.caption is not None:
            captxt = wx.StaticText(self.panel, label=self.caption)
            if platform == Win32:
                captxt.SetBackgroundColour(wx.Color(255, 255, 255))
            self.txt_sizer.Add(captxt, border=platform.error_bitmap_border, flag=wx.TOP)
            f = captxt.GetFont()
            f.SetWeight(wx.BOLD)
            captxt.SetFont(f)
        if sys.platform.startswith('linux'):
            txt = wx.StaticText(self.panel, label=self.message)
        else:
            txt = StaticLinkText(self.panel, label=self.message)
        txt.Wrap(platform.error_dialog_width - bmp.GetSize().GetWidth() - platform.error_bitmap_border * 3)
        self.txt_sizer.Add(txt, border=platform.error_bitmap_border / 2, flag=wx.TOP)
        self.hsizer.Add(self.txt_sizer, border=platform.error_bitmap_border, flag=wx.RIGHT)
        self.vsizer.Add(self.hsizer, border=platform.error_bitmap_border, flag=wx.BOTTOM)
        self.buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        if not ok_only:
            cancel_text = MiscStrings.cancel_button
        else:
            cancel_text = MiscStrings.ok_button
        cancel_button = wx.Button(self.panel, label=cancel_text, size=wx.Size(platform.error_button_width, -1))
        cancel_button.Bind(wx.EVT_BUTTON, self.handle_cancel)
        self.cancel_event = threading.Event()
        if not ok_only:
            get_help_button = wx.Button(self.panel, label=MiscStrings.get_help)
            get_help_button.Bind(wx.EVT_BUTTON, self.handle_get_help)
            button_tuple = (get_help_button, cancel_button)
        else:
            button_tuple = (cancel_button,)
        for btn in button_tuple:
            if btn.GetSize().GetWidth() < platform.error_button_width:
                btn.SetSize(wx.Size(platform.error_button_width, btn.GetSize().GetHeight()))

        self.buttonsizer.AddSpacer(wx.Size(0, 0), proportion=1)
        self.buttonsizer.Add(cancel_button, border=platform.error_button_horizontal_border, flag=wx.ALIGN_RIGHT | wx.RIGHT)
        if not ok_only:
            self.buttonsizer.Add(get_help_button, border=platform.error_button_horizontal_border, flag=wx.ALIGN_RIGHT | wx.RIGHT)
        self.vsizer.Add(self.buttonsizer, flag=wx.EXPAND)
        self.vsizer.AddSpacer(wx.Size(0, platform.error_button_vertical_border))
        self.panel.SetSizerAndFit(self.vsizer)
        self.Fit()
        self.Center(wx.BOTH)
        self.Show(True)
        self.Raise()
