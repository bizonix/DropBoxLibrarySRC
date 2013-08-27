#Embedded file name: ui/common/uikit.py
import functools
from dropbox.callbacks import Handler
from dropbox.gui import message_sender
from dropbox.trace import unhandled_exc_handler, report_bad_assumption
from dropbox.platform import platform
from .camera import CameraUI

class PlatformUIKitBase(object):

    def __init__(self, app):
        self.app = app
        self.sync_engine = None
        self.post_link = False
        self._sync_engine_handler = Handler(handle_exc=unhandled_exc_handler)
        self._post_link_handler = Handler(handle_exc=unhandled_exc_handler)

    def set_prefs(self, prefs):
        raise NotImplementedError('set_prefs should be overridden by the PlatformUIKit (%r)' % (self,))

    def add_sync_engine_handler(self, callback):
        self._sync_engine_handler.add_handler(callback)

    def set_sync_engine(self, se):
        self.sync_engine = se
        self._sync_engine_handler.run_handlers(se)

    def add_post_link_handler(self, callback):
        self._post_link_handler.add_handler(callback)

    def set_post_link(self):
        self.post_link = True
        self._post_link_handler.run_handlers()

    def enter_setupwizkit(self, linked_event):
        raise NotImplementedError('enter_setupwizkit should be overridden by the PlatformUIKit (%r)' % (self,))

    def enter_setupwizard(self, panel, force = True, definitely_connected = False, should_raise = False):
        raise NotImplementedError('enter_setupwizard should be overridden by the PlatformUIKit (%r)' % (self,))

    def setupwizard_should_register_wait(self):
        raise NotImplementedError('setupwizard_should_register_wait should be overridden by the PlatformUIKit (%r)' % (self,))

    def yield_setupwizard_successful_link(self, ret):
        raise NotImplementedError('yield_setupwizard_successful_link should be overridden by the PlatformUIKit (%r)' % (self,))

    def copy_text_to_clipboard(self, text):
        raise NotImplementedError('copy_text_to_clipboard should be overridden by the PlatformUIKit (%r)' % (self,))

    def get_text_from_clipboard(self):
        raise NotImplementedError('get_text_from_clipboard should be overridden by the PlatformUIKit (%r)' % (self,))

    def enter_proxy_settings(self, panel = None):
        raise NotImplementedError('enter_proxy_settings should be overridden by the PlatformUIKit (%r)' % (self,))

    def enter_preferences(self, panel = None):
        raise NotImplementedError('enter_preferences should be overridden by the PlatformUIKit (%r)' % (self,))

    def refresh_panel(self, panel):
        raise NotImplementedError('refresh_panel should be overridden by the PlatformUIKit (%r)' % self)

    def mainloop(self):
        raise NotImplementedError('mainloop should be overridden by the PlatformUIKit (%r)' % (self,))

    def pass_message(self, f, *n, **kw):
        raise NotImplementedError('pass_message should be overridden by the PlatformUIKit (%r)' % (self,))

    def exit_mainloop(self):
        raise NotImplementedError('exit_mainloop should be overridden by the PlatformUIKit (%r)' % (self,))

    def create_camera_ui(self, **kw):
        return CameraUI(**kw)

    def show_bubble(self, bubble):
        raise NotImplementedError('show_bubble should be overridden by the PlatformUIKit (%r)' % (self,))

    def seconds_idle(self):
        raise NotImplementedError('seconds_idle should be overridden by the PlatformUIKit (%r)' % (self,))

    def is_trackable(self):
        raise NotImplementedError('is_trackable should be overridden by the PlatformUIKit (%r)' % (self,))

    def start_tray_arrow(self):
        raise NotImplementedError('start_tray_arrow should be overridden by the PlatformUIKit (%r)' % (self,))

    def stop_tray_arrow(self):
        raise NotImplementedError('stop_tray_arrow should be overridden by the PlatformUIKit (%r)' % (self,))

    def start_tray_icon(self):
        raise NotImplementedError('stop_tray_arrow should be overridden by the PlatformUIKit (%r)' % (self,))

    def update_tray_icon(self, **kwargs):
        raise NotImplementedError('update_tray_icon should be overridden by the PlatformUIKit (%r)' % (self,))

    def update_tray_menu(self, items):
        raise NotImplementedError('update_tray_menu should be overridden by the PlatformUIKit (%r)' % (self,))

    def show_tray_popup(self):
        raise NotImplementedError('show_tray_popup should be overridden by the PlatformUIKit (%r)' % (self,))

    def move_tray_popup(self, rect):
        raise NotImplementedError('move_tray_popup should be overridden by the PlatformUIKit (%r)' % (self,))

    def hide_tray_popup(self):
        raise NotImplementedError('hide_tray_popup should be overridden by the PlatformUIKit (%r)' % (self,))

    def update_notifications(self):
        raise NotImplementedError('update_notifications should be overridden by the PlatformUIKit (%r)' % (self,))

    def update_status(self, *args, **kwargs):
        raise NotImplementedError('update_status should be overridden by the PlatformUIKit (%r)' % (self,))

    def show_screenshots_dialog(self, always_cb, never_cb, close_cb):
        raise NotImplementedError('show_screenshots_dialog should be overridden by the PlatformUIKit (%r)' % (self,))

    def show_dialog(self, **kwargs):
        raise NotImplementedError('show_dialog should be overridden by the PlatformUIKit (%r)' % (self,))

    def show_gallery_import_dialog(self, *args, **kwargs):
        raise NotImplementedError('show_gallery_import_dialog should be overridden by the PlatformUIKit (%r)' % (self,))

    def enable_multiaccount(self):
        raise NotImplementedError('enable_multiaccount should be overridden by the PlatformUIKit (%r)' % (self,))

    def disable_multiaccount(self):
        raise NotImplementedError('disable_multiaccount should be overridden by the PlatformUIKit (%r)' % (self,))

    def call_later(self, seconds, fn, *args, **kwargs):
        raise NotImplementedError('call_later should be overridden by the PlatformUIKit (%r)' % (self,))


if platform == 'mac':
    from PyObjCTools import AppHelper
    on_main_thread = functools.partial(message_sender, AppHelper.callAfter)
elif platform == 'win':
    import wx
    on_main_thread = functools.partial(message_sender, wx.CallAfter)
elif platform == 'linux':

    def real_call_after(fn, *n, **kw):
        report_bad_assumption('Linux: Decorating function with on_main_thread but call_after is not set by uikit.')


    def call_after(fn, *n, **kw):
        real_call_after(fn, *n, **kw)


    on_main_thread = functools.partial(message_sender, call_after)
