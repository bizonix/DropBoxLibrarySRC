#Embedded file name: arch/linux/tray_icon.py
from __future__ import absolute_import
import os
import time
import build_number
from build_number import BUILD_KEY
from .internal import get_contents_root
from .util import bubble_external, refresh_tray_menu_external, change_state_external, hard_exit
from dropbox.functions import handle_exceptions
from dropbox.gui import message_sender, assert_message_queue
from dropbox.i18n import trans
from dropbox.trace import TRACE, unhandled_exc_handler
try:
    import dbus
    import wx
    import ui.images
    with_wx = True
except:
    unhandled_exc_handler()
    with_wx = False

class TrayIcon(object):

    def __init__(self, app):
        self.app = app
        self.wx_ui_kit = None
        self._dn = None
        self.dn = None
        self.tray_icon = None
        self._initial_icon_state = None
        self._initial_menu = None
        self._initial_tooltip = None

    @assert_message_queue
    def _destroy(self):
        if self.tray_icon is None:
            return
        self.tray_icon.Destroy()
        self.tray_icon = None
        self.dn = None
        TRACE('Tray icon turned off')

    def destroy(self):
        if self.wx_ui_kit is not None:
            message_sender(self.wx_ui_kit.pass_message)(self._destroy)()

    @assert_message_queue
    def _enable(self):
        if self.tray_icon is not None or not with_wx:
            return
        if hasattr(build_number, 'frozen'):
            bad_files = ['libdbus-glib-1.so.2', 'libdbus-1.so.3']
            for path in (os.path.join(get_contents_root(), name) for name in bad_files):
                if os.path.exists(path):
                    try:
                        TRACE("Removing %r because it doesn't belong.", path)
                        os.remove(path)
                    except:
                        unhandled_exc_handler()

        if self._dn is None:
            try:
                self._dn = DesktopNotify('Dropbox', self.app)
            except:
                unhandled_exc_handler(False)

        if self.dn is None:
            self.dn = self._dn
        try:
            try:
                from .tray_icon_app_indicator import TrayIcon as TrayIconAppIndicator
                self.tray_icon = TrayIconAppIndicator(self._initial_icon_state, self._initial_menu, self._initial_tooltip, self.app)
            except:
                unhandled_exc_handler(False)
                from .tray_icon_wx import TrayIcon as TrayIconWx
                self.tray_icon = TrayIconWx(self._initial_icon_state, self._initial_menu, self._initial_tooltip, self.app)

        except:
            unhandled_exc_handler(False)
            self.dn = None
            raise

        TRACE('Tray icon turned on')
        self._initial_menu = None
        self._initial_icon_state = None
        self._initial_tooltip = None

    def enable(self, ui_kit):
        self.ui_kit = ui_kit
        self.wx_ui_kit = ui_kit.wx_ui_kit
        if self.wx_ui_kit is not None:
            message_sender(self.wx_ui_kit.pass_message)(self._enable)()

    @handle_exceptions
    def render_bubble(self, bubble):
        assert bubble.has_no_ctxt_ref() or bubble.has_valid_ctxt_ref()
        if self.dn is None:
            bubble_external(self.app, bubble.msg, bubble.caption, bubble.ctxt_ref)
        elif self.tray_icon is not None:
            msg = bubble.msg
            if not self.dn.can_click_bubbles() and bubble.msg_passive is not None:
                msg = bubble.msg_passive
            self.wx_ui_kit.pass_message(self.dn.bubble, self.get_screen_rect, bubble.caption, msg, bubble.ctxt_ref)
        self.app.report_show_bubble(bubble)

    def update_tray_icon(self, icon_state = None, tooltip = None, flashing = None, badge_count = 0, trigger_ping = False):
        if tooltip is not None:
            long_tooltip = tooltip[1]
            if self.tray_icon:
                self.wx_ui_kit.pass_message(self.tray_icon.set_tooltip, long_tooltip)
            else:
                self._initial_tooltip = long_tooltip
        if icon_state is not None:
            if self.tray_icon is not None:
                self.wx_ui_kit.pass_message(self.tray_icon.change_state, icon_state)
            else:
                self._initial_icon_state = icon_state
                change_state_external(icon_state)
        if flashing is not None and self.tray_icon:
            self.wx_ui_kit.pass_message(self.tray_icon.set_flash, flashing)

    def update_tray_menu(self, menu):
        menu = list(menu) + [(trans(u'Quit %s') % (BUILD_KEY,), hard_exit)]
        if self.tray_icon:
            self.wx_ui_kit.pass_message(self.tray_icon.refresh_tray_menu, menu)
        else:
            self._initial_menu = menu
            refresh_tray_menu_external(menu)

    def get_screen_rect(self):
        if self.tray_icon is not None:
            return self.tray_icon.get_screen_rect()


