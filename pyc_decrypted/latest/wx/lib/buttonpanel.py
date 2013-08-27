#Embedded file name: wx/lib/buttonpanel.py
import wx
BP_BACKGROUND_COLOR = 0
BP_GRADIENT_COLOR_FROM = 1
BP_GRADIENT_COLOR_TO = 2
BP_BORDER_COLOR = 3
BP_TEXT_COLOR = 4
BP_BUTTONTEXT_COLOR = 5
BP_BUTTONTEXT_INACTIVE_COLOR = 6
BP_SELECTION_BRUSH_COLOR = 7
BP_SELECTION_PEN_COLOR = 8
BP_SEPARATOR_COLOR = 9
BP_TEXT_FONT = 10
BP_BUTTONTEXT_FONT = 11
BP_BUTTONTEXT_ALIGN_BOTTOM = 12
BP_BUTTONTEXT_ALIGN_RIGHT = 13
BP_SEPARATOR_SIZE = 14
BP_MARGINS_SIZE = 15
BP_BORDER_SIZE = 16
BP_PADDING_SIZE = 17
BP_GRADIENT_NONE = 0
BP_GRADIENT_VERTICAL = 1
BP_GRADIENT_HORIZONTAL = 2
BP_HT_BUTTON = 200
BP_HT_NONE = 201
BP_ALIGN_RIGHT = 1
BP_ALIGN_LEFT = 2
BP_ALIGN_TOP = 4
BP_ALIGN_BOTTOM = 8
BP_DEFAULT_STYLE = 1
BP_USE_GRADIENT = 2
_DELAY = 3000
if wx.VERSION_STRING < '2.7':
    wx.Rect.Contains = lambda self, point: wx.Rect.Inside(self, point)

def BrightenColour(color, factor):
    val = color.Red() * factor
    if val > 255:
        red = 255
    else:
        red = val
    val = color.Green() * factor
    if val > 255:
        green = 255
    else:
        green = val
    val = color.Blue() * factor
    if val > 255:
        blue = 255
    else:
        blue = val
    return wx.Color(red, green, blue)


def GrayOut(anImage):
    factor = 0.7
    anImage = anImage.ConvertToImage()
    if anImage.HasAlpha():
        anImage.ConvertAlphaToMask(1)
    if anImage.HasMask():
        maskColor = (anImage.GetMaskRed(), anImage.GetMaskGreen(), anImage.GetMaskBlue())
    else:
        maskColor = None
    data = map(ord, list(anImage.GetData()))
    for i in range(0, len(data), 3):
        pixel = (data[i], data[i + 1], data[i + 2])
        pixel = MakeGray(pixel, factor, maskColor)
        for x in range(3):
            data[i + x] = pixel[x]

    anImage.SetData(''.join(map(chr, data)))
    anImage = anImage.ConvertToBitmap()
    return anImage


def MakeGray((r, g, b), factor, maskColor):
    if (r, g, b) != maskColor:
        return map(lambda x: int((230 - x) * factor) + x, (r, g, b))
    else:
        return (r, g, b)


