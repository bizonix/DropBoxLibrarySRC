#Embedded file name: ui/wxpython/static_link_text.py
from __future__ import absolute_import
import wx
from dropbox.gui import event_handler
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.url_info import dropbox_url_info
from .constants import platform, Colors, GNOME
from .dropbox_controls import TransparentPanel, UnfocusableMixin
from .util import dirty_rects, ExtendedLinkedText, SPACE_TOKENS, tokenize

def CopyFont(font):
    return wx.Font(pointSize=font.GetPointSize(), family=font.GetFamily(), style=font.GetStyle(), weight=font.GetWeight(), underline=font.GetUnderlined(), encoding=font.GetEncoding(), **({'face': font.GetFaceName()} if font.GetFaceName() else {}))


class StaticLinkText(TransparentPanel, UnfocusableMixin):
    old_cursor = None

    def __init__(self, parent, label, on_click = None, *n, **kw):
        if 'line_height' in kw:
            self.line_height = kw['line_height']
            del kw['line_height']
        else:
            self.line_height = None
        super(StaticLinkText, self).__init__(parent, *n, **kw)
        self.label = label
        self.on_click = on_click
        self.mouseDown = False
        self.lastMouseRect = None
        self.background_color, self.foreground_color = (None, None)
        self.last_munch = None
        self.wrap = None
        self.fixed_width = False
        self.hovering_rect = None
        self.center = False
        self.tip = wx.ToolTip(tip='')
        self.SetToolTip(self.tip)
        self.tip.Enable(False)
        self.text_font = None
        self._buffer = None
        try:
            self.SetFont(platform.get_themed_font(parent))
        except Exception:
            TRACE("Couldn't set themed font!")
            unhandled_exc_handler()

        if self.old_cursor is None:
            self.old_cursor = self.GetCursor()
        self.click_rects = {}
        self.OnSize(None)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOVE, self.OnSize)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMotion)
        if platform is GNOME:
            self.Bind(wx.EVT_ERASE_BACKGROUND, None)

    def get_width(self, dc, token_list):
        return dc.GetTextExtent(''.join(token_list))[0]

    def munch(self, dc):
        if self.last_munch:
            if self.last_munch[0] == (self.label, self.wrap, self.text_font):
                return self.last_munch[1]
        tokens = tokenize(self.label)
        lines = []
        current_line = []
        current_spacers = []
        for token in tokens:
            if token == '\n':
                lines.append(current_line)
                current_line = []
                current_spacers = []
                continue
            elif token in SPACE_TOKENS:
                if not current_line:
                    continue
                else:
                    current_spacers += token
                    continue
            potential_line = current_line + current_spacers + [token]
            if self.wrap:
                if current_line:
                    if self.get_width(dc, potential_line) > self.wrap:
                        lines.append(current_line)
                        current_spacers = []
                        current_line = [token]
                        continue
            current_line = potential_line
            current_spacers = []

        lines.append(current_line)
        munches = []
        h = 0
        for line in lines:
            text = ''.join(line)
            link_runs = []
            offset = 0
            for token in line:
                if isinstance(token, ExtendedLinkedText):
                    link_runs.append((offset + token.start, offset + token.end, token.url))
                offset += len(token)

            munches.append((text, link_runs))
            line_height = dc.GetTextExtent(text)[1] if text else dc.GetTextExtent('A')[1]
            if self.line_height is not None and h != 0:
                line_height = max(self.line_height, line_height)
            h += line_height

        retval = (munches, h)
        self.last_munch = ((self.label, self.wrap, self.text_font), retval)
        return retval

    @event_handler
    def Draw(self, dc):
        if not dc:
            return
        dc.SetFont(self.text_font)
        if self.GetBackground(self):
            bmp, (x, y) = self.GetBackground(self)
            dc.SetBackground(wx.WHITE_BRUSH)
            dc.Clear()
            dc.DrawBitmap(bmp, x, y)
        else:
            bg_col = self.background_color if self.background_color else Colors.white
            dc.SetPen(wx.Pen(bg_col))
            dc.SetBrush(wx.Brush(bg_col, wx.SOLID))
            dc.DrawRectangle(0, 0, self.width, self.height)
        lines, height = self.munch(dc)
        y = 0
        self.click_rects = {}
        for line, link_runs in lines:
            if link_runs:
                pieces = [(line[:link_runs[0][0]], '')] if link_runs[0][0] else []
                for i in range(len(link_runs)):
                    pieces.append((line[link_runs[i][0]:link_runs[i][1]], link_runs[i][2]))
                    pieces.append((line[link_runs[i][1]:link_runs[i + 1][0]] if i < len(link_runs) - 1 else line[link_runs[i][1]:], ''))

            else:
                pieces = [(line, '')]
            x = 0
            h = 0
            if self.center:
                total_width = sum((dc.GetTextExtent(piece[0])[0] for piece in pieces))
                if total_width < dc.GetSize().GetWidth():
                    x = (dc.GetSize().GetWidth() - total_width) // 2
            for piece in pieces:
                if piece != ('', ''):
                    w, this_h = dc.GetTextExtent(piece[0])
                    r = wx.Rect(x, y, w, this_h)
                    if self.hovering_rect is not None and self.hovering_rect == r:
                        dc.SetFont(self.link_font)
                    else:
                        dc.SetFont(self.text_font)
                    if piece[1]:
                        self.click_rects[r] = piece[1]
                        dc.SetTextForeground(Colors.link)
                    else:
                        dc.SetTextForeground(self.foreground_color if self.foreground_color else Colors.black)
                    dc.DrawLabel(piece[0], r)
                    x += w
                    h = max(h, this_h)
                else:
                    h = max(h, dc.GetTextExtent('A')[1])

            if self.line_height is not None:
                h = max(h, self.line_height)
            y += h

    @event_handler
    def OnMotion(self, event):
        for r in self.click_rects:
            if r.Contains(event.GetPosition()):
                self.tip.SetTip(self.click_rects[r])
                self.tip.Enable(True)
                self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
                if self.hovering_rect != r:
                    old_rect = self.hovering_rect
                    self.hovering_rect = r
                    self.OnSize(None)
                    self.RefreshRect(old_rect)
                    self.RefreshRect(r)
                return

        self.tip.Enable(False)
        self.SetCursor(self.old_cursor)
        if self.hovering_rect is not None:
            old_rect = self.hovering_rect
            self.hovering_rect = None
            self.OnSize(None)
            self.RefreshRect(old_rect)

    @event_handler
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        for x, y, w, h in dirty_rects(self):
            dc.Blit(x, y, w, h, self._mem_dc, x, y)

    @event_handler
    def init_buffer(self):
        if self._buffer and self._buffer.GetWidth() == self.width:
            if self._buffer.GetHeight() == self.height:
                return True
        dc = wx.ClientDC(self)
        dc.SetFont(self.text_font)
        lines, self.height = self.munch(dc)
        raw_text = '\n'.join([ line[0] for line in lines ])
        text_width = dc.GetMultiLineTextExtent(raw_text)[0]
        if self.wrap:
            if self.fixed_width:
                self.width = self.wrap
            else:
                self.width = min(text_width, self.wrap)
        else:
            self.width = text_width
        self.SetMinSize(wx.Size(self.width, self.height))
        self._buffer = wx.EmptyBitmap(self.width, self.height)
        return True

    @event_handler
    def OnSize(self, event):
        if self.init_buffer():
            self._mem_dc = wx.MemoryDC()
            self._mem_dc.SelectObject(self._buffer)
            self.Draw(self._mem_dc)

    @event_handler
    def OnMouseDown(self, event):
        self.mouseDown = True
        self.lastMouseRect = None
        for r in self.click_rects:
            if r.Contains(event.GetPosition()):
                self.lastMouseRect = r

    @event_handler
    def OnMouseUp(self, event):
        processed = False
        for r in self.click_rects:
            if r.Contains(event.GetPosition()):
                processed = True
                if self.lastMouseRect == r:
                    self.link_handler(self.click_rects[r])

        if not processed and self.on_click is not None and self.mouseDown and self.lastMouseRect == None:
            self.on_click(self.click_rects[r])
        self.mouseDown = False
        self.lastMouseRect = None

    @event_handler
    def link_handler(self, link):
        dropbox_url_info.launch_full_url(link)

    @event_handler
    def SetLabel(self, label):
        self.label = label
        self.OnSize(None)
        self.Refresh()

    @event_handler
    def Wrap(self, width, fixed_width = False, center = False):
        self.wrap = width
        self.fixed_width = fixed_width
        self.center = center
        self._buffer = None
        self.OnSize(None)

    def GetFont(self):
        return CopyFont(self.text_font)

    @event_handler
    def SetFont(self, font):
        if font != self.text_font:
            self.text_font = CopyFont(font)
            self.link_font = CopyFont(font)
            self.link_font.SetUnderlined(True)
            self.last_munch = None
            self.OnSize(None)

    Font = property(GetFont, SetFont)

    @event_handler
    def SetForegroundColour(self, color):
        if color != self.foreground_color:
            self.foreground_color = color
            self.OnSize(None)

    @event_handler
    def SetBackgroundColour(self, color):
        if color != self.background_color:
            self.background_color = color
            self.OnSize(None)
