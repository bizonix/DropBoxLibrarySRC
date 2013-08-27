#Embedded file name: arch/linux/uikit.py
from __future__ import absolute_import
import collections
import functools
import threading
import time
import sys
from dropbox.gui import event_handler, message_sender
from dropbox.low_functions import add_inner_methods
from dropbox.i18n import trans
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.common.setupwizard import ConnectionTrouble, DropboxMissing, UnlinkFailure, WelcomePanel
from ui.common.tray import TrayOptionStrings
from ui.common.uikit import PlatformUIKitBase
from .idletracker import IdleTracker
from .tray_icon import TrayIcon
from .util import copy_text_to_clipboard as ct_copy_text_to_clipboard

def safe_print(u):
    print u.encode(sys.stdout.encoding or 'utf8', 'ignore')


class DegradedUIKit(PlatformUIKitBase):

    def __init__(self, app):
        PlatformUIKitBase.__init__(self, app)
        self.stopped = False
        self.using_xui = False
        self.msg_q = collections.deque()
        self.mainloop_c = threading.Condition()
        self.launched_auth_page = None

    def mainloop(self):
        TRACE("Entering %r's mainloop" % (self,))
        while not self.stopped:
            with self.mainloop_c:
                while not self.msg_q:
                    self.mainloop_c.wait()

                f, n, kw = self.msg_q.popleft()
            try:
                f(*n, **kw)
            except:
                unhandled_exc_handler()

        TRACE("Exiting %r's mainloop" % (self,))

    def pass_message(self, f, *n, **kw):
        with self.mainloop_c:
            self.msg_q.append((f, n, kw))
            self.mainloop_c.notify()

    def exit_mainloop(self):
        self.stopped = True
        with self.mainloop_c:
            self.mainloop_c.notify()

    def set_prefs(self, prefs):
        self.prefs = prefs

    def enter_setupwizard(self, panel):
        try:
            if panel == UnlinkFailure:
                safe_print(trans(u'Something went wrong when you unlinked Dropbox'))
            elif panel == DropboxMissing:
                safe_print(trans(u"Couldn't locate your Dropbox folder. Did you move it somewhere?"))
            elif panel == WelcomePanel:
                if self.launched_auth_page is None:
                    self.launched_auth_page = time.time()
                    try:
                        pass
                    except:
                        unhandled_exc_handler()

                safe_print(trans(u"This computer isn't linked to any Dropbox account..."))
                safe_print(trans(u'Please visit %(url)s to link this device.') % dict(url=self.app.dropbox_url_info.cli_link_url()))
            elif panel == ConnectionTrouble:
                safe_print(trans(u'Dropbox is having trouble connecting. Please check your Internet connection.'))
        except:
            unhandled_exc_handler()

    def setupwizard_should_register_wait(self):
        if self.launched_auth_page is not None and time.time() - self.launched_auth_page < 450:
            time.sleep(5)
        else:
            time.sleep(30)

    def yield_setupwizard_successful_link(self, ret, when_done = None):
        try:
            if 'userfname' in ret:
                safe_print(trans(u'This computer is now linked to Dropbox. Welcome %s') % ret['userfname'])
            else:
                safe_print(trans(u'This computer is now linked to Dropbox.'))
        except:
            unhandled_exc_handler()

        if when_done is not None:
            try:
                when_done({})
            except:
                unhandled_exc_handler()


def call_using_self_pass_message(fn):

    @functools.wraps(fn)
    def wrapped(self, *n, **kw):
        return message_sender(self.pass_message, block=True)(fn)(self, *n, **kw)

    return wrapped


@add_inner_methods('is_trackable', 'seconds_idle', decorator=call_using_self_pass_message, inner_name='idletracker')