class BPArt():

    def __init__(self, parentStyle):
        base_color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        self._background_brush = wx.Brush(base_color, wx.SOLID)
        self._gradient_color_to = wx.WHITE
        self._gradient_color_from = wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
        if parentStyle & BP_USE_GRADIENT:
            self._border_pen = wx.Pen(wx.WHITE, 3)
            self._caption_text_color = wx.WHITE
            self._buttontext_color = wx.Colour(70, 143, 255)
            self._separator_pen = wx.Pen(BrightenColour(self._gradient_color_from, 1.4))
            self._gradient_type = BP_GRADIENT_VERTICAL
        else:
            self._border_pen = wx.Pen(BrightenColour(base_color, 0.9), 3)
            self._caption_text_color = wx.BLACK
            self._buttontext_color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_BTNTEXT)
            self._separator_pen = wx.Pen(BrightenColour(base_color, 0.9))
            self._gradient_type = BP_GRADIENT_NONE
        self._buttontext_inactive_color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT)
        self._selection_brush = wx.Brush(wx.Color(225, 225, 255))
        self._selection_pen = wx.Pen(wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION))
        sysfont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self._caption_font = wx.Font(sysfont.GetPointSize(), wx.DEFAULT, wx.NORMAL, wx.BOLD, False, sysfont.GetFaceName())
        self._buttontext_font = wx.Font(sysfont.GetPointSize(), wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, sysfont.GetFaceName())
        self._separator_size = 7
        self._margins_size = wx.Size(6, 6)
        self._caption_border_size = 3
        self._padding_size = wx.Size(6, 6)

    def GetMetric(self, id):
        if id == BP_SEPARATOR_SIZE:
            return self._separator_size
        if id == BP_MARGINS_SIZE:
            return self._margins_size
        if id == BP_BORDER_SIZE:
            return self._caption_border_size
        if id == BP_PADDING_SIZE:
            return self._padding_size
        raise '\nERROR: Invalid Metric Ordinal. '

    def SetMetric(self, id, new_val):
        if id == BP_SEPARATOR_SIZE:
            self._separator_size = new_val
        elif id == BP_MARGINS_SIZE:
            self._margins_size = new_val
        elif id == BP_BORDER_SIZE:
            self._caption_border_size = new_val
            self._border_pen.SetWidth(new_val)
        elif id == BP_PADDING_SIZE:
            self._padding_size = new_val
        else:
            raise '\nERROR: Invalid Metric Ordinal. '

    def GetColor(self, id):
        if id == BP_BACKGROUND_COLOR:
            return self._background_brush.GetColour()
        if id == BP_GRADIENT_COLOR_FROM:
            return self._gradient_color_from
        if id == BP_GRADIENT_COLOR_TO:
            return self._gradient_color_to
        if id == BP_BORDER_COLOR:
            return self._border_pen.GetColour()
        if id == BP_TEXT_COLOR:
            return self._caption_text_color
        if id == BP_BUTTONTEXT_COLOR:
            return self._buttontext_color
        if id == BP_BUTTONTEXT_INACTIVE_COLOR:
            return self._buttontext_inactive_color
        if id == BP_SELECTION_BRUSH_COLOR:
            return self._selection_brush.GetColour()
        if id == BP_SELECTION_PEN_COLOR:
            return self._selection_pen.GetColour()
        if id == BP_SEPARATOR_COLOR:
            return self._separator_pen.GetColour()
        raise '\nERROR: Invalid Colour Ordinal. '

    def SetColor(self, id, colour):
        if id == BP_BACKGROUND_COLOR:
            self._background_brush.SetColour(colour)
        elif id == BP_GRADIENT_COLOR_FROM:
            self._gradient_color_from = colour
        elif id == BP_GRADIENT_COLOR_TO:
            self._gradient_color_to = colour
        elif id == BP_BORDER_COLOR:
            self._border_pen.SetColour(colour)
        elif id == BP_TEXT_COLOR:
            self._caption_text_color = colour
        elif id == BP_BUTTONTEXT_COLOR:
            self._buttontext_color = colour
        elif id == BP_BUTTONTEXT_INACTIVE_COLOR:
            self._buttontext_inactive_color = colour
        elif id == BP_SELECTION_BRUSH_COLOR:
            self._selection_brush.SetColour(colour)
        elif id == BP_SELECTION_PEN_COLOR:
            self._selection_pen.SetColour(colour)
        elif id == BP_SEPARATOR_COLOR:
            self._separator_pen.SetColour(colour)
        else:
            raise '\nERROR: Invalid Colour Ordinal. '

    GetColour = GetColor
    SetColour = SetColor

    def SetFont(self, id, font):
        if id == BP_TEXT_FONT:
            self._caption_font = font
        elif id == BP_BUTTONTEXT_FONT:
            self._buttontext_font = font

    def GetFont(self, id):
        if id == BP_TEXT_FONT:
            return self._caption_font
        if id == BP_BUTTONTEXT_FONT:
            return self._buttontext_font
        return wx.NoneFont

    def SetGradientType(self, gradient):
        self._gradient_type = gradient

    def GetGradientType(self):
        return self._gradient_type

    def DrawSeparator(self, dc, rect, isVertical):
        dc.SetPen(self._separator_pen)
        if isVertical:
            ystart = yend = rect.y + rect.height / 2
            xstart = int(rect.x + 1.5 * self._caption_border_size)
            xend = int(rect.x + rect.width - 1.5 * self._caption_border_size)
            dc.DrawLine(xstart, ystart, xend, yend)
        else:
            xstart = xend = rect.x + rect.width / 2
            ystart = int(rect.y + 1.5 * self._caption_border_size)
            yend = int(rect.y + rect.height - 1.5 * self._caption_border_size)
            dc.DrawLine(xstart, ystart, xend, yend)

    def DrawCaption(self, dc, rect, captionText):
        textColour = self._caption_text_color
        textFont = self._caption_font
        padding = self._padding_size
        dc.SetTextForeground(textColour)
        dc.SetFont(textFont)
        dc.DrawText(captionText, rect.x + padding.x, rect.y + padding.y)

    def DrawButton(self, dc, rect, parentSize, buttonBitmap, isVertical, buttonStatus, isToggled, textAlignment, text = ''):
        bmpxsize, bmpysize = buttonBitmap.GetWidth(), buttonBitmap.GetHeight()
        dx = dy = focus = 0
        borderw = self._caption_border_size
        padding = self._padding_size
        buttonFont = self._buttontext_font
        dc.SetFont(buttonFont)
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
        if buttonStatus in ('Pressed', 'Toggled', 'Hover'):
            dc.SetBrush(self._selection_brush)
            dc.SetPen(self._selection_pen)
            dc.DrawRoundedRectangleRect(rect, 4)
        if buttonStatus == 'Pressed' or isToggled:
            dx = dy = 1
        if buttonBitmap:
            dc.DrawBitmap(buttonBitmap, bmpxpos + dx, bmpypos + dy, True)
        if text != '':
            isEnabled = buttonStatus != 'Disabled'
            self.DrawLabel(dc, text, isEnabled, textxpos + dx, textypos + dy)

    def DrawLabel(self, dc, text, isEnabled, xpos, ypos):
        if not isEnabled:
            dc.SetTextForeground(self._buttontext_inactive_color)
        else:
            dc.SetTextForeground(self._buttontext_color)
        dc.DrawText(text, xpos, ypos)

    def DrawButtonPanel(self, dc, rect, style):
        if style & BP_USE_GRADIENT:
            self.FillGradientColor(dc, rect)
        backBrush = (style & BP_USE_GRADIENT and [wx.TRANSPARENT_BRUSH] or [self._background_brush])[0]
        dc.SetBrush(backBrush)
        dc.SetPen(self._border_pen)
        dc.DrawRectangleRect(rect)

    def FillGradientColor(self, dc, rect):
        if rect.height < 1 or rect.width < 1:
            return
        isVertical = self._gradient_type == BP_GRADIENT_VERTICAL
        size = (isVertical and [rect.height] or [rect.width])[0]
        start = (isVertical and [rect.y] or [rect.x])[0]
        col2 = self._gradient_color_from
        col1 = self._gradient_color_to
        rf, gf, bf = (0, 0, 0)
        rstep = float(col2.Red() - col1.Red()) / float(size)
        gstep = float(col2.Green() - col1.Green()) / float(size)
        bstep = float(col2.Blue() - col1.Blue()) / float(size)
        for coord in xrange(start, start + size):
            currCol = wx.Colour(col1.Red() + rf, col1.Green() + gf, col1.Blue() + bf)
            dc.SetBrush(wx.Brush(currCol, wx.SOLID))
            dc.SetPen(wx.Pen(currCol))
            if isVertical:
                dc.DrawLine(rect.x, coord, rect.x + rect.width, coord)
            else:
                dc.DrawLine(coord, rect.y, coord, rect.y + rect.height)
            rf += rstep
            gf += gstep
            bf += bstep


