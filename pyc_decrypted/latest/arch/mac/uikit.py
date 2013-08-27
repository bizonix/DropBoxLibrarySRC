#Embedded file name: arch/mac/uikit.py
import threading
import functools
from PyObjCTools import AppHelper
from AppKit import NSPasteboard, NSThread, NSStringPboardType
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.low_functions import add_inner_methods
from dropbox.mac.internal import show_finder_popup
from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.cocoa.uikit import CocoaUIKit
from ui.common.tray import TrayOptionStrings
from ui.common.setupwizard import ConnectionTrouble, WelcomePanel, LoginPanel
from ui.common.uikit import PlatformUIKitBase
from .idletracker import IdleTracker

@add_inner_methods('is_trackable', 'seconds_idle', inner_name='idletracker')

class PlatformUIKit(PlatformUIKitBase):

    def __init__(self, app):
        PlatformUIKitBase.__init__(self, app)
        result = False
        if MAC_VERSION > SNOW_LEOPARD:
            result = True
        elif MAC_VERSION == SNOW_LEOPARD:
            if MAC_VERSION.point_release >= 8:
                result = True
        self.using_xui = result
        self.cocoa_ui_kit = CocoaUIKit(self.app, self.using_xui)
        self.show_alert_dialog = self.cocoa_ui_kit.show_alert_dialog
        self.idletracker = IdleTracker()
        try:
            self.enter_demo = self.cocoa_ui_kit.enter_demo
        except:
            pass

        self.create_camera_ui = self.cocoa_ui_kit.create_camera_ui
        self.get_text_from_clipboard = self.cocoa_ui_kit.get_text_from_clipboard

    def set_prefs(self, prefs):
        self.prefs = prefs
        self.cocoa_ui_kit.set_prefs(prefs)
        self.app.tray_controller.add_callbacks_for_options({TrayOptionStrings.preferences_dotdotdot: self.enter_preferences})

    def enter_preferences(self, panel = None):
        self.cocoa_ui_kit.enter_preferences(panel)

    def refresh_panel(self, panel):
        self.cocoa_ui_kit.refresh_panel(panel)

    def enter_proxy_settings(self):
        self.cocoa_ui_kit.enter_proxy_settings()

    def enter_setupwizard(self, panel, linked_event, force = True, definitely_connected = False, should_raise = True, **kw):
        self.cocoa_ui_kit.enter_setupwizard(panel, linked_event, force, definitely_connected, should_raise, functools.partial(self.enter_preferences, 'proxies'), self.start_tray_arrow, self.stop_tray_arrow, **kw)

    def enter_setupwizkit(self, linked_event, definitely_connected = False, connection_error = False, **kw):
        try:
            self.cocoa_ui_kit.enter_setupwizkit(linked_event, functools.partial(self.enter_preferences, 'proxies'), definitely_connected, connection_error, **kw)
        except Exception:
            unhandled_exc_handler()
            self.cocoa_ui_kit.wizkit = None
            self.cocoa_ui_kit.wizkit_controller = None
            if connection_error:
                self.enter_setupwizard(ConnectionTrouble, linked_event, force=True)
            else:
                login_only = kw.get('login_only', False)
                email = kw.get('email_address', None)
                start_panel = LoginPanel if login_only else WelcomePanel
                self.enter_setupwizard(start_panel, linked_event, definitely_connected=definitely_connected, force=False, email_address=email)

    def setupwizard_should_register_wait(self):
        return self.cocoa_ui_kit.setupwizard_should_register_wait()

    def yield_setupwizard_successful_link(self, ret, when_done = None):
        return self.cocoa_ui_kit.yield_setupwizard_successful_link(ret, when_done=when_done)

    def start_tray_arrow(self):
        return self.cocoa_ui_kit.start_tray_arrow()

    def stop_tray_arrow(self):
        return self.cocoa_ui_kit.stop_tray_arrow()

    def create_progress_window(self, message, max_value):
        return self.cocoa_ui_kit.create_progress_window(message, max_value)

    @message_sender(AppHelper.callAfter, block=True)
    def copy_text_to_clipboard(self, text):
        assert type(text) is unicode
        TRACE('copying to clipboard: %r' % text)
        board = NSPasteboard.generalPasteboard()
        board.declareTypes_owner_([NSStringPboardType], None)
        board.setString_forType_(text, NSStringPboardType)

    def pass_message(self, f, *n, **kw):
        self.cocoa_ui_kit.pass_message(f, *n, **kw)

    @assert_message_queue
    def mainloop(self):
        try:
            NSThread.mainThread().setThreadPriority_(1.0)
        except AttributeError:
            pass
        except:
            unhandled_exc_handler()

        threading.currentThread().signal_stop = self.exit_mainloop
        self.cocoa_ui_kit.mainloop()

    def exit_mainloop(self):
        self.cocoa_ui_kit.exit_mainloop()

    def show_bubble(self, bubble):
        self.cocoa_ui_kit.show_bubble(bubble)

    def start_tray_icon(self):
        self.cocoa_ui_kit.start_tray_icon()

    def update_tray_icon(self, **kwargs):
        return self.cocoa_ui_kit.update_tray_icon(**kwargs)

    def update_options(self, options):
        self.cocoa_ui_kit.update_options(options)

    def show_tray_popup(self, context_menu = False):
        self.cocoa_ui_kit.show_tray_popup(context_menu)

    def move_tray_popup(self, rect):
        self.cocoa_ui_kit.move_tray_popup(rect)

    def hide_tray_popup(self):
        self.cocoa_ui_kit.hide_tray_popup()

    def update_notifications(self, *args, **kwargs):
        self.cocoa_ui_kit.update_notifications(*args, **kwargs)

    def update_status(self, *args, **kwargs):
        self.cocoa_ui_kit.update_status(*args, **kwargs)

    def show_screenshots_dialog(self, *args, **kwargs):
        return self.cocoa_ui_kit.show_screenshots_dialog(*args, **kwargs)

    def show_gallery_import_dialog(self, *args, **kwargs):
        return self.cocoa_ui_kit.show_gallery_import_dialog(*args, **kwargs)

    def show_dialog(self, **kwargs):
        caption = kwargs.pop('caption', None)
        msg = kwargs.pop('message')
        buttons = kwargs.pop('buttons', [])
        default_button = kwargs.pop('default_button', 0)
        cancel_button = kwargs.pop('cancel_button', -1)
        return show_finder_popup(caption, msg, buttons, default_button, cancel_button)

    def enable_multiaccount(self):
        self.cocoa_ui_kit.enable_multiaccount()

    def disable_multiaccount(self):
        self.cocoa_ui_kit.disable_multiaccount()
