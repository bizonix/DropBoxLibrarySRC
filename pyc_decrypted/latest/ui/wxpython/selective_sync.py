#Embedded file name: ui/wxpython/selective_sync.py
from __future__ import absolute_import
import sys
import time
import wx
from .constants import Colors, GNOME, platform, Win32
import ui.images
from dropbox.debugging import easy_repr
from dropbox.gui import assert_message_queue, event_handler, message_sender, spawn_thread_with_name
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from .dropbox_controls import DropboxWxMenu, TransparentPanel, TransparentStaticText
from .util import dirty_rects, draw_on_bitmap
from ..common.selective_sync import CachingLazySelectiveSyncUI, selsync_strings, failed_unignores_message_from_failures
if sys.platform.startswith('win'):
    from dropbox.win32.version import VISTA, WIN2K, WINDOWS_VERSION
REMOTE_EVENT_CHILLOUT = 1
LAUNCH_LABEL_INITIAL_WIDTH = 100

class NativeRenderStore(object):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self):
        TRACE('loading wx native renderer')
        self._renderer = wx.RendererNative.Get()
        if platform == GNOME:
            self._load_linux()
        elif platform == Win32:
            self._load_windows()
        self._load_folders()
        self.draw_selection = self._renderer.DrawItemSelectionRect

    @event_handler
    def _load_windows(self):
        TRACE('loading win2k/winxp style tree bitmaps')
        self._tree_bitmaps = {}
        self._tree_bitmaps[0] = ui.images.wximages.TreeCollapsed.GetBitmap()
        self._tree_bitmaps[wx.CONTROL_EXPANDED] = ui.images.wximages.TreeExpanded.GetBitmap()
        if WINDOWS_VERSION < VISTA:
            self._tree_bitmaps[wx.CONTROL_CURRENT] = ui.images.wximages.TreeCollapsed.GetBitmap()
            self._tree_bitmaps[wx.CONTROL_CURRENT | wx.CONTROL_EXPANDED] = ui.images.wximages.TreeExpanded.GetBitmap()
        else:
            TRACE('loading vista/win7 style tree bitmaps')
            self._tree_bitmaps[wx.CONTROL_CURRENT] = ui.images.wximages.TreeCollapsedHover.GetBitmap()
            self._tree_bitmaps[wx.CONTROL_CURRENT | wx.CONTROL_EXPANDED] = ui.images.wximages.TreeExpandedHover.GetBitmap()
        size = None
        for bitmap in self._tree_bitmaps.itervalues():
            if size is not None and size != bitmap.GetSize():
                report_bad_assumption("tree bitmaps should NOT be different size within a platform, they'll jump around the screen otherwise")
            size = bitmap.GetSize()

        self.draw_tree = self._draw_tree_win32
        self.size_tree = self._size_tree_win32
        self._checkbox_bitmaps = {}
        if WINDOWS_VERSION == WIN2K:
            TRACE('loading win2k style checkbox bitmaps')
            self._checkbox_bitmaps[0] = ui.images.wximages.CheckboxUnchecked2k.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_PRESSED] = ui.images.wximages.CheckboxUnchecked.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_CURRENT] = ui.images.wximages.CheckboxUnchecked.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_CHECKED] = ui.images.wximages.CheckboxChecked.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_CHECKED | wx.CONTROL_PRESSED] = ui.images.wximages.CheckboxChecked.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_CHECKED | wx.CONTROL_CURRENT] = ui.images.wximages.CheckboxChecked.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_UNDETERMINED] = ui.images.wximages.CheckboxTristate.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_UNDETERMINED | wx.CONTROL_PRESSED] = ui.images.wximages.CheckboxTristate.GetBitmap()
            self._checkbox_bitmaps[wx.CONTROL_UNDETERMINED | wx.CONTROL_CURRENT] = ui.images.wximages.CheckboxTristate.GetBitmap()
        else:
            for state in ((0, 'Unchecked'), (wx.CONTROL_CHECKED, 'Checked'), (wx.CONTROL_UNDETERMINED, 'Tristate')):
                for flag in ((0, ''), (wx.CONTROL_PRESSED, 'Pressed'), (wx.CONTROL_CURRENT, 'Hover')):
                    self._checkbox_bitmaps[state[0] | flag[0]] = getattr(ui.images.wximages, 'Checkbox%s%s' % (state[1], flag[1])).GetBitmap()

        self.size_checkbox = self._size_checkbox_win32
        self.draw_checkbox = self._draw_checkbox_win32

    @event_handler
    def _size_tree_win32(self):
        return self._tree_bitmaps[0].GetSize().Get()

    @event_handler
    def _draw_tree_win32(self, win, dc, rect, flags):
        dc.DrawBitmapPoint(self._tree_bitmaps[flags], rect.position)

    @event_handler
    def _load_linux(self):
        self.draw_tree = self._draw_tree_linux
        self.size_tree = self._size_tree_linux
        self.size_checkbox = self._size_checkbox_linux
        self.draw_checkbox = self._renderer.DrawCheckBox

    @event_handler
    def _size_tree_linux(self):
        return (22, 26)

    @event_handler
    def _draw_tree_linux(self, win, dc, rect, flags):
        new_rect = rect.Get()
        new_rect = wx.Rect(new_rect[0] + 6, new_rect[1] + 10, new_rect[2], new_rect[3])
        self._renderer.DrawTreeItemButton(win, dc, new_rect, flags)

    @event_handler
    def _size_checkbox_linux(self, win):
        chk = wx.CheckBox(win, style=wx.CHK_NO_SIBLING_LABEL)
        size = chk.GetSize().Get()
        chk.Show(False)
        chk.Destroy()
        return size

    @event_handler
    def _size_checkbox_win32(self, win):
        return self._checkbox_bitmaps[0].GetSize().Get()

    @event_handler
    def _draw_checkbox_win32(self, window, dc, rect, flags):
        dc.DrawBitmapPoint(self._checkbox_bitmaps[flags], rect.position)

    @event_handler
    def font(self, win):
        if platform == Win32 and WINDOWS_VERSION >= VISTA:
            return platform.get_themed_font(win)
        else:
            return wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

    @event_handler
    def _load_folders(self):
        if platform == Win32 and WINDOWS_VERSION >= VISTA:
            terminator = 'Vista'
        else:
            terminator = ''
        self._folder_bitmaps = {'dropbox': getattr(ui.images.wximages, 'SelectiveSyncDropboxFolder%s' % (terminator,)).GetBitmap(),
         'shared': getattr(ui.images.wximages, 'SelectiveSyncSharedFolder%s' % (terminator,)).GetBitmap(),
         'sandbox': getattr(ui.images.wximages, 'SelectiveSyncAppFolder%s' % (terminator,)).GetBitmap(),
         'public': getattr(ui.images.wximages, 'SelectiveSyncPublicFolder%s' % (terminator,)).GetBitmap(),
         'photos': getattr(ui.images.wximages, 'SelectiveSyncPhotosFolder%s' % (terminator,)).GetBitmap(),
         'camerauploads': getattr(ui.images.wximages, 'SelectiveSyncCameraUploadsFolder%s' % (terminator,)).GetBitmap(),
         'folder': getattr(ui.images.wximages, 'SelectiveSyncFolder%s' % (terminator,)).GetBitmap()}

    @event_handler
    def bitmap_for_folder_tag(self, tag):
        return self._folder_bitmaps[tag]


