#Embedded file name: ui/wxpython/preferences.py
from __future__ import absolute_import
import itertools
import functools
import sys
import wx
from build_number import VERSION
import arch
from dropbox.features import feature_enabled
from dropbox.globals import dropbox_globals
from dropbox.gui import assert_message_queue, event_handler, message_sender, spawn_thread_with_name
import dropbox.i18n
from dropbox.preferences import NO_PROXY, AUTO_PROXY, MANUAL_PROXY, OPT_BUBBLES, OPT_LANG, OPT_P2P, OPT_STARTUP, HTTP, SOCKS4, SOCKS5
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.client.screenshots import ScreenshotsController
from ui.wxpython.screenshots import ScreenshotsSelector
import ui.images
from ..common.preferences import ValidPort, ValidBandwidth, pref_strings, change_client_language, PanelNames
from ..common.selective_sync import selsync_strings
from .camera import CameraUploadLauncher, PhotoImportLauncher
from .constants import platform, GNOME
from .dropbox_controls import TypeBox, SpinTypeBox, Throbber
from .location_changer import DropboxLocationChanger
from .selective_sync import SelectiveSyncLauncher
from .static_link_text import StaticLinkText
from .tabbedframe import DropboxTabbedFrame, InvalidEntryException, DropboxTabPanel
if sys.platform.startswith('win'):
    from dropbox.win32.version import VISTA, WINDOWS_VERSION

