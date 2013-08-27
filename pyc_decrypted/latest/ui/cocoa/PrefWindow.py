#Embedded file name: ui/cocoa/PrefWindow.py
from __future__ import absolute_import
import objc
from objc import NO, YES, ivar
from AppKit import NSAlternateKeyMask, NSApp, NSBackingStoreBuffered, NSBeginAlertSheet, NSButton, NSClosableWindowMask, NSColor, NSFloatingWindowLevel, NSMatrix, NSNumberFormatter, NSOnState, NSOffState, NSProgressIndicator, NSPopUpButton, NSSecureTextField, NSTabView, NSTabViewItem, NSTextField, NSTitledWindowMask, NSToolbar, NSToolbarItem, NSView, NSWindow, NSNotificationCenter, NSViewFrameDidChangeNotification
from Foundation import NSHeight, NSMaxX, NSMaxY, NSObject, NSPoint, NSRect, NSSize, NSWidth, NSZeroRect
from PyObjCTools import AppHelper
from build_number import VERSION
from dropbox.client.multiaccount.constants import Roles
from dropbox.client.screenshots import ScreenshotsController
from dropbox.features import feature_enabled
from dropbox.globals import dropbox_globals
from dropbox.gui import event_handler, message_sender, spawn_thread_with_name
import dropbox.i18n
from dropbox.i18n import trans
from dropbox.preferences import HTTP, OPT_BUBBLES, OPT_LANG, OPT_LEOPARD, OPT_PHOTO, OPT_P2P, OPT_STARTUP, OPT_SCREENSHOTS, SOCKS4, SOCKS5
from dropbox.trace import TRACE, unhandled_exc_handler
from .constants import ENTER_KEY, ESCAPE_KEY, Images
from ..common.misc import MiscStrings
from ..common.preferences import change_client_language, pref_strings, PanelNames
from ..common.selective_sync import selsync_strings
import arch
from .dropbox_controls import TextFieldWithLink, LocationButton, RemoteLocationButton, DropboxSheetErrorFactory, NumericStepper, PrefView, FlippedView
from .dynamic_layouts import align_center_to_offset, help_button, BUTTON_LEFT_ALIGNMENT_OFFSET, BUTTON_TO_HELP_BUTTON_ADJUSTMENT_FLIPPED, CHECKBOX_VERTICAL_SPACING, CONTENT_BORDER, HORIZ_BUTTON_SPACING, NEARBY_CONTROL_BORDER
from .selective_sync import SelectiveSyncSheet
PREF_WINDOW_WIDTH = 520

class CheckboxView(NSView):

    def initWithFrame_(self, rect):
        self = super(CheckboxView, self).initWithFrame_(rect)
        self.key_to_checkbox = {}
        return self

    def layoutCheckboxView(self, options, width_needed, height_needed, clear_key_to_checkbox = True):
        if clear_key_to_checkbox:
            self.key_to_checkbox.clear()
        for i, (key, message, action) in enumerate(reversed(options)):
            state = NSOnState if self._dropbox_app.pref_controller[key] else NSOffState
            width_needed, height_needed = self.addSingleOption(message, key, state, action, width_needed, height_needed)

        self.setFrameSize_((width_needed, height_needed))
        return (width_needed, height_needed)

    def addSingleOption(self, message, key, state, action, width_needed, height_needed):
        the_checkbox = NSButton.createNormalCheckboxWithTitle_origin_(message, (0, height_needed))
        self.key_to_checkbox[key] = the_checkbox
        the_checkbox.setState_(state)
        the_checkbox_size = the_checkbox.frame().size
        width_needed = max(the_checkbox_size.width, width_needed)
        height_needed += the_checkbox_size.height
        self.addSubview_(the_checkbox)
        the_checkbox.setTarget_(self)
        the_checkbox.setAction_(action)
        height_needed += CHECKBOX_VERTICAL_SPACING
        return (width_needed, height_needed)


class InnerAccountView(NSView):

    def __new__(cls, dropbox_app, width):
        return InnerAccountView.alloc().initWithDropboxApp_width_(dropbox_app, width)

    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(InnerAccountView, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self._dropbox_app = dropbox_app
            self._width = width
            self._secondary_account_indicator = None
            self.layout()
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def unlinkThisComputer_(self, sender):
        if self._dropbox_app.sync_engine and self._dropbox_app.sync_engine.status.is_true('importing'):
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(self.window(), pref_strings.unlink_warning_caption, pref_strings.unlink_while_importing, lambda : None, None)
            return
        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), pref_strings.unlink_dialog_caption, pref_strings.unlink_dialog_message, self.do_unlink, lambda : None, MiscStrings.unlink_button, MiscStrings.cancel_button)

    @objc.typedSelector('v@:')
    @event_handler
    def do_unlink(self):
        self._dropbox_app.restart_and_unlink()

    @objc.typedSelector('v@:@')
    @event_handler
    def linkSecondaryAccount_(self, sender):
        self._link_secondary_button.setEnabled_(NO)
        self._link_secondary_button.setTitle_(trans(u'Linking Second Account...'))
        self._secondary_account_indicator.startAnimation_(self)
        self._secondary_account_indicator.setHidden_(NO)
        self._dropbox_app.mbox.enable()

    @objc.typedSelector('v@:@')
    @event_handler
    def unlinkSecondaryAccount_(self, sender):
        self._secondary_account_indicator.startAnimation_(self)
        self._secondary_account_indicator.setHidden_(NO)
        self._dropbox_app.mbox.unlink_secondary()

    def layout(self):
        subviews = list(self.subviews())
        for view in subviews:
            view.removeFromSuperview()

        if self._dropbox_app.mbox.enabled:
            account_label = self._dropbox_app.mbox.account_labels.primary
        else:
            account_label = pref_strings.account_label
        account_label_field = NSTextField.createLabelWithText_maxWidth_(account_label, self._width)
        account_label_height = NSHeight(account_label_field.frame())
        version_label_field = NSTextField.createLabelWithText_maxWidth_(pref_strings.version_label, self._width)
        version_label_height = NSHeight(version_label_field.frame())
        hostdisplayname_label_field = NSTextField.createLabelWithText_maxWidth_(pref_strings.hostdisplayname_label, self._width)
        hostdisplayname_label_height = NSHeight(version_label_field.frame())
        if self._dropbox_app.mbox.paired:
            secondary_account_label = self._dropbox_app.mbox.account_labels.secondary
            secondary_account_label_field = NSTextField.createLabelWithText_maxWidth_(secondary_account_label, self._width)
            secondary_account_label_field_width = NSWidth(secondary_account_label_field.frame())
        else:
            secondary_account_label_field = None
            secondary_account_label_field_width = 0
        left_column_width = max(NSWidth(account_label_field.frame()), NSWidth(version_label_field.frame()), NSWidth(hostdisplayname_label_field.frame()), secondary_account_label_field_width)
        if self._dropbox_app.mbox.enabled:
            unlink_msg = self._dropbox_app.mbox.unlink_labels.primary
        else:
            unlink_msg = pref_strings.unlink_button
        self._unlink_button = NSButton.createNormalRoundButtonWithTitle_(unlink_msg)
        self._unlink_button.setTarget_(self)
        self._unlink_button.setAction_(self.unlinkThisComputer_)
        self._progress_indicator = NSProgressIndicator.createSmallSpinner()
        self._progress_indicator.setHidden_(YES)
        self._progress_indicator.sizeToFit()
        if self._dropbox_app.mbox.paired:
            self._secondary_account_indicator = NSProgressIndicator.createSmallSpinner()
            self._secondary_account_indicator.setHidden_(YES)
            self._secondary_account_indicator.sizeToFit()
        enable_unlink = YES
        hostdisplayname_field_text = dropbox_globals.get('displayname')
        if 'userdisplayname' in dropbox_globals and self._dropbox_app.dropbox_url_info.email:
            account_field_text = u'%s (%s)' % (dropbox_globals['userdisplayname'], self._dropbox_app.dropbox_url_info.email)
        elif self._dropbox_app.dropbox_url_info.email:
            account_field_text = self._dropbox_app.dropbox_url_info.email
        else:
            enable_unlink = NO
            account_field_text = pref_strings.account_unlinked_display
        self._unlink_button.setEnabled_(enable_unlink)
        max_width = self._width - (left_column_width + NEARBY_CONTROL_BORDER)
        account_field = NSTextField.createLabelWithText_maxWidth_(account_field_text, max_width)
        account_height = NSHeight(account_field.frame())
        if hostdisplayname_field_text:
            hostdisplayname_field = NSTextField.createLabelWithText_maxWidth_(hostdisplayname_field_text, max_width)
            hostdisplayname_height = NSHeight(hostdisplayname_field.frame())
        version_field = NSTextField.createLabelWithText_maxWidth_(pref_strings.buildkey_and_version % dict(version_string=VERSION), max_width)
        version_height = NSHeight(version_field.frame())
        self.secondary_account_field = None
        self._link_secondary_button = None
        if self._dropbox_app.mbox.paired:
            if self._dropbox_app.mbox.enabled:
                self._setup_secondary_unlink_button(max_width)
            else:
                self._setup_secondary_link_button(max_width)
        right_column_width = max(NSWidth(account_field.frame()), NSWidth(version_field.frame()), NSWidth(hostdisplayname_field.frame()) if hostdisplayname_field_text else 0, NSWidth(self._unlink_button.frame()), NSWidth(self._link_secondary_button.frame()) if self._link_secondary_button else 0, NSWidth(self.secondary_account_field.frame()) if self.secondary_account_field else 0)
        height_needed = 0
        if self._link_secondary_button:
            self._link_secondary_button.setFrameOrigin_(NSPoint(left_column_width + NEARBY_CONTROL_BORDER + BUTTON_LEFT_ALIGNMENT_OFFSET, height_needed))
            height_needed += NSHeight(self._link_secondary_button.frame())
            self._secondary_account_indicator.setFrameOrigin_(NSPoint(NSMaxX(self._link_secondary_button.frame()) + NEARBY_CONTROL_BORDER, NSHeight(self._secondary_account_indicator.frame()) / 2))
        self._unlink_button.setFrameOrigin_(NSPoint(left_column_width + NEARBY_CONTROL_BORDER + BUTTON_LEFT_ALIGNMENT_OFFSET, height_needed))
        self._progress_indicator.setFrameOrigin_(NSPoint(NSMaxX(self._unlink_button.frame()) + NEARBY_CONTROL_BORDER, height_needed + NSHeight(self._progress_indicator.frame()) / 2))
        height_needed += NSHeight(self._unlink_button.frame())
        height_needed += NEARBY_CONTROL_BORDER
        if hostdisplayname_field_text:
            hostdisplayname_field.setFrameOrigin_(NSPoint(left_column_width + NEARBY_CONTROL_BORDER, height_needed))
            hostdisplayname_label_field.placeRelativeToControl_(hostdisplayname_field)
            height_needed += max(hostdisplayname_height, hostdisplayname_label_height)
            height_needed += NEARBY_CONTROL_BORDER
        if self.secondary_account_field:
            self.secondary_account_field.setFrameOrigin_(NSPoint(left_column_width + NEARBY_CONTROL_BORDER, height_needed))
            secondary_account_label_field.placeRelativeToControl_(self.secondary_account_field)
            height_needed += max(NSHeight(self.secondary_account_field.frame()), NSHeight(secondary_account_label_field.frame()))
            height_needed += NEARBY_CONTROL_BORDER
        account_field.setFrameOrigin_(NSPoint(left_column_width + NEARBY_CONTROL_BORDER, height_needed))
        account_label_field.placeRelativeToControl_(account_field)
        height_needed += max(account_height, account_label_height)
        height_needed += NEARBY_CONTROL_BORDER
        version_field.setFrameOrigin_(NSPoint(left_column_width + NEARBY_CONTROL_BORDER, height_needed))
        version_label_field.placeRelativeToControl_(version_field)
        height_needed += max(version_height, version_label_height)
        self.setFrame_(NSRect((0, 0), (left_column_width + NEARBY_CONTROL_BORDER + right_column_width, height_needed)))
        self.addSubview_(account_label_field)
        self.addSubview_(account_field)
        if hostdisplayname_field_text:
            self.addSubview_(hostdisplayname_label_field)
            self.addSubview_(hostdisplayname_field)
        self.addSubview_(self._unlink_button)
        self.addSubview_(self._progress_indicator)
        if self.secondary_account_field:
            self.addSubview_(self.secondary_account_field)
            self.addSubview_(secondary_account_label_field)
        if self._link_secondary_button:
            self.addSubview_(self._link_secondary_button)
            self.addSubview_(self._secondary_account_indicator)
        self.addSubview_(version_field)
        self.addSubview_(version_label_field)

    def _setup_secondary_link_button(self, max_width):
        text = self._dropbox_app.mbox.link_labels.secondary
        self.secondary_account_field = None
        action = self.linkSecondaryAccount_
        self._link_secondary_button = NSButton.createNormalRoundButtonWithTitle_(text)
        self._link_secondary_button.setTarget_(self)
        self._link_secondary_button.setAction_(action)

    def _setup_secondary_unlink_button(self, max_width):
        secondary_account_field_text = u'%s (%s)' % (self._dropbox_app.config['secondary_client_userdisplayname'], self._dropbox_app.config['secondary_client_email'])
        self.secondary_account_field = NSTextField.createLabelWithText_maxWidth_(secondary_account_field_text, max_width)
        text = self._dropbox_app.mbox.unlink_labels.secondary
        action = self.unlinkSecondaryAccount_
        self._link_secondary_button = NSButton.createNormalRoundButtonWithTitle_(text)
        self._link_secondary_button.setTarget_(self)
        self._link_secondary_button.setAction_(action)

    def flagsChanged_(self, event):
        if event.modifierFlags() & NSAlternateKeyMask:
            self._unlink_button.setTitle_(pref_strings.unlink_button_fix_perms)
            self._unlink_button.setAction_(self._fix_permissions)
        else:
            self._unlink_button.setTitle_(pref_strings.unlink_button)
            self._unlink_button.setAction_(self.unlinkThisComputer_)

    def _fix_permissions(self):
        self._unlink_button.setEnabled_(NO)
        self._progress_indicator.startAnimation_(self)
        self._progress_indicator.setHidden_(NO)
        message_sender(spawn_thread_with_name('FIX_PERMS'), on_success=self._fix_perms_success, on_exception=self._fix_perms_failed, block=False, dont_post=lambda : False)(arch.fixperms.fix_whole_dropbox_permissions)(AppHelper.callAfter)

    @objc.typedSelector('v@:')
    @message_sender(AppHelper.callAfter)
    def _fix_perms_success(self, failures):
        self._progress_indicator.stopAnimation_(self)
        self._progress_indicator.setHidden_(YES)
        self._unlink_button.setEnabled_(YES)
        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), pref_strings.fix_perms_worked_caption, pref_strings.fix_perms_worked_message, lambda : None, lambda : None, MiscStrings.ok_button, None)

    @objc.typedSelector('v@:')
    @message_sender(AppHelper.callAfter)
    def _fix_perms_failed(self, exc, exc_info):
        TRACE('failed to fix permissions')
        unhandled_exc_handler(exc_info=exc_info)
        self._progress_indicator.stopAnimation_(self)
        self._progress_indicator.setHidden_(YES)
        self._unlink_button.setEnabled_(YES)
        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), pref_strings.fix_perms_really_bad_error_caption, pref_strings.fix_perms_really_bad_error_message, lambda : None, lambda : None, MiscStrings.ok_button, None)


