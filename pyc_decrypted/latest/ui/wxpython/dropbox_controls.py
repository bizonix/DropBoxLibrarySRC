#Embedded file name: ui/wxpython/dropbox_controls.py
from __future__ import absolute_import
import functools
import operator
import time
import sys
from Crypto.Random import random
import wx
import wx.lib.buttonpanel
import wx.lib.newevent
import wx.combo
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.gui import event_handler, message_sender
from ui.wxpython.constants import Colors, platform, Win32, GNOME
import ui.images
from .util import dirty_rects, draw_on_bitmap, wordwrap, wordwrap_helper
from wx.lib.buttonpanel import BP_BUTTONTEXT_ALIGN_RIGHT, BP_GRADIENT_COLOR_FROM, BP_GRADIENT_COLOR_TO, BP_BUTTONTEXT_COLOR, BP_SELECTION_BRUSH_COLOR, BP_SELECTION_PEN_COLOR, BP_BORDER_SIZE
if platform == Win32:
    from dropbox.win32.version import VISTA, WINDOWS_VERSION
_SHOULD_OVERRIDE_SYSTEM_COLORS = platform == GNOME

class DropboxWxMenu(wx.Menu):

    def __init__(self, descriptor, func_list = None, *n, **kw):
        super(DropboxWxMenu, self).__init__(*n, **kw)
        if func_list is None:
            self.func_list = []
        else:
            self.func_list = func_list
        for text, func in descriptor:
            if text is not None:
                text = text.replace('&', '&&')
            if text is None:
                self.AppendSeparator()
            elif type(func) in (list, tuple):
                self.AppendSubMenu(text=text, submenu=DropboxWxMenu(func, func_list=self.func_list))
            elif func is None:
                self.Append(text=text, id=wx.ID_ANY).Enable(False)
            else:
                self.func_list.append(func)
                self.Append(text=text, id=len(self.func_list) - 1)

        self.Bind(wx.EVT_MENU, self.handle_menu)

    def handle_menu(self, theEvent):
        self.func_list[theEvent.GetId()]()


class AutoTip(wx.ToolTip):

    def __init__(self, parent, children_to_tips, children_to_tip_callbacks = {}):
        super(AutoTip, self).__init__(tip=children_to_tips.values()[0])
        self.parent = parent
        self.children_to_tips = children_to_tips
        self.children_to_tip_callbacks = children_to_tip_callbacks
        self.Enable(False)
        for child in self.children_to_tips:
            child.SetToolTip(self)
            for evt_t in (wx.EVT_MOTION, wx.EVT_ENTER_WINDOW, wx.EVT_LEAVE_WINDOW):
                child.Bind(evt_t, self.OnMotion)

            child.GetTopLevelParent().Bind(wx.EVT_ACTIVATE, functools.partial(self.OnTopLevelActivate, child))

    @event_handler
    def OnMotion(self, theEvent):
        self.do_enable(theEvent.GetEventObject(), theEvent.GetEventType() != wx.EVT_LEAVE_WINDOW.typeId)

    @event_handler
    def OnTopLevelActivate(self, child, theEvent):
        if not theEvent.GetActive():
            self.do_enable(child, False)

    def do_enable(self, child, should_enable):
        if should_enable:
            if child in self.children_to_tip_callbacks:
                self.children_to_tips[child] = self.children_to_tip_callbacks[child]()
            self.SetTip(self.children_to_tips[child])
            self.Enable(True)
        else:
            self.Enable(False)


class Throbber(wx.Panel):

    def __init__(self, *n, **kw):
        if not hasattr(Throbber, '_bitmap'):
            Throbber._bitmap = ui.images.wximages.Throb22.GetBitmap()
            Throbber._w = Throbber._bitmap.GetWidth() / 8
            Throbber._h = Throbber._bitmap.GetHeight() / 4
            Throbber._frames = reduce(operator.add, [ [ Throbber._bitmap.GetSubBitmap(wx.Rect(xoff * Throbber._w, yoff * Throbber._h, Throbber._w, Throbber._h)) for xoff in range(8) ] for yoff in range(4) ])
        super(Throbber, self).__init__(*n, **kw)
        size = self._frames[0].GetSize()
        self.SetMinSize(size)
        self.SetMaxSize(size)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.tick, self.timer)
        self.xoff = 0
        self.reset()
        self._buffer = wx.EmptyBitmap(size[0], size[1])

    @event_handler
    def OnPaint(self, theEvent):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self._frames[self.index], self.xoff, 0)
        theEvent.Skip()

    def tick(self, theEvent):
        self.Refresh()
        self.index = max((self.index + 1) % len(self._frames), 1)

    def start(self):
        self.timer.Start(50)

    def stop(self):
        self.timer.Stop()

    def reset(self):
        self.index = 0


