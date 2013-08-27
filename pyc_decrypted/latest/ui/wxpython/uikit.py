#Embedded file name: ui/wxpython/uikit.py
from __future__ import absolute_import
import collections
import os
import sys
import threading
import time
import wx
import arch
from build_number import is_frozen
from dropbox.bubble import BubbleKind, Bubble
from dropbox.debugging import easy_repr
from dropbox.features import feature_enabled
from dropbox.gui import assert_message_queue, event_handler, message_sender
import dropbox.i18n
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from .camera import WxCameraUI, WxGalleryImporterSplashFrame
from .constants import platform
from .dropbox_controls import ProgressWindow
from .dialogs import DropboxModalDialog
from .preferences import PrefsFrame, ProxySettingsPanel
from .setupwizard2 import SetupWizardWindow
from ..common.misc import MiscStrings
from ..common.setupwizard import SetupWizard, SetupWizardStrings
from ui.common.xui.tray_popup import TrayPopupController
from ui.common.xui.wizkit import WizkitController
import ui.images
from .screenshots import ScreenshotsSplashScreen
if sys.platform.startswith('win'):
    from .tray_arrow import TrayArrow
if sys.platform.startswith('darwin'):
    from dropbox.mac.internal import raise_application
else:
    raise_application = arch.util.raise_application