class DynamicAccountView(PrefView):
    innerAccountView = ivar('innerAccountView')

    def __new__(cls, dropbox_app, width):
        return DynamicAccountView.alloc().initWithDropboxApp_width_(dropbox_app, width)

    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(DynamicAccountView, self).initWithDropboxApp_width_(dropbox_app, width)
        if self is None:
            return
        self.innerAccountView = InnerAccountView(dropbox_app, width)
        self.addSubview_(self.innerAccountView)
        dropbox_app.ui_kit.add_sync_engine_handler(self.sync_engine_is_valid)
        self.layout()
        return self

    @objc.typedSelector('v@:@')
    @message_sender(AppHelper.callAfter)
    def sync_engine_is_valid(self, sync_engine):
        self.settingsChanged()

    @objc.typedSelector('v@:')
    @event_handler
    def settingsChanged(self):
        if self.innerAccountView._secondary_account_indicator:
            self.innerAccountView._secondary_account_indicator.stopAnimation_(self)
            self.innerAccountView._secondary_account_indicator.setHidden_(YES)
        self.innerAccountView.layout()
        self.layout()

    def layout(self):
        height_needed = self.initialHeightNeeded_()
        account_view_frame = self.innerAccountView.frame()
        account_view_frame.origin.x = max(0, (self._width - account_view_frame.size.width) / 2.0)
        account_view_frame.origin.y = height_needed
        height_needed += account_view_frame.size.height + CONTENT_BORDER
        self.setFrameSize_(NSSize(self._width, height_needed))
        self.innerAccountView.setFrame_(account_view_frame)
        self.helpButton.alignBottomInSuperview()

    def flagsChanged_(self, event):
        self.innerAccountView.flagsChanged_(event)


class LanguageButton(NSPopUpButton):

    def __new__(cls, dropbox_app):
        return cls.alloc().initWithDropboxApp_(dropbox_app)

    @objc.typedSelector('v@:@')
    @event_handler
    def initWithDropboxApp_(self, dropbox_app):
        self = super(LanguageButton, self).initWithFrame_(NSZeroRect)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        self.codes = []
        self.choices = []
        for code, translated, english in dropbox.i18n.get_available_languages():
            self.codes.append(code)
            self.choices.append(translated)

        self.addItemsWithTitles_(self.choices)
        try:
            self.prev_pos = self.codes.index(self._dropbox_app.pref_controller[OPT_LANG])
        except (KeyError, ValueError):
            self.prev_pos = 0

        self.selectItemAtIndex_(self.prev_pos)
        self.setAutoenablesItems_(NO)
        self.setTarget_(self)
        self.setAction_(self.confirmRestart_)
        self.sizeToFit()
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def confirmRestart_(self, sender):
        selection = self.indexOfSelectedItem()
        code = self.codes[selection]

        def prompt_cb(message, caption = None, on_ok = None, on_cancel = None, ok_button = None, cancel_button = None):
            assert on_ok
            assert ok_button
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), caption, message, on_ok, on_cancel, ok_button, cancel_button)

        def on_done():
            self.saveSetting()
            self.window().makeFirstResponder_(self)
            self.prev_pos = selection

        change_client_language(self._dropbox_app, code, prompt_cb, on_done=on_done, on_cancel=self.on_cancel, on_restart=self.on_restart)

    @objc.typedSelector('v@:')
    @event_handler
    def on_restart(self):
        self.saveSetting()

    @objc.typedSelector('v@:')
    @event_handler
    def on_cancel(self):
        self.selectItemAtIndex_(self.prev_pos)
        self.window().makeFirstResponder_(self)

    def saveSetting(self):
        try:
            option = self.indexOfSelectedItem()
            lang_code = self.codes[option]
            self._dropbox_app.pref_controller.update({OPT_LANG: lang_code})
        except IOError:
            pass
        except:
            unhandled_exc_handler()