class SelectiveSyncTreeRow(object):
    __slots__ = ['_path',
     '_root',
     '_advanced',
     'treebutton_rect',
     'checkbox_rect',
     'bitmap_rect',
     'title_rect',
     'item_rect',
     'content_rect',
     '_native_render_store',
     '_bitmap',
     '_title',
     '_check_state',
     '_mouse_down_in_check',
     '_mouse_hovering_over_check',
     '_mouse_hovering_over_treebutton',
     '_selected',
     '_isleaf',
     '_expanded',
     '_font']

    def __repr__(self):
        return easy_repr(self, *self.__slots__)

    def __init__(self, path, root, advanced, bitmap, title, native_render_store):
        self._path = path
        self._root = root
        self._advanced = advanced
        self.treebutton_rect = None
        self.checkbox_rect = None
        self.bitmap_rect = None
        self.title_rect = None
        self.item_rect = None
        self._bitmap = bitmap
        self._title = title
        self._native_render_store = native_render_store
        self._check_state = 0
        self._mouse_down_in_check = False
        self._mouse_hovering_over_check = False
        self._mouse_hovering_over_treebutton = False
        self._selected = False
        self._isleaf = False
        self._expanded = False
        self._font = None

    def is_showing_self(self):
        return True

    def is_showing_checkbox(self):
        return not self._root

    def is_showing_treebutton(self):
        return self._advanced and not self._root

    def path(self):
        return self._path

    def title(self):
        return self._title

    def set_selected(self, selected):
        self._selected = selected

    def set_leaf(self, leaf):
        self._isleaf = leaf

    def set_expanded(self, expanded):
        self._expanded = expanded

    def expanded(self):
        return self._expanded

    def set_check_state(self, check_state):
        if check_state != self._check_state:
            self._check_state = check_state
            return True
        else:
            return False

    def check_state(self):
        return self._check_state

    def next_check_state(self):
        if self._check_state:
            return 0
        return 1

    def mouse_hovering_over(self, point):
        dirty_rect = wx.Rect(0, 0, 0, 0)
        events = []
        if self.is_showing_treebutton() and self.treebutton_rect.Contains(point):
            if not self._mouse_hovering_over_treebutton:
                self._mouse_hovering_over_treebutton = True
                dirty_rect.Union(self.treebutton_rect)
                if self._mouse_hovering_over_check:
                    self._mouse_hovering_over_check = False
                    dirty_rect.Union(self.checkbox_rect)
        elif self.is_showing_checkbox() and self.checkbox_rect.Contains(point):
            if not self._mouse_hovering_over_check:
                self._mouse_hovering_over_check = True
                dirty_rect.Union(self.checkbox_rect)
                if self._mouse_hovering_over_treebutton:
                    self._mouse_hovering_over_treebutton = False
                    dirty_rect.Union(self.treebutton_rect)
        elif self._mouse_hovering_over_check:
            self._mouse_hovering_over_check = False
            dirty_rect.Union(self.checkbox_rect)
        elif self._mouse_hovering_over_treebutton:
            self._mouse_hovering_over_treebutton = False
            dirty_rect.Union(self.treebutton_rect)
        return (dirty_rect, events)

    def mouse_down_at(self, point):
        dirty_rect = wx.Rect(0, 0, 0, 0)
        events = []
        if self.is_showing_treebutton() and self.treebutton_rect.Contains(point) and not self._isleaf:
            events.append('collapse' if self._expanded else 'expand')
            self._expanded = not self._expanded
            dirty_rect.Union(self.treebutton_rect)
        elif self.is_showing_checkbox() and self.checkbox_rect.Contains(point):
            if not self._mouse_down_in_check:
                self._mouse_down_in_check = True
                dirty_rect.Union(self.checkbox_rect)
        elif self.is_showing_self() and self.item_rect.Contains(point):
            events.append('focus')
        return (dirty_rect, events)

    def mouse_up_at(self, point):
        dirty_rect = wx.Rect(0, 0, 0, 0)
        events = []
        if self._mouse_down_in_check:
            self._mouse_down_in_check = False
            if self.is_showing_checkbox() and self.checkbox_rect.Contains(point):
                self._mouse_hovering_over_check = True
                self._check_state = self.next_check_state()
                events.append('check')
            else:
                self._mouse_hovering_over_check = False
            dirty_rect.Union(self.checkbox_rect)
        return (dirty_rect, events)

    def get_selection_flags(self, focused):
        selection_flags = wx.CONTROL_SELECTED
        if focused:
            selection_flags |= wx.CONTROL_FOCUSED
        return selection_flags

    def get_treebutton_flags(self):
        state = None
        if not self._isleaf:
            state = wx.CONTROL_EXPANDED if self._expanded else 0
            if self._mouse_hovering_over_treebutton:
                state |= wx.CONTROL_CURRENT
        return state

    @event_handler
    def get_checkbox_flags(self):
        state = wx.CONTROL_CHECKED if self._check_state == 1 else (0 if self._check_state == 0 else wx.CONTROL_UNDETERMINED)
        if self._mouse_down_in_check:
            if self._mouse_hovering_over_check:
                state |= wx.CONTROL_PRESSED
            else:
                state |= wx.CONTROL_CURRENT
        elif self._mouse_hovering_over_check:
            state |= wx.CONTROL_CURRENT
        return state

    @event_handler
    def layout(self, window, origin, dc):
        self._font = self._native_render_store.font(window)
        h = 0
        ox, oy = origin.Get()
        x, y = origin.Get()
        x += platform.selsync_root_left_border
        if self.is_showing_treebutton():
            x += platform.selsync_treebutton_left_border
        if self.is_showing_treebutton():
            tree_button_w, tree_button_h = self._native_render_store.size_tree()
            self.treebutton_rect = wx.Rect(x, y + platform.selsync_treebutton_baseline_adjustment, tree_button_w, tree_button_h)
            h = max(platform.selsync_treebutton_baseline_adjustment + tree_button_h, h)
            x += tree_button_w
            x += platform.selsync_checkbox_folder_spacing
        if self.is_showing_checkbox():
            checkbox_w, checkbox_h = self._native_render_store.size_checkbox(window)
            self.checkbox_rect = wx.Rect(x, y + platform.selsync_checkbox_baseline_adjustment, checkbox_w, checkbox_h)
            x += checkbox_w
            h = max(checkbox_h, h)
            x += platform.selsync_checkbox_folder_spacing
        size = self._bitmap.GetSize()
        self.bitmap_rect = wx.Rect(x, (y + platform.selsync_folder_top_padding), *size.Get())
        x += size.GetWidth()
        h = max(size.GetHeight() + platform.selsync_folder_top_padding, h)
        x += platform.selsync_folder_text_spacing
        dc.SetFont(self._font)
        title_w, title_h = dc.GetTextExtent(self._title)
        self.title_rect = wx.Rect(x - platform.tree_text_highlight_left, y + platform.selsync_text_top_padding, title_w + platform.tree_text_highlight_left + platform.tree_text_highlight_right, title_h + platform.tree_text_highlight_vert * 2)
        x += title_w + platform.tree_text_highlight_left + platform.tree_text_highlight_right
        h = max(title_h + platform.tree_text_highlight_vert * 2 + platform.selsync_text_top_padding, h)
        if platform.tree_row_contents_centered:
            if self.is_showing_treebutton():
                tree_spacing = (h - self.treebutton_rect.GetSize().Get()[1]) / 2
                self.treebutton_rect.SetTop(oy + tree_spacing)
            if self.is_showing_checkbox():
                check_spacing = (h - self.checkbox_rect.GetSize().Get()[1]) / 2
                self.checkbox_rect.SetTop(oy + check_spacing)
            bitmap_spacing = (h - self.bitmap_rect.GetSize().Get()[1]) / 2
            self.bitmap_rect.SetTop(oy + bitmap_spacing)
            title_spacing = (h - self.title_rect.GetSize().Get()[1]) / 2
            self.title_rect.SetTop(oy + title_spacing)
        self.content_rect = wx.Rect(ox, oy, x - ox, h)
        self.item_rect = self.content_rect

    @event_handler
    def adjust_for_client_width(self, client_width):
        x, y, w, h = self.item_rect.Get()
        self.item_rect = wx.Rect(0, y, client_width, h)

    @event_handler
    def paint(self, window, dc, text_color, highlight_text_color, focused, dirty_rect):
        if dirty_rect.Intersects(self.item_rect) and platform.tree_highlight_entire_row and self._selected:
            self._native_render_store.draw_selection(window, dc, self.item_rect, self.get_selection_flags(focused))
        if self.is_showing_treebutton() and dirty_rect.Intersects(self.treebutton_rect):
            flags = self.get_treebutton_flags()
            if flags is not None:
                self._native_render_store.draw_tree(window, dc, self.treebutton_rect, flags)
                dirty_rect.Union(self.treebutton_rect)
        if self.is_showing_checkbox() and dirty_rect.Intersects(self.checkbox_rect):
            self._native_render_store.draw_checkbox(window, dc, self.checkbox_rect, self.get_checkbox_flags())
            dirty_rect.Union(self.checkbox_rect)
        if dirty_rect.Intersects(self.bitmap_rect):
            dc.DrawBitmapPoint(self._bitmap, self.bitmap_rect.position)
            dirty_rect.Union(self.bitmap_rect)
        if dirty_rect.Intersects(self.title_rect):
            dc.SetFont(self._font)
            if self._selected:
                dc.SetTextForeground(highlight_text_color)
                if not platform.tree_highlight_entire_row:
                    self._native_render_store.draw_selection(window, dc, self.title_rect, self.get_selection_flags(focused))
            else:
                dc.SetTextForeground(text_color)
            dc.DrawText(self._title, self.title_rect.Get()[0] + platform.tree_text_highlight_left, self.title_rect.Get()[1] + platform.tree_text_highlight_vert)
            dirty_rect.Union(self.title_rect)