class StatusBarTimer(wx.Timer):

    def __init__(self, owner):
        wx.Timer.__init__(self)
        self._owner = owner

    def Notify(self):
        self._owner.OnStatusBarTimer()


class Control(wx.EvtHandler):

    def __init__(self, parent, size = wx.Size(-1, -1)):
        wx.EvtHandler.__init__(self)
        self._parent = parent
        self._id = wx.NewId()
        self._size = size
        self._isshown = True
        self._focus = False

    def Show(self, show = True):
        self._isshown = show

    def Hide(self):
        self.Show(False)

    def IsShown(self):
        return self._isshown

    def GetId(self):
        return self._id

    def GetBestSize(self):
        return self._size

    def Disable(self):
        self.Enable(False)

    def Enable(self, value = True):
        self.disabled = not value

    def SetFocus(self, focus = True):
        self._focus = focus

    def HasFocus(self):
        return self._focus

    def OnMouseEvent(self, x, y, event):
        pass

    def Draw(self, rect):
        pass


class Sizer(object):

    def __init__(self):
        self.children = []

    def Draw(self, dc, x1 = 0, y1 = 0, x2 = 0, y2 = 0):
        for item in self.children:
            c = item.GetUserData()
            c.Draw(dc, item.GetRect())

    def GetBestSize(self):
        return self.GetMinSize()


