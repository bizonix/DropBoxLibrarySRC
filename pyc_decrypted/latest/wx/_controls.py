#Embedded file name: wx/_controls.py
import _controls_
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
BU_LEFT = _controls_.BU_LEFT
BU_TOP = _controls_.BU_TOP
BU_RIGHT = _controls_.BU_RIGHT
BU_BOTTOM = _controls_.BU_BOTTOM
BU_ALIGN_MASK = _controls_.BU_ALIGN_MASK
BU_EXACTFIT = _controls_.BU_EXACTFIT
BU_AUTODRAW = _controls_.BU_AUTODRAW

class Button(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.Button_swiginit(self, _controls_.new_Button(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.Button_Create(*args, **kwargs)

    def SetDefault(*args, **kwargs):
        return _controls_.Button_SetDefault(*args, **kwargs)

    def GetDefaultSize(*args, **kwargs):
        return _controls_.Button_GetDefaultSize(*args, **kwargs)

    GetDefaultSize = staticmethod(GetDefaultSize)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.Button_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_controls_.Button_swigregister(Button)
cvar = _controls_.cvar
ButtonNameStr = cvar.ButtonNameStr

def PreButton(*args, **kwargs):
    val = _controls_.new_PreButton(*args, **kwargs)
    return val


def Button_GetDefaultSize(*args):
    return _controls_.Button_GetDefaultSize(*args)


def Button_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.Button_GetClassDefaultAttributes(*args, **kwargs)


class BitmapButton(Button):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.BitmapButton_swiginit(self, _controls_.new_BitmapButton(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.BitmapButton_Create(*args, **kwargs)

    def GetBitmapLabel(*args, **kwargs):
        return _controls_.BitmapButton_GetBitmapLabel(*args, **kwargs)

    def GetBitmapDisabled(*args, **kwargs):
        return _controls_.BitmapButton_GetBitmapDisabled(*args, **kwargs)

    def GetBitmapFocus(*args, **kwargs):
        return _controls_.BitmapButton_GetBitmapFocus(*args, **kwargs)

    def GetBitmapSelected(*args, **kwargs):
        return _controls_.BitmapButton_GetBitmapSelected(*args, **kwargs)

    def GetBitmapHover(*args, **kwargs):
        return _controls_.BitmapButton_GetBitmapHover(*args, **kwargs)

    def SetBitmapDisabled(*args, **kwargs):
        return _controls_.BitmapButton_SetBitmapDisabled(*args, **kwargs)

    def SetBitmapFocus(*args, **kwargs):
        return _controls_.BitmapButton_SetBitmapFocus(*args, **kwargs)

    def SetBitmapSelected(*args, **kwargs):
        return _controls_.BitmapButton_SetBitmapSelected(*args, **kwargs)

    def SetBitmapLabel(*args, **kwargs):
        return _controls_.BitmapButton_SetBitmapLabel(*args, **kwargs)

    def SetBitmapHover(*args, **kwargs):
        return _controls_.BitmapButton_SetBitmapHover(*args, **kwargs)

    def SetMargins(*args, **kwargs):
        return _controls_.BitmapButton_SetMargins(*args, **kwargs)

    def GetMarginX(*args, **kwargs):
        return _controls_.BitmapButton_GetMarginX(*args, **kwargs)

    def GetMarginY(*args, **kwargs):
        return _controls_.BitmapButton_GetMarginY(*args, **kwargs)

    BitmapDisabled = property(GetBitmapDisabled, SetBitmapDisabled, doc='See `GetBitmapDisabled` and `SetBitmapDisabled`')
    BitmapFocus = property(GetBitmapFocus, SetBitmapFocus, doc='See `GetBitmapFocus` and `SetBitmapFocus`')
    BitmapHover = property(GetBitmapHover, SetBitmapHover, doc='See `GetBitmapHover` and `SetBitmapHover`')
    BitmapLabel = property(GetBitmapLabel, SetBitmapLabel, doc='See `GetBitmapLabel` and `SetBitmapLabel`')
    BitmapSelected = property(GetBitmapSelected, SetBitmapSelected, doc='See `GetBitmapSelected` and `SetBitmapSelected`')
    MarginX = property(GetMarginX, doc='See `GetMarginX`')
    MarginY = property(GetMarginY, doc='See `GetMarginY`')


_controls_.BitmapButton_swigregister(BitmapButton)

def PreBitmapButton(*args, **kwargs):
    val = _controls_.new_PreBitmapButton(*args, **kwargs)
    return val


CHK_2STATE = _controls_.CHK_2STATE
CHK_3STATE = _controls_.CHK_3STATE
CHK_ALLOW_3RD_STATE_FOR_USER = _controls_.CHK_ALLOW_3RD_STATE_FOR_USER
CHK_NO_SIBLING_LABEL = _controls_.CHK_NO_SIBLING_LABEL
CHK_UNCHECKED = _controls_.CHK_UNCHECKED
CHK_CHECKED = _controls_.CHK_CHECKED
CHK_UNDETERMINED = _controls_.CHK_UNDETERMINED

class CheckBox(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.CheckBox_swiginit(self, _controls_.new_CheckBox(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.CheckBox_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.CheckBox_GetValue(*args, **kwargs)

    def IsChecked(*args, **kwargs):
        return _controls_.CheckBox_IsChecked(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.CheckBox_SetValue(*args, **kwargs)

    def Get3StateValue(*args, **kwargs):
        return _controls_.CheckBox_Get3StateValue(*args, **kwargs)

    def Set3StateValue(*args, **kwargs):
        return _controls_.CheckBox_Set3StateValue(*args, **kwargs)

    def Is3State(*args, **kwargs):
        return _controls_.CheckBox_Is3State(*args, **kwargs)

    def Is3rdStateAllowedForUser(*args, **kwargs):
        return _controls_.CheckBox_Is3rdStateAllowedForUser(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.CheckBox_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    ThreeStateValue = property(Get3StateValue, Set3StateValue, doc='See `Get3StateValue` and `Set3StateValue`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.CheckBox_swigregister(CheckBox)
CheckBoxNameStr = cvar.CheckBoxNameStr

def PreCheckBox(*args, **kwargs):
    val = _controls_.new_PreCheckBox(*args, **kwargs)
    return val


def CheckBox_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.CheckBox_GetClassDefaultAttributes(*args, **kwargs)


class Choice(_core.ControlWithItems):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.Choice_swiginit(self, _controls_.new_Choice(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.Choice_Create(*args, **kwargs)

    def GetCurrentSelection(*args, **kwargs):
        return _controls_.Choice_GetCurrentSelection(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.Choice_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    CurrentSelection = property(GetCurrentSelection, doc='See `GetCurrentSelection`')


_controls_.Choice_swigregister(Choice)
ChoiceNameStr = cvar.ChoiceNameStr

def PreChoice(*args, **kwargs):
    val = _controls_.new_PreChoice(*args, **kwargs)
    return val


def Choice_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.Choice_GetClassDefaultAttributes(*args, **kwargs)


class ComboBox(_core.Control, _core.ItemContainer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ComboBox_swiginit(self, _controls_.new_ComboBox(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.ComboBox_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.ComboBox_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.ComboBox_SetValue(*args, **kwargs)

    def Copy(*args, **kwargs):
        return _controls_.ComboBox_Copy(*args, **kwargs)

    def Cut(*args, **kwargs):
        return _controls_.ComboBox_Cut(*args, **kwargs)

    def Paste(*args, **kwargs):
        return _controls_.ComboBox_Paste(*args, **kwargs)

    def SetInsertionPoint(*args, **kwargs):
        return _controls_.ComboBox_SetInsertionPoint(*args, **kwargs)

    def GetInsertionPoint(*args, **kwargs):
        return _controls_.ComboBox_GetInsertionPoint(*args, **kwargs)

    def GetLastPosition(*args, **kwargs):
        return _controls_.ComboBox_GetLastPosition(*args, **kwargs)

    def Replace(*args, **kwargs):
        return _controls_.ComboBox_Replace(*args, **kwargs)

    def SetMark(*args, **kwargs):
        return _controls_.ComboBox_SetMark(*args, **kwargs)

    def GetMark(*args, **kwargs):
        return _controls_.ComboBox_GetMark(*args, **kwargs)

    def GetCurrentSelection(*args, **kwargs):
        return _controls_.ComboBox_GetCurrentSelection(*args, **kwargs)

    def SetStringSelection(*args, **kwargs):
        return _controls_.ComboBox_SetStringSelection(*args, **kwargs)

    def SetEditable(*args, **kwargs):
        return _controls_.ComboBox_SetEditable(*args, **kwargs)

    def SetInsertionPointEnd(*args, **kwargs):
        return _controls_.ComboBox_SetInsertionPointEnd(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _controls_.ComboBox_Remove(*args, **kwargs)

    def IsEditable(*args, **kwargs):
        return _controls_.ComboBox_IsEditable(*args, **kwargs)

    def Undo(*args, **kwargs):
        return _controls_.ComboBox_Undo(*args, **kwargs)

    def Redo(*args, **kwargs):
        return _controls_.ComboBox_Redo(*args, **kwargs)

    def SelectAll(*args, **kwargs):
        return _controls_.ComboBox_SelectAll(*args, **kwargs)

    def CanCopy(*args, **kwargs):
        return _controls_.ComboBox_CanCopy(*args, **kwargs)

    def CanCut(*args, **kwargs):
        return _controls_.ComboBox_CanCut(*args, **kwargs)

    def CanPaste(*args, **kwargs):
        return _controls_.ComboBox_CanPaste(*args, **kwargs)

    def CanUndo(*args, **kwargs):
        return _controls_.ComboBox_CanUndo(*args, **kwargs)

    def CanRedo(*args, **kwargs):
        return _controls_.ComboBox_CanRedo(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.ComboBox_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    CurrentSelection = property(GetCurrentSelection, doc='See `GetCurrentSelection`')
    InsertionPoint = property(GetInsertionPoint, SetInsertionPoint, doc='See `GetInsertionPoint` and `SetInsertionPoint`')
    LastPosition = property(GetLastPosition, doc='See `GetLastPosition`')
    Mark = property(GetMark, SetMark, doc='See `GetMark` and `SetMark`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.ComboBox_swigregister(ComboBox)
ComboBoxNameStr = cvar.ComboBoxNameStr

def PreComboBox(*args, **kwargs):
    val = _controls_.new_PreComboBox(*args, **kwargs)
    return val


def ComboBox_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.ComboBox_GetClassDefaultAttributes(*args, **kwargs)


GA_HORIZONTAL = _controls_.GA_HORIZONTAL
GA_VERTICAL = _controls_.GA_VERTICAL
GA_SMOOTH = _controls_.GA_SMOOTH
GA_PROGRESSBAR = 0

class Gauge(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.Gauge_swiginit(self, _controls_.new_Gauge(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.Gauge_Create(*args, **kwargs)

    def SetRange(*args, **kwargs):
        return _controls_.Gauge_SetRange(*args, **kwargs)

    def GetRange(*args, **kwargs):
        return _controls_.Gauge_GetRange(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.Gauge_SetValue(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.Gauge_GetValue(*args, **kwargs)

    def Pulse(*args, **kwargs):
        return _controls_.Gauge_Pulse(*args, **kwargs)

    def IsVertical(*args, **kwargs):
        return _controls_.Gauge_IsVertical(*args, **kwargs)

    def SetShadowWidth(*args, **kwargs):
        return _controls_.Gauge_SetShadowWidth(*args, **kwargs)

    def GetShadowWidth(*args, **kwargs):
        return _controls_.Gauge_GetShadowWidth(*args, **kwargs)

    def SetBezelFace(*args, **kwargs):
        return _controls_.Gauge_SetBezelFace(*args, **kwargs)

    def GetBezelFace(*args, **kwargs):
        return _controls_.Gauge_GetBezelFace(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.Gauge_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    BezelFace = property(GetBezelFace, SetBezelFace, doc='See `GetBezelFace` and `SetBezelFace`')
    Range = property(GetRange, SetRange, doc='See `GetRange` and `SetRange`')
    ShadowWidth = property(GetShadowWidth, SetShadowWidth, doc='See `GetShadowWidth` and `SetShadowWidth`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.Gauge_swigregister(Gauge)
GaugeNameStr = cvar.GaugeNameStr

def PreGauge(*args, **kwargs):
    val = _controls_.new_PreGauge(*args, **kwargs)
    return val


def Gauge_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.Gauge_GetClassDefaultAttributes(*args, **kwargs)


class StaticBox(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.StaticBox_swiginit(self, _controls_.new_StaticBox(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.StaticBox_Create(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.StaticBox_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_controls_.StaticBox_swigregister(StaticBox)
StaticBitmapNameStr = cvar.StaticBitmapNameStr
StaticBoxNameStr = cvar.StaticBoxNameStr
StaticTextNameStr = cvar.StaticTextNameStr
StaticLineNameStr = cvar.StaticLineNameStr

def PreStaticBox(*args, **kwargs):
    val = _controls_.new_PreStaticBox(*args, **kwargs)
    return val


def StaticBox_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.StaticBox_GetClassDefaultAttributes(*args, **kwargs)


class StaticLine(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.StaticLine_swiginit(self, _controls_.new_StaticLine(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.StaticLine_Create(*args, **kwargs)

    def IsVertical(*args, **kwargs):
        return _controls_.StaticLine_IsVertical(*args, **kwargs)

    def GetDefaultSize(*args, **kwargs):
        return _controls_.StaticLine_GetDefaultSize(*args, **kwargs)

    GetDefaultSize = staticmethod(GetDefaultSize)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.StaticLine_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_controls_.StaticLine_swigregister(StaticLine)

def PreStaticLine(*args, **kwargs):
    val = _controls_.new_PreStaticLine(*args, **kwargs)
    return val


def StaticLine_GetDefaultSize(*args):
    return _controls_.StaticLine_GetDefaultSize(*args)


def StaticLine_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.StaticLine_GetClassDefaultAttributes(*args, **kwargs)


class StaticText(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.StaticText_swiginit(self, _controls_.new_StaticText(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.StaticText_Create(*args, **kwargs)

    def Wrap(*args, **kwargs):
        return _controls_.StaticText_Wrap(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.StaticText_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_controls_.StaticText_swigregister(StaticText)

def PreStaticText(*args, **kwargs):
    val = _controls_.new_PreStaticText(*args, **kwargs)
    return val


def StaticText_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.StaticText_GetClassDefaultAttributes(*args, **kwargs)


class StaticBitmap(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.StaticBitmap_swiginit(self, _controls_.new_StaticBitmap(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.StaticBitmap_Create(*args, **kwargs)

    def GetBitmap(*args, **kwargs):
        return _controls_.StaticBitmap_GetBitmap(*args, **kwargs)

    def SetBitmap(*args, **kwargs):
        return _controls_.StaticBitmap_SetBitmap(*args, **kwargs)

    def SetIcon(*args, **kwargs):
        return _controls_.StaticBitmap_SetIcon(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.StaticBitmap_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_controls_.StaticBitmap_swigregister(StaticBitmap)

def PreStaticBitmap(*args, **kwargs):
    val = _controls_.new_PreStaticBitmap(*args, **kwargs)
    return val


def StaticBitmap_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.StaticBitmap_GetClassDefaultAttributes(*args, **kwargs)


class ListBox(_core.ControlWithItems):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ListBox_swiginit(self, _controls_.new_ListBox(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.ListBox_Create(*args, **kwargs)

    def Insert(*args, **kwargs):
        return _controls_.ListBox_Insert(*args, **kwargs)

    def InsertItems(*args, **kwargs):
        return _controls_.ListBox_InsertItems(*args, **kwargs)

    def Set(*args, **kwargs):
        return _controls_.ListBox_Set(*args, **kwargs)

    def IsSelected(*args, **kwargs):
        return _controls_.ListBox_IsSelected(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.ListBox_SetSelection(*args, **kwargs)

    def Select(*args, **kwargs):
        return _controls_.ListBox_Select(*args, **kwargs)

    def Deselect(*args, **kwargs):
        return _controls_.ListBox_Deselect(*args, **kwargs)

    def DeselectAll(*args, **kwargs):
        return _controls_.ListBox_DeselectAll(*args, **kwargs)

    def SetStringSelection(*args, **kwargs):
        return _controls_.ListBox_SetStringSelection(*args, **kwargs)

    def GetSelections(*args, **kwargs):
        return _controls_.ListBox_GetSelections(*args, **kwargs)

    def SetFirstItem(*args, **kwargs):
        return _controls_.ListBox_SetFirstItem(*args, **kwargs)

    def SetFirstItemStr(*args, **kwargs):
        return _controls_.ListBox_SetFirstItemStr(*args, **kwargs)

    def EnsureVisible(*args, **kwargs):
        return _controls_.ListBox_EnsureVisible(*args, **kwargs)

    def AppendAndEnsureVisible(*args, **kwargs):
        return _controls_.ListBox_AppendAndEnsureVisible(*args, **kwargs)

    def IsSorted(*args, **kwargs):
        return _controls_.ListBox_IsSorted(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _controls_.ListBox_HitTest(*args, **kwargs)

    def SetItemForegroundColour(*args, **kwargs):
        return _controls_.ListBox_SetItemForegroundColour(*args, **kwargs)

    def SetItemBackgroundColour(*args, **kwargs):
        return _controls_.ListBox_SetItemBackgroundColour(*args, **kwargs)

    def SetItemFont(*args, **kwargs):
        return _controls_.ListBox_SetItemFont(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.ListBox_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    Selections = property(GetSelections, doc='See `GetSelections`')


_controls_.ListBox_swigregister(ListBox)
ListBoxNameStr = cvar.ListBoxNameStr

def PreListBox(*args, **kwargs):
    val = _controls_.new_PreListBox(*args, **kwargs)
    return val


def ListBox_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.ListBox_GetClassDefaultAttributes(*args, **kwargs)


TE_NO_VSCROLL = _controls_.TE_NO_VSCROLL
TE_AUTO_SCROLL = _controls_.TE_AUTO_SCROLL
TE_READONLY = _controls_.TE_READONLY
TE_MULTILINE = _controls_.TE_MULTILINE
TE_PROCESS_TAB = _controls_.TE_PROCESS_TAB
TE_LEFT = _controls_.TE_LEFT
TE_CENTER = _controls_.TE_CENTER
TE_RIGHT = _controls_.TE_RIGHT
TE_CENTRE = _controls_.TE_CENTRE
TE_RICH = _controls_.TE_RICH
TE_PROCESS_ENTER = _controls_.TE_PROCESS_ENTER
TE_PASSWORD = _controls_.TE_PASSWORD
TE_AUTO_URL = _controls_.TE_AUTO_URL
TE_NOHIDESEL = _controls_.TE_NOHIDESEL
TE_DONTWRAP = _controls_.TE_DONTWRAP
TE_CHARWRAP = _controls_.TE_CHARWRAP
TE_WORDWRAP = _controls_.TE_WORDWRAP
TE_BESTWRAP = _controls_.TE_BESTWRAP
TE_RICH2 = _controls_.TE_RICH2
TE_CAPITALIZE = _controls_.TE_CAPITALIZE
TE_LINEWRAP = TE_CHARWRAP
TEXT_ALIGNMENT_DEFAULT = _controls_.TEXT_ALIGNMENT_DEFAULT
TEXT_ALIGNMENT_LEFT = _controls_.TEXT_ALIGNMENT_LEFT
TEXT_ALIGNMENT_CENTRE = _controls_.TEXT_ALIGNMENT_CENTRE
TEXT_ALIGNMENT_CENTER = _controls_.TEXT_ALIGNMENT_CENTER
TEXT_ALIGNMENT_RIGHT = _controls_.TEXT_ALIGNMENT_RIGHT
TEXT_ALIGNMENT_JUSTIFIED = _controls_.TEXT_ALIGNMENT_JUSTIFIED
TEXT_ATTR_TEXT_COLOUR = _controls_.TEXT_ATTR_TEXT_COLOUR
TEXT_ATTR_BACKGROUND_COLOUR = _controls_.TEXT_ATTR_BACKGROUND_COLOUR
TEXT_ATTR_FONT_FACE = _controls_.TEXT_ATTR_FONT_FACE
TEXT_ATTR_FONT_SIZE = _controls_.TEXT_ATTR_FONT_SIZE
TEXT_ATTR_FONT_WEIGHT = _controls_.TEXT_ATTR_FONT_WEIGHT
TEXT_ATTR_FONT_ITALIC = _controls_.TEXT_ATTR_FONT_ITALIC
TEXT_ATTR_FONT_UNDERLINE = _controls_.TEXT_ATTR_FONT_UNDERLINE
TEXT_ATTR_FONT = _controls_.TEXT_ATTR_FONT
TEXT_ATTR_ALIGNMENT = _controls_.TEXT_ATTR_ALIGNMENT
TEXT_ATTR_LEFT_INDENT = _controls_.TEXT_ATTR_LEFT_INDENT
TEXT_ATTR_RIGHT_INDENT = _controls_.TEXT_ATTR_RIGHT_INDENT
TEXT_ATTR_TABS = _controls_.TEXT_ATTR_TABS
TE_HT_UNKNOWN = _controls_.TE_HT_UNKNOWN
TE_HT_BEFORE = _controls_.TE_HT_BEFORE
TE_HT_ON_TEXT = _controls_.TE_HT_ON_TEXT
TE_HT_BELOW = _controls_.TE_HT_BELOW
TE_HT_BEYOND = _controls_.TE_HT_BEYOND
OutOfRangeTextCoord = _controls_.OutOfRangeTextCoord
InvalidTextCoord = _controls_.InvalidTextCoord
TEXT_TYPE_ANY = _controls_.TEXT_TYPE_ANY

class TextAttr(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.TextAttr_swiginit(self, _controls_.new_TextAttr(*args, **kwargs))

    __swig_destroy__ = _controls_.delete_TextAttr
    __del__ = lambda self: None

    def Init(*args, **kwargs):
        return _controls_.TextAttr_Init(*args, **kwargs)

    def Merge(*args, **kwargs):
        return _controls_.TextAttr_Merge(*args, **kwargs)

    Merge = staticmethod(Merge)

    def SetTextColour(*args, **kwargs):
        return _controls_.TextAttr_SetTextColour(*args, **kwargs)

    def SetBackgroundColour(*args, **kwargs):
        return _controls_.TextAttr_SetBackgroundColour(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _controls_.TextAttr_SetFont(*args, **kwargs)

    def SetAlignment(*args, **kwargs):
        return _controls_.TextAttr_SetAlignment(*args, **kwargs)

    def SetTabs(*args, **kwargs):
        return _controls_.TextAttr_SetTabs(*args, **kwargs)

    def SetLeftIndent(*args, **kwargs):
        return _controls_.TextAttr_SetLeftIndent(*args, **kwargs)

    def SetRightIndent(*args, **kwargs):
        return _controls_.TextAttr_SetRightIndent(*args, **kwargs)

    def SetFlags(*args, **kwargs):
        return _controls_.TextAttr_SetFlags(*args, **kwargs)

    def HasTextColour(*args, **kwargs):
        return _controls_.TextAttr_HasTextColour(*args, **kwargs)

    def HasBackgroundColour(*args, **kwargs):
        return _controls_.TextAttr_HasBackgroundColour(*args, **kwargs)

    def HasFont(*args, **kwargs):
        return _controls_.TextAttr_HasFont(*args, **kwargs)

    def HasAlignment(*args, **kwargs):
        return _controls_.TextAttr_HasAlignment(*args, **kwargs)

    def HasTabs(*args, **kwargs):
        return _controls_.TextAttr_HasTabs(*args, **kwargs)

    def HasLeftIndent(*args, **kwargs):
        return _controls_.TextAttr_HasLeftIndent(*args, **kwargs)

    def HasRightIndent(*args, **kwargs):
        return _controls_.TextAttr_HasRightIndent(*args, **kwargs)

    def HasFlag(*args, **kwargs):
        return _controls_.TextAttr_HasFlag(*args, **kwargs)

    def GetTextColour(*args, **kwargs):
        return _controls_.TextAttr_GetTextColour(*args, **kwargs)

    def GetBackgroundColour(*args, **kwargs):
        return _controls_.TextAttr_GetBackgroundColour(*args, **kwargs)

    def GetFont(*args, **kwargs):
        return _controls_.TextAttr_GetFont(*args, **kwargs)

    def GetAlignment(*args, **kwargs):
        return _controls_.TextAttr_GetAlignment(*args, **kwargs)

    def GetTabs(*args, **kwargs):
        return _controls_.TextAttr_GetTabs(*args, **kwargs)

    def GetLeftIndent(*args, **kwargs):
        return _controls_.TextAttr_GetLeftIndent(*args, **kwargs)

    def GetLeftSubIndent(*args, **kwargs):
        return _controls_.TextAttr_GetLeftSubIndent(*args, **kwargs)

    def GetRightIndent(*args, **kwargs):
        return _controls_.TextAttr_GetRightIndent(*args, **kwargs)

    def GetFlags(*args, **kwargs):
        return _controls_.TextAttr_GetFlags(*args, **kwargs)

    def IsDefault(*args, **kwargs):
        return _controls_.TextAttr_IsDefault(*args, **kwargs)

    def Combine(*args, **kwargs):
        return _controls_.TextAttr_Combine(*args, **kwargs)

    Combine = staticmethod(Combine)
    Alignment = property(GetAlignment, SetAlignment, doc='See `GetAlignment` and `SetAlignment`')
    BackgroundColour = property(GetBackgroundColour, SetBackgroundColour, doc='See `GetBackgroundColour` and `SetBackgroundColour`')
    Flags = property(GetFlags, SetFlags, doc='See `GetFlags` and `SetFlags`')
    Font = property(GetFont, SetFont, doc='See `GetFont` and `SetFont`')
    LeftIndent = property(GetLeftIndent, SetLeftIndent, doc='See `GetLeftIndent` and `SetLeftIndent`')
    LeftSubIndent = property(GetLeftSubIndent, doc='See `GetLeftSubIndent`')
    RightIndent = property(GetRightIndent, SetRightIndent, doc='See `GetRightIndent` and `SetRightIndent`')
    Tabs = property(GetTabs, SetTabs, doc='See `GetTabs` and `SetTabs`')
    TextColour = property(GetTextColour, SetTextColour, doc='See `GetTextColour` and `SetTextColour`')


_controls_.TextAttr_swigregister(TextAttr)
TextCtrlNameStr = cvar.TextCtrlNameStr

def TextAttr_Merge(*args, **kwargs):
    return _controls_.TextAttr_Merge(*args, **kwargs)


def TextAttr_Combine(*args, **kwargs):
    return _controls_.TextAttr_Combine(*args, **kwargs)


class TextCtrl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.TextCtrl_swiginit(self, _controls_.new_TextCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.TextCtrl_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.TextCtrl_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.TextCtrl_SetValue(*args, **kwargs)

    def IsEmpty(*args, **kwargs):
        return _controls_.TextCtrl_IsEmpty(*args, **kwargs)

    def ChangeValue(*args, **kwargs):
        return _controls_.TextCtrl_ChangeValue(*args, **kwargs)

    def GetRange(*args, **kwargs):
        return _controls_.TextCtrl_GetRange(*args, **kwargs)

    def GetLineLength(*args, **kwargs):
        return _controls_.TextCtrl_GetLineLength(*args, **kwargs)

    def GetLineText(*args, **kwargs):
        return _controls_.TextCtrl_GetLineText(*args, **kwargs)

    def GetNumberOfLines(*args, **kwargs):
        return _controls_.TextCtrl_GetNumberOfLines(*args, **kwargs)

    def IsModified(*args, **kwargs):
        return _controls_.TextCtrl_IsModified(*args, **kwargs)

    def IsEditable(*args, **kwargs):
        return _controls_.TextCtrl_IsEditable(*args, **kwargs)

    def IsSingleLine(*args, **kwargs):
        return _controls_.TextCtrl_IsSingleLine(*args, **kwargs)

    def IsMultiLine(*args, **kwargs):
        return _controls_.TextCtrl_IsMultiLine(*args, **kwargs)

    def GetSelection(*args, **kwargs):
        return _controls_.TextCtrl_GetSelection(*args, **kwargs)

    def GetStringSelection(*args, **kwargs):
        return _controls_.TextCtrl_GetStringSelection(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _controls_.TextCtrl_Clear(*args, **kwargs)

    def Replace(*args, **kwargs):
        return _controls_.TextCtrl_Replace(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _controls_.TextCtrl_Remove(*args, **kwargs)

    def LoadFile(*args, **kwargs):
        return _controls_.TextCtrl_LoadFile(*args, **kwargs)

    def SaveFile(*args, **kwargs):
        return _controls_.TextCtrl_SaveFile(*args, **kwargs)

    def MarkDirty(*args, **kwargs):
        return _controls_.TextCtrl_MarkDirty(*args, **kwargs)

    def DiscardEdits(*args, **kwargs):
        return _controls_.TextCtrl_DiscardEdits(*args, **kwargs)

    def SetModified(*args, **kwargs):
        return _controls_.TextCtrl_SetModified(*args, **kwargs)

    def SetMaxLength(*args, **kwargs):
        return _controls_.TextCtrl_SetMaxLength(*args, **kwargs)

    def WriteText(*args, **kwargs):
        return _controls_.TextCtrl_WriteText(*args, **kwargs)

    def AppendText(*args, **kwargs):
        return _controls_.TextCtrl_AppendText(*args, **kwargs)

    def EmulateKeyPress(*args, **kwargs):
        return _controls_.TextCtrl_EmulateKeyPress(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _controls_.TextCtrl_SetStyle(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _controls_.TextCtrl_GetStyle(*args, **kwargs)

    def SetDefaultStyle(*args, **kwargs):
        return _controls_.TextCtrl_SetDefaultStyle(*args, **kwargs)

    def GetDefaultStyle(*args, **kwargs):
        return _controls_.TextCtrl_GetDefaultStyle(*args, **kwargs)

    def XYToPosition(*args, **kwargs):
        return _controls_.TextCtrl_XYToPosition(*args, **kwargs)

    def PositionToXY(*args, **kwargs):
        return _controls_.TextCtrl_PositionToXY(*args, **kwargs)

    def ShowPosition(*args, **kwargs):
        return _controls_.TextCtrl_ShowPosition(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _controls_.TextCtrl_HitTest(*args, **kwargs)

    def HitTestPos(*args, **kwargs):
        return _controls_.TextCtrl_HitTestPos(*args, **kwargs)

    def Copy(*args, **kwargs):
        return _controls_.TextCtrl_Copy(*args, **kwargs)

    def Cut(*args, **kwargs):
        return _controls_.TextCtrl_Cut(*args, **kwargs)

    def Paste(*args, **kwargs):
        return _controls_.TextCtrl_Paste(*args, **kwargs)

    def CanCopy(*args, **kwargs):
        return _controls_.TextCtrl_CanCopy(*args, **kwargs)

    def CanCut(*args, **kwargs):
        return _controls_.TextCtrl_CanCut(*args, **kwargs)

    def CanPaste(*args, **kwargs):
        return _controls_.TextCtrl_CanPaste(*args, **kwargs)

    def Undo(*args, **kwargs):
        return _controls_.TextCtrl_Undo(*args, **kwargs)

    def Redo(*args, **kwargs):
        return _controls_.TextCtrl_Redo(*args, **kwargs)

    def CanUndo(*args, **kwargs):
        return _controls_.TextCtrl_CanUndo(*args, **kwargs)

    def CanRedo(*args, **kwargs):
        return _controls_.TextCtrl_CanRedo(*args, **kwargs)

    def SetInsertionPoint(*args, **kwargs):
        return _controls_.TextCtrl_SetInsertionPoint(*args, **kwargs)

    def SetInsertionPointEnd(*args, **kwargs):
        return _controls_.TextCtrl_SetInsertionPointEnd(*args, **kwargs)

    def GetInsertionPoint(*args, **kwargs):
        return _controls_.TextCtrl_GetInsertionPoint(*args, **kwargs)

    def GetLastPosition(*args, **kwargs):
        return _controls_.TextCtrl_GetLastPosition(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.TextCtrl_SetSelection(*args, **kwargs)

    def SelectAll(*args, **kwargs):
        return _controls_.TextCtrl_SelectAll(*args, **kwargs)

    def SetEditable(*args, **kwargs):
        return _controls_.TextCtrl_SetEditable(*args, **kwargs)

    def MacCheckSpelling(*args, **kwargs):
        return _controls_.TextCtrl_MacCheckSpelling(*args, **kwargs)

    def SendTextUpdatedEvent(*args, **kwargs):
        return _controls_.TextCtrl_SendTextUpdatedEvent(*args, **kwargs)

    def write(*args, **kwargs):
        return _controls_.TextCtrl_write(*args, **kwargs)

    def GetString(*args, **kwargs):
        return _controls_.TextCtrl_GetString(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.TextCtrl_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    DefaultStyle = property(GetDefaultStyle, SetDefaultStyle, doc='See `GetDefaultStyle` and `SetDefaultStyle`')
    InsertionPoint = property(GetInsertionPoint, SetInsertionPoint, doc='See `GetInsertionPoint` and `SetInsertionPoint`')
    LastPosition = property(GetLastPosition, doc='See `GetLastPosition`')
    NumberOfLines = property(GetNumberOfLines, doc='See `GetNumberOfLines`')
    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')
    StringSelection = property(GetStringSelection, doc='See `GetStringSelection`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.TextCtrl_swigregister(TextCtrl)

def PreTextCtrl(*args, **kwargs):
    val = _controls_.new_PreTextCtrl(*args, **kwargs)
    return val


def TextCtrl_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.TextCtrl_GetClassDefaultAttributes(*args, **kwargs)


wxEVT_COMMAND_TEXT_UPDATED = _controls_.wxEVT_COMMAND_TEXT_UPDATED
wxEVT_COMMAND_TEXT_ENTER = _controls_.wxEVT_COMMAND_TEXT_ENTER
wxEVT_COMMAND_TEXT_URL = _controls_.wxEVT_COMMAND_TEXT_URL
wxEVT_COMMAND_TEXT_MAXLEN = _controls_.wxEVT_COMMAND_TEXT_MAXLEN

class TextUrlEvent(_core.CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.TextUrlEvent_swiginit(self, _controls_.new_TextUrlEvent(*args, **kwargs))

    def GetMouseEvent(*args, **kwargs):
        return _controls_.TextUrlEvent_GetMouseEvent(*args, **kwargs)

    def GetURLStart(*args, **kwargs):
        return _controls_.TextUrlEvent_GetURLStart(*args, **kwargs)

    def GetURLEnd(*args, **kwargs):
        return _controls_.TextUrlEvent_GetURLEnd(*args, **kwargs)

    MouseEvent = property(GetMouseEvent, doc='See `GetMouseEvent`')
    URLEnd = property(GetURLEnd, doc='See `GetURLEnd`')
    URLStart = property(GetURLStart, doc='See `GetURLStart`')


_controls_.TextUrlEvent_swigregister(TextUrlEvent)
EVT_TEXT = wx.PyEventBinder(wxEVT_COMMAND_TEXT_UPDATED, 1)
EVT_TEXT_ENTER = wx.PyEventBinder(wxEVT_COMMAND_TEXT_ENTER, 1)
EVT_TEXT_URL = wx.PyEventBinder(wxEVT_COMMAND_TEXT_URL, 1)
EVT_TEXT_MAXLEN = wx.PyEventBinder(wxEVT_COMMAND_TEXT_MAXLEN, 1)

class ScrollBar(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ScrollBar_swiginit(self, _controls_.new_ScrollBar(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.ScrollBar_Create(*args, **kwargs)

    def GetThumbPosition(*args, **kwargs):
        return _controls_.ScrollBar_GetThumbPosition(*args, **kwargs)

    def GetThumbSize(*args, **kwargs):
        return _controls_.ScrollBar_GetThumbSize(*args, **kwargs)

    GetThumbLength = GetThumbSize

    def GetPageSize(*args, **kwargs):
        return _controls_.ScrollBar_GetPageSize(*args, **kwargs)

    def GetRange(*args, **kwargs):
        return _controls_.ScrollBar_GetRange(*args, **kwargs)

    def IsVertical(*args, **kwargs):
        return _controls_.ScrollBar_IsVertical(*args, **kwargs)

    def SetThumbPosition(*args, **kwargs):
        return _controls_.ScrollBar_SetThumbPosition(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.ScrollBar_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    PageSize = property(GetPageSize, doc='See `GetPageSize`')
    Range = property(GetRange, doc='See `GetRange`')
    ThumbPosition = property(GetThumbPosition, SetThumbPosition, doc='See `GetThumbPosition` and `SetThumbPosition`')
    ThumbSize = property(GetThumbSize, doc='See `GetThumbSize`')


_controls_.ScrollBar_swigregister(ScrollBar)
ScrollBarNameStr = cvar.ScrollBarNameStr

def PreScrollBar(*args, **kwargs):
    val = _controls_.new_PreScrollBar(*args, **kwargs)
    return val


def ScrollBar_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.ScrollBar_GetClassDefaultAttributes(*args, **kwargs)


SP_HORIZONTAL = _controls_.SP_HORIZONTAL
SP_VERTICAL = _controls_.SP_VERTICAL
SP_ARROW_KEYS = _controls_.SP_ARROW_KEYS
SP_WRAP = _controls_.SP_WRAP

class SpinButton(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.SpinButton_swiginit(self, _controls_.new_SpinButton(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.SpinButton_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.SpinButton_GetValue(*args, **kwargs)

    def GetMin(*args, **kwargs):
        return _controls_.SpinButton_GetMin(*args, **kwargs)

    def GetMax(*args, **kwargs):
        return _controls_.SpinButton_GetMax(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.SpinButton_SetValue(*args, **kwargs)

    def SetMin(*args, **kwargs):
        return _controls_.SpinButton_SetMin(*args, **kwargs)

    def SetMax(*args, **kwargs):
        return _controls_.SpinButton_SetMax(*args, **kwargs)

    def SetRange(*args, **kwargs):
        return _controls_.SpinButton_SetRange(*args, **kwargs)

    def IsVertical(*args, **kwargs):
        return _controls_.SpinButton_IsVertical(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.SpinButton_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    Max = property(GetMax, SetMax, doc='See `GetMax` and `SetMax`')
    Min = property(GetMin, SetMin, doc='See `GetMin` and `SetMin`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.SpinButton_swigregister(SpinButton)
SPIN_BUTTON_NAME = cvar.SPIN_BUTTON_NAME
SpinCtrlNameStr = cvar.SpinCtrlNameStr

def PreSpinButton(*args, **kwargs):
    val = _controls_.new_PreSpinButton(*args, **kwargs)
    return val


def SpinButton_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.SpinButton_GetClassDefaultAttributes(*args, **kwargs)


class SpinCtrl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.SpinCtrl_swiginit(self, _controls_.new_SpinCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.SpinCtrl_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.SpinCtrl_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.SpinCtrl_SetValue(*args, **kwargs)

    def SetValueString(*args, **kwargs):
        return _controls_.SpinCtrl_SetValueString(*args, **kwargs)

    def SetRange(*args, **kwargs):
        return _controls_.SpinCtrl_SetRange(*args, **kwargs)

    def GetMin(*args, **kwargs):
        return _controls_.SpinCtrl_GetMin(*args, **kwargs)

    def GetMax(*args, **kwargs):
        return _controls_.SpinCtrl_GetMax(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.SpinCtrl_SetSelection(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.SpinCtrl_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    Max = property(GetMax, doc='See `GetMax`')
    Min = property(GetMin, doc='See `GetMin`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.SpinCtrl_swigregister(SpinCtrl)

def PreSpinCtrl(*args, **kwargs):
    val = _controls_.new_PreSpinCtrl(*args, **kwargs)
    return val


def SpinCtrl_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.SpinCtrl_GetClassDefaultAttributes(*args, **kwargs)


class SpinEvent(_core.NotifyEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.SpinEvent_swiginit(self, _controls_.new_SpinEvent(*args, **kwargs))

    def GetPosition(*args, **kwargs):
        return _controls_.SpinEvent_GetPosition(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _controls_.SpinEvent_SetPosition(*args, **kwargs)

    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')


_controls_.SpinEvent_swigregister(SpinEvent)
wxEVT_COMMAND_SPINCTRL_UPDATED = _controls_.wxEVT_COMMAND_SPINCTRL_UPDATED
EVT_SPIN_UP = wx.PyEventBinder(wx.wxEVT_SCROLL_LINEUP, 1)
EVT_SPIN_DOWN = wx.PyEventBinder(wx.wxEVT_SCROLL_LINEDOWN, 1)
EVT_SPIN = wx.PyEventBinder(wx.wxEVT_SCROLL_THUMBTRACK, 1)
EVT_SPINCTRL = wx.PyEventBinder(wxEVT_COMMAND_SPINCTRL_UPDATED, 1)

class RadioBox(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('point'):
            kwargs['pos'] = kwargs['point']
            del kwargs['point']
        _controls_.RadioBox_swiginit(self, _controls_.new_RadioBox(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.RadioBox_Create(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.RadioBox_SetSelection(*args, **kwargs)

    def GetSelection(*args, **kwargs):
        return _controls_.RadioBox_GetSelection(*args, **kwargs)

    def GetStringSelection(*args, **kwargs):
        return _controls_.RadioBox_GetStringSelection(*args, **kwargs)

    def SetStringSelection(*args, **kwargs):
        return _controls_.RadioBox_SetStringSelection(*args, **kwargs)

    def GetCount(*args, **kwargs):
        return _controls_.RadioBox_GetCount(*args, **kwargs)

    def FindString(*args, **kwargs):
        return _controls_.RadioBox_FindString(*args, **kwargs)

    def GetString(*args, **kwargs):
        return _controls_.RadioBox_GetString(*args, **kwargs)

    def SetString(*args, **kwargs):
        return _controls_.RadioBox_SetString(*args, **kwargs)

    GetItemLabel = GetString
    SetItemLabel = SetString

    def EnableItem(*args, **kwargs):
        return _controls_.RadioBox_EnableItem(*args, **kwargs)

    def ShowItem(*args, **kwargs):
        return _controls_.RadioBox_ShowItem(*args, **kwargs)

    def IsItemEnabled(*args, **kwargs):
        return _controls_.RadioBox_IsItemEnabled(*args, **kwargs)

    def IsItemShown(*args, **kwargs):
        return _controls_.RadioBox_IsItemShown(*args, **kwargs)

    def GetColumnCount(*args, **kwargs):
        return _controls_.RadioBox_GetColumnCount(*args, **kwargs)

    def GetRowCount(*args, **kwargs):
        return _controls_.RadioBox_GetRowCount(*args, **kwargs)

    def GetNextItem(*args, **kwargs):
        return _controls_.RadioBox_GetNextItem(*args, **kwargs)

    def SetItemToolTip(*args, **kwargs):
        return _controls_.RadioBox_SetItemToolTip(*args, **kwargs)

    def GetItemToolTip(*args, **kwargs):
        return _controls_.RadioBox_GetItemToolTip(*args, **kwargs)

    def SetItemHelpText(*args, **kwargs):
        return _controls_.RadioBox_SetItemHelpText(*args, **kwargs)

    def GetItemHelpText(*args, **kwargs):
        return _controls_.RadioBox_GetItemHelpText(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.RadioBox_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    ColumnCount = property(GetColumnCount, doc='See `GetColumnCount`')
    Count = property(GetCount, doc='See `GetCount`')
    RowCount = property(GetRowCount, doc='See `GetRowCount`')
    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')
    StringSelection = property(GetStringSelection, SetStringSelection, doc='See `GetStringSelection` and `SetStringSelection`')


_controls_.RadioBox_swigregister(RadioBox)
RadioBoxNameStr = cvar.RadioBoxNameStr
RadioButtonNameStr = cvar.RadioButtonNameStr

def PreRadioBox(*args, **kwargs):
    val = _controls_.new_PreRadioBox(*args, **kwargs)
    return val


def RadioBox_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.RadioBox_GetClassDefaultAttributes(*args, **kwargs)


class RadioButton(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.RadioButton_swiginit(self, _controls_.new_RadioButton(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.RadioButton_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.RadioButton_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.RadioButton_SetValue(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.RadioButton_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.RadioButton_swigregister(RadioButton)

def PreRadioButton(*args, **kwargs):
    val = _controls_.new_PreRadioButton(*args, **kwargs)
    return val


def RadioButton_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.RadioButton_GetClassDefaultAttributes(*args, **kwargs)


SL_HORIZONTAL = _controls_.SL_HORIZONTAL
SL_VERTICAL = _controls_.SL_VERTICAL
SL_TICKS = _controls_.SL_TICKS
SL_AUTOTICKS = _controls_.SL_AUTOTICKS
SL_LABELS = _controls_.SL_LABELS
SL_LEFT = _controls_.SL_LEFT
SL_TOP = _controls_.SL_TOP
SL_RIGHT = _controls_.SL_RIGHT
SL_BOTTOM = _controls_.SL_BOTTOM
SL_BOTH = _controls_.SL_BOTH
SL_SELRANGE = _controls_.SL_SELRANGE
SL_INVERSE = _controls_.SL_INVERSE

class Slider(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('point'):
            kwargs['pos'] = kwargs['point']
            del kwargs['point']
        _controls_.Slider_swiginit(self, _controls_.new_Slider(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.Slider_Create(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.Slider_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.Slider_SetValue(*args, **kwargs)

    def GetMin(*args, **kwargs):
        return _controls_.Slider_GetMin(*args, **kwargs)

    def GetMax(*args, **kwargs):
        return _controls_.Slider_GetMax(*args, **kwargs)

    def SetMin(*args, **kwargs):
        return _controls_.Slider_SetMin(*args, **kwargs)

    def SetMax(*args, **kwargs):
        return _controls_.Slider_SetMax(*args, **kwargs)

    def SetRange(*args, **kwargs):
        return _controls_.Slider_SetRange(*args, **kwargs)

    def GetRange(self):
        return (self.GetMin(), self.GetMax())

    def SetLineSize(*args, **kwargs):
        return _controls_.Slider_SetLineSize(*args, **kwargs)

    def SetPageSize(*args, **kwargs):
        return _controls_.Slider_SetPageSize(*args, **kwargs)

    def GetLineSize(*args, **kwargs):
        return _controls_.Slider_GetLineSize(*args, **kwargs)

    def GetPageSize(*args, **kwargs):
        return _controls_.Slider_GetPageSize(*args, **kwargs)

    def SetThumbLength(*args, **kwargs):
        return _controls_.Slider_SetThumbLength(*args, **kwargs)

    def GetThumbLength(*args, **kwargs):
        return _controls_.Slider_GetThumbLength(*args, **kwargs)

    def SetTickFreq(*args, **kwargs):
        return _controls_.Slider_SetTickFreq(*args, **kwargs)

    def GetTickFreq(*args, **kwargs):
        return _controls_.Slider_GetTickFreq(*args, **kwargs)

    def ClearTicks(*args, **kwargs):
        return _controls_.Slider_ClearTicks(*args, **kwargs)

    def SetTick(*args, **kwargs):
        return _controls_.Slider_SetTick(*args, **kwargs)

    def ClearSel(*args, **kwargs):
        return _controls_.Slider_ClearSel(*args, **kwargs)

    def GetSelEnd(*args, **kwargs):
        return _controls_.Slider_GetSelEnd(*args, **kwargs)

    def GetSelStart(*args, **kwargs):
        return _controls_.Slider_GetSelStart(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.Slider_SetSelection(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.Slider_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    LineSize = property(GetLineSize, SetLineSize, doc='See `GetLineSize` and `SetLineSize`')
    Max = property(GetMax, SetMax, doc='See `GetMax` and `SetMax`')
    Min = property(GetMin, SetMin, doc='See `GetMin` and `SetMin`')
    PageSize = property(GetPageSize, SetPageSize, doc='See `GetPageSize` and `SetPageSize`')
    SelEnd = property(GetSelEnd, doc='See `GetSelEnd`')
    SelStart = property(GetSelStart, doc='See `GetSelStart`')
    ThumbLength = property(GetThumbLength, SetThumbLength, doc='See `GetThumbLength` and `SetThumbLength`')
    TickFreq = property(GetTickFreq, SetTickFreq, doc='See `GetTickFreq` and `SetTickFreq`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.Slider_swigregister(Slider)
SliderNameStr = cvar.SliderNameStr

def PreSlider(*args, **kwargs):
    val = _controls_.new_PreSlider(*args, **kwargs)
    return val


def Slider_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.Slider_GetClassDefaultAttributes(*args, **kwargs)


wxEVT_COMMAND_TOGGLEBUTTON_CLICKED = _controls_.wxEVT_COMMAND_TOGGLEBUTTON_CLICKED
EVT_TOGGLEBUTTON = wx.PyEventBinder(wxEVT_COMMAND_TOGGLEBUTTON_CLICKED, 1)

class ToggleButton(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ToggleButton_swiginit(self, _controls_.new_ToggleButton(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.ToggleButton_Create(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _controls_.ToggleButton_SetValue(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.ToggleButton_GetValue(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.ToggleButton_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.ToggleButton_swigregister(ToggleButton)
ToggleButtonNameStr = cvar.ToggleButtonNameStr

def PreToggleButton(*args, **kwargs):
    val = _controls_.new_PreToggleButton(*args, **kwargs)
    return val


def ToggleButton_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.ToggleButton_GetClassDefaultAttributes(*args, **kwargs)


BK_DEFAULT = _controls_.BK_DEFAULT
BK_TOP = _controls_.BK_TOP
BK_BOTTOM = _controls_.BK_BOTTOM
BK_LEFT = _controls_.BK_LEFT
BK_RIGHT = _controls_.BK_RIGHT
BK_ALIGN_MASK = _controls_.BK_ALIGN_MASK
BK_HITTEST_NOWHERE = _controls_.BK_HITTEST_NOWHERE
BK_HITTEST_ONICON = _controls_.BK_HITTEST_ONICON
BK_HITTEST_ONLABEL = _controls_.BK_HITTEST_ONLABEL
BK_HITTEST_ONITEM = _controls_.BK_HITTEST_ONITEM
BK_HITTEST_ONPAGE = _controls_.BK_HITTEST_ONPAGE

class BookCtrlBase(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetPageCount(*args, **kwargs):
        return _controls_.BookCtrlBase_GetPageCount(*args, **kwargs)

    def GetPage(*args, **kwargs):
        return _controls_.BookCtrlBase_GetPage(*args, **kwargs)

    def GetCurrentPage(*args, **kwargs):
        return _controls_.BookCtrlBase_GetCurrentPage(*args, **kwargs)

    def GetSelection(*args, **kwargs):
        return _controls_.BookCtrlBase_GetSelection(*args, **kwargs)

    def SetPageText(*args, **kwargs):
        return _controls_.BookCtrlBase_SetPageText(*args, **kwargs)

    def GetPageText(*args, **kwargs):
        return _controls_.BookCtrlBase_GetPageText(*args, **kwargs)

    def SetImageList(*args, **kwargs):
        return _controls_.BookCtrlBase_SetImageList(*args, **kwargs)

    def AssignImageList(*args, **kwargs):
        return _controls_.BookCtrlBase_AssignImageList(*args, **kwargs)

    def GetImageList(*args, **kwargs):
        return _controls_.BookCtrlBase_GetImageList(*args, **kwargs)

    def GetPageImage(*args, **kwargs):
        return _controls_.BookCtrlBase_GetPageImage(*args, **kwargs)

    def SetPageImage(*args, **kwargs):
        return _controls_.BookCtrlBase_SetPageImage(*args, **kwargs)

    def SetPageSize(*args, **kwargs):
        return _controls_.BookCtrlBase_SetPageSize(*args, **kwargs)

    def CalcSizeFromPage(*args, **kwargs):
        return _controls_.BookCtrlBase_CalcSizeFromPage(*args, **kwargs)

    def GetInternalBorder(*args, **kwargs):
        return _controls_.BookCtrlBase_GetInternalBorder(*args, **kwargs)

    def SetInternalBorder(*args, **kwargs):
        return _controls_.BookCtrlBase_SetInternalBorder(*args, **kwargs)

    def IsVertical(*args, **kwargs):
        return _controls_.BookCtrlBase_IsVertical(*args, **kwargs)

    def SetControlMargin(*args, **kwargs):
        return _controls_.BookCtrlBase_SetControlMargin(*args, **kwargs)

    def GetControlMargin(*args, **kwargs):
        return _controls_.BookCtrlBase_GetControlMargin(*args, **kwargs)

    def SetFitToCurrentPage(*args, **kwargs):
        return _controls_.BookCtrlBase_SetFitToCurrentPage(*args, **kwargs)

    def GetFitToCurrentPage(*args, **kwargs):
        return _controls_.BookCtrlBase_GetFitToCurrentPage(*args, **kwargs)

    def GetControlSizer(*args, **kwargs):
        return _controls_.BookCtrlBase_GetControlSizer(*args, **kwargs)

    def DeletePage(*args, **kwargs):
        return _controls_.BookCtrlBase_DeletePage(*args, **kwargs)

    def RemovePage(*args, **kwargs):
        return _controls_.BookCtrlBase_RemovePage(*args, **kwargs)

    def DeleteAllPages(*args, **kwargs):
        return _controls_.BookCtrlBase_DeleteAllPages(*args, **kwargs)

    def AddPage(*args, **kwargs):
        return _controls_.BookCtrlBase_AddPage(*args, **kwargs)

    def InsertPage(*args, **kwargs):
        return _controls_.BookCtrlBase_InsertPage(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.BookCtrlBase_SetSelection(*args, **kwargs)

    def ChangeSelection(*args, **kwargs):
        return _controls_.BookCtrlBase_ChangeSelection(*args, **kwargs)

    def AdvanceSelection(*args, **kwargs):
        return _controls_.BookCtrlBase_AdvanceSelection(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _controls_.BookCtrlBase_HitTest(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.BookCtrlBase_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    ControlMargin = property(GetControlMargin, SetControlMargin, doc='See `GetControlMargin` and `SetControlMargin`')
    ControlSizer = property(GetControlSizer, doc='See `GetControlSizer`')
    CurrentPage = property(GetCurrentPage, doc='See `GetCurrentPage`')
    FitToCurrentPage = property(GetFitToCurrentPage, SetFitToCurrentPage, doc='See `GetFitToCurrentPage` and `SetFitToCurrentPage`')
    ImageList = property(GetImageList, SetImageList, doc='See `GetImageList` and `SetImageList`')
    InternalBorder = property(GetInternalBorder, SetInternalBorder, doc='See `GetInternalBorder` and `SetInternalBorder`')
    Page = property(GetPage, doc='See `GetPage`')
    PageCount = property(GetPageCount, doc='See `GetPageCount`')
    PageImage = property(GetPageImage, SetPageImage, doc='See `GetPageImage` and `SetPageImage`')
    PageText = property(GetPageText, SetPageText, doc='See `GetPageText` and `SetPageText`')
    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')


_controls_.BookCtrlBase_swigregister(BookCtrlBase)
NotebookNameStr = cvar.NotebookNameStr

def BookCtrlBase_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.BookCtrlBase_GetClassDefaultAttributes(*args, **kwargs)


class BookCtrlBaseEvent(_core.NotifyEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.BookCtrlBaseEvent_swiginit(self, _controls_.new_BookCtrlBaseEvent(*args, **kwargs))

    def GetSelection(*args, **kwargs):
        return _controls_.BookCtrlBaseEvent_GetSelection(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _controls_.BookCtrlBaseEvent_SetSelection(*args, **kwargs)

    def GetOldSelection(*args, **kwargs):
        return _controls_.BookCtrlBaseEvent_GetOldSelection(*args, **kwargs)

    def SetOldSelection(*args, **kwargs):
        return _controls_.BookCtrlBaseEvent_SetOldSelection(*args, **kwargs)

    OldSelection = property(GetOldSelection, SetOldSelection, doc='See `GetOldSelection` and `SetOldSelection`')
    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')


_controls_.BookCtrlBaseEvent_swigregister(BookCtrlBaseEvent)
NB_FIXEDWIDTH = _controls_.NB_FIXEDWIDTH
NB_TOP = _controls_.NB_TOP
NB_LEFT = _controls_.NB_LEFT
NB_RIGHT = _controls_.NB_RIGHT
NB_BOTTOM = _controls_.NB_BOTTOM
NB_MULTILINE = _controls_.NB_MULTILINE
NB_NOPAGETHEME = _controls_.NB_NOPAGETHEME
NB_HITTEST_NOWHERE = _controls_.NB_HITTEST_NOWHERE
NB_HITTEST_ONICON = _controls_.NB_HITTEST_ONICON
NB_HITTEST_ONLABEL = _controls_.NB_HITTEST_ONLABEL
NB_HITTEST_ONITEM = _controls_.NB_HITTEST_ONITEM
NB_HITTEST_ONPAGE = _controls_.NB_HITTEST_ONPAGE

class Notebook(BookCtrlBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.Notebook_swiginit(self, _controls_.new_Notebook(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.Notebook_Create(*args, **kwargs)

    def GetRowCount(*args, **kwargs):
        return _controls_.Notebook_GetRowCount(*args, **kwargs)

    def SetPadding(*args, **kwargs):
        return _controls_.Notebook_SetPadding(*args, **kwargs)

    def SetTabSize(*args, **kwargs):
        return _controls_.Notebook_SetTabSize(*args, **kwargs)

    def GetThemeBackgroundColour(*args, **kwargs):
        return _controls_.Notebook_GetThemeBackgroundColour(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.Notebook_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)

    def SendPageChangingEvent(*args, **kwargs):
        return _controls_.Notebook_SendPageChangingEvent(*args, **kwargs)

    def SendPageChangedEvent(*args, **kwargs):
        return _controls_.Notebook_SendPageChangedEvent(*args, **kwargs)

    RowCount = property(GetRowCount, doc='See `GetRowCount`')
    ThemeBackgroundColour = property(GetThemeBackgroundColour, doc='See `GetThemeBackgroundColour`')


_controls_.Notebook_swigregister(Notebook)

def PreNotebook(*args, **kwargs):
    val = _controls_.new_PreNotebook(*args, **kwargs)
    return val


def Notebook_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.Notebook_GetClassDefaultAttributes(*args, **kwargs)


class NotebookEvent(BookCtrlBaseEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.NotebookEvent_swiginit(self, _controls_.new_NotebookEvent(*args, **kwargs))


_controls_.NotebookEvent_swigregister(NotebookEvent)
wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGED = _controls_.wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGED
wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGING = _controls_.wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGING
EVT_NOTEBOOK_PAGE_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGED, 1)
EVT_NOTEBOOK_PAGE_CHANGING = wx.PyEventBinder(wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGING, 1)

class NotebookPage(wx.Panel):

    def __init__(self, parent, id = -1, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.TAB_TRAVERSAL, name = 'panel'):
        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        self.child = None
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, evt):
        if self.child is None:
            children = self.GetChildren()
            if len(children):
                self.child = children[0]
        if self.child:
            self.child.SetPosition((0, 0))
            self.child.SetSize(self.GetSize())


TOOL_STYLE_BUTTON = _controls_.TOOL_STYLE_BUTTON
TOOL_STYLE_SEPARATOR = _controls_.TOOL_STYLE_SEPARATOR
TOOL_STYLE_CONTROL = _controls_.TOOL_STYLE_CONTROL
TB_HORIZONTAL = _controls_.TB_HORIZONTAL
TB_VERTICAL = _controls_.TB_VERTICAL
TB_TOP = _controls_.TB_TOP
TB_LEFT = _controls_.TB_LEFT
TB_BOTTOM = _controls_.TB_BOTTOM
TB_RIGHT = _controls_.TB_RIGHT
TB_3DBUTTONS = _controls_.TB_3DBUTTONS
TB_FLAT = _controls_.TB_FLAT
TB_DOCKABLE = _controls_.TB_DOCKABLE
TB_NOICONS = _controls_.TB_NOICONS
TB_TEXT = _controls_.TB_TEXT
TB_NODIVIDER = _controls_.TB_NODIVIDER
TB_NOALIGN = _controls_.TB_NOALIGN
TB_HORZ_LAYOUT = _controls_.TB_HORZ_LAYOUT
TB_HORZ_TEXT = _controls_.TB_HORZ_TEXT
TB_NO_TOOLTIPS = _controls_.TB_NO_TOOLTIPS

class ToolBarToolBase(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetId(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetId(*args, **kwargs)

    def GetControl(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetControl(*args, **kwargs)

    def GetToolBar(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetToolBar(*args, **kwargs)

    def IsButton(*args, **kwargs):
        return _controls_.ToolBarToolBase_IsButton(*args, **kwargs)

    def IsControl(*args, **kwargs):
        return _controls_.ToolBarToolBase_IsControl(*args, **kwargs)

    def IsSeparator(*args, **kwargs):
        return _controls_.ToolBarToolBase_IsSeparator(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetStyle(*args, **kwargs)

    def GetKind(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetKind(*args, **kwargs)

    def IsEnabled(*args, **kwargs):
        return _controls_.ToolBarToolBase_IsEnabled(*args, **kwargs)

    def IsToggled(*args, **kwargs):
        return _controls_.ToolBarToolBase_IsToggled(*args, **kwargs)

    def CanBeToggled(*args, **kwargs):
        return _controls_.ToolBarToolBase_CanBeToggled(*args, **kwargs)

    def GetNormalBitmap(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetNormalBitmap(*args, **kwargs)

    def GetDisabledBitmap(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetDisabledBitmap(*args, **kwargs)

    def GetBitmap(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetBitmap(*args, **kwargs)

    def GetLabel(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetLabel(*args, **kwargs)

    def GetShortHelp(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetShortHelp(*args, **kwargs)

    def GetLongHelp(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetLongHelp(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _controls_.ToolBarToolBase_Enable(*args, **kwargs)

    def Toggle(*args, **kwargs):
        return _controls_.ToolBarToolBase_Toggle(*args, **kwargs)

    def SetToggle(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetToggle(*args, **kwargs)

    def SetShortHelp(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetShortHelp(*args, **kwargs)

    def SetLongHelp(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetLongHelp(*args, **kwargs)

    def SetNormalBitmap(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetNormalBitmap(*args, **kwargs)

    def SetDisabledBitmap(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetDisabledBitmap(*args, **kwargs)

    def SetLabel(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetLabel(*args, **kwargs)

    def Detach(*args, **kwargs):
        return _controls_.ToolBarToolBase_Detach(*args, **kwargs)

    def Attach(*args, **kwargs):
        return _controls_.ToolBarToolBase_Attach(*args, **kwargs)

    def GetClientData(*args, **kwargs):
        return _controls_.ToolBarToolBase_GetClientData(*args, **kwargs)

    def SetClientData(*args, **kwargs):
        return _controls_.ToolBarToolBase_SetClientData(*args, **kwargs)

    GetBitmap1 = GetNormalBitmap
    GetBitmap2 = GetDisabledBitmap
    SetBitmap1 = SetNormalBitmap
    SetBitmap2 = SetDisabledBitmap
    Bitmap = property(GetBitmap, doc='See `GetBitmap`')
    ClientData = property(GetClientData, SetClientData, doc='See `GetClientData` and `SetClientData`')
    Control = property(GetControl, doc='See `GetControl`')
    DisabledBitmap = property(GetDisabledBitmap, SetDisabledBitmap, doc='See `GetDisabledBitmap` and `SetDisabledBitmap`')
    Id = property(GetId, doc='See `GetId`')
    Kind = property(GetKind, doc='See `GetKind`')
    Label = property(GetLabel, SetLabel, doc='See `GetLabel` and `SetLabel`')
    LongHelp = property(GetLongHelp, SetLongHelp, doc='See `GetLongHelp` and `SetLongHelp`')
    NormalBitmap = property(GetNormalBitmap, SetNormalBitmap, doc='See `GetNormalBitmap` and `SetNormalBitmap`')
    ShortHelp = property(GetShortHelp, SetShortHelp, doc='See `GetShortHelp` and `SetShortHelp`')
    Style = property(GetStyle, doc='See `GetStyle`')
    ToolBar = property(GetToolBar, doc='See `GetToolBar`')


_controls_.ToolBarToolBase_swigregister(ToolBarToolBase)

class ToolBarBase(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def DoAddTool(*args, **kwargs):
        return _controls_.ToolBarBase_DoAddTool(*args, **kwargs)

    def DoInsertTool(*args, **kwargs):
        return _controls_.ToolBarBase_DoInsertTool(*args, **kwargs)

    def AddTool(self, id, bitmap, pushedBitmap = wx.NullBitmap, isToggle = 0, clientData = None, shortHelpString = '', longHelpString = ''):
        kind = wx.ITEM_NORMAL
        if isToggle:
            kind = wx.ITEM_CHECK
        return self.DoAddTool(id, '', bitmap, pushedBitmap, kind, shortHelpString, longHelpString, clientData)

    def AddSimpleTool(self, id, bitmap, shortHelpString = '', longHelpString = '', isToggle = 0):
        kind = wx.ITEM_NORMAL
        if isToggle:
            kind = wx.ITEM_CHECK
        return self.DoAddTool(id, '', bitmap, wx.NullBitmap, kind, shortHelpString, longHelpString, None)

    def InsertTool(self, pos, id, bitmap, pushedBitmap = wx.NullBitmap, isToggle = 0, clientData = None, shortHelpString = '', longHelpString = ''):
        kind = wx.ITEM_NORMAL
        if isToggle:
            kind = wx.ITEM_CHECK
        return self.DoInsertTool(pos, id, '', bitmap, pushedBitmap, kind, shortHelpString, longHelpString, clientData)

    def InsertSimpleTool(self, pos, id, bitmap, shortHelpString = '', longHelpString = '', isToggle = 0):
        kind = wx.ITEM_NORMAL
        if isToggle:
            kind = wx.ITEM_CHECK
        return self.DoInsertTool(pos, id, '', bitmap, wx.NullBitmap, kind, shortHelpString, longHelpString, None)

    def AddLabelTool(self, id, label, bitmap, bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = '', longHelp = '', clientData = None):
        return self.DoAddTool(id, label, bitmap, bmpDisabled, kind, shortHelp, longHelp, clientData)

    def InsertLabelTool(self, pos, id, label, bitmap, bmpDisabled = wx.NullBitmap, kind = wx.ITEM_NORMAL, shortHelp = '', longHelp = '', clientData = None):
        return self.DoInsertTool(pos, id, label, bitmap, bmpDisabled, kind, shortHelp, longHelp, clientData)

    def AddCheckLabelTool(self, id, label, bitmap, bmpDisabled = wx.NullBitmap, shortHelp = '', longHelp = '', clientData = None):
        return self.DoAddTool(id, label, bitmap, bmpDisabled, wx.ITEM_CHECK, shortHelp, longHelp, clientData)

    def AddRadioLabelTool(self, id, label, bitmap, bmpDisabled = wx.NullBitmap, shortHelp = '', longHelp = '', clientData = None):
        return self.DoAddTool(id, label, bitmap, bmpDisabled, wx.ITEM_RADIO, shortHelp, longHelp, clientData)

    def AddCheckTool(self, id, bitmap, bmpDisabled = wx.NullBitmap, shortHelp = '', longHelp = '', clientData = None):
        return self.DoAddTool(id, '', bitmap, bmpDisabled, wx.ITEM_CHECK, shortHelp, longHelp, clientData)

    def AddRadioTool(self, id, bitmap, bmpDisabled = wx.NullBitmap, shortHelp = '', longHelp = '', clientData = None):
        return self.DoAddTool(id, '', bitmap, bmpDisabled, wx.ITEM_RADIO, shortHelp, longHelp, clientData)

    def AddToolItem(*args, **kwargs):
        return _controls_.ToolBarBase_AddToolItem(*args, **kwargs)

    def InsertToolItem(*args, **kwargs):
        return _controls_.ToolBarBase_InsertToolItem(*args, **kwargs)

    def AddControl(*args, **kwargs):
        return _controls_.ToolBarBase_AddControl(*args, **kwargs)

    def InsertControl(*args, **kwargs):
        return _controls_.ToolBarBase_InsertControl(*args, **kwargs)

    def FindControl(*args, **kwargs):
        return _controls_.ToolBarBase_FindControl(*args, **kwargs)

    def AddSeparator(*args, **kwargs):
        return _controls_.ToolBarBase_AddSeparator(*args, **kwargs)

    def InsertSeparator(*args, **kwargs):
        return _controls_.ToolBarBase_InsertSeparator(*args, **kwargs)

    def RemoveTool(*args, **kwargs):
        return _controls_.ToolBarBase_RemoveTool(*args, **kwargs)

    def DeleteToolByPos(*args, **kwargs):
        return _controls_.ToolBarBase_DeleteToolByPos(*args, **kwargs)

    def DeleteTool(*args, **kwargs):
        return _controls_.ToolBarBase_DeleteTool(*args, **kwargs)

    def ClearTools(*args, **kwargs):
        return _controls_.ToolBarBase_ClearTools(*args, **kwargs)

    def Realize(*args, **kwargs):
        return _controls_.ToolBarBase_Realize(*args, **kwargs)

    def EnableTool(*args, **kwargs):
        return _controls_.ToolBarBase_EnableTool(*args, **kwargs)

    def ToggleTool(*args, **kwargs):
        return _controls_.ToolBarBase_ToggleTool(*args, **kwargs)

    def SetToggle(*args, **kwargs):
        return _controls_.ToolBarBase_SetToggle(*args, **kwargs)

    def GetToolClientData(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolClientData(*args, **kwargs)

    def SetToolClientData(*args, **kwargs):
        return _controls_.ToolBarBase_SetToolClientData(*args, **kwargs)

    def GetToolPos(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolPos(*args, **kwargs)

    def GetToolState(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolState(*args, **kwargs)

    def GetToolEnabled(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolEnabled(*args, **kwargs)

    def SetToolShortHelp(*args, **kwargs):
        return _controls_.ToolBarBase_SetToolShortHelp(*args, **kwargs)

    def GetToolShortHelp(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolShortHelp(*args, **kwargs)

    def SetToolLongHelp(*args, **kwargs):
        return _controls_.ToolBarBase_SetToolLongHelp(*args, **kwargs)

    def GetToolLongHelp(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolLongHelp(*args, **kwargs)

    def SetMarginsXY(*args, **kwargs):
        return _controls_.ToolBarBase_SetMarginsXY(*args, **kwargs)

    def SetMargins(*args, **kwargs):
        return _controls_.ToolBarBase_SetMargins(*args, **kwargs)

    def SetToolPacking(*args, **kwargs):
        return _controls_.ToolBarBase_SetToolPacking(*args, **kwargs)

    def SetToolSeparation(*args, **kwargs):
        return _controls_.ToolBarBase_SetToolSeparation(*args, **kwargs)

    def GetToolMargins(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolMargins(*args, **kwargs)

    def GetMargins(*args, **kwargs):
        return _controls_.ToolBarBase_GetMargins(*args, **kwargs)

    def GetToolPacking(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolPacking(*args, **kwargs)

    def GetToolSeparation(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolSeparation(*args, **kwargs)

    def SetRows(*args, **kwargs):
        return _controls_.ToolBarBase_SetRows(*args, **kwargs)

    def SetMaxRowsCols(*args, **kwargs):
        return _controls_.ToolBarBase_SetMaxRowsCols(*args, **kwargs)

    def GetMaxRows(*args, **kwargs):
        return _controls_.ToolBarBase_GetMaxRows(*args, **kwargs)

    def GetMaxCols(*args, **kwargs):
        return _controls_.ToolBarBase_GetMaxCols(*args, **kwargs)

    def SetToolBitmapSize(*args, **kwargs):
        return _controls_.ToolBarBase_SetToolBitmapSize(*args, **kwargs)

    def GetToolBitmapSize(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolBitmapSize(*args, **kwargs)

    def GetToolSize(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolSize(*args, **kwargs)

    def FindToolForPosition(*args, **kwargs):
        return _controls_.ToolBarBase_FindToolForPosition(*args, **kwargs)

    def FindById(*args, **kwargs):
        return _controls_.ToolBarBase_FindById(*args, **kwargs)

    def IsVertical(*args, **kwargs):
        return _controls_.ToolBarBase_IsVertical(*args, **kwargs)

    def GetToolsCount(*args, **kwargs):
        return _controls_.ToolBarBase_GetToolsCount(*args, **kwargs)

    Margins = property(GetMargins, SetMargins, doc='See `GetMargins` and `SetMargins`')
    MaxCols = property(GetMaxCols, doc='See `GetMaxCols`')
    MaxRows = property(GetMaxRows, doc='See `GetMaxRows`')
    ToolBitmapSize = property(GetToolBitmapSize, SetToolBitmapSize, doc='See `GetToolBitmapSize` and `SetToolBitmapSize`')
    ToolMargins = property(GetToolMargins, doc='See `GetToolMargins`')
    ToolPacking = property(GetToolPacking, SetToolPacking, doc='See `GetToolPacking` and `SetToolPacking`')
    ToolSeparation = property(GetToolSeparation, SetToolSeparation, doc='See `GetToolSeparation` and `SetToolSeparation`')
    ToolSize = property(GetToolSize, doc='See `GetToolSize`')
    ToolsCount = property(GetToolsCount, doc='See `GetToolsCount`')


_controls_.ToolBarBase_swigregister(ToolBarBase)

class ToolBar(ToolBarBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ToolBar_swiginit(self, _controls_.new_ToolBar(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.ToolBar_Create(*args, **kwargs)

    def SetToolNormalBitmap(*args, **kwargs):
        return _controls_.ToolBar_SetToolNormalBitmap(*args, **kwargs)

    def SetToolDisabledBitmap(*args, **kwargs):
        return _controls_.ToolBar_SetToolDisabledBitmap(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.ToolBar_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_controls_.ToolBar_swigregister(ToolBar)

def PreToolBar(*args, **kwargs):
    val = _controls_.new_PreToolBar(*args, **kwargs)
    return val


def ToolBar_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.ToolBar_GetClassDefaultAttributes(*args, **kwargs)


LC_VRULES = _controls_.LC_VRULES
LC_HRULES = _controls_.LC_HRULES
LC_ICON = _controls_.LC_ICON
LC_SMALL_ICON = _controls_.LC_SMALL_ICON
LC_LIST = _controls_.LC_LIST
LC_REPORT = _controls_.LC_REPORT
LC_ALIGN_TOP = _controls_.LC_ALIGN_TOP
LC_ALIGN_LEFT = _controls_.LC_ALIGN_LEFT
LC_AUTOARRANGE = _controls_.LC_AUTOARRANGE
LC_VIRTUAL = _controls_.LC_VIRTUAL
LC_EDIT_LABELS = _controls_.LC_EDIT_LABELS
LC_NO_HEADER = _controls_.LC_NO_HEADER
LC_NO_SORT_HEADER = _controls_.LC_NO_SORT_HEADER
LC_SINGLE_SEL = _controls_.LC_SINGLE_SEL
LC_SORT_ASCENDING = _controls_.LC_SORT_ASCENDING
LC_SORT_DESCENDING = _controls_.LC_SORT_DESCENDING
LC_MASK_TYPE = _controls_.LC_MASK_TYPE
LC_MASK_ALIGN = _controls_.LC_MASK_ALIGN
LC_MASK_SORT = _controls_.LC_MASK_SORT
LIST_MASK_STATE = _controls_.LIST_MASK_STATE
LIST_MASK_TEXT = _controls_.LIST_MASK_TEXT
LIST_MASK_IMAGE = _controls_.LIST_MASK_IMAGE
LIST_MASK_DATA = _controls_.LIST_MASK_DATA
LIST_SET_ITEM = _controls_.LIST_SET_ITEM
LIST_MASK_WIDTH = _controls_.LIST_MASK_WIDTH
LIST_MASK_FORMAT = _controls_.LIST_MASK_FORMAT
LIST_STATE_DONTCARE = _controls_.LIST_STATE_DONTCARE
LIST_STATE_DROPHILITED = _controls_.LIST_STATE_DROPHILITED
LIST_STATE_FOCUSED = _controls_.LIST_STATE_FOCUSED
LIST_STATE_SELECTED = _controls_.LIST_STATE_SELECTED
LIST_STATE_CUT = _controls_.LIST_STATE_CUT
LIST_STATE_DISABLED = _controls_.LIST_STATE_DISABLED
LIST_STATE_FILTERED = _controls_.LIST_STATE_FILTERED
LIST_STATE_INUSE = _controls_.LIST_STATE_INUSE
LIST_STATE_PICKED = _controls_.LIST_STATE_PICKED
LIST_STATE_SOURCE = _controls_.LIST_STATE_SOURCE
LIST_HITTEST_ABOVE = _controls_.LIST_HITTEST_ABOVE
LIST_HITTEST_BELOW = _controls_.LIST_HITTEST_BELOW
LIST_HITTEST_NOWHERE = _controls_.LIST_HITTEST_NOWHERE
LIST_HITTEST_ONITEMICON = _controls_.LIST_HITTEST_ONITEMICON
LIST_HITTEST_ONITEMLABEL = _controls_.LIST_HITTEST_ONITEMLABEL
LIST_HITTEST_ONITEMRIGHT = _controls_.LIST_HITTEST_ONITEMRIGHT
LIST_HITTEST_ONITEMSTATEICON = _controls_.LIST_HITTEST_ONITEMSTATEICON
LIST_HITTEST_TOLEFT = _controls_.LIST_HITTEST_TOLEFT
LIST_HITTEST_TORIGHT = _controls_.LIST_HITTEST_TORIGHT
LIST_HITTEST_ONITEM = _controls_.LIST_HITTEST_ONITEM
LIST_GETSUBITEMRECT_WHOLEITEM = _controls_.LIST_GETSUBITEMRECT_WHOLEITEM
LIST_NEXT_ABOVE = _controls_.LIST_NEXT_ABOVE
LIST_NEXT_ALL = _controls_.LIST_NEXT_ALL
LIST_NEXT_BELOW = _controls_.LIST_NEXT_BELOW
LIST_NEXT_LEFT = _controls_.LIST_NEXT_LEFT
LIST_NEXT_RIGHT = _controls_.LIST_NEXT_RIGHT
LIST_ALIGN_DEFAULT = _controls_.LIST_ALIGN_DEFAULT
LIST_ALIGN_LEFT = _controls_.LIST_ALIGN_LEFT
LIST_ALIGN_TOP = _controls_.LIST_ALIGN_TOP
LIST_ALIGN_SNAP_TO_GRID = _controls_.LIST_ALIGN_SNAP_TO_GRID
LIST_FORMAT_LEFT = _controls_.LIST_FORMAT_LEFT
LIST_FORMAT_RIGHT = _controls_.LIST_FORMAT_RIGHT
LIST_FORMAT_CENTRE = _controls_.LIST_FORMAT_CENTRE
LIST_FORMAT_CENTER = _controls_.LIST_FORMAT_CENTER
LIST_AUTOSIZE = _controls_.LIST_AUTOSIZE
LIST_AUTOSIZE_USEHEADER = _controls_.LIST_AUTOSIZE_USEHEADER
LIST_RECT_BOUNDS = _controls_.LIST_RECT_BOUNDS
LIST_RECT_ICON = _controls_.LIST_RECT_ICON
LIST_RECT_LABEL = _controls_.LIST_RECT_LABEL
LIST_FIND_UP = _controls_.LIST_FIND_UP
LIST_FIND_DOWN = _controls_.LIST_FIND_DOWN
LIST_FIND_LEFT = _controls_.LIST_FIND_LEFT
LIST_FIND_RIGHT = _controls_.LIST_FIND_RIGHT

class ListItemAttr(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ListItemAttr_swiginit(self, _controls_.new_ListItemAttr(*args, **kwargs))

    __swig_destroy__ = _controls_.delete_ListItemAttr
    __del__ = lambda self: None

    def SetTextColour(*args, **kwargs):
        return _controls_.ListItemAttr_SetTextColour(*args, **kwargs)

    def SetBackgroundColour(*args, **kwargs):
        return _controls_.ListItemAttr_SetBackgroundColour(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _controls_.ListItemAttr_SetFont(*args, **kwargs)

    def HasTextColour(*args, **kwargs):
        return _controls_.ListItemAttr_HasTextColour(*args, **kwargs)

    def HasBackgroundColour(*args, **kwargs):
        return _controls_.ListItemAttr_HasBackgroundColour(*args, **kwargs)

    def HasFont(*args, **kwargs):
        return _controls_.ListItemAttr_HasFont(*args, **kwargs)

    def GetTextColour(*args, **kwargs):
        return _controls_.ListItemAttr_GetTextColour(*args, **kwargs)

    def GetBackgroundColour(*args, **kwargs):
        return _controls_.ListItemAttr_GetBackgroundColour(*args, **kwargs)

    def GetFont(*args, **kwargs):
        return _controls_.ListItemAttr_GetFont(*args, **kwargs)

    def AssignFrom(*args, **kwargs):
        return _controls_.ListItemAttr_AssignFrom(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _controls_.ListItemAttr_Destroy(*args, **kwargs)

    BackgroundColour = property(GetBackgroundColour, SetBackgroundColour, doc='See `GetBackgroundColour` and `SetBackgroundColour`')
    Font = property(GetFont, SetFont, doc='See `GetFont` and `SetFont`')
    TextColour = property(GetTextColour, SetTextColour, doc='See `GetTextColour` and `SetTextColour`')


_controls_.ListItemAttr_swigregister(ListItemAttr)
ListCtrlNameStr = cvar.ListCtrlNameStr

class ListItem(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ListItem_swiginit(self, _controls_.new_ListItem(*args, **kwargs))

    __swig_destroy__ = _controls_.delete_ListItem
    __del__ = lambda self: None

    def Clear(*args, **kwargs):
        return _controls_.ListItem_Clear(*args, **kwargs)

    def ClearAttributes(*args, **kwargs):
        return _controls_.ListItem_ClearAttributes(*args, **kwargs)

    def SetMask(*args, **kwargs):
        return _controls_.ListItem_SetMask(*args, **kwargs)

    def SetId(*args, **kwargs):
        return _controls_.ListItem_SetId(*args, **kwargs)

    def SetColumn(*args, **kwargs):
        return _controls_.ListItem_SetColumn(*args, **kwargs)

    def SetState(*args, **kwargs):
        return _controls_.ListItem_SetState(*args, **kwargs)

    def SetStateMask(*args, **kwargs):
        return _controls_.ListItem_SetStateMask(*args, **kwargs)

    def SetText(*args, **kwargs):
        return _controls_.ListItem_SetText(*args, **kwargs)

    def SetImage(*args, **kwargs):
        return _controls_.ListItem_SetImage(*args, **kwargs)

    def SetData(*args, **kwargs):
        return _controls_.ListItem_SetData(*args, **kwargs)

    def SetWidth(*args, **kwargs):
        return _controls_.ListItem_SetWidth(*args, **kwargs)

    def SetAlign(*args, **kwargs):
        return _controls_.ListItem_SetAlign(*args, **kwargs)

    def SetTextColour(*args, **kwargs):
        return _controls_.ListItem_SetTextColour(*args, **kwargs)

    def SetBackgroundColour(*args, **kwargs):
        return _controls_.ListItem_SetBackgroundColour(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _controls_.ListItem_SetFont(*args, **kwargs)

    def GetMask(*args, **kwargs):
        return _controls_.ListItem_GetMask(*args, **kwargs)

    def GetId(*args, **kwargs):
        return _controls_.ListItem_GetId(*args, **kwargs)

    def GetColumn(*args, **kwargs):
        return _controls_.ListItem_GetColumn(*args, **kwargs)

    def GetState(*args, **kwargs):
        return _controls_.ListItem_GetState(*args, **kwargs)

    def GetText(*args, **kwargs):
        return _controls_.ListItem_GetText(*args, **kwargs)

    def GetImage(*args, **kwargs):
        return _controls_.ListItem_GetImage(*args, **kwargs)

    def GetData(*args, **kwargs):
        return _controls_.ListItem_GetData(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _controls_.ListItem_GetWidth(*args, **kwargs)

    def GetAlign(*args, **kwargs):
        return _controls_.ListItem_GetAlign(*args, **kwargs)

    def GetAttributes(*args, **kwargs):
        return _controls_.ListItem_GetAttributes(*args, **kwargs)

    def HasAttributes(*args, **kwargs):
        return _controls_.ListItem_HasAttributes(*args, **kwargs)

    def GetTextColour(*args, **kwargs):
        return _controls_.ListItem_GetTextColour(*args, **kwargs)

    def GetBackgroundColour(*args, **kwargs):
        return _controls_.ListItem_GetBackgroundColour(*args, **kwargs)

    def GetFont(*args, **kwargs):
        return _controls_.ListItem_GetFont(*args, **kwargs)

    m_mask = property(_controls_.ListItem_m_mask_get, _controls_.ListItem_m_mask_set)
    m_itemId = property(_controls_.ListItem_m_itemId_get, _controls_.ListItem_m_itemId_set)
    m_col = property(_controls_.ListItem_m_col_get, _controls_.ListItem_m_col_set)
    m_state = property(_controls_.ListItem_m_state_get, _controls_.ListItem_m_state_set)
    m_stateMask = property(_controls_.ListItem_m_stateMask_get, _controls_.ListItem_m_stateMask_set)
    m_text = property(_controls_.ListItem_m_text_get, _controls_.ListItem_m_text_set)
    m_image = property(_controls_.ListItem_m_image_get, _controls_.ListItem_m_image_set)
    m_data = property(_controls_.ListItem_m_data_get, _controls_.ListItem_m_data_set)
    m_format = property(_controls_.ListItem_m_format_get, _controls_.ListItem_m_format_set)
    m_width = property(_controls_.ListItem_m_width_get, _controls_.ListItem_m_width_set)
    Align = property(GetAlign, SetAlign, doc='See `GetAlign` and `SetAlign`')
    Attributes = property(GetAttributes, doc='See `GetAttributes`')
    BackgroundColour = property(GetBackgroundColour, SetBackgroundColour, doc='See `GetBackgroundColour` and `SetBackgroundColour`')
    Column = property(GetColumn, SetColumn, doc='See `GetColumn` and `SetColumn`')
    Data = property(GetData, SetData, doc='See `GetData` and `SetData`')
    Font = property(GetFont, SetFont, doc='See `GetFont` and `SetFont`')
    Id = property(GetId, SetId, doc='See `GetId` and `SetId`')
    Image = property(GetImage, SetImage, doc='See `GetImage` and `SetImage`')
    Mask = property(GetMask, SetMask, doc='See `GetMask` and `SetMask`')
    State = property(GetState, SetState, doc='See `GetState` and `SetState`')
    Text = property(GetText, SetText, doc='See `GetText` and `SetText`')
    TextColour = property(GetTextColour, SetTextColour, doc='See `GetTextColour` and `SetTextColour`')
    Width = property(GetWidth, SetWidth, doc='See `GetWidth` and `SetWidth`')


_controls_.ListItem_swigregister(ListItem)

class ListEvent(_core.NotifyEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ListEvent_swiginit(self, _controls_.new_ListEvent(*args, **kwargs))

    m_code = property(_controls_.ListEvent_m_code_get, _controls_.ListEvent_m_code_set)
    m_oldItemIndex = property(_controls_.ListEvent_m_oldItemIndex_get, _controls_.ListEvent_m_oldItemIndex_set)
    m_itemIndex = property(_controls_.ListEvent_m_itemIndex_get, _controls_.ListEvent_m_itemIndex_set)
    m_col = property(_controls_.ListEvent_m_col_get, _controls_.ListEvent_m_col_set)
    m_pointDrag = property(_controls_.ListEvent_m_pointDrag_get, _controls_.ListEvent_m_pointDrag_set)
    m_item = property(_controls_.ListEvent_m_item_get)

    def GetKeyCode(*args, **kwargs):
        return _controls_.ListEvent_GetKeyCode(*args, **kwargs)

    GetCode = GetKeyCode

    def GetIndex(*args, **kwargs):
        return _controls_.ListEvent_GetIndex(*args, **kwargs)

    def GetColumn(*args, **kwargs):
        return _controls_.ListEvent_GetColumn(*args, **kwargs)

    def GetPoint(*args, **kwargs):
        return _controls_.ListEvent_GetPoint(*args, **kwargs)

    GetPosition = GetPoint

    def GetLabel(*args, **kwargs):
        return _controls_.ListEvent_GetLabel(*args, **kwargs)

    def GetText(*args, **kwargs):
        return _controls_.ListEvent_GetText(*args, **kwargs)

    def GetImage(*args, **kwargs):
        return _controls_.ListEvent_GetImage(*args, **kwargs)

    def GetData(*args, **kwargs):
        return _controls_.ListEvent_GetData(*args, **kwargs)

    def GetMask(*args, **kwargs):
        return _controls_.ListEvent_GetMask(*args, **kwargs)

    def GetItem(*args, **kwargs):
        return _controls_.ListEvent_GetItem(*args, **kwargs)

    def GetCacheFrom(*args, **kwargs):
        return _controls_.ListEvent_GetCacheFrom(*args, **kwargs)

    def GetCacheTo(*args, **kwargs):
        return _controls_.ListEvent_GetCacheTo(*args, **kwargs)

    def IsEditCancelled(*args, **kwargs):
        return _controls_.ListEvent_IsEditCancelled(*args, **kwargs)

    def SetEditCanceled(*args, **kwargs):
        return _controls_.ListEvent_SetEditCanceled(*args, **kwargs)

    CacheFrom = property(GetCacheFrom, doc='See `GetCacheFrom`')
    CacheTo = property(GetCacheTo, doc='See `GetCacheTo`')
    Column = property(GetColumn, doc='See `GetColumn`')
    Data = property(GetData, doc='See `GetData`')
    Image = property(GetImage, doc='See `GetImage`')
    Index = property(GetIndex, doc='See `GetIndex`')
    Item = property(GetItem, doc='See `GetItem`')
    KeyCode = property(GetKeyCode, doc='See `GetKeyCode`')
    Label = property(GetLabel, doc='See `GetLabel`')
    Mask = property(GetMask, doc='See `GetMask`')
    Point = property(GetPoint, doc='See `GetPoint`')
    Text = property(GetText, doc='See `GetText`')


_controls_.ListEvent_swigregister(ListEvent)
wxEVT_COMMAND_LIST_BEGIN_DRAG = _controls_.wxEVT_COMMAND_LIST_BEGIN_DRAG
wxEVT_COMMAND_LIST_BEGIN_RDRAG = _controls_.wxEVT_COMMAND_LIST_BEGIN_RDRAG
wxEVT_COMMAND_LIST_BEGIN_LABEL_EDIT = _controls_.wxEVT_COMMAND_LIST_BEGIN_LABEL_EDIT
wxEVT_COMMAND_LIST_END_LABEL_EDIT = _controls_.wxEVT_COMMAND_LIST_END_LABEL_EDIT
wxEVT_COMMAND_LIST_DELETE_ITEM = _controls_.wxEVT_COMMAND_LIST_DELETE_ITEM
wxEVT_COMMAND_LIST_DELETE_ALL_ITEMS = _controls_.wxEVT_COMMAND_LIST_DELETE_ALL_ITEMS
wxEVT_COMMAND_LIST_ITEM_SELECTED = _controls_.wxEVT_COMMAND_LIST_ITEM_SELECTED
wxEVT_COMMAND_LIST_ITEM_DESELECTED = _controls_.wxEVT_COMMAND_LIST_ITEM_DESELECTED
wxEVT_COMMAND_LIST_KEY_DOWN = _controls_.wxEVT_COMMAND_LIST_KEY_DOWN
wxEVT_COMMAND_LIST_INSERT_ITEM = _controls_.wxEVT_COMMAND_LIST_INSERT_ITEM
wxEVT_COMMAND_LIST_COL_CLICK = _controls_.wxEVT_COMMAND_LIST_COL_CLICK
wxEVT_COMMAND_LIST_ITEM_RIGHT_CLICK = _controls_.wxEVT_COMMAND_LIST_ITEM_RIGHT_CLICK
wxEVT_COMMAND_LIST_ITEM_MIDDLE_CLICK = _controls_.wxEVT_COMMAND_LIST_ITEM_MIDDLE_CLICK
wxEVT_COMMAND_LIST_ITEM_ACTIVATED = _controls_.wxEVT_COMMAND_LIST_ITEM_ACTIVATED
wxEVT_COMMAND_LIST_CACHE_HINT = _controls_.wxEVT_COMMAND_LIST_CACHE_HINT
wxEVT_COMMAND_LIST_COL_RIGHT_CLICK = _controls_.wxEVT_COMMAND_LIST_COL_RIGHT_CLICK
wxEVT_COMMAND_LIST_COL_BEGIN_DRAG = _controls_.wxEVT_COMMAND_LIST_COL_BEGIN_DRAG
wxEVT_COMMAND_LIST_COL_DRAGGING = _controls_.wxEVT_COMMAND_LIST_COL_DRAGGING
wxEVT_COMMAND_LIST_COL_END_DRAG = _controls_.wxEVT_COMMAND_LIST_COL_END_DRAG
wxEVT_COMMAND_LIST_ITEM_FOCUSED = _controls_.wxEVT_COMMAND_LIST_ITEM_FOCUSED
EVT_LIST_BEGIN_DRAG = wx.PyEventBinder(wxEVT_COMMAND_LIST_BEGIN_DRAG, 1)
EVT_LIST_BEGIN_RDRAG = wx.PyEventBinder(wxEVT_COMMAND_LIST_BEGIN_RDRAG, 1)
EVT_LIST_BEGIN_LABEL_EDIT = wx.PyEventBinder(wxEVT_COMMAND_LIST_BEGIN_LABEL_EDIT, 1)
EVT_LIST_END_LABEL_EDIT = wx.PyEventBinder(wxEVT_COMMAND_LIST_END_LABEL_EDIT, 1)
EVT_LIST_DELETE_ITEM = wx.PyEventBinder(wxEVT_COMMAND_LIST_DELETE_ITEM, 1)
EVT_LIST_DELETE_ALL_ITEMS = wx.PyEventBinder(wxEVT_COMMAND_LIST_DELETE_ALL_ITEMS, 1)
EVT_LIST_ITEM_SELECTED = wx.PyEventBinder(wxEVT_COMMAND_LIST_ITEM_SELECTED, 1)
EVT_LIST_ITEM_DESELECTED = wx.PyEventBinder(wxEVT_COMMAND_LIST_ITEM_DESELECTED, 1)
EVT_LIST_KEY_DOWN = wx.PyEventBinder(wxEVT_COMMAND_LIST_KEY_DOWN, 1)
EVT_LIST_INSERT_ITEM = wx.PyEventBinder(wxEVT_COMMAND_LIST_INSERT_ITEM, 1)
EVT_LIST_COL_CLICK = wx.PyEventBinder(wxEVT_COMMAND_LIST_COL_CLICK, 1)
EVT_LIST_ITEM_RIGHT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_LIST_ITEM_RIGHT_CLICK, 1)
EVT_LIST_ITEM_MIDDLE_CLICK = wx.PyEventBinder(wxEVT_COMMAND_LIST_ITEM_MIDDLE_CLICK, 1)
EVT_LIST_ITEM_ACTIVATED = wx.PyEventBinder(wxEVT_COMMAND_LIST_ITEM_ACTIVATED, 1)
EVT_LIST_CACHE_HINT = wx.PyEventBinder(wxEVT_COMMAND_LIST_CACHE_HINT, 1)
EVT_LIST_COL_RIGHT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_LIST_COL_RIGHT_CLICK, 1)
EVT_LIST_COL_BEGIN_DRAG = wx.PyEventBinder(wxEVT_COMMAND_LIST_COL_BEGIN_DRAG, 1)
EVT_LIST_COL_DRAGGING = wx.PyEventBinder(wxEVT_COMMAND_LIST_COL_DRAGGING, 1)
EVT_LIST_COL_END_DRAG = wx.PyEventBinder(wxEVT_COMMAND_LIST_COL_END_DRAG, 1)
EVT_LIST_ITEM_FOCUSED = wx.PyEventBinder(wxEVT_COMMAND_LIST_ITEM_FOCUSED, 1)

class ListCtrl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ListCtrl_swiginit(self, _controls_.new_ListCtrl(*args, **kwargs))
        self._setOORInfo(self)
        ListCtrl._setCallbackInfo(self, self, ListCtrl)

    def Create(*args, **kwargs):
        return _controls_.ListCtrl_Create(*args, **kwargs)

    def _setCallbackInfo(*args, **kwargs):
        return _controls_.ListCtrl__setCallbackInfo(*args, **kwargs)

    def GetColumn(*args, **kwargs):
        val = _controls_.ListCtrl_GetColumn(*args, **kwargs)
        if val is not None:
            val.thisown = 1
        return val

    def SetColumn(*args, **kwargs):
        return _controls_.ListCtrl_SetColumn(*args, **kwargs)

    def GetColumnWidth(*args, **kwargs):
        return _controls_.ListCtrl_GetColumnWidth(*args, **kwargs)

    def SetColumnWidth(*args, **kwargs):
        return _controls_.ListCtrl_SetColumnWidth(*args, **kwargs)

    def GetCountPerPage(*args, **kwargs):
        return _controls_.ListCtrl_GetCountPerPage(*args, **kwargs)

    def GetViewRect(*args, **kwargs):
        return _controls_.ListCtrl_GetViewRect(*args, **kwargs)

    def GetEditControl(*args, **kwargs):
        return _controls_.ListCtrl_GetEditControl(*args, **kwargs)

    def GetItem(*args, **kwargs):
        val = _controls_.ListCtrl_GetItem(*args, **kwargs)
        if val is not None:
            val.thisown = 1
        return val

    def SetItem(*args, **kwargs):
        return _controls_.ListCtrl_SetItem(*args, **kwargs)

    def SetStringItem(*args, **kwargs):
        return _controls_.ListCtrl_SetStringItem(*args, **kwargs)

    def GetItemState(*args, **kwargs):
        return _controls_.ListCtrl_GetItemState(*args, **kwargs)

    def SetItemState(*args, **kwargs):
        return _controls_.ListCtrl_SetItemState(*args, **kwargs)

    def SetItemImage(*args, **kwargs):
        return _controls_.ListCtrl_SetItemImage(*args, **kwargs)

    def SetItemColumnImage(*args, **kwargs):
        return _controls_.ListCtrl_SetItemColumnImage(*args, **kwargs)

    def GetItemText(*args, **kwargs):
        return _controls_.ListCtrl_GetItemText(*args, **kwargs)

    def SetItemText(*args, **kwargs):
        return _controls_.ListCtrl_SetItemText(*args, **kwargs)

    def GetItemData(*args, **kwargs):
        return _controls_.ListCtrl_GetItemData(*args, **kwargs)

    def SetItemData(*args, **kwargs):
        return _controls_.ListCtrl_SetItemData(*args, **kwargs)

    def GetItemPosition(*args, **kwargs):
        return _controls_.ListCtrl_GetItemPosition(*args, **kwargs)

    def GetItemRect(*args, **kwargs):
        return _controls_.ListCtrl_GetItemRect(*args, **kwargs)

    def SetItemPosition(*args, **kwargs):
        return _controls_.ListCtrl_SetItemPosition(*args, **kwargs)

    def GetItemCount(*args, **kwargs):
        return _controls_.ListCtrl_GetItemCount(*args, **kwargs)

    def GetColumnCount(*args, **kwargs):
        return _controls_.ListCtrl_GetColumnCount(*args, **kwargs)

    def GetItemSpacing(*args, **kwargs):
        return _controls_.ListCtrl_GetItemSpacing(*args, **kwargs)

    def SetItemSpacing(*args, **kwargs):
        return _controls_.ListCtrl_SetItemSpacing(*args, **kwargs)

    def GetSelectedItemCount(*args, **kwargs):
        return _controls_.ListCtrl_GetSelectedItemCount(*args, **kwargs)

    def GetTextColour(*args, **kwargs):
        return _controls_.ListCtrl_GetTextColour(*args, **kwargs)

    def SetTextColour(*args, **kwargs):
        return _controls_.ListCtrl_SetTextColour(*args, **kwargs)

    def GetTopItem(*args, **kwargs):
        return _controls_.ListCtrl_GetTopItem(*args, **kwargs)

    def SetSingleStyle(*args, **kwargs):
        return _controls_.ListCtrl_SetSingleStyle(*args, **kwargs)

    def GetNextItem(*args, **kwargs):
        return _controls_.ListCtrl_GetNextItem(*args, **kwargs)

    def GetImageList(*args, **kwargs):
        return _controls_.ListCtrl_GetImageList(*args, **kwargs)

    def SetImageList(*args, **kwargs):
        return _controls_.ListCtrl_SetImageList(*args, **kwargs)

    def AssignImageList(*args, **kwargs):
        return _controls_.ListCtrl_AssignImageList(*args, **kwargs)

    def InReportView(*args, **kwargs):
        return _controls_.ListCtrl_InReportView(*args, **kwargs)

    def IsVirtual(*args, **kwargs):
        return _controls_.ListCtrl_IsVirtual(*args, **kwargs)

    def RefreshItem(*args, **kwargs):
        return _controls_.ListCtrl_RefreshItem(*args, **kwargs)

    def RefreshItems(*args, **kwargs):
        return _controls_.ListCtrl_RefreshItems(*args, **kwargs)

    def Arrange(*args, **kwargs):
        return _controls_.ListCtrl_Arrange(*args, **kwargs)

    def DeleteItem(*args, **kwargs):
        return _controls_.ListCtrl_DeleteItem(*args, **kwargs)

    def DeleteAllItems(*args, **kwargs):
        return _controls_.ListCtrl_DeleteAllItems(*args, **kwargs)

    def DeleteColumn(*args, **kwargs):
        return _controls_.ListCtrl_DeleteColumn(*args, **kwargs)

    def DeleteAllColumns(*args, **kwargs):
        return _controls_.ListCtrl_DeleteAllColumns(*args, **kwargs)

    def ClearAll(*args, **kwargs):
        return _controls_.ListCtrl_ClearAll(*args, **kwargs)

    def EditLabel(*args, **kwargs):
        return _controls_.ListCtrl_EditLabel(*args, **kwargs)

    def EnsureVisible(*args, **kwargs):
        return _controls_.ListCtrl_EnsureVisible(*args, **kwargs)

    def FindItem(*args, **kwargs):
        return _controls_.ListCtrl_FindItem(*args, **kwargs)

    def FindItemData(*args, **kwargs):
        return _controls_.ListCtrl_FindItemData(*args, **kwargs)

    def FindItemAtPos(*args, **kwargs):
        return _controls_.ListCtrl_FindItemAtPos(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _controls_.ListCtrl_HitTest(*args, **kwargs)

    def HitTestSubItem(*args, **kwargs):
        return _controls_.ListCtrl_HitTestSubItem(*args, **kwargs)

    def InsertItem(*args, **kwargs):
        return _controls_.ListCtrl_InsertItem(*args, **kwargs)

    def InsertStringItem(*args, **kwargs):
        return _controls_.ListCtrl_InsertStringItem(*args, **kwargs)

    def InsertImageItem(*args, **kwargs):
        return _controls_.ListCtrl_InsertImageItem(*args, **kwargs)

    def InsertImageStringItem(*args, **kwargs):
        return _controls_.ListCtrl_InsertImageStringItem(*args, **kwargs)

    def InsertColumnItem(*args, **kwargs):
        return _controls_.ListCtrl_InsertColumnItem(*args, **kwargs)

    InsertColumnInfo = InsertColumnItem

    def InsertColumn(*args, **kwargs):
        return _controls_.ListCtrl_InsertColumn(*args, **kwargs)

    def SetItemCount(*args, **kwargs):
        return _controls_.ListCtrl_SetItemCount(*args, **kwargs)

    def ScrollList(*args, **kwargs):
        return _controls_.ListCtrl_ScrollList(*args, **kwargs)

    def SetItemTextColour(*args, **kwargs):
        return _controls_.ListCtrl_SetItemTextColour(*args, **kwargs)

    def GetItemTextColour(*args, **kwargs):
        return _controls_.ListCtrl_GetItemTextColour(*args, **kwargs)

    def SetItemBackgroundColour(*args, **kwargs):
        return _controls_.ListCtrl_SetItemBackgroundColour(*args, **kwargs)

    def GetItemBackgroundColour(*args, **kwargs):
        return _controls_.ListCtrl_GetItemBackgroundColour(*args, **kwargs)

    def SetItemFont(*args, **kwargs):
        return _controls_.ListCtrl_SetItemFont(*args, **kwargs)

    def GetItemFont(*args, **kwargs):
        return _controls_.ListCtrl_GetItemFont(*args, **kwargs)

    def Select(self, idx, on = 1):
        if on:
            state = wx.LIST_STATE_SELECTED
        else:
            state = 0
        self.SetItemState(idx, state, wx.LIST_STATE_SELECTED)

    def Focus(self, idx):
        self.SetItemState(idx, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED)
        self.EnsureVisible(idx)

    def GetFocusedItem(self):
        return self.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_FOCUSED)

    def GetFirstSelected(self, *args):
        return self.GetNextSelected(-1)

    def GetNextSelected(self, item):
        return self.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)

    def IsSelected(self, idx):
        return self.GetItemState(idx, wx.LIST_STATE_SELECTED) & wx.LIST_STATE_SELECTED != 0

    def SetColumnImage(self, col, image):
        item = self.GetColumn(col)
        item.SetMask(wx.LIST_MASK_STATE | wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_DATA | wx.LIST_SET_ITEM | wx.LIST_MASK_WIDTH | wx.LIST_MASK_FORMAT)
        item.SetImage(image)
        self.SetColumn(col, item)

    def ClearColumnImage(self, col):
        self.SetColumnImage(col, -1)

    def Append(self, entry):
        if len(entry):
            if wx.USE_UNICODE:
                cvtfunc = unicode
            else:
                cvtfunc = str
            pos = self.GetItemCount()
            self.InsertStringItem(pos, cvtfunc(entry[0]))
            for i in range(1, len(entry)):
                self.SetStringItem(pos, i, cvtfunc(entry[i]))

            return pos

    def SortItems(*args, **kwargs):
        return _controls_.ListCtrl_SortItems(*args, **kwargs)

    def GetMainWindow(*args, **kwargs):
        return _controls_.ListCtrl_GetMainWindow(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.ListCtrl_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    ColumnCount = property(GetColumnCount, doc='See `GetColumnCount`')
    CountPerPage = property(GetCountPerPage, doc='See `GetCountPerPage`')
    EditControl = property(GetEditControl, doc='See `GetEditControl`')
    FocusedItem = property(GetFocusedItem, doc='See `GetFocusedItem`')
    ItemCount = property(GetItemCount, SetItemCount, doc='See `GetItemCount` and `SetItemCount`')
    MainWindow = property(GetMainWindow, doc='See `GetMainWindow`')
    SelectedItemCount = property(GetSelectedItemCount, doc='See `GetSelectedItemCount`')
    TextColour = property(GetTextColour, SetTextColour, doc='See `GetTextColour` and `SetTextColour`')
    TopItem = property(GetTopItem, doc='See `GetTopItem`')
    ViewRect = property(GetViewRect, doc='See `GetViewRect`')


_controls_.ListCtrl_swigregister(ListCtrl)

def PreListCtrl(*args, **kwargs):
    val = _controls_.new_PreListCtrl(*args, **kwargs)
    return val


def ListCtrl_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.ListCtrl_GetClassDefaultAttributes(*args, **kwargs)


class ListView(ListCtrl):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ListView_swiginit(self, _controls_.new_ListView(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.ListView_Create(*args, **kwargs)

    def Select(*args, **kwargs):
        return _controls_.ListView_Select(*args, **kwargs)

    def Focus(*args, **kwargs):
        return _controls_.ListView_Focus(*args, **kwargs)

    def GetFocusedItem(*args, **kwargs):
        return _controls_.ListView_GetFocusedItem(*args, **kwargs)

    def GetNextSelected(*args, **kwargs):
        return _controls_.ListView_GetNextSelected(*args, **kwargs)

    def GetFirstSelected(*args, **kwargs):
        return _controls_.ListView_GetFirstSelected(*args, **kwargs)

    def IsSelected(*args, **kwargs):
        return _controls_.ListView_IsSelected(*args, **kwargs)

    def SetColumnImage(*args, **kwargs):
        return _controls_.ListView_SetColumnImage(*args, **kwargs)

    def ClearColumnImage(*args, **kwargs):
        return _controls_.ListView_ClearColumnImage(*args, **kwargs)

    FocusedItem = property(GetFocusedItem, doc='See `GetFocusedItem`')


_controls_.ListView_swigregister(ListView)

def PreListView(*args, **kwargs):
    val = _controls_.new_PreListView(*args, **kwargs)
    return val


TR_NO_BUTTONS = _controls_.TR_NO_BUTTONS
TR_HAS_BUTTONS = _controls_.TR_HAS_BUTTONS
TR_NO_LINES = _controls_.TR_NO_LINES
TR_LINES_AT_ROOT = _controls_.TR_LINES_AT_ROOT
TR_SINGLE = _controls_.TR_SINGLE
TR_MULTIPLE = _controls_.TR_MULTIPLE
TR_EXTENDED = _controls_.TR_EXTENDED
TR_HAS_VARIABLE_ROW_HEIGHT = _controls_.TR_HAS_VARIABLE_ROW_HEIGHT
TR_EDIT_LABELS = _controls_.TR_EDIT_LABELS
TR_HIDE_ROOT = _controls_.TR_HIDE_ROOT
TR_ROW_LINES = _controls_.TR_ROW_LINES
TR_FULL_ROW_HIGHLIGHT = _controls_.TR_FULL_ROW_HIGHLIGHT
TR_DEFAULT_STYLE = _controls_.TR_DEFAULT_STYLE
TR_TWIST_BUTTONS = _controls_.TR_TWIST_BUTTONS
TR_MAC_BUTTONS = 0
wxTR_AQUA_BUTTONS = 0
TreeItemIcon_Normal = _controls_.TreeItemIcon_Normal
TreeItemIcon_Selected = _controls_.TreeItemIcon_Selected
TreeItemIcon_Expanded = _controls_.TreeItemIcon_Expanded
TreeItemIcon_SelectedExpanded = _controls_.TreeItemIcon_SelectedExpanded
TreeItemIcon_Max = _controls_.TreeItemIcon_Max
TREE_HITTEST_ABOVE = _controls_.TREE_HITTEST_ABOVE
TREE_HITTEST_BELOW = _controls_.TREE_HITTEST_BELOW
TREE_HITTEST_NOWHERE = _controls_.TREE_HITTEST_NOWHERE
TREE_HITTEST_ONITEMBUTTON = _controls_.TREE_HITTEST_ONITEMBUTTON
TREE_HITTEST_ONITEMICON = _controls_.TREE_HITTEST_ONITEMICON
TREE_HITTEST_ONITEMINDENT = _controls_.TREE_HITTEST_ONITEMINDENT
TREE_HITTEST_ONITEMLABEL = _controls_.TREE_HITTEST_ONITEMLABEL
TREE_HITTEST_ONITEMRIGHT = _controls_.TREE_HITTEST_ONITEMRIGHT
TREE_HITTEST_ONITEMSTATEICON = _controls_.TREE_HITTEST_ONITEMSTATEICON
TREE_HITTEST_TOLEFT = _controls_.TREE_HITTEST_TOLEFT
TREE_HITTEST_TORIGHT = _controls_.TREE_HITTEST_TORIGHT
TREE_HITTEST_ONITEMUPPERPART = _controls_.TREE_HITTEST_ONITEMUPPERPART
TREE_HITTEST_ONITEMLOWERPART = _controls_.TREE_HITTEST_ONITEMLOWERPART
TREE_HITTEST_ONITEM = _controls_.TREE_HITTEST_ONITEM

class TreeItemId(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.TreeItemId_swiginit(self, _controls_.new_TreeItemId(*args, **kwargs))

    __swig_destroy__ = _controls_.delete_TreeItemId
    __del__ = lambda self: None

    def IsOk(*args, **kwargs):
        return _controls_.TreeItemId_IsOk(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _controls_.TreeItemId___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _controls_.TreeItemId___ne__(*args, **kwargs)

    m_pItem = property(_controls_.TreeItemId_m_pItem_get, _controls_.TreeItemId_m_pItem_set)
    Ok = IsOk

    def __nonzero__(self):
        return self.IsOk()


_controls_.TreeItemId_swigregister(TreeItemId)
TreeCtrlNameStr = cvar.TreeCtrlNameStr

class TreeItemData(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.TreeItemData_swiginit(self, _controls_.new_TreeItemData(*args, **kwargs))

    __swig_destroy__ = _controls_.delete_TreeItemData
    __del__ = lambda self: None

    def GetData(*args, **kwargs):
        return _controls_.TreeItemData_GetData(*args, **kwargs)

    def SetData(*args, **kwargs):
        return _controls_.TreeItemData_SetData(*args, **kwargs)

    def GetId(*args, **kwargs):
        return _controls_.TreeItemData_GetId(*args, **kwargs)

    def SetId(*args, **kwargs):
        return _controls_.TreeItemData_SetId(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _controls_.TreeItemData_Destroy(*args, **kwargs)

    Data = property(GetData, SetData, doc='See `GetData` and `SetData`')
    Id = property(GetId, SetId, doc='See `GetId` and `SetId`')


_controls_.TreeItemData_swigregister(TreeItemData)
wxEVT_COMMAND_TREE_BEGIN_DRAG = _controls_.wxEVT_COMMAND_TREE_BEGIN_DRAG
wxEVT_COMMAND_TREE_BEGIN_RDRAG = _controls_.wxEVT_COMMAND_TREE_BEGIN_RDRAG
wxEVT_COMMAND_TREE_BEGIN_LABEL_EDIT = _controls_.wxEVT_COMMAND_TREE_BEGIN_LABEL_EDIT
wxEVT_COMMAND_TREE_END_LABEL_EDIT = _controls_.wxEVT_COMMAND_TREE_END_LABEL_EDIT
wxEVT_COMMAND_TREE_DELETE_ITEM = _controls_.wxEVT_COMMAND_TREE_DELETE_ITEM
wxEVT_COMMAND_TREE_GET_INFO = _controls_.wxEVT_COMMAND_TREE_GET_INFO
wxEVT_COMMAND_TREE_SET_INFO = _controls_.wxEVT_COMMAND_TREE_SET_INFO
wxEVT_COMMAND_TREE_ITEM_EXPANDED = _controls_.wxEVT_COMMAND_TREE_ITEM_EXPANDED
wxEVT_COMMAND_TREE_ITEM_EXPANDING = _controls_.wxEVT_COMMAND_TREE_ITEM_EXPANDING
wxEVT_COMMAND_TREE_ITEM_COLLAPSED = _controls_.wxEVT_COMMAND_TREE_ITEM_COLLAPSED
wxEVT_COMMAND_TREE_ITEM_COLLAPSING = _controls_.wxEVT_COMMAND_TREE_ITEM_COLLAPSING
wxEVT_COMMAND_TREE_SEL_CHANGED = _controls_.wxEVT_COMMAND_TREE_SEL_CHANGED
wxEVT_COMMAND_TREE_SEL_CHANGING = _controls_.wxEVT_COMMAND_TREE_SEL_CHANGING
wxEVT_COMMAND_TREE_KEY_DOWN = _controls_.wxEVT_COMMAND_TREE_KEY_DOWN
wxEVT_COMMAND_TREE_ITEM_ACTIVATED = _controls_.wxEVT_COMMAND_TREE_ITEM_ACTIVATED
wxEVT_COMMAND_TREE_ITEM_RIGHT_CLICK = _controls_.wxEVT_COMMAND_TREE_ITEM_RIGHT_CLICK
wxEVT_COMMAND_TREE_ITEM_MIDDLE_CLICK = _controls_.wxEVT_COMMAND_TREE_ITEM_MIDDLE_CLICK
wxEVT_COMMAND_TREE_END_DRAG = _controls_.wxEVT_COMMAND_TREE_END_DRAG
wxEVT_COMMAND_TREE_STATE_IMAGE_CLICK = _controls_.wxEVT_COMMAND_TREE_STATE_IMAGE_CLICK
wxEVT_COMMAND_TREE_ITEM_GETTOOLTIP = _controls_.wxEVT_COMMAND_TREE_ITEM_GETTOOLTIP
wxEVT_COMMAND_TREE_ITEM_MENU = _controls_.wxEVT_COMMAND_TREE_ITEM_MENU
EVT_TREE_BEGIN_DRAG = wx.PyEventBinder(wxEVT_COMMAND_TREE_BEGIN_DRAG, 1)
EVT_TREE_BEGIN_RDRAG = wx.PyEventBinder(wxEVT_COMMAND_TREE_BEGIN_RDRAG, 1)
EVT_TREE_BEGIN_LABEL_EDIT = wx.PyEventBinder(wxEVT_COMMAND_TREE_BEGIN_LABEL_EDIT, 1)
EVT_TREE_END_LABEL_EDIT = wx.PyEventBinder(wxEVT_COMMAND_TREE_END_LABEL_EDIT, 1)
EVT_TREE_DELETE_ITEM = wx.PyEventBinder(wxEVT_COMMAND_TREE_DELETE_ITEM, 1)
EVT_TREE_GET_INFO = wx.PyEventBinder(wxEVT_COMMAND_TREE_GET_INFO, 1)
EVT_TREE_SET_INFO = wx.PyEventBinder(wxEVT_COMMAND_TREE_SET_INFO, 1)
EVT_TREE_ITEM_EXPANDED = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_EXPANDED, 1)
EVT_TREE_ITEM_EXPANDING = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_EXPANDING, 1)
EVT_TREE_ITEM_COLLAPSED = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_COLLAPSED, 1)
EVT_TREE_ITEM_COLLAPSING = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_COLLAPSING, 1)
EVT_TREE_SEL_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_TREE_SEL_CHANGED, 1)
EVT_TREE_SEL_CHANGING = wx.PyEventBinder(wxEVT_COMMAND_TREE_SEL_CHANGING, 1)
EVT_TREE_KEY_DOWN = wx.PyEventBinder(wxEVT_COMMAND_TREE_KEY_DOWN, 1)
EVT_TREE_ITEM_ACTIVATED = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_ACTIVATED, 1)
EVT_TREE_ITEM_RIGHT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_RIGHT_CLICK, 1)
EVT_TREE_ITEM_MIDDLE_CLICK = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_MIDDLE_CLICK, 1)
EVT_TREE_END_DRAG = wx.PyEventBinder(wxEVT_COMMAND_TREE_END_DRAG, 1)
EVT_TREE_STATE_IMAGE_CLICK = wx.PyEventBinder(wxEVT_COMMAND_TREE_STATE_IMAGE_CLICK, 1)
EVT_TREE_ITEM_GETTOOLTIP = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_GETTOOLTIP, 1)
EVT_TREE_ITEM_MENU = wx.PyEventBinder(wxEVT_COMMAND_TREE_ITEM_MENU, 1)

class TreeEvent(_core.NotifyEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _controls_.TreeEvent_swiginit(self, _controls_.new_TreeEvent(*args))

    def GetItem(*args, **kwargs):
        return _controls_.TreeEvent_GetItem(*args, **kwargs)

    def SetItem(*args, **kwargs):
        return _controls_.TreeEvent_SetItem(*args, **kwargs)

    def GetOldItem(*args, **kwargs):
        return _controls_.TreeEvent_GetOldItem(*args, **kwargs)

    def SetOldItem(*args, **kwargs):
        return _controls_.TreeEvent_SetOldItem(*args, **kwargs)

    def GetPoint(*args, **kwargs):
        return _controls_.TreeEvent_GetPoint(*args, **kwargs)

    def SetPoint(*args, **kwargs):
        return _controls_.TreeEvent_SetPoint(*args, **kwargs)

    def GetKeyEvent(*args, **kwargs):
        return _controls_.TreeEvent_GetKeyEvent(*args, **kwargs)

    def GetKeyCode(*args, **kwargs):
        return _controls_.TreeEvent_GetKeyCode(*args, **kwargs)

    def SetKeyEvent(*args, **kwargs):
        return _controls_.TreeEvent_SetKeyEvent(*args, **kwargs)

    def GetLabel(*args, **kwargs):
        return _controls_.TreeEvent_GetLabel(*args, **kwargs)

    def SetLabel(*args, **kwargs):
        return _controls_.TreeEvent_SetLabel(*args, **kwargs)

    def IsEditCancelled(*args, **kwargs):
        return _controls_.TreeEvent_IsEditCancelled(*args, **kwargs)

    def SetEditCanceled(*args, **kwargs):
        return _controls_.TreeEvent_SetEditCanceled(*args, **kwargs)

    def SetToolTip(*args, **kwargs):
        return _controls_.TreeEvent_SetToolTip(*args, **kwargs)

    def GetToolTip(*args, **kwargs):
        return _controls_.TreeEvent_GetToolTip(*args, **kwargs)

    Item = property(GetItem, SetItem, doc='See `GetItem` and `SetItem`')
    KeyCode = property(GetKeyCode, doc='See `GetKeyCode`')
    KeyEvent = property(GetKeyEvent, SetKeyEvent, doc='See `GetKeyEvent` and `SetKeyEvent`')
    Label = property(GetLabel, SetLabel, doc='See `GetLabel` and `SetLabel`')
    OldItem = property(GetOldItem, SetOldItem, doc='See `GetOldItem` and `SetOldItem`')
    Point = property(GetPoint, SetPoint, doc='See `GetPoint` and `SetPoint`')
    ToolTip = property(GetToolTip, SetToolTip, doc='See `GetToolTip` and `SetToolTip`')
    EditCancelled = property(IsEditCancelled, SetEditCanceled, doc='See `IsEditCancelled` and `SetEditCanceled`')


_controls_.TreeEvent_swigregister(TreeEvent)

class TreeCtrl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.TreeCtrl_swiginit(self, _controls_.new_TreeCtrl(*args, **kwargs))
        self._setOORInfo(self)
        TreeCtrl._setCallbackInfo(self, self, TreeCtrl)

    def Create(*args, **kwargs):
        return _controls_.TreeCtrl_Create(*args, **kwargs)

    def _setCallbackInfo(*args, **kwargs):
        return _controls_.TreeCtrl__setCallbackInfo(*args, **kwargs)

    def GetCount(*args, **kwargs):
        return _controls_.TreeCtrl_GetCount(*args, **kwargs)

    def GetIndent(*args, **kwargs):
        return _controls_.TreeCtrl_GetIndent(*args, **kwargs)

    def SetIndent(*args, **kwargs):
        return _controls_.TreeCtrl_SetIndent(*args, **kwargs)

    def GetSpacing(*args, **kwargs):
        return _controls_.TreeCtrl_GetSpacing(*args, **kwargs)

    def SetSpacing(*args, **kwargs):
        return _controls_.TreeCtrl_SetSpacing(*args, **kwargs)

    def GetImageList(*args, **kwargs):
        return _controls_.TreeCtrl_GetImageList(*args, **kwargs)

    def GetStateImageList(*args, **kwargs):
        return _controls_.TreeCtrl_GetStateImageList(*args, **kwargs)

    def SetImageList(*args, **kwargs):
        return _controls_.TreeCtrl_SetImageList(*args, **kwargs)

    def SetStateImageList(*args, **kwargs):
        return _controls_.TreeCtrl_SetStateImageList(*args, **kwargs)

    def AssignImageList(*args, **kwargs):
        return _controls_.TreeCtrl_AssignImageList(*args, **kwargs)

    def AssignStateImageList(*args, **kwargs):
        return _controls_.TreeCtrl_AssignStateImageList(*args, **kwargs)

    def GetItemText(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemText(*args, **kwargs)

    def GetItemImage(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemImage(*args, **kwargs)

    def GetItemData(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemData(*args, **kwargs)

    def GetItemPyData(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemPyData(*args, **kwargs)

    GetPyData = GetItemPyData

    def GetItemTextColour(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemTextColour(*args, **kwargs)

    def GetItemBackgroundColour(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemBackgroundColour(*args, **kwargs)

    def GetItemFont(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemFont(*args, **kwargs)

    def SetItemText(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemText(*args, **kwargs)

    def SetItemImage(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemImage(*args, **kwargs)

    def SetItemData(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemData(*args, **kwargs)

    def SetItemPyData(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemPyData(*args, **kwargs)

    SetPyData = SetItemPyData

    def SetItemHasChildren(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemHasChildren(*args, **kwargs)

    def SetItemBold(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemBold(*args, **kwargs)

    def SetItemDropHighlight(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemDropHighlight(*args, **kwargs)

    def SetItemTextColour(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemTextColour(*args, **kwargs)

    def SetItemBackgroundColour(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemBackgroundColour(*args, **kwargs)

    def SetItemFont(*args, **kwargs):
        return _controls_.TreeCtrl_SetItemFont(*args, **kwargs)

    def IsVisible(*args, **kwargs):
        return _controls_.TreeCtrl_IsVisible(*args, **kwargs)

    def ItemHasChildren(*args, **kwargs):
        return _controls_.TreeCtrl_ItemHasChildren(*args, **kwargs)

    def IsExpanded(*args, **kwargs):
        return _controls_.TreeCtrl_IsExpanded(*args, **kwargs)

    def IsSelected(*args, **kwargs):
        return _controls_.TreeCtrl_IsSelected(*args, **kwargs)

    def IsBold(*args, **kwargs):
        return _controls_.TreeCtrl_IsBold(*args, **kwargs)

    def IsEmpty(*args, **kwargs):
        return _controls_.TreeCtrl_IsEmpty(*args, **kwargs)

    def GetChildrenCount(*args, **kwargs):
        return _controls_.TreeCtrl_GetChildrenCount(*args, **kwargs)

    def GetRootItem(*args, **kwargs):
        return _controls_.TreeCtrl_GetRootItem(*args, **kwargs)

    def GetSelection(*args, **kwargs):
        return _controls_.TreeCtrl_GetSelection(*args, **kwargs)

    def GetSelections(*args, **kwargs):
        return _controls_.TreeCtrl_GetSelections(*args, **kwargs)

    def GetItemParent(*args, **kwargs):
        return _controls_.TreeCtrl_GetItemParent(*args, **kwargs)

    def GetFirstChild(*args, **kwargs):
        return _controls_.TreeCtrl_GetFirstChild(*args, **kwargs)

    def GetNextChild(*args, **kwargs):
        return _controls_.TreeCtrl_GetNextChild(*args, **kwargs)

    def GetLastChild(*args, **kwargs):
        return _controls_.TreeCtrl_GetLastChild(*args, **kwargs)

    def GetNextSibling(*args, **kwargs):
        return _controls_.TreeCtrl_GetNextSibling(*args, **kwargs)

    def GetPrevSibling(*args, **kwargs):
        return _controls_.TreeCtrl_GetPrevSibling(*args, **kwargs)

    def GetFirstVisibleItem(*args, **kwargs):
        return _controls_.TreeCtrl_GetFirstVisibleItem(*args, **kwargs)

    def GetNextVisible(*args, **kwargs):
        return _controls_.TreeCtrl_GetNextVisible(*args, **kwargs)

    def GetPrevVisible(*args, **kwargs):
        return _controls_.TreeCtrl_GetPrevVisible(*args, **kwargs)

    def AddRoot(*args, **kwargs):
        return _controls_.TreeCtrl_AddRoot(*args, **kwargs)

    def PrependItem(*args, **kwargs):
        return _controls_.TreeCtrl_PrependItem(*args, **kwargs)

    def InsertItem(*args, **kwargs):
        return _controls_.TreeCtrl_InsertItem(*args, **kwargs)

    def InsertItemBefore(*args, **kwargs):
        return _controls_.TreeCtrl_InsertItemBefore(*args, **kwargs)

    def AppendItem(*args, **kwargs):
        return _controls_.TreeCtrl_AppendItem(*args, **kwargs)

    def Delete(*args, **kwargs):
        return _controls_.TreeCtrl_Delete(*args, **kwargs)

    def DeleteChildren(*args, **kwargs):
        return _controls_.TreeCtrl_DeleteChildren(*args, **kwargs)

    def DeleteAllItems(*args, **kwargs):
        return _controls_.TreeCtrl_DeleteAllItems(*args, **kwargs)

    def Expand(*args, **kwargs):
        return _controls_.TreeCtrl_Expand(*args, **kwargs)

    def ExpandAllChildren(*args, **kwargs):
        return _controls_.TreeCtrl_ExpandAllChildren(*args, **kwargs)

    def ExpandAll(*args, **kwargs):
        return _controls_.TreeCtrl_ExpandAll(*args, **kwargs)

    def Collapse(*args, **kwargs):
        return _controls_.TreeCtrl_Collapse(*args, **kwargs)

    def CollapseAllChildren(*args, **kwargs):
        return _controls_.TreeCtrl_CollapseAllChildren(*args, **kwargs)

    def CollapseAll(*args, **kwargs):
        return _controls_.TreeCtrl_CollapseAll(*args, **kwargs)

    def CollapseAndReset(*args, **kwargs):
        return _controls_.TreeCtrl_CollapseAndReset(*args, **kwargs)

    def Toggle(*args, **kwargs):
        return _controls_.TreeCtrl_Toggle(*args, **kwargs)

    def Unselect(*args, **kwargs):
        return _controls_.TreeCtrl_Unselect(*args, **kwargs)

    def UnselectItem(*args, **kwargs):
        return _controls_.TreeCtrl_UnselectItem(*args, **kwargs)

    def UnselectAll(*args, **kwargs):
        return _controls_.TreeCtrl_UnselectAll(*args, **kwargs)

    def SelectItem(*args, **kwargs):
        return _controls_.TreeCtrl_SelectItem(*args, **kwargs)

    def ToggleItemSelection(*args, **kwargs):
        return _controls_.TreeCtrl_ToggleItemSelection(*args, **kwargs)

    def EnsureVisible(*args, **kwargs):
        return _controls_.TreeCtrl_EnsureVisible(*args, **kwargs)

    def ScrollTo(*args, **kwargs):
        return _controls_.TreeCtrl_ScrollTo(*args, **kwargs)

    def EditLabel(*args, **kwargs):
        return _controls_.TreeCtrl_EditLabel(*args, **kwargs)

    def GetEditControl(*args, **kwargs):
        return _controls_.TreeCtrl_GetEditControl(*args, **kwargs)

    def SortChildren(*args, **kwargs):
        return _controls_.TreeCtrl_SortChildren(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _controls_.TreeCtrl_HitTest(*args, **kwargs)

    def GetBoundingRect(*args, **kwargs):
        return _controls_.TreeCtrl_GetBoundingRect(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _controls_.TreeCtrl_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)

    def SetQuickBestSize(*args, **kwargs):
        return _controls_.TreeCtrl_SetQuickBestSize(*args, **kwargs)

    def GetQuickBestSize(*args, **kwargs):
        return _controls_.TreeCtrl_GetQuickBestSize(*args, **kwargs)

    Count = property(GetCount, doc='See `GetCount`')
    EditControl = property(GetEditControl, doc='See `GetEditControl`')
    FirstVisibleItem = property(GetFirstVisibleItem, doc='See `GetFirstVisibleItem`')
    ImageList = property(GetImageList, SetImageList, doc='See `GetImageList` and `SetImageList`')
    Indent = property(GetIndent, SetIndent, doc='See `GetIndent` and `SetIndent`')
    QuickBestSize = property(GetQuickBestSize, SetQuickBestSize, doc='See `GetQuickBestSize` and `SetQuickBestSize`')
    RootItem = property(GetRootItem, doc='See `GetRootItem`')
    Selection = property(GetSelection, doc='See `GetSelection`')
    Selections = property(GetSelections, doc='See `GetSelections`')
    Spacing = property(GetSpacing, SetSpacing, doc='See `GetSpacing` and `SetSpacing`')
    StateImageList = property(GetStateImageList, SetStateImageList, doc='See `GetStateImageList` and `SetStateImageList`')


_controls_.TreeCtrl_swigregister(TreeCtrl)

def PreTreeCtrl(*args, **kwargs):
    val = _controls_.new_PreTreeCtrl(*args, **kwargs)
    return val


def TreeCtrl_GetClassDefaultAttributes(*args, **kwargs):
    return _controls_.TreeCtrl_GetClassDefaultAttributes(*args, **kwargs)


DIRCTRL_DIR_ONLY = _controls_.DIRCTRL_DIR_ONLY
DIRCTRL_SELECT_FIRST = _controls_.DIRCTRL_SELECT_FIRST
DIRCTRL_SHOW_FILTERS = _controls_.DIRCTRL_SHOW_FILTERS
DIRCTRL_3D_INTERNAL = _controls_.DIRCTRL_3D_INTERNAL
DIRCTRL_EDIT_LABELS = _controls_.DIRCTRL_EDIT_LABELS

class DirItemData(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def SetNewDirName(*args, **kwargs):
        return _controls_.DirItemData_SetNewDirName(*args, **kwargs)

    m_path = property(_controls_.DirItemData_m_path_get, _controls_.DirItemData_m_path_set)
    m_name = property(_controls_.DirItemData_m_name_get, _controls_.DirItemData_m_name_set)
    m_isHidden = property(_controls_.DirItemData_m_isHidden_get, _controls_.DirItemData_m_isHidden_set)
    m_isExpanded = property(_controls_.DirItemData_m_isExpanded_get, _controls_.DirItemData_m_isExpanded_set)
    m_isDir = property(_controls_.DirItemData_m_isDir_get, _controls_.DirItemData_m_isDir_set)


_controls_.DirItemData_swigregister(DirItemData)
DirDialogDefaultFolderStr = cvar.DirDialogDefaultFolderStr

class GenericDirCtrl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.GenericDirCtrl_swiginit(self, _controls_.new_GenericDirCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.GenericDirCtrl_Create(*args, **kwargs)

    def ExpandPath(*args, **kwargs):
        return _controls_.GenericDirCtrl_ExpandPath(*args, **kwargs)

    def CollapsePath(*args, **kwargs):
        return _controls_.GenericDirCtrl_CollapsePath(*args, **kwargs)

    def GetDefaultPath(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetDefaultPath(*args, **kwargs)

    def SetDefaultPath(*args, **kwargs):
        return _controls_.GenericDirCtrl_SetDefaultPath(*args, **kwargs)

    def GetPath(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetPath(*args, **kwargs)

    def GetFilePath(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetFilePath(*args, **kwargs)

    def SetPath(*args, **kwargs):
        return _controls_.GenericDirCtrl_SetPath(*args, **kwargs)

    def ShowHidden(*args, **kwargs):
        return _controls_.GenericDirCtrl_ShowHidden(*args, **kwargs)

    def GetShowHidden(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetShowHidden(*args, **kwargs)

    def GetFilter(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetFilter(*args, **kwargs)

    def SetFilter(*args, **kwargs):
        return _controls_.GenericDirCtrl_SetFilter(*args, **kwargs)

    def GetFilterIndex(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetFilterIndex(*args, **kwargs)

    def SetFilterIndex(*args, **kwargs):
        return _controls_.GenericDirCtrl_SetFilterIndex(*args, **kwargs)

    def GetRootId(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetRootId(*args, **kwargs)

    def GetTreeCtrl(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetTreeCtrl(*args, **kwargs)

    def GetFilterListCtrl(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetFilterListCtrl(*args, **kwargs)

    def GetDirItemData(*args, **kwargs):
        return _controls_.GenericDirCtrl_GetDirItemData(*args, **kwargs)

    def FindChild(*args, **kwargs):
        return _controls_.GenericDirCtrl_FindChild(*args, **kwargs)

    def DoResize(*args, **kwargs):
        return _controls_.GenericDirCtrl_DoResize(*args, **kwargs)

    def ReCreateTree(*args, **kwargs):
        return _controls_.GenericDirCtrl_ReCreateTree(*args, **kwargs)

    DefaultPath = property(GetDefaultPath, SetDefaultPath, doc='See `GetDefaultPath` and `SetDefaultPath`')
    FilePath = property(GetFilePath, doc='See `GetFilePath`')
    Filter = property(GetFilter, SetFilter, doc='See `GetFilter` and `SetFilter`')
    FilterIndex = property(GetFilterIndex, SetFilterIndex, doc='See `GetFilterIndex` and `SetFilterIndex`')
    FilterListCtrl = property(GetFilterListCtrl, doc='See `GetFilterListCtrl`')
    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')
    RootId = property(GetRootId, doc='See `GetRootId`')
    TreeCtrl = property(GetTreeCtrl, doc='See `GetTreeCtrl`')


_controls_.GenericDirCtrl_swigregister(GenericDirCtrl)

def PreGenericDirCtrl(*args, **kwargs):
    val = _controls_.new_PreGenericDirCtrl(*args, **kwargs)
    return val


class DirFilterListCtrl(Choice):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.DirFilterListCtrl_swiginit(self, _controls_.new_DirFilterListCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.DirFilterListCtrl_Create(*args, **kwargs)

    def FillFilterList(*args, **kwargs):
        return _controls_.DirFilterListCtrl_FillFilterList(*args, **kwargs)


_controls_.DirFilterListCtrl_swigregister(DirFilterListCtrl)

def PreDirFilterListCtrl(*args, **kwargs):
    val = _controls_.new_PreDirFilterListCtrl(*args, **kwargs)
    return val


class PyControl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.PyControl_swiginit(self, _controls_.new_PyControl(*args, **kwargs))
        self._setOORInfo(self)
        PyControl._setCallbackInfo(self, self, PyControl)

    def _setCallbackInfo(*args, **kwargs):
        return _controls_.PyControl__setCallbackInfo(*args, **kwargs)

    SetBestSize = wx.Window.SetInitialSize

    def DoEraseBackground(*args, **kwargs):
        return _controls_.PyControl_DoEraseBackground(*args, **kwargs)

    def DoMoveWindow(*args, **kwargs):
        return _controls_.PyControl_DoMoveWindow(*args, **kwargs)

    def DoSetSize(*args, **kwargs):
        return _controls_.PyControl_DoSetSize(*args, **kwargs)

    def DoSetClientSize(*args, **kwargs):
        return _controls_.PyControl_DoSetClientSize(*args, **kwargs)

    def DoSetVirtualSize(*args, **kwargs):
        return _controls_.PyControl_DoSetVirtualSize(*args, **kwargs)

    def DoGetSize(*args, **kwargs):
        return _controls_.PyControl_DoGetSize(*args, **kwargs)

    def DoGetClientSize(*args, **kwargs):
        return _controls_.PyControl_DoGetClientSize(*args, **kwargs)

    def DoGetPosition(*args, **kwargs):
        return _controls_.PyControl_DoGetPosition(*args, **kwargs)

    def DoGetVirtualSize(*args, **kwargs):
        return _controls_.PyControl_DoGetVirtualSize(*args, **kwargs)

    def DoGetBestSize(*args, **kwargs):
        return _controls_.PyControl_DoGetBestSize(*args, **kwargs)

    def InitDialog(*args, **kwargs):
        return _controls_.PyControl_InitDialog(*args, **kwargs)

    def TransferDataToWindow(*args, **kwargs):
        return _controls_.PyControl_TransferDataToWindow(*args, **kwargs)

    def TransferDataFromWindow(*args, **kwargs):
        return _controls_.PyControl_TransferDataFromWindow(*args, **kwargs)

    def Validate(*args, **kwargs):
        return _controls_.PyControl_Validate(*args, **kwargs)

    def GetDefaultAttributes(*args, **kwargs):
        return _controls_.PyControl_GetDefaultAttributes(*args, **kwargs)

    def OnInternalIdle(*args, **kwargs):
        return _controls_.PyControl_OnInternalIdle(*args, **kwargs)

    def base_DoMoveWindow(*args, **kw):
        return PyControl.DoMoveWindow(*args, **kw)

    base_DoMoveWindow = wx._deprecated(base_DoMoveWindow, 'Please use PyControl.DoMoveWindow instead.')

    def base_DoSetSize(*args, **kw):
        return PyControl.DoSetSize(*args, **kw)

    base_DoSetSize = wx._deprecated(base_DoSetSize, 'Please use PyControl.DoSetSize instead.')

    def base_DoSetClientSize(*args, **kw):
        return PyControl.DoSetClientSize(*args, **kw)

    base_DoSetClientSize = wx._deprecated(base_DoSetClientSize, 'Please use PyControl.DoSetClientSize instead.')

    def base_DoSetVirtualSize(*args, **kw):
        return PyControl.DoSetVirtualSize(*args, **kw)

    base_DoSetVirtualSize = wx._deprecated(base_DoSetVirtualSize, 'Please use PyControl.DoSetVirtualSize instead.')

    def base_DoGetSize(*args, **kw):
        return PyControl.DoGetSize(*args, **kw)

    base_DoGetSize = wx._deprecated(base_DoGetSize, 'Please use PyControl.DoGetSize instead.')

    def base_DoGetClientSize(*args, **kw):
        return PyControl.DoGetClientSize(*args, **kw)

    base_DoGetClientSize = wx._deprecated(base_DoGetClientSize, 'Please use PyControl.DoGetClientSize instead.')

    def base_DoGetPosition(*args, **kw):
        return PyControl.DoGetPosition(*args, **kw)

    base_DoGetPosition = wx._deprecated(base_DoGetPosition, 'Please use PyControl.DoGetPosition instead.')

    def base_DoGetVirtualSize(*args, **kw):
        return PyControl.DoGetVirtualSize(*args, **kw)

    base_DoGetVirtualSize = wx._deprecated(base_DoGetVirtualSize, 'Please use PyControl.DoGetVirtualSize instead.')

    def base_DoGetBestSize(*args, **kw):
        return PyControl.DoGetBestSize(*args, **kw)

    base_DoGetBestSize = wx._deprecated(base_DoGetBestSize, 'Please use PyControl.DoGetBestSize instead.')

    def base_InitDialog(*args, **kw):
        return PyControl.InitDialog(*args, **kw)

    base_InitDialog = wx._deprecated(base_InitDialog, 'Please use PyControl.InitDialog instead.')

    def base_TransferDataToWindow(*args, **kw):
        return PyControl.TransferDataToWindow(*args, **kw)

    base_TransferDataToWindow = wx._deprecated(base_TransferDataToWindow, 'Please use PyControl.TransferDataToWindow instead.')

    def base_TransferDataFromWindow(*args, **kw):
        return PyControl.TransferDataFromWindow(*args, **kw)

    base_TransferDataFromWindow = wx._deprecated(base_TransferDataFromWindow, 'Please use PyControl.TransferDataFromWindow instead.')

    def base_Validate(*args, **kw):
        return PyControl.Validate(*args, **kw)

    base_Validate = wx._deprecated(base_Validate, 'Please use PyControl.Validate instead.')

    def base_AcceptsFocus(*args, **kw):
        return PyControl.AcceptsFocus(*args, **kw)

    base_AcceptsFocus = wx._deprecated(base_AcceptsFocus, 'Please use PyControl.AcceptsFocus instead.')

    def base_AcceptsFocusFromKeyboard(*args, **kw):
        return PyControl.AcceptsFocusFromKeyboard(*args, **kw)

    base_AcceptsFocusFromKeyboard = wx._deprecated(base_AcceptsFocusFromKeyboard, 'Please use PyControl.AcceptsFocusFromKeyboard instead.')

    def base_GetMaxSize(*args, **kw):
        return PyControl.GetMaxSize(*args, **kw)

    base_GetMaxSize = wx._deprecated(base_GetMaxSize, 'Please use PyControl.GetMaxSize instead.')

    def base_AddChild(*args, **kw):
        return PyControl.AddChild(*args, **kw)

    base_AddChild = wx._deprecated(base_AddChild, 'Please use PyControl.AddChild instead.')

    def base_RemoveChild(*args, **kw):
        return PyControl.RemoveChild(*args, **kw)

    base_RemoveChild = wx._deprecated(base_RemoveChild, 'Please use PyControl.RemoveChild instead.')

    def base_ShouldInheritColours(*args, **kw):
        return PyControl.ShouldInheritColours(*args, **kw)

    base_ShouldInheritColours = wx._deprecated(base_ShouldInheritColours, 'Please use PyControl.ShouldInheritColours instead.')

    def base_GetDefaultAttributes(*args, **kw):
        return PyControl.GetDefaultAttributes(*args, **kw)

    base_GetDefaultAttributes = wx._deprecated(base_GetDefaultAttributes, 'Please use PyControl.GetDefaultAttributes instead.')

    def base_OnInternalIdle(*args, **kw):
        return PyControl.OnInternalIdle(*args, **kw)

    base_OnInternalIdle = wx._deprecated(base_OnInternalIdle, 'Please use PyControl.OnInternalIdle instead.')


_controls_.PyControl_swigregister(PyControl)

def PrePyControl(*args, **kwargs):
    val = _controls_.new_PrePyControl(*args, **kwargs)
    return val


wxEVT_HELP = _controls_.wxEVT_HELP
wxEVT_DETAILED_HELP = _controls_.wxEVT_DETAILED_HELP
EVT_HELP = wx.PyEventBinder(wxEVT_HELP, 1)
EVT_HELP_RANGE = wx.PyEventBinder(wxEVT_HELP, 2)
EVT_DETAILED_HELP = wx.PyEventBinder(wxEVT_DETAILED_HELP, 1)
EVT_DETAILED_HELP_RANGE = wx.PyEventBinder(wxEVT_DETAILED_HELP, 2)

class HelpEvent(_core.CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    Origin_Unknown = _controls_.HelpEvent_Origin_Unknown
    Origin_Keyboard = _controls_.HelpEvent_Origin_Keyboard
    Origin_HelpButton = _controls_.HelpEvent_Origin_HelpButton

    def __init__(self, *args, **kwargs):
        _controls_.HelpEvent_swiginit(self, _controls_.new_HelpEvent(*args, **kwargs))

    def GetPosition(*args, **kwargs):
        return _controls_.HelpEvent_GetPosition(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _controls_.HelpEvent_SetPosition(*args, **kwargs)

    def GetLink(*args, **kwargs):
        return _controls_.HelpEvent_GetLink(*args, **kwargs)

    def SetLink(*args, **kwargs):
        return _controls_.HelpEvent_SetLink(*args, **kwargs)

    def GetTarget(*args, **kwargs):
        return _controls_.HelpEvent_GetTarget(*args, **kwargs)

    def SetTarget(*args, **kwargs):
        return _controls_.HelpEvent_SetTarget(*args, **kwargs)

    def GetOrigin(*args, **kwargs):
        return _controls_.HelpEvent_GetOrigin(*args, **kwargs)

    def SetOrigin(*args, **kwargs):
        return _controls_.HelpEvent_SetOrigin(*args, **kwargs)

    Link = property(GetLink, SetLink, doc='See `GetLink` and `SetLink`')
    Origin = property(GetOrigin, SetOrigin, doc='See `GetOrigin` and `SetOrigin`')
    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')
    Target = property(GetTarget, SetTarget, doc='See `GetTarget` and `SetTarget`')


_controls_.HelpEvent_swigregister(HelpEvent)

class ContextHelp(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ContextHelp_swiginit(self, _controls_.new_ContextHelp(*args, **kwargs))

    __swig_destroy__ = _controls_.delete_ContextHelp
    __del__ = lambda self: None

    def BeginContextHelp(*args, **kwargs):
        return _controls_.ContextHelp_BeginContextHelp(*args, **kwargs)

    def EndContextHelp(*args, **kwargs):
        return _controls_.ContextHelp_EndContextHelp(*args, **kwargs)


_controls_.ContextHelp_swigregister(ContextHelp)

class ContextHelpButton(BitmapButton):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.ContextHelpButton_swiginit(self, _controls_.new_ContextHelpButton(*args, **kwargs))
        self._setOORInfo(self)


_controls_.ContextHelpButton_swigregister(ContextHelpButton)

class HelpProvider(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _controls_.delete_HelpProvider
    __del__ = lambda self: None

    def Set(*args, **kwargs):
        return _controls_.HelpProvider_Set(*args, **kwargs)

    Set = staticmethod(Set)

    def Get(*args, **kwargs):
        return _controls_.HelpProvider_Get(*args, **kwargs)

    Get = staticmethod(Get)

    def GetHelp(*args, **kwargs):
        return _controls_.HelpProvider_GetHelp(*args, **kwargs)

    def ShowHelp(*args, **kwargs):
        return _controls_.HelpProvider_ShowHelp(*args, **kwargs)

    def ShowHelpAtPoint(*args, **kwargs):
        return _controls_.HelpProvider_ShowHelpAtPoint(*args, **kwargs)

    def AddHelp(*args, **kwargs):
        return _controls_.HelpProvider_AddHelp(*args, **kwargs)

    def AddHelpById(*args, **kwargs):
        return _controls_.HelpProvider_AddHelpById(*args, **kwargs)

    def RemoveHelp(*args, **kwargs):
        return _controls_.HelpProvider_RemoveHelp(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _controls_.HelpProvider_Destroy(*args, **kwargs)


_controls_.HelpProvider_swigregister(HelpProvider)

def HelpProvider_Set(*args, **kwargs):
    return _controls_.HelpProvider_Set(*args, **kwargs)


def HelpProvider_Get(*args):
    return _controls_.HelpProvider_Get(*args)


class SimpleHelpProvider(HelpProvider):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.SimpleHelpProvider_swiginit(self, _controls_.new_SimpleHelpProvider(*args, **kwargs))


_controls_.SimpleHelpProvider_swigregister(SimpleHelpProvider)
DP_DEFAULT = _controls_.DP_DEFAULT
DP_SPIN = _controls_.DP_SPIN
DP_DROPDOWN = _controls_.DP_DROPDOWN
DP_SHOWCENTURY = _controls_.DP_SHOWCENTURY
DP_ALLOWNONE = _controls_.DP_ALLOWNONE

class DatePickerCtrlBase(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def SetValue(*args, **kwargs):
        return _controls_.DatePickerCtrlBase_SetValue(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _controls_.DatePickerCtrlBase_GetValue(*args, **kwargs)

    def SetRange(*args, **kwargs):
        return _controls_.DatePickerCtrlBase_SetRange(*args, **kwargs)

    def GetLowerLimit(*args, **kwargs):
        return _controls_.DatePickerCtrlBase_GetLowerLimit(*args, **kwargs)

    def GetUpperLimit(*args, **kwargs):
        return _controls_.DatePickerCtrlBase_GetUpperLimit(*args, **kwargs)

    LowerLimit = property(GetLowerLimit, doc='See `GetLowerLimit`')
    UpperLimit = property(GetUpperLimit, doc='See `GetUpperLimit`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_controls_.DatePickerCtrlBase_swigregister(DatePickerCtrlBase)
DatePickerCtrlNameStr = cvar.DatePickerCtrlNameStr

class DatePickerCtrl(DatePickerCtrlBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.DatePickerCtrl_swiginit(self, _controls_.new_DatePickerCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.DatePickerCtrl_Create(*args, **kwargs)


_controls_.DatePickerCtrl_swigregister(DatePickerCtrl)

def PreDatePickerCtrl(*args, **kwargs):
    val = _controls_.new_PreDatePickerCtrl(*args, **kwargs)
    return val


class GenericDatePickerCtrl(DatePickerCtrl):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.GenericDatePickerCtrl_swiginit(self, _controls_.new_GenericDatePickerCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.GenericDatePickerCtrl_Create(*args, **kwargs)


_controls_.GenericDatePickerCtrl_swigregister(GenericDatePickerCtrl)

def PreGenericDatePickerCtrl(*args, **kwargs):
    val = _controls_.new_PreGenericDatePickerCtrl(*args, **kwargs)
    return val


PB_USE_TEXTCTRL = _controls_.PB_USE_TEXTCTRL

class PickerBase(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def CreateBase(*args, **kwargs):
        return _controls_.PickerBase_CreateBase(*args, **kwargs)

    def SetInternalMargin(*args, **kwargs):
        return _controls_.PickerBase_SetInternalMargin(*args, **kwargs)

    def GetInternalMargin(*args, **kwargs):
        return _controls_.PickerBase_GetInternalMargin(*args, **kwargs)

    def SetTextCtrlProportion(*args, **kwargs):
        return _controls_.PickerBase_SetTextCtrlProportion(*args, **kwargs)

    def GetTextCtrlProportion(*args, **kwargs):
        return _controls_.PickerBase_GetTextCtrlProportion(*args, **kwargs)

    def SetPickerCtrlProportion(*args, **kwargs):
        return _controls_.PickerBase_SetPickerCtrlProportion(*args, **kwargs)

    def GetPickerCtrlProportion(*args, **kwargs):
        return _controls_.PickerBase_GetPickerCtrlProportion(*args, **kwargs)

    def IsTextCtrlGrowable(*args, **kwargs):
        return _controls_.PickerBase_IsTextCtrlGrowable(*args, **kwargs)

    def SetTextCtrlGrowable(*args, **kwargs):
        return _controls_.PickerBase_SetTextCtrlGrowable(*args, **kwargs)

    def IsPickerCtrlGrowable(*args, **kwargs):
        return _controls_.PickerBase_IsPickerCtrlGrowable(*args, **kwargs)

    def SetPickerCtrlGrowable(*args, **kwargs):
        return _controls_.PickerBase_SetPickerCtrlGrowable(*args, **kwargs)

    def HasTextCtrl(*args, **kwargs):
        return _controls_.PickerBase_HasTextCtrl(*args, **kwargs)

    def GetTextCtrl(*args, **kwargs):
        return _controls_.PickerBase_GetTextCtrl(*args, **kwargs)

    def GetPickerCtrl(*args, **kwargs):
        return _controls_.PickerBase_GetPickerCtrl(*args, **kwargs)

    InternalMargin = property(GetInternalMargin, SetInternalMargin, doc='See `GetInternalMargin` and `SetInternalMargin`')
    PickerCtrl = property(GetPickerCtrl, doc='See `GetPickerCtrl`')
    PickerCtrlProportion = property(GetPickerCtrlProportion, SetPickerCtrlProportion, doc='See `GetPickerCtrlProportion` and `SetPickerCtrlProportion`')
    TextCtrl = property(GetTextCtrl, doc='See `GetTextCtrl`')
    TextCtrlProportion = property(GetTextCtrlProportion, SetTextCtrlProportion, doc='See `GetTextCtrlProportion` and `SetTextCtrlProportion`')
    TextCtrlGrowable = property(IsTextCtrlGrowable, SetTextCtrlGrowable, doc='See `IsTextCtrlGrowable` and `SetTextCtrlGrowable`')
    PickerCtrlGrowable = property(IsPickerCtrlGrowable, SetPickerCtrlGrowable, doc='See `IsPickerCtrlGrowable` and `SetPickerCtrlGrowable`')


_controls_.PickerBase_swigregister(PickerBase)
FLP_OPEN = _controls_.FLP_OPEN
FLP_SAVE = _controls_.FLP_SAVE
FLP_OVERWRITE_PROMPT = _controls_.FLP_OVERWRITE_PROMPT
FLP_FILE_MUST_EXIST = _controls_.FLP_FILE_MUST_EXIST
FLP_CHANGE_DIR = _controls_.FLP_CHANGE_DIR
DIRP_DIR_MUST_EXIST = _controls_.DIRP_DIR_MUST_EXIST
DIRP_CHANGE_DIR = _controls_.DIRP_CHANGE_DIR
FLP_USE_TEXTCTRL = _controls_.FLP_USE_TEXTCTRL
FLP_DEFAULT_STYLE = _controls_.FLP_DEFAULT_STYLE
DIRP_USE_TEXTCTRL = _controls_.DIRP_USE_TEXTCTRL
DIRP_DEFAULT_STYLE = _controls_.DIRP_DEFAULT_STYLE

class FilePickerCtrl(PickerBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.FilePickerCtrl_swiginit(self, _controls_.new_FilePickerCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.FilePickerCtrl_Create(*args, **kwargs)

    def GetPath(*args, **kwargs):
        return _controls_.FilePickerCtrl_GetPath(*args, **kwargs)

    def SetPath(*args, **kwargs):
        return _controls_.FilePickerCtrl_SetPath(*args, **kwargs)

    def CheckPath(*args, **kwargs):
        return _controls_.FilePickerCtrl_CheckPath(*args, **kwargs)

    def GetTextCtrlValue(*args, **kwargs):
        return _controls_.FilePickerCtrl_GetTextCtrlValue(*args, **kwargs)

    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')
    TextCtrlValue = property(GetTextCtrlValue, doc='See `GetTextCtrlValue`')


_controls_.FilePickerCtrl_swigregister(FilePickerCtrl)
FilePickerCtrlNameStr = cvar.FilePickerCtrlNameStr
FileSelectorPromptStr = cvar.FileSelectorPromptStr
DirPickerCtrlNameStr = cvar.DirPickerCtrlNameStr
DirSelectorPromptStr = cvar.DirSelectorPromptStr
FileSelectorDefaultWildcardStr = cvar.FileSelectorDefaultWildcardStr

def PreFilePickerCtrl(*args, **kwargs):
    val = _controls_.new_PreFilePickerCtrl(*args, **kwargs)
    return val


class DirPickerCtrl(PickerBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.DirPickerCtrl_swiginit(self, _controls_.new_DirPickerCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.DirPickerCtrl_Create(*args, **kwargs)

    def GetPath(*args, **kwargs):
        return _controls_.DirPickerCtrl_GetPath(*args, **kwargs)

    def SetPath(*args, **kwargs):
        return _controls_.DirPickerCtrl_SetPath(*args, **kwargs)

    def CheckPath(*args, **kwargs):
        return _controls_.DirPickerCtrl_CheckPath(*args, **kwargs)

    def GetTextCtrlValue(*args, **kwargs):
        return _controls_.DirPickerCtrl_GetTextCtrlValue(*args, **kwargs)

    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')
    TextCtrlValue = property(GetTextCtrlValue, doc='See `GetTextCtrlValue`')


_controls_.DirPickerCtrl_swigregister(DirPickerCtrl)

def PreDirPickerCtrl(*args, **kwargs):
    val = _controls_.new_PreDirPickerCtrl(*args, **kwargs)
    return val


wxEVT_COMMAND_FILEPICKER_CHANGED = _controls_.wxEVT_COMMAND_FILEPICKER_CHANGED
wxEVT_COMMAND_DIRPICKER_CHANGED = _controls_.wxEVT_COMMAND_DIRPICKER_CHANGED
EVT_FILEPICKER_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_FILEPICKER_CHANGED, 1)
EVT_DIRPICKER_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_DIRPICKER_CHANGED, 1)

class FileDirPickerEvent(_core.CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.FileDirPickerEvent_swiginit(self, _controls_.new_FileDirPickerEvent(*args, **kwargs))

    def GetPath(*args, **kwargs):
        return _controls_.FileDirPickerEvent_GetPath(*args, **kwargs)

    def SetPath(*args, **kwargs):
        return _controls_.FileDirPickerEvent_SetPath(*args, **kwargs)

    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')


_controls_.FileDirPickerEvent_swigregister(FileDirPickerEvent)

class SearchCtrl(TextCtrl):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _controls_.SearchCtrl_swiginit(self, _controls_.new_SearchCtrl(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _controls_.SearchCtrl_Create(*args, **kwargs)

    def SetMenu(*args, **kwargs):
        return _controls_.SearchCtrl_SetMenu(*args, **kwargs)

    def GetMenu(*args, **kwargs):
        return _controls_.SearchCtrl_GetMenu(*args, **kwargs)

    def ShowSearchButton(*args, **kwargs):
        return _controls_.SearchCtrl_ShowSearchButton(*args, **kwargs)

    def IsSearchButtonVisible(*args, **kwargs):
        return _controls_.SearchCtrl_IsSearchButtonVisible(*args, **kwargs)

    def ShowCancelButton(*args, **kwargs):
        return _controls_.SearchCtrl_ShowCancelButton(*args, **kwargs)

    def IsCancelButtonVisible(*args, **kwargs):
        return _controls_.SearchCtrl_IsCancelButtonVisible(*args, **kwargs)

    def SetDescriptiveText(*args, **kwargs):
        return _controls_.SearchCtrl_SetDescriptiveText(*args, **kwargs)

    def GetDescriptiveText(*args, **kwargs):
        return _controls_.SearchCtrl_GetDescriptiveText(*args, **kwargs)

    def SetSearchBitmap(*args, **kwargs):
        return _controls_.SearchCtrl_SetSearchBitmap(*args, **kwargs)

    def SetSearchMenuBitmap(*args, **kwargs):
        return _controls_.SearchCtrl_SetSearchMenuBitmap(*args, **kwargs)

    def SetCancelBitmap(*args, **kwargs):
        return _controls_.SearchCtrl_SetCancelBitmap(*args, **kwargs)

    Menu = property(GetMenu, SetMenu)
    SearchButtonVisible = property(IsSearchButtonVisible, ShowSearchButton)
    CancelButtonVisible = property(IsCancelButtonVisible, ShowCancelButton)
    DescriptiveText = property(GetDescriptiveText, SetDescriptiveText)


_controls_.SearchCtrl_swigregister(SearchCtrl)
SearchCtrlNameStr = cvar.SearchCtrlNameStr

def PreSearchCtrl(*args, **kwargs):
    val = _controls_.new_PreSearchCtrl(*args, **kwargs)
    return val


wxEVT_COMMAND_SEARCHCTRL_CANCEL_BTN = _controls_.wxEVT_COMMAND_SEARCHCTRL_CANCEL_BTN
wxEVT_COMMAND_SEARCHCTRL_SEARCH_BTN = _controls_.wxEVT_COMMAND_SEARCHCTRL_SEARCH_BTN
EVT_SEARCHCTRL_CANCEL_BTN = wx.PyEventBinder(wxEVT_COMMAND_SEARCHCTRL_CANCEL_BTN, 1)
EVT_SEARCHCTRL_SEARCH_BTN = wx.PyEventBinder(wxEVT_COMMAND_SEARCHCTRL_SEARCH_BTN, 1)
