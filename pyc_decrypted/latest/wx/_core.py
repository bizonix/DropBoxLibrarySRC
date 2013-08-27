#Embedded file name: wx/_core.py
import _core_
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


_core_._wxPySetDictionary(vars())
import sys as _sys
wx = _sys.modules[__name__]

def _deprecated(callable, msg = None):
    if msg is None:
        msg = '%s is deprecated' % callable

    def deprecatedWrapper(*args, **kwargs):
        import warnings
        warnings.warn(msg, DeprecationWarning, stacklevel=2)
        return callable(*args, **kwargs)

    deprecatedWrapper.__doc__ = msg
    return deprecatedWrapper


NOT_FOUND = _core_.NOT_FOUND
VSCROLL = _core_.VSCROLL
HSCROLL = _core_.HSCROLL
CAPTION = _core_.CAPTION
DOUBLE_BORDER = _core_.DOUBLE_BORDER
SUNKEN_BORDER = _core_.SUNKEN_BORDER
RAISED_BORDER = _core_.RAISED_BORDER
BORDER = _core_.BORDER
SIMPLE_BORDER = _core_.SIMPLE_BORDER
STATIC_BORDER = _core_.STATIC_BORDER
TRANSPARENT_WINDOW = _core_.TRANSPARENT_WINDOW
NO_BORDER = _core_.NO_BORDER
DEFAULT_CONTROL_BORDER = _core_.DEFAULT_CONTROL_BORDER
DEFAULT_STATUSBAR_STYLE = _core_.DEFAULT_STATUSBAR_STYLE
TAB_TRAVERSAL = _core_.TAB_TRAVERSAL
WANTS_CHARS = _core_.WANTS_CHARS
POPUP_WINDOW = _core_.POPUP_WINDOW
CENTER_FRAME = _core_.CENTER_FRAME
CENTRE_ON_SCREEN = _core_.CENTRE_ON_SCREEN
CENTER_ON_SCREEN = _core_.CENTER_ON_SCREEN
CLIP_CHILDREN = _core_.CLIP_CHILDREN
CLIP_SIBLINGS = _core_.CLIP_SIBLINGS
WINDOW_STYLE_MASK = _core_.WINDOW_STYLE_MASK
ALWAYS_SHOW_SB = _core_.ALWAYS_SHOW_SB
RETAINED = _core_.RETAINED
BACKINGSTORE = _core_.BACKINGSTORE
COLOURED = _core_.COLOURED
FIXED_LENGTH = _core_.FIXED_LENGTH
LB_NEEDED_SB = _core_.LB_NEEDED_SB
LB_ALWAYS_SB = _core_.LB_ALWAYS_SB
LB_SORT = _core_.LB_SORT
LB_SINGLE = _core_.LB_SINGLE
LB_MULTIPLE = _core_.LB_MULTIPLE
LB_EXTENDED = _core_.LB_EXTENDED
LB_OWNERDRAW = _core_.LB_OWNERDRAW
LB_HSCROLL = _core_.LB_HSCROLL
PROCESS_ENTER = _core_.PROCESS_ENTER
PASSWORD = _core_.PASSWORD
CB_SIMPLE = _core_.CB_SIMPLE
CB_DROPDOWN = _core_.CB_DROPDOWN
CB_SORT = _core_.CB_SORT
CB_READONLY = _core_.CB_READONLY
RA_HORIZONTAL = _core_.RA_HORIZONTAL
RA_VERTICAL = _core_.RA_VERTICAL
RA_SPECIFY_ROWS = _core_.RA_SPECIFY_ROWS
RA_SPECIFY_COLS = _core_.RA_SPECIFY_COLS
RA_USE_CHECKBOX = _core_.RA_USE_CHECKBOX
RB_GROUP = _core_.RB_GROUP
RB_SINGLE = _core_.RB_SINGLE
SB_HORIZONTAL = _core_.SB_HORIZONTAL
SB_VERTICAL = _core_.SB_VERTICAL
RB_USE_CHECKBOX = _core_.RB_USE_CHECKBOX
ST_SIZEGRIP = _core_.ST_SIZEGRIP
ST_NO_AUTORESIZE = _core_.ST_NO_AUTORESIZE
ST_DOTS_MIDDLE = _core_.ST_DOTS_MIDDLE
ST_DOTS_END = _core_.ST_DOTS_END
FLOOD_SURFACE = _core_.FLOOD_SURFACE
FLOOD_BORDER = _core_.FLOOD_BORDER
ODDEVEN_RULE = _core_.ODDEVEN_RULE
WINDING_RULE = _core_.WINDING_RULE
TOOL_TOP = _core_.TOOL_TOP
TOOL_BOTTOM = _core_.TOOL_BOTTOM
TOOL_LEFT = _core_.TOOL_LEFT
TOOL_RIGHT = _core_.TOOL_RIGHT
OK = _core_.OK
YES_NO = _core_.YES_NO
CANCEL = _core_.CANCEL
YES = _core_.YES
NO = _core_.NO
NO_DEFAULT = _core_.NO_DEFAULT
YES_DEFAULT = _core_.YES_DEFAULT
ICON_EXCLAMATION = _core_.ICON_EXCLAMATION
ICON_HAND = _core_.ICON_HAND
ICON_QUESTION = _core_.ICON_QUESTION
ICON_INFORMATION = _core_.ICON_INFORMATION
ICON_STOP = _core_.ICON_STOP
ICON_ASTERISK = _core_.ICON_ASTERISK
ICON_MASK = _core_.ICON_MASK
ICON_WARNING = _core_.ICON_WARNING
ICON_ERROR = _core_.ICON_ERROR
FORWARD = _core_.FORWARD
BACKWARD = _core_.BACKWARD
RESET = _core_.RESET
HELP = _core_.HELP
MORE = _core_.MORE
SETUP = _core_.SETUP
SIZE_AUTO_WIDTH = _core_.SIZE_AUTO_WIDTH
SIZE_AUTO_HEIGHT = _core_.SIZE_AUTO_HEIGHT
SIZE_AUTO = _core_.SIZE_AUTO
SIZE_USE_EXISTING = _core_.SIZE_USE_EXISTING
SIZE_ALLOW_MINUS_ONE = _core_.SIZE_ALLOW_MINUS_ONE
SIZE_FORCE = _core_.SIZE_FORCE
PORTRAIT = _core_.PORTRAIT
LANDSCAPE = _core_.LANDSCAPE
PRINT_QUALITY_HIGH = _core_.PRINT_QUALITY_HIGH
PRINT_QUALITY_MEDIUM = _core_.PRINT_QUALITY_MEDIUM
PRINT_QUALITY_LOW = _core_.PRINT_QUALITY_LOW
PRINT_QUALITY_DRAFT = _core_.PRINT_QUALITY_DRAFT
ID_ANY = _core_.ID_ANY
ID_SEPARATOR = _core_.ID_SEPARATOR
ID_NONE = _core_.ID_NONE
ID_LOWEST = _core_.ID_LOWEST
ID_OPEN = _core_.ID_OPEN
ID_CLOSE = _core_.ID_CLOSE
ID_NEW = _core_.ID_NEW
ID_SAVE = _core_.ID_SAVE
ID_SAVEAS = _core_.ID_SAVEAS
ID_REVERT = _core_.ID_REVERT
ID_EXIT = _core_.ID_EXIT
ID_UNDO = _core_.ID_UNDO
ID_REDO = _core_.ID_REDO
ID_HELP = _core_.ID_HELP
ID_PRINT = _core_.ID_PRINT
ID_PRINT_SETUP = _core_.ID_PRINT_SETUP
ID_PAGE_SETUP = _core_.ID_PAGE_SETUP
ID_PREVIEW = _core_.ID_PREVIEW
ID_ABOUT = _core_.ID_ABOUT
ID_HELP_CONTENTS = _core_.ID_HELP_CONTENTS
ID_HELP_COMMANDS = _core_.ID_HELP_COMMANDS
ID_HELP_PROCEDURES = _core_.ID_HELP_PROCEDURES
ID_HELP_CONTEXT = _core_.ID_HELP_CONTEXT
ID_HELP_INDEX = _core_.ID_HELP_INDEX
ID_HELP_SEARCH = _core_.ID_HELP_SEARCH
ID_CLOSE_ALL = _core_.ID_CLOSE_ALL
ID_PREFERENCES = _core_.ID_PREFERENCES
ID_EDIT = _core_.ID_EDIT
ID_CUT = _core_.ID_CUT
ID_COPY = _core_.ID_COPY
ID_PASTE = _core_.ID_PASTE
ID_CLEAR = _core_.ID_CLEAR
ID_FIND = _core_.ID_FIND
ID_DUPLICATE = _core_.ID_DUPLICATE
ID_SELECTALL = _core_.ID_SELECTALL
ID_DELETE = _core_.ID_DELETE
ID_REPLACE = _core_.ID_REPLACE
ID_REPLACE_ALL = _core_.ID_REPLACE_ALL
ID_PROPERTIES = _core_.ID_PROPERTIES
ID_VIEW_DETAILS = _core_.ID_VIEW_DETAILS
ID_VIEW_LARGEICONS = _core_.ID_VIEW_LARGEICONS
ID_VIEW_SMALLICONS = _core_.ID_VIEW_SMALLICONS
ID_VIEW_LIST = _core_.ID_VIEW_LIST
ID_VIEW_SORTDATE = _core_.ID_VIEW_SORTDATE
ID_VIEW_SORTNAME = _core_.ID_VIEW_SORTNAME
ID_VIEW_SORTSIZE = _core_.ID_VIEW_SORTSIZE
ID_VIEW_SORTTYPE = _core_.ID_VIEW_SORTTYPE
ID_FILE = _core_.ID_FILE
ID_FILE1 = _core_.ID_FILE1
ID_FILE2 = _core_.ID_FILE2
ID_FILE3 = _core_.ID_FILE3
ID_FILE4 = _core_.ID_FILE4
ID_FILE5 = _core_.ID_FILE5
ID_FILE6 = _core_.ID_FILE6
ID_FILE7 = _core_.ID_FILE7
ID_FILE8 = _core_.ID_FILE8
ID_FILE9 = _core_.ID_FILE9
ID_OK = _core_.ID_OK
ID_CANCEL = _core_.ID_CANCEL
ID_APPLY = _core_.ID_APPLY
ID_YES = _core_.ID_YES
ID_NO = _core_.ID_NO
ID_STATIC = _core_.ID_STATIC
ID_FORWARD = _core_.ID_FORWARD
ID_BACKWARD = _core_.ID_BACKWARD
ID_DEFAULT = _core_.ID_DEFAULT
ID_MORE = _core_.ID_MORE
ID_SETUP = _core_.ID_SETUP
ID_RESET = _core_.ID_RESET
ID_CONTEXT_HELP = _core_.ID_CONTEXT_HELP
ID_YESTOALL = _core_.ID_YESTOALL
ID_NOTOALL = _core_.ID_NOTOALL
ID_ABORT = _core_.ID_ABORT
ID_RETRY = _core_.ID_RETRY
ID_IGNORE = _core_.ID_IGNORE
ID_ADD = _core_.ID_ADD
ID_REMOVE = _core_.ID_REMOVE
ID_UP = _core_.ID_UP
ID_DOWN = _core_.ID_DOWN
ID_HOME = _core_.ID_HOME
ID_REFRESH = _core_.ID_REFRESH
ID_STOP = _core_.ID_STOP
ID_INDEX = _core_.ID_INDEX
ID_BOLD = _core_.ID_BOLD
ID_ITALIC = _core_.ID_ITALIC
ID_JUSTIFY_CENTER = _core_.ID_JUSTIFY_CENTER
ID_JUSTIFY_FILL = _core_.ID_JUSTIFY_FILL
ID_JUSTIFY_RIGHT = _core_.ID_JUSTIFY_RIGHT
ID_JUSTIFY_LEFT = _core_.ID_JUSTIFY_LEFT
ID_UNDERLINE = _core_.ID_UNDERLINE
ID_INDENT = _core_.ID_INDENT
ID_UNINDENT = _core_.ID_UNINDENT
ID_ZOOM_100 = _core_.ID_ZOOM_100
ID_ZOOM_FIT = _core_.ID_ZOOM_FIT
ID_ZOOM_IN = _core_.ID_ZOOM_IN
ID_ZOOM_OUT = _core_.ID_ZOOM_OUT
ID_UNDELETE = _core_.ID_UNDELETE
ID_REVERT_TO_SAVED = _core_.ID_REVERT_TO_SAVED
ID_HIGHEST = _core_.ID_HIGHEST
MENU_TEAROFF = _core_.MENU_TEAROFF
MB_DOCKABLE = _core_.MB_DOCKABLE
NO_FULL_REPAINT_ON_RESIZE = _core_.NO_FULL_REPAINT_ON_RESIZE
FULL_REPAINT_ON_RESIZE = _core_.FULL_REPAINT_ON_RESIZE
LI_HORIZONTAL = _core_.LI_HORIZONTAL
LI_VERTICAL = _core_.LI_VERTICAL
WS_EX_VALIDATE_RECURSIVELY = _core_.WS_EX_VALIDATE_RECURSIVELY
WS_EX_BLOCK_EVENTS = _core_.WS_EX_BLOCK_EVENTS
WS_EX_TRANSIENT = _core_.WS_EX_TRANSIENT
WS_EX_THEMED_BACKGROUND = _core_.WS_EX_THEMED_BACKGROUND
WS_EX_PROCESS_IDLE = _core_.WS_EX_PROCESS_IDLE
WS_EX_PROCESS_UI_UPDATES = _core_.WS_EX_PROCESS_UI_UPDATES
MM_TEXT = _core_.MM_TEXT
MM_LOMETRIC = _core_.MM_LOMETRIC
MM_HIMETRIC = _core_.MM_HIMETRIC
MM_LOENGLISH = _core_.MM_LOENGLISH
MM_HIENGLISH = _core_.MM_HIENGLISH
MM_TWIPS = _core_.MM_TWIPS
MM_ISOTROPIC = _core_.MM_ISOTROPIC
MM_ANISOTROPIC = _core_.MM_ANISOTROPIC
MM_POINTS = _core_.MM_POINTS
MM_METRIC = _core_.MM_METRIC
CENTRE = _core_.CENTRE
CENTER = _core_.CENTER
HORIZONTAL = _core_.HORIZONTAL
VERTICAL = _core_.VERTICAL
BOTH = _core_.BOTH
LEFT = _core_.LEFT
RIGHT = _core_.RIGHT
UP = _core_.UP
DOWN = _core_.DOWN
TOP = _core_.TOP
BOTTOM = _core_.BOTTOM
NORTH = _core_.NORTH
SOUTH = _core_.SOUTH
WEST = _core_.WEST
EAST = _core_.EAST
ALL = _core_.ALL
ALIGN_NOT = _core_.ALIGN_NOT
ALIGN_CENTER_HORIZONTAL = _core_.ALIGN_CENTER_HORIZONTAL
ALIGN_CENTRE_HORIZONTAL = _core_.ALIGN_CENTRE_HORIZONTAL
ALIGN_LEFT = _core_.ALIGN_LEFT
ALIGN_TOP = _core_.ALIGN_TOP
ALIGN_RIGHT = _core_.ALIGN_RIGHT
ALIGN_BOTTOM = _core_.ALIGN_BOTTOM
ALIGN_CENTER_VERTICAL = _core_.ALIGN_CENTER_VERTICAL
ALIGN_CENTRE_VERTICAL = _core_.ALIGN_CENTRE_VERTICAL
ALIGN_CENTER = _core_.ALIGN_CENTER
ALIGN_CENTRE = _core_.ALIGN_CENTRE
ALIGN_MASK = _core_.ALIGN_MASK
STRETCH_NOT = _core_.STRETCH_NOT
SHRINK = _core_.SHRINK
GROW = _core_.GROW
EXPAND = _core_.EXPAND
SHAPED = _core_.SHAPED
FIXED_MINSIZE = _core_.FIXED_MINSIZE
RESERVE_SPACE_EVEN_IF_HIDDEN = _core_.RESERVE_SPACE_EVEN_IF_HIDDEN
TILE = _core_.TILE
ADJUST_MINSIZE = _core_.ADJUST_MINSIZE
BORDER_DEFAULT = _core_.BORDER_DEFAULT
BORDER_NONE = _core_.BORDER_NONE
BORDER_STATIC = _core_.BORDER_STATIC
BORDER_SIMPLE = _core_.BORDER_SIMPLE
BORDER_RAISED = _core_.BORDER_RAISED
BORDER_SUNKEN = _core_.BORDER_SUNKEN
BORDER_DOUBLE = _core_.BORDER_DOUBLE
BORDER_THEME = _core_.BORDER_THEME
BORDER_MASK = _core_.BORDER_MASK
BG_STYLE_SYSTEM = _core_.BG_STYLE_SYSTEM
BG_STYLE_COLOUR = _core_.BG_STYLE_COLOUR
BG_STYLE_CUSTOM = _core_.BG_STYLE_CUSTOM
DEFAULT = _core_.DEFAULT
DECORATIVE = _core_.DECORATIVE
ROMAN = _core_.ROMAN
SCRIPT = _core_.SCRIPT
SWISS = _core_.SWISS
MODERN = _core_.MODERN
TELETYPE = _core_.TELETYPE
VARIABLE = _core_.VARIABLE
FIXED = _core_.FIXED
NORMAL = _core_.NORMAL
LIGHT = _core_.LIGHT
BOLD = _core_.BOLD
ITALIC = _core_.ITALIC
SLANT = _core_.SLANT
SOLID = _core_.SOLID
DOT = _core_.DOT
LONG_DASH = _core_.LONG_DASH
SHORT_DASH = _core_.SHORT_DASH
DOT_DASH = _core_.DOT_DASH
USER_DASH = _core_.USER_DASH
TRANSPARENT = _core_.TRANSPARENT
STIPPLE = _core_.STIPPLE
STIPPLE_MASK = _core_.STIPPLE_MASK
STIPPLE_MASK_OPAQUE = _core_.STIPPLE_MASK_OPAQUE
BDIAGONAL_HATCH = _core_.BDIAGONAL_HATCH
CROSSDIAG_HATCH = _core_.CROSSDIAG_HATCH
FDIAGONAL_HATCH = _core_.FDIAGONAL_HATCH
CROSS_HATCH = _core_.CROSS_HATCH
HORIZONTAL_HATCH = _core_.HORIZONTAL_HATCH
VERTICAL_HATCH = _core_.VERTICAL_HATCH
JOIN_BEVEL = _core_.JOIN_BEVEL
JOIN_MITER = _core_.JOIN_MITER
JOIN_ROUND = _core_.JOIN_ROUND
CAP_ROUND = _core_.CAP_ROUND
CAP_PROJECTING = _core_.CAP_PROJECTING
CAP_BUTT = _core_.CAP_BUTT
CLEAR = _core_.CLEAR
XOR = _core_.XOR
INVERT = _core_.INVERT
OR_REVERSE = _core_.OR_REVERSE
AND_REVERSE = _core_.AND_REVERSE
COPY = _core_.COPY
AND = _core_.AND
AND_INVERT = _core_.AND_INVERT
NO_OP = _core_.NO_OP
NOR = _core_.NOR
EQUIV = _core_.EQUIV
SRC_INVERT = _core_.SRC_INVERT
OR_INVERT = _core_.OR_INVERT
NAND = _core_.NAND
OR = _core_.OR
SET = _core_.SET
WXK_BACK = _core_.WXK_BACK
WXK_TAB = _core_.WXK_TAB
WXK_RETURN = _core_.WXK_RETURN
WXK_ESCAPE = _core_.WXK_ESCAPE
WXK_SPACE = _core_.WXK_SPACE
WXK_DELETE = _core_.WXK_DELETE
WXK_START = _core_.WXK_START
WXK_LBUTTON = _core_.WXK_LBUTTON
WXK_RBUTTON = _core_.WXK_RBUTTON
WXK_CANCEL = _core_.WXK_CANCEL
WXK_MBUTTON = _core_.WXK_MBUTTON
WXK_CLEAR = _core_.WXK_CLEAR
WXK_SHIFT = _core_.WXK_SHIFT
WXK_ALT = _core_.WXK_ALT
WXK_CONTROL = _core_.WXK_CONTROL
WXK_MENU = _core_.WXK_MENU
WXK_PAUSE = _core_.WXK_PAUSE
WXK_CAPITAL = _core_.WXK_CAPITAL
WXK_PRIOR = _core_.WXK_PRIOR
WXK_NEXT = _core_.WXK_NEXT
WXK_END = _core_.WXK_END
WXK_HOME = _core_.WXK_HOME
WXK_LEFT = _core_.WXK_LEFT
WXK_UP = _core_.WXK_UP
WXK_RIGHT = _core_.WXK_RIGHT
WXK_DOWN = _core_.WXK_DOWN
WXK_SELECT = _core_.WXK_SELECT
WXK_PRINT = _core_.WXK_PRINT
WXK_EXECUTE = _core_.WXK_EXECUTE
WXK_SNAPSHOT = _core_.WXK_SNAPSHOT
WXK_INSERT = _core_.WXK_INSERT
WXK_HELP = _core_.WXK_HELP
WXK_NUMPAD0 = _core_.WXK_NUMPAD0
WXK_NUMPAD1 = _core_.WXK_NUMPAD1
WXK_NUMPAD2 = _core_.WXK_NUMPAD2
WXK_NUMPAD3 = _core_.WXK_NUMPAD3
WXK_NUMPAD4 = _core_.WXK_NUMPAD4
WXK_NUMPAD5 = _core_.WXK_NUMPAD5
WXK_NUMPAD6 = _core_.WXK_NUMPAD6
WXK_NUMPAD7 = _core_.WXK_NUMPAD7
WXK_NUMPAD8 = _core_.WXK_NUMPAD8
WXK_NUMPAD9 = _core_.WXK_NUMPAD9
WXK_MULTIPLY = _core_.WXK_MULTIPLY
WXK_ADD = _core_.WXK_ADD
WXK_SEPARATOR = _core_.WXK_SEPARATOR
WXK_SUBTRACT = _core_.WXK_SUBTRACT
WXK_DECIMAL = _core_.WXK_DECIMAL
WXK_DIVIDE = _core_.WXK_DIVIDE
WXK_F1 = _core_.WXK_F1
WXK_F2 = _core_.WXK_F2
WXK_F3 = _core_.WXK_F3
WXK_F4 = _core_.WXK_F4
WXK_F5 = _core_.WXK_F5
WXK_F6 = _core_.WXK_F6
WXK_F7 = _core_.WXK_F7
WXK_F8 = _core_.WXK_F8
WXK_F9 = _core_.WXK_F9
WXK_F10 = _core_.WXK_F10
WXK_F11 = _core_.WXK_F11
WXK_F12 = _core_.WXK_F12
WXK_F13 = _core_.WXK_F13
WXK_F14 = _core_.WXK_F14
WXK_F15 = _core_.WXK_F15
WXK_F16 = _core_.WXK_F16
WXK_F17 = _core_.WXK_F17
WXK_F18 = _core_.WXK_F18
WXK_F19 = _core_.WXK_F19
WXK_F20 = _core_.WXK_F20
WXK_F21 = _core_.WXK_F21
WXK_F22 = _core_.WXK_F22
WXK_F23 = _core_.WXK_F23
WXK_F24 = _core_.WXK_F24
WXK_NUMLOCK = _core_.WXK_NUMLOCK
WXK_SCROLL = _core_.WXK_SCROLL
WXK_PAGEUP = _core_.WXK_PAGEUP
WXK_PAGEDOWN = _core_.WXK_PAGEDOWN
WXK_NUMPAD_SPACE = _core_.WXK_NUMPAD_SPACE
WXK_NUMPAD_TAB = _core_.WXK_NUMPAD_TAB
WXK_NUMPAD_ENTER = _core_.WXK_NUMPAD_ENTER
WXK_NUMPAD_F1 = _core_.WXK_NUMPAD_F1
WXK_NUMPAD_F2 = _core_.WXK_NUMPAD_F2
WXK_NUMPAD_F3 = _core_.WXK_NUMPAD_F3
WXK_NUMPAD_F4 = _core_.WXK_NUMPAD_F4
WXK_NUMPAD_HOME = _core_.WXK_NUMPAD_HOME
WXK_NUMPAD_LEFT = _core_.WXK_NUMPAD_LEFT
WXK_NUMPAD_UP = _core_.WXK_NUMPAD_UP
WXK_NUMPAD_RIGHT = _core_.WXK_NUMPAD_RIGHT
WXK_NUMPAD_DOWN = _core_.WXK_NUMPAD_DOWN
WXK_NUMPAD_PRIOR = _core_.WXK_NUMPAD_PRIOR
WXK_NUMPAD_PAGEUP = _core_.WXK_NUMPAD_PAGEUP
WXK_NUMPAD_NEXT = _core_.WXK_NUMPAD_NEXT
WXK_NUMPAD_PAGEDOWN = _core_.WXK_NUMPAD_PAGEDOWN
WXK_NUMPAD_END = _core_.WXK_NUMPAD_END
WXK_NUMPAD_BEGIN = _core_.WXK_NUMPAD_BEGIN
WXK_NUMPAD_INSERT = _core_.WXK_NUMPAD_INSERT
WXK_NUMPAD_DELETE = _core_.WXK_NUMPAD_DELETE
WXK_NUMPAD_EQUAL = _core_.WXK_NUMPAD_EQUAL
WXK_NUMPAD_MULTIPLY = _core_.WXK_NUMPAD_MULTIPLY
WXK_NUMPAD_ADD = _core_.WXK_NUMPAD_ADD
WXK_NUMPAD_SEPARATOR = _core_.WXK_NUMPAD_SEPARATOR
WXK_NUMPAD_SUBTRACT = _core_.WXK_NUMPAD_SUBTRACT
WXK_NUMPAD_DECIMAL = _core_.WXK_NUMPAD_DECIMAL
WXK_NUMPAD_DIVIDE = _core_.WXK_NUMPAD_DIVIDE
WXK_WINDOWS_LEFT = _core_.WXK_WINDOWS_LEFT
WXK_WINDOWS_RIGHT = _core_.WXK_WINDOWS_RIGHT
WXK_WINDOWS_MENU = _core_.WXK_WINDOWS_MENU
WXK_COMMAND = _core_.WXK_COMMAND
WXK_SPECIAL1 = _core_.WXK_SPECIAL1
WXK_SPECIAL2 = _core_.WXK_SPECIAL2
WXK_SPECIAL3 = _core_.WXK_SPECIAL3
WXK_SPECIAL4 = _core_.WXK_SPECIAL4
WXK_SPECIAL5 = _core_.WXK_SPECIAL5
WXK_SPECIAL6 = _core_.WXK_SPECIAL6
WXK_SPECIAL7 = _core_.WXK_SPECIAL7
WXK_SPECIAL8 = _core_.WXK_SPECIAL8
WXK_SPECIAL9 = _core_.WXK_SPECIAL9
WXK_SPECIAL10 = _core_.WXK_SPECIAL10
WXK_SPECIAL11 = _core_.WXK_SPECIAL11
WXK_SPECIAL12 = _core_.WXK_SPECIAL12
WXK_SPECIAL13 = _core_.WXK_SPECIAL13
WXK_SPECIAL14 = _core_.WXK_SPECIAL14
WXK_SPECIAL15 = _core_.WXK_SPECIAL15
WXK_SPECIAL16 = _core_.WXK_SPECIAL16
WXK_SPECIAL17 = _core_.WXK_SPECIAL17
WXK_SPECIAL18 = _core_.WXK_SPECIAL18
WXK_SPECIAL19 = _core_.WXK_SPECIAL19
WXK_SPECIAL20 = _core_.WXK_SPECIAL20
PAPER_NONE = _core_.PAPER_NONE
PAPER_LETTER = _core_.PAPER_LETTER
PAPER_LEGAL = _core_.PAPER_LEGAL
PAPER_A4 = _core_.PAPER_A4
PAPER_CSHEET = _core_.PAPER_CSHEET
PAPER_DSHEET = _core_.PAPER_DSHEET
PAPER_ESHEET = _core_.PAPER_ESHEET
PAPER_LETTERSMALL = _core_.PAPER_LETTERSMALL
PAPER_TABLOID = _core_.PAPER_TABLOID
PAPER_LEDGER = _core_.PAPER_LEDGER
PAPER_STATEMENT = _core_.PAPER_STATEMENT
PAPER_EXECUTIVE = _core_.PAPER_EXECUTIVE
PAPER_A3 = _core_.PAPER_A3
PAPER_A4SMALL = _core_.PAPER_A4SMALL
PAPER_A5 = _core_.PAPER_A5
PAPER_B4 = _core_.PAPER_B4
PAPER_B5 = _core_.PAPER_B5
PAPER_FOLIO = _core_.PAPER_FOLIO
PAPER_QUARTO = _core_.PAPER_QUARTO
PAPER_10X14 = _core_.PAPER_10X14
PAPER_11X17 = _core_.PAPER_11X17
PAPER_NOTE = _core_.PAPER_NOTE
PAPER_ENV_9 = _core_.PAPER_ENV_9
PAPER_ENV_10 = _core_.PAPER_ENV_10
PAPER_ENV_11 = _core_.PAPER_ENV_11
PAPER_ENV_12 = _core_.PAPER_ENV_12
PAPER_ENV_14 = _core_.PAPER_ENV_14
PAPER_ENV_DL = _core_.PAPER_ENV_DL
PAPER_ENV_C5 = _core_.PAPER_ENV_C5
PAPER_ENV_C3 = _core_.PAPER_ENV_C3
PAPER_ENV_C4 = _core_.PAPER_ENV_C4
PAPER_ENV_C6 = _core_.PAPER_ENV_C6
PAPER_ENV_C65 = _core_.PAPER_ENV_C65
PAPER_ENV_B4 = _core_.PAPER_ENV_B4
PAPER_ENV_B5 = _core_.PAPER_ENV_B5
PAPER_ENV_B6 = _core_.PAPER_ENV_B6
PAPER_ENV_ITALY = _core_.PAPER_ENV_ITALY
PAPER_ENV_MONARCH = _core_.PAPER_ENV_MONARCH
PAPER_ENV_PERSONAL = _core_.PAPER_ENV_PERSONAL
PAPER_FANFOLD_US = _core_.PAPER_FANFOLD_US
PAPER_FANFOLD_STD_GERMAN = _core_.PAPER_FANFOLD_STD_GERMAN
PAPER_FANFOLD_LGL_GERMAN = _core_.PAPER_FANFOLD_LGL_GERMAN
PAPER_ISO_B4 = _core_.PAPER_ISO_B4
PAPER_JAPANESE_POSTCARD = _core_.PAPER_JAPANESE_POSTCARD
PAPER_9X11 = _core_.PAPER_9X11
PAPER_10X11 = _core_.PAPER_10X11
PAPER_15X11 = _core_.PAPER_15X11
PAPER_ENV_INVITE = _core_.PAPER_ENV_INVITE
PAPER_LETTER_EXTRA = _core_.PAPER_LETTER_EXTRA
PAPER_LEGAL_EXTRA = _core_.PAPER_LEGAL_EXTRA
PAPER_TABLOID_EXTRA = _core_.PAPER_TABLOID_EXTRA
PAPER_A4_EXTRA = _core_.PAPER_A4_EXTRA
PAPER_LETTER_TRANSVERSE = _core_.PAPER_LETTER_TRANSVERSE
PAPER_A4_TRANSVERSE = _core_.PAPER_A4_TRANSVERSE
PAPER_LETTER_EXTRA_TRANSVERSE = _core_.PAPER_LETTER_EXTRA_TRANSVERSE
PAPER_A_PLUS = _core_.PAPER_A_PLUS
PAPER_B_PLUS = _core_.PAPER_B_PLUS
PAPER_LETTER_PLUS = _core_.PAPER_LETTER_PLUS
PAPER_A4_PLUS = _core_.PAPER_A4_PLUS
PAPER_A5_TRANSVERSE = _core_.PAPER_A5_TRANSVERSE
PAPER_B5_TRANSVERSE = _core_.PAPER_B5_TRANSVERSE
PAPER_A3_EXTRA = _core_.PAPER_A3_EXTRA
PAPER_A5_EXTRA = _core_.PAPER_A5_EXTRA
PAPER_B5_EXTRA = _core_.PAPER_B5_EXTRA
PAPER_A2 = _core_.PAPER_A2
PAPER_A3_TRANSVERSE = _core_.PAPER_A3_TRANSVERSE
PAPER_A3_EXTRA_TRANSVERSE = _core_.PAPER_A3_EXTRA_TRANSVERSE
PAPER_DBL_JAPANESE_POSTCARD = _core_.PAPER_DBL_JAPANESE_POSTCARD
PAPER_A6 = _core_.PAPER_A6
PAPER_JENV_KAKU2 = _core_.PAPER_JENV_KAKU2
PAPER_JENV_KAKU3 = _core_.PAPER_JENV_KAKU3
PAPER_JENV_CHOU3 = _core_.PAPER_JENV_CHOU3
PAPER_JENV_CHOU4 = _core_.PAPER_JENV_CHOU4
PAPER_LETTER_ROTATED = _core_.PAPER_LETTER_ROTATED
PAPER_A3_ROTATED = _core_.PAPER_A3_ROTATED
PAPER_A4_ROTATED = _core_.PAPER_A4_ROTATED
PAPER_A5_ROTATED = _core_.PAPER_A5_ROTATED
PAPER_B4_JIS_ROTATED = _core_.PAPER_B4_JIS_ROTATED
PAPER_B5_JIS_ROTATED = _core_.PAPER_B5_JIS_ROTATED
PAPER_JAPANESE_POSTCARD_ROTATED = _core_.PAPER_JAPANESE_POSTCARD_ROTATED
PAPER_DBL_JAPANESE_POSTCARD_ROTATED = _core_.PAPER_DBL_JAPANESE_POSTCARD_ROTATED
PAPER_A6_ROTATED = _core_.PAPER_A6_ROTATED
PAPER_JENV_KAKU2_ROTATED = _core_.PAPER_JENV_KAKU2_ROTATED
PAPER_JENV_KAKU3_ROTATED = _core_.PAPER_JENV_KAKU3_ROTATED
PAPER_JENV_CHOU3_ROTATED = _core_.PAPER_JENV_CHOU3_ROTATED
PAPER_JENV_CHOU4_ROTATED = _core_.PAPER_JENV_CHOU4_ROTATED
PAPER_B6_JIS = _core_.PAPER_B6_JIS
PAPER_B6_JIS_ROTATED = _core_.PAPER_B6_JIS_ROTATED
PAPER_12X11 = _core_.PAPER_12X11
PAPER_JENV_YOU4 = _core_.PAPER_JENV_YOU4
PAPER_JENV_YOU4_ROTATED = _core_.PAPER_JENV_YOU4_ROTATED
PAPER_P16K = _core_.PAPER_P16K
PAPER_P32K = _core_.PAPER_P32K
PAPER_P32KBIG = _core_.PAPER_P32KBIG
PAPER_PENV_1 = _core_.PAPER_PENV_1
PAPER_PENV_2 = _core_.PAPER_PENV_2
PAPER_PENV_3 = _core_.PAPER_PENV_3
PAPER_PENV_4 = _core_.PAPER_PENV_4
PAPER_PENV_5 = _core_.PAPER_PENV_5
PAPER_PENV_6 = _core_.PAPER_PENV_6
PAPER_PENV_7 = _core_.PAPER_PENV_7
PAPER_PENV_8 = _core_.PAPER_PENV_8
PAPER_PENV_9 = _core_.PAPER_PENV_9
PAPER_PENV_10 = _core_.PAPER_PENV_10
PAPER_P16K_ROTATED = _core_.PAPER_P16K_ROTATED
PAPER_P32K_ROTATED = _core_.PAPER_P32K_ROTATED
PAPER_P32KBIG_ROTATED = _core_.PAPER_P32KBIG_ROTATED
PAPER_PENV_1_ROTATED = _core_.PAPER_PENV_1_ROTATED
PAPER_PENV_2_ROTATED = _core_.PAPER_PENV_2_ROTATED
PAPER_PENV_3_ROTATED = _core_.PAPER_PENV_3_ROTATED
PAPER_PENV_4_ROTATED = _core_.PAPER_PENV_4_ROTATED
PAPER_PENV_5_ROTATED = _core_.PAPER_PENV_5_ROTATED
PAPER_PENV_6_ROTATED = _core_.PAPER_PENV_6_ROTATED
PAPER_PENV_7_ROTATED = _core_.PAPER_PENV_7_ROTATED
PAPER_PENV_8_ROTATED = _core_.PAPER_PENV_8_ROTATED
PAPER_PENV_9_ROTATED = _core_.PAPER_PENV_9_ROTATED
PAPER_PENV_10_ROTATED = _core_.PAPER_PENV_10_ROTATED
DUPLEX_SIMPLEX = _core_.DUPLEX_SIMPLEX
DUPLEX_HORIZONTAL = _core_.DUPLEX_HORIZONTAL
DUPLEX_VERTICAL = _core_.DUPLEX_VERTICAL
ITEM_SEPARATOR = _core_.ITEM_SEPARATOR
ITEM_NORMAL = _core_.ITEM_NORMAL
ITEM_CHECK = _core_.ITEM_CHECK
ITEM_RADIO = _core_.ITEM_RADIO
ITEM_MAX = _core_.ITEM_MAX
HT_NOWHERE = _core_.HT_NOWHERE
HT_SCROLLBAR_FIRST = _core_.HT_SCROLLBAR_FIRST
HT_SCROLLBAR_ARROW_LINE_1 = _core_.HT_SCROLLBAR_ARROW_LINE_1
HT_SCROLLBAR_ARROW_LINE_2 = _core_.HT_SCROLLBAR_ARROW_LINE_2
HT_SCROLLBAR_ARROW_PAGE_1 = _core_.HT_SCROLLBAR_ARROW_PAGE_1
HT_SCROLLBAR_ARROW_PAGE_2 = _core_.HT_SCROLLBAR_ARROW_PAGE_2
HT_SCROLLBAR_THUMB = _core_.HT_SCROLLBAR_THUMB
HT_SCROLLBAR_BAR_1 = _core_.HT_SCROLLBAR_BAR_1
HT_SCROLLBAR_BAR_2 = _core_.HT_SCROLLBAR_BAR_2
HT_SCROLLBAR_LAST = _core_.HT_SCROLLBAR_LAST
HT_WINDOW_OUTSIDE = _core_.HT_WINDOW_OUTSIDE
HT_WINDOW_INSIDE = _core_.HT_WINDOW_INSIDE
HT_WINDOW_VERT_SCROLLBAR = _core_.HT_WINDOW_VERT_SCROLLBAR
HT_WINDOW_HORZ_SCROLLBAR = _core_.HT_WINDOW_HORZ_SCROLLBAR
HT_WINDOW_CORNER = _core_.HT_WINDOW_CORNER
HT_MAX = _core_.HT_MAX
MOD_NONE = _core_.MOD_NONE
MOD_ALT = _core_.MOD_ALT
MOD_CONTROL = _core_.MOD_CONTROL
MOD_ALTGR = _core_.MOD_ALTGR
MOD_SHIFT = _core_.MOD_SHIFT
MOD_META = _core_.MOD_META
MOD_WIN = _core_.MOD_WIN
MOD_CMD = _core_.MOD_CMD
MOD_ALL = _core_.MOD_ALL
UPDATE_UI_NONE = _core_.UPDATE_UI_NONE
UPDATE_UI_RECURSE = _core_.UPDATE_UI_RECURSE
UPDATE_UI_FROMIDLE = _core_.UPDATE_UI_FROMIDLE
NOTIFY_NONE = _core_.NOTIFY_NONE
NOTIFY_ONCE = _core_.NOTIFY_ONCE
NOTIFY_REPEAT = _core_.NOTIFY_REPEAT
Layout_Default = _core_.Layout_Default
Layout_LeftToRight = _core_.Layout_LeftToRight
Layout_RightToLeft = _core_.Layout_RightToLeft