class BoxSizer(Sizer, wx.BoxSizer):

    def __init__(self, orient = wx.HORIZONTAL):
        wx.BoxSizer.__init__(self, orient)
        Sizer.__init__(self)

    def Add(self, item, proportion = 0, flag = 0, border = 0, userData = None):
        if isinstance(item, Sizer):
            szitem = wx.BoxSizer.Add(self, item, proportion, flag, border, item)
            self.children.append(szitem)
        elif isinstance(item, Control):
            sz = item.GetBestSize()
            szitem = wx.BoxSizer.Add(self, sz, proportion, flag, border, item)
            self.children.append(szitem)
        else:
            wx.BoxSizer.Add(self, item, proportion, flag, border, userData)

    def Prepend(self, item, proportion = 0, flag = 0, border = 0, userData = None):
        if isinstance(item, Sizer):
            szitem = wx.BoxSizer.Prepend(self, item, proportion, flag, border, item)
            self.children.append(szitem)
        elif isinstance(item, Control):
            sz = item.GetBestSize()
            szitem = wx.BoxSizer.Prepend(self, sz, proportion, flag, border, item)
            self.children.insert(0, szitem)
        else:
            wx.BoxSizer.Prepend(self, item, proportion, flag, border, userData)

    def Insert(self, before, item, proportion = 0, flag = 0, border = 0, userData = None, realIndex = None):
        if isinstance(item, Sizer):
            szitem = wx.BoxSizer.Insert(self, before, item, proportion, flag, border, item)
            self.children.append(szitem)
        elif isinstance(item, Control):
            sz = item.GetBestSize()
            szitem = wx.BoxSizer.Insert(self, before, sz, proportion, flag, border, item)
            if realIndex is not None:
                self.children.insert(realIndex, szitem)
            else:
                self.children.insert(before, szitem)
        else:
            wx.BoxSizer.Insert(self, before, item, proportion, flag, border, userData)

    def Remove(self, indx, pop = -1):
        if pop >= 0:
            self.children.pop(pop)
        wx.BoxSizer.Remove(self, indx)

    def Layout(self):
        for ii, child in enumerate(self.GetChildren()):
            item = child.GetUserData()
            if item and child.IsShown():
                self.SetItemMinSize(ii, *item.GetBestSize())

        wx.BoxSizer.Layout(self)

    def Show(self, item, show = True):
        child = self.GetChildren()[item]
        if child and child.GetUserData():
            child.GetUserData().Show(show)
        wx.BoxSizer.Show(self, item, show)


class Separator(Control):

    def __init__(self, parent):
        self._isshown = True
        self._parent = parent
        Control.__init__(self, parent)

    def GetBestSize(self):
        if self._parent.IsVertical():
            return wx.Size(10, self._parent._art.GetMetric(BP_SEPARATOR_SIZE))
        else:
            return wx.Size(self._parent._art.GetMetric(BP_SEPARATOR_SIZE), 10)

    def Draw(self, dc, rect):
        if not self.IsShown():
            return
        isVertical = self._parent.IsVertical()
        self._parent._art.DrawSeparator(dc, rect, isVertical)


class ButtonPanelText(Control):

    def __init__(self, parent, text = ''):
        self._text = text
        self._isshown = True
        self._parent = parent
        Control.__init__(self, parent)

    def GetText(self):
        return self._text

    def SetText(self, text = ''):
        self._text = text

    def CreateDC(self):
        dc = wx.ClientDC(self._parent)
        textFont = self._parent._art.GetFont(BP_TEXT_FONT)
        dc.SetFont(textFont)
        return dc

    def GetBestSize(self):
        if self._text == '':
            return wx.Size(0, 0)
        dc = self.CreateDC()
        rect = self._parent.GetClientRect()
        tw, th = dc.GetTextExtent(self._text)
        padding = self._parent._art.GetMetric(BP_PADDING_SIZE)
        self._size = wx.Size(tw + 2 * padding.x, th + 2 * padding.y)
        return self._size

    def Draw(self, dc, rect):
        if not self.IsShown():
            return
        captionText = self.GetText()
        self._parent._art.DrawCaption(dc, rect, captionText)