class DesktopNotify(object):
    initted_dbus_loop = False

    def __init__(self, name, app):
        if not DesktopNotify.initted_dbus_loop:
            import dbus.mainloop.glib
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            DesktopNotify.initted_dbus_loop = True
        self.app = app
        self.app_name = name
        self.id = 0
        self.on_click = None
        self.actions = []
        self.bubble_ctx_ref = None
        self._add_proxy()

    def _add_proxy(self):
        self.proxy = dbus.SessionBus().get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        self.proxy.connect_to_signal('ActionInvoked', self.action_invoked, dbus_interface='org.freedesktop.Notifications')
        self.proxy.connect_to_signal('NotificationClosed', self.notification_closed, dbus_interface='org.freedesktop.Notifications')
        try:
            self.proxy.GetCapabilities(dbus_interface='org.freedesktop.Notifications', reply_handler=self.cap_reply_handler, error_handler=self.cap_reply_handler)
        except:
            unhandled_exc_handler(False)

    def cap_reply_handler(self, *args, **kw):
        if len(args) != 0:
            yo = args[0]
            if not isinstance(yo, Exception) and 'actions' in yo:
                self.actions = ['default', 'default']

    def notification_closed(self, *args, **kw):
        if len(args) != 0:
            id = args[0]
            if self.id == id:
                self.id = 0
                self.on_click = None

    def action_invoked(self, *args, **kw):
        if len(args) != 0:
            id = args[0]
            if self.id == id and self.bubble_ctx_ref is not None:
                try:
                    self.app.bubble_context.get_context_ref(self.bubble_ctx_ref).thunk()
                except:
                    unhandled_exc_handler()

    def can_click_bubbles(self):
        return len(self.actions) > 0

    @classmethod
    def proper_x_y(cls, rect, disp):
        x, y, w, h = rect
        dw, dh = disp
        if y <= h:
            ret = (x + w / 2, y + h - h / 3)
        elif y >= dh - h:
            ret = (x + w / 2, y + h / 3)
        elif x < w:
            ret = (x + w - w / 3, y + h / 2)
        else:
            ret = (x + w / 3, y + h / 2)
        return ret

    def bubble(self, func_rect, caption, message, ctx_ref = None):
        hints = {'icon_data': ui.images.dbusimages.NotifyIconOld if self.actions else ui.images.dbusimages.NotifyIconNew}
        rect = func_rect()
        if rect:
            x, y = DesktopNotify.proper_x_y(rect, wx.Display().GetGeometry().GetSize().Get())
            hints.update({'x': x,
             'y': y})
        notify_args = (self.app_name,
         dbus.UInt32(self.id),
         '',
         caption,
         message,
         self.actions,
         hints,
         -1)
        notify_kwargs = dict(dbus_interface='org.freedesktop.Notifications')
        try:
            self.id = self.proxy.Notify(*notify_args, **notify_kwargs)
        except dbus.DBusException:
            TRACE('DBusException in bubble(); refreshing proxy and retrying')
            try:
                self._add_proxy()
                self.id = self.proxy.Notify(*notify_args, **notify_kwargs)
            except Exception:
                unhandled_exc_handler()

        except Exception:
            unhandled_exc_handler()

        if self.bubble_ctx_ref is not None:
            try:
                self.app.bubble_context.expire_context_ref(self.bubble_ctx_ref)
            except:
                unhandled_exc_handler()

        self.bubble_ctx_ref = ctx_ref
