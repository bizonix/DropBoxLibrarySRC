#Embedded file name: ui/wxpython/location_changer.py
from __future__ import absolute_import
import os
import sys
import threading
import time
import wx
from ..common.preferences import pref_strings
from .dropbox_controls import Throbber, TransparentPanel
from .constants import Colors, GNOME, platform
import arch
from build_number import BUILD_KEY
from dropbox.globals import dropbox_globals
from dropbox.gui import message_sender, assert_message_queue, spawn_thread_with_name
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.sync_engine.move_dropbox import path_makes_invalid_dropbox_parent, path_endswith_dropbox
if sys.platform.startswith('win'):
    from dropbox.win32.version import VISTA, WINDOWS_VERSION

class DirDialog(wx.DirDialog):

    @assert_message_queue
    def __init__(self, parent, text = None, title = None, button = None, start_path = None, style = wx.DD_DEFAULT_STYLE):
        assert start_path
        kw = {'defaultPath': start_path}
        if text is not None:
            kw['message'] = text
        if style is not None:
            kw['style'] = style
        super(DirDialog, self).__init__(parent, **kw)
        if title is not None:
            self.SetTitle(title)


class MoveDropboxProgressDialog(wx.ProgressDialog):

    @assert_message_queue
    def __init__(self, parent, sync_engine):
        assert sync_engine
        try:
            self.approx_n_to_move = sync_engine.get_dropbox_file_count()
        except Exception:
            unhandled_exc_handler()
            self.approx_n_to_move = 0

        TRACE('about to move %d files' % self.approx_n_to_move)
        kw = dict(title=pref_strings.loc_changer_title_moving_dropbox, message=pref_strings.loc_changer_move_progress_determinate_t % dict(completed=self.approx_n_to_move, total=self.approx_n_to_move), maximum=self.approx_n_to_move, style=wx.PD_APP_MODAL | wx.PD_REMAINING_TIME)
        super(MoveDropboxProgressDialog, self).__init__(parent=parent, **kw)
        self.n_moved = 0
        self.last_user_update = time.time()
        self.in_update = False
        self.die_after_update = False
        self.Update(self.n_moved, pref_strings.loc_changer_move_progress_indeterminate)

    @assert_message_queue
    def Destroy(self):
        if self.in_update:
            self.die_after_update = True
        else:
            super(MoveDropboxProgressDialog, self).Destroy()

    @assert_message_queue
    def Update(self, *n, **kw):
        try:
            self.in_update = True
            super(MoveDropboxProgressDialog, self).Update(*n, **kw)
        finally:
            self.in_update = False

        if self.die_after_update:
            self.Destroy()

    @message_sender(wx.CallAfter)
    def one_file(self):
        self.n_moved += 1
        t = time.time()
        if t - self.last_user_update > 0.1:
            self.last_user_update = t
            self.Update(self.n_moved, pref_strings.loc_changer_move_progress_determinate_t % dict(completed=self.n_moved, total=self.approx_n_to_move))


EVT_DROPBOX_LOCATION_CHANGED = wx.PyEventBinder(wx.NewEventType(), 1)

class DropboxLocationChangedEvent(wx.PyCommandEvent):

    def __init__(self, win):
        super(DropboxLocationChangedEvent, self).__init__(EVT_DROPBOX_LOCATION_CHANGED.typeId, win.GetId())
        self.EventObject = win