class ProxySettingsPanel(DropboxTabPanel):

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsNetwork.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.proxy_tab_label

    @staticmethod
    def help_index():
        return 'proxies'

    @event_handler
    def read(self, state):
        if state['proxy_mode'] == NO_PROXY:
            self.rb[0].SetValue(True)
        elif state['proxy_mode'] == AUTO_PROXY:
            self.rb[1].SetValue(True)
        else:
            self.rb[2].SetValue(True)
        self.proxy_type_choice.SetStringSelection(state['proxy_type'])
        self.server_text.SetValue(state['proxy_server'])
        self.port_nsbox.SetValue(state['proxy_port'])
        self.auth_req.SetValue(state['proxy_requires_auth'])
        self.user_text.SetValue(state['proxy_username'])
        self.pass_text.SetValue(state['proxy_password'])
        self.handle_proxy_choice(None)
        self.handle_prox_type_choice(None)

    @event_handler
    def save(self, theEvent):
        state = {}
        if self.rb[0].GetValue():
            state['proxy_mode'] = NO_PROXY
        elif self.rb[1].GetValue():
            state['proxy_mode'] = AUTO_PROXY
        else:
            state['proxy_mode'] = MANUAL_PROXY
        state['proxy_type'] = self.proxy_type_choice.GetStringSelection()
        state['proxy_server'] = self.server_text.GetValue()
        try:
            state['proxy_port'] = self.port_nsbox.GetValue()
        except TypeBox.EntryErrors:
            raise InvalidEntryException(self.__class__, pref_strings.proxy_port_error)

        state['proxy_requires_auth'] = self.auth_req.GetValue()
        state['proxy_username'] = self.user_text.GetValue()
        state['proxy_password'] = self.pass_text.GetValue()
        return state

    @event_handler
    def handle_proxy_choice(self, theEvent):
        for win in [self.proxlbl,
         self.proxy_type_choice,
         self.slbl,
         self.server_text,
         self.port_nsbox,
         self.auth_req,
         self.ulbl,
         self.passlbl,
         self.user_text,
         self.pass_text]:
            win.Enable(self.rb[2].GetValue())

        self.handle_prox_type_choice(theEvent)

    @event_handler
    def handle_prox_type_choice(self, theEvent):
        for win in [self.auth_req,
         self.ulbl,
         self.passlbl,
         self.user_text,
         self.pass_text]:
            win.Enable(self.rb[2].GetValue() and self.proxy_type_choice.GetStringSelection() in (HTTP, SOCKS5))

        self.handle_auth_checkbox(theEvent)

    @event_handler
    def handle_auth_checkbox(self, theEvent):
        for win in [self.ulbl,
         self.passlbl,
         self.user_text,
         self.pass_text]:
            win.Enable(self.auth_req.GetValue() and self.rb[2].GetValue() and self.proxy_type_choice.GetStringSelection() in (HTTP, SOCKS5))

        self.invalidate(theEvent)

    @event_handler
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(ProxySettingsPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.has_own_borders = has_own_borders
        border = self.border = wx.BoxSizer(wx.VERTICAL)
        if self.has_own_borders:
            proxy_box = wx.StaticBox(self)
            pb_sizer = wx.StaticBoxSizer(proxy_box, wx.VERTICAL)
            TypeBox_t = TypeBox
        else:
            TypeBox_t = SpinTypeBox
        self.up_self = up_self = wx.Panel(self)
        self.rb = rb = [wx.RadioButton(up_self, label=pref_strings.no_proxy_choice, style=wx.RB_GROUP), wx.RadioButton(up_self, label=pref_strings.auto_proxy_choice), wx.RadioButton(up_self, label=pref_strings.manual_proxy_choice)]
        windows_wx_bug_workaround = wx.RadioButton(up_self, style=wx.RB_GROUP)
        windows_wx_bug_workaround.Show(False)

        def cell():
            up_sizer.AddSpacer(wx.Size(0, 0))

        up_sizer = wx.FlexGridSizer(cols=5)
        up_self.SetSizer(up_sizer)
        self.proxy_settings_lbl = proxy_settings_lbl = wx.StaticText(up_self, label=pref_strings.proxy_settings_label)
        up_sizer.AddStretchSpacer()
        up_sizer.Add(proxy_settings_lbl, border=platform.statictext_baseline_adjustment_to_match_radio, flag=wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT | wx.BOTTOM)
        up_sizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0))
        up_sizer.Add(rb[0], flag=wx.LEFT | wx.ALIGN_BOTTOM)
        up_sizer.AddStretchSpacer()
        up_sizer.AddSpacer(wx.Size(0, platform.radio_group_spacer))
        cell()
        cell()
        cell()
        cell()
        cell()
        cell()
        cell()
        up_sizer.Add(rb[1], flag=wx.LEFT)
        cell()
        up_sizer.AddSpacer(wx.Size(0, platform.radio_group_spacer))
        cell()
        cell()
        cell()
        cell()
        cell()
        cell()
        cell()
        up_sizer.Add(rb[2], flag=wx.LEFT, border=0)
        cell()
        up_sizer.AddSpacer(wx.Size(0, platform.radio_group_spacer))
        cell()
        cell()
        cell()
        cell()
        self.proxlbl = proxlbl = wx.StaticText(up_self, label=pref_strings.proxy_type_label)
        self.proxy_type_choice = proxy_type_choice = wx.Choice(up_self, choices=[HTTP, SOCKS4, SOCKS5])
        proxy_type_choice.Bind(wx.EVT_CHOICE, self.handle_prox_type_choice)
        cell()
        up_sizer.Add(proxlbl, border=platform.statictext_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        cell()
        up_sizer.Add(proxy_type_choice, border=platform.choice_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM)
        cell()
        up_sizer.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        cell()
        cell()
        cell()
        cell()
        if platform == GNOME:
            port_size = 60
        else:
            port_size = 48
        self.slbl = slbl = wx.StaticText(up_self, label=pref_strings.proxy_server_label)
        self.server_text = server_text = wx.TextCtrl(up_self, value='', size=wx.Size(platform.username_textctrl_width, -1))
        self.port_nsbox = TypeBox_t(up_self, ValidPort, size=wx.Size(port_size, -1), on_text=[self.invalidate])
        server_text_and_more_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        server_text_and_more_hsizer.Add(server_text)
        server_text_and_more_hsizer.AddSpacer(wx.Size(platform.textctrl_statictext_horizontal_spacing / 2, 0))
        server_text_and_more_hsizer.Add(wx.StaticText(up_self, label=':'), border=1, flag=wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL)
        server_text_and_more_hsizer.AddSpacer(wx.Size(platform.textctrl_statictext_horizontal_spacing / 2, 0))
        server_text_and_more_hsizer.Add(self.port_nsbox)
        cell()
        up_sizer.Add(slbl, border=platform.statictext_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        cell()
        up_sizer.Add(server_text_and_more_hsizer, border=platform.textctrl_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM)
        cell()
        self.auth_req = auth_req = wx.CheckBox(up_self, label=pref_strings.proxy_requires_password_checkbox)
        self.auth_req.Bind(wx.EVT_CHECKBOX, self.handle_auth_checkbox)
        up_sizer.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        cell()
        cell()
        cell()
        cell()
        cell()
        cell()
        cell()
        up_sizer.Add(auth_req, border=platform.checkbox_baseline_adjustment, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM)
        cell()
        up_sizer.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        cell()
        cell()
        cell()
        cell()
        self.ulbl = ulbl = wx.StaticText(up_self, label=pref_strings.proxy_username_label)
        self.user_text = user_text = wx.TextCtrl(up_self, value='', size=wx.Size(platform.username_textctrl_width, -1))
        cell()
        up_sizer.Add(ulbl, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM | wx.ALIGN_RIGHT)
        up_sizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0))
        up_sizer.Add(user_text, border=platform.textctrl_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        cell()
        self.passlbl = passlbl = wx.StaticText(up_self, label=pref_strings.proxy_password_label)
        self.pass_text = pass_text = wx.TextCtrl(up_self, value='', size=wx.Size(platform.username_textctrl_width, -1), style=wx.TE_PASSWORD)
        up_sizer.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        cell()
        cell()
        cell()
        cell()
        cell()
        up_sizer.Add(passlbl, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM | wx.ALIGN_RIGHT)
        up_sizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0))
        up_sizer.Add(pass_text, border=platform.textctrl_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        cell()
        up_sizer.AddSpacer(wx.Size(0, platform.swap_panel_border))
        cell()
        cell()
        cell()
        cell()
        the_sizer = pb_sizer if self.has_own_borders else border
        self.Bind(wx.EVT_RADIOBUTTON, self.handle_proxy_choice)
        the_sizer.Add(up_self, proportion=0, flag=wx.RIGHT | wx.LEFT | wx.TOP | wx.EXPAND, border=platform.radio_static_box_interior)
        if self.has_own_borders:
            border.Add(pb_sizer, border=16, flag=wx.BOTTOM | wx.EXPAND)
        self.Bind(wx.EVT_TEXT, self.invalidate)
        self.SetSizer(border)
        self.Layout()


class BandwidthSettingsPanel(DropboxTabPanel):

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsBandwidth.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.bandwidth_tab_label

    @staticmethod
    def help_index():
        return 'bandwidth'

    @event_handler
    def read(self, state):
        self.upload_rb[state['throttle_upload_style']].SetValue(True)
        self.upload_box.SetValue(state['throttle_upload_speed'])
        if state['throttle_download_style'] == 2:
            self.download_rb[1].SetValue(True)
        else:
            self.download_rb[0].SetValue(True)
        self.download_box.SetValue(state['throttle_download_speed'])
        self.handle_upload_rb(None)
        self.handle_download_rb(None)

    @event_handler
    def save(self, theEvent):
        state = {}
        should_raise = False
        if self.download_rb[0].GetValue():
            state['throttle_download_style'] = 0
        else:
            state['throttle_download_style'] = 2
        try:
            state['throttle_download_speed'] = self.download_box.GetValue()
        except TypeBox.EntryErrors:
            should_raise = pref_strings.download_limit_error

        if self.upload_rb[0].GetValue():
            state['throttle_upload_style'] = 0
        elif self.upload_rb[1].GetValue():
            state['throttle_upload_style'] = 1
        else:
            state['throttle_upload_style'] = 2
        try:
            state['throttle_upload_speed'] = self.upload_box.GetValue()
        except TypeBox.EntryErrors:
            should_raise = pref_strings.upload_limit_error

        if should_raise is not False:
            raise InvalidEntryException(self.__class__, should_raise)
        return state

    @event_handler
    def handle_download_rb(self, theEvent):
        ability = self.download_rb[1].GetValue()
        self.download_box.Enable(ability)
        self.download_units.Enable(ability)
        self.invalidate(theEvent)

    @event_handler
    def handle_upload_rb(self, theEvent):
        ability = self.upload_rb[2].GetValue()
        self.upload_box.Enable(ability)
        self.upload_units.Enable(ability)
        self.invalidate(theEvent)

    @event_handler
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(BandwidthSettingsPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.has_own_borders = has_own_borders
        radio_interior = platform.radio_static_box_interior if self.has_own_borders else platform.radio_notebook_interior
        border = self.border = wx.BoxSizer(wx.VERTICAL)
        if self.has_own_borders:
            download_box = wx.StaticBox(self, label=pref_strings.download_label)
            download_sizer = wx.StaticBoxSizer(download_box, wx.VERTICAL)
            TypeBox_t = TypeBox
        else:
            download_sizer = wx.BoxSizer(wx.VERTICAL)
            download_label = wx.StaticText(self, label=pref_strings.download_label)
            font = download_label.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            download_label.SetFont(font)
            download_sizer.Add(download_label, flag=wx.ALIGN_LEFT)
            TypeBox_t = SpinTypeBox
        self.download_rb = [wx.RadioButton(self, label=pref_strings.dont_limit_download, style=wx.RB_GROUP), wx.RadioButton(self, label=pref_strings.speed_limit_download)]
        for rb in self.download_rb:
            self.Bind(wx.EVT_RADIOBUTTON, self.handle_download_rb, rb)

        second_row_download_sizer = wx.BoxSizer(wx.HORIZONTAL)
        second_row_download_sizer.Add(self.download_rb[1], border=platform.radio_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_LEFT)
        second_row_download_sizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0))
        self.download_box = TypeBox_t(self, ValidBandwidth, size=wx.Size(50, -1), on_text=[self.invalidate])
        second_row_download_sizer.Add(self.download_box, border=platform.textctrl_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        second_row_download_sizer.AddSpacer(wx.Size(platform.textctrl_statictext_horizontal_spacing, 0))
        self.download_units = wx.StaticText(self, label=pref_strings.rate_units)
        second_row_download_sizer.Add(self.download_units, border=platform.statictext_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        second_row_download_sizer.AddStretchSpacer()
        download_sizer.Add(self.download_rb[0], flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.LEFT | wx.TOP | wx.RIGHT, border=radio_interior)
        download_sizer.AddSpacer(wx.Size(0, platform.top_of_baselined_textctrl_to_bottom_of_radio))
        download_sizer.Add(second_row_download_sizer, flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=radio_interior)
        border.Add(download_sizer, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        if self.has_own_borders:
            upload_box = wx.StaticBox(self, label=pref_strings.upload_label)
            upload_sizer = wx.StaticBoxSizer(upload_box, wx.VERTICAL)
        else:
            upload_sizer = wx.BoxSizer(wx.VERTICAL)
            upload_label = wx.StaticText(self, label=pref_strings.upload_label)
            font = upload_label.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            upload_label.SetFont(font)
            upload_sizer.Add(upload_label, flag=wx.ALIGN_LEFT)
        self.upload_rb = [wx.RadioButton(self, label=pref_strings.dont_limit_upload, style=wx.RB_GROUP), wx.RadioButton(self, label=pref_strings.auto_limit_upload), wx.RadioButton(self, label=pref_strings.speed_limit_upload)]
        for rb in self.upload_rb:
            self.Bind(wx.EVT_RADIOBUTTON, self.handle_upload_rb, rb)

        second_row_upload_sizer = wx.BoxSizer(wx.HORIZONTAL)
        second_row_upload_sizer.Add(self.upload_rb[2], border=platform.radio_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_LEFT)
        second_row_upload_sizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0))
        self.upload_box = TypeBox_t(self, ValidBandwidth, size=wx.Size(50, -1), on_text=[self.invalidate])
        second_row_upload_sizer.Add(self.upload_box, border=platform.textctrl_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        second_row_upload_sizer.AddSpacer(wx.Size(platform.textctrl_statictext_horizontal_spacing, 0))
        self.upload_units = wx.StaticText(self, label=pref_strings.rate_units)
        second_row_upload_sizer.Add(self.upload_units, border=platform.statictext_baseline_adjustment, flag=wx.BOTTOM | wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        second_row_upload_sizer.AddStretchSpacer()
        upload_sizer.Add(self.upload_rb[0], flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.LEFT | wx.TOP | wx.RIGHT, border=radio_interior)
        upload_sizer.AddSpacer(wx.Size(0, platform.radio_group_spacer))
        upload_sizer.Add(self.upload_rb[1], flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.LEFT | wx.RIGHT, border=radio_interior)
        upload_sizer.AddSpacer(wx.Size(0, platform.top_of_baselined_textctrl_to_bottom_of_radio))
        upload_sizer.Add(second_row_upload_sizer, flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=radio_interior)
        border.Add(upload_sizer, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        windows_wx_bug_workaround = wx.RadioButton(self, style=wx.RB_GROUP)
        windows_wx_bug_workaround.Show(False)
        self.SetSizer(border)
        self.Layout()
        self.Bind(wx.EVT_TEXT, self.invalidate)


@event_handler
def handle_unlink(self, theEvent):
    if self.dropbox_app.sync_engine and self.dropbox_app.sync_engine.status.is_true('importing'):
        wx.MessageDialog(self, pref_strings.unlink_while_importing, caption=pref_strings.unlink_warning_caption, style=wx.OK | wx.ICON_WARNING).ShowModal()
        return
    if 'displayname' in dropbox_globals:
        caption = pref_strings.unlink_dialog_caption_short_with_displayname % dict(displayname=dropbox_globals['displayname'])
    else:
        caption = pref_strings.unlink_dialog_caption_short
    if wx.MessageDialog(self, pref_strings.unlink_dialog_message, caption=caption, style=wx.OK | wx.CANCEL | wx.ICON_QUESTION).ShowModal() == wx.ID_OK:
        self.dropbox_app.restart_and_unlink()


@event_handler
def handle_link_secondary(self, theEvent):
    self.link_secondary_button.Disable()
    self.dropbox_app.mbox.enable()


@event_handler
def handle_unlink_secondary(self, theEvent):
    TRACE('!! unlinking')
    self.secondary_unlink_button.Disable()
    self.dropbox_app.mbox.unlink_secondary()


class WindowsAccountPanel(DropboxTabPanel):

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsAccount.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.account_tab_label

    @staticmethod
    def help_index():
        return 'account'

    def read(self, state):
        pass

    def save(self, theEvent):
        state = {}
        return state

    def set_url_info(self, url_info):
        self.url_info = url_info

    @event_handler
    def on_ctrldown(self, *n):
        pass

    @message_sender(wx.CallAfter)
    def sync_engine_is_valid(self, sync_engine):
        self.on_show()
        self.parent.resize_for_panel(type(self))

    @event_handler
    def on_show(self):
        assert self.dropbox_app.dropbox_url_info is not None, 'this should be set by now'
        if 'displayname' in dropbox_globals:
            self.a_box.SetLabel(pref_strings.account_info_with_displayname % dropbox_globals)
        if 'userdisplayname' in dropbox_globals and self.dropbox_app.dropbox_url_info.email:
            if self.dropbox_app.mbox.enabled:
                emails = self.dropbox_app.mbox.email_addresses
                account_text = pref_strings.multiaccount_linked % dict(user=dropbox_globals['userdisplayname'], personal_email=emails.personal, business_email=emails.business)
            else:
                account_text = pref_strings.account_linked_to_user % dict(user=dropbox_globals['userdisplayname'], email=self.dropbox_app.dropbox_url_info.email)
            self.unlink_button.Enable(True)
        elif self.dropbox_app.dropbox_url_info.email:
            account_text = pref_strings.account_linked_but_not_connected % dict(email=self.dropbox_app.dropbox_url_info.email)
            self.unlink_button.Enable(True)
        else:
            account_text = pref_strings.account_unlinked_display
            self.unlink_button.Enable(False)
        self.account_text.SetLabel(account_text)
        self.account_text.SetSize(wx.Size(100, self.account_text.GetBestSize().GetHeight()))
        self.Layout()
        self.parent.panel.Layout()
        self.account_text.Wrap(self.unlink_sizer.GetSize().GetWidth())
        self.Layout()
        self.parent.panel.Layout()

    @message_sender(wx.CallAfter)
    def on_secondary_link(self, linked):
        if self.dropbox_app.mbox.paired:
            primary_label = self.dropbox_app.mbox.unlink_labels.primary
        else:
            primary_label = pref_strings.unlink_button
        self.unlink_button.SetLabel(primary_label)
        self.reset_multiaccount_buttons()
        self.Layout()

    @event_handler
    def add_multiaccount_buttons(self):
        self.buttons_vertical_spacer = wx.BoxSizer(wx.VERTICAL)
        self.buttons_vertical_spacer.Add(wx.Size(0, platform.static_box_button_vertical_spacing))
        self.link_secondary_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.a_sizer.Add(self.buttons_vertical_spacer)
        self.a_sizer.Add(self.link_secondary_sizer, flag=wx.EXPAND)
        self.reset_multiaccount_buttons()

    @event_handler
    def reset_multiaccount_buttons(self):
        mbox = self.dropbox_app.mbox
        if not mbox.paired:
            self.a_sizer.Hide(self.buttons_vertical_spacer)
            self.a_sizer.Hide(self.link_secondary_sizer)
        else:
            self.link_secondary_sizer.Clear(True)
            if mbox.enabled:
                secondary_label = mbox.unlink_labels.secondary
                secondary_button = wx.Button(self, label=secondary_label)
                self.secondary_unlink_button = secondary_button
                self.secondary_unlink_button.Bind(wx.EVT_BUTTON, functools.partial(handle_unlink_secondary, self))
            else:
                secondary_label = mbox.link_labels.secondary
                secondary_button = wx.Button(self, label=secondary_label)
                self.link_secondary_button = secondary_button
                self.link_secondary_button.Bind(wx.EVT_BUTTON, functools.partial(handle_link_secondary, self))
            self.link_secondary_sizer.AddSpacer(wx.Size(0, 0), proportion=1, flag=wx.EXPAND)
            self.link_secondary_sizer.Add(secondary_button, border=platform.button_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
            self.a_sizer.Show(self.buttons_vertical_spacer)
            self.a_sizer.Show(self.link_secondary_sizer)

    @event_handler
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(WindowsAccountPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.has_own_borders = has_own_borders
        border = self.border = wx.BoxSizer(wx.VERTICAL)
        self.a_box = a_box = wx.StaticBox(self)
        a_boxsizer = wx.StaticBoxSizer(a_box, wx.HORIZONTAL)
        a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.account_text = wx.StaticText(self, label='')
        a_sizer.Add(self.account_text, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.BOTTOM)
        self.version_text = wx.StaticText(self, label=pref_strings.buildkey_and_version_installed % dict(version_string=VERSION))
        self.version_text.Enable(False)
        a_sizer.Add(self.version_text, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        if self.dropbox_app.mbox.paired:
            primary_label = self.dropbox_app.mbox.unlink_labels.primary
        else:
            primary_label = pref_strings.unlink_button
        self.unlink_sizer = unlink_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.unlink_button = wx.Button(self, label=primary_label)
        self.unlink_button.Bind(wx.EVT_BUTTON, functools.partial(handle_unlink, self))
        unlink_sizer.AddSpacer(wx.Size(0, 0), proportion=1, flag=wx.EXPAND)
        unlink_sizer.Add(self.unlink_button, border=platform.button_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        a_sizer.Add(unlink_sizer, flag=wx.EXPAND)
        self.a_sizer = a_sizer
        self.add_multiaccount_buttons()
        a_boxsizer.Add(a_sizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=platform.radio_static_box_interior)
        border.Add(a_boxsizer, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        dropbox_app.ui_kit.add_sync_engine_handler(self.sync_engine_is_valid)
        self.SetSizer(border)
        self.Layout()


class LinuxAccountPanel(DropboxTabPanel):

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsAccount.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.account_tab_label

    @staticmethod
    def help_index():
        return 'account'

    def read(self, state):
        pass

    def save(self, theEvent):
        return {}

    def set_url_info(self, url_info):
        self.url_info = url_info

    @event_handler
    def on_keyup(self, theEvent):
        if theEvent.KeyCode == wx.WXK_CONTROL:
            self.unlink_button.SetLabel(pref_strings.unlink_button)
            self.unlink_fix_perms = False
        theEvent.Skip()

    @event_handler
    def disambiguate_unlink(self, theEvent):
        if self.unlink_fix_perms:
            self.fix_permissions(theEvent)
        else:
            handle_unlink(self, theEvent)

    def on_ctrldown(self, *n):
        self.unlink_button.SetLabel(pref_strings.unlink_button_fix_perms)
        self.unlink_fix_perms = True

    @event_handler
    def fix_permissions(self, theEvent):
        self.unlink_button.SetLabel(pref_strings.unlink_button_fixing_perms)
        self.unlink_button.Enable(False)
        self.throbber.start()
        message_sender(spawn_thread_with_name('FIX_PERMS'), on_success=self.fix_perms_success, on_exception=self.fix_perms_failed, block=False, dont_post=lambda : False)(arch.fixperms.fix_whole_dropbox_permissions)(wx.CallAfter)

    @message_sender(wx.CallAfter)
    def fix_perms_success(self, failures):
        TRACE('finished fixing permissions')
        self.unlink_button.SetLabel(pref_strings.unlink_button)
        self.unlink_button.Enable(True)
        self.throbber.stop()
        self.throbber.Hide()
        wx.MessageDialog(self, pref_strings.fix_perms_worked_message, caption=pref_strings.fix_perms_worked_caption, style=wx.OK).ShowModal()

    @message_sender(wx.CallAfter)
    def fix_perms_failed(self, exc, exc_info):
        TRACE('failed to fix permissions')
        unhandled_exc_handler(exc_info=exc_info)
        self.unlink_button.SetLabel(pref_strings.unlink_button)
        self.unlink_button.Enable(True)
        self.throbber.stop()
        self.throbber.Hide()
        wx.MessageDialog(self, pref_strings.fix_perms_really_bad_error_message, caption=pref_strings.fix_perms_really_bad_error_caption, style=wx.OK | wx.ICON_ERROR).ShowModal()

    @message_sender(wx.CallAfter)
    def sync_engine_is_valid(self, sync_engine):
        self.on_show()
        self.parent.resize_for_panel(type(self))

    @event_handler
    def on_show(self):
        assert self.url_info is not None, 'this should be set by now'
        unlink_ability = True
        if 'userdisplayname' in dropbox_globals and self.url_info.email:
            account_text_string = u'%s (%s)' % (dropbox_globals['userdisplayname'], self.url_info.email)
        elif self.url_info.email:
            account_text_string = u'%s' % self.url_info.email
        else:
            account_text_string = pref_strings.account_unlinked_display
            unlink_ability = False
        self.unlink_button.Enable(unlink_ability)
        self.unlink_button.Bind(wx.EVT_BUTTON, self.disambiguate_unlink)
        self.unlink_button.SetLabel(pref_strings.unlink_button)
        self.unlink_fix_perms = False
        unlink_button_width = self.unlink_button.GetSize().GetWidth()
        unlink_throbber_width = self.throbber.GetSize().GetWidth()
        unlink_width = unlink_button_width + unlink_throbber_width
        self.account_text.SetLabel(account_text_string)
        self.account_text.SetSize(wx.Size(100, self.account_text.GetBestSize().GetHeight()))
        self.Layout()
        self.account_text.Wrap(self.GetSize().GetWidth() - unlink_width - platform.statictext_notebook_interior * 2)
        self.Layout()
        if not self.unlink_sizer_setup:
            account_text_width = self.account_text.GetSize().GetWidth()
            unlink_border_width = self.GetSize().GetWidth() - account_text_width - unlink_width - platform.statictext_notebook_interior
            self.unlink_sizer.Add(self.unlink_button, border=unlink_border_width, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL)
            self.unlink_sizer.Add(self.throbber, flag=wx.ALIGN_CENTER_VERTICAL)
            self.unlink_sizer.Layout()
            self.Layout()
            self.unlink_sizer_setup = True

    @event_handler
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(LinuxAccountPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.has_own_borders = has_own_borders
        self.url_info = self.dropbox_app.dropbox_url_info
        inner_border = wx.BoxSizer(wx.VERTICAL)
        version_label = wx.StaticText(self, label=pref_strings.version_label_plain)
        font = version_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        version_label.SetFont(font)
        inner_border.Add(version_label, flag=wx.ALIGN_LEFT)
        version_text = wx.StaticText(self, label=pref_strings.buildkey_and_version % dict(version_string=VERSION))
        inner_border.Add(version_text, border=platform.statictext_notebook_interior, flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL)
        account_label = wx.StaticText(self, label=pref_strings.account_label_plain)
        font = account_label.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        account_label.SetFont(font)
        inner_border.Add(account_label, flag=wx.ALIGN_LEFT)
        self.account_text = wx.StaticText(self, label=pref_strings.account_unlinked_display)
        self.unlink_button = wx.Button(self, label=pref_strings.unlink_button)
        self.throbber = Throbber(self)
        self.unlink_fix_perms = False
        self.unlink_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.unlink_sizer.Add(self.account_text, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.unlink_sizer.Layout()
        self.unlink_sizer_setup = False
        inner_border.Add(self.unlink_sizer, border=platform.statictext_notebook_interior, flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.LEFT | wx.TOP | wx.BOTTOM)
        dropbox_app.ui_kit.add_sync_engine_handler(self.sync_engine_is_valid)
        if feature_enabled('multiaccount'):
            if self.dropbox_app.mbox.enabled:
                self.secondary_account_text = wx.StaticText(self, label=self.dropbox_app.config['secondary_client_email'])
            else:
                self.secondary_account_text = wx.StaticText(self, label=pref_strings.account_unlinked_display)
            self.secondary_action_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.secondary_action_sizer.Add(self.secondary_account_text, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
            self.secondary_action_sizer.Layout()
            self.secondary_unlink_sizer_setup = False
            self.link_secondary_sizer = link_secondary_sizer = wx.BoxSizer(wx.HORIZONTAL)
            if self.dropbox_app.mbox.enabled:
                TRACE('!! secondary detected')
                secondary_unlink_label = dropbox_app.mbox.unlink_labels.secondary
                action_button = wx.Button(self, label=secondary_unlink_label)
                self.secondary_unlink_button = action_button
                self.secondary_unlink_button.Bind(wx.EVT_BUTTON, functools.partial(handle_unlink_secondary, self))
            else:
                TRACE('!! secondary not detected')
                secondary_link_label = dropbox_app.mbox.link_labels.secondary
                action_button = self.link_secondary_button = wx.Button(self, label=secondary_link_label)
                self.link_secondary_button.Bind(wx.EVT_BUTTON, functools.partial(handle_link_secondary, self))
            link_secondary_sizer.Add(action_button, border=platform.button_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
            link_secondary_sizer.AddSpacer(wx.Size(0, 0), proportion=1, flag=wx.EXPAND)
            self.secondary_action_sizer.Add(link_secondary_sizer, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
            inner_border.Add(self.secondary_action_sizer)
        self.SetSizer(inner_border)
        self.Layout()


if platform.use_notebook:
    AccountPanel = LinuxAccountPanel
else:
    AccountPanel = WindowsAccountPanel

class ImportPanel(DropboxTabPanel):

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsImport.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.import_tab_label

    @staticmethod
    def help_index():
        return 'import'

    @event_handler
    def read(self, state):
        if self.screenshots_selector:
            self.screenshots_selector.read(state)

    @event_handler
    def save(self, theEvent):
        if self.screenshots_selector:
            self.screenshots_selector.save()
        return {}

    @event_handler
    def on_show(self):
        self.Layout()
        self.parent.panel.Layout()
        needs_relayout = False
        if self.camera_launcher:
            self.camera_launcher.on_show()
            needs_relayout = True
        if self.photo_import_launcher:
            self.photo_import_launcher.on_show()
            needs_relayout = True
        if self.screenshots_selector and self.screenshots_selector.needs_refresh():
            self.screenshots_selector.on_show()
            needs_relayout = True
        if needs_relayout:
            self.Layout()
            self.parent.panel.Layout()
        self.screenshots_selector.enabled(bool(self.dropbox_app.screenshots_controller))

    @event_handler
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(ImportPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.has_own_borders = has_own_borders
        self.pref_controller = self.dropbox_app.pref_controller
        self.screenshots_selector = None
        self.camera_launcher = None
        self.photo_import_launcher = None
        self.dropbox_app = dropbox_app
        border = wx.BoxSizer(wx.VERTICAL)
        if feature_enabled('screenshots') and ScreenshotsController.is_supported(self.dropbox_app):
            try:
                self.screenshots_selector = ScreenshotsSelector(self, self.dropbox_app, self.has_own_borders, self.invalidate)
                border.Add(self.screenshots_selector, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
            except Exception:
                unhandled_exc_handler()

        if arch.photouploader.USE_PHOTOUPLOADER:
            try:
                self.camera_launcher = CameraUploadLauncher(self, self.dropbox_app)
                border.Add(self.camera_launcher, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
            except Exception:
                unhandled_exc_handler()

        importer = self.dropbox_app.stuff_importer
        if importer:
            show_pictures, show_documents = importer.show_import_button(self.dropbox_app)
            if show_pictures:
                self.photo_import_launcher = PhotoImportLauncher(self, self.dropbox_app)
                border.Add(self.photo_import_launcher, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        self.SetSizerAndFit(border)
        self.Layout()


class AdvancedPanel(DropboxTabPanel):

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsAdvanced.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.advanced_tab_label

    @staticmethod
    def help_index():
        return 'advanced'

    @event_handler
    def read(self, state):
        self.langchoice.last_selection = self.codes.index(state[OPT_LANG])
        self.langchoice.SetSelection(self.langchoice.last_selection)

    @event_handler
    def save(self, theEvent):
        self.langchoice.last_selection = self.langchoice.GetSelection()
        return {OPT_LANG: self.codes[self.langchoice.last_selection]}

    @event_handler
    def on_show(self):
        self.Layout()
        self.parent.re_layout()

    def Layout(self):
        self.parent.panel.Layout()
        self.selsync_launcher.on_show()
        if self.secondary_selsync_launcher:
            self.secondary_selsync_launcher.on_show()
        super(AdvancedPanel, self).Layout()

    @event_handler
    def handle_langchoice(self, theEvent):
        selection = self.langchoice.GetSelection()
        code = self.codes[selection]

        def prompt_cb(message, caption = None, on_ok = None, on_cancel = None, ok_button = None, cancel_button = None):
            assert on_ok
            style = wx.OK | wx.CANCEL if on_cancel else wx.OK
            if wx.MessageDialog(self, message, caption, style).ShowModal() == wx.ID_OK:
                on_ok()
            elif on_cancel:
                on_cancel()

        def on_restart():
            self.parent.save(theEvent, skip_errors=True)

        def on_done():
            self.langchoice.last_selection = selection
            self.langchoice.SetFocus()
            self.invalidate(theEvent, False)

        def on_cancel():
            self.langchoice.SetSelection(self.langchoice.last_selection)
            self.langchoice.SetFocus()
            self.invalidate(theEvent, False)

        change_client_language(self.dropbox_app, code, prompt_cb, on_done, on_cancel, on_restart)

    def add_location_changer(self, secondary = False):
        if self.dropbox_app.mbox.enabled:
            labels = self.dropbox_app.mbox.location_changer_labels
            label = labels.secondary if secondary else labels.primary
        else:
            label = pref_strings.loc_changer_label
        if not self.has_own_borders:
            l_label = wx.StaticText(self, label=label)
            l_font = l_label.GetFont()
            l_font.SetWeight(wx.FONTWEIGHT_BOLD)
            l_label.SetFont(l_font)
            self.border.Add(l_label, flag=wx.EXPAND | wx.BOTTOM)
            self.border.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        location_changer = DropboxLocationChanger(self, self.dropbox_app, move=True, has_own_borders=self.has_own_borders, transparent_hack=False, secondary=secondary, label=label)
        self.border.Add(location_changer, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        self.border.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        return location_changer

    def add_selective_sync_launcher(self, secondary = False):
        if self.dropbox_app.mbox.enabled:
            labels = self.dropbox_app.mbox.selective_sync_labels
            label = labels.secondary if secondary else labels.primary
        else:
            label = selsync_strings.prefs_group_label
        if not self.has_own_borders:
            l_label = wx.StaticText(self, label=label)
            l_font = l_label.GetFont()
            l_font.SetWeight(wx.FONTWEIGHT_BOLD)
            l_label.SetFont(l_font)
            self.border.Add(l_label, flag=wx.EXPAND | wx.BOTTOM)
        selsync_launcher = SelectiveSyncLauncher(self, self.dropbox_app, has_own_borders=self.has_own_borders, transparent_hack=False, secondary=secondary, label=label)
        self.border.Add(selsync_launcher, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        self.border.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        return selsync_launcher

    @assert_message_queue
    def reset(self):
        if self.border:
            self.border.Clear(True)
        border = self.border = wx.BoxSizer(wx.VERTICAL)
        self.location_changer = self.add_location_changer(secondary=False)
        if self.dropbox_app.mbox.enabled:
            self.secondary_location_changer = self.add_location_changer(secondary=True)
        else:
            self.secondary_location_changer = None
        self.selsync_launcher = self.add_selective_sync_launcher(secondary=False)
        if self.dropbox_app.mbox.enabled:
            self.secondary_selsync_launcher = self.add_selective_sync_launcher(secondary=True)
        else:
            self.secondary_selsync_launcher = None
        self.dropbox_app.ui_kit.add_post_link_handler(self.post_link_handler)
        self.codes = []
        choices = []
        for code, translated, english in dropbox.i18n.get_available_languages():
            self.codes.append(code)
            choices.append('%s [%s]' % (translated, english))

        self.langchoice = wx.Choice(self, -1, choices=choices)
        self.langchoice.Bind(wx.EVT_CHOICE, self.handle_langchoice)
        if self.has_own_borders:
            self.l_box = wx.StaticBox(self, label=pref_strings.language_label)
            choice_vsizer = wx.StaticBoxSizer(self.l_box, wx.VERTICAL)
            choice_hsizer = wx.BoxSizer(wx.HORIZONTAL)
            choice_hsizer.Add(self.langchoice, proportion=1, flag=wx.EXPAND)
            choice_vsizer.Add(choice_hsizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=platform.radio_static_box_interior)
        else:
            choice_vsizer = wx.BoxSizer(wx.HORIZONTAL)
            lang_text = wx.StaticText(self, label=pref_strings.language_colon)
            choice_vsizer.Add(lang_text, flag=wx.ALIGN_CENTER_VERTICAL)
            choice_vsizer.AddSpacer(wx.Size(platform.statictext_textctrl_horizontal_spacing, 0), proportion=0, flag=wx.EXPAND)
            choice_vsizer.Add(self.langchoice, flag=wx.ALIGN_CENTER_VERTICAL)
        border.Add(choice_vsizer, proportion=0, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        url_map = {'url': self.dropbox_app.dropbox_url_info.help_url('open_source_software')}
        label = pref_strings.open_source_label % url_map
        open_source_note = StaticLinkText(self, label)
        open_source_note.SetBackgroundColour(self.parent.panel.GetBackgroundColour())
        border.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        border.Add(open_source_note, flag=wx.ALIGN_CENTER_VERTICAL)
        border.AddSpacer(wx.Size(0, platform.textctrl_textctrl_vertical_spacing))
        self.SetSizer(border)
        self.Layout()

    @assert_message_queue
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(AdvancedPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.dropbox_app = dropbox_app
        self.has_own_borders = has_own_borders
        self.border = None
        self.reset()

    @assert_message_queue
    def on_secondary_link(self, linked):
        self.reset()

    @message_sender(wx.CallAfter)
    def post_link_handler(self):
        self.selsync_launcher.Enable(True)
        self.location_changer.Enable(True)
        if self.secondary_selsync_launcher:
            self.secondary_selsync_launcher.Enable(True)
        if self.secondary_location_changer:
            self.secondary_location_changer.Enable(True)


class MainPanel(DropboxTabPanel):
    QUIT_LABEL_WIDTH = 150

    @staticmethod
    def icon():
        return ui.images.wximages.PrefsMain.GetBitmap()

    @staticmethod
    def shortname():
        return pref_strings.main_tab_label

    @staticmethod
    def help_index():
        return 'general'

    @event_handler
    def read(self, state):
        if arch.startup.can_configure_startupitem:
            self.startbox.SetValue(state[OPT_STARTUP])
        self.notifybox.SetValue(state[OPT_BUBBLES])
        self.lanbox.SetValue(state[OPT_P2P])

    @event_handler
    def save(self, theEvent):
        state = {}
        if arch.startup.can_configure_startupitem:
            state[OPT_STARTUP] = self.startbox.GetValue()
        state[OPT_BUBBLES] = self.notifybox.GetValue()
        state[OPT_P2P] = self.lanbox.GetValue()
        return state

    @event_handler
    def on_show(self):
        self.startbox.Show(arch.startup.can_configure_startupitem)
        self.Layout()
        self.parent.panel.Layout()

    @event_handler
    def __init__(self, wx_parent, parent, dropbox_app, has_own_borders):
        super(MainPanel, self).__init__(wx_parent, parent, dropbox_app)
        self.has_own_borders = has_own_borders
        self.pref_controller = self.dropbox_app.pref_controller
        self.camera_launcher = None
        border = wx.BoxSizer(wx.VERTICAL)
        if self.has_own_borders:
            i_box = wx.StaticBox(self)
            i_sizer = wx.StaticBoxSizer(i_box, wx.VERTICAL)
        else:
            i_sizer = wx.BoxSizer(wx.VERTICAL)
        notifysizer = wx.BoxSizer(wx.HORIZONTAL)
        self.notifybox = wx.CheckBox(self, label=pref_strings.show_bubbles)
        self.notifybox.Bind(wx.EVT_CHECKBOX, self.invalidate)
        notifysizer.Add(self.notifybox, border=platform.radio_static_box_interior, flag=wx.LEFT | wx.RIGHT | wx.TOP)
        notifysizer.AddSpacer(wx.Size(0, 0), proportion=1, flag=wx.EXPAND)
        i_sizer.Add(notifysizer, proportion=0, flag=wx.EXPAND)
        i_sizer.AddSpacer(wx.Size(0, platform.checkbox_group_spacer))
        startsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.startbox = wx.CheckBox(self, label=pref_strings.startup_item)
        self.startbox.Bind(wx.EVT_CHECKBOX, self.invalidate)
        startsizer.Add(self.startbox, border=platform.radio_static_box_interior, flag=wx.LEFT | wx.RIGHT)
        startsizer.AddSpacer(wx.Size(0, 0), proportion=1, flag=wx.EXPAND)
        i_sizer.Add(startsizer, proportion=0, flag=wx.EXPAND)
        i_sizer.AddSpacer(wx.Size(0, platform.checkbox_group_spacer))
        lansizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lanbox = wx.CheckBox(self, label=pref_strings.p2p_enabled)
        self.lanbox.Bind(wx.EVT_CHECKBOX, self.invalidate)
        lansizer.Add(self.lanbox, border=platform.checkbox_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        lansizer.AddSpacer(wx.Size(platform.radio_static_box_interior, 0), proportion=0, flag=wx.EXPAND)
        i_sizer.Add(lansizer, border=platform.radio_static_box_interior, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM)
        border.Add(i_sizer, flag=wx.EXPAND | wx.BOTTOM, border=platform.swap_panel_border)
        self.SetSizerAndFit(border)
        self.Layout()


class PrefsFrame(DropboxTabbedFrame):
    PANELS = [MainPanel,
     AccountPanel,
     ImportPanel,
     BandwidthSettingsPanel,
     ProxySettingsPanel,
     AdvancedPanel]
    PANEL_NAME_TO_TYPE = {PanelNames.GENERAL: MainPanel,
     PanelNames.ACCOUNT: AccountPanel,
     PanelNames.IMPORT: ImportPanel,
     PanelNames.ADVANCED: AdvancedPanel}
    DEFAULT_PANEL = PANELS[0]
    first_show = True

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, dropbox_app, *n, **kw):
        kw['atable_extensions'] = [(wx.ACCEL_NORMAL, wx.WXK_CONTROL, self.on_ctrldown)]
        super(PrefsFrame, self).__init__(parent, dropbox_app, *n, **kw)
        self.pref_controller = dropbox_app.pref_controller
        dropbox_app.mbox.on_secondary_link.add_handler(self.on_secondary_link)

    @event_handler
    def switch_help_url(self):
        if self.help_link is not None:
            if WINDOWS_VERSION >= VISTA:
                the_os = 'vista'
            else:
                the_os = 'xp'
            new_url = self.dropbox_app.dropbox_url_info.help_url('prefs/%s/%s' % (the_os, self.current_panel_t.help_index()))
            self.help_link.SetLabel(u'<a href="%s">%s</a>' % (new_url, pref_strings.help_label))

    def setup(self, kw):
        kw['title'] = pref_strings.dropbox_prefs
        return kw

    @message_sender(wx.CallAfter)
    def on_secondary_link(self, linked):
        if linked is True or linked is False:
            for panel in self.all_panels.itervalues():
                panel.on_secondary_link(linked)

            self.update_biggest_dimensions()
            self.update_resize_sizer()
            self.re_layout()

    @event_handler
    def save(self, theEvent, skip_errors = False):
        state_update = {}
        for panel in itertools.chain((self.all_panels[panel_t] for panel_t in self.all_panels if panel_t == self.current_panel_t), (self.all_panels[panel_t] for panel_t in self.all_panels if panel_t != self.current_panel_t)):
            try:
                state_update.update(panel.save(theEvent))
            except InvalidEntryException as e:
                unhandled_exc_handler(False)
                if not skip_errors:
                    self.panel_swapper_factory(e.args[0])(None)
                    self.all_panels[e.args[0]].on_show()
                    wx.MessageDialog(self, e.args[1], caption='', style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()
                    raise
            except Exception:
                unhandled_exc_handler()

        else:
            self.pref_controller.update(state_update)
            self.invalidate(theEvent, False)

    @event_handler
    def help(self, theEvent):
        the_url = self.dropbox_app.dropbox_url_info.help_url('prefs/linux/%s' % self.current_panel_t.help_index())
        self.dropbox_app.dropbox_url_info.launch_full_url(the_url)

    def post_init(self):
        pass

    @message_sender(wx.CallAfter)
    def read(self, pref_state):
        for panel in self.all_panels.values():
            panel.read(pref_state)

        self.invalidate(None, False)

    @event_handler
    def close(self, theEvent):
        TRACE('Closing prefs pane')
        if not hasattr(self.all_panels[self.DEFAULT_PANEL], 'location_changer') or self.all_panels[self.DEFAULT_PANEL].location_changer.not_moving.isSet():
            self.hide_user()

    @event_handler
    def on_ctrldown(self, *n):
        try:
            self.all_panels[AccountPanel].on_ctrldown(*n)
        except AttributeError:
            pass
