#Embedded file name: wx/_gdi.py
import _gdi_
import new
new_instancemethod = new.instancemethod

def _swig_setattr_nondynamic(self, class_type, name, value, static = 1):
    if name == 'thisown':
        return self.this.own(value)
    if name == 'this':
        if type(value).__name__ == 'PySwigObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method:
        return method(self, value)
    if not static or hasattr(self, name):
        self.__dict__[name] = value
    else:
        raise AttributeError('You cannot add attributes to %s' % self)


def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)


def _swig_getattr(self, class_type, name):
    if name == 'thisown':
        return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method:
        return method(self)
    raise AttributeError, name


def _swig_repr(self):
    try:
        strthis = 'proxy of ' + self.this.__repr__()
    except:
        strthis = ''

    return '<%s.%s; %s >' % (self.__class__.__module__, self.__class__.__name__, strthis)


import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:

    class _object():
        pass


    _newclass = 0

del types

def _swig_setattr_nondynamic_method(set):

    def set_attr(self, name, value):
        if name == 'thisown':
            return self.this.own(value)
        if hasattr(self, name) or name == 'this':
            set(self, name, value)
        else:
            raise AttributeError('You cannot add attributes to %s' % self)

    return set_attr


import _core
wx = _core

class GDIObject(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.GDIObject_swiginit(self, _gdi_.new_GDIObject(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_GDIObject
    __del__ = lambda self: None

    def IsNull(*args, **kwargs):
        return _gdi_.GDIObject_IsNull(*args, **kwargs)


_gdi_.GDIObject_swigregister(GDIObject)
C2S_NAME = _gdi_.C2S_NAME
C2S_CSS_SYNTAX = _gdi_.C2S_CSS_SYNTAX
C2S_HTML_SYNTAX = _gdi_.C2S_HTML_SYNTAX
ALPHA_TRANSPARENT = _gdi_.ALPHA_TRANSPARENT
ALPHA_OPAQUE = _gdi_.ALPHA_OPAQUE

class Colour(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Colour_swiginit(self, _gdi_.new_Colour(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Colour
    __del__ = lambda self: None

    def Red(*args, **kwargs):
        return _gdi_.Colour_Red(*args, **kwargs)

    def Green(*args, **kwargs):
        return _gdi_.Colour_Green(*args, **kwargs)

    def Blue(*args, **kwargs):
        return _gdi_.Colour_Blue(*args, **kwargs)

    def Alpha(*args, **kwargs):
        return _gdi_.Colour_Alpha(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.Colour_IsOk(*args, **kwargs)

    Ok = IsOk

    def Set(*args, **kwargs):
        return _gdi_.Colour_Set(*args, **kwargs)

    def SetRGB(*args, **kwargs):
        return _gdi_.Colour_SetRGB(*args, **kwargs)

    def SetFromName(*args, **kwargs):
        return _gdi_.Colour_SetFromName(*args, **kwargs)

    def GetAsString(*args, **kwargs):
        return _gdi_.Colour_GetAsString(*args, **kwargs)

    def GetPixel(*args, **kwargs):
        return _gdi_.Colour_GetPixel(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _gdi_.Colour___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _gdi_.Colour___ne__(*args, **kwargs)

    def Get(*args, **kwargs):
        return _gdi_.Colour_Get(*args, **kwargs)

    def GetRGB(*args, **kwargs):
        return _gdi_.Colour_GetRGB(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get(True))

    def __repr__(self):
        if hasattr(self, 'this'):
            return 'wx.Colour' + str(self.Get(True))
        else:
            return 'wx.Colour()'

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __nonzero__(self):
        return self.IsOk()

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (Colour, self.Get(True))

    Pixel = property(GetPixel, doc='See `GetPixel`')
    RGB = property(GetRGB, SetRGB, doc='See `GetRGB` and `SetRGB`')


_gdi_.Colour_swigregister(Colour)

def NamedColour(*args, **kwargs):
    val = _gdi_.new_NamedColour(*args, **kwargs)
    return val


def ColourRGB(*args, **kwargs):
    val = _gdi_.new_ColourRGB(*args, **kwargs)
    return val


Color = Colour
NamedColor = NamedColour
ColorRGB = ColourRGB

class Palette(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Palette_swiginit(self, _gdi_.new_Palette(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Palette
    __del__ = lambda self: None

    def GetPixel(*args, **kwargs):
        return _gdi_.Palette_GetPixel(*args, **kwargs)

    def GetRGB(*args, **kwargs):
        return _gdi_.Palette_GetRGB(*args, **kwargs)

    def GetColoursCount(*args, **kwargs):
        return _gdi_.Palette_GetColoursCount(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.Palette_IsOk(*args, **kwargs)

    Ok = IsOk

    def __nonzero__(self):
        return self.IsOk()

    ColoursCount = property(GetColoursCount, doc='See `GetColoursCount`')


_gdi_.Palette_swigregister(Palette)

class Pen(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Pen_swiginit(self, _gdi_.new_Pen(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Pen
    __del__ = lambda self: None

    def GetCap(*args, **kwargs):
        return _gdi_.Pen_GetCap(*args, **kwargs)

    def GetColour(*args, **kwargs):
        return _gdi_.Pen_GetColour(*args, **kwargs)

    def GetJoin(*args, **kwargs):
        return _gdi_.Pen_GetJoin(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _gdi_.Pen_GetStyle(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _gdi_.Pen_GetWidth(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.Pen_IsOk(*args, **kwargs)

    Ok = IsOk

    def SetCap(*args, **kwargs):
        return _gdi_.Pen_SetCap(*args, **kwargs)

    def SetColour(*args, **kwargs):
        return _gdi_.Pen_SetColour(*args, **kwargs)

    def SetJoin(*args, **kwargs):
        return _gdi_.Pen_SetJoin(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _gdi_.Pen_SetStyle(*args, **kwargs)

    def SetWidth(*args, **kwargs):
        return _gdi_.Pen_SetWidth(*args, **kwargs)

    def SetDashes(*args, **kwargs):
        return _gdi_.Pen_SetDashes(*args, **kwargs)

    def GetDashes(*args, **kwargs):
        return _gdi_.Pen_GetDashes(*args, **kwargs)

    def _SetDashes(*args, **kwargs):
        return _gdi_.Pen__SetDashes(*args, **kwargs)

    def SetDashes(self, dashes):
        self._SetDashes(self, dashes)

    def GetDashCount(*args, **kwargs):
        return _gdi_.Pen_GetDashCount(*args, **kwargs)

    DashCount = property(GetDashCount, doc='See `GetDashCount`')

    def __eq__(*args, **kwargs):
        return _gdi_.Pen___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _gdi_.Pen___ne__(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    Cap = property(GetCap, SetCap, doc='See `GetCap` and `SetCap`')
    Colour = property(GetColour, SetColour, doc='See `GetColour` and `SetColour`')
    Dashes = property(GetDashes, SetDashes, doc='See `GetDashes` and `SetDashes`')
    Join = property(GetJoin, SetJoin, doc='See `GetJoin` and `SetJoin`')
    Style = property(GetStyle, SetStyle, doc='See `GetStyle` and `SetStyle`')
    Width = property(GetWidth, SetWidth, doc='See `GetWidth` and `SetWidth`')


_gdi_.Pen_swigregister(Pen)

class Brush(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Brush_swiginit(self, _gdi_.new_Brush(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Brush
    __del__ = lambda self: None

    def SetColour(*args, **kwargs):
        return _gdi_.Brush_SetColour(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _gdi_.Brush_SetStyle(*args, **kwargs)

    def SetStipple(*args, **kwargs):
        return _gdi_.Brush_SetStipple(*args, **kwargs)

    def GetColour(*args, **kwargs):
        return _gdi_.Brush_GetColour(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _gdi_.Brush_GetStyle(*args, **kwargs)

    def GetStipple(*args, **kwargs):
        return _gdi_.Brush_GetStipple(*args, **kwargs)

    def IsHatch(*args, **kwargs):
        return _gdi_.Brush_IsHatch(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.Brush_IsOk(*args, **kwargs)

    Ok = IsOk

    def __nonzero__(self):
        return self.IsOk()

    Colour = property(GetColour, SetColour, doc='See `GetColour` and `SetColour`')
    Stipple = property(GetStipple, SetStipple, doc='See `GetStipple` and `SetStipple`')
    Style = property(GetStyle, SetStyle, doc='See `GetStyle` and `SetStyle`')


_gdi_.Brush_swigregister(Brush)

def BrushFromBitmap(*args, **kwargs):
    val = _gdi_.new_BrushFromBitmap(*args, **kwargs)
    return val


BitmapBufferFormat_RGB = _gdi_.BitmapBufferFormat_RGB
BitmapBufferFormat_RGBA = _gdi_.BitmapBufferFormat_RGBA
BitmapBufferFormat_RGB32 = _gdi_.BitmapBufferFormat_RGB32
BitmapBufferFormat_ARGB32 = _gdi_.BitmapBufferFormat_ARGB32

class Bitmap(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Bitmap_swiginit(self, _gdi_.new_Bitmap(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Bitmap
    __del__ = lambda self: None

    def IsOk(*args, **kwargs):
        return _gdi_.Bitmap_IsOk(*args, **kwargs)

    Ok = IsOk

    def GetWidth(*args, **kwargs):
        return _gdi_.Bitmap_GetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _gdi_.Bitmap_GetHeight(*args, **kwargs)

    def GetDepth(*args, **kwargs):
        return _gdi_.Bitmap_GetDepth(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _gdi_.Bitmap_GetSize(*args, **kwargs)

    def ConvertToImage(*args, **kwargs):
        return _gdi_.Bitmap_ConvertToImage(*args, **kwargs)

    def GetMask(*args, **kwargs):
        return _gdi_.Bitmap_GetMask(*args, **kwargs)

    def SetMask(*args, **kwargs):
        return _gdi_.Bitmap_SetMask(*args, **kwargs)

    def SetMaskColour(*args, **kwargs):
        return _gdi_.Bitmap_SetMaskColour(*args, **kwargs)

    def GetSubBitmap(*args, **kwargs):
        return _gdi_.Bitmap_GetSubBitmap(*args, **kwargs)

    def SaveFile(*args, **kwargs):
        return _gdi_.Bitmap_SaveFile(*args, **kwargs)

    def LoadFile(*args, **kwargs):
        return _gdi_.Bitmap_LoadFile(*args, **kwargs)

    def GetPalette(*args, **kwargs):
        return _gdi_.Bitmap_GetPalette(*args, **kwargs)

    def CopyFromIcon(*args, **kwargs):
        return _gdi_.Bitmap_CopyFromIcon(*args, **kwargs)

    def SetHeight(*args, **kwargs):
        return _gdi_.Bitmap_SetHeight(*args, **kwargs)

    def SetWidth(*args, **kwargs):
        return _gdi_.Bitmap_SetWidth(*args, **kwargs)

    def SetDepth(*args, **kwargs):
        return _gdi_.Bitmap_SetDepth(*args, **kwargs)

    def SetSize(*args, **kwargs):
        return _gdi_.Bitmap_SetSize(*args, **kwargs)

    def CopyFromBuffer(*args, **kwargs):
        return _gdi_.Bitmap_CopyFromBuffer(*args, **kwargs)

    def CopyFromBufferRGBA(self, buffer):
        self.CopyFromBuffer(buffer, wx.BitmapBufferFormat_RGBA)

    def CopyToBuffer(*args, **kwargs):
        return _gdi_.Bitmap_CopyToBuffer(*args, **kwargs)

    def HasAlpha(*args, **kwargs):
        return _gdi_.Bitmap_HasAlpha(*args, **kwargs)

    def UseAlpha(*args, **kwargs):
        return _gdi_.Bitmap_UseAlpha(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def __eq__(*args, **kwargs):
        return _gdi_.Bitmap___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _gdi_.Bitmap___ne__(*args, **kwargs)

    Depth = property(GetDepth, SetDepth, doc='See `GetDepth` and `SetDepth`')
    Height = property(GetHeight, SetHeight, doc='See `GetHeight` and `SetHeight`')
    Mask = property(GetMask, SetMask, doc='See `GetMask` and `SetMask`')
    Palette = property(GetPalette, doc='See `GetPalette`')
    Size = property(GetSize, SetSize, doc='See `GetSize` and `SetSize`')
    SubBitmap = property(GetSubBitmap, doc='See `GetSubBitmap`')
    Width = property(GetWidth, SetWidth, doc='See `GetWidth` and `SetWidth`')


_gdi_.Bitmap_swigregister(Bitmap)

def EmptyBitmap(*args, **kwargs):
    val = _gdi_.new_EmptyBitmap(*args, **kwargs)
    return val


def BitmapFromIcon(*args, **kwargs):
    val = _gdi_.new_BitmapFromIcon(*args, **kwargs)
    return val


def BitmapFromImage(*args, **kwargs):
    val = _gdi_.new_BitmapFromImage(*args, **kwargs)
    return val


def BitmapFromXPMData(*args, **kwargs):
    val = _gdi_.new_BitmapFromXPMData(*args, **kwargs)
    return val


def BitmapFromBits(*args, **kwargs):
    val = _gdi_.new_BitmapFromBits(*args, **kwargs)
    return val


def _BitmapFromBufferAlpha(*args, **kwargs):
    return _gdi_._BitmapFromBufferAlpha(*args, **kwargs)


def _BitmapFromBuffer(*args, **kwargs):
    return _gdi_._BitmapFromBuffer(*args, **kwargs)


def BitmapFromBuffer(width, height, dataBuffer, alphaBuffer = None):
    if alphaBuffer is not None:
        return _gdi_._BitmapFromBufferAlpha(width, height, dataBuffer, alphaBuffer)
    else:
        return _gdi_._BitmapFromBuffer(width, height, dataBuffer)


def _BitmapFromBufferRGBA(*args, **kwargs):
    return _gdi_._BitmapFromBufferRGBA(*args, **kwargs)


def BitmapFromBufferRGBA(width, height, dataBuffer):
    return _gdi_._BitmapFromBufferRGBA(width, height, dataBuffer)


def _EmptyBitmapRGBA(*args, **kwargs):
    return _gdi_._EmptyBitmapRGBA(*args, **kwargs)


def EmptyBitmapRGBA(width, height, red = 0, green = 0, blue = 0, alpha = 0):
    return _gdi_._EmptyBitmapRGBA(width, height, red, green, blue, alpha)


class PixelDataBase(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetOrigin(*args, **kwargs):
        return _gdi_.PixelDataBase_GetOrigin(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _gdi_.PixelDataBase_GetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _gdi_.PixelDataBase_GetHeight(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _gdi_.PixelDataBase_GetSize(*args, **kwargs)

    def GetRowStride(*args, **kwargs):
        return _gdi_.PixelDataBase_GetRowStride(*args, **kwargs)

    Height = property(GetHeight, doc='See `GetHeight`')
    Origin = property(GetOrigin, doc='See `GetOrigin`')
    RowStride = property(GetRowStride, doc='See `GetRowStride`')
    Size = property(GetSize, doc='See `GetSize`')
    Width = property(GetWidth, doc='See `GetWidth`')


_gdi_.PixelDataBase_swigregister(PixelDataBase)

class NativePixelData(PixelDataBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.NativePixelData_swiginit(self, _gdi_.new_NativePixelData(*args))

    __swig_destroy__ = _gdi_.delete_NativePixelData
    __del__ = lambda self: None

    def GetPixels(*args, **kwargs):
        return _gdi_.NativePixelData_GetPixels(*args, **kwargs)

    def UseAlpha(*args, **kwargs):
        return _gdi_.NativePixelData_UseAlpha(*args, **kwargs)

    def __nonzero__(*args, **kwargs):
        return _gdi_.NativePixelData___nonzero__(*args, **kwargs)

    def __iter__(self):
        width = self.GetWidth()
        height = self.GetHeight()
        pixels = self.GetPixels()

        class PixelFacade(object):

            def Get(self):
                return pixels.Get()

            def Set(self, *args, **kw):
                return pixels.Set(*args, **kw)

            def __str__(self):
                return str(self.Get())

            def __repr__(self):
                return 'pixel(%d,%d): %s' % (x, y, self.Get())

            X = property(lambda self: x)
            Y = property(lambda self: y)

        pf = PixelFacade()
        for y in xrange(height):
            pixels.MoveTo(self, 0, y)
            for x in xrange(width):
                yield pf
                pixels.nextPixel()

    Pixels = property(GetPixels, doc='See `GetPixels`')


_gdi_.NativePixelData_swigregister(NativePixelData)

class NativePixelData_Accessor(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.NativePixelData_Accessor_swiginit(self, _gdi_.new_NativePixelData_Accessor(*args))

    __swig_destroy__ = _gdi_.delete_NativePixelData_Accessor
    __del__ = lambda self: None

    def Reset(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_Reset(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_IsOk(*args, **kwargs)

    def nextPixel(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_nextPixel(*args, **kwargs)

    def Offset(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_Offset(*args, **kwargs)

    def OffsetX(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_OffsetX(*args, **kwargs)

    def OffsetY(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_OffsetY(*args, **kwargs)

    def MoveTo(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_MoveTo(*args, **kwargs)

    def Set(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _gdi_.NativePixelData_Accessor_Get(*args, **kwargs)


_gdi_.NativePixelData_Accessor_swigregister(NativePixelData_Accessor)

class AlphaPixelData(PixelDataBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.AlphaPixelData_swiginit(self, _gdi_.new_AlphaPixelData(*args))
        self.UseAlpha()

    __swig_destroy__ = _gdi_.delete_AlphaPixelData
    __del__ = lambda self: None

    def GetPixels(*args, **kwargs):
        return _gdi_.AlphaPixelData_GetPixels(*args, **kwargs)

    def UseAlpha(*args, **kwargs):
        return _gdi_.AlphaPixelData_UseAlpha(*args, **kwargs)

    def __nonzero__(*args, **kwargs):
        return _gdi_.AlphaPixelData___nonzero__(*args, **kwargs)

    def __iter__(self):
        width = self.GetWidth()
        height = self.GetHeight()
        pixels = self.GetPixels()

        class PixelFacade(object):

            def Get(self):
                return pixels.Get()

            def Set(self, *args, **kw):
                return pixels.Set(*args, **kw)

            def __str__(self):
                return str(self.Get())

            def __repr__(self):
                return 'pixel(%d,%d): %s' % (x, y, self.Get())

            X = property(lambda self: x)
            Y = property(lambda self: y)

        pf = PixelFacade()
        for y in xrange(height):
            pixels.MoveTo(self, 0, y)
            for x in xrange(width):
                yield pf
                pixels.nextPixel()

    Pixels = property(GetPixels, doc='See `GetPixels`')


_gdi_.AlphaPixelData_swigregister(AlphaPixelData)

class AlphaPixelData_Accessor(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.AlphaPixelData_Accessor_swiginit(self, _gdi_.new_AlphaPixelData_Accessor(*args))

    __swig_destroy__ = _gdi_.delete_AlphaPixelData_Accessor
    __del__ = lambda self: None

    def Reset(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_Reset(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_IsOk(*args, **kwargs)

    def nextPixel(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_nextPixel(*args, **kwargs)

    def Offset(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_Offset(*args, **kwargs)

    def OffsetX(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_OffsetX(*args, **kwargs)

    def OffsetY(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_OffsetY(*args, **kwargs)

    def MoveTo(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_MoveTo(*args, **kwargs)

    def Set(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _gdi_.AlphaPixelData_Accessor_Get(*args, **kwargs)


_gdi_.AlphaPixelData_Accessor_swigregister(AlphaPixelData_Accessor)

class Mask(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Mask_swiginit(self, _gdi_.new_Mask(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Mask
    __del__ = lambda self: None


_gdi_.Mask_swigregister(Mask)
MaskColour = wx._deprecated(Mask, 'wx.MaskColour is deprecated, use `wx.Mask` instead.')

class Icon(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Icon_swiginit(self, _gdi_.new_Icon(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Icon
    __del__ = lambda self: None

    def LoadFile(*args, **kwargs):
        return _gdi_.Icon_LoadFile(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.Icon_IsOk(*args, **kwargs)

    Ok = IsOk

    def GetWidth(*args, **kwargs):
        return _gdi_.Icon_GetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _gdi_.Icon_GetHeight(*args, **kwargs)

    def GetDepth(*args, **kwargs):
        return _gdi_.Icon_GetDepth(*args, **kwargs)

    def SetWidth(*args, **kwargs):
        return _gdi_.Icon_SetWidth(*args, **kwargs)

    def SetHeight(*args, **kwargs):
        return _gdi_.Icon_SetHeight(*args, **kwargs)

    def SetDepth(*args, **kwargs):
        return _gdi_.Icon_SetDepth(*args, **kwargs)

    def CopyFromBitmap(*args, **kwargs):
        return _gdi_.Icon_CopyFromBitmap(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    Depth = property(GetDepth, SetDepth, doc='See `GetDepth` and `SetDepth`')
    Height = property(GetHeight, SetHeight, doc='See `GetHeight` and `SetHeight`')
    Width = property(GetWidth, SetWidth, doc='See `GetWidth` and `SetWidth`')


_gdi_.Icon_swigregister(Icon)

def EmptyIcon(*args, **kwargs):
    val = _gdi_.new_EmptyIcon(*args, **kwargs)
    return val


def IconFromLocation(*args, **kwargs):
    val = _gdi_.new_IconFromLocation(*args, **kwargs)
    return val


def IconFromBitmap(*args, **kwargs):
    val = _gdi_.new_IconFromBitmap(*args, **kwargs)
    return val


def IconFromXPMData(*args, **kwargs):
    val = _gdi_.new_IconFromXPMData(*args, **kwargs)
    return val


class IconLocation(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.IconLocation_swiginit(self, _gdi_.new_IconLocation(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_IconLocation
    __del__ = lambda self: None

    def IsOk(*args, **kwargs):
        return _gdi_.IconLocation_IsOk(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def SetFileName(*args, **kwargs):
        return _gdi_.IconLocation_SetFileName(*args, **kwargs)

    def GetFileName(*args, **kwargs):
        return _gdi_.IconLocation_GetFileName(*args, **kwargs)

    def SetIndex(*args, **kwargs):
        return _gdi_.IconLocation_SetIndex(*args, **kwargs)

    def GetIndex(*args, **kwargs):
        return _gdi_.IconLocation_GetIndex(*args, **kwargs)

    FileName = property(GetFileName, SetFileName, doc='See `GetFileName` and `SetFileName`')
    Index = property(GetIndex, SetIndex, doc='See `GetIndex` and `SetIndex`')


_gdi_.IconLocation_swigregister(IconLocation)

class IconBundle(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.IconBundle_swiginit(self, _gdi_.new_IconBundle(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_IconBundle
    __del__ = lambda self: None

    def AddIcon(*args, **kwargs):
        return _gdi_.IconBundle_AddIcon(*args, **kwargs)

    def AddIconFromFile(*args, **kwargs):
        return _gdi_.IconBundle_AddIconFromFile(*args, **kwargs)

    def GetIcon(*args, **kwargs):
        return _gdi_.IconBundle_GetIcon(*args, **kwargs)

    Icon = property(GetIcon, doc='See `GetIcon`')


_gdi_.IconBundle_swigregister(IconBundle)

def IconBundleFromFile(*args, **kwargs):
    val = _gdi_.new_IconBundleFromFile(*args, **kwargs)
    return val


def IconBundleFromIcon(*args, **kwargs):
    val = _gdi_.new_IconBundleFromIcon(*args, **kwargs)
    return val


class Cursor(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Cursor_swiginit(self, _gdi_.new_Cursor(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Cursor
    __del__ = lambda self: None

    def IsOk(*args, **kwargs):
        return _gdi_.Cursor_IsOk(*args, **kwargs)

    Ok = IsOk

    def __nonzero__(self):
        return self.IsOk()


_gdi_.Cursor_swigregister(Cursor)

def StockCursor(*args, **kwargs):
    val = _gdi_.new_StockCursor(*args, **kwargs)
    return val


def CursorFromImage(*args, **kwargs):
    val = _gdi_.new_CursorFromImage(*args, **kwargs)
    return val


OutRegion = _gdi_.OutRegion
PartRegion = _gdi_.PartRegion
InRegion = _gdi_.InRegion

class Region(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Region_swiginit(self, _gdi_.new_Region(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Region
    __del__ = lambda self: None

    def Clear(*args, **kwargs):
        return _gdi_.Region_Clear(*args, **kwargs)

    def Offset(*args, **kwargs):
        return _gdi_.Region_Offset(*args, **kwargs)

    def Contains(*args, **kwargs):
        return _gdi_.Region_Contains(*args, **kwargs)

    def ContainsPoint(*args, **kwargs):
        return _gdi_.Region_ContainsPoint(*args, **kwargs)

    def ContainsRect(*args, **kwargs):
        return _gdi_.Region_ContainsRect(*args, **kwargs)

    def ContainsRectDim(*args, **kwargs):
        return _gdi_.Region_ContainsRectDim(*args, **kwargs)

    def GetBox(*args, **kwargs):
        return _gdi_.Region_GetBox(*args, **kwargs)

    def Intersect(*args, **kwargs):
        return _gdi_.Region_Intersect(*args, **kwargs)

    def IntersectRect(*args, **kwargs):
        return _gdi_.Region_IntersectRect(*args, **kwargs)

    def IntersectRegion(*args, **kwargs):
        return _gdi_.Region_IntersectRegion(*args, **kwargs)

    def IsEmpty(*args, **kwargs):
        return _gdi_.Region_IsEmpty(*args, **kwargs)

    def IsEqual(*args, **kwargs):
        return _gdi_.Region_IsEqual(*args, **kwargs)

    def Union(*args, **kwargs):
        return _gdi_.Region_Union(*args, **kwargs)

    def UnionRect(*args, **kwargs):
        return _gdi_.Region_UnionRect(*args, **kwargs)

    def UnionRegion(*args, **kwargs):
        return _gdi_.Region_UnionRegion(*args, **kwargs)

    def Subtract(*args, **kwargs):
        return _gdi_.Region_Subtract(*args, **kwargs)

    def SubtractRect(*args, **kwargs):
        return _gdi_.Region_SubtractRect(*args, **kwargs)

    def SubtractRegion(*args, **kwargs):
        return _gdi_.Region_SubtractRegion(*args, **kwargs)

    def Xor(*args, **kwargs):
        return _gdi_.Region_Xor(*args, **kwargs)

    def XorRect(*args, **kwargs):
        return _gdi_.Region_XorRect(*args, **kwargs)

    def XorRegion(*args, **kwargs):
        return _gdi_.Region_XorRegion(*args, **kwargs)

    def ConvertToBitmap(*args, **kwargs):
        return _gdi_.Region_ConvertToBitmap(*args, **kwargs)

    def UnionBitmap(*args, **kwargs):
        return _gdi_.Region_UnionBitmap(*args, **kwargs)

    def UnionBitmapColour(*args, **kwargs):
        return _gdi_.Region_UnionBitmapColour(*args, **kwargs)

    Box = property(GetBox, doc='See `GetBox`')


_gdi_.Region_swigregister(Region)

def RegionFromBitmap(*args, **kwargs):
    val = _gdi_.new_RegionFromBitmap(*args, **kwargs)
    return val


def RegionFromBitmapColour(*args, **kwargs):
    val = _gdi_.new_RegionFromBitmapColour(*args, **kwargs)
    return val


def RegionFromPoints(*args, **kwargs):
    val = _gdi_.new_RegionFromPoints(*args, **kwargs)
    return val


class RegionIterator(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.RegionIterator_swiginit(self, _gdi_.new_RegionIterator(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_RegionIterator
    __del__ = lambda self: None

    def GetX(*args, **kwargs):
        return _gdi_.RegionIterator_GetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _gdi_.RegionIterator_GetY(*args, **kwargs)

    def GetW(*args, **kwargs):
        return _gdi_.RegionIterator_GetW(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _gdi_.RegionIterator_GetWidth(*args, **kwargs)

    def GetH(*args, **kwargs):
        return _gdi_.RegionIterator_GetH(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _gdi_.RegionIterator_GetHeight(*args, **kwargs)

    def GetRect(*args, **kwargs):
        return _gdi_.RegionIterator_GetRect(*args, **kwargs)

    def HaveRects(*args, **kwargs):
        return _gdi_.RegionIterator_HaveRects(*args, **kwargs)

    def Reset(*args, **kwargs):
        return _gdi_.RegionIterator_Reset(*args, **kwargs)

    def Next(*args, **kwargs):
        return _gdi_.RegionIterator_Next(*args, **kwargs)

    def __nonzero__(*args, **kwargs):
        return _gdi_.RegionIterator___nonzero__(*args, **kwargs)

    H = property(GetH, doc='See `GetH`')
    Height = property(GetHeight, doc='See `GetHeight`')
    Rect = property(GetRect, doc='See `GetRect`')
    W = property(GetW, doc='See `GetW`')
    Width = property(GetWidth, doc='See `GetWidth`')
    X = property(GetX, doc='See `GetX`')
    Y = property(GetY, doc='See `GetY`')


_gdi_.RegionIterator_swigregister(RegionIterator)
FONTFAMILY_DEFAULT = _gdi_.FONTFAMILY_DEFAULT
FONTFAMILY_DECORATIVE = _gdi_.FONTFAMILY_DECORATIVE
FONTFAMILY_ROMAN = _gdi_.FONTFAMILY_ROMAN
FONTFAMILY_SCRIPT = _gdi_.FONTFAMILY_SCRIPT
FONTFAMILY_SWISS = _gdi_.FONTFAMILY_SWISS
FONTFAMILY_MODERN = _gdi_.FONTFAMILY_MODERN
FONTFAMILY_TELETYPE = _gdi_.FONTFAMILY_TELETYPE
FONTFAMILY_MAX = _gdi_.FONTFAMILY_MAX
FONTFAMILY_UNKNOWN = _gdi_.FONTFAMILY_UNKNOWN
FONTSTYLE_NORMAL = _gdi_.FONTSTYLE_NORMAL
FONTSTYLE_ITALIC = _gdi_.FONTSTYLE_ITALIC
FONTSTYLE_SLANT = _gdi_.FONTSTYLE_SLANT
FONTSTYLE_MAX = _gdi_.FONTSTYLE_MAX
FONTWEIGHT_NORMAL = _gdi_.FONTWEIGHT_NORMAL
FONTWEIGHT_LIGHT = _gdi_.FONTWEIGHT_LIGHT
FONTWEIGHT_BOLD = _gdi_.FONTWEIGHT_BOLD
FONTWEIGHT_MAX = _gdi_.FONTWEIGHT_MAX
FONTFLAG_DEFAULT = _gdi_.FONTFLAG_DEFAULT
FONTFLAG_ITALIC = _gdi_.FONTFLAG_ITALIC
FONTFLAG_SLANT = _gdi_.FONTFLAG_SLANT
FONTFLAG_LIGHT = _gdi_.FONTFLAG_LIGHT
FONTFLAG_BOLD = _gdi_.FONTFLAG_BOLD
FONTFLAG_ANTIALIASED = _gdi_.FONTFLAG_ANTIALIASED
FONTFLAG_NOT_ANTIALIASED = _gdi_.FONTFLAG_NOT_ANTIALIASED
FONTFLAG_UNDERLINED = _gdi_.FONTFLAG_UNDERLINED
FONTFLAG_STRIKETHROUGH = _gdi_.FONTFLAG_STRIKETHROUGH
FONTFLAG_MASK = _gdi_.FONTFLAG_MASK
FONTENCODING_SYSTEM = _gdi_.FONTENCODING_SYSTEM
FONTENCODING_DEFAULT = _gdi_.FONTENCODING_DEFAULT
FONTENCODING_ISO8859_1 = _gdi_.FONTENCODING_ISO8859_1
FONTENCODING_ISO8859_2 = _gdi_.FONTENCODING_ISO8859_2
FONTENCODING_ISO8859_3 = _gdi_.FONTENCODING_ISO8859_3
FONTENCODING_ISO8859_4 = _gdi_.FONTENCODING_ISO8859_4
FONTENCODING_ISO8859_5 = _gdi_.FONTENCODING_ISO8859_5
FONTENCODING_ISO8859_6 = _gdi_.FONTENCODING_ISO8859_6
FONTENCODING_ISO8859_7 = _gdi_.FONTENCODING_ISO8859_7
FONTENCODING_ISO8859_8 = _gdi_.FONTENCODING_ISO8859_8
FONTENCODING_ISO8859_9 = _gdi_.FONTENCODING_ISO8859_9
FONTENCODING_ISO8859_10 = _gdi_.FONTENCODING_ISO8859_10
FONTENCODING_ISO8859_11 = _gdi_.FONTENCODING_ISO8859_11
FONTENCODING_ISO8859_12 = _gdi_.FONTENCODING_ISO8859_12
FONTENCODING_ISO8859_13 = _gdi_.FONTENCODING_ISO8859_13
FONTENCODING_ISO8859_14 = _gdi_.FONTENCODING_ISO8859_14
FONTENCODING_ISO8859_15 = _gdi_.FONTENCODING_ISO8859_15
FONTENCODING_ISO8859_MAX = _gdi_.FONTENCODING_ISO8859_MAX
FONTENCODING_KOI8 = _gdi_.FONTENCODING_KOI8
FONTENCODING_KOI8_U = _gdi_.FONTENCODING_KOI8_U
FONTENCODING_ALTERNATIVE = _gdi_.FONTENCODING_ALTERNATIVE
FONTENCODING_BULGARIAN = _gdi_.FONTENCODING_BULGARIAN
FONTENCODING_CP437 = _gdi_.FONTENCODING_CP437
FONTENCODING_CP850 = _gdi_.FONTENCODING_CP850
FONTENCODING_CP852 = _gdi_.FONTENCODING_CP852
FONTENCODING_CP855 = _gdi_.FONTENCODING_CP855
FONTENCODING_CP866 = _gdi_.FONTENCODING_CP866
FONTENCODING_CP874 = _gdi_.FONTENCODING_CP874
FONTENCODING_CP932 = _gdi_.FONTENCODING_CP932
FONTENCODING_CP936 = _gdi_.FONTENCODING_CP936
FONTENCODING_CP949 = _gdi_.FONTENCODING_CP949
FONTENCODING_CP950 = _gdi_.FONTENCODING_CP950
FONTENCODING_CP1250 = _gdi_.FONTENCODING_CP1250
FONTENCODING_CP1251 = _gdi_.FONTENCODING_CP1251
FONTENCODING_CP1252 = _gdi_.FONTENCODING_CP1252
FONTENCODING_CP1253 = _gdi_.FONTENCODING_CP1253
FONTENCODING_CP1254 = _gdi_.FONTENCODING_CP1254
FONTENCODING_CP1255 = _gdi_.FONTENCODING_CP1255
FONTENCODING_CP1256 = _gdi_.FONTENCODING_CP1256
FONTENCODING_CP1257 = _gdi_.FONTENCODING_CP1257
FONTENCODING_CP12_MAX = _gdi_.FONTENCODING_CP12_MAX
FONTENCODING_UTF7 = _gdi_.FONTENCODING_UTF7
FONTENCODING_UTF8 = _gdi_.FONTENCODING_UTF8
FONTENCODING_EUC_JP = _gdi_.FONTENCODING_EUC_JP
FONTENCODING_UTF16BE = _gdi_.FONTENCODING_UTF16BE
FONTENCODING_UTF16LE = _gdi_.FONTENCODING_UTF16LE
FONTENCODING_UTF32BE = _gdi_.FONTENCODING_UTF32BE
FONTENCODING_UTF32LE = _gdi_.FONTENCODING_UTF32LE
FONTENCODING_MACROMAN = _gdi_.FONTENCODING_MACROMAN
FONTENCODING_MACJAPANESE = _gdi_.FONTENCODING_MACJAPANESE
FONTENCODING_MACCHINESETRAD = _gdi_.FONTENCODING_MACCHINESETRAD
FONTENCODING_MACKOREAN = _gdi_.FONTENCODING_MACKOREAN
FONTENCODING_MACARABIC = _gdi_.FONTENCODING_MACARABIC
FONTENCODING_MACHEBREW = _gdi_.FONTENCODING_MACHEBREW
FONTENCODING_MACGREEK = _gdi_.FONTENCODING_MACGREEK
FONTENCODING_MACCYRILLIC = _gdi_.FONTENCODING_MACCYRILLIC
FONTENCODING_MACDEVANAGARI = _gdi_.FONTENCODING_MACDEVANAGARI
FONTENCODING_MACGURMUKHI = _gdi_.FONTENCODING_MACGURMUKHI
FONTENCODING_MACGUJARATI = _gdi_.FONTENCODING_MACGUJARATI
FONTENCODING_MACORIYA = _gdi_.FONTENCODING_MACORIYA
FONTENCODING_MACBENGALI = _gdi_.FONTENCODING_MACBENGALI
FONTENCODING_MACTAMIL = _gdi_.FONTENCODING_MACTAMIL
FONTENCODING_MACTELUGU = _gdi_.FONTENCODING_MACTELUGU
FONTENCODING_MACKANNADA = _gdi_.FONTENCODING_MACKANNADA
FONTENCODING_MACMALAJALAM = _gdi_.FONTENCODING_MACMALAJALAM
FONTENCODING_MACSINHALESE = _gdi_.FONTENCODING_MACSINHALESE
FONTENCODING_MACBURMESE = _gdi_.FONTENCODING_MACBURMESE
FONTENCODING_MACKHMER = _gdi_.FONTENCODING_MACKHMER
FONTENCODING_MACTHAI = _gdi_.FONTENCODING_MACTHAI
FONTENCODING_MACLAOTIAN = _gdi_.FONTENCODING_MACLAOTIAN
FONTENCODING_MACGEORGIAN = _gdi_.FONTENCODING_MACGEORGIAN
FONTENCODING_MACARMENIAN = _gdi_.FONTENCODING_MACARMENIAN
FONTENCODING_MACCHINESESIMP = _gdi_.FONTENCODING_MACCHINESESIMP
FONTENCODING_MACTIBETAN = _gdi_.FONTENCODING_MACTIBETAN
FONTENCODING_MACMONGOLIAN = _gdi_.FONTENCODING_MACMONGOLIAN
FONTENCODING_MACETHIOPIC = _gdi_.FONTENCODING_MACETHIOPIC
FONTENCODING_MACCENTRALEUR = _gdi_.FONTENCODING_MACCENTRALEUR
FONTENCODING_MACVIATNAMESE = _gdi_.FONTENCODING_MACVIATNAMESE
FONTENCODING_MACARABICEXT = _gdi_.FONTENCODING_MACARABICEXT
FONTENCODING_MACSYMBOL = _gdi_.FONTENCODING_MACSYMBOL
FONTENCODING_MACDINGBATS = _gdi_.FONTENCODING_MACDINGBATS
FONTENCODING_MACTURKISH = _gdi_.FONTENCODING_MACTURKISH
FONTENCODING_MACCROATIAN = _gdi_.FONTENCODING_MACCROATIAN
FONTENCODING_MACICELANDIC = _gdi_.FONTENCODING_MACICELANDIC
FONTENCODING_MACROMANIAN = _gdi_.FONTENCODING_MACROMANIAN
FONTENCODING_MACCELTIC = _gdi_.FONTENCODING_MACCELTIC
FONTENCODING_MACGAELIC = _gdi_.FONTENCODING_MACGAELIC
FONTENCODING_MACKEYBOARD = _gdi_.FONTENCODING_MACKEYBOARD
FONTENCODING_MACMIN = _gdi_.FONTENCODING_MACMIN
FONTENCODING_MACMAX = _gdi_.FONTENCODING_MACMAX
FONTENCODING_MAX = _gdi_.FONTENCODING_MAX
FONTENCODING_UTF16 = _gdi_.FONTENCODING_UTF16
FONTENCODING_UTF32 = _gdi_.FONTENCODING_UTF32
FONTENCODING_UNICODE = _gdi_.FONTENCODING_UNICODE
FONTENCODING_GB2312 = _gdi_.FONTENCODING_GB2312
FONTENCODING_BIG5 = _gdi_.FONTENCODING_BIG5
FONTENCODING_SHIFT_JIS = _gdi_.FONTENCODING_SHIFT_JIS

class NativeFontInfo(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.NativeFontInfo_swiginit(self, _gdi_.new_NativeFontInfo(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_NativeFontInfo
    __del__ = lambda self: None

    def Init(*args, **kwargs):
        return _gdi_.NativeFontInfo_Init(*args, **kwargs)

    def InitFromFont(*args, **kwargs):
        return _gdi_.NativeFontInfo_InitFromFont(*args, **kwargs)

    def GetPointSize(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetPointSize(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetStyle(*args, **kwargs)

    def GetWeight(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetWeight(*args, **kwargs)

    def GetUnderlined(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetUnderlined(*args, **kwargs)

    def GetFaceName(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetFaceName(*args, **kwargs)

    def GetFamily(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetFamily(*args, **kwargs)

    def GetEncoding(*args, **kwargs):
        return _gdi_.NativeFontInfo_GetEncoding(*args, **kwargs)

    def SetPointSize(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetPointSize(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetStyle(*args, **kwargs)

    def SetWeight(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetWeight(*args, **kwargs)

    def SetUnderlined(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetUnderlined(*args, **kwargs)

    def SetFaceName(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetFaceName(*args, **kwargs)

    def SetFamily(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetFamily(*args, **kwargs)

    def SetEncoding(*args, **kwargs):
        return _gdi_.NativeFontInfo_SetEncoding(*args, **kwargs)

    def FromString(*args, **kwargs):
        return _gdi_.NativeFontInfo_FromString(*args, **kwargs)

    def ToString(*args, **kwargs):
        return _gdi_.NativeFontInfo_ToString(*args, **kwargs)

    def __str__(*args, **kwargs):
        return _gdi_.NativeFontInfo___str__(*args, **kwargs)

    def FromUserString(*args, **kwargs):
        return _gdi_.NativeFontInfo_FromUserString(*args, **kwargs)

    def ToUserString(*args, **kwargs):
        return _gdi_.NativeFontInfo_ToUserString(*args, **kwargs)

    Encoding = property(GetEncoding, SetEncoding, doc='See `GetEncoding` and `SetEncoding`')
    FaceName = property(GetFaceName, SetFaceName, doc='See `GetFaceName` and `SetFaceName`')
    Family = property(GetFamily, SetFamily, doc='See `GetFamily` and `SetFamily`')
    PointSize = property(GetPointSize, SetPointSize, doc='See `GetPointSize` and `SetPointSize`')
    Style = property(GetStyle, SetStyle, doc='See `GetStyle` and `SetStyle`')
    Underlined = property(GetUnderlined, SetUnderlined, doc='See `GetUnderlined` and `SetUnderlined`')
    Weight = property(GetWeight, SetWeight, doc='See `GetWeight` and `SetWeight`')


_gdi_.NativeFontInfo_swigregister(NativeFontInfo)

class NativeEncodingInfo(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    facename = property(_gdi_.NativeEncodingInfo_facename_get, _gdi_.NativeEncodingInfo_facename_set)
    encoding = property(_gdi_.NativeEncodingInfo_encoding_get, _gdi_.NativeEncodingInfo_encoding_set)

    def __init__(self, *args, **kwargs):
        _gdi_.NativeEncodingInfo_swiginit(self, _gdi_.new_NativeEncodingInfo(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_NativeEncodingInfo
    __del__ = lambda self: None

    def FromString(*args, **kwargs):
        return _gdi_.NativeEncodingInfo_FromString(*args, **kwargs)

    def ToString(*args, **kwargs):
        return _gdi_.NativeEncodingInfo_ToString(*args, **kwargs)


_gdi_.NativeEncodingInfo_swigregister(NativeEncodingInfo)

def GetNativeFontEncoding(*args, **kwargs):
    return _gdi_.GetNativeFontEncoding(*args, **kwargs)


def TestFontEncoding(*args, **kwargs):
    return _gdi_.TestFontEncoding(*args, **kwargs)


class FontMapper(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.FontMapper_swiginit(self, _gdi_.new_FontMapper(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_FontMapper
    __del__ = lambda self: None

    def Get(*args, **kwargs):
        return _gdi_.FontMapper_Get(*args, **kwargs)

    Get = staticmethod(Get)

    def Set(*args, **kwargs):
        return _gdi_.FontMapper_Set(*args, **kwargs)

    Set = staticmethod(Set)

    def CharsetToEncoding(*args, **kwargs):
        return _gdi_.FontMapper_CharsetToEncoding(*args, **kwargs)

    def GetSupportedEncodingsCount(*args, **kwargs):
        return _gdi_.FontMapper_GetSupportedEncodingsCount(*args, **kwargs)

    GetSupportedEncodingsCount = staticmethod(GetSupportedEncodingsCount)

    def GetEncoding(*args, **kwargs):
        return _gdi_.FontMapper_GetEncoding(*args, **kwargs)

    GetEncoding = staticmethod(GetEncoding)

    def GetEncodingName(*args, **kwargs):
        return _gdi_.FontMapper_GetEncodingName(*args, **kwargs)

    GetEncodingName = staticmethod(GetEncodingName)

    def GetEncodingDescription(*args, **kwargs):
        return _gdi_.FontMapper_GetEncodingDescription(*args, **kwargs)

    GetEncodingDescription = staticmethod(GetEncodingDescription)

    def GetEncodingFromName(*args, **kwargs):
        return _gdi_.FontMapper_GetEncodingFromName(*args, **kwargs)

    GetEncodingFromName = staticmethod(GetEncodingFromName)

    def SetConfigPath(*args, **kwargs):
        return _gdi_.FontMapper_SetConfigPath(*args, **kwargs)

    def GetDefaultConfigPath(*args, **kwargs):
        return _gdi_.FontMapper_GetDefaultConfigPath(*args, **kwargs)

    GetDefaultConfigPath = staticmethod(GetDefaultConfigPath)

    def GetAltForEncoding(*args, **kwargs):
        return _gdi_.FontMapper_GetAltForEncoding(*args, **kwargs)

    def IsEncodingAvailable(*args, **kwargs):
        return _gdi_.FontMapper_IsEncodingAvailable(*args, **kwargs)

    def SetDialogParent(*args, **kwargs):
        return _gdi_.FontMapper_SetDialogParent(*args, **kwargs)

    def SetDialogTitle(*args, **kwargs):
        return _gdi_.FontMapper_SetDialogTitle(*args, **kwargs)

    AltForEncoding = property(GetAltForEncoding, doc='See `GetAltForEncoding`')


_gdi_.FontMapper_swigregister(FontMapper)

def FontMapper_Get(*args):
    return _gdi_.FontMapper_Get(*args)


def FontMapper_Set(*args, **kwargs):
    return _gdi_.FontMapper_Set(*args, **kwargs)


def FontMapper_GetSupportedEncodingsCount(*args):
    return _gdi_.FontMapper_GetSupportedEncodingsCount(*args)


def FontMapper_GetEncoding(*args, **kwargs):
    return _gdi_.FontMapper_GetEncoding(*args, **kwargs)


def FontMapper_GetEncodingName(*args, **kwargs):
    return _gdi_.FontMapper_GetEncodingName(*args, **kwargs)


def FontMapper_GetEncodingDescription(*args, **kwargs):
    return _gdi_.FontMapper_GetEncodingDescription(*args, **kwargs)


def FontMapper_GetEncodingFromName(*args, **kwargs):
    return _gdi_.FontMapper_GetEncodingFromName(*args, **kwargs)


def FontMapper_GetDefaultConfigPath(*args):
    return _gdi_.FontMapper_GetDefaultConfigPath(*args)


class Font(GDIObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('faceName'):
            kwargs['face'] = kwargs['faceName']
            del kwargs['faceName']
        _gdi_.Font_swiginit(self, _gdi_.new_Font(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Font
    __del__ = lambda self: None

    def IsOk(*args, **kwargs):
        return _gdi_.Font_IsOk(*args, **kwargs)

    Ok = IsOk

    def __nonzero__(self):
        return self.IsOk()

    def __eq__(*args, **kwargs):
        return _gdi_.Font___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _gdi_.Font___ne__(*args, **kwargs)

    def GetPointSize(*args, **kwargs):
        return _gdi_.Font_GetPointSize(*args, **kwargs)

    def GetPixelSize(*args, **kwargs):
        return _gdi_.Font_GetPixelSize(*args, **kwargs)

    def IsUsingSizeInPixels(*args, **kwargs):
        return _gdi_.Font_IsUsingSizeInPixels(*args, **kwargs)

    def GetFamily(*args, **kwargs):
        return _gdi_.Font_GetFamily(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _gdi_.Font_GetStyle(*args, **kwargs)

    def GetWeight(*args, **kwargs):
        return _gdi_.Font_GetWeight(*args, **kwargs)

    def GetUnderlined(*args, **kwargs):
        return _gdi_.Font_GetUnderlined(*args, **kwargs)

    def GetFaceName(*args, **kwargs):
        return _gdi_.Font_GetFaceName(*args, **kwargs)

    def GetEncoding(*args, **kwargs):
        return _gdi_.Font_GetEncoding(*args, **kwargs)

    def GetNativeFontInfo(*args, **kwargs):
        return _gdi_.Font_GetNativeFontInfo(*args, **kwargs)

    def IsFixedWidth(*args, **kwargs):
        return _gdi_.Font_IsFixedWidth(*args, **kwargs)

    def GetNativeFontInfoDesc(*args, **kwargs):
        return _gdi_.Font_GetNativeFontInfoDesc(*args, **kwargs)

    def GetNativeFontInfoUserDesc(*args, **kwargs):
        return _gdi_.Font_GetNativeFontInfoUserDesc(*args, **kwargs)

    def SetPointSize(*args, **kwargs):
        return _gdi_.Font_SetPointSize(*args, **kwargs)

    def SetPixelSize(*args, **kwargs):
        return _gdi_.Font_SetPixelSize(*args, **kwargs)

    def SetFamily(*args, **kwargs):
        return _gdi_.Font_SetFamily(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _gdi_.Font_SetStyle(*args, **kwargs)

    def SetWeight(*args, **kwargs):
        return _gdi_.Font_SetWeight(*args, **kwargs)

    def SetFaceName(*args, **kwargs):
        return _gdi_.Font_SetFaceName(*args, **kwargs)

    def SetUnderlined(*args, **kwargs):
        return _gdi_.Font_SetUnderlined(*args, **kwargs)

    def SetEncoding(*args, **kwargs):
        return _gdi_.Font_SetEncoding(*args, **kwargs)

    def SetNativeFontInfo(*args, **kwargs):
        return _gdi_.Font_SetNativeFontInfo(*args, **kwargs)

    def SetNativeFontInfoFromString(*args, **kwargs):
        return _gdi_.Font_SetNativeFontInfoFromString(*args, **kwargs)

    def SetNativeFontInfoUserDesc(*args, **kwargs):
        return _gdi_.Font_SetNativeFontInfoUserDesc(*args, **kwargs)

    def GetFamilyString(*args, **kwargs):
        return _gdi_.Font_GetFamilyString(*args, **kwargs)

    def GetStyleString(*args, **kwargs):
        return _gdi_.Font_GetStyleString(*args, **kwargs)

    def GetWeightString(*args, **kwargs):
        return _gdi_.Font_GetWeightString(*args, **kwargs)

    def SetNoAntiAliasing(*args, **kwargs):
        return _gdi_.Font_SetNoAntiAliasing(*args, **kwargs)

    def GetNoAntiAliasing(*args, **kwargs):
        return _gdi_.Font_GetNoAntiAliasing(*args, **kwargs)

    def GetPangoFontDescription(*args, **kwargs):
        return _gdi_.Font_GetPangoFontDescription(*args, **kwargs)

    def GetDefaultEncoding(*args, **kwargs):
        return _gdi_.Font_GetDefaultEncoding(*args, **kwargs)

    GetDefaultEncoding = staticmethod(GetDefaultEncoding)

    def SetDefaultEncoding(*args, **kwargs):
        return _gdi_.Font_SetDefaultEncoding(*args, **kwargs)

    SetDefaultEncoding = staticmethod(SetDefaultEncoding)
    Encoding = property(GetEncoding, SetEncoding, doc='See `GetEncoding` and `SetEncoding`')
    FaceName = property(GetFaceName, SetFaceName, doc='See `GetFaceName` and `SetFaceName`')
    Family = property(GetFamily, SetFamily, doc='See `GetFamily` and `SetFamily`')
    FamilyString = property(GetFamilyString, doc='See `GetFamilyString`')
    NativeFontInfo = property(GetNativeFontInfo, SetNativeFontInfo, doc='See `GetNativeFontInfo` and `SetNativeFontInfo`')
    NativeFontInfoDesc = property(GetNativeFontInfoDesc, doc='See `GetNativeFontInfoDesc`')
    NativeFontInfoUserDesc = property(GetNativeFontInfoUserDesc, SetNativeFontInfoUserDesc, doc='See `GetNativeFontInfoUserDesc` and `SetNativeFontInfoUserDesc`')
    NoAntiAliasing = property(GetNoAntiAliasing, SetNoAntiAliasing, doc='See `GetNoAntiAliasing` and `SetNoAntiAliasing`')
    PixelSize = property(GetPixelSize, SetPixelSize, doc='See `GetPixelSize` and `SetPixelSize`')
    PointSize = property(GetPointSize, SetPointSize, doc='See `GetPointSize` and `SetPointSize`')
    Style = property(GetStyle, SetStyle, doc='See `GetStyle` and `SetStyle`')
    StyleString = property(GetStyleString, doc='See `GetStyleString`')
    Underlined = property(GetUnderlined, SetUnderlined, doc='See `GetUnderlined` and `SetUnderlined`')
    Weight = property(GetWeight, SetWeight, doc='See `GetWeight` and `SetWeight`')
    WeightString = property(GetWeightString, doc='See `GetWeightString`')


_gdi_.Font_swigregister(Font)

def FontFromNativeInfo(*args, **kwargs):
    if kwargs.has_key('faceName'):
        kwargs['face'] = kwargs['faceName']
        del kwargs['faceName']
    val = _gdi_.new_FontFromNativeInfo(*args, **kwargs)
    return val


def FontFromNativeInfoString(*args, **kwargs):
    if kwargs.has_key('faceName'):
        kwargs['face'] = kwargs['faceName']
        del kwargs['faceName']
    val = _gdi_.new_FontFromNativeInfoString(*args, **kwargs)
    return val


def FFont(*args, **kwargs):
    if kwargs.has_key('faceName'):
        kwargs['face'] = kwargs['faceName']
        del kwargs['faceName']
    val = _gdi_.new_FFont(*args, **kwargs)
    return val


def FontFromPixelSize(*args, **kwargs):
    if kwargs.has_key('faceName'):
        kwargs['face'] = kwargs['faceName']
        del kwargs['faceName']
    val = _gdi_.new_FontFromPixelSize(*args, **kwargs)
    return val


def FFontFromPixelSize(*args, **kwargs):
    if kwargs.has_key('faceName'):
        kwargs['face'] = kwargs['faceName']
        del kwargs['faceName']
    val = _gdi_.new_FFontFromPixelSize(*args, **kwargs)
    return val


def Font_GetDefaultEncoding(*args):
    return _gdi_.Font_GetDefaultEncoding(*args)


def Font_SetDefaultEncoding(*args, **kwargs):
    return _gdi_.Font_SetDefaultEncoding(*args, **kwargs)


Font2 = wx._deprecated(FFont, 'Use `wx.FFont` instead.')

class FontEnumerator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.FontEnumerator_swiginit(self, _gdi_.new_FontEnumerator(*args, **kwargs))
        FontEnumerator._setCallbackInfo(self, self, FontEnumerator)

    __swig_destroy__ = _gdi_.delete_FontEnumerator
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _gdi_.FontEnumerator__setCallbackInfo(*args, **kwargs)

    def EnumerateFacenames(*args, **kwargs):
        return _gdi_.FontEnumerator_EnumerateFacenames(*args, **kwargs)

    def EnumerateEncodings(*args, **kwargs):
        return _gdi_.FontEnumerator_EnumerateEncodings(*args, **kwargs)

    def GetEncodings(*args, **kwargs):
        return _gdi_.FontEnumerator_GetEncodings(*args, **kwargs)

    GetEncodings = staticmethod(GetEncodings)

    def GetFacenames(*args, **kwargs):
        return _gdi_.FontEnumerator_GetFacenames(*args, **kwargs)

    GetFacenames = staticmethod(GetFacenames)

    def IsValidFacename(*args, **kwargs):
        return _gdi_.FontEnumerator_IsValidFacename(*args, **kwargs)

    IsValidFacename = staticmethod(IsValidFacename)


_gdi_.FontEnumerator_swigregister(FontEnumerator)

def FontEnumerator_GetEncodings(*args):
    return _gdi_.FontEnumerator_GetEncodings(*args)


def FontEnumerator_GetFacenames(*args):
    return _gdi_.FontEnumerator_GetFacenames(*args)


def FontEnumerator_IsValidFacename(*args, **kwargs):
    return _gdi_.FontEnumerator_IsValidFacename(*args, **kwargs)


LANGUAGE_DEFAULT = _gdi_.LANGUAGE_DEFAULT
LANGUAGE_UNKNOWN = _gdi_.LANGUAGE_UNKNOWN
LANGUAGE_ABKHAZIAN = _gdi_.LANGUAGE_ABKHAZIAN
LANGUAGE_AFAR = _gdi_.LANGUAGE_AFAR
LANGUAGE_AFRIKAANS = _gdi_.LANGUAGE_AFRIKAANS
LANGUAGE_ALBANIAN = _gdi_.LANGUAGE_ALBANIAN
LANGUAGE_AMHARIC = _gdi_.LANGUAGE_AMHARIC
LANGUAGE_ARABIC = _gdi_.LANGUAGE_ARABIC
LANGUAGE_ARABIC_ALGERIA = _gdi_.LANGUAGE_ARABIC_ALGERIA
LANGUAGE_ARABIC_BAHRAIN = _gdi_.LANGUAGE_ARABIC_BAHRAIN
LANGUAGE_ARABIC_EGYPT = _gdi_.LANGUAGE_ARABIC_EGYPT
LANGUAGE_ARABIC_IRAQ = _gdi_.LANGUAGE_ARABIC_IRAQ
LANGUAGE_ARABIC_JORDAN = _gdi_.LANGUAGE_ARABIC_JORDAN
LANGUAGE_ARABIC_KUWAIT = _gdi_.LANGUAGE_ARABIC_KUWAIT
LANGUAGE_ARABIC_LEBANON = _gdi_.LANGUAGE_ARABIC_LEBANON
LANGUAGE_ARABIC_LIBYA = _gdi_.LANGUAGE_ARABIC_LIBYA
LANGUAGE_ARABIC_MOROCCO = _gdi_.LANGUAGE_ARABIC_MOROCCO
LANGUAGE_ARABIC_OMAN = _gdi_.LANGUAGE_ARABIC_OMAN
LANGUAGE_ARABIC_QATAR = _gdi_.LANGUAGE_ARABIC_QATAR
LANGUAGE_ARABIC_SAUDI_ARABIA = _gdi_.LANGUAGE_ARABIC_SAUDI_ARABIA
LANGUAGE_ARABIC_SUDAN = _gdi_.LANGUAGE_ARABIC_SUDAN
LANGUAGE_ARABIC_SYRIA = _gdi_.LANGUAGE_ARABIC_SYRIA
LANGUAGE_ARABIC_TUNISIA = _gdi_.LANGUAGE_ARABIC_TUNISIA
LANGUAGE_ARABIC_UAE = _gdi_.LANGUAGE_ARABIC_UAE
LANGUAGE_ARABIC_YEMEN = _gdi_.LANGUAGE_ARABIC_YEMEN
LANGUAGE_ARMENIAN = _gdi_.LANGUAGE_ARMENIAN
LANGUAGE_ASSAMESE = _gdi_.LANGUAGE_ASSAMESE
LANGUAGE_AYMARA = _gdi_.LANGUAGE_AYMARA
LANGUAGE_AZERI = _gdi_.LANGUAGE_AZERI
LANGUAGE_AZERI_CYRILLIC = _gdi_.LANGUAGE_AZERI_CYRILLIC
LANGUAGE_AZERI_LATIN = _gdi_.LANGUAGE_AZERI_LATIN
LANGUAGE_BASHKIR = _gdi_.LANGUAGE_BASHKIR
LANGUAGE_BASQUE = _gdi_.LANGUAGE_BASQUE
LANGUAGE_BELARUSIAN = _gdi_.LANGUAGE_BELARUSIAN
LANGUAGE_BENGALI = _gdi_.LANGUAGE_BENGALI
LANGUAGE_BHUTANI = _gdi_.LANGUAGE_BHUTANI
LANGUAGE_BIHARI = _gdi_.LANGUAGE_BIHARI
LANGUAGE_BISLAMA = _gdi_.LANGUAGE_BISLAMA
LANGUAGE_BRETON = _gdi_.LANGUAGE_BRETON
LANGUAGE_BULGARIAN = _gdi_.LANGUAGE_BULGARIAN
LANGUAGE_BURMESE = _gdi_.LANGUAGE_BURMESE
LANGUAGE_CAMBODIAN = _gdi_.LANGUAGE_CAMBODIAN
LANGUAGE_CATALAN = _gdi_.LANGUAGE_CATALAN
LANGUAGE_CHINESE = _gdi_.LANGUAGE_CHINESE
LANGUAGE_CHINESE_SIMPLIFIED = _gdi_.LANGUAGE_CHINESE_SIMPLIFIED
LANGUAGE_CHINESE_TRADITIONAL = _gdi_.LANGUAGE_CHINESE_TRADITIONAL
LANGUAGE_CHINESE_HONGKONG = _gdi_.LANGUAGE_CHINESE_HONGKONG
LANGUAGE_CHINESE_MACAU = _gdi_.LANGUAGE_CHINESE_MACAU
LANGUAGE_CHINESE_SINGAPORE = _gdi_.LANGUAGE_CHINESE_SINGAPORE
LANGUAGE_CHINESE_TAIWAN = _gdi_.LANGUAGE_CHINESE_TAIWAN
LANGUAGE_CORSICAN = _gdi_.LANGUAGE_CORSICAN
LANGUAGE_CROATIAN = _gdi_.LANGUAGE_CROATIAN
LANGUAGE_CZECH = _gdi_.LANGUAGE_CZECH
LANGUAGE_DANISH = _gdi_.LANGUAGE_DANISH
LANGUAGE_DUTCH = _gdi_.LANGUAGE_DUTCH
LANGUAGE_DUTCH_BELGIAN = _gdi_.LANGUAGE_DUTCH_BELGIAN
LANGUAGE_ENGLISH = _gdi_.LANGUAGE_ENGLISH
LANGUAGE_ENGLISH_UK = _gdi_.LANGUAGE_ENGLISH_UK
LANGUAGE_ENGLISH_US = _gdi_.LANGUAGE_ENGLISH_US
LANGUAGE_ENGLISH_AUSTRALIA = _gdi_.LANGUAGE_ENGLISH_AUSTRALIA
LANGUAGE_ENGLISH_BELIZE = _gdi_.LANGUAGE_ENGLISH_BELIZE
LANGUAGE_ENGLISH_BOTSWANA = _gdi_.LANGUAGE_ENGLISH_BOTSWANA
LANGUAGE_ENGLISH_CANADA = _gdi_.LANGUAGE_ENGLISH_CANADA
LANGUAGE_ENGLISH_CARIBBEAN = _gdi_.LANGUAGE_ENGLISH_CARIBBEAN
LANGUAGE_ENGLISH_DENMARK = _gdi_.LANGUAGE_ENGLISH_DENMARK
LANGUAGE_ENGLISH_EIRE = _gdi_.LANGUAGE_ENGLISH_EIRE
LANGUAGE_ENGLISH_JAMAICA = _gdi_.LANGUAGE_ENGLISH_JAMAICA
LANGUAGE_ENGLISH_NEW_ZEALAND = _gdi_.LANGUAGE_ENGLISH_NEW_ZEALAND
LANGUAGE_ENGLISH_PHILIPPINES = _gdi_.LANGUAGE_ENGLISH_PHILIPPINES
LANGUAGE_ENGLISH_SOUTH_AFRICA = _gdi_.LANGUAGE_ENGLISH_SOUTH_AFRICA
LANGUAGE_ENGLISH_TRINIDAD = _gdi_.LANGUAGE_ENGLISH_TRINIDAD
LANGUAGE_ENGLISH_ZIMBABWE = _gdi_.LANGUAGE_ENGLISH_ZIMBABWE
LANGUAGE_ESPERANTO = _gdi_.LANGUAGE_ESPERANTO
LANGUAGE_ESTONIAN = _gdi_.LANGUAGE_ESTONIAN
LANGUAGE_FAEROESE = _gdi_.LANGUAGE_FAEROESE
LANGUAGE_FARSI = _gdi_.LANGUAGE_FARSI
LANGUAGE_FIJI = _gdi_.LANGUAGE_FIJI
LANGUAGE_FINNISH = _gdi_.LANGUAGE_FINNISH
LANGUAGE_FRENCH = _gdi_.LANGUAGE_FRENCH
LANGUAGE_FRENCH_BELGIAN = _gdi_.LANGUAGE_FRENCH_BELGIAN
LANGUAGE_FRENCH_CANADIAN = _gdi_.LANGUAGE_FRENCH_CANADIAN
LANGUAGE_FRENCH_LUXEMBOURG = _gdi_.LANGUAGE_FRENCH_LUXEMBOURG
LANGUAGE_FRENCH_MONACO = _gdi_.LANGUAGE_FRENCH_MONACO
LANGUAGE_FRENCH_SWISS = _gdi_.LANGUAGE_FRENCH_SWISS
LANGUAGE_FRISIAN = _gdi_.LANGUAGE_FRISIAN
LANGUAGE_GALICIAN = _gdi_.LANGUAGE_GALICIAN
LANGUAGE_GEORGIAN = _gdi_.LANGUAGE_GEORGIAN
LANGUAGE_GERMAN = _gdi_.LANGUAGE_GERMAN
LANGUAGE_GERMAN_AUSTRIAN = _gdi_.LANGUAGE_GERMAN_AUSTRIAN
LANGUAGE_GERMAN_BELGIUM = _gdi_.LANGUAGE_GERMAN_BELGIUM
LANGUAGE_GERMAN_LIECHTENSTEIN = _gdi_.LANGUAGE_GERMAN_LIECHTENSTEIN
LANGUAGE_GERMAN_LUXEMBOURG = _gdi_.LANGUAGE_GERMAN_LUXEMBOURG
LANGUAGE_GERMAN_SWISS = _gdi_.LANGUAGE_GERMAN_SWISS
LANGUAGE_GREEK = _gdi_.LANGUAGE_GREEK
LANGUAGE_GREENLANDIC = _gdi_.LANGUAGE_GREENLANDIC
LANGUAGE_GUARANI = _gdi_.LANGUAGE_GUARANI
LANGUAGE_GUJARATI = _gdi_.LANGUAGE_GUJARATI
LANGUAGE_HAUSA = _gdi_.LANGUAGE_HAUSA
LANGUAGE_HEBREW = _gdi_.LANGUAGE_HEBREW
LANGUAGE_HINDI = _gdi_.LANGUAGE_HINDI
LANGUAGE_HUNGARIAN = _gdi_.LANGUAGE_HUNGARIAN
LANGUAGE_ICELANDIC = _gdi_.LANGUAGE_ICELANDIC
LANGUAGE_INDONESIAN = _gdi_.LANGUAGE_INDONESIAN
LANGUAGE_INTERLINGUA = _gdi_.LANGUAGE_INTERLINGUA
LANGUAGE_INTERLINGUE = _gdi_.LANGUAGE_INTERLINGUE
LANGUAGE_INUKTITUT = _gdi_.LANGUAGE_INUKTITUT
LANGUAGE_INUPIAK = _gdi_.LANGUAGE_INUPIAK
LANGUAGE_IRISH = _gdi_.LANGUAGE_IRISH
LANGUAGE_ITALIAN = _gdi_.LANGUAGE_ITALIAN
LANGUAGE_ITALIAN_SWISS = _gdi_.LANGUAGE_ITALIAN_SWISS
LANGUAGE_JAPANESE = _gdi_.LANGUAGE_JAPANESE
LANGUAGE_JAVANESE = _gdi_.LANGUAGE_JAVANESE
LANGUAGE_KANNADA = _gdi_.LANGUAGE_KANNADA
LANGUAGE_KASHMIRI = _gdi_.LANGUAGE_KASHMIRI
LANGUAGE_KASHMIRI_INDIA = _gdi_.LANGUAGE_KASHMIRI_INDIA
LANGUAGE_KAZAKH = _gdi_.LANGUAGE_KAZAKH
LANGUAGE_KERNEWEK = _gdi_.LANGUAGE_KERNEWEK
LANGUAGE_KINYARWANDA = _gdi_.LANGUAGE_KINYARWANDA
LANGUAGE_KIRGHIZ = _gdi_.LANGUAGE_KIRGHIZ
LANGUAGE_KIRUNDI = _gdi_.LANGUAGE_KIRUNDI
LANGUAGE_KONKANI = _gdi_.LANGUAGE_KONKANI
LANGUAGE_KOREAN = _gdi_.LANGUAGE_KOREAN
LANGUAGE_KURDISH = _gdi_.LANGUAGE_KURDISH
LANGUAGE_LAOTHIAN = _gdi_.LANGUAGE_LAOTHIAN
LANGUAGE_LATIN = _gdi_.LANGUAGE_LATIN
LANGUAGE_LATVIAN = _gdi_.LANGUAGE_LATVIAN
LANGUAGE_LINGALA = _gdi_.LANGUAGE_LINGALA
LANGUAGE_LITHUANIAN = _gdi_.LANGUAGE_LITHUANIAN
LANGUAGE_MACEDONIAN = _gdi_.LANGUAGE_MACEDONIAN
LANGUAGE_MALAGASY = _gdi_.LANGUAGE_MALAGASY
LANGUAGE_MALAY = _gdi_.LANGUAGE_MALAY
LANGUAGE_MALAYALAM = _gdi_.LANGUAGE_MALAYALAM
LANGUAGE_MALAY_BRUNEI_DARUSSALAM = _gdi_.LANGUAGE_MALAY_BRUNEI_DARUSSALAM
LANGUAGE_MALAY_MALAYSIA = _gdi_.LANGUAGE_MALAY_MALAYSIA
LANGUAGE_MALTESE = _gdi_.LANGUAGE_MALTESE
LANGUAGE_MANIPURI = _gdi_.LANGUAGE_MANIPURI
LANGUAGE_MAORI = _gdi_.LANGUAGE_MAORI
LANGUAGE_MARATHI = _gdi_.LANGUAGE_MARATHI
LANGUAGE_MOLDAVIAN = _gdi_.LANGUAGE_MOLDAVIAN
LANGUAGE_MONGOLIAN = _gdi_.LANGUAGE_MONGOLIAN
LANGUAGE_NAURU = _gdi_.LANGUAGE_NAURU
LANGUAGE_NEPALI = _gdi_.LANGUAGE_NEPALI
LANGUAGE_NEPALI_INDIA = _gdi_.LANGUAGE_NEPALI_INDIA
LANGUAGE_NORWEGIAN_BOKMAL = _gdi_.LANGUAGE_NORWEGIAN_BOKMAL
LANGUAGE_NORWEGIAN_NYNORSK = _gdi_.LANGUAGE_NORWEGIAN_NYNORSK
LANGUAGE_OCCITAN = _gdi_.LANGUAGE_OCCITAN
LANGUAGE_ORIYA = _gdi_.LANGUAGE_ORIYA
LANGUAGE_OROMO = _gdi_.LANGUAGE_OROMO
LANGUAGE_PASHTO = _gdi_.LANGUAGE_PASHTO
LANGUAGE_POLISH = _gdi_.LANGUAGE_POLISH
LANGUAGE_PORTUGUESE = _gdi_.LANGUAGE_PORTUGUESE
LANGUAGE_PORTUGUESE_BRAZILIAN = _gdi_.LANGUAGE_PORTUGUESE_BRAZILIAN
LANGUAGE_PUNJABI = _gdi_.LANGUAGE_PUNJABI
LANGUAGE_QUECHUA = _gdi_.LANGUAGE_QUECHUA
LANGUAGE_RHAETO_ROMANCE = _gdi_.LANGUAGE_RHAETO_ROMANCE
LANGUAGE_ROMANIAN = _gdi_.LANGUAGE_ROMANIAN
LANGUAGE_RUSSIAN = _gdi_.LANGUAGE_RUSSIAN
LANGUAGE_RUSSIAN_UKRAINE = _gdi_.LANGUAGE_RUSSIAN_UKRAINE
LANGUAGE_SAMI = _gdi_.LANGUAGE_SAMI
LANGUAGE_SAMOAN = _gdi_.LANGUAGE_SAMOAN
LANGUAGE_SANGHO = _gdi_.LANGUAGE_SANGHO
LANGUAGE_SANSKRIT = _gdi_.LANGUAGE_SANSKRIT
LANGUAGE_SCOTS_GAELIC = _gdi_.LANGUAGE_SCOTS_GAELIC
LANGUAGE_SERBIAN = _gdi_.LANGUAGE_SERBIAN
LANGUAGE_SERBIAN_CYRILLIC = _gdi_.LANGUAGE_SERBIAN_CYRILLIC
LANGUAGE_SERBIAN_LATIN = _gdi_.LANGUAGE_SERBIAN_LATIN
LANGUAGE_SERBO_CROATIAN = _gdi_.LANGUAGE_SERBO_CROATIAN
LANGUAGE_SESOTHO = _gdi_.LANGUAGE_SESOTHO
LANGUAGE_SETSWANA = _gdi_.LANGUAGE_SETSWANA
LANGUAGE_SHONA = _gdi_.LANGUAGE_SHONA
LANGUAGE_SINDHI = _gdi_.LANGUAGE_SINDHI
LANGUAGE_SINHALESE = _gdi_.LANGUAGE_SINHALESE
LANGUAGE_SISWATI = _gdi_.LANGUAGE_SISWATI
LANGUAGE_SLOVAK = _gdi_.LANGUAGE_SLOVAK
LANGUAGE_SLOVENIAN = _gdi_.LANGUAGE_SLOVENIAN
LANGUAGE_SOMALI = _gdi_.LANGUAGE_SOMALI
LANGUAGE_SPANISH = _gdi_.LANGUAGE_SPANISH
LANGUAGE_SPANISH_ARGENTINA = _gdi_.LANGUAGE_SPANISH_ARGENTINA
LANGUAGE_SPANISH_BOLIVIA = _gdi_.LANGUAGE_SPANISH_BOLIVIA
LANGUAGE_SPANISH_CHILE = _gdi_.LANGUAGE_SPANISH_CHILE
LANGUAGE_SPANISH_COLOMBIA = _gdi_.LANGUAGE_SPANISH_COLOMBIA
LANGUAGE_SPANISH_COSTA_RICA = _gdi_.LANGUAGE_SPANISH_COSTA_RICA
LANGUAGE_SPANISH_DOMINICAN_REPUBLIC = _gdi_.LANGUAGE_SPANISH_DOMINICAN_REPUBLIC
LANGUAGE_SPANISH_ECUADOR = _gdi_.LANGUAGE_SPANISH_ECUADOR
LANGUAGE_SPANISH_EL_SALVADOR = _gdi_.LANGUAGE_SPANISH_EL_SALVADOR
LANGUAGE_SPANISH_GUATEMALA = _gdi_.LANGUAGE_SPANISH_GUATEMALA
LANGUAGE_SPANISH_HONDURAS = _gdi_.LANGUAGE_SPANISH_HONDURAS
LANGUAGE_SPANISH_MEXICAN = _gdi_.LANGUAGE_SPANISH_MEXICAN
LANGUAGE_SPANISH_MODERN = _gdi_.LANGUAGE_SPANISH_MODERN
LANGUAGE_SPANISH_NICARAGUA = _gdi_.LANGUAGE_SPANISH_NICARAGUA
LANGUAGE_SPANISH_PANAMA = _gdi_.LANGUAGE_SPANISH_PANAMA
LANGUAGE_SPANISH_PARAGUAY = _gdi_.LANGUAGE_SPANISH_PARAGUAY
LANGUAGE_SPANISH_PERU = _gdi_.LANGUAGE_SPANISH_PERU
LANGUAGE_SPANISH_PUERTO_RICO = _gdi_.LANGUAGE_SPANISH_PUERTO_RICO
LANGUAGE_SPANISH_URUGUAY = _gdi_.LANGUAGE_SPANISH_URUGUAY
LANGUAGE_SPANISH_US = _gdi_.LANGUAGE_SPANISH_US
LANGUAGE_SPANISH_VENEZUELA = _gdi_.LANGUAGE_SPANISH_VENEZUELA
LANGUAGE_SUNDANESE = _gdi_.LANGUAGE_SUNDANESE
LANGUAGE_SWAHILI = _gdi_.LANGUAGE_SWAHILI
LANGUAGE_SWEDISH = _gdi_.LANGUAGE_SWEDISH
LANGUAGE_SWEDISH_FINLAND = _gdi_.LANGUAGE_SWEDISH_FINLAND
LANGUAGE_TAGALOG = _gdi_.LANGUAGE_TAGALOG
LANGUAGE_TAJIK = _gdi_.LANGUAGE_TAJIK
LANGUAGE_TAMIL = _gdi_.LANGUAGE_TAMIL
LANGUAGE_TATAR = _gdi_.LANGUAGE_TATAR
LANGUAGE_TELUGU = _gdi_.LANGUAGE_TELUGU
LANGUAGE_THAI = _gdi_.LANGUAGE_THAI
LANGUAGE_TIBETAN = _gdi_.LANGUAGE_TIBETAN
LANGUAGE_TIGRINYA = _gdi_.LANGUAGE_TIGRINYA
LANGUAGE_TONGA = _gdi_.LANGUAGE_TONGA
LANGUAGE_TSONGA = _gdi_.LANGUAGE_TSONGA
LANGUAGE_TURKISH = _gdi_.LANGUAGE_TURKISH
LANGUAGE_TURKMEN = _gdi_.LANGUAGE_TURKMEN
LANGUAGE_TWI = _gdi_.LANGUAGE_TWI
LANGUAGE_UIGHUR = _gdi_.LANGUAGE_UIGHUR
LANGUAGE_UKRAINIAN = _gdi_.LANGUAGE_UKRAINIAN
LANGUAGE_URDU = _gdi_.LANGUAGE_URDU
LANGUAGE_URDU_INDIA = _gdi_.LANGUAGE_URDU_INDIA
LANGUAGE_URDU_PAKISTAN = _gdi_.LANGUAGE_URDU_PAKISTAN
LANGUAGE_UZBEK = _gdi_.LANGUAGE_UZBEK
LANGUAGE_UZBEK_CYRILLIC = _gdi_.LANGUAGE_UZBEK_CYRILLIC
LANGUAGE_UZBEK_LATIN = _gdi_.LANGUAGE_UZBEK_LATIN
LANGUAGE_VALENCIAN = _gdi_.LANGUAGE_VALENCIAN
LANGUAGE_VIETNAMESE = _gdi_.LANGUAGE_VIETNAMESE
LANGUAGE_VOLAPUK = _gdi_.LANGUAGE_VOLAPUK
LANGUAGE_WELSH = _gdi_.LANGUAGE_WELSH
LANGUAGE_WOLOF = _gdi_.LANGUAGE_WOLOF
LANGUAGE_XHOSA = _gdi_.LANGUAGE_XHOSA
LANGUAGE_YIDDISH = _gdi_.LANGUAGE_YIDDISH
LANGUAGE_YORUBA = _gdi_.LANGUAGE_YORUBA
LANGUAGE_ZHUANG = _gdi_.LANGUAGE_ZHUANG
LANGUAGE_ZULU = _gdi_.LANGUAGE_ZULU
LANGUAGE_USER_DEFINED = _gdi_.LANGUAGE_USER_DEFINED

class LanguageInfo(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    Language = property(_gdi_.LanguageInfo_Language_get, _gdi_.LanguageInfo_Language_set)
    CanonicalName = property(_gdi_.LanguageInfo_CanonicalName_get, _gdi_.LanguageInfo_CanonicalName_set)
    Description = property(_gdi_.LanguageInfo_Description_get, _gdi_.LanguageInfo_Description_set)


_gdi_.LanguageInfo_swigregister(LanguageInfo)
LOCALE_CAT_NUMBER = _gdi_.LOCALE_CAT_NUMBER
LOCALE_CAT_DATE = _gdi_.LOCALE_CAT_DATE
LOCALE_CAT_MONEY = _gdi_.LOCALE_CAT_MONEY
LOCALE_CAT_MAX = _gdi_.LOCALE_CAT_MAX
LOCALE_THOUSANDS_SEP = _gdi_.LOCALE_THOUSANDS_SEP
LOCALE_DECIMAL_POINT = _gdi_.LOCALE_DECIMAL_POINT
LOCALE_LOAD_DEFAULT = _gdi_.LOCALE_LOAD_DEFAULT
LOCALE_CONV_ENCODING = _gdi_.LOCALE_CONV_ENCODING

class Locale(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Locale_swiginit(self, _gdi_.new_Locale(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Locale
    __del__ = lambda self: None

    def Init1(*args, **kwargs):
        return _gdi_.Locale_Init1(*args, **kwargs)

    def Init2(*args, **kwargs):
        return _gdi_.Locale_Init2(*args, **kwargs)

    def Init(self, *_args, **_kwargs):
        if type(_args[0]) in [type(''), type(u'')]:
            val = self.Init1(*_args, **_kwargs)
        else:
            val = self.Init2(*_args, **_kwargs)
        return val

    def GetSystemLanguage(*args, **kwargs):
        return _gdi_.Locale_GetSystemLanguage(*args, **kwargs)

    GetSystemLanguage = staticmethod(GetSystemLanguage)

    def GetSystemEncoding(*args, **kwargs):
        return _gdi_.Locale_GetSystemEncoding(*args, **kwargs)

    GetSystemEncoding = staticmethod(GetSystemEncoding)

    def GetSystemEncodingName(*args, **kwargs):
        return _gdi_.Locale_GetSystemEncodingName(*args, **kwargs)

    GetSystemEncodingName = staticmethod(GetSystemEncodingName)

    def IsOk(*args, **kwargs):
        return _gdi_.Locale_IsOk(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def GetLocale(*args, **kwargs):
        return _gdi_.Locale_GetLocale(*args, **kwargs)

    def GetLanguage(*args, **kwargs):
        return _gdi_.Locale_GetLanguage(*args, **kwargs)

    def GetSysName(*args, **kwargs):
        return _gdi_.Locale_GetSysName(*args, **kwargs)

    def GetCanonicalName(*args, **kwargs):
        return _gdi_.Locale_GetCanonicalName(*args, **kwargs)

    def AddCatalogLookupPathPrefix(*args, **kwargs):
        return _gdi_.Locale_AddCatalogLookupPathPrefix(*args, **kwargs)

    AddCatalogLookupPathPrefix = staticmethod(AddCatalogLookupPathPrefix)

    def AddCatalog(*args, **kwargs):
        return _gdi_.Locale_AddCatalog(*args, **kwargs)

    def IsAvailable(*args, **kwargs):
        return _gdi_.Locale_IsAvailable(*args, **kwargs)

    IsAvailable = staticmethod(IsAvailable)

    def IsLoaded(*args, **kwargs):
        return _gdi_.Locale_IsLoaded(*args, **kwargs)

    def GetLanguageInfo(*args, **kwargs):
        return _gdi_.Locale_GetLanguageInfo(*args, **kwargs)

    GetLanguageInfo = staticmethod(GetLanguageInfo)

    def GetLanguageName(*args, **kwargs):
        return _gdi_.Locale_GetLanguageName(*args, **kwargs)

    GetLanguageName = staticmethod(GetLanguageName)

    def FindLanguageInfo(*args, **kwargs):
        return _gdi_.Locale_FindLanguageInfo(*args, **kwargs)

    FindLanguageInfo = staticmethod(FindLanguageInfo)

    def AddLanguage(*args, **kwargs):
        return _gdi_.Locale_AddLanguage(*args, **kwargs)

    AddLanguage = staticmethod(AddLanguage)

    def GetString(*args, **kwargs):
        return _gdi_.Locale_GetString(*args, **kwargs)

    def GetName(*args, **kwargs):
        return _gdi_.Locale_GetName(*args, **kwargs)

    CanonicalName = property(GetCanonicalName, doc='See `GetCanonicalName`')
    Language = property(GetLanguage, doc='See `GetLanguage`')
    Locale = property(GetLocale, doc='See `GetLocale`')
    Name = property(GetName, doc='See `GetName`')
    String = property(GetString, doc='See `GetString`')
    SysName = property(GetSysName, doc='See `GetSysName`')


_gdi_.Locale_swigregister(Locale)

def Locale_GetSystemLanguage(*args):
    return _gdi_.Locale_GetSystemLanguage(*args)


def Locale_GetSystemEncoding(*args):
    return _gdi_.Locale_GetSystemEncoding(*args)


def Locale_GetSystemEncodingName(*args):
    return _gdi_.Locale_GetSystemEncodingName(*args)


def Locale_AddCatalogLookupPathPrefix(*args, **kwargs):
    return _gdi_.Locale_AddCatalogLookupPathPrefix(*args, **kwargs)


def Locale_IsAvailable(*args, **kwargs):
    return _gdi_.Locale_IsAvailable(*args, **kwargs)


def Locale_GetLanguageInfo(*args, **kwargs):
    return _gdi_.Locale_GetLanguageInfo(*args, **kwargs)


def Locale_GetLanguageName(*args, **kwargs):
    return _gdi_.Locale_GetLanguageName(*args, **kwargs)


def Locale_FindLanguageInfo(*args, **kwargs):
    return _gdi_.Locale_FindLanguageInfo(*args, **kwargs)


def Locale_AddLanguage(*args, **kwargs):
    return _gdi_.Locale_AddLanguage(*args, **kwargs)


class PyLocale(Locale):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.PyLocale_swiginit(self, _gdi_.new_PyLocale(*args, **kwargs))
        PyLocale._setCallbackInfo(self, self, PyLocale)

    __swig_destroy__ = _gdi_.delete_PyLocale
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _gdi_.PyLocale__setCallbackInfo(*args, **kwargs)

    def GetSingularString(*args, **kwargs):
        return _gdi_.PyLocale_GetSingularString(*args, **kwargs)

    def GetPluralString(*args, **kwargs):
        return _gdi_.PyLocale_GetPluralString(*args, **kwargs)


_gdi_.PyLocale_swigregister(PyLocale)

def GetLocale(*args):
    return _gdi_.GetLocale(*args)


CONVERT_STRICT = _gdi_.CONVERT_STRICT
CONVERT_SUBSTITUTE = _gdi_.CONVERT_SUBSTITUTE
PLATFORM_CURRENT = _gdi_.PLATFORM_CURRENT
PLATFORM_UNIX = _gdi_.PLATFORM_UNIX
PLATFORM_WINDOWS = _gdi_.PLATFORM_WINDOWS
PLATFORM_OS2 = _gdi_.PLATFORM_OS2
PLATFORM_MAC = _gdi_.PLATFORM_MAC

class EncodingConverter(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.EncodingConverter_swiginit(self, _gdi_.new_EncodingConverter(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_EncodingConverter
    __del__ = lambda self: None

    def Init(*args, **kwargs):
        return _gdi_.EncodingConverter_Init(*args, **kwargs)

    def Convert(*args, **kwargs):
        return _gdi_.EncodingConverter_Convert(*args, **kwargs)

    def GetPlatformEquivalents(*args, **kwargs):
        return _gdi_.EncodingConverter_GetPlatformEquivalents(*args, **kwargs)

    GetPlatformEquivalents = staticmethod(GetPlatformEquivalents)

    def GetAllEquivalents(*args, **kwargs):
        return _gdi_.EncodingConverter_GetAllEquivalents(*args, **kwargs)

    GetAllEquivalents = staticmethod(GetAllEquivalents)

    def CanConvert(*args, **kwargs):
        return _gdi_.EncodingConverter_CanConvert(*args, **kwargs)

    CanConvert = staticmethod(CanConvert)

    def __nonzero__(self):
        return self.IsOk()


_gdi_.EncodingConverter_swigregister(EncodingConverter)

def GetTranslation(*args):
    return _gdi_.GetTranslation(*args)


def EncodingConverter_GetPlatformEquivalents(*args, **kwargs):
    return _gdi_.EncodingConverter_GetPlatformEquivalents(*args, **kwargs)


def EncodingConverter_GetAllEquivalents(*args, **kwargs):
    return _gdi_.EncodingConverter_GetAllEquivalents(*args, **kwargs)


def EncodingConverter_CanConvert(*args, **kwargs):
    return _gdi_.EncodingConverter_CanConvert(*args, **kwargs)


import os
_localedir = os.path.join(os.path.dirname(__file__), 'locale')
if os.path.exists(_localedir):
    Locale.AddCatalogLookupPathPrefix(_localedir)
del os

class DC(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _gdi_.delete_DC
    __del__ = lambda self: None

    def BeginDrawing(self):
        pass

    def EndDrawing(self):
        pass

    def FloodFill(*args, **kwargs):
        return _gdi_.DC_FloodFill(*args, **kwargs)

    def FloodFillPoint(*args, **kwargs):
        return _gdi_.DC_FloodFillPoint(*args, **kwargs)

    def GradientFillConcentric(*args, **kwargs):
        return _gdi_.DC_GradientFillConcentric(*args, **kwargs)

    def GradientFillLinear(*args, **kwargs):
        return _gdi_.DC_GradientFillLinear(*args, **kwargs)

    def GetPixel(*args, **kwargs):
        return _gdi_.DC_GetPixel(*args, **kwargs)

    def GetPixelPoint(*args, **kwargs):
        return _gdi_.DC_GetPixelPoint(*args, **kwargs)

    def DrawLine(*args, **kwargs):
        return _gdi_.DC_DrawLine(*args, **kwargs)

    def DrawLinePoint(*args, **kwargs):
        return _gdi_.DC_DrawLinePoint(*args, **kwargs)

    def CrossHair(*args, **kwargs):
        return _gdi_.DC_CrossHair(*args, **kwargs)

    def CrossHairPoint(*args, **kwargs):
        return _gdi_.DC_CrossHairPoint(*args, **kwargs)

    def DrawArc(*args, **kwargs):
        return _gdi_.DC_DrawArc(*args, **kwargs)

    def DrawArcPoint(*args, **kwargs):
        return _gdi_.DC_DrawArcPoint(*args, **kwargs)

    def DrawCheckMark(*args, **kwargs):
        return _gdi_.DC_DrawCheckMark(*args, **kwargs)

    def DrawCheckMarkRect(*args, **kwargs):
        return _gdi_.DC_DrawCheckMarkRect(*args, **kwargs)

    def DrawEllipticArc(*args, **kwargs):
        return _gdi_.DC_DrawEllipticArc(*args, **kwargs)

    def DrawEllipticArcPointSize(*args, **kwargs):
        return _gdi_.DC_DrawEllipticArcPointSize(*args, **kwargs)

    def DrawPoint(*args, **kwargs):
        return _gdi_.DC_DrawPoint(*args, **kwargs)

    def DrawPointPoint(*args, **kwargs):
        return _gdi_.DC_DrawPointPoint(*args, **kwargs)

    def DrawRectangle(*args, **kwargs):
        return _gdi_.DC_DrawRectangle(*args, **kwargs)

    def DrawRectangleRect(*args, **kwargs):
        return _gdi_.DC_DrawRectangleRect(*args, **kwargs)

    def DrawRectanglePointSize(*args, **kwargs):
        return _gdi_.DC_DrawRectanglePointSize(*args, **kwargs)

    def DrawRoundedRectangle(*args, **kwargs):
        return _gdi_.DC_DrawRoundedRectangle(*args, **kwargs)

    def DrawRoundedRectangleRect(*args, **kwargs):
        return _gdi_.DC_DrawRoundedRectangleRect(*args, **kwargs)

    def DrawRoundedRectanglePointSize(*args, **kwargs):
        return _gdi_.DC_DrawRoundedRectanglePointSize(*args, **kwargs)

    def DrawCircle(*args, **kwargs):
        return _gdi_.DC_DrawCircle(*args, **kwargs)

    def DrawCirclePoint(*args, **kwargs):
        return _gdi_.DC_DrawCirclePoint(*args, **kwargs)

    def DrawEllipse(*args, **kwargs):
        return _gdi_.DC_DrawEllipse(*args, **kwargs)

    def DrawEllipseRect(*args, **kwargs):
        return _gdi_.DC_DrawEllipseRect(*args, **kwargs)

    def DrawEllipsePointSize(*args, **kwargs):
        return _gdi_.DC_DrawEllipsePointSize(*args, **kwargs)

    def DrawIcon(*args, **kwargs):
        return _gdi_.DC_DrawIcon(*args, **kwargs)

    def DrawIconPoint(*args, **kwargs):
        return _gdi_.DC_DrawIconPoint(*args, **kwargs)

    def DrawBitmap(*args, **kwargs):
        return _gdi_.DC_DrawBitmap(*args, **kwargs)

    def DrawBitmapPoint(*args, **kwargs):
        return _gdi_.DC_DrawBitmapPoint(*args, **kwargs)

    def DrawText(*args, **kwargs):
        return _gdi_.DC_DrawText(*args, **kwargs)

    def DrawTextPoint(*args, **kwargs):
        return _gdi_.DC_DrawTextPoint(*args, **kwargs)

    def DrawRotatedText(*args, **kwargs):
        return _gdi_.DC_DrawRotatedText(*args, **kwargs)

    def DrawRotatedTextPoint(*args, **kwargs):
        return _gdi_.DC_DrawRotatedTextPoint(*args, **kwargs)

    def Blit(*args, **kwargs):
        return _gdi_.DC_Blit(*args, **kwargs)

    def BlitPointSize(*args, **kwargs):
        return _gdi_.DC_BlitPointSize(*args, **kwargs)

    def GetAsBitmap(*args, **kwargs):
        return _gdi_.DC_GetAsBitmap(*args, **kwargs)

    def SetClippingRegion(*args, **kwargs):
        return _gdi_.DC_SetClippingRegion(*args, **kwargs)

    def SetClippingRegionPointSize(*args, **kwargs):
        return _gdi_.DC_SetClippingRegionPointSize(*args, **kwargs)

    def SetClippingRegionAsRegion(*args, **kwargs):
        return _gdi_.DC_SetClippingRegionAsRegion(*args, **kwargs)

    def SetClippingRect(*args, **kwargs):
        return _gdi_.DC_SetClippingRect(*args, **kwargs)

    def DrawLines(*args, **kwargs):
        return _gdi_.DC_DrawLines(*args, **kwargs)

    def DrawPolygon(*args, **kwargs):
        return _gdi_.DC_DrawPolygon(*args, **kwargs)

    def DrawLabel(*args, **kwargs):
        return _gdi_.DC_DrawLabel(*args, **kwargs)

    def DrawImageLabel(*args, **kwargs):
        return _gdi_.DC_DrawImageLabel(*args, **kwargs)

    def DrawSpline(*args, **kwargs):
        return _gdi_.DC_DrawSpline(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _gdi_.DC_Clear(*args, **kwargs)

    def StartDoc(*args, **kwargs):
        return _gdi_.DC_StartDoc(*args, **kwargs)

    def EndDoc(*args, **kwargs):
        return _gdi_.DC_EndDoc(*args, **kwargs)

    def StartPage(*args, **kwargs):
        return _gdi_.DC_StartPage(*args, **kwargs)

    def EndPage(*args, **kwargs):
        return _gdi_.DC_EndPage(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _gdi_.DC_SetFont(*args, **kwargs)

    def SetPen(*args, **kwargs):
        return _gdi_.DC_SetPen(*args, **kwargs)

    def SetBrush(*args, **kwargs):
        return _gdi_.DC_SetBrush(*args, **kwargs)

    def SetBackground(*args, **kwargs):
        return _gdi_.DC_SetBackground(*args, **kwargs)

    def SetBackgroundMode(*args, **kwargs):
        return _gdi_.DC_SetBackgroundMode(*args, **kwargs)

    def SetPalette(*args, **kwargs):
        return _gdi_.DC_SetPalette(*args, **kwargs)

    def DestroyClippingRegion(*args, **kwargs):
        return _gdi_.DC_DestroyClippingRegion(*args, **kwargs)

    def GetClippingBox(*args, **kwargs):
        return _gdi_.DC_GetClippingBox(*args, **kwargs)

    def GetClippingRect(*args, **kwargs):
        return _gdi_.DC_GetClippingRect(*args, **kwargs)

    def GetCharHeight(*args, **kwargs):
        return _gdi_.DC_GetCharHeight(*args, **kwargs)

    def GetCharWidth(*args, **kwargs):
        return _gdi_.DC_GetCharWidth(*args, **kwargs)

    def GetTextExtent(*args, **kwargs):
        return _gdi_.DC_GetTextExtent(*args, **kwargs)

    def GetFullTextExtent(*args, **kwargs):
        return _gdi_.DC_GetFullTextExtent(*args, **kwargs)

    def GetMultiLineTextExtent(*args, **kwargs):
        return _gdi_.DC_GetMultiLineTextExtent(*args, **kwargs)

    def GetPartialTextExtents(*args, **kwargs):
        return _gdi_.DC_GetPartialTextExtents(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _gdi_.DC_GetSize(*args, **kwargs)

    def GetSizeTuple(*args, **kwargs):
        return _gdi_.DC_GetSizeTuple(*args, **kwargs)

    def GetSizeMM(*args, **kwargs):
        return _gdi_.DC_GetSizeMM(*args, **kwargs)

    def GetSizeMMTuple(*args, **kwargs):
        return _gdi_.DC_GetSizeMMTuple(*args, **kwargs)

    def DeviceToLogicalX(*args, **kwargs):
        return _gdi_.DC_DeviceToLogicalX(*args, **kwargs)

    def DeviceToLogicalY(*args, **kwargs):
        return _gdi_.DC_DeviceToLogicalY(*args, **kwargs)

    def DeviceToLogicalXRel(*args, **kwargs):
        return _gdi_.DC_DeviceToLogicalXRel(*args, **kwargs)

    def DeviceToLogicalYRel(*args, **kwargs):
        return _gdi_.DC_DeviceToLogicalYRel(*args, **kwargs)

    def LogicalToDeviceX(*args, **kwargs):
        return _gdi_.DC_LogicalToDeviceX(*args, **kwargs)

    def LogicalToDeviceY(*args, **kwargs):
        return _gdi_.DC_LogicalToDeviceY(*args, **kwargs)

    def LogicalToDeviceXRel(*args, **kwargs):
        return _gdi_.DC_LogicalToDeviceXRel(*args, **kwargs)

    def LogicalToDeviceYRel(*args, **kwargs):
        return _gdi_.DC_LogicalToDeviceYRel(*args, **kwargs)

    def CanDrawBitmap(*args, **kwargs):
        return _gdi_.DC_CanDrawBitmap(*args, **kwargs)

    def CanGetTextExtent(*args, **kwargs):
        return _gdi_.DC_CanGetTextExtent(*args, **kwargs)

    def GetDepth(*args, **kwargs):
        return _gdi_.DC_GetDepth(*args, **kwargs)

    def GetPPI(*args, **kwargs):
        return _gdi_.DC_GetPPI(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _gdi_.DC_IsOk(*args, **kwargs)

    Ok = IsOk

    def GetBackgroundMode(*args, **kwargs):
        return _gdi_.DC_GetBackgroundMode(*args, **kwargs)

    def GetBackground(*args, **kwargs):
        return _gdi_.DC_GetBackground(*args, **kwargs)

    def GetBrush(*args, **kwargs):
        return _gdi_.DC_GetBrush(*args, **kwargs)

    def GetFont(*args, **kwargs):
        return _gdi_.DC_GetFont(*args, **kwargs)

    def GetPen(*args, **kwargs):
        return _gdi_.DC_GetPen(*args, **kwargs)

    def GetTextBackground(*args, **kwargs):
        return _gdi_.DC_GetTextBackground(*args, **kwargs)

    def GetTextForeground(*args, **kwargs):
        return _gdi_.DC_GetTextForeground(*args, **kwargs)

    def SetTextForeground(*args, **kwargs):
        return _gdi_.DC_SetTextForeground(*args, **kwargs)

    def SetTextBackground(*args, **kwargs):
        return _gdi_.DC_SetTextBackground(*args, **kwargs)

    def GetMapMode(*args, **kwargs):
        return _gdi_.DC_GetMapMode(*args, **kwargs)

    def SetMapMode(*args, **kwargs):
        return _gdi_.DC_SetMapMode(*args, **kwargs)

    def GetUserScale(*args, **kwargs):
        return _gdi_.DC_GetUserScale(*args, **kwargs)

    def SetUserScale(*args, **kwargs):
        return _gdi_.DC_SetUserScale(*args, **kwargs)

    def GetLogicalScale(*args, **kwargs):
        return _gdi_.DC_GetLogicalScale(*args, **kwargs)

    def SetLogicalScale(*args, **kwargs):
        return _gdi_.DC_SetLogicalScale(*args, **kwargs)

    def GetLogicalOrigin(*args, **kwargs):
        return _gdi_.DC_GetLogicalOrigin(*args, **kwargs)

    def GetLogicalOriginTuple(*args, **kwargs):
        return _gdi_.DC_GetLogicalOriginTuple(*args, **kwargs)

    def SetLogicalOrigin(*args, **kwargs):
        return _gdi_.DC_SetLogicalOrigin(*args, **kwargs)

    def SetLogicalOriginPoint(*args, **kwargs):
        return _gdi_.DC_SetLogicalOriginPoint(*args, **kwargs)

    def GetDeviceOrigin(*args, **kwargs):
        return _gdi_.DC_GetDeviceOrigin(*args, **kwargs)

    def GetDeviceOriginTuple(*args, **kwargs):
        return _gdi_.DC_GetDeviceOriginTuple(*args, **kwargs)

    def SetDeviceOrigin(*args, **kwargs):
        return _gdi_.DC_SetDeviceOrigin(*args, **kwargs)

    def SetDeviceOriginPoint(*args, **kwargs):
        return _gdi_.DC_SetDeviceOriginPoint(*args, **kwargs)

    def SetAxisOrientation(*args, **kwargs):
        return _gdi_.DC_SetAxisOrientation(*args, **kwargs)

    def GetLogicalFunction(*args, **kwargs):
        return _gdi_.DC_GetLogicalFunction(*args, **kwargs)

    def SetLogicalFunction(*args, **kwargs):
        return _gdi_.DC_SetLogicalFunction(*args, **kwargs)

    def ComputeScaleAndOrigin(*args, **kwargs):
        return _gdi_.DC_ComputeScaleAndOrigin(*args, **kwargs)

    def SetOptimization(self, optimize):
        pass

    def GetOptimization(self):
        return False

    SetOptimization = wx._deprecated(SetOptimization)
    GetOptimization = wx._deprecated(GetOptimization)

    def CalcBoundingBox(*args, **kwargs):
        return _gdi_.DC_CalcBoundingBox(*args, **kwargs)

    def CalcBoundingBoxPoint(*args, **kwargs):
        return _gdi_.DC_CalcBoundingBoxPoint(*args, **kwargs)

    def ResetBoundingBox(*args, **kwargs):
        return _gdi_.DC_ResetBoundingBox(*args, **kwargs)

    def MinX(*args, **kwargs):
        return _gdi_.DC_MinX(*args, **kwargs)

    def MaxX(*args, **kwargs):
        return _gdi_.DC_MaxX(*args, **kwargs)

    def MinY(*args, **kwargs):
        return _gdi_.DC_MinY(*args, **kwargs)

    def MaxY(*args, **kwargs):
        return _gdi_.DC_MaxY(*args, **kwargs)

    def GetBoundingBox(*args, **kwargs):
        return _gdi_.DC_GetBoundingBox(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def GetLayoutDirection(*args, **kwargs):
        return _gdi_.DC_GetLayoutDirection(*args, **kwargs)

    def SetLayoutDirection(*args, **kwargs):
        return _gdi_.DC_SetLayoutDirection(*args, **kwargs)

    def GetGdkDrawable(*args, **kwargs):
        return _gdi_.DC_GetGdkDrawable(*args, **kwargs)

    def _DrawPointList(*args, **kwargs):
        return _gdi_.DC__DrawPointList(*args, **kwargs)

    def _DrawLineList(*args, **kwargs):
        return _gdi_.DC__DrawLineList(*args, **kwargs)

    def _DrawRectangleList(*args, **kwargs):
        return _gdi_.DC__DrawRectangleList(*args, **kwargs)

    def _DrawEllipseList(*args, **kwargs):
        return _gdi_.DC__DrawEllipseList(*args, **kwargs)

    def _DrawPolygonList(*args, **kwargs):
        return _gdi_.DC__DrawPolygonList(*args, **kwargs)

    def _DrawTextList(*args, **kwargs):
        return _gdi_.DC__DrawTextList(*args, **kwargs)

    def DrawPointList(self, points, pens = None):
        if pens is None:
            pens = []
        elif isinstance(pens, wx.Pen):
            pens = [pens]
        elif len(pens) != len(points):
            raise ValueError('points and pens must have same length')
        return self._DrawPointList(points, pens, [])

    def DrawLineList(self, lines, pens = None):
        if pens is None:
            pens = []
        elif isinstance(pens, wx.Pen):
            pens = [pens]
        elif len(pens) != len(lines):
            raise ValueError('lines and pens must have same length')
        return self._DrawLineList(lines, pens, [])

    def DrawRectangleList(self, rectangles, pens = None, brushes = None):
        if pens is None:
            pens = []
        elif isinstance(pens, wx.Pen):
            pens = [pens]
        elif len(pens) != len(rectangles):
            raise ValueError('rectangles and pens must have same length')
        if brushes is None:
            brushes = []
        elif isinstance(brushes, wx.Brush):
            brushes = [brushes]
        elif len(brushes) != len(rectangles):
            raise ValueError('rectangles and brushes must have same length')
        return self._DrawRectangleList(rectangles, pens, brushes)

    def DrawEllipseList(self, ellipses, pens = None, brushes = None):
        if pens is None:
            pens = []
        elif isinstance(pens, wx.Pen):
            pens = [pens]
        elif len(pens) != len(ellipses):
            raise ValueError('ellipses and pens must have same length')
        if brushes is None:
            brushes = []
        elif isinstance(brushes, wx.Brush):
            brushes = [brushes]
        elif len(brushes) != len(ellipses):
            raise ValueError('ellipses and brushes must have same length')
        return self._DrawEllipseList(ellipses, pens, brushes)

    def DrawPolygonList(self, polygons, pens = None, brushes = None):
        if pens is None:
            pens = []
        elif isinstance(pens, wx.Pen):
            pens = [pens]
        elif len(pens) != len(polygons):
            raise ValueError('polygons and pens must have same length')
        if brushes is None:
            brushes = []
        elif isinstance(brushes, wx.Brush):
            brushes = [brushes]
        elif len(brushes) != len(polygons):
            raise ValueError('polygons and brushes must have same length')
        return self._DrawPolygonList(polygons, pens, brushes)

    def DrawTextList(self, textList, coords, foregrounds = None, backgrounds = None):
        if type(textList) == type(''):
            textList = [textList]
        elif len(textList) != len(coords):
            raise ValueError('textlist and coords must have same length')
        if foregrounds is None:
            foregrounds = []
        elif isinstance(foregrounds, wx.Colour):
            foregrounds = [foregrounds]
        elif len(foregrounds) != len(coords):
            raise ValueError('foregrounds and coords must have same length')
        if backgrounds is None:
            backgrounds = []
        elif isinstance(backgrounds, wx.Colour):
            backgrounds = [backgrounds]
        elif len(backgrounds) != len(coords):
            raise ValueError('backgrounds and coords must have same length')
        return self._DrawTextList(textList, coords, foregrounds, backgrounds)

    Background = property(GetBackground, SetBackground, doc='See `GetBackground` and `SetBackground`')
    BackgroundMode = property(GetBackgroundMode, SetBackgroundMode, doc='See `GetBackgroundMode` and `SetBackgroundMode`')
    BoundingBox = property(GetBoundingBox, doc='See `GetBoundingBox`')
    Brush = property(GetBrush, SetBrush, doc='See `GetBrush` and `SetBrush`')
    CharHeight = property(GetCharHeight, doc='See `GetCharHeight`')
    CharWidth = property(GetCharWidth, doc='See `GetCharWidth`')
    ClippingBox = property(GetClippingBox, doc='See `GetClippingBox`')
    ClippingRect = property(GetClippingRect, SetClippingRect, doc='See `GetClippingRect` and `SetClippingRect`')
    Depth = property(GetDepth, doc='See `GetDepth`')
    DeviceOrigin = property(GetDeviceOrigin, SetDeviceOrigin, doc='See `GetDeviceOrigin` and `SetDeviceOrigin`')
    Font = property(GetFont, SetFont, doc='See `GetFont` and `SetFont`')
    FullTextExtent = property(GetFullTextExtent, doc='See `GetFullTextExtent`')
    LogicalFunction = property(GetLogicalFunction, SetLogicalFunction, doc='See `GetLogicalFunction` and `SetLogicalFunction`')
    LogicalOrigin = property(GetLogicalOrigin, SetLogicalOrigin, doc='See `GetLogicalOrigin` and `SetLogicalOrigin`')
    LogicalScale = property(GetLogicalScale, SetLogicalScale, doc='See `GetLogicalScale` and `SetLogicalScale`')
    MapMode = property(GetMapMode, SetMapMode, doc='See `GetMapMode` and `SetMapMode`')
    MultiLineTextExtent = property(GetMultiLineTextExtent, doc='See `GetMultiLineTextExtent`')
    Optimization = property(GetOptimization, SetOptimization, doc='See `GetOptimization` and `SetOptimization`')
    PPI = property(GetPPI, doc='See `GetPPI`')
    PartialTextExtents = property(GetPartialTextExtents, doc='See `GetPartialTextExtents`')
    Pen = property(GetPen, SetPen, doc='See `GetPen` and `SetPen`')
    Pixel = property(GetPixel, doc='See `GetPixel`')
    PixelPoint = property(GetPixelPoint, doc='See `GetPixelPoint`')
    Size = property(GetSize, doc='See `GetSize`')
    SizeMM = property(GetSizeMM, doc='See `GetSizeMM`')
    TextBackground = property(GetTextBackground, SetTextBackground, doc='See `GetTextBackground` and `SetTextBackground`')
    TextExtent = property(GetTextExtent, doc='See `GetTextExtent`')
    TextForeground = property(GetTextForeground, SetTextForeground, doc='See `GetTextForeground` and `SetTextForeground`')
    UserScale = property(GetUserScale, SetUserScale, doc='See `GetUserScale` and `SetUserScale`')
    LayoutDirection = property(GetLayoutDirection, SetLayoutDirection)


_gdi_.DC_swigregister(DC)

class DCTextColourChanger(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.DCTextColourChanger_swiginit(self, _gdi_.new_DCTextColourChanger(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_DCTextColourChanger
    __del__ = lambda self: None


_gdi_.DCTextColourChanger_swigregister(DCTextColourChanger)

class DCPenChanger(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.DCPenChanger_swiginit(self, _gdi_.new_DCPenChanger(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_DCPenChanger
    __del__ = lambda self: None


_gdi_.DCPenChanger_swigregister(DCPenChanger)

class DCBrushChanger(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.DCBrushChanger_swiginit(self, _gdi_.new_DCBrushChanger(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_DCBrushChanger
    __del__ = lambda self: None


_gdi_.DCBrushChanger_swigregister(DCBrushChanger)

class DCClipper(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.DCClipper_swiginit(self, _gdi_.new_DCClipper(*args))

    __swig_destroy__ = _gdi_.delete_DCClipper
    __del__ = lambda self: None


_gdi_.DCClipper_swigregister(DCClipper)

class ScreenDC(DC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.ScreenDC_swiginit(self, _gdi_.new_ScreenDC(*args, **kwargs))

    def StartDrawingOnTopWin(*args, **kwargs):
        return _gdi_.ScreenDC_StartDrawingOnTopWin(*args, **kwargs)

    def StartDrawingOnTop(*args, **kwargs):
        return _gdi_.ScreenDC_StartDrawingOnTop(*args, **kwargs)

    def EndDrawingOnTop(*args, **kwargs):
        return _gdi_.ScreenDC_EndDrawingOnTop(*args, **kwargs)


_gdi_.ScreenDC_swigregister(ScreenDC)

class WindowDC(DC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.WindowDC_swiginit(self, _gdi_.new_WindowDC(*args, **kwargs))


_gdi_.WindowDC_swigregister(WindowDC)

class ClientDC(WindowDC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.ClientDC_swiginit(self, _gdi_.new_ClientDC(*args, **kwargs))


_gdi_.ClientDC_swigregister(ClientDC)

class PaintDC(ClientDC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.PaintDC_swiginit(self, _gdi_.new_PaintDC(*args, **kwargs))


_gdi_.PaintDC_swigregister(PaintDC)

class MemoryDC(WindowDC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.MemoryDC_swiginit(self, _gdi_.new_MemoryDC(*args, **kwargs))

    def SelectObject(*args, **kwargs):
        return _gdi_.MemoryDC_SelectObject(*args, **kwargs)

    def SelectObjectAsSource(*args, **kwargs):
        return _gdi_.MemoryDC_SelectObjectAsSource(*args, **kwargs)


_gdi_.MemoryDC_swigregister(MemoryDC)

def MemoryDCFromDC(*args, **kwargs):
    val = _gdi_.new_MemoryDCFromDC(*args, **kwargs)
    return val


BUFFER_VIRTUAL_AREA = _gdi_.BUFFER_VIRTUAL_AREA
BUFFER_CLIENT_AREA = _gdi_.BUFFER_CLIENT_AREA

class BufferedDC(MemoryDC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.BufferedDC_swiginit(self, _gdi_.new_BufferedDC(*args))
        self.__dc = args[0]
        if len(args) > 1:
            self.__bmp = args[1]

    __swig_destroy__ = _gdi_.delete_BufferedDC
    __del__ = lambda self: None

    def UnMask(*args, **kwargs):
        return _gdi_.BufferedDC_UnMask(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _gdi_.BufferedDC_SetStyle(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _gdi_.BufferedDC_GetStyle(*args, **kwargs)


_gdi_.BufferedDC_swigregister(BufferedDC)

class BufferedPaintDC(BufferedDC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.BufferedPaintDC_swiginit(self, _gdi_.new_BufferedPaintDC(*args, **kwargs))
        if len(args) > 1:
            self.__bmp = args[1]


_gdi_.BufferedPaintDC_swigregister(BufferedPaintDC)

class AutoBufferedPaintDC(DC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.AutoBufferedPaintDC_swiginit(self, _gdi_.new_AutoBufferedPaintDC(*args, **kwargs))


_gdi_.AutoBufferedPaintDC_swigregister(AutoBufferedPaintDC)

def AutoBufferedPaintDCFactory(*args, **kwargs):
    return _gdi_.AutoBufferedPaintDCFactory(*args, **kwargs)


class MirrorDC(DC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.MirrorDC_swiginit(self, _gdi_.new_MirrorDC(*args, **kwargs))


_gdi_.MirrorDC_swigregister(MirrorDC)

class MetaFile(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.MetaFile_swiginit(self, _gdi_.new_MetaFile(*args, **kwargs))


_gdi_.MetaFile_swigregister(MetaFile)

class MetaFileDC(DC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.MetaFileDC_swiginit(self, _gdi_.new_MetaFileDC(*args, **kwargs))


_gdi_.MetaFileDC_swigregister(MetaFileDC)

class GraphicsObject(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.GraphicsObject_swiginit(self, _gdi_.new_GraphicsObject(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_GraphicsObject
    __del__ = lambda self: None

    def IsNull(*args, **kwargs):
        return _gdi_.GraphicsObject_IsNull(*args, **kwargs)

    def GetRenderer(*args, **kwargs):
        return _gdi_.GraphicsObject_GetRenderer(*args, **kwargs)


_gdi_.GraphicsObject_swigregister(GraphicsObject)

class GraphicsPen(GraphicsObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.GraphicsPen_swiginit(self, _gdi_.new_GraphicsPen(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_GraphicsPen
    __del__ = lambda self: None


_gdi_.GraphicsPen_swigregister(GraphicsPen)

class GraphicsBrush(GraphicsObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.GraphicsBrush_swiginit(self, _gdi_.new_GraphicsBrush(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_GraphicsBrush
    __del__ = lambda self: None


_gdi_.GraphicsBrush_swigregister(GraphicsBrush)

class GraphicsFont(GraphicsObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.GraphicsFont_swiginit(self, _gdi_.new_GraphicsFont(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_GraphicsFont
    __del__ = lambda self: None


_gdi_.GraphicsFont_swigregister(GraphicsFont)

class GraphicsMatrix(GraphicsObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _gdi_.delete_GraphicsMatrix
    __del__ = lambda self: None

    def Concat(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Concat(*args, **kwargs)

    def Set(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Get(*args, **kwargs)

    def Invert(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Invert(*args, **kwargs)

    def IsEqual(*args, **kwargs):
        return _gdi_.GraphicsMatrix_IsEqual(*args, **kwargs)

    def IsIdentity(*args, **kwargs):
        return _gdi_.GraphicsMatrix_IsIdentity(*args, **kwargs)

    def Translate(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Translate(*args, **kwargs)

    def Scale(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Scale(*args, **kwargs)

    def Rotate(*args, **kwargs):
        return _gdi_.GraphicsMatrix_Rotate(*args, **kwargs)

    def TransformPoint(*args, **kwargs):
        return _gdi_.GraphicsMatrix_TransformPoint(*args, **kwargs)

    def TransformDistance(*args, **kwargs):
        return _gdi_.GraphicsMatrix_TransformDistance(*args, **kwargs)

    def GetNativeMatrix(*args, **kwargs):
        return _gdi_.GraphicsMatrix_GetNativeMatrix(*args, **kwargs)


_gdi_.GraphicsMatrix_swigregister(GraphicsMatrix)

class GraphicsPath(GraphicsObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _gdi_.delete_GraphicsPath
    __del__ = lambda self: None

    def MoveToPoint(*args):
        return _gdi_.GraphicsPath_MoveToPoint(*args)

    def AddLineToPoint(*args):
        return _gdi_.GraphicsPath_AddLineToPoint(*args)

    def AddCurveToPoint(*args):
        return _gdi_.GraphicsPath_AddCurveToPoint(*args)

    def AddPath(*args, **kwargs):
        return _gdi_.GraphicsPath_AddPath(*args, **kwargs)

    def CloseSubpath(*args, **kwargs):
        return _gdi_.GraphicsPath_CloseSubpath(*args, **kwargs)

    def GetCurrentPoint(*args, **kwargs):
        return _gdi_.GraphicsPath_GetCurrentPoint(*args, **kwargs)

    def AddArc(*args):
        return _gdi_.GraphicsPath_AddArc(*args)

    def AddQuadCurveToPoint(*args, **kwargs):
        return _gdi_.GraphicsPath_AddQuadCurveToPoint(*args, **kwargs)

    def AddRectangle(*args, **kwargs):
        return _gdi_.GraphicsPath_AddRectangle(*args, **kwargs)

    def AddCircle(*args, **kwargs):
        return _gdi_.GraphicsPath_AddCircle(*args, **kwargs)

    def AddArcToPoint(*args, **kwargs):
        return _gdi_.GraphicsPath_AddArcToPoint(*args, **kwargs)

    def AddEllipse(*args, **kwargs):
        return _gdi_.GraphicsPath_AddEllipse(*args, **kwargs)

    def AddRoundedRectangle(*args, **kwargs):
        return _gdi_.GraphicsPath_AddRoundedRectangle(*args, **kwargs)

    def GetNativePath(*args, **kwargs):
        return _gdi_.GraphicsPath_GetNativePath(*args, **kwargs)

    def UnGetNativePath(*args, **kwargs):
        return _gdi_.GraphicsPath_UnGetNativePath(*args, **kwargs)

    def Transform(*args, **kwargs):
        return _gdi_.GraphicsPath_Transform(*args, **kwargs)

    def GetBox(*args, **kwargs):
        return _gdi_.GraphicsPath_GetBox(*args, **kwargs)

    def Contains(*args):
        return _gdi_.GraphicsPath_Contains(*args)


_gdi_.GraphicsPath_swigregister(GraphicsPath)

class GraphicsContext(GraphicsObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _gdi_.delete_GraphicsContext
    __del__ = lambda self: None

    def Create(*args):
        val = _gdi_.GraphicsContext_Create(*args)
        val.__dc = args[0]
        return val

    Create = staticmethod(Create)

    def CreateMeasuringContext(*args):
        return _gdi_.GraphicsContext_CreateMeasuringContext(*args)

    CreateMeasuringContext = staticmethod(CreateMeasuringContext)

    def CreateFromNative(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateFromNative(*args, **kwargs)

    CreateFromNative = staticmethod(CreateFromNative)

    def CreateFromNativeWindow(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateFromNativeWindow(*args, **kwargs)

    CreateFromNativeWindow = staticmethod(CreateFromNativeWindow)

    def CreatePath(*args, **kwargs):
        return _gdi_.GraphicsContext_CreatePath(*args, **kwargs)

    def CreatePen(*args, **kwargs):
        return _gdi_.GraphicsContext_CreatePen(*args, **kwargs)

    def CreateBrush(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateBrush(*args, **kwargs)

    def CreateLinearGradientBrush(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateLinearGradientBrush(*args, **kwargs)

    def CreateRadialGradientBrush(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateRadialGradientBrush(*args, **kwargs)

    def CreateFont(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateFont(*args, **kwargs)

    def CreateMatrix(*args, **kwargs):
        return _gdi_.GraphicsContext_CreateMatrix(*args, **kwargs)

    def PushState(*args, **kwargs):
        return _gdi_.GraphicsContext_PushState(*args, **kwargs)

    def PopState(*args, **kwargs):
        return _gdi_.GraphicsContext_PopState(*args, **kwargs)

    def ClipRegion(*args, **kwargs):
        return _gdi_.GraphicsContext_ClipRegion(*args, **kwargs)

    def Clip(*args, **kwargs):
        return _gdi_.GraphicsContext_Clip(*args, **kwargs)

    def ResetClip(*args, **kwargs):
        return _gdi_.GraphicsContext_ResetClip(*args, **kwargs)

    def GetNativeContext(*args, **kwargs):
        return _gdi_.GraphicsContext_GetNativeContext(*args, **kwargs)

    def GetLogicalFunction(*args, **kwargs):
        return _gdi_.GraphicsContext_GetLogicalFunction(*args, **kwargs)

    def SetLogicalFunction(*args, **kwargs):
        return _gdi_.GraphicsContext_SetLogicalFunction(*args, **kwargs)

    def Translate(*args, **kwargs):
        return _gdi_.GraphicsContext_Translate(*args, **kwargs)

    def Scale(*args, **kwargs):
        return _gdi_.GraphicsContext_Scale(*args, **kwargs)

    def Rotate(*args, **kwargs):
        return _gdi_.GraphicsContext_Rotate(*args, **kwargs)

    def ConcatTransform(*args, **kwargs):
        return _gdi_.GraphicsContext_ConcatTransform(*args, **kwargs)

    def SetTransform(*args, **kwargs):
        return _gdi_.GraphicsContext_SetTransform(*args, **kwargs)

    def GetTransform(*args, **kwargs):
        return _gdi_.GraphicsContext_GetTransform(*args, **kwargs)

    def SetPen(*args):
        return _gdi_.GraphicsContext_SetPen(*args)

    def SetBrush(*args):
        return _gdi_.GraphicsContext_SetBrush(*args)

    def SetFont(*args):
        return _gdi_.GraphicsContext_SetFont(*args)

    def StrokePath(*args, **kwargs):
        return _gdi_.GraphicsContext_StrokePath(*args, **kwargs)

    def FillPath(*args, **kwargs):
        return _gdi_.GraphicsContext_FillPath(*args, **kwargs)

    def DrawPath(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawPath(*args, **kwargs)

    def DrawText(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawText(*args, **kwargs)

    def DrawRotatedText(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawRotatedText(*args, **kwargs)

    def GetFullTextExtent(*args, **kwargs):
        return _gdi_.GraphicsContext_GetFullTextExtent(*args, **kwargs)

    def GetTextExtent(*args, **kwargs):
        return _gdi_.GraphicsContext_GetTextExtent(*args, **kwargs)

    def GetPartialTextExtents(*args, **kwargs):
        return _gdi_.GraphicsContext_GetPartialTextExtents(*args, **kwargs)

    def DrawBitmap(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawBitmap(*args, **kwargs)

    def DrawIcon(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawIcon(*args, **kwargs)

    def StrokeLine(*args, **kwargs):
        return _gdi_.GraphicsContext_StrokeLine(*args, **kwargs)

    def StrokeLines(*args, **kwargs):
        return _gdi_.GraphicsContext_StrokeLines(*args, **kwargs)

    def StrokeLineSegements(*args, **kwargs):
        return _gdi_.GraphicsContext_StrokeLineSegements(*args, **kwargs)

    def DrawLines(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawLines(*args, **kwargs)

    def DrawRectangle(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawRectangle(*args, **kwargs)

    def DrawEllipse(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawEllipse(*args, **kwargs)

    def DrawRoundedRectangle(*args, **kwargs):
        return _gdi_.GraphicsContext_DrawRoundedRectangle(*args, **kwargs)

    def ShouldOffset(*args, **kwargs):
        return _gdi_.GraphicsContext_ShouldOffset(*args, **kwargs)


_gdi_.GraphicsContext_swigregister(GraphicsContext)
cvar = _gdi_.cvar
NullGraphicsPen = cvar.NullGraphicsPen
NullGraphicsBrush = cvar.NullGraphicsBrush
NullGraphicsFont = cvar.NullGraphicsFont
NullGraphicsMatrix = cvar.NullGraphicsMatrix
NullGraphicsPath = cvar.NullGraphicsPath

def GraphicsContext_Create(*args):
    val = _gdi_.GraphicsContext_Create(*args)
    val.__dc = args[0]
    return val


def GraphicsContext_CreateMeasuringContext(*args):
    return _gdi_.GraphicsContext_CreateMeasuringContext(*args)


def GraphicsContext_CreateFromNative(*args, **kwargs):
    return _gdi_.GraphicsContext_CreateFromNative(*args, **kwargs)


def GraphicsContext_CreateFromNativeWindow(*args, **kwargs):
    return _gdi_.GraphicsContext_CreateFromNativeWindow(*args, **kwargs)


class GraphicsRenderer(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _gdi_.delete_GraphicsRenderer
    __del__ = lambda self: None

    def GetDefaultRenderer(*args, **kwargs):
        return _gdi_.GraphicsRenderer_GetDefaultRenderer(*args, **kwargs)

    GetDefaultRenderer = staticmethod(GetDefaultRenderer)

    def CreateContext(*args):
        return _gdi_.GraphicsRenderer_CreateContext(*args)

    def CreateMeasuringContext(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateMeasuringContext(*args, **kwargs)

    def CreateContextFromNativeContext(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateContextFromNativeContext(*args, **kwargs)

    def CreateContextFromNativeWindow(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateContextFromNativeWindow(*args, **kwargs)

    def CreatePath(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreatePath(*args, **kwargs)

    def CreateMatrix(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateMatrix(*args, **kwargs)

    def CreatePen(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreatePen(*args, **kwargs)

    def CreateBrush(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateBrush(*args, **kwargs)

    def CreateLinearGradientBrush(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateLinearGradientBrush(*args, **kwargs)

    def CreateRadialGradientBrush(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateRadialGradientBrush(*args, **kwargs)

    def CreateFont(*args, **kwargs):
        return _gdi_.GraphicsRenderer_CreateFont(*args, **kwargs)


_gdi_.GraphicsRenderer_swigregister(GraphicsRenderer)

def GraphicsRenderer_GetDefaultRenderer(*args):
    return _gdi_.GraphicsRenderer_GetDefaultRenderer(*args)


class GCDC(DC):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.GCDC_swiginit(self, _gdi_.new_GCDC(*args))
        self.__dc = args[0]

    __swig_destroy__ = _gdi_.delete_GCDC
    __del__ = lambda self: None

    def GetGraphicsContext(*args, **kwargs):
        return _gdi_.GCDC_GetGraphicsContext(*args, **kwargs)

    def SetGraphicsContext(*args, **kwargs):
        return _gdi_.GCDC_SetGraphicsContext(*args, **kwargs)

    def Flush(*args, **kwargs):
        return _gdi_.GCDC_Flush(*args, **kwargs)

    GraphicsContext = property(GetGraphicsContext, SetGraphicsContext)


_gdi_.GCDC_swigregister(GCDC)

class Overlay(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Overlay_swiginit(self, _gdi_.new_Overlay(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_Overlay
    __del__ = lambda self: None

    def Reset(*args, **kwargs):
        return _gdi_.Overlay_Reset(*args, **kwargs)


_gdi_.Overlay_swigregister(Overlay)

class DCOverlay(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _gdi_.DCOverlay_swiginit(self, _gdi_.new_DCOverlay(*args))
        self.__dc = args[1]

    __swig_destroy__ = _gdi_.delete_DCOverlay
    __del__ = lambda self: None

    def Clear(*args, **kwargs):
        return _gdi_.DCOverlay_Clear(*args, **kwargs)


_gdi_.DCOverlay_swigregister(DCOverlay)
IMAGELIST_DRAW_NORMAL = _gdi_.IMAGELIST_DRAW_NORMAL
IMAGELIST_DRAW_TRANSPARENT = _gdi_.IMAGELIST_DRAW_TRANSPARENT
IMAGELIST_DRAW_SELECTED = _gdi_.IMAGELIST_DRAW_SELECTED
IMAGELIST_DRAW_FOCUSED = _gdi_.IMAGELIST_DRAW_FOCUSED
IMAGE_LIST_NORMAL = _gdi_.IMAGE_LIST_NORMAL
IMAGE_LIST_SMALL = _gdi_.IMAGE_LIST_SMALL
IMAGE_LIST_STATE = _gdi_.IMAGE_LIST_STATE

class ImageList(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.ImageList_swiginit(self, _gdi_.new_ImageList(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_ImageList
    __del__ = lambda self: None

    def Add(*args, **kwargs):
        return _gdi_.ImageList_Add(*args, **kwargs)

    def AddWithColourMask(*args, **kwargs):
        return _gdi_.ImageList_AddWithColourMask(*args, **kwargs)

    def AddIcon(*args, **kwargs):
        return _gdi_.ImageList_AddIcon(*args, **kwargs)

    def GetBitmap(*args, **kwargs):
        return _gdi_.ImageList_GetBitmap(*args, **kwargs)

    def GetIcon(*args, **kwargs):
        return _gdi_.ImageList_GetIcon(*args, **kwargs)

    def Replace(*args, **kwargs):
        return _gdi_.ImageList_Replace(*args, **kwargs)

    def Draw(*args, **kwargs):
        return _gdi_.ImageList_Draw(*args, **kwargs)

    def GetImageCount(*args, **kwargs):
        return _gdi_.ImageList_GetImageCount(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _gdi_.ImageList_Remove(*args, **kwargs)

    def RemoveAll(*args, **kwargs):
        return _gdi_.ImageList_RemoveAll(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _gdi_.ImageList_GetSize(*args, **kwargs)

    ImageCount = property(GetImageCount, doc='See `GetImageCount`')
    Size = property(GetSize, doc='See `GetSize`')


_gdi_.ImageList_swigregister(ImageList)

class StockGDI(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    BRUSH_BLACK = _gdi_.StockGDI_BRUSH_BLACK
    BRUSH_BLUE = _gdi_.StockGDI_BRUSH_BLUE
    BRUSH_CYAN = _gdi_.StockGDI_BRUSH_CYAN
    BRUSH_GREEN = _gdi_.StockGDI_BRUSH_GREEN
    BRUSH_GREY = _gdi_.StockGDI_BRUSH_GREY
    BRUSH_LIGHTGREY = _gdi_.StockGDI_BRUSH_LIGHTGREY
    BRUSH_MEDIUMGREY = _gdi_.StockGDI_BRUSH_MEDIUMGREY
    BRUSH_RED = _gdi_.StockGDI_BRUSH_RED
    BRUSH_TRANSPARENT = _gdi_.StockGDI_BRUSH_TRANSPARENT
    BRUSH_WHITE = _gdi_.StockGDI_BRUSH_WHITE
    COLOUR_BLACK = _gdi_.StockGDI_COLOUR_BLACK
    COLOUR_BLUE = _gdi_.StockGDI_COLOUR_BLUE
    COLOUR_CYAN = _gdi_.StockGDI_COLOUR_CYAN
    COLOUR_GREEN = _gdi_.StockGDI_COLOUR_GREEN
    COLOUR_LIGHTGREY = _gdi_.StockGDI_COLOUR_LIGHTGREY
    COLOUR_RED = _gdi_.StockGDI_COLOUR_RED
    COLOUR_WHITE = _gdi_.StockGDI_COLOUR_WHITE
    CURSOR_CROSS = _gdi_.StockGDI_CURSOR_CROSS
    CURSOR_HOURGLASS = _gdi_.StockGDI_CURSOR_HOURGLASS
    CURSOR_STANDARD = _gdi_.StockGDI_CURSOR_STANDARD
    FONT_ITALIC = _gdi_.StockGDI_FONT_ITALIC
    FONT_NORMAL = _gdi_.StockGDI_FONT_NORMAL
    FONT_SMALL = _gdi_.StockGDI_FONT_SMALL
    FONT_SWISS = _gdi_.StockGDI_FONT_SWISS
    PEN_BLACK = _gdi_.StockGDI_PEN_BLACK
    PEN_BLACKDASHED = _gdi_.StockGDI_PEN_BLACKDASHED
    PEN_CYAN = _gdi_.StockGDI_PEN_CYAN
    PEN_GREEN = _gdi_.StockGDI_PEN_GREEN
    PEN_GREY = _gdi_.StockGDI_PEN_GREY
    PEN_LIGHTGREY = _gdi_.StockGDI_PEN_LIGHTGREY
    PEN_MEDIUMGREY = _gdi_.StockGDI_PEN_MEDIUMGREY
    PEN_RED = _gdi_.StockGDI_PEN_RED
    PEN_TRANSPARENT = _gdi_.StockGDI_PEN_TRANSPARENT
    PEN_WHITE = _gdi_.StockGDI_PEN_WHITE
    ITEMCOUNT = _gdi_.StockGDI_ITEMCOUNT

    def __init__(self, *args, **kwargs):
        _gdi_.StockGDI_swiginit(self, _gdi_.new_StockGDI(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_StockGDI
    __del__ = lambda self: None

    def DeleteAll(*args, **kwargs):
        return _gdi_.StockGDI_DeleteAll(*args, **kwargs)

    DeleteAll = staticmethod(DeleteAll)

    def instance(*args, **kwargs):
        return _gdi_.StockGDI_instance(*args, **kwargs)

    instance = staticmethod(instance)

    def GetBrush(*args, **kwargs):
        return _gdi_.StockGDI_GetBrush(*args, **kwargs)

    GetBrush = staticmethod(GetBrush)

    def GetColour(*args, **kwargs):
        return _gdi_.StockGDI_GetColour(*args, **kwargs)

    GetColour = staticmethod(GetColour)

    def GetCursor(*args, **kwargs):
        return _gdi_.StockGDI_GetCursor(*args, **kwargs)

    GetCursor = staticmethod(GetCursor)

    def GetPen(*args, **kwargs):
        return _gdi_.StockGDI_GetPen(*args, **kwargs)

    GetPen = staticmethod(GetPen)

    def GetFont(*args, **kwargs):
        return _gdi_.StockGDI_GetFont(*args, **kwargs)

    def _initStockObjects():
        import wx
        wx.ITALIC_FONT.this = StockGDI.instance().GetFont(StockGDI.FONT_ITALIC).this
        wx.NORMAL_FONT.this = StockGDI.instance().GetFont(StockGDI.FONT_NORMAL).this
        wx.SMALL_FONT.this = StockGDI.instance().GetFont(StockGDI.FONT_SMALL).this
        wx.SWISS_FONT.this = StockGDI.instance().GetFont(StockGDI.FONT_SWISS).this
        wx.BLACK_DASHED_PEN.this = StockGDI.GetPen(StockGDI.PEN_BLACKDASHED).this
        wx.BLACK_PEN.this = StockGDI.GetPen(StockGDI.PEN_BLACK).this
        wx.CYAN_PEN.this = StockGDI.GetPen(StockGDI.PEN_CYAN).this
        wx.GREEN_PEN.this = StockGDI.GetPen(StockGDI.PEN_GREEN).this
        wx.GREY_PEN.this = StockGDI.GetPen(StockGDI.PEN_GREY).this
        wx.LIGHT_GREY_PEN.this = StockGDI.GetPen(StockGDI.PEN_LIGHTGREY).this
        wx.MEDIUM_GREY_PEN.this = StockGDI.GetPen(StockGDI.PEN_MEDIUMGREY).this
        wx.RED_PEN.this = StockGDI.GetPen(StockGDI.PEN_RED).this
        wx.TRANSPARENT_PEN.this = StockGDI.GetPen(StockGDI.PEN_TRANSPARENT).this
        wx.WHITE_PEN.this = StockGDI.GetPen(StockGDI.PEN_WHITE).this
        wx.BLACK_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_BLACK).this
        wx.BLUE_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_BLUE).this
        wx.CYAN_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_CYAN).this
        wx.GREEN_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_GREEN).this
        wx.GREY_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_GREY).this
        wx.LIGHT_GREY_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_LIGHTGREY).this
        wx.MEDIUM_GREY_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_MEDIUMGREY).this
        wx.RED_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_RED).this
        wx.TRANSPARENT_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_TRANSPARENT).this
        wx.WHITE_BRUSH.this = StockGDI.GetBrush(StockGDI.BRUSH_WHITE).this
        wx.BLACK.this = StockGDI.GetColour(StockGDI.COLOUR_BLACK).this
        wx.BLUE.this = StockGDI.GetColour(StockGDI.COLOUR_BLUE).this
        wx.CYAN.this = StockGDI.GetColour(StockGDI.COLOUR_CYAN).this
        wx.GREEN.this = StockGDI.GetColour(StockGDI.COLOUR_GREEN).this
        wx.LIGHT_GREY.this = StockGDI.GetColour(StockGDI.COLOUR_LIGHTGREY).this
        wx.RED.this = StockGDI.GetColour(StockGDI.COLOUR_RED).this
        wx.WHITE.this = StockGDI.GetColour(StockGDI.COLOUR_WHITE).this
        wx.CROSS_CURSOR.this = StockGDI.GetCursor(StockGDI.CURSOR_CROSS).this
        wx.HOURGLASS_CURSOR.this = StockGDI.GetCursor(StockGDI.CURSOR_HOURGLASS).this
        wx.STANDARD_CURSOR.this = StockGDI.GetCursor(StockGDI.CURSOR_STANDARD).this
        wx.TheFontList.this = _wxPyInitTheFontList().this
        wx.ThePenList.this = _wxPyInitThePenList().this
        wx.TheBrushList.this = _wxPyInitTheBrushList().this
        wx.TheColourDatabase.this = _wxPyInitTheColourDatabase().this

    _initStockObjects = staticmethod(_initStockObjects)


_gdi_.StockGDI_swigregister(StockGDI)

def StockGDI_DeleteAll(*args):
    return _gdi_.StockGDI_DeleteAll(*args)


def StockGDI_instance(*args):
    return _gdi_.StockGDI_instance(*args)


def StockGDI_GetBrush(*args, **kwargs):
    return _gdi_.StockGDI_GetBrush(*args, **kwargs)


def StockGDI_GetColour(*args, **kwargs):
    return _gdi_.StockGDI_GetColour(*args, **kwargs)


def StockGDI_GetCursor(*args, **kwargs):
    return _gdi_.StockGDI_GetCursor(*args, **kwargs)


def StockGDI_GetPen(*args, **kwargs):
    return _gdi_.StockGDI_GetPen(*args, **kwargs)


ITALIC_FONT = Font.__new__(Font)
NORMAL_FONT = Font.__new__(Font)
SMALL_FONT = Font.__new__(Font)
SWISS_FONT = Font.__new__(Font)
BLACK_DASHED_PEN = Pen.__new__(Pen)
BLACK_PEN = Pen.__new__(Pen)
CYAN_PEN = Pen.__new__(Pen)
GREEN_PEN = Pen.__new__(Pen)
GREY_PEN = Pen.__new__(Pen)
LIGHT_GREY_PEN = Pen.__new__(Pen)
MEDIUM_GREY_PEN = Pen.__new__(Pen)
RED_PEN = Pen.__new__(Pen)
TRANSPARENT_PEN = Pen.__new__(Pen)
WHITE_PEN = Pen.__new__(Pen)
BLACK_BRUSH = Brush.__new__(Brush)
BLUE_BRUSH = Brush.__new__(Brush)
CYAN_BRUSH = Brush.__new__(Brush)
GREEN_BRUSH = Brush.__new__(Brush)
GREY_BRUSH = Brush.__new__(Brush)
LIGHT_GREY_BRUSH = Brush.__new__(Brush)
MEDIUM_GREY_BRUSH = Brush.__new__(Brush)
RED_BRUSH = Brush.__new__(Brush)
TRANSPARENT_BRUSH = Brush.__new__(Brush)
WHITE_BRUSH = Brush.__new__(Brush)
BLACK = Colour.__new__(Colour)
BLUE = Colour.__new__(Colour)
CYAN = Colour.__new__(Colour)
GREEN = Colour.__new__(Colour)
LIGHT_GREY = Colour.__new__(Colour)
RED = Colour.__new__(Colour)
WHITE = Colour.__new__(Colour)
CROSS_CURSOR = Cursor.__new__(Cursor)
HOURGLASS_CURSOR = Cursor.__new__(Cursor)
STANDARD_CURSOR = Cursor.__new__(Cursor)

class GDIObjListBase(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.GDIObjListBase_swiginit(self, _gdi_.new_GDIObjListBase(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_GDIObjListBase
    __del__ = lambda self: None


_gdi_.GDIObjListBase_swigregister(GDIObjListBase)
NullBitmap = cvar.NullBitmap
NullIcon = cvar.NullIcon
NullCursor = cvar.NullCursor
NullPen = cvar.NullPen
NullBrush = cvar.NullBrush
NullPalette = cvar.NullPalette
NullFont = cvar.NullFont
NullColour = cvar.NullColour

class PenList(GDIObjListBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def FindOrCreatePen(*args, **kwargs):
        return _gdi_.PenList_FindOrCreatePen(*args, **kwargs)

    def AddPen(*args, **kwargs):
        return _gdi_.PenList_AddPen(*args, **kwargs)

    def RemovePen(*args, **kwargs):
        return _gdi_.PenList_RemovePen(*args, **kwargs)

    AddPen = wx._deprecated(AddPen)
    RemovePen = wx._deprecated(RemovePen)


_gdi_.PenList_swigregister(PenList)

class BrushList(GDIObjListBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def FindOrCreateBrush(*args, **kwargs):
        return _gdi_.BrushList_FindOrCreateBrush(*args, **kwargs)

    def AddBrush(*args, **kwargs):
        return _gdi_.BrushList_AddBrush(*args, **kwargs)

    def RemoveBrush(*args, **kwargs):
        return _gdi_.BrushList_RemoveBrush(*args, **kwargs)

    AddBrush = wx._deprecated(AddBrush)
    RemoveBrush = wx._deprecated(RemoveBrush)


_gdi_.BrushList_swigregister(BrushList)

class FontList(GDIObjListBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def FindOrCreateFont(*args, **kwargs):
        return _gdi_.FontList_FindOrCreateFont(*args, **kwargs)

    def AddFont(*args, **kwargs):
        return _gdi_.FontList_AddFont(*args, **kwargs)

    def RemoveFont(*args, **kwargs):
        return _gdi_.FontList_RemoveFont(*args, **kwargs)

    AddFont = wx._deprecated(AddFont)
    RemoveFont = wx._deprecated(RemoveFont)


_gdi_.FontList_swigregister(FontList)

class ColourDatabase(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.ColourDatabase_swiginit(self, _gdi_.new_ColourDatabase(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_ColourDatabase
    __del__ = lambda self: None

    def Find(*args, **kwargs):
        return _gdi_.ColourDatabase_Find(*args, **kwargs)

    def FindName(*args, **kwargs):
        return _gdi_.ColourDatabase_FindName(*args, **kwargs)

    FindColour = Find

    def AddColour(*args, **kwargs):
        return _gdi_.ColourDatabase_AddColour(*args, **kwargs)

    def Append(*args, **kwargs):
        return _gdi_.ColourDatabase_Append(*args, **kwargs)


_gdi_.ColourDatabase_swigregister(ColourDatabase)

def _wxPyInitTheFontList(*args):
    return _gdi_._wxPyInitTheFontList(*args)


def _wxPyInitThePenList(*args):
    return _gdi_._wxPyInitThePenList(*args)


def _wxPyInitTheBrushList(*args):
    return _gdi_._wxPyInitTheBrushList(*args)


def _wxPyInitTheColourDatabase(*args):
    return _gdi_._wxPyInitTheColourDatabase(*args)


TheFontList = FontList.__new__(FontList)
ThePenList = PenList.__new__(PenList)
TheBrushList = BrushList.__new__(BrushList)
TheColourDatabase = ColourDatabase.__new__(ColourDatabase)
NullColor = NullColour

class Effects(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.Effects_swiginit(self, _gdi_.new_Effects(*args, **kwargs))

    def GetHighlightColour(*args, **kwargs):
        return _gdi_.Effects_GetHighlightColour(*args, **kwargs)

    def GetLightShadow(*args, **kwargs):
        return _gdi_.Effects_GetLightShadow(*args, **kwargs)

    def GetFaceColour(*args, **kwargs):
        return _gdi_.Effects_GetFaceColour(*args, **kwargs)

    def GetMediumShadow(*args, **kwargs):
        return _gdi_.Effects_GetMediumShadow(*args, **kwargs)

    def GetDarkShadow(*args, **kwargs):
        return _gdi_.Effects_GetDarkShadow(*args, **kwargs)

    def SetHighlightColour(*args, **kwargs):
        return _gdi_.Effects_SetHighlightColour(*args, **kwargs)

    def SetLightShadow(*args, **kwargs):
        return _gdi_.Effects_SetLightShadow(*args, **kwargs)

    def SetFaceColour(*args, **kwargs):
        return _gdi_.Effects_SetFaceColour(*args, **kwargs)

    def SetMediumShadow(*args, **kwargs):
        return _gdi_.Effects_SetMediumShadow(*args, **kwargs)

    def SetDarkShadow(*args, **kwargs):
        return _gdi_.Effects_SetDarkShadow(*args, **kwargs)

    def Set(*args, **kwargs):
        return _gdi_.Effects_Set(*args, **kwargs)

    def DrawSunkenEdge(*args, **kwargs):
        return _gdi_.Effects_DrawSunkenEdge(*args, **kwargs)

    def TileBitmap(*args, **kwargs):
        return _gdi_.Effects_TileBitmap(*args, **kwargs)

    DarkShadow = property(GetDarkShadow, SetDarkShadow, doc='See `GetDarkShadow` and `SetDarkShadow`')
    FaceColour = property(GetFaceColour, SetFaceColour, doc='See `GetFaceColour` and `SetFaceColour`')
    HighlightColour = property(GetHighlightColour, SetHighlightColour, doc='See `GetHighlightColour` and `SetHighlightColour`')
    LightShadow = property(GetLightShadow, SetLightShadow, doc='See `GetLightShadow` and `SetLightShadow`')
    MediumShadow = property(GetMediumShadow, SetMediumShadow, doc='See `GetMediumShadow` and `SetMediumShadow`')


_gdi_.Effects_swigregister(Effects)
CONTROL_DISABLED = _gdi_.CONTROL_DISABLED
CONTROL_FOCUSED = _gdi_.CONTROL_FOCUSED
CONTROL_PRESSED = _gdi_.CONTROL_PRESSED
CONTROL_SPECIAL = _gdi_.CONTROL_SPECIAL
CONTROL_ISDEFAULT = _gdi_.CONTROL_ISDEFAULT
CONTROL_ISSUBMENU = _gdi_.CONTROL_ISSUBMENU
CONTROL_EXPANDED = _gdi_.CONTROL_EXPANDED
CONTROL_SIZEGRIP = _gdi_.CONTROL_SIZEGRIP
CONTROL_CURRENT = _gdi_.CONTROL_CURRENT
CONTROL_SELECTED = _gdi_.CONTROL_SELECTED
CONTROL_CHECKED = _gdi_.CONTROL_CHECKED
CONTROL_CHECKABLE = _gdi_.CONTROL_CHECKABLE
CONTROL_UNDETERMINED = _gdi_.CONTROL_UNDETERMINED
CONTROL_FLAGS_MASK = _gdi_.CONTROL_FLAGS_MASK
CONTROL_DIRTY = _gdi_.CONTROL_DIRTY

class SplitterRenderParams(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.SplitterRenderParams_swiginit(self, _gdi_.new_SplitterRenderParams(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_SplitterRenderParams
    __del__ = lambda self: None
    widthSash = property(_gdi_.SplitterRenderParams_widthSash_get)
    border = property(_gdi_.SplitterRenderParams_border_get)
    isHotSensitive = property(_gdi_.SplitterRenderParams_isHotSensitive_get)


_gdi_.SplitterRenderParams_swigregister(SplitterRenderParams)

class HeaderButtonParams(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.HeaderButtonParams_swiginit(self, _gdi_.new_HeaderButtonParams(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_HeaderButtonParams
    __del__ = lambda self: None
    m_arrowColour = property(_gdi_.HeaderButtonParams_m_arrowColour_get, _gdi_.HeaderButtonParams_m_arrowColour_set)
    m_selectionColour = property(_gdi_.HeaderButtonParams_m_selectionColour_get, _gdi_.HeaderButtonParams_m_selectionColour_set)
    m_labelText = property(_gdi_.HeaderButtonParams_m_labelText_get, _gdi_.HeaderButtonParams_m_labelText_set)
    m_labelFont = property(_gdi_.HeaderButtonParams_m_labelFont_get, _gdi_.HeaderButtonParams_m_labelFont_set)
    m_labelColour = property(_gdi_.HeaderButtonParams_m_labelColour_get, _gdi_.HeaderButtonParams_m_labelColour_set)
    m_labelBitmap = property(_gdi_.HeaderButtonParams_m_labelBitmap_get, _gdi_.HeaderButtonParams_m_labelBitmap_set)
    m_labelAlignment = property(_gdi_.HeaderButtonParams_m_labelAlignment_get, _gdi_.HeaderButtonParams_m_labelAlignment_set)


_gdi_.HeaderButtonParams_swigregister(HeaderButtonParams)
HDR_SORT_ICON_NONE = _gdi_.HDR_SORT_ICON_NONE
HDR_SORT_ICON_UP = _gdi_.HDR_SORT_ICON_UP
HDR_SORT_ICON_DOWN = _gdi_.HDR_SORT_ICON_DOWN

class RendererVersion(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.RendererVersion_swiginit(self, _gdi_.new_RendererVersion(*args, **kwargs))

    __swig_destroy__ = _gdi_.delete_RendererVersion
    __del__ = lambda self: None
    Current_Version = _gdi_.RendererVersion_Current_Version
    Current_Age = _gdi_.RendererVersion_Current_Age

    def IsCompatible(*args, **kwargs):
        return _gdi_.RendererVersion_IsCompatible(*args, **kwargs)

    IsCompatible = staticmethod(IsCompatible)
    version = property(_gdi_.RendererVersion_version_get)
    age = property(_gdi_.RendererVersion_age_get)


_gdi_.RendererVersion_swigregister(RendererVersion)

def RendererVersion_IsCompatible(*args, **kwargs):
    return _gdi_.RendererVersion_IsCompatible(*args, **kwargs)


class RendererNative(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def DrawHeaderButton(*args, **kwargs):
        return _gdi_.RendererNative_DrawHeaderButton(*args, **kwargs)

    def DrawHeaderButtonContents(*args, **kwargs):
        return _gdi_.RendererNative_DrawHeaderButtonContents(*args, **kwargs)

    def GetHeaderButtonHeight(*args, **kwargs):
        return _gdi_.RendererNative_GetHeaderButtonHeight(*args, **kwargs)

    def DrawTreeItemButton(*args, **kwargs):
        return _gdi_.RendererNative_DrawTreeItemButton(*args, **kwargs)

    def DrawSplitterBorder(*args, **kwargs):
        return _gdi_.RendererNative_DrawSplitterBorder(*args, **kwargs)

    def DrawSplitterSash(*args, **kwargs):
        return _gdi_.RendererNative_DrawSplitterSash(*args, **kwargs)

    def DrawComboBoxDropButton(*args, **kwargs):
        return _gdi_.RendererNative_DrawComboBoxDropButton(*args, **kwargs)

    def DrawDropArrow(*args, **kwargs):
        return _gdi_.RendererNative_DrawDropArrow(*args, **kwargs)

    def DrawCheckBox(*args, **kwargs):
        return _gdi_.RendererNative_DrawCheckBox(*args, **kwargs)

    def DrawPushButton(*args, **kwargs):
        return _gdi_.RendererNative_DrawPushButton(*args, **kwargs)

    def DrawItemSelectionRect(*args, **kwargs):
        return _gdi_.RendererNative_DrawItemSelectionRect(*args, **kwargs)

    def GetSplitterParams(*args, **kwargs):
        return _gdi_.RendererNative_GetSplitterParams(*args, **kwargs)

    def DrawChoice(*args, **kwargs):
        return _gdi_.RendererNative_DrawChoice(*args, **kwargs)

    def DrawComboBox(*args, **kwargs):
        return _gdi_.RendererNative_DrawComboBox(*args, **kwargs)

    def DrawTextCtrl(*args, **kwargs):
        return _gdi_.RendererNative_DrawTextCtrl(*args, **kwargs)

    def DrawRadioButton(*args, **kwargs):
        return _gdi_.RendererNative_DrawRadioButton(*args, **kwargs)

    def Get(*args, **kwargs):
        return _gdi_.RendererNative_Get(*args, **kwargs)

    Get = staticmethod(Get)

    def GetGeneric(*args, **kwargs):
        return _gdi_.RendererNative_GetGeneric(*args, **kwargs)

    GetGeneric = staticmethod(GetGeneric)

    def GetDefault(*args, **kwargs):
        return _gdi_.RendererNative_GetDefault(*args, **kwargs)

    GetDefault = staticmethod(GetDefault)

    def Set(*args, **kwargs):
        return _gdi_.RendererNative_Set(*args, **kwargs)

    Set = staticmethod(Set)

    def GetVersion(*args, **kwargs):
        return _gdi_.RendererNative_GetVersion(*args, **kwargs)

    SplitterParams = property(GetSplitterParams, doc='See `GetSplitterParams`')
    Version = property(GetVersion, doc='See `GetVersion`')


_gdi_.RendererNative_swigregister(RendererNative)

def RendererNative_Get(*args):
    return _gdi_.RendererNative_Get(*args)


def RendererNative_GetGeneric(*args):
    return _gdi_.RendererNative_GetGeneric(*args)


def RendererNative_GetDefault(*args):
    return _gdi_.RendererNative_GetDefault(*args)


def RendererNative_Set(*args, **kwargs):
    return _gdi_.RendererNative_Set(*args, **kwargs)


class PseudoDC(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _gdi_.PseudoDC_swiginit(self, _gdi_.new_PseudoDC(*args, **kwargs))

    def BeginDrawing(*args, **kwargs):
        return _gdi_.PseudoDC_BeginDrawing(*args, **kwargs)

    def EndDrawing(*args, **kwargs):
        return _gdi_.PseudoDC_EndDrawing(*args, **kwargs)

    __swig_destroy__ = _gdi_.delete_PseudoDC
    __del__ = lambda self: None

    def RemoveAll(*args, **kwargs):
        return _gdi_.PseudoDC_RemoveAll(*args, **kwargs)

    def GetLen(*args, **kwargs):
        return _gdi_.PseudoDC_GetLen(*args, **kwargs)

    def SetId(*args, **kwargs):
        return _gdi_.PseudoDC_SetId(*args, **kwargs)

    def ClearId(*args, **kwargs):
        return _gdi_.PseudoDC_ClearId(*args, **kwargs)

    def RemoveId(*args, **kwargs):
        return _gdi_.PseudoDC_RemoveId(*args, **kwargs)

    def TranslateId(*args, **kwargs):
        return _gdi_.PseudoDC_TranslateId(*args, **kwargs)

    def SetIdGreyedOut(*args, **kwargs):
        return _gdi_.PseudoDC_SetIdGreyedOut(*args, **kwargs)

    def GetIdGreyedOut(*args, **kwargs):
        return _gdi_.PseudoDC_GetIdGreyedOut(*args, **kwargs)

    def FindObjects(*args, **kwargs):
        return _gdi_.PseudoDC_FindObjects(*args, **kwargs)

    def FindObjectsByBBox(*args, **kwargs):
        return _gdi_.PseudoDC_FindObjectsByBBox(*args, **kwargs)

    def DrawIdToDC(*args, **kwargs):
        return _gdi_.PseudoDC_DrawIdToDC(*args, **kwargs)

    def SetIdBounds(*args, **kwargs):
        return _gdi_.PseudoDC_SetIdBounds(*args, **kwargs)

    def GetIdBounds(*args, **kwargs):
        return _gdi_.PseudoDC_GetIdBounds(*args, **kwargs)

    def DrawToDCClipped(*args, **kwargs):
        return _gdi_.PseudoDC_DrawToDCClipped(*args, **kwargs)

    def DrawToDCClippedRgn(*args, **kwargs):
        return _gdi_.PseudoDC_DrawToDCClippedRgn(*args, **kwargs)

    def DrawToDC(*args, **kwargs):
        return _gdi_.PseudoDC_DrawToDC(*args, **kwargs)

    def FloodFill(*args, **kwargs):
        return _gdi_.PseudoDC_FloodFill(*args, **kwargs)

    def FloodFillPoint(*args, **kwargs):
        return _gdi_.PseudoDC_FloodFillPoint(*args, **kwargs)

    def DrawLine(*args, **kwargs):
        return _gdi_.PseudoDC_DrawLine(*args, **kwargs)

    def DrawLinePoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawLinePoint(*args, **kwargs)

    def CrossHair(*args, **kwargs):
        return _gdi_.PseudoDC_CrossHair(*args, **kwargs)

    def CrossHairPoint(*args, **kwargs):
        return _gdi_.PseudoDC_CrossHairPoint(*args, **kwargs)

    def DrawArc(*args, **kwargs):
        return _gdi_.PseudoDC_DrawArc(*args, **kwargs)

    def DrawArcPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawArcPoint(*args, **kwargs)

    def DrawCheckMark(*args, **kwargs):
        return _gdi_.PseudoDC_DrawCheckMark(*args, **kwargs)

    def DrawCheckMarkRect(*args, **kwargs):
        return _gdi_.PseudoDC_DrawCheckMarkRect(*args, **kwargs)

    def DrawEllipticArc(*args, **kwargs):
        return _gdi_.PseudoDC_DrawEllipticArc(*args, **kwargs)

    def DrawEllipticArcPointSize(*args, **kwargs):
        return _gdi_.PseudoDC_DrawEllipticArcPointSize(*args, **kwargs)

    def DrawPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawPoint(*args, **kwargs)

    def DrawPointPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawPointPoint(*args, **kwargs)

    def DrawRectangle(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRectangle(*args, **kwargs)

    def DrawRectangleRect(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRectangleRect(*args, **kwargs)

    def DrawRectanglePointSize(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRectanglePointSize(*args, **kwargs)

    def DrawRoundedRectangle(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRoundedRectangle(*args, **kwargs)

    def DrawRoundedRectangleRect(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRoundedRectangleRect(*args, **kwargs)

    def DrawRoundedRectanglePointSize(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRoundedRectanglePointSize(*args, **kwargs)

    def DrawCircle(*args, **kwargs):
        return _gdi_.PseudoDC_DrawCircle(*args, **kwargs)

    def DrawCirclePoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawCirclePoint(*args, **kwargs)

    def DrawEllipse(*args, **kwargs):
        return _gdi_.PseudoDC_DrawEllipse(*args, **kwargs)

    def DrawEllipseRect(*args, **kwargs):
        return _gdi_.PseudoDC_DrawEllipseRect(*args, **kwargs)

    def DrawEllipsePointSize(*args, **kwargs):
        return _gdi_.PseudoDC_DrawEllipsePointSize(*args, **kwargs)

    def DrawIcon(*args, **kwargs):
        return _gdi_.PseudoDC_DrawIcon(*args, **kwargs)

    def DrawIconPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawIconPoint(*args, **kwargs)

    def DrawBitmap(*args, **kwargs):
        return _gdi_.PseudoDC_DrawBitmap(*args, **kwargs)

    def DrawBitmapPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawBitmapPoint(*args, **kwargs)

    def DrawText(*args, **kwargs):
        return _gdi_.PseudoDC_DrawText(*args, **kwargs)

    def DrawTextPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawTextPoint(*args, **kwargs)

    def DrawRotatedText(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRotatedText(*args, **kwargs)

    def DrawRotatedTextPoint(*args, **kwargs):
        return _gdi_.PseudoDC_DrawRotatedTextPoint(*args, **kwargs)

    def DrawLines(*args, **kwargs):
        return _gdi_.PseudoDC_DrawLines(*args, **kwargs)

    def DrawPolygon(*args, **kwargs):
        return _gdi_.PseudoDC_DrawPolygon(*args, **kwargs)

    def DrawLabel(*args, **kwargs):
        return _gdi_.PseudoDC_DrawLabel(*args, **kwargs)

    def DrawImageLabel(*args, **kwargs):
        return _gdi_.PseudoDC_DrawImageLabel(*args, **kwargs)

    def DrawSpline(*args, **kwargs):
        return _gdi_.PseudoDC_DrawSpline(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _gdi_.PseudoDC_Clear(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _gdi_.PseudoDC_SetFont(*args, **kwargs)

    def SetPen(*args, **kwargs):
        return _gdi_.PseudoDC_SetPen(*args, **kwargs)

    def SetBrush(*args, **kwargs):
        return _gdi_.PseudoDC_SetBrush(*args, **kwargs)

    def SetBackground(*args, **kwargs):
        return _gdi_.PseudoDC_SetBackground(*args, **kwargs)

    def SetBackgroundMode(*args, **kwargs):
        return _gdi_.PseudoDC_SetBackgroundMode(*args, **kwargs)

    def SetPalette(*args, **kwargs):
        return _gdi_.PseudoDC_SetPalette(*args, **kwargs)

    def SetTextForeground(*args, **kwargs):
        return _gdi_.PseudoDC_SetTextForeground(*args, **kwargs)

    def SetTextBackground(*args, **kwargs):
        return _gdi_.PseudoDC_SetTextBackground(*args, **kwargs)

    def SetLogicalFunction(*args, **kwargs):
        return _gdi_.PseudoDC_SetLogicalFunction(*args, **kwargs)

    IdBounds = property(GetIdBounds, SetIdBounds, doc='See `GetIdBounds` and `SetIdBounds`')
    Len = property(GetLen, doc='See `GetLen`')


_gdi_.PseudoDC_swigregister(PseudoDC)