class TreeDelegate(object):

    def __repr__(self):
        return easy_repr(self, '_forest', '_native_render_store')

    def __init__(self, forest, native_render_store):
        self._forest = forest
        self._native_render_store = native_render_store

    def native_render_store(self):
        return self._native_render_store

    def bitmap_for_path(self, path):
        return self._native_render_store.bitmap_for_folder_tag(self._forest.image_tag_for_path(path))

    def title_for_path(self, path):
        return self._forest.title_for_path(path)

    def check_state_for_path(self, path):
        return self._forest.check_state_for_path(path)

    def set_check_state_from_ui(self, path, check_state):
        self._forest.set_check_state_from_ui(path, check_state)

    def dir_children_for_path(self, path):
        return self._forest.dir_children_for_path(path)

    def context_menu_for_path(self, path):
        return DropboxWxMenu(self._forest.context_menu_for_path(path))

    def show_advanced_view(self):
        return self._forest.advanced_view

    def root_path(self):
        return self._forest.get_root_paths()[0]


class RowStateManager(object):

    def __repr__(self):
        return easy_repr(self, '_rows', '_selection', '_tree_delegate')

    def __init__(self, tree_delegate):
        super(RowStateManager, self).__init__()
        self._tree_delegate = tree_delegate
        self._selection = None
        self._rows = [(self._make_row(self._tree_delegate.root_path(), root=True), -1)]
        self.expand_row(self._rows[0][0])

    def _make_row(self, path, root = False):
        row = SelectiveSyncTreeRow(path, root, self._tree_delegate.show_advanced_view(), self._tree_delegate.bitmap_for_path(path), self._tree_delegate.title_for_path(path), self._tree_delegate.native_render_store())
        row.set_check_state(self._tree_delegate.check_state_for_path(path))
        return row

    def row_at_index(self, i):
        return self._rows[i][0]

    def index_of_row(self, row):
        for i, row_depth in enumerate(self._rows):
            if row_depth[0] == row:
                return i

    def set_check_state_from_ui(self, row):
        dirty_rect = wx.Rect(0, 0, 0, 0)
        self._tree_delegate.set_check_state_from_ui(row.path(), row.check_state())
        for row, depth in self._rows:
            if row.set_check_state(self._tree_delegate.check_state_for_path(row.path())):
                if row.is_showing_checkbox():
                    dirty_rect.Union(row.checkbox_rect)

        return dirty_rect

    def expand_row(self, row, dir_children = None):
        i = self.index_of_row(row)
        if dir_children is None:
            dir_children = self._tree_delegate.dir_children_for_path(row.path())
        row.set_expanded(True)
        new_depth = self._rows[i][1] + 1
        for new_child, has_own_children in dir_children:
            child_row = self._make_row(new_child)
            child_row.set_leaf(not has_own_children)
            self._rows.insert(i + 1, (child_row, new_depth))
            i += 1

        return True

    def collapse_row(self, row):
        row.set_expanded(False)
        i = self.index_of_row(row)
        depth_to_cut_from = self._rows[i][1]
        new_rows = self._rows[:i + 1]
        start_adding = False
        for later_row, depth in iter(self._rows[i + 1:]):
            if depth <= depth_to_cut_from:
                start_adding = True
            if start_adding:
                new_rows.append((later_row, depth))
            elif self._selection == later_row:
                row.set_selected(True)
                self._selection = row

        self._rows = new_rows
        return True

    def view_order_iterator(self):
        for row, depth in list(self._rows):
            if row.is_showing_self():
                yield (row, depth)

    @event_handler
    def move_selection(self, down):
        dirty_rect = wx.Rect(0, 0, 0, 0)
        if self._selection is None:
            for row, depth in self.view_order_iterator():
                dirty_rect.Union(self.request_selection(row))
                break

        else:
            last_row = None
            for row, depth in self.view_order_iterator():
                if not down and self._selection == row:
                    if last_row is not None:
                        dirty_rect.Union(self.request_selection(last_row))
                    break
                elif down and last_row == self._selection:
                    dirty_rect.Union(self.request_selection(row))
                    break
                last_row = row

        return dirty_rect

    @event_handler
    def expand_selection(self, expand):
        if self._selection is not None and self._selection.is_showing_treebutton() and not self._selection._isleaf and self._selection.expanded() != expand:
            return (self.expand_row if expand else self.collapse_row)(self._selection)

    @event_handler
    def request_selection(self, row):
        dirty_rect = None
        if self._selection != row:
            if self._selection is not None:
                self._selection.set_selected(False)
                if self._selection.item_rect is not None:
                    dirty_rect = wx.Rect(*self._selection.item_rect.Get())
            if row is None:
                self._selection = None
            elif self._selection != row:
                row.set_selected(True)
                self._selection = row
                if dirty_rect is not None:
                    dirty_rect.Union(row.item_rect)
                else:
                    dirty_rect = wx.Rect(*row.item_rect.Get())
        return dirty_rect

    def selection(self):
        return self._selection

    @event_handler
    def context_menu_for_row(self, row):
        return self._tree_delegate.context_menu_for_path(row.path())

    @event_handler
    def refresh_path_with_children(self, path, dir_children):
        l_path = path.lower()
        for row, depth in self._rows:
            if row.path().lower() == l_path:
                row.set_leaf(not dir_children)
                if row.expanded():
                    relayout = True
                    self.collapse_row(row)
                else:
                    relayout = False
                if dir_children:
                    relayout = True
                    self.expand_row(row, dir_children=dir_children)
                return (relayout, False)

        return (False, False)

    def select_by_chars(self, chars):
        for row, depth in self._rows:
            if row.title().lower().startswith(chars.lower()):
                return self.request_selection(row)


