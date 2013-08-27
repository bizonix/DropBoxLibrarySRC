#Embedded file name: ui/wxpython/background_panel.py
from __future__ import absolute_import
import sys
import wx
from dropbox.gui import message_sender, event_handler
from .util import dirty_rects, draw_on_bitmap
if sys.platform.startswith('win'):
    from pynt.dlls.gdi32 import gdi32

    class BackgroundPanel(wx.Panel):

        @message_sender(wx.CallAfter, block=True)
        def __init__(self, parent, bitmap, double_buffered = True):
            super(BackgroundPanel, self).__init__(parent=parent, style=wx.TRANSPARENT_WINDOW | wx.TAB_TRAVERSAL)
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
            self.SetDoubleBuffered(double_buffered)
            self._bmp = None
            self._brush = wx.NullBrush
            self._source_bitmap = bitmap
            vsizer = wx.BoxSizer(wx.VERTICAL)
            self.SetAutoLayout(True)
            self.SetSizerAndFit(vsizer)
            self.Bind(wx.EVT_SIZE, self.OnSize)
            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.Bind(wx.EVT_CTLCOLOR, self.OnCtlColor)

        @property
        def Brush(self):
            return self._brush

        @event_handler
        def GetBlendedBrush(self, colour):
            new_bmp = wx.EmptyBitmap(self._bmp.Width, self._bmp.Height)
            with draw_on_bitmap(new_bmp) as dc:
                gcdc = wx.GCDC(dc)
                gcdc.DrawBitmap(self._bmp, 0, 0)
                gcdc.SetPen(wx.TRANSPARENT_PEN)
                gcdc.SetBrush(wx.Brush(colour))
                gcdc.DrawRectanglePointSize((0, 0), self._bmp.Size)
                del gcdc
            return wx.BrushFromBitmap(new_bmp)

        @event_handler
        def GetBackground(self, win):
            wx, wy = win.GetPosition()
            offset = self.GetRect().GetHeight() - self._bmp.GetHeight()
            return (self._bmp, (-wx, offset - wy))

        @event_handler
        def OnCtlColor(self, evt):
            target_rect = evt.GetWindow().GetScreenRect()
            target_rect.Position = self.ScreenToClient(evt.Window.ScreenRect.Position)
            client_rect = self.GetClientRect()
            gdi32.SetBrushOrgEx(evt.DC.GetHDC(), -target_rect.Left, client_rect.Bottom - target_rect.Top, None)
            if evt.Brush is None:
                evt.Brush = self._brush

        @event_handler
        def OnPaint(self, evt):
            if not self._bmp:
                self.OnSize(None)
            dc = wx.PaintDC(self)
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(self._brush)
            client_rect = self.GetClientRect()
            gdi32.SetBrushOrgEx(dc.GetHDC(), client_rect.GetLeft(), client_rect.GetBottom(), None)
            for dirty_rect in dirty_rects(self):
                dc.DrawRectangleRect(dirty_rect)

        @event_handler
        def OnSize(self, evt):
            w, h = self.GetClientSize()
            empty_bmp = wx.EmptyBitmap(w, h)
            bmp_w, bmp_h = self._source_bitmap.GetSize()
            with draw_on_bitmap(empty_bmp) as dc:
                dc.SetBrush(wx.WHITE_BRUSH)
                dc.Clear()
                dc.DrawBitmap(self._source_bitmap, 0, h - bmp_h)
            self._bmp = empty_bmp
            self._brush = wx.BrushFromBitmap(self._bmp)
            if evt:
                evt.Skip()


else:

    class BackgroundPanel(wx.Panel):

        def __init__(self, parent, bitmap):
            super(BackgroundPanel, self).__init__(parent=parent, style=wx.TRANSPARENT_WINDOW | wx.TAB_TRAVERSAL)
            self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
            self.SetDoubleBuffered(True)
            self._bitmap = bitmap
            vsizer = wx.BoxSizer(wx.VERTICAL)
            self.SetAutoLayout(True)
            self.SetSizerAndFit(vsizer)
            self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

        @event_handler
        def GetBackground(self, win):
            wx, wy = win.GetPosition()
            offset = self.GetRect().GetHeight() - self._bitmap.GetHeight()
            return (self._bitmap, (-wx, offset - wy))

        @event_handler
        def OnEraseBackground(self, event):
            dc = event.GetDC()
            if not dc:
                dc = wx.ClientDC(self)
                rect = self.GetUpdateRegion().GetBox()
                dc.SetClippingRect(rect)
            dc.Clear()
            dc.DrawBitmap(self._bitmap, 0, self.GetRect().GetHeight() - self._bitmap.GetSize().GetHeight())