class TypeBox(wx.Panel):
    EntryErrors = (ValueError, OverflowError, TypeError)

    def __init__(self, parent, the_type, value = None, size = wx.DefaultSize, on_text = ()):
        super(TypeBox, self).__init__(parent)
        self.hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.text_ctrl = wx.TextCtrl(self, size=size, style=wx.ALIGN_RIGHT)
        self.hsizer.Add(self.text_ctrl, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        self.last_good_value = value
        self.the_type = the_type
        self.on_text = on_text
        if value is not None:
            self.SetValue(value)
        elif the_type.min is not None:
            self.SetValue(the_type.min + 1)
        elif the_type.max is not None:
            self.SetValue(the_type.max - 1)
        self.text_ctrl.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.SetSizer(self.hsizer)
        self.Fit()
        self.Layout()

    def GetValue(self):
        return self.the_type.from_unicode(self.text_ctrl.GetValue())

    def SetValue(self, v):
        try:
            str_v = self.the_type.to_unicode(v)
        except Exception:
            unhandled_exc_handler()
            raise
        else:
            self.last_good_value = v
            self.text_ctrl.SetValue(str_v)

    def _grab_value(self):
        try:
            v = self.GetValue()
        except self.EntryErrors:
            if self.last_good_value is not None:
                ip = self.text_ctrl.GetInsertionPoint()
                self.SetValue(self.last_good_value)
                self.text_ctrl.SetInsertionPoint(ip - 1)
        else:
            self.last_good_value = v

        return self.last_good_value

    def OnKillFocus(self, theEvent):
        self._grab_value()
        for cb in self.on_text:
            try:
                cb(theEvent)
            except Exception:
                unhandled_exc_handler()


class SpinTypeBox(TypeBox):

    def __init__(self, *n, **kw):
        self._no_modify_spin = True
        super(SpinTypeBox, self).__init__(*n, **kw)
        text_ctrl_pos = self.text_ctrl.GetPosition().Get()
        text_ctrl_size = self.text_ctrl.GetSize().Get()
        self.spin_button = wx.SpinButton(self, size=wx.Size(-1, text_ctrl_size[1]), style=wx.SP_VERTICAL)
        default_spin_size = self.spin_button.GetSize().Get()
        self.hsizer.AddSpacer(wx.Size(default_spin_size[0] - 1, default_spin_size[1]))
        self.Fit()
        self.Layout()
        self.spin_button.SetPosition(wx.Point(text_ctrl_pos[0] + text_ctrl_size[0] - 1, text_ctrl_pos[1] - (text_ctrl_size[1] - default_spin_size[1])))
        if self.the_type.min is not None:
            self.spin_button.SetMin(self.the_type.to_int(self.the_type.min) + 1)
        if self.the_type.max is not None:
            self.spin_button.SetMax(self.the_type.to_int(self.the_type.max) - 1)
        self.spin_button.Bind(wx.EVT_SPIN_UP, self.OnSpinUp)
        self.spin_button.Bind(wx.EVT_SPIN_DOWN, self.OnSpinDown)
        self._no_modify_spin = False

    def _grab_spin_from_last(self):
        self.spin_button.SetValue(self.the_type.to_int(self.last_good_value))

    @event_handler
    def OnSpinUp(self, theEvent):
        theEvent.Skip()
        self._no_modify_spin = True
        try:
            self.SetValue(self._grab_value() + 1)
        finally:
            self._no_modify_spin = False

    @event_handler
    def OnSpinDown(self, theEvent):
        theEvent.Skip()
        self._no_modify_spin = True
        try:
            self.SetValue(self._grab_value() - 1)
        finally:
            self._no_modify_spin = False

    def SetValue(self, v):
        super(SpinTypeBox, self).SetValue(v)
        if not self._no_modify_spin:
            self.spin_button.SetValue(self.the_type.to_int(v))
        else:
            wx.CallAfter(self._grab_spin_from_last)


class ColorPanel(wx.Panel):

    def __init__(self, parent, color, *n, **kw):
        super(ColorPanel, self).__init__(parent, *n, **kw)
        self._brush = wx.Brush(color, wx.SOLID)
        self._pen = wx.Pen(color)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    @event_handler
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        gcdc = wx.GCDC(dc)
        for update_rect in dirty_rects(self):
            gcdc.SetBrush(self._brush)
            gcdc.SetPen(self._pen)
            gcdc.DrawRectangleRect(update_rect)


class TransparentPanel(wx.Panel):

    def __init__(self, parent, style = 0, transparent_hack = True):
        super(TransparentPanel, self).__init__(parent, style=wx.TRANSPARENT_WINDOW | style)
        self.SetDoubleBuffered(True)
        self.SetTransparent(wx.CLEAR)
        self.BackgroundStyle = wx.BG_STYLE_CUSTOM
        self.Bind(wx.EVT_CTLCOLOR, self.OnCtlColor)
        if platform is GNOME and transparent_hack:
            self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self._brushes = {}

    @event_handler
    def GetBackground(self, win):
        ctl = self.Parent
        while ctl is not None:
            if hasattr(ctl, 'GetBackground'):
                return ctl.GetBackground(win)
            ctl = ctl.Parent

    @event_handler
    def OnEraseBackground(self, event):
        self.width, self.height = self.GetClientSizeTuple()
        self._buffer = wx.EmptyBitmapRGBA(self.width, self.height)
        with draw_on_bitmap(self._buffer) as mem_dc:
            dc = wx.GCDC(mem_dc)
            self.DrawBackground(dc, self.ClientRect)
            dc = event.GetDC()
            if not dc:
                dc = wx.ClientDC(self)
                rect = self.GetUpdateRegion().GetBox()
                dc.SetClippingRect(rect)
            for x, y, w, h in dirty_rects(self):
                dc.Blit(x, y, w, h, mem_dc, x, y)

    def DrawBackground(self, dc, rect):
        if hasattr(self.Parent, 'Compose'):
            crect = self.GetRect()
            rect.X += crect.X
            rect.Y += crect.Y
            return self.Parent.Compose(dc, rect)
        crap = self.GetBackground(self)
        if crap:
            bmp, (x, y) = crap
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()
            dc.DrawBitmap(bmp, x - rect.X, y - rect.Y)

    def Compose(self, dc, rect):
        self.DrawBackground(dc, rect)

    @event_handler
    def OnCtlColor(self, evt):
        ctl = self.Parent
        if not evt.Window.WindowStyle & wx.TRANSPARENT_WINDOW:
            self._brushes[evt.Window] = wx.Brush(evt.Window.BackgroundColour)
            evt.Brush = self._brushes[evt.Window]
            return
        while ctl is not None:
            if hasattr(ctl, 'OnCtlColor'):
                return ctl.OnCtlColor(evt)
            ctl = ctl.Parent


class UnfocusableMixin(wx.PyPanel):

    def AcceptsFocus(self):
        return False


class TransparentStaticText(wx.StaticText):

    def __init__(self, parent, label, style = 0):
        super(TransparentStaticText, self).__init__(parent, label=label, style=wx.TRANSPARENT_WINDOW | style)
        self.SetDoubleBuffered(True)

    def Wrap(self, width):
        dc = wx.ClientDC(self)
        dc.SetFont(self.Font)
        label = wordwrap(self.GetLabel(), width, dc, False)
        self.SetLabel(label)

    def BalancedWrap(self, width):
        dc = wx.ClientDC(self)
        dc.SetFont(self.Font)
        lines = wordwrap_helper(self.GetLabel(), width, dc, False)
        if len(lines) > 1:
            label = self.GetLabel()
            lo = 0
            hi = width
            last = len(lines)
            while lo < hi:
                mid = (lo + hi) // 2
                new_lines = wordwrap_helper(label, mid, dc, False)
                if len(new_lines) > last:
                    lo = mid + 1
                else:
                    lines = new_lines
                    hi = mid - 1

        self.SetLabel('\n'.join(lines))
        return len(lines)


class TransparentStaticBitmapLinux(wx.StaticBitmap):

    def __init__(self, parent, embedded_image, style = 0):
        bitmap = embedded_image.Bitmap
        super(TransparentStaticBitmap, self).__init__(parent, bitmap=bitmap, style=wx.TRANSPARENT_WINDOW | style)
        self.SetDoubleBuffered(True)


class TransparentStaticBitmapWin(wx.Panel):

    def __init__(self, parent, embedded_image, style = 0):
        super(TransparentStaticBitmap, self).__init__(parent, style=wx.TRANSPARENT_WINDOW | style)
        self.SetDoubleBuffered(True)
        self._bitmap = embedded_image.Bitmap
        self.SetClientSize(self._bitmap.Size)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)

    @event_handler
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        bmp_w, bmp_h = self._bitmap.Size.Get()
        self_w, self_h = self.Size.Get()
        x_offset = (self_w - bmp_w) / 2
        y_offset = (self_h - bmp_h) / 2
        image_rect = wx.Rect(x_offset, y_offset, bmp_w, bmp_h)
        with draw_on_bitmap(self._bitmap) as mem_dc:
            for x, y, w, h in dirty_rects(self):
                dest_x, dest_y, dest_w, dest_h = image_rect.Intersect(wx.Rect(x, y, w, h)).Get()
                dc.Blit(dest_x, dest_y, dest_w, dest_h, mem_dc, dest_x - x_offset, dest_y - y_offset)

    @event_handler
    def OnEraseBackground(self, evt):
        pass


