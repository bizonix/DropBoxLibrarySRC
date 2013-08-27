#Embedded file name: ui/cocoa/uikit.py
from __future__ import absolute_import
import os
import threading
import traceback
import objc
from AppKit import NSApp, NSApplication, NSMenu, NSPasteboard, NSStringPboardType, NSUserDefaults
from ExceptionHandling import NSExceptionHandler, NSLogAndHandleEveryExceptionMask
from Foundation import NSObject
from PyObjCTools import AppHelper
import build_number
from dropbox.gui import message_sender, event_handler
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.features import feature_enabled
from ui.cocoa.bubble import Bubbler
from ui.cocoa.camera import CocoaCameraUI, get_gallery_import_splash
from ui.cocoa.dropbox_controls import DropboxDefaultMenuDelegate, ProgressWindow
from ui.cocoa.PrefWindow import PrefWindowController
from ui.cocoa.setupwizard import SetupWizardWindow
from ui.cocoa.tray_arrow import TrayArrow
from ui.cocoa.tray_icon import TrayIcon
from ui.common.setupwizard import SetupWizard
from ui.common.xui.tray_popup import TrayPopupController
from ui.cocoa.screenshots import ScreenshotsSplashScreen
import traceback
from ExceptionHandling import NSExceptionHandler, NSLogAndHandleEveryExceptionMask
from ui.common.xui.wizkit import WizkitController
from ui.cocoa.dialogs import showAlertDialogWithCaption_message_andButtons_
if False:
    import ui.cocoa.constants
    import ui.cocoa.setupwizard
    import ui.common.setupwizard

class PyObjCExceptionDelegate(NSObject):

    @staticmethod
    def isPythonException(exception):
        return (exception.userInfo() or {}).get(u'__pyobjc_exc_type__') is not None

    def exceptionHandler_shouldLogException_mask_(self, sender, exception, aMask):
        try:
            if self.isPythonException(exception):
                userInfo = exception.userInfo()
                type = userInfo[u'__pyobjc_exc_type__']
                value = userInfo[u'__pyobjc_exc_value__']
                tb = userInfo.get(u'__pyobjc_exc_traceback__', [])
                TRACE('PYTHON OBJC UNCAUGHT EXCEPTION!! %s' % ''.join(traceback.format_exception(type, value, tb)))
                unhandled_exc_handler(exc_info=(type, value, tb))
            TRACE('OBJC UNCAUGHT EXCEPTION: %s %s %s' % (sender, exception, aMask))
        except Exception:
            TRACE('OBJC EXCEPTION AND EXCEPTION WHILE TRACING THE ERROR')
            unhandled_exc_handler()
        finally:
            return True

    def exceptionHandler_shouldHandleException_mask_(self, sender, exception, aMask):
        return False