EVT_IGNORE_LIST_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)

class IgnoreListChangedEvent(wx.PyCommandEvent):

    def __init__(self, win):
        super(IgnoreListChangedEvent, self).__init__(EVT_IGNORE_LIST_CHANGED.typeId, win.GetId())
        self.EventObject = win


class SelectiveSyncTree(wx.Panel):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, tree_delegate):
        super(SelectiveSyncTree, self).__init__(parent, style=wx.NO_FULL_REPAINT_ON_RESIZE | wx.WANTS_CHARS)
        self._buffer = None
        self._row_state_manager = RowStateManager(tree_delegate)
        self._popped_menu = None
        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self.handle_color_changed)
        self.Bind(wx.EVT_PAINT, self.handle_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.handle_erase_background)
        self.Bind(wx.EVT_MOTION, self.handle_mouse_motion)
        self.Bind(wx.EVT_ENTER_WINDOW, self.handle_mouse_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.handle_mouse_motion)
        self.Bind(wx.EVT_LEFT_DOWN, self.handle_mouse_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.handle_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.handle_mouse_up)
        self._type_select_timeout = 2
        self._last_chr_event = None
        self.Bind(wx.EVT_KEY_DOWN, self.handle_key_down)
        self.Bind(wx.EVT_CHAR, self.handle_char)
        self.Bind(wx.EVT_CONTEXT_MENU, self.handle_context_menu)
        self.Bind(wx.EVT_KILL_FOCUS, self.refresh_selected_item)
        self.Bind(wx.EVT_SET_FOCUS, self.refresh_selected_item)
        self.pending_paths_to_invalidate = {}
        self.last_ui_invalidation = None
        self.SetClientSize(self._size_to_fit())
        self.handle_color_changed(None)
        self.handle_size(None)
        self.Bind(wx.EVT_SIZE, self.handle_size)
        self.SetFocus()

    @event_handler
    def handle_erase_background(self, theEvent):
        pass

    @event_handler
    def handle_char(self, theEvent):
        the_time = time.time()
        if self._last_chr_event is None or the_time - self._last_chr_event > self._type_select_timeout:
            self._current_type_selection = u''
        self._last_chr_event = the_time
        self._current_type_selection += unichr(theEvent.GetUniChar())
        dirty = self._row_state_manager.select_by_chars(self._current_type_selection)
        if dirty:
            self._redraw(dirty_rect=dirty)
            selected_row = self._row_state_manager.selection()
            if selected_row is not None:
                if selected_row.item_rect is not None:
                    self.Parent.assure_rect_revealed(selected_row.content_rect)

    @event_handler
    def invalidate_ui_callback(self, paths_to_invalidate):
        TRACE('++ remote told me to invalidate: %r' % (paths_to_invalidate,))
        self.pending_paths_to_invalidate.update(paths_to_invalidate)
        incoming = time.time()
        if self.last_ui_invalidation is not None and incoming - self.last_ui_invalidation < REMOTE_EVENT_CHILLOUT:
            TRACE('chilling out for a bit')
            wx.CallLater(max(REMOTE_EVENT_CHILLOUT - (incoming - self.last_ui_invalidation), 1) * 1000, self.invalidate_ui_callback, {})
            return
        self.last_ui_invalidation = incoming
        needs_relayout = False
        needs_redraw = False
        for lowered in self.pending_paths_to_invalidate:
            inner_needs_relayout, inner_needs_redraw = self._row_state_manager.refresh_path_with_children(lowered, self.pending_paths_to_invalidate[lowered])
            needs_relayout |= inner_needs_relayout
            needs_redraw |= inner_needs_redraw

        if needs_relayout or self._buffer is None:
            new_size = self._size_to_fit()
            self.SetClientSize(new_size)
        else:
            self._redraw()
        self.pending_paths_to_invalidate = {}

    def layout_for_new_parent_size(self, redraw = True):
        _, h = self.GetClientSize().Get()
        w = max(self._laid_out_size, self.Parent.GetClientSize().Get()[0])
        for row, depth in self._row_state_manager.view_order_iterator():
            row.adjust_for_client_width(w)

        if platform.tree_highlight_entire_row and redraw:
            selection = self._row_state_manager.selection()
            if selection is not None:
                dirty_rect = selection.item_rect
            else:
                dirty_rect = wx.Rect(0, 0, 0, 0)
            self.SetClientSize((w, h))
        return w

    @event_handler
    def _size_to_fit(self):
        client_dc = wx.ClientDC(self)
        w = h = 0
        for row, depth in self._row_state_manager.view_order_iterator():
            row.layout(self, wx.Point(platform.selsync_item_indent * max(depth, 0), h), client_dc)
            h += row.content_rect.GetHeight()
            w = max(w, row.content_rect.GetRight())

        self._laid_out_size = w
        w = self.layout_for_new_parent_size(redraw=False)
        return wx.Size(w, h)

    def _init_buffer(self):
        w, h = self.GetClientSize().Get()
        self._buffer = wx.EmptyBitmap(w, h)
        with draw_on_bitmap(self._buffer) as dc:
            dc.SetBackground(wx.Brush(self._background_color, wx.SOLID))
            dc.Clear()

    @event_handler
    def handle_size(self, theEvent):
        w, h = self.GetClientSize().Get()
        if w > 0 and h > 0 and (self._buffer is None or w != self._buffer.GetWidth() or h != self._buffer.GetHeight()):
            self.Parent.resize_to_fit_tree(self, (w, h))
            self._init_buffer()
            self._redraw()
        if theEvent is not None:
            theEvent.Skip()

    @event_handler
    def handle_paint(self, theEvent):
        if not self._buffer:
            return
        paint_dc = wx.PaintDC(self)
        with draw_on_bitmap(self._buffer) as source_dc:
            for dirty_rect in dirty_rects(self):
                paint_dc.Blit(dirty_rect.x, dirty_rect.y, dirty_rect.width, dirty_rect.height, source_dc, dirty_rect.x, dirty_rect.y)

    @event_handler
    def _redraw(self, dirty_rect = None):
        if dirty_rect is None:
            dirty_rect = wx.Rect(0, 0, *self._buffer.GetSize().Get())
        else:
            dirty_rect = wx.Rect(*dirty_rect.Get())
        with draw_on_bitmap(self._buffer) as dc:
            dc.SetPen(wx.Pen(self._background_color))
            dc.SetBrush(wx.Brush(self._background_color, wx.SOLID))
            dc.DrawRectangleRect(dirty_rect)
            for row, depth in self._row_state_manager.view_order_iterator():
                row.paint(self, dc, self._text_color, self._highlight_text_color, bool(self.FindFocus()), dirty_rect)

        self.RefreshRect(dirty_rect)

    @event_handler
    def handle_color_changed(self, theEvent):
        self._background_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        self._highlight_text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        self._text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        if theEvent is not None:
            self._redraw()

    @event_handler
    def GetRowSize(self):
        for row, depth in self._row_state_manager.view_order_iterator():
            if depth >= 0:
                return row.item_rect.GetSize()

        return wx.Size(18, 18)

    @event_handler
    def _dirtying_mouse_event_over_all_rows(self, f, position):
        dirty_rect = wx.Rect()
        needs_relayout = False
        for row, depth in self._row_state_manager.view_order_iterator():
            inner_dirty_rect, events = f(row, position)
            for event in events:
                if event == 'expand':
                    needs_relayout |= self._row_state_manager.expand_row(row)
                elif event == 'collapse':
                    needs_relayout |= self._row_state_manager.collapse_row(row)
                elif event == 'check':
                    dirty_rect.Union(self._row_state_manager.set_check_state_from_ui(row))
                    launcher = self.GetTopLevelParent().Parent
                    evt = IgnoreListChangedEvent(launcher)
                    wx.PostEvent(launcher, evt)
                    self.GetTopLevelParent().reload_invalid()
                elif event == 'focus':
                    dirty_rect.Union(self._row_state_manager.request_selection(row))

            dirty_rect.Union(inner_dirty_rect)

        if needs_relayout:
            self.SetClientSize(self._size_to_fit())
        elif dirty_rect.width > 0 and dirty_rect.height > 0:
            self._redraw(dirty_rect=dirty_rect)

    @event_handler
    def handle_mouse_motion(self, theEvent):
        self._dirtying_mouse_event_over_all_rows(SelectiveSyncTreeRow.mouse_hovering_over, theEvent.GetPosition())

    @event_handler
    def handle_mouse_down(self, theEvent):
        self._dirtying_mouse_event_over_all_rows(SelectiveSyncTreeRow.mouse_down_at, theEvent.GetPosition())

    @event_handler
    def handle_mouse_up(self, theEvent):
        self._dirtying_mouse_event_over_all_rows(SelectiveSyncTreeRow.mouse_up_at, theEvent.GetPosition())

    @event_handler
    def refresh_selected_item(self, theEvent):
        selection = self._row_state_manager.selection()
        if selection is not None:
            self._redraw(dirty_rect=selection.item_rect)

    @event_handler
    def handle_key_down(self, theEvent):
        keycode = theEvent.GetKeyCode()
        if keycode in (wx.WXK_DOWN, wx.WXK_UP):
            dirty_rect = self._row_state_manager.move_selection(keycode == wx.WXK_DOWN)
            if dirty_rect.width > 0 and dirty_rect.height > 0:
                selected_row = self._row_state_manager.selection()
                if selected_row is not None:
                    if selected_row.item_rect is not None:
                        self.Parent.assure_rect_revealed(selected_row.content_rect)
                self._redraw(dirty_rect=dirty_rect)
        elif keycode in (wx.WXK_RIGHT, wx.WXK_LEFT):
            selected_row = self._row_state_manager.selection()
            if selected_row is not None and selected_row.is_showing_treebutton():
                if self._row_state_manager.expand_selection(keycode == wx.WXK_RIGHT):
                    self.SetClientSize(self._size_to_fit())
        elif keycode == wx.WXK_SPACE:
            selected_row = self._row_state_manager.selection()
            if selected_row is not None and selected_row.is_showing_checkbox():
                selected_row.set_check_state(selected_row.next_check_state())
                dirty_rect = wx.Rect(*selected_row.checkbox_rect.Get())
                dirty_rect.Union(self._row_state_manager.set_check_state_from_ui(selected_row))
                launcher = self.GetTopLevelParent().Parent
                evt = IgnoreListChangedEvent(launcher)
                wx.PostEvent(launcher, evt)
                self.GetTopLevelParent().reload_invalid()
                self._redraw(dirty_rect=dirty_rect)
        else:
            theEvent.Skip()

    @event_handler
    def handle_context_menu(self, theEvent):
        if self._popped_menu is not None:
            self._popped_menu.Destroy()
            self._popped_menu = None
        win = theEvent.GetEventObject()
        pos = win.ScreenToClient(theEvent.GetPosition())
        y = pos.Get()[1]
        to_update = None
        for row, depth in self._row_state_manager.view_order_iterator():
            top = row.item_rect.position.y
            bottom = row.item_rect.position.y + row.item_rect.size.height
            if y >= top and y < bottom:
                to_update = self._row_state_manager.request_selection(row)
                try:
                    self._popped_menu = self._row_state_manager.context_menu_for_row(row)
                except Exception:
                    unhandled_exc_handler()
                    return

                break

        if to_update is not None:
            self._redraw(dirty_rect=to_update)
        if self._popped_menu is not None:
            self.PopupMenu(self._popped_menu, pos)


