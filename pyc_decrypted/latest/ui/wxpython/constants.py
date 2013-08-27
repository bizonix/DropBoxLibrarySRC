#Embedded file name: ui/wxpython/constants.py
from __future__ import absolute_import
import sys
import wx
import ui.images
import build_number
from dropbox.build_common import get_icon_suffix
from dropbox.gui import event_handler
from dropbox.trace import TRACE, unhandled_exc_handler
from ..common.constants import colors
if sys.platform.startswith('win'):
    from dropbox.win32.version import VISTA, WIN2K, WINDOWS_VERSION

class MetaColors(type):

    def __getattr__(cls, attr):
        if attr not in colors:
            raise AttributeError("Color '%s' is not defined." % attr)
        r, g, b, a = colors[attr]
        return MetaColors.__makecolor(r, g, b, a)

    @classmethod
    def __makecolor(cls, r = 0, g = 0, b = 0, a = 0):
        return wx.Colour(r, g, b, a)


class Colors(object):
    __metaclass__ = MetaColors


def auto_select_textctrl(theEvent):
    obj = theEvent.GetEventObject()
    if isinstance(obj, wx.TextCtrl):
        obj.SelectAll()
    theEvent.Skip()


def find_and_select_textctrl_factory(parent):

    def find_and_select_textctrl(theEvent):
        obj = parent.FindFocus()
        if isinstance(obj, wx.TextCtrl):
            obj.SelectAll()
        theEvent.Skip()

    return find_and_select_textctrl


def set_accel_table(window, entry_list):
    i = 0
    dummymenu = wx.Menu()
    atable_list = []
    for entry in entry_list:
        flags, keycode, callback = entry
        dummyitem = dummymenu.Append(i, 'item%d' % i)
        atable_list.append((flags, keycode, dummyitem.GetId()))
        window.Bind(wx.EVT_MENU, callback, dummyitem)
        i += 1

    atable = wx.AcceleratorTable(atable_list)
    window.SetAcceleratorTable(atable)


REVERT, SAVE, CLOSE, SAVE_AND_CLOSE, HELP = range(5)
DEFAULT_FONT, INFO_TEXT_FONT, SMALL_RADIO_TEXT_FONT, FLASH_FONT, PLAN_SIZE_FONT = range(5)
FLEX_SPACE = '__flex_space__'
FANCY_HELP = '__fancy_help__'

