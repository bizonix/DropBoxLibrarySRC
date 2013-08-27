#Embedded file name: arch/linux/tray_icon_wx.py
from __future__ import absolute_import
import os
import time
from dropbox.globals import dropbox_globals
import build_number
from build_number import BUILD_KEY, VERSION
from dropbox.gui import assert_message_queue
from dropbox.trace import unhandled_exc_handler, TRACE, report_bad_assumption
from dropbox.build_common import get_icon_suffix
from ui.common.tray import TrayController
from .util import launch_folder, hard_exit
from .internal import get_contents_root
import wx
import ui.images
from ui.wxpython.dropbox_controls import DropboxWxMenu

class TrayIcon(wx.TaskBarIcon):
    _STATE_MAP = {TrayController.IDLE: 'idle',
     TrayController.CONNECTING: 'logo',
     TrayController.BUSY: 'busy',
     TrayController.BROKEN: 'x',
     TrayController.PAUSED: 'logo'}

    @staticmethod
    def load_icon_with_fallback(name, icon_path):
        try:
            icon = wx.ArtProvider.GetIcon(name)
            if icon.Ok():
                return icon
        except:
            unhandled_exc_handler()

        icon = wx.Icon(os.path.join(icon_path, name + '.png'), wx.BITMAP_TYPE_PNG)
        if not icon.Ok():
            report_bad_assumption('failed to load tray icon %r', name)
        return icon

    def __init__(self, initial_state, initial_menu, initial_tooltip, app, *n, **kw):
        super(TrayIcon, self).__init__(*n, **kw)
        self.app = app
        icon_path = os.path.join(get_contents_root(), 'images', 'hicolor', '16x16', 'status') if hasattr(build_number, 'frozen') else os.path.join(get_contents_root(), 'images', 'status')
        icon_suffix = get_icon_suffix(BUILD_KEY)
        self.icons = dict([ (state, self.load_icon_with_fallback('dropboxstatus-' + state + icon_suffix, icon_path)) for state in ('logo', 'busy', 'busy2', 'idle', 'x') ])
        w, h = self.icons['logo'].GetWidth(), self.icons['logo'].GetHeight()
        tmpimg = wx.EmptyImage(w, h)
        if not tmpimg.HasAlpha():
            tmpimg.InitAlpha()
        for x in range(w):
            for y in range(h):
                tmpimg.SetAlpha(x, y, 0)

        self.icons['blank'] = wx.EmptyIcon()
        self.icons['blank'].CopyFromBitmap(wx.BitmapFromImage(tmpimg))
        self.tooltip_properly_set = False
        self.tooltip = initial_tooltip if initial_tooltip else '%s %s' % (BUILD_KEY, VERSION)
        self.busy_timer = wx.Timer(self)
        self.flashing_state = None
        self.which_busy = False
        self.Bind(wx.EVT_TIMER, self.busy_tick, self.busy_timer)
        self.cur_menu = None
        self.popped_menu = None
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.handle_left_click)
        self.Bind(wx.EVT_TASKBAR_CLICK, self.handle_right_click)
        self.current_state = None
        self.change_state(initial_state if initial_state is not None else TrayController.CONNECTING)
        if initial_menu:
            self.refresh_tray_menu(initial_menu)

    def handle_left_click(self, theEvent):
        t = time.time()
        if not hasattr(self, 'last_left_down') or self.last_left_down < t - 0.5:
            launch_folder(dropbox_globals['dropbox'])
        self.last_left_down = t

    def PopupMenu(self, *n, **kw):
        if self.app:
            self.app.event.report('tray-menu')
        wx.TaskBarIcon.PopupMenu(self, *n, **kw)

    def handle_right_click(self, theEvent):
        if self.popped_menu is not None:
            self.popped_menu.Destroy()
        assert self.cur_menu is not None, 'How were we clicked without having a current menu?'
        self.popped_menu = DropboxWxMenu(self.cur_menu)
        self.PopupMenu(self.popped_menu)

    def busy_tick(self, theEvent):
        if self.current_state == TrayController.BUSY:
            icon = self.icons['busy' if self.which_busy else 'busy2']
            self.which_busy = not self.which_busy
        else:
            icon = self.icons[self._STATE_MAP[self.current_state]]
        if self.flashing_state is not None:
            if self.flashing_state:
                icon = self.icons['blank']
            self.flashing_state = not self.flashing_state
        self.SetIcon(icon, self.tooltip)

    def Destroy(self, *n, **kw):
        self.stop_if_running()
        self.busy_timer.Destroy()
        super(TrayIcon, self).Destroy(*n, **kw)

    @assert_message_queue
    def get_screen_rect(self):
        return self.GetScreenRect().Get()

    def stop_if_running(self):
        if self.busy_timer.IsRunning():
            self.busy_timer.Stop()

    def start_if_not_running(self):
        if not self.busy_timer.IsRunning():
            self.busy_timer.Start(500)

    def set_flash(self, on):
        if (self.flashing_state is not None) != on:
            self.stop_if_running()
            self.flashing_state = False if on else None
            self.SetIcon(self.icons['blank'] if on else self.icons[self._STATE_MAP[self.current_state]], self.tooltip or u'')
            if self.current_state == TrayController.BUSY or self.flashing_state is not None:
                self.start_if_not_running()

    def change_state(self, new_state, first_time = False):
        if new_state == self.current_state:
            return
        self.stop_if_running()
        self.current_state = new_state
        self.SetIcon(self.icons[self._STATE_MAP[new_state]], self.tooltip)
        self.which_busy = False
        if new_state == TrayController.BUSY or self.flashing_state is not None:
            self.start_if_not_running()

    def refresh_tray_menu(self, menu):
        self.cur_menu = menu

    def set_tooltip(self, tooltip):
        if tooltip != self.tooltip:
            self.tooltip = tooltip
            self.change_state(self.current_state)