class BandwidthSheet(NSWindow):

    def __new__(cls, dropbox_app):
        return BandwidthSheet.alloc().initWithDropboxApp_(dropbox_app)

    def initWithDropboxApp_(self, dropbox_app):
        self = super(BandwidthSheet, self).initWithContentRect_styleMask_backing_defer_(NSZeroRect, NSTitledWindowMask | NSClosableWindowMask, NSBackingStoreBuffered, YES)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        try:
            self.innerView = InnerBandwidthView(self._dropbox_app)
            self.contentView().addSubview_(self.innerView)
            size = self.innerView.frame().size
            self.setContentMinSize_(size)
            self.setContentSize_(size)
            self.setReleasedWhenClosed_(NO)
        except:
            unhandled_exc_handler()

        return self

    def readFromPreferences(self):
        self.innerView.setDownloadSpeed_(self._dropbox_app.pref_controller['throttle_download_speed'])
        self.innerView.setUploadSpeed_(self._dropbox_app.pref_controller['throttle_upload_speed'])
        self.innerView.setDownloadStyle_(self._dropbox_app.pref_controller['throttle_download_style'])
        self.innerView.setUploadStyle_(self._dropbox_app.pref_controller['throttle_upload_style'])

    def beginSheetForWindow_(self, window):
        self.relevantWindow = window
        try:
            self.innerView.beginSheet_forWindow_(self, window)
        except:
            unhandled_exc_handler()

    def savePreferences(self):
        state = dict(throttle_download_style=self.innerView.downloadStyle(), throttle_download_speed=self.innerView.downloadSpeed(), throttle_upload_style=self.innerView.uploadStyle(), throttle_upload_speed=self.innerView.uploadSpeed())
        self._dropbox_app.pref_controller.update(state)


class ProxiesSheet(NSWindow):

    def __new__(cls, dropbox_app):
        return ProxiesSheet.alloc().initWithDropboxApp_(dropbox_app)

    def initWithDropboxApp_(self, dropbox_app):
        self = super(ProxiesSheet, self).initWithContentRect_styleMask_backing_defer_(NSZeroRect, NSTitledWindowMask | NSClosableWindowMask, NSBackingStoreBuffered, YES)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        try:
            self.innerView = InnerProxiesView(self._dropbox_app)
            self.contentView().addSubview_(self.innerView)
            size = self.innerView.frame().size
            self.setContentMinSize_(size)
            self.setContentSize_(size)
            self.setReleasedWhenClosed_(NO)
        except:
            unhandled_exc_handler()

        return self

    def beginSheetForWindow_(self, window):
        self.relevantWindow = window
        try:
            self.innerView.beginSheet_forWindow_(self, window)
        except:
            unhandled_exc_handler()

    def readFromPreferences(self):
        self.innerView.setProxyMode_(self._dropbox_app.pref_controller['proxy_mode'])
        self.innerView.setProxyType_(self._dropbox_app.pref_controller['proxy_type'])
        self.innerView.setProxyServer_(self._dropbox_app.pref_controller['proxy_server'])
        self.innerView.setProxyPort_(self._dropbox_app.pref_controller['proxy_port'])
        self.innerView.setProxyRequiresAuth_(self._dropbox_app.pref_controller['proxy_requires_auth'])
        self.innerView.setUsername_(self._dropbox_app.pref_controller['proxy_username'])
        self.innerView.setPassword_(self._dropbox_app.pref_controller['proxy_password'])

    def savePreferences(self):
        state = {}
        state['proxy_mode'] = self.innerView.proxyMode()
        state['proxy_type'] = self.innerView.proxyType()
        state['proxy_server'] = self.innerView.proxyServer()
        state['proxy_port'] = self.innerView.proxyPort()
        state['proxy_requires_auth'] = self.innerView.proxyRequiresAuth()
        state['proxy_username'] = self.innerView.username()
        state['proxy_password'] = self.innerView.password()
        self._dropbox_app.pref_controller.update(state)


class InnerNetworkView(CheckboxView):

    def __new__(cls, dropbox_app):
        return cls.alloc().initWithFrame_DropboxApp_(NSZeroRect, dropbox_app)

    def set_button_width(self, button, width):
        new_frame = button.frame()
        new_frame.size.width = max(width, NSWidth(new_frame) + 12)
        button.setFrame_(new_frame)

    @objc.typedSelector('v@:@@')
    @event_handler
    def initWithFrame_DropboxApp_(self, frame, dropbox_app):
        self = super(InnerNetworkView, self).initWithFrame_(frame)
        if self is None:
            return self
        self._dropbox_app = dropbox_app
        self.bandwidth_label = self.addNormalTextFieldWithLabel_(pref_strings.bandwidth_colon)
        self.bandwidth_launcher = self.addNormalRoundButtonWithTitle_action_(pref_strings.change_settings_button, self.bandwidthSheetLaunch_)
        self.bandwidth_sheet = BandwidthSheet(self._dropbox_app)
        self.proxies_label = self.addNormalTextFieldWithLabel_(pref_strings.proxies_colon)
        self.proxies_launcher = self.addNormalRoundButtonWithTitle_action_(pref_strings.change_settings_button, self.proxySheetLaunch_)
        self.proxies_sheet = ProxiesSheet(self._dropbox_app)
        self.sizeToFit()
        return self

    def isFlipped(self):
        return YES

    def sizeToFit(self):
        width_needed = 0
        height_needed = 2
        items = [(self.bandwidth_label, self.bandwidth_launcher), (self.proxies_label, self.proxies_launcher)]
        label_width = max((NSWidth(label.frame()) for label, _ in items))
        for label, control in items:
            label.setFrameOrigin_((label_width - NSWidth(label.frame()), height_needed))
            control.placeRelativeToLabel_(label)
            width_needed = max(width_needed, NSMaxX(control.frame()))
            height_needed += NSHeight(control.frame()) + control.verticalPadding()

        options = [(OPT_P2P, pref_strings.p2p_enabled, self.setP2P_)]
        width_needed, height_needed = self.layoutCheckboxView(options, width_needed, height_needed - control.verticalPadding() + 10)
        checkbox = self.key_to_checkbox[OPT_P2P]
        extra_width_needed = NSWidth(checkbox.frame()) - NSWidth(self.proxies_launcher.frame())
        if extra_width_needed > 0:
            width_needed += extra_width_needed + 4
        checkbox.setFrameOrigin_((self.proxies_launcher.frame().origin.x + 4, checkbox.frame().origin.y))
        self.setFrameSize_((width_needed, height_needed))

    @objc.typedSelector('v@:@')
    @event_handler
    def bandwidthSheetLaunch_(self, sender):
        self.window().makeFirstResponder_(self.bandwidth_launcher)
        self.bandwidth_sheet.readFromPreferences()
        self.bandwidth_sheet.beginSheetForWindow_(self.window())

    @objc.typedSelector('v@:@')
    @event_handler
    def proxySheetLaunch_(self, sender):
        self.window().makeFirstResponder_(self.proxies_launcher)
        self.proxies_sheet.readFromPreferences()
        self.proxies_sheet.beginSheetForWindow_(self.window())

    @objc.typedSelector('v@:@')
    @event_handler
    def setP2P_(self, sender):
        self._dropbox_app.pref_controller.update({OPT_P2P: sender.state() == NSOnState})


class DynamicNetworkView(PrefView):

    def __new__(cls, dropbox_app, width):
        return DynamicNetworkView.alloc().initWithDropboxApp_width_(dropbox_app, width)

    @objc.typedSelector('@@:@i')
    @event_handler
    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(DynamicNetworkView, self).initWithDropboxApp_width_(dropbox_app, width)
        if self is None:
            return
        self.networkView = InnerNetworkView(self._dropbox_app)
        self.addSubview_(self.networkView)
        self.layout()
        return self

    def isFlipped(self):
        return YES

    def layout(self):
        self.setFrameSize_(NSSize(self._width, 0))
        height_needed = self.initialHeightNeeded_()
        self.networkView.setFrameOrigin_(NSPoint(0, CONTENT_BORDER))
        self.networkView.centerHorizontallyInSuperview()
        height_needed += NSHeight(self.networkView.frame())
        height_needed += CONTENT_BORDER
        self.setFrameSize_(NSSize(self._width, height_needed))
        self.helpButton.alignBottomInSuperview()

    def show_proxy_sheet(self):
        self.networkView.proxySheetLaunch_(self)