if sys.platform.startswith('win'):
    TransparentStaticBitmap = TransparentStaticBitmapWin
else:
    TransparentStaticBitmap = TransparentStaticBitmapLinux

class TranslucentPanel(TransparentPanel):

    def __init__(self, parent, hover_colour, hover_border_colour, selected_colour, selected_border_colour, radius = 3, style = 0):
        super(TranslucentPanel, self).__init__(parent, style=style)
        self._hover_colour = hover_colour
        self._hover_border_colour = hover_border_colour
        self._selected_colour = selected_colour
        self._selected_border_colour = selected_border_colour
        self._hover_brush = wx.Brush(self._hover_colour)
        self._hover_pen = wx.Pen(self._hover_border_colour)
        self._selected_brush = wx.Brush(self._selected_colour)
        self._selected_pen = wx.Pen(self._selected_border_colour)
        self._hover = False
        self._selected = False
        self._radius = radius
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CTLCOLOR, self.OnCtlColor)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)

    def _get_blended_brushes(self):
        ctl = self.Parent
        while ctl is not None:
            if hasattr(ctl, 'GetBlendedBrush'):
                self._blended_brush = ctl.GetBlendedBrush(self._hover_colour)
                self._blended_selected_brush = ctl.GetBlendedBrush(self._selected_colour)
            ctl = ctl.Parent

    @event_handler
    def OnEnterWindow(self, event):
        if not self._hover:
            self._hover = True
            if not self._selected:
                self.Refresh()

    @event_handler
    def OnLeaveWindow(self, event):
        if event.EventObject == self:
            if self.ClientRect.Contains(event.Position):
                return
        else:
            offset_position = event.Position + event.EventObject.Rect.TopLeft
            if self.ClientRect.Contains(offset_position):
                return
        if self._hover:
            self._hover = False
            if not self._selected:
                self.Refresh()

    @event_handler
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        for update_box in dirty_rects(self):
            if self._selected:
                gcdc = platform.get_gcdc(dc)
                gcdc.SetBrush(self._selected_brush)
                gcdc.SetPen(wx.TRANSPARENT_PEN)
                if update_box.X == 0 and update_box.Y == 0:
                    gcdc.DrawRoundedRectangleRect(update_box, self._radius)
                else:
                    gcdc.DrawRectangleRect(update_box)
                gcdc.SetBrush(wx.TRANSPARENT_BRUSH)
                gcdc.SetPen(self._selected_pen)
                gcdc.DrawRoundedRectangleRect(self.GetClientRect(), self._radius)
            elif self._hover:
                gcdc = platform.get_gcdc(dc)
                gcdc.SetBrush(self._hover_brush)
                gcdc.SetPen(wx.TRANSPARENT_PEN)
                if update_box.X == 0 and update_box.Y == 0:
                    gcdc.DrawRoundedRectangleRect(update_box, self._radius)
                else:
                    gcdc.DrawRectangleRect(update_box)
                gcdc.SetBrush(wx.TRANSPARENT_BRUSH)
                gcdc.SetPen(self._hover_pen)
                gcdc.DrawRoundedRectangleRect(self.GetClientRect(), self._radius)

    @event_handler
    def OnSize(self, evt):
        self._get_blended_brushes()
        evt.Skip()

    @event_handler
    def OnMove(self, evt):
        self._get_blended_brushes()
        evt.Skip()

    def Compose(self, gcdc, update_box):
        super(TranslucentPanel, self).Compose(gcdc, update_box)
        if self._selected:
            gcdc.SetBrush(self._selected_brush)
            gcdc.SetPen(wx.TRANSPARENT_PEN)
            gcdc.DrawRectangle(0, 0, update_box.Width, update_box.Height)
        elif self._hover:
            gcdc.SetBrush(self._hover_brush)
            gcdc.SetPen(wx.TRANSPARENT_PEN)
            gcdc.DrawRectangle(0, 0, update_box.Width, update_box.Height)

    @event_handler
    def OnCtlColor(self, event):
        if self._selected:
            event.Brush = self._blended_selected_brush
        elif self._hover:
            event.Brush = self._blended_brush
        ctl = self.Parent
        while ctl is not None:
            if hasattr(ctl, 'OnCtlColor'):
                return ctl.OnCtlColor(event)
            ctl = self.Parent


