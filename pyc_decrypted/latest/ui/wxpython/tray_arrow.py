#Embedded file name: ui/wxpython/tray_arrow.py
from __future__ import absolute_import
import functools
import wx
from dropbox.gui import event_handler
from dropbox.trace import report_bad_assumption, unhandled_exc_handler, TRACE
from ..common import tray_arrow
from .util import draw_on_bitmap
import ui.images
from ctypes import Structure, c_int, pointer, windll
from ctypes.wintypes import BOOL, BYTE, COLORREF, DWORD, HDC, HWND, LONG, POINTER
try:
    import arch
except:
    unhandled_exc_handler()

class BLENDFUNCTION(Structure):
    _fields_ = [('BlendOp', BYTE),
     ('BlendFlags', BYTE),
     ('SourceConstantAlpha', BYTE),
     ('AlphaFormat', BYTE)]


LPBLENDFUNCTION = POINTER(BLENDFUNCTION)
AC_SRC_OVER = 0
AC_SRC_ALPHA = 1
ULW_COLORKEY = 1
ULW_ALPHA = 2
ULW_OPAQUE = 4

class POINT(Structure):
    _fields_ = [('x', LONG), ('y', LONG)]


PPOINT = POINTER(POINT)
LPPOINT = POINTER(POINT)

class SIZE(Structure):
    _fields_ = [('cx', LONG), ('cy', LONG)]


PSIZE = POINTER(SIZE)
LPSIZE = POINTER(SIZE)
try:
    UpdateLayeredWindow = windll.user32.UpdateLayeredWindow
    UpdateLayeredWindow.argtypes = [HWND,
     HDC,
     LPPOINT,
     LPSIZE,
     HDC,
     LPPOINT,
     COLORREF,
     LPBLENDFUNCTION,
     DWORD]
    UpdateLayeredWindow.restype = BOOL
    GetWindowLong = windll.user32.GetWindowLongW
    GetWindowLong.argtypes = [HWND, c_int]
    GetWindowLong.restype = DWORD
    SetWindowLong = windll.user32.SetWindowLongW
    SetWindowLong.argtypes = [HWND, c_int, LONG]
    SetWindowLong.restype = LONG
    GetLastError = windll.kernel32.GetLastError
    GetLastError.restype = DWORD
    GWL_EXSTYLE = -20
    GWL_HINSTANCE = -6
    GWL_ID = -12
    GWL_STYLE = -16
    GWL_USERDATA = -21
    GWL_WNDPROC = -4
    WS_EX_LAYERED = 524288
    WS_EX_NOACTIVATE = 134217728
except Exception:
    unhandled_exc_handler()

    def GetWindowLong(*n):
        return 0


    def SetWindowLong(*n):
        return 0


    def GetLastError(*n):
        return 0


class TrayArrow(wx.Frame):
    PERIOD_LENGTH = tray_arrow.PERIOD_LENGTH
    TICK_RATE = tray_arrow.TICK_RATE
    PADDING_FACTOR = tray_arrow.PADDING_FACTOR

    @event_handler
    def __init__(self, rect, **kw):
        TRACE('Creating WX TrayArrow pointing at %r', rect)
        self.pointing_at = rect
        self.tick = functools.partial(tray_arrow.tick, self)
        self.get_current_position = functools.partial(tray_arrow.get_current_position, self)
        self.determine_motion = functools.partial(tray_arrow.determine_motion, self)
        self.timer = None
        kw['style'] = wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR | wx.NO_BORDER
        super(TrayArrow, self).__init__(None, **kw)
        self.Bind(wx.EVT_LEFT_DOWN, self.stop)
        window_style = GetWindowLong(self.Handle, GWL_EXSTYLE)
        if not window_style:
            report_bad_assumption('Error obtaining window style: %r', GetLastError())
        if not SetWindowLong(self.Handle, GWL_EXSTYLE, window_style | WS_EX_LAYERED | WS_EX_NOACTIVATE):
            TRACE("!! Couldn't make the window layered. Those arrows are going to be ugly.")
            report_bad_assumption('Error setting window style: %r', GetLastError())

    @event_handler
    def proper_orientation(self, disp):
        rx, ry, rw, rh = self.pointing_at
        dx, dy, dw, dh = disp
        top_dist = ry - dy
        bottom_dist = dh - (ry + rh) + dy
        left_dist = rx - dx
        right_dist = dw - (rx + rw) + dx
        min_dist = min(top_dist, bottom_dist, left_dist, right_dist)
        if top_dist == min_dist:
            self.orientation = 0
            self._bitmap = ui.images.wximages.TrayArrowUp.GetBitmap()
            motion_factor = 1
        elif left_dist == min_dist:
            self.orientation = 90
            self._bitmap = ui.images.wximages.TrayArrowLeft.GetBitmap()
            motion_factor = 1
        elif bottom_dist == min_dist:
            self.orientation = 180
            self._bitmap = ui.images.wximages.TrayArrowDown.GetBitmap()
            motion_factor = -1
        else:
            self.orientation = 270
            self._bitmap = ui.images.wximages.TrayArrowRight.GetBitmap()
            motion_factor = -1
        self.w, self.h = self._bitmap.GetSize().Get()
        if self.orientation == 0:
            self.y_factor = TrayArrow.PADDING_FACTOR * rh + rh
        elif self.orientation == 180:
            self.y_factor = -(TrayArrow.PADDING_FACTOR * rh + self.h)
        self.range_of_motion = self.h / 6.0 * motion_factor

    @event_handler
    def place(self):
        x, y = self.get_current_position()
        self.SetPosition(wx.Point(x, y))

    @event_handler
    def stop(self, *n, **kw):
        if self.timer:
            self.timer.Stop()
        self.Show(False)

    @event_handler
    def make_pretty_arrow(self):
        try:
            screenDC = wx.ScreenDC()
            empty_bitmap = wx.EmptyBitmap(self._bitmap.Width, self._bitmap.Height, 32)
            with draw_on_bitmap(empty_bitmap) as memoryDC:
                gcdc = wx.GCDC(memoryDC)
                gcdc.DrawBitmap(self._bitmap, 0, 0)
                bf = BLENDFUNCTION()
                bf.BlendOp = AC_SRC_OVER
                bf.BlendFlags = 0
                bf.SourceConstantAlpha = 255
                bf.AlphaFormat = AC_SRC_ALPHA
                win_pos = POINT(*self.get_current_position())
                pos = POINT(0, 0)
                wnd_size = SIZE(self._bitmap.Width, self._bitmap.Height)
                if not UpdateLayeredWindow(self.Handle, screenDC.GetHDC(), pointer(win_pos), pointer(wnd_size), memoryDC.GetHDC(), pointer(pos), 0, pointer(bf), ULW_ALPHA):
                    report_bad_assumption('UpdateLayeredWindow failed %r' % GetLastError())
        except:
            unhandled_exc_handler()

    @event_handler
    def start(self):
        rect = getattr(self, 'pointing_at', None)
        if rect is not None:
            display_index = wx.Display.GetFromPoint(wx.Point(rect[0], rect[1]))
            if display_index < 0:
                display_index = 0
            disp = wx.Display(display_index).GetGeometry().Get()
            self.proper_orientation(disp)
            self.determine_motion()
            self.t = 0
            self.place()
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.tick, self.timer)
            self.timer.Start(1000 * self.TICK_RATE)
            self.Show(True)
            self.make_pretty_arrow()
        else:
            TRACE('!! No tray icon to point at')