class ScrolledSelectiveSyncTree(wx.PyScrolledWindow):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, forest, *n, **kw):
        super(ScrolledSelectiveSyncTree, self).__init__(parent, *n, **kw)
        self._forest = forest
        self._native_render_store = NativeRenderStore()
        self._tree_delegate = TreeDelegate(self._forest, self._native_render_store)
        self._inner_tree_control = None
        self.handle_color_changed(None)
        self.Bind(wx.EVT_SYS_COLOUR_CHANGED, self.handle_color_changed)
        self._reload_tree()
        self.Bind(wx.EVT_SCROLLWIN, self.handle_scroll)

    @event_handler
    def GetRowSize(self):
        return self._inner_tree_control.GetRowSize()

    @event_handler
    def handle_scroll(self, theEvent):
        theEvent.Skip()
        wx.CallAfter(self.flush_scroll_at_maxima)

    @event_handler
    def flush_scroll_at_maxima(self):
        tcx, tcy = self._inner_tree_control.GetPosition().Get()
        sx, sy = -tcx, -tcy
        sw, sh = self.GetClientSize().Get()
        vw, vh = self.GetVirtualSize().Get()
        newx, newy = (None, None)
        if sy + sh > vh:
            newy = sh - vh
        elif sy < 0:
            newy = 0
        if sx + sw > vw:
            newx = sw - vw
        elif sx < 0:
            newx = 0
        if newx is not None or newy is not None:
            nx, ny = self._inner_tree_control.GetPosition().Get()
            nx = newx if newx is not None else nx
            ny = newy if newy is not None else ny
            self._inner_tree_control.SetPosition(wx.Point(nx, ny))

    @event_handler
    def handle_color_changed(self, theEvent):
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

    @event_handler
    def assure_rect_revealed(self, rect):
        tcx, tcy = self._inner_tree_control.GetPosition().Get()
        sx, sy = -tcx, -tcy
        sw, sh = self.GetClientSize().Get()
        vx, vy, vw, vh = rect.Get()
        vx += tcx
        vy += tcy
        unit = self._inner_tree_control.GetRowSize().Get()[1]
        target_y = None
        if vy < 0:
            target_y = (sy + vy) / unit
        elif vy + vh > sh:
            target_y = (sy + vy + vh - sh) / unit + 1
        target_x = None
        if vx < 0:
            target_x = (sx + vx) / unit
        if target_y is not None or target_x is not None:
            if target_y is None:
                target_y = sy / unit
            if target_x is None:
                target_x = sx / unit
            self.Scroll(target_x, target_y)
            self.flush_scroll_at_maxima()

    @event_handler
    def set_advanced_view(self, advanced_view):
        self._forest.set_advanced_view(advanced_view)
        self._reload_tree()

    @event_handler
    def handle_size(self, theEvent):
        size = self.GetSize()
        if size.GetWidth() > 0 and size.GetHeight() > 0:
            self._inner_tree_control.layout_for_new_parent_size()

    @event_handler
    def resize_to_fit_tree(self, tree, size):
        self.SetVirtualSize(size)
        self._unit = tree.GetRowSize().GetHeight()
        self.SetScrollRate(self._unit, self._unit)

    @event_handler
    def _reload_tree(self):
        self.Unbind(wx.EVT_SIZE)
        if self._inner_tree_control is not None:
            self._forest.clear_invalidate_ui_callback()
            self._inner_tree_control.Destroy()
            del self._inner_tree_control
        self.Scroll(0, 0)
        self._inner_tree_control = SelectiveSyncTree(self, self._tree_delegate)
        self._inner_tree_control.SetPosition(wx.Point(0, 0))
        self._forest.set_invalidate_ui_callback(message_sender(wx.CallAfter)(self._inner_tree_control.invalidate_ui_callback))
        self.Bind(wx.EVT_KEY_DOWN, self._inner_tree_control.handle_key_down)
        self.Bind(wx.EVT_CHAR, self._inner_tree_control.handle_char)
        self.handle_size(None)
        self.Bind(wx.EVT_SIZE, self.handle_size)

    def GetValue(self):
        return self._forest.current_directory_ignore_set

    def SetValue(self, value):
        pass

    Value = property(GetValue, SetValue)