class FancyRadioPanel(TranslucentPanel):
    LEFT_RIGHT_PADDING = 12
    TOP_BOTTOM_PADDING = 20

    def __init__(self, parent, hover_colour, hover_border_colour, selected_colour, selected_border_colour, radius = 3, first = False):
        super(FancyRadioPanel, self).__init__(parent, hover_colour, hover_border_colour, selected_colour, selected_border_colour, radius, style=wx.TAB_TRAVERSAL)
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if platform is GNOME:
            self._dummy_radio = wx.RadioButton(self, wx.RB_GROUP)
            self._dummy_radio.Show(False)
        self._radio_button = self.add_window(wx.RadioButton, style=wx.TRANSPARENT_WINDOW)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self._inner_sizer.Add((FancyRadioPanel.LEFT_RIGHT_PADDING, 0))
        self._inner_sizer.Add(self._radio_button, flag=wx.ALIGN_CENTER)
        self._sizer.Add(self._inner_sizer, border=FancyRadioPanel.TOP_BOTTOM_PADDING, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)
        self.SetAutoLayout(True)
        self.SetSizer(self._sizer)

    @event_handler
    def OnClick(self, event):
        if not self._selected:
            self.SetValue(1)
            rb_event = wx.CommandEvent(wx.EVT_RADIOBUTTON.typeId, self.Id)
            rb_event.EventObject = self._radio_button
            self.GetEventHandler().ProcessEvent(rb_event)

    def GetValue(self):
        return self._selected

    def SetValue(self, value):
        if self._selected != value:
            self._selected = value
            self.Refresh()
        if platform is Win32:
            self._radio_button.SetValue(value)
            return
        if not value:
            self._dummy_radio.SetValue(True)
        else:
            self._radio_button.SetValue(True)
            self._radio_button.SetFocus()

    Value = property(GetValue, SetValue)

    def add_window(self, window_t, *n, **kw):
        win = window_t(self, *n, **kw)
        self.setup_bindings(win)
        return win

    def setup_bindings(self, control):
        control.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        control.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        control.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)

    def layout_to_max_widths(self):
        pass


class FancyRadioGroup(TransparentPanel, UnfocusableMixin):

    def __init__(self, parent):
        super(FancyRadioGroup, self).__init__(parent)
        self._panels = []
        self._value = 0
        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.SetAutoLayout(True)
        self.SetSizer(vsizer)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton)

    def AddChoicePanel(self, panel):
        self._panels.append(panel)
        self.Sizer.Add(panel, 0, flag=wx.EXPAND | wx.ALL, border=5)

    @event_handler
    def OnRadioButton(self, event):
        i = self._panels.index(event.EventObject.Parent)
        self.SetValue(i)

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        self._value = value
        for i, panel in enumerate(self._panels):
            if i == value:
                panel.Value = True
            else:
                panel.Value = False

        evt = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, self.GetId())
        evt.EventObject = self
        wx.PostEvent(self.Parent, evt)

    Value = property(GetValue, SetValue)

    def _layout_children(self):
        for panel in self._panels:
            panel.layout_to_max_widths()

    def __getitem__(self, key):
        return self._panels[key]