class InnerAdvancedView(NSView):

    def __new__(cls, dropbox_app, remote = False):
        return cls.alloc().initWithFrame_DropboxApp_Remote_(NSZeroRect, dropbox_app, remote)

    def set_button_width(self, button, width):
        new_frame = button.frame()
        new_frame.size.width = max(width, NSWidth(new_frame) + 12)
        button.setFrame_(new_frame)

    @objc.typedSelector('v@:@@@')
    @event_handler
    def initWithFrame_DropboxApp_Remote_(self, frame, dropbox_app, remote):
        self = super(InnerAdvancedView, self).initWithFrame_(frame)
        if self is not None:
            self._dropbox_app = dropbox_app
            self._remote = remote
            self.loc_changer_label = self.addNormalTextFieldWithLabel_(pref_strings.loc_changer_label_colon)
            self.loc_changer = RemoteLocationButton(self._dropbox_app) if remote else LocationButton(self._dropbox_app)
            self.set_button_width(self.loc_changer, 200)
            self.addSubview_(self.loc_changer)
            self.sel_sync_label = self.addNormalTextFieldWithLabel_(selsync_strings.prefs_group_label_colon)
            self.selsync_launcher = self.addNormalRoundButtonWithTitle_action_(selsync_strings.prefs_change_label, self.selsyncLaunch_)
            self.selsync_launcher.setEnabled_(self._dropbox_app.ui_kit.post_link)
            if not self._dropbox_app.mbox.enabled:
                self.lang_label = self.addNormalTextFieldWithLabel_(pref_strings.language_colon)
                self.lang_chooser = LanguageButton(self._dropbox_app)
                self.set_button_width(self.lang_chooser, 200)
                self.addSubview_(self.lang_chooser)
            self.sizeToFit()
        return self

    def isFlipped(self):
        return YES

    def sizeToFit(self):
        width_needed = 0
        height_needed = 2
        items = [(self.loc_changer_label, self.loc_changer), (self.sel_sync_label, self.selsync_launcher)]
        if not self._dropbox_app.mbox.has_secondary:
            items.append((self.lang_label, self.lang_chooser))
        self.label_width = label_width = max((NSWidth(label.frame()) for label, _ in items))
        for label, control in items:
            label.setFrameOrigin_((label_width - NSWidth(label.frame()), height_needed))
            control.placeRelativeToLabel_(label)
            width_needed = max(width_needed, NSMaxX(control.frame()))
            height_needed += NSHeight(control.frame()) + control.verticalPadding()

        self.setFrameSize_(NSSize(width_needed, height_needed - control.verticalPadding() + 10))

    @objc.typedSelector('v@:@')
    @event_handler
    def selsyncLaunch_(self, sender):
        self.selectiveSyncSheet = SelectiveSyncSheet(self._dropbox_app, take_action=self.selsyncSetBusy_, remote=self._remote)
        self.selectiveSyncSheet.beginSheetForWindow_(self.window())

    @objc.typedSelector('v@:B')
    @event_handler
    def selsyncSetBusy_(self, busy):
        self.selsync_launcher.setTitle_(selsync_strings.prefs_working_button if busy else selsync_strings.prefs_change_label)
        self.selsync_launcher.setEnabled_(not busy)

    def postLink(self):
        self.selsync_launcher.setEnabled_(self._dropbox_app.ui_kit.post_link)
        self.loc_changer.reloadChoices()


class InnerAdvancedViewWithSecondary(FlippedView):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, dropbox_app):
        return cls.alloc().initWithApp_(dropbox_app)

    def initWithApp_(self, dropbox_app):
        self = super(InnerAdvancedViewWithSecondary, self).initWithFrame_(NSZeroRect)
        if self is None:
            return self
        self._dropbox_app = dropbox_app
        self.layout()
        return self

    def set_button_width(self, button, width):
        new_frame = button.frame()
        new_frame.size.width = max(width, NSWidth(new_frame) + 12)
        button.setFrame_(new_frame)

    def layout(self):
        self.tab_view = NSTabView.alloc().initWithFrame_(NSRect((15, 0), (480, 150)))
        self.primary_view = InnerAdvancedView(self._dropbox_app, remote=False)
        self.primary_stupid_view = NSView.alloc().initWithFrame_(self.tab_view.contentRect())
        self.primary_stupid_view.addSubview_(self.primary_view)
        account_labels = self._dropbox_app.mbox.account_labels_plain
        primary_text = account_labels.primary
        secondary_text = account_labels.secondary
        self.primary = NSTabViewItem.alloc().initWithIdentifier_(primary_text)
        self.primary.setLabel_(primary_text)
        self.primary.setView_(self.primary_stupid_view)
        self.secondary_view = InnerAdvancedView(self._dropbox_app, remote=True)
        self.secondary_stupid_view = NSView.alloc().initWithFrame_(self.tab_view.contentRect())
        self.secondary_stupid_view.addSubview_(self.secondary_view)
        self.secondary = NSTabViewItem.alloc().initWithIdentifier_(secondary_text)
        self.secondary.setLabel_(secondary_text)
        self.secondary.setView_(self.secondary_stupid_view)
        self.tab_view.addTabViewItem_(self.primary)
        self.tab_view.addTabViewItem_(self.secondary)
        self.addSubview_(self.tab_view)
        self.lang_label = self.addNormalTextFieldWithLabel_(pref_strings.language_colon)
        self.lang_chooser = LanguageButton(self._dropbox_app)
        self.set_button_width(self.lang_chooser, 200)
        self.addSubview_(self.lang_chooser)
        self.sizeToFit()

    def sizeToFit(self):
        width_needed = 0
        height_needed = 2
        self._dropbox_app.foo = self
        self.primary_view.centerInSuperview()
        self.secondary_view.centerInSuperview()
        height_needed += NSHeight(self.tab_view.frame())
        items = [(self.lang_label, self.lang_chooser)]
        label_width = self.primary_view.label_width + 91
        for label, control in items:
            label.setFrameOrigin_((label_width - NSWidth(label.frame()), height_needed))
            control.placeRelativeToLabel_(label)
            width_needed = max(width_needed, NSMaxX(control.frame()))
            height_needed += NSHeight(control.frame()) + control.verticalPadding()

        self.setFrameSize_((PREF_WINDOW_WIDTH - 10, height_needed - 10))


class DynamicAdvancedView(PrefView):
    locationChanger = ivar('locationChanger')
    selsyncLauncher = ivar('selsyncLauncher')

    def __new__(cls, dropbox_app, width):
        return DynamicAdvancedView.alloc().initWithDropboxApp_width_(dropbox_app, width)

    @objc.typedSelector('@@:@i')
    @event_handler
    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(DynamicAdvancedView, self).initWithDropboxApp_width_(dropbox_app, width)
        if self is None:
            return
        url_map = {'url': self._dropbox_app.dropbox_url_info.help_url('open_source_software')}
        label = pref_strings.open_source_label % url_map
        self.link = TextFieldWithLink(label, max_width=None, font=None, center=False, bold=False, size_diff=-2)
        self.addSubview_(self.link)
        self.createAdvancedView()
        self.layout()
        return self

    def createAdvancedView(self):
        if self._dropbox_app.mbox.enabled:
            self.advancedView = InnerAdvancedViewWithSecondary(self._dropbox_app)
        else:
            self.advancedView = InnerAdvancedView(self._dropbox_app)
        self.addSubview_(self.advancedView)

    def isFlipped(self):
        return YES

    @objc.typedSelector('v@:@')
    @event_handler
    def postLink(self):
        self.advancedView.postLink()

    @objc.typedSelector('v@:')
    @event_handler
    def settingsChanged(self):
        self.layout()

    @objc.typedSelector('v@:@')
    @event_handler
    def selsyncLauncherChangedFrame_(self, notification):
        notification_center = NSNotificationCenter.defaultCenter()
        notification_center.removeObserver_name_object_(self, NSViewFrameDidChangeNotification, self.selsyncLauncher)
        self.layout()
        notification_center.addObserver_selector_name_object_(self, self.selsyncLauncherChangedFrame_.selector, NSViewFrameDidChangeNotification, self.selsyncLauncher)

    def layout(self):
        if isinstance(self.advancedView, InnerAdvancedViewWithSecondary) != self._dropbox_app.mbox.enabled:
            self.advancedView.removeFromSuperview()
            self.createAdvancedView()
        self.setFrameSize_(NSSize(self._width, 0))
        height_needed = CONTENT_BORDER
        self.advancedView.setFrameOrigin_(NSPoint(0, height_needed))
        self.advancedView.centerHorizontallyInSuperview()
        height_needed += NSHeight(self.advancedView.frame())
        self.helpButton.alignRightInSuperview()
        height_needed += NSHeight(self.helpButton.frame())
        height_needed += CONTENT_BORDER
        self.setFrameSize_(NSSize(self._width, height_needed))
        advanced_frame = self.frame()
        x = advanced_frame.origin.x + CONTENT_BORDER
        y = advanced_frame.origin.y + advanced_frame.size.height - CONTENT_BORDER - self.link.frame().size.height
        self.link.setFrameOrigin_(NSPoint(x, y))
        self.helpButton.alignBottomInSuperview()

    def dealloc(self):
        try:
            notification_center = NSNotificationCenter.defaultCenter()
            notification_center.removeObserver_name_object_(self, NSViewFrameDidChangeNotification, self.selsyncLauncher)
        except:
            unhandled_exc_handler()
        finally:
            super(DynamicAdvancedView, self).dealloc()