class PlatformUIKit(PlatformUIKitBase):

    def __init__(self, app):
        PlatformUIKitBase.__init__(self, app)
        self.exited = False
        self.using_xui = False
        try:
            from ui.wxpython.uikit import WxUIKit
            self.wx_ui_kit = WxUIKit(app, self.using_xui)
        except:
            unhandled_exc_handler()
            self.wx_ui_kit = None

        self.idletracker = IdleTracker()
        self.degraded_ui_kit = DegradedUIKit(app)
        self.using_wx_setupwizard = True
        self.using_wx_mainloop = True
        self.tray_icon = TrayIcon(app)

    def set_prefs(self, prefs):
        if self.wx_ui_kit is not None:
            self.wx_ui_kit.set_prefs(prefs)
        self.app.tray_controller.add_callbacks_for_options({TrayOptionStrings.preferences_dotdotdot: self.enter_preferences})

    def idle_is_trackable(self):
        if self.idletracker:
            return self.idletracker.is_trackable()
        else:
            return self.degraded_ui_kit.setupwizard_should_register_wait()

    def enter_setupwizard(self, panel, linked_event, force = True, definitely_connected = False, should_raise = False, **kw):
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            self.wx_ui_kit.enter_setupwizard(panel, linked_event, force, definitely_connected, should_raise, functools.partial(self.enter_preferences, 'proxies'), **kw)
            self.using_wx_setupwizard = True
        else:
            self.degraded_ui_kit.enter_setupwizard(panel)
            self.using_wx_setupwizard = False

    def setupwizard_should_register_wait(self):
        if self.wx_ui_kit is not None and self.using_wx_setupwizard and self.wx_ui_kit.wants_dispatch():
            return self.wx_ui_kit.setupwizard_should_register_wait()
        else:
            return self.degraded_ui_kit.setupwizard_should_register_wait()

    def yield_setupwizard_successful_link(self, ret, when_done = None):
        if self.wx_ui_kit is not None and self.using_wx_setupwizard and self.wx_ui_kit.wants_dispatch():
            return self.wx_ui_kit.yield_setupwizard_successful_link(ret, when_done=when_done)
        else:
            return self.degraded_ui_kit.yield_setupwizard_successful_link(ret, when_done=when_done)

    def start_tray_arrow(self):
        pass

    def stop_tray_arrow(self):
        pass

    def copy_text_to_clipboard(self, text):
        TRACE('copying to clipboard: %r' % text)
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            try:
                self.wx_ui_kit.copy_text_to_clipboard(text)
            except:
                unhandled_exc_handler()
                ct_copy_text_to_clipboard(text)

        else:
            ct_copy_text_to_clipboard(text)

    def get_text_from_clipboard(self):
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            return self.wx_ui_kit.get_text_from_clipboard()
        return ''

    def create_progress_window(self, message, max_value):
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            return self.wx_ui_kit.create_progress_window(message, max_value)

    def enter_preferences(self, panel = None):
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            self.wx_ui_kit.enter_preferences(panel)

    def enter_proxy_settings(self):
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            self.wx_ui_kit.enter_proxy_settings()

    @event_handler
    def mainloop(self):
        threading.currentThread().signal_stop = self.exit_mainloop
        from ui.common import uikit
        try:
            if self.wx_ui_kit is not None:
                import wx
                uikit.real_call_after = wx.CallAfter
                self.wx_ui_kit.mainloop()
        except:
            unhandled_exc_handler()

        if not self.exited:
            self.using_wx_mainloop = False
            uikit.real_call_after = self.pass_message
            self.degraded_ui_kit.mainloop()

    def pass_message(self, f, *n, **kw):
        if self.using_wx_mainloop:
            self.wx_ui_kit.pass_message(f, *n, **kw)
        else:
            self.degraded_ui_kit.pass_message(f, *n, **kw)

    def exit_mainloop(self):
        self.exited = True
        if self.wx_ui_kit is not None:
            self.wx_ui_kit.exit_mainloop()
        self.degraded_ui_kit.exit_mainloop()

    def show_bubble(self, bubble):
        if not self.app.pref_controller['show_bubbles'] and not bubble.show_when_disabled:
            return
        self.tray_icon.render_bubble(bubble)

    def start_tray_icon(self):
        self.tray_icon.enable(self)

    def update_tray_icon(self, **kwargs):
        return self.tray_icon.update_tray_icon(**kwargs)

    def update_options(self, options):
        return self.tray_icon.update_tray_menu(options.values())

    def call_later(self, seconds, fn, *n, **kw):
        if self.using_wx_mainloop:
            self.wx_ui_kit.call_later(seconds, fn, *n, **kw)

    def show_tray_popup(self, *args, **kwargs):
        pass

    def move_tray_popup(self, *args, **kwargs):
        pass

    def hide_tray_popup(self, *args, **kwargs):
        pass

    def update_notifications(self, *args, **kwargs):
        pass

    def update_status(self, *args, **kwargs):
        pass

    def show_dialog(self, **kwargs):
        if self.wx_ui_kit is not None and self.wx_ui_kit.wants_dispatch():
            return self.wx_ui_kit.show_dialog(self, kwargs)

    def enable_multiaccount(self):
        pass

    def disable_multiaccount(self):
        pass