@assert_message_queue
def request_valid_dropbox_path_from_user(dropbox_app, start_path = None, care_about_existing_dropbox = True, move = False, parent = None, secondary = False):
    if move:
        assert dropbox_app.sync_engine, 'no sync_engine?'
    if not secondary:
        default_dropbox_folder_name = dropbox_app.default_dropbox_folder_name
    else:
        default_dropbox_folder_name = dropbox_app.mbox.get_dropbox_folder_name()
    text = pref_strings.loc_changer_select_message1 + u'\n' + pref_strings.loc_changer_select_message2 % dict(folder_name=default_dropbox_folder_name)
    dlg = DirDialog(parent=parent, title=pref_strings.loc_changer_select_title, button=pref_strings.loc_changer_select_button, text=text, start_path=os.path.dirname(start_path), style=wx.DD_DEFAULT_STYLE)
    while True:
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        parent_path = dlg.GetPath()
        TRACE('Checking if requested parent path is invalid')
        invalid = path_makes_invalid_dropbox_parent(parent_path, sync_engine=dropbox_app.sync_engine, care_about_existing_dropbox=care_about_existing_dropbox, arch=dropbox_app.sync_engine.arch)
        if invalid:
            TRACE("It's invalid thanks to: %s, notifying user and relooping" % str(invalid))
            wx.MessageDialog(parent, unicode(invalid), caption='Error with selected folder', style=wx.OK | wx.ICON_ERROR).ShowModal()
        else:
            path = os.path.join(parent_path, default_dropbox_folder_name)
            if os.path.exists(path):
                if os.path.isdir(path):
                    msg = pref_strings.loc_changer_dialog_merge_question % (default_dropbox_folder_name,)
                    if wx.MessageDialog(parent, msg, caption=BUILD_KEY, style=wx.OK | wx.CANCEL | wx.ICON_QUESTION).ShowModal() != wx.ID_OK:
                        continue
                else:
                    wx.MessageDialog(parent, pref_strings.loc_changer_dialog_merge_is_file % (default_dropbox_folder_name,), caption=BUILD_KEY, style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()
                    continue
            else:
                contains_dropbox = path_endswith_dropbox(parent_path, care_about_existing_dropbox=care_about_existing_dropbox, arch=dropbox_app.sync_engine_arch)
                if contains_dropbox:
                    if wx.MessageDialog(parent, unicode(contains_dropbox), caption=BUILD_KEY, style=wx.OK | wx.CANCEL | wx.ICON_QUESTION).ShowModal() != wx.ID_OK:
                        continue
            dlg.Destroy()
            return path


class DropboxLocationChanger(TransparentPanel):

    @assert_message_queue
    def handle_button(self, theEvent):
        kw = {'start_path': self.start_location,
         'move': self.move}
        if not self.move:
            kw['care_about_existing_dropbox'] = False
            if hasattr(self, 'path_to_save'):
                kw['start_path'] = self.path_to_save
        path = request_valid_dropbox_path_from_user(self.dropbox_app, secondary=self.secondary, **kw)
        if path:
            if self.move:
                if wx.MessageDialog(self.parent, pref_strings.loc_changer_move_confirm_message % {'folder_name': path}, caption=pref_strings.loc_changer_move_confirm_caption, style=wx.OK | wx.CANCEL | wx.ICON_QUESTION).ShowModal() != wx.ID_OK:
                    return
                TRACE("It's valid, trying to move")
                if not os.path.exists(self.dropbox_app.pref_controller['dropbox_path']):
                    pass
                self.start_move(path)
            elif path:
                self.path_to_save = path
                self.locbox.SetValue(path)
                evt = DropboxLocationChangedEvent(self)
                wx.PostEvent(self.Parent, evt)

    @message_sender(wx.CallAfter, block=True)
    def do_warn(self, text, cancel = True):
        TRACE('Warning thanks to:%s, cautioning user' % text)
        style = wx.OK | wx.ICON_WARNING
        if cancel:
            style |= wx.CANCEL
        return wx.MessageDialog(self.parent, text, caption=pref_strings.loc_changer_moving_warning, style=style).ShowModal() == wx.ID_OK

    @assert_message_queue
    def start_move(self, path):
        assert self.dropbox_app.sync_engine, '%r has no sync_engine?' % self
        self.not_moving.clear()
        self.start_move_ui()
        if not self.secondary:
            message_sender(spawn_thread_with_name('MOVE'), on_success=self.finish_move, on_exception=self.finish_move_on_exception)(self.dropbox_app.sync_engine.move)(path, self.do_warn, progress_callback=self.do_progress, error_callback=self.dropbox_app.restart_and_unlink)
        else:
            self.dropbox_app.mbox.sync_engine.move_dropbox(path=path, progress_callback=self.do_progress, exception_callback=self.finish_move_on_exception, success_callback=self.finish_move, warn_external_callback=lambda *n, **kw: None)

    def finish_move_on_exception(self, exc, exc_info):
        try:
            raise exc
        except Exception:
            unhandled_exc_handler()

        self.finish_move(pref_strings.loc_changer_unexpected_problem)

    @message_sender(wx.CallAfter)
    def finish_move(self, ret):
        self.stop_move_ui()
        self.not_moving.set()
        if ret:
            TRACE('Move failed, these codes could be ugly so not showing the user unless they are a dev: %s' % ret)
            wx.MessageDialog(self.parent, ret, caption=pref_strings.loc_changer_error_moving, style=wx.OK | wx.ICON_ERROR).ShowModal()
        else:
            TRACE('Move succeeded, breaking')
        if not self.secondary:
            new_loc = self.dropbox_app.pref_controller['dropbox_path']
        else:
            new_loc = self.dropbox_app.mbox.get_dropbox_location()
        self.locbox.SetValue(new_loc)

    @assert_message_queue
    def start_move_ui(self):
        self.parent.parent.custom_enable(False)
        move_w = self.move_button.GetSize().GetWidth()
        self.move_button.Show(False)
        if not hasattr(self, 'throbber'):
            self.throbber = Throbber(self.parent)
        self.l_hsizer.Clear()
        self.l_hsizer.Add(self.locbox, border=platform.textctrl_baseline_adjustment, proportion=1, flag=wx.EXPAND | wx.ALIGN_BOTTOM | wx.BOTTOM)
        self.l_hsizer.AddSpacer(wx.Size(platform.textctrl_button_horizontal_spacing, 0))
        self.l_hsizer.Add(self.throbber, border=(move_w - self.throbber.GetSize().GetWidth()) / 2, flag=wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.throbber.Show(True)
        self.l_hsizer.Layout()
        self.throbber.start()
        self.progress_dialog = MoveDropboxProgressDialog(self.parent, self.dropbox_app.sync_engine)
        self.progress_dialog.Show(False)

    @message_sender(wx.CallAfter)
    def do_progress(self):
        self.progress_dialog.one_file()
        self.progress_dialog.Show(True)

    @assert_message_queue
    def stop_move_ui(self):
        self.throbber.stop()
        self.throbber.Show(False)
        self.l_hsizer.Clear()
        self.l_hsizer.Add(self.locbox, border=platform.textctrl_baseline_adjustment, proportion=1, flag=wx.EXPAND | wx.ALIGN_BOTTOM | wx.BOTTOM)
        self.l_hsizer.AddSpacer(wx.Size(platform.textctrl_button_horizontal_spacing, 0))
        self.l_hsizer.Add(self.move_button, border=platform.button_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        self.move_button.Show(True)
        self.l_hsizer.Layout()
        self.parent.parent.custom_enable(True)
        self.throbber.reset()
        if self.progress_dialog:
            self.progress_dialog.Show(False)
            self.progress_dialog.Destroy()
            self.progress_dialog = None

    @assert_message_queue
    def on_show(self):
        self.Enable(not self.move or 'email' in dropbox_globals)
        self.locbox.SetValue(self.dropbox_app.pref_controller['dropbox_path'])

    @assert_message_queue
    def Enable(self, enable = True):
        self.move_button.Enable(enable)

    @assert_message_queue
    def Disable(self):
        self._move_button.Enable(False)

    @assert_message_queue
    def GetValue(self):
        return self.locbox.GetValue()

    def SetValue(self, value):
        if value is not None:
            self.locbox.SetValue(value)

    Value = property(GetValue, SetValue)

    def SetFont(self, font):
        self.locbox.SetFont(font)
        self.move_button.SetFont(font)

    @assert_message_queue
    def __init__(self, parent, dropbox_app, move = True, has_own_borders = True, transparent_hack = True, font = None, override_system_colors = False, secondary = False, label = None):
        super(DropboxLocationChanger, self).__init__(parent, transparent_hack=transparent_hack)
        self.move = move
        self.parent = parent
        self.has_own_borders = has_own_borders
        self.dropbox_app = dropbox_app
        self.not_moving = threading.Event()
        self.not_moving.set()
        self.override_system_colors = override_system_colors
        self.secondary = secondary
        if self.has_own_borders:
            label = label or pref_strings.loc_changer_label
            self.l_box = wx.StaticBox(self, label=label)
            self.l_vsizer = wx.StaticBoxSizer(self.l_box, wx.VERTICAL)
        else:
            self.l_vsizer = wx.BoxSizer(wx.VERTICAL)
        self.l_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        if not secondary:
            self.start_location = self.dropbox_app.pref_controller['dropbox_path']
        else:
            self.start_location = self.dropbox_app.mbox.get_dropbox_location()
        self.locbox = wx.TextCtrl(self, value=self.start_location)
        if font:
            self.locbox.Font = font
        self.locbox.Enable(False)
        self.move_button = wx.Button(self, label=pref_strings.loc_changer_move_dotdotdot if move else pref_strings.loc_changer_change_dotdotdot)
        if font:
            self.move_button.Font = font
        self.move_button.Bind(wx.EVT_BUTTON, self.handle_button)
        if self.move:
            self.Enable(dropbox_app.ui_kit.post_link)
        if self.override_system_colors:
            self.move_button.SetBackgroundColour(Colors.white)
            self.move_button.SetForegroundColour(Colors.black)
            self.locbox.SetBackgroundColour(Colors.white)
            self.locbox.SetForegroundColour(Colors.black)
        if platform == GNOME:
            textctrl_border = platform.textctrl_baseline_adjustment
            button_border = platform.button_baseline_adjustment
            our_align = wx.BOTTOM
        else:
            textctrl_border = 2
            if sys.platform.startswith('win') and WINDOWS_VERSION >= VISTA:
                textctrl_border = 1
            button_border = 0
            our_align = wx.TOP
        self.l_hsizer.Add(self.locbox, border=textctrl_border, proportion=1, flag=wx.EXPAND | wx.ALIGN_BOTTOM | our_align)
        self.l_hsizer.AddSpacer(wx.Size(platform.textctrl_button_horizontal_spacing, 0))
        self.l_hsizer.Add(self.move_button, border=button_border, flag=wx.ALIGN_BOTTOM | our_align)
        b = platform.radio_static_box_interior if self.has_own_borders else 0
        self.l_vsizer.Add(self.l_hsizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=b)
        self.SetSizerAndFit(self.l_vsizer)
        self.progress_dialog = None