class SelectiveSyncWindow(wx.Dialog):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, wx_parent, dropbox_app, take_action, initial_ignore_set, secondary = False, *n, **kw):
        self.secondary = secondary
        self.pref_controller = dropbox_app.pref_controller
        self._take_action = take_action
        self.sync_engine = dropbox_app.mbox.sync_engine if secondary else dropbox_app.sync_engine
        if platform.simple_frame_style:
            kw['style'] = platform.simple_frame_style | wx.RESIZE_BORDER
        kw['title'] = selsync_strings.window_title
        super(SelectiveSyncWindow, self).__init__(wx_parent, *n, **kw)
        platform.frame_icon(self)
        self.panel = panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        if take_action:
            initial_ignore_set = None
        self.forest = CachingLazySelectiveSyncUI(dropbox_app, self.sync_engine, dropbox_app.dropbox_url_info, use_tri_state_checks=True, initial_directory_ignore_set=initial_ignore_set)
        if self.pref_controller['selsync_advanced_view_hint']:
            self.forest.advanced_view = True
        self.info_label = wx.StaticText(panel, label=selsync_strings.info)
        button_sizer_border = platform.outer_button_border + platform.text_static_box_interior
        sizer.Add(self.info_label, border=button_sizer_border, flag=wx.ALL | wx.ALIGN_LEFT)
        self.selsync_tree = ScrolledSelectiveSyncTree(panel, self.forest, style=wx.SUNKEN_BORDER | wx.CLIP_CHILDREN)
        sizer.Add(self.selsync_tree, border=button_sizer_border, proportion=1, flag=wx.EXPAND | wx.ALL & ~wx.TOP)
        self.throbber = None
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.button_sizer, border=button_sizer_border, flag=wx.EXPAND | wx.ALL & ~wx.TOP)
        panel.SetSizer(sizer)
        bw, bh = (0, 0)
        for swapper in (self._swap_to_steady_state,):
            swapper()
            w, h = self.button_sizer.CalcMin().Get()
            bw = max(w, bw)
            bh = max(h, bh)

        bw = max(w, self.info_label.GetSize().Get()[0])
        min_w = bw + button_sizer_border * 2
        proper_w = max(min_w, wx_parent.GetSize().Get()[0] - 50)
        row_h = self.selsync_tree.GetRowSize()[1]
        min_h = button_sizer_border * 4 + bh + self.info_label.GetSize().Get()[1] + row_h * 6
        proper_h = min_h + row_h * 9
        self.SetClientSize(wx.Size(min_w, min_h))
        self.SetMinSize(self.GetSize())
        self.SetClientSize(wx.Size(proper_w, proper_h))
        self.Layout()
        self.Bind(wx.EVT_CLOSE, self.handle_close)

    @event_handler
    def reload_invalid(self):
        self.ok_button.Enable(self.forest.invalid())

    @event_handler
    def _clear_button_state(self):
        if self.throbber is not None:
            self.throbber.stop()
            self.throbber.Show(False)
            self.throbber = None
        self.button_sizer.Clear(True)

    def _same_height_buttons(self, buttons):
        h = 0
        for button in buttons:
            h = max(h, button.GetSize().GetHeight())

        for button in buttons:
            new_size = wx.Size(button.GetSize().GetWidth(), h)
            button.SetMinSize(new_size)

    @event_handler
    def _swap_to_steady_state(self):
        self._clear_button_state()
        buttons = []
        if not self.forest.advanced_view:
            self.switch_button = wx.Button(self.panel, label=selsync_strings.switch_to_advanced_view)
            self.switch_button.Bind(wx.EVT_BUTTON, self.switch_to_advanced_view)
            self.button_sizer.Add(self.switch_button, border=platform.button_horizontal_spacing * 3, flag=wx.RIGHT)
            buttons.append(self.switch_button)
        self.ok_button = wx.Button(self.panel, id=wx.ID_OK, label=selsync_strings.window_ok_button)
        self.ok_button.Bind(wx.EVT_BUTTON, self.handle_ok)
        self.button_sizer.AddStretchSpacer()
        self.button_sizer.Add(self.ok_button, border=platform.button_horizontal_spacing, flag=wx.RIGHT)
        buttons.append(self.ok_button)
        cancel_button = wx.Button(self.panel, id=wx.ID_CANCEL, label=selsync_strings.cancel_button)
        cancel_button.Bind(wx.EVT_BUTTON, self.handle_cancel)
        buttons.append(cancel_button)
        self._same_height_buttons(buttons)
        self.button_sizer.Add(cancel_button)
        self.reload_invalid()
        self.button_sizer.Layout()

    @event_handler
    def handle_ok(self, theEvent):
        if self.forest.advanced_view:
            self.pref_controller.update({'selsync_advanced_view_hint': True})
        if not self._take_action:
            TRACE('Not supposed to take action, exiting.')
            self.EndModal(0)
            return
        if wx.MessageDialog(self, self.forest.get_confirmation_message(), caption=selsync_strings.confirmation_caption, style=wx.OK | wx.CANCEL | wx.ICON_QUESTION).ShowModal() == wx.ID_OK:
            self.selsync_tree.Enable(False)
            self.start_prep_selsync()

    @event_handler
    def start_prep_selsync(self):
        self.Parent.set_busy()
        message_sender(spawn_thread_with_name('PREP_SELSYNC'), on_success=message_sender(wx.CallAfter)(self.Parent.prep_selsync_success), on_exception=message_sender(wx.CallAfter)(self.Parent.prep_selsync_failed), block=False, handle_exceptions=True, dont_post=lambda : False)(self.forest.write_changes_to_sync_engine)(self.sync_engine)
        self.EndModal(0)

    @event_handler
    def handle_cancel(self, theEvent):
        self.forest.reset()
        launcher = self.Parent
        evt = IgnoreListChangedEvent(launcher)
        wx.PostEvent(launcher, evt)
        self.EndModal(0)

    @event_handler
    def switch_to_advanced_view(self, theEvent):
        self.selsync_tree.set_advanced_view(True)
        self.switch_button.Show(False)
        self.Layout()

    @event_handler
    def handle_close(self, theEvent):
        self.EndModal(0)

    @event_handler
    def Destroy(self, *n, **kw):
        self.forest.clear_invalidate_ui_callback()
        self.forest.remove_remote_file_event_callback()
        super(SelectiveSyncWindow, self).Destroy(*n, **kw)

    def GetValue(self):
        return frozenset(self.forest.current_directory_ignore_set)

    Value = property(GetValue)