class Object(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetClassName(*args, **kwargs):
        return _core_.Object_GetClassName(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _core_.Object_Destroy(*args, **kwargs)

    def IsSameAs(*args, **kwargs):
        return _core_.Object_IsSameAs(*args, **kwargs)

    ClassName = property(GetClassName, doc='See `GetClassName`')


_core_.Object_swigregister(Object)
_wxPySetDictionary = _core_._wxPySetDictionary
cvar = _core_.cvar
EmptyString = cvar.EmptyString
BITMAP_TYPE_INVALID = _core_.BITMAP_TYPE_INVALID
BITMAP_TYPE_BMP = _core_.BITMAP_TYPE_BMP
BITMAP_TYPE_ICO = _core_.BITMAP_TYPE_ICO
BITMAP_TYPE_CUR = _core_.BITMAP_TYPE_CUR
BITMAP_TYPE_XBM = _core_.BITMAP_TYPE_XBM
BITMAP_TYPE_XBM_DATA = _core_.BITMAP_TYPE_XBM_DATA
BITMAP_TYPE_XPM = _core_.BITMAP_TYPE_XPM
BITMAP_TYPE_XPM_DATA = _core_.BITMAP_TYPE_XPM_DATA
BITMAP_TYPE_TIF = _core_.BITMAP_TYPE_TIF
BITMAP_TYPE_GIF = _core_.BITMAP_TYPE_GIF
BITMAP_TYPE_PNG = _core_.BITMAP_TYPE_PNG
BITMAP_TYPE_JPEG = _core_.BITMAP_TYPE_JPEG
BITMAP_TYPE_PNM = _core_.BITMAP_TYPE_PNM
BITMAP_TYPE_PCX = _core_.BITMAP_TYPE_PCX
BITMAP_TYPE_PICT = _core_.BITMAP_TYPE_PICT
BITMAP_TYPE_ICON = _core_.BITMAP_TYPE_ICON
BITMAP_TYPE_ANI = _core_.BITMAP_TYPE_ANI
BITMAP_TYPE_IFF = _core_.BITMAP_TYPE_IFF
BITMAP_TYPE_TGA = _core_.BITMAP_TYPE_TGA
BITMAP_TYPE_MACCURSOR = _core_.BITMAP_TYPE_MACCURSOR
BITMAP_TYPE_ANY = _core_.BITMAP_TYPE_ANY
CURSOR_NONE = _core_.CURSOR_NONE
CURSOR_ARROW = _core_.CURSOR_ARROW
CURSOR_RIGHT_ARROW = _core_.CURSOR_RIGHT_ARROW
CURSOR_BULLSEYE = _core_.CURSOR_BULLSEYE
CURSOR_CHAR = _core_.CURSOR_CHAR
CURSOR_CROSS = _core_.CURSOR_CROSS
CURSOR_HAND = _core_.CURSOR_HAND
CURSOR_IBEAM = _core_.CURSOR_IBEAM
CURSOR_LEFT_BUTTON = _core_.CURSOR_LEFT_BUTTON
CURSOR_MAGNIFIER = _core_.CURSOR_MAGNIFIER
CURSOR_MIDDLE_BUTTON = _core_.CURSOR_MIDDLE_BUTTON
CURSOR_NO_ENTRY = _core_.CURSOR_NO_ENTRY
CURSOR_PAINT_BRUSH = _core_.CURSOR_PAINT_BRUSH
CURSOR_PENCIL = _core_.CURSOR_PENCIL
CURSOR_POINT_LEFT = _core_.CURSOR_POINT_LEFT
CURSOR_POINT_RIGHT = _core_.CURSOR_POINT_RIGHT
CURSOR_QUESTION_ARROW = _core_.CURSOR_QUESTION_ARROW
CURSOR_RIGHT_BUTTON = _core_.CURSOR_RIGHT_BUTTON
CURSOR_SIZENESW = _core_.CURSOR_SIZENESW
CURSOR_SIZENS = _core_.CURSOR_SIZENS
CURSOR_SIZENWSE = _core_.CURSOR_SIZENWSE
CURSOR_SIZEWE = _core_.CURSOR_SIZEWE
CURSOR_SIZING = _core_.CURSOR_SIZING
CURSOR_SPRAYCAN = _core_.CURSOR_SPRAYCAN
CURSOR_WAIT = _core_.CURSOR_WAIT
CURSOR_WATCH = _core_.CURSOR_WATCH
CURSOR_BLANK = _core_.CURSOR_BLANK
CURSOR_DEFAULT = _core_.CURSOR_DEFAULT
CURSOR_COPY_ARROW = _core_.CURSOR_COPY_ARROW
CURSOR_ARROWWAIT = _core_.CURSOR_ARROWWAIT
CURSOR_MAX = _core_.CURSOR_MAX

class Size(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    width = property(_core_.Size_width_get, _core_.Size_width_set)
    height = property(_core_.Size_height_get, _core_.Size_height_set)
    x = width
    y = height

    def __init__(self, *args, **kwargs):
        _core_.Size_swiginit(self, _core_.new_Size(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Size
    __del__ = lambda self: None

    def __eq__(*args, **kwargs):
        return _core_.Size___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.Size___ne__(*args, **kwargs)

    def __add__(*args, **kwargs):
        return _core_.Size___add__(*args, **kwargs)

    def __sub__(*args, **kwargs):
        return _core_.Size___sub__(*args, **kwargs)

    def IncTo(*args, **kwargs):
        return _core_.Size_IncTo(*args, **kwargs)

    def DecTo(*args, **kwargs):
        return _core_.Size_DecTo(*args, **kwargs)

    def IncBy(*args, **kwargs):
        return _core_.Size_IncBy(*args, **kwargs)

    def DecBy(*args, **kwargs):
        return _core_.Size_DecBy(*args, **kwargs)

    def Scale(*args, **kwargs):
        return _core_.Size_Scale(*args, **kwargs)

    def Set(*args, **kwargs):
        return _core_.Size_Set(*args, **kwargs)

    def SetWidth(*args, **kwargs):
        return _core_.Size_SetWidth(*args, **kwargs)

    def SetHeight(*args, **kwargs):
        return _core_.Size_SetHeight(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _core_.Size_GetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _core_.Size_GetHeight(*args, **kwargs)

    def IsFullySpecified(*args, **kwargs):
        return _core_.Size_IsFullySpecified(*args, **kwargs)

    def SetDefaults(*args, **kwargs):
        return _core_.Size_SetDefaults(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.Size_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.Size' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.width = val
        elif index == 1:
            self.height = val
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0, 0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.Size, self.Get())


_core_.Size_swigregister(Size)

class RealPoint(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    x = property(_core_.RealPoint_x_get, _core_.RealPoint_x_set)
    y = property(_core_.RealPoint_y_get, _core_.RealPoint_y_set)

    def __init__(self, *args, **kwargs):
        _core_.RealPoint_swiginit(self, _core_.new_RealPoint(*args, **kwargs))

    __swig_destroy__ = _core_.delete_RealPoint
    __del__ = lambda self: None

    def __eq__(*args, **kwargs):
        return _core_.RealPoint___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.RealPoint___ne__(*args, **kwargs)

    def __add__(*args, **kwargs):
        return _core_.RealPoint___add__(*args, **kwargs)

    def __sub__(*args, **kwargs):
        return _core_.RealPoint___sub__(*args, **kwargs)

    def Set(*args, **kwargs):
        return _core_.RealPoint_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.RealPoint_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.RealPoint' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.x = val
        elif index == 1:
            self.y = val
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0.0, 0.0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.RealPoint, self.Get())


_core_.RealPoint_swigregister(RealPoint)

class Point(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    x = property(_core_.Point_x_get, _core_.Point_x_set)
    y = property(_core_.Point_y_get, _core_.Point_y_set)

    def __init__(self, *args, **kwargs):
        _core_.Point_swiginit(self, _core_.new_Point(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Point
    __del__ = lambda self: None

    def __eq__(*args, **kwargs):
        return _core_.Point___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.Point___ne__(*args, **kwargs)

    def __add__(*args, **kwargs):
        return _core_.Point___add__(*args, **kwargs)

    def __sub__(*args, **kwargs):
        return _core_.Point___sub__(*args, **kwargs)

    def __iadd__(*args, **kwargs):
        return _core_.Point___iadd__(*args, **kwargs)

    def __isub__(*args, **kwargs):
        return _core_.Point___isub__(*args, **kwargs)

    def Set(*args, **kwargs):
        return _core_.Point_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.Point_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.Point' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.x = val
        elif index == 1:
            self.y = val
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0, 0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.Point, self.Get())


_core_.Point_swigregister(Point)

class Rect(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Rect_swiginit(self, _core_.new_Rect(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Rect
    __del__ = lambda self: None

    def GetX(*args, **kwargs):
        return _core_.Rect_GetX(*args, **kwargs)

    def SetX(*args, **kwargs):
        return _core_.Rect_SetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _core_.Rect_GetY(*args, **kwargs)

    def SetY(*args, **kwargs):
        return _core_.Rect_SetY(*args, **kwargs)

    def GetWidth(*args, **kwargs):
        return _core_.Rect_GetWidth(*args, **kwargs)

    def SetWidth(*args, **kwargs):
        return _core_.Rect_SetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _core_.Rect_GetHeight(*args, **kwargs)

    def SetHeight(*args, **kwargs):
        return _core_.Rect_SetHeight(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.Rect_GetPosition(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _core_.Rect_SetPosition(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _core_.Rect_GetSize(*args, **kwargs)

    def SetSize(*args, **kwargs):
        return _core_.Rect_SetSize(*args, **kwargs)

    def IsEmpty(*args, **kwargs):
        return _core_.Rect_IsEmpty(*args, **kwargs)

    def GetTopLeft(*args, **kwargs):
        return _core_.Rect_GetTopLeft(*args, **kwargs)

    def SetTopLeft(*args, **kwargs):
        return _core_.Rect_SetTopLeft(*args, **kwargs)

    def GetBottomRight(*args, **kwargs):
        return _core_.Rect_GetBottomRight(*args, **kwargs)

    def SetBottomRight(*args, **kwargs):
        return _core_.Rect_SetBottomRight(*args, **kwargs)

    def GetTopRight(*args, **kwargs):
        return _core_.Rect_GetTopRight(*args, **kwargs)

    def SetTopRight(*args, **kwargs):
        return _core_.Rect_SetTopRight(*args, **kwargs)

    def GetBottomLeft(*args, **kwargs):
        return _core_.Rect_GetBottomLeft(*args, **kwargs)

    def SetBottomLeft(*args, **kwargs):
        return _core_.Rect_SetBottomLeft(*args, **kwargs)

    def GetLeft(*args, **kwargs):
        return _core_.Rect_GetLeft(*args, **kwargs)

    def GetTop(*args, **kwargs):
        return _core_.Rect_GetTop(*args, **kwargs)

    def GetBottom(*args, **kwargs):
        return _core_.Rect_GetBottom(*args, **kwargs)

    def GetRight(*args, **kwargs):
        return _core_.Rect_GetRight(*args, **kwargs)

    def SetLeft(*args, **kwargs):
        return _core_.Rect_SetLeft(*args, **kwargs)

    def SetRight(*args, **kwargs):
        return _core_.Rect_SetRight(*args, **kwargs)

    def SetTop(*args, **kwargs):
        return _core_.Rect_SetTop(*args, **kwargs)

    def SetBottom(*args, **kwargs):
        return _core_.Rect_SetBottom(*args, **kwargs)

    position = property(GetPosition, SetPosition)
    size = property(GetSize, SetSize)
    left = property(GetLeft, SetLeft)
    right = property(GetRight, SetRight)
    top = property(GetTop, SetTop)
    bottom = property(GetBottom, SetBottom)

    def Inflate(*args, **kwargs):
        return _core_.Rect_Inflate(*args, **kwargs)

    def Deflate(*args, **kwargs):
        return _core_.Rect_Deflate(*args, **kwargs)

    def OffsetXY(*args, **kwargs):
        return _core_.Rect_OffsetXY(*args, **kwargs)

    def Offset(*args, **kwargs):
        return _core_.Rect_Offset(*args, **kwargs)

    def Intersect(*args, **kwargs):
        return _core_.Rect_Intersect(*args, **kwargs)

    def Union(*args, **kwargs):
        return _core_.Rect_Union(*args, **kwargs)

    def __add__(*args, **kwargs):
        return _core_.Rect___add__(*args, **kwargs)

    def __iadd__(*args, **kwargs):
        return _core_.Rect___iadd__(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _core_.Rect___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.Rect___ne__(*args, **kwargs)

    def ContainsXY(*args, **kwargs):
        return _core_.Rect_ContainsXY(*args, **kwargs)

    def Contains(*args, **kwargs):
        return _core_.Rect_Contains(*args, **kwargs)

    def ContainsRect(*args, **kwargs):
        return _core_.Rect_ContainsRect(*args, **kwargs)

    Inside = Contains
    InsideXY = ContainsXY
    InsideRect = ContainsRect

    def Intersects(*args, **kwargs):
        return _core_.Rect_Intersects(*args, **kwargs)

    def CenterIn(*args, **kwargs):
        return _core_.Rect_CenterIn(*args, **kwargs)

    CentreIn = CenterIn
    x = property(_core_.Rect_x_get, _core_.Rect_x_set)
    y = property(_core_.Rect_y_get, _core_.Rect_y_set)
    width = property(_core_.Rect_width_get, _core_.Rect_width_set)
    height = property(_core_.Rect_height_get, _core_.Rect_height_set)

    def Set(*args, **kwargs):
        return _core_.Rect_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.Rect_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.Rect' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.x = val
        elif index == 1:
            self.y = val
        elif index == 2:
            self.width = val
        elif index == 3:
            self.height = val
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0, 0, 0, 0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.Rect, self.Get())

    Bottom = property(GetBottom, SetBottom, doc='See `GetBottom` and `SetBottom`')
    BottomRight = property(GetBottomRight, SetBottomRight, doc='See `GetBottomRight` and `SetBottomRight`')
    BottomLeft = property(GetBottomLeft, SetBottomLeft, doc='See `GetBottomLeft` and `SetBottomLeft`')
    Height = property(GetHeight, SetHeight, doc='See `GetHeight` and `SetHeight`')
    Left = property(GetLeft, SetLeft, doc='See `GetLeft` and `SetLeft`')
    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')
    Right = property(GetRight, SetRight, doc='See `GetRight` and `SetRight`')
    Size = property(GetSize, SetSize, doc='See `GetSize` and `SetSize`')
    Top = property(GetTop, SetTop, doc='See `GetTop` and `SetTop`')
    TopLeft = property(GetTopLeft, SetTopLeft, doc='See `GetTopLeft` and `SetTopLeft`')
    TopRight = property(GetTopRight, SetTopRight, doc='See `GetTopRight` and `SetTopRight`')
    Width = property(GetWidth, SetWidth, doc='See `GetWidth` and `SetWidth`')
    X = property(GetX, SetX, doc='See `GetX` and `SetX`')
    Y = property(GetY, SetY, doc='See `GetY` and `SetY`')
    Empty = property(IsEmpty, doc='See `IsEmpty`')


_core_.Rect_swigregister(Rect)

def RectPP(*args, **kwargs):
    val = _core_.new_RectPP(*args, **kwargs)
    return val


def RectPS(*args, **kwargs):
    val = _core_.new_RectPS(*args, **kwargs)
    return val


def RectS(*args, **kwargs):
    val = _core_.new_RectS(*args, **kwargs)
    return val


def IntersectRect(*args, **kwargs):
    return _core_.IntersectRect(*args, **kwargs)


class Point2D(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Point2D_swiginit(self, _core_.new_Point2D(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Point2D
    __del__ = lambda self: None

    def GetFloor(*args, **kwargs):
        return _core_.Point2D_GetFloor(*args, **kwargs)

    def GetRounded(*args, **kwargs):
        return _core_.Point2D_GetRounded(*args, **kwargs)

    def GetVectorLength(*args, **kwargs):
        return _core_.Point2D_GetVectorLength(*args, **kwargs)

    def GetVectorAngle(*args, **kwargs):
        return _core_.Point2D_GetVectorAngle(*args, **kwargs)

    def SetVectorLength(*args, **kwargs):
        return _core_.Point2D_SetVectorLength(*args, **kwargs)

    def SetVectorAngle(*args, **kwargs):
        return _core_.Point2D_SetVectorAngle(*args, **kwargs)

    def SetPolarCoordinates(self, angle, length):
        self.SetVectorLength(length)
        self.SetVectorAngle(angle)

    def Normalize(self):
        self.SetVectorLength(1.0)

    def GetDistance(*args, **kwargs):
        return _core_.Point2D_GetDistance(*args, **kwargs)

    def GetDistanceSquare(*args, **kwargs):
        return _core_.Point2D_GetDistanceSquare(*args, **kwargs)

    def GetDotProduct(*args, **kwargs):
        return _core_.Point2D_GetDotProduct(*args, **kwargs)

    def GetCrossProduct(*args, **kwargs):
        return _core_.Point2D_GetCrossProduct(*args, **kwargs)

    def __neg__(*args, **kwargs):
        return _core_.Point2D___neg__(*args, **kwargs)

    def __iadd__(*args, **kwargs):
        return _core_.Point2D___iadd__(*args, **kwargs)

    def __isub__(*args, **kwargs):
        return _core_.Point2D___isub__(*args, **kwargs)

    def __imul__(*args):
        return _core_.Point2D___imul__(*args)

    def __idiv__(*args):
        return _core_.Point2D___idiv__(*args)

    def __add__(*args):
        return _core_.Point2D___add__(*args)

    def __sub__(*args):
        return _core_.Point2D___sub__(*args)

    def __mul__(*args):
        return _core_.Point2D___mul__(*args)

    def __div__(*args):
        return _core_.Point2D___div__(*args)

    def __eq__(*args, **kwargs):
        return _core_.Point2D___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.Point2D___ne__(*args, **kwargs)

    x = property(_core_.Point2D_x_get, _core_.Point2D_x_set)
    y = property(_core_.Point2D_y_get, _core_.Point2D_y_set)

    def Set(*args, **kwargs):
        return _core_.Point2D_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.Point2D_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.Point2D' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.x = val
        elif index == 1:
            self.y = val
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0.0, 0.0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.Point2D, self.Get())

    Floor = property(GetFloor, doc='See `GetFloor`')
    Rounded = property(GetRounded, doc='See `GetRounded`')
    VectorAngle = property(GetVectorAngle, SetVectorAngle, doc='See `GetVectorAngle` and `SetVectorAngle`')
    VectorLength = property(GetVectorLength, SetVectorLength, doc='See `GetVectorLength` and `SetVectorLength`')


_core_.Point2D_swigregister(Point2D)

def Point2DCopy(*args, **kwargs):
    val = _core_.new_Point2DCopy(*args, **kwargs)
    return val


def Point2DFromPoint(*args, **kwargs):
    val = _core_.new_Point2DFromPoint(*args, **kwargs)
    return val


Inside = _core_.Inside
OutLeft = _core_.OutLeft
OutRight = _core_.OutRight
OutTop = _core_.OutTop
OutBottom = _core_.OutBottom

class Rect2D(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Rect2D_swiginit(self, _core_.new_Rect2D(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Rect2D
    __del__ = lambda self: None

    def GetPosition(*args, **kwargs):
        return _core_.Rect2D_GetPosition(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _core_.Rect2D_GetSize(*args, **kwargs)

    def GetLeft(*args, **kwargs):
        return _core_.Rect2D_GetLeft(*args, **kwargs)

    def SetLeft(*args, **kwargs):
        return _core_.Rect2D_SetLeft(*args, **kwargs)

    def MoveLeftTo(*args, **kwargs):
        return _core_.Rect2D_MoveLeftTo(*args, **kwargs)

    def GetTop(*args, **kwargs):
        return _core_.Rect2D_GetTop(*args, **kwargs)

    def SetTop(*args, **kwargs):
        return _core_.Rect2D_SetTop(*args, **kwargs)

    def MoveTopTo(*args, **kwargs):
        return _core_.Rect2D_MoveTopTo(*args, **kwargs)

    def GetBottom(*args, **kwargs):
        return _core_.Rect2D_GetBottom(*args, **kwargs)

    def SetBottom(*args, **kwargs):
        return _core_.Rect2D_SetBottom(*args, **kwargs)

    def MoveBottomTo(*args, **kwargs):
        return _core_.Rect2D_MoveBottomTo(*args, **kwargs)

    def GetRight(*args, **kwargs):
        return _core_.Rect2D_GetRight(*args, **kwargs)

    def SetRight(*args, **kwargs):
        return _core_.Rect2D_SetRight(*args, **kwargs)

    def MoveRightTo(*args, **kwargs):
        return _core_.Rect2D_MoveRightTo(*args, **kwargs)

    def GetLeftTop(*args, **kwargs):
        return _core_.Rect2D_GetLeftTop(*args, **kwargs)

    def SetLeftTop(*args, **kwargs):
        return _core_.Rect2D_SetLeftTop(*args, **kwargs)

    def MoveLeftTopTo(*args, **kwargs):
        return _core_.Rect2D_MoveLeftTopTo(*args, **kwargs)

    def GetLeftBottom(*args, **kwargs):
        return _core_.Rect2D_GetLeftBottom(*args, **kwargs)

    def SetLeftBottom(*args, **kwargs):
        return _core_.Rect2D_SetLeftBottom(*args, **kwargs)

    def MoveLeftBottomTo(*args, **kwargs):
        return _core_.Rect2D_MoveLeftBottomTo(*args, **kwargs)

    def GetRightTop(*args, **kwargs):
        return _core_.Rect2D_GetRightTop(*args, **kwargs)

    def SetRightTop(*args, **kwargs):
        return _core_.Rect2D_SetRightTop(*args, **kwargs)

    def MoveRightTopTo(*args, **kwargs):
        return _core_.Rect2D_MoveRightTopTo(*args, **kwargs)

    def GetRightBottom(*args, **kwargs):
        return _core_.Rect2D_GetRightBottom(*args, **kwargs)

    def SetRightBottom(*args, **kwargs):
        return _core_.Rect2D_SetRightBottom(*args, **kwargs)

    def MoveRightBottomTo(*args, **kwargs):
        return _core_.Rect2D_MoveRightBottomTo(*args, **kwargs)

    def GetCentre(*args, **kwargs):
        return _core_.Rect2D_GetCentre(*args, **kwargs)

    def SetCentre(*args, **kwargs):
        return _core_.Rect2D_SetCentre(*args, **kwargs)

    def MoveCentreTo(*args, **kwargs):
        return _core_.Rect2D_MoveCentreTo(*args, **kwargs)

    def GetOutcode(*args, **kwargs):
        return _core_.Rect2D_GetOutcode(*args, **kwargs)

    def Contains(*args, **kwargs):
        return _core_.Rect2D_Contains(*args, **kwargs)

    def ContainsRect(*args, **kwargs):
        return _core_.Rect2D_ContainsRect(*args, **kwargs)

    def IsEmpty(*args, **kwargs):
        return _core_.Rect2D_IsEmpty(*args, **kwargs)

    def HaveEqualSize(*args, **kwargs):
        return _core_.Rect2D_HaveEqualSize(*args, **kwargs)

    def Inset(*args):
        return _core_.Rect2D_Inset(*args)

    def Offset(*args, **kwargs):
        return _core_.Rect2D_Offset(*args, **kwargs)

    def ConstrainTo(*args, **kwargs):
        return _core_.Rect2D_ConstrainTo(*args, **kwargs)

    def Interpolate(*args, **kwargs):
        return _core_.Rect2D_Interpolate(*args, **kwargs)

    def Intersect(*args, **kwargs):
        return _core_.Rect2D_Intersect(*args, **kwargs)

    def CreateIntersection(*args, **kwargs):
        return _core_.Rect2D_CreateIntersection(*args, **kwargs)

    def Intersects(*args, **kwargs):
        return _core_.Rect2D_Intersects(*args, **kwargs)

    def Union(*args, **kwargs):
        return _core_.Rect2D_Union(*args, **kwargs)

    def CreateUnion(*args, **kwargs):
        return _core_.Rect2D_CreateUnion(*args, **kwargs)

    def Scale(*args):
        return _core_.Rect2D_Scale(*args)

    def __eq__(*args, **kwargs):
        return _core_.Rect2D___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.Rect2D___ne__(*args, **kwargs)

    x = property(_core_.Rect2D_x_get, _core_.Rect2D_x_set)
    y = property(_core_.Rect2D_y_get, _core_.Rect2D_y_set)
    width = property(_core_.Rect2D_width_get, _core_.Rect2D_width_set)
    height = property(_core_.Rect2D_height_get, _core_.Rect2D_height_set)

    def Set(*args, **kwargs):
        return _core_.Rect2D_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.Rect2D_Get(*args, **kwargs)

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.Rect2D' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.x = val
        elif index == 1:
            self.y = val
        elif index == 2:
            self.width = val
        elif index == 3:
            self.height = val
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0.0, 0.0, 0.0, 0.0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.Rect2D, self.Get())


_core_.Rect2D_swigregister(Rect2D)
FromStart = _core_.FromStart
FromCurrent = _core_.FromCurrent
FromEnd = _core_.FromEnd

class InputStream(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.InputStream_swiginit(self, _core_.new_InputStream(*args, **kwargs))

    __swig_destroy__ = _core_.delete_InputStream
    __del__ = lambda self: None

    def close(*args, **kwargs):
        return _core_.InputStream_close(*args, **kwargs)

    def flush(*args, **kwargs):
        return _core_.InputStream_flush(*args, **kwargs)

    def eof(*args, **kwargs):
        return _core_.InputStream_eof(*args, **kwargs)

    def read(*args, **kwargs):
        return _core_.InputStream_read(*args, **kwargs)

    def readline(*args, **kwargs):
        return _core_.InputStream_readline(*args, **kwargs)

    def readlines(*args, **kwargs):
        return _core_.InputStream_readlines(*args, **kwargs)

    def seek(*args, **kwargs):
        return _core_.InputStream_seek(*args, **kwargs)

    def tell(*args, **kwargs):
        return _core_.InputStream_tell(*args, **kwargs)

    def Peek(*args, **kwargs):
        return _core_.InputStream_Peek(*args, **kwargs)

    def GetC(*args, **kwargs):
        return _core_.InputStream_GetC(*args, **kwargs)

    def LastRead(*args, **kwargs):
        return _core_.InputStream_LastRead(*args, **kwargs)

    def CanRead(*args, **kwargs):
        return _core_.InputStream_CanRead(*args, **kwargs)

    def Eof(*args, **kwargs):
        return _core_.InputStream_Eof(*args, **kwargs)

    def Ungetch(*args, **kwargs):
        return _core_.InputStream_Ungetch(*args, **kwargs)

    def SeekI(*args, **kwargs):
        return _core_.InputStream_SeekI(*args, **kwargs)

    def TellI(*args, **kwargs):
        return _core_.InputStream_TellI(*args, **kwargs)


_core_.InputStream_swigregister(InputStream)
DefaultPosition = cvar.DefaultPosition
DefaultSize = cvar.DefaultSize

class OutputStream(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.OutputStream_swiginit(self, _core_.new_OutputStream(*args, **kwargs))

    __swig_destroy__ = _core_.delete_OutputStream
    __del__ = lambda self: None

    def close(*args, **kwargs):
        return _core_.OutputStream_close(*args, **kwargs)

    def flush(*args, **kwargs):
        return _core_.OutputStream_flush(*args, **kwargs)

    def eof(*args, **kwargs):
        return _core_.OutputStream_eof(*args, **kwargs)

    def seek(*args, **kwargs):
        return _core_.OutputStream_seek(*args, **kwargs)

    def tell(*args, **kwargs):
        return _core_.OutputStream_tell(*args, **kwargs)

    def write(*args, **kwargs):
        return _core_.OutputStream_write(*args, **kwargs)

    def PutC(*args, **kwargs):
        return _core_.OutputStream_PutC(*args, **kwargs)

    def LastWrite(*args, **kwargs):
        return _core_.OutputStream_LastWrite(*args, **kwargs)

    def SeekO(*args, **kwargs):
        return _core_.OutputStream_SeekO(*args, **kwargs)

    def TellO(*args, **kwargs):
        return _core_.OutputStream_TellO(*args, **kwargs)


_core_.OutputStream_swigregister(OutputStream)
IMAGE_ALPHA_TRANSPARENT = _core_.IMAGE_ALPHA_TRANSPARENT
IMAGE_ALPHA_THRESHOLD = _core_.IMAGE_ALPHA_THRESHOLD
IMAGE_ALPHA_OPAQUE = _core_.IMAGE_ALPHA_OPAQUE
IMAGE_QUALITY_NORMAL = _core_.IMAGE_QUALITY_NORMAL
IMAGE_QUALITY_HIGH = _core_.IMAGE_QUALITY_HIGH

class ImageHandler(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetName(*args, **kwargs):
        return _core_.ImageHandler_GetName(*args, **kwargs)

    def GetExtension(*args, **kwargs):
        return _core_.ImageHandler_GetExtension(*args, **kwargs)

    def GetType(*args, **kwargs):
        return _core_.ImageHandler_GetType(*args, **kwargs)

    def GetMimeType(*args, **kwargs):
        return _core_.ImageHandler_GetMimeType(*args, **kwargs)

    def CanRead(*args, **kwargs):
        return _core_.ImageHandler_CanRead(*args, **kwargs)

    def CanReadStream(*args, **kwargs):
        return _core_.ImageHandler_CanReadStream(*args, **kwargs)

    def SetName(*args, **kwargs):
        return _core_.ImageHandler_SetName(*args, **kwargs)

    def SetExtension(*args, **kwargs):
        return _core_.ImageHandler_SetExtension(*args, **kwargs)

    def SetType(*args, **kwargs):
        return _core_.ImageHandler_SetType(*args, **kwargs)

    def SetMimeType(*args, **kwargs):
        return _core_.ImageHandler_SetMimeType(*args, **kwargs)

    Extension = property(GetExtension, SetExtension, doc='See `GetExtension` and `SetExtension`')
    MimeType = property(GetMimeType, SetMimeType, doc='See `GetMimeType` and `SetMimeType`')
    Name = property(GetName, SetName, doc='See `GetName` and `SetName`')
    Type = property(GetType, SetType, doc='See `GetType` and `SetType`')


_core_.ImageHandler_swigregister(ImageHandler)

class PyImageHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PyImageHandler_swiginit(self, _core_.new_PyImageHandler(*args, **kwargs))
        self._SetSelf(self)

    def _SetSelf(*args, **kwargs):
        return _core_.PyImageHandler__SetSelf(*args, **kwargs)


_core_.PyImageHandler_swigregister(PyImageHandler)

class ImageHistogram(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ImageHistogram_swiginit(self, _core_.new_ImageHistogram(*args, **kwargs))

    def MakeKey(*args, **kwargs):
        return _core_.ImageHistogram_MakeKey(*args, **kwargs)

    MakeKey = staticmethod(MakeKey)

    def FindFirstUnusedColour(*args, **kwargs):
        return _core_.ImageHistogram_FindFirstUnusedColour(*args, **kwargs)

    def GetCount(*args, **kwargs):
        return _core_.ImageHistogram_GetCount(*args, **kwargs)

    def GetCountRGB(*args, **kwargs):
        return _core_.ImageHistogram_GetCountRGB(*args, **kwargs)

    def GetCountColour(*args, **kwargs):
        return _core_.ImageHistogram_GetCountColour(*args, **kwargs)


_core_.ImageHistogram_swigregister(ImageHistogram)

def ImageHistogram_MakeKey(*args, **kwargs):
    return _core_.ImageHistogram_MakeKey(*args, **kwargs)


class Image_RGBValue(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Image_RGBValue_swiginit(self, _core_.new_Image_RGBValue(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Image_RGBValue
    __del__ = lambda self: None
    red = property(_core_.Image_RGBValue_red_get, _core_.Image_RGBValue_red_set)
    green = property(_core_.Image_RGBValue_green_get, _core_.Image_RGBValue_green_set)
    blue = property(_core_.Image_RGBValue_blue_get, _core_.Image_RGBValue_blue_set)


_core_.Image_RGBValue_swigregister(Image_RGBValue)

class Image_HSVValue(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Image_HSVValue_swiginit(self, _core_.new_Image_HSVValue(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Image_HSVValue
    __del__ = lambda self: None
    hue = property(_core_.Image_HSVValue_hue_get, _core_.Image_HSVValue_hue_set)
    saturation = property(_core_.Image_HSVValue_saturation_get, _core_.Image_HSVValue_saturation_set)
    value = property(_core_.Image_HSVValue_value_get, _core_.Image_HSVValue_value_set)


_core_.Image_HSVValue_swigregister(Image_HSVValue)

class Image(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Image_swiginit(self, _core_.new_Image(*args, **kwargs))

    __swig_destroy__ = _core_.delete_Image
    __del__ = lambda self: None

    def Create(*args, **kwargs):
        return _core_.Image_Create(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _core_.Image_Destroy(*args, **kwargs)

    def Scale(*args, **kwargs):
        return _core_.Image_Scale(*args, **kwargs)

    def ResampleBox(*args, **kwargs):
        return _core_.Image_ResampleBox(*args, **kwargs)

    def ResampleBicubic(*args, **kwargs):
        return _core_.Image_ResampleBicubic(*args, **kwargs)

    def Blur(*args, **kwargs):
        return _core_.Image_Blur(*args, **kwargs)

    def BlurHorizontal(*args, **kwargs):
        return _core_.Image_BlurHorizontal(*args, **kwargs)

    def BlurVertical(*args, **kwargs):
        return _core_.Image_BlurVertical(*args, **kwargs)

    def ShrinkBy(*args, **kwargs):
        return _core_.Image_ShrinkBy(*args, **kwargs)

    def Rescale(*args, **kwargs):
        return _core_.Image_Rescale(*args, **kwargs)

    def Resize(*args, **kwargs):
        return _core_.Image_Resize(*args, **kwargs)

    def SetRGB(*args, **kwargs):
        return _core_.Image_SetRGB(*args, **kwargs)

    def SetRGBRect(*args, **kwargs):
        return _core_.Image_SetRGBRect(*args, **kwargs)

    def GetRed(*args, **kwargs):
        return _core_.Image_GetRed(*args, **kwargs)

    def GetGreen(*args, **kwargs):
        return _core_.Image_GetGreen(*args, **kwargs)

    def GetBlue(*args, **kwargs):
        return _core_.Image_GetBlue(*args, **kwargs)

    def SetAlpha(*args, **kwargs):
        return _core_.Image_SetAlpha(*args, **kwargs)

    def GetAlpha(*args, **kwargs):
        return _core_.Image_GetAlpha(*args, **kwargs)

    def HasAlpha(*args, **kwargs):
        return _core_.Image_HasAlpha(*args, **kwargs)

    def InitAlpha(*args, **kwargs):
        return _core_.Image_InitAlpha(*args, **kwargs)

    def IsTransparent(*args, **kwargs):
        return _core_.Image_IsTransparent(*args, **kwargs)

    def FindFirstUnusedColour(*args, **kwargs):
        return _core_.Image_FindFirstUnusedColour(*args, **kwargs)

    def ConvertAlphaToMask(*args, **kwargs):
        return _core_.Image_ConvertAlphaToMask(*args, **kwargs)

    def ConvertColourToAlpha(*args, **kwargs):
        return _core_.Image_ConvertColourToAlpha(*args, **kwargs)

    def SetMaskFromImage(*args, **kwargs):
        return _core_.Image_SetMaskFromImage(*args, **kwargs)

    def CanRead(*args, **kwargs):
        return _core_.Image_CanRead(*args, **kwargs)

    CanRead = staticmethod(CanRead)

    def GetImageCount(*args, **kwargs):
        return _core_.Image_GetImageCount(*args, **kwargs)

    GetImageCount = staticmethod(GetImageCount)

    def LoadFile(*args, **kwargs):
        return _core_.Image_LoadFile(*args, **kwargs)

    def LoadMimeFile(*args, **kwargs):
        return _core_.Image_LoadMimeFile(*args, **kwargs)

    def SaveFile(*args, **kwargs):
        return _core_.Image_SaveFile(*args, **kwargs)

    def SaveMimeFile(*args, **kwargs):
        return _core_.Image_SaveMimeFile(*args, **kwargs)

    def SaveStream(*args, **kwargs):
        return _core_.Image_SaveStream(*args, **kwargs)

    def SaveMimeStream(*args, **kwargs):
        return _core_.Image_SaveMimeStream(*args, **kwargs)

    def CanReadStream(*args, **kwargs):
        return _core_.Image_CanReadStream(*args, **kwargs)

    CanReadStream = staticmethod(CanReadStream)

    def LoadStream(*args, **kwargs):
        return _core_.Image_LoadStream(*args, **kwargs)

    def LoadMimeStream(*args, **kwargs):
        return _core_.Image_LoadMimeStream(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _core_.Image_IsOk(*args, **kwargs)

    Ok = IsOk

    def GetWidth(*args, **kwargs):
        return _core_.Image_GetWidth(*args, **kwargs)

    def GetHeight(*args, **kwargs):
        return _core_.Image_GetHeight(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _core_.Image_GetSize(*args, **kwargs)

    def GetSubImage(*args, **kwargs):
        return _core_.Image_GetSubImage(*args, **kwargs)

    def Size(*args, **kwargs):
        return _core_.Image_Size(*args, **kwargs)

    def Copy(*args, **kwargs):
        return _core_.Image_Copy(*args, **kwargs)

    def Paste(*args, **kwargs):
        return _core_.Image_Paste(*args, **kwargs)

    def GetData(*args, **kwargs):
        return _core_.Image_GetData(*args, **kwargs)

    def SetData(*args, **kwargs):
        return _core_.Image_SetData(*args, **kwargs)

    def GetDataBuffer(*args, **kwargs):
        return _core_.Image_GetDataBuffer(*args, **kwargs)

    def SetDataBuffer(*args, **kwargs):
        return _core_.Image_SetDataBuffer(*args, **kwargs)

    def GetAlphaData(*args, **kwargs):
        return _core_.Image_GetAlphaData(*args, **kwargs)

    def SetAlphaData(*args, **kwargs):
        return _core_.Image_SetAlphaData(*args, **kwargs)

    def GetAlphaBuffer(*args, **kwargs):
        return _core_.Image_GetAlphaBuffer(*args, **kwargs)

    def SetAlphaBuffer(*args, **kwargs):
        return _core_.Image_SetAlphaBuffer(*args, **kwargs)

    def SetMaskColour(*args, **kwargs):
        return _core_.Image_SetMaskColour(*args, **kwargs)

    def GetOrFindMaskColour(*args, **kwargs):
        return _core_.Image_GetOrFindMaskColour(*args, **kwargs)

    def GetMaskRed(*args, **kwargs):
        return _core_.Image_GetMaskRed(*args, **kwargs)

    def GetMaskGreen(*args, **kwargs):
        return _core_.Image_GetMaskGreen(*args, **kwargs)

    def GetMaskBlue(*args, **kwargs):
        return _core_.Image_GetMaskBlue(*args, **kwargs)

    def SetMask(*args, **kwargs):
        return _core_.Image_SetMask(*args, **kwargs)

    def HasMask(*args, **kwargs):
        return _core_.Image_HasMask(*args, **kwargs)

    def Rotate(*args, **kwargs):
        return _core_.Image_Rotate(*args, **kwargs)

    def Rotate90(*args, **kwargs):
        return _core_.Image_Rotate90(*args, **kwargs)

    def Mirror(*args, **kwargs):
        return _core_.Image_Mirror(*args, **kwargs)

    def Replace(*args, **kwargs):
        return _core_.Image_Replace(*args, **kwargs)

    def ConvertToGreyscale(*args, **kwargs):
        return _core_.Image_ConvertToGreyscale(*args, **kwargs)

    def ConvertToMono(*args, **kwargs):
        return _core_.Image_ConvertToMono(*args, **kwargs)

    def SetOption(*args, **kwargs):
        return _core_.Image_SetOption(*args, **kwargs)

    def SetOptionInt(*args, **kwargs):
        return _core_.Image_SetOptionInt(*args, **kwargs)

    def GetOption(*args, **kwargs):
        return _core_.Image_GetOption(*args, **kwargs)

    def GetOptionInt(*args, **kwargs):
        return _core_.Image_GetOptionInt(*args, **kwargs)

    def HasOption(*args, **kwargs):
        return _core_.Image_HasOption(*args, **kwargs)

    def CountColours(*args, **kwargs):
        return _core_.Image_CountColours(*args, **kwargs)

    def ComputeHistogram(*args, **kwargs):
        return _core_.Image_ComputeHistogram(*args, **kwargs)

    def AddHandler(*args, **kwargs):
        return _core_.Image_AddHandler(*args, **kwargs)

    AddHandler = staticmethod(AddHandler)

    def InsertHandler(*args, **kwargs):
        return _core_.Image_InsertHandler(*args, **kwargs)

    InsertHandler = staticmethod(InsertHandler)

    def RemoveHandler(*args, **kwargs):
        return _core_.Image_RemoveHandler(*args, **kwargs)

    RemoveHandler = staticmethod(RemoveHandler)

    def GetHandlers(*args, **kwargs):
        return _core_.Image_GetHandlers(*args, **kwargs)

    GetHandlers = staticmethod(GetHandlers)

    def GetImageExtWildcard(*args, **kwargs):
        return _core_.Image_GetImageExtWildcard(*args, **kwargs)

    GetImageExtWildcard = staticmethod(GetImageExtWildcard)

    def ConvertToBitmap(*args, **kwargs):
        return _core_.Image_ConvertToBitmap(*args, **kwargs)

    def ConvertToMonoBitmap(*args, **kwargs):
        return _core_.Image_ConvertToMonoBitmap(*args, **kwargs)

    def RotateHue(*args, **kwargs):
        return _core_.Image_RotateHue(*args, **kwargs)

    def RGBtoHSV(*args, **kwargs):
        return _core_.Image_RGBtoHSV(*args, **kwargs)

    RGBtoHSV = staticmethod(RGBtoHSV)

    def HSVtoRGB(*args, **kwargs):
        return _core_.Image_HSVtoRGB(*args, **kwargs)

    HSVtoRGB = staticmethod(HSVtoRGB)

    def __nonzero__(self):
        return self.IsOk()

    def AdjustChannels(*args, **kwargs):
        return _core_.Image_AdjustChannels(*args, **kwargs)

    AlphaBuffer = property(GetAlphaBuffer, SetAlphaBuffer, doc='See `GetAlphaBuffer` and `SetAlphaBuffer`')
    AlphaData = property(GetAlphaData, SetAlphaData, doc='See `GetAlphaData` and `SetAlphaData`')
    Data = property(GetData, SetData, doc='See `GetData` and `SetData`')
    DataBuffer = property(GetDataBuffer, SetDataBuffer, doc='See `GetDataBuffer` and `SetDataBuffer`')
    Height = property(GetHeight, doc='See `GetHeight`')
    MaskBlue = property(GetMaskBlue, doc='See `GetMaskBlue`')
    MaskGreen = property(GetMaskGreen, doc='See `GetMaskGreen`')
    MaskRed = property(GetMaskRed, doc='See `GetMaskRed`')
    Width = property(GetWidth, doc='See `GetWidth`')


_core_.Image_swigregister(Image)

def ImageFromMime(*args, **kwargs):
    val = _core_.new_ImageFromMime(*args, **kwargs)
    return val


def ImageFromStream(*args, **kwargs):
    val = _core_.new_ImageFromStream(*args, **kwargs)
    return val


def ImageFromStreamMime(*args, **kwargs):
    val = _core_.new_ImageFromStreamMime(*args, **kwargs)
    return val


def EmptyImage(*args, **kwargs):
    val = _core_.new_EmptyImage(*args, **kwargs)
    return val


def ImageFromBitmap(*args, **kwargs):
    val = _core_.new_ImageFromBitmap(*args, **kwargs)
    return val


def ImageFromData(*args, **kwargs):
    val = _core_.new_ImageFromData(*args, **kwargs)
    return val


def ImageFromDataWithAlpha(*args, **kwargs):
    val = _core_.new_ImageFromDataWithAlpha(*args, **kwargs)
    return val


def Image_CanRead(*args, **kwargs):
    return _core_.Image_CanRead(*args, **kwargs)


def Image_GetImageCount(*args, **kwargs):
    return _core_.Image_GetImageCount(*args, **kwargs)


def Image_CanReadStream(*args, **kwargs):
    return _core_.Image_CanReadStream(*args, **kwargs)


def Image_AddHandler(*args, **kwargs):
    return _core_.Image_AddHandler(*args, **kwargs)


def Image_InsertHandler(*args, **kwargs):
    return _core_.Image_InsertHandler(*args, **kwargs)


def Image_RemoveHandler(*args, **kwargs):
    return _core_.Image_RemoveHandler(*args, **kwargs)


def Image_GetHandlers(*args):
    return _core_.Image_GetHandlers(*args)


def Image_GetImageExtWildcard(*args):
    return _core_.Image_GetImageExtWildcard(*args)


def Image_RGBtoHSV(*args, **kwargs):
    return _core_.Image_RGBtoHSV(*args, **kwargs)


def Image_HSVtoRGB(*args, **kwargs):
    return _core_.Image_HSVtoRGB(*args, **kwargs)


def _ImageFromBuffer(*args, **kwargs):
    return _core_._ImageFromBuffer(*args, **kwargs)


def ImageFromBuffer(width, height, dataBuffer, alphaBuffer = None):
    image = _core_._ImageFromBuffer(width, height, dataBuffer, alphaBuffer)
    image._buffer = dataBuffer
    image._alpha = alphaBuffer
    return image


def InitAllImageHandlers():
    pass


IMAGE_RESOLUTION_INCHES = _core_.IMAGE_RESOLUTION_INCHES
IMAGE_RESOLUTION_CM = _core_.IMAGE_RESOLUTION_CM
PNG_TYPE_COLOUR = _core_.PNG_TYPE_COLOUR
PNG_TYPE_GREY = _core_.PNG_TYPE_GREY
PNG_TYPE_GREY_RED = _core_.PNG_TYPE_GREY_RED
BMP_24BPP = _core_.BMP_24BPP
BMP_8BPP = _core_.BMP_8BPP
BMP_8BPP_GREY = _core_.BMP_8BPP_GREY
BMP_8BPP_GRAY = _core_.BMP_8BPP_GRAY
BMP_8BPP_RED = _core_.BMP_8BPP_RED
BMP_8BPP_PALETTE = _core_.BMP_8BPP_PALETTE
BMP_4BPP = _core_.BMP_4BPP
BMP_1BPP = _core_.BMP_1BPP
BMP_1BPP_BW = _core_.BMP_1BPP_BW

class BMPHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.BMPHandler_swiginit(self, _core_.new_BMPHandler(*args, **kwargs))


_core_.BMPHandler_swigregister(BMPHandler)
NullImage = cvar.NullImage
IMAGE_OPTION_FILENAME = cvar.IMAGE_OPTION_FILENAME
IMAGE_OPTION_BMP_FORMAT = cvar.IMAGE_OPTION_BMP_FORMAT
IMAGE_OPTION_CUR_HOTSPOT_X = cvar.IMAGE_OPTION_CUR_HOTSPOT_X
IMAGE_OPTION_CUR_HOTSPOT_Y = cvar.IMAGE_OPTION_CUR_HOTSPOT_Y
IMAGE_OPTION_RESOLUTION = cvar.IMAGE_OPTION_RESOLUTION
IMAGE_OPTION_RESOLUTIONX = cvar.IMAGE_OPTION_RESOLUTIONX
IMAGE_OPTION_RESOLUTIONY = cvar.IMAGE_OPTION_RESOLUTIONY
IMAGE_OPTION_RESOLUTIONUNIT = cvar.IMAGE_OPTION_RESOLUTIONUNIT
IMAGE_OPTION_QUALITY = cvar.IMAGE_OPTION_QUALITY
IMAGE_OPTION_BITSPERSAMPLE = cvar.IMAGE_OPTION_BITSPERSAMPLE
IMAGE_OPTION_SAMPLESPERPIXEL = cvar.IMAGE_OPTION_SAMPLESPERPIXEL
IMAGE_OPTION_COMPRESSION = cvar.IMAGE_OPTION_COMPRESSION
IMAGE_OPTION_IMAGEDESCRIPTOR = cvar.IMAGE_OPTION_IMAGEDESCRIPTOR
IMAGE_OPTION_PNG_FORMAT = cvar.IMAGE_OPTION_PNG_FORMAT
IMAGE_OPTION_PNG_BITDEPTH = cvar.IMAGE_OPTION_PNG_BITDEPTH

class ICOHandler(BMPHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ICOHandler_swiginit(self, _core_.new_ICOHandler(*args, **kwargs))


_core_.ICOHandler_swigregister(ICOHandler)

class CURHandler(ICOHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.CURHandler_swiginit(self, _core_.new_CURHandler(*args, **kwargs))


_core_.CURHandler_swigregister(CURHandler)

class ANIHandler(CURHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ANIHandler_swiginit(self, _core_.new_ANIHandler(*args, **kwargs))


_core_.ANIHandler_swigregister(ANIHandler)

class PNGHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PNGHandler_swiginit(self, _core_.new_PNGHandler(*args, **kwargs))


_core_.PNGHandler_swigregister(PNGHandler)

class GIFHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.GIFHandler_swiginit(self, _core_.new_GIFHandler(*args, **kwargs))


_core_.GIFHandler_swigregister(GIFHandler)

class PCXHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PCXHandler_swiginit(self, _core_.new_PCXHandler(*args, **kwargs))


_core_.PCXHandler_swigregister(PCXHandler)

class JPEGHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.JPEGHandler_swiginit(self, _core_.new_JPEGHandler(*args, **kwargs))


_core_.JPEGHandler_swigregister(JPEGHandler)

class XPMHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.XPMHandler_swiginit(self, _core_.new_XPMHandler(*args, **kwargs))


_core_.XPMHandler_swigregister(XPMHandler)

class TIFFHandler(ImageHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.TIFFHandler_swiginit(self, _core_.new_TIFFHandler(*args, **kwargs))


_core_.TIFFHandler_swigregister(TIFFHandler)
QUANTIZE_INCLUDE_WINDOWS_COLOURS = _core_.QUANTIZE_INCLUDE_WINDOWS_COLOURS
QUANTIZE_FILL_DESTINATION_IMAGE = _core_.QUANTIZE_FILL_DESTINATION_IMAGE

class Quantize(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def Quantize(*args, **kwargs):
        return _core_.Quantize_Quantize(*args, **kwargs)

    Quantize = staticmethod(Quantize)


_core_.Quantize_swigregister(Quantize)

def Quantize_Quantize(*args, **kwargs):
    return _core_.Quantize_Quantize(*args, **kwargs)


class EvtHandler(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.EvtHandler_swiginit(self, _core_.new_EvtHandler(*args, **kwargs))
        self._setOORInfo(self)

    def GetNextHandler(*args, **kwargs):
        return _core_.EvtHandler_GetNextHandler(*args, **kwargs)

    def GetPreviousHandler(*args, **kwargs):
        return _core_.EvtHandler_GetPreviousHandler(*args, **kwargs)

    def SetNextHandler(*args, **kwargs):
        return _core_.EvtHandler_SetNextHandler(*args, **kwargs)

    def SetPreviousHandler(*args, **kwargs):
        return _core_.EvtHandler_SetPreviousHandler(*args, **kwargs)

    def GetEvtHandlerEnabled(*args, **kwargs):
        return _core_.EvtHandler_GetEvtHandlerEnabled(*args, **kwargs)

    def SetEvtHandlerEnabled(*args, **kwargs):
        return _core_.EvtHandler_SetEvtHandlerEnabled(*args, **kwargs)

    def ProcessEvent(*args, **kwargs):
        return _core_.EvtHandler_ProcessEvent(*args, **kwargs)

    def AddPendingEvent(*args, **kwargs):
        return _core_.EvtHandler_AddPendingEvent(*args, **kwargs)

    def ProcessPendingEvents(*args, **kwargs):
        return _core_.EvtHandler_ProcessPendingEvents(*args, **kwargs)

    def Connect(*args, **kwargs):
        return _core_.EvtHandler_Connect(*args, **kwargs)

    def Disconnect(*args, **kwargs):
        return _core_.EvtHandler_Disconnect(*args, **kwargs)

    def _setOORInfo(*args, **kwargs):
        val = _core_.EvtHandler__setOORInfo(*args, **kwargs)
        args[0].this.own(False)
        return val

    def Bind(self, event, handler, source = None, id = wx.ID_ANY, id2 = wx.ID_ANY):
        if source is not None:
            id = source.GetId()
        event.Bind(self, id, id2, handler)

    def Unbind(self, event, source = None, id = wx.ID_ANY, id2 = wx.ID_ANY):
        if source is not None:
            id = source.GetId()
        return event.Unbind(self, id, id2)

    EvtHandlerEnabled = property(GetEvtHandlerEnabled, SetEvtHandlerEnabled, doc='See `GetEvtHandlerEnabled` and `SetEvtHandlerEnabled`')
    NextHandler = property(GetNextHandler, SetNextHandler, doc='See `GetNextHandler` and `SetNextHandler`')
    PreviousHandler = property(GetPreviousHandler, SetPreviousHandler, doc='See `GetPreviousHandler` and `SetPreviousHandler`')


_core_.EvtHandler_swigregister(EvtHandler)

class PyEvtHandler(EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PyEvtHandler_swiginit(self, _core_.new_PyEvtHandler(*args, **kwargs))
        self._setOORInfo(self)
        PyEvtHandler._setCallbackInfo(self, self, PyEvtHandler)

    def _setCallbackInfo(*args, **kwargs):
        return _core_.PyEvtHandler__setCallbackInfo(*args, **kwargs)

    def ProcessEvent(*args, **kwargs):
        return _core_.PyEvtHandler_ProcessEvent(*args, **kwargs)


_core_.PyEvtHandler_swigregister(PyEvtHandler)

class PyEventBinder(object):

    def __init__(self, evtType, expectedIDs = 0):
        if expectedIDs not in (0, 1, 2):
            raise ValueError, 'Invalid number of expectedIDs'
        self.expectedIDs = expectedIDs
        if type(evtType) == list or type(evtType) == tuple:
            self.evtType = evtType
        else:
            self.evtType = [evtType]

    def Bind(self, target, id1, id2, function):
        for et in self.evtType:
            target.Connect(id1, id2, et, function)

    def Unbind(self, target, id1, id2):
        success = 0
        for et in self.evtType:
            success += target.Disconnect(id1, id2, et)

        return success != 0

    def _getEvtType(self):
        return self.evtType[0]

    typeId = property(_getEvtType)

    def __call__(self, *args):
        assert len(args) == 2 + self.expectedIDs
        id1 = wx.ID_ANY
        id2 = wx.ID_ANY
        target = args[0]
        if self.expectedIDs == 0:
            func = args[1]
        elif self.expectedIDs == 1:
            id1 = args[1]
            func = args[2]
        elif self.expectedIDs == 2:
            id1 = args[1]
            id2 = args[2]
            func = args[3]
        else:
            raise ValueError, 'Unexpected number of IDs'
        self.Bind(target, id1, id2, func)


def EVT_COMMAND(win, id, cmd, func):
    win.Connect(id, -1, cmd, func)


def EVT_COMMAND_RANGE(win, id1, id2, cmd, func):
    win.Connect(id1, id2, cmd, func)


EVENT_PROPAGATE_NONE = _core_.EVENT_PROPAGATE_NONE
EVENT_PROPAGATE_MAX = _core_.EVENT_PROPAGATE_MAX

def NewEventType(*args):
    return _core_.NewEventType(*args)


wxEVT_NULL = _core_.wxEVT_NULL
wxEVT_FIRST = _core_.wxEVT_FIRST
wxEVT_USER_FIRST = _core_.wxEVT_USER_FIRST
wxEVT_COMMAND_BUTTON_CLICKED = _core_.wxEVT_COMMAND_BUTTON_CLICKED
wxEVT_COMMAND_CHECKBOX_CLICKED = _core_.wxEVT_COMMAND_CHECKBOX_CLICKED
wxEVT_COMMAND_CHOICE_SELECTED = _core_.wxEVT_COMMAND_CHOICE_SELECTED
wxEVT_COMMAND_LISTBOX_SELECTED = _core_.wxEVT_COMMAND_LISTBOX_SELECTED
wxEVT_COMMAND_LISTBOX_DOUBLECLICKED = _core_.wxEVT_COMMAND_LISTBOX_DOUBLECLICKED
wxEVT_COMMAND_CHECKLISTBOX_TOGGLED = _core_.wxEVT_COMMAND_CHECKLISTBOX_TOGGLED
wxEVT_COMMAND_MENU_SELECTED = _core_.wxEVT_COMMAND_MENU_SELECTED
wxEVT_COMMAND_TOOL_CLICKED = _core_.wxEVT_COMMAND_TOOL_CLICKED
wxEVT_COMMAND_SLIDER_UPDATED = _core_.wxEVT_COMMAND_SLIDER_UPDATED
wxEVT_COMMAND_RADIOBOX_SELECTED = _core_.wxEVT_COMMAND_RADIOBOX_SELECTED
wxEVT_COMMAND_RADIOBUTTON_SELECTED = _core_.wxEVT_COMMAND_RADIOBUTTON_SELECTED
wxEVT_COMMAND_SCROLLBAR_UPDATED = _core_.wxEVT_COMMAND_SCROLLBAR_UPDATED
wxEVT_COMMAND_VLBOX_SELECTED = _core_.wxEVT_COMMAND_VLBOX_SELECTED
wxEVT_COMMAND_COMBOBOX_SELECTED = _core_.wxEVT_COMMAND_COMBOBOX_SELECTED
wxEVT_COMMAND_TOOL_RCLICKED = _core_.wxEVT_COMMAND_TOOL_RCLICKED
wxEVT_COMMAND_TOOL_ENTER = _core_.wxEVT_COMMAND_TOOL_ENTER
wxEVT_LEFT_DOWN = _core_.wxEVT_LEFT_DOWN
wxEVT_LEFT_UP = _core_.wxEVT_LEFT_UP
wxEVT_MIDDLE_DOWN = _core_.wxEVT_MIDDLE_DOWN
wxEVT_MIDDLE_UP = _core_.wxEVT_MIDDLE_UP
wxEVT_RIGHT_DOWN = _core_.wxEVT_RIGHT_DOWN
wxEVT_RIGHT_UP = _core_.wxEVT_RIGHT_UP
wxEVT_MOTION = _core_.wxEVT_MOTION
wxEVT_ENTER_WINDOW = _core_.wxEVT_ENTER_WINDOW
wxEVT_LEAVE_WINDOW = _core_.wxEVT_LEAVE_WINDOW
wxEVT_LEFT_DCLICK = _core_.wxEVT_LEFT_DCLICK
wxEVT_MIDDLE_DCLICK = _core_.wxEVT_MIDDLE_DCLICK
wxEVT_RIGHT_DCLICK = _core_.wxEVT_RIGHT_DCLICK
wxEVT_SET_FOCUS = _core_.wxEVT_SET_FOCUS
wxEVT_KILL_FOCUS = _core_.wxEVT_KILL_FOCUS
wxEVT_CHILD_FOCUS = _core_.wxEVT_CHILD_FOCUS
wxEVT_MOUSEWHEEL = _core_.wxEVT_MOUSEWHEEL
wxEVT_NC_LEFT_DOWN = _core_.wxEVT_NC_LEFT_DOWN
wxEVT_NC_LEFT_UP = _core_.wxEVT_NC_LEFT_UP
wxEVT_NC_MIDDLE_DOWN = _core_.wxEVT_NC_MIDDLE_DOWN
wxEVT_NC_MIDDLE_UP = _core_.wxEVT_NC_MIDDLE_UP
wxEVT_NC_RIGHT_DOWN = _core_.wxEVT_NC_RIGHT_DOWN
wxEVT_NC_RIGHT_UP = _core_.wxEVT_NC_RIGHT_UP
wxEVT_NC_MOTION = _core_.wxEVT_NC_MOTION
wxEVT_NC_ENTER_WINDOW = _core_.wxEVT_NC_ENTER_WINDOW
wxEVT_NC_LEAVE_WINDOW = _core_.wxEVT_NC_LEAVE_WINDOW
wxEVT_NC_LEFT_DCLICK = _core_.wxEVT_NC_LEFT_DCLICK
wxEVT_NC_MIDDLE_DCLICK = _core_.wxEVT_NC_MIDDLE_DCLICK
wxEVT_NC_RIGHT_DCLICK = _core_.wxEVT_NC_RIGHT_DCLICK
wxEVT_CHAR = _core_.wxEVT_CHAR
wxEVT_CHAR_HOOK = _core_.wxEVT_CHAR_HOOK
wxEVT_NAVIGATION_KEY = _core_.wxEVT_NAVIGATION_KEY
wxEVT_KEY_DOWN = _core_.wxEVT_KEY_DOWN
wxEVT_KEY_UP = _core_.wxEVT_KEY_UP
wxEVT_HOTKEY = _core_.wxEVT_HOTKEY
wxEVT_SET_CURSOR = _core_.wxEVT_SET_CURSOR
wxEVT_SCROLL_TOP = _core_.wxEVT_SCROLL_TOP
wxEVT_SCROLL_BOTTOM = _core_.wxEVT_SCROLL_BOTTOM
wxEVT_SCROLL_LINEUP = _core_.wxEVT_SCROLL_LINEUP
wxEVT_SCROLL_LINEDOWN = _core_.wxEVT_SCROLL_LINEDOWN
wxEVT_SCROLL_PAGEUP = _core_.wxEVT_SCROLL_PAGEUP
wxEVT_SCROLL_PAGEDOWN = _core_.wxEVT_SCROLL_PAGEDOWN
wxEVT_SCROLL_THUMBTRACK = _core_.wxEVT_SCROLL_THUMBTRACK
wxEVT_SCROLL_THUMBRELEASE = _core_.wxEVT_SCROLL_THUMBRELEASE
wxEVT_SCROLL_CHANGED = _core_.wxEVT_SCROLL_CHANGED
wxEVT_SCROLL_ENDSCROLL = wxEVT_SCROLL_CHANGED
wxEVT_SCROLLWIN_TOP = _core_.wxEVT_SCROLLWIN_TOP
wxEVT_SCROLLWIN_BOTTOM = _core_.wxEVT_SCROLLWIN_BOTTOM
wxEVT_SCROLLWIN_LINEUP = _core_.wxEVT_SCROLLWIN_LINEUP
wxEVT_SCROLLWIN_LINEDOWN = _core_.wxEVT_SCROLLWIN_LINEDOWN
wxEVT_SCROLLWIN_PAGEUP = _core_.wxEVT_SCROLLWIN_PAGEUP
wxEVT_SCROLLWIN_PAGEDOWN = _core_.wxEVT_SCROLLWIN_PAGEDOWN
wxEVT_SCROLLWIN_THUMBTRACK = _core_.wxEVT_SCROLLWIN_THUMBTRACK
wxEVT_SCROLLWIN_THUMBRELEASE = _core_.wxEVT_SCROLLWIN_THUMBRELEASE
wxEVT_SIZE = _core_.wxEVT_SIZE
wxEVT_MOVE = _core_.wxEVT_MOVE
wxEVT_CLOSE_WINDOW = _core_.wxEVT_CLOSE_WINDOW
wxEVT_END_SESSION = _core_.wxEVT_END_SESSION
wxEVT_QUERY_END_SESSION = _core_.wxEVT_QUERY_END_SESSION
wxEVT_ACTIVATE_APP = _core_.wxEVT_ACTIVATE_APP
wxEVT_ACTIVATE = _core_.wxEVT_ACTIVATE
wxEVT_CREATE = _core_.wxEVT_CREATE
wxEVT_DESTROY = _core_.wxEVT_DESTROY
wxEVT_SHOW = _core_.wxEVT_SHOW
wxEVT_ICONIZE = _core_.wxEVT_ICONIZE
wxEVT_MAXIMIZE = _core_.wxEVT_MAXIMIZE
wxEVT_MOUSE_CAPTURE_CHANGED = _core_.wxEVT_MOUSE_CAPTURE_CHANGED
wxEVT_MOUSE_CAPTURE_LOST = _core_.wxEVT_MOUSE_CAPTURE_LOST
wxEVT_PAINT = _core_.wxEVT_PAINT
wxEVT_ERASE_BACKGROUND = _core_.wxEVT_ERASE_BACKGROUND
wxEVT_NC_PAINT = _core_.wxEVT_NC_PAINT
wxEVT_PAINT_ICON = _core_.wxEVT_PAINT_ICON
wxEVT_MENU_OPEN = _core_.wxEVT_MENU_OPEN
wxEVT_MENU_CLOSE = _core_.wxEVT_MENU_CLOSE
wxEVT_MENU_HIGHLIGHT = _core_.wxEVT_MENU_HIGHLIGHT
wxEVT_CONTEXT_MENU = _core_.wxEVT_CONTEXT_MENU
wxEVT_SYS_COLOUR_CHANGED = _core_.wxEVT_SYS_COLOUR_CHANGED
wxEVT_DISPLAY_CHANGED = _core_.wxEVT_DISPLAY_CHANGED
wxEVT_SETTING_CHANGED = _core_.wxEVT_SETTING_CHANGED
wxEVT_QUERY_NEW_PALETTE = _core_.wxEVT_QUERY_NEW_PALETTE
wxEVT_PALETTE_CHANGED = _core_.wxEVT_PALETTE_CHANGED
wxEVT_DROP_FILES = _core_.wxEVT_DROP_FILES
wxEVT_DRAW_ITEM = _core_.wxEVT_DRAW_ITEM
wxEVT_MEASURE_ITEM = _core_.wxEVT_MEASURE_ITEM
wxEVT_COMPARE_ITEM = _core_.wxEVT_COMPARE_ITEM
wxEVT_INIT_DIALOG = _core_.wxEVT_INIT_DIALOG
wxEVT_IDLE = _core_.wxEVT_IDLE
wxEVT_UPDATE_UI = _core_.wxEVT_UPDATE_UI
wxEVT_SIZING = _core_.wxEVT_SIZING
wxEVT_MOVING = _core_.wxEVT_MOVING
wxEVT_HIBERNATE = _core_.wxEVT_HIBERNATE
wxEVT_COMMAND_TEXT_COPY = _core_.wxEVT_COMMAND_TEXT_COPY
wxEVT_COMMAND_TEXT_CUT = _core_.wxEVT_COMMAND_TEXT_CUT
wxEVT_COMMAND_TEXT_PASTE = _core_.wxEVT_COMMAND_TEXT_PASTE
wxEVT_COMMAND_LEFT_CLICK = _core_.wxEVT_COMMAND_LEFT_CLICK
wxEVT_COMMAND_LEFT_DCLICK = _core_.wxEVT_COMMAND_LEFT_DCLICK
wxEVT_COMMAND_RIGHT_CLICK = _core_.wxEVT_COMMAND_RIGHT_CLICK
wxEVT_COMMAND_RIGHT_DCLICK = _core_.wxEVT_COMMAND_RIGHT_DCLICK
wxEVT_COMMAND_SET_FOCUS = _core_.wxEVT_COMMAND_SET_FOCUS
wxEVT_COMMAND_KILL_FOCUS = _core_.wxEVT_COMMAND_KILL_FOCUS
wxEVT_COMMAND_ENTER = _core_.wxEVT_COMMAND_ENTER
wxEVT_CTLCOLOR = _core_.wxEVT_CTLCOLOR
EVT_SIZE = wx.PyEventBinder(wxEVT_SIZE)
EVT_SIZING = wx.PyEventBinder(wxEVT_SIZING)
EVT_MOVE = wx.PyEventBinder(wxEVT_MOVE)
EVT_MOVING = wx.PyEventBinder(wxEVT_MOVING)
EVT_CLOSE = wx.PyEventBinder(wxEVT_CLOSE_WINDOW)
EVT_END_SESSION = wx.PyEventBinder(wxEVT_END_SESSION)
EVT_QUERY_END_SESSION = wx.PyEventBinder(wxEVT_QUERY_END_SESSION)
EVT_PAINT = wx.PyEventBinder(wxEVT_PAINT)
EVT_NC_PAINT = wx.PyEventBinder(wxEVT_NC_PAINT)
EVT_ERASE_BACKGROUND = wx.PyEventBinder(wxEVT_ERASE_BACKGROUND)
EVT_CHAR = wx.PyEventBinder(wxEVT_CHAR)
EVT_KEY_DOWN = wx.PyEventBinder(wxEVT_KEY_DOWN)
EVT_KEY_UP = wx.PyEventBinder(wxEVT_KEY_UP)
EVT_HOTKEY = wx.PyEventBinder(wxEVT_HOTKEY, 1)
EVT_CHAR_HOOK = wx.PyEventBinder(wxEVT_CHAR_HOOK)
EVT_MENU_OPEN = wx.PyEventBinder(wxEVT_MENU_OPEN)
EVT_MENU_CLOSE = wx.PyEventBinder(wxEVT_MENU_CLOSE)
EVT_MENU_HIGHLIGHT = wx.PyEventBinder(wxEVT_MENU_HIGHLIGHT, 1)
EVT_MENU_HIGHLIGHT_ALL = wx.PyEventBinder(wxEVT_MENU_HIGHLIGHT)
EVT_SET_FOCUS = wx.PyEventBinder(wxEVT_SET_FOCUS)
EVT_KILL_FOCUS = wx.PyEventBinder(wxEVT_KILL_FOCUS)
EVT_CHILD_FOCUS = wx.PyEventBinder(wxEVT_CHILD_FOCUS)
EVT_ACTIVATE = wx.PyEventBinder(wxEVT_ACTIVATE)
EVT_ACTIVATE_APP = wx.PyEventBinder(wxEVT_ACTIVATE_APP)
EVT_HIBERNATE = wx.PyEventBinder(wxEVT_HIBERNATE)
EVT_END_SESSION = wx.PyEventBinder(wxEVT_END_SESSION)
EVT_QUERY_END_SESSION = wx.PyEventBinder(wxEVT_QUERY_END_SESSION)
EVT_DROP_FILES = wx.PyEventBinder(wxEVT_DROP_FILES)
EVT_INIT_DIALOG = wx.PyEventBinder(wxEVT_INIT_DIALOG)
EVT_SYS_COLOUR_CHANGED = wx.PyEventBinder(wxEVT_SYS_COLOUR_CHANGED)
EVT_DISPLAY_CHANGED = wx.PyEventBinder(wxEVT_DISPLAY_CHANGED)
EVT_SHOW = wx.PyEventBinder(wxEVT_SHOW)
EVT_MAXIMIZE = wx.PyEventBinder(wxEVT_MAXIMIZE)
EVT_ICONIZE = wx.PyEventBinder(wxEVT_ICONIZE)
EVT_NAVIGATION_KEY = wx.PyEventBinder(wxEVT_NAVIGATION_KEY)
EVT_PALETTE_CHANGED = wx.PyEventBinder(wxEVT_PALETTE_CHANGED)
EVT_QUERY_NEW_PALETTE = wx.PyEventBinder(wxEVT_QUERY_NEW_PALETTE)
EVT_WINDOW_CREATE = wx.PyEventBinder(wxEVT_CREATE)
EVT_WINDOW_DESTROY = wx.PyEventBinder(wxEVT_DESTROY)
EVT_SET_CURSOR = wx.PyEventBinder(wxEVT_SET_CURSOR)
EVT_MOUSE_CAPTURE_CHANGED = wx.PyEventBinder(wxEVT_MOUSE_CAPTURE_CHANGED)
EVT_MOUSE_CAPTURE_LOST = wx.PyEventBinder(wxEVT_MOUSE_CAPTURE_LOST)
EVT_LEFT_DOWN = wx.PyEventBinder(wxEVT_LEFT_DOWN)
EVT_LEFT_UP = wx.PyEventBinder(wxEVT_LEFT_UP)
EVT_MIDDLE_DOWN = wx.PyEventBinder(wxEVT_MIDDLE_DOWN)
EVT_MIDDLE_UP = wx.PyEventBinder(wxEVT_MIDDLE_UP)
EVT_RIGHT_DOWN = wx.PyEventBinder(wxEVT_RIGHT_DOWN)
EVT_RIGHT_UP = wx.PyEventBinder(wxEVT_RIGHT_UP)
EVT_MOTION = wx.PyEventBinder(wxEVT_MOTION)
EVT_LEFT_DCLICK = wx.PyEventBinder(wxEVT_LEFT_DCLICK)
EVT_MIDDLE_DCLICK = wx.PyEventBinder(wxEVT_MIDDLE_DCLICK)
EVT_RIGHT_DCLICK = wx.PyEventBinder(wxEVT_RIGHT_DCLICK)
EVT_LEAVE_WINDOW = wx.PyEventBinder(wxEVT_LEAVE_WINDOW)
EVT_ENTER_WINDOW = wx.PyEventBinder(wxEVT_ENTER_WINDOW)
EVT_MOUSEWHEEL = wx.PyEventBinder(wxEVT_MOUSEWHEEL)
EVT_MOUSE_EVENTS = wx.PyEventBinder([wxEVT_LEFT_DOWN,
 wxEVT_LEFT_UP,
 wxEVT_MIDDLE_DOWN,
 wxEVT_MIDDLE_UP,
 wxEVT_RIGHT_DOWN,
 wxEVT_RIGHT_UP,
 wxEVT_MOTION,
 wxEVT_LEFT_DCLICK,
 wxEVT_MIDDLE_DCLICK,
 wxEVT_RIGHT_DCLICK,
 wxEVT_ENTER_WINDOW,
 wxEVT_LEAVE_WINDOW,
 wxEVT_MOUSEWHEEL])
EVT_SCROLLWIN = wx.PyEventBinder([wxEVT_SCROLLWIN_TOP,
 wxEVT_SCROLLWIN_BOTTOM,
 wxEVT_SCROLLWIN_LINEUP,
 wxEVT_SCROLLWIN_LINEDOWN,
 wxEVT_SCROLLWIN_PAGEUP,
 wxEVT_SCROLLWIN_PAGEDOWN,
 wxEVT_SCROLLWIN_THUMBTRACK,
 wxEVT_SCROLLWIN_THUMBRELEASE])
EVT_SCROLLWIN_TOP = wx.PyEventBinder(wxEVT_SCROLLWIN_TOP)
EVT_SCROLLWIN_BOTTOM = wx.PyEventBinder(wxEVT_SCROLLWIN_BOTTOM)
EVT_SCROLLWIN_LINEUP = wx.PyEventBinder(wxEVT_SCROLLWIN_LINEUP)
EVT_SCROLLWIN_LINEDOWN = wx.PyEventBinder(wxEVT_SCROLLWIN_LINEDOWN)
EVT_SCROLLWIN_PAGEUP = wx.PyEventBinder(wxEVT_SCROLLWIN_PAGEUP)
EVT_SCROLLWIN_PAGEDOWN = wx.PyEventBinder(wxEVT_SCROLLWIN_PAGEDOWN)
EVT_SCROLLWIN_THUMBTRACK = wx.PyEventBinder(wxEVT_SCROLLWIN_THUMBTRACK)
EVT_SCROLLWIN_THUMBRELEASE = wx.PyEventBinder(wxEVT_SCROLLWIN_THUMBRELEASE)
EVT_SCROLL = wx.PyEventBinder([wxEVT_SCROLL_TOP,
 wxEVT_SCROLL_BOTTOM,
 wxEVT_SCROLL_LINEUP,
 wxEVT_SCROLL_LINEDOWN,
 wxEVT_SCROLL_PAGEUP,
 wxEVT_SCROLL_PAGEDOWN,
 wxEVT_SCROLL_THUMBTRACK,
 wxEVT_SCROLL_THUMBRELEASE,
 wxEVT_SCROLL_CHANGED])
EVT_SCROLL_TOP = wx.PyEventBinder(wxEVT_SCROLL_TOP)
EVT_SCROLL_BOTTOM = wx.PyEventBinder(wxEVT_SCROLL_BOTTOM)
EVT_SCROLL_LINEUP = wx.PyEventBinder(wxEVT_SCROLL_LINEUP)
EVT_SCROLL_LINEDOWN = wx.PyEventBinder(wxEVT_SCROLL_LINEDOWN)
EVT_SCROLL_PAGEUP = wx.PyEventBinder(wxEVT_SCROLL_PAGEUP)
EVT_SCROLL_PAGEDOWN = wx.PyEventBinder(wxEVT_SCROLL_PAGEDOWN)
EVT_SCROLL_THUMBTRACK = wx.PyEventBinder(wxEVT_SCROLL_THUMBTRACK)
EVT_SCROLL_THUMBRELEASE = wx.PyEventBinder(wxEVT_SCROLL_THUMBRELEASE)
EVT_SCROLL_CHANGED = wx.PyEventBinder(wxEVT_SCROLL_CHANGED)
EVT_SCROLL_ENDSCROLL = EVT_SCROLL_CHANGED
EVT_COMMAND_SCROLL = wx.PyEventBinder([wxEVT_SCROLL_TOP,
 wxEVT_SCROLL_BOTTOM,
 wxEVT_SCROLL_LINEUP,
 wxEVT_SCROLL_LINEDOWN,
 wxEVT_SCROLL_PAGEUP,
 wxEVT_SCROLL_PAGEDOWN,
 wxEVT_SCROLL_THUMBTRACK,
 wxEVT_SCROLL_THUMBRELEASE,
 wxEVT_SCROLL_CHANGED], 1)
EVT_COMMAND_SCROLL_TOP = wx.PyEventBinder(wxEVT_SCROLL_TOP, 1)
EVT_COMMAND_SCROLL_BOTTOM = wx.PyEventBinder(wxEVT_SCROLL_BOTTOM, 1)
EVT_COMMAND_SCROLL_LINEUP = wx.PyEventBinder(wxEVT_SCROLL_LINEUP, 1)
EVT_COMMAND_SCROLL_LINEDOWN = wx.PyEventBinder(wxEVT_SCROLL_LINEDOWN, 1)
EVT_COMMAND_SCROLL_PAGEUP = wx.PyEventBinder(wxEVT_SCROLL_PAGEUP, 1)
EVT_COMMAND_SCROLL_PAGEDOWN = wx.PyEventBinder(wxEVT_SCROLL_PAGEDOWN, 1)
EVT_COMMAND_SCROLL_THUMBTRACK = wx.PyEventBinder(wxEVT_SCROLL_THUMBTRACK, 1)
EVT_COMMAND_SCROLL_THUMBRELEASE = wx.PyEventBinder(wxEVT_SCROLL_THUMBRELEASE, 1)
EVT_COMMAND_SCROLL_CHANGED = wx.PyEventBinder(wxEVT_SCROLL_CHANGED, 1)
EVT_COMMAND_SCROLL_ENDSCROLL = EVT_COMMAND_SCROLL_CHANGED
EVT_BUTTON = wx.PyEventBinder(wxEVT_COMMAND_BUTTON_CLICKED, 1)
EVT_CHECKBOX = wx.PyEventBinder(wxEVT_COMMAND_CHECKBOX_CLICKED, 1)
EVT_CHOICE = wx.PyEventBinder(wxEVT_COMMAND_CHOICE_SELECTED, 1)
EVT_LISTBOX = wx.PyEventBinder(wxEVT_COMMAND_LISTBOX_SELECTED, 1)
EVT_LISTBOX_DCLICK = wx.PyEventBinder(wxEVT_COMMAND_LISTBOX_DOUBLECLICKED, 1)
EVT_MENU = wx.PyEventBinder(wxEVT_COMMAND_MENU_SELECTED, 1)
EVT_MENU_RANGE = wx.PyEventBinder(wxEVT_COMMAND_MENU_SELECTED, 2)
EVT_SLIDER = wx.PyEventBinder(wxEVT_COMMAND_SLIDER_UPDATED, 1)
EVT_RADIOBOX = wx.PyEventBinder(wxEVT_COMMAND_RADIOBOX_SELECTED, 1)
EVT_RADIOBUTTON = wx.PyEventBinder(wxEVT_COMMAND_RADIOBUTTON_SELECTED, 1)
EVT_SCROLLBAR = wx.PyEventBinder(wxEVT_COMMAND_SCROLLBAR_UPDATED, 1)
EVT_VLBOX = wx.PyEventBinder(wxEVT_COMMAND_VLBOX_SELECTED, 1)
EVT_COMBOBOX = wx.PyEventBinder(wxEVT_COMMAND_COMBOBOX_SELECTED, 1)
EVT_TOOL = wx.PyEventBinder(wxEVT_COMMAND_TOOL_CLICKED, 1)
EVT_TOOL_RANGE = wx.PyEventBinder(wxEVT_COMMAND_TOOL_CLICKED, 2)
EVT_TOOL_RCLICKED = wx.PyEventBinder(wxEVT_COMMAND_TOOL_RCLICKED, 1)
EVT_TOOL_RCLICKED_RANGE = wx.PyEventBinder(wxEVT_COMMAND_TOOL_RCLICKED, 2)
EVT_TOOL_ENTER = wx.PyEventBinder(wxEVT_COMMAND_TOOL_ENTER, 1)
EVT_CHECKLISTBOX = wx.PyEventBinder(wxEVT_COMMAND_CHECKLISTBOX_TOGGLED, 1)
EVT_COMMAND_LEFT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_LEFT_CLICK, 1)
EVT_COMMAND_LEFT_DCLICK = wx.PyEventBinder(wxEVT_COMMAND_LEFT_DCLICK, 1)
EVT_COMMAND_RIGHT_CLICK = wx.PyEventBinder(wxEVT_COMMAND_RIGHT_CLICK, 1)
EVT_COMMAND_RIGHT_DCLICK = wx.PyEventBinder(wxEVT_COMMAND_RIGHT_DCLICK, 1)
EVT_COMMAND_SET_FOCUS = wx.PyEventBinder(wxEVT_COMMAND_SET_FOCUS, 1)
EVT_COMMAND_KILL_FOCUS = wx.PyEventBinder(wxEVT_COMMAND_KILL_FOCUS, 1)
EVT_COMMAND_ENTER = wx.PyEventBinder(wxEVT_COMMAND_ENTER, 1)
EVT_CTLCOLOR = wx.PyEventBinder(wxEVT_CTLCOLOR, 1)
EVT_IDLE = wx.PyEventBinder(wxEVT_IDLE)
EVT_UPDATE_UI = wx.PyEventBinder(wxEVT_UPDATE_UI, 1)
EVT_UPDATE_UI_RANGE = wx.PyEventBinder(wxEVT_UPDATE_UI, 2)
EVT_CONTEXT_MENU = wx.PyEventBinder(wxEVT_CONTEXT_MENU)
EVT_TEXT_CUT = wx.PyEventBinder(wxEVT_COMMAND_TEXT_CUT)
EVT_TEXT_COPY = wx.PyEventBinder(wxEVT_COMMAND_TEXT_COPY)
EVT_TEXT_PASTE = wx.PyEventBinder(wxEVT_COMMAND_TEXT_PASTE)

class Event(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_Event
    __del__ = lambda self: None

    def SetEventType(*args, **kwargs):
        return _core_.Event_SetEventType(*args, **kwargs)

    def GetEventType(*args, **kwargs):
        return _core_.Event_GetEventType(*args, **kwargs)

    def GetEventObject(*args, **kwargs):
        return _core_.Event_GetEventObject(*args, **kwargs)

    def SetEventObject(*args, **kwargs):
        return _core_.Event_SetEventObject(*args, **kwargs)

    def GetTimestamp(*args, **kwargs):
        return _core_.Event_GetTimestamp(*args, **kwargs)

    def SetTimestamp(*args, **kwargs):
        return _core_.Event_SetTimestamp(*args, **kwargs)

    def GetId(*args, **kwargs):
        return _core_.Event_GetId(*args, **kwargs)

    def SetId(*args, **kwargs):
        return _core_.Event_SetId(*args, **kwargs)

    def IsCommandEvent(*args, **kwargs):
        return _core_.Event_IsCommandEvent(*args, **kwargs)

    def Skip(*args, **kwargs):
        return _core_.Event_Skip(*args, **kwargs)

    def GetSkipped(*args, **kwargs):
        return _core_.Event_GetSkipped(*args, **kwargs)

    def ShouldPropagate(*args, **kwargs):
        return _core_.Event_ShouldPropagate(*args, **kwargs)

    def StopPropagation(*args, **kwargs):
        return _core_.Event_StopPropagation(*args, **kwargs)

    def ResumePropagation(*args, **kwargs):
        return _core_.Event_ResumePropagation(*args, **kwargs)

    def Clone(*args, **kwargs):
        return _core_.Event_Clone(*args, **kwargs)

    EventObject = property(GetEventObject, SetEventObject, doc='See `GetEventObject` and `SetEventObject`')
    EventType = property(GetEventType, SetEventType, doc='See `GetEventType` and `SetEventType`')
    Id = property(GetId, SetId, doc='See `GetId` and `SetId`')
    Skipped = property(GetSkipped, doc='See `GetSkipped`')
    Timestamp = property(GetTimestamp, SetTimestamp, doc='See `GetTimestamp` and `SetTimestamp`')


_core_.Event_swigregister(Event)

class PropagationDisabler(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PropagationDisabler_swiginit(self, _core_.new_PropagationDisabler(*args, **kwargs))

    __swig_destroy__ = _core_.delete_PropagationDisabler
    __del__ = lambda self: None


_core_.PropagationDisabler_swigregister(PropagationDisabler)

class PropagateOnce(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PropagateOnce_swiginit(self, _core_.new_PropagateOnce(*args, **kwargs))

    __swig_destroy__ = _core_.delete_PropagateOnce
    __del__ = lambda self: None


_core_.PropagateOnce_swigregister(PropagateOnce)

class CommandEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.CommandEvent_swiginit(self, _core_.new_CommandEvent(*args, **kwargs))

    def GetSelection(*args, **kwargs):
        return _core_.CommandEvent_GetSelection(*args, **kwargs)

    def SetString(*args, **kwargs):
        return _core_.CommandEvent_SetString(*args, **kwargs)

    def GetString(*args, **kwargs):
        return _core_.CommandEvent_GetString(*args, **kwargs)

    def IsChecked(*args, **kwargs):
        return _core_.CommandEvent_IsChecked(*args, **kwargs)

    Checked = IsChecked

    def IsSelection(*args, **kwargs):
        return _core_.CommandEvent_IsSelection(*args, **kwargs)

    def SetExtraLong(*args, **kwargs):
        return _core_.CommandEvent_SetExtraLong(*args, **kwargs)

    def GetExtraLong(*args, **kwargs):
        return _core_.CommandEvent_GetExtraLong(*args, **kwargs)

    def SetInt(*args, **kwargs):
        return _core_.CommandEvent_SetInt(*args, **kwargs)

    def GetInt(*args, **kwargs):
        return _core_.CommandEvent_GetInt(*args, **kwargs)

    def GetClientData(*args, **kwargs):
        return _core_.CommandEvent_GetClientData(*args, **kwargs)

    def SetClientData(*args, **kwargs):
        return _core_.CommandEvent_SetClientData(*args, **kwargs)

    GetClientObject = GetClientData
    SetClientObject = SetClientData

    def Clone(*args, **kwargs):
        return _core_.CommandEvent_Clone(*args, **kwargs)

    ClientData = property(GetClientData, SetClientData, doc='See `GetClientData` and `SetClientData`')
    ClientObject = property(GetClientObject, SetClientObject, doc='See `GetClientObject` and `SetClientObject`')
    ExtraLong = property(GetExtraLong, SetExtraLong, doc='See `GetExtraLong` and `SetExtraLong`')
    Int = property(GetInt, SetInt, doc='See `GetInt` and `SetInt`')
    Selection = property(GetSelection, doc='See `GetSelection`')
    String = property(GetString, SetString, doc='See `GetString` and `SetString`')


_core_.CommandEvent_swigregister(CommandEvent)

class NotifyEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.NotifyEvent_swiginit(self, _core_.new_NotifyEvent(*args, **kwargs))

    def Veto(*args, **kwargs):
        return _core_.NotifyEvent_Veto(*args, **kwargs)

    def Allow(*args, **kwargs):
        return _core_.NotifyEvent_Allow(*args, **kwargs)

    def IsAllowed(*args, **kwargs):
        return _core_.NotifyEvent_IsAllowed(*args, **kwargs)


_core_.NotifyEvent_swigregister(NotifyEvent)

class ScrollEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ScrollEvent_swiginit(self, _core_.new_ScrollEvent(*args, **kwargs))

    def GetOrientation(*args, **kwargs):
        return _core_.ScrollEvent_GetOrientation(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.ScrollEvent_GetPosition(*args, **kwargs)

    def SetOrientation(*args, **kwargs):
        return _core_.ScrollEvent_SetOrientation(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _core_.ScrollEvent_SetPosition(*args, **kwargs)

    Orientation = property(GetOrientation, SetOrientation, doc='See `GetOrientation` and `SetOrientation`')
    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')


_core_.ScrollEvent_swigregister(ScrollEvent)

class ScrollWinEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ScrollWinEvent_swiginit(self, _core_.new_ScrollWinEvent(*args, **kwargs))

    def GetOrientation(*args, **kwargs):
        return _core_.ScrollWinEvent_GetOrientation(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.ScrollWinEvent_GetPosition(*args, **kwargs)

    def SetOrientation(*args, **kwargs):
        return _core_.ScrollWinEvent_SetOrientation(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _core_.ScrollWinEvent_SetPosition(*args, **kwargs)

    Orientation = property(GetOrientation, SetOrientation, doc='See `GetOrientation` and `SetOrientation`')
    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')


_core_.ScrollWinEvent_swigregister(ScrollWinEvent)
MOUSE_BTN_ANY = _core_.MOUSE_BTN_ANY
MOUSE_BTN_NONE = _core_.MOUSE_BTN_NONE
MOUSE_BTN_LEFT = _core_.MOUSE_BTN_LEFT
MOUSE_BTN_MIDDLE = _core_.MOUSE_BTN_MIDDLE
MOUSE_BTN_RIGHT = _core_.MOUSE_BTN_RIGHT

class MouseEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MouseEvent_swiginit(self, _core_.new_MouseEvent(*args, **kwargs))

    def IsButton(*args, **kwargs):
        return _core_.MouseEvent_IsButton(*args, **kwargs)

    def ButtonDown(*args, **kwargs):
        return _core_.MouseEvent_ButtonDown(*args, **kwargs)

    def ButtonDClick(*args, **kwargs):
        return _core_.MouseEvent_ButtonDClick(*args, **kwargs)

    def ButtonUp(*args, **kwargs):
        return _core_.MouseEvent_ButtonUp(*args, **kwargs)

    def Button(*args, **kwargs):
        return _core_.MouseEvent_Button(*args, **kwargs)

    def ButtonIsDown(*args, **kwargs):
        return _core_.MouseEvent_ButtonIsDown(*args, **kwargs)

    def GetButton(*args, **kwargs):
        return _core_.MouseEvent_GetButton(*args, **kwargs)

    def ControlDown(*args, **kwargs):
        return _core_.MouseEvent_ControlDown(*args, **kwargs)

    def MetaDown(*args, **kwargs):
        return _core_.MouseEvent_MetaDown(*args, **kwargs)

    def AltDown(*args, **kwargs):
        return _core_.MouseEvent_AltDown(*args, **kwargs)

    def ShiftDown(*args, **kwargs):
        return _core_.MouseEvent_ShiftDown(*args, **kwargs)

    def CmdDown(*args, **kwargs):
        return _core_.MouseEvent_CmdDown(*args, **kwargs)

    def LeftDown(*args, **kwargs):
        return _core_.MouseEvent_LeftDown(*args, **kwargs)

    def MiddleDown(*args, **kwargs):
        return _core_.MouseEvent_MiddleDown(*args, **kwargs)

    def RightDown(*args, **kwargs):
        return _core_.MouseEvent_RightDown(*args, **kwargs)

    def LeftUp(*args, **kwargs):
        return _core_.MouseEvent_LeftUp(*args, **kwargs)

    def MiddleUp(*args, **kwargs):
        return _core_.MouseEvent_MiddleUp(*args, **kwargs)

    def RightUp(*args, **kwargs):
        return _core_.MouseEvent_RightUp(*args, **kwargs)

    def LeftDClick(*args, **kwargs):
        return _core_.MouseEvent_LeftDClick(*args, **kwargs)

    def MiddleDClick(*args, **kwargs):
        return _core_.MouseEvent_MiddleDClick(*args, **kwargs)

    def RightDClick(*args, **kwargs):
        return _core_.MouseEvent_RightDClick(*args, **kwargs)

    def LeftIsDown(*args, **kwargs):
        return _core_.MouseEvent_LeftIsDown(*args, **kwargs)

    def MiddleIsDown(*args, **kwargs):
        return _core_.MouseEvent_MiddleIsDown(*args, **kwargs)

    def RightIsDown(*args, **kwargs):
        return _core_.MouseEvent_RightIsDown(*args, **kwargs)

    def Dragging(*args, **kwargs):
        return _core_.MouseEvent_Dragging(*args, **kwargs)

    def Moving(*args, **kwargs):
        return _core_.MouseEvent_Moving(*args, **kwargs)

    def Entering(*args, **kwargs):
        return _core_.MouseEvent_Entering(*args, **kwargs)

    def Leaving(*args, **kwargs):
        return _core_.MouseEvent_Leaving(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.MouseEvent_GetPosition(*args, **kwargs)

    def GetPositionTuple(*args, **kwargs):
        return _core_.MouseEvent_GetPositionTuple(*args, **kwargs)

    def GetLogicalPosition(*args, **kwargs):
        return _core_.MouseEvent_GetLogicalPosition(*args, **kwargs)

    def GetX(*args, **kwargs):
        return _core_.MouseEvent_GetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _core_.MouseEvent_GetY(*args, **kwargs)

    def GetWheelRotation(*args, **kwargs):
        return _core_.MouseEvent_GetWheelRotation(*args, **kwargs)

    def GetWheelDelta(*args, **kwargs):
        return _core_.MouseEvent_GetWheelDelta(*args, **kwargs)

    def GetLinesPerAction(*args, **kwargs):
        return _core_.MouseEvent_GetLinesPerAction(*args, **kwargs)

    def IsPageScroll(*args, **kwargs):
        return _core_.MouseEvent_IsPageScroll(*args, **kwargs)

    m_x = property(_core_.MouseEvent_m_x_get, _core_.MouseEvent_m_x_set)
    m_y = property(_core_.MouseEvent_m_y_get, _core_.MouseEvent_m_y_set)
    m_leftDown = property(_core_.MouseEvent_m_leftDown_get, _core_.MouseEvent_m_leftDown_set)
    m_middleDown = property(_core_.MouseEvent_m_middleDown_get, _core_.MouseEvent_m_middleDown_set)
    m_rightDown = property(_core_.MouseEvent_m_rightDown_get, _core_.MouseEvent_m_rightDown_set)
    m_controlDown = property(_core_.MouseEvent_m_controlDown_get, _core_.MouseEvent_m_controlDown_set)
    m_shiftDown = property(_core_.MouseEvent_m_shiftDown_get, _core_.MouseEvent_m_shiftDown_set)
    m_altDown = property(_core_.MouseEvent_m_altDown_get, _core_.MouseEvent_m_altDown_set)
    m_metaDown = property(_core_.MouseEvent_m_metaDown_get, _core_.MouseEvent_m_metaDown_set)
    m_wheelRotation = property(_core_.MouseEvent_m_wheelRotation_get, _core_.MouseEvent_m_wheelRotation_set)
    m_wheelDelta = property(_core_.MouseEvent_m_wheelDelta_get, _core_.MouseEvent_m_wheelDelta_set)
    m_linesPerAction = property(_core_.MouseEvent_m_linesPerAction_get, _core_.MouseEvent_m_linesPerAction_set)
    Button = property(GetButton, doc='See `GetButton`')
    LinesPerAction = property(GetLinesPerAction, doc='See `GetLinesPerAction`')
    LogicalPosition = property(GetLogicalPosition, doc='See `GetLogicalPosition`')
    Position = property(GetPosition, doc='See `GetPosition`')
    WheelDelta = property(GetWheelDelta, doc='See `GetWheelDelta`')
    WheelRotation = property(GetWheelRotation, doc='See `GetWheelRotation`')
    X = property(GetX, doc='See `GetX`')
    Y = property(GetY, doc='See `GetY`')


_core_.MouseEvent_swigregister(MouseEvent)

class SetCursorEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.SetCursorEvent_swiginit(self, _core_.new_SetCursorEvent(*args, **kwargs))

    def GetX(*args, **kwargs):
        return _core_.SetCursorEvent_GetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _core_.SetCursorEvent_GetY(*args, **kwargs)

    def SetCursor(*args, **kwargs):
        return _core_.SetCursorEvent_SetCursor(*args, **kwargs)

    def GetCursor(*args, **kwargs):
        return _core_.SetCursorEvent_GetCursor(*args, **kwargs)

    def HasCursor(*args, **kwargs):
        return _core_.SetCursorEvent_HasCursor(*args, **kwargs)

    Cursor = property(GetCursor, SetCursor, doc='See `GetCursor` and `SetCursor`')
    X = property(GetX, doc='See `GetX`')
    Y = property(GetY, doc='See `GetY`')


_core_.SetCursorEvent_swigregister(SetCursorEvent)

class KeyEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.KeyEvent_swiginit(self, _core_.new_KeyEvent(*args, **kwargs))

    def GetModifiers(*args, **kwargs):
        return _core_.KeyEvent_GetModifiers(*args, **kwargs)

    def ControlDown(*args, **kwargs):
        return _core_.KeyEvent_ControlDown(*args, **kwargs)

    def MetaDown(*args, **kwargs):
        return _core_.KeyEvent_MetaDown(*args, **kwargs)

    def AltDown(*args, **kwargs):
        return _core_.KeyEvent_AltDown(*args, **kwargs)

    def ShiftDown(*args, **kwargs):
        return _core_.KeyEvent_ShiftDown(*args, **kwargs)

    def CmdDown(*args, **kwargs):
        return _core_.KeyEvent_CmdDown(*args, **kwargs)

    def HasModifiers(*args, **kwargs):
        return _core_.KeyEvent_HasModifiers(*args, **kwargs)

    def GetKeyCode(*args, **kwargs):
        return _core_.KeyEvent_GetKeyCode(*args, **kwargs)

    def GetUnicodeKey(*args, **kwargs):
        return _core_.KeyEvent_GetUnicodeKey(*args, **kwargs)

    GetUniChar = GetUnicodeKey

    def SetUnicodeKey(*args, **kwargs):
        return _core_.KeyEvent_SetUnicodeKey(*args, **kwargs)

    def GetRawKeyCode(*args, **kwargs):
        return _core_.KeyEvent_GetRawKeyCode(*args, **kwargs)

    def GetRawKeyFlags(*args, **kwargs):
        return _core_.KeyEvent_GetRawKeyFlags(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.KeyEvent_GetPosition(*args, **kwargs)

    def GetPositionTuple(*args, **kwargs):
        return _core_.KeyEvent_GetPositionTuple(*args, **kwargs)

    def GetX(*args, **kwargs):
        return _core_.KeyEvent_GetX(*args, **kwargs)

    def GetY(*args, **kwargs):
        return _core_.KeyEvent_GetY(*args, **kwargs)

    m_x = property(_core_.KeyEvent_m_x_get, _core_.KeyEvent_m_x_set)
    m_y = property(_core_.KeyEvent_m_y_get, _core_.KeyEvent_m_y_set)
    m_keyCode = property(_core_.KeyEvent_m_keyCode_get, _core_.KeyEvent_m_keyCode_set)
    m_controlDown = property(_core_.KeyEvent_m_controlDown_get, _core_.KeyEvent_m_controlDown_set)
    m_shiftDown = property(_core_.KeyEvent_m_shiftDown_get, _core_.KeyEvent_m_shiftDown_set)
    m_altDown = property(_core_.KeyEvent_m_altDown_get, _core_.KeyEvent_m_altDown_set)
    m_metaDown = property(_core_.KeyEvent_m_metaDown_get, _core_.KeyEvent_m_metaDown_set)
    m_scanCode = property(_core_.KeyEvent_m_scanCode_get, _core_.KeyEvent_m_scanCode_set)
    m_rawCode = property(_core_.KeyEvent_m_rawCode_get, _core_.KeyEvent_m_rawCode_set)
    m_rawFlags = property(_core_.KeyEvent_m_rawFlags_get, _core_.KeyEvent_m_rawFlags_set)
    KeyCode = property(GetKeyCode, doc='See `GetKeyCode`')
    Modifiers = property(GetModifiers, doc='See `GetModifiers`')
    Position = property(GetPosition, doc='See `GetPosition`')
    RawKeyCode = property(GetRawKeyCode, doc='See `GetRawKeyCode`')
    RawKeyFlags = property(GetRawKeyFlags, doc='See `GetRawKeyFlags`')
    UnicodeKey = property(GetUnicodeKey, SetUnicodeKey, doc='See `GetUnicodeKey` and `SetUnicodeKey`')
    X = property(GetX, doc='See `GetX`')
    Y = property(GetY, doc='See `GetY`')


_core_.KeyEvent_swigregister(KeyEvent)

class SizeEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.SizeEvent_swiginit(self, _core_.new_SizeEvent(*args, **kwargs))

    def GetSize(*args, **kwargs):
        return _core_.SizeEvent_GetSize(*args, **kwargs)

    def GetRect(*args, **kwargs):
        return _core_.SizeEvent_GetRect(*args, **kwargs)

    def SetRect(*args, **kwargs):
        return _core_.SizeEvent_SetRect(*args, **kwargs)

    def SetSize(*args, **kwargs):
        return _core_.SizeEvent_SetSize(*args, **kwargs)

    m_size = property(_core_.SizeEvent_m_size_get, _core_.SizeEvent_m_size_set)
    m_rect = property(_core_.SizeEvent_m_rect_get, _core_.SizeEvent_m_rect_set)
    Rect = property(GetRect, SetRect, doc='See `GetRect` and `SetRect`')
    Size = property(GetSize, SetSize, doc='See `GetSize` and `SetSize`')


_core_.SizeEvent_swigregister(SizeEvent)

class MoveEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MoveEvent_swiginit(self, _core_.new_MoveEvent(*args, **kwargs))

    def GetPosition(*args, **kwargs):
        return _core_.MoveEvent_GetPosition(*args, **kwargs)

    def GetRect(*args, **kwargs):
        return _core_.MoveEvent_GetRect(*args, **kwargs)

    def SetRect(*args, **kwargs):
        return _core_.MoveEvent_SetRect(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _core_.MoveEvent_SetPosition(*args, **kwargs)

    m_pos = property(GetPosition, SetPosition)
    m_rect = property(GetRect, SetRect)
    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')
    Rect = property(GetRect, SetRect, doc='See `GetRect` and `SetRect`')


_core_.MoveEvent_swigregister(MoveEvent)

class PaintEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PaintEvent_swiginit(self, _core_.new_PaintEvent(*args, **kwargs))


_core_.PaintEvent_swigregister(PaintEvent)

class NcPaintEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.NcPaintEvent_swiginit(self, _core_.new_NcPaintEvent(*args, **kwargs))


_core_.NcPaintEvent_swigregister(NcPaintEvent)

class EraseEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.EraseEvent_swiginit(self, _core_.new_EraseEvent(*args, **kwargs))

    def GetDC(*args, **kwargs):
        return _core_.EraseEvent_GetDC(*args, **kwargs)

    DC = property(GetDC, doc='See `GetDC`')


_core_.EraseEvent_swigregister(EraseEvent)

class FocusEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.FocusEvent_swiginit(self, _core_.new_FocusEvent(*args, **kwargs))

    def GetWindow(*args, **kwargs):
        return _core_.FocusEvent_GetWindow(*args, **kwargs)

    def SetWindow(*args, **kwargs):
        return _core_.FocusEvent_SetWindow(*args, **kwargs)

    Window = property(GetWindow, SetWindow, doc='See `GetWindow` and `SetWindow`')


_core_.FocusEvent_swigregister(FocusEvent)

class ChildFocusEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ChildFocusEvent_swiginit(self, _core_.new_ChildFocusEvent(*args, **kwargs))

    def GetWindow(*args, **kwargs):
        return _core_.ChildFocusEvent_GetWindow(*args, **kwargs)

    Window = property(GetWindow, doc='See `GetWindow`')


_core_.ChildFocusEvent_swigregister(ChildFocusEvent)

class ActivateEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ActivateEvent_swiginit(self, _core_.new_ActivateEvent(*args, **kwargs))

    def GetActive(*args, **kwargs):
        return _core_.ActivateEvent_GetActive(*args, **kwargs)

    Active = property(GetActive, doc='See `GetActive`')


_core_.ActivateEvent_swigregister(ActivateEvent)

class InitDialogEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.InitDialogEvent_swiginit(self, _core_.new_InitDialogEvent(*args, **kwargs))


_core_.InitDialogEvent_swigregister(InitDialogEvent)

class MenuEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MenuEvent_swiginit(self, _core_.new_MenuEvent(*args, **kwargs))

    def GetMenuId(*args, **kwargs):
        return _core_.MenuEvent_GetMenuId(*args, **kwargs)

    def IsPopup(*args, **kwargs):
        return _core_.MenuEvent_IsPopup(*args, **kwargs)

    def GetMenu(*args, **kwargs):
        return _core_.MenuEvent_GetMenu(*args, **kwargs)

    Menu = property(GetMenu, doc='See `GetMenu`')
    MenuId = property(GetMenuId, doc='See `GetMenuId`')


_core_.MenuEvent_swigregister(MenuEvent)

class CloseEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.CloseEvent_swiginit(self, _core_.new_CloseEvent(*args, **kwargs))

    def SetLoggingOff(*args, **kwargs):
        return _core_.CloseEvent_SetLoggingOff(*args, **kwargs)

    def GetLoggingOff(*args, **kwargs):
        return _core_.CloseEvent_GetLoggingOff(*args, **kwargs)

    def Veto(*args, **kwargs):
        return _core_.CloseEvent_Veto(*args, **kwargs)

    def GetVeto(*args, **kwargs):
        return _core_.CloseEvent_GetVeto(*args, **kwargs)

    def SetCanVeto(*args, **kwargs):
        return _core_.CloseEvent_SetCanVeto(*args, **kwargs)

    def CanVeto(*args, **kwargs):
        return _core_.CloseEvent_CanVeto(*args, **kwargs)

    LoggingOff = property(GetLoggingOff, SetLoggingOff, doc='See `GetLoggingOff` and `SetLoggingOff`')


_core_.CloseEvent_swigregister(CloseEvent)

class ShowEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ShowEvent_swiginit(self, _core_.new_ShowEvent(*args, **kwargs))

    def SetShow(*args, **kwargs):
        return _core_.ShowEvent_SetShow(*args, **kwargs)

    def GetShow(*args, **kwargs):
        return _core_.ShowEvent_GetShow(*args, **kwargs)

    Show = property(GetShow, SetShow, doc='See `GetShow` and `SetShow`')


_core_.ShowEvent_swigregister(ShowEvent)

class IconizeEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.IconizeEvent_swiginit(self, _core_.new_IconizeEvent(*args, **kwargs))

    def Iconized(*args, **kwargs):
        return _core_.IconizeEvent_Iconized(*args, **kwargs)


_core_.IconizeEvent_swigregister(IconizeEvent)

class MaximizeEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MaximizeEvent_swiginit(self, _core_.new_MaximizeEvent(*args, **kwargs))


_core_.MaximizeEvent_swigregister(MaximizeEvent)

class DropFilesEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def GetPosition(*args, **kwargs):
        return _core_.DropFilesEvent_GetPosition(*args, **kwargs)

    def GetNumberOfFiles(*args, **kwargs):
        return _core_.DropFilesEvent_GetNumberOfFiles(*args, **kwargs)

    def GetFiles(*args, **kwargs):
        return _core_.DropFilesEvent_GetFiles(*args, **kwargs)

    Files = property(GetFiles, doc='See `GetFiles`')
    NumberOfFiles = property(GetNumberOfFiles, doc='See `GetNumberOfFiles`')
    Position = property(GetPosition, doc='See `GetPosition`')


_core_.DropFilesEvent_swigregister(DropFilesEvent)
UPDATE_UI_PROCESS_ALL = _core_.UPDATE_UI_PROCESS_ALL
UPDATE_UI_PROCESS_SPECIFIED = _core_.UPDATE_UI_PROCESS_SPECIFIED

class UpdateUIEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.UpdateUIEvent_swiginit(self, _core_.new_UpdateUIEvent(*args, **kwargs))

    def GetChecked(*args, **kwargs):
        return _core_.UpdateUIEvent_GetChecked(*args, **kwargs)

    def GetEnabled(*args, **kwargs):
        return _core_.UpdateUIEvent_GetEnabled(*args, **kwargs)

    def GetShown(*args, **kwargs):
        return _core_.UpdateUIEvent_GetShown(*args, **kwargs)

    def GetText(*args, **kwargs):
        return _core_.UpdateUIEvent_GetText(*args, **kwargs)

    def GetSetText(*args, **kwargs):
        return _core_.UpdateUIEvent_GetSetText(*args, **kwargs)

    def GetSetChecked(*args, **kwargs):
        return _core_.UpdateUIEvent_GetSetChecked(*args, **kwargs)

    def GetSetEnabled(*args, **kwargs):
        return _core_.UpdateUIEvent_GetSetEnabled(*args, **kwargs)

    def GetSetShown(*args, **kwargs):
        return _core_.UpdateUIEvent_GetSetShown(*args, **kwargs)

    def Check(*args, **kwargs):
        return _core_.UpdateUIEvent_Check(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _core_.UpdateUIEvent_Enable(*args, **kwargs)

    def Show(*args, **kwargs):
        return _core_.UpdateUIEvent_Show(*args, **kwargs)

    def SetText(*args, **kwargs):
        return _core_.UpdateUIEvent_SetText(*args, **kwargs)

    def SetUpdateInterval(*args, **kwargs):
        return _core_.UpdateUIEvent_SetUpdateInterval(*args, **kwargs)

    SetUpdateInterval = staticmethod(SetUpdateInterval)

    def GetUpdateInterval(*args, **kwargs):
        return _core_.UpdateUIEvent_GetUpdateInterval(*args, **kwargs)

    GetUpdateInterval = staticmethod(GetUpdateInterval)

    def CanUpdate(*args, **kwargs):
        return _core_.UpdateUIEvent_CanUpdate(*args, **kwargs)

    CanUpdate = staticmethod(CanUpdate)

    def ResetUpdateTime(*args, **kwargs):
        return _core_.UpdateUIEvent_ResetUpdateTime(*args, **kwargs)

    ResetUpdateTime = staticmethod(ResetUpdateTime)

    def SetMode(*args, **kwargs):
        return _core_.UpdateUIEvent_SetMode(*args, **kwargs)

    SetMode = staticmethod(SetMode)

    def GetMode(*args, **kwargs):
        return _core_.UpdateUIEvent_GetMode(*args, **kwargs)

    GetMode = staticmethod(GetMode)
    Checked = property(GetChecked, Check, doc='See `GetChecked`')
    Enabled = property(GetEnabled, Enable, doc='See `GetEnabled`')
    Shown = property(GetShown, Show, doc='See `GetShown`')
    Text = property(GetText, SetText, doc='See `GetText` and `SetText`')


_core_.UpdateUIEvent_swigregister(UpdateUIEvent)

def UpdateUIEvent_SetUpdateInterval(*args, **kwargs):
    return _core_.UpdateUIEvent_SetUpdateInterval(*args, **kwargs)


def UpdateUIEvent_GetUpdateInterval(*args):
    return _core_.UpdateUIEvent_GetUpdateInterval(*args)


def UpdateUIEvent_CanUpdate(*args, **kwargs):
    return _core_.UpdateUIEvent_CanUpdate(*args, **kwargs)


def UpdateUIEvent_ResetUpdateTime(*args):
    return _core_.UpdateUIEvent_ResetUpdateTime(*args)


def UpdateUIEvent_SetMode(*args, **kwargs):
    return _core_.UpdateUIEvent_SetMode(*args, **kwargs)


def UpdateUIEvent_GetMode(*args):
    return _core_.UpdateUIEvent_GetMode(*args)


class SysColourChangedEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.SysColourChangedEvent_swiginit(self, _core_.new_SysColourChangedEvent(*args, **kwargs))


_core_.SysColourChangedEvent_swigregister(SysColourChangedEvent)

class MouseCaptureChangedEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MouseCaptureChangedEvent_swiginit(self, _core_.new_MouseCaptureChangedEvent(*args, **kwargs))

    def GetCapturedWindow(*args, **kwargs):
        return _core_.MouseCaptureChangedEvent_GetCapturedWindow(*args, **kwargs)

    CapturedWindow = property(GetCapturedWindow, doc='See `GetCapturedWindow`')


_core_.MouseCaptureChangedEvent_swigregister(MouseCaptureChangedEvent)

class MouseCaptureLostEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MouseCaptureLostEvent_swiginit(self, _core_.new_MouseCaptureLostEvent(*args, **kwargs))


_core_.MouseCaptureLostEvent_swigregister(MouseCaptureLostEvent)

class DisplayChangedEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.DisplayChangedEvent_swiginit(self, _core_.new_DisplayChangedEvent(*args, **kwargs))


_core_.DisplayChangedEvent_swigregister(DisplayChangedEvent)

class PaletteChangedEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PaletteChangedEvent_swiginit(self, _core_.new_PaletteChangedEvent(*args, **kwargs))

    def SetChangedWindow(*args, **kwargs):
        return _core_.PaletteChangedEvent_SetChangedWindow(*args, **kwargs)

    def GetChangedWindow(*args, **kwargs):
        return _core_.PaletteChangedEvent_GetChangedWindow(*args, **kwargs)

    ChangedWindow = property(GetChangedWindow, SetChangedWindow, doc='See `GetChangedWindow` and `SetChangedWindow`')


_core_.PaletteChangedEvent_swigregister(PaletteChangedEvent)

class QueryNewPaletteEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.QueryNewPaletteEvent_swiginit(self, _core_.new_QueryNewPaletteEvent(*args, **kwargs))

    def SetPaletteRealized(*args, **kwargs):
        return _core_.QueryNewPaletteEvent_SetPaletteRealized(*args, **kwargs)

    def GetPaletteRealized(*args, **kwargs):
        return _core_.QueryNewPaletteEvent_GetPaletteRealized(*args, **kwargs)

    PaletteRealized = property(GetPaletteRealized, SetPaletteRealized, doc='See `GetPaletteRealized` and `SetPaletteRealized`')


_core_.QueryNewPaletteEvent_swigregister(QueryNewPaletteEvent)

class NavigationKeyEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.NavigationKeyEvent_swiginit(self, _core_.new_NavigationKeyEvent(*args, **kwargs))

    def GetDirection(*args, **kwargs):
        return _core_.NavigationKeyEvent_GetDirection(*args, **kwargs)

    def SetDirection(*args, **kwargs):
        return _core_.NavigationKeyEvent_SetDirection(*args, **kwargs)

    def IsWindowChange(*args, **kwargs):
        return _core_.NavigationKeyEvent_IsWindowChange(*args, **kwargs)

    def SetWindowChange(*args, **kwargs):
        return _core_.NavigationKeyEvent_SetWindowChange(*args, **kwargs)

    def IsFromTab(*args, **kwargs):
        return _core_.NavigationKeyEvent_IsFromTab(*args, **kwargs)

    def SetFromTab(*args, **kwargs):
        return _core_.NavigationKeyEvent_SetFromTab(*args, **kwargs)

    def SetFlags(*args, **kwargs):
        return _core_.NavigationKeyEvent_SetFlags(*args, **kwargs)

    def GetCurrentFocus(*args, **kwargs):
        return _core_.NavigationKeyEvent_GetCurrentFocus(*args, **kwargs)

    def SetCurrentFocus(*args, **kwargs):
        return _core_.NavigationKeyEvent_SetCurrentFocus(*args, **kwargs)

    IsBackward = _core_.NavigationKeyEvent_IsBackward
    IsForward = _core_.NavigationKeyEvent_IsForward
    WinChange = _core_.NavigationKeyEvent_WinChange
    FromTab = _core_.NavigationKeyEvent_FromTab
    CurrentFocus = property(GetCurrentFocus, SetCurrentFocus, doc='See `GetCurrentFocus` and `SetCurrentFocus`')
    Direction = property(GetDirection, SetDirection, doc='See `GetDirection` and `SetDirection`')


_core_.NavigationKeyEvent_swigregister(NavigationKeyEvent)

class WindowCreateEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.WindowCreateEvent_swiginit(self, _core_.new_WindowCreateEvent(*args, **kwargs))

    def GetWindow(*args, **kwargs):
        return _core_.WindowCreateEvent_GetWindow(*args, **kwargs)

    Window = property(GetWindow, doc='See `GetWindow`')


_core_.WindowCreateEvent_swigregister(WindowCreateEvent)

class WindowDestroyEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.WindowDestroyEvent_swiginit(self, _core_.new_WindowDestroyEvent(*args, **kwargs))

    def GetWindow(*args, **kwargs):
        return _core_.WindowDestroyEvent_GetWindow(*args, **kwargs)

    Window = property(GetWindow, doc='See `GetWindow`')


_core_.WindowDestroyEvent_swigregister(WindowDestroyEvent)

class ContextMenuEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ContextMenuEvent_swiginit(self, _core_.new_ContextMenuEvent(*args, **kwargs))

    def GetPosition(*args, **kwargs):
        return _core_.ContextMenuEvent_GetPosition(*args, **kwargs)

    def SetPosition(*args, **kwargs):
        return _core_.ContextMenuEvent_SetPosition(*args, **kwargs)

    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')


_core_.ContextMenuEvent_swigregister(ContextMenuEvent)
IDLE_PROCESS_ALL = _core_.IDLE_PROCESS_ALL
IDLE_PROCESS_SPECIFIED = _core_.IDLE_PROCESS_SPECIFIED

class IdleEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.IdleEvent_swiginit(self, _core_.new_IdleEvent(*args, **kwargs))

    def RequestMore(*args, **kwargs):
        return _core_.IdleEvent_RequestMore(*args, **kwargs)

    def MoreRequested(*args, **kwargs):
        return _core_.IdleEvent_MoreRequested(*args, **kwargs)

    def SetMode(*args, **kwargs):
        return _core_.IdleEvent_SetMode(*args, **kwargs)

    SetMode = staticmethod(SetMode)

    def GetMode(*args, **kwargs):
        return _core_.IdleEvent_GetMode(*args, **kwargs)

    GetMode = staticmethod(GetMode)

    def CanSend(*args, **kwargs):
        return _core_.IdleEvent_CanSend(*args, **kwargs)

    CanSend = staticmethod(CanSend)


_core_.IdleEvent_swigregister(IdleEvent)

def IdleEvent_SetMode(*args, **kwargs):
    return _core_.IdleEvent_SetMode(*args, **kwargs)


def IdleEvent_GetMode(*args):
    return _core_.IdleEvent_GetMode(*args)


def IdleEvent_CanSend(*args, **kwargs):
    return _core_.IdleEvent_CanSend(*args, **kwargs)


class ClipboardTextEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.ClipboardTextEvent_swiginit(self, _core_.new_ClipboardTextEvent(*args, **kwargs))


_core_.ClipboardTextEvent_swigregister(ClipboardTextEvent)

class CtlColorEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.CtlColorEvent_swiginit(self, _core_.new_CtlColorEvent(*args, **kwargs))

    def GetDC(*args, **kwargs):
        return _core_.CtlColorEvent_GetDC(*args, **kwargs)

    def GetBrush(*args, **kwargs):
        return _core_.CtlColorEvent_GetBrush(*args, **kwargs)

    def SetBrush(*args, **kwargs):
        return _core_.CtlColorEvent_SetBrush(*args, **kwargs)

    def GetWindow(*args, **kwargs):
        return _core_.CtlColorEvent_GetWindow(*args, **kwargs)

    def SetWindow(*args, **kwargs):
        return _core_.CtlColorEvent_SetWindow(*args, **kwargs)

    DC = property(GetDC, doc='See `GetDC`')
    Brush = property(GetBrush, SetBrush)
    Window = property(GetWindow, SetWindow)


_core_.CtlColorEvent_swigregister(CtlColorEvent)

class PyEvent(Event):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PyEvent_swiginit(self, _core_.new_PyEvent(*args, **kwargs))
        self._SetSelf(self)

    __swig_destroy__ = _core_.delete_PyEvent
    __del__ = lambda self: None

    def _SetSelf(*args, **kwargs):
        return _core_.PyEvent__SetSelf(*args, **kwargs)

    def _GetSelf(*args, **kwargs):
        return _core_.PyEvent__GetSelf(*args, **kwargs)


_core_.PyEvent_swigregister(PyEvent)

class PyCommandEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PyCommandEvent_swiginit(self, _core_.new_PyCommandEvent(*args, **kwargs))
        self._SetSelf(self)

    __swig_destroy__ = _core_.delete_PyCommandEvent
    __del__ = lambda self: None

    def _SetSelf(*args, **kwargs):
        return _core_.PyCommandEvent__SetSelf(*args, **kwargs)

    def _GetSelf(*args, **kwargs):
        return _core_.PyCommandEvent__GetSelf(*args, **kwargs)


_core_.PyCommandEvent_swigregister(PyCommandEvent)

class DateEvent(CommandEvent):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.DateEvent_swiginit(self, _core_.new_DateEvent(*args, **kwargs))

    def GetDate(*args, **kwargs):
        return _core_.DateEvent_GetDate(*args, **kwargs)

    def SetDate(*args, **kwargs):
        return _core_.DateEvent_SetDate(*args, **kwargs)

    Date = property(GetDate, SetDate, doc='See `GetDate` and `SetDate`')


_core_.DateEvent_swigregister(DateEvent)
wxEVT_DATE_CHANGED = _core_.wxEVT_DATE_CHANGED
EVT_DATE_CHANGED = wx.PyEventBinder(wxEVT_DATE_CHANGED, 1)
PYAPP_ASSERT_SUPPRESS = _core_.PYAPP_ASSERT_SUPPRESS
PYAPP_ASSERT_EXCEPTION = _core_.PYAPP_ASSERT_EXCEPTION
PYAPP_ASSERT_DIALOG = _core_.PYAPP_ASSERT_DIALOG
PYAPP_ASSERT_LOG = _core_.PYAPP_ASSERT_LOG
PRINT_WINDOWS = _core_.PRINT_WINDOWS
PRINT_POSTSCRIPT = _core_.PRINT_POSTSCRIPT

class PyApp(EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PyApp_swiginit(self, _core_.new_PyApp(*args, **kwargs))
        self._setOORInfo(self, False)
        PyApp._setCallbackInfo(self, self, PyApp)
        self.this.own(True)

    __swig_destroy__ = _core_.delete_PyApp
    __del__ = lambda self: None

    def _setCallbackInfo(*args, **kwargs):
        return _core_.PyApp__setCallbackInfo(*args, **kwargs)

    def GetAppName(*args, **kwargs):
        return _core_.PyApp_GetAppName(*args, **kwargs)

    def SetAppName(*args, **kwargs):
        return _core_.PyApp_SetAppName(*args, **kwargs)

    def GetClassName(*args, **kwargs):
        return _core_.PyApp_GetClassName(*args, **kwargs)

    def SetClassName(*args, **kwargs):
        return _core_.PyApp_SetClassName(*args, **kwargs)

    def GetVendorName(*args, **kwargs):
        return _core_.PyApp_GetVendorName(*args, **kwargs)

    def SetVendorName(*args, **kwargs):
        return _core_.PyApp_SetVendorName(*args, **kwargs)

    def GetTraits(*args, **kwargs):
        return _core_.PyApp_GetTraits(*args, **kwargs)

    def ProcessPendingEvents(*args, **kwargs):
        return _core_.PyApp_ProcessPendingEvents(*args, **kwargs)

    def Yield(*args, **kwargs):
        return _core_.PyApp_Yield(*args, **kwargs)

    def WakeUpIdle(*args, **kwargs):
        return _core_.PyApp_WakeUpIdle(*args, **kwargs)

    def IsMainLoopRunning(*args, **kwargs):
        return _core_.PyApp_IsMainLoopRunning(*args, **kwargs)

    IsMainLoopRunning = staticmethod(IsMainLoopRunning)

    def MainLoop(*args, **kwargs):
        return _core_.PyApp_MainLoop(*args, **kwargs)

    def Exit(*args, **kwargs):
        return _core_.PyApp_Exit(*args, **kwargs)

    def GetLayoutDirection(*args, **kwargs):
        return _core_.PyApp_GetLayoutDirection(*args, **kwargs)

    def ExitMainLoop(*args, **kwargs):
        return _core_.PyApp_ExitMainLoop(*args, **kwargs)

    def Pending(*args, **kwargs):
        return _core_.PyApp_Pending(*args, **kwargs)

    def Dispatch(*args, **kwargs):
        return _core_.PyApp_Dispatch(*args, **kwargs)

    def ProcessIdle(*args, **kwargs):
        return _core_.PyApp_ProcessIdle(*args, **kwargs)

    def SendIdleEvents(*args, **kwargs):
        return _core_.PyApp_SendIdleEvents(*args, **kwargs)

    def IsActive(*args, **kwargs):
        return _core_.PyApp_IsActive(*args, **kwargs)

    def SetTopWindow(*args, **kwargs):
        return _core_.PyApp_SetTopWindow(*args, **kwargs)

    def GetTopWindow(*args, **kwargs):
        return _core_.PyApp_GetTopWindow(*args, **kwargs)

    def SetExitOnFrameDelete(*args, **kwargs):
        return _core_.PyApp_SetExitOnFrameDelete(*args, **kwargs)

    def GetExitOnFrameDelete(*args, **kwargs):
        return _core_.PyApp_GetExitOnFrameDelete(*args, **kwargs)

    def SetUseBestVisual(*args, **kwargs):
        return _core_.PyApp_SetUseBestVisual(*args, **kwargs)

    def GetUseBestVisual(*args, **kwargs):
        return _core_.PyApp_GetUseBestVisual(*args, **kwargs)

    def SetPrintMode(*args, **kwargs):
        return _core_.PyApp_SetPrintMode(*args, **kwargs)

    def GetPrintMode(*args, **kwargs):
        return _core_.PyApp_GetPrintMode(*args, **kwargs)

    def SetAssertMode(*args, **kwargs):
        return _core_.PyApp_SetAssertMode(*args, **kwargs)

    def GetAssertMode(*args, **kwargs):
        return _core_.PyApp_GetAssertMode(*args, **kwargs)

    def MacHideApp(*args, **kwargs):
        return _core_.PyApp_MacHideApp(*args, **kwargs)

    def MacRequestUserAttention(*args, **kwargs):
        return _core_.PyApp_MacRequestUserAttention(*args, **kwargs)

    def GetMacSupportPCMenuShortcuts(*args, **kwargs):
        return _core_.PyApp_GetMacSupportPCMenuShortcuts(*args, **kwargs)

    GetMacSupportPCMenuShortcuts = staticmethod(GetMacSupportPCMenuShortcuts)

    def GetMacAboutMenuItemId(*args, **kwargs):
        return _core_.PyApp_GetMacAboutMenuItemId(*args, **kwargs)

    GetMacAboutMenuItemId = staticmethod(GetMacAboutMenuItemId)

    def GetMacPreferencesMenuItemId(*args, **kwargs):
        return _core_.PyApp_GetMacPreferencesMenuItemId(*args, **kwargs)

    GetMacPreferencesMenuItemId = staticmethod(GetMacPreferencesMenuItemId)

    def GetMacExitMenuItemId(*args, **kwargs):
        return _core_.PyApp_GetMacExitMenuItemId(*args, **kwargs)

    GetMacExitMenuItemId = staticmethod(GetMacExitMenuItemId)

    def GetMacHelpMenuTitleName(*args, **kwargs):
        return _core_.PyApp_GetMacHelpMenuTitleName(*args, **kwargs)

    GetMacHelpMenuTitleName = staticmethod(GetMacHelpMenuTitleName)

    def SetMacSupportPCMenuShortcuts(*args, **kwargs):
        return _core_.PyApp_SetMacSupportPCMenuShortcuts(*args, **kwargs)

    SetMacSupportPCMenuShortcuts = staticmethod(SetMacSupportPCMenuShortcuts)

    def SetMacAboutMenuItemId(*args, **kwargs):
        return _core_.PyApp_SetMacAboutMenuItemId(*args, **kwargs)

    SetMacAboutMenuItemId = staticmethod(SetMacAboutMenuItemId)

    def SetMacPreferencesMenuItemId(*args, **kwargs):
        return _core_.PyApp_SetMacPreferencesMenuItemId(*args, **kwargs)

    SetMacPreferencesMenuItemId = staticmethod(SetMacPreferencesMenuItemId)

    def SetMacExitMenuItemId(*args, **kwargs):
        return _core_.PyApp_SetMacExitMenuItemId(*args, **kwargs)

    SetMacExitMenuItemId = staticmethod(SetMacExitMenuItemId)

    def SetMacHelpMenuTitleName(*args, **kwargs):
        return _core_.PyApp_SetMacHelpMenuTitleName(*args, **kwargs)

    SetMacHelpMenuTitleName = staticmethod(SetMacHelpMenuTitleName)

    def _BootstrapApp(*args, **kwargs):
        return _core_.PyApp__BootstrapApp(*args, **kwargs)

    def GetComCtl32Version(*args, **kwargs):
        return _core_.PyApp_GetComCtl32Version(*args, **kwargs)

    GetComCtl32Version = staticmethod(GetComCtl32Version)

    def IsDisplayAvailable(*args, **kwargs):
        return _core_.PyApp_IsDisplayAvailable(*args, **kwargs)

    IsDisplayAvailable = staticmethod(IsDisplayAvailable)
    AppName = property(GetAppName, SetAppName, doc='See `GetAppName` and `SetAppName`')
    AssertMode = property(GetAssertMode, SetAssertMode, doc='See `GetAssertMode` and `SetAssertMode`')
    ClassName = property(GetClassName, SetClassName, doc='See `GetClassName` and `SetClassName`')
    ExitOnFrameDelete = property(GetExitOnFrameDelete, SetExitOnFrameDelete, doc='See `GetExitOnFrameDelete` and `SetExitOnFrameDelete`')
    LayoutDirection = property(GetLayoutDirection, doc='See `GetLayoutDirection`')
    PrintMode = property(GetPrintMode, SetPrintMode, doc='See `GetPrintMode` and `SetPrintMode`')
    TopWindow = property(GetTopWindow, SetTopWindow, doc='See `GetTopWindow` and `SetTopWindow`')
    Traits = property(GetTraits, doc='See `GetTraits`')
    UseBestVisual = property(GetUseBestVisual, SetUseBestVisual, doc='See `GetUseBestVisual` and `SetUseBestVisual`')
    VendorName = property(GetVendorName, SetVendorName, doc='See `GetVendorName` and `SetVendorName`')
    Active = property(IsActive)


_core_.PyApp_swigregister(PyApp)

def PyApp_IsMainLoopRunning(*args):
    return _core_.PyApp_IsMainLoopRunning(*args)


def PyApp_GetMacSupportPCMenuShortcuts(*args):
    return _core_.PyApp_GetMacSupportPCMenuShortcuts(*args)


def PyApp_GetMacAboutMenuItemId(*args):
    return _core_.PyApp_GetMacAboutMenuItemId(*args)


def PyApp_GetMacPreferencesMenuItemId(*args):
    return _core_.PyApp_GetMacPreferencesMenuItemId(*args)


def PyApp_GetMacExitMenuItemId(*args):
    return _core_.PyApp_GetMacExitMenuItemId(*args)


def PyApp_GetMacHelpMenuTitleName(*args):
    return _core_.PyApp_GetMacHelpMenuTitleName(*args)


def PyApp_SetMacSupportPCMenuShortcuts(*args, **kwargs):
    return _core_.PyApp_SetMacSupportPCMenuShortcuts(*args, **kwargs)


def PyApp_SetMacAboutMenuItemId(*args, **kwargs):
    return _core_.PyApp_SetMacAboutMenuItemId(*args, **kwargs)


def PyApp_SetMacPreferencesMenuItemId(*args, **kwargs):
    return _core_.PyApp_SetMacPreferencesMenuItemId(*args, **kwargs)


def PyApp_SetMacExitMenuItemId(*args, **kwargs):
    return _core_.PyApp_SetMacExitMenuItemId(*args, **kwargs)


def PyApp_SetMacHelpMenuTitleName(*args, **kwargs):
    return _core_.PyApp_SetMacHelpMenuTitleName(*args, **kwargs)


def PyApp_GetComCtl32Version(*args):
    return _core_.PyApp_GetComCtl32Version(*args)


def PyApp_IsDisplayAvailable(*args):
    return _core_.PyApp_IsDisplayAvailable(*args)


def Exit(*args):
    return _core_.Exit(*args)


def Yield(*args):
    return _core_.Yield(*args)


def YieldIfNeeded(*args):
    return _core_.YieldIfNeeded(*args)


def SafeYield(*args, **kwargs):
    return _core_.SafeYield(*args, **kwargs)


def WakeUpIdle(*args):
    return _core_.WakeUpIdle(*args)


def PostEvent(*args, **kwargs):
    return _core_.PostEvent(*args, **kwargs)


def App_CleanUp(*args):
    return _core_.App_CleanUp(*args)


def GetApp(*args):
    return _core_.GetApp(*args)


def SetDefaultPyEncoding(*args, **kwargs):
    return _core_.SetDefaultPyEncoding(*args, **kwargs)


def GetDefaultPyEncoding(*args):
    return _core_.GetDefaultPyEncoding(*args)


class PyOnDemandOutputWindow():

    def __init__(self, title = 'wxPython: stdout/stderr'):
        self.frame = None
        self.title = title
        self.pos = wx.DefaultPosition
        self.size = (450, 300)
        self.parent = None
        self.triggers = []

    def SetParent(self, parent):
        self.parent = parent

    def RaiseWhenSeen(self, trigger):
        import types
        if type(trigger) in types.StringTypes:
            trigger = [trigger]
        self.triggers = trigger

    def CreateOutputWindow(self, st):
        self.frame = wx.Frame(self.parent, -1, self.title, self.pos, self.size, style=wx.DEFAULT_FRAME_STYLE)
        self.text = wx.TextCtrl(self.frame, -1, '', style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.text.AppendText(st)
        self.frame.Show(True)
        self.frame.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnCloseWindow(self, event):
        if self.frame is not None:
            self.frame.Destroy()
        self.frame = None
        self.text = None
        self.parent = None

    def write(self, text):
        if self.frame is None:
            if not wx.Thread_IsMain():
                wx.CallAfter(self.CreateOutputWindow, text)
            else:
                self.CreateOutputWindow(text)
        elif not wx.Thread_IsMain():
            wx.CallAfter(self.__write, text)
        else:
            self.__write(text)

    def __write(self, text):
        self.text.AppendText(text)
        for item in self.triggers:
            if item in text:
                self.frame.Raise()
                break

    def close(self):
        if self.frame is not None:
            wx.CallAfter(self.frame.Close)

    def flush(self):
        pass


_defRedirect = wx.Platform == '__WXMSW__' or wx.Platform == '__WXMAC__'

class App(wx.PyApp):
    outputWindowClass = PyOnDemandOutputWindow

    def __init__(self, redirect = _defRedirect, filename = None, useBestVisual = False, clearSigInt = True):
        wx.PyApp.__init__(self)
        if not self.IsDisplayAvailable():
            if wx.Platform == '__WXMAC__':
                msg = "This program needs access to the screen.\nPlease run with 'pythonw', not 'python', and only when you are logged\nin on the main display of your Mac."
            elif wx.Platform == '__WXGTK__':
                msg = 'Unable to access the X Display, is $DISPLAY set properly?'
            else:
                msg = 'Unable to create GUI'
            raise SystemExit(msg)
        self.SetUseBestVisual(useBestVisual)
        if clearSigInt:
            try:
                import signal
                signal.signal(signal.SIGINT, signal.SIG_DFL)
            except:
                pass

        self.stdioWin = None
        self.saveStdio = (_sys.stdout, _sys.stderr)
        if redirect:
            self.RedirectStdio(filename)
        wx.StandardPaths.Get().SetInstallPrefix(_sys.prefix)
        wx.SystemOptions.SetOptionInt('mac.listctrl.always_use_generic', 1)
        self._BootstrapApp()

    def OnPreInit(self):
        wx.StockGDI._initStockObjects()

    def __del__(self, destroy = wx.PyApp.__del__):
        self.RestoreStdio()
        destroy(self)

    def Destroy(self):
        self.this.own(False)
        wx.PyApp.Destroy(self)

    def SetTopWindow(self, frame):
        if self.stdioWin:
            self.stdioWin.SetParent(frame)
        wx.PyApp.SetTopWindow(self, frame)

    def MainLoop(self):
        wx.PyApp.MainLoop(self)
        self.RestoreStdio()

    def RedirectStdio(self, filename = None):
        if filename:
            _sys.stdout = _sys.stderr = open(filename, 'a')
        else:
            self.stdioWin = self.outputWindowClass()
            _sys.stdout = _sys.stderr = self.stdioWin

    def RestoreStdio(self):
        try:
            _sys.stdout, _sys.stderr = self.saveStdio
        except:
            pass

    def SetOutputWindowAttributes(self, title = None, pos = None, size = None):
        if self.stdioWin:
            if title is not None:
                self.stdioWin.title = title
            if pos is not None:
                self.stdioWin.pos = pos
            if size is not None:
                self.stdioWin.size = size


App_GetMacSupportPCMenuShortcuts = _core_.PyApp_GetMacSupportPCMenuShortcuts
App_GetMacAboutMenuItemId = _core_.PyApp_GetMacAboutMenuItemId
App_GetMacPreferencesMenuItemId = _core_.PyApp_GetMacPreferencesMenuItemId
App_GetMacExitMenuItemId = _core_.PyApp_GetMacExitMenuItemId
App_GetMacHelpMenuTitleName = _core_.PyApp_GetMacHelpMenuTitleName
App_SetMacSupportPCMenuShortcuts = _core_.PyApp_SetMacSupportPCMenuShortcuts
App_SetMacAboutMenuItemId = _core_.PyApp_SetMacAboutMenuItemId
App_SetMacPreferencesMenuItemId = _core_.PyApp_SetMacPreferencesMenuItemId
App_SetMacExitMenuItemId = _core_.PyApp_SetMacExitMenuItemId
App_SetMacHelpMenuTitleName = _core_.PyApp_SetMacHelpMenuTitleName
App_GetComCtl32Version = _core_.PyApp_GetComCtl32Version

class PySimpleApp(wx.App):

    def __init__(self, redirect = False, filename = None, useBestVisual = False, clearSigInt = True):
        wx.App.__init__(self, redirect, filename, useBestVisual, clearSigInt)

    def OnInit(self):
        return True


class PyWidgetTester(wx.App):

    def __init__(self, size = (250, 100)):
        self.size = size
        wx.App.__init__(self, 0)

    def OnInit(self):
        self.frame = wx.Frame(None, -1, 'Widget Tester', pos=(0, 0), size=self.size)
        self.SetTopWindow(self.frame)
        return True

    def SetWidget(self, widgetClass, *args, **kwargs):
        w = widgetClass(self.frame, *args, **kwargs)
        self.frame.Show(True)


class __wxPyCleanup():

    def __init__(self):
        self.cleanup = _core_.App_CleanUp

    def __del__(self):
        self.cleanup()


_sys.__wxPythonCleanup = __wxPyCleanup()

class EventLoop(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.EventLoop_swiginit(self, _core_.new_EventLoop(*args, **kwargs))

    __swig_destroy__ = _core_.delete_EventLoop
    __del__ = lambda self: None

    def Run(*args, **kwargs):
        return _core_.EventLoop_Run(*args, **kwargs)

    def Exit(*args, **kwargs):
        return _core_.EventLoop_Exit(*args, **kwargs)

    def Pending(*args, **kwargs):
        return _core_.EventLoop_Pending(*args, **kwargs)

    def Dispatch(*args, **kwargs):
        return _core_.EventLoop_Dispatch(*args, **kwargs)

    def IsRunning(*args, **kwargs):
        return _core_.EventLoop_IsRunning(*args, **kwargs)

    def GetActive(*args, **kwargs):
        return _core_.EventLoop_GetActive(*args, **kwargs)

    GetActive = staticmethod(GetActive)

    def SetActive(*args, **kwargs):
        return _core_.EventLoop_SetActive(*args, **kwargs)

    SetActive = staticmethod(SetActive)


_core_.EventLoop_swigregister(EventLoop)

def EventLoop_GetActive(*args):
    return _core_.EventLoop_GetActive(*args)


def EventLoop_SetActive(*args, **kwargs):
    return _core_.EventLoop_SetActive(*args, **kwargs)


class EventLoopActivator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.EventLoopActivator_swiginit(self, _core_.new_EventLoopActivator(*args, **kwargs))

    __swig_destroy__ = _core_.delete_EventLoopActivator
    __del__ = lambda self: None


_core_.EventLoopActivator_swigregister(EventLoopActivator)

class EventLoopGuarantor(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.EventLoopGuarantor_swiginit(self, _core_.new_EventLoopGuarantor(*args, **kwargs))

    __swig_destroy__ = _core_.delete_EventLoopGuarantor
    __del__ = lambda self: None


_core_.EventLoopGuarantor_swigregister(EventLoopGuarantor)
ACCEL_ALT = _core_.ACCEL_ALT
ACCEL_CTRL = _core_.ACCEL_CTRL
ACCEL_SHIFT = _core_.ACCEL_SHIFT
ACCEL_NORMAL = _core_.ACCEL_NORMAL
ACCEL_CMD = _core_.ACCEL_CMD

class AcceleratorEntry(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.AcceleratorEntry_swiginit(self, _core_.new_AcceleratorEntry(*args, **kwargs))

    __swig_destroy__ = _core_.delete_AcceleratorEntry
    __del__ = lambda self: None

    def Set(*args, **kwargs):
        return _core_.AcceleratorEntry_Set(*args, **kwargs)

    def Create(*args, **kwargs):
        return _core_.AcceleratorEntry_Create(*args, **kwargs)

    Create = staticmethod(Create)

    def GetFlags(*args, **kwargs):
        return _core_.AcceleratorEntry_GetFlags(*args, **kwargs)

    def GetKeyCode(*args, **kwargs):
        return _core_.AcceleratorEntry_GetKeyCode(*args, **kwargs)

    def GetCommand(*args, **kwargs):
        return _core_.AcceleratorEntry_GetCommand(*args, **kwargs)

    def IsOk(*args, **kwargs):
        return _core_.AcceleratorEntry_IsOk(*args, **kwargs)

    def ToString(*args, **kwargs):
        return _core_.AcceleratorEntry_ToString(*args, **kwargs)

    def FromString(*args, **kwargs):
        return _core_.AcceleratorEntry_FromString(*args, **kwargs)

    Command = property(GetCommand, doc='See `GetCommand`')
    Flags = property(GetFlags, doc='See `GetFlags`')
    KeyCode = property(GetKeyCode, doc='See `GetKeyCode`')


_core_.AcceleratorEntry_swigregister(AcceleratorEntry)

def AcceleratorEntry_Create(*args, **kwargs):
    return _core_.AcceleratorEntry_Create(*args, **kwargs)


class AcceleratorTable(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.AcceleratorTable_swiginit(self, _core_.new_AcceleratorTable(*args, **kwargs))

    __swig_destroy__ = _core_.delete_AcceleratorTable
    __del__ = lambda self: None

    def IsOk(*args, **kwargs):
        return _core_.AcceleratorTable_IsOk(*args, **kwargs)

    Ok = IsOk


_core_.AcceleratorTable_swigregister(AcceleratorTable)

def GetAccelFromString(*args, **kwargs):
    return _core_.GetAccelFromString(*args, **kwargs)


class WindowList_iterator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_WindowList_iterator
    __del__ = lambda self: None

    def next(*args, **kwargs):
        return _core_.WindowList_iterator_next(*args, **kwargs)


_core_.WindowList_iterator_swigregister(WindowList_iterator)
NullAcceleratorTable = cvar.NullAcceleratorTable
PanelNameStr = cvar.PanelNameStr

class WindowList(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_WindowList
    __del__ = lambda self: None

    def __len__(*args, **kwargs):
        return _core_.WindowList___len__(*args, **kwargs)

    def __getitem__(*args, **kwargs):
        return _core_.WindowList___getitem__(*args, **kwargs)

    def __contains__(*args, **kwargs):
        return _core_.WindowList___contains__(*args, **kwargs)

    def __iter__(*args, **kwargs):
        return _core_.WindowList___iter__(*args, **kwargs)

    def index(*args, **kwargs):
        return _core_.WindowList_index(*args, **kwargs)

    def __repr__(self):
        return 'wxWindowList: ' + repr(list(self))


_core_.WindowList_swigregister(WindowList)

class VisualAttributes(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.VisualAttributes_swiginit(self, _core_.new_VisualAttributes(*args, **kwargs))

    __swig_destroy__ = _core_.delete_VisualAttributes
    __del__ = lambda self: None

    def _get_font(*args, **kwargs):
        return _core_.VisualAttributes__get_font(*args, **kwargs)

    def _get_colFg(*args, **kwargs):
        return _core_.VisualAttributes__get_colFg(*args, **kwargs)

    def _get_colBg(*args, **kwargs):
        return _core_.VisualAttributes__get_colBg(*args, **kwargs)

    font = property(_get_font)
    colFg = property(_get_colFg)
    colBg = property(_get_colBg)


_core_.VisualAttributes_swigregister(VisualAttributes)
WINDOW_VARIANT_NORMAL = _core_.WINDOW_VARIANT_NORMAL
WINDOW_VARIANT_SMALL = _core_.WINDOW_VARIANT_SMALL
WINDOW_VARIANT_MINI = _core_.WINDOW_VARIANT_MINI
WINDOW_VARIANT_LARGE = _core_.WINDOW_VARIANT_LARGE
WINDOW_VARIANT_MAX = _core_.WINDOW_VARIANT_MAX

class Window(EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Window_swiginit(self, _core_.new_Window(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _core_.Window_Create(*args, **kwargs)

    def Close(*args, **kwargs):
        return _core_.Window_Close(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _core_.Window_Destroy(*args, **kwargs)

    def DestroyChildren(*args, **kwargs):
        return _core_.Window_DestroyChildren(*args, **kwargs)

    def IsBeingDeleted(*args, **kwargs):
        return _core_.Window_IsBeingDeleted(*args, **kwargs)

    def SetLabel(*args, **kwargs):
        return _core_.Window_SetLabel(*args, **kwargs)

    def GetLabel(*args, **kwargs):
        return _core_.Window_GetLabel(*args, **kwargs)

    def SetName(*args, **kwargs):
        return _core_.Window_SetName(*args, **kwargs)

    def GetName(*args, **kwargs):
        return _core_.Window_GetName(*args, **kwargs)

    def SetWindowVariant(*args, **kwargs):
        return _core_.Window_SetWindowVariant(*args, **kwargs)

    def GetWindowVariant(*args, **kwargs):
        return _core_.Window_GetWindowVariant(*args, **kwargs)

    def SetId(*args, **kwargs):
        return _core_.Window_SetId(*args, **kwargs)

    def GetId(*args, **kwargs):
        return _core_.Window_GetId(*args, **kwargs)

    def NewControlId(*args, **kwargs):
        return _core_.Window_NewControlId(*args, **kwargs)

    NewControlId = staticmethod(NewControlId)

    def NextControlId(*args, **kwargs):
        return _core_.Window_NextControlId(*args, **kwargs)

    NextControlId = staticmethod(NextControlId)

    def PrevControlId(*args, **kwargs):
        return _core_.Window_PrevControlId(*args, **kwargs)

    PrevControlId = staticmethod(PrevControlId)

    def GetLayoutDirection(*args, **kwargs):
        return _core_.Window_GetLayoutDirection(*args, **kwargs)

    def SetLayoutDirection(*args, **kwargs):
        return _core_.Window_SetLayoutDirection(*args, **kwargs)

    def AdjustForLayoutDirection(*args, **kwargs):
        return _core_.Window_AdjustForLayoutDirection(*args, **kwargs)

    def SetSize(*args, **kwargs):
        return _core_.Window_SetSize(*args, **kwargs)

    def SetDimensions(*args, **kwargs):
        return _core_.Window_SetDimensions(*args, **kwargs)

    def SetRect(*args, **kwargs):
        return _core_.Window_SetRect(*args, **kwargs)

    def SetSizeWH(*args, **kwargs):
        return _core_.Window_SetSizeWH(*args, **kwargs)

    def Move(*args, **kwargs):
        return _core_.Window_Move(*args, **kwargs)

    SetPosition = Move

    def MoveXY(*args, **kwargs):
        return _core_.Window_MoveXY(*args, **kwargs)

    def SetInitialSize(*args, **kwargs):
        return _core_.Window_SetInitialSize(*args, **kwargs)

    SetBestFittingSize = wx._deprecated(SetInitialSize, 'Use `SetInitialSize`')

    def Raise(*args, **kwargs):
        return _core_.Window_Raise(*args, **kwargs)

    def Lower(*args, **kwargs):
        return _core_.Window_Lower(*args, **kwargs)

    def SetClientSize(*args, **kwargs):
        return _core_.Window_SetClientSize(*args, **kwargs)

    def SetClientSizeWH(*args, **kwargs):
        return _core_.Window_SetClientSizeWH(*args, **kwargs)

    def SetClientRect(*args, **kwargs):
        return _core_.Window_SetClientRect(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.Window_GetPosition(*args, **kwargs)

    def GetPositionTuple(*args, **kwargs):
        return _core_.Window_GetPositionTuple(*args, **kwargs)

    def GetScreenPosition(*args, **kwargs):
        return _core_.Window_GetScreenPosition(*args, **kwargs)

    def GetScreenPositionTuple(*args, **kwargs):
        return _core_.Window_GetScreenPositionTuple(*args, **kwargs)

    def GetScreenRect(*args, **kwargs):
        return _core_.Window_GetScreenRect(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _core_.Window_GetSize(*args, **kwargs)

    def GetSizeTuple(*args, **kwargs):
        return _core_.Window_GetSizeTuple(*args, **kwargs)

    def GetRect(*args, **kwargs):
        return _core_.Window_GetRect(*args, **kwargs)

    def GetClientSize(*args, **kwargs):
        return _core_.Window_GetClientSize(*args, **kwargs)

    def GetClientSizeTuple(*args, **kwargs):
        return _core_.Window_GetClientSizeTuple(*args, **kwargs)

    def GetClientAreaOrigin(*args, **kwargs):
        return _core_.Window_GetClientAreaOrigin(*args, **kwargs)

    def GetClientRect(*args, **kwargs):
        return _core_.Window_GetClientRect(*args, **kwargs)

    def ClientToWindowSize(*args, **kwargs):
        return _core_.Window_ClientToWindowSize(*args, **kwargs)

    def WindowToClientSize(*args, **kwargs):
        return _core_.Window_WindowToClientSize(*args, **kwargs)

    def GetBestSize(*args, **kwargs):
        return _core_.Window_GetBestSize(*args, **kwargs)

    def GetBestSizeTuple(*args, **kwargs):
        return _core_.Window_GetBestSizeTuple(*args, **kwargs)

    def InvalidateBestSize(*args, **kwargs):
        return _core_.Window_InvalidateBestSize(*args, **kwargs)

    def CacheBestSize(*args, **kwargs):
        return _core_.Window_CacheBestSize(*args, **kwargs)

    def GetEffectiveMinSize(*args, **kwargs):
        return _core_.Window_GetEffectiveMinSize(*args, **kwargs)

    GetBestFittingSize = wx._deprecated(GetEffectiveMinSize, 'Use `GetEffectiveMinSize` instead.')

    def GetAdjustedBestSize(self):
        s = self.GetBestSize()
        return wx.Size(max(s.width, self.GetMinWidth()), max(s.height, self.GetMinHeight()))

    GetAdjustedBestSize = wx._deprecated(GetAdjustedBestSize, 'Use `GetEffectiveMinSize` instead.')

    def Center(*args, **kwargs):
        return _core_.Window_Center(*args, **kwargs)

    Centre = Center

    def CenterOnParent(*args, **kwargs):
        return _core_.Window_CenterOnParent(*args, **kwargs)

    CentreOnParent = CenterOnParent

    def Fit(*args, **kwargs):
        return _core_.Window_Fit(*args, **kwargs)

    def FitInside(*args, **kwargs):
        return _core_.Window_FitInside(*args, **kwargs)

    def SetSizeHints(*args, **kwargs):
        return _core_.Window_SetSizeHints(*args, **kwargs)

    def SetSizeHintsSz(*args, **kwargs):
        return _core_.Window_SetSizeHintsSz(*args, **kwargs)

    def SetVirtualSizeHints(*args, **kwargs):
        return _core_.Window_SetVirtualSizeHints(*args, **kwargs)

    def SetVirtualSizeHintsSz(*args, **kwargs):
        return _core_.Window_SetVirtualSizeHintsSz(*args, **kwargs)

    def GetMaxSize(*args, **kwargs):
        return _core_.Window_GetMaxSize(*args, **kwargs)

    def GetMinSize(*args, **kwargs):
        return _core_.Window_GetMinSize(*args, **kwargs)

    def SetMinSize(*args, **kwargs):
        return _core_.Window_SetMinSize(*args, **kwargs)

    def SetMaxSize(*args, **kwargs):
        return _core_.Window_SetMaxSize(*args, **kwargs)

    def GetMinWidth(*args, **kwargs):
        return _core_.Window_GetMinWidth(*args, **kwargs)

    def GetMinHeight(*args, **kwargs):
        return _core_.Window_GetMinHeight(*args, **kwargs)

    def GetMaxWidth(*args, **kwargs):
        return _core_.Window_GetMaxWidth(*args, **kwargs)

    def GetMaxHeight(*args, **kwargs):
        return _core_.Window_GetMaxHeight(*args, **kwargs)

    def SetVirtualSize(*args, **kwargs):
        return _core_.Window_SetVirtualSize(*args, **kwargs)

    def SetVirtualSizeWH(*args, **kwargs):
        return _core_.Window_SetVirtualSizeWH(*args, **kwargs)

    def GetVirtualSize(*args, **kwargs):
        return _core_.Window_GetVirtualSize(*args, **kwargs)

    def GetVirtualSizeTuple(*args, **kwargs):
        return _core_.Window_GetVirtualSizeTuple(*args, **kwargs)

    def GetWindowBorderSize(*args, **kwargs):
        return _core_.Window_GetWindowBorderSize(*args, **kwargs)

    def GetBestVirtualSize(*args, **kwargs):
        return _core_.Window_GetBestVirtualSize(*args, **kwargs)

    def Show(*args, **kwargs):
        return _core_.Window_Show(*args, **kwargs)

    def Hide(*args, **kwargs):
        return _core_.Window_Hide(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _core_.Window_Enable(*args, **kwargs)

    def Disable(*args, **kwargs):
        return _core_.Window_Disable(*args, **kwargs)

    def IsShown(*args, **kwargs):
        return _core_.Window_IsShown(*args, **kwargs)

    def IsEnabled(*args, **kwargs):
        return _core_.Window_IsEnabled(*args, **kwargs)

    def IsShownOnScreen(*args, **kwargs):
        return _core_.Window_IsShownOnScreen(*args, **kwargs)

    def SetWindowStyleFlag(*args, **kwargs):
        return _core_.Window_SetWindowStyleFlag(*args, **kwargs)

    def GetWindowStyleFlag(*args, **kwargs):
        return _core_.Window_GetWindowStyleFlag(*args, **kwargs)

    SetWindowStyle = SetWindowStyleFlag
    GetWindowStyle = GetWindowStyleFlag

    def HasFlag(*args, **kwargs):
        return _core_.Window_HasFlag(*args, **kwargs)

    def IsRetained(*args, **kwargs):
        return _core_.Window_IsRetained(*args, **kwargs)

    def ToggleWindowStyle(*args, **kwargs):
        return _core_.Window_ToggleWindowStyle(*args, **kwargs)

    def SetExtraStyle(*args, **kwargs):
        return _core_.Window_SetExtraStyle(*args, **kwargs)

    def GetExtraStyle(*args, **kwargs):
        return _core_.Window_GetExtraStyle(*args, **kwargs)

    def MakeModal(*args, **kwargs):
        return _core_.Window_MakeModal(*args, **kwargs)

    def SetThemeEnabled(*args, **kwargs):
        return _core_.Window_SetThemeEnabled(*args, **kwargs)

    def GetThemeEnabled(*args, **kwargs):
        return _core_.Window_GetThemeEnabled(*args, **kwargs)

    def SetFocus(*args, **kwargs):
        return _core_.Window_SetFocus(*args, **kwargs)

    def SetFocusFromKbd(*args, **kwargs):
        return _core_.Window_SetFocusFromKbd(*args, **kwargs)

    def FindFocus(*args, **kwargs):
        return _core_.Window_FindFocus(*args, **kwargs)

    FindFocus = staticmethod(FindFocus)

    def AcceptsFocus(*args, **kwargs):
        return _core_.Window_AcceptsFocus(*args, **kwargs)

    def AcceptsFocusFromKeyboard(*args, **kwargs):
        return _core_.Window_AcceptsFocusFromKeyboard(*args, **kwargs)

    def Navigate(*args, **kwargs):
        return _core_.Window_Navigate(*args, **kwargs)

    def MoveAfterInTabOrder(*args, **kwargs):
        return _core_.Window_MoveAfterInTabOrder(*args, **kwargs)

    def MoveBeforeInTabOrder(*args, **kwargs):
        return _core_.Window_MoveBeforeInTabOrder(*args, **kwargs)

    def GetChildren(*args, **kwargs):
        return _core_.Window_GetChildren(*args, **kwargs)

    def GetParent(*args, **kwargs):
        return _core_.Window_GetParent(*args, **kwargs)

    def GetGrandParent(*args, **kwargs):
        return _core_.Window_GetGrandParent(*args, **kwargs)

    def GetTopLevelParent(*args, **kwargs):
        return _core_.Window_GetTopLevelParent(*args, **kwargs)

    def IsTopLevel(*args, **kwargs):
        return _core_.Window_IsTopLevel(*args, **kwargs)

    def Reparent(*args, **kwargs):
        return _core_.Window_Reparent(*args, **kwargs)

    def AddChild(*args, **kwargs):
        return _core_.Window_AddChild(*args, **kwargs)

    def RemoveChild(*args, **kwargs):
        return _core_.Window_RemoveChild(*args, **kwargs)

    def FindWindowById(*args, **kwargs):
        return _core_.Window_FindWindowById(*args, **kwargs)

    def FindWindowByName(*args, **kwargs):
        return _core_.Window_FindWindowByName(*args, **kwargs)

    def FindWindowByLabel(*args, **kwargs):
        return _core_.Window_FindWindowByLabel(*args, **kwargs)

    def GetEventHandler(*args, **kwargs):
        return _core_.Window_GetEventHandler(*args, **kwargs)

    def SetEventHandler(*args, **kwargs):
        return _core_.Window_SetEventHandler(*args, **kwargs)

    def PushEventHandler(*args, **kwargs):
        return _core_.Window_PushEventHandler(*args, **kwargs)

    def PopEventHandler(*args, **kwargs):
        return _core_.Window_PopEventHandler(*args, **kwargs)

    def RemoveEventHandler(*args, **kwargs):
        return _core_.Window_RemoveEventHandler(*args, **kwargs)

    def SetAcceleratorTable(*args, **kwargs):
        return _core_.Window_SetAcceleratorTable(*args, **kwargs)

    def GetAcceleratorTable(*args, **kwargs):
        return _core_.Window_GetAcceleratorTable(*args, **kwargs)

    def RegisterHotKey(*args, **kwargs):
        return _core_.Window_RegisterHotKey(*args, **kwargs)

    def UnregisterHotKey(*args, **kwargs):
        return _core_.Window_UnregisterHotKey(*args, **kwargs)

    def ConvertDialogPointToPixels(*args, **kwargs):
        return _core_.Window_ConvertDialogPointToPixels(*args, **kwargs)

    def ConvertDialogSizeToPixels(*args, **kwargs):
        return _core_.Window_ConvertDialogSizeToPixels(*args, **kwargs)

    def DLG_PNT(*args, **kwargs):
        return _core_.Window_DLG_PNT(*args, **kwargs)

    def DLG_SZE(*args, **kwargs):
        return _core_.Window_DLG_SZE(*args, **kwargs)

    def ConvertPixelPointToDialog(*args, **kwargs):
        return _core_.Window_ConvertPixelPointToDialog(*args, **kwargs)

    def ConvertPixelSizeToDialog(*args, **kwargs):
        return _core_.Window_ConvertPixelSizeToDialog(*args, **kwargs)

    def WarpPointer(*args, **kwargs):
        return _core_.Window_WarpPointer(*args, **kwargs)

    def CaptureMouse(*args, **kwargs):
        return _core_.Window_CaptureMouse(*args, **kwargs)

    def ReleaseMouse(*args, **kwargs):
        return _core_.Window_ReleaseMouse(*args, **kwargs)

    def GetCapture(*args, **kwargs):
        return _core_.Window_GetCapture(*args, **kwargs)

    GetCapture = staticmethod(GetCapture)

    def HasCapture(*args, **kwargs):
        return _core_.Window_HasCapture(*args, **kwargs)

    def Refresh(*args, **kwargs):
        return _core_.Window_Refresh(*args, **kwargs)

    def RefreshRect(*args, **kwargs):
        return _core_.Window_RefreshRect(*args, **kwargs)

    def Update(*args, **kwargs):
        return _core_.Window_Update(*args, **kwargs)

    def ClearBackground(*args, **kwargs):
        return _core_.Window_ClearBackground(*args, **kwargs)

    def Freeze(*args, **kwargs):
        return _core_.Window_Freeze(*args, **kwargs)

    def IsFrozen(*args, **kwargs):
        return _core_.Window_IsFrozen(*args, **kwargs)

    def Thaw(*args, **kwargs):
        return _core_.Window_Thaw(*args, **kwargs)

    def PrepareDC(*args, **kwargs):
        return _core_.Window_PrepareDC(*args, **kwargs)

    def IsDoubleBuffered(*args, **kwargs):
        return _core_.Window_IsDoubleBuffered(*args, **kwargs)

    def SetDoubleBuffered(*args, **kwargs):
        return _core_.Window_SetDoubleBuffered(*args, **kwargs)

    def GetUpdateRegion(*args, **kwargs):
        return _core_.Window_GetUpdateRegion(*args, **kwargs)

    def GetUpdateClientRect(*args, **kwargs):
        return _core_.Window_GetUpdateClientRect(*args, **kwargs)

    def IsExposed(*args, **kwargs):
        return _core_.Window_IsExposed(*args, **kwargs)

    def IsExposedPoint(*args, **kwargs):
        return _core_.Window_IsExposedPoint(*args, **kwargs)

    def IsExposedRect(*args, **kwargs):
        return _core_.Window_IsExposedRect(*args, **kwargs)

    def GetDefaultAttributes(*args, **kwargs):
        return _core_.Window_GetDefaultAttributes(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _core_.Window_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)

    def SetBackgroundColour(*args, **kwargs):
        return _core_.Window_SetBackgroundColour(*args, **kwargs)

    def SetOwnBackgroundColour(*args, **kwargs):
        return _core_.Window_SetOwnBackgroundColour(*args, **kwargs)

    def SetForegroundColour(*args, **kwargs):
        return _core_.Window_SetForegroundColour(*args, **kwargs)

    def SetOwnForegroundColour(*args, **kwargs):
        return _core_.Window_SetOwnForegroundColour(*args, **kwargs)

    def GetBackgroundColour(*args, **kwargs):
        return _core_.Window_GetBackgroundColour(*args, **kwargs)

    def GetForegroundColour(*args, **kwargs):
        return _core_.Window_GetForegroundColour(*args, **kwargs)

    def InheritsBackgroundColour(*args, **kwargs):
        return _core_.Window_InheritsBackgroundColour(*args, **kwargs)

    def UseBgCol(*args, **kwargs):
        return _core_.Window_UseBgCol(*args, **kwargs)

    def SetBackgroundStyle(*args, **kwargs):
        return _core_.Window_SetBackgroundStyle(*args, **kwargs)

    def GetBackgroundStyle(*args, **kwargs):
        return _core_.Window_GetBackgroundStyle(*args, **kwargs)

    def HasTransparentBackground(*args, **kwargs):
        return _core_.Window_HasTransparentBackground(*args, **kwargs)

    def SetCursor(*args, **kwargs):
        return _core_.Window_SetCursor(*args, **kwargs)

    def GetCursor(*args, **kwargs):
        return _core_.Window_GetCursor(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _core_.Window_SetFont(*args, **kwargs)

    def SetOwnFont(*args, **kwargs):
        return _core_.Window_SetOwnFont(*args, **kwargs)

    def GetFont(*args, **kwargs):
        return _core_.Window_GetFont(*args, **kwargs)

    def SetCaret(*args, **kwargs):
        return _core_.Window_SetCaret(*args, **kwargs)

    def GetCaret(*args, **kwargs):
        return _core_.Window_GetCaret(*args, **kwargs)

    def GetCharHeight(*args, **kwargs):
        return _core_.Window_GetCharHeight(*args, **kwargs)

    def GetCharWidth(*args, **kwargs):
        return _core_.Window_GetCharWidth(*args, **kwargs)

    def GetTextExtent(*args, **kwargs):
        return _core_.Window_GetTextExtent(*args, **kwargs)

    def GetFullTextExtent(*args, **kwargs):
        return _core_.Window_GetFullTextExtent(*args, **kwargs)

    def ClientToScreenXY(*args, **kwargs):
        return _core_.Window_ClientToScreenXY(*args, **kwargs)

    def ScreenToClientXY(*args, **kwargs):
        return _core_.Window_ScreenToClientXY(*args, **kwargs)

    def ClientToScreen(*args, **kwargs):
        return _core_.Window_ClientToScreen(*args, **kwargs)

    def ScreenToClient(*args, **kwargs):
        return _core_.Window_ScreenToClient(*args, **kwargs)

    def HitTestXY(*args, **kwargs):
        return _core_.Window_HitTestXY(*args, **kwargs)

    def HitTest(*args, **kwargs):
        return _core_.Window_HitTest(*args, **kwargs)

    def GetBorder(*args):
        return _core_.Window_GetBorder(*args)

    def UpdateWindowUI(*args, **kwargs):
        return _core_.Window_UpdateWindowUI(*args, **kwargs)

    def PopupMenuXY(*args, **kwargs):
        return _core_.Window_PopupMenuXY(*args, **kwargs)

    def PopupMenu(*args, **kwargs):
        return _core_.Window_PopupMenu(*args, **kwargs)

    def HasMultiplePages(*args, **kwargs):
        return _core_.Window_HasMultiplePages(*args, **kwargs)

    def GetHandle(*args, **kwargs):
        return _core_.Window_GetHandle(*args, **kwargs)

    def AssociateHandle(*args, **kwargs):
        return _core_.Window_AssociateHandle(*args, **kwargs)

    def DissociateHandle(*args, **kwargs):
        return _core_.Window_DissociateHandle(*args, **kwargs)

    def GetGtkWidget(*args, **kwargs):
        return _core_.Window_GetGtkWidget(*args, **kwargs)

    def HasScrollbar(*args, **kwargs):
        return _core_.Window_HasScrollbar(*args, **kwargs)

    def SetScrollbar(*args, **kwargs):
        return _core_.Window_SetScrollbar(*args, **kwargs)

    def SetScrollPos(*args, **kwargs):
        return _core_.Window_SetScrollPos(*args, **kwargs)

    def GetScrollPos(*args, **kwargs):
        return _core_.Window_GetScrollPos(*args, **kwargs)

    def GetScrollThumb(*args, **kwargs):
        return _core_.Window_GetScrollThumb(*args, **kwargs)

    def GetScrollRange(*args, **kwargs):
        return _core_.Window_GetScrollRange(*args, **kwargs)

    def ScrollWindow(*args, **kwargs):
        return _core_.Window_ScrollWindow(*args, **kwargs)

    def ScrollLines(*args, **kwargs):
        return _core_.Window_ScrollLines(*args, **kwargs)

    def ScrollPages(*args, **kwargs):
        return _core_.Window_ScrollPages(*args, **kwargs)

    def LineUp(*args, **kwargs):
        return _core_.Window_LineUp(*args, **kwargs)

    def LineDown(*args, **kwargs):
        return _core_.Window_LineDown(*args, **kwargs)

    def PageUp(*args, **kwargs):
        return _core_.Window_PageUp(*args, **kwargs)

    def PageDown(*args, **kwargs):
        return _core_.Window_PageDown(*args, **kwargs)

    def SetHelpText(*args, **kwargs):
        return _core_.Window_SetHelpText(*args, **kwargs)

    def SetHelpTextForId(*args, **kwargs):
        return _core_.Window_SetHelpTextForId(*args, **kwargs)

    def GetHelpTextAtPoint(*args, **kwargs):
        return _core_.Window_GetHelpTextAtPoint(*args, **kwargs)

    def GetHelpText(*args, **kwargs):
        return _core_.Window_GetHelpText(*args, **kwargs)

    def SetToolTipString(*args, **kwargs):
        return _core_.Window_SetToolTipString(*args, **kwargs)

    def SetToolTip(*args, **kwargs):
        return _core_.Window_SetToolTip(*args, **kwargs)

    def GetToolTip(*args, **kwargs):
        return _core_.Window_GetToolTip(*args, **kwargs)

    def SetDropTarget(*args, **kwargs):
        return _core_.Window_SetDropTarget(*args, **kwargs)

    def GetDropTarget(*args, **kwargs):
        return _core_.Window_GetDropTarget(*args, **kwargs)

    def DragAcceptFiles(*args, **kwargs):
        return _core_.Window_DragAcceptFiles(*args, **kwargs)

    def SetConstraints(*args, **kwargs):
        return _core_.Window_SetConstraints(*args, **kwargs)

    def GetConstraints(*args, **kwargs):
        return _core_.Window_GetConstraints(*args, **kwargs)

    def SetAutoLayout(*args, **kwargs):
        return _core_.Window_SetAutoLayout(*args, **kwargs)

    def GetAutoLayout(*args, **kwargs):
        return _core_.Window_GetAutoLayout(*args, **kwargs)

    def Layout(*args, **kwargs):
        return _core_.Window_Layout(*args, **kwargs)

    def SetSizer(*args, **kwargs):
        return _core_.Window_SetSizer(*args, **kwargs)

    def SetSizerAndFit(*args, **kwargs):
        return _core_.Window_SetSizerAndFit(*args, **kwargs)

    def GetSizer(*args, **kwargs):
        return _core_.Window_GetSizer(*args, **kwargs)

    def SetContainingSizer(*args, **kwargs):
        return _core_.Window_SetContainingSizer(*args, **kwargs)

    def GetContainingSizer(*args, **kwargs):
        return _core_.Window_GetContainingSizer(*args, **kwargs)

    def InheritAttributes(*args, **kwargs):
        return _core_.Window_InheritAttributes(*args, **kwargs)

    def ShouldInheritColours(*args, **kwargs):
        return _core_.Window_ShouldInheritColours(*args, **kwargs)

    def CanSetTransparent(*args, **kwargs):
        return _core_.Window_CanSetTransparent(*args, **kwargs)

    def SetTransparent(*args, **kwargs):
        return _core_.Window_SetTransparent(*args, **kwargs)

    def PostCreate(self, pre):
        self.this = pre.this
        self.thisown = pre.thisown
        pre.thisown = 0
        if hasattr(self, '_setOORInfo'):
            try:
                self._setOORInfo(self)
            except TypeError:
                pass

        if hasattr(self, '_setCallbackInfo'):
            try:
                self._setCallbackInfo(self, pre.__class__)
            except TypeError:
                pass

    def SendSizeEvent(self):
        self.GetEventHandler().ProcessEvent(wx.SizeEvent((-1, -1)))

    AcceleratorTable = property(GetAcceleratorTable, SetAcceleratorTable, doc='See `GetAcceleratorTable` and `SetAcceleratorTable`')
    AutoLayout = property(GetAutoLayout, SetAutoLayout, doc='See `GetAutoLayout` and `SetAutoLayout`')
    BackgroundColour = property(GetBackgroundColour, SetBackgroundColour, doc='See `GetBackgroundColour` and `SetBackgroundColour`')
    BackgroundStyle = property(GetBackgroundStyle, SetBackgroundStyle, doc='See `GetBackgroundStyle` and `SetBackgroundStyle`')
    EffectiveMinSize = property(GetEffectiveMinSize, doc='See `GetEffectiveMinSize`')
    BestSize = property(GetBestSize, doc='See `GetBestSize`')
    BestVirtualSize = property(GetBestVirtualSize, doc='See `GetBestVirtualSize`')
    Border = property(GetBorder, doc='See `GetBorder`')
    Caret = property(GetCaret, SetCaret, doc='See `GetCaret` and `SetCaret`')
    CharHeight = property(GetCharHeight, doc='See `GetCharHeight`')
    CharWidth = property(GetCharWidth, doc='See `GetCharWidth`')
    Children = property(GetChildren, doc='See `GetChildren`')
    ClientAreaOrigin = property(GetClientAreaOrigin, doc='See `GetClientAreaOrigin`')
    ClientRect = property(GetClientRect, SetClientRect, doc='See `GetClientRect` and `SetClientRect`')
    ClientSize = property(GetClientSize, SetClientSize, doc='See `GetClientSize` and `SetClientSize`')
    Constraints = property(GetConstraints, SetConstraints, doc='See `GetConstraints` and `SetConstraints`')
    ContainingSizer = property(GetContainingSizer, SetContainingSizer, doc='See `GetContainingSizer` and `SetContainingSizer`')
    Cursor = property(GetCursor, SetCursor, doc='See `GetCursor` and `SetCursor`')
    DefaultAttributes = property(GetDefaultAttributes, doc='See `GetDefaultAttributes`')
    DropTarget = property(GetDropTarget, SetDropTarget, doc='See `GetDropTarget` and `SetDropTarget`')
    EventHandler = property(GetEventHandler, SetEventHandler, doc='See `GetEventHandler` and `SetEventHandler`')
    ExtraStyle = property(GetExtraStyle, SetExtraStyle, doc='See `GetExtraStyle` and `SetExtraStyle`')
    Font = property(GetFont, SetFont, doc='See `GetFont` and `SetFont`')
    ForegroundColour = property(GetForegroundColour, SetForegroundColour, doc='See `GetForegroundColour` and `SetForegroundColour`')
    GrandParent = property(GetGrandParent, doc='See `GetGrandParent`')
    TopLevelParent = property(GetTopLevelParent, doc='See `GetTopLevelParent`')
    Handle = property(GetHandle, doc='See `GetHandle`')
    HelpText = property(GetHelpText, SetHelpText, doc='See `GetHelpText` and `SetHelpText`')
    Id = property(GetId, SetId, doc='See `GetId` and `SetId`')
    Label = property(GetLabel, SetLabel, doc='See `GetLabel` and `SetLabel`')
    LayoutDirection = property(GetLayoutDirection, SetLayoutDirection, doc='See `GetLayoutDirection` and `SetLayoutDirection`')
    MaxHeight = property(GetMaxHeight, doc='See `GetMaxHeight`')
    MaxSize = property(GetMaxSize, SetMaxSize, doc='See `GetMaxSize` and `SetMaxSize`')
    MaxWidth = property(GetMaxWidth, doc='See `GetMaxWidth`')
    MinHeight = property(GetMinHeight, doc='See `GetMinHeight`')
    MinSize = property(GetMinSize, SetMinSize, doc='See `GetMinSize` and `SetMinSize`')
    MinWidth = property(GetMinWidth, doc='See `GetMinWidth`')
    Name = property(GetName, SetName, doc='See `GetName` and `SetName`')
    Parent = property(GetParent, doc='See `GetParent`')
    Position = property(GetPosition, SetPosition, doc='See `GetPosition` and `SetPosition`')
    Rect = property(GetRect, SetRect, doc='See `GetRect` and `SetRect`')
    ScreenPosition = property(GetScreenPosition, doc='See `GetScreenPosition`')
    ScreenRect = property(GetScreenRect, doc='See `GetScreenRect`')
    Size = property(GetSize, SetSize, doc='See `GetSize` and `SetSize`')
    Sizer = property(GetSizer, SetSizer, doc='See `GetSizer` and `SetSizer`')
    ThemeEnabled = property(GetThemeEnabled, SetThemeEnabled, doc='See `GetThemeEnabled` and `SetThemeEnabled`')
    ToolTip = property(GetToolTip, SetToolTip, doc='See `GetToolTip` and `SetToolTip`')
    UpdateClientRect = property(GetUpdateClientRect, doc='See `GetUpdateClientRect`')
    UpdateRegion = property(GetUpdateRegion, doc='See `GetUpdateRegion`')
    VirtualSize = property(GetVirtualSize, SetVirtualSize, doc='See `GetVirtualSize` and `SetVirtualSize`')
    WindowStyle = property(GetWindowStyle, SetWindowStyle, doc='See `GetWindowStyle` and `SetWindowStyle`')
    WindowStyleFlag = property(GetWindowStyleFlag, SetWindowStyleFlag, doc='See `GetWindowStyleFlag` and `SetWindowStyleFlag`')
    WindowVariant = property(GetWindowVariant, SetWindowVariant, doc='See `GetWindowVariant` and `SetWindowVariant`')
    Shown = property(IsShown, Show, doc='See `IsShown` and `Show`')
    Enabled = property(IsEnabled, Enable, doc='See `IsEnabled` and `Enable`')
    TopLevel = property(IsTopLevel, doc='See `IsTopLevel`')
    GtkWidget = property(GetGtkWidget)


_core_.Window_swigregister(Window)

def PreWindow(*args, **kwargs):
    val = _core_.new_PreWindow(*args, **kwargs)
    return val


def Window_NewControlId(*args):
    return _core_.Window_NewControlId(*args)


def Window_NextControlId(*args, **kwargs):
    return _core_.Window_NextControlId(*args, **kwargs)


def Window_PrevControlId(*args, **kwargs):
    return _core_.Window_PrevControlId(*args, **kwargs)


def Window_FindFocus(*args):
    return _core_.Window_FindFocus(*args)


def Window_GetCapture(*args):
    return _core_.Window_GetCapture(*args)


def Window_GetClassDefaultAttributes(*args, **kwargs):
    return _core_.Window_GetClassDefaultAttributes(*args, **kwargs)


def DLG_PNT(win, point_or_x, y = None):
    if y is None:
        return win.ConvertDialogPointToPixels(point_or_x)
    else:
        return win.ConvertDialogPointToPixels(wx.Point(point_or_x, y))


def DLG_SZE(win, size_width, height = None):
    if height is None:
        return win.ConvertDialogSizeToPixels(size_width)
    else:
        return win.ConvertDialogSizeToPixels(wx.Size(size_width, height))


def FindWindowById(*args, **kwargs):
    return _core_.FindWindowById(*args, **kwargs)


def FindWindowByName(*args, **kwargs):
    return _core_.FindWindowByName(*args, **kwargs)


def FindWindowByLabel(*args, **kwargs):
    return _core_.FindWindowByLabel(*args, **kwargs)


def Window_FromHWND(*args, **kwargs):
    return _core_.Window_FromHWND(*args, **kwargs)


def GetTopLevelWindows(*args):
    return _core_.GetTopLevelWindows(*args)


class MenuItemList_iterator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_MenuItemList_iterator
    __del__ = lambda self: None

    def next(*args, **kwargs):
        return _core_.MenuItemList_iterator_next(*args, **kwargs)


_core_.MenuItemList_iterator_swigregister(MenuItemList_iterator)

class MenuItemList(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_MenuItemList
    __del__ = lambda self: None

    def __len__(*args, **kwargs):
        return _core_.MenuItemList___len__(*args, **kwargs)

    def __getitem__(*args, **kwargs):
        return _core_.MenuItemList___getitem__(*args, **kwargs)

    def __contains__(*args, **kwargs):
        return _core_.MenuItemList___contains__(*args, **kwargs)

    def __iter__(*args, **kwargs):
        return _core_.MenuItemList___iter__(*args, **kwargs)

    def index(*args, **kwargs):
        return _core_.MenuItemList_index(*args, **kwargs)

    def __repr__(self):
        return 'wxMenuItemList: ' + repr(list(self))


_core_.MenuItemList_swigregister(MenuItemList)

class Menu(EvtHandler):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Menu_swiginit(self, _core_.new_Menu(*args, **kwargs))
        self._setOORInfo(self)

    def Append(*args, **kwargs):
        return _core_.Menu_Append(*args, **kwargs)

    def AppendSeparator(*args, **kwargs):
        return _core_.Menu_AppendSeparator(*args, **kwargs)

    def AppendCheckItem(*args, **kwargs):
        return _core_.Menu_AppendCheckItem(*args, **kwargs)

    def AppendRadioItem(*args, **kwargs):
        return _core_.Menu_AppendRadioItem(*args, **kwargs)

    def AppendMenu(*args, **kwargs):
        return _core_.Menu_AppendMenu(*args, **kwargs)

    def AppendSubMenu(*args, **kwargs):
        return _core_.Menu_AppendSubMenu(*args, **kwargs)

    def AppendItem(*args, **kwargs):
        return _core_.Menu_AppendItem(*args, **kwargs)

    def InsertItem(*args, **kwargs):
        return _core_.Menu_InsertItem(*args, **kwargs)

    def PrependItem(*args, **kwargs):
        return _core_.Menu_PrependItem(*args, **kwargs)

    def Break(*args, **kwargs):
        return _core_.Menu_Break(*args, **kwargs)

    def Insert(*args, **kwargs):
        return _core_.Menu_Insert(*args, **kwargs)

    def InsertSeparator(*args, **kwargs):
        return _core_.Menu_InsertSeparator(*args, **kwargs)

    def InsertCheckItem(*args, **kwargs):
        return _core_.Menu_InsertCheckItem(*args, **kwargs)

    def InsertRadioItem(*args, **kwargs):
        return _core_.Menu_InsertRadioItem(*args, **kwargs)

    def InsertMenu(*args, **kwargs):
        return _core_.Menu_InsertMenu(*args, **kwargs)

    def Prepend(*args, **kwargs):
        return _core_.Menu_Prepend(*args, **kwargs)

    def PrependSeparator(*args, **kwargs):
        return _core_.Menu_PrependSeparator(*args, **kwargs)

    def PrependCheckItem(*args, **kwargs):
        return _core_.Menu_PrependCheckItem(*args, **kwargs)

    def PrependRadioItem(*args, **kwargs):
        return _core_.Menu_PrependRadioItem(*args, **kwargs)

    def PrependMenu(*args, **kwargs):
        return _core_.Menu_PrependMenu(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _core_.Menu_Remove(*args, **kwargs)

    def RemoveItem(self, item):
        val = _core_.Menu_RemoveItem(self, item)
        item.this.own(val.this.own())
        val.this.disown()
        return item

    def Delete(*args, **kwargs):
        return _core_.Menu_Delete(*args, **kwargs)

    def DeleteItem(*args, **kwargs):
        return _core_.Menu_DeleteItem(*args, **kwargs)

    def Destroy(*args, **kwargs):
        args[0].this.own(False)
        return _core_.Menu_Destroy(*args, **kwargs)

    def DestroyId(*args, **kwargs):
        return _core_.Menu_DestroyId(*args, **kwargs)

    def DestroyItem(*args, **kwargs):
        return _core_.Menu_DestroyItem(*args, **kwargs)

    def GetMenuItemCount(*args, **kwargs):
        return _core_.Menu_GetMenuItemCount(*args, **kwargs)

    def GetMenuItems(*args, **kwargs):
        return _core_.Menu_GetMenuItems(*args, **kwargs)

    def FindItem(*args, **kwargs):
        return _core_.Menu_FindItem(*args, **kwargs)

    def FindItemById(*args, **kwargs):
        return _core_.Menu_FindItemById(*args, **kwargs)

    def FindItemByPosition(*args, **kwargs):
        return _core_.Menu_FindItemByPosition(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _core_.Menu_Enable(*args, **kwargs)

    def IsEnabled(*args, **kwargs):
        return _core_.Menu_IsEnabled(*args, **kwargs)

    def Check(*args, **kwargs):
        return _core_.Menu_Check(*args, **kwargs)

    def IsChecked(*args, **kwargs):
        return _core_.Menu_IsChecked(*args, **kwargs)

    def SetLabel(*args, **kwargs):
        return _core_.Menu_SetLabel(*args, **kwargs)

    def GetLabel(*args, **kwargs):
        return _core_.Menu_GetLabel(*args, **kwargs)

    def SetHelpString(*args, **kwargs):
        return _core_.Menu_SetHelpString(*args, **kwargs)

    def GetHelpString(*args, **kwargs):
        return _core_.Menu_GetHelpString(*args, **kwargs)

    def SetTitle(*args, **kwargs):
        return _core_.Menu_SetTitle(*args, **kwargs)

    def GetTitle(*args, **kwargs):
        return _core_.Menu_GetTitle(*args, **kwargs)

    def SetEventHandler(*args, **kwargs):
        return _core_.Menu_SetEventHandler(*args, **kwargs)

    def GetEventHandler(*args, **kwargs):
        return _core_.Menu_GetEventHandler(*args, **kwargs)

    def SetInvokingWindow(*args, **kwargs):
        return _core_.Menu_SetInvokingWindow(*args, **kwargs)

    def GetInvokingWindow(*args, **kwargs):
        return _core_.Menu_GetInvokingWindow(*args, **kwargs)

    def GetStyle(*args, **kwargs):
        return _core_.Menu_GetStyle(*args, **kwargs)

    def UpdateUI(*args, **kwargs):
        return _core_.Menu_UpdateUI(*args, **kwargs)

    def GetMenuBar(*args, **kwargs):
        return _core_.Menu_GetMenuBar(*args, **kwargs)

    def Attach(*args, **kwargs):
        return _core_.Menu_Attach(*args, **kwargs)

    def Detach(*args, **kwargs):
        return _core_.Menu_Detach(*args, **kwargs)

    def IsAttached(*args, **kwargs):
        return _core_.Menu_IsAttached(*args, **kwargs)

    def SetParent(*args, **kwargs):
        return _core_.Menu_SetParent(*args, **kwargs)

    def GetParent(*args, **kwargs):
        return _core_.Menu_GetParent(*args, **kwargs)

    def GetLabelText(*args, **kwargs):
        return _core_.Menu_GetLabelText(*args, **kwargs)

    EventHandler = property(GetEventHandler, SetEventHandler, doc='See `GetEventHandler` and `SetEventHandler`')
    HelpString = property(GetHelpString, SetHelpString, doc='See `GetHelpString` and `SetHelpString`')
    InvokingWindow = property(GetInvokingWindow, SetInvokingWindow, doc='See `GetInvokingWindow` and `SetInvokingWindow`')
    MenuBar = property(GetMenuBar, doc='See `GetMenuBar`')
    MenuItemCount = property(GetMenuItemCount, doc='See `GetMenuItemCount`')
    MenuItems = property(GetMenuItems, doc='See `GetMenuItems`')
    Parent = property(GetParent, SetParent, doc='See `GetParent` and `SetParent`')
    Style = property(GetStyle, doc='See `GetStyle`')
    Title = property(GetTitle, SetTitle, doc='See `GetTitle` and `SetTitle`')

    def GetGtkWidget(*args, **kwargs):
        return _core_.Menu_GetGtkWidget(*args, **kwargs)


_core_.Menu_swigregister(Menu)

class MenuBar(Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MenuBar_swiginit(self, _core_.new_MenuBar(*args, **kwargs))
        self._setOORInfo(self)

    def Append(*args, **kwargs):
        return _core_.MenuBar_Append(*args, **kwargs)

    def Insert(*args, **kwargs):
        return _core_.MenuBar_Insert(*args, **kwargs)

    def GetMenuCount(*args, **kwargs):
        return _core_.MenuBar_GetMenuCount(*args, **kwargs)

    def GetMenu(*args, **kwargs):
        return _core_.MenuBar_GetMenu(*args, **kwargs)

    def Replace(*args, **kwargs):
        return _core_.MenuBar_Replace(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _core_.MenuBar_Remove(*args, **kwargs)

    def EnableTop(*args, **kwargs):
        return _core_.MenuBar_EnableTop(*args, **kwargs)

    def IsEnabledTop(*args, **kwargs):
        return _core_.MenuBar_IsEnabledTop(*args, **kwargs)

    def SetLabelTop(*args, **kwargs):
        return _core_.MenuBar_SetLabelTop(*args, **kwargs)

    def GetLabelTop(*args, **kwargs):
        return _core_.MenuBar_GetLabelTop(*args, **kwargs)

    def FindMenuItem(*args, **kwargs):
        return _core_.MenuBar_FindMenuItem(*args, **kwargs)

    def FindItemById(*args, **kwargs):
        return _core_.MenuBar_FindItemById(*args, **kwargs)

    def FindMenu(*args, **kwargs):
        return _core_.MenuBar_FindMenu(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _core_.MenuBar_Enable(*args, **kwargs)

    def Check(*args, **kwargs):
        return _core_.MenuBar_Check(*args, **kwargs)

    def IsChecked(*args, **kwargs):
        return _core_.MenuBar_IsChecked(*args, **kwargs)

    def IsEnabled(*args, **kwargs):
        return _core_.MenuBar_IsEnabled(*args, **kwargs)

    def SetLabel(*args, **kwargs):
        return _core_.MenuBar_SetLabel(*args, **kwargs)

    def GetLabel(*args, **kwargs):
        return _core_.MenuBar_GetLabel(*args, **kwargs)

    def SetHelpString(*args, **kwargs):
        return _core_.MenuBar_SetHelpString(*args, **kwargs)

    def GetHelpString(*args, **kwargs):
        return _core_.MenuBar_GetHelpString(*args, **kwargs)

    def GetFrame(*args, **kwargs):
        return _core_.MenuBar_GetFrame(*args, **kwargs)

    def IsAttached(*args, **kwargs):
        return _core_.MenuBar_IsAttached(*args, **kwargs)

    def Attach(*args, **kwargs):
        return _core_.MenuBar_Attach(*args, **kwargs)

    def Detach(*args, **kwargs):
        return _core_.MenuBar_Detach(*args, **kwargs)

    def UpdateMenus(*args, **kwargs):
        return _core_.MenuBar_UpdateMenus(*args, **kwargs)

    def SetAutoWindowMenu(*args, **kwargs):
        return _core_.MenuBar_SetAutoWindowMenu(*args, **kwargs)

    SetAutoWindowMenu = staticmethod(SetAutoWindowMenu)

    def GetAutoWindowMenu(*args, **kwargs):
        return _core_.MenuBar_GetAutoWindowMenu(*args, **kwargs)

    GetAutoWindowMenu = staticmethod(GetAutoWindowMenu)

    def MacSetCommonMenuBar(*args, **kwargs):
        return _core_.MenuBar_MacSetCommonMenuBar(*args, **kwargs)

    MacSetCommonMenuBar = staticmethod(MacSetCommonMenuBar)

    def GetMenuLabel(*args, **kwargs):
        return _core_.MenuBar_GetMenuLabel(*args, **kwargs)

    def SetMenuLabel(*args, **kwargs):
        return _core_.MenuBar_SetMenuLabel(*args, **kwargs)

    def GetMenuLabelText(*args, **kwargs):
        return _core_.MenuBar_GetMenuLabelText(*args, **kwargs)

    def GetMenus(self):
        return [ (self.GetMenu(i), self.GetLabelTop(i)) for i in range(self.GetMenuCount()) ]

    def SetMenus(self, items):
        for i in range(self.GetMenuCount() - 1, -1, -1):
            self.Remove(i)

        for m, l in items:
            self.Append(m, l)

    Frame = property(GetFrame, doc='See `GetFrame`')
    MenuCount = property(GetMenuCount, doc='See `GetMenuCount`')
    Menus = property(GetMenus, SetMenus, doc='See `GetMenus` and `SetMenus`')


_core_.MenuBar_swigregister(MenuBar)

def MenuBar_SetAutoWindowMenu(*args, **kwargs):
    return _core_.MenuBar_SetAutoWindowMenu(*args, **kwargs)


def MenuBar_GetAutoWindowMenu(*args):
    return _core_.MenuBar_GetAutoWindowMenu(*args)


def MenuBar_MacSetCommonMenuBar(*args, **kwargs):
    return _core_.MenuBar_MacSetCommonMenuBar(*args, **kwargs)


class MenuItem(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.MenuItem_swiginit(self, _core_.new_MenuItem(*args, **kwargs))

    __swig_destroy__ = _core_.delete_MenuItem
    __del__ = lambda self: None

    def Destroy(self):
        pass

    def GetMenu(*args, **kwargs):
        return _core_.MenuItem_GetMenu(*args, **kwargs)

    def SetMenu(*args, **kwargs):
        return _core_.MenuItem_SetMenu(*args, **kwargs)

    def SetId(*args, **kwargs):
        return _core_.MenuItem_SetId(*args, **kwargs)

    def GetId(*args, **kwargs):
        return _core_.MenuItem_GetId(*args, **kwargs)

    def IsSeparator(*args, **kwargs):
        return _core_.MenuItem_IsSeparator(*args, **kwargs)

    def SetText(*args, **kwargs):
        return _core_.MenuItem_SetText(*args, **kwargs)

    def GetLabel(*args, **kwargs):
        return _core_.MenuItem_GetLabel(*args, **kwargs)

    def GetText(*args, **kwargs):
        return _core_.MenuItem_GetText(*args, **kwargs)

    def GetLabelFromText(*args, **kwargs):
        return _core_.MenuItem_GetLabelFromText(*args, **kwargs)

    GetLabelFromText = staticmethod(GetLabelFromText)

    def GetKind(*args, **kwargs):
        return _core_.MenuItem_GetKind(*args, **kwargs)

    def SetKind(*args, **kwargs):
        return _core_.MenuItem_SetKind(*args, **kwargs)

    def SetCheckable(*args, **kwargs):
        return _core_.MenuItem_SetCheckable(*args, **kwargs)

    def IsCheckable(*args, **kwargs):
        return _core_.MenuItem_IsCheckable(*args, **kwargs)

    def IsSubMenu(*args, **kwargs):
        return _core_.MenuItem_IsSubMenu(*args, **kwargs)

    def SetSubMenu(*args, **kwargs):
        return _core_.MenuItem_SetSubMenu(*args, **kwargs)

    def GetSubMenu(*args, **kwargs):
        return _core_.MenuItem_GetSubMenu(*args, **kwargs)

    def Enable(*args, **kwargs):
        return _core_.MenuItem_Enable(*args, **kwargs)

    def IsEnabled(*args, **kwargs):
        return _core_.MenuItem_IsEnabled(*args, **kwargs)

    def Check(*args, **kwargs):
        return _core_.MenuItem_Check(*args, **kwargs)

    def IsChecked(*args, **kwargs):
        return _core_.MenuItem_IsChecked(*args, **kwargs)

    def Toggle(*args, **kwargs):
        return _core_.MenuItem_Toggle(*args, **kwargs)

    def SetHelp(*args, **kwargs):
        return _core_.MenuItem_SetHelp(*args, **kwargs)

    def GetHelp(*args, **kwargs):
        return _core_.MenuItem_GetHelp(*args, **kwargs)

    def GetAccel(*args, **kwargs):
        return _core_.MenuItem_GetAccel(*args, **kwargs)

    def SetAccel(*args, **kwargs):
        return _core_.MenuItem_SetAccel(*args, **kwargs)

    def SetBitmap(*args, **kwargs):
        return _core_.MenuItem_SetBitmap(*args, **kwargs)

    def GetBitmap(*args, **kwargs):
        return _core_.MenuItem_GetBitmap(*args, **kwargs)

    def SetFont(*args, **kwargs):
        return _core_.MenuItem_SetFont(*args, **kwargs)

    def GetFont(*args, **kwargs):
        return _core_.MenuItem_GetFont(*args, **kwargs)

    def SetTextColour(*args, **kwargs):
        return _core_.MenuItem_SetTextColour(*args, **kwargs)

    def GetTextColour(*args, **kwargs):
        return _core_.MenuItem_GetTextColour(*args, **kwargs)

    def SetBackgroundColour(*args, **kwargs):
        return _core_.MenuItem_SetBackgroundColour(*args, **kwargs)

    def GetBackgroundColour(*args, **kwargs):
        return _core_.MenuItem_GetBackgroundColour(*args, **kwargs)

    def SetBitmaps(*args, **kwargs):
        return _core_.MenuItem_SetBitmaps(*args, **kwargs)

    def SetDisabledBitmap(*args, **kwargs):
        return _core_.MenuItem_SetDisabledBitmap(*args, **kwargs)

    def GetDisabledBitmap(*args, **kwargs):
        return _core_.MenuItem_GetDisabledBitmap(*args, **kwargs)

    def SetMarginWidth(*args, **kwargs):
        return _core_.MenuItem_SetMarginWidth(*args, **kwargs)

    def GetMarginWidth(*args, **kwargs):
        return _core_.MenuItem_GetMarginWidth(*args, **kwargs)

    def GetDefaultMarginWidth(*args, **kwargs):
        return _core_.MenuItem_GetDefaultMarginWidth(*args, **kwargs)

    GetDefaultMarginWidth = staticmethod(GetDefaultMarginWidth)

    def IsOwnerDrawn(*args, **kwargs):
        return _core_.MenuItem_IsOwnerDrawn(*args, **kwargs)

    def SetOwnerDrawn(*args, **kwargs):
        return _core_.MenuItem_SetOwnerDrawn(*args, **kwargs)

    def ResetOwnerDrawn(*args, **kwargs):
        return _core_.MenuItem_ResetOwnerDrawn(*args, **kwargs)

    def GetItemLabel(*args, **kwargs):
        return _core_.MenuItem_GetItemLabel(*args, **kwargs)

    def SetItemLabel(*args, **kwargs):
        return _core_.MenuItem_SetItemLabel(*args, **kwargs)

    def GetItemLabelText(*args, **kwargs):
        return _core_.MenuItem_GetItemLabelText(*args, **kwargs)

    def GetLabelText(*args, **kwargs):
        return _core_.MenuItem_GetLabelText(*args, **kwargs)

    GetLabelText = staticmethod(GetLabelText)
    Accel = property(GetAccel, SetAccel, doc='See `GetAccel` and `SetAccel`')
    BackgroundColour = property(GetBackgroundColour, SetBackgroundColour, doc='See `GetBackgroundColour` and `SetBackgroundColour`')
    Bitmap = property(GetBitmap, SetBitmap, doc='See `GetBitmap` and `SetBitmap`')
    DisabledBitmap = property(GetDisabledBitmap, SetDisabledBitmap, doc='See `GetDisabledBitmap` and `SetDisabledBitmap`')
    Font = property(GetFont, SetFont, doc='See `GetFont` and `SetFont`')
    Help = property(GetHelp, SetHelp, doc='See `GetHelp` and `SetHelp`')
    Id = property(GetId, SetId, doc='See `GetId` and `SetId`')
    Kind = property(GetKind, SetKind, doc='See `GetKind` and `SetKind`')
    Label = property(GetLabel, doc='See `GetLabel`')
    MarginWidth = property(GetMarginWidth, SetMarginWidth, doc='See `GetMarginWidth` and `SetMarginWidth`')
    Menu = property(GetMenu, SetMenu, doc='See `GetMenu` and `SetMenu`')
    SubMenu = property(GetSubMenu, SetSubMenu, doc='See `GetSubMenu` and `SetSubMenu`')
    Text = property(GetText, SetText, doc='See `GetText` and `SetText`')
    TextColour = property(GetTextColour, SetTextColour, doc='See `GetTextColour` and `SetTextColour`')
    ItemLabel = property(GetItemLabel)


_core_.MenuItem_swigregister(MenuItem)

def MenuItem_GetLabelFromText(*args, **kwargs):
    return _core_.MenuItem_GetLabelFromText(*args, **kwargs)


def MenuItem_GetDefaultMarginWidth(*args):
    return _core_.MenuItem_GetDefaultMarginWidth(*args)


def MenuItem_GetLabelText(*args, **kwargs):
    return _core_.MenuItem_GetLabelText(*args, **kwargs)


class Control(Window):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.Control_swiginit(self, _core_.new_Control(*args, **kwargs))
        self._setOORInfo(self)

    def Create(*args, **kwargs):
        return _core_.Control_Create(*args, **kwargs)

    def GetAlignment(*args, **kwargs):
        return _core_.Control_GetAlignment(*args, **kwargs)

    def GetLabelText(*args, **kwargs):
        return _core_.Control_GetLabelText(*args, **kwargs)

    def Command(*args, **kwargs):
        return _core_.Control_Command(*args, **kwargs)

    def GetClassDefaultAttributes(*args, **kwargs):
        return _core_.Control_GetClassDefaultAttributes(*args, **kwargs)

    GetClassDefaultAttributes = staticmethod(GetClassDefaultAttributes)
    Alignment = property(GetAlignment, doc='See `GetAlignment`')
    LabelText = property(GetLabelText, doc='See `GetLabelText`')


_core_.Control_swigregister(Control)
ControlNameStr = cvar.ControlNameStr

def PreControl(*args, **kwargs):
    val = _core_.new_PreControl(*args, **kwargs)
    return val


def Control_GetClassDefaultAttributes(*args, **kwargs):
    return _core_.Control_GetClassDefaultAttributes(*args, **kwargs)


class ItemContainer(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def Append(*args, **kwargs):
        return _core_.ItemContainer_Append(*args, **kwargs)

    def AppendItems(*args, **kwargs):
        return _core_.ItemContainer_AppendItems(*args, **kwargs)

    def Insert(*args, **kwargs):
        return _core_.ItemContainer_Insert(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _core_.ItemContainer_Clear(*args, **kwargs)

    def Delete(*args, **kwargs):
        return _core_.ItemContainer_Delete(*args, **kwargs)

    def GetClientData(*args, **kwargs):
        return _core_.ItemContainer_GetClientData(*args, **kwargs)

    def SetClientData(*args, **kwargs):
        return _core_.ItemContainer_SetClientData(*args, **kwargs)

    def GetCount(*args, **kwargs):
        return _core_.ItemContainer_GetCount(*args, **kwargs)

    def IsEmpty(*args, **kwargs):
        return _core_.ItemContainer_IsEmpty(*args, **kwargs)

    def GetString(*args, **kwargs):
        return _core_.ItemContainer_GetString(*args, **kwargs)

    def GetStrings(*args, **kwargs):
        return _core_.ItemContainer_GetStrings(*args, **kwargs)

    def SetString(*args, **kwargs):
        return _core_.ItemContainer_SetString(*args, **kwargs)

    def FindString(*args, **kwargs):
        return _core_.ItemContainer_FindString(*args, **kwargs)

    def SetSelection(*args, **kwargs):
        return _core_.ItemContainer_SetSelection(*args, **kwargs)

    def GetSelection(*args, **kwargs):
        return _core_.ItemContainer_GetSelection(*args, **kwargs)

    def SetStringSelection(*args, **kwargs):
        return _core_.ItemContainer_SetStringSelection(*args, **kwargs)

    def GetStringSelection(*args, **kwargs):
        return _core_.ItemContainer_GetStringSelection(*args, **kwargs)

    def Select(*args, **kwargs):
        return _core_.ItemContainer_Select(*args, **kwargs)

    def GetItems(self):
        return [ self.GetString(i) for i in xrange(self.GetCount()) ]

    def SetItems(self, items):
        self.Clear()
        self.AppendItems(items)

    Count = property(GetCount, doc='See `GetCount`')
    Items = property(GetItems, SetItems, doc='See `GetItems` and `SetItems`')
    Selection = property(GetSelection, SetSelection, doc='See `GetSelection` and `SetSelection`')
    StringSelection = property(GetStringSelection, SetStringSelection, doc='See `GetStringSelection` and `SetStringSelection`')
    Strings = property(GetStrings, doc='See `GetStrings`')


_core_.ItemContainer_swigregister(ItemContainer)

class ControlWithItems(Control, ItemContainer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr


_core_.ControlWithItems_swigregister(ControlWithItems)

class SizerFlags(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.SizerFlags_swiginit(self, _core_.new_SizerFlags(*args, **kwargs))

    __swig_destroy__ = _core_.delete_SizerFlags
    __del__ = lambda self: None

    def Proportion(*args, **kwargs):
        return _core_.SizerFlags_Proportion(*args, **kwargs)

    def Align(*args, **kwargs):
        return _core_.SizerFlags_Align(*args, **kwargs)

    def Expand(*args, **kwargs):
        return _core_.SizerFlags_Expand(*args, **kwargs)

    def Centre(*args, **kwargs):
        return _core_.SizerFlags_Centre(*args, **kwargs)

    def Center(*args, **kwargs):
        return _core_.SizerFlags_Center(*args, **kwargs)

    def Left(*args, **kwargs):
        return _core_.SizerFlags_Left(*args, **kwargs)

    def Right(*args, **kwargs):
        return _core_.SizerFlags_Right(*args, **kwargs)

    def Top(*args, **kwargs):
        return _core_.SizerFlags_Top(*args, **kwargs)

    def Bottom(*args, **kwargs):
        return _core_.SizerFlags_Bottom(*args, **kwargs)

    def Shaped(*args, **kwargs):
        return _core_.SizerFlags_Shaped(*args, **kwargs)

    def FixedMinSize(*args, **kwargs):
        return _core_.SizerFlags_FixedMinSize(*args, **kwargs)

    def ReserveSpaceEvenIfHidden(*args, **kwargs):
        return _core_.SizerFlags_ReserveSpaceEvenIfHidden(*args, **kwargs)

    def Border(*args, **kwargs):
        return _core_.SizerFlags_Border(*args, **kwargs)

    def DoubleBorder(*args, **kwargs):
        return _core_.SizerFlags_DoubleBorder(*args, **kwargs)

    def TripleBorder(*args, **kwargs):
        return _core_.SizerFlags_TripleBorder(*args, **kwargs)

    def HorzBorder(*args, **kwargs):
        return _core_.SizerFlags_HorzBorder(*args, **kwargs)

    def DoubleHorzBorder(*args, **kwargs):
        return _core_.SizerFlags_DoubleHorzBorder(*args, **kwargs)

    def GetDefaultBorder(*args, **kwargs):
        return _core_.SizerFlags_GetDefaultBorder(*args, **kwargs)

    GetDefaultBorder = staticmethod(GetDefaultBorder)

    def GetProportion(*args, **kwargs):
        return _core_.SizerFlags_GetProportion(*args, **kwargs)

    def GetFlags(*args, **kwargs):
        return _core_.SizerFlags_GetFlags(*args, **kwargs)

    def GetBorderInPixels(*args, **kwargs):
        return _core_.SizerFlags_GetBorderInPixels(*args, **kwargs)


_core_.SizerFlags_swigregister(SizerFlags)

def SizerFlags_GetDefaultBorder(*args):
    return _core_.SizerFlags_GetDefaultBorder(*args)


class SizerItemList_iterator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_SizerItemList_iterator
    __del__ = lambda self: None

    def next(*args, **kwargs):
        return _core_.SizerItemList_iterator_next(*args, **kwargs)


_core_.SizerItemList_iterator_swigregister(SizerItemList_iterator)

class SizerItemList(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_SizerItemList
    __del__ = lambda self: None

    def __len__(*args, **kwargs):
        return _core_.SizerItemList___len__(*args, **kwargs)

    def __getitem__(*args, **kwargs):
        return _core_.SizerItemList___getitem__(*args, **kwargs)

    def __contains__(*args, **kwargs):
        return _core_.SizerItemList___contains__(*args, **kwargs)

    def __iter__(*args, **kwargs):
        return _core_.SizerItemList___iter__(*args, **kwargs)

    def index(*args, **kwargs):
        return _core_.SizerItemList_index(*args, **kwargs)

    def __repr__(self):
        return 'wxSizerItemList: ' + repr(list(self))


_core_.SizerItemList_swigregister(SizerItemList)

class SizerItem(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.SizerItem_swiginit(self, _core_.new_SizerItem(*args, **kwargs))

    __swig_destroy__ = _core_.delete_SizerItem
    __del__ = lambda self: None

    def DeleteWindows(*args, **kwargs):
        return _core_.SizerItem_DeleteWindows(*args, **kwargs)

    def DetachSizer(*args, **kwargs):
        return _core_.SizerItem_DetachSizer(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _core_.SizerItem_GetSize(*args, **kwargs)

    def CalcMin(*args, **kwargs):
        return _core_.SizerItem_CalcMin(*args, **kwargs)

    def SetDimension(*args, **kwargs):
        return _core_.SizerItem_SetDimension(*args, **kwargs)

    def GetMinSize(*args, **kwargs):
        return _core_.SizerItem_GetMinSize(*args, **kwargs)

    def GetMinSizeWithBorder(*args, **kwargs):
        return _core_.SizerItem_GetMinSizeWithBorder(*args, **kwargs)

    def SetInitSize(*args, **kwargs):
        return _core_.SizerItem_SetInitSize(*args, **kwargs)

    def SetRatioWH(*args, **kwargs):
        return _core_.SizerItem_SetRatioWH(*args, **kwargs)

    def SetRatioSize(*args, **kwargs):
        return _core_.SizerItem_SetRatioSize(*args, **kwargs)

    def SetRatio(*args, **kwargs):
        return _core_.SizerItem_SetRatio(*args, **kwargs)

    def GetRatio(*args, **kwargs):
        return _core_.SizerItem_GetRatio(*args, **kwargs)

    def GetRect(*args, **kwargs):
        return _core_.SizerItem_GetRect(*args, **kwargs)

    def IsWindow(*args, **kwargs):
        return _core_.SizerItem_IsWindow(*args, **kwargs)

    def IsSizer(*args, **kwargs):
        return _core_.SizerItem_IsSizer(*args, **kwargs)

    def IsSpacer(*args, **kwargs):
        return _core_.SizerItem_IsSpacer(*args, **kwargs)

    def SetProportion(*args, **kwargs):
        return _core_.SizerItem_SetProportion(*args, **kwargs)

    def GetProportion(*args, **kwargs):
        return _core_.SizerItem_GetProportion(*args, **kwargs)

    SetOption = wx._deprecated(SetProportion, 'Please use `SetProportion` instead.')
    GetOption = wx._deprecated(GetProportion, 'Please use `GetProportion` instead.')

    def SetFlag(*args, **kwargs):
        return _core_.SizerItem_SetFlag(*args, **kwargs)

    def GetFlag(*args, **kwargs):
        return _core_.SizerItem_GetFlag(*args, **kwargs)

    def SetBorder(*args, **kwargs):
        return _core_.SizerItem_SetBorder(*args, **kwargs)

    def GetBorder(*args, **kwargs):
        return _core_.SizerItem_GetBorder(*args, **kwargs)

    def GetWindow(*args, **kwargs):
        return _core_.SizerItem_GetWindow(*args, **kwargs)

    def SetWindow(*args, **kwargs):
        return _core_.SizerItem_SetWindow(*args, **kwargs)

    def GetSizer(*args, **kwargs):
        return _core_.SizerItem_GetSizer(*args, **kwargs)

    def SetSizer(*args, **kwargs):
        return _core_.SizerItem_SetSizer(*args, **kwargs)

    def GetSpacer(*args, **kwargs):
        return _core_.SizerItem_GetSpacer(*args, **kwargs)

    def SetSpacer(*args, **kwargs):
        return _core_.SizerItem_SetSpacer(*args, **kwargs)

    def Show(*args, **kwargs):
        return _core_.SizerItem_Show(*args, **kwargs)

    def IsShown(*args, **kwargs):
        return _core_.SizerItem_IsShown(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.SizerItem_GetPosition(*args, **kwargs)

    def GetUserData(*args, **kwargs):
        return _core_.SizerItem_GetUserData(*args, **kwargs)

    def SetUserData(*args, **kwargs):
        return _core_.SizerItem_SetUserData(*args, **kwargs)

    Border = property(GetBorder, SetBorder, doc='See `GetBorder` and `SetBorder`')
    Flag = property(GetFlag, SetFlag, doc='See `GetFlag` and `SetFlag`')
    MinSize = property(GetMinSize, doc='See `GetMinSize`')
    MinSizeWithBorder = property(GetMinSizeWithBorder, doc='See `GetMinSizeWithBorder`')
    Position = property(GetPosition, doc='See `GetPosition`')
    Proportion = property(GetProportion, SetProportion, doc='See `GetProportion` and `SetProportion`')
    Ratio = property(GetRatio, SetRatio, doc='See `GetRatio` and `SetRatio`')
    Rect = property(GetRect, doc='See `GetRect`')
    Size = property(GetSize, doc='See `GetSize`')
    Sizer = property(GetSizer, SetSizer, doc='See `GetSizer` and `SetSizer`')
    Spacer = property(GetSpacer, SetSpacer, doc='See `GetSpacer` and `SetSpacer`')
    UserData = property(GetUserData, SetUserData, doc='See `GetUserData` and `SetUserData`')
    Window = property(GetWindow, SetWindow, doc='See `GetWindow` and `SetWindow`')


_core_.SizerItem_swigregister(SizerItem)

def SizerItemWindow(*args, **kwargs):
    val = _core_.new_SizerItemWindow(*args, **kwargs)
    return val


def SizerItemSpacer(*args, **kwargs):
    val = _core_.new_SizerItemSpacer(*args, **kwargs)
    return val


def SizerItemSizer(*args, **kwargs):
    val = _core_.new_SizerItemSizer(*args, **kwargs)
    return val


class Sizer(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_Sizer
    __del__ = lambda self: None

    def _setOORInfo(*args, **kwargs):
        return _core_.Sizer__setOORInfo(*args, **kwargs)

    def Add(*args, **kwargs):
        return _core_.Sizer_Add(*args, **kwargs)

    def AddF(*args, **kwargs):
        return _core_.Sizer_AddF(*args, **kwargs)

    def Insert(*args, **kwargs):
        return _core_.Sizer_Insert(*args, **kwargs)

    def InsertF(*args, **kwargs):
        return _core_.Sizer_InsertF(*args, **kwargs)

    def Prepend(*args, **kwargs):
        return _core_.Sizer_Prepend(*args, **kwargs)

    def PrependF(*args, **kwargs):
        return _core_.Sizer_PrependF(*args, **kwargs)

    def Remove(*args, **kwargs):
        return _core_.Sizer_Remove(*args, **kwargs)

    def Detach(*args, **kwargs):
        return _core_.Sizer_Detach(*args, **kwargs)

    def GetItem(*args, **kwargs):
        return _core_.Sizer_GetItem(*args, **kwargs)

    def _SetItemMinSize(*args, **kwargs):
        return _core_.Sizer__SetItemMinSize(*args, **kwargs)

    def _ReplaceWin(*args, **kwargs):
        return _core_.Sizer__ReplaceWin(*args, **kwargs)

    def _ReplaceSizer(*args, **kwargs):
        return _core_.Sizer__ReplaceSizer(*args, **kwargs)

    def _ReplaceItem(*args, **kwargs):
        return _core_.Sizer__ReplaceItem(*args, **kwargs)

    def Replace(self, olditem, item, recursive = False):
        if isinstance(olditem, wx.Window):
            return self._ReplaceWin(olditem, item, recursive)
        if isinstance(olditem, wx.Sizer):
            return self._ReplaceSizer(olditem, item, recursive)
        if isinstance(olditem, int):
            return self._ReplaceItem(olditem, item)
        raise TypeError('Expected Window, Sizer, or integer for first parameter.')

    def SetContainingWindow(*args, **kwargs):
        return _core_.Sizer_SetContainingWindow(*args, **kwargs)

    def GetContainingWindow(*args, **kwargs):
        return _core_.Sizer_GetContainingWindow(*args, **kwargs)

    def SetItemMinSize(self, item, *args):
        if len(args) == 2:
            return self._SetItemMinSize(item, args)
        else:
            return self._SetItemMinSize(item, args[0])

    def AddItem(*args, **kwargs):
        return _core_.Sizer_AddItem(*args, **kwargs)

    def InsertItem(*args, **kwargs):
        return _core_.Sizer_InsertItem(*args, **kwargs)

    def PrependItem(*args, **kwargs):
        return _core_.Sizer_PrependItem(*args, **kwargs)

    def AddMany(self, items):
        for item in items:
            if type(item) != type(()) or len(item) == 2 and type(item[0]) == type(1):
                item = (item,)
            self.Add(*item)

    def AddSpacer(self, *args, **kw):
        if args and type(args[0]) == int:
            return self.Add((args[0], args[0]), 0)
        else:
            return self.Add(*args, **kw)

    def PrependSpacer(self, *args, **kw):
        if args and type(args[0]) == int:
            return self.Prepend((args[0], args[0]), 0)
        else:
            return self.Prepend(*args, **kw)

    def InsertSpacer(self, index, *args, **kw):
        if args and type(args[0]) == int:
            return self.Insert(index, (args[0], args[0]), 0)
        else:
            return self.Insert(index, *args, **kw)

    def AddStretchSpacer(self, prop = 1):
        return self.Add((0, 0), prop)

    def PrependStretchSpacer(self, prop = 1):
        return self.Prepend((0, 0), prop)

    def InsertStretchSpacer(self, index, prop = 1):
        return self.Insert(index, (0, 0), prop)

    def AddWindow(self, *args, **kw):
        return self.Add(*args, **kw)

    def AddSizer(self, *args, **kw):
        return self.Add(*args, **kw)

    def PrependWindow(self, *args, **kw):
        return self.Prepend(*args, **kw)

    def PrependSizer(self, *args, **kw):
        return self.Prepend(*args, **kw)

    def InsertWindow(self, *args, **kw):
        return self.Insert(*args, **kw)

    def InsertSizer(self, *args, **kw):
        return self.Insert(*args, **kw)

    def RemoveWindow(self, *args, **kw):
        return self.Remove(*args, **kw)

    def RemoveSizer(self, *args, **kw):
        return self.Remove(*args, **kw)

    def RemovePos(self, *args, **kw):
        return self.Remove(*args, **kw)

    def SetDimension(*args, **kwargs):
        return _core_.Sizer_SetDimension(*args, **kwargs)

    def SetMinSize(*args, **kwargs):
        return _core_.Sizer_SetMinSize(*args, **kwargs)

    def GetSize(*args, **kwargs):
        return _core_.Sizer_GetSize(*args, **kwargs)

    def GetPosition(*args, **kwargs):
        return _core_.Sizer_GetPosition(*args, **kwargs)

    def GetMinSize(*args, **kwargs):
        return _core_.Sizer_GetMinSize(*args, **kwargs)

    def GetSizeTuple(self):
        return self.GetSize().Get()

    def GetPositionTuple(self):
        return self.GetPosition().Get()

    def GetMinSizeTuple(self):
        return self.GetMinSize().Get()

    def RecalcSizes(*args, **kwargs):
        return _core_.Sizer_RecalcSizes(*args, **kwargs)

    def CalcMin(*args, **kwargs):
        return _core_.Sizer_CalcMin(*args, **kwargs)

    def Layout(*args, **kwargs):
        return _core_.Sizer_Layout(*args, **kwargs)

    def ComputeFittingClientSize(*args, **kwargs):
        return _core_.Sizer_ComputeFittingClientSize(*args, **kwargs)

    def ComputeFittingWindowSize(*args, **kwargs):
        return _core_.Sizer_ComputeFittingWindowSize(*args, **kwargs)

    def Fit(*args, **kwargs):
        return _core_.Sizer_Fit(*args, **kwargs)

    def FitInside(*args, **kwargs):
        return _core_.Sizer_FitInside(*args, **kwargs)

    def SetSizeHints(*args, **kwargs):
        return _core_.Sizer_SetSizeHints(*args, **kwargs)

    def SetVirtualSizeHints(*args, **kwargs):
        return _core_.Sizer_SetVirtualSizeHints(*args, **kwargs)

    def Clear(*args, **kwargs):
        return _core_.Sizer_Clear(*args, **kwargs)

    def DeleteWindows(*args, **kwargs):
        return _core_.Sizer_DeleteWindows(*args, **kwargs)

    def GetChildren(*args, **kwargs):
        return _core_.Sizer_GetChildren(*args, **kwargs)

    def Show(*args, **kwargs):
        return _core_.Sizer_Show(*args, **kwargs)

    def IsShown(*args, **kwargs):
        return _core_.Sizer_IsShown(*args, **kwargs)

    def Hide(self, item, recursive = False):
        return self.Show(item, False, recursive)

    def ShowItems(*args, **kwargs):
        return _core_.Sizer_ShowItems(*args, **kwargs)

    Children = property(GetChildren, doc='See `GetChildren`')
    ContainingWindow = property(GetContainingWindow, SetContainingWindow, doc='See `GetContainingWindow` and `SetContainingWindow`')
    MinSize = property(GetMinSize, SetMinSize, doc='See `GetMinSize` and `SetMinSize`')
    Position = property(GetPosition, doc='See `GetPosition`')
    Size = property(GetSize, doc='See `GetSize`')


_core_.Sizer_swigregister(Sizer)

class PySizer(Sizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.PySizer_swiginit(self, _core_.new_PySizer(*args, **kwargs))
        self._setOORInfo(self)
        PySizer._setCallbackInfo(self, self, PySizer)

    def _setCallbackInfo(*args, **kwargs):
        return _core_.PySizer__setCallbackInfo(*args, **kwargs)


_core_.PySizer_swigregister(PySizer)

class BoxSizer(Sizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.BoxSizer_swiginit(self, _core_.new_BoxSizer(*args, **kwargs))
        self._setOORInfo(self)

    def GetOrientation(*args, **kwargs):
        return _core_.BoxSizer_GetOrientation(*args, **kwargs)

    def SetOrientation(*args, **kwargs):
        return _core_.BoxSizer_SetOrientation(*args, **kwargs)

    Orientation = property(GetOrientation, SetOrientation, doc='See `GetOrientation` and `SetOrientation`')


_core_.BoxSizer_swigregister(BoxSizer)

class StaticBoxSizer(BoxSizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.StaticBoxSizer_swiginit(self, _core_.new_StaticBoxSizer(*args, **kwargs))
        self._setOORInfo(self)

    def GetStaticBox(*args, **kwargs):
        return _core_.StaticBoxSizer_GetStaticBox(*args, **kwargs)

    StaticBox = property(GetStaticBox, doc='See `GetStaticBox`')


_core_.StaticBoxSizer_swigregister(StaticBoxSizer)

class GridSizer(Sizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.GridSizer_swiginit(self, _core_.new_GridSizer(*args, **kwargs))
        self._setOORInfo(self)

    def SetCols(*args, **kwargs):
        return _core_.GridSizer_SetCols(*args, **kwargs)

    def SetRows(*args, **kwargs):
        return _core_.GridSizer_SetRows(*args, **kwargs)

    def SetVGap(*args, **kwargs):
        return _core_.GridSizer_SetVGap(*args, **kwargs)

    def SetHGap(*args, **kwargs):
        return _core_.GridSizer_SetHGap(*args, **kwargs)

    def GetCols(*args, **kwargs):
        return _core_.GridSizer_GetCols(*args, **kwargs)

    def GetRows(*args, **kwargs):
        return _core_.GridSizer_GetRows(*args, **kwargs)

    def GetVGap(*args, **kwargs):
        return _core_.GridSizer_GetVGap(*args, **kwargs)

    def GetHGap(*args, **kwargs):
        return _core_.GridSizer_GetHGap(*args, **kwargs)

    def CalcRowsCols(self):
        nitems = len(self.GetChildren())
        rows = self.GetRows()
        cols = self.GetCols()
        assert rows != 0 or cols != 0, 'Grid sizer must have either rows or columns fixed'
        if cols != 0:
            rows = (nitems + cols - 1) / cols
        elif rows != 0:
            cols = (nitems + rows - 1) / rows
        return (rows, cols)

    Cols = property(GetCols, SetCols, doc='See `GetCols` and `SetCols`')
    HGap = property(GetHGap, SetHGap, doc='See `GetHGap` and `SetHGap`')
    Rows = property(GetRows, SetRows, doc='See `GetRows` and `SetRows`')
    VGap = property(GetVGap, SetVGap, doc='See `GetVGap` and `SetVGap`')


_core_.GridSizer_swigregister(GridSizer)
FLEX_GROWMODE_NONE = _core_.FLEX_GROWMODE_NONE
FLEX_GROWMODE_SPECIFIED = _core_.FLEX_GROWMODE_SPECIFIED
FLEX_GROWMODE_ALL = _core_.FLEX_GROWMODE_ALL

class FlexGridSizer(GridSizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.FlexGridSizer_swiginit(self, _core_.new_FlexGridSizer(*args, **kwargs))
        self._setOORInfo(self)

    def AddGrowableRow(*args, **kwargs):
        return _core_.FlexGridSizer_AddGrowableRow(*args, **kwargs)

    def RemoveGrowableRow(*args, **kwargs):
        return _core_.FlexGridSizer_RemoveGrowableRow(*args, **kwargs)

    def AddGrowableCol(*args, **kwargs):
        return _core_.FlexGridSizer_AddGrowableCol(*args, **kwargs)

    def RemoveGrowableCol(*args, **kwargs):
        return _core_.FlexGridSizer_RemoveGrowableCol(*args, **kwargs)

    def SetFlexibleDirection(*args, **kwargs):
        return _core_.FlexGridSizer_SetFlexibleDirection(*args, **kwargs)

    def GetFlexibleDirection(*args, **kwargs):
        return _core_.FlexGridSizer_GetFlexibleDirection(*args, **kwargs)

    def SetNonFlexibleGrowMode(*args, **kwargs):
        return _core_.FlexGridSizer_SetNonFlexibleGrowMode(*args, **kwargs)

    def GetNonFlexibleGrowMode(*args, **kwargs):
        return _core_.FlexGridSizer_GetNonFlexibleGrowMode(*args, **kwargs)

    def GetRowHeights(*args, **kwargs):
        return _core_.FlexGridSizer_GetRowHeights(*args, **kwargs)

    def GetColWidths(*args, **kwargs):
        return _core_.FlexGridSizer_GetColWidths(*args, **kwargs)

    ColWidths = property(GetColWidths, doc='See `GetColWidths`')
    FlexibleDirection = property(GetFlexibleDirection, SetFlexibleDirection, doc='See `GetFlexibleDirection` and `SetFlexibleDirection`')
    NonFlexibleGrowMode = property(GetNonFlexibleGrowMode, SetNonFlexibleGrowMode, doc='See `GetNonFlexibleGrowMode` and `SetNonFlexibleGrowMode`')
    RowHeights = property(GetRowHeights, doc='See `GetRowHeights`')


_core_.FlexGridSizer_swigregister(FlexGridSizer)

class StdDialogButtonSizer(BoxSizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.StdDialogButtonSizer_swiginit(self, _core_.new_StdDialogButtonSizer(*args, **kwargs))

    def AddButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_AddButton(*args, **kwargs)

    def Realize(*args, **kwargs):
        return _core_.StdDialogButtonSizer_Realize(*args, **kwargs)

    def SetAffirmativeButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_SetAffirmativeButton(*args, **kwargs)

    def SetNegativeButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_SetNegativeButton(*args, **kwargs)

    def SetCancelButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_SetCancelButton(*args, **kwargs)

    def GetAffirmativeButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_GetAffirmativeButton(*args, **kwargs)

    def GetApplyButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_GetApplyButton(*args, **kwargs)

    def GetNegativeButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_GetNegativeButton(*args, **kwargs)

    def GetCancelButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_GetCancelButton(*args, **kwargs)

    def GetHelpButton(*args, **kwargs):
        return _core_.StdDialogButtonSizer_GetHelpButton(*args, **kwargs)

    AffirmativeButton = property(GetAffirmativeButton, SetAffirmativeButton, doc='See `GetAffirmativeButton` and `SetAffirmativeButton`')
    ApplyButton = property(GetApplyButton, doc='See `GetApplyButton`')
    CancelButton = property(GetCancelButton, SetCancelButton, doc='See `GetCancelButton` and `SetCancelButton`')
    HelpButton = property(GetHelpButton, doc='See `GetHelpButton`')
    NegativeButton = property(GetNegativeButton, SetNegativeButton, doc='See `GetNegativeButton` and `SetNegativeButton`')


_core_.StdDialogButtonSizer_swigregister(StdDialogButtonSizer)

class GBPosition(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.GBPosition_swiginit(self, _core_.new_GBPosition(*args, **kwargs))

    __swig_destroy__ = _core_.delete_GBPosition
    __del__ = lambda self: None

    def GetRow(*args, **kwargs):
        return _core_.GBPosition_GetRow(*args, **kwargs)

    def GetCol(*args, **kwargs):
        return _core_.GBPosition_GetCol(*args, **kwargs)

    def SetRow(*args, **kwargs):
        return _core_.GBPosition_SetRow(*args, **kwargs)

    def SetCol(*args, **kwargs):
        return _core_.GBPosition_SetCol(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _core_.GBPosition___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.GBPosition___ne__(*args, **kwargs)

    def Set(*args, **kwargs):
        return _core_.GBPosition_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.GBPosition_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.GBPosition' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.SetRow(val)
        elif index == 1:
            self.SetCol(val)
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0, 0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.GBPosition, self.Get())

    row = property(GetRow, SetRow)
    col = property(GetCol, SetCol)


_core_.GBPosition_swigregister(GBPosition)

class GBSpan(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.GBSpan_swiginit(self, _core_.new_GBSpan(*args, **kwargs))

    __swig_destroy__ = _core_.delete_GBSpan
    __del__ = lambda self: None

    def GetRowspan(*args, **kwargs):
        return _core_.GBSpan_GetRowspan(*args, **kwargs)

    def GetColspan(*args, **kwargs):
        return _core_.GBSpan_GetColspan(*args, **kwargs)

    def SetRowspan(*args, **kwargs):
        return _core_.GBSpan_SetRowspan(*args, **kwargs)

    def SetColspan(*args, **kwargs):
        return _core_.GBSpan_SetColspan(*args, **kwargs)

    def __eq__(*args, **kwargs):
        return _core_.GBSpan___eq__(*args, **kwargs)

    def __ne__(*args, **kwargs):
        return _core_.GBSpan___ne__(*args, **kwargs)

    def Set(*args, **kwargs):
        return _core_.GBSpan_Set(*args, **kwargs)

    def Get(*args, **kwargs):
        return _core_.GBSpan_Get(*args, **kwargs)

    asTuple = wx._deprecated(Get, 'asTuple is deprecated, use `Get` instead')

    def __str__(self):
        return str(self.Get())

    def __repr__(self):
        return 'wx.GBSpan' + str(self.Get())

    def __len__(self):
        return len(self.Get())

    def __getitem__(self, index):
        return self.Get()[index]

    def __setitem__(self, index, val):
        if index == 0:
            self.SetRowspan(val)
        elif index == 1:
            self.SetColspan(val)
        else:
            raise IndexError

    def __nonzero__(self):
        return self.Get() != (0, 0)

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return (wx.GBSpan, self.Get())

    rowspan = property(GetRowspan, SetRowspan)
    colspan = property(GetColspan, SetColspan)


_core_.GBSpan_swigregister(GBSpan)

class GBSizerItem(SizerItem):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.GBSizerItem_swiginit(self, _core_.new_GBSizerItem(*args, **kwargs))

    __swig_destroy__ = _core_.delete_GBSizerItem
    __del__ = lambda self: None

    def GetPos(*args, **kwargs):
        return _core_.GBSizerItem_GetPos(*args, **kwargs)

    def GetPosTuple(self):
        return self.GetPos().Get()

    def GetSpan(*args, **kwargs):
        return _core_.GBSizerItem_GetSpan(*args, **kwargs)

    def GetSpanTuple(self):
        return self.GetSpan().Get()

    def SetPos(*args, **kwargs):
        return _core_.GBSizerItem_SetPos(*args, **kwargs)

    def SetSpan(*args, **kwargs):
        return _core_.GBSizerItem_SetSpan(*args, **kwargs)

    def Intersects(*args, **kwargs):
        return _core_.GBSizerItem_Intersects(*args, **kwargs)

    def IntersectsPos(*args, **kwargs):
        return _core_.GBSizerItem_IntersectsPos(*args, **kwargs)

    def GetEndPos(*args, **kwargs):
        return _core_.GBSizerItem_GetEndPos(*args, **kwargs)

    def GetGBSizer(*args, **kwargs):
        return _core_.GBSizerItem_GetGBSizer(*args, **kwargs)

    def SetGBSizer(*args, **kwargs):
        return _core_.GBSizerItem_SetGBSizer(*args, **kwargs)

    EndPos = property(GetEndPos, doc='See `GetEndPos`')
    GBSizer = property(GetGBSizer, SetGBSizer, doc='See `GetGBSizer` and `SetGBSizer`')
    Pos = property(GetPos, SetPos, doc='See `GetPos` and `SetPos`')
    Span = property(GetSpan, SetSpan, doc='See `GetSpan` and `SetSpan`')


_core_.GBSizerItem_swigregister(GBSizerItem)
DefaultSpan = cvar.DefaultSpan

def GBSizerItemWindow(*args, **kwargs):
    val = _core_.new_GBSizerItemWindow(*args, **kwargs)
    return val


def GBSizerItemSizer(*args, **kwargs):
    val = _core_.new_GBSizerItemSizer(*args, **kwargs)
    return val


def GBSizerItemSpacer(*args, **kwargs):
    val = _core_.new_GBSizerItemSpacer(*args, **kwargs)
    return val


class GBSizerItemList_iterator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_GBSizerItemList_iterator
    __del__ = lambda self: None

    def next(*args, **kwargs):
        return _core_.GBSizerItemList_iterator_next(*args, **kwargs)


_core_.GBSizerItemList_iterator_swigregister(GBSizerItemList_iterator)

class GBSizerItemList(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr
    __swig_destroy__ = _core_.delete_GBSizerItemList
    __del__ = lambda self: None

    def __len__(*args, **kwargs):
        return _core_.GBSizerItemList___len__(*args, **kwargs)

    def __getitem__(*args, **kwargs):
        return _core_.GBSizerItemList___getitem__(*args, **kwargs)

    def __contains__(*args, **kwargs):
        return _core_.GBSizerItemList___contains__(*args, **kwargs)

    def __iter__(*args, **kwargs):
        return _core_.GBSizerItemList___iter__(*args, **kwargs)

    def index(*args, **kwargs):
        return _core_.GBSizerItemList_index(*args, **kwargs)

    def __repr__(self):
        return 'wxGBSizerItemList: ' + repr(list(self))


_core_.GBSizerItemList_swigregister(GBSizerItemList)

class GridBagSizer(FlexGridSizer):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr

    def __init__(self, *args, **kwargs):
        _core_.GridBagSizer_swiginit(self, _core_.new_GridBagSizer(*args, **kwargs))
        self._setOORInfo(self)

    def Add(*args, **kwargs):
        return _core_.GridBagSizer_Add(*args, **kwargs)

    def AddItem(*args, **kwargs):
        return _core_.GridBagSizer_AddItem(*args, **kwargs)

    def GetCellSize(*args, **kwargs):
        return _core_.GridBagSizer_GetCellSize(*args, **kwargs)

    def GetEmptyCellSize(*args, **kwargs):
        return _core_.GridBagSizer_GetEmptyCellSize(*args, **kwargs)

    def SetEmptyCellSize(*args, **kwargs):
        return _core_.GridBagSizer_SetEmptyCellSize(*args, **kwargs)

    def GetItemPosition(*args):
        return _core_.GridBagSizer_GetItemPosition(*args)

    def SetItemPosition(*args):
        return _core_.GridBagSizer_SetItemPosition(*args)

    def GetItemSpan(*args):
        return _core_.GridBagSizer_GetItemSpan(*args)

    def SetItemSpan(*args):
        return _core_.GridBagSizer_SetItemSpan(*args)

    def FindItem(*args):
        return _core_.GridBagSizer_FindItem(*args)

    def GetItem(self, item):
        gbsi = None
        si = wx.FlexGridSizer.GetItem(self, item)
        if not si:
            return
        if type(item) is not int:
            gbsi = self.FindItem(item)
        if gbsi:
            return gbsi
        return si

    def FindItemAtPosition(*args, **kwargs):
        return _core_.GridBagSizer_FindItemAtPosition(*args, **kwargs)

    def FindItemAtPoint(*args, **kwargs):
        return _core_.GridBagSizer_FindItemAtPoint(*args, **kwargs)

    def GetChildren(*args, **kwargs):
        return _core_.GridBagSizer_GetChildren(*args, **kwargs)

    def CheckForIntersection(*args, **kwargs):
        return _core_.GridBagSizer_CheckForIntersection(*args, **kwargs)

    def CheckForIntersectionPos(*args, **kwargs):
        return _core_.GridBagSizer_CheckForIntersectionPos(*args, **kwargs)


_core_.GridBagSizer_swigregister(GridBagSizer)
Left = _core_.Left
Top = _core_.Top
Right = _core_.Right
Bottom = _core_.Bottom
Width = _core_.Width
Height = _core_.Height
Centre = _core_.Centre
Center = _core_.Center
CentreX = _core_.CentreX
CentreY = _core_.CentreY
Unconstrained = _core_.Unconstrained
AsIs = _core_.AsIs
PercentOf = _core_.PercentOf
Above = _core_.Above
Below = _core_.Below
LeftOf = _core_.LeftOf
RightOf = _core_.RightOf
SameAs = _core_.SameAs
Absolute = _core_.Absolute

class IndividualLayoutConstraint(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')

    def __init__(self):
        raise AttributeError, 'No constructor defined'

    __repr__ = _swig_repr

    def Set(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_Set(*args, **kwargs)

    def LeftOf(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_LeftOf(*args, **kwargs)

    def RightOf(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_RightOf(*args, **kwargs)

    def Above(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_Above(*args, **kwargs)

    def Below(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_Below(*args, **kwargs)

    def SameAs(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SameAs(*args, **kwargs)

    def PercentOf(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_PercentOf(*args, **kwargs)

    def Absolute(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_Absolute(*args, **kwargs)

    def Unconstrained(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_Unconstrained(*args, **kwargs)

    def AsIs(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_AsIs(*args, **kwargs)

    def GetOtherWindow(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetOtherWindow(*args, **kwargs)

    def GetMyEdge(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetMyEdge(*args, **kwargs)

    def SetEdge(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SetEdge(*args, **kwargs)

    def SetValue(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SetValue(*args, **kwargs)

    def GetMargin(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetMargin(*args, **kwargs)

    def SetMargin(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SetMargin(*args, **kwargs)

    def GetValue(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetValue(*args, **kwargs)

    def GetPercent(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetPercent(*args, **kwargs)

    def GetOtherEdge(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetOtherEdge(*args, **kwargs)

    def GetDone(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetDone(*args, **kwargs)

    def SetDone(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SetDone(*args, **kwargs)

    def GetRelationship(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetRelationship(*args, **kwargs)

    def SetRelationship(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SetRelationship(*args, **kwargs)

    def ResetIfWin(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_ResetIfWin(*args, **kwargs)

    def SatisfyConstraint(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_SatisfyConstraint(*args, **kwargs)

    def GetEdge(*args, **kwargs):
        return _core_.IndividualLayoutConstraint_GetEdge(*args, **kwargs)

    Done = property(GetDone, SetDone, doc='See `GetDone` and `SetDone`')
    Margin = property(GetMargin, SetMargin, doc='See `GetMargin` and `SetMargin`')
    MyEdge = property(GetMyEdge, doc='See `GetMyEdge`')
    OtherEdge = property(GetOtherEdge, doc='See `GetOtherEdge`')
    OtherWindow = property(GetOtherWindow, doc='See `GetOtherWindow`')
    Percent = property(GetPercent, doc='See `GetPercent`')
    Relationship = property(GetRelationship, SetRelationship, doc='See `GetRelationship` and `SetRelationship`')
    Value = property(GetValue, SetValue, doc='See `GetValue` and `SetValue`')


_core_.IndividualLayoutConstraint_swigregister(IndividualLayoutConstraint)

class LayoutConstraints(Object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc='The membership flag')
    __repr__ = _swig_repr
    left = property(_core_.LayoutConstraints_left_get)
    top = property(_core_.LayoutConstraints_top_get)
    right = property(_core_.LayoutConstraints_right_get)
    bottom = property(_core_.LayoutConstraints_bottom_get)
    width = property(_core_.LayoutConstraints_width_get)
    height = property(_core_.LayoutConstraints_height_get)
    centreX = property(_core_.LayoutConstraints_centreX_get)
    centreY = property(_core_.LayoutConstraints_centreY_get)

    def __init__(self, *args, **kwargs):
        _core_.LayoutConstraints_swiginit(self, _core_.new_LayoutConstraints(*args, **kwargs))

    __swig_destroy__ = _core_.delete_LayoutConstraints
    __del__ = lambda self: None

    def SatisfyConstraints(*args, **kwargs):
        return _core_.LayoutConstraints_SatisfyConstraints(*args, **kwargs)

    def AreSatisfied(*args, **kwargs):
        return _core_.LayoutConstraints_AreSatisfied(*args, **kwargs)


_core_.LayoutConstraints_swigregister(LayoutConstraints)
try:
    True
except NameError:
    __builtins__.True = 1 == 1
    __builtins__.False = 1 == 0

    def bool(value):
        return not not value


    __builtins__.bool = bool

__wxPyPtrTypeMap['wxGauge95'] = 'wxGauge'
__wxPyPtrTypeMap['wxSlider95'] = 'wxSlider'
__wxPyPtrTypeMap['wxStatusBar95'] = 'wxStatusBar'
from __version__ import *
__version__ = VERSION_STRING
assert MAJOR_VERSION == _core_.MAJOR_VERSION, 'wxPython/wxWidgets version mismatch'
assert MINOR_VERSION == _core_.MINOR_VERSION, 'wxPython/wxWidgets version mismatch'
if RELEASE_VERSION != _core_.RELEASE_VERSION:
    import warnings
    warnings.warn('wxPython/wxWidgets release number mismatch')

def version():
    ctype = wx.USE_UNICODE and 'unicode' or 'ansi'
    if wx.Platform == '__WXMSW__':
        port = 'msw'
    elif wx.Platform == '__WXMAC__':
        port = 'mac'
    elif wx.Platform == '__WXGTK__':
        port = 'gtk'
        if 'gtk2' in wx.PlatformInfo:
            port = 'gtk2'
    else:
        port = '?'
    return '%s (%s-%s)' % (wx.VERSION_STRING, port, ctype)


default = _sys.getdefaultencoding()
if default == 'ascii':
    import locale
    import codecs
    try:
        if hasattr(locale, 'getpreferredencoding'):
            default = locale.getpreferredencoding()
        else:
            default = locale.getdefaultlocale()[1]
        codecs.lookup(default)
    except (ValueError, LookupError, TypeError):
        default = _sys.getdefaultencoding()

    del locale
    del codecs
if default:
    wx.SetDefaultPyEncoding(default)
del default

class PyDeadObjectError(AttributeError):
    pass


class _wxPyDeadObject(object):
    reprStr = 'wxPython wrapper for DELETED %s object! (The C++ object no longer exists.)'
    attrStr = 'The C++ part of the %s object has been deleted, attribute access no longer allowed.'

    def __repr__(self):
        if not hasattr(self, '_name'):
            self._name = '[unknown]'
        return self.reprStr % self._name

    def __getattr__(self, *args):
        if not hasattr(self, '_name'):
            self._name = '[unknown]'
        raise PyDeadObjectError(self.attrStr % self._name)

    def __nonzero__(self):
        return 0


class PyUnbornObjectError(AttributeError):
    pass


class _wxPyUnbornObject(object):
    reprStr = 'wxPython wrapper for UNBORN object! (The C++ object is not initialized yet.)'
    attrStr = 'The C++ part of this object has not been initialized, attribute access not allowed.'

    def __repr__(self):
        return self.reprStr

    def __getattr__(self, *args):
        raise PyUnbornObjectError(self.attrStr)

    def __nonzero__(self):
        return 0


def CallAfter(callable, *args, **kw):
    app = wx.GetApp()
    assert app is not None, 'No wx.App created yet'
    if not hasattr(app, '_CallAfterId'):
        app._CallAfterId = wx.NewEventType()
        app.Connect(-1, -1, app._CallAfterId, lambda event: event.callable(*event.args, **event.kw))
    evt = wx.PyEvent()
    evt.SetEventType(app._CallAfterId)
    evt.callable = callable
    evt.args = args
    evt.kw = kw
    wx.PostEvent(app, evt)


class CallLater():

    def __init__(self, millis, callable, *args, **kwargs):
        self.millis = millis
        self.callable = callable
        self.SetArgs(*args, **kwargs)
        self.runCount = 0
        self.running = False
        self.hasRun = False
        self.result = None
        self.timer = None
        self.Start()

    def __del__(self):
        self.Stop()

    def Start(self, millis = None, *args, **kwargs):
        self.hasRun = False
        if millis is not None:
            self.millis = millis
        if args or kwargs:
            self.SetArgs(*args, **kwargs)
        self.Stop()
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(self.millis, wx.TIMER_ONE_SHOT)
        self.running = True

    Restart = Start

    def Stop(self):
        if self.timer is not None:
            self.timer.Stop()
            self.timer = None

    def GetInterval(self):
        if self.timer is not None:
            return self.timer.GetInterval()
        else:
            return 0

    def IsRunning(self):
        return self.timer is not None and self.timer.IsRunning()

    def SetArgs(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def HasRun(self):
        return self.hasRun

    def GetResult(self):
        return self.result

    def Notify(self):
        if self.callable and getattr(self.callable, 'im_self', True):
            self.runCount += 1
            self.running = False
            self.result = self.callable(*self.args, **self.kwargs)
        self.hasRun = True
        if not self.running:
            wx.CallAfter(self.Stop)

    Interval = property(GetInterval)
    Result = property(GetResult)


class FutureCall(CallLater):
    pass


class __DocFilter():

    def __init__(self, globals):
        self._globals = globals

    def __call__(self, name):
        import types
        obj = self._globals.get(name, None)
        if type(obj) not in [type,
         types.ClassType,
         types.FunctionType,
         types.BuiltinFunctionType]:
            return False
        if name.startswith('_') or name.startswith('EVT') or name.endswith('_swigregister') or name.endswith('Ptr'):
            return False
        if name.find('_') != -1:
            cls = self._globals.get(name.split('_')[0], None)
            methname = name.split('_')[1]
            if hasattr(cls, methname) and type(getattr(cls, methname)) is types.FunctionType:
                return False
        return True


from _gdi import *
from _windows import *
from _controls import *
from _misc import *