class ButtonInfo(Control):

    def __init__(self, parent, id = wx.ID_ANY, bmp = wx.NullBitmap, status = 'Normal', text = '', kind = wx.ITEM_NORMAL, shortHelp = '', longHelp = ''):
        if id == wx.ID_ANY:
            id = wx.NewId()
        self._status = status
        self._rect = wx.Rect()
        self._text = text
        self._kind = kind
        self._toggle = False
        self._textAlignment = BP_BUTTONTEXT_ALIGN_BOTTOM
        self._shortHelp = shortHelp
        self._longHelp = longHelp
        if bmp:
            disabledbmp = GrayOut(bmp)
        else:
            disabledbmp = wx.NullBitmap
        self._bitmaps = {'Normal': bmp,
         'Toggled': None,
         'Disabled': disabledbmp,
         'Hover': None,
         'Pressed': None}
        Control.__init__(self, parent)

    def GetBestSize(self):
        xsize = self.GetBitmap().GetWidth()
        ysize = self.GetBitmap().GetHeight()
        if self.HasText():
            dc = wx.ClientDC(self._parent)
            normalFont = self._parent._art.GetFont(BP_BUTTONTEXT_FONT)
            dc.SetFont(normalFont)
            tw, th = dc.GetTextExtent(self.GetText())
            if self.GetTextAlignment() == BP_BUTTONTEXT_ALIGN_BOTTOM:
                xsize = max(xsize, tw)
                ysize = ysize + th
            else:
                xsize = xsize + tw
                ysize = max(ysize, th)
        border = self._parent._art.GetMetric(BP_BORDER_SIZE)
        padding = self._parent._art.GetMetric(BP_PADDING_SIZE)
        if self._parent.IsVertical():
            xsize = xsize + 2 * border
        else:
            ysize = ysize + 2 * border
        self._size = wx.Size(xsize + 2 * padding.x, ysize + 2 * padding.y)
        return self._size

    def Draw(self, dc, rect):
        if not self.IsShown():
            return
        buttonBitmap = self.GetBitmap()
        isVertical = self._parent.IsVertical()
        text = self.GetText()
        parentSize = self._parent.GetSize()[not isVertical]
        buttonStatus = self.GetStatus()
        isToggled = self.GetToggled()
        textAlignment = self.GetTextAlignment()
        self._parent._art.DrawButton(dc, rect, parentSize, buttonBitmap, isVertical, buttonStatus, isToggled, textAlignment, text)
        self.SetRect(rect)

    def CheckRefresh(self, status):
        if status == self._status:
            self._parent.RefreshRect(self.GetRect())

    def SetBitmap(self, bmp, status = 'Normal'):
        self._bitmaps[status] = bmp
        self.CheckRefresh(status)

    def GetBitmap(self, status = None):
        if status is None:
            status = self._status
        if not self.IsEnabled():
            status = 'Disabled'
        if self._bitmaps[status] is None:
            return self._bitmaps['Normal']
        return self._bitmaps[status]

    def GetRect(self):
        return self._rect

    def GetStatus(self):
        return self._status

    def GetId(self):
        return self._id

    def SetRect(self, rect):
        self._rect = rect

    def SetStatus(self, status):
        if status == self._status:
            return
        if self.GetToggled() and status == 'Normal':
            status = 'Toggled'
        self._status = status
        self._parent.RefreshRect(self.GetRect())

    def GetTextAlignment(self):
        return self._textAlignment

    def SetTextAlignment(self, alignment):
        if alignment == self._textAlignment:
            return
        self._textAlignment = alignment

    def GetToggled(self):
        if self._kind == wx.ITEM_NORMAL:
            return False
        return self._toggle

    def SetToggled(self, toggle = True):
        if self._kind == wx.ITEM_NORMAL:
            return
        self._toggle = toggle

    def SetId(self, id):
        self._id = id

    def AddStatus(self, name = 'Custom', bmp = wx.NullBitmap):
        self._bitmaps.update({name: bmp})

    def Enable(self, enable = True):
        if enable:
            self._status = 'Normal'
        else:
            self._status = 'Disabled'

    def IsEnabled(self):
        return self._status != 'Disabled'

    def SetText(self, text = ''):
        self._text = text

    def GetText(self):
        return self._text

    def HasText(self):
        return self._text != ''

    def SetKind(self, kind = wx.ITEM_NORMAL):
        self._kind = kind

    def GetKind(self):
        return self._kind

    def SetShortHelp(self, help = ''):
        self._shortHelp = help

    def GetShortHelp(self):
        return self._shortHelp

    def SetLongHelp(self, help = ''):
        self._longHelp = help

    def GetLongHelp(self):
        return self._longHelp

    Bitmap = property(GetBitmap, SetBitmap)
    Id = property(GetId, SetId)
    Rect = property(GetRect, SetRect)
    Status = property(GetStatus, SetStatus)


