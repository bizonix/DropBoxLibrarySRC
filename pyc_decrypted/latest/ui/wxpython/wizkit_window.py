#Embedded file name: ui/wxpython/wizkit_window.py
import win32api
import win32con
import wx
import arch
from dropbox.event import report
from dropbox.gui import message_sender, assert_message_queue, event_handler, TRACE
from ui.common.uikit import on_main_thread
from ui.common.xui.wizkit import WizkitStrings
from ui.wxpython.xui import WxFrameXUIHost
from .constants import platform
from .dialogs import DropboxModalDialog
from .location_changer import request_valid_dropbox_path_from_user
from ..common.misc import MiscStrings
from .selective_sync import SelectiveSyncWindow

class WizkitWindow(WxFrameXUIHost):
    SCREEN_PADDING = 8
    BASE_WIDTH = 310
    BASE_HEIGHT = 468
    SCREEN_SIZE = (BASE_WIDTH, BASE_HEIGHT)

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, app, controller):
        self._app = app
        self._controller = controller
        self._controller.window = self
        self._when_done = None
        style = wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.STAY_ON_TOP
        WxFrameXUIHost.__init__(self, controller, parent=None, title=WizkitStrings.window_title, style=style, size=self.SCREEN_SIZE)
        self._Anchor = None
        self._TargetHeight = self.BASE_HEIGHT
        self.ClientSize = self.SCREEN_SIZE
        self.Center(wx.BOTH)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        platform.frame_icon(self)
        self._InitializeCef()

    @event_handler
    def OnClose(self, event):
        if self._controller.done:
            self._controller.do_finish()
        else:
            if not event.CanVeto():
                self.Destroy()
                return
            if wx.MessageDialog(self, self._controller.exit_prompt, self._controller.exit_caption, style=wx.OK | wx.CANCEL | wx.ICON_ERROR).ShowModal() == wx.ID_OK:
                self._controller.exit()
                self.Destroy()
            else:
                TRACE('Vetoing window close')
                event.Veto()

    @on_main_thread(block=True)
    def Show(self, show = True):
        if show:
            report('setup-wizkit', info='shown')
            self._controller.dropbox_app.ui_kit.wx_ui_kit._start_cef_animation_timer()
            self._app.event.flush_async()
        else:
            self._controller.dropbox_app.ui_kit.wx_ui_kit._stop_cef_animation_timer()
        super(WizkitWindow, self).Show(show)

    def linked_successfully(self, when_done = None):
        TRACE('OK, AUTHENTICATE claims we linked!')
        self._when_done = when_done

    def onFinish(self):
        if self._when_done is not None:
            self._when_done(dict(dropbox_path=self._controller.dropbox_path, show_bubbles=True, directory_ignore_set=self._controller.directory_ignore_set, enable_xattrs=True, open_dropbox_folder=True))
            self._when_done = None
        self.Show(False)

    @assert_message_queue
    def ask_yes_no(self, prompt, yes_button_text, no_button_text, expl_text = None, on_yes = None, on_no = None):
        TRACE("Asking user '%s'", prompt)
        dlg = DropboxModalDialog(self, message=expl_text or prompt, caption=prompt if expl_text else '', buttons=[no_button_text or MiscStrings.cancel_button, yes_button_text or MiscStrings.ok_button], title=prompt if expl_text else '', style=wx.STAY_ON_TOP)
        ret = dlg.show_modal()
        if ret == 1:
            if callable(on_yes):
                on_yes()
        elif callable(on_no):
            on_no()

    @assert_message_queue
    def choose_dropbox_location(self, on_location = None, on_cancel = None):
        loc = request_valid_dropbox_path_from_user(self._controller.dropbox_app, self._controller.dropbox_path, care_about_existing_dropbox=False, move=False, parent=self)
        if loc and callable(on_location):
            on_location(loc)
        elif callable(on_cancel):
            on_cancel()

    def disallow_covering(self):
        style = self.GetWindowStyle()
        style |= wx.STAY_ON_TOP
        self.SetWindowStyle(style)

    def allow_covering(self):
        style = self.GetWindowStyle()
        style ^= wx.STAY_ON_TOP
        self.SetWindowStyle(style)

    def choose_selective_sync_folders(self):
        assert self._controller.dropbox_app.sync_engine is not None
        assert self._controller.dropbox_app.dropbox_url_info is not None
        self.selective_sync_window = SelectiveSyncWindow(self, self._controller.dropbox_app, False, self._controller.directory_ignore_set)
        self.selective_sync_window.CenterOnParent()
        self.selective_sync_window.ShowModal()
        TRACE('modal dying, cleaning up')
        self._controller.directory_ignore_set = set([ unicode(a) for a in self.selective_sync_window.Value ])
        self.selective_sync_window.Destroy()
        self.selective_sync_window = None
