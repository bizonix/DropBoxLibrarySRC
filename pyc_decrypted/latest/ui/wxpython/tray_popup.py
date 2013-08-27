#Embedded file name: ui/wxpython/tray_popup.py
import win32api
import win32gui
import win32con
import wx
from dropbox.functions import handle_exceptions
from dropbox.gui import message_sender, assert_message_queue, event_handler, TRACE
from dropbox.trace import unhandled_exc_handler
from dropbox.win32.version import WINXP, WINDOWS_VERSION
from ui.common.xui.tray_popup import TrayPopupStrings
from ui.wxpython.xui import WxFrameXUIHost
from pynt.helpers.shell import get_taskbar_position

class TrayPopupWindow(WxFrameXUIHost):
    SCREEN_PADDING = 8
    BASE_WIDTH = 310
    BASE_HEIGHT = 200
    SCREEN_SIZE = (BASE_WIDTH, BASE_HEIGHT)
    INIT_SCREEN_SIZE = (500, 500)

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, app, tray_popup_controller):
        self._app = app
        self._tray_icon = app.ui_kit.tray_icon
        self._tray_popup_controller = tray_popup_controller
        style = wx.DEFAULT_FRAME_STYLE
        style |= wx.STAY_ON_TOP
        style |= wx.TAB_TRAVERSAL
        style |= wx.FRAME_TOOL_WINDOW
        style &= ~wx.CAPTION
        self._DwmEnabled = None
        self._HasDwmChanged()
        self._Anchor = None
        self._TargetHeight = TrayPopupWindow.BASE_HEIGHT
        self._Placed = False
        self._SkipShow = False
        WxFrameXUIHost.__init__(self, tray_popup_controller, parent=None, title='', style=style, size=TrayPopupWindow.INIT_SCREEN_SIZE)
        self.ClientSize = self.SCREEN_SIZE
        self.Bind(wx.EVT_NAVIGATION_KEY, self.OnNavigationKey)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self._UpdateWindowStyle()
        self._InitializeCef()
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.Button(self, label=TrayPopupStrings.open_dropbox_menu)
        label.Bind(wx.EVT_BUTTON, self.OnButton)
        sizer.Add(label, 0, wx.EXPAND)
        self.SetSizer(sizer)

    @event_handler
    def OnButton(self, event):
        self._app.ui_kit.show_tray_popup(context_menu=True)
        event.Skip()

    @event_handler
    def OnNavigationKey(self, event):
        pass

    @assert_message_queue
    def set_height(self, height):
        self.MoveToAnchor(height=height)

    @assert_message_queue
    def is_visible(self):
        return self.IsShown()

    def _HasDwmChanged(self):
        current = self._tray_icon.is_dwm_enabled()
        if self._DwmEnabled != current:
            self._DwmEnabled = current
            return True
        return False

    @assert_message_queue
    @handle_exceptions
    def _UpdateWindowStyle(self):
        current_style = win32gui.GetWindowLong(self.GetHandle(), win32con.GWL_STYLE)
        current_style |= win32con.WS_POPUP
        current_style |= win32con.WS_BORDER
        if not self._DwmEnabled and WINDOWS_VERSION > WINXP:
            current_style &= ~win32con.WS_THICKFRAME
        else:
            current_style |= win32con.WS_THICKFRAME
        win32gui.SetWindowLong(self.GetHandle(), win32con.GWL_STYLE, current_style)
        win32gui.SetWindowPos(self.GetHandle(), None, 0, 0, 0, 0, win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    @event_handler
    def OnClose(self, event):
        if not event.CanVeto():
            event.Skip()
        event.Veto()

    @handle_exceptions
    def _TrySkip(self):
        if self._Anchor is not None:
            x, y = win32gui.GetCursorPos()
            in_anchor = wx.Rect(*self._Anchor).ContainsXY(x, y)
            if in_anchor:
                self._SkipShow = True

    def ResetSkip(self):
        self._SkipShow = False

    @event_handler
    def OnActivate(self, event):
        if not event.GetActive():
            self._TrySkip()
            self.Show(False)
        event.Skip()

    def MoveToAnchor(self, anchor = None, height = None):
        refresh_anchor = False
        refresh_height = False
        if anchor is not None and self._Anchor != anchor:
            refresh_anchor = True
        if self._HasDwmChanged():
            self._UpdateWindowStyle()
            refresh_anchor = True
        if height is not None and self._TargetHeight != height:
            refresh_height = True
        if not (refresh_anchor or refresh_height) and self._Placed:
            return
        if refresh_anchor:
            self._Placed = False
            self._Anchor = anchor
        if refresh_height:
            self._TargetHeight = height
        if self._Anchor is None:
            return
        self.MinSize, self.MaxSize = (0, 0), (500, 500)
        self.ClientSize = (self.BASE_WIDTH, self._TargetHeight)
        self.MinSize = self.MaxSize = self.Size
        rx, ry, rw, rh = self._Anchor
        ww, wh = self.GetSize()
        monitor = win32api.MonitorFromRect((rx,
         ry,
         rw,
         rh), win32con.MONITOR_DEFAULTTONULL)
        if monitor is None:
            raise Exception('Failed to find monitor the tray icon is on!')
        info = win32api.GetMonitorInfo(monitor)
        sx, sy, sx2, sy2 = info['Monitor']
        bx, by, bx2, by2 = info['Work']
        sw = sx2 - sx
        sh = sy2 - sy
        try:
            tx, ty, tx2, ty2 = get_taskbar_position()
            TRACE('Taskbar Rect: (%r,%r) (%r,%r)', tx, ty, tx2, ty2)
            if (tx, ty) == (bx, by):
                if bx2 == tx2 and ty2:
                    by = ty2
                elif by2 == ty2 and tx2:
                    bx = tx2
            elif (tx2, ty2) == (bx2, by2):
                if bx == tx and ty:
                    by2 = ty
                elif by == ty and tx:
                    bx2 = tx
        except Exception:
            unhandled_exc_handler()

        TRACE('Screen Rect: (%r,%r) (%r,%r)', sx, sy, sx2, sy2)
        TRACE('Work Rect: (%r,%r) (%r,%r)', bx, by, bx2, by2)
        top_distance = ry - sy
        bottom_distance = sh - (ry + rh) + sy
        left_distance = rx - sx
        right_distance = sw - (rx + rw) + sx
        min_distance = min(top_distance, bottom_distance, left_distance, right_distance)
        if self._DwmEnabled or WINDOWS_VERSION <= WINXP:
            padding = self.SCREEN_PADDING
        else:
            padding = 0
        if min_distance == top_distance:
            x = rx + rw / 2 - ww / 2
            x = min(x, bx2 - padding - ww)
            x = max(x, bx + padding)
            y = by + padding
        elif min_distance == left_distance:
            x = bx + padding
            y = ry + rh / 2 - wh / 2
            y = min(y, by2 - padding - wh)
            y = max(y, by + padding)
        elif min_distance == bottom_distance:
            x = rx + rw / 2 - ww / 2
            x = min(x, bx2 - padding - ww)
            x = max(x, bx + padding)
            y = by2 - padding - wh
        else:
            x = bx2 - padding - ww
            y = ry + rh / 2 - wh / 2
            y = min(y, by2 - padding - wh)
            y = max(y, by + padding)
        self.Move((x, y))
        self._Placed = True

    @assert_message_queue
    def ShowAnchored(self, rect):
        assert not self.failed, 'Host has failed!'
        if self.IsShown() or self._SkipShow:
            self.Show(False)
        else:
            self._tray_popup_controller.refresh()
            self.MoveToAnchor(rect)
            TRACE('Displaying tray popup at %r.', self.GetPosition())
            self._ClearHoverState()
            self.Show()
            self.Raise()
            self._app.event.report('tray-popup')
        self._SkipShow = False

    def Show(self, show = True):
        return super(TrayPopupWindow, self).Show(show)