class ButtonPanel(wx.PyPanel):

    def __init__(self, parent, id = wx.ID_ANY, text = '', style = BP_DEFAULT_STYLE, alignment = BP_ALIGN_LEFT, name = 'buttonPanel'):
        wx.PyPanel.__init__(self, parent, id, wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER, name=name)
        self._vButtons = []
        self._vSeparators = []
        self._nStyle = style
        self._alignment = alignment
        self._statusTimer = None
        self._useHelp = True
        self._freezeCount = 0
        self._currentButton = -1
        self._haveTip = False
        self._art = BPArt(style)
        self._controlCreated = False
        direction = (self.IsVertical() and [wx.VERTICAL] or [wx.HORIZONTAL])[0]
        self._mainsizer = BoxSizer(direction)
        self.SetSizer(self._mainsizer)
        margins = self._art.GetMetric(BP_MARGINS_SIZE)
        self._mainsizer.Add((margins.x, margins.y), 0)
        self._mainsizer.Add((margins.x, margins.y), 0)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnterWindow)
        self.SetBarText(text)
        self.LayoutItems()

    def SetBarText(self, text):
        self.Freeze()
        text = text.strip()
        if self._controlCreated:
            self.RemoveText()
        self._text = ButtonPanelText(self, text)
        lenChildren = len(self._mainsizer.GetChildren())
        if text == '':
            if self.IsStandard():
                self._mainsizer.Insert(1, self._text, 0, wx.ALIGN_CENTER, userData=self._text, realIndex=0)
            else:
                self._mainsizer.Insert(lenChildren - 1, self._text, 0, wx.ALIGN_CENTER, userData=self._text, realIndex=lenChildren)
            return
        if self.IsStandard():
            self._mainsizer.Insert(1, self._text, 0, wx.ALIGN_CENTER, userData=self._text, realIndex=0)
            self._mainsizer.Insert(2, (0, 0), 1, wx.EXPAND)
        else:
            self._mainsizer.Insert(lenChildren - 1, self._text, 0, wx.ALIGN_CENTER, userData=self._text, realIndex=lenChildren)
            self._mainsizer.Insert(lenChildren - 1, (0, 0), 1, wx.EXPAND)

    def RemoveText(self):
        lenChildren = len(self._mainsizer.GetChildren())
        lenCustom = len(self._vButtons) + len(self._vSeparators) + 1
        if self.IsStandard():
            self._mainsizer.Remove(1, 0)
            if self.HasBarText():
                self._mainsizer.Remove(1, -1)
        else:
            self._mainsizer.Remove(lenChildren - 2, lenCustom - 1)
            if self.HasBarText():
                self._mainsizer.Remove(lenChildren - 3, -1)

    def GetBarText(self):
        return self._text.GetText()

    def HasBarText(self):
        return hasattr(self, '_text') and self._text.GetText() != ''

    def AddButton(self, btnInfo):
        lenChildren = len(self._mainsizer.GetChildren())
        self._mainsizer.Insert(lenChildren - 1, btnInfo, 0, wx.ALIGN_CENTER | wx.EXPAND, userData=btnInfo)
        self._vButtons.append(btnInfo)

    def AddSpacer(self, size = (0, 0), proportion = 1, flag = wx.EXPAND):
        lenChildren = len(self._mainsizer.GetChildren())
        self._mainsizer.Insert(lenChildren - 1, size, proportion, flag)

    def AddControl(self, control, proportion = 0, flag = wx.ALIGN_CENTER | wx.ALL, border = None):
        lenChildren = len(self._mainsizer.GetChildren())
        if border is None:
            border = self._art.GetMetric(BP_PADDING_SIZE)
            border = max(border.x, border.y)
        self._mainsizer.Insert(lenChildren - 1, control, proportion, flag, border)

    def AddSeparator(self):
        lenChildren = len(self._mainsizer.GetChildren())
        separator = Separator(self)
        self._mainsizer.Insert(lenChildren - 1, separator, 0, wx.EXPAND)
        self._vSeparators.append(separator)

    def RemoveAllButtons(self):
        self._vButtons = []

    def RemoveAllSeparators(self):
        self._vSeparators = []

    def GetAlignment(self):
        return self._alignment

    def SetAlignment(self, alignment):
        if alignment == self._alignment:
            return
        self.Freeze()
        text = self.GetBarText()
        self.RemoveText()
        self._mainsizer.Remove(0, -1)
        self._mainsizer.Remove(len(self._mainsizer.GetChildren()) - 1, -1)
        self._alignment = alignment
        self.ReCreateSizer(text)

    def IsVertical(self):
        return self._alignment not in [BP_ALIGN_RIGHT, BP_ALIGN_LEFT]

    def IsStandard(self):
        return self._alignment in [BP_ALIGN_LEFT, BP_ALIGN_TOP]

    def DoLayout(self):
        margins = self._art.GetMetric(BP_MARGINS_SIZE)
        lenChildren = len(self._mainsizer.GetChildren())
        self._mainsizer.SetItemMinSize(0, (margins.x, margins.y))
        self._mainsizer.SetItemMinSize(lenChildren - 1, (margins.x, margins.y))
        self._controlCreated = True
        self.LayoutItems()
        size = self.GetSize()
        self.SetSize((size.x + 1, size.y + 1))
        self.SetSize((size.x, size.y))
        if self.IsFrozen():
            self.Thaw()

    def ReCreateSizer(self, text):
        children = self._mainsizer.GetChildren()
        self.RemoveAllButtons()
        self.RemoveAllSeparators()
        direction = (self.IsVertical() and [wx.VERTICAL] or [wx.HORIZONTAL])[0]
        self._mainsizer = BoxSizer(direction)
        margins = self._art.GetMetric(BP_MARGINS_SIZE)
        self._mainsizer.Add((margins.x, margins.y), 0)
        self._mainsizer.Add((margins.x, margins.y), 0)
        self._controlCreated = False
        for child in children:
            userData = child.GetUserData()
            if userData:
                if isinstance(userData, ButtonInfo):
                    self.AddButton(child.GetUserData())
                elif isinstance(userData, Separator):
                    self.AddSeparator()
            elif child.IsSpacer():
                self.AddSpacer(child.GetSize(), child.GetProportion(), child.GetFlag())
            else:
                self.AddControl(child.GetWindow(), child.GetProportion(), child.GetFlag(), child.GetBorder())

        self.SetSizer(self._mainsizer)
        self.SetBarText(text)
        self.DoLayout()
        self.Thaw()

    def DoGetBestSize(self):
        w = h = btnWidth = btnHeight = 0
        isVertical = self.IsVertical()
        padding = self._art.GetMetric(BP_PADDING_SIZE)
        border = self._art.GetMetric(BP_BORDER_SIZE)
        margins = self._art.GetMetric(BP_MARGINS_SIZE)
        separator_size = self._art.GetMetric(BP_SEPARATOR_SIZE)
        if self.HasBarText():
            w, h = self._text.GetBestSize()
            if isVertical:
                h += padding.y
            else:
                w += padding.x
        else:
            w = h = border
        for btn in self._vButtons:
            bw, bh = btn.GetBestSize()
            btnWidth = max(btnWidth, bw)
            btnHeight = max(btnHeight, bh)
            if isVertical:
                w = max(w, btnWidth)
                h += bh
            else:
                h = max(h, btnHeight)
                w += bw

        for control in self.GetControls():
            cw, ch = control.GetSize()
            if isVertical:
                h += ch
                w = max(w, cw)
            else:
                w += cw
                h = max(h, ch)

        if self.IsVertical():
            h += 2 * margins.y + len(self._vSeparators) * separator_size
        else:
            w += 2 * margins.x + len(self._vSeparators) * separator_size
        return wx.Size(w, h)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        rect = self.GetClientRect()
        self._art.DrawButtonPanel(dc, rect, self._nStyle)
        self._mainsizer.Draw(dc)

    def OnEraseBackground(self, event):
        pass

    def OnSize(self, event):
        self.LayoutItems()
        self.Refresh()
        event.Skip()

    def LayoutItems(self):
        nonspacers, allchildren = self.GetNonFlexibleChildren()
        if self.HasBarText():
            self.FlexibleLayout(nonspacers, allchildren)
        else:
            self.SizeLayout(nonspacers, allchildren)
        self._mainsizer.Layout()

    def SizeLayout(self, nonspacers, children):
        size = self.GetSize()
        isVertical = self.IsVertical()
        corner = 0
        indx1 = len(nonspacers)
        for item in nonspacers:
            corner += self.GetItemSize(item, isVertical)
            if corner > size[isVertical]:
                indx1 = nonspacers.index(item)
                break

        for ii in xrange(len(nonspacers) - 1):
            indx = children.index(nonspacers[ii])
            self._mainsizer.Show(indx, ii < indx1)

    def GetItemSize(self, item, isVertical):
        if item.GetUserData():
            return item.GetUserData().GetBestSize()[isVertical]
        else:
            return item.GetSize()[isVertical]

    def FlexibleLayout(self, nonspacers, allchildren):
        if len(nonspacers) < 2:
            return
        isVertical = self.IsVertical()
        isStandard = self.IsStandard()
        size = self.GetSize()[isVertical]
        padding = self._art.GetMetric(BP_PADDING_SIZE)
        fixed = (isStandard and [nonspacers[1]] or [nonspacers[-2]])[0]
        if isStandard:
            nonspacers.reverse()
            leftendx = fixed.GetSize()[isVertical] + padding.x
        else:
            rightstartx = size - fixed.GetSize()[isVertical]
            size = 0
        count = lennonspacers = len(nonspacers)
        for item in nonspacers:
            if isStandard:
                size -= self.GetItemSize(item, isVertical)
                if size < leftendx:
                    break
            else:
                size += self.GetItemSize(item, isVertical)
                if size > rightstartx:
                    break
            count = count - 1

        nonspacers.reverse()
        for jj in xrange(2, lennonspacers):
            indx = allchildren.index(nonspacers[jj])
            self._mainsizer.Show(indx, jj >= count)

    def GetNonFlexibleChildren(self):
        children1 = []
        children2 = list(self._mainsizer.GetChildren())
        for child in children2:
            if child.IsSpacer():
                if child.GetUserData() or child.GetProportion() == 0:
                    children1.append(child)
            else:
                children1.append(child)

        return (children1, children2)

    def GetControls(self):
        children2 = self._mainsizer.GetChildren()
        children1 = [ child for child in children2 if not child.IsSpacer() ]
        return children1

    def SetStyle(self, style):
        if style == self._nStyle:
            return
        self._nStyle = style
        self.Refresh()

    def GetStyle(self):
        return self._nStyle

    def OnMouseMove(self, event):
        tabId, flags = self.HitTest(event.GetPosition())
        if flags != BP_HT_BUTTON:
            self.RemoveHelp()
            self.RepaintOldSelection()
            self._currentButton = -1
            return
        btn = self._vButtons[tabId]
        if not btn.IsEnabled():
            self.RemoveHelp()
            self.RepaintOldSelection()
            return
        if tabId != self._currentButton:
            self.RepaintOldSelection()
        if btn.GetRect().Contains(event.GetPosition()):
            if btn.GetStatus() != 'Pressed':
                btn.SetStatus('Hover')
        else:
            btn.SetStatus('Normal')
        if tabId != self._currentButton:
            self.RemoveHelp()
            self.DoGiveHelp(btn)
        self._currentButton = tabId
        event.Skip()

    def OnLeftDown(self, event):
        tabId, hit = self.HitTest(event.GetPosition())
        if hit == BP_HT_BUTTON:
            btn = self._vButtons[tabId]
            if btn.IsEnabled():
                btn.SetStatus('Pressed')
                self._currentButton = tabId

    def OnLeftUp(self, event):
        tabId, flags = self.HitTest(event.GetPosition())
        if flags != BP_HT_BUTTON:
            return
        hit = self._vButtons[tabId]
        if hit.GetStatus() == 'Disabled':
            return
        for btn in self._vButtons:
            if btn != hit:
                btn.SetFocus(False)

        if hit.GetStatus() == 'Pressed':
            hit.SetToggled(not hit.GetToggled())
            hit.SetStatus('Hover')
            hit.SetFocus()
            self._currentButton = tabId
            btnEvent = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, hit.GetId())
            self.GetEventHandler().ProcessEvent(btnEvent)

    def OnMouseLeave(self, event):
        for btn in self._vButtons:
            if not btn.IsEnabled():
                continue
            btn.SetStatus('Normal')

        self.RemoveHelp()
        event.Skip()

    def OnMouseEnterWindow(self, event):
        tabId, flags = self.HitTest(event.GetPosition())
        if flags == BP_HT_BUTTON:
            hit = self._vButtons[tabId]
            if hit.GetStatus() == 'Disabled':
                event.Skip()
                return
            self.DoGiveHelp(hit)
            self._currentButton = tabId
        event.Skip()

    def DoGiveHelp(self, hit):
        if not self.GetUseHelp():
            return
        shortHelp = hit.GetShortHelp()
        if shortHelp:
            self.SetToolTipString(shortHelp)
            self._haveTip = True
        longHelp = hit.GetLongHelp()
        if not longHelp:
            return
        topLevel = wx.GetTopLevelParent(self)
        if isinstance(topLevel, wx.Frame) and topLevel.GetStatusBar():
            statusBar = topLevel.GetStatusBar()
            if self._statusTimer and self._statusTimer.IsRunning():
                self._statusTimer.Stop()
                statusBar.PopStatusText(0)
            statusBar.PushStatusText(longHelp, 0)
            self._statusTimer = StatusBarTimer(self)
            self._statusTimer.Start(_DELAY, wx.TIMER_ONE_SHOT)

    def RemoveHelp(self):
        if not self.GetUseHelp():
            return
        if self._haveTip:
            self.SetToolTipString('')
            self._haveTip = False
        if self._statusTimer and self._statusTimer.IsRunning():
            topLevel = wx.GetTopLevelParent(self)
            statusBar = topLevel.GetStatusBar()
            self._statusTimer.Stop()
            statusBar.PopStatusText(0)
            self._statusTimer = None

    def RepaintOldSelection(self):
        current = self._currentButton
        if current == -1:
            return
        btn = self._vButtons[current]
        if not btn.IsEnabled():
            return
        btn.SetStatus('Normal')

    def OnStatusBarTimer(self):
        topLevel = wx.GetTopLevelParent(self)
        statusBar = topLevel.GetStatusBar()
        statusBar.PopStatusText(0)

    def SetUseHelp(self, useHelp = True):
        self._useHelp = useHelp

    def GetUseHelp(self):
        return self._useHelp

    def HitTest(self, pt):
        for ii in xrange(len(self._vButtons)):
            if not self._vButtons[ii].IsEnabled():
                continue
            if self._vButtons[ii].GetRect().Contains(pt):
                return (ii, BP_HT_BUTTON)

        return (-1, BP_HT_NONE)

    def GetBPArt(self):
        return self._art

    def SetBPArt(self, art):
        self._art = art
        self.Refresh()

    if wx.VERSION < (2, 7, 1, 1):

        def Freeze(self):
            self._freezeCount = self._freezeCount + 1
            wx.PyPanel.Freeze(self)

        def Thaw(self):
            if self._freezeCount == 0:
                raise '\nERROR: Thawing Unfrozen ButtonPanel?'
            self._freezeCount = self._freezeCount - 1
            wx.PyPanel.Thaw(self)

        def IsFrozen(self):
            return self._freezeCount != 0