class WxUIKit(object):

    def __repr__(self):
        return easy_repr(self, 'wx_app', 'planning_to_start_wx_app', 'stopped', 'exited', 'preapp_msg_q', 'wizard', 'prefs_frame', 'selective_sync_frame')

    def __init__(self, dropbox_app, using_xui):
        self.dropbox_app = dropbox_app
        self.using_xui = using_xui
        self.wx_app = None
        self.planning_to_start_wx_app = threading.Event()
        self.stopped = False
        self.exited = False
        self.preapp_msg_q_lock = threading.Lock()
        self.preapp_msg_q = collections.deque()
        self.pref_controller = None
        self.show_alert_dialog = self.show_dialog
        self.wizard = None
        self.wizard_lock = threading.Lock()
        self.prefs_frame = None
        self.prefs_frame_lock = threading.Lock()
        self.selective_sync_frame = None
        self.selective_sync_frame_lock = threading.Lock()
        self.tray_arrow = None
        self.tray_popup = None
        self.tray_popup_controller = None
        self.cef_timer = None
        self.cef_timer_interval = 34
        self.dropbox_app.tray_controller.add_callbacks_for_options({SetupWizardStrings.link_this_computer: self._raise_setupwizard})
        self.wizkit = None
        self.wizkit_controller = None

    def set_prefs(self, pref_controller):
        self.pref_controller = pref_controller

    def _load_tray_popup(self):
        try:
            from .tray_popup import TrayPopupWindow
            self.tray_popup_controller = TrayPopupController(self.dropbox_app)
            self.tray_popup = TrayPopupWindow(self.dropbox_app, self.tray_popup_controller)
        except Exception:
            unhandled_exc_handler()
            self.tray_popup_controller = None
            self.tray_popup = None

    def _initialize_cef(self):
        TRACE('Initializing CEF (Wx)')
        import pycef
        from ui.wxpython.xui import XUIApplication
        settings = pycef.CefSettings()
        settings.product_version = 'DropboxXUI'
        settings.multi_threaded_message_loop = False
        if is_frozen():
            settings.pack_loading_disabled = True
            settings.log_severity = pycef.LOGSEVERITY_DISABLE
        else:
            settings.release_dcheck_enabled = True
        app = XUIApplication()
        if not pycef.CefInitialize(settings, app):
            raise Exception('Failed to initialize CEF')

        def handleCefEvents(event):
            pycef.CefDoMessageLoopWork()

        self.cef_timer = wx.Timer(self.wx_app)
        self.top_level_window.Bind(wx.EVT_TIMER, handleCefEvents, self.cef_timer)
        self.dropbox_app.add_quit_handler(app.shutdown)

        @event_handler
        def idle_cef(event):
            pycef.CefDoMessageLoopWork()
            event.Skip()

        self.top_level_window.Bind(wx.EVT_IDLE, idle_cef)

    def _start_cef_animation_timer(self):
        if self.cef_timer is not None:
            self.cef_timer.Start(self.cef_timer_interval)

    def _stop_cef_animation_timer(self):
        if self.cef_timer is not None:
            self.cef_timer.Stop()

    @assert_message_queue
    def mainloop(self):
        TRACE('Waiting for preconditions to be met (wx)')
        if not arch.startup.wait_wx_preconditions():
            TRACE('MainThread told never to start mainloop!')
            return
        self.planning_to_start_wx_app.set()
        with self.preapp_msg_q_lock:
            TRACE('Making App (wx)')
            self.wx_app = wx.App(redirect=False)
            if sys.platform.startswith('linux'):
                code = dropbox.i18n.get_current_code()
                if code:
                    try:
                        info = wx.Locale.FindLanguageInfo(code)
                        if info and wx.Locale.IsAvailable(info.Language):
                            TRACE('Setting wx locale to %s (%s)', info.Description, info.CanonicalName)
                            try:
                                del os.environ['LANGUAGE']
                            except KeyError:
                                pass

                            l = wx.Locale(info.Language)
                        else:
                            TRACE('!!Unable to set wx Language to %s', info.CanonicalName if info else 'Unknown')
                    except:
                        unhandled_exc_handler()

            TRACE('Creating blank top-level window (Wx)')
            self.top_level_window = wx.Frame(None)
            self.top_level_window.Show(False)
            self.wx_app.SetTopWindow(self.top_level_window)
            self.top_level_window.Bind(wx.EVT_CLOSE, lambda : arch.util.hard_exit())
            if sys.platform.startswith('win') and self.using_xui:
                try:
                    self._initialize_cef()
                except Exception:
                    report_bad_assumption('Failed to initialize CEF.')
                    unhandled_exc_handler()
                else:
                    self._load_tray_popup()
                    if feature_enabled('setupwizkit'):
                        self._load_wizkit()
            TRACE('Initializing images (Wx)')
            ui.images.init()
            TRACE('Initializing platform (Wx)')
            platform.init()
            while self.preapp_msg_q:
                f, n, kw = self.preapp_msg_q.popleft()
                message_sender(wx.CallAfter)(f)(*n, **kw)

        self.dropbox_app.tray_controller.trigger_update()
        if not self.stopped:
            TRACE('Entering wx mainloop')
            self.wx_app.MainLoop()
            TRACE('Exited wx mainloop')
        self.exited = True

    def pass_message(self, f, *n, **kw):
        with self.preapp_msg_q_lock:
            if self.wx_app is not None:
                message_sender(wx.CallAfter)(f)(*n, **kw)
            else:
                self.preapp_msg_q.append((f, n, kw))

    def exit_mainloop(self):
        self.stopped = True
        if self.wx_app is not None:
            self.wx_app.ExitMainLoop()

    def wants_dispatch(self):
        if not self.stopped and not self.exited:
            self.planning_to_start_wx_app.wait(timeout=5)
            return self.planning_to_start_wx_app.isSet() and self.wx_app
        return False

    def copy_text_to_clipboard(self, text):
        message_sender(self.pass_message)(self._copy_text_to_clipboard)(text)

    def get_text_from_clipboard(self):
        self._wait_for_wx_start()
        clipdata = wx.TextDataObject()
        wx.TheClipboard.Open()
        wx.TheClipboard.GetData(clipdata)
        wx.TheClipboard.Close()
        return clipdata.GetText()

    def _wait_for_wx_start(self):
        self.planning_to_start_wx_app.wait()
        while self.wx_app is None:
            time.sleep(0.05)

    def _load_wizkit(self):
        if feature_enabled('setupwizkit') and self.using_xui:
            from .wizkit_window import WizkitWindow
            self.wizkit_controller = WizkitController(self.dropbox_app)
            self.wizkit = WizkitWindow(self.dropbox_app, self.wizkit_controller)
        else:
            report_bad_assumption('setupwizkit was disabled but entry point was called')

    def enter_setupwizkit(self, linked_event, enter_proxy_settings, definitely_connected, connection_error, email_address = None, login_only = False):
        if feature_enabled('setupwizkit') and self.using_xui:
            self._wait_for_wx_start()
            self._linked_event = linked_event
            self.wizkit_controller.email = email_address
            self.wizkit_controller.login_only = login_only
            self.wizkit_controller.enter(linked_event, enter_proxy_settings, definitely_connected, connection_error)
            self.wizkit.Show()
        else:
            report_bad_assumption('setupwizkit was disabled but entry point was called')

    def enter_setupwizard(self, panel_t, linked_event, force, definitely_connected, should_raise, enter_proxy_settings, **kw):
        self._wait_for_wx_start()
        self._linked_event = linked_event
        with self.wizard_lock:
            if self.wizard is None:
                TRACE('Making setupwizard (wx)')
                self.wizard = SetupWizard(SetupWizardWindow, linked_event, show_network_settings=enter_proxy_settings, dropbox_app=self.dropbox_app, **kw)
                TRACE('Made setupwizard (wx)')
        self.wizard.enter(panel_t, force=force, definitely_connected=definitely_connected, should_raise=should_raise)

    def setupwizard_should_register_wait(self):
        return self._linked_event.wait()

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

    def start_tray_arrow(self, rect):
        self._wait_for_wx_start()
        try:
            self.tray_arrow = TrayArrow(rect)
            self.tray_arrow.start()
        except Exception:
            unhandled_exc_handler()

    def stop_tray_arrow(self):
        if self.tray_arrow:
            self.tray_arrow.stop()
            self.tray_arrow = None

    def create_progress_window(self, message, max_value):
        return ProgressWindow(message, max_value)

    def _copy_text_to_clipboard(self, text):
        self._wait_for_wx_start()
        clipdata = wx.TextDataObject()
        clipdata.SetText(text)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

    def _raise_setupwizard(self):
        if self.wizard is not None:
            self.wizard.raise_window()
            raise_application()

    def enter_proxy_settings(self):
        self.enter_preferences('proxies')

    def enter_preferences(self, panel = None):
        self._wait_for_wx_start()
        if panel == 'proxies':
            panel_t = ProxySettingsPanel
        else:
            panel_t = None
        with self.prefs_frame_lock:
            if self.prefs_frame is None:
                self.prefs_frame = PrefsFrame(None, self.dropbox_app)
        self.prefs_frame.show_user(panel_t)

    def refresh_panel(self, panel):
        if self.prefs_frame:
            self.prefs_frame.refresh_panel(panel)

    def create_camera_ui(self, **kw):
        return WxCameraUI(**kw)

    @message_sender(wx.CallAfter, block=True)
    def show_tray_popup(self, rect):
        if self.tray_popup:
            self.tray_popup.ShowAnchored(rect)

    @message_sender(wx.CallAfter)
    def move_tray_popup(self, rect):
        pass

    @message_sender(wx.CallAfter, block=True)
    def hide_tray_popup(self):
        if self.tray_popup:
            self.tray_popup.Show(False)

    @message_sender(wx.CallAfter)
    def update_options(self, *args, **kwargs):
        if self.tray_popup_controller:
            self.tray_popup_controller.update_options(*args, **kwargs)

    @message_sender(wx.CallAfter)
    def update_notifications(self, *args, **kwargs):
        if self.tray_popup_controller:
            self.tray_popup_controller.update_notifications(*args, **kwargs)

    @message_sender(wx.CallAfter)
    def update_status(self, *args, **kwargs):
        if self.tray_popup_controller:
            self.tray_popup_controller.update_status(*args, **kwargs)

    @message_sender(wx.CallAfter)
    def call_later(self, seconds, fn, *args, **kwargs):
        return wx.CallLater((seconds * 1000), fn, *args, **kwargs)

    @message_sender(wx.CallAfter)
    def show_screenshots_dialog(self, *args, **kwargs):
        splash_screen = ScreenshotsSplashScreen(*args, **kwargs)
        splash_screen.show()

    @message_sender(wx.CallAfter)
    def show_gallery_import_dialog(self, *args, **kwargs):
        splash_screen = WxGalleryImporterSplashFrame(*args, **kwargs)
        splash_screen.Show(True)

    @message_sender(wx.CallAfter)
    def show_dialog(self, **kwargs):
        kwargs.pop('default_button', None)
        kwargs.pop('cancel_button', None)
        dlg = DropboxModalDialog(None, **kwargs)
        return dlg.show_modal()

    @message_sender(wx.CallAfter)
    def enable_multiaccount(self):
        if self.using_xui and self.tray_popup_controller:
            self.tray_popup_controller.enable_multiaccount()

    @message_sender(wx.CallAfter)
    def disable_multiaccount(self):
        if self.using_xui and self.tray_popup_controller:
            self.tray_popup_controller.disable_multiaccount()