class Win32(object):
    button_order = [FANCY_HELP,
     FLEX_SPACE,
     wx.ID_OK,
     wx.ID_CANCEL,
     wx.ID_APPLY]
    buttons = {wx.ID_OK: SAVE_AND_CLOSE,
     wx.ID_CANCEL: CLOSE,
     wx.ID_APPLY: SAVE}
    default_button = wx.ID_OK
    button_horizontal_spacing = 6
    swap_panel_border = 11
    text_static_box_interior = 6
    static_box_button_vertical_spacing = 8
    outer_button_border = 10
    outer_notebook_border = 20
    statictext_textctrl_horizontal_spacing = 10
    textctrl_statictext_horizontal_spacing = 7
    textctrl_button_horizontal_spacing = 7
    textctrl_textctrl_vertical_spacing = 6
    radio_group_spacer = 7
    checkbox_group_spacer = 7
    radio_static_box_interior = 10
    username_textctrl_width = 186
    loginpanel_textctrl_width = 179
    checkbox_staticlinktext_horizontal_spacing = 3
    subtext_vertical_aid_spacing = 15
    subtext_vertical_spacing = 2
    textctrl_cutoff_spacing = 6
    min_buttonpanel_width = 50
    tour_text_offset = 10
    tour_text_vertical_offset = 8
    top_of_baselined_textctrl_to_bottom_of_radio = 4
    radio_baseline_adjustment = 5
    choice_baseline_adjustment = 0
    statictext_baseline_adjustment = 5
    statictext_baseline_adjustment_to_match_radio = 0
    checkbox_baseline_adjustment = 5
    textctrl_baseline_adjustment = 0
    button_baseline_adjustment = 0
    error_button_width = 70
    error_dialog_width = 400
    error_bitmap_border = 15
    error_button_vertical_border = 10
    error_button_horizontal_border = 15
    delay_tree_button_event_until_mouse_up = False
    tree_alternate_background = False
    tree_highlight_entire_row = False
    tree_row_contents_centered = False
    tree_text_highlight_vert = 2
    tree_text_highlight_left = 2
    tree_text_highlight_right = 5
    selsync_root_left_border = 3
    selsync_treebutton_left_border = 4
    selsync_item_indent = 19
    selsync_treebutton_baseline_adjustment = 3
    selsync_checkbox_baseline_adjustment = 2
    selsync_checkbox_folder_spacing = 4
    selsync_folder_text_spacing = 5
    selsync_folder_top_padding = 2
    selsync_text_top_padding = 0
    selsync_row_stretcher = 0
    if sys.platform.startswith('win') and WINDOWS_VERSION >= VISTA:
        selsync_row_stretcher = 21
        selsync_checkbox_baseline_adjustment = 4
        selsync_text_top_padding = 1
        selsync_treebutton_baseline_adjustment = 4
        button_baseline_adjustment = -1
    elif hasattr(build_number, 'frozen'):
        selsync_treebutton_baseline_adjustment = 5

    @staticmethod
    def get_tour_font(window, point = 9):
        import arch
        face_name = 'Segoe UI' if WINDOWS_VERSION >= VISTA else 'MS Shell Dlg 2'
        if WINDOWS_VERSION == WIN2K:
            point -= 1
        lfHeight = arch.win32.internal.pointsize_to_lfHeight(point)
        tour_font = '0;%d;0;0;0;400;0;0;0;0;0;0;5;0;%s' % (lfHeight, face_name)
        font = window.GetFont()
        font_info = wx.NativeFontInfo()
        font_info.FromString(tour_font)
        font.SetNativeFontInfo(font_info)
        return font

    @staticmethod
    def apply_tour_font(window, point = 9, override_system_colors = False):
        font = Win32.get_tour_font(window, point)
        window.SetFont(font)

    @staticmethod
    def get_themed_font(window, font = DEFAULT_FONT):
        to_return = window.GetFont()
        try:
            import arch
            if hasattr(arch.win32.internal, 'font_for_hwnd'):
                win_const = arch.win32.internal.TMT_SMALLCAPTIONFONT if font == INFO_TEXT_FONT else arch.win32.internal.TMT_CAPTIONFONT
                the_font = arch.win32.internal.font_for_hwnd(window.GetHandle(), win_const)
                the_fontinfo = wx.NativeFontInfo()
                the_fontinfo.SetFaceName(the_font.lfFaceName)
                the_fontinfo.SetUnderlined(the_font.lfUnderline)
                the_fontinfo.SetPointSize(arch.win32.internal.lfHeight_to_pointsize(the_font.lfHeight))
                if the_font.lfFaceName != 'Segoe UI':
                    if font == INFO_TEXT_FONT:
                        the_fontinfo.SetPointSize(7)
                    elif font == SMALL_RADIO_TEXT_FONT:
                        the_fontinfo.SetPointSize(8)
                    elif font == FLASH_FONT:
                        the_fontinfo.SetPointSize(8)
                if font == PLAN_SIZE_FONT:
                    the_fontinfo.SetPointSize(16)
                    the_fontinfo.SetWeight(wx.FONTWEIGHT_BOLD)
                to_return.SetNativeFontInfo(the_fontinfo)
        except Exception:
            unhandled_exc_handler()
            if font == INFO_TEXT_FONT:
                the_fontinfo.SetPointSize(7)
            elif font == SMALL_RADIO_TEXT_FONT:
                to_return.SetPointSize(8)
            elif font == FLASH_FONT:
                to_return.SetPointSize(8)
            elif font == PLAN_SIZE_FONT:
                to_return.SetPointSize(16)
                to_return.SetWeight(wx.FONTWEIGHT_BOLD)

        return to_return

    @staticmethod
    @event_handler
    def frame_icon(frame):
        import arch
        icon_index = arch.constants.ICON_INDEX_LOGO
        if hasattr(build_number, 'frozen'):
            icon_path = u'%s;-%s' % (arch.util.executable()[0].decode('mbcs'), icon_index)
        else:
            icon_path = arch.constants.ICON_PATHS[icon_index] % {'suffix': get_icon_suffix(build_number.BUILD_KEY)}
        TRACE('loading frame icon from: %r' % (icon_path,))
        frame.SetIcon(wx.Icon(icon_path, wx.BITMAP_TYPE_ICO))

    @staticmethod
    def native_behavior(window, close_function = None, atable_extensions = []):
        if WINDOWS_VERSION < VISTA:
            atable_list = [(wx.ACCEL_CTRL, ord('A'), find_and_select_textctrl_factory(window))]
            atable_list.extend(atable_extensions)
            set_accel_table(window, atable_list)

    frame_t = wx.Frame
    simple_frame_style = wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX & ~wx.MINIMIZE_BOX & ~wx.RESIZE_BORDER
    animate_on_swap = False
    use_native_toolbar = False
    use_notebook = False
    use_buffered_dc = True
    dropbox_choices_hover = True
    memory_dc = None
    nullbmp = None

    @staticmethod
    def text_extent(text, font = None):
        if font:
            f = Win32.memory_dc.GetFont()
            Win32.memory_dc.SetFont(font)
        extent = Win32.memory_dc.GetTextExtent(text)
        if font:
            Win32.memory_dc.SetFont(f)
        return extent

    @staticmethod
    def get_gcdc(dc):
        if WINDOWS_VERSION >= VISTA:
            return wx.GCDC(dc)
        else:
            return dc

    @staticmethod
    def init():
        Win32.nullbmp = wx.EmptyBitmap(1, 1)
        Win32.memory_dc = wx.MemoryDC()
        Win32.memory_dc.SelectObject(Win32.nullbmp)