class GeneralCheckboxesSubview(CheckboxView):

    def __new__(cls, dropbox_app):
        return GeneralCheckboxesSubview.alloc().initWithDropboxApp_(dropbox_app)

    def initWithDropboxApp_(self, dropbox_app):
        self = super(GeneralCheckboxesSubview, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self._dropbox_app = dropbox_app
            self.layout()
        return self

    def layout(self):
        subviews = list(self.subviews())
        for view in subviews:
            view.removeFromSuperview()

        options = [(OPT_BUBBLES, pref_strings.show_bubbles, self.setBubbles_), (OPT_LEOPARD, pref_strings.leopard_icons, self.setLeopardIcons_), (OPT_STARTUP, pref_strings.startup_item, self.setStartup_)]
        self.layoutCheckboxView(options, 0, 0)

    @objc.typedSelector('v@:@')
    @event_handler
    def setLeopardIcons_(self, sender):
        self._dropbox_app.pref_controller.update({OPT_LEOPARD: sender.state() == NSOnState})

    @objc.typedSelector('v@:@')
    @event_handler
    def setStartup_(self, sender):
        self._dropbox_app.pref_controller.update({OPT_STARTUP: sender.state() == NSOnState})

    @objc.typedSelector('v@:@')
    @event_handler
    def setBubbles_(self, sender):
        self._dropbox_app.pref_controller.update({OPT_BUBBLES: sender.state() == NSOnState})


class DynamicGeneralView(PrefView):
    checkboxesSubview = ivar('checkboxesSubview')

    def __new__(cls, dropbox_app, width):
        return DynamicGeneralView.alloc().initWithDropboxApp_width_(dropbox_app, width)

    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(DynamicGeneralView, self).initWithDropboxApp_width_(dropbox_app, width)
        if self is None:
            return
        self.checkboxesSubview = GeneralCheckboxesSubview(dropbox_app)
        self.addSubview_(self.checkboxesSubview)
        self.layout()
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def quitDropbox_(self, sender):
        arch.util.hard_exit()

    def layout(self):
        height_needed = self.initialHeightNeeded_()
        self.checkboxesSubview.setFrameOrigin_(NSPoint(0, height_needed))
        align_center_to_offset(self.checkboxesSubview, self._width / 2.0)
        height_needed += self.checkboxesSubview.frame().size.height
        height_needed += CONTENT_BORDER
        self.setFrameSize_(NSSize(self._width, height_needed))
        self.helpButton.alignBottomInSuperview()


class InnerImportView(CheckboxView):

    def __new__(cls, dropbox_app):
        return InnerImportView.alloc().initWithDropboxApp_(dropbox_app)

    def initWithDropboxApp_(self, dropbox_app):
        self = super(InnerImportView, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self._dropbox_app = dropbox_app
            self.layout()
        return self

    def layout(self):
        subviews = list(self.subviews())
        for view in subviews:
            view.removeFromSuperview()

        height_needed = 0
        width_needed = 0
        iphoto_importer = self._dropbox_app.stuff_importer
        if iphoto_importer:
            import_from_iphoto, _ = iphoto_importer.show_import_button(self._dropbox_app)
            if import_from_iphoto:
                self._iphoto_import_button = NSButton.createNormalRoundButtonWithTitle_(pref_strings.iphoto_import_button)
                self._iphoto_import_button.setTarget_(self)
                self._iphoto_import_button.setAction_(self.importFromIPhoto_)
                self._iphoto_import_button.setFrameOrigin_(NSPoint(BUTTON_LEFT_ALIGNMENT_OFFSET, height_needed))
                width_needed = max(NSWidth(self._iphoto_import_button.frame()), width_needed)
                height_needed += NSHeight(self._iphoto_import_button.frame()) + NEARBY_CONTROL_BORDER
                self.addSubview_(self._iphoto_import_button)
        options = []
        if arch.photouploader.USE_PHOTOUPLOADER:
            options.append((OPT_PHOTO, pref_strings.photo_import_enabled, self.setPhoto_))
        self.multiaccount_button = None
        use_screenshots = feature_enabled('screenshots') and ScreenshotsController.is_supported(self._dropbox_app)
        if use_screenshots and not self._dropbox_app.mbox.enabled:
            options.append((OPT_SCREENSHOTS, pref_strings.screenshots, self.setScreenshots_))
        if not use_screenshots or not self._dropbox_app.mbox.enabled:
            self.layoutCheckboxView(options, width_needed, height_needed)
        else:
            app = self._dropbox_app
            mbox = app.mbox
            checkbox_state, role = ScreenshotsController.current_prefs_state(app)
            state = NSOnState if checkbox_state else NSOffState
            height_needed = max(height_needed, 2)
            width_needed, height_needed = self.addSingleOption(pref_strings.screenshots_multiaccount, OPT_SCREENSHOTS, state, self.setScreenshots_, width_needed, height_needed)
            checkbox = self.key_to_checkbox[OPT_SCREENSHOTS]
            checkbox_frame = checkbox.frame()
            selections = [mbox.account_labels_plain_long.personal, mbox.account_labels_plain_long.business]
            default = 0 if role == Roles.PERSONAL else 1
            SELECTOR_MAX_WIDTH = 400
            CHECKBOX_OFFSET = 14
            BUTTON_SPACING = 8
            button = NSPopUpButton.createNormalPopUpButtonWithChoices_default_(selections, default)
            self.multiaccount_button = button
            button.sizeToFit()
            button.setTarget_(self)
            button.setAction_(self.setScreenshots_)
            self.addSubview_(button)
            if checkbox_frame.size.width + button.frame().size.width > SELECTOR_MAX_WIDTH:
                extra_height = button.frame().size.height + BUTTON_SPACING
                button.setFrameOrigin_(NSPoint(checkbox_frame.origin.x + CHECKBOX_OFFSET, checkbox_frame.origin.y + button.frame().size.height - checkbox_frame.size.height))
                checkbox.setFrameOrigin_(NSPoint(checkbox_frame.origin.x, checkbox_frame.origin.y + extra_height))
                height_needed += extra_height
                width_needed = max(width_needed, button.frame().size.width)
            else:
                button.setFrameOrigin_(NSPoint(checkbox_frame.origin.x + checkbox_frame.size.width, checkbox_frame.origin.y - (button.frame().size.height - checkbox_frame.size.height) / 2.0 - 1.0))
                width_needed = max(width_needed, button.frame().size.width + checkbox_frame.size.width)
            self.layoutCheckboxView(options, width_needed, height_needed, clear_key_to_checkbox=False)

    @objc.typedSelector('v@:@')
    @event_handler
    def importFromIPhoto_(self, sender):
        self._dropbox_app.stuff_importer.prompt_import()

    @objc.typedSelector('v@:@')
    @event_handler
    def setPhoto_(self, sender):
        if sender.state() == NSOnState and self._dropbox_app.mbox.is_dfb_user_without_linked_pair:
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), pref_strings.camera_upload_dialog_caption, None, lambda : self.set_camera_upload(True), lambda : self.key_to_checkbox[OPT_PHOTO].setState_(NSOffState), MiscStrings.yes_button, MiscStrings.no_button)
        else:
            self.set_camera_upload(sender.state() == NSOnState)

    def set_camera_upload(self, state):
        self._dropbox_app.pref_controller.update({OPT_PHOTO: state})

    @objc.typedSelector('v@:@')
    @event_handler
    def setScreenshots_(self, sender):
        role = None
        if self.multiaccount_button:
            role = Roles.PERSONAL if self.multiaccount_button.indexOfSelectedItem() == 0 else Roles.BUSINESS
        checkbox_state = self.key_to_checkbox[OPT_SCREENSHOTS].state()
        if self._dropbox_app.screenshots_controller:
            self._dropbox_app.screenshots_controller.update_from_prefs_window(checkbox_state == NSOnState, role)
        else:
            self._dropbox_app.pref_controller.update({OPT_SCREENSHOTS: ScreenshotsController.STATE_UNKNOWN if checkbox_state == NSOnState else ScreenshotsController.NEVER_SAVE})


class DynamicImportView(PrefView):

    def __new__(cls, dropbox_app, width):
        return DynamicImportView.alloc().initWithDropboxApp_width_(dropbox_app, width)

    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(DynamicImportView, self).initWithDropboxApp_width_(dropbox_app, width)
        if self is None:
            return
        self.checkboxesSubview = InnerImportView(dropbox_app)
        self.addSubview_(self.checkboxesSubview)
        self.layout()
        return self

    @objc.typedSelector('v@:')
    @event_handler
    def settingsChanged(self):
        self.checkboxesSubview.layout()
        self.layout()

    def layout(self):
        height_needed = self.initialHeightNeeded_()
        self.checkboxesSubview.setFrameOrigin_(NSPoint(0, height_needed))
        align_center_to_offset(self.checkboxesSubview, self._width / 2.0)
        height_needed += self.checkboxesSubview.frame().size.height
        height_needed += CONTENT_BORDER
        self.setFrameSize_(NSSize(self._width, height_needed))
        self.helpButton.alignBottomInSuperview()


