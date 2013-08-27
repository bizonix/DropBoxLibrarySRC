#Embedded file name: wx/combo.py
import _combo
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


import _windows
import _core
wx = _core
__docfilter__ = wx.__DocFilter(globals())
CC_BUTTON_OUTSIDE_BORDER = _combo.CC_BUTTON_OUTSIDE_BORDER
CC_POPUP_ON_MOUSE_UP = _combo.CC_POPUP_ON_MOUSE_UP
CC_NO_TEXT_AUTO_SELECT = _combo.CC_NO_TEXT_AUTO_SELECT
CC_MF_ON_BUTTON = _combo.CC_MF_ON_BUTTON
CC_MF_ON_CLICK_AREA = _combo.CC_MF_ON_CLICK_AREA

class ComboCtrlFeatures(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    MovableButton = _combo.ComboCtrlFeatures_MovableButton
    BitmapButton = _combo.ComboCtrlFeatures_BitmapButton
    ButtonSpacing = _combo.ComboCtrlFeatures_ButtonSpacing
    TextIndent = _combo.ComboCtrlFeatures_TextIndent
    PaintControl = _combo.ComboCtrlFeatures_PaintControl
    PaintWritable = _combo.ComboCtrlFeatures_PaintWritable
    Borderless = _combo.ComboCtrlFeatures_Borderless
    All = _combo.ComboCtrlFeatures_All


_combo.ComboCtrlFeatures_swigregister(ComboCtrlFeatures)

class ComboCtrl(_core.Control):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _combo.ComboCtrl_swiginit(self, _combo.new_ComboCtrl(*args, **kwargs))
        self._setOORInfo(self)
        ComboCtrl._setCallbackInfo(self, self, ComboCtrl)

    def _setCallbackInfo(*args, **kwargs):
        return _combo.ComboCtrl__setCallbackInfo(*args, **kwargs)

    def ShowPopup(*args, **kwargs):
        return _combo.ComboCtrl_ShowPopup(*args, **kwargs)

    def HidePopup(*args, **kwargs):
        return _combo.ComboCtrl_HidePopup(*args, **kwargs)

    def OnButtonClick(*args, **kwargs):
        return _combo.ComboCtrl_OnButtonClick(*args, **kwargs)

    def IsPopupShown(*args, **kwargs):
        return _combo.ComboCtrl_IsPopupShown(*args, **kwargs)

    def SetPopupControl(*args, **kwargs):
        return _combo.ComboCtrl_SetPopupControl(*args, **kwargs)

    def GetPopupControl(*args, **kwargs):
        return _combo.ComboCtrl_GetPopupControl(*args, **kwargs)

    def GetPopupWindow(*args, **kwargs):
        return _combo.ComboCtrl_GetPopupWindow(*args, **kwargs)

    def GetTextCtrl(*args, **kwargs):
        return _combo.ComboCtrl_GetTextCtrl(*args, **kwargs)

    def GetButton(*args, **kwargs):
        return _combo.ComboCtrl_GetButton(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _combo.ComboCtrl_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _combo.ComboCtrl_SetValue(*args, **kwargs)

    def Copy(*args, **kwargs):
        return _combo.ComboCtrl_Copy(*args, **kwargs)

    def Cut(*args, **kwargs):
        return _combo.ComboCtrl_Cut(*args, **kwargs)

    def Paste(*args, **kwargs):
        return _combo.ComboCtrl_Paste(*args, **kwargs)

    def SetInsertionPoint(*args, **kwargs):
        return _combo.ComboCtrl_SetInsertionPoint(*args, **kwargs)

    def SetInsertionPointEnd(*args, **kwargs):
        return _combo.ComboCtrl_SetInsertionPointEnd(*args, **kwargs)

    def GetInsertionPoint(*args, **kwargs):
        return _combo.ComboCtrl_GetInsertionPoint(*args, **kwargs)

    def GetLastPosition(*args, **kwargs):
        return _combo.ComboCtrl_GetLastPosition(*args, **kwargs)

    def Replace(*args, **kwargs):
        return _combo.ComboCtrl_Replace(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _combo.ComboCtrl_Remove(*args, **kwargs)

    def Undo(*args, **kwargs):
        return _combo.ComboCtrl_Undo(*args, **kwargs)

    def SetMark(*args, **kwargs):
        return _combo.ComboCtrl_SetMark(*args, **kwargs)

    def SetText(*args, **kwargs):
        return _combo.ComboCtrl_SetText(*args, **kwargs)

    def SetValueWithEvent(*args, **kwargs):
        return _combo.ComboCtrl_SetValueWithEvent(*args, **kwargs)

    def SetPopupMinWidth(*args, **kwargs):
        return _combo.ComboCtrl_SetPopupMinWidth(*args, **kwargs)

    def SetPopupMaxHeight(*args, **kwargs):
        return _combo.ComboCtrl_SetPopupMaxHeight(*args, **kwargs)

    def SetPopupExtents(*args, **kwargs):
        return _combo.ComboCtrl_SetPopupExtents(*args, **kwargs)

    def SetCustomPaintWidth(*args, **kwargs):
        return _combo.ComboCtrl_SetCustomPaintWidth(*args, **kwargs)

    def GetCustomPaintWidth(*args, **kwargs):
        return _combo.ComboCtrl_GetCustomPaintWidth(*args, **kwargs)

    def SetPopupAnchor(*args, **kwargs):
        return _combo.ComboCtrl_SetPopupAnchor(*args, **kwargs)

    def SetButtonPosition(*args, **kwargs):
        return _combo.ComboCtrl_SetButtonPosition(*args, **kwargs)

    def GetButtonSize(*args, **kwargs):
        return _combo.ComboCtrl_GetButtonSize(*args, **kwargs)

    def SetButtonBitmaps(*args, **kwargs):
        return _combo.ComboCtrl_SetButtonBitmaps(*args, **kwargs)

    def SetTextIndent(*args, **kwargs):
        return _combo.ComboCtrl_SetTextIndent(*args, **kwargs)

    def GetTextIndent(*args, **kwargs):
        return _combo.ComboCtrl_GetTextIndent(*args, **kwargs)

    def GetTextRect(*args, **kwargs):
        return _combo.ComboCtrl_GetTextRect(*args, **kwargs)

    def UseAltPopupWindow(*args, **kwargs):
        return _combo.ComboCtrl_UseAltPopupWindow(*args, **kwargs)

    def EnablePopupAnimation(*args, **kwargs):
        return _combo.ComboCtrl_EnablePopupAnimation(*args, **kwargs)

    def IsKeyPopupToggle(*args, **kwargs):
        return _combo.ComboCtrl_IsKeyPopupToggle(*args, **kwargs)

    def PrepareBackground(*args, **kwargs):
        return _combo.ComboCtrl_PrepareBackground(*args, **kwargs)

    def ShouldDrawFocus(*args, **kwargs):
        return _combo.ComboCtrl_ShouldDrawFocus(*args, **kwargs)

    def GetBitmapNormal(*args, **kwargs):
        return _combo.ComboCtrl_GetBitmapNormal(*args, **kwargs)

    def GetBitmapPressed(*args, **kwargs):
        return _combo.ComboCtrl_GetBitmapPressed(*args, **kwargs)

    def GetBitmapHover(*args, **kwargs):
        return _combo.ComboCtrl_GetBitmapHover(*args, **kwargs)

    def GetBitmapDisabled(*args, **kwargs):
        return _combo.ComboCtrl_GetBitmapDisabled(*args, **kwargs)

    def GetInternalFlags(*args, **kwargs):
        return _combo.ComboCtrl_GetInternalFlags(*args, **kwargs)

    def IsCreated(*args, **kwargs):
        return _combo.ComboCtrl_IsCreated(*args, **kwargs)

    def OnPopupDismiss(*args, **kwargs):
        return _combo.ComboCtrl_OnPopupDismiss(*args, **kwargs)

    Hidden = _combo.ComboCtrl_Hidden
    Animating = _combo.ComboCtrl_Animating
    Visible = _combo.ComboCtrl_Visible

    def IsPopupWindowState(*args, **kwargs):
        return _combo.ComboCtrl_IsPopupWindowState(*args, **kwargs)

    def GetPopupWindowState(*args, **kwargs):
        return _combo.ComboCtrl_GetPopupWindowState(*args, **kwargs)

    def SetCtrlMainWnd(*args, **kwargs):
        return _combo.ComboCtrl_SetCtrlMainWnd(*args, **kwargs)

    def GetMainWindowOfCompositeControl(*args, **kwargs):
        return _combo.ComboCtrl_GetMainWindowOfCompositeControl(*args, **kwargs)

    def GetFeatures(*args, **kwargs):
        return _combo.ComboCtrl_GetFeatures(*args, **kwargs)

    GetFeatures = staticmethod(GetFeatures)
    ShowBelow = _combo.ComboCtrl_ShowBelow
    ShowAbove = _combo.ComboCtrl_ShowAbove
    CanDeferShow = _combo.ComboCtrl_CanDeferShow

    def DoShowPopup(*args, **kwargs):
        return _combo.ComboCtrl_DoShowPopup(*args, **kwargs)

    def AnimateShow(*args, **kwargs):
        return _combo.ComboCtrl_AnimateShow(*args, **kwargs)

    PopupControl = property(GetPopupControl, SetPopupControl)
    PopupWindow = property(GetPopupWindow)
    TextCtrl = property(GetTextCtrl)
    Button = property(GetButton)
    Value = property(GetValue, SetValue)
    InsertionPoint = property(GetInsertionPoint)
    CustomPaintWidth = property(GetCustomPaintWidth, SetCustomPaintWidth)
    ButtonSize = property(GetButtonSize)
    TextIndent = property(GetTextIndent, SetTextIndent)
    TextRect = property(GetTextRect)
    BitmapNormal = property(GetBitmapNormal)
    BitmapPressed = property(GetBitmapPressed)
    BitmapHover = property(GetBitmapHover)
    BitmapDisabled = property(GetBitmapDisabled)
    PopupWindowState = property(GetPopupWindowState)


_combo.ComboCtrl_swigregister(ComboCtrl)

def PreComboCtrl(*args, **kwargs):
    val = _combo.new_PreComboCtrl(*args, **kwargs)
    return val


def ComboCtrl_GetFeatures(*args):
    return _combo.ComboCtrl_GetFeatures(*args)


class ComboPopup(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _combo.ComboPopup_swiginit(self, _combo.new_ComboPopup(*args, **kwargs))
        ComboPopup._setCallbackInfo(self, self, ComboPopup)

    __swig_destroy__ = _combo.delete_ComboPopup
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _combo.ComboPopup__setCallbackInfo(*args, **kwargs)

    def Init(*args, **kwargs):
        return _combo.ComboPopup_Init(*args, **kwargs)

    def Create(*args, **kwargs):
        return _combo.ComboPopup_Create(*args, **kwargs)

    def GetControl(*args, **kwargs):
        return _combo.ComboPopup_GetControl(*args, **kwargs)

    def OnPopup(*args, **kwargs):
        return _combo.ComboPopup_OnPopup(*args, **kwargs)

    def OnDismiss(*args, **kwargs):
        return _combo.ComboPopup_OnDismiss(*args, **kwargs)

    def SetStringValue(*args, **kwargs):
        return _combo.ComboPopup_SetStringValue(*args, **kwargs)

    def GetStringValue(*args, **kwargs):
        return _combo.ComboPopup_GetStringValue(*args, **kwargs)

    def PaintComboControl(*args, **kwargs):
        return _combo.ComboPopup_PaintComboControl(*args, **kwargs)

    def OnComboKeyEvent(*args, **kwargs):
        return _combo.ComboPopup_OnComboKeyEvent(*args, **kwargs)

    def OnComboDoubleClick(*args, **kwargs):
        return _combo.ComboPopup_OnComboDoubleClick(*args, **kwargs)

    def GetAdjustedSize(*args, **kwargs):
        return _combo.ComboPopup_GetAdjustedSize(*args, **kwargs)

    def LazyCreate(*args, **kwargs):
        return _combo.ComboPopup_LazyCreate(*args, **kwargs)

    def Dismiss(*args, **kwargs):
        return _combo.ComboPopup_Dismiss(*args, **kwargs)

    def IsCreated(*args, **kwargs):
        return _combo.ComboPopup_IsCreated(*args, **kwargs)

    def DefaultPaintComboControl(*args, **kwargs):
        return _combo.ComboPopup_DefaultPaintComboControl(*args, **kwargs)

    DefaultPaintComboControl = staticmethod(DefaultPaintComboControl)

    def GetCombo(*args, **kwargs):
        return _combo.ComboPopup_GetCombo(*args, **kwargs)


_combo.ComboPopup_swigregister(ComboPopup)

def ComboPopup_DefaultPaintComboControl(*args, **kwargs):
    return _combo.ComboPopup_DefaultPaintComboControl(*args, **kwargs)


ODCB_DCLICK_CYCLES = _combo.ODCB_DCLICK_CYCLES
ODCB_STD_CONTROL_PAINT = _combo.ODCB_STD_CONTROL_PAINT
ODCB_PAINTING_CONTROL = _combo.ODCB_PAINTING_CONTROL
ODCB_PAINTING_SELECTED = _combo.ODCB_PAINTING_SELECTED

class OwnerDrawnComboBox(ComboCtrl, _core.ItemContainer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _combo.OwnerDrawnComboBox_swiginit(self, _combo.new_OwnerDrawnComboBox(*args, **kwargs))
        self._setOORInfo(self)
        OwnerDrawnComboBox._setCallbackInfo(self, self, OwnerDrawnComboBox)

    def _setCallbackInfo(*args, **kwargs):
        return _combo.OwnerDrawnComboBox__setCallbackInfo(*args, **kwargs)

    def Create(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_Create(*args, **kwargs)

    def GetWidestItemWidth(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_GetWidestItemWidth(*args, **kwargs)

    def GetWidestItem(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_GetWidestItem(*args, **kwargs)

    def SetMark(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_SetMark(*args, **kwargs)

    def OnDrawItem(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_OnDrawItem(*args, **kwargs)

    def OnMeasureItem(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_OnMeasureItem(*args, **kwargs)

    def OnMeasureItemWidth(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_OnMeasureItemWidth(*args, **kwargs)

    def OnDrawBackground(*args, **kwargs):
        return _combo.OwnerDrawnComboBox_OnDrawBackground(*args, **kwargs)


_combo.OwnerDrawnComboBox_swigregister(OwnerDrawnComboBox)

def PreOwnerDrawnComboBox(*args, **kwargs):
    val = _combo.new_PreOwnerDrawnComboBox(*args, **kwargs)
    return val


class BitmapComboBox(OwnerDrawnComboBox):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _combo.BitmapComboBox_swiginit(self, _combo.new_BitmapComboBox(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _combo.BitmapComboBox_Create(*args, **kwargs)

    def Append(*args, **kwargs):
        return _combo.BitmapComboBox_Append(*args, **kwargs)

    def GetItemBitmap(*args, **kwargs):
        return _combo.BitmapComboBox_GetItemBitmap(*args, **kwargs)

    def Insert(*args, **kwargs):
        return _combo.BitmapComboBox_Insert(*args, **kwargs)

    def SetItemBitmap(*args, **kwargs):
        return _combo.BitmapComboBox_SetItemBitmap(*args, **kwargs)

    def GetBitmapSize(*args, **kwargs):
        return _combo.BitmapComboBox_GetBitmapSize(*args, **kwargs)


_combo.BitmapComboBox_swigregister(BitmapComboBox)

def PreBitmapComboBox(*args, **kwargs):
    val = _combo.new_PreBitmapComboBox(*args, **kwargs)
    return val