class PlanChoicePanel(FancyRadioPanel):
    max_gb_width = 0
    max_price_width = 0
    PADDING = 5

    def __init__(self, parent, plan_data, base_font, i):
        super(PlanChoicePanel, self).__init__(parent, Colors.default_hover_color, Colors.default_hover_border_color, Colors.default_selected_color, Colors.default_selected_border_color, radius=3, first=i == 0)
        self._box_image = self.add_window(TransparentStaticBitmap, self._pick_image(plan_data, i))
        self._inner_sizer.Add((PlanChoicePanel.PADDING, 0))
        space = (72 - self._box_image.GetBestSize()[0]) / 2
        self._inner_sizer.Add((space, 0))
        self._inner_sizer.Add(self._box_image, flag=wx.ALIGN_CENTER)
        self._inner_sizer.Add((space, 0))
        gb_text = plan_data['name']
        self._gb_text = self.add_window(TransparentStaticText, label=gb_text)
        self._gb_text.Font = base_font
        gb_font = self._gb_text.Font
        gb_font.SetWeight(wx.FONTWEIGHT_BOLD)
        gb_font.SetPointSize(16)
        self._gb_text.Font = gb_font
        self._gb_sizer = wx.BoxSizer(wx.VERTICAL)
        PlanChoicePanel.max_gb_width = max(self._gb_text.BestSize[0], PlanChoicePanel.max_gb_width)
        self._gb_sizer.Add(self._gb_text, flag=wx.ALIGN_CENTER)
        self._inner_sizer.Add((PlanChoicePanel.PADDING, 0))
        self._inner_sizer.Add(self._gb_sizer, flag=wx.ALIGN_CENTER)
        self._inner_sizer.AddStretchSpacer(1)
        self._price_text = self.add_window(TransparentStaticText, label=plan_data['description'])
        self._price_text.Font = base_font
        PlanChoicePanel.max_price_width = max(self._price_text.BestSize[0], PlanChoicePanel.max_price_width)
        self._inner_sizer.Add(self._price_text, flag=wx.ALIGN_CENTER)
        self._inner_sizer.Add((FancyRadioPanel.LEFT_RIGHT_PADDING, 0))
        self._inner_sizer.SetMinSize((450, -1))
        self._inner_sizer.Layout()

    def GetValue(self):
        return self._selected

    def SetValue(self, value):
        if self._selected != value:
            colour = self._selected_border_colour if value else wx.BLACK
            self._gb_text.ForegroundColour = colour
            self._price_text.ForegroundColour = colour
            super(PlanChoicePanel, self).SetValue(value)

    Value = property(GetValue, SetValue)

    def _pick_image(self, plan_data, i):
        if i == 0:
            return ui.images.wximages.BoxSmall
        elif i == 1:
            return ui.images.wximages.BoxMed
        else:
            return ui.images.wximages.BoxLarge

    def layout_to_max_widths(self):
        self._gb_sizer.SetMinSize((PlanChoicePanel.max_gb_width, -1))
        self._price_text.SetMinSize((PlanChoicePanel.max_price_width, -1))


class PlanChoicesWidget(FancyRadioGroup):

    def __init__(self, parent, choices, base_font):
        super(PlanChoicesWidget, self).__init__(parent)
        self._choices = choices
        for i, choice in enumerate(choices):
            plan_choice_panel = PlanChoicePanel(self, choice, base_font, i)
            self.AddChoicePanel(plan_choice_panel)

        self._layout_children()

    def GetValue(self):
        return self._choices[self._value]

    def SetValue(self, value):
        if value is None:
            return
        try:
            int(value)
            super(PlanChoicesWidget, self).SetValue(value)
        except (ValueError, TypeError):
            super(PlanChoicesWidget, self).SetValue(self._choices.index(value))

    Value = property(GetValue, SetValue)