class InnerBandwidthView(NSView):
    SPACE_BEFORE_STEPPER = 20

    def __new__(cls, dropbox_app):
        return cls.alloc().initWithFrame_DropboxApp_(NSZeroRect, dropbox_app)

    def initWithFrame_DropboxApp_(self, frame, dropbox_app):
        self = super(InnerBandwidthView, self).initWithFrame_(frame)
        if self is not None:
            self._dropbox_app = dropbox_app
            self.downloadLabel = NSTextField.createLabelWithText_(pref_strings.download_label)
            self.addSubview_(self.downloadLabel)
            self.downloadMatrix = NSMatrix.createRadioGroup_([pref_strings.dont_limit_download, pref_strings.speed_limit_download])
            self.downloadMatrix.setTarget_(self)
            self.downloadMatrix.setAction_(self.radioGroupAction_)
            self.addSubview_(self.downloadMatrix)
            self.downloadStepper = NumericStepper(1, 99999, pref_strings.rate_units, pref_strings.download_rate, pref_strings.invalid_download_rate)
            self.downloadStepper.setEnabled_(NO)
            self.addSubview_(self.downloadStepper)
            self.uploadLabel = NSTextField.createLabelWithText_(pref_strings.upload_label)
            self.addSubview_(self.uploadLabel)
            self.uploadMatrix = NSMatrix.createRadioGroup_([pref_strings.dont_limit_upload, pref_strings.auto_limit_upload, pref_strings.speed_limit_upload])
            self.uploadMatrix.setTarget_(self)
            self.uploadMatrix.setAction_(self.radioGroupAction_)
            self.addSubview_(self.uploadMatrix)
            self.uploadStepper = NumericStepper(1, 99999, pref_strings.rate_units, pref_strings.upload_rate, pref_strings.invalid_upload_rate)
            self.uploadStepper.setEnabled_(NO)
            self.addSubview_(self.uploadStepper)
            self._cancelButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.cancel_button, self.windowCancel_)
            self._cancelButton.setKeyEquivalent_(ESCAPE_KEY)
            self._okButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.window_ok_button, self.windowOk_)
            self._okButton.setKeyEquivalent_(ENTER_KEY)
            self.helpButton = help_button(0, 0)
            self.helpButton.setTarget_(self)
            self.helpButton.setAction_(self.userNeedsHelp_)
            self.addSubview_(self.helpButton)
            self.sizeToFit()
        return self

    def isFlipped(self):
        return YES

    @objc.typedSelector('v@:@@')
    @event_handler
    def beginSheet_forWindow_(self, sheet, window):
        self.relevantWindow = window
        self.relevantSheet = sheet
        NSApp().beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(sheet, window, self, self.sheetDidEnd_returnCode_contextInfo_.selector, 0)

    @objc.typedSelector('v@:@')
    @event_handler
    def windowOk_(self, sender):
        if self.downloadStyle() == 2 and not self.isDownloadValid():
            self.downloadStepper.tickleAlertSheet()
        elif self.uploadStyle() == 2 and not self.isUploadValid():
            self.uploadStepper.tickleAlertSheet()
        else:
            self.relevantSheet.savePreferences()
            NSApp().endSheet_(self.relevantSheet)

    @objc.typedSelector('v@:@')
    @event_handler
    def windowCancel_(self, sender):
        NSApp().endSheet_(self.relevantSheet)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def sheetDidEnd_returnCode_contextInfo_(self, sheet, returnCode, contextInfo):
        sheet.orderOut_(self)

    def sizeToFit(self):
        height_needed = CONTENT_BORDER
        width_needed = 0
        self.downloadLabel.setFrameOrigin_((CONTENT_BORDER, height_needed))
        self.downloadMatrix.placeRelativeToLabel_(self.downloadLabel)
        width_needed = max(width_needed, NSMaxX(self.downloadMatrix.frame()))
        height_needed += NSHeight(self.downloadMatrix.frame()) + self.downloadMatrix.verticalPadding()
        self.uploadLabel.setFrameOrigin_((NSMaxX(self.downloadLabel.frame()) - NSWidth(self.uploadLabel.frame()), height_needed))
        self.uploadMatrix.placeRelativeToLabel_(self.uploadLabel)
        width_needed = max(width_needed, NSMaxX(self.uploadMatrix.frame()))
        height_needed += NSHeight(self.uploadMatrix.frame()) + self.uploadMatrix.verticalPadding()
        width_needed += 5
        width_needed_for_radio = max(NSWidth(self.downloadMatrix.frame()), NSWidth(self.uploadMatrix.frame()))
        download_limit_cell = self.downloadMatrix.cells()[-1]
        dl_stepper_adjust = width_needed_for_radio - download_limit_cell.cellSize().width
        self.downloadStepper.setFrameOrigin_((width_needed - dl_stepper_adjust + self.SPACE_BEFORE_STEPPER, NSMaxY(self.downloadMatrix.frame()) + self.downloadStepper.baselineOffset() - NSHeight(self.downloadStepper.frame())))
        upload_limit_cell = self.uploadMatrix.cells()[-1]
        ul_stepper_adjust = width_needed_for_radio - upload_limit_cell.cellSize().width
        self.uploadStepper.setFrameOrigin_((width_needed - ul_stepper_adjust + self.SPACE_BEFORE_STEPPER, NSMaxY(self.uploadMatrix.frame()) + self.uploadStepper.baselineOffset() - NSHeight(self.uploadStepper.frame())))
        width_needed = max(width_needed, NSMaxX(self.downloadStepper.frame()), NSMaxX(self.uploadStepper.frame()))
        height_needed += NEARBY_CONTROL_BORDER
        self._cancelButton.setFrameOrigin_((CONTENT_BORDER, height_needed))
        button_size = self._okButton.frame().size
        self._okButton.setFrameOrigin_((width_needed - button_size.width, height_needed))
        height_needed += button_size.height + 10
        width_needed += CONTENT_BORDER
        self.setFrameSize_(NSSize(width_needed, height_needed))
        self.helpButton.alignLeftInSuperview()
        self.helpButton.alignBottomInSuperview()
        y = self.helpButton.frame().origin.y - BUTTON_TO_HELP_BUTTON_ADJUSTMENT_FLIPPED
        self._okButton.alignRightInSuperview()
        x = self._okButton.frame().origin.x
        self._okButton.setFrameOrigin_((x, y))
        x -= self._cancelButton.frame().size.width + HORIZ_BUTTON_SPACING
        self._cancelButton.setFrameOrigin_((x, y))

    def radioGroupAction_(self, sender):
        if sender is self.downloadMatrix:
            self.downloadStepper.setEnabled_(sender.selectedCell().tag() == 1)
        else:
            self.uploadStepper.setEnabled_(sender.selectedCell().tag() == 2)

    def setDownloadSpeed_(self, speed):
        self.downloadStepper.setIntValue_(speed)

    def downloadSpeed(self):
        return float(self.downloadStepper.intValue())

    def setUploadSpeed_(self, speed):
        self.uploadStepper.setIntValue_(speed)

    def uploadSpeed(self):
        return float(self.uploadStepper.intValue())

    def setDownloadStyle_(self, style):
        assert style in range(3)
        translated_style = 1 if style == 2 else 0
        self.downloadMatrix.selectCellWithTag_(translated_style)
        self.downloadMatrix.sendAction_to_(self.downloadMatrix.action(), None)

    def downloadStyle(self):
        if self.downloadMatrix.selectedCell().tag() == 1:
            return 2
        return 0

    def setUploadStyle_(self, style):
        assert style in range(3)
        self.uploadMatrix.selectCellWithTag_(style)
        self.uploadMatrix.sendAction_to_(self.uploadMatrix.action(), None)

    def uploadStyle(self):
        return self.uploadMatrix.selectedCell().tag()

    def isDownloadValid(self):
        return self.downloadStepper.isValid()

    def isUploadValid(self):
        return self.uploadStepper.isValid()

    @objc.typedSelector('v@:@')
    @event_handler
    def userNeedsHelp_(self, sender):
        helpForPane_DropboxApp_('bandwidth', self._dropbox_app)


