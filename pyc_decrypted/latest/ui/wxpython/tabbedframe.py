#Embedded file name: ui/wxpython/tabbedframe.py
from __future__ import absolute_import
import wx
import sys
from .dropbox_controls import ButtonInfo, ColorPanel, BPArt
from .constants import platform, Win32, GNOME, REVERT, SAVE, CLOSE, SAVE_AND_CLOSE, HELP, FLEX_SPACE, FANCY_HELP
from .static_link_text import StaticLinkText
import ui.images
from dropbox.gui import message_sender, assert_message_queue, event_handler
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from ..common.preferences import pref_strings
from ..common.misc import MiscStrings
if sys.platform.startswith('win'):
    from dropbox.win32.version import WIN7, WINDOWS_VERSION
if platform == GNOME:
    FORCE_PANEL_WIDTH = 475
else:
    FORCE_PANEL_WIDTH = -1

class InvalidEntryException(Exception):
    pass


class DropboxTabbedFrame(platform.frame_t):
    PANELS = None
    PANEL_NAME_TO_TYPE = None
    DEFAULT_PANEL = None
    first_show = True
    want_toolbar = True
    want_buttons = True
    showing = False

    @message_sender(wx.CallAfter)
    def refresh_panel(self, panel_name):
        if self.showing:
            if self.PANEL_NAME_TO_TYPE:
                try:
                    panel = self.all_panels[self.PANEL_NAME_TO_TYPE[panel_name]]
                    panel.read(self.dropbox_app.pref_controller.get_unlocked())
                    panel.Layout()
                    self.Layout()
                except Exception:
                    unhandled_exc_handler()

    @message_sender(wx.CallAfter)
    def show_user(self, panel_t = None):
        if not self.showing:
            self.read(self.dropbox_app.pref_controller.get_unlocked())
        self.panel.Layout()
        self.panel.Fit()
        self.Layout()
        self.Fit()
        if panel_t:
            if platform.use_notebook:
                self.notebook.SetSelection(self.PANELS.index(panel_t))
            else:
                self.panel_swapper_factory(panel_t)(None)
            to_show = panel_t
        else:
            to_show = self.current_panel_t
        if to_show not in self.all_panels:
            report_bad_assumption('Panel is not in self.all_panels. panel = %r, all_panels = %r', to_show, self.all_panels)
        self.all_panels[to_show].on_show()
        self.switch_help_url()
        if self.first_show:
            self.CenterOnScreen()
            self.first_show = False
        self.pre_show()
        self.Raise()

    @event_handler
    def pre_show(self):
        self.Show()
        self.showing = True

    @event_handler
    def hide_user(self):
        self.showing = False
        self.Show(False)
        self.post_hide()

    def post_hide(self):
        pass

    @event_handler
    def custom_enable(self, ability = True):
        if not hasattr(self, 'dont_change'):
            self.dont_change = []
            self.last_ability = ability
        if self.dont_change:
            if self.last_ability == ability:
                return
            self.last_ability = ability
        try_to_change = list(self.Children)
        while try_to_change:
            current = try_to_change.pop()
            if isinstance(current, wx.Panel):
                try_to_change.extend(current.Children)
            elif current not in self.dont_change:
                if not current.Enable(ability):
                    self.dont_change.append(current)
            else:
                self.dont_change.remove(current)

        if not self.dont_change:
            del self.dont_change

    def switch_help_url(self):
        pass

    def save(self, theEvent):
        pass

    def help(self, theEvent):
        pass

    @event_handler
    def save_and_close(self, theEvent):
        try:
            self.save(theEvent)
        except Exception:
            unhandled_exc_handler()
        else:
            self.close(theEvent)

    @event_handler
    def close(self, theEvent):
        self.hide_user()

    def read(self, pref_state):
        pass

    @event_handler
    def revert(self, theEvent):
        self.read(self.dropbox_app.pref_controller.get_unlocked())

    @event_handler
    def invalidate(self, theEvent, ability = True):
        for button in self.invalid_buttons:
            button.Enable(ability)

        self.Refresh()

    def panel_swapper_factory(self, panel_t):

        @assert_message_queue
        def swapper(theEvent):
            if not platform.use_native_toolbar:
                [ b.SetToggled(b == self.buttons[panel_t]) for b in self.buttons.values() ]
                [ b.SetStatus('Pressed' if b == self.buttons[panel_t] else 'Normal') for b in self.buttons.values() ]
            if panel_t == self.current_panel_t:
                return
            self.swap_sizer.Replace(self.all_panels[self.current_panel_t], self.all_panels[panel_t])
            [ self.all_panels[p_t].Show(p_t == panel_t) for p_t in self.all_panels ]
            self.all_panels[panel_t].on_show()
            self.resize_for_panel(panel_t)

        return swapper

    @assert_message_queue
    def resize_for_panel(self, panel_t):
        assert panel_t in self.PANELS
        if self.resize_sizer:
            self.update_resize_sizer()
        self.current_panel_t = panel_t
        self.switch_help_url()
        self.re_layout()

    class animator(object):

        def __init__(self, frame):
            self.panel = frame.panel
            self.swap_panel = frame.swap_panel
            self.daddy_swap = frame.daddy_swap
            self.frame = frame
            self.timer = wx.Timer(self.frame)
            current_height = self.frame.all_panels[self.frame.current_panel_t].border.GetMinSize().GetHeight()
            new_height = self.frame.all_panels[self.frame.next_panel_t].border.GetMinSize().GetHeight()
            total_height_diff = new_height - current_height
            self.step_size = total_height_diff / 10
            self.need_extra_pix = total_height_diff - self.step_size * 10
            self.frame.Bind(wx.EVT_TIMER, self, self.timer)
            self.frame.resize_sizer.Clear(True)
            if total_height_diff < 0:
                self.frame.swap_sizer.Replace(self.frame.all_panels[self.frame.current_panel_t], self.frame.all_panels[self.frame.next_panel_t])
                [ self.frame.all_panels[p_t].Show(p_t == self.frame.next_panel_t) for p_t in self.frame.all_panels ]
                self.frame.resize_sizer.AddSpacer(wx.Size(self.frame.biggest_width_needed, -total_height_diff))
            else:
                self.frame.resize_sizer.AddSpacer(wx.Size(self.frame.biggest_width_needed, 0))
            self.frame.last_panel_t = self.frame.current_panel_t
            self.frame.current_panel_t = self.frame.next_panel_t
            self.total_height_diff = total_height_diff
            self.panel.Layout()
            self.panel.Fit()
            self.frame.Layout()
            self.frame.Fit()

        def start(self):
            self.timer.Start(10)

        def __call__(self, theEvent):
            height = self.frame.resize_sizer.GetSize()[1]
            next_height = height + self.step_size
            if self.need_extra_pix != 0:
                adjust = 1 if self.need_extra_pix > 0 else -1
                next_height += adjust
                self.need_extra_pix -= adjust
            if self.step_size > 0 and next_height == self.total_height_diff or self.step_size < 0 and next_height == 0:
                if self.step_size > 0:
                    self.frame.swap_sizer.Replace(self.frame.all_panels[self.frame.last_panel_t], self.frame.all_panels[self.frame.current_panel_t])
                self.frame.resize_sizer.Clear(True)
                self.frame.resize_sizer.AddSpacer(wx.Size(self.frame.biggest_width_needed, 0))
                [ self.frame.all_panels[p_t].Show(p_t == self.frame.current_panel_t) for p_t in self.frame.all_panels ]
                self.timer.Stop()
                del self.timer
            else:
                self.frame.resize_sizer.Clear(True)
                self.frame.resize_sizer.AddSpacer(wx.Size(self.frame.biggest_width_needed, next_height))
            self.panel.Layout()
            self.panel.Fit()
            self.frame.Layout()
            self.frame.Fit()

    def animating_panel_swapper_factory(self, panel_t):

        def swapper(theEvent):
            self.next_panel_t = panel_t
            if not platform.use_native_toolbar:
                [ b.SetToggled(b == self.buttons[panel_t]) for b in self.buttons.values() ]
                [ b.SetStatus('Pressed' if b == self.buttons[panel_t] else 'Normal') for b in self.buttons.values() ]
            if panel_t == self.current_panel_t:
                return
            self.animator(self).start()

        return swapper

    def post_init(self):
        pass

    @event_handler
    def make_button_panel(self):
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        from wx.lib.buttonpanel import ButtonPanel, BP_BUTTONTEXT_ALIGN_BOTTOM, BP_USE_GRADIENT
        kw = {'color': wx.Color(255, 255, 255)}
        if platform == GNOME:
            kw['style'] = wx.BORDER_SUNKEN
        sunken_panel = ColorPanel(self.panel, **kw)
        button_panel = self.button_panel = ButtonPanel(sunken_panel, style=BP_USE_GRADIENT)
        button_panel.SetBPArt(BPArt(button_panel._nStyle, button_panel))
        top_sizer.Add(self.button_panel, proportion=0, flag=wx.ALIGN_CENTER)
        top_sizer.AddSpacer(wx.Size(0, 0), proportion=1)
        self.buttons = {}
        for p in self.PANELS:
            thisb = ButtonInfo(button_panel, bmp=p.icon(), text=p.shortname(), kind=wx.ITEM_CHECK)
            thisb.SetTextAlignment(BP_BUTTONTEXT_ALIGN_BOTTOM)
            self.Bind(wx.EVT_BUTTON, (self.animating_panel_swapper_factory if platform.animate_on_swap else self.panel_swapper_factory)(p), thisb)
            self.buttons[p] = thisb
            button_panel.AddButton(thisb)

        button_panel.DoLayout()
        sunken_panel.SetSizerAndFit(top_sizer)
        button_panel_flags = wx.EXPAND if platform is not GNOME else wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT
        self.panel_sizer.Add(sunken_panel, proportion=0, border=platform.swap_panel_border, flag=button_panel_flags)
        if platform is Win32:
            self.panel_sizer.Add(wx.StaticLine(self.panel), flag=wx.EXPAND)

    @event_handler
    def make_toolbar_panel(self):
        self.toolbar = toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT | wx.TB_TEXT | wx.TB_HORZ_LAYOUT)
        w, h = (0, 0)
        self.CreateStatusBar()
        self.buttons = {}
        for p in self.PANELS:
            tool_id = wx.NewId()
            self.buttons[p] = toolbar.AddLabelTool(id=tool_id, label=p.shortname(), bitmap=p.icon())
            w = max(w, p.icon().GetSize().GetWidth())
            h = max(w, p.icon().GetSize().GetHeight())
            self.Bind(wx.EVT_TOOL, (self.animating_panel_swapper_factory if platform.animate_on_swap else self.panel_swapper_factory)(p), id=tool_id)
            toolbar.AddSeparator()

        toolbar.SetToolBitmapSize(wx.Size(w, h))
        toolbar.Realize()

    def handle_notebook_page_changing(self, theEvent):
        self.notebook.GetPage(theEvent.GetSelection()).GetChildren()[0].on_show()

    def handle_notebook_page_changed(self, theEvent):
        self.current_panel_t = type(self.notebook.GetPage(theEvent.GetSelection()).GetChildren()[0])
        self.switch_help_url()

    @event_handler
    def handle_notebook_keydown(self, theEvent):
        try:
            self.notebook.GetCurrentPage().GetChildren()[0].on_keydown(theEvent)
        except AttributeError:
            TRACE("%s didn't have on_keydown" % self.notebook.GetCurrentPage().GetChildren[0])

    @event_handler
    def handle_notebook_keyup(self, theEvent):
        try:
            self.notebook.GetCurrentPage().GetChildren()[0].on_keyup(theEvent)
        except AttributeError:
            TRACE("%s didn't have on_keyup" % self.notebook.GetCurrentPage().GetChildren()[0])

    @assert_message_queue
    @event_handler
    def make_notebook(self):
        self.notebook = wx.Notebook(self.panel)
        self.all_panels = {}
        self.biggest_width_needed = 0
        self.biggest_height_needed = 0
        for panel_t in self.PANELS:
            border_panel = wx.Panel(self.notebook)
            border_panel_sizer = wx.BoxSizer(wx.VERTICAL)
            self.all_panels[panel_t] = p = panel_t(border_panel, self, self.dropbox_app, has_own_borders=False)
            self.biggest_width_needed = max(self.biggest_width_needed, p.GetBestSize().GetWidth())
            self.biggest_height_needed = max(self.biggest_height_needed, p.GetBestSize().GetHeight())
            border_panel_sizer.Add(p, proportion=1, border=platform.notebook_panel_border, flag=wx.EXPAND | wx.ALL)
            border_panel.SetSizer(border_panel_sizer)
            if p.has_content:
                self.notebook.AddPage(border_panel, p.shortname())

        self.current_panel_t = self.DEFAULT_PANEL
        for i in range(self.notebook.GetPageCount()):
            if type(self.notebook.GetPage(i)) == self.DEFAULT_PANEL:
                self.notebook.ChangeSelection(i)
                break

        self.panel_sizer.Add(self.notebook, proportion=0, flag=wx.EXPAND | wx.ALL, border=platform.outer_notebook_border)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.handle_notebook_page_changing)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.handle_notebook_page_changed)
        self.notebook.Bind(wx.EVT_KEY_DOWN, self.handle_notebook_keydown)
        self.notebook.Bind(wx.EVT_KEY_UP, self.handle_notebook_keyup)

    def setup(self):
        pass

    @event_handler
    def __init__(self, parent, dropbox_app, *n, **kw):
        kw = self.setup(kw)
        if platform.simple_frame_style:
            kw['style'] = platform.simple_frame_style
        atable_ext = kw.pop('atable_extensions', [])
        super(DropboxTabbedFrame, self).__init__(parent, *n, **kw)
        platform.native_behavior(self, atable_extensions=atable_ext)
        self.dropbox_app = dropbox_app
        platform.frame_icon(self)
        self.panel = wx.Panel(self)
        self.panel.SetFont(platform.get_themed_font(self.panel))
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.resize_sizer = None
        self.make_notebook() if platform.use_notebook else self.make_button_or_toolbar_panel_and_friends()
        self.help_link = None
        self.make_save_buttons()
        self.Bind(wx.EVT_CLOSE, self.close)
        self.post_init()
        self.panel.SetSizer(self.panel_sizer)
        self.re_layout()
        if self.resize_sizer:
            self.update_biggest_dimensions()
            self.update_resize_sizer()

    @event_handler
    def re_layout(self):
        self.panel.Layout()
        self.panel.Fit()
        self.Layout()
        self.Fit()

    @event_handler
    def update_biggest_dimensions(self, recompute_height = True):

        def compute_biggest_dimensions():
            self.biggest_width_needed = 0
            self.biggest_height_needed = 0
            for panel_t in self.PANELS:
                p = self.all_panels[panel_t]
                size = p.GetBestSize()
                self.biggest_width_needed = max(self.biggest_width_needed, size.GetWidth())
                self.biggest_height_needed = max(self.biggest_height_needed, size.GetHeight())

        compute_biggest_dimensions()

        def replace_panel(current_t, replacement_t):
            self.swap_sizer.Replace(self.all_panels[current_t], self.all_panels[replacement_t])
            self.all_panels[replacement_t].Show()
            self.all_panels[replacement_t].on_show()
            self.swap_sizer.Layout()

        if recompute_height and not platform.animate_on_swap:
            last_panel_t = self.current_panel_t
            for panel_t in self.all_panels:
                replace_panel(last_panel_t, panel_t)
                self.all_panels[panel_t].Hide()
                last_panel_t = panel_t

            replace_panel(last_panel_t, self.current_panel_t)
            compute_biggest_dimensions()

    @event_handler
    def update_resize_sizer(self):
        self.resize_sizer.Clear(True)
        width = self.biggest_width_needed
        height = 0 if platform.animate_on_swap else self.biggest_height_needed - self.swap_sizer.GetMinSize().GetHeight()
        self.resize_sizer.AddSpacer(wx.Size(width, height))

    @event_handler
    def make_button_or_toolbar_panel_and_friends(self):
        if self.want_toolbar:
            self.make_toolbar_panel() if platform.use_native_toolbar else self.make_button_panel()
        self.all_panels = {}
        self.swap_panel = wx.Panel(self.panel)
        for panel_t in self.PANELS:
            self.all_panels[panel_t] = panel_t(self.swap_panel, self, self.dropbox_app, has_own_borders=True)

        self.daddy_swap = wx.BoxSizer(wx.VERTICAL)
        self.swap_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.daddy_swap.Add(self.swap_sizer, proportion=1, flag=wx.EXPAND | wx.TOP, border=platform.swap_panel_border)
        self.swap_sizer.Add(self.all_panels[self.DEFAULT_PANEL], proportion=1, flag=wx.EXPAND | wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border=platform.swap_panel_border)
        self.current_panel_t = self.DEFAULT_PANEL
        if self.want_toolbar and not platform.use_native_toolbar:
            self.buttons[self.DEFAULT_PANEL].SetStatus('Pressed')
            self.buttons[self.DEFAULT_PANEL].SetToggled(True)
        for panel_t in self.all_panels:
            self.all_panels[panel_t].Show(panel_t == self.DEFAULT_PANEL)

        self.swap_panel.SetSizer(self.daddy_swap)
        self.swap_panel.Layout()
        self.panel_sizer.Add(self.swap_panel, proportion=0, flag=wx.EXPAND | wx.ALIGN_CENTER)
        self.resize_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel_sizer.Add(self.resize_sizer, proportion=0, flag=wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ALIGN_CENTER, border=platform.swap_panel_border)

    def make_save_buttons(self):
        save_sizer = wx.FlexGridSizer(cols=len(platform.button_order))
        self.invalid_buttons = []
        wx_buttons = []
        max_height = 0
        if self.want_buttons:
            localized_button_labels = {wx.ID_OK: MiscStrings.ok_button,
             wx.ID_CANCEL: MiscStrings.cancel_button,
             wx.ID_APPLY: MiscStrings.apply_button,
             wx.ID_HELP: pref_strings.help_label,
             wx.ID_CLOSE: MiscStrings.close_button}
            for i, button in enumerate(platform.button_order):
                if button == FLEX_SPACE:
                    save_sizer.AddSpacer(wx.Size(0, 0))
                    save_sizer.AddGrowableCol(i)
                    continue
                if button == FANCY_HELP:
                    help_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    help_image = wx.StaticBitmap(self.panel, bitmap=ui.images.wximages.Help.GetBitmap())
                    help_sizer.Add(help_image, border=platform.checkbox_staticlinktext_horizontal_spacing, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
                    self.help_link = StaticLinkText(self.panel, label=u'<a href="%s">%s</a>' % ('http://halp', pref_strings.help_label))
                    self.help_link.SetBackgroundColour(self.panel.GetBackgroundColour())
                    help_sizer.Add(self.help_link, flag=wx.ALIGN_CENTER_VERTICAL)
                    extra_win7_border = 0
                    if platform == Win32 and WINDOWS_VERSION >= WIN7:
                        extra_win7_border = 1
                    save_sizer.Add(help_sizer, flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP, border=extra_win7_border)
                    continue
                elif type(button) == str:
                    wx_button = wx.Button(self.panel, label=button)
                elif type(button) == int:
                    try:
                        wx_button = wx.Button(self.panel, label=localized_button_labels[button])
                    except KeyError:
                        unhandled_exc_handler()
                        wx_button = wx.Button(self.panel, id=button)

                wx_buttons.append(wx_button)
                max_height = max(max_height, wx_button.GetBestSize().GetHeight())
                if platform.buttons[button] not in [HELP, CLOSE, SAVE_AND_CLOSE]:
                    self.invalid_buttons.append(wx_button)
                if platform.buttons[button] == SAVE:
                    self.Bind(wx.EVT_BUTTON, self.save, wx_button)
                elif platform.buttons[button] == REVERT:
                    self.Bind(wx.EVT_BUTTON, self.revert, wx_button)
                elif platform.buttons[button] == CLOSE:
                    self.Bind(wx.EVT_BUTTON, self.close, wx_button)
                elif platform.buttons[button] == SAVE_AND_CLOSE:
                    self.Bind(wx.EVT_BUTTON, self.save_and_close, wx_button)
                elif platform.buttons[button] == HELP:
                    self.Bind(wx.EVT_BUTTON, self.help, wx_button)
                if button == platform.default_button:
                    wx_button.SetDefault()
                save_sizer.Add(wx_button, flag=wx.LEFT, border=platform.button_horizontal_spacing)

            for b in wx_buttons:
                b.SetMinSize(wx.Size(-1, max_height))

        self.panel_sizer.Add(save_sizer, flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT, border=platform.outer_button_border)
        self.panel_sizer.Layout()


class DropboxTabPanel(wx.Panel):

    def invalidate(self, theEvent, ability = True):
        self.parent.invalidate(theEvent, ability)

    @assert_message_queue
    def __init__(self, wx_parent, parent, dropbox_app):
        super(DropboxTabPanel, self).__init__(wx_parent)
        self.parent = parent
        self.dropbox_app = dropbox_app
        self.has_content = False
        platform.native_behavior(self, close_function=self.parent.close)
        self.SetMinSize(wx.Size(FORCE_PANEL_WIDTH, -1))

    def on_secondary_link(self, linked):
        pass

    def pre_show(self, frame):
        frame.Show(True)

    def on_show(self):
        pass

    def on_keydown(self, theEvent):
        theEvent.Skip()

    def on_keyup(self, theEvent):
        theEvent.Skip()

    def SetSizer(self, border):
        super(DropboxTabPanel, self).SetSizer(border)
        TRACE('Preferences panel Sizer children count:%r, panel:%r', len(border.GetChildren()), self)
        self.has_content = len(border.GetChildren())

    def SetSizerAndFit(self, border):
        super(DropboxTabPanel, self).SetSizerAndFit(border)
        TRACE('Preferences panelSizer count:%r, children panel:%r', len(border.GetChildren()), self)
        self.has_content = len(border.GetChildren())
