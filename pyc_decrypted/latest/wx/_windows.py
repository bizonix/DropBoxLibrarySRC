#Embedded file name: wx/_windows.py
import _windows_
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

class Panel(_core.Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.Panel_swiginit(self, _windows_.new_Panel(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.Panel_Create(*args, **kwargs)

    def InitDialog(*args, **kwargs):
        return _windows_.Panel_InitDialog(*args, **kwargs)

    def SetFocusIgnoringChildren(*args, **kwargs):
        return _windows_.Panel_SetFocusIgnoringChildren(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _windows_.Panel_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)


_windows_.Panel_swigregister(Panel)

def PrePanel(*args, **kwargs):
    val = _windows_.new_PrePanel(*args, **kwargs)
    return val


def Panel_GetClassDefaultAttributes(*args, **kwargs):
    return _windows_.Panel_GetClassDefaultAttributes(*args, **kwargs)


class ScrolledWindow(Panel):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.ScrolledWindow_swiginit(self, _windows_.new_ScrolledWindow(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.ScrolledWindow_Create(*args, **kwargs)

    def SetScrollbars(*args, **kwargs):
        return _windows_.ScrolledWindow_SetScrollbars(*args, **kwargs)

    def Scroll(*args, **kwargs):
        return _windows_.ScrolledWindow_Scroll(*args, **kwargs)

    def GetScrollPageSize(*args, **kwargs):
        return _windows_.ScrolledWindow_GetScrollPageSize(*args, **kwargs)

    def SetScrollPageSize(*args, **kwargs):
        return _windows_.ScrolledWindow_SetScrollPageSize(*args, **kwargs)

    def SetScrollRate(*args, **kwargs):
        return _windows_.ScrolledWindow_SetScrollRate(*args, **kwargs)

    def GetScrollPixelsPerUnit(*args, **kwargs):
        return _windows_.ScrolledWindow_GetScrollPixelsPerUnit(*args, **kwargs)

    def EnableScrolling(*args, **kwargs):
        return _windows_.ScrolledWindow_EnableScrolling(*args, **kwargs)

    def GetViewStart(*args, **kwargs):
        return _windows_.ScrolledWindow_GetViewStart(*args, **kwargs)

    def SetScale(*args, **kwargs):
        return _windows_.ScrolledWindow_SetScale(*args, **kwargs)

    def GetScaleX(*args, **kwargs):
        return _windows_.ScrolledWindow_GetScaleX(*args, **kwargs)

    def GetScaleY(*args, **kwargs):
        return _windows_.ScrolledWindow_GetScaleY(*args, **kwargs)

    def CalcScrolledPosition(*args):
        return _windows_.ScrolledWindow_CalcScrolledPosition(*args)

    def CalcUnscrolledPosition(*args):
        return _windows_.ScrolledWindow_CalcUnscrolledPosition(*args)

    def AdjustScrollbars(*args, **kwargs):
        return _windows_.ScrolledWindow_AdjustScrollbars(*args, **kwargs)

    def CalcScrollInc(*args, **kwargs):
        return _windows_.ScrolledWindow_CalcScrollInc(*args, **kwargs)

    def SetTargetWindow(*args, **kwargs):
        return _windows_.ScrolledWindow_SetTargetWindow(*args, **kwargs)

    def GetTargetWindow(*args, **kwargs):
        return _windows_.ScrolledWindow_GetTargetWindow(*args, **kwargs)

    def DoPrepareDC(*args, **kwargs):
        return _windows_.ScrolledWindow_DoPrepareDC(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _windows_.ScrolledWindow_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    ScaleX = property(GetScaleX, doc='See `GetScaleX`')
    ScaleY = property(GetScaleY, doc='See `GetScaleY`')
    TargetWindow = property(GetTargetWindow, SetTargetWindow, doc='See `GetTargetWindow` and `SetTargetWindow`')
    ViewStart = property(GetViewStart, doc='See `GetViewStart`')


_windows_.ScrolledWindow_swigregister(ScrolledWindow)

def PreScrolledWindow(*args, **kwargs):
    val = _windows_.new_PreScrolledWindow(*args, **kwargs)
    return val


def ScrolledWindow_GetClassDefaultAttributes(*args, **kwargs):
    return _windows_.ScrolledWindow_GetClassDefaultAttributes(*args, **kwargs)


STAY_ON_TOP = _windows_.STAY_ON_TOP
ICONIZE = _windows_.ICONIZE
MINIMIZE = _windows_.MINIMIZE
MAXIMIZE = _windows_.MAXIMIZE
CLOSE_BOX = _windows_.CLOSE_BOX
THICK_FRAME = _windows_.THICK_FRAME
SYSTEM_MENU = _windows_.SYSTEM_MENU
MINIMIZE_BOX = _windows_.MINIMIZE_BOX
MAXIMIZE_BOX = _windows_.MAXIMIZE_BOX
TINY_CAPTION_HORIZ = _windows_.TINY_CAPTION_HORIZ
TINY_CAPTION_VERT = _windows_.TINY_CAPTION_VERT
RESIZE_BOX = _windows_.RESIZE_BOX
RESIZE_BORDER = _windows_.RESIZE_BORDER
DIALOG_NO_PARENT = _windows_.DIALOG_NO_PARENT
DEFAULT_FRAME_STYLE = _windows_.DEFAULT_FRAME_STYLE
DEFAULT_DIALOG_STYLE = _windows_.DEFAULT_DIALOG_STYLE
FRAME_TOOL_WINDOW = _windows_.FRAME_TOOL_WINDOW
FRAME_FLOAT_ON_PARENT = _windows_.FRAME_FLOAT_ON_PARENT
FRAME_NO_WINDOW_MENU = _windows_.FRAME_NO_WINDOW_MENU
FRAME_NO_TASKBAR = _windows_.FRAME_NO_TASKBAR
FRAME_SHAPED = _windows_.FRAME_SHAPED
FRAME_DRAWER = _windows_.FRAME_DRAWER
FRAME_EX_METAL = _windows_.FRAME_EX_METAL
DIALOG_EX_METAL = _windows_.DIALOG_EX_METAL
WS_EX_CONTEXTHELP = _windows_.WS_EX_CONTEXTHELP
DIALOG_MODAL = _windows_.DIALOG_MODAL
DIALOG_MODELESS = _windows_.DIALOG_MODELESS
USER_COLOURS = _windows_.USER_COLOURS
NO_3D = _windows_.NO_3D
FRAME_EX_CONTEXTHELP = _windows_.FRAME_EX_CONTEXTHELP
DIALOG_EX_CONTEXTHELP = _windows_.DIALOG_EX_CONTEXTHELP
FULLSCREEN_NOMENUBAR = _windows_.FULLSCREEN_NOMENUBAR
FULLSCREEN_NOTOOLBAR = _windows_.FULLSCREEN_NOTOOLBAR
FULLSCREEN_NOSTATUSBAR = _windows_.FULLSCREEN_NOSTATUSBAR
FULLSCREEN_NOBORDER = _windows_.FULLSCREEN_NOBORDER
FULLSCREEN_NOCAPTION = _windows_.FULLSCREEN_NOCAPTION
FULLSCREEN_ALL = _windows_.FULLSCREEN_ALL
TOPLEVEL_EX_DIALOG = _windows_.TOPLEVEL_EX_DIALOG
USER_ATTENTION_INFO = _windows_.USER_ATTENTION_INFO
USER_ATTENTION_ERROR = _windows_.USER_ATTENTION_ERROR

class TopLevelWindow(_core.Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def Maximize(*args, **kwargs):
        return _windows_.TopLevelWindow_Maximize(*args, **kwargs)

    def Restore(*args, **kwargs):
        return _windows_.TopLevelWindow_Restore(*args, **kwargs)

    def Iconize(*args, **kwargs):
        return _windows_.TopLevelWindow_Iconize(*args, **kwargs)

    def IsMaximized(*args, **kwargs):
        return _windows_.TopLevelWindow_IsMaximized(*args, **kwargs)

    def IsAlwaysMaximized(*args, **kwargs):
        return _windows_.TopLevelWindow_IsAlwaysMaximized(*args, **kwargs)

    def IsIconized(*args, **kwargs):
        return _windows_.TopLevelWindow_IsIconized(*args, **kwargs)

    def GetIcon(*args, **kwargs):
        return _windows_.TopLevelWindow_GetIcon(*args, **kwargs)

    def SetIcon(*args, **kwargs):
        return _windows_.TopLevelWindow_SetIcon(*args, **kwargs)

    def SetIcons(*args, **kwargs):
        return _windows_.TopLevelWindow_SetIcons(*args, **kwargs)

    def ShowFullScreen(*args, **kwargs):
        return _windows_.TopLevelWindow_ShowFullScreen(*args, **kwargs)

    def IsFullScreen(*args, **kwargs):
        return _windows_.TopLevelWindow_IsFullScreen(*args, **kwargs)

    def SetTitle(*args, **kwargs):
        return _windows_.TopLevelWindow_SetTitle(*args, **kwargs)

    def GetTitle(*args, **kwargs):
        return _windows_.TopLevelWindow_GetTitle(*args, **kwargs)

    def EnableCloseButton(*args, **kwargs):
        return _windows_.TopLevelWindow_EnableCloseButton(*args, **kwargs)

    def SetShape(*args, **kwargs):
        return _windows_.TopLevelWindow_SetShape(*args, **kwargs)

    def RequestUserAttention(*args, **kwargs):
        return _windows_.TopLevelWindow_RequestUserAttention(*args, **kwargs)

    def IsActive(*args, **kwargs):
        return _windows_.TopLevelWindow_IsActive(*args, **kwargs)

    def MacSetMetalAppearance(*args, **kwargs):
        return _windows_.TopLevelWindow_MacSetMetalAppearance(*args, **kwargs)

    def MacGetMetalAppearance(*args, **kwargs):
        return _windows_.TopLevelWindow_MacGetMetalAppearance(*args, **kwargs)

    def MacGetUnifiedAppearance(*args, **kwargs):
        return _windows_.TopLevelWindow_MacGetUnifiedAppearance(*args, **kwargs)

    def MacGetTopLevelWindowRef(*args, **kwargs):
        return _windows_.TopLevelWindow_MacGetTopLevelWindowRef(*args, **kwargs)

    def CenterOnScreen(*args, **kwargs):
        return _windows_.TopLevelWindow_CenterOnScreen(*args, **kwargs)

    CentreOnScreen = CenterOnScreen

    def GetDefaultItem(*args, **kwargs):
        return _windows_.TopLevelWindow_GetDefaultItem(*args, **kwargs)

    def SetDefaultItem(*args, **kwargs):
        return _windows_.TopLevelWindow_SetDefaultItem(*args, **kwargs)

    def SetTmpDefaultItem(*args, **kwargs):
        return _windows_.TopLevelWindow_SetTmpDefaultItem(*args, **kwargs)

    def GetTmpDefaultItem(*args, **kwargs):
        return _windows_.TopLevelWindow_GetTmpDefaultItem(*args, **kwargs)

    DefaultItem = property(GetDefaultItem, SetDefaultItem, doc='See `GetDefaultItem` and `SetDefaultItem`')
    Icon = property(GetIcon, SetIcon, doc='See `GetIcon` and `SetIcon`')
    Title = property(GetTitle, SetTitle, doc='See `GetTitle` and `SetTitle`')
    TmpDefaultItem = property(GetTmpDefaultItem, SetTmpDefaultItem, doc='See `GetTmpDefaultItem` and `SetTmpDefaultItem`')


_windows_.TopLevelWindow_swigregister(TopLevelWindow)
cvar = _windows_.cvar
FrameNameStr = cvar.FrameNameStr
DialogNameStr = cvar.DialogNameStr
StatusLineNameStr = cvar.StatusLineNameStr
ToolBarNameStr = cvar.ToolBarNameStr

class Frame(TopLevelWindow):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.Frame_swiginit(self, _windows_.new_Frame(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.Frame_Create(*args, **kwargs)

    def SendSizeEvent(*args, **kwargs):
        return _windows_.Frame_SendSizeEvent(*args, **kwargs)

    def SetMenuBar(*args, **kwargs):
        return _windows_.Frame_SetMenuBar(*args, **kwargs)

    def GetMenuBar(*args, **kwargs):
        return _windows_.Frame_GetMenuBar(*args, **kwargs)

    def ProcessCommand(*args, **kwargs):
        return _windows_.Frame_ProcessCommand(*args, **kwargs)

    Command = ProcessCommand

    def CreateStatusBar(*args, **kwargs):
        return _windows_.Frame_CreateStatusBar(*args, **kwargs)

    def GetStatusBar(*args, **kwargs):
        return _windows_.Frame_GetStatusBar(*args, **kwargs)

    def SetStatusBar(*args, **kwargs):
        return _windows_.Frame_SetStatusBar(*args, **kwargs)

    def SetStatusText(*args, **kwargs):
        return _windows_.Frame_SetStatusText(*args, **kwargs)

    def SetStatusWidths(*args, **kwargs):
        return _windows_.Frame_SetStatusWidths(*args, **kwargs)

    def PushStatusText(*args, **kwargs):
        return _windows_.Frame_PushStatusText(*args, **kwargs)

    def PopStatusText(*args, **kwargs):
        return _windows_.Frame_PopStatusText(*args, **kwargs)

    def SetStatusBarPane(*args, **kwargs):
        return _windows_.Frame_SetStatusBarPane(*args, **kwargs)

    def GetStatusBarPane(*args, **kwargs):
        return _windows_.Frame_GetStatusBarPane(*args, **kwargs)

    def CreateToolBar(*args, **kwargs):
        return _windows_.Frame_CreateToolBar(*args, **kwargs)

    def GetToolBar(*args, **kwargs):
        return _windows_.Frame_GetToolBar(*args, **kwargs)

    def SetToolBar(*args, **kwargs):
        return _windows_.Frame_SetToolBar(*args, **kwargs)

    def DoGiveHelp(*args, **kwargs):
        return _windows_.Frame_DoGiveHelp(*args, **kwargs)

    def DoMenuUpdates(*args, **kwargs):
        return _windows_.Frame_DoMenuUpdates(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _windows_.Frame_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    MenuBar = property(GetMenuBar, SetMenuBar, doc='See `GetMenuBar` and `SetMenuBar`')
    StatusBar = property(GetStatusBar, SetStatusBar, doc='See `GetStatusBar` and `SetStatusBar`')
    StatusBarPane = property(GetStatusBarPane, SetStatusBarPane, doc='See `GetStatusBarPane` and `SetStatusBarPane`')
    ToolBar = property(GetToolBar, SetToolBar, doc='See `GetToolBar` and `SetToolBar`')


_windows_.Frame_swigregister(Frame)

def PreFrame(*args, **kwargs):
    val = _windows_.new_PreFrame(*args, **kwargs)
    return val


def Frame_GetClassDefaultAttributes(*args, **kwargs):
    return _windows_.Frame_GetClassDefaultAttributes(*args, **kwargs)


class Dialog(TopLevelWindow):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    ButtonSizerFlags = _windows_.Dialog_ButtonSizerFlags

    def __init__(self, *args, **kwargs):
        _windows_.Dialog_swiginit(self, _windows_.new_Dialog(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.Dialog_Create(*args, **kwargs)

    def SetReturnCode(*args, **kwargs):
        return _windows_.Dialog_SetReturnCode(*args, **kwargs)

    def GetReturnCode(*args, **kwargs):
        return _windows_.Dialog_GetReturnCode(*args, **kwargs)

    def SetAffirmativeId(*args, **kwargs):
        return _windows_.Dialog_SetAffirmativeId(*args, **kwargs)

    def GetAffirmativeId(*args, **kwargs):
        return _windows_.Dialog_GetAffirmativeId(*args, **kwargs)

    def SetEscapeId(*args, **kwargs):
        return _windows_.Dialog_SetEscapeId(*args, **kwargs)

    def GetEscapeId(*args, **kwargs):
        return _windows_.Dialog_GetEscapeId(*args, **kwargs)

    def CreateTextSizer(*args, **kwargs):
        return _windows_.Dialog_CreateTextSizer(*args, **kwargs)

    def _CreateButtonSizer(*args, **kwargs):
        return _windows_.Dialog__CreateButtonSizer(*args, **kwargs)

    def CreateButtonSizer(self, flags, *ignored):
        return self._CreateButtonSizer(flags)

    def CreateSeparatedButtonSizer(*args, **kwargs):
        return _windows_.Dialog_CreateSeparatedButtonSizer(*args, **kwargs)

    def CreateStdDialogButtonSizer(*args, **kwargs):
        return _windows_.Dialog_CreateStdDialogButtonSizer(*args, **kwargs)

    def IsModal(*args, **kwargs):
        return _windows_.Dialog_IsModal(*args, **kwargs)

    def ShowModal(*args, **kwargs):
        return _windows_.Dialog_ShowModal(*args, **kwargs)

    def EndModal(*args, **kwargs):
        return _windows_.Dialog_EndModal(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _windows_.Dialog_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    AffirmativeId = property(GetAffirmativeId, SetAffirmativeId, doc='See `GetAffirmativeId` and `SetAffirmativeId`')
    EscapeId = property(GetEscapeId, SetEscapeId, doc='See `GetEscapeId` and `SetEscapeId`')
    ReturnCode = property(GetReturnCode, SetReturnCode, doc='See `GetReturnCode` and `SetReturnCode`')


_windows_.Dialog_swigregister(Dialog)

def PreDialog(*args, **kwargs):
    val = _windows_.new_PreDialog(*args, **kwargs)
    return val


def Dialog_GetClassDefaultAttributes(*args, **kwargs):
    return _windows_.Dialog_GetClassDefaultAttributes(*args, **kwargs)


SB_NORMAL = _windows_.SB_NORMAL
SB_FLAT = _windows_.SB_FLAT
SB_RAISED = _windows_.SB_RAISED

class StatusBar(_core.Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.StatusBar_swiginit(self, _windows_.new_StatusBar(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.StatusBar_Create(*args, **kwargs)

    def SetFieldsCount(*args, **kwargs):
        return _windows_.StatusBar_SetFieldsCount(*args, **kwargs)

    def GetFieldsCount(*args, **kwargs):
        return _windows_.StatusBar_GetFieldsCount(*args, **kwargs)

    def SetStatusText(*args, **kwargs):
        return _windows_.StatusBar_SetStatusText(*args, **kwargs)

    def GetStatusText(*args, **kwargs):
        return _windows_.StatusBar_GetStatusText(*args, **kwargs)

    def PushStatusText(*args, **kwargs):
        return _windows_.StatusBar_PushStatusText(*args, **kwargs)

    def PopStatusText(*args, **kwargs):
        return _windows_.StatusBar_PopStatusText(*args, **kwargs)

    def SetStatusWidths(*args, **kwargs):
        return _windows_.StatusBar_SetStatusWidths(*args, **kwargs)

    def SetStatusStyles(*args, **kwargs):
        return _windows_.StatusBar_SetStatusStyles(*args, **kwargs)

    def GetFieldRect(*args, **kwargs):
        return _windows_.StatusBar_GetFieldRect(*args, **kwargs)

    def SetMinHeight(*args, **kwargs):
        return _windows_.StatusBar_SetMinHeight(*args, **kwargs)

    def GetBorderX(*args, **kwargs):
        return _windows_.StatusBar_GetBorderX(*args, **kwargs)

    def GetBorderY(*args, **kwargs):
        return _windows_.StatusBar_GetBorderY(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _windows_.StatusBar_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)

    def GetFields(self):
        return [ self.GetStatusText(i) for i in range(self.GetFieldsCount()) ]

    def SetFields(self, items):
        self.SetFieldsCount(len(items))
        for i in range(len(items)):
            self.SetStatusText(items[i], i)

    BorderX = property(GetBorderX, doc='See `GetBorderX`')
    BorderY = property(GetBorderY, doc='See `GetBorderY`')
    FieldRect = property(GetFieldRect, doc='See `GetFieldRect`')
    Fields = property(GetFields, SetFields, doc='See `GetFields` and `SetFields`')
    FieldsCount = property(GetFieldsCount, SetFieldsCount, doc='See `GetFieldsCount` and `SetFieldsCount`')
    StatusText = property(GetStatusText, SetStatusText, doc='See `GetStatusText` and `SetStatusText`')


_windows_.StatusBar_swigregister(StatusBar)

def PreStatusBar(*args, **kwargs):
    val = _windows_.new_PreStatusBar(*args, **kwargs)
    return val


def StatusBar_GetClassDefaultAttributes(*args, **kwargs):
    return _windows_.StatusBar_GetClassDefaultAttributes(*args, **kwargs)


SP_NOBORDER = _windows_.SP_NOBORDER
SP_NOSASH = _windows_.SP_NOSASH
SP_PERMIT_UNSPLIT = _windows_.SP_PERMIT_UNSPLIT
SP_LIVE_UPDATE = _windows_.SP_LIVE_UPDATE
SP_3DSASH = _windows_.SP_3DSASH
SP_3DBORDER = _windows_.SP_3DBORDER
SP_NO_XP_THEME = _windows_.SP_NO_XP_THEME
SP_BORDER = _windows_.SP_BORDER
SP_3D = _windows_.SP_3D
SPLIT_HORIZONTAL = _windows_.SPLIT_HORIZONTAL
SPLIT_VERTICAL = _windows_.SPLIT_VERTICAL
SPLIT_DRAG_NONE = _windows_.SPLIT_DRAG_NONE
SPLIT_DRAG_DRAGGING = _windows_.SPLIT_DRAG_DRAGGING
SPLIT_DRAG_LEFT_DOWN = _windows_.SPLIT_DRAG_LEFT_DOWN

class SplitterWindow(_core.Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('point'):
            kwargs['pos'] = kwargs['point']
            del kwargs['point']
        _windows_.SplitterWindow_swiginit(self, _windows_.new_SplitterWindow(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.SplitterWindow_Create(*args, **kwargs)

    def GetWindow1(*args, **kwargs):
        return _windows_.SplitterWindow_GetWindow1(*args, **kwargs)

    def GetWindow2(*args, **kwargs):
        return _windows_.SplitterWindow_GetWindow2(*args, **kwargs)

    def SetSplitMode(*args, **kwargs):
        return _windows_.SplitterWindow_SetSplitMode(*args, **kwargs)

    def GetSplitMode(*args, **kwargs):
        return _windows_.SplitterWindow_GetSplitMode(*args, **kwargs)

    def Initialize(*args, **kwargs):
        return _windows_.SplitterWindow_Initialize(*args, **kwargs)

    def SplitVertically(*args, **kwargs):
        return _windows_.SplitterWindow_SplitVertically(*args, **kwargs)

    def SplitHorizontally(*args, **kwargs):
        return _windows_.SplitterWindow_SplitHorizontally(*args, **kwargs)

    def Unsplit(*args, **kwargs):
        return _windows_.SplitterWindow_Unsplit(*args, **kwargs)

    def ReplaceWindow(*args, **kwargs):
        return _windows_.SplitterWindow_ReplaceWindow(*args, **kwargs)

    def UpdateSize(*args, **kwargs):
        return _windows_.SplitterWindow_UpdateSize(*args, **kwargs)

    def IsSplit(*args, **kwargs):
        return _windows_.SplitterWindow_IsSplit(*args, **kwargs)

    def SetSashSize(*args, **kwargs):
        return _windows_.SplitterWindow_SetSashSize(*args, **kwargs)

    def SetBorderSize(*args, **kwargs):
        return _windows_.SplitterWindow_SetBorderSize(*args, **kwargs)

    def GetSashSize(*args, **kwargs):
        return _windows_.SplitterWindow_GetSashSize(*args, **kwargs)

    def GetBorderSize(*args, **kwargs):
        return _windows_.SplitterWindow_GetBorderSize(*args, **kwargs)

    def SetSashPosition(*args, **kwargs):
        return _windows_.SplitterWindow_SetSashPosition(*args, **kwargs)

    def GetSashPosition(*args, **kwargs):
        return _windows_.SplitterWindow_GetSashPosition(*args, **kwargs)

    def SetSashGravity(*args, **kwargs):
        return _windows_.SplitterWindow_SetSashGravity(*args, **kwargs)

    def GetSashGravity(*args, **kwargs):
        return _windows_.SplitterWindow_GetSashGravity(*args, **kwargs)

    def SetMinimumPaneSize(*args, **kwargs):
        return _windows_.SplitterWindow_SetMinimumPaneSize(*args, **kwargs)

    def GetMinimumPaneSize(*args, **kwargs):
        return _windows_.SplitterWindow_GetMinimumPaneSize(*args, **kwargs)

    def SashHitTest(*args, **kwargs):
        return _windows_.SplitterWindow_SashHitTest(*args, **kwargs)

    def SizeWindows(*args, **kwargs):
        return _windows_.SplitterWindow_SizeWindows(*args, **kwargs)

    def SetNeedUpdating(*args, **kwargs):
        return _windows_.SplitterWindow_SetNeedUpdating(*args, **kwargs)

    def GetNeedUpdating(*args, **kwargs):
        return _windows_.SplitterWindow_GetNeedUpdating(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _windows_.SplitterWindow_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    BorderSize = property(GetBorderSize, SetBorderSize, doc='See `GetBorderSize` and `SetBorderSize`')
    MinimumPaneSize = property(GetMinimumPaneSize, SetMinimumPaneSize, doc='See `GetMinimumPaneSize` and `SetMinimumPaneSize`')
    NeedUpdating = property(GetNeedUpdating, SetNeedUpdating, doc='See `GetNeedUpdating` and `SetNeedUpdating`')
    SashGravity = property(GetSashGravity, SetSashGravity, doc='See `GetSashGravity` and `SetSashGravity`')
    SashPosition = property(GetSashPosition, SetSashPosition, doc='See `GetSashPosition` and `SetSashPosition`')
    SashSize = property(GetSashSize, SetSashSize, doc='See `GetSashSize` and `SetSashSize`')
    SplitMode = property(GetSplitMode, SetSplitMode, doc='See `GetSplitMode` and `SetSplitMode`')
    Window1 = property(GetWindow1, doc='See `GetWindow1`')
    Window2 = property(GetWindow2, doc='See `GetWindow2`')


_windows_.SplitterWindow_swigregister(SplitterWindow)
SplitterNameStr = cvar.SplitterNameStr

def PreSplitterWindow(*args, **kwargs):
    val = _windows_.new_PreSplitterWindow(*args, **kwargs)
    return val


def SplitterWindow_GetClassDefaultAttributes(*args, **kwargs):
    return _windows_.SplitterWindow_GetClassDefaultAttributes(*args, **kwargs)


class SplitterEvent(_core.NotifyEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.SplitterEvent_swiginit(self, _windows_.new_SplitterEvent(*args, **kwargs))

    def SetSashPosition(*args, **kwargs):
        return _windows_.SplitterEvent_SetSashPosition(*args, **kwargs)

    def GetSashPosition(*args, **kwargs):
        return _windows_.SplitterEvent_GetSashPosition(*args, **kwargs)

    def GetWindowBeingRemoved(*args, **kwargs):
        return _windows_.SplitterEvent_GetWindowBeingRemoved(*args, **kwargs)

    def GetX(*args, **kwargs):
        return _windows_.SplitterEvent_GetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _windows_.SplitterEvent_GetY(*args, **kwargs)

    SashPosition = property(GetSashPosition, SetSashPosition, doc='See `GetSashPosition` and `SetSashPosition`')
    WindowBeingRemoved = property(GetWindowBeingRemoved, doc='See `GetWindowBeingRemoved`')
    X = property(GetX, doc='See `GetX`')
    Y = property(GetY, doc='See `GetY`')


_windows_.SplitterEvent_swigregister(SplitterEvent)
wxEVT_COMMAND_SPLITTER_SASH_POS_CHANGED = _windows_.wxEVT_COMMAND_SPLITTER_SASH_POS_CHANGED
wxEVT_COMMAND_SPLITTER_SASH_POS_CHANGING = _windows_.wxEVT_COMMAND_SPLITTER_SASH_POS_CHANGING
wxEVT_COMMAND_SPLITTER_DOUBLECLICKED = _windows_.wxEVT_COMMAND_SPLITTER_DOUBLECLICKED
wxEVT_COMMAND_SPLITTER_UNSPLIT = _windows_.wxEVT_COMMAND_SPLITTER_UNSPLIT
EVT_SPLITTER_SASH_POS_CHANGED = wx.PyEventBinder(wxEVT_COMMAND_SPLITTER_SASH_POS_CHANGED, 1)
EVT_SPLITTER_SASH_POS_CHANGING = wx.PyEventBinder(wxEVT_COMMAND_SPLITTER_SASH_POS_CHANGING, 1)
EVT_SPLITTER_DOUBLECLICKED = wx.PyEventBinder(wxEVT_COMMAND_SPLITTER_DOUBLECLICKED, 1)
EVT_SPLITTER_UNSPLIT = wx.PyEventBinder(wxEVT_COMMAND_SPLITTER_UNSPLIT, 1)
EVT_SPLITTER_DCLICK = EVT_SPLITTER_DOUBLECLICKED

class PopupWindow(_core.Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.PopupWindow_swiginit(self, _windows_.new_PopupWindow(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _windows_.PopupWindow_Create(*args, **kwargs)

    def Position(*args, **kwargs):
        return _windows_.PopupWindow_Position(*args, **kwargs)


_windows_.PopupWindow_swigregister(PopupWindow)

def PrePopupWindow(*args, **kwargs):
    val = _windows_.new_PrePopupWindow(*args, **kwargs)
    return val


class PopupTransientWindow(PopupWindow):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.PopupTransientWindow_swiginit(self, _windows_.new_PopupTransientWindow(*args, **kwargs))
        self._setOORInfo(self)
        PopupTransientWindow._setCallbackInfo(self, self, PopupTransientWindow)

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.PopupTransientWindow__setCallbackInfo(*args, **kwargs)

    def Popup(*args, **kwargs):
        return _windows_.PopupTransientWindow_Popup(*args, **kwargs)

    def Dismiss(*args, **kwargs):
        return _windows_.PopupTransientWindow_Dismiss(*args, **kwargs)


_windows_.PopupTransientWindow_swigregister(PopupTransientWindow)

def PrePopupTransientWindow(*args, **kwargs):
    val = _windows_.new_PrePopupTransientWindow(*args, **kwargs)
    return val


class TipWindow(PopupTransientWindow):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.TipWindow_swiginit(self, _windows_.new_TipWindow(*args, **kwargs))
        self._setOORInfo(self)

    def SetBoundingRect(*args, **kwargs):
        return _windows_.TipWindow_SetBoundingRect(*args, **kwargs)

    def Close(*args, **kwargs):
        return _windows_.TipWindow_Close(*args, **kwargs)


_windows_.TipWindow_swigregister(TipWindow)

class VScrolledWindow(Panel):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.VScrolledWindow_swiginit(self, _windows_.new_VScrolledWindow(*args, **kwargs))
        self._setOORInfo(self)
        VScrolledWindow._setCallbackInfo(self, self, VScrolledWindow)

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.VScrolledWindow__setCallbackInfo(*args, **kwargs)

    def Create(*args, **kwargs):
        return _windows_.VScrolledWindow_Create(*args, **kwargs)

    def SetLineCount(*args, **kwargs):
        return _windows_.VScrolledWindow_SetLineCount(*args, **kwargs)

    def ScrollToLine(*args, **kwargs):
        return _windows_.VScrolledWindow_ScrollToLine(*args, **kwargs)

    def RefreshLine(*args, **kwargs):
        return _windows_.VScrolledWindow_RefreshLine(*args, **kwargs)

    def RefreshLines(*args, **kwargs):
        return _windows_.VScrolledWindow_RefreshLines(*args, **kwargs)

    def HitTestXY(*args, **kwargs):
        return _windows_.VScrolledWindow_HitTestXY(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _windows_.VScrolledWindow_HitTest(*args, **kwargs)

    def RefreshAll(*args, **kwargs):
        return _windows_.VScrolledWindow_RefreshAll(*args, **kwargs)

    def GetLineCount(*args, **kwargs):
        return _windows_.VScrolledWindow_GetLineCount(*args, **kwargs)

    def GetVisibleBegin(*args, **kwargs):
        return _windows_.VScrolledWindow_GetVisibleBegin(*args, **kwargs)

    def GetVisibleEnd(*args, **kwargs):
        return _windows_.VScrolledWindow_GetVisibleEnd(*args, **kwargs)

    def IsVisible(*args, **kwargs):
        return _windows_.VScrolledWindow_IsVisible(*args, **kwargs)

    def GetFirstVisibleLine(*args, **kwargs):
        return _windows_.VScrolledWindow_GetFirstVisibleLine(*args, **kwargs)

    def GetLastVisibleLine(*args, **kwargs):
        return _windows_.VScrolledWindow_GetLastVisibleLine(*args, **kwargs)

    def FindFirstFromBottom(*args, **kwargs):
        return _windows_.VScrolledWindow_FindFirstFromBottom(*args, **kwargs)

    def GetLinesHeight(*args, **kwargs):
        return _windows_.VScrolledWindow_GetLinesHeight(*args, **kwargs)

    FirstVisibleLine = property(GetFirstVisibleLine, doc='See `GetFirstVisibleLine`')
    LastVisibleLine = property(GetLastVisibleLine, doc='See `GetLastVisibleLine`')
    LineCount = property(GetLineCount, SetLineCount, doc='See `GetLineCount` and `SetLineCount`')
    VisibleBegin = property(GetVisibleBegin, doc='See `GetVisibleBegin`')
    VisibleEnd = property(GetVisibleEnd, doc='See `GetVisibleEnd`')


_windows_.VScrolledWindow_swigregister(VScrolledWindow)

def PreVScrolledWindow(*args, **kwargs):
    val = _windows_.new_PreVScrolledWindow(*args, **kwargs)
    return val


class VListBox(VScrolledWindow):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.VListBox_swiginit(self, _windows_.new_VListBox(*args, **kwargs))
        self._setOORInfo(self)
        VListBox._setCallbackInfo(self, self, VListBox)

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.VListBox__setCallbackInfo(*args, **kwargs)

    def Create(*args, **kwargs):
        return _windows_.VListBox_Create(*args, **kwargs)

    def GetItemCount(*args, **kwargs):
        return _windows_.VListBox_GetItemCount(*args, **kwargs)

    def HasMultipleSelection(*args, **kwargs):
        return _windows_.VListBox_HasMultipleSelection(*args, **kwargs)

    def GetSelection(*args, **kwargs):
        return _windows_.VListBox_GetSelection(*args, **kwargs)

    def IsCurrent(*args, **kwargs):
        return _windows_.VListBox_IsCurrent(*args, **kwargs)

    def IsSelected(*args, **kwargs):
        return _windows_.VListBox_IsSelected(*args, **kwargs)

    def GetSelectedCount(*args, **kwargs):
        return _windows_.VListBox_GetSelectedCount(*args, **kwargs)

    def GetFirstSelected(*args, **kwargs):
        return _windows_.VListBox_GetFirstSelected(*args, **kwargs)

    def GetNextSelected(*args, **kwargs):
        return _windows_.VListBox_GetNextSelected(*args, **kwargs)

    def GetMargins(*args, **kwargs):
        return _windows_.VListBox_GetMargins(*args, **kwargs)

    def GetSelectionBackground(*args, **kwargs):
        return _windows_.VListBox_GetSelectionBackground(*args, **kwargs)

    def SetItemCount(*args, **kwargs):
        return _windows_.VListBox_SetItemCount(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _windows_.VListBox_Clear(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _windows_.VListBox_SetSelection(*args, **kwargs)

    def Select(*args, **kwargs):
        return _windows_.VListBox_Select(*args, **kwargs)

    def SelectRange(*args, **kwargs):
        return _windows_.VListBox_SelectRange(*args, **kwargs)

    def Toggle(*args, **kwargs):
        return _windows_.VListBox_Toggle(*args, **kwargs)

    def SelectAll(*args, **kwargs):
        return _windows_.VListBox_SelectAll(*args, **kwargs)

    def DeselectAll(*args, **kwargs):
        return _windows_.VListBox_DeselectAll(*args, **kwargs)

    def SetMargins(*args, **kwargs):
        return _windows_.VListBox_SetMargins(*args, **kwargs)

    def SetMarginsXY(*args, **kwargs):
        return _windows_.VListBox_SetMarginsXY(*args, **kwargs)

    def SetSelectionBackground(*args, **kwargs):
        return _windows_.VListBox_SetSelectionBackground(*args, **kwargs)

    def OnDrawSeparator(*args, **kwargs):
        return _windows_.VListBox_OnDrawSeparator(*args, **kwargs)

    def OnDrawBackground(*args, **kwargs):
        return _windows_.VListBox_OnDrawBackground(*args, **kwargs)

    FirstSelected = property(GetFirstSelected, doc='See `GetFirstSelected`')
    ItemCount = property(GetItemCount, SetItemCount, doc='See `GetItemCount` and `SetItemCount`')
    Margins = property(GetMargins, SetMargins, doc='See `GetMargins` and `SetMargins`')
    SelectedCount = property(GetSelectedCount, doc='See `GetSelectedCount`')
    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')
    SelectionBackground = property(GetSelectionBackground, SetSelectionBackground, doc='See `GetSelectionBackground` and `SetSelectionBackground`')


_windows_.VListBox_swigregister(VListBox)
VListBoxNameStr = cvar.VListBoxNameStr

def PreVListBox(*args, **kwargs):
    val = _windows_.new_PreVListBox(*args, **kwargs)
    return val


class TaskBarIcon(_core.EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.TaskBarIcon_swiginit(self, _windows_.new_TaskBarIcon(*args, **kwargs))
        TaskBarIcon._setCallbackInfo(self, self, TaskBarIcon)

    __swig_destroy__ = _windows_.delete_TaskBarIcon
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.TaskBarIcon__setCallbackInfo(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _windows_.TaskBarIcon_Destroy(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _windows_.TaskBarIcon_IsOk(*args, **kwargs)

    def __nonzero__(self):
        return self.IsOk()

    def GetScreenRect(*args, **kwargs):
        return _windows_.TaskBarIcon_GetScreenRect(*args, **kwargs)

    def IsIconInstalled(*args, **kwargs):
        return _windows_.TaskBarIcon_IsIconInstalled(*args, **kwargs)

    def SetIcon(*args, **kwargs):
        return _windows_.TaskBarIcon_SetIcon(*args, **kwargs)

    def RemoveIcon(*args, **kwargs):
        return _windows_.TaskBarIcon_RemoveIcon(*args, **kwargs)

    def PopupMenu(*args, **kwargs):
        return _windows_.TaskBarIcon_PopupMenu(*args, **kwargs)


_windows_.TaskBarIcon_swigregister(TaskBarIcon)

class TaskBarIconEvent(_core.Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.TaskBarIconEvent_swiginit(self, _windows_.new_TaskBarIconEvent(*args, **kwargs))


_windows_.TaskBarIconEvent_swigregister(TaskBarIconEvent)
wxEVT_TASKBAR_MOVE = _windows_.wxEVT_TASKBAR_MOVE
wxEVT_TASKBAR_LEFT_DOWN = _windows_.wxEVT_TASKBAR_LEFT_DOWN
wxEVT_TASKBAR_LEFT_UP = _windows_.wxEVT_TASKBAR_LEFT_UP
wxEVT_TASKBAR_RIGHT_DOWN = _windows_.wxEVT_TASKBAR_RIGHT_DOWN
wxEVT_TASKBAR_RIGHT_UP = _windows_.wxEVT_TASKBAR_RIGHT_UP
wxEVT_TASKBAR_LEFT_DCLICK = _windows_.wxEVT_TASKBAR_LEFT_DCLICK
wxEVT_TASKBAR_RIGHT_DCLICK = _windows_.wxEVT_TASKBAR_RIGHT_DCLICK
wxEVT_TASKBAR_CLICK = _windows_.wxEVT_TASKBAR_CLICK
EVT_TASKBAR_MOVE = wx.PyEventBinder(wxEVT_TASKBAR_MOVE)
EVT_TASKBAR_LEFT_DOWN = wx.PyEventBinder(wxEVT_TASKBAR_LEFT_DOWN)
EVT_TASKBAR_LEFT_UP = wx.PyEventBinder(wxEVT_TASKBAR_LEFT_UP)
EVT_TASKBAR_RIGHT_DOWN = wx.PyEventBinder(wxEVT_TASKBAR_RIGHT_DOWN)
EVT_TASKBAR_RIGHT_UP = wx.PyEventBinder(wxEVT_TASKBAR_RIGHT_UP)
EVT_TASKBAR_LEFT_DCLICK = wx.PyEventBinder(wxEVT_TASKBAR_LEFT_DCLICK)
EVT_TASKBAR_RIGHT_DCLICK = wx.PyEventBinder(wxEVT_TASKBAR_RIGHT_DCLICK)
EVT_TASKBAR_CLICK = wx.PyEventBinder(wxEVT_TASKBAR_CLICK)
DD_CHANGE_DIR = _windows_.DD_CHANGE_DIR
DD_DIR_MUST_EXIST = _windows_.DD_DIR_MUST_EXIST
DD_NEW_DIR_BUTTON = _windows_.DD_NEW_DIR_BUTTON
DD_DEFAULT_STYLE = _windows_.DD_DEFAULT_STYLE

class DirDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.DirDialog_swiginit(self, _windows_.new_DirDialog(*args, **kwargs))
        self._setOORInfo(self)

    def GetPath(*args, **kwargs):
        return _windows_.DirDialog_GetPath(*args, **kwargs)

    def GetMessage(*args, **kwargs):
        return _windows_.DirDialog_GetMessage(*args, **kwargs)

    def SetMessage(*args, **kwargs):
        return _windows_.DirDialog_SetMessage(*args, **kwargs)

    def SetPath(*args, **kwargs):
        return _windows_.DirDialog_SetPath(*args, **kwargs)

    Message = property(GetMessage, SetMessage, doc='See `GetMessage` and `SetMessage`')
    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')


_windows_.DirDialog_swigregister(DirDialog)
FileSelectorPromptStr = cvar.FileSelectorPromptStr
DirSelectorPromptStr = cvar.DirSelectorPromptStr
DirDialogNameStr = cvar.DirDialogNameStr
FileSelectorDefaultWildcardStr = cvar.FileSelectorDefaultWildcardStr
GetTextFromUserPromptStr = cvar.GetTextFromUserPromptStr
MessageBoxCaptionStr = cvar.MessageBoxCaptionStr
OPEN = _windows_.OPEN
SAVE = _windows_.SAVE
OVERWRITE_PROMPT = _windows_.OVERWRITE_PROMPT
FILE_MUST_EXIST = _windows_.FILE_MUST_EXIST
MULTIPLE = _windows_.MULTIPLE
CHANGE_DIR = _windows_.CHANGE_DIR
HIDE_READONLY = _windows_.HIDE_READONLY
FD_OPEN = _windows_.FD_OPEN
FD_SAVE = _windows_.FD_SAVE
FD_OVERWRITE_PROMPT = _windows_.FD_OVERWRITE_PROMPT
FD_FILE_MUST_EXIST = _windows_.FD_FILE_MUST_EXIST
FD_MULTIPLE = _windows_.FD_MULTIPLE
FD_CHANGE_DIR = _windows_.FD_CHANGE_DIR
FD_PREVIEW = _windows_.FD_PREVIEW
FD_DEFAULT_STYLE = _windows_.FD_DEFAULT_STYLE

class FileDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.FileDialog_swiginit(self, _windows_.new_FileDialog(*args, **kwargs))
        self._setOORInfo(self)

    def SetMessage(*args, **kwargs):
        return _windows_.FileDialog_SetMessage(*args, **kwargs)

    def SetPath(*args, **kwargs):
        return _windows_.FileDialog_SetPath(*args, **kwargs)

    def SetDirectory(*args, **kwargs):
        return _windows_.FileDialog_SetDirectory(*args, **kwargs)

    def SetFilename(*args, **kwargs):
        return _windows_.FileDialog_SetFilename(*args, **kwargs)

    def SetWildcard(*args, **kwargs):
        return _windows_.FileDialog_SetWildcard(*args, **kwargs)

    def SetFilterIndex(*args, **kwargs):
        return _windows_.FileDialog_SetFilterIndex(*args, **kwargs)

    def GetMessage(*args, **kwargs):
        return _windows_.FileDialog_GetMessage(*args, **kwargs)

    def GetPath(*args, **kwargs):
        return _windows_.FileDialog_GetPath(*args, **kwargs)

    def GetDirectory(*args, **kwargs):
        return _windows_.FileDialog_GetDirectory(*args, **kwargs)

    def GetFilename(*args, **kwargs):
        return _windows_.FileDialog_GetFilename(*args, **kwargs)

    def GetWildcard(*args, **kwargs):
        return _windows_.FileDialog_GetWildcard(*args, **kwargs)

    def GetFilterIndex(*args, **kwargs):
        return _windows_.FileDialog_GetFilterIndex(*args, **kwargs)

    def GetFilenames(*args, **kwargs):
        return _windows_.FileDialog_GetFilenames(*args, **kwargs)

    def GetPaths(*args, **kwargs):
        return _windows_.FileDialog_GetPaths(*args, **kwargs)

    Directory = property(GetDirectory, SetDirectory, doc='See `GetDirectory` and `SetDirectory`')
    Filename = property(GetFilename, SetFilename, doc='See `GetFilename` and `SetFilename`')
    Filenames = property(GetFilenames, doc='See `GetFilenames`')
    FilterIndex = property(GetFilterIndex, SetFilterIndex, doc='See `GetFilterIndex` and `SetFilterIndex`')
    Message = property(GetMessage, SetMessage, doc='See `GetMessage` and `SetMessage`')
    Path = property(GetPath, SetPath, doc='See `GetPath` and `SetPath`')
    Paths = property(GetPaths, doc='See `GetPaths`')
    Wildcard = property(GetWildcard, SetWildcard, doc='See `GetWildcard` and `SetWildcard`')


_windows_.FileDialog_swigregister(FileDialog)
CHOICEDLG_STYLE = _windows_.CHOICEDLG_STYLE

class MultiChoiceDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.MultiChoiceDialog_swiginit(self, _windows_.new_MultiChoiceDialog(*args, **kwargs))
        self._setOORInfo(self)

    def SetSelections(*args, **kwargs):
        return _windows_.MultiChoiceDialog_SetSelections(*args, **kwargs)

    def GetSelections(*args, **kwargs):
        return _windows_.MultiChoiceDialog_GetSelections(*args, **kwargs)

    Selections = property(GetSelections, SetSelections, doc='See `GetSelections` and `SetSelections`')


_windows_.MultiChoiceDialog_swigregister(MultiChoiceDialog)

class SingleChoiceDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.SingleChoiceDialog_swiginit(self, _windows_.new_SingleChoiceDialog(*args, **kwargs))
        self._setOORInfo(self)

    def GetSelection(*args, **kwargs):
        return _windows_.SingleChoiceDialog_GetSelection(*args, **kwargs)

    def GetStringSelection(*args, **kwargs):
        return _windows_.SingleChoiceDialog_GetStringSelection(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _windows_.SingleChoiceDialog_SetSelection(*args, **kwargs)

    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')
    StringSelection = property(GetStringSelection, doc='See `GetStringSelection`')


_windows_.SingleChoiceDialog_swigregister(SingleChoiceDialog)
TextEntryDialogStyle = _windows_.TextEntryDialogStyle

class TextEntryDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.TextEntryDialog_swiginit(self, _windows_.new_TextEntryDialog(*args, **kwargs))
        self._setOORInfo(self)

    def GetValue(*args, **kwargs):
        return _windows_.TextEntryDialog_GetValue(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _windows_.TextEntryDialog_SetValue(*args, **kwargs)

    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_windows_.TextEntryDialog_swigregister(TextEntryDialog)

class PasswordEntryDialog(TextEntryDialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.PasswordEntryDialog_swiginit(self, _windows_.new_PasswordEntryDialog(*args, **kwargs))


_windows_.PasswordEntryDialog_swigregister(PasswordEntryDialog)
GetPasswordFromUserPromptStr = cvar.GetPasswordFromUserPromptStr

class MessageDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.MessageDialog_swiginit(self, _windows_.new_MessageDialog(*args, **kwargs))
        self._setOORInfo(self)


_windows_.MessageDialog_swigregister(MessageDialog)
PD_AUTO_HIDE = _windows_.PD_AUTO_HIDE
PD_APP_MODAL = _windows_.PD_APP_MODAL
PD_CAN_ABORT = _windows_.PD_CAN_ABORT
PD_ELAPSED_TIME = _windows_.PD_ELAPSED_TIME
PD_ESTIMATED_TIME = _windows_.PD_ESTIMATED_TIME
PD_REMAINING_TIME = _windows_.PD_REMAINING_TIME
PD_SMOOTH = _windows_.PD_SMOOTH
PD_CAN_SKIP = _windows_.PD_CAN_SKIP

class ProgressDialog(Dialog):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.ProgressDialog_swiginit(self, _windows_.new_ProgressDialog(*args, **kwargs))
        self._setOORInfo(self)

    def Update(*args, **kwargs):
        return _windows_.ProgressDialog_Update(*args, **kwargs)

    def Pulse(*args, **kwargs):
        return _windows_.ProgressDialog_Pulse(*args, **kwargs)

    UpdatePulse = Pulse

    def Resume(*args, **kwargs):
        return _windows_.ProgressDialog_Resume(*args, **kwargs)


_windows_.ProgressDialog_swigregister(ProgressDialog)

class PyWindow(_core.Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.PyWindow_swiginit(self, _windows_.new_PyWindow(*args, **kwargs))
        self._setOORInfo(self)
        PyWindow._setCallbackInfo(self, self, PyWindow)

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.PyWindow__setCallbackInfo(*args, **kwargs)

    SetBestSize = wx.Window.SetInitialSize

    def DoEraseBackground(*args, **kwargs):
        return _windows_.PyWindow_DoEraseBackground(*args, **kwargs)

    def DoMoveWindow(*args, **kwargs):
        return _windows_.PyWindow_DoMoveWindow(*args, **kwargs)

    def DoSetSize(*args, **kwargs):
        return _windows_.PyWindow_DoSetSize(*args, **kwargs)

    def DoSetClientSize(*args, **kwargs):
        return _windows_.PyWindow_DoSetClientSize(*args, **kwargs)

    def DoSetVirtualSize(*args, **kwargs):
        return _windows_.PyWindow_DoSetVirtualSize(*args, **kwargs)

    def DoGetSize(*args, **kwargs):
        return _windows_.PyWindow_DoGetSize(*args, **kwargs)

    def DoGetClientSize(*args, **kwargs):
        return _windows_.PyWindow_DoGetClientSize(*args, **kwargs)

    def DoGetPosition(*args, **kwargs):
        return _windows_.PyWindow_DoGetPosition(*args, **kwargs)

    def DoGetVirtualSize(*args, **kwargs):
        return _windows_.PyWindow_DoGetVirtualSize(*args, **kwargs)

    def DoGetBestSize(*args, **kwargs):
        return _windows_.PyWindow_DoGetBestSize(*args, **kwargs)

    def InitDialog(*args, **kwargs):
        return _windows_.PyWindow_InitDialog(*args, **kwargs)

    def TransferDataToWindow(*args, **kwargs):
        return _windows_.PyWindow_TransferDataToWindow(*args, **kwargs)

    def TransferDataFromWindow(*args, **kwargs):
        return _windows_.PyWindow_TransferDataFromWindow(*args, **kwargs)

    def Validate(*args, **kwargs):
        return _windows_.PyWindow_Validate(*args, **kwargs)

    def GetDefaultAttributes(*args, **kwargs):
        return _windows_.PyWindow_GetDefaultAttributes(*args, **kwargs)

    def OnInternalIdle(*args, **kwargs):
        return _windows_.PyWindow_OnInternalIdle(*args, **kwargs)

    def base_DoMoveWindow(*args, **kw):
        return PyWindow.DoMoveWindow(*args, **kw)

    base_DoMoveWindow = wx._deprecated(base_DoMoveWindow, 'Please use PyWindow.DoMoveWindow instead.')

    def base_DoSetSize(*args, **kw):
        return PyWindow.DoSetSize(*args, **kw)

    base_DoSetSize = wx._deprecated(base_DoSetSize, 'Please use PyWindow.DoSetSize instead.')

    def base_DoSetClientSize(*args, **kw):
        return PyWindow.DoSetClientSize(*args, **kw)

    base_DoSetClientSize = wx._deprecated(base_DoSetClientSize, 'Please use PyWindow.DoSetClientSize instead.')

    def base_DoSetVirtualSize(*args, **kw):
        return PyWindow.DoSetVirtualSize(*args, **kw)

    base_DoSetVirtualSize = wx._deprecated(base_DoSetVirtualSize, 'Please use PyWindow.DoSetVirtualSize instead.')

    def base_DoGetSize(*args, **kw):
        return PyWindow.DoGetSize(*args, **kw)

    base_DoGetSize = wx._deprecated(base_DoGetSize, 'Please use PyWindow.DoGetSize instead.')

    def base_DoGetClientSize(*args, **kw):
        return PyWindow.DoGetClientSize(*args, **kw)

    base_DoGetClientSize = wx._deprecated(base_DoGetClientSize, 'Please use PyWindow.DoGetClientSize instead.')

    def base_DoGetPosition(*args, **kw):
        return PyWindow.DoGetPosition(*args, **kw)

    base_DoGetPosition = wx._deprecated(base_DoGetPosition, 'Please use PyWindow.DoGetPosition instead.')

    def base_DoGetVirtualSize(*args, **kw):
        return PyWindow.DoGetVirtualSize(*args, **kw)

    base_DoGetVirtualSize = wx._deprecated(base_DoGetVirtualSize, 'Please use PyWindow.DoGetVirtualSize instead.')

    def base_DoGetBestSize(*args, **kw):
        return PyWindow.DoGetBestSize(*args, **kw)

    base_DoGetBestSize = wx._deprecated(base_DoGetBestSize, 'Please use PyWindow.DoGetBestSize instead.')

    def base_InitDialog(*args, **kw):
        return PyWindow.InitDialog(*args, **kw)

    base_InitDialog = wx._deprecated(base_InitDialog, 'Please use PyWindow.InitDialog instead.')

    def base_TransferDataToWindow(*args, **kw):
        return PyWindow.TransferDataToWindow(*args, **kw)

    base_TransferDataToWindow = wx._deprecated(base_TransferDataToWindow, 'Please use PyWindow.TransferDataToWindow instead.')

    def base_TransferDataFromWindow(*args, **kw):
        return PyWindow.TransferDataFromWindow(*args, **kw)

    base_TransferDataFromWindow = wx._deprecated(base_TransferDataFromWindow, 'Please use PyWindow.TransferDataFromWindow instead.')

    def base_Validate(*args, **kw):
        return PyWindow.Validate(*args, **kw)

    base_Validate = wx._deprecated(base_Validate, 'Please use PyWindow.Validate instead.')

    def base_AcceptsFocus(*args, **kw):
        return PyWindow.AcceptsFocus(*args, **kw)

    base_AcceptsFocus = wx._deprecated(base_AcceptsFocus, 'Please use PyWindow.AcceptsFocus instead.')

    def base_AcceptsFocusFromKeyboard(*args, **kw):
        return PyWindow.AcceptsFocusFromKeyboard(*args, **kw)

    base_AcceptsFocusFromKeyboard = wx._deprecated(base_AcceptsFocusFromKeyboard, 'Please use PyWindow.AcceptsFocusFromKeyboard instead.')

    def base_GetMaxSize(*args, **kw):
        return PyWindow.GetMaxSize(*args, **kw)

    base_GetMaxSize = wx._deprecated(base_GetMaxSize, 'Please use PyWindow.GetMaxSize instead.')

    def base_AddChild(*args, **kw):
        return PyWindow.AddChild(*args, **kw)

    base_AddChild = wx._deprecated(base_AddChild, 'Please use PyWindow.AddChild instead.')

    def base_RemoveChild(*args, **kw):
        return PyWindow.RemoveChild(*args, **kw)

    base_RemoveChild = wx._deprecated(base_RemoveChild, 'Please use PyWindow.RemoveChild instead.')

    def base_ShouldInheritColours(*args, **kw):
        return PyWindow.ShouldInheritColours(*args, **kw)

    base_ShouldInheritColours = wx._deprecated(base_ShouldInheritColours, 'Please use PyWindow.ShouldInheritColours instead.')

    def base_GetDefaultAttributes(*args, **kw):
        return PyWindow.GetDefaultAttributes(*args, **kw)

    base_GetDefaultAttributes = wx._deprecated(base_GetDefaultAttributes, 'Please use PyWindow.GetDefaultAttributes instead.')

    def base_OnInternalIdle(*args, **kw):
        return PyWindow.OnInternalIdle(*args, **kw)

    base_OnInternalIdle = wx._deprecated(base_OnInternalIdle, 'Please use PyWindow.OnInternalIdle instead.')


_windows_.PyWindow_swigregister(PyWindow)

def PrePyWindow(*args, **kwargs):
    val = _windows_.new_PrePyWindow(*args, **kwargs)
    return val


class PyPanel(Panel):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.PyPanel_swiginit(self, _windows_.new_PyPanel(*args, **kwargs))
        self._setOORInfo(self)
        PyPanel._setCallbackInfo(self, self, PyPanel)

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.PyPanel__setCallbackInfo(*args, **kwargs)

    SetBestSize = wx.Window.SetInitialSize

    def DoEraseBackground(*args, **kwargs):
        return _windows_.PyPanel_DoEraseBackground(*args, **kwargs)

    def DoMoveWindow(*args, **kwargs):
        return _windows_.PyPanel_DoMoveWindow(*args, **kwargs)

    def DoSetSize(*args, **kwargs):
        return _windows_.PyPanel_DoSetSize(*args, **kwargs)

    def DoSetClientSize(*args, **kwargs):
        return _windows_.PyPanel_DoSetClientSize(*args, **kwargs)

    def DoSetVirtualSize(*args, **kwargs):
        return _windows_.PyPanel_DoSetVirtualSize(*args, **kwargs)

    def DoGetSize(*args, **kwargs):
        return _windows_.PyPanel_DoGetSize(*args, **kwargs)

    def DoGetClientSize(*args, **kwargs):
        return _windows_.PyPanel_DoGetClientSize(*args, **kwargs)

    def DoGetPosition(*args, **kwargs):
        return _windows_.PyPanel_DoGetPosition(*args, **kwargs)

    def DoGetVirtualSize(*args, **kwargs):
        return _windows_.PyPanel_DoGetVirtualSize(*args, **kwargs)

    def DoGetBestSize(*args, **kwargs):
        return _windows_.PyPanel_DoGetBestSize(*args, **kwargs)

    def InitDialog(*args, **kwargs):
        return _windows_.PyPanel_InitDialog(*args, **kwargs)

    def TransferDataToWindow(*args, **kwargs):
        return _windows_.PyPanel_TransferDataToWindow(*args, **kwargs)

    def TransferDataFromWindow(*args, **kwargs):
        return _windows_.PyPanel_TransferDataFromWindow(*args, **kwargs)

    def Validate(*args, **kwargs):
        return _windows_.PyPanel_Validate(*args, **kwargs)

    def GetDefaultAttributes(*args, **kwargs):
        return _windows_.PyPanel_GetDefaultAttributes(*args, **kwargs)

    def OnInternalIdle(*args, **kwargs):
        return _windows_.PyPanel_OnInternalIdle(*args, **kwargs)

    def base_DoMoveWindow(*args, **kw):
        return PyPanel.DoMoveWindow(*args, **kw)

    base_DoMoveWindow = wx._deprecated(base_DoMoveWindow, 'Please use PyPanel.DoMoveWindow instead.')

    def base_DoSetSize(*args, **kw):
        return PyPanel.DoSetSize(*args, **kw)

    base_DoSetSize = wx._deprecated(base_DoSetSize, 'Please use PyPanel.DoSetSize instead.')

    def base_DoSetClientSize(*args, **kw):
        return PyPanel.DoSetClientSize(*args, **kw)

    base_DoSetClientSize = wx._deprecated(base_DoSetClientSize, 'Please use PyPanel.DoSetClientSize instead.')

    def base_DoSetVirtualSize(*args, **kw):
        return PyPanel.DoSetVirtualSize(*args, **kw)

    base_DoSetVirtualSize = wx._deprecated(base_DoSetVirtualSize, 'Please use PyPanel.DoSetVirtualSize instead.')

    def base_DoGetSize(*args, **kw):
        return PyPanel.DoGetSize(*args, **kw)

    base_DoGetSize = wx._deprecated(base_DoGetSize, 'Please use PyPanel.DoGetSize instead.')

    def base_DoGetClientSize(*args, **kw):
        return PyPanel.DoGetClientSize(*args, **kw)

    base_DoGetClientSize = wx._deprecated(base_DoGetClientSize, 'Please use PyPanel.DoGetClientSize instead.')

    def base_DoGetPosition(*args, **kw):
        return PyPanel.DoGetPosition(*args, **kw)

    base_DoGetPosition = wx._deprecated(base_DoGetPosition, 'Please use PyPanel.DoGetPosition instead.')

    def base_DoGetVirtualSize(*args, **kw):
        return PyPanel.DoGetVirtualSize(*args, **kw)

    base_DoGetVirtualSize = wx._deprecated(base_DoGetVirtualSize, 'Please use PyPanel.DoGetVirtualSize instead.')

    def base_DoGetBestSize(*args, **kw):
        return PyPanel.DoGetBestSize(*args, **kw)

    base_DoGetBestSize = wx._deprecated(base_DoGetBestSize, 'Please use PyPanel.DoGetBestSize instead.')

    def base_InitDialog(*args, **kw):
        return PyPanel.InitDialog(*args, **kw)

    base_InitDialog = wx._deprecated(base_InitDialog, 'Please use PyPanel.InitDialog instead.')

    def base_TransferDataToWindow(*args, **kw):
        return PyPanel.TransferDataToWindow(*args, **kw)

    base_TransferDataToWindow = wx._deprecated(base_TransferDataToWindow, 'Please use PyPanel.TransferDataToWindow instead.')

    def base_TransferDataFromWindow(*args, **kw):
        return PyPanel.TransferDataFromWindow(*args, **kw)

    base_TransferDataFromWindow = wx._deprecated(base_TransferDataFromWindow, 'Please use PyPanel.TransferDataFromWindow instead.')

    def base_Validate(*args, **kw):
        return PyPanel.Validate(*args, **kw)

    base_Validate = wx._deprecated(base_Validate, 'Please use PyPanel.Validate instead.')

    def base_AcceptsFocus(*args, **kw):
        return PyPanel.AcceptsFocus(*args, **kw)

    base_AcceptsFocus = wx._deprecated(base_AcceptsFocus, 'Please use PyPanel.AcceptsFocus instead.')

    def base_AcceptsFocusFromKeyboard(*args, **kw):
        return PyPanel.AcceptsFocusFromKeyboard(*args, **kw)

    base_AcceptsFocusFromKeyboard = wx._deprecated(base_AcceptsFocusFromKeyboard, 'Please use PyPanel.AcceptsFocusFromKeyboard instead.')

    def base_GetMaxSize(*args, **kw):
        return PyPanel.GetMaxSize(*args, **kw)

    base_GetMaxSize = wx._deprecated(base_GetMaxSize, 'Please use PyPanel.GetMaxSize instead.')

    def base_AddChild(*args, **kw):
        return PyPanel.AddChild(*args, **kw)

    base_AddChild = wx._deprecated(base_AddChild, 'Please use PyPanel.AddChild instead.')

    def base_RemoveChild(*args, **kw):
        return PyPanel.RemoveChild(*args, **kw)

    base_RemoveChild = wx._deprecated(base_RemoveChild, 'Please use PyPanel.RemoveChild instead.')

    def base_ShouldInheritColours(*args, **kw):
        return PyPanel.ShouldInheritColours(*args, **kw)

    base_ShouldInheritColours = wx._deprecated(base_ShouldInheritColours, 'Please use PyPanel.ShouldInheritColours instead.')

    def base_GetDefaultAttributes(*args, **kw):
        return PyPanel.GetDefaultAttributes(*args, **kw)

    base_GetDefaultAttributes = wx._deprecated(base_GetDefaultAttributes, 'Please use PyPanel.GetDefaultAttributes instead.')

    def base_OnInternalIdle(*args, **kw):
        return PyPanel.OnInternalIdle(*args, **kw)

    base_OnInternalIdle = wx._deprecated(base_OnInternalIdle, 'Please use PyPanel.OnInternalIdle instead.')


_windows_.PyPanel_swigregister(PyPanel)

def PrePyPanel(*args, **kwargs):
    val = _windows_.new_PrePyPanel(*args, **kwargs)
    return val


class PyScrolledWindow(ScrolledWindow):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _windows_.PyScrolledWindow_swiginit(self, _windows_.new_PyScrolledWindow(*args, **kwargs))
        self._setOORInfo(self)
        PyScrolledWindow._setCallbackInfo(self, self, PyScrolledWindow)

    def _setCallbackInfo(*args, **kwargs):
        return _windows_.PyScrolledWindow__setCallbackInfo(*args, **kwargs)

    SetBestSize = wx.Window.SetInitialSize

    def DoEraseBackground(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoEraseBackground(*args, **kwargs)

    def DoMoveWindow(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoMoveWindow(*args, **kwargs)

    def DoSetSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoSetSize(*args, **kwargs)

    def DoSetClientSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoSetClientSize(*args, **kwargs)

    def DoSetVirtualSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoSetVirtualSize(*args, **kwargs)

    def DoGetSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoGetSize(*args, **kwargs)

    def DoGetClientSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoGetClientSize(*args, **kwargs)

    def DoGetPosition(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoGetPosition(*args, **kwargs)

    def DoGetVirtualSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoGetVirtualSize(*args, **kwargs)

    def DoGetBestSize(*args, **kwargs):
        return _windows_.PyScrolledWindow_DoGetBestSize(*args, **kwargs)

    def InitDialog(*args, **kwargs):
        return _windows_.PyScrolledWindow_InitDialog(*args, **kwargs)

    def TransferDataToWindow(*args, **kwargs):
        return _windows_.PyScrolledWindow_TransferDataToWindow(*args, **kwargs)

    def TransferDataFromWindow(*args, **kwargs):
        return _windows_.PyScrolledWindow_TransferDataFromWindow(*args, **kwargs)

    def Validate(*args, **kwargs):
        return _windows_.PyScrolledWindow_Validate(*args, **kwargs)

    def GetDefaultAttributes(*args, **kwargs):
        return _windows_.PyScrolledWindow_GetDefaultAttributes(*args, **kwargs)

    def OnInternalIdle(*args, **kwargs):
        return _windows_.PyScrolledWindow_OnInternalIdle(*args, **kwargs)

    def base_DoMoveWindow(*args, **kw):
        return PyScrolledWindow.DoMoveWindow(*args, **kw)

    base_DoMoveWindow = wx._deprecated(base_DoMoveWindow, 'Please use PyScrolledWindow.DoMoveWindow instead.')

    def base_DoSetSize(*args, **kw):
        return PyScrolledWindow.DoSetSize(*args, **kw)

    base_DoSetSize = wx._deprecated(base_DoSetSize, 'Please use PyScrolledWindow.DoSetSize instead.')

    def base_DoSetClientSize(*args, **kw):
        return PyScrolledWindow.DoSetClientSize(*args, **kw)

    base_DoSetClientSize = wx._deprecated(base_DoSetClientSize, 'Please use PyScrolledWindow.DoSetClientSize instead.')

    def base_DoSetVirtualSize(*args, **kw):
        return PyScrolledWindow.DoSetVirtualSize(*args, **kw)

    base_DoSetVirtualSize = wx._deprecated(base_DoSetVirtualSize, 'Please use PyScrolledWindow.DoSetVirtualSize instead.')

    def base_DoGetSize(*args, **kw):
        return PyScrolledWindow.DoGetSize(*args, **kw)

    base_DoGetSize = wx._deprecated(base_DoGetSize, 'Please use PyScrolledWindow.DoGetSize instead.')

    def base_DoGetClientSize(*args, **kw):
        return PyScrolledWindow.DoGetClientSize(*args, **kw)

    base_DoGetClientSize = wx._deprecated(base_DoGetClientSize, 'Please use PyScrolledWindow.DoGetClientSize instead.')

    def base_DoGetPosition(*args, **kw):
        return PyScrolledWindow.DoGetPosition(*args, **kw)

    base_DoGetPosition = wx._deprecated(base_DoGetPosition, 'Please use PyScrolledWindow.DoGetPosition instead.')

    def base_DoGetVirtualSize(*args, **kw):
        return PyScrolledWindow.DoGetVirtualSize(*args, **kw)

    base_DoGetVirtualSize = wx._deprecated(base_DoGetVirtualSize, 'Please use PyScrolledWindow.DoGetVirtualSize instead.')

    def base_DoGetBestSize(*args, **kw):
        return PyScrolledWindow.DoGetBestSize(*args, **kw)

    base_DoGetBestSize = wx._deprecated(base_DoGetBestSize, 'Please use PyScrolledWindow.DoGetBestSize instead.')

    def base_InitDialog(*args, **kw):
        return PyScrolledWindow.InitDialog(*args, **kw)

    base_InitDialog = wx._deprecated(base_InitDialog, 'Please use PyScrolledWindow.InitDialog instead.')

    def base_TransferDataToWindow(*args, **kw):
        return PyScrolledWindow.TransferDataToWindow(*args, **kw)

    base_TransferDataToWindow = wx._deprecated(base_TransferDataToWindow, 'Please use PyScrolledWindow.TransferDataToWindow instead.')

    def base_TransferDataFromWindow(*args, **kw):
        return PyScrolledWindow.TransferDataFromWindow(*args, **kw)

    base_TransferDataFromWindow = wx._deprecated(base_TransferDataFromWindow, 'Please use PyScrolledWindow.TransferDataFromWindow instead.')

    def base_Validate(*args, **kw):
        return PyScrolledWindow.Validate(*args, **kw)

    base_Validate = wx._deprecated(base_Validate, 'Please use PyScrolledWindow.Validate instead.')

    def base_AcceptsFocus(*args, **kw):
        return PyScrolledWindow.AcceptsFocus(*args, **kw)

    base_AcceptsFocus = wx._deprecated(base_AcceptsFocus, 'Please use PyScrolledWindow.AcceptsFocus instead.')

    def base_AcceptsFocusFromKeyboard(*args, **kw):
        return PyScrolledWindow.AcceptsFocusFromKeyboard(*args, **kw)

    base_AcceptsFocusFromKeyboard = wx._deprecated(base_AcceptsFocusFromKeyboard, 'Please use PyScrolledWindow.AcceptsFocusFromKeyboard instead.')

    def base_GetMaxSize(*args, **kw):
        return PyScrolledWindow.GetMaxSize(*args, **kw)

    base_GetMaxSize = wx._deprecated(base_GetMaxSize, 'Please use PyScrolledWindow.GetMaxSize instead.')

    def base_AddChild(*args, **kw):
        return PyScrolledWindow.AddChild(*args, **kw)

    base_AddChild = wx._deprecated(base_AddChild, 'Please use PyScrolledWindow.AddChild instead.')

    def base_RemoveChild(*args, **kw):
        return PyScrolledWindow.RemoveChild(*args, **kw)

    base_RemoveChild = wx._deprecated(base_RemoveChild, 'Please use PyScrolledWindow.RemoveChild instead.')

    def base_ShouldInheritColours(*args, **kw):
        return PyScrolledWindow.ShouldInheritColours(*args, **kw)

    base_ShouldInheritColours = wx._deprecated(base_ShouldInheritColours, 'Please use PyScrolledWindow.ShouldInheritColours instead.')

    def base_GetDefaultAttributes(*args, **kw):
        return PyScrolledWindow.GetDefaultAttributes(*args, **kw)

    base_GetDefaultAttributes = wx._deprecated(base_GetDefaultAttributes, 'Please use PyScrolledWindow.GetDefaultAttributes instead.')

    def base_OnInternalIdle(*args, **kw):
        return PyScrolledWindow.OnInternalIdle(*args, **kw)

    base_OnInternalIdle = wx._deprecated(base_OnInternalIdle, 'Please use PyScrolledWindow.OnInternalIdle instead.')


_windows_.PyScrolledWindow_swigregister(PyScrolledWindow)

def PrePyScrolledWindow(*args, **kwargs):
    val = _windows_.new_PrePyScrolledWindow(*args, **kwargs)
    return val