class CocoaUIKit(object):
    MAX_POPUP_ERRORS = 5

    def __init__(self, dropbox_app, using_xui):
        self.dropbox_app = dropbox_app
        self.using_xui = using_xui
        self.pref_window_controller = None
        self.pref_window_controller_lock = threading.Lock()
        self.no_dispatch = False
        self.bubbler = Bubbler(dropbox_app)
        self.tray_icon = TrayIcon(dropbox_app)
        self.tray_arrow = None
        self.tray_popup = None
        self.tray_popup_controller = None
        self.tray_popup_errors = 0
        self.show_alert_dialog = showAlertDialogWithCaption_message_andButtons_
        self.pass_message = AppHelper.callAfter
        self.wizard = None
        self.wizard_lock = threading.Lock()
        self.screenshots_splash_screen = None
        self.wizkit_controller = None
        self.wizkit = None

    def set_prefs(self, prefs):
        self.prefs = prefs
        self._load_defaults()
        self._load_pref_controller()
        if self.using_xui:
            self._load_tray_popup()

    @message_sender(AppHelper.callAfter, block=True)
    def _load_defaults(self):
        if not hasattr(build_number, 'frozen'):
            debugging = objc.YES
            self.exceptiondelegate = PyObjCExceptionDelegate.alloc().init()
            NSExceptionHandler.defaultExceptionHandler().setExceptionHandlingMask_(NSLogAndHandleEveryExceptionMask)
            NSExceptionHandler.defaultExceptionHandler().setDelegate_(self.exceptiondelegate)
        else:
            debugging = objc.NO
        if self.using_xui:
            NSUserDefaults.standardUserDefaults().registerDefaults_({'WebKitDeveloperExtras': debugging})

    @message_sender(AppHelper.callAfter, block=True)
    def _load_pref_controller(self):
        with self.pref_window_controller_lock:
            if self.pref_window_controller is None:
                self.pref_window_controller = PrefWindowController(self.dropbox_app)

    @message_sender(AppHelper.callAfter, block=True)
    def _load_tray_popup(self):
        try:
            from ui.cocoa.tray_popup import TrayPopupWindow
            self.tray_popup_controller = TrayPopupController(self.dropbox_app)
            self.tray_popup = TrayPopupWindow.alloc().init(self.dropbox_app, self.tray_popup_controller)
        except Exception:
            unhandled_exc_handler()
            self.tray_popup_controller = None
            self.tray_popup = None

    @message_sender(AppHelper.callAfter)
    def enter_preferences(self, panel = None):
        if self.pref_window_controller is not None:
            self.pref_window_controller.show_user(panel)
        NSApp().activateIgnoringOtherApps_(True)

    @message_sender(AppHelper.callAfter)
    def refresh_panel(self, panel):
        if self.pref_window_controller is not None:
            self.pref_window_controller.refresh_panel(panel)

    @message_sender(AppHelper.callAfter)
    def enter_demo(self):
        try:
            from ui.cocoa.panel import SickWindow
            from ui.cocoa.util import get_image_dir
            if getattr(self, 'sw', None):
                return
            hi_self = self

            class WindowDelegate(NSObject):

                def windowWillClose_(self, notification):
                    hi_self.wd = None
                    hi_self.sw = None

            self.sw = SickWindow.alloc().initWithImageDir_(os.path.join(get_image_dir(), u'about'))
            self.wd = WindowDelegate.alloc().init()
            self.sw.setDelegate_(self.wd)
            self.sw.center()
            self.sw.makeKeyAndOrderFront_(self)
            self.sw.orderFrontRegardless()
            NSApp().activateIgnoringOtherApps_(True)
            self.dropbox_app.csr.report_event('demo')
        except Exception:
            pass

    @message_sender(AppHelper.callAfter, block=True)
    def enter_setupwizkit(self, linked_event, enter_proxy_settings, definitely_connected, connection_error, email_address = None, login_only = False):
        if feature_enabled('setupwizkit') and self.using_xui:
            if self.wizkit is None:
                self._linked_event = linked_event
                from .wizkit_window import WizkitWindow
                self.wizkit_controller = WizkitController(self.dropbox_app)
                self.wizkit_controller.email = email_address
                self.wizkit_controller.login_only = login_only
                self.wizkit = WizkitWindow.alloc().init(self.dropbox_app, self.wizkit_controller)
            if self.wizkit_controller is not None:
                self.wizkit_controller.enter(linked_event, enter_proxy_settings, definitely_connected, connection_error)
            self.wizkit.show_()
        else:
            report_bad_assumption('setupwizkit was disabled but entry point was called')

    def enter_setupwizard(self, panel, linked_event, force, definitely_connected, should_raise, enter_proxy_settings, start_tray_arrow, stop_tray_arrow, **kw):
        self._linked_event = linked_event
        with self.wizard_lock:
            if self.wizard is None:
                TRACE('Making setupwizard (cocoa)')
                self.wizard = SetupWizard(SetupWizardWindow, linked_event, show_network_settings=enter_proxy_settings, dropbox_app=self.dropbox_app, **kw)
                TRACE('Made setupwizard (cocoa)')
        self.wizard.enter(panel, force=force, definitely_connected=definitely_connected, should_raise=should_raise)

    def setupwizard_should_register_wait(self):
        self._linked_event.wait()

    def yield_setupwizard_successful_link(self, ret, when_done = None):
        if feature_enabled('setupwizkit') and self.wizkit is not None:
            self.wizkit_controller.email = ret.get('email', None)
            self.wizkit_controller.root_ns = ret.get('root_ns', None)
            self.wizkit_controller.linked_successfully(when_done)
        elif self.wizard is not None:
            self.wizard.first_name = ret.get('userfname', None)
            self.wizard.email_address = ret.get('email', None)
            self.wizard.root_ns = ret.get('root_ns', None)
            self.wizard.linked_successfully(when_done=when_done)

    def get_text_from_clipboard(self):
        try:
            pb = NSPasteboard.generalPasteboard()
            if not pb:
                return ''
            clipboard_string = pb.stringForType_(NSStringPboardType)
            if clipboard_string is None:
                return ''
            return clipboard_string
        except Exception:
            unhandled_exc_handler()
            return ''

    @message_sender(AppHelper.callAfter)
    def start_tray_arrow(self, rect = None):
        if rect is None:
            rect = self.tray_icon.get_screen_rect()
        self.tray_arrow = TrayArrow(rect)
        self.tray_arrow.start()

    @message_sender(AppHelper.callAfter)
    def stop_tray_arrow(self):
        if self.tray_arrow:
            self.tray_arrow.stop()
            self.tray_arrow = None

    @event_handler
    def create_progress_window(self, message, max_value):
        return ProgressWindow(message, max_value)

    def enter_proxy_settings(self):
        self.enter_preferences('proxies')

    @event_handler
    def _make_main_menu(self):
        self.main_menu = NSMenu.alloc().init()
        self.main_menu_delegate = DropboxDefaultMenuDelegate.alloc().init()
        self.main_menu.setDelegate_(self.main_menu_delegate)
        NSApplication.sharedApplication().setMainMenu_(self.main_menu)

    def mainloop(self):
        real_self = self
        app = NSApplication.sharedApplication()

        class ApplicationDelegate(NSObject):

            def __new__(cls):
                return ApplicationDelegate.alloc().init()

            def applicationWillFinishLaunching_(self, notication):
                real_self._make_main_menu()

            def applicationDidFinishLaunching_(self, notication):
                pass

        holder = ApplicationDelegate()
        app.setDelegate_(holder)
        AppHelper.installMachInterrupt()
        AppHelper.runEventLoop()
        self.no_dispatch = True

    def exit_mainloop(self):
        self.no_dispatch = True
        AppHelper.stopEventLoop()

    def wants_dispatch(self):
        return not self.no_dispatch

    def create_camera_ui(self, **kw):
        return CocoaCameraUI(**kw)

    @message_sender(AppHelper.callAfter)
    def show_bubble(self, bubble):
        if not self.dropbox_app.pref_controller['show_bubbles'] and not bubble.show_when_disabled:
            return
        self.bubbler.render_bubble(bubble)

    @message_sender(AppHelper.callAfter, block=True)
    def start_tray_icon(self):
        try:
            self.tray_icon.enable(self)
        except Exception:
            unhandled_exc_handler()

    @message_sender(AppHelper.callAfter, block=True)
    def stop_tray_icon(self):
        self.tray_icon.disable()

    def update_tray_icon(self, **kwargs):
        return self.tray_icon.update_tray_icon(**kwargs)

    @message_sender(AppHelper.callAfter)
    def update_options(self, options):
        self.tray_icon.update_tray_menu(options.itervalues())
        if self.tray_popup_controller:
            self.tray_popup_controller.update_options(options)

    @message_sender(AppHelper.callAfter, block=True)
    def show_tray_popup(self, context_menu):
        if not self.using_xui or context_menu:
            self.tray_icon.show_tray_menu()
            return
        try:
            if NSApp().isHidden():
                NSApp().unhideWithoutActivation()
            rect = self.tray_icon.get_screen_rect()
            self.tray_popup.showAnchoredToRect_(rect)
            if self.using_xui:
                self.tray_popup_controller.on_show()
        except Exception:
            self.tray_icon.disable_badge_count()
            self.tray_popup_errors += 1
            if self.tray_popup_errors >= self.MAX_POPUP_ERRORS:
                self.using_xui = False
                report_bad_assumption('Giving up on the tray popup!')
            unhandled_exc_handler()
            self.tray_icon.show_tray_menu()

    @message_sender(AppHelper.callAfter)
    def move_tray_popup(self, rect):
        if self.tray_popup:
            self.tray_popup.moveToAnchor_withHeight_(rect, None)

    @message_sender(AppHelper.callAfter)
    def hide_tray_popup(self):
        if self.tray_popup:
            self.tray_popup.orderOut_(None)

    @message_sender(AppHelper.callAfter)
    def update_notifications(self, *args, **kwargs):
        if self.tray_popup_controller:
            self.tray_popup_controller.update_notifications(*args, **kwargs)

    @message_sender(AppHelper.callAfter)
    def update_status(self, *args, **kwargs):
        if self.tray_popup_controller:
            self.tray_popup_controller.update_status(*args, **kwargs)

    @message_sender(AppHelper.callAfter)
    def call_later(self, seconds, fn, *args, **kwargs):
        return AppHelper.callLater(seconds, fn, *args, **kwargs)

    @message_sender(AppHelper.callAfter)
    def show_screenshots_dialog(self, *args, **kwargs):
        self.screenshots_splash_screen = ScreenshotsSplashScreen(*args, **kwargs)
        self.screenshots_splash_screen.show_window()

    @message_sender(AppHelper.callAfter, block=True)
    def show_gallery_import_dialog(self, *args, **kwargs):
        splash = get_gallery_import_splash(*args, **kwargs)
        splash.show_window()
        return splash.close_window

    @message_sender(AppHelper.callAfter)
    def enable_multiaccount(self):
        if self.using_xui and self.tray_popup_controller:
            self.tray_popup_controller.enable_multiaccount()

    @message_sender(AppHelper.callAfter)
    def disable_multiaccount(self):
        if self.using_xui and self.tray_popup_controller:
            self.tray_popup_controller.disable_multiaccount()
