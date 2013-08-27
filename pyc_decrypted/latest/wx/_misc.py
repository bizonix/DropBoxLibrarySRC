#Embedded file name: wx/_misc.py
import _misc_
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
SYS_OEM_FIXED_FONT = _misc_.SYS_OEM_FIXED_FONT
SYS_ANSI_FIXED_FONT = _misc_.SYS_ANSI_FIXED_FONT
SYS_ANSI_VAR_FONT = _misc_.SYS_ANSI_VAR_FONT
SYS_SYSTEM_FONT = _misc_.SYS_SYSTEM_FONT
SYS_DEVICE_DEFAULT_FONT = _misc_.SYS_DEVICE_DEFAULT_FONT
SYS_DEFAULT_PALETTE = _misc_.SYS_DEFAULT_PALETTE
SYS_SYSTEM_FIXED_FONT = _misc_.SYS_SYSTEM_FIXED_FONT
SYS_DEFAULT_GUI_FONT = _misc_.SYS_DEFAULT_GUI_FONT
SYS_ICONTITLE_FONT = _misc_.SYS_ICONTITLE_FONT
SYS_COLOUR_SCROLLBAR = _misc_.SYS_COLOUR_SCROLLBAR
SYS_COLOUR_BACKGROUND = _misc_.SYS_COLOUR_BACKGROUND
SYS_COLOUR_DESKTOP = _misc_.SYS_COLOUR_DESKTOP
SYS_COLOUR_ACTIVECAPTION = _misc_.SYS_COLOUR_ACTIVECAPTION
SYS_COLOUR_INACTIVECAPTION = _misc_.SYS_COLOUR_INACTIVECAPTION
SYS_COLOUR_MENU = _misc_.SYS_COLOUR_MENU
SYS_COLOUR_WINDOW = _misc_.SYS_COLOUR_WINDOW
SYS_COLOUR_WINDOWFRAME = _misc_.SYS_COLOUR_WINDOWFRAME
SYS_COLOUR_MENUTEXT = _misc_.SYS_COLOUR_MENUTEXT
SYS_COLOUR_WINDOWTEXT = _misc_.SYS_COLOUR_WINDOWTEXT
SYS_COLOUR_CAPTIONTEXT = _misc_.SYS_COLOUR_CAPTIONTEXT
SYS_COLOUR_ACTIVEBORDER = _misc_.SYS_COLOUR_ACTIVEBORDER
SYS_COLOUR_INACTIVEBORDER = _misc_.SYS_COLOUR_INACTIVEBORDER
SYS_COLOUR_APPWORKSPACE = _misc_.SYS_COLOUR_APPWORKSPACE
SYS_COLOUR_HIGHLIGHT = _misc_.SYS_COLOUR_HIGHLIGHT
SYS_COLOUR_HIGHLIGHTTEXT = _misc_.SYS_COLOUR_HIGHLIGHTTEXT
SYS_COLOUR_BTNFACE = _misc_.SYS_COLOUR_BTNFACE
SYS_COLOUR_3DFACE = _misc_.SYS_COLOUR_3DFACE
SYS_COLOUR_BTNSHADOW = _misc_.SYS_COLOUR_BTNSHADOW
SYS_COLOUR_3DSHADOW = _misc_.SYS_COLOUR_3DSHADOW
SYS_COLOUR_GRAYTEXT = _misc_.SYS_COLOUR_GRAYTEXT
SYS_COLOUR_BTNTEXT = _misc_.SYS_COLOUR_BTNTEXT
SYS_COLOUR_INACTIVECAPTIONTEXT = _misc_.SYS_COLOUR_INACTIVECAPTIONTEXT
SYS_COLOUR_BTNHIGHLIGHT = _misc_.SYS_COLOUR_BTNHIGHLIGHT
SYS_COLOUR_BTNHILIGHT = _misc_.SYS_COLOUR_BTNHILIGHT
SYS_COLOUR_3DHIGHLIGHT = _misc_.SYS_COLOUR_3DHIGHLIGHT
SYS_COLOUR_3DHILIGHT = _misc_.SYS_COLOUR_3DHILIGHT
SYS_COLOUR_3DDKSHADOW = _misc_.SYS_COLOUR_3DDKSHADOW
SYS_COLOUR_3DLIGHT = _misc_.SYS_COLOUR_3DLIGHT
SYS_COLOUR_INFOTEXT = _misc_.SYS_COLOUR_INFOTEXT
SYS_COLOUR_INFOBK = _misc_.SYS_COLOUR_INFOBK
SYS_COLOUR_LISTBOX = _misc_.SYS_COLOUR_LISTBOX
SYS_COLOUR_HOTLIGHT = _misc_.SYS_COLOUR_HOTLIGHT
SYS_COLOUR_GRADIENTACTIVECAPTION = _misc_.SYS_COLOUR_GRADIENTACTIVECAPTION
SYS_COLOUR_GRADIENTINACTIVECAPTION = _misc_.SYS_COLOUR_GRADIENTINACTIVECAPTION
SYS_COLOUR_MENUHILIGHT = _misc_.SYS_COLOUR_MENUHILIGHT
SYS_COLOUR_MENUBAR = _misc_.SYS_COLOUR_MENUBAR
SYS_COLOUR_MAX = _misc_.SYS_COLOUR_MAX
SYS_MOUSE_BUTTONS = _misc_.SYS_MOUSE_BUTTONS
SYS_BORDER_X = _misc_.SYS_BORDER_X
SYS_BORDER_Y = _misc_.SYS_BORDER_Y
SYS_CURSOR_X = _misc_.SYS_CURSOR_X
SYS_CURSOR_Y = _misc_.SYS_CURSOR_Y
SYS_DCLICK_X = _misc_.SYS_DCLICK_X
SYS_DCLICK_Y = _misc_.SYS_DCLICK_Y
SYS_DRAG_X = _misc_.SYS_DRAG_X
SYS_DRAG_Y = _misc_.SYS_DRAG_Y
SYS_EDGE_X = _misc_.SYS_EDGE_X
SYS_EDGE_Y = _misc_.SYS_EDGE_Y
SYS_HSCROLL_ARROW_X = _misc_.SYS_HSCROLL_ARROW_X
SYS_HSCROLL_ARROW_Y = _misc_.SYS_HSCROLL_ARROW_Y
SYS_HTHUMB_X = _misc_.SYS_HTHUMB_X
SYS_ICON_X = _misc_.SYS_ICON_X
SYS_ICON_Y = _misc_.SYS_ICON_Y
SYS_ICONSPACING_X = _misc_.SYS_ICONSPACING_X
SYS_ICONSPACING_Y = _misc_.SYS_ICONSPACING_Y
SYS_WINDOWMIN_X = _misc_.SYS_WINDOWMIN_X
SYS_WINDOWMIN_Y = _misc_.SYS_WINDOWMIN_Y
SYS_SCREEN_X = _misc_.SYS_SCREEN_X
SYS_SCREEN_Y = _misc_.SYS_SCREEN_Y
SYS_FRAMESIZE_X = _misc_.SYS_FRAMESIZE_X
SYS_FRAMESIZE_Y = _misc_.SYS_FRAMESIZE_Y
SYS_SMALLICON_X = _misc_.SYS_SMALLICON_X
SYS_SMALLICON_Y = _misc_.SYS_SMALLICON_Y
SYS_HSCROLL_Y = _misc_.SYS_HSCROLL_Y
SYS_VSCROLL_X = _misc_.SYS_VSCROLL_X
SYS_VSCROLL_ARROW_X = _misc_.SYS_VSCROLL_ARROW_X
SYS_VSCROLL_ARROW_Y = _misc_.SYS_VSCROLL_ARROW_Y
SYS_VTHUMB_Y = _misc_.SYS_VTHUMB_Y
SYS_CAPTION_Y = _misc_.SYS_CAPTION_Y
SYS_MENU_Y = _misc_.SYS_MENU_Y
SYS_NETWORK_PRESENT = _misc_.SYS_NETWORK_PRESENT
SYS_PENWINDOWS_PRESENT = _misc_.SYS_PENWINDOWS_PRESENT
SYS_SHOW_SOUNDS = _misc_.SYS_SHOW_SOUNDS
SYS_SWAP_BUTTONS = _misc_.SYS_SWAP_BUTTONS
SYS_CAN_DRAW_FRAME_DECORATIONS = _misc_.SYS_CAN_DRAW_FRAME_DECORATIONS
SYS_CAN_ICONIZE_FRAME = _misc_.SYS_CAN_ICONIZE_FRAME
SYS_TABLET_PRESENT = _misc_.SYS_TABLET_PRESENT
SYS_SCREEN_NONE = _misc_.SYS_SCREEN_NONE
SYS_SCREEN_TINY = _misc_.SYS_SCREEN_TINY
SYS_SCREEN_PDA = _misc_.SYS_SCREEN_PDA
SYS_SCREEN_SMALL = _misc_.SYS_SCREEN_SMALL
SYS_SCREEN_DESKTOP = _misc_.SYS_SCREEN_DESKTOP

