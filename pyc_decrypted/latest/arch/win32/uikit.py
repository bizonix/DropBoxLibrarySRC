#Embedded file name: arch/win32/uikit.py
import threading
import functools
import win32clipboard
from dropbox.gui import assert_message_queue
from dropbox.low_functions import add_inner_methods
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.win32.version import WINXP, WINDOWS_VERSION
from ui.common.tray import TrayOptionStrings
from ui.common.setupwizard import ConnectionTrouble, WelcomePanel, LoginPanel
from ui.common.uikit import PlatformUIKitBase
from ui.wxpython.uikit import WxUIKit
from .idletracker import IdleTracker
from .tray_icon import TrayIcon

@add_inner_methods('is_trackable', 'seconds_idle', inner_name='idletracker')

class PlatformUIKit(PlatformUIKitBase):
    MAX_POPUP_ERRORS = 5

    def __init__(self, app):
        PlatformUIKitBase.__init__(self, app)
        self.using_xui = WINDOWS_VERSION >= WINXP
        self.popup_errors = 0
        self.wx_ui_kit = WxUIKit(self.app, self.using_xui)
        self.get_text_from_clipboard = self.wx_ui_kit.get_text_from_clipboard
        self.show_alert_dialog = self.wx_ui_kit.show_alert_dialog
        self.idletracker = IdleTracker()
        self.create_camera_ui = self.wx_ui_kit.create_camera_ui
        self._made_tray_visible = False
        self.tray_icon = TrayIcon(self.app)

    def set_prefs(self, prefs):
        self.wx_ui_kit.set_prefs(prefs)
        self.app.tray_controller.add_callbacks_for_options({TrayOptionStrings.preferences_dotdotdot: self.enter_preferences})

    def enter_setupwizkit(self, linked_event, definitely_connected = False, connection_error = False, **kw):
        try:
            self.wx_ui_kit.enter_setupwizkit(linked_event, functools.partial(self.enter_preferences, 'proxies'), definitely_connected, connection_error, **kw)
        except Exception:
            unhandled_exc_handler()
            self.wx_ui_kit.wizkit = None
            self.wx_ui_kit.wizkit_controller = None
            if connection_error:
                self.enter_setupwizard(ConnectionTrouble, linked_event, force=True)
            else:
                login_only = kw.get('login_only', False)
                email = kw.get('email_address', None)
                start_panel = LoginPanel if login_only else WelcomePanel
                self.enter_setupwizard(start_panel, linked_event, definitely_connected=definitely_connected, force=False, email_address=email)

    def enter_setupwizard(self, panel, linked_event, force = True, definitely_connected = False, should_raise = True, **kw):
        self.wx_ui_kit.enter_setupwizard(panel, linked_event, force, definitely_connected, should_raise, functools.partial(self.enter_preferences, 'proxies'), **kw)

    def setupwizard_should_register_wait(self):
        return self.wx_ui_kit.setupwizard_should_register_wait()

    def yield_setupwizard_successful_link(self, ret, when_done = None):
        return self.wx_ui_kit.yield_setupwizard_successful_link(ret, when_done=when_done)

    def start_tray_arrow(self):
        rect = self.tray_icon.get_screen_rect()
        if rect is None:
            report_bad_assumption('Failed to find an anchor for the tray arrow!')
            return
        return self.wx_ui_kit.start_tray_arrow(rect)

    def stop_tray_arrow(self):
        return self.wx_ui_kit.stop_tray_arrow()

    def create_progress_window(self, message, max_value):
        return self.wx_ui_kit.create_progress_window(message, max_value)

    def copy_text_to_clipboard(self, text):
        TRACE('copying to clipboard: %r' % text)
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            if text:
                win32clipboard.SetClipboardText(text)
        finally:
            win32clipboard.CloseClipboard()

    def enter_preferences(self, panel = None):
        self.wx_ui_kit.enter_preferences(panel)

    def refresh_panel(self, panel):
        self.wx_ui_kit.refresh_panel(panel)

    def enter_proxy_settings(self):
        self.wx_ui_kit.enter_proxy_settings()

    @assert_message_queue
    def mainloop(self):
        threading.currentThread().signal_stop = self.exit_mainloop
        self.wx_ui_kit.mainloop()

    def pass_message(self, f, *n, **kw):
        self.wx_ui_kit.pass_message(f, *n, **kw)

    def exit_mainloop(self):
        self.wx_ui_kit.exit_mainloop()

    def show_bubble(self, bubble):
        if not self.app.pref_controller['show_bubbles'] and not bubble.show_when_disabled:
            return
        try:
            if self.seconds_idle() > 300:
                TRACE('Bubble suppressed (user has been idle for more than 5 minutes): %r', bubble)
                return
        except Exception:
            unhandled_exc_handler()

        self.tray_icon.render_bubble(bubble)

    def start_tray_icon(self):
        try:
            self.tray_icon.enable(self)
        except Exception:
            unhandled_exc_handler()

    def update_tray_icon(self, **kwargs):
        return self.tray_icon.update_tray_icon(**kwargs)

    def update_options(self, options):
        self.tray_icon.update_tray_menu(options.values())
        if self.using_xui:
            self.wx_ui_kit.update_options(options)

    def show_tray_popup(self, context_menu = False):
        if not self.using_xui or context_menu:
            self.tray_icon.show_tray_menu()
            return
        try:
            rect = self.tray_icon.get_screen_rect()
            self.wx_ui_kit.show_tray_popup(rect)
        except Exception:
            self.popup_errors += 1
            if self.popup_errors >= self.MAX_POPUP_ERRORS:
                self.using_xui = False
                report_bad_assumption('Giving up on the tray popup!')
            unhandled_exc_handler()
            self.tray_icon.show_tray_menu()

    def move_tray_popup(self, rect):
        self.wx_ui_kit.move_tray_popup(rect)

    def hide_tray_popup(self):
        self.wx_ui_kit.hide_tray_popup()

    def update_notifications(self, *args, **kwargs):
        self.wx_ui_kit.update_notifications(*args, **kwargs)

    def update_status(self, *args, **kwargs):
        self.wx_ui_kit.update_status(*args, **kwargs)

    def show_screenshots_dialog(self, *args, **kwargs):
        self.wx_ui_kit.show_screenshots_dialog(*args, **kwargs)

    def show_gallery_import_dialog(self, *args, **kwargs):
        self.wx_ui_kit.show_gallery_import_dialog(*args, **kwargs)

    def show_dialog(self, **kwargs):
        return self.wx_ui_kit.show_dialog(**kwargs)

    def enable_multiaccount(self):
        self.wx_ui_kit.enable_multiaccount()

    def disable_multiaccount(self):
        self.wx_ui_kit.disable_multiaccount()