class WizardChoicePanel(FancyRadioPanel):
    PADDING = 5

    def __init__(self, parent, choice, first = False):
        super(WizardChoicePanel, self).__init__(parent, Colors.default_hover_color, Colors.default_hover_border_color, Colors.default_selected_color, Colors.default_selected_border_color, radius=3, first=first)
        self._inner_sizer.SetMinSize((450, -1))
        self._image = self.add_window(TransparentStaticBitmap, choice['image'])
        self._image.SetMinSize((72, -1))
        self._inner_sizer.Add((WizardChoicePanel.PADDING, 0))
        self._inner_sizer.Add(self._image, flag=wx.ALIGN_CENTER)
        content_sizer = wx.BoxSizer(wx.VERTICAL)
        label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._label = self.add_window(TransparentStaticText, label=choice['label'])
        label_font = platform.get_tour_font(self._label)
        label_font.Weight = wx.FONTWEIGHT_BOLD
        label_font.PointSize = 12
        self._label.Font = label_font
        label_sizer.Add(self._label)
        if 'sublabel' in choice and choice['sublabel'] is not None:
            self._sublabel = self.add_window(TransparentStaticText, label=choice['sublabel'])
            platform.apply_tour_font(self._sublabel, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
            self._sublabel.ForegroundColour = Colors.disabled_text
            dc = wx.WindowDC(self)
            label_baseline_offset = dc.GetFullTextExtent(choice['label'], label_font)[2]
            sublabel_baseline_offset = dc.GetFullTextExtent(choice['sublabel'], self._sublabel.Font)[2]
            del dc
            label_sizer.Add((WizardChoicePanel.PADDING, 0))
            label_sizer.Add(self._sublabel, flag=wx.ALIGN_BOTTOM | wx.BOTTOM, border=label_baseline_offset - sublabel_baseline_offset)
        content_sizer.Add(label_sizer)
        content_sizer.Add((0, WizardChoicePanel.PADDING))
        self._description = self.add_window(TransparentStaticText, label=choice['description'])
        platform.apply_tour_font(self._description, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        self._description.Wrap(360)
        content_sizer.Add(self._description)
        content_sizer.Add((16, 0))
        self._inner_sizer.Add(content_sizer, flag=wx.ALIGN_CENTER | wx.EXPAND)
        self._inner_sizer.Add((16, 0))
        self._inner_sizer.Layout()


class WizardRadioGroup(FancyRadioGroup):

    def __init__(self, parent, choices):
        super(WizardRadioGroup, self).__init__(parent)
        self._choices = choices
        for i, choice in enumerate(choices):
            panel = WizardChoicePanel(self, choice, i == 0)
            self.AddChoicePanel(panel)

        self._layout_children()

    def GetValue(self):
        return self._choices[self._value]

    def SetValue(self, value):
        if value is None:
            return
        try:
            int(value)
            super(WizardRadioGroup, self).SetValue(value)
        except (ValueError, TypeError):
            super(WizardRadioGroup, self).SetValue(self._choices.index(value))

    Value = property(GetValue, SetValue)


class AdvancedWizardChoicePanel(FancyRadioPanel):

    def __init__(self, parent, choice, first):
        super(AdvancedWizardChoicePanel, self).__init__(parent, Colors.default_hover_color, Colors.default_hover_border_color, Colors.default_selected_color, Colors.default_selected_border_color, radius=3, first=first)
        self._inner_sizer.SetMinSize((450, -1))
        rb_sizer_item = self._inner_sizer.GetItem(self._radio_button)
        if platform is GNOME:
            rb_sizer_item.SetFlag(wx.ALIGN_TOP)
        else:
            rb_sizer_item.SetFlag(wx.ALIGN_TOP | wx.TOP)
            rb_sizer_item.SetBorder(1)
        self._subcontrol_sizer = wx.GridBagSizer(10, 10)
        self._subcontrol_sizer.AddGrowableCol(0, 1)
        self._label = self.add_window(TransparentStaticText, label=choice)
        platform.apply_tour_font(self._label, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        self._label.Wrap(425)
        if platform is GNOME:
            border = 1
            flag = wx.TOP
        else:
            border = 0
            flag = 0
        self._subcontrol_sizer.Add(self._label, pos=(0, 0), span=(1, 2), border=border, flag=flag)
        self._inner_sizer.Add(self._subcontrol_sizer, 1, border=10, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        self._initial_controls = list(self.Children)
        self.Fit()

    def _get_subcontrol_sizer(self):
        return self._subcontrol_sizer

    subcontrol_sizer = property(_get_subcontrol_sizer)

    def GetValue(self):
        return super(AdvancedWizardChoicePanel, self).GetValue()

    def SetValue(self, value):
        super(AdvancedWizardChoicePanel, self).SetValue(value)
        for child in self.Children:
            if child not in self._initial_controls:
                child.Enable(value)

    Value = property(GetValue, SetValue)


class AdvancedWizardRadioGroup(FancyRadioGroup):

    def __init__(self, parent, choices):
        super(AdvancedWizardRadioGroup, self).__init__(parent)
        self._choices = choices
        for i, choice in enumerate(choices):
            panel = AdvancedWizardChoicePanel(self, choice, i == 0)
            self.AddChoicePanel(panel)

        self._layout_children()


EVT_DATE_PICKER_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)

class DatePickerChangedEvent(wx.PyCommandEvent):

    def __init__(self, win):
        super(DatePickerChangedEvent, self).__init__(EVT_DATE_PICKER_CHANGED.typeId, win.GetId())
        self.EventObject = win


class DatePicker(TransparentPanel):

    def __init__(self, parent, font, vgap = 5):
        super(DatePicker, self).__init__(parent, style=wx.TAB_TRAVERSAL)
        now = time.localtime()
        self._months = [ str(x) for x in xrange(1, 13) ]
        self._years = [ str(x) for x in xrange(now[0], now[0] + 20) ]
        self._month_picker = wx.Choice(self, choices=self._months)
        self._month_picker.SetFont(font)
        self._month_picker.SetSelection(self._months.index(str(now[1])))
        self._year_picker = wx.Choice(self, choices=self._years)
        self._year_picker.SetFont(font)
        self._year_picker.SetSelection(0)
        self._value = [self._month_picker.StringSelection, self._year_picker.StringSelection]
        self.Bind(wx.EVT_CHOICE, self.OnChoice)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._month_picker)
        sizer.AddSpacer((vgap, 0))
        sizer.Add(self._year_picker)
        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

    @event_handler
    def OnChoice(self, event):
        if event.EventObject is self._month_picker:
            self._value[0] = event.EventObject.StringSelection
        elif event.EventObject is self._year_picker:
            self._value[1] = event.EventObject.StringSelection
        else:
            return
        evt = DatePickerChangedEvent(self)
        wx.PostEvent(self.Parent, evt)

    def SetValue(self, value):
        if value is None:
            return
        assert len(value) == 2
        assert value[0] in self._months and value[1] in self._years
        self._month_picker.SetSelection(self._months.index(value[0]))
        self._month_picker.Refresh()
        self._year_picker.SetSelection(self._years.index(value[1]))
        self._year_picker.Refresh()
        self._value = value

    def GetValue(self):
        return self._value

    Value = property(GetValue, SetValue)


class CreditCardTypePanel(TransparentPanel, UnfocusableMixin):
    ALL_CARD_TYPES = [u'visa', u'mastercard', u'amex']

    def __init__(self, parent, vgap = 5):
        super(CreditCardTypePanel, self).__init__(parent)
        self.SetDoubleBuffered(True)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._setup_card_images()
        self._static_bitmaps = {}
        for i, card in enumerate(CreditCardTypePanel.ALL_CARD_TYPES):
            self._static_bitmaps[card] = wx.StaticBitmap(self, bitmap=self._images[card][0])
            sizer.Add(self._static_bitmaps[card])
            if i != len(CreditCardTypePanel.ALL_CARD_TYPES) - 1:
                sizer.AddSpacer((vgap, 0))

        self.SetAutoLayout(True)
        self.SetSizerAndFit(sizer)

    def _setup_card_images(self):
        CARD_IMAGES = {u'amex': ui.images.wximages.Amex,
         u'mastercard': ui.images.wximages.Mastercard,
         u'visa': ui.images.wximages.Visa}
        self._images = {}
        for k, v in CARD_IMAGES.iteritems():
            whole_bmp = v.Bitmap
            card_on = whole_bmp.GetSubBitmap((0,
             0,
             whole_bmp.Width / 2,
             whole_bmp.Height))
            card_off = whole_bmp.GetSubBitmap((whole_bmp.Width / 2,
             0,
             whole_bmp.Width / 2,
             whole_bmp.Height))
            self._images[k] = (card_on, card_off)

    def SetValue(self, val):
        for k, v in self._static_bitmaps.iteritems():
            if k == val or val is None:
                if v.GetBitmap() != self._images[k][0]:
                    v.SetBitmap(self._images[k][0])
            elif v.GetBitmap() != self._images[k][1]:
                v.SetBitmap(self._images[k][1])


class ButtonInfo(wx.lib.buttonpanel.ButtonInfo):

    def GetBestSize(self):
        size = super(ButtonInfo, self).GetBestSize()
        return wx.Size(max(size.GetWidth(), platform.min_buttonpanel_width), size.GetHeight())


class BPArt(wx.lib.buttonpanel.BPArt):

    def __init__(self, parentStyle, window):
        wx.lib.buttonpanel.BPArt.__init__(self, parentStyle)
        self._buttontext_font = platform.get_themed_font(window)
        self.SetColor(BP_GRADIENT_COLOR_FROM, Colors.white)
        self.SetColor(BP_GRADIENT_COLOR_TO, Colors.white)
        self.SetColor(BP_BUTTONTEXT_COLOR, Colors.black)
        self.SetColor(BP_SELECTION_BRUSH_COLOR, Colors.preferences_selection)
        self.SetColor(BP_SELECTION_PEN_COLOR, Colors.preferences_selection)
        self.SetMetric(BP_BORDER_SIZE, 0)

    def DrawButton(self, dc, rect, parentSize, buttonBitmap, isVertical, buttonStatus, isToggled, textAlignment, text = ''):
        bmpxsize, bmpysize = buttonBitmap.GetWidth(), buttonBitmap.GetHeight()
        dx = dy = 0
        borderw = self._caption_border_size
        padding = self._padding_size
        buttonFont = self._buttontext_font
        try:
            dc.SetFont(buttonFont)
        except Exception:
            TRACE("Couldn't set themed font!")
            unhandled_exc_handler()

        if isVertical:
            rect = wx.Rect(borderw, rect.y, rect.width - 2 * borderw, rect.height)
            if text != '':
                textW, textH = dc.GetTextExtent(text)
                if textAlignment == BP_BUTTONTEXT_ALIGN_RIGHT:
                    fullExtent = bmpxsize + padding.x / 2 + textW
                    bmpypos = rect.y + (rect.height - bmpysize) / 2
                    bmpxpos = rect.x + (rect.width - fullExtent) / 2
                    textxpos = bmpxpos + padding.x / 2 + bmpxsize
                    textypos = bmpypos + (bmpysize - textH) / 2
                else:
                    bmpxpos = rect.x + (rect.width - bmpxsize) / 2
                    bmpypos = rect.y + padding.y
                    textxpos = rect.x + (rect.width - textW) / 2
                    textypos = bmpypos + bmpysize + padding.y / 2
            else:
                bmpxpos = rect.x + (rect.width - bmpxsize) / 2
                bmpypos = rect.y + (rect.height - bmpysize) / 2
        else:
            rect = wx.Rect(rect.x, borderw, rect.width, rect.height - 2 * borderw)
            if text != '':
                textW, textH = dc.GetTextExtent(text)
                if textAlignment == BP_BUTTONTEXT_ALIGN_RIGHT:
                    fullExtent = bmpxsize + padding.x / 2 + textW
                    bmpypos = rect.y + (rect.height - bmpysize) / 2
                    bmpxpos = rect.x + (rect.width - fullExtent) / 2
                    textxpos = bmpxpos + padding.x / 2 + bmpxsize
                    textypos = bmpypos + (bmpysize - textH) / 2
                else:
                    fullExtent = bmpysize + padding.y / 2 + textH
                    bmpxpos = rect.x + (rect.width - bmpxsize) / 2
                    bmpypos = rect.y + (rect.height - fullExtent) / 2
                    textxpos = rect.x + (rect.width - textW) / 2
                    textypos = bmpypos + bmpysize + padding.y / 2
            else:
                bmpxpos = rect.x + (rect.width - bmpxsize) / 2
                bmpypos = rect.y + (rect.height - bmpysize) / 2
        if buttonStatus in ('Pressed', 'Toggled') or isToggled:
            dc.SetBrush(self._selection_brush)
            dc.SetPen(self._selection_pen)
            dc.DrawRectangleRect(rect)
            if buttonStatus == 'Toggled' or isToggled:
                dc.SetPen(wx.Pen(Colors.link))
                dc.DrawLine(rect.x, rect.y, rect.x, rect.y + rect.height)
                dc.DrawLine(rect.x + rect.width - 1, rect.y, rect.x + rect.width - 1, rect.y + rect.height)
        elif buttonStatus == 'Hover':
            if not hasattr(self, '_hover_brush'):
                self._hover_brush = wx.Brush(Colors.plan_choice_hover_background)
                self._hover_pen = wx.Pen(Colors.plan_choice_hover_background)
            dc.SetBrush(self._hover_brush)
            dc.SetPen(self._hover_pen)
            dc.DrawRectangleRect(rect)
        if buttonBitmap:
            dc.DrawBitmap(buttonBitmap, bmpxpos + dx, bmpypos + dy, True)
        if text != '':
            isEnabled = buttonStatus != 'Disabled'
            self.DrawLabel(dc, text, isEnabled, textxpos + dx, textypos + dy)


class DropboxFlagChoice(wx.combo.OwnerDrawnComboBox):

    def __init__(self, *n, **kw):
        if 'choices' in kw:
            self.country_choices = kw['choices']
            kw['choices'] = [ x[1] for x in kw['choices'] ]
        super(DropboxFlagChoice, self).__init__(*n, **kw)
        self.max_width = 0
        self.spacer_width = 8
        if self.country_choices:
            self.flag_width = self.country_choices[0][0].GetBitmap().GetWidth()
        else:
            raise ValueError("Can't instantiate an empty DropboxFlagChoice")

    def OnDrawItem(self, device_context, rect, item, flags):
        if item == wx.NOT_FOUND:
            return
        country_flag, country_name, country_number = self.country_choices[item]
        country_flag = country_flag.GetBitmap()
        rect = wx.Rect(*rect)
        rect.Deflate(3, 5)
        if not self.max_width:
            max_country_name_width = max((device_context.GetTextExtent(x[1])[0] for x in self.country_choices))
            self.max_width = self.spacer_width * 3 + max_country_name_width + self.flag_width + device_context.GetTextExtent('+0123')[0]
        offset_flag = [self.spacer_width / 2, 2]
        offset_country_name = [offset_flag[0] + self.spacer_width + self.flag_width, 0]
        offset_country_number = [rect.GetWidth() - device_context.GetTextExtent('+0123')[0], 0]
        if flags & wx.combo.ODCB_PAINTING_CONTROL:
            offset_country_number = [rect.GetWidth() - device_context.GetTextExtent(str(country_number.strip()))[0], 0]
            if platform == Win32 and WINDOWS_VERSION < VISTA:
                offset_country_number[0] -= 1
            max_country_len = offset_country_number[0] - self.flag_width - self.spacer_width
            if device_context.GetTextExtent(country_name)[0] > max_country_len:
                for i in xrange(10, len(country_name)):
                    if device_context.GetTextExtent(country_name)[0] > max_country_len:
                        country_name = country_name[:-2]
                    else:
                        country_name = country_name[:-3]
                        country_name = country_name.strip() + '...'
                        break

            offset_flag[1] = 0
            offset_country_name[1] = -2
            offset_country_number[1] = -2
            if platform == Win32:
                offset_flag[1] = -1
                offset_country_name[1] = -3
                offset_country_number[1] = -3
        device_context.DrawBitmap(country_flag, rect.x + offset_flag[0], rect.y + offset_flag[1])
        device_context.DrawText(country_name, rect.x + offset_country_name[0], rect.y + offset_country_name[1])
        device_context.DrawText(country_number, rect.x + offset_country_number[0], rect.y + offset_country_number[1])

    def OnDrawBackground(self, dc, rect, item, flags):
        if item % 2 == 0 or flags & (wx.combo.ODCB_PAINTING_CONTROL | wx.combo.ODCB_PAINTING_SELECTED):
            wx.combo.OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return
        bgCol = wx.Colour(240, 240, 250)
        dc.SetBrush(wx.Brush(bgCol))
        dc.SetPen(wx.Pen(bgCol))
        dc.DrawRectangleRect(rect)

    def OnMeasureItem(self, item):
        return 24

    def OnMeasureItemWidth(self, item):
        if not self.max_width:
            return 250
        return self.max_width


class ProgressWindow(object):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, msg, max_value):
        self.progress_dialog = wx.ProgressDialog(title='Copying', message=msg + ' ' * 50, maximum=max_value, style=wx.PD_CAN_ABORT | wx.PD_REMAINING_TIME)
        self.progress_dialog.Fit()

    @message_sender(wx.CallAfter, block=True)
    def set_progress(self, n):
        self.progress_dialog.Update(n)

    @message_sender(wx.CallAfter, block=True)
    def set_max_value(self, max_value):
        self.progress_dialog.maximum = max_value

    @message_sender(wx.CallAfter, block=True)
    def set_message(self, msg):
        self.progress_dialog.Update(0, msg)

    @message_sender(wx.CallAfter, block=True)
    def close(self):
        self.progress_dialog.Show(False)


class FancyGaugePanel(TransparentPanel):

    def __init__(self, parent, width, meters, colors, skip, value = 0):
        super(FancyGaugePanel, self).__init__(parent=parent)
        avail_width = width - (meters + 1) * skip
        control = wx.BoxSizer(wx.VERTICAL)
        fancy_gauge = wx.BoxSizer(wx.HORIZONTAL)
        panel_width = avail_width / meters
        self._panels = []
        self._colors = colors
        self._value = value
        self._default_color = colors[0]
        skip_size = (skip, 0)
        fancy_gauge.AddSpacer(skip_size)
        for n in range(0, meters):
            panel = wx.Panel(self, -1, size=(panel_width, 5))
            panel.SetBackgroundColour(self._default_color)
            self._panels.append(panel)
            fancy_gauge.Add(panel, border=skip, flag=wx.LEFT)

        fancy_gauge.AddSpacer(skip_size)
        control.Add(fancy_gauge)
        text = TransparentStaticText(self, label='')
        text_sizer = wx.BoxSizer(wx.HORIZONTAL)
        platform.apply_tour_font(text, override_system_colors=_SHOULD_OVERRIDE_SYSTEM_COLORS)
        font = text.Font
        font.PointSize = 7
        text.Font = font
        text_sizer.AddSpacer((skip * 2, 0))
        text_sizer.Add(text, flag=wx.ALIGN_LEFT | wx.EXPAND)
        control.Add(text_sizer)
        self._text = text
        self.SetSizerAndFit(control)

    def SetValue(self, v):
        value, text = v
        self._value = value
        self._text.SetLabel(text)
        self._text.Refresh()
        for n, panel in enumerate(self._panels):
            if n < value:
                panel.SetBackgroundColour(self._colors[value])
            else:
                panel.SetBackgroundColour(self._default_color)
            panel.Refresh()