class InnerProxiesView(NSView):

    def __new__(cls, dropbox_app):
        return cls.alloc().initWithFrame_DropboxApp_(NSZeroRect, dropbox_app)

    def initWithFrame_DropboxApp_(self, frame, dropbox_app):
        self = super(InnerProxiesView, self).initWithFrame_(frame)
        if self is not None:
            self._dropbox_app = dropbox_app
            self.proxySettingsLabel = NSTextField.createLabelWithText_(pref_strings.proxy_settings_label)
            self.addSubview_(self.proxySettingsLabel)
            self.proxySettingsMatrix = NSMatrix.createRadioGroup_([pref_strings.no_proxy_choice, pref_strings.auto_proxy_choice, pref_strings.manual_proxy_choice])
            self.proxySettingsMatrix.setTarget_(self)
            self.proxySettingsMatrix.setAction_(self.radioGroupAction_)
            self.addSubview_(self.proxySettingsMatrix)
            self.proxyTypeLabel = NSTextField.createLabelWithText_(pref_strings.proxy_type_label)
            self.addSubview_(self.proxyTypeLabel)
            self.proxyTypePopup = NSPopUpButton.createNormalPopUpButtonWithChoices_default_([HTTP, SOCKS4, SOCKS5], 0)
            self.proxyTypePopup.setAutoenablesItems_(NO)
            self.addSubview_(self.proxyTypePopup)
            self.proxyServerLabel = NSTextField.createLabelWithText_(pref_strings.proxy_server_label)
            self.addSubview_(self.proxyServerLabel)
            self.proxyServerTextField = NSTextField.createNormalTextField()
            self.proxyServerTextField.setFrameSize_((200, NSHeight(self.proxyServerTextField.frame())))
            self.addSubview_(self.proxyServerTextField)
            self.colonLabel = NSTextField.createLabelWithText_(':')
            self.addSubview_(self.colonLabel)
            self.proxyPortTextField = NSTextField.createNormalTextField()
            self.proxyPortTextField.setStringValue_('8080')
            self.proxyPortTextField.setDelegate_(self)
            self.proxyPortTextField.setFrame_(NSRect((0, self.proxyPortTextField.baselineOffset()), (56, NSHeight(self.proxyPortTextField.frame()))))
            formatter = NSNumberFormatter.alloc().init()
            formatter.setFormatterBehavior_(1040)
            formatter.setMinimum_(1)
            formatter.setMaximum_(65535)
            formatter.setNumberStyle_(1)
            formatter.setUsesGroupingSeparator_(NO)
            self.proxyPortTextField.setFormatter_(formatter)
            self.addSubview_(self.proxyPortTextField)
            self.proxyRequiresPassword = NSButton.createNormalCheckboxWithTitle_(pref_strings.proxy_requires_password_checkbox)
            self.proxyRequiresPassword.setTarget_(self)
            self.proxyRequiresPassword.setAction_(self.checkboxAction_)
            self.addSubview_(self.proxyRequiresPassword)
            self.usernameLabel = NSTextField.createLabelWithText_(pref_strings.proxy_username_label)
            self.addSubview_(self.usernameLabel)
            self.usernameTextField = NSTextField.createNormalTextField()
            self.usernameTextField.setFrameSize_((200, NSHeight(self.usernameTextField.frame())))
            self.addSubview_(self.usernameTextField)
            self.passwordLabel = NSTextField.createLabelWithText_(pref_strings.proxy_password_label)
            self.addSubview_(self.passwordLabel)
            self.passwordTextField = NSSecureTextField.createNormalSecureTextField()
            self.passwordTextField.setFrameSize_((200, NSHeight(self.passwordTextField.frame())))
            self.addSubview_(self.passwordTextField)
            self.non_login_controls = [self.proxyTypePopup,
             self.proxyServerTextField,
             self.proxyPortTextField,
             self.proxyRequiresPassword]
            self.non_login_labels = [self.proxyTypeLabel, self.proxyServerLabel, self.colonLabel]
            self.login_controls = [self.usernameTextField, self.passwordTextField]
            self.login_labels = [self.usernameLabel, self.passwordLabel]
            self._cancelButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.cancel_button, self.windowCancel_)
            self._cancelButton.setKeyEquivalent_(ESCAPE_KEY)
            self._okButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.window_ok_button, self.windowOk_)
            self._okButton.setKeyEquivalent_(ENTER_KEY)
            self.helpButton = help_button(0, 0)
            self.helpButton.setTarget_(self)
            self.helpButton.setAction_(self.userNeedsHelp_)
            self.addSubview_(self.helpButton)
            self.sizeToFit()
        return self

    def isFlipped(self):
        return YES

    @objc.typedSelector('v@:@@')
    @event_handler
    def beginSheet_forWindow_(self, sheet, window):
        self.relevantWindow = window
        self.relevantSheet = sheet
        NSApp().beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(sheet, window, self, self.sheetDidEnd_returnCode_contextInfo_.selector, 0)

    @objc.typedSelector('v@:@')
    @event_handler
    def windowOk_(self, sender):
        if self.proxyMode() == 2 and not self.portIsValid():
            self.tickleAlertSheetForPort()
        elif self.proxyMode() == 2 and not self.proxyServer().strip():
            NSBeginAlertSheet(pref_strings.proxy_server_not_set, MiscStrings.ok_button, None, None, self.window(), self, None, None, 0, '%@', pref_strings.proxy_server_not_set_explanation)
        else:
            self.relevantSheet.savePreferences()
            NSApp().endSheet_(self.relevantSheet)

    @objc.typedSelector('v@:@')
    @event_handler
    def windowCancel_(self, sender):
        NSApp().endSheet_(self.relevantSheet)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def sheetDidEnd_returnCode_contextInfo_(self, sheet, returnCode, contextInfo):
        sheet.orderOut_(self)

    def sizeToFit(self):
        height_needed = CONTENT_BORDER
        width_needed = 0
        max_label_x = max(NSWidth(self.proxySettingsLabel.frame()), NSWidth(self.proxyTypeLabel.frame()), NSWidth(self.proxyServerLabel.frame()))
        max_label_x += CONTENT_BORDER
        self.proxySettingsLabel.setFrameOrigin_((max_label_x - NSWidth(self.proxySettingsLabel.frame()), height_needed))
        self.proxySettingsMatrix.placeRelativeToLabel_(self.proxySettingsLabel)
        width_needed = max(width_needed, NSMaxX(self.proxySettingsMatrix.frame()))
        height_needed = self.proxySettingsMatrix.nextControlY()
        self.proxyTypeLabel.setFrameOrigin_((max_label_x - NSWidth(self.proxyTypeLabel.frame()), height_needed))
        self.proxyTypePopup.placeRelativeToLabel_(self.proxyTypeLabel)
        width_needed = max(width_needed, NSMaxX(self.proxyTypePopup.frame()))
        height_needed = self.proxyTypePopup.nextControlY()
        self.proxyServerLabel.setFrameOrigin_((max_label_x - NSWidth(self.proxyServerLabel.frame()), height_needed))
        self.proxyServerTextField.placeRelativeToLabel_(self.proxyServerLabel)
        self.proxyServerTextField.setDelegate_(self)
        self.colonLabel.setFrameOrigin_((NSMaxX(self.proxyServerTextField.frame()), self.proxyServerLabel.frame().origin.y))
        self.proxyPortTextField.placeRelativeToLabel_(self.colonLabel)
        self.proxyPortTextField.setFrameOrigin_((self.proxyPortTextField.frame().origin.x - self.colonLabel.horizontalPadding(), self.proxyPortTextField.frame().origin.y))
        width_needed = max(width_needed, NSMaxX(self.proxyPortTextField.frame()))
        height_needed = self.proxyServerTextField.nextControlY()
        self.proxyRequiresPassword.setFrameOrigin_((self.proxyServerTextField.frame().origin.x, height_needed))
        width_needed = max(width_needed, NSMaxX(self.proxyRequiresPassword.frame()))
        height_needed = self.proxyRequiresPassword.nextControlY()
        self.usernameLabel.setFrameOrigin_((max_label_x - NSWidth(self.usernameLabel.frame()), height_needed))
        self.usernameTextField.placeRelativeToLabel_(self.usernameLabel)
        self.usernameTextField.setDelegate_(self)
        width_needed = max(width_needed, NSMaxX(self.usernameTextField.frame()))
        height_needed = self.usernameTextField.nextControlY()
        self.passwordLabel.setFrameOrigin_((max_label_x - NSWidth(self.passwordLabel.frame()), height_needed))
        self.passwordTextField.placeRelativeToLabel_(self.passwordLabel)
        self.passwordTextField.setDelegate_(self)
        width_needed = max(width_needed, NSMaxX(self.passwordTextField.frame()))
        height_needed = self.passwordTextField.nextControlY()
        height_needed += NEARBY_CONTROL_BORDER
        button_size = self._okButton.frame().size
        height_needed += button_size.height + 10
        width_needed += CONTENT_BORDER
        self.setFrameSize_(NSSize(width_needed, height_needed))
        self.helpButton.alignLeftInSuperview()
        self.helpButton.alignBottomInSuperview()
        y = self.helpButton.frame().origin.y - BUTTON_TO_HELP_BUTTON_ADJUSTMENT_FLIPPED
        self._okButton.alignRightInSuperview()
        x = self._okButton.frame().origin.x
        self._okButton.setFrameOrigin_((x, y))
        x -= self._cancelButton.frame().size.width + HORIZ_BUTTON_SPACING
        self._cancelButton.setFrameOrigin_((x, y))

    def portIsValid(self):
        text = self.proxyPortTextField.stringValue()
        valid, number, error = self.proxyPortTextField.formatter().getObjectValue_forString_errorDescription_(None, text, None)
        return valid

    def safePortValue_(self, value):
        valid, number, error = self.proxyPortTextField.formatter().getObjectValue_forString_errorDescription_(None, value, None)
        if valid:
            return number

    @objc.typedSelector('v@:@')
    @event_handler
    def checkboxAction_(self, sender):
        for c in self.login_controls:
            c.setEnabled_(sender.state())

        for c in self.login_labels:
            c.setTextColor_(NSColor.controlTextColor() if sender.state() else NSColor.disabledControlTextColor())

    @objc.typedSelector('v@:@')
    @event_handler
    def radioGroupAction_(self, sender):
        t = sender.selectedCell().tag()
        if t is 0 or t is 1:
            for c in self.non_login_controls + self.login_controls:
                c.setEnabled_(NO)

            for c in self.non_login_labels + self.login_labels:
                c.setTextColor_(NSColor.disabledControlTextColor())

        else:
            for c in self.non_login_controls:
                c.setEnabled_(YES)

            for c in self.non_login_labels:
                c.setTextColor_(NSColor.controlTextColor())

            self.checkboxAction_(self.proxyRequiresPassword)

    def proxyMode(self):
        return self.proxySettingsMatrix.selectedCell().tag()

    def setProxyMode_(self, proxy_mode):
        assert proxy_mode in range(3)
        self.proxySettingsMatrix.selectCellWithTag_(proxy_mode)
        self.proxySettingsMatrix.sendAction_to_(self.proxySettingsMatrix.action(), None)

    def proxyType(self):
        return self.proxyTypePopup.selectedItem().title()

    def setProxyType_(self, proxy_type):
        self.proxyTypePopup.selectItemWithTitle_(proxy_type)

    def proxyServer(self):
        return self.proxyServerTextField.stringValue()

    def setProxyServer_(self, proxy_server):
        self.proxyServerTextField.setStringValue_(proxy_server)

    def proxyPort(self):
        return self.safePortValue_(self.proxyPortTextField.stringValue())

    def setProxyPort_(self, proxy_port):
        self.proxyPortTextField.setIntValue_(proxy_port)

    def proxyRequiresAuth(self):
        return self.proxyRequiresPassword.state()

    def setProxyRequiresAuth_(self, auth):
        self.proxyRequiresPassword.setState_(auth)
        self.proxyRequiresPassword.sendAction_to_(self.proxyRequiresPassword.action(), self)

    def username(self):
        return self.usernameTextField.stringValue()

    def setUsername_(self, username):
        self.usernameTextField.setStringValue_(username)

    def password(self):
        return self.passwordTextField.stringValue()

    def setPassword_(self, password):
        self.passwordTextField.setStringValue_(password)

    def tickleAlertSheetForPort(self):
        text = self.proxyPortTextField.stringValue()
        valid, number, error = self.proxyPortTextField.formatter().getObjectValue_forString_errorDescription_(None, text, None)
        if not valid:
            self.control_didFailToFormatString_errorDescription_(None, None, error)

    def control_didFailToFormatString_errorDescription_(self, control, string, error):
        NSBeginAlertSheet(pref_strings.invalid_port, MiscStrings.ok_button, None, None, self.window(), self, None, None, 0, '%@', error)
        return NO

    @objc.typedSelector('v@:@')
    @event_handler
    def userNeedsHelp_(self, sender):
        helpForPane_DropboxApp_('proxies', self._dropbox_app)


class PrefWindowToolbarDelegate(NSObject):

    def __new__(cls, window, item_map):
        return PrefWindowToolbarDelegate.alloc().initWithWindow_itemMap_(window, item_map)

    def initWithWindow_itemMap_(self, window, item_map):
        self = super(PrefWindowToolbarDelegate, self).init()
        if self is None:
            return
        self._window = window
        self._item_map = dict(item_map)
        self._item_identifiers = [ k for k, v in item_map ]
        return self

    @objc.typedSelector('@@:@@c')
    @event_handler
    def toolbar_itemForItemIdentifier_willBeInsertedIntoToolbar_(self, toolbar, identifier, insert):
        if identifier not in self._item_map:
            return None
        general_item = NSToolbarItem.alloc().initWithItemIdentifier_(identifier)
        general_item.setLabel_(self._item_map[identifier]['label'])
        general_item.setImage_(self._item_map[identifier]['image'])
        general_item.setTarget_(self._window)
        general_item.setAction_(self._item_map[identifier]['action'])
        return general_item

    @objc.typedSelector('@@:@')
    @event_handler
    def toolbarAllowedItemIdentifiers_(self, toolbar):
        return self._item_identifiers

    @objc.typedSelector('@@:@')
    @event_handler
    def toolbarDefaultItemIdentifiers_(self, toolbar):
        return self._item_identifiers

    @objc.typedSelector('@@:@')
    @event_handler
    def toolbarSelectableItemIdentifiers_(self, toolbar):
        return self._item_identifiers