class SelectiveSyncLauncher(TransparentPanel):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, dropbox_app, has_own_borders = True, take_action = True, transparent_hack = True, font = None, hide_text = False, override_system_colors = False, secondary = False, label = None):
        super(SelectiveSyncLauncher, self).__init__(parent, transparent_hack=transparent_hack)
        self._dropbox_app = dropbox_app
        self._take_action = take_action
        self._font = font
        self._hide_text = hide_text
        self.secondary = secondary
        self.override_system_colors = override_system_colors
        self._last_value = frozenset()
        self._window = None
        if has_own_borders:
            label = label or selsync_strings.prefs_group_label
            selsync_box = wx.StaticBox(self, label=label)
            self.l_vsizer = wx.StaticBoxSizer(selsync_box, wx.VERTICAL)
        else:
            self.l_vsizer = wx.BoxSizer(wx.VERTICAL)
        self.l_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self._setup()
        self.Enable(dropbox_app.ui_kit.post_link)
        if has_own_borders:
            border = platform.radio_static_box_interior
            self.l_vsizer.AddSpacer(wx.Size(0, 5))
            flag = wx.LEFT | wx.RIGHT | wx.BOTTOM
        else:
            border = 0
            flag = 0
        self.l_vsizer.Add(self.l_hsizer, proportion=0, flag=wx.EXPAND | flag, border=border)
        self.SetSizerAndFit(self.l_vsizer)

    def on_show(self):
        if not self._hide_text:
            self.selsync_launch_label.SetLabel(selsync_strings.prefs_launch_label)
            width = self.l_hsizer.GetSize().GetWidth() - self.selsync_launch_button.GetSize().GetWidth() - platform.statictext_textctrl_horizontal_spacing
            self.selsync_launch_label.Wrap(width)
            self.l_vsizer.SetSizeHints(self)

    def Bind(self, event, handler, source = None, id = -1, id2 = -1):
        if event == wx.EVT_LEFT_DOWN and self.selsync_launch_label:
            self.selsync_launch_label.Bind(event, handler, source, id, id2)
        super(SelectiveSyncLauncher, self).Bind(event, handler, source, id, id2)

    @assert_message_queue
    def _setup(self):
        if not self._hide_text:
            self.selsync_launch_label = TransparentStaticText(self, label=selsync_strings.prefs_launch_label)
            if self._font:
                self.selsync_launch_label.SetFont(self._font)
            self.selsync_launch_label.Wrap(LAUNCH_LABEL_INITIAL_WIDTH)
            self.l_hsizer.Add(self.selsync_launch_label, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM | wx.TOP)
        else:
            self.selsync_launch_label = None
        self.selsync_launch_button = wx.Button(self, label=selsync_strings.prefs_launch_button)
        if self._font:
            self.selsync_launch_button.SetFont(self._font)
        self.selsync_launch_button.Bind(wx.EVT_BUTTON, self.handle_selsync_launch_button)
        self.l_hsizer.AddStretchSpacer()
        if not self._hide_text:
            self.l_hsizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0))
        adj = 0
        if platform == GNOME:
            adj = -1
        self.l_hsizer.Add(self.selsync_launch_button, border=platform.button_baseline_adjustment + adj, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        if self.override_system_colors:
            self.selsync_launch_button.SetBackgroundColour(Colors.white)
            self.selsync_launch_button.SetForegroundColour(Colors.black)
            if self.selsync_launch_label:
                self.selsync_launch_label.SetBackgroundColour(Colors.white)
                self.selsync_launch_label.SetForegroundColour(Colors.black)

    def sync_engine_is_valid(self, sync_engine):
        self.Enable()

    @event_handler
    def handle_selsync_launch_button(self, event):
        assert self._dropbox_app.sync_engine is not None
        assert self._dropbox_app.dropbox_url_info is not None
        self._window = SelectiveSyncWindow(self, self._dropbox_app, self._take_action, self._last_value, secondary=self.secondary)
        self._window.CenterOnParent()
        self._window.ShowModal()
        TRACE('modal dying, cleaning up')
        self._last_value = self._window.Value
        self._window.Destroy()
        self._window = None

    def GetValue(self):
        if self._window:
            return self._window.Value
        return self._last_value

    def SetValue(self, value):
        assert not self._window
        if value is None:
            return
        self._last_value = value

    Value = property(GetValue, SetValue)

    @message_sender(wx.CallAfter)
    def Enable(self, enable = True):
        self.selsync_launch_button.Enable(enable)

    @message_sender(wx.CallAfter)
    def set_busy(self):
        self.selsync_launch_button.SetLabel(selsync_strings.prefs_working_button)
        self.selsync_launch_button.Enable(False)

    @message_sender(wx.CallAfter)
    def clear_busy(self):
        self.selsync_launch_button.SetLabel(selsync_strings.prefs_launch_button)
        self.selsync_launch_button.Enable(True)

    @event_handler
    def prep_selsync_success(self, failures):
        TRACE('selective sync succeeded!')
        self.clear_busy()
        if failures:
            wx.MessageDialog(None, failed_unignores_message_from_failures(failures, self._dropbox_app.default_dropbox_path), caption=selsync_strings.unignore_error_caption, style=wx.OK | wx.ICON_ERROR).ShowModal()

    @event_handler
    def prep_selsync_failed(self, exc, exc_info):
        TRACE('selective sync failed!')
        unhandled_exc_handler(exc_info=exc_info)
        self.clear_busy()
        wx.MessageDialog(None, selsync_strings.really_bad_error_message, caption=selsync_strings.really_bad_error_caption, style=wx.OK | wx.ICON_ERROR).ShowModal()