class GNOME(object):
    button_order = [wx.ID_HELP, FLEX_SPACE, wx.ID_CLOSE]
    buttons = {wx.ID_HELP: HELP,
     wx.ID_CLOSE: SAVE_AND_CLOSE}
    default_button = wx.ID_CLOSE
    button_horizontal_spacing = 6
    swap_panel_border = 11
    notebook_panel_border = 12
    text_static_box_interior = 6
    static_box_button_vertical_spacing = 8
    outer_button_border = 10
    outer_notebook_border = 12
    statictext_textctrl_horizontal_spacing = 10
    textctrl_statictext_horizontal_spacing = 7
    textctrl_button_horizontal_spacing = 7
    textctrl_textctrl_vertical_spacing = 6
    radio_group_spacer = 6
    checkbox_group_spacer = 6
    radio_static_box_interior = 10
    radio_notebook_interior = 12
    statictext_notebook_interior = 12
    username_textctrl_width = 186
    textctrl_cutoff_spacing = 6
    min_buttonpanel_width = 65
    tour_text_offset = 20
    tour_text_vertical_offset = 10
    loginpanel_textctrl_width = 186
    checkbox_staticlinktext_horizontal_spacing = 0
    subtext_vertical_spacing = 2
    subtext_vertical_aid_spacing = 15
    top_of_baselined_textctrl_to_bottom_of_radio = 3
    radio_baseline_adjustment = 2
    choice_baseline_adjustment = 1
    statictext_baseline_adjustment = 5
    checkbox_baseline_adjustment = 4
    textctrl_baseline_adjustment = 0
    statictext_baseline_adjustment_to_match_button = 10
    statictext_baseline_adjustment_to_match_radio = 3
    button_baseline_adjustment = 0
    error_button_width = 70
    error_dialog_width = 474
    error_bitmap_border = 20
    error_button_vertical_border = 19
    error_button_horizontal_border = 24
    delay_tree_button_event_until_mouse_up = True
    tree_alternate_background = False
    tree_highlight_entire_row = True
    tree_row_contents_centered = True
    tree_text_highlight_vert = 2
    tree_text_highlight_left = 2
    tree_text_highlight_right = 5
    tree_button_checkbox_spacing = 0
    selsync_root_left_border = 3
    selsync_treebutton_left_border = 4
    selsync_item_indent = 19
    selsync_treebutton_baseline_adjustment = 0
    selsync_checkbox_baseline_adjustment = 2
    selsync_checkbox_folder_spacing = 4
    selsync_folder_text_spacing = 5
    selsync_folder_top_padding = 2
    selsync_text_top_padding = 0
    selsync_row_stretcher = 0

    @staticmethod
    @event_handler
    def frame_icon(frame):
        frame.SetIcon(ui.images.wximages.Logo.GetIcon())

    @staticmethod
    def native_behavior(window, close_function = None, atable_extensions = []):
        atable_list = []
        atable_list.extend(atable_extensions)
        set_accel_table(window, atable_list)

    frame_t = wx.Frame
    simple_frame_style = wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER
    animate_on_swap = False
    use_native_toolbar = False
    use_notebook = hasattr(wx, 'Notebook')
    use_buffered_dc = True
    dropbox_choices_hover = True
    memory_dc = None
    nullbmp = None

    @staticmethod
    def get_tour_font(window, size = 9):
        the_font = window.GetFont()
        the_font.SetPointSize(size)
        return the_font

    @staticmethod
    def apply_tour_font(window, size = 9, override_system_colors = False):
        font = GNOME.get_tour_font(window, size)
        window.SetFont(font)
        if override_system_colors:
            window.SetForegroundColour(Colors.black)
            window.SetBackgroundColour(Colors.white)

    @staticmethod
    def get_themed_font(window, font = DEFAULT_FONT):
        the_font = window.GetFont()
        if font == INFO_TEXT_FONT:
            the_font.SetPointSize(8)
        elif font == SMALL_RADIO_TEXT_FONT:
            the_font.SetPointSize(8)
        elif font == FLASH_FONT:
            the_font.SetPointSize(8)
        elif font == PLAN_SIZE_FONT:
            the_font.SetPointSize(16)
            the_font.SetWeight(wx.FONTWEIGHT_BOLD)
        return the_font

    @staticmethod
    def text_extent(text, font = None):
        if font:
            f = GNOME.memory_dc.GetFont()
            GNOME.memory_dc.SetFont(font)
        extent = GNOME.memory_dc.GetTextExtent(text)
        if font:
            GNOME.memory_dc.SetFont(f)
        return extent

    @staticmethod
    def get_gcdc(dc):
        return wx.GCDC(dc)

    @staticmethod
    def init():
        GNOME.nullbmp = wx.EmptyBitmap(1, 1)
        GNOME.memory_dc = wx.MemoryDC()
        GNOME.memory_dc.SelectObject(GNOME.nullbmp)


if sys.platform.lower() == 'win32':
    platform = Win32
elif sys.platform.lower().startswith('linux'):
    platform = GNOME