class SystemSettings(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetColour(*args, **kwargs):
        return _misc_.SystemSettings_GetColour(*args, **kwargs)

    GetColour = staticmethod(GetColour)

    def GetFont(*args, **kwargs):
        return _misc_.SystemSettings_GetFont(*args, **kwargs)

    GetFont = staticmethod(GetFont)

    def GetMetric(*args, **kwargs):
        return _misc_.SystemSettings_GetMetric(*args, **kwargs)

    GetMetric = staticmethod(GetMetric)

    def HasFeature(*args, **kwargs):
        return _misc_.SystemSettings_HasFeature(*args, **kwargs)

    HasFeature = staticmethod(HasFeature)

    def GetScreenType(*args, **kwargs):
        return _misc_.SystemSettings_GetScreenType(*args, **kwargs)

    GetScreenType = staticmethod(GetScreenType)

    def SetScreenType(*args, **kwargs):
        return _misc_.SystemSettings_SetScreenType(*args, **kwargs)

    SetScreenType = staticmethod(SetScreenType)


_misc_.SystemSettings_swigregister(SystemSettings)

def SystemSettings_GetColour(*args, **kwargs):
    return _misc_.SystemSettings_GetColour(*args, **kwargs)


def SystemSettings_GetFont(*args, **kwargs):
    return _misc_.SystemSettings_GetFont(*args, **kwargs)


def SystemSettings_GetMetric(*args, **kwargs):
    return _misc_.SystemSettings_GetMetric(*args, **kwargs)


def SystemSettings_HasFeature(*args, **kwargs):
    return _misc_.SystemSettings_HasFeature(*args, **kwargs)


def SystemSettings_GetScreenType(*args):
    return _misc_.SystemSettings_GetScreenType(*args)


def SystemSettings_SetScreenType(*args, **kwargs):
    return _misc_.SystemSettings_SetScreenType(*args, **kwargs)


class SystemOptions(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.SystemOptions_swiginit(self, _misc_.new_SystemOptions(*args, **kwargs))

    def SetOption(*args, **kwargs):
        return _misc_.SystemOptions_SetOption(*args, **kwargs)

    SetOption = staticmethod(SetOption)

    def SetOptionInt(*args, **kwargs):
        return _misc_.SystemOptions_SetOptionInt(*args, **kwargs)

    SetOptionInt = staticmethod(SetOptionInt)

    def GetOption(*args, **kwargs):
        return _misc_.SystemOptions_GetOption(*args, **kwargs)

    GetOption = staticmethod(GetOption)

    def GetOptionInt(*args, **kwargs):
        return _misc_.SystemOptions_GetOptionInt(*args, **kwargs)

    GetOptionInt = staticmethod(GetOptionInt)

    def HasOption(*args, **kwargs):
        return _misc_.SystemOptions_HasOption(*args, **kwargs)

    HasOption = staticmethod(HasOption)

    def IsFalse(*args, **kwargs):
        return _misc_.SystemOptions_IsFalse(*args, **kwargs)

    IsFalse = staticmethod(IsFalse)


_misc_.SystemOptions_swigregister(SystemOptions)
cvar = _misc_.cvar
WINDOW_DEFAULT_VARIANT = cvar.WINDOW_DEFAULT_VARIANT

def SystemOptions_SetOption(*args, **kwargs):
    return _misc_.SystemOptions_SetOption(*args, **kwargs)


def SystemOptions_SetOptionInt(*args, **kwargs):
    return _misc_.SystemOptions_SetOptionInt(*args, **kwargs)


def SystemOptions_GetOption(*args, **kwargs):
    return _misc_.SystemOptions_GetOption(*args, **kwargs)


def SystemOptions_GetOptionInt(*args, **kwargs):
    return _misc_.SystemOptions_GetOptionInt(*args, **kwargs)


def SystemOptions_HasOption(*args, **kwargs):
    return _misc_.SystemOptions_HasOption(*args, **kwargs)


def SystemOptions_IsFalse(*args, **kwargs):
    return _misc_.SystemOptions_IsFalse(*args, **kwargs)


def NewId(*args):
    return _misc_.NewId(*args)


def RegisterId(*args, **kwargs):
    return _misc_.RegisterId(*args, **kwargs)


def GetCurrentId(*args):
    return _misc_.GetCurrentId(*args)


def IsStockID(*args, **kwargs):
    return _misc_.IsStockID(*args, **kwargs)


def IsStockLabel(*args, **kwargs):
    return _misc_.IsStockLabel(*args, **kwargs)


STOCK_NOFLAGS = _misc_.STOCK_NOFLAGS
STOCK_WITH_MNEMONIC = _misc_.STOCK_WITH_MNEMONIC
STOCK_WITH_ACCELERATOR = _misc_.STOCK_WITH_ACCELERATOR

def GetStockLabel(*args, **kwargs):
    return _misc_.GetStockLabel(*args, **kwargs)


STOCK_MENU = _misc_.STOCK_MENU

def GetStockHelpString(*args, **kwargs):
    return _misc_.GetStockHelpString(*args, **kwargs)


def Bell(*args):
    return _misc_.Bell(*args)


def EndBusyCursor(*args):
    return _misc_.EndBusyCursor(*args)


def GetElapsedTime(*args, **kwargs):
    return _misc_.GetElapsedTime(*args, **kwargs)


GetElapsedTime = wx._deprecated(GetElapsedTime)

def IsBusy(*args):
    return _misc_.IsBusy(*args)


def Now(*args):
    return _misc_.Now(*args)


def Shell(*args, **kwargs):
    return _misc_.Shell(*args, **kwargs)


def StartTimer(*args):
    return _misc_.StartTimer(*args)


def GetOsVersion(*args):
    return _misc_.GetOsVersion(*args)


def GetOsDescription(*args):
    return _misc_.GetOsDescription(*args)


def IsPlatformLittleEndian(*args):
    return _misc_.IsPlatformLittleEndian(*args)


def IsPlatform64Bit(*args):
    return _misc_.IsPlatform64Bit(*args)


def GetFreeMemory(*args):
    return _misc_.GetFreeMemory(*args)


SHUTDOWN_POWEROFF = _misc_.SHUTDOWN_POWEROFF
SHUTDOWN_REBOOT = _misc_.SHUTDOWN_REBOOT

def Shutdown(*args, **kwargs):
    return _misc_.Shutdown(*args, **kwargs)


def Sleep(*args, **kwargs):
    return _misc_.Sleep(*args, **kwargs)


def MilliSleep(*args, **kwargs):
    return _misc_.MilliSleep(*args, **kwargs)


def MicroSleep(*args, **kwargs):
    return _misc_.MicroSleep(*args, **kwargs)


Usleep = MilliSleep

def EnableTopLevelWindows(*args, **kwargs):
    return _misc_.EnableTopLevelWindows(*args, **kwargs)


def StripMenuCodes(*args, **kwargs):
    return _misc_.StripMenuCodes(*args, **kwargs)


def GetEmailAddress(*args):
    return _misc_.GetEmailAddress(*args)


def GetHostName(*args):
    return _misc_.GetHostName(*args)


def GetFullHostName(*args):
    return _misc_.GetFullHostName(*args)


def GetUserId(*args):
    return _misc_.GetUserId(*args)


def GetUserName(*args):
    return _misc_.GetUserName(*args)


def GetHomeDir(*args):
    return _misc_.GetHomeDir(*args)


def GetUserHome(*args, **kwargs):
    return _misc_.GetUserHome(*args, **kwargs)


def GetProcessId(*args):
    return _misc_.GetProcessId(*args)


def Trap(*args):
    return _misc_.Trap(*args)


def FileSelector(*args, **kwargs):
    return _misc_.FileSelector(*args, **kwargs)


def LoadFileSelector(*args, **kwargs):
    return _misc_.LoadFileSelector(*args, **kwargs)


def SaveFileSelector(*args, **kwargs):
    return _misc_.SaveFileSelector(*args, **kwargs)


def DirSelector(*args, **kwargs):
    return _misc_.DirSelector(*args, **kwargs)


def GetTextFromUser(*args, **kwargs):
    return _misc_.GetTextFromUser(*args, **kwargs)


def GetPasswordFromUser(*args, **kwargs):
    return _misc_.GetPasswordFromUser(*args, **kwargs)


def GetSingleChoice(*args, **kwargs):
    return _misc_.GetSingleChoice(*args, **kwargs)


def GetSingleChoiceIndex(*args, **kwargs):
    return _misc_.GetSingleChoiceIndex(*args, **kwargs)


def MessageBox(*args, **kwargs):
    return _misc_.MessageBox(*args, **kwargs)


def ColourDisplay(*args):
    return _misc_.ColourDisplay(*args)


def DisplayDepth(*args):
    return _misc_.DisplayDepth(*args)


def GetDisplayDepth(*args):
    return _misc_.GetDisplayDepth(*args)


def DisplaySize(*args):
    return _misc_.DisplaySize(*args)


def GetDisplaySize(*args):
    return _misc_.GetDisplaySize(*args)


def DisplaySizeMM(*args):
    return _misc_.DisplaySizeMM(*args)


def GetDisplaySizeMM(*args):
    return _misc_.GetDisplaySizeMM(*args)


def ClientDisplayRect(*args):
    return _misc_.ClientDisplayRect(*args)


def GetClientDisplayRect(*args):
    return _misc_.GetClientDisplayRect(*args)


def SetCursor(*args, **kwargs):
    return _misc_.SetCursor(*args, **kwargs)


def GetXDisplay(*args):
    return _misc_.GetXDisplay(*args)


def BeginBusyCursor(*args, **kwargs):
    return _misc_.BeginBusyCursor(*args, **kwargs)


def GetMousePosition(*args):
    return _misc_.GetMousePosition(*args)


def FindWindowAtPointer(*args):
    return _misc_.FindWindowAtPointer(*args)


def GetActiveWindow(*args):
    return _misc_.GetActiveWindow(*args)


def GenericFindWindowAtPoint(*args, **kwargs):
    return _misc_.GenericFindWindowAtPoint(*args, **kwargs)


def FindWindowAtPoint(*args, **kwargs):
    return _misc_.FindWindowAtPoint(*args, **kwargs)


def GetTopLevelParent(*args, **kwargs):
    return _misc_.GetTopLevelParent(*args, **kwargs)


def LaunchDefaultBrowser(*args, **kwargs):
    return _misc_.LaunchDefaultBrowser(*args, **kwargs)


def GetKeyState(*args, **kwargs):
    return _misc_.GetKeyState(*args, **kwargs)


class MouseState(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.MouseState_swiginit(self, _misc_.new_MouseState(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_MouseState
    __del__ = lambda self: None

    def GetX(*args, **kwargs):
        return _misc_.MouseState_GetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _misc_.MouseState_GetY(*args, **kwargs)

    def LeftDown(*args, **kwargs):
        return _misc_.MouseState_LeftDown(*args, **kwargs)

    def MiddleDown(*args, **kwargs):
        return _misc_.MouseState_MiddleDown(*args, **kwargs)

    def RightDown(*args, **kwargs):
        return _misc_.MouseState_RightDown(*args, **kwargs)

    def ControlDown(*args, **kwargs):
        return _misc_.MouseState_ControlDown(*args, **kwargs)

    def ShiftDown(*args, **kwargs):
        return _misc_.MouseState_ShiftDown(*args, **kwargs)

    def AltDown(*args, **kwargs):
        return _misc_.MouseState_AltDown(*args, **kwargs)

    def MetaDown(*args, **kwargs):
        return _misc_.MouseState_MetaDown(*args, **kwargs)

    def CmdDown(*args, **kwargs):
        return _misc_.MouseState_CmdDown(*args, **kwargs)

    def SetX(*args, **kwargs):
        return _misc_.MouseState_SetX(*args, **kwargs)

    def SetY(*args, **kwargs):
        return _misc_.MouseState_SetY(*args, **kwargs)

    def SetLeftDown(*args, **kwargs):
        return _misc_.MouseState_SetLeftDown(*args, **kwargs)

    def SetMiddleDown(*args, **kwargs):
        return _misc_.MouseState_SetMiddleDown(*args, **kwargs)

    def SetRightDown(*args, **kwargs):
        return _misc_.MouseState_SetRightDown(*args, **kwargs)

    def SetControlDown(*args, **kwargs):
        return _misc_.MouseState_SetControlDown(*args, **kwargs)

    def SetShiftDown(*args, **kwargs):
        return _misc_.MouseState_SetShiftDown(*args, **kwargs)

    def SetAltDown(*args, **kwargs):
        return _misc_.MouseState_SetAltDown(*args, **kwargs)

    def SetMetaDown(*args, **kwargs):
        return _misc_.MouseState_SetMetaDown(*args, **kwargs)

    x = property(GetX, SetX)
    y = property(GetY, SetY)
    leftDown = property(LeftDown, SetLeftDown)
    middleDown = property(MiddleDown, SetMiddleDown)
    rightDown = property(RightDown, SetRightDown)
    controlDown = property(ControlDown, SetControlDown)
    shiftDown = property(ShiftDown, SetShiftDown)
    altDown = property(AltDown, SetAltDown)
    metaDown = property(MetaDown, SetMetaDown)
    cmdDown = property(CmdDown)


_misc_.MouseState_swigregister(MouseState)
FileSelectorPromptStr = cvar.FileSelectorPromptStr
FileSelectorDefaultWildcardStr = cvar.FileSelectorDefaultWildcardStr
DirSelectorPromptStr = cvar.DirSelectorPromptStr

def GetMouseState(*args):
    return _misc_.GetMouseState(*args)


def WakeUpMainThread(*args):
    return _misc_.WakeUpMainThread(*args)


def MutexGuiEnter(*args):
    return _misc_.MutexGuiEnter(*args)


def MutexGuiLeave(*args):
    return _misc_.MutexGuiLeave(*args)


class MutexGuiLocker(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.MutexGuiLocker_swiginit(self, _misc_.new_MutexGuiLocker(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_MutexGuiLocker
    __del__ = lambda self: None


_misc_.MutexGuiLocker_swigregister(MutexGuiLocker)

def Thread_IsMain(*args):
    return _misc_.Thread_IsMain(*args)


class ToolTip(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.ToolTip_swiginit(self, _misc_.new_ToolTip(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_ToolTip
    __del__ = lambda self: None

    def SetTip(*args, **kwargs):
        return _misc_.ToolTip_SetTip(*args, **kwargs)

    def GetTip(*args, **kwargs):
        return _misc_.ToolTip_GetTip(*args, **kwargs)

    def GetWindow(*args, **kwargs):
        return _misc_.ToolTip_GetWindow(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _misc_.ToolTip_Enable(*args, **kwargs)

    Enable = staticmethod(Enable)

    def SetDelay(*args, **kwargs):
        return _misc_.ToolTip_SetDelay(*args, **kwargs)

    SetDelay = staticmethod(SetDelay)
    Tip = property(GetTip, SetTip, doc='See `GetTip` and `SetTip`')
    Window = property(GetWindow, doc='See `GetWindow`')


_misc_.ToolTip_swigregister(ToolTip)

def ToolTip_Enable(*args, **kwargs):
    return _misc_.ToolTip_Enable(*args, **kwargs)


def ToolTip_SetDelay(*args, **kwargs):
    return _misc_.ToolTip_SetDelay(*args, **kwargs)


class Caret(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.Caret_swiginit(self, _misc_.new_Caret(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_Caret
    __del__ = lambda self: None

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _misc_.Caret_Destroy(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _misc_.Caret_IsOk(*args, **kwargs)

    def IsVisible(*args, **kwargs):
        return _misc_.Caret_IsVisible(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _misc_.Caret_GetPosition(*args, **kwargs)

    def GetPositionTuple(*args, **kwargs):
        return _misc_.Caret_GetPositionTuple(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _misc_.Caret_GetSize(*args, **kwargs)

    def GetSizeTuple(*args, **kwargs):
        return _misc_.Caret_GetSizeTuple(*args, **kwargs)

    def GetWindow(*args, **kwargs):
        return _misc_.Caret_GetWindow(*args, **kwargs)

    def MoveXY(*args, **kwargs):
        return _misc_.Caret_MoveXY(*args, **kwargs)

    def Move(*args, **kwargs):
        return _misc_.Caret_Move(*args, **kwargs)

    def SetSizeWH(*args, **kwargs):
        return _misc_.Caret_SetSizeWH(*args, **kwargs)

    def SetSize(*args, **kwargs):
        return _misc_.Caret_SetSize(*args, **kwargs)

    def Show(*args, **kwargs):
        return _misc_.Caret_Show(*args, **kwargs)

    def Hide(*args, **kwargs):
        return _misc_.Caret_Hide(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def GetBlinkTime(*args, **kwargs):
        return _misc_.Caret_GetBlinkTime(*args, **kwargs)

    GetBlinkTime = staticmethod(GetBlinkTime)

    def SetBlinkTime(*args, **kwargs):
        return _misc_.Caret_SetBlinkTime(*args, **kwargs)

    SetBlinkTime = staticmethod(SetBlinkTime)
    Position = property(GetPosition, doc='See `GetPosition`')
    Size = property(GetSize, SetSize, doc='See `GetSize` and `SetSize`')
    Window = property(GetWindow, doc='See `GetWindow`')


_misc_.Caret_swigregister(Caret)

def Caret_GetBlinkTime(*args):
    return _misc_.Caret_GetBlinkTime(*args)


def Caret_SetBlinkTime(*args, **kwargs):
    return _misc_.Caret_SetBlinkTime(*args, **kwargs)


class BusyCursor(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.BusyCursor_swiginit(self, _misc_.new_BusyCursor(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_BusyCursor
    __del__ = lambda self: None


_misc_.BusyCursor_swigregister(BusyCursor)

class WindowDisabler(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.WindowDisabler_swiginit(self, _misc_.new_WindowDisabler(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_WindowDisabler
    __del__ = lambda self: None


_misc_.WindowDisabler_swigregister(WindowDisabler)
OS_UNKNOWN = _misc_.OS_UNKNOWN
OS_MAC_OS = _misc_.OS_MAC_OS
OS_MAC_OSX_DARWIN = _misc_.OS_MAC_OSX_DARWIN
OS_MAC = _misc_.OS_MAC
OS_WINDOWS_9X = _misc_.OS_WINDOWS_9X
OS_WINDOWS_NT = _misc_.OS_WINDOWS_NT
OS_WINDOWS_MICRO = _misc_.OS_WINDOWS_MICRO
OS_WINDOWS_CE = _misc_.OS_WINDOWS_CE
OS_WINDOWS = _misc_.OS_WINDOWS
OS_UNIX_LINUX = _misc_.OS_UNIX_LINUX
OS_UNIX_FREEBSD = _misc_.OS_UNIX_FREEBSD
OS_UNIX_OPENBSD = _misc_.OS_UNIX_OPENBSD
OS_UNIX_NETBSD = _misc_.OS_UNIX_NETBSD
OS_UNIX_SOLARIS = _misc_.OS_UNIX_SOLARIS
OS_UNIX_AIX = _misc_.OS_UNIX_AIX
OS_UNIX_HPUX = _misc_.OS_UNIX_HPUX
OS_UNIX = _misc_.OS_UNIX
OS_DOS = _misc_.OS_DOS
OS_OS2 = _misc_.OS_OS2
PORT_UNKNOWN = _misc_.PORT_UNKNOWN
PORT_BASE = _misc_.PORT_BASE
PORT_MSW = _misc_.PORT_MSW
PORT_MOTIF = _misc_.PORT_MOTIF
PORT_GTK = _misc_.PORT_GTK
PORT_MGL = _misc_.PORT_MGL
PORT_X11 = _misc_.PORT_X11
PORT_PM = _misc_.PORT_PM
PORT_OS2 = _misc_.PORT_OS2
PORT_MAC = _misc_.PORT_MAC
PORT_COCOA = _misc_.PORT_COCOA
PORT_WINCE = _misc_.PORT_WINCE
PORT_PALMOS = _misc_.PORT_PALMOS
PORT_DFB = _misc_.PORT_DFB
ARCH_INVALID = _misc_.ARCH_INVALID
ARCH_32 = _misc_.ARCH_32
ARCH_64 = _misc_.ARCH_64
ARCH_MAX = _misc_.ARCH_MAX
ENDIAN_INVALID = _misc_.ENDIAN_INVALID
ENDIAN_BIG = _misc_.ENDIAN_BIG
ENDIAN_LITTLE = _misc_.ENDIAN_LITTLE
ENDIAN_PDP = _misc_.ENDIAN_PDP
ENDIAN_MAX = _misc_.ENDIAN_MAX

class PlatformInformation(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.PlatformInformation_swiginit(self, _misc_.new_PlatformInformation(*args, **kwargs))

    def __eq__(*args, **kwargs):
        return _misc_.PlatformInformation___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _misc_.PlatformInformation___ne__(*args, **kwargs)

    def GetOSMajorVersion(*args, **kwargs):
        return _misc_.PlatformInformation_GetOSMajorVersion(*args, **kwargs)

    def GetOSMinorVersion(*args, **kwargs):
        return _misc_.PlatformInformation_GetOSMinorVersion(*args, **kwargs)

    def CheckOSVersion(*args, **kwargs):
        return _misc_.PlatformInformation_CheckOSVersion(*args, **kwargs)

    def GetToolkitMajorVersion(*args, **kwargs):
        return _misc_.PlatformInformation_GetToolkitMajorVersion(*args, **kwargs)

    def GetToolkitMinorVersion(*args, **kwargs):
        return _misc_.PlatformInformation_GetToolkitMinorVersion(*args, **kwargs)

    def CheckToolkitVersion(*args, **kwargs):
        return _misc_.PlatformInformation_CheckToolkitVersion(*args, **kwargs)

    def IsUsingUniversalWidgets(*args, **kwargs):
        return _misc_.PlatformInformation_IsUsingUniversalWidgets(*args, **kwargs)

    def GetOperatingSystemId(*args, **kwargs):
        return _misc_.PlatformInformation_GetOperatingSystemId(*args, **kwargs)

    def GetPortId(*args, **kwargs):
        return _misc_.PlatformInformation_GetPortId(*args, **kwargs)

    def GetArchitecture(*args, **kwargs):
        return _misc_.PlatformInformation_GetArchitecture(*args, **kwargs)

    def GetEndianness(*args, **kwargs):
        return _misc_.PlatformInformation_GetEndianness(*args, **kwargs)

    def GetOperatingSystemFamilyName(*args, **kwargs):
        return _misc_.PlatformInformation_GetOperatingSystemFamilyName(*args, **kwargs)

    def GetOperatingSystemIdName(*args, **kwargs):
        return _misc_.PlatformInformation_GetOperatingSystemIdName(*args, **kwargs)

    def GetPortIdName(*args, **kwargs):
        return _misc_.PlatformInformation_GetPortIdName(*args, **kwargs)

    def GetPortIdShortName(*args, **kwargs):
        return _misc_.PlatformInformation_GetPortIdShortName(*args, **kwargs)

    def GetArchName(*args, **kwargs):
        return _misc_.PlatformInformation_GetArchName(*args, **kwargs)

    def GetEndiannessName(*args, **kwargs):
        return _misc_.PlatformInformation_GetEndiannessName(*args, **kwargs)

    def SetOSVersion(*args, **kwargs):
        return _misc_.PlatformInformation_SetOSVersion(*args, **kwargs)

    def SetToolkitVersion(*args, **kwargs):
        return _misc_.PlatformInformation_SetToolkitVersion(*args, **kwargs)

    def SetOperatingSystemId(*args, **kwargs):
        return _misc_.PlatformInformation_SetOperatingSystemId(*args, **kwargs)

    def SetPortId(*args, **kwargs):
        return _misc_.PlatformInformation_SetPortId(*args, **kwargs)

    def SetArchitecture(*args, **kwargs):
        return _misc_.PlatformInformation_SetArchitecture(*args, **kwargs)

    def SetEndianness(*args, **kwargs):
        return _misc_.PlatformInformation_SetEndianness(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _misc_.PlatformInformation_IsOk(*args, **kwargs)

    ArchName = property(GetArchName, doc='See `GetArchName`')
    Architecture = property(GetArchitecture, SetArchitecture, doc='See `GetArchitecture` and `SetArchitecture`')
    Endianness = property(GetEndianness, SetEndianness, doc='See `GetEndianness` and `SetEndianness`')
    EndiannessName = property(GetEndiannessName, doc='See `GetEndiannessName`')
    OSMajorVersion = property(GetOSMajorVersion, doc='See `GetOSMajorVersion`')
    OSMinorVersion = property(GetOSMinorVersion, doc='See `GetOSMinorVersion`')
    OperatingSystemFamilyName = property(GetOperatingSystemFamilyName, doc='See `GetOperatingSystemFamilyName`')
    OperatingSystemId = property(GetOperatingSystemId, SetOperatingSystemId, doc='See `GetOperatingSystemId` and `SetOperatingSystemId`')
    OperatingSystemIdName = property(GetOperatingSystemIdName, doc='See `GetOperatingSystemIdName`')
    PortId = property(GetPortId, SetPortId, doc='See `GetPortId` and `SetPortId`')
    PortIdName = property(GetPortIdName, doc='See `GetPortIdName`')
    PortIdShortName = property(GetPortIdShortName, doc='See `GetPortIdShortName`')
    ToolkitMajorVersion = property(GetToolkitMajorVersion, doc='See `GetToolkitMajorVersion`')
    ToolkitMinorVersion = property(GetToolkitMinorVersion, doc='See `GetToolkitMinorVersion`')


_misc_.PlatformInformation_swigregister(PlatformInformation)

def DrawWindowOnDC(*args, **kwargs):
    return _misc_.DrawWindowOnDC(*args, **kwargs)


TIMER_CONTINUOUS = _misc_.TIMER_CONTINUOUS
TIMER_ONE_SHOT = _misc_.TIMER_ONE_SHOT
wxEVT_TIMER = _misc_.wxEVT_TIMER

class Timer(_core.EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.Timer_swiginit(self, _misc_.new_Timer(*args, **kwargs))
        self._setOORInfo(self, 0)
        self.this.own(True)
        Timer._setCallbackInfo(self, self, Timer)

    __swig_destroy__ = _misc_.delete_Timer
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.Timer__setCallbackInfo(*args, **kwargs)

    def SetOwner(*args, **kwargs):
        return _misc_.Timer_SetOwner(*args, **kwargs)

    def GetOwner(*args, **kwargs):
        return _misc_.Timer_GetOwner(*args, **kwargs)

    def Start(*args, **kwargs):
        return _misc_.Timer_Start(*args, **kwargs)

    def Stop(*args, **kwargs):
        return _misc_.Timer_Stop(*args, **kwargs)

    def Notify(*args, **kwargs):
        return _misc_.Timer_Notify(*args, **kwargs)

    def IsRunning(*args, **kwargs):
        return _misc_.Timer_IsRunning(*args, **kwargs)

    def GetInterval(*args, **kwargs):
        return _misc_.Timer_GetInterval(*args, **kwargs)

    def GetId(*args, **kwargs):
        return _misc_.Timer_GetId(*args, **kwargs)

    def IsOneShot(*args, **kwargs):
        return _misc_.Timer_IsOneShot(*args, **kwargs)

    def Destroy(self):
        pass

    Id = property(GetId, doc='See `GetId`')
    Interval = property(GetInterval, doc='See `GetInterval`')
    Owner = property(GetOwner, SetOwner, doc='See `GetOwner` and `SetOwner`')


_misc_.Timer_swigregister(Timer)

class PyTimer(Timer):

    def __init__(self, notify):
        Timer.__init__(self)
        self.notify = notify

    def Notify(self):
        if self.notify:
            self.notify()


EVT_TIMER = wx.PyEventBinder(wxEVT_TIMER, 1)

class TimerEvent(_core.Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.TimerEvent_swiginit(self, _misc_.new_TimerEvent(*args, **kwargs))

    def GetInterval(*args, **kwargs):
        return _misc_.TimerEvent_GetInterval(*args, **kwargs)

    Interval = property(GetInterval, doc='See `GetInterval`')


_misc_.TimerEvent_swigregister(TimerEvent)

class TimerRunner(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _misc_.TimerRunner_swiginit(self, _misc_.new_TimerRunner(*args))

    __swig_destroy__ = _misc_.delete_TimerRunner
    __del__ = lambda self: None

    def Start(*args, **kwargs):
        return _misc_.TimerRunner_Start(*args, **kwargs)


_misc_.TimerRunner_swigregister(TimerRunner)
LOG_FatalError = _misc_.LOG_FatalError
LOG_Error = _misc_.LOG_Error
LOG_Warning = _misc_.LOG_Warning
LOG_Message = _misc_.LOG_Message
LOG_Status = _misc_.LOG_Status
LOG_Info = _misc_.LOG_Info
LOG_Debug = _misc_.LOG_Debug
LOG_Trace = _misc_.LOG_Trace
LOG_Progress = _misc_.LOG_Progress
LOG_User = _misc_.LOG_User
LOG_Max = _misc_.LOG_Max
TRACE_MemAlloc = _misc_.TRACE_MemAlloc
TRACE_Messages = _misc_.TRACE_Messages
TRACE_ResAlloc = _misc_.TRACE_ResAlloc
TRACE_RefCount = _misc_.TRACE_RefCount
TRACE_OleCalls = _misc_.TRACE_OleCalls
TraceMemAlloc = _misc_.TraceMemAlloc
TraceMessages = _misc_.TraceMessages
TraceResAlloc = _misc_.TraceResAlloc
TraceRefCount = _misc_.TraceRefCount
TraceOleCalls = _misc_.TraceOleCalls

class Log(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.Log_swiginit(self, _misc_.new_Log(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_Log
    __del__ = lambda self: None

    def IsEnabled(*args, **kwargs):
        return _misc_.Log_IsEnabled(*args, **kwargs)

    IsEnabled = staticmethod(IsEnabled)

    def EnableLogging(*args, **kwargs):
        return _misc_.Log_EnableLogging(*args, **kwargs)

    EnableLogging = staticmethod(EnableLogging)

    def OnLog(*args, **kwargs):
        return _misc_.Log_OnLog(*args, **kwargs)

    OnLog = staticmethod(OnLog)

    def Flush(*args, **kwargs):
        return _misc_.Log_Flush(*args, **kwargs)

    def FlushActive(*args, **kwargs):
        return _misc_.Log_FlushActive(*args, **kwargs)

    FlushActive = staticmethod(FlushActive)

    def GetActiveTarget(*args, **kwargs):
        return _misc_.Log_GetActiveTarget(*args, **kwargs)

    GetActiveTarget = staticmethod(GetActiveTarget)

    def SetActiveTarget(*args, **kwargs):
        return _misc_.Log_SetActiveTarget(*args, **kwargs)

    SetActiveTarget = staticmethod(SetActiveTarget)

    def Suspend(*args, **kwargs):
        return _misc_.Log_Suspend(*args, **kwargs)

    Suspend = staticmethod(Suspend)

    def Resume(*args, **kwargs):
        return _misc_.Log_Resume(*args, **kwargs)

    Resume = staticmethod(Resume)

    def SetVerbose(*args, **kwargs):
        return _misc_.Log_SetVerbose(*args, **kwargs)

    SetVerbose = staticmethod(SetVerbose)

    def SetLogLevel(*args, **kwargs):
        return _misc_.Log_SetLogLevel(*args, **kwargs)

    SetLogLevel = staticmethod(SetLogLevel)

    def DontCreateOnDemand(*args, **kwargs):
        return _misc_.Log_DontCreateOnDemand(*args, **kwargs)

    DontCreateOnDemand = staticmethod(DontCreateOnDemand)

    def SetRepetitionCounting(*args, **kwargs):
        return _misc_.Log_SetRepetitionCounting(*args, **kwargs)

    SetRepetitionCounting = staticmethod(SetRepetitionCounting)

    def GetRepetitionCounting(*args, **kwargs):
        return _misc_.Log_GetRepetitionCounting(*args, **kwargs)

    GetRepetitionCounting = staticmethod(GetRepetitionCounting)

    def SetTraceMask(*args, **kwargs):
        return _misc_.Log_SetTraceMask(*args, **kwargs)

    SetTraceMask = staticmethod(SetTraceMask)

    def AddTraceMask(*args, **kwargs):
        return _misc_.Log_AddTraceMask(*args, **kwargs)

    AddTraceMask = staticmethod(AddTraceMask)

    def RemoveTraceMask(*args, **kwargs):
        return _misc_.Log_RemoveTraceMask(*args, **kwargs)

    RemoveTraceMask = staticmethod(RemoveTraceMask)

    def ClearTraceMasks(*args, **kwargs):
        return _misc_.Log_ClearTraceMasks(*args, **kwargs)

    ClearTraceMasks = staticmethod(ClearTraceMasks)

    def GetTraceMasks(*args, **kwargs):
        return _misc_.Log_GetTraceMasks(*args, **kwargs)

    GetTraceMasks = staticmethod(GetTraceMasks)

    def SetTimestamp(*args, **kwargs):
        return _misc_.Log_SetTimestamp(*args, **kwargs)

    SetTimestamp = staticmethod(SetTimestamp)

    def GetVerbose(*args, **kwargs):
        return _misc_.Log_GetVerbose(*args, **kwargs)

    GetVerbose = staticmethod(GetVerbose)

    def GetTraceMask(*args, **kwargs):
        return _misc_.Log_GetTraceMask(*args, **kwargs)

    GetTraceMask = staticmethod(GetTraceMask)

    def IsAllowedTraceMask(*args, **kwargs):
        return _misc_.Log_IsAllowedTraceMask(*args, **kwargs)

    IsAllowedTraceMask = staticmethod(IsAllowedTraceMask)

    def GetLogLevel(*args, **kwargs):
        return _misc_.Log_GetLogLevel(*args, **kwargs)

    GetLogLevel = staticmethod(GetLogLevel)

    def GetTimestamp(*args, **kwargs):
        return _misc_.Log_GetTimestamp(*args, **kwargs)

    GetTimestamp = staticmethod(GetTimestamp)

    def TimeStamp(*args, **kwargs):
        return _misc_.Log_TimeStamp(*args, **kwargs)

    TimeStamp = staticmethod(TimeStamp)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _misc_.Log_Destroy(*args, **kwargs)


_misc_.Log_swigregister(Log)

def Log_IsEnabled(*args):
    return _misc_.Log_IsEnabled(*args)


def Log_EnableLogging(*args, **kwargs):
    return _misc_.Log_EnableLogging(*args, **kwargs)


def Log_OnLog(*args, **kwargs):
    return _misc_.Log_OnLog(*args, **kwargs)


def Log_FlushActive(*args):
    return _misc_.Log_FlushActive(*args)


def Log_GetActiveTarget(*args):
    return _misc_.Log_GetActiveTarget(*args)


def Log_SetActiveTarget(*args, **kwargs):
    return _misc_.Log_SetActiveTarget(*args, **kwargs)


def Log_Suspend(*args):
    return _misc_.Log_Suspend(*args)


def Log_Resume(*args):
    return _misc_.Log_Resume(*args)


def Log_SetVerbose(*args, **kwargs):
    return _misc_.Log_SetVerbose(*args, **kwargs)


def Log_SetLogLevel(*args, **kwargs):
    return _misc_.Log_SetLogLevel(*args, **kwargs)


def Log_DontCreateOnDemand(*args):
    return _misc_.Log_DontCreateOnDemand(*args)


def Log_SetRepetitionCounting(*args, **kwargs):
    return _misc_.Log_SetRepetitionCounting(*args, **kwargs)


def Log_GetRepetitionCounting(*args):
    return _misc_.Log_GetRepetitionCounting(*args)


def Log_SetTraceMask(*args, **kwargs):
    return _misc_.Log_SetTraceMask(*args, **kwargs)


def Log_AddTraceMask(*args, **kwargs):
    return _misc_.Log_AddTraceMask(*args, **kwargs)


def Log_RemoveTraceMask(*args, **kwargs):
    return _misc_.Log_RemoveTraceMask(*args, **kwargs)


def Log_ClearTraceMasks(*args):
    return _misc_.Log_ClearTraceMasks(*args)


def Log_GetTraceMasks(*args):
    return _misc_.Log_GetTraceMasks(*args)


def Log_SetTimestamp(*args, **kwargs):
    return _misc_.Log_SetTimestamp(*args, **kwargs)


def Log_GetVerbose(*args):
    return _misc_.Log_GetVerbose(*args)


def Log_GetTraceMask(*args):
    return _misc_.Log_GetTraceMask(*args)


def Log_IsAllowedTraceMask(*args, **kwargs):
    return _misc_.Log_IsAllowedTraceMask(*args, **kwargs)


def Log_GetLogLevel(*args):
    return _misc_.Log_GetLogLevel(*args)


def Log_GetTimestamp(*args):
    return _misc_.Log_GetTimestamp(*args)


def Log_TimeStamp(*args):
    return _misc_.Log_TimeStamp(*args)


class LogStderr(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogStderr_swiginit(self, _misc_.new_LogStderr(*args, **kwargs))


_misc_.LogStderr_swigregister(LogStderr)

class LogTextCtrl(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogTextCtrl_swiginit(self, _misc_.new_LogTextCtrl(*args, **kwargs))


_misc_.LogTextCtrl_swigregister(LogTextCtrl)

class LogGui(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogGui_swiginit(self, _misc_.new_LogGui(*args, **kwargs))


_misc_.LogGui_swigregister(LogGui)

class LogWindow(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogWindow_swiginit(self, _misc_.new_LogWindow(*args, **kwargs))

    def Show(*args, **kwargs):
        return _misc_.LogWindow_Show(*args, **kwargs)

    def GetFrame(*args, **kwargs):
        return _misc_.LogWindow_GetFrame(*args, **kwargs)

    def GetOldLog(*args, **kwargs):
        return _misc_.LogWindow_GetOldLog(*args, **kwargs)

    def IsPassingMessages(*args, **kwargs):
        return _misc_.LogWindow_IsPassingMessages(*args, **kwargs)

    def PassMessages(*args, **kwargs):
        return _misc_.LogWindow_PassMessages(*args, **kwargs)

    Frame = property(GetFrame, doc='See `GetFrame`')
    OldLog = property(GetOldLog, doc='See `GetOldLog`')


_misc_.LogWindow_swigregister(LogWindow)

class LogChain(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogChain_swiginit(self, _misc_.new_LogChain(*args, **kwargs))

    def SetLog(*args, **kwargs):
        return _misc_.LogChain_SetLog(*args, **kwargs)

    def PassMessages(*args, **kwargs):
        return _misc_.LogChain_PassMessages(*args, **kwargs)

    def IsPassingMessages(*args, **kwargs):
        return _misc_.LogChain_IsPassingMessages(*args, **kwargs)

    def GetOldLog(*args, **kwargs):
        return _misc_.LogChain_GetOldLog(*args, **kwargs)

    def DetachOldLog(*args, **kwargs):
        return _misc_.LogChain_DetachOldLog(*args, **kwargs)

    OldLog = property(GetOldLog, doc='See `GetOldLog`')


_misc_.LogChain_swigregister(LogChain)

class LogBuffer(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogBuffer_swiginit(self, _misc_.new_LogBuffer(*args, **kwargs))

    def GetBuffer(*args, **kwargs):
        return _misc_.LogBuffer_GetBuffer(*args, **kwargs)

    Buffer = property(GetBuffer, doc='See `GetBuffer`')


_misc_.LogBuffer_swigregister(LogBuffer)

def SysErrorCode(*args):
    return _misc_.SysErrorCode(*args)


def SysErrorMsg(*args, **kwargs):
    return _misc_.SysErrorMsg(*args, **kwargs)


def LogFatalError(*args, **kwargs):
    return _misc_.LogFatalError(*args, **kwargs)


def LogError(*args, **kwargs):
    return _misc_.LogError(*args, **kwargs)


def LogWarning(*args, **kwargs):
    return _misc_.LogWarning(*args, **kwargs)


def LogMessage(*args, **kwargs):
    return _misc_.LogMessage(*args, **kwargs)


def LogInfo(*args, **kwargs):
    return _misc_.LogInfo(*args, **kwargs)


def LogDebug(*args, **kwargs):
    return _misc_.LogDebug(*args, **kwargs)


def LogVerbose(*args, **kwargs):
    return _misc_.LogVerbose(*args, **kwargs)


def LogStatus(*args, **kwargs):
    return _misc_.LogStatus(*args, **kwargs)


def LogStatusFrame(*args, **kwargs):
    return _misc_.LogStatusFrame(*args, **kwargs)


def LogSysError(*args, **kwargs):
    return _misc_.LogSysError(*args, **kwargs)


def LogGeneric(*args, **kwargs):
    return _misc_.LogGeneric(*args, **kwargs)


def SafeShowMessage(*args, **kwargs):
    return _misc_.SafeShowMessage(*args, **kwargs)


class LogNull(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.LogNull_swiginit(self, _misc_.new_LogNull(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_LogNull
    __del__ = lambda self: None


_misc_.LogNull_swigregister(LogNull)

def LogTrace(*args):
    return _misc_.LogTrace(*args)


class PyLog(Log):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.PyLog_swiginit(self, _misc_.new_PyLog(*args, **kwargs))
        PyLog._setCallbackInfo(self, self, PyLog)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.PyLog__setCallbackInfo(*args, **kwargs)


_misc_.PyLog_swigregister(PyLog)
PROCESS_DEFAULT = _misc_.PROCESS_DEFAULT
PROCESS_REDIRECT = _misc_.PROCESS_REDIRECT
KILL_OK = _misc_.KILL_OK
KILL_BAD_SIGNAL = _misc_.KILL_BAD_SIGNAL
KILL_ACCESS_DENIED = _misc_.KILL_ACCESS_DENIED
KILL_NO_PROCESS = _misc_.KILL_NO_PROCESS
KILL_ERROR = _misc_.KILL_ERROR
KILL_NOCHILDREN = _misc_.KILL_NOCHILDREN
KILL_CHILDREN = _misc_.KILL_CHILDREN
SIGNONE = _misc_.SIGNONE
SIGHUP = _misc_.SIGHUP
SIGINT = _misc_.SIGINT
SIGQUIT = _misc_.SIGQUIT
SIGILL = _misc_.SIGILL
SIGTRAP = _misc_.SIGTRAP
SIGABRT = _misc_.SIGABRT
SIGIOT = _misc_.SIGIOT
SIGEMT = _misc_.SIGEMT
SIGFPE = _misc_.SIGFPE
SIGKILL = _misc_.SIGKILL
SIGBUS = _misc_.SIGBUS
SIGSEGV = _misc_.SIGSEGV
SIGSYS = _misc_.SIGSYS
SIGPIPE = _misc_.SIGPIPE
SIGALRM = _misc_.SIGALRM
SIGTERM = _misc_.SIGTERM

class Process(_core.EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def Kill(*args, **kwargs):
        return _misc_.Process_Kill(*args, **kwargs)

    Kill = staticmethod(Kill)

    def Exists(*args, **kwargs):
        return _misc_.Process_Exists(*args, **kwargs)

    Exists = staticmethod(Exists)

    def Open(*args, **kwargs):
        return _misc_.Process_Open(*args, **kwargs)

    Open = staticmethod(Open)

    def __init__(self, *args, **kwargs):
        _misc_.Process_swiginit(self, _misc_.new_Process(*args, **kwargs))
        Process._setCallbackInfo(self, self, Process)
        self.this.own(False)

    __swig_destroy__ = _misc_.delete_Process
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.Process__setCallbackInfo(*args, **kwargs)

    def GetPid(*args, **kwargs):
        return _misc_.Process_GetPid(*args, **kwargs)

    def OnTerminate(*args, **kwargs):
        return _misc_.Process_OnTerminate(*args, **kwargs)

    def base_OnTerminate(*args, **kw):
        return Process.OnTerminate(*args, **kw)

    base_OnTerminate = wx._deprecated(base_OnTerminate, 'Please use Process.OnTerminate instead.')

    def Redirect(*args, **kwargs):
        return _misc_.Process_Redirect(*args, **kwargs)

    def IsRedirected(*args, **kwargs):
        return _misc_.Process_IsRedirected(*args, **kwargs)

    def Detach(*args, **kwargs):
        return _misc_.Process_Detach(*args, **kwargs)

    def GetInputStream(*args, **kwargs):
        return _misc_.Process_GetInputStream(*args, **kwargs)

    def GetErrorStream(*args, **kwargs):
        return _misc_.Process_GetErrorStream(*args, **kwargs)

    def GetOutputStream(*args, **kwargs):
        return _misc_.Process_GetOutputStream(*args, **kwargs)

    def CloseOutput(*args, **kwargs):
        return _misc_.Process_CloseOutput(*args, **kwargs)

    def IsInputOpened(*args, **kwargs):
        return _misc_.Process_IsInputOpened(*args, **kwargs)

    def IsInputAvailable(*args, **kwargs):
        return _misc_.Process_IsInputAvailable(*args, **kwargs)

    def IsErrorAvailable(*args, **kwargs):
        return _misc_.Process_IsErrorAvailable(*args, **kwargs)

    ErrorStream = property(GetErrorStream, doc='See `GetErrorStream`')
    InputStream = property(GetInputStream, doc='See `GetInputStream`')
    OutputStream = property(GetOutputStream, doc='See `GetOutputStream`')
    InputOpened = property(IsInputOpened)
    InputAvailable = property(IsInputAvailable)
    ErrorAvailable = property(IsErrorAvailable)


_misc_.Process_swigregister(Process)

def Process_Kill(*args, **kwargs):
    return _misc_.Process_Kill(*args, **kwargs)


def Process_Exists(*args, **kwargs):
    return _misc_.Process_Exists(*args, **kwargs)


def Process_Open(*args, **kwargs):
    return _misc_.Process_Open(*args, **kwargs)


class ProcessEvent(_core.Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.ProcessEvent_swiginit(self, _misc_.new_ProcessEvent(*args, **kwargs))

    def GetPid(*args, **kwargs):
        return _misc_.ProcessEvent_GetPid(*args, **kwargs)

    def GetExitCode(*args, **kwargs):
        return _misc_.ProcessEvent_GetExitCode(*args, **kwargs)

    m_pid = property(_misc_.ProcessEvent_m_pid_get, _misc_.ProcessEvent_m_pid_set)
    m_exitcode = property(_misc_.ProcessEvent_m_exitcode_get, _misc_.ProcessEvent_m_exitcode_set)
    ExitCode = property(GetExitCode, doc='See `GetExitCode`')
    Pid = property(GetPid, doc='See `GetPid`')


_misc_.ProcessEvent_swigregister(ProcessEvent)
wxEVT_END_PROCESS = _misc_.wxEVT_END_PROCESS
EVT_END_PROCESS = wx.PyEventBinder(wxEVT_END_PROCESS, 1)
EXEC_ASYNC = _misc_.EXEC_ASYNC
EXEC_SYNC = _misc_.EXEC_SYNC
EXEC_NOHIDE = _misc_.EXEC_NOHIDE
EXEC_MAKE_GROUP_LEADER = _misc_.EXEC_MAKE_GROUP_LEADER
EXEC_NODISABLE = _misc_.EXEC_NODISABLE

def Execute(*args, **kwargs):
    return _misc_.Execute(*args, **kwargs)


def Kill(*args, **kwargs):
    return _misc_.Kill(*args, **kwargs)


MAILCAP_STANDARD = _misc_.MAILCAP_STANDARD
MAILCAP_NETSCAPE = _misc_.MAILCAP_NETSCAPE
MAILCAP_KDE = _misc_.MAILCAP_KDE
MAILCAP_GNOME = _misc_.MAILCAP_GNOME
MAILCAP_ALL = _misc_.MAILCAP_ALL

class FileTypeInfo(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.FileTypeInfo_swiginit(self, _misc_.new_FileTypeInfo(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_FileTypeInfo
    __del__ = lambda self: None

    def IsValid(*args, **kwargs):
        return _misc_.FileTypeInfo_IsValid(*args, **kwargs)

    def SetIcon(*args, **kwargs):
        return _misc_.FileTypeInfo_SetIcon(*args, **kwargs)

    def SetShortDesc(*args, **kwargs):
        return _misc_.FileTypeInfo_SetShortDesc(*args, **kwargs)

    def GetMimeType(*args, **kwargs):
        return _misc_.FileTypeInfo_GetMimeType(*args, **kwargs)

    def GetOpenCommand(*args, **kwargs):
        return _misc_.FileTypeInfo_GetOpenCommand(*args, **kwargs)

    def GetPrintCommand(*args, **kwargs):
        return _misc_.FileTypeInfo_GetPrintCommand(*args, **kwargs)

    def GetShortDesc(*args, **kwargs):
        return _misc_.FileTypeInfo_GetShortDesc(*args, **kwargs)

    def GetDescription(*args, **kwargs):
        return _misc_.FileTypeInfo_GetDescription(*args, **kwargs)

    def GetExtensions(*args, **kwargs):
        return _misc_.FileTypeInfo_GetExtensions(*args, **kwargs)

    def GetExtensionsCount(*args, **kwargs):
        return _misc_.FileTypeInfo_GetExtensionsCount(*args, **kwargs)

    def GetIconFile(*args, **kwargs):
        return _misc_.FileTypeInfo_GetIconFile(*args, **kwargs)

    def GetIconIndex(*args, **kwargs):
        return _misc_.FileTypeInfo_GetIconIndex(*args, **kwargs)

    Description = property(GetDescription, doc='See `GetDescription`')
    Extensions = property(GetExtensions, doc='See `GetExtensions`')
    ExtensionsCount = property(GetExtensionsCount, doc='See `GetExtensionsCount`')
    IconFile = property(GetIconFile, doc='See `GetIconFile`')
    IconIndex = property(GetIconIndex, doc='See `GetIconIndex`')
    MimeType = property(GetMimeType, doc='See `GetMimeType`')
    OpenCommand = property(GetOpenCommand, doc='See `GetOpenCommand`')
    PrintCommand = property(GetPrintCommand, doc='See `GetPrintCommand`')
    ShortDesc = property(GetShortDesc, SetShortDesc, doc='See `GetShortDesc` and `SetShortDesc`')


_misc_.FileTypeInfo_swigregister(FileTypeInfo)

def FileTypeInfoSequence(*args, **kwargs):
    val = _misc_.new_FileTypeInfoSequence(*args, **kwargs)
    return val


def NullFileTypeInfo(*args, **kwargs):
    val = _misc_.new_NullFileTypeInfo(*args, **kwargs)
    return val


class FileType(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.FileType_swiginit(self, _misc_.new_FileType(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_FileType
    __del__ = lambda self: None

    def GetMimeType(*args, **kwargs):
        return _misc_.FileType_GetMimeType(*args, **kwargs)

    def GetMimeTypes(*args, **kwargs):
        return _misc_.FileType_GetMimeTypes(*args, **kwargs)

    def GetExtensions(*args, **kwargs):
        return _misc_.FileType_GetExtensions(*args, **kwargs)

    def GetIcon(*args, **kwargs):
        return _misc_.FileType_GetIcon(*args, **kwargs)

    def GetIconInfo(*args, **kwargs):
        return _misc_.FileType_GetIconInfo(*args, **kwargs)

    def GetDescription(*args, **kwargs):
        return _misc_.FileType_GetDescription(*args, **kwargs)

    def GetOpenCommand(*args, **kwargs):
        return _misc_.FileType_GetOpenCommand(*args, **kwargs)

    def GetPrintCommand(*args, **kwargs):
        return _misc_.FileType_GetPrintCommand(*args, **kwargs)

    def GetAllCommands(*args, **kwargs):
        return _misc_.FileType_GetAllCommands(*args, **kwargs)

    def SetCommand(*args, **kwargs):
        return _misc_.FileType_SetCommand(*args, **kwargs)

    def SetDefaultIcon(*args, **kwargs):
        return _misc_.FileType_SetDefaultIcon(*args, **kwargs)

    def Unassociate(*args, **kwargs):
        return _misc_.FileType_Unassociate(*args, **kwargs)

    def ExpandCommand(*args, **kwargs):
        return _misc_.FileType_ExpandCommand(*args, **kwargs)

    ExpandCommand = staticmethod(ExpandCommand)
    AllCommands = property(GetAllCommands, doc='See `GetAllCommands`')
    Description = property(GetDescription, doc='See `GetDescription`')
    Extensions = property(GetExtensions, doc='See `GetExtensions`')
    Icon = property(GetIcon, doc='See `GetIcon`')
    IconInfo = property(GetIconInfo, doc='See `GetIconInfo`')
    MimeType = property(GetMimeType, doc='See `GetMimeType`')
    MimeTypes = property(GetMimeTypes, doc='See `GetMimeTypes`')
    OpenCommand = property(GetOpenCommand, doc='See `GetOpenCommand`')
    PrintCommand = property(GetPrintCommand, doc='See `GetPrintCommand`')


_misc_.FileType_swigregister(FileType)

def FileType_ExpandCommand(*args, **kwargs):
    return _misc_.FileType_ExpandCommand(*args, **kwargs)


class MimeTypesManager(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def IsOfType(*args, **kwargs):
        return _misc_.MimeTypesManager_IsOfType(*args, **kwargs)

    IsOfType = staticmethod(IsOfType)

    def __init__(self, *args, **kwargs):
        _misc_.MimeTypesManager_swiginit(self, _misc_.new_MimeTypesManager(*args, **kwargs))

    def Initialize(*args, **kwargs):
        return _misc_.MimeTypesManager_Initialize(*args, **kwargs)

    def ClearData(*args, **kwargs):
        return _misc_.MimeTypesManager_ClearData(*args, **kwargs)

    def GetFileTypeFromExtension(*args, **kwargs):
        return _misc_.MimeTypesManager_GetFileTypeFromExtension(*args, **kwargs)

    def GetFileTypeFromMimeType(*args, **kwargs):
        return _misc_.MimeTypesManager_GetFileTypeFromMimeType(*args, **kwargs)

    def ReadMailcap(*args, **kwargs):
        return _misc_.MimeTypesManager_ReadMailcap(*args, **kwargs)

    def ReadMimeTypes(*args, **kwargs):
        return _misc_.MimeTypesManager_ReadMimeTypes(*args, **kwargs)

    def EnumAllFileTypes(*args, **kwargs):
        return _misc_.MimeTypesManager_EnumAllFileTypes(*args, **kwargs)

    def AddFallback(*args, **kwargs):
        return _misc_.MimeTypesManager_AddFallback(*args, **kwargs)

    def Associate(*args, **kwargs):
        return _misc_.MimeTypesManager_Associate(*args, **kwargs)

    def Unassociate(*args, **kwargs):
        return _misc_.MimeTypesManager_Unassociate(*args, **kwargs)

    __swig_destroy__ = _misc_.delete_MimeTypesManager
    __del__ = lambda self: None


_misc_.MimeTypesManager_swigregister(MimeTypesManager)
TheMimeTypesManager = cvar.TheMimeTypesManager

def MimeTypesManager_IsOfType(*args, **kwargs):
    return _misc_.MimeTypesManager_IsOfType(*args, **kwargs)


class ArtProvider(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.ArtProvider_swiginit(self, _misc_.new_ArtProvider(*args, **kwargs))
        ArtProvider._setCallbackInfo(self, self, ArtProvider)

    __swig_destroy__ = _misc_.delete_ArtProvider
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.ArtProvider__setCallbackInfo(*args, **kwargs)

    def Push(*args, **kwargs):
        return _misc_.ArtProvider_Push(*args, **kwargs)

    Push = staticmethod(Push)
    PushProvider = Push

    def Insert(*args, **kwargs):
        return _misc_.ArtProvider_Insert(*args, **kwargs)

    Insert = staticmethod(Insert)
    InsertProvider = Insert

    def Pop(*args, **kwargs):
        return _misc_.ArtProvider_Pop(*args, **kwargs)

    Pop = staticmethod(Pop)
    PopProvider = Pop

    def Delete(*args, **kwargs):
        val = _misc_.ArtProvider_Delete(*args, **kwargs)
        args[1].thisown = 1
        return val

    Delete = staticmethod(Delete)
    RemoveProvider = Delete

    def GetBitmap(*args, **kwargs):
        return _misc_.ArtProvider_GetBitmap(*args, **kwargs)

    GetBitmap = staticmethod(GetBitmap)

    def GetIcon(*args, **kwargs):
        return _misc_.ArtProvider_GetIcon(*args, **kwargs)

    GetIcon = staticmethod(GetIcon)

    def GetSizeHint(*args, **kwargs):
        return _misc_.ArtProvider_GetSizeHint(*args, **kwargs)

    GetSizeHint = staticmethod(GetSizeHint)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _misc_.ArtProvider_Destroy(*args, **kwargs)


_misc_.ArtProvider_swigregister(ArtProvider)
ART_TOOLBAR = cvar.ART_TOOLBAR
ART_MENU = cvar.ART_MENU
ART_FRAME_ICON = cvar.ART_FRAME_ICON
ART_CMN_DIALOG = cvar.ART_CMN_DIALOG
ART_HELP_BROWSER = cvar.ART_HELP_BROWSER
ART_MESSAGE_BOX = cvar.ART_MESSAGE_BOX
ART_BUTTON = cvar.ART_BUTTON
ART_OTHER = cvar.ART_OTHER
ART_ADD_BOOKMARK = cvar.ART_ADD_BOOKMARK
ART_DEL_BOOKMARK = cvar.ART_DEL_BOOKMARK
ART_HELP_SIDE_PANEL = cvar.ART_HELP_SIDE_PANEL
ART_HELP_SETTINGS = cvar.ART_HELP_SETTINGS
ART_HELP_BOOK = cvar.ART_HELP_BOOK
ART_HELP_FOLDER = cvar.ART_HELP_FOLDER
ART_HELP_PAGE = cvar.ART_HELP_PAGE
ART_GO_BACK = cvar.ART_GO_BACK
ART_GO_FORWARD = cvar.ART_GO_FORWARD
ART_GO_UP = cvar.ART_GO_UP
ART_GO_DOWN = cvar.ART_GO_DOWN
ART_GO_TO_PARENT = cvar.ART_GO_TO_PARENT
ART_GO_HOME = cvar.ART_GO_HOME
ART_FILE_OPEN = cvar.ART_FILE_OPEN
ART_FILE_SAVE = cvar.ART_FILE_SAVE
ART_FILE_SAVE_AS = cvar.ART_FILE_SAVE_AS
ART_PRINT = cvar.ART_PRINT
ART_HELP = cvar.ART_HELP
ART_TIP = cvar.ART_TIP
ART_REPORT_VIEW = cvar.ART_REPORT_VIEW
ART_LIST_VIEW = cvar.ART_LIST_VIEW
ART_NEW_DIR = cvar.ART_NEW_DIR
ART_HARDDISK = cvar.ART_HARDDISK
ART_FLOPPY = cvar.ART_FLOPPY
ART_CDROM = cvar.ART_CDROM
ART_REMOVABLE = cvar.ART_REMOVABLE
ART_FOLDER = cvar.ART_FOLDER
ART_FOLDER_OPEN = cvar.ART_FOLDER_OPEN
ART_GO_DIR_UP = cvar.ART_GO_DIR_UP
ART_EXECUTABLE_FILE = cvar.ART_EXECUTABLE_FILE
ART_NORMAL_FILE = cvar.ART_NORMAL_FILE
ART_TICK_MARK = cvar.ART_TICK_MARK
ART_CROSS_MARK = cvar.ART_CROSS_MARK
ART_ERROR = cvar.ART_ERROR
ART_QUESTION = cvar.ART_QUESTION
ART_WARNING = cvar.ART_WARNING
ART_INFORMATION = cvar.ART_INFORMATION
ART_MISSING_IMAGE = cvar.ART_MISSING_IMAGE
ART_COPY = cvar.ART_COPY
ART_CUT = cvar.ART_CUT
ART_PASTE = cvar.ART_PASTE
ART_DELETE = cvar.ART_DELETE
ART_NEW = cvar.ART_NEW
ART_UNDO = cvar.ART_UNDO
ART_REDO = cvar.ART_REDO
ART_QUIT = cvar.ART_QUIT
ART_FIND = cvar.ART_FIND
ART_FIND_AND_REPLACE = cvar.ART_FIND_AND_REPLACE

def ArtProvider_Push(*args, **kwargs):
    return _misc_.ArtProvider_Push(*args, **kwargs)


def ArtProvider_Insert(*args, **kwargs):
    return _misc_.ArtProvider_Insert(*args, **kwargs)


def ArtProvider_Pop(*args):
    return _misc_.ArtProvider_Pop(*args)


def ArtProvider_Delete(*args, **kwargs):
    val = _misc_.ArtProvider_Delete(*args, **kwargs)
    args[1].thisown = 1
    return val


def ArtProvider_GetBitmap(*args, **kwargs):
    return _misc_.ArtProvider_GetBitmap(*args, **kwargs)


def ArtProvider_GetIcon(*args, **kwargs):
    return _misc_.ArtProvider_GetIcon(*args, **kwargs)


def ArtProvider_GetSizeHint(*args, **kwargs):
    return _misc_.ArtProvider_GetSizeHint(*args, **kwargs)


CONFIG_USE_LOCAL_FILE = _misc_.CONFIG_USE_LOCAL_FILE
CONFIG_USE_GLOBAL_FILE = _misc_.CONFIG_USE_GLOBAL_FILE
CONFIG_USE_RELATIVE_PATH = _misc_.CONFIG_USE_RELATIVE_PATH
CONFIG_USE_NO_ESCAPE_CHARACTERS = _misc_.CONFIG_USE_NO_ESCAPE_CHARACTERS

class ConfigBase(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _misc_.delete_ConfigBase
    __del__ = lambda self: None
    Type_Unknown = _misc_.ConfigBase_Type_Unknown
    Type_String = _misc_.ConfigBase_Type_String
    Type_Boolean = _misc_.ConfigBase_Type_Boolean
    Type_Integer = _misc_.ConfigBase_Type_Integer
    Type_Float = _misc_.ConfigBase_Type_Float

    def Set(*args, **kwargs):
        return _misc_.ConfigBase_Set(*args, **kwargs)

    Set = staticmethod(Set)

    def Get(*args, **kwargs):
        return _misc_.ConfigBase_Get(*args, **kwargs)

    Get = staticmethod(Get)

    def Create(*args, **kwargs):
        return _misc_.ConfigBase_Create(*args, **kwargs)

    Create = staticmethod(Create)

    def DontCreateOnDemand(*args, **kwargs):
        return _misc_.ConfigBase_DontCreateOnDemand(*args, **kwargs)

    DontCreateOnDemand = staticmethod(DontCreateOnDemand)

    def SetPath(*args, **kwargs):
        return _misc_.ConfigBase_SetPath(*args, **kwargs)

    def GetPath(*args, **kwargs):
        return _misc_.ConfigBase_GetPath(*args, **kwargs)

    def GetFirstGroup(*args, **kwargs):
        return _misc_.ConfigBase_GetFirstGroup(*args, **kwargs)

    def GetNextGroup(*args, **kwargs):
        return _misc_.ConfigBase_GetNextGroup(*args, **kwargs)

    def GetFirstEntry(*args, **kwargs):
        return _misc_.ConfigBase_GetFirstEntry(*args, **kwargs)

    def GetNextEntry(*args, **kwargs):
        return _misc_.ConfigBase_GetNextEntry(*args, **kwargs)

    def GetNumberOfEntries(*args, **kwargs):
        return _misc_.ConfigBase_GetNumberOfEntries(*args, **kwargs)

    def GetNumberOfGroups(*args, **kwargs):
        return _misc_.ConfigBase_GetNumberOfGroups(*args, **kwargs)

    def HasGroup(*args, **kwargs):
        return _misc_.ConfigBase_HasGroup(*args, **kwargs)

    def HasEntry(*args, **kwargs):
        return _misc_.ConfigBase_HasEntry(*args, **kwargs)

    def Exists(*args, **kwargs):
        return _misc_.ConfigBase_Exists(*args, **kwargs)

    def GetEntryType(*args, **kwargs):
        return _misc_.ConfigBase_GetEntryType(*args, **kwargs)

    def Read(*args, **kwargs):
        return _misc_.ConfigBase_Read(*args, **kwargs)

    def ReadInt(*args, **kwargs):
        return _misc_.ConfigBase_ReadInt(*args, **kwargs)

    def ReadFloat(*args, **kwargs):
        return _misc_.ConfigBase_ReadFloat(*args, **kwargs)

    def ReadBool(*args, **kwargs):
        return _misc_.ConfigBase_ReadBool(*args, **kwargs)

    def Write(*args, **kwargs):
        return _misc_.ConfigBase_Write(*args, **kwargs)

    def WriteInt(*args, **kwargs):
        return _misc_.ConfigBase_WriteInt(*args, **kwargs)

    def WriteFloat(*args, **kwargs):
        return _misc_.ConfigBase_WriteFloat(*args, **kwargs)

    def WriteBool(*args, **kwargs):
        return _misc_.ConfigBase_WriteBool(*args, **kwargs)

    def Flush(*args, **kwargs):
        return _misc_.ConfigBase_Flush(*args, **kwargs)

    def RenameEntry(*args, **kwargs):
        return _misc_.ConfigBase_RenameEntry(*args, **kwargs)

    def RenameGroup(*args, **kwargs):
        return _misc_.ConfigBase_RenameGroup(*args, **kwargs)

    def DeleteEntry(*args, **kwargs):
        return _misc_.ConfigBase_DeleteEntry(*args, **kwargs)

    def DeleteGroup(*args, **kwargs):
        return _misc_.ConfigBase_DeleteGroup(*args, **kwargs)

    def DeleteAll(*args, **kwargs):
        return _misc_.ConfigBase_DeleteAll(*args, **kwargs)

    def SetExpandEnvVars(*args, **kwargs):
        return _misc_.ConfigBase_SetExpandEnvVars(*args, **kwargs)

    def IsExpandingEnvVars(*args, **kwargs):
        return _misc_.ConfigBase_IsExpandingEnvVars(*args, **kwargs)

    def SetRecordDefaults(*args, **kwargs):
        return _misc_.ConfigBase_SetRecordDefaults(*args, **kwargs)

    def IsRecordingDefaults(*args, **kwargs):
        return _misc_.ConfigBase_IsRecordingDefaults(*args, **kwargs)

    def ExpandEnvVars(*args, **kwargs):
        return _misc_.ConfigBase_ExpandEnvVars(*args, **kwargs)

    def GetAppName(*args, **kwargs):
        return _misc_.ConfigBase_GetAppName(*args, **kwargs)

    def GetVendorName(*args, **kwargs):
        return _misc_.ConfigBase_GetVendorName(*args, **kwargs)

    def SetAppName(*args, **kwargs):
        return _misc_.ConfigBase_SetAppName(*args, **kwargs)

    def SetVendorName(*args, **kwargs):
        return _misc_.ConfigBase_SetVendorName(*args, **kwargs)

    def SetStyle(*args, **kwargs):
        return _misc_.ConfigBase_SetStyle(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _misc_.ConfigBase_GetStyle(*args, **kwargs)

    AppName = property(GetAppName, SetAppName, doc='See `GetAppName` and `SetAppName`')
    EntryType = property(GetEntryType, doc='See `GetEntryType`')
    FirstEntry = property(GetFirstEntry, doc='See `GetFirstEntry`')
    FirstGroup = property(GetFirstGroup, doc='See `GetFirstGroup`')
    NextEntry = property(GetNextEntry, doc='See `GetNextEntry`')
    NextGroup = property(GetNextGroup, doc='See `GetNextGroup`')
    NumberOfEntries = property(GetNumberOfEntries, doc='See `GetNumberOfEntries`')
    NumberOfGroups = property(GetNumberOfGroups, doc='See `GetNumberOfGroups`')
    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')
    Style = property(GetStyle, SetStyle, doc='See `GetStyle` and `SetStyle`')
    VendorName = property(GetVendorName, SetVendorName, doc='See `GetVendorName` and `SetVendorName`')


_misc_.ConfigBase_swigregister(ConfigBase)

def ConfigBase_Set(*args, **kwargs):
    return _misc_.ConfigBase_Set(*args, **kwargs)


def ConfigBase_Get(*args, **kwargs):
    return _misc_.ConfigBase_Get(*args, **kwargs)


def ConfigBase_Create(*args):
    return _misc_.ConfigBase_Create(*args)


def ConfigBase_DontCreateOnDemand(*args):
    return _misc_.ConfigBase_DontCreateOnDemand(*args)


class Config(ConfigBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.Config_swiginit(self, _misc_.new_Config(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_Config
    __del__ = lambda self: None


_misc_.Config_swigregister(Config)

class FileConfig(ConfigBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.FileConfig_swiginit(self, _misc_.new_FileConfig(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_FileConfig
    __del__ = lambda self: None


_misc_.FileConfig_swigregister(FileConfig)

class ConfigPathChanger(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.ConfigPathChanger_swiginit(self, _misc_.new_ConfigPathChanger(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_ConfigPathChanger
    __del__ = lambda self: None

    def Name(*args, **kwargs):
        return _misc_.ConfigPathChanger_Name(*args, **kwargs)


_misc_.ConfigPathChanger_swigregister(ConfigPathChanger)

def ExpandEnvVars(*args, **kwargs):
    return _misc_.ExpandEnvVars(*args, **kwargs)


class DateTime(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    Local = _misc_.DateTime_Local
    GMT_12 = _misc_.DateTime_GMT_12
    GMT_11 = _misc_.DateTime_GMT_11
    GMT_10 = _misc_.DateTime_GMT_10
    GMT_9 = _misc_.DateTime_GMT_9
    GMT_8 = _misc_.DateTime_GMT_8
    GMT_7 = _misc_.DateTime_GMT_7
    GMT_6 = _misc_.DateTime_GMT_6
    GMT_5 = _misc_.DateTime_GMT_5
    GMT_4 = _misc_.DateTime_GMT_4
    GMT_3 = _misc_.DateTime_GMT_3
    GMT_2 = _misc_.DateTime_GMT_2
    GMT_1 = _misc_.DateTime_GMT_1
    GMT0 = _misc_.DateTime_GMT0
    GMT1 = _misc_.DateTime_GMT1
    GMT2 = _misc_.DateTime_GMT2
    GMT3 = _misc_.DateTime_GMT3
    GMT4 = _misc_.DateTime_GMT4
    GMT5 = _misc_.DateTime_GMT5
    GMT6 = _misc_.DateTime_GMT6
    GMT7 = _misc_.DateTime_GMT7
    GMT8 = _misc_.DateTime_GMT8
    GMT9 = _misc_.DateTime_GMT9
    GMT10 = _misc_.DateTime_GMT10
    GMT11 = _misc_.DateTime_GMT11
    GMT12 = _misc_.DateTime_GMT12
    GMT13 = _misc_.DateTime_GMT13
    WET = _misc_.DateTime_WET
    WEST = _misc_.DateTime_WEST
    CET = _misc_.DateTime_CET
    CEST = _misc_.DateTime_CEST
    EET = _misc_.DateTime_EET
    EEST = _misc_.DateTime_EEST
    MSK = _misc_.DateTime_MSK
    MSD = _misc_.DateTime_MSD
    AST = _misc_.DateTime_AST
    ADT = _misc_.DateTime_ADT
    EST = _misc_.DateTime_EST
    EDT = _misc_.DateTime_EDT
    CST = _misc_.DateTime_CST
    CDT = _misc_.DateTime_CDT
    MST = _misc_.DateTime_MST
    MDT = _misc_.DateTime_MDT
    PST = _misc_.DateTime_PST
    PDT = _misc_.DateTime_PDT
    HST = _misc_.DateTime_HST
    AKST = _misc_.DateTime_AKST
    AKDT = _misc_.DateTime_AKDT
    A_WST = _misc_.DateTime_A_WST
    A_CST = _misc_.DateTime_A_CST
    A_EST = _misc_.DateTime_A_EST
    A_ESST = _misc_.DateTime_A_ESST
    NZST = _misc_.DateTime_NZST
    NZDT = _misc_.DateTime_NZDT
    UTC = _misc_.DateTime_UTC
    Gregorian = _misc_.DateTime_Gregorian
    Julian = _misc_.DateTime_Julian
    Gr_Unknown = _misc_.DateTime_Gr_Unknown
    Gr_Standard = _misc_.DateTime_Gr_Standard
    Gr_Alaska = _misc_.DateTime_Gr_Alaska
    Gr_Albania = _misc_.DateTime_Gr_Albania
    Gr_Austria = _misc_.DateTime_Gr_Austria
    Gr_Austria_Brixen = _misc_.DateTime_Gr_Austria_Brixen
    Gr_Austria_Salzburg = _misc_.DateTime_Gr_Austria_Salzburg
    Gr_Austria_Tyrol = _misc_.DateTime_Gr_Austria_Tyrol
    Gr_Austria_Carinthia = _misc_.DateTime_Gr_Austria_Carinthia
    Gr_Austria_Styria = _misc_.DateTime_Gr_Austria_Styria
    Gr_Belgium = _misc_.DateTime_Gr_Belgium
    Gr_Bulgaria = _misc_.DateTime_Gr_Bulgaria
    Gr_Bulgaria_1 = _misc_.DateTime_Gr_Bulgaria_1
    Gr_Bulgaria_2 = _misc_.DateTime_Gr_Bulgaria_2
    Gr_Bulgaria_3 = _misc_.DateTime_Gr_Bulgaria_3
    Gr_Canada = _misc_.DateTime_Gr_Canada
    Gr_China = _misc_.DateTime_Gr_China
    Gr_China_1 = _misc_.DateTime_Gr_China_1
    Gr_China_2 = _misc_.DateTime_Gr_China_2
    Gr_Czechoslovakia = _misc_.DateTime_Gr_Czechoslovakia
    Gr_Denmark = _misc_.DateTime_Gr_Denmark
    Gr_Egypt = _misc_.DateTime_Gr_Egypt
    Gr_Estonia = _misc_.DateTime_Gr_Estonia
    Gr_Finland = _misc_.DateTime_Gr_Finland
    Gr_France = _misc_.DateTime_Gr_France
    Gr_France_Alsace = _misc_.DateTime_Gr_France_Alsace
    Gr_France_Lorraine = _misc_.DateTime_Gr_France_Lorraine
    Gr_France_Strasbourg = _misc_.DateTime_Gr_France_Strasbourg
    Gr_Germany = _misc_.DateTime_Gr_Germany
    Gr_Germany_Catholic = _misc_.DateTime_Gr_Germany_Catholic
    Gr_Germany_Prussia = _misc_.DateTime_Gr_Germany_Prussia
    Gr_Germany_Protestant = _misc_.DateTime_Gr_Germany_Protestant
    Gr_GreatBritain = _misc_.DateTime_Gr_GreatBritain
    Gr_Greece = _misc_.DateTime_Gr_Greece
    Gr_Hungary = _misc_.DateTime_Gr_Hungary
    Gr_Ireland = _misc_.DateTime_Gr_Ireland
    Gr_Italy = _misc_.DateTime_Gr_Italy
    Gr_Japan = _misc_.DateTime_Gr_Japan
    Gr_Japan_1 = _misc_.DateTime_Gr_Japan_1
    Gr_Japan_2 = _misc_.DateTime_Gr_Japan_2
    Gr_Japan_3 = _misc_.DateTime_Gr_Japan_3
    Gr_Latvia = _misc_.DateTime_Gr_Latvia
    Gr_Lithuania = _misc_.DateTime_Gr_Lithuania
    Gr_Luxemburg = _misc_.DateTime_Gr_Luxemburg
    Gr_Netherlands = _misc_.DateTime_Gr_Netherlands
    Gr_Netherlands_Groningen = _misc_.DateTime_Gr_Netherlands_Groningen
    Gr_Netherlands_Gelderland = _misc_.DateTime_Gr_Netherlands_Gelderland
    Gr_Netherlands_Utrecht = _misc_.DateTime_Gr_Netherlands_Utrecht
    Gr_Netherlands_Friesland = _misc_.DateTime_Gr_Netherlands_Friesland
    Gr_Norway = _misc_.DateTime_Gr_Norway
    Gr_Poland = _misc_.DateTime_Gr_Poland
    Gr_Portugal = _misc_.DateTime_Gr_Portugal
    Gr_Romania = _misc_.DateTime_Gr_Romania
    Gr_Russia = _misc_.DateTime_Gr_Russia
    Gr_Scotland = _misc_.DateTime_Gr_Scotland
    Gr_Spain = _misc_.DateTime_Gr_Spain
    Gr_Sweden = _misc_.DateTime_Gr_Sweden
    Gr_Switzerland = _misc_.DateTime_Gr_Switzerland
    Gr_Switzerland_Catholic = _misc_.DateTime_Gr_Switzerland_Catholic
    Gr_Switzerland_Protestant = _misc_.DateTime_Gr_Switzerland_Protestant
    Gr_Turkey = _misc_.DateTime_Gr_Turkey
    Gr_USA = _misc_.DateTime_Gr_USA
    Gr_Wales = _misc_.DateTime_Gr_Wales
    Gr_Yugoslavia = _misc_.DateTime_Gr_Yugoslavia
    Country_Unknown = _misc_.DateTime_Country_Unknown
    Country_Default = _misc_.DateTime_Country_Default
    Country_WesternEurope_Start = _misc_.DateTime_Country_WesternEurope_Start
    Country_EEC = _misc_.DateTime_Country_EEC
    France = _misc_.DateTime_France
    Germany = _misc_.DateTime_Germany
    UK = _misc_.DateTime_UK
    Country_WesternEurope_End = _misc_.DateTime_Country_WesternEurope_End
    Russia = _misc_.DateTime_Russia
    USA = _misc_.DateTime_USA
    Jan = _misc_.DateTime_Jan
    Feb = _misc_.DateTime_Feb
    Mar = _misc_.DateTime_Mar
    Apr = _misc_.DateTime_Apr
    May = _misc_.DateTime_May
    Jun = _misc_.DateTime_Jun
    Jul = _misc_.DateTime_Jul
    Aug = _misc_.DateTime_Aug
    Sep = _misc_.DateTime_Sep
    Oct = _misc_.DateTime_Oct
    Nov = _misc_.DateTime_Nov
    Dec = _misc_.DateTime_Dec
    Inv_Month = _misc_.DateTime_Inv_Month
    Sun = _misc_.DateTime_Sun
    Mon = _misc_.DateTime_Mon
    Tue = _misc_.DateTime_Tue
    Wed = _misc_.DateTime_Wed
    Thu = _misc_.DateTime_Thu
    Fri = _misc_.DateTime_Fri
    Sat = _misc_.DateTime_Sat
    Inv_WeekDay = _misc_.DateTime_Inv_WeekDay
    Inv_Year = _misc_.DateTime_Inv_Year
    Name_Full = _misc_.DateTime_Name_Full
    Name_Abbr = _misc_.DateTime_Name_Abbr
    Default_First = _misc_.DateTime_Default_First
    Monday_First = _misc_.DateTime_Monday_First
    Sunday_First = _misc_.DateTime_Sunday_First

    def SetCountry(*args, **kwargs):
        return _misc_.DateTime_SetCountry(*args, **kwargs)

    SetCountry = staticmethod(SetCountry)

    def GetCountry(*args, **kwargs):
        return _misc_.DateTime_GetCountry(*args, **kwargs)

    GetCountry = staticmethod(GetCountry)

    def IsWestEuropeanCountry(*args, **kwargs):
        return _misc_.DateTime_IsWestEuropeanCountry(*args, **kwargs)

    IsWestEuropeanCountry = staticmethod(IsWestEuropeanCountry)

    def GetCurrentYear(*args, **kwargs):
        return _misc_.DateTime_GetCurrentYear(*args, **kwargs)

    GetCurrentYear = staticmethod(GetCurrentYear)

    def ConvertYearToBC(*args, **kwargs):
        return _misc_.DateTime_ConvertYearToBC(*args, **kwargs)

    ConvertYearToBC = staticmethod(ConvertYearToBC)

    def GetCurrentMonth(*args, **kwargs):
        return _misc_.DateTime_GetCurrentMonth(*args, **kwargs)

    GetCurrentMonth = staticmethod(GetCurrentMonth)

    def IsLeapYear(*args, **kwargs):
        return _misc_.DateTime_IsLeapYear(*args, **kwargs)

    IsLeapYear = staticmethod(IsLeapYear)

    def GetCentury(*args, **kwargs):
        return _misc_.DateTime_GetCentury(*args, **kwargs)

    GetCentury = staticmethod(GetCentury)

    def GetNumberOfDaysInYear(*args, **kwargs):
        return _misc_.DateTime_GetNumberOfDaysInYear(*args, **kwargs)

    GetNumberOfDaysInYear = staticmethod(GetNumberOfDaysInYear)
    GetNumberOfDaysinYear = GetNumberOfDaysInYear

    def GetNumberOfDaysInMonth(*args, **kwargs):
        return _misc_.DateTime_GetNumberOfDaysInMonth(*args, **kwargs)

    GetNumberOfDaysInMonth = staticmethod(GetNumberOfDaysInMonth)

    def GetMonthName(*args, **kwargs):
        return _misc_.DateTime_GetMonthName(*args, **kwargs)

    GetMonthName = staticmethod(GetMonthName)

    def GetWeekDayName(*args, **kwargs):
        return _misc_.DateTime_GetWeekDayName(*args, **kwargs)

    GetWeekDayName = staticmethod(GetWeekDayName)

    def GetAmPmStrings(*args, **kwargs):
        return _misc_.DateTime_GetAmPmStrings(*args, **kwargs)

    GetAmPmStrings = staticmethod(GetAmPmStrings)

    def IsDSTApplicable(*args, **kwargs):
        return _misc_.DateTime_IsDSTApplicable(*args, **kwargs)

    IsDSTApplicable = staticmethod(IsDSTApplicable)

    def GetBeginDST(*args, **kwargs):
        return _misc_.DateTime_GetBeginDST(*args, **kwargs)

    GetBeginDST = staticmethod(GetBeginDST)

    def GetEndDST(*args, **kwargs):
        return _misc_.DateTime_GetEndDST(*args, **kwargs)

    GetEndDST = staticmethod(GetEndDST)

    def Now(*args, **kwargs):
        return _misc_.DateTime_Now(*args, **kwargs)

    Now = staticmethod(Now)

    def UNow(*args, **kwargs):
        return _misc_.DateTime_UNow(*args, **kwargs)

    UNow = staticmethod(UNow)

    def Today(*args, **kwargs):
        return _misc_.DateTime_Today(*args, **kwargs)

    Today = staticmethod(Today)

    def __init__(self, *args, **kwargs):
        _misc_.DateTime_swiginit(self, _misc_.new_DateTime(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_DateTime
    __del__ = lambda self: None

    def SetToCurrent(*args, **kwargs):
        return _misc_.DateTime_SetToCurrent(*args, **kwargs)

    def SetTimeT(*args, **kwargs):
        return _misc_.DateTime_SetTimeT(*args, **kwargs)

    def SetJDN(*args, **kwargs):
        return _misc_.DateTime_SetJDN(*args, **kwargs)

    def SetHMS(*args, **kwargs):
        return _misc_.DateTime_SetHMS(*args, **kwargs)

    def Set(*args, **kwargs):
        return _misc_.DateTime_Set(*args, **kwargs)

    def ResetTime(*args, **kwargs):
        return _misc_.DateTime_ResetTime(*args, **kwargs)

    def GetDateOnly(*args, **kwargs):
        return _misc_.DateTime_GetDateOnly(*args, **kwargs)

    def SetYear(*args, **kwargs):
        return _misc_.DateTime_SetYear(*args, **kwargs)

    def SetMonth(*args, **kwargs):
        return _misc_.DateTime_SetMonth(*args, **kwargs)

    def SetDay(*args, **kwargs):
        return _misc_.DateTime_SetDay(*args, **kwargs)

    def SetHour(*args, **kwargs):
        return _misc_.DateTime_SetHour(*args, **kwargs)

    def SetMinute(*args, **kwargs):
        return _misc_.DateTime_SetMinute(*args, **kwargs)

    def SetSecond(*args, **kwargs):
        return _misc_.DateTime_SetSecond(*args, **kwargs)

    def SetMillisecond(*args, **kwargs):
        return _misc_.DateTime_SetMillisecond(*args, **kwargs)

    def SetToWeekDayInSameWeek(*args, **kwargs):
        return _misc_.DateTime_SetToWeekDayInSameWeek(*args, **kwargs)

    def GetWeekDayInSameWeek(*args, **kwargs):
        return _misc_.DateTime_GetWeekDayInSameWeek(*args, **kwargs)

    def SetToNextWeekDay(*args, **kwargs):
        return _misc_.DateTime_SetToNextWeekDay(*args, **kwargs)

    def GetNextWeekDay(*args, **kwargs):
        return _misc_.DateTime_GetNextWeekDay(*args, **kwargs)

    def SetToPrevWeekDay(*args, **kwargs):
        return _misc_.DateTime_SetToPrevWeekDay(*args, **kwargs)

    def GetPrevWeekDay(*args, **kwargs):
        return _misc_.DateTime_GetPrevWeekDay(*args, **kwargs)

    def SetToWeekDay(*args, **kwargs):
        return _misc_.DateTime_SetToWeekDay(*args, **kwargs)

    def SetToLastWeekDay(*args, **kwargs):
        return _misc_.DateTime_SetToLastWeekDay(*args, **kwargs)

    def GetLastWeekDay(*args, **kwargs):
        return _misc_.DateTime_GetLastWeekDay(*args, **kwargs)

    def SetToTheWeek(*args, **kwargs):
        return _misc_.DateTime_SetToTheWeek(*args, **kwargs)

    def GetWeek(*args, **kwargs):
        return _misc_.DateTime_GetWeek(*args, **kwargs)

    SetToTheWeek = wx._deprecated(SetToTheWeek, 'SetToTheWeek is deprecated, use (static) SetToWeekOfYear instead')
    GetWeek = wx._deprecated(GetWeek, 'GetWeek is deprecated, use GetWeekOfYear instead')

    def SetToWeekOfYear(*args, **kwargs):
        return _misc_.DateTime_SetToWeekOfYear(*args, **kwargs)

    SetToWeekOfYear = staticmethod(SetToWeekOfYear)

    def SetToLastMonthDay(*args, **kwargs):
        return _misc_.DateTime_SetToLastMonthDay(*args, **kwargs)

    def GetLastMonthDay(*args, **kwargs):
        return _misc_.DateTime_GetLastMonthDay(*args, **kwargs)

    def SetToYearDay(*args, **kwargs):
        return _misc_.DateTime_SetToYearDay(*args, **kwargs)

    def GetYearDay(*args, **kwargs):
        return _misc_.DateTime_GetYearDay(*args, **kwargs)

    def GetJulianDayNumber(*args, **kwargs):
        return _misc_.DateTime_GetJulianDayNumber(*args, **kwargs)

    def GetJDN(*args, **kwargs):
        return _misc_.DateTime_GetJDN(*args, **kwargs)

    def GetModifiedJulianDayNumber(*args, **kwargs):
        return _misc_.DateTime_GetModifiedJulianDayNumber(*args, **kwargs)

    def GetMJD(*args, **kwargs):
        return _misc_.DateTime_GetMJD(*args, **kwargs)

    def GetRataDie(*args, **kwargs):
        return _misc_.DateTime_GetRataDie(*args, **kwargs)

    def ToTimezone(*args, **kwargs):
        return _misc_.DateTime_ToTimezone(*args, **kwargs)

    def MakeTimezone(*args, **kwargs):
        return _misc_.DateTime_MakeTimezone(*args, **kwargs)

    def FromTimezone(*args, **kwargs):
        return _misc_.DateTime_FromTimezone(*args, **kwargs)

    def MakeFromTimezone(*args, **kwargs):
        return _misc_.DateTime_MakeFromTimezone(*args, **kwargs)

    def ToUTC(*args, **kwargs):
        return _misc_.DateTime_ToUTC(*args, **kwargs)

    def MakeUTC(*args, **kwargs):
        return _misc_.DateTime_MakeUTC(*args, **kwargs)

    def ToGMT(*args, **kwargs):
        return _misc_.DateTime_ToGMT(*args, **kwargs)

    def MakeGMT(*args, **kwargs):
        return _misc_.DateTime_MakeGMT(*args, **kwargs)

    def FromUTC(*args, **kwargs):
        return _misc_.DateTime_FromUTC(*args, **kwargs)

    def MakeFromUTC(*args, **kwargs):
        return _misc_.DateTime_MakeFromUTC(*args, **kwargs)

    def IsDST(*args, **kwargs):
        return _misc_.DateTime_IsDST(*args, **kwargs)

    def IsValid(*args, **kwargs):
        return _misc_.DateTime_IsValid(*args, **kwargs)

    IsOk = IsValid
    Ok = IsOk

    def __nonzero__(self):
        return self.IsOk()

    def GetTicks(*args, **kwargs):
        return _misc_.DateTime_GetTicks(*args, **kwargs)

    def GetYear(*args, **kwargs):
        return _misc_.DateTime_GetYear(*args, **kwargs)

    def GetMonth(*args, **kwargs):
        return _misc_.DateTime_GetMonth(*args, **kwargs)

    def GetDay(*args, **kwargs):
        return _misc_.DateTime_GetDay(*args, **kwargs)

    def GetWeekDay(*args, **kwargs):
        return _misc_.DateTime_GetWeekDay(*args, **kwargs)

    def GetHour(*args, **kwargs):
        return _misc_.DateTime_GetHour(*args, **kwargs)

    def GetMinute(*args, **kwargs):
        return _misc_.DateTime_GetMinute(*args, **kwargs)

    def GetSecond(*args, **kwargs):
        return _misc_.DateTime_GetSecond(*args, **kwargs)

    def GetMillisecond(*args, **kwargs):
        return _misc_.DateTime_GetMillisecond(*args, **kwargs)

    def GetDayOfYear(*args, **kwargs):
        return _misc_.DateTime_GetDayOfYear(*args, **kwargs)

    def GetWeekOfYear(*args, **kwargs):
        return _misc_.DateTime_GetWeekOfYear(*args, **kwargs)

    def GetWeekOfMonth(*args, **kwargs):
        return _misc_.DateTime_GetWeekOfMonth(*args, **kwargs)

    def IsWorkDay(*args, **kwargs):
        return _misc_.DateTime_IsWorkDay(*args, **kwargs)

    def IsEqualTo(*args, **kwargs):
        return _misc_.DateTime_IsEqualTo(*args, **kwargs)

    def IsEarlierThan(*args, **kwargs):
        return _misc_.DateTime_IsEarlierThan(*args, **kwargs)

    def IsLaterThan(*args, **kwargs):
        return _misc_.DateTime_IsLaterThan(*args, **kwargs)

    def IsStrictlyBetween(*args, **kwargs):
        return _misc_.DateTime_IsStrictlyBetween(*args, **kwargs)

    def IsBetween(*args, **kwargs):
        return _misc_.DateTime_IsBetween(*args, **kwargs)

    def IsSameDate(*args, **kwargs):
        return _misc_.DateTime_IsSameDate(*args, **kwargs)

    def IsSameTime(*args, **kwargs):
        return _misc_.DateTime_IsSameTime(*args, **kwargs)

    def IsEqualUpTo(*args, **kwargs):
        return _misc_.DateTime_IsEqualUpTo(*args, **kwargs)

    def AddTS(*args, **kwargs):
        return _misc_.DateTime_AddTS(*args, **kwargs)

    def AddDS(*args, **kwargs):
        return _misc_.DateTime_AddDS(*args, **kwargs)

    def SubtractTS(*args, **kwargs):
        return _misc_.DateTime_SubtractTS(*args, **kwargs)

    def SubtractDS(*args, **kwargs):
        return _misc_.DateTime_SubtractDS(*args, **kwargs)

    def Subtract(*args, **kwargs):
        return _misc_.DateTime_Subtract(*args, **kwargs)

    def __iadd__(*args):
        return _misc_.DateTime___iadd__(*args)

    def __isub__(*args):
        return _misc_.DateTime___isub__(*args)

    def __add__(*args):
        return _misc_.DateTime___add__(*args)

    def __sub__(*args):
        return _misc_.DateTime___sub__(*args)

    def __lt__(*args, **kwargs):
        return _misc_.DateTime___lt__(*args, **kwargs)

    def __le__(*args, **kwargs):
        return _misc_.DateTime___le__(*args, **kwargs)

    def __gt__(*args, **kwargs):
        return _misc_.DateTime___gt__(*args, **kwargs)

    def __ge__(*args, **kwargs):
        return _misc_.DateTime___ge__(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _misc_.DateTime___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _misc_.DateTime___ne__(*args, **kwargs)

    def ParseRfc822Date(*args, **kwargs):
        return _misc_.DateTime_ParseRfc822Date(*args, **kwargs)

    def ParseFormat(*args, **kwargs):
        return _misc_.DateTime_ParseFormat(*args, **kwargs)

    def ParseDateTime(*args, **kwargs):
        return _misc_.DateTime_ParseDateTime(*args, **kwargs)

    def ParseDate(*args, **kwargs):
        return _misc_.DateTime_ParseDate(*args, **kwargs)

    def ParseTime(*args, **kwargs):
        return _misc_.DateTime_ParseTime(*args, **kwargs)

    def Format(*args, **kwargs):
        return _misc_.DateTime_Format(*args, **kwargs)

    def FormatDate(*args, **kwargs):
        return _misc_.DateTime_FormatDate(*args, **kwargs)

    def FormatTime(*args, **kwargs):
        return _misc_.DateTime_FormatTime(*args, **kwargs)

    def FormatISODate(*args, **kwargs):
        return _misc_.DateTime_FormatISODate(*args, **kwargs)

    def FormatISOTime(*args, **kwargs):
        return _misc_.DateTime_FormatISOTime(*args, **kwargs)

    def __repr__(self):
        if self.IsValid():
            f = self.Format().encode(wx.GetDefaultPyEncoding())
            return '<wx.DateTime: "%s" at %s>' % (f, self.this)
        else:
            return '<wx.DateTime: "INVALID" at %s>' % self.this

    def __str__(self):
        if self.IsValid():
            return self.Format().encode(wx.GetDefaultPyEncoding())
        else:
            return 'INVALID DateTime'

    Day = property(GetDay, SetDay, doc='See `GetDay` and `SetDay`')
    DayOfYear = property(GetDayOfYear, doc='See `GetDayOfYear`')
    Hour = property(GetHour, SetHour, doc='See `GetHour` and `SetHour`')
    JDN = property(GetJDN, SetJDN, doc='See `GetJDN` and `SetJDN`')
    JulianDayNumber = property(GetJulianDayNumber, doc='See `GetJulianDayNumber`')
    LastMonthDay = property(GetLastMonthDay, doc='See `GetLastMonthDay`')
    LastWeekDay = property(GetLastWeekDay, doc='See `GetLastWeekDay`')
    MJD = property(GetMJD, doc='See `GetMJD`')
    Millisecond = property(GetMillisecond, SetMillisecond, doc='See `GetMillisecond` and `SetMillisecond`')
    Minute = property(GetMinute, SetMinute, doc='See `GetMinute` and `SetMinute`')
    ModifiedJulianDayNumber = property(GetModifiedJulianDayNumber, doc='See `GetModifiedJulianDayNumber`')
    Month = property(GetMonth, SetMonth, doc='See `GetMonth` and `SetMonth`')
    NextWeekDay = property(GetNextWeekDay, doc='See `GetNextWeekDay`')
    PrevWeekDay = property(GetPrevWeekDay, doc='See `GetPrevWeekDay`')
    RataDie = property(GetRataDie, doc='See `GetRataDie`')
    Second = property(GetSecond, SetSecond, doc='See `GetSecond` and `SetSecond`')
    Ticks = property(GetTicks, doc='See `GetTicks`')
    Week = property(GetWeek, doc='See `GetWeek`')
    WeekDay = property(GetWeekDay, doc='See `GetWeekDay`')
    WeekDayInSameWeek = property(GetWeekDayInSameWeek, doc='See `GetWeekDayInSameWeek`')
    WeekOfMonth = property(GetWeekOfMonth, doc='See `GetWeekOfMonth`')
    WeekOfYear = property(GetWeekOfYear, doc='See `GetWeekOfYear`')
    Year = property(GetYear, SetYear, doc='See `GetYear` and `SetYear`')
    YearDay = property(GetYearDay, doc='See `GetYearDay`')


_misc_.DateTime_swigregister(DateTime)
DefaultDateTimeFormat = cvar.DefaultDateTimeFormat
DefaultTimeSpanFormat = cvar.DefaultTimeSpanFormat

def DateTime_SetCountry(*args, **kwargs):
    return _misc_.DateTime_SetCountry(*args, **kwargs)


def DateTime_GetCountry(*args):
    return _misc_.DateTime_GetCountry(*args)


def DateTime_IsWestEuropeanCountry(*args, **kwargs):
    return _misc_.DateTime_IsWestEuropeanCountry(*args, **kwargs)


def DateTime_GetCurrentYear(*args, **kwargs):
    return _misc_.DateTime_GetCurrentYear(*args, **kwargs)


def DateTime_ConvertYearToBC(*args, **kwargs):
    return _misc_.DateTime_ConvertYearToBC(*args, **kwargs)


def DateTime_GetCurrentMonth(*args, **kwargs):
    return _misc_.DateTime_GetCurrentMonth(*args, **kwargs)


def DateTime_IsLeapYear(*args, **kwargs):
    return _misc_.DateTime_IsLeapYear(*args, **kwargs)


def DateTime_GetCentury(*args, **kwargs):
    return _misc_.DateTime_GetCentury(*args, **kwargs)


def DateTime_GetNumberOfDaysInYear(*args, **kwargs):
    return _misc_.DateTime_GetNumberOfDaysInYear(*args, **kwargs)


def DateTime_GetNumberOfDaysInMonth(*args, **kwargs):
    return _misc_.DateTime_GetNumberOfDaysInMonth(*args, **kwargs)


def DateTime_GetMonthName(*args, **kwargs):
    return _misc_.DateTime_GetMonthName(*args, **kwargs)


def DateTime_GetWeekDayName(*args, **kwargs):
    return _misc_.DateTime_GetWeekDayName(*args, **kwargs)


def DateTime_GetAmPmStrings(*args):
    return _misc_.DateTime_GetAmPmStrings(*args)


def DateTime_IsDSTApplicable(*args, **kwargs):
    return _misc_.DateTime_IsDSTApplicable(*args, **kwargs)


def DateTime_GetBeginDST(*args, **kwargs):
    return _misc_.DateTime_GetBeginDST(*args, **kwargs)


def DateTime_GetEndDST(*args, **kwargs):
    return _misc_.DateTime_GetEndDST(*args, **kwargs)


def DateTime_Now(*args):
    return _misc_.DateTime_Now(*args)


def DateTime_UNow(*args):
    return _misc_.DateTime_UNow(*args)


def DateTime_Today(*args):
    return _misc_.DateTime_Today(*args)


def DateTimeFromTimeT(*args, **kwargs):
    val = _misc_.new_DateTimeFromTimeT(*args, **kwargs)
    return val


def DateTimeFromJDN(*args, **kwargs):
    val = _misc_.new_DateTimeFromJDN(*args, **kwargs)
    return val


def DateTimeFromHMS(*args, **kwargs):
    val = _misc_.new_DateTimeFromHMS(*args, **kwargs)
    return val


def DateTimeFromDMY(*args, **kwargs):
    val = _misc_.new_DateTimeFromDMY(*args, **kwargs)
    return val


def DateTimeFromDateTime(*args, **kwargs):
    val = _misc_.new_DateTimeFromDateTime(*args, **kwargs)
    return val


def DateTime_SetToWeekOfYear(*args, **kwargs):
    return _misc_.DateTime_SetToWeekOfYear(*args, **kwargs)


class TimeSpan(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def Milliseconds(*args, **kwargs):
        return _misc_.TimeSpan_Milliseconds(*args, **kwargs)

    Milliseconds = staticmethod(Milliseconds)

    def Millisecond(*args, **kwargs):
        return _misc_.TimeSpan_Millisecond(*args, **kwargs)

    Millisecond = staticmethod(Millisecond)

    def Seconds(*args, **kwargs):
        return _misc_.TimeSpan_Seconds(*args, **kwargs)

    Seconds = staticmethod(Seconds)

    def Second(*args, **kwargs):
        return _misc_.TimeSpan_Second(*args, **kwargs)

    Second = staticmethod(Second)

    def Minutes(*args, **kwargs):
        return _misc_.TimeSpan_Minutes(*args, **kwargs)

    Minutes = staticmethod(Minutes)

    def Minute(*args, **kwargs):
        return _misc_.TimeSpan_Minute(*args, **kwargs)

    Minute = staticmethod(Minute)

    def Hours(*args, **kwargs):
        return _misc_.TimeSpan_Hours(*args, **kwargs)

    Hours = staticmethod(Hours)

    def Hour(*args, **kwargs):
        return _misc_.TimeSpan_Hour(*args, **kwargs)

    Hour = staticmethod(Hour)

    def Days(*args, **kwargs):
        return _misc_.TimeSpan_Days(*args, **kwargs)

    Days = staticmethod(Days)

    def Day(*args, **kwargs):
        return _misc_.TimeSpan_Day(*args, **kwargs)

    Day = staticmethod(Day)

    def Weeks(*args, **kwargs):
        return _misc_.TimeSpan_Weeks(*args, **kwargs)

    Weeks = staticmethod(Weeks)

    def Week(*args, **kwargs):
        return _misc_.TimeSpan_Week(*args, **kwargs)

    Week = staticmethod(Week)

    def __init__(self, *args, **kwargs):
        _misc_.TimeSpan_swiginit(self, _misc_.new_TimeSpan(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_TimeSpan
    __del__ = lambda self: None

    def Add(*args, **kwargs):
        return _misc_.TimeSpan_Add(*args, **kwargs)

    def Subtract(*args, **kwargs):
        return _misc_.TimeSpan_Subtract(*args, **kwargs)

    def Multiply(*args, **kwargs):
        return _misc_.TimeSpan_Multiply(*args, **kwargs)

    def Neg(*args, **kwargs):
        return _misc_.TimeSpan_Neg(*args, **kwargs)

    def Abs(*args, **kwargs):
        return _misc_.TimeSpan_Abs(*args, **kwargs)

    def __iadd__(*args, **kwargs):
        return _misc_.TimeSpan___iadd__(*args, **kwargs)

    def __isub__(*args, **kwargs):
        return _misc_.TimeSpan___isub__(*args, **kwargs)

    def __imul__(*args, **kwargs):
        return _misc_.TimeSpan___imul__(*args, **kwargs)

    def __neg__(*args, **kwargs):
        return _misc_.TimeSpan___neg__(*args, **kwargs)

    def __add__(*args, **kwargs):
        return _misc_.TimeSpan___add__(*args, **kwargs)

    def __sub__(*args, **kwargs):
        return _misc_.TimeSpan___sub__(*args, **kwargs)

    def __mul__(*args, **kwargs):
        return _misc_.TimeSpan___mul__(*args, **kwargs)

    def __rmul__(*args, **kwargs):
        return _misc_.TimeSpan___rmul__(*args, **kwargs)

    def __lt__(*args, **kwargs):
        return _misc_.TimeSpan___lt__(*args, **kwargs)

    def __le__(*args, **kwargs):
        return _misc_.TimeSpan___le__(*args, **kwargs)

    def __gt__(*args, **kwargs):
        return _misc_.TimeSpan___gt__(*args, **kwargs)

    def __ge__(*args, **kwargs):
        return _misc_.TimeSpan___ge__(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _misc_.TimeSpan___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _misc_.TimeSpan___ne__(*args, **kwargs)

    def IsNull(*args, **kwargs):
        return _misc_.TimeSpan_IsNull(*args, **kwargs)

    def IsPositive(*args, **kwargs):
        return _misc_.TimeSpan_IsPositive(*args, **kwargs)

    def IsNegative(*args, **kwargs):
        return _misc_.TimeSpan_IsNegative(*args, **kwargs)

    def IsEqualTo(*args, **kwargs):
        return _misc_.TimeSpan_IsEqualTo(*args, **kwargs)

    def IsLongerThan(*args, **kwargs):
        return _misc_.TimeSpan_IsLongerThan(*args, **kwargs)

    def IsShorterThan(*args, **kwargs):
        return _misc_.TimeSpan_IsShorterThan(*args, **kwargs)

    def GetWeeks(*args, **kwargs):
        return _misc_.TimeSpan_GetWeeks(*args, **kwargs)

    def GetDays(*args, **kwargs):
        return _misc_.TimeSpan_GetDays(*args, **kwargs)

    def GetHours(*args, **kwargs):
        return _misc_.TimeSpan_GetHours(*args, **kwargs)

    def GetMinutes(*args, **kwargs):
        return _misc_.TimeSpan_GetMinutes(*args, **kwargs)

    def GetSeconds(*args, **kwargs):
        return _misc_.TimeSpan_GetSeconds(*args, **kwargs)

    def GetMilliseconds(*args, **kwargs):
        return _misc_.TimeSpan_GetMilliseconds(*args, **kwargs)

    def Format(*args, **kwargs):
        return _misc_.TimeSpan_Format(*args, **kwargs)

    def __repr__(self):
        f = self.Format().encode(wx.GetDefaultPyEncoding())
        return '<wx.TimeSpan: "%s" at %s>' % (f, self.this)

    def __str__(self):
        return self.Format().encode(wx.GetDefaultPyEncoding())

    days = property(GetDays, doc='See `GetDays`')
    hours = property(GetHours, doc='See `GetHours`')
    milliseconds = property(GetMilliseconds, doc='See `GetMilliseconds`')
    minutes = property(GetMinutes, doc='See `GetMinutes`')
    seconds = property(GetSeconds, doc='See `GetSeconds`')
    weeks = property(GetWeeks, doc='See `GetWeeks`')


_misc_.TimeSpan_swigregister(TimeSpan)

def TimeSpan_Milliseconds(*args, **kwargs):
    return _misc_.TimeSpan_Milliseconds(*args, **kwargs)


def TimeSpan_Millisecond(*args):
    return _misc_.TimeSpan_Millisecond(*args)


def TimeSpan_Seconds(*args, **kwargs):
    return _misc_.TimeSpan_Seconds(*args, **kwargs)


def TimeSpan_Second(*args):
    return _misc_.TimeSpan_Second(*args)


def TimeSpan_Minutes(*args, **kwargs):
    return _misc_.TimeSpan_Minutes(*args, **kwargs)


def TimeSpan_Minute(*args):
    return _misc_.TimeSpan_Minute(*args)


def TimeSpan_Hours(*args, **kwargs):
    return _misc_.TimeSpan_Hours(*args, **kwargs)


def TimeSpan_Hour(*args):
    return _misc_.TimeSpan_Hour(*args)


def TimeSpan_Days(*args, **kwargs):
    return _misc_.TimeSpan_Days(*args, **kwargs)


def TimeSpan_Day(*args):
    return _misc_.TimeSpan_Day(*args)


def TimeSpan_Weeks(*args, **kwargs):
    return _misc_.TimeSpan_Weeks(*args, **kwargs)


def TimeSpan_Week(*args):
    return _misc_.TimeSpan_Week(*args)


class DateSpan(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.DateSpan_swiginit(self, _misc_.new_DateSpan(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_DateSpan
    __del__ = lambda self: None

    def Days(*args, **kwargs):
        return _misc_.DateSpan_Days(*args, **kwargs)

    Days = staticmethod(Days)

    def Day(*args, **kwargs):
        return _misc_.DateSpan_Day(*args, **kwargs)

    Day = staticmethod(Day)

    def Weeks(*args, **kwargs):
        return _misc_.DateSpan_Weeks(*args, **kwargs)

    Weeks = staticmethod(Weeks)

    def Week(*args, **kwargs):
        return _misc_.DateSpan_Week(*args, **kwargs)

    Week = staticmethod(Week)

    def Months(*args, **kwargs):
        return _misc_.DateSpan_Months(*args, **kwargs)

    Months = staticmethod(Months)

    def Month(*args, **kwargs):
        return _misc_.DateSpan_Month(*args, **kwargs)

    Month = staticmethod(Month)

    def Years(*args, **kwargs):
        return _misc_.DateSpan_Years(*args, **kwargs)

    Years = staticmethod(Years)

    def Year(*args, **kwargs):
        return _misc_.DateSpan_Year(*args, **kwargs)

    Year = staticmethod(Year)

    def SetYears(*args, **kwargs):
        return _misc_.DateSpan_SetYears(*args, **kwargs)

    def SetMonths(*args, **kwargs):
        return _misc_.DateSpan_SetMonths(*args, **kwargs)

    def SetWeeks(*args, **kwargs):
        return _misc_.DateSpan_SetWeeks(*args, **kwargs)

    def SetDays(*args, **kwargs):
        return _misc_.DateSpan_SetDays(*args, **kwargs)

    def GetYears(*args, **kwargs):
        return _misc_.DateSpan_GetYears(*args, **kwargs)

    def GetMonths(*args, **kwargs):
        return _misc_.DateSpan_GetMonths(*args, **kwargs)

    def GetWeeks(*args, **kwargs):
        return _misc_.DateSpan_GetWeeks(*args, **kwargs)

    def GetDays(*args, **kwargs):
        return _misc_.DateSpan_GetDays(*args, **kwargs)

    def GetTotalDays(*args, **kwargs):
        return _misc_.DateSpan_GetTotalDays(*args, **kwargs)

    def Add(*args, **kwargs):
        return _misc_.DateSpan_Add(*args, **kwargs)

    def Subtract(*args, **kwargs):
        return _misc_.DateSpan_Subtract(*args, **kwargs)

    def Neg(*args, **kwargs):
        return _misc_.DateSpan_Neg(*args, **kwargs)

    def Multiply(*args, **kwargs):
        return _misc_.DateSpan_Multiply(*args, **kwargs)

    def __iadd__(*args, **kwargs):
        return _misc_.DateSpan___iadd__(*args, **kwargs)

    def __isub__(*args, **kwargs):
        return _misc_.DateSpan___isub__(*args, **kwargs)

    def __neg__(*args, **kwargs):
        return _misc_.DateSpan___neg__(*args, **kwargs)

    def __imul__(*args, **kwargs):
        return _misc_.DateSpan___imul__(*args, **kwargs)

    def __add__(*args, **kwargs):
        return _misc_.DateSpan___add__(*args, **kwargs)

    def __sub__(*args, **kwargs):
        return _misc_.DateSpan___sub__(*args, **kwargs)

    def __mul__(*args, **kwargs):
        return _misc_.DateSpan___mul__(*args, **kwargs)

    def __rmul__(*args, **kwargs):
        return _misc_.DateSpan___rmul__(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _misc_.DateSpan___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _misc_.DateSpan___ne__(*args, **kwargs)

    days = property(GetDays, SetDays, doc='See `GetDays` and `SetDays`')
    months = property(GetMonths, SetMonths, doc='See `GetMonths` and `SetMonths`')
    totalDays = property(GetTotalDays, doc='See `GetTotalDays`')
    weeks = property(GetWeeks, SetWeeks, doc='See `GetWeeks` and `SetWeeks`')
    years = property(GetYears, SetYears, doc='See `GetYears` and `SetYears`')


_misc_.DateSpan_swigregister(DateSpan)

def DateSpan_Days(*args, **kwargs):
    return _misc_.DateSpan_Days(*args, **kwargs)


def DateSpan_Day(*args):
    return _misc_.DateSpan_Day(*args)


def DateSpan_Weeks(*args, **kwargs):
    return _misc_.DateSpan_Weeks(*args, **kwargs)


def DateSpan_Week(*args):
    return _misc_.DateSpan_Week(*args)


def DateSpan_Months(*args, **kwargs):
    return _misc_.DateSpan_Months(*args, **kwargs)


def DateSpan_Month(*args):
    return _misc_.DateSpan_Month(*args)


def DateSpan_Years(*args, **kwargs):
    return _misc_.DateSpan_Years(*args, **kwargs)


def DateSpan_Year(*args):
    return _misc_.DateSpan_Year(*args)


def GetLocalTime(*args):
    return _misc_.GetLocalTime(*args)


def GetUTCTime(*args):
    return _misc_.GetUTCTime(*args)


def GetCurrentTime(*args):
    return _misc_.GetCurrentTime(*args)


def GetLocalTimeMillis(*args):
    return _misc_.GetLocalTimeMillis(*args)


DF_INVALID = _misc_.DF_INVALID
DF_TEXT = _misc_.DF_TEXT
DF_BITMAP = _misc_.DF_BITMAP
DF_METAFILE = _misc_.DF_METAFILE
DF_SYLK = _misc_.DF_SYLK
DF_DIF = _misc_.DF_DIF
DF_TIFF = _misc_.DF_TIFF
DF_OEMTEXT = _misc_.DF_OEMTEXT
DF_DIB = _misc_.DF_DIB
DF_PALETTE = _misc_.DF_PALETTE
DF_PENDATA = _misc_.DF_PENDATA
DF_RIFF = _misc_.DF_RIFF
DF_WAVE = _misc_.DF_WAVE
DF_UNICODETEXT = _misc_.DF_UNICODETEXT
DF_ENHMETAFILE = _misc_.DF_ENHMETAFILE
DF_FILENAME = _misc_.DF_FILENAME
DF_LOCALE = _misc_.DF_LOCALE
DF_PRIVATE = _misc_.DF_PRIVATE
DF_HTML = _misc_.DF_HTML
DF_MAX = _misc_.DF_MAX

class DataFormat(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.DataFormat_swiginit(self, _misc_.new_DataFormat(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_DataFormat
    __del__ = lambda self: None

    def __eq__(*args):
        return _misc_.DataFormat___eq__(*args)

    def __ne__(*args):
        return _misc_.DataFormat___ne__(*args)

    def SetType(*args, **kwargs):
        return _misc_.DataFormat_SetType(*args, **kwargs)

    def GetType(*args, **kwargs):
        return _misc_.DataFormat_GetType(*args, **kwargs)

    def _GetId(*args, **kwargs):
        return _misc_.DataFormat__GetId(*args, **kwargs)

    def GetId(self):
        nolog = wx.LogNull()
        return self._GetId()

    def SetId(*args, **kwargs):
        return _misc_.DataFormat_SetId(*args, **kwargs)

    Id = property(GetId, SetId, doc='See `GetId` and `SetId`')
    Type = property(GetType, SetType, doc='See `GetType` and `SetType`')


_misc_.DataFormat_swigregister(DataFormat)
DefaultDateTime = cvar.DefaultDateTime

def CustomDataFormat(*args, **kwargs):
    val = _misc_.new_CustomDataFormat(*args, **kwargs)
    return val


class DataObject(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    Get = _misc_.DataObject_Get
    Set = _misc_.DataObject_Set
    Both = _misc_.DataObject_Both
    __swig_destroy__ = _misc_.delete_DataObject
    __del__ = lambda self: None

    def GetPreferredFormat(*args, **kwargs):
        return _misc_.DataObject_GetPreferredFormat(*args, **kwargs)

    def GetFormatCount(*args, **kwargs):
        return _misc_.DataObject_GetFormatCount(*args, **kwargs)

    def IsSupported(*args, **kwargs):
        return _misc_.DataObject_IsSupported(*args, **kwargs)

    def GetDataSize(*args, **kwargs):
        return _misc_.DataObject_GetDataSize(*args, **kwargs)

    def GetAllFormats(*args, **kwargs):
        return _misc_.DataObject_GetAllFormats(*args, **kwargs)

    def GetDataHere(*args, **kwargs):
        return _misc_.DataObject_GetDataHere(*args, **kwargs)

    def SetData(*args, **kwargs):
        return _misc_.DataObject_SetData(*args, **kwargs)

    AllFormats = property(GetAllFormats, doc='See `GetAllFormats`')
    DataHere = property(GetDataHere, doc='See `GetDataHere`')
    DataSize = property(GetDataSize, doc='See `GetDataSize`')
    FormatCount = property(GetFormatCount, doc='See `GetFormatCount`')
    PreferredFormat = property(GetPreferredFormat, doc='See `GetPreferredFormat`')


_misc_.DataObject_swigregister(DataObject)
FormatInvalid = cvar.FormatInvalid

class DataObjectSimple(DataObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.DataObjectSimple_swiginit(self, _misc_.new_DataObjectSimple(*args, **kwargs))

    def GetFormat(*args, **kwargs):
        return _misc_.DataObjectSimple_GetFormat(*args, **kwargs)

    def SetFormat(*args, **kwargs):
        return _misc_.DataObjectSimple_SetFormat(*args, **kwargs)

    def GetDataSize(*args, **kwargs):
        return _misc_.DataObjectSimple_GetDataSize(*args, **kwargs)

    def GetDataHere(*args, **kwargs):
        return _misc_.DataObjectSimple_GetDataHere(*args, **kwargs)

    def SetData(*args, **kwargs):
        return _misc_.DataObjectSimple_SetData(*args, **kwargs)

    Format = property(GetFormat, SetFormat, doc='See `GetFormat` and `SetFormat`')


_misc_.DataObjectSimple_swigregister(DataObjectSimple)

class PyDataObjectSimple(DataObjectSimple):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.PyDataObjectSimple_swiginit(self, _misc_.new_PyDataObjectSimple(*args, **kwargs))
        PyDataObjectSimple._setCallbackInfo(self, self, PyDataObjectSimple)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.PyDataObjectSimple__setCallbackInfo(*args, **kwargs)


_misc_.PyDataObjectSimple_swigregister(PyDataObjectSimple)

class DataObjectComposite(DataObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.DataObjectComposite_swiginit(self, _misc_.new_DataObjectComposite(*args, **kwargs))

    def Add(*args, **kwargs):
        return _misc_.DataObjectComposite_Add(*args, **kwargs)

    def GetReceivedFormat(*args, **kwargs):
        return _misc_.DataObjectComposite_GetReceivedFormat(*args, **kwargs)

    ReceivedFormat = property(GetReceivedFormat, doc='See `GetReceivedFormat`')


_misc_.DataObjectComposite_swigregister(DataObjectComposite)

class TextDataObject(DataObjectSimple):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.TextDataObject_swiginit(self, _misc_.new_TextDataObject(*args, **kwargs))

    def GetTextLength(*args, **kwargs):
        return _misc_.TextDataObject_GetTextLength(*args, **kwargs)

    def GetText(*args, **kwargs):
        return _misc_.TextDataObject_GetText(*args, **kwargs)

    def SetText(*args, **kwargs):
        return _misc_.TextDataObject_SetText(*args, **kwargs)

    Text = property(GetText, SetText, doc='See `GetText` and `SetText`')
    TextLength = property(GetTextLength, doc='See `GetTextLength`')


_misc_.TextDataObject_swigregister(TextDataObject)

class PyTextDataObject(TextDataObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.PyTextDataObject_swiginit(self, _misc_.new_PyTextDataObject(*args, **kwargs))
        PyTextDataObject._setCallbackInfo(self, self, PyTextDataObject)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.PyTextDataObject__setCallbackInfo(*args, **kwargs)


_misc_.PyTextDataObject_swigregister(PyTextDataObject)

class BitmapDataObject(DataObjectSimple):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.BitmapDataObject_swiginit(self, _misc_.new_BitmapDataObject(*args, **kwargs))

    def GetBitmap(*args, **kwargs):
        return _misc_.BitmapDataObject_GetBitmap(*args, **kwargs)

    def SetBitmap(*args, **kwargs):
        return _misc_.BitmapDataObject_SetBitmap(*args, **kwargs)

    Bitmap = property(GetBitmap, SetBitmap, doc='See `GetBitmap` and `SetBitmap`')


_misc_.BitmapDataObject_swigregister(BitmapDataObject)

class PyBitmapDataObject(BitmapDataObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.PyBitmapDataObject_swiginit(self, _misc_.new_PyBitmapDataObject(*args, **kwargs))
        PyBitmapDataObject._setCallbackInfo(self, self, PyBitmapDataObject)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.PyBitmapDataObject__setCallbackInfo(*args, **kwargs)


_misc_.PyBitmapDataObject_swigregister(PyBitmapDataObject)

class FileDataObject(DataObjectSimple):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.FileDataObject_swiginit(self, _misc_.new_FileDataObject(*args, **kwargs))

    def GetFilenames(*args, **kwargs):
        return _misc_.FileDataObject_GetFilenames(*args, **kwargs)

    def AddFile(*args, **kwargs):
        return _misc_.FileDataObject_AddFile(*args, **kwargs)

    Filenames = property(GetFilenames, doc='See `GetFilenames`')


_misc_.FileDataObject_swigregister(FileDataObject)

class CustomDataObject(DataObjectSimple):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args):
        _misc_.CustomDataObject_swiginit(self, _misc_.new_CustomDataObject(*args))

    def SetData(*args, **kwargs):
        return _misc_.CustomDataObject_SetData(*args, **kwargs)

    TakeData = SetData

    def GetSize(*args, **kwargs):
        return _misc_.CustomDataObject_GetSize(*args, **kwargs)

    def GetData(*args, **kwargs):
        return _misc_.CustomDataObject_GetData(*args, **kwargs)

    Data = property(GetData, SetData, doc='See `GetData` and `SetData`')
    Size = property(GetSize, doc='See `GetSize`')


_misc_.CustomDataObject_swigregister(CustomDataObject)

class URLDataObject(DataObject):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.URLDataObject_swiginit(self, _misc_.new_URLDataObject(*args, **kwargs))

    def GetURL(*args, **kwargs):
        return _misc_.URLDataObject_GetURL(*args, **kwargs)

    def SetURL(*args, **kwargs):
        return _misc_.URLDataObject_SetURL(*args, **kwargs)

    URL = property(GetURL, SetURL, doc='See `GetURL` and `SetURL`')


_misc_.URLDataObject_swigregister(URLDataObject)

class MetafileDataObject(DataObjectSimple):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.MetafileDataObject_swiginit(self, _misc_.new_MetafileDataObject(*args, **kwargs))


_misc_.MetafileDataObject_swigregister(MetafileDataObject)
Drag_CopyOnly = _misc_.Drag_CopyOnly
Drag_AllowMove = _misc_.Drag_AllowMove
Drag_DefaultMove = _misc_.Drag_DefaultMove
DragError = _misc_.DragError
DragNone = _misc_.DragNone
DragCopy = _misc_.DragCopy
DragMove = _misc_.DragMove
DragLink = _misc_.DragLink
DragCancel = _misc_.DragCancel

def IsDragResultOk(*args, **kwargs):
    return _misc_.IsDragResultOk(*args, **kwargs)


class DropSource(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.DropSource_swiginit(self, _misc_.new_DropSource(*args, **kwargs))
        DropSource._setCallbackInfo(self, self, DropSource)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.DropSource__setCallbackInfo(*args, **kwargs)

    __swig_destroy__ = _misc_.delete_DropSource
    __del__ = lambda self: None

    def SetData(*args, **kwargs):
        return _misc_.DropSource_SetData(*args, **kwargs)

    def GetDataObject(*args, **kwargs):
        return _misc_.DropSource_GetDataObject(*args, **kwargs)

    def SetCursor(*args, **kwargs):
        return _misc_.DropSource_SetCursor(*args, **kwargs)

    def DoDragDrop(*args, **kwargs):
        return _misc_.DropSource_DoDragDrop(*args, **kwargs)

    def GiveFeedback(*args, **kwargs):
        return _misc_.DropSource_GiveFeedback(*args, **kwargs)

    def base_GiveFeedback(*args, **kw):
        return DropSource.GiveFeedback(*args, **kw)

    base_GiveFeedback = wx._deprecated(base_GiveFeedback, 'Please use DropSource.GiveFeedback instead.')
    DataObject = property(GetDataObject, SetData, doc='See `GetDataObject` and `SetData`')


_misc_.DropSource_swigregister(DropSource)

def DROP_ICON(filename):
    img = wx.Image(filename)
    if wx.Platform == '__WXGTK__':
        return wx.IconFromBitmap(wx.BitmapFromImage(img))
    else:
        return wx.CursorFromImage(img)


class DropTarget(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.DropTarget_swiginit(self, _misc_.new_DropTarget(*args, **kwargs))
        DropTarget._setCallbackInfo(self, self, DropTarget)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.DropTarget__setCallbackInfo(*args, **kwargs)

    __swig_destroy__ = _misc_.delete_DropTarget
    __del__ = lambda self: None

    def GetDataObject(*args, **kwargs):
        return _misc_.DropTarget_GetDataObject(*args, **kwargs)

    def SetDataObject(*args, **kwargs):
        return _misc_.DropTarget_SetDataObject(*args, **kwargs)

    def OnEnter(*args, **kwargs):
        return _misc_.DropTarget_OnEnter(*args, **kwargs)

    def OnDragOver(*args, **kwargs):
        return _misc_.DropTarget_OnDragOver(*args, **kwargs)

    def OnLeave(*args, **kwargs):
        return _misc_.DropTarget_OnLeave(*args, **kwargs)

    def OnDrop(*args, **kwargs):
        return _misc_.DropTarget_OnDrop(*args, **kwargs)

    def base_OnEnter(*args, **kw):
        return DropTarget.OnEnter(*args, **kw)

    base_OnEnter = wx._deprecated(base_OnEnter, 'Please use DropTarget.OnEnter instead.')

    def base_OnDragOver(*args, **kw):
        return DropTarget.OnDragOver(*args, **kw)

    base_OnDragOver = wx._deprecated(base_OnDragOver, 'Please use DropTarget.OnDragOver instead.')

    def base_OnLeave(*args, **kw):
        return DropTarget.OnLeave(*args, **kw)

    base_OnLeave = wx._deprecated(base_OnLeave, 'Please use DropTarget.OnLeave instead.')

    def base_OnDrop(*args, **kw):
        return DropTarget.OnDrop(*args, **kw)

    base_OnDrop = wx._deprecated(base_OnDrop, 'Please use DropTarget.OnDrop instead.')

    def GetData(*args, **kwargs):
        return _misc_.DropTarget_GetData(*args, **kwargs)

    def SetDefaultAction(*args, **kwargs):
        return _misc_.DropTarget_SetDefaultAction(*args, **kwargs)

    def GetDefaultAction(*args, **kwargs):
        return _misc_.DropTarget_GetDefaultAction(*args, **kwargs)

    DataObject = property(GetDataObject, SetDataObject, doc='See `GetDataObject` and `SetDataObject`')
    DefaultAction = property(GetDefaultAction, SetDefaultAction, doc='See `GetDefaultAction` and `SetDefaultAction`')


_misc_.DropTarget_swigregister(DropTarget)
PyDropTarget = DropTarget

class TextDropTarget(DropTarget):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.TextDropTarget_swiginit(self, _misc_.new_TextDropTarget(*args, **kwargs))
        TextDropTarget._setCallbackInfo(self, self, TextDropTarget)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.TextDropTarget__setCallbackInfo(*args, **kwargs)

    def OnDropText(*args, **kwargs):
        return _misc_.TextDropTarget_OnDropText(*args, **kwargs)

    def OnEnter(*args, **kwargs):
        return _misc_.TextDropTarget_OnEnter(*args, **kwargs)

    def OnDragOver(*args, **kwargs):
        return _misc_.TextDropTarget_OnDragOver(*args, **kwargs)

    def OnLeave(*args, **kwargs):
        return _misc_.TextDropTarget_OnLeave(*args, **kwargs)

    def OnDrop(*args, **kwargs):
        return _misc_.TextDropTarget_OnDrop(*args, **kwargs)

    def OnData(*args, **kwargs):
        return _misc_.TextDropTarget_OnData(*args, **kwargs)

    def base_OnDropText(*args, **kw):
        return TextDropTarget.OnDropText(*args, **kw)

    base_OnDropText = wx._deprecated(base_OnDropText, 'Please use TextDropTarget.OnDropText instead.')

    def base_OnEnter(*args, **kw):
        return TextDropTarget.OnEnter(*args, **kw)

    base_OnEnter = wx._deprecated(base_OnEnter, 'Please use TextDropTarget.OnEnter instead.')

    def base_OnDragOver(*args, **kw):
        return TextDropTarget.OnDragOver(*args, **kw)

    base_OnDragOver = wx._deprecated(base_OnDragOver, 'Please use TextDropTarget.OnDragOver instead.')

    def base_OnLeave(*args, **kw):
        return TextDropTarget.OnLeave(*args, **kw)

    base_OnLeave = wx._deprecated(base_OnLeave, 'Please use TextDropTarget.OnLeave instead.')

    def base_OnDrop(*args, **kw):
        return TextDropTarget.OnDrop(*args, **kw)

    base_OnDrop = wx._deprecated(base_OnDrop, 'Please use TextDropTarget.OnDrop instead.')

    def base_OnData(*args, **kw):
        return TextDropTarget.OnData(*args, **kw)

    base_OnData = wx._deprecated(base_OnData, 'Please use TextDropTarget.OnData instead.')


_misc_.TextDropTarget_swigregister(TextDropTarget)

class FileDropTarget(DropTarget):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.FileDropTarget_swiginit(self, _misc_.new_FileDropTarget(*args, **kwargs))
        FileDropTarget._setCallbackInfo(self, self, FileDropTarget)

    def _setCallbackInfo(*args, **kwargs):
        return _misc_.FileDropTarget__setCallbackInfo(*args, **kwargs)

    def OnDropFiles(*args, **kwargs):
        return _misc_.FileDropTarget_OnDropFiles(*args, **kwargs)

    def OnEnter(*args, **kwargs):
        return _misc_.FileDropTarget_OnEnter(*args, **kwargs)

    def OnDragOver(*args, **kwargs):
        return _misc_.FileDropTarget_OnDragOver(*args, **kwargs)

    def OnLeave(*args, **kwargs):
        return _misc_.FileDropTarget_OnLeave(*args, **kwargs)

    def OnDrop(*args, **kwargs):
        return _misc_.FileDropTarget_OnDrop(*args, **kwargs)

    def OnData(*args, **kwargs):
        return _misc_.FileDropTarget_OnData(*args, **kwargs)

    def base_OnDropFiles(*args, **kw):
        return FileDropTarget.OnDropFiles(*args, **kw)

    base_OnDropFiles = wx._deprecated(base_OnDropFiles, 'Please use FileDropTarget.OnDropFiles instead.')

    def base_OnEnter(*args, **kw):
        return FileDropTarget.OnEnter(*args, **kw)

    base_OnEnter = wx._deprecated(base_OnEnter, 'Please use FileDropTarget.OnEnter instead.')

    def base_OnDragOver(*args, **kw):
        return FileDropTarget.OnDragOver(*args, **kw)

    base_OnDragOver = wx._deprecated(base_OnDragOver, 'Please use FileDropTarget.OnDragOver instead.')

    def base_OnLeave(*args, **kw):
        return FileDropTarget.OnLeave(*args, **kw)

    base_OnLeave = wx._deprecated(base_OnLeave, 'Please use FileDropTarget.OnLeave instead.')

    def base_OnDrop(*args, **kw):
        return FileDropTarget.OnDrop(*args, **kw)

    base_OnDrop = wx._deprecated(base_OnDrop, 'Please use FileDropTarget.OnDrop instead.')

    def base_OnData(*args, **kw):
        return FileDropTarget.OnData(*args, **kw)

    base_OnData = wx._deprecated(base_OnData, 'Please use FileDropTarget.OnData instead.')


_misc_.FileDropTarget_swigregister(FileDropTarget)

class Clipboard(_core.Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.Clipboard_swiginit(self, _misc_.new_Clipboard(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_Clipboard
    __del__ = lambda self: None

    def Open(*args, **kwargs):
        return _misc_.Clipboard_Open(*args, **kwargs)

    def Close(*args, **kwargs):
        return _misc_.Clipboard_Close(*args, **kwargs)

    def IsOpened(*args, **kwargs):
        return _misc_.Clipboard_IsOpened(*args, **kwargs)

    def AddData(*args, **kwargs):
        return _misc_.Clipboard_AddData(*args, **kwargs)

    def SetData(*args, **kwargs):
        return _misc_.Clipboard_SetData(*args, **kwargs)

    def IsSupported(*args, **kwargs):
        return _misc_.Clipboard_IsSupported(*args, **kwargs)

    def GetData(*args, **kwargs):
        return _misc_.Clipboard_GetData(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _misc_.Clipboard_Clear(*args, **kwargs)

    def Flush(*args, **kwargs):
        return _misc_.Clipboard_Flush(*args, **kwargs)

    def UsePrimarySelection(*args, **kwargs):
        return _misc_.Clipboard_UsePrimarySelection(*args, **kwargs)

    def Get(*args, **kwargs):
        return _misc_.Clipboard_Get(*args, **kwargs)

    Get = staticmethod(Get)


_misc_.Clipboard_swigregister(Clipboard)

def Clipboard_Get(*args):
    return _misc_.Clipboard_Get(*args)


class _wxPyDelayedInitWrapper(object):

    def __init__(self, initfunc, *args, **kwargs):
        self._initfunc = initfunc
        self._args = args
        self._kwargs = kwargs
        self._instance = None

    def _checkInstance(self):
        if self._instance is None:
            if wx.GetApp():
                self._instance = self._initfunc(*self._args, **self._kwargs)

    def __getattr__(self, name):
        self._checkInstance()
        return getattr(self._instance, name)

    def __repr__(self):
        self._checkInstance()
        return repr(self._instance)


TheClipboard = _wxPyDelayedInitWrapper(Clipboard.Get)

class ClipboardLocker(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.ClipboardLocker_swiginit(self, _misc_.new_ClipboardLocker(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_ClipboardLocker
    __del__ = lambda self: None

    def __nonzero__(*args, **kwargs):
        return _misc_.ClipboardLocker___nonzero__(*args, **kwargs)


_misc_.ClipboardLocker_swigregister(ClipboardLocker)

class VideoMode(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.VideoMode_swiginit(self, _misc_.new_VideoMode(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_VideoMode
    __del__ = lambda self: None

    def Matches(*args, **kwargs):
        return _misc_.VideoMode_Matches(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _misc_.VideoMode_GetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _misc_.VideoMode_GetHeight(*args, **kwargs)

    def GetDepth(*args, **kwargs):
        return _misc_.VideoMode_GetDepth(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _misc_.VideoMode_IsOk(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def __eq__(*args, **kwargs):
        return _misc_.VideoMode___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _misc_.VideoMode___ne__(*args, **kwargs)

    w = property(_misc_.VideoMode_w_get, _misc_.VideoMode_w_set)
    h = property(_misc_.VideoMode_h_get, _misc_.VideoMode_h_set)
    bpp = property(_misc_.VideoMode_bpp_get, _misc_.VideoMode_bpp_set)
    refresh = property(_misc_.VideoMode_refresh_get, _misc_.VideoMode_refresh_set)
    Depth = property(GetDepth, doc='See `GetDepth`')
    Height = property(GetHeight, doc='See `GetHeight`')
    Width = property(GetWidth, doc='See `GetWidth`')


_misc_.VideoMode_swigregister(VideoMode)

class Display(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.Display_swiginit(self, _misc_.new_Display(*args, **kwargs))

    __swig_destroy__ = _misc_.delete_Display
    __del__ = lambda self: None

    def GetCount(*args, **kwargs):
        return _misc_.Display_GetCount(*args, **kwargs)

    GetCount = staticmethod(GetCount)

    def GetFromPoint(*args, **kwargs):
        return _misc_.Display_GetFromPoint(*args, **kwargs)

    GetFromPoint = staticmethod(GetFromPoint)

    def GetFromWindow(*args, **kwargs):
        return _misc_.Display_GetFromWindow(*args, **kwargs)

    GetFromWindow = staticmethod(GetFromWindow)

    def IsOk(*args, **kwargs):
        return _misc_.Display_IsOk(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def GetGeometry(*args, **kwargs):
        return _misc_.Display_GetGeometry(*args, **kwargs)

    def GetClientArea(*args, **kwargs):
        return _misc_.Display_GetClientArea(*args, **kwargs)

    def GetName(*args, **kwargs):
        return _misc_.Display_GetName(*args, **kwargs)

    def IsPrimary(*args, **kwargs):
        return _misc_.Display_IsPrimary(*args, **kwargs)

    def GetModes(*args, **kwargs):
        return _misc_.Display_GetModes(*args, **kwargs)

    def GetCurrentMode(*args, **kwargs):
        return _misc_.Display_GetCurrentMode(*args, **kwargs)

    def ChangeMode(*args, **kwargs):
        return _misc_.Display_ChangeMode(*args, **kwargs)

    def ResetMode(*args, **kwargs):
        return _misc_.Display_ResetMode(*args, **kwargs)

    ClientArea = property(GetClientArea, doc='See `GetClientArea`')
    CurrentMode = property(GetCurrentMode, doc='See `GetCurrentMode`')
    Geometry = property(GetGeometry, doc='See `GetGeometry`')
    Modes = property(GetModes, doc='See `GetModes`')
    Name = property(GetName, doc='See `GetName`')


_misc_.Display_swigregister(Display)
DefaultVideoMode = cvar.DefaultVideoMode

def Display_GetCount(*args):
    return _misc_.Display_GetCount(*args)


def Display_GetFromPoint(*args, **kwargs):
    return _misc_.Display_GetFromPoint(*args, **kwargs)


def Display_GetFromWindow(*args, **kwargs):
    return _misc_.Display_GetFromWindow(*args, **kwargs)


class StandardPaths(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    ResourceCat_None = _misc_.StandardPaths_ResourceCat_None
    ResourceCat_Messages = _misc_.StandardPaths_ResourceCat_Messages
    ResourceCat_Max = _misc_.StandardPaths_ResourceCat_Max

    def Get(*args, **kwargs):
        return _misc_.StandardPaths_Get(*args, **kwargs)

    Get = staticmethod(Get)

    def GetExecutablePath(*args, **kwargs):
        return _misc_.StandardPaths_GetExecutablePath(*args, **kwargs)

    def GetConfigDir(*args, **kwargs):
        return _misc_.StandardPaths_GetConfigDir(*args, **kwargs)

    def GetUserConfigDir(*args, **kwargs):
        return _misc_.StandardPaths_GetUserConfigDir(*args, **kwargs)

    def GetDataDir(*args, **kwargs):
        return _misc_.StandardPaths_GetDataDir(*args, **kwargs)

    def GetLocalDataDir(*args, **kwargs):
        return _misc_.StandardPaths_GetLocalDataDir(*args, **kwargs)

    def GetUserDataDir(*args, **kwargs):
        return _misc_.StandardPaths_GetUserDataDir(*args, **kwargs)

    def GetUserLocalDataDir(*args, **kwargs):
        return _misc_.StandardPaths_GetUserLocalDataDir(*args, **kwargs)

    def GetPluginsDir(*args, **kwargs):
        return _misc_.StandardPaths_GetPluginsDir(*args, **kwargs)

    def GetResourcesDir(*args, **kwargs):
        return _misc_.StandardPaths_GetResourcesDir(*args, **kwargs)

    def GetLocalizedResourcesDir(*args, **kwargs):
        return _misc_.StandardPaths_GetLocalizedResourcesDir(*args, **kwargs)

    def GetDocumentsDir(*args, **kwargs):
        return _misc_.StandardPaths_GetDocumentsDir(*args, **kwargs)

    def GetTempDir(*args, **kwargs):
        return _misc_.StandardPaths_GetTempDir(*args, **kwargs)

    def SetInstallPrefix(*args, **kwargs):
        return _misc_.StandardPaths_SetInstallPrefix(*args, **kwargs)

    def GetInstallPrefix(*args, **kwargs):
        return _misc_.StandardPaths_GetInstallPrefix(*args, **kwargs)


_misc_.StandardPaths_swigregister(StandardPaths)

def StandardPaths_Get(*args):
    return _misc_.StandardPaths_Get(*args)


POWER_SOCKET = _misc_.POWER_SOCKET
POWER_BATTERY = _misc_.POWER_BATTERY
POWER_UNKNOWN = _misc_.POWER_UNKNOWN
BATTERY_NORMAL_STATE = _misc_.BATTERY_NORMAL_STATE
BATTERY_LOW_STATE = _misc_.BATTERY_LOW_STATE
BATTERY_CRITICAL_STATE = _misc_.BATTERY_CRITICAL_STATE
BATTERY_SHUTDOWN_STATE = _misc_.BATTERY_SHUTDOWN_STATE
BATTERY_UNKNOWN_STATE = _misc_.BATTERY_UNKNOWN_STATE

class PowerEvent(_core.Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _misc_.PowerEvent_swiginit(self, _misc_.new_PowerEvent(*args, **kwargs))

    def Veto(*args, **kwargs):
        return _misc_.PowerEvent_Veto(*args, **kwargs)

    def IsVetoed(*args, **kwargs):
        return _misc_.PowerEvent_IsVetoed(*args, **kwargs)


_misc_.PowerEvent_swigregister(PowerEvent)
wxEVT_POWER_SUSPENDING = _misc_.wxEVT_POWER_SUSPENDING
wxEVT_POWER_SUSPENDED = _misc_.wxEVT_POWER_SUSPENDED
wxEVT_POWER_SUSPEND_CANCEL = _misc_.wxEVT_POWER_SUSPEND_CANCEL
wxEVT_POWER_RESUME = _misc_.wxEVT_POWER_RESUME
EVT_POWER_SUSPENDING = wx.PyEventBinder(wxEVT_POWER_SUSPENDING, 1)
EVT_POWER_SUSPENDED = wx.PyEventBinder(wxEVT_POWER_SUSPENDED, 1)
EVT_POWER_SUSPEND_CANCEL = wx.PyEventBinder(wxEVT_POWER_SUSPEND_CANCEL, 1)
EVT_POWER_RESUME = wx.PyEventBinder(wxEVT_POWER_RESUME, 1)

def GetPowerType(*args):
    return _misc_.GetPowerType(*args)


def GetBatteryState(*args):
    return _misc_.GetBatteryState(*args)