class PrefWindow(NSWindow):

    def __new__(cls, dropbox_app, close_callback):
        return PrefWindow.alloc().initWithDropboxApp_closeCallback_(dropbox_app, close_callback)

    def initWithDropboxApp_closeCallback_(self, dropbox_app, close_callback):
        self = super(PrefWindow, self).initWithContentRect_styleMask_backing_defer_(NSRect((0, 0), (PREF_WINDOW_WIDTH, 0)), NSTitledWindowMask | NSClosableWindowMask, NSBackingStoreBuffered, YES)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        self._sync_engine = dropbox_app.sync_engine
        width = PREF_WINDOW_WIDTH
        TRACE("PrefWindow thinks it's %r px wide", width)
        self._network_view = DynamicNetworkView(self._dropbox_app, width)
        self._general_view = DynamicGeneralView(self._dropbox_app, width)
        self._account_view = DynamicAccountView(self._dropbox_app, width)
        self._advanced_view = DynamicAdvancedView(self._dropbox_app, width)
        self._import_view = DynamicImportView(self._dropbox_app, width)
        self._all_views = (self._general_view,
         self._account_view,
         self._import_view,
         self._network_view,
         self._advanced_view)
        self._name_to_view = {PanelNames.GENERAL: self._general_view,
         PanelNames.ACCOUNT: self._account_view,
         PanelNames.IMPORT: self._import_view,
         PanelNames.NETWORK: self._network_view,
         PanelNames.ADVANCED: self._advanced_view}
        self._close_callback = close_callback
        self.setReleasedWhenClosed_(NO)
        self.setShowsToolbarButton_(NO)
        self.setLevel_(NSFloatingWindowLevel)
        dropbox_app.ui_kit.add_sync_engine_handler(self.setSyncEngine_)
        dropbox_app.ui_kit.add_post_link_handler(self.postLink)
        dropbox_app.mbox.on_secondary_link.add_handler(self.onSecondaryLink_)
        toolbar, self._toolbar_delegate = self.makeToolbar()
        self.setToolbar_(toolbar)
        return self

    @objc.typedSelector('v@:@')
    @message_sender(AppHelper.callAfter)
    def setSyncEngine_(self, sync_engine):
        self._sync_engine = sync_engine

    @objc.typedSelector('v@:')
    @message_sender(AppHelper.callAfter)
    def postLink(self):
        self._advanced_view.postLink()

    @objc.typedSelector('v@:@')
    @message_sender(AppHelper.callAfter)
    def onSecondaryLink_(self, arg):
        for view in self._name_to_view.itervalues():
            view.settingsChanged()

    @objc.typedSelector('v@:@')
    @message_sender(AppHelper.callAfter)
    def refreshSettings(self, view_name):
        TRACE('REFRESH SETTINGS: %s' % view_name)
        if view_name in self._name_to_view:
            self._name_to_view[view_name].settingsChanged()

    def wantsDropboxWindowMenuEvents(self):
        return True

    @objc.typedSelector('v@:@')
    @event_handler
    def switchToView_(self, view):
        notification_center = NSNotificationCenter.defaultCenter()
        old_content_rect = self.contentRectForFrameRect_(self.frame())
        subviews = list(self.contentView().subviews())
        for existing_view in subviews:
            notification_center.removeObserver_name_object_(self, NSViewFrameDidChangeNotification, existing_view)
            existing_view.removeFromSuperview()

        self.toolbar().setSelectedItemIdentifier_(self.identifierForView(view))
        new_view_frame = view.frame()
        r = NSRect((old_content_rect.origin.x, old_content_rect.origin.y + old_content_rect.size.height - new_view_frame.size.height), (new_view_frame.size.width, new_view_frame.size.height))
        TRACE('PrefWindow changing size to %r because new view frame is %r', r, new_view_frame)
        self.setFrame_display_animate_(self.frameRectForContentRect_(r), YES, YES)
        self.contentView().addSubview_(view)
        self.setTitle_(self.titleForView(view))
        notification_center.addObserver_selector_name_object_(self, self.contentViewChangedFrameNotification_.selector, NSViewFrameDidChangeNotification, view)
        self.makeFirstResponder_(view)
        self.recalculateKeyViewLoop()
        self.selectNextKeyView_(self)
        TRACE('switching to view %r %r', new_view_frame, view)

    @objc.typedSelector('v@:@')
    @event_handler
    def contentViewChangedFrameNotification_(self, notification):
        self.switchToView_(self.contentView().subviews()[0])

    @objc.typedSelector('v@:')
    @event_handler
    def switchToGeneral(self):
        self.switchToView_(self._general_view)

    @objc.typedSelector('v@:')
    @event_handler
    def switchToAccount(self):
        self.switchToView_(self._account_view)

    @objc.typedSelector('v@:')
    @event_handler
    def switchToImport(self):
        self.switchToView_(self._import_view)

    @objc.typedSelector('v@:')
    @event_handler
    def switchToNetwork(self):
        self.switchToView_(self._network_view)

    @objc.typedSelector('v@:')
    @event_handler
    def switchToAdvanced(self):
        self.switchToView_(self._advanced_view)

    @objc.typedSelector('@@:@')
    @event_handler
    def identifierForView(self, theView):
        return {self._general_view: 'com.dropbox.preferences.toolbaritem.general',
         self._account_view: 'com.dropbox.preferences.toolbaritem.account',
         self._import_view: 'com.dropbox.preferences.toolbaritem.import',
         self._network_view: 'com.dropbox.preferences.toolbaritem.network',
         self._advanced_view: 'com.dropbox.preferences.toolbaritem.advanced'}[theView]

    @objc.typedSelector('@@:@')
    @event_handler
    def titleForView(self, theView):
        return {self._general_view: pref_strings.main_tab_label,
         self._account_view: pref_strings.account_tab_label,
         self._import_view: pref_strings.import_tab_label,
         self._network_view: pref_strings.network_tab_label,
         self._advanced_view: pref_strings.advanced_tab_label}[theView]

    def makeToolbar(self):
        toolbar = NSToolbar.alloc().initWithIdentifier_('com.dropbox.preferences.toolbar')
        toolbar_delegate = PrefWindowToolbarDelegate(self, ((self.identifierForView(self._general_view), dict(label=pref_strings.main_tab_label, image=Images.PrefsMain, action='switchToGeneral')),
         (self.identifierForView(self._account_view), dict(label=pref_strings.account_tab_label, image=Images.PrefsAccount, action='switchToAccount')),
         (self.identifierForView(self._import_view), dict(label=pref_strings.import_tab_label, image=Images.PrefsImport, action='switchToImport')),
         (self.identifierForView(self._network_view), dict(label=pref_strings.network_tab_label, image=Images.PrefsNetwork, action='switchToNetwork')),
         (self.identifierForView(self._advanced_view), dict(label=pref_strings.advanced_tab_label, image=Images.PrefsAdvanced, action='switchToAdvanced'))))
        toolbar.setDelegate_(toolbar_delegate)
        toolbar.setAllowsUserCustomization_(NO)
        return (toolbar, toolbar_delegate)

    @objc.typedSelector('c@:@')
    @event_handler
    def windowShouldClose_(self, sender):
        self._close_callback()
        return YES

    @objc.typedSelector('v@:@')
    @event_handler
    def userNeedsHelp_(self, sender):
        toolbar_id = self.identifierForView(self.contentView().subviews()[0])
        pane = toolbar_id.rsplit('.', 1)[1]
        helpForPane_DropboxApp_(pane, self._dropbox_app)


def helpForPane_DropboxApp_(pane, dropbox_app):
    help_url = 'prefs/mac/%s' % (pane,)
    dropbox_app.dropbox_url_info.launch_full_url(dropbox_app.dropbox_url_info.help_url(help_url))


class PrefWindowController(object):

    def __init__(self, dropbox_app):
        self._dropbox_app = dropbox_app
        self._pref_window = None
        self.syncEngine = None

    @event_handler
    def setSyncEngine_(self, sync_engine):
        self.syncEngine = sync_engine
        if self._pref_window:
            self._pref_window.setSyncEngine_(sync_engine)

    @event_handler
    def windowClosed(self):
        pass

    @event_handler
    def refresh_panel(self, panel):
        if self._pref_window:
            self._pref_window.refreshSettings(panel)

    @event_handler
    def show_user(self, viewname = None):
        if viewname is None:
            viewname = 'general'
        enter_proxies = False
        if viewname == 'proxies':
            viewname = 'network'
            enter_proxies = True
        just_made = False
        if not self._pref_window:
            TRACE('making pref window')
            self._pref_window = PrefWindow(self._dropbox_app, self.windowClosed)
            if self.syncEngine:
                self._pref_window.setSyncEngine_(self.syncEngine)
            just_made = True
        try:
            view = self._pref_window._name_to_view[viewname]
            self._pref_window.switchToView_(view)
        except KeyError:
            unhandled_exc_handler()
            return

        TRACE('bringing pref window forward')
        if just_made:
            self._pref_window.center()
        self._pref_window.makeKeyAndOrderFront_(self)
        self._pref_window.orderFrontRegardless()
        TRACE('pref window showing at: %r %r' % (self._pref_window.frame(), self._pref_window.screen()))
        if enter_proxies:
            view.show_proxy_sheet()
