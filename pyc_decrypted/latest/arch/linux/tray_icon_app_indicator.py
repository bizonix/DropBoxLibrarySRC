#Embedded file name: arch/linux/tray_icon_app_indicator.py
from __future__ import absolute_import
import wx
import dbus
import dbus.mainloop.glib
import os
import ctypes
import ctypes.util
import sys
from dbus.lowlevel import MethodCallMessage
import build_number
from build_number import BUILD_KEY
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.build_common import get_icon_suffix
from ui.common.tray import TrayController
from ui.wxpython.dropbox_controls import DropboxWxMenu
from .internal import get_contents_root
from .tray_icon_wx import TrayIcon as TrayIconWX
new_with_path = None
set_status = None
set_icon = None
set_attention_icon = None
set_menu = None
get_status = None
gtk = None
APP_INDICATOR_CATEGORY_APPLICATION_STATUS = 0
APP_INDICATOR_STATUS_PASSIVE = 0
APP_INDICATOR_STATUS_ACTIVE = 1
APP_INDICATOR_STATUS_ATTENTION = 2

def lazy_init_libappindicator():
    global gtk
    global set_menu
    global set_attention_icon
    global set_icon
    global get_status
    global new_with_path
    global set_status
    AppIndicator = ctypes.c_void_p
    AppIndicatorCategory = ctypes.c_int
    AppIndicatorStatus = ctypes.c_int
    libappindicator = ctypes.cdll.LoadLibrary(ctypes.util.find_library('appindicator'))
    gtk = ctypes.cdll.LoadLibrary(ctypes.util.find_library('gtk-x11-2.0'))
    new_with_path = libappindicator.app_indicator_new_with_path
    set_status = libappindicator.app_indicator_set_status
    set_icon = libappindicator.app_indicator_set_icon
    set_attention_icon = libappindicator.app_indicator_set_attention_icon
    set_menu = libappindicator.app_indicator_set_menu
    get_status = libappindicator.app_indicator_get_status
    new_with_path.restype = AppIndicator
    new_with_path.argtypes = [ctypes.c_char_p,
     ctypes.c_char_p,
     AppIndicatorCategory,
     ctypes.c_char_p]
    set_status.restype = None
    set_status.argtypes = [AppIndicator, AppIndicatorStatus]
    get_status.restype = AppIndicatorStatus
    get_status.argtypes = [AppIndicator]
    set_attention_icon.restype = None
    set_attention_icon.argtypes = [AppIndicator, ctypes.c_char_p]
    set_icon.restype = None
    set_icon.argtypes = [AppIndicator, ctypes.c_char_p]
    set_menu.restype = None
    set_menu.argtypes = [AppIndicator, ctypes.c_long]
    gtk.gtk_icon_theme_append_search_path.restype = None
    gtk.gtk_icon_theme_append_search_path.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    gtk.gtk_icon_theme_get_default.restype = ctypes.c_void_p
    gtk.gtk_icon_theme_get_default.argtypes = []


class TrayIcon(object):
    initted_dbus_loop = False
    NOT_BUS_NAME = 'org.kde.StatusNotifierWatcher'
    NOT_BUS_PATH = '/StatusNotifierWatcher'
    ICON_SUFFIX = get_icon_suffix(BUILD_KEY)
    BUSY2ICON = 'dropboxstatus-busy2' + ICON_SUFFIX
    BLANKICON = 'dropboxstatus-blank'
    _STATE_MAP = {TrayController.IDLE: 'dropboxstatus-idle' + ICON_SUFFIX,
     TrayController.CONNECTING: 'dropboxstatus-logo' + ICON_SUFFIX,
     TrayController.BUSY: 'dropboxstatus-busy' + ICON_SUFFIX,
     TrayController.BROKEN: 'dropboxstatus-x' + ICON_SUFFIX,
     TrayController.PAUSED: 'dropboxstatus-logo' + ICON_SUFFIX}

    def __init__(self, state, menu, tooltip, app, *n, **kw):
        lazy_init_libappindicator()
        if 'KDE_FULL_SESSION' in os.environ:
            raise Exception('running KDE')
        if not self.initted_dbus_loop:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.initted_dbus_loop = True
        self.wx_tray_icon = None
        self.app = app
        self.notification_owner = None
        self.bus = dbus.SessionBus()
        try:
            self.register_with_indicator(state, menu, tooltip)
        except Exception:
            unhandled_exc_handler(False)
            self.bus.watch_name_owner(self.NOT_BUS_NAME, self._owner_changed)
            self.wx_tray_icon = TrayIconWX(state, menu, tooltip, app)

    def message_filter(self, connection, message):
        try:
            if not isinstance(message, MethodCallMessage):
                return
            method = message.get_member()
            if method == 'AboutToShow':
                args = message.get_args_list()
                self.AboutToShow(*args)
            elif method == 'AboutToShowGroup':
                for args in message.get_args_list():
                    self.AboutToShow(*args)

        except Exception:
            unhandled_exc_handler()

    def register_with_indicator(self, state, menu, tooltip):
        notifier_watcher_object = self.bus.get_object(self.NOT_BUS_NAME, self.NOT_BUS_PATH)
        self.notification_owner = notifier_watcher_object.bus_name
        icon_path = (os.path.join(get_contents_root(), 'images') if hasattr(build_number, 'frozen') else os.path.join(get_contents_root(), 'images', 'status')).encode(sys.getfilesystemencoding())
        self.indicator = new_with_path('dropbox-client-%d' % os.getpid(), self._STATE_MAP[TrayController.IDLE], APP_INDICATOR_CATEGORY_APPLICATION_STATUS, icon_path)
        try:
            self.bus.add_match_string("eavesdrop=true,type='method_call',path='/org/ayatana/NotificationItem/dropbox_client_%d/Menu',member='AboutToShow'" % os.getpid())
            self.bus.add_match_string("eavesdrop=true,type='method_call',path='/com/canonical/NotificationItem/dropbox_client_%d/Menu',member='AboutToShow'" % os.getpid())
            self.bus.add_match_string("eavesdrop=true,type='method_call',path='/org/ayatana/NotificationItem/dropbox_client_%d/Menu',member='AboutToShowGroup'" % os.getpid())
        except dbus.DBusException as e:
            TRACE('Not using eavesdrop because %r', e)
            self.bus.add_match_string("type='method_call',path='/org/ayatana/NotificationItem/dropbox_client_%d/Menu',member='AboutToShow'" % os.getpid())
            self.bus.add_match_string("type='method_call',path='/com/canonical/NotificationItem/dropbox_client_%d/Menu',member='AboutToShow'" % os.getpid())
            self.bus.add_match_string("type='method_call',path='/org/ayatana/NotificationItem/dropbox_client_%d/Menu',member='AboutToShowGroup'" % os.getpid())

        self.bus.add_message_filter(self.message_filter)
        gtk.gtk_icon_theme_append_search_path(gtk.gtk_icon_theme_get_default(), icon_path)
        self.busy_timer = None
        self.flashing = False
        self.current_state = None
        self.tooltip = tooltip
        self.menu = []
        self.last_menu = None
        if menu:
            self.refresh_tray_menu(menu)
        self.change_state(state if state is not None else TrayController.CONNECTING)
        self.update_menu()

    def _owner_changed(self, newowner):
        if newowner == '':
            pass
        elif self.notification_owner != newowner:
            try:
                if self.wx_tray_icon:
                    TRACE('Upgrading to App Indicator')
                    wx_tray_icon = self.wx_tray_icon
                    self.wx_tray_icon = None
                    try:
                        self.register_with_indicator(wx_tray_icon.current_state, wx_tray_icon.cur_menu, wx_tray_icon.tooltip)
                    except Exception:
                        unhandled_exc_handler()
                        self.wx_tray_icon = wx_tray_icon
                    else:
                        try:
                            if wx_tray_icon.flashing_state is not None:
                                self.set_flash(True)
                        except Exception:
                            unhandled_exc_handler()

                        try:
                            wx_tray_icon.Destroy()
                        except Exception:
                            unhandled_exc_handler()

            except Exception:
                unhandled_exc_handler()

        self.notification_owner = newowner

    def AboutToShow(self, id_):
        try:
            if id_ == 0:
                if self.app:
                    self.app.event.report('tray-menu')
                self.update_menu()
        except Exception:
            unhandled_exc_handler()

        return False

    def set_status(self, status):
        return set_status(self.indicator, status)

    def get_status(self):
        return get_status(self.indicator)

    def set_attention_icon(self, icon_name):
        return set_attention_icon(self.indicator, icon_name)

    def set_icon(self, icon_name):
        return set_icon(self.indicator, icon_name)

    def update_menu(self):
        if self.last_menu != self.menu:
            self.wxmenu = DropboxWxMenu(self.menu)
            set_menu(self.indicator, self.wxmenu.GetGtkWidget())
            self.last_menu = self.menu

    def stop_if_running(self):
        if self.busy_timer:
            self.busy_timer.Stop()
            self.busy_timer = None

    def start_if_not_running(self):
        if not self.busy_timer:
            self.busy_timer = wx.CallLater(500, self.busy_tick)

    def busy_tick(self):
        if self.busy_timer:
            old_status = self.get_status()
            self.set_status(APP_INDICATOR_STATUS_ATTENTION if old_status == APP_INDICATOR_STATUS_ACTIVE else APP_INDICATOR_STATUS_ACTIVE)
            self.busy_timer = wx.CallLater(500, self.busy_tick)

    def set_flash(self, on):
        if self.wx_tray_icon:
            return self.wx_tray_icon.set_flash(on)
        if self.flashing != on:
            self.stop_if_running()
            self.flashing = on
            if on:
                self.set_attention_icon(self.BLANKICON)
                self.set_status(APP_INDICATOR_STATUS_ATTENTION)
            else:
                self.set_attention_icon(self.BUSY2ICON if self.current_state == TrayController.BUSY else self.BLANKICON)
                self.set_status(APP_INDICATOR_STATUS_ACTIVE)
            if self.current_state == TrayController.BUSY or self.flashing:
                self.start_if_not_running()

    def change_state(self, new_state, first_time = False):
        if self.wx_tray_icon:
            return self.wx_tray_icon.change_state(new_state, first_time)
        if new_state == self.current_state:
            return
        self.stop_if_running()
        self.current_state = new_state
        self.set_icon(self._STATE_MAP[new_state])
        self.set_attention_icon(self.BUSY2ICON if new_state == TrayController.BUSY else self.BLANKICON)
        self.set_status(APP_INDICATOR_STATUS_ACTIVE)
        if new_state == TrayController.BUSY or self.flashing:
            self.start_if_not_running()

    def refresh_tray_menu(self, menu):
        if self.wx_tray_icon:
            return self.wx_tray_icon.refresh_tray_menu(menu)
        self.menu = menu

    def set_tooltip(self, tooltip):
        if self.wx_tray_icon:
            return self.wx_tray_icon.set_tooltip(tooltip)
        self.tooltip = tooltip

    def Destroy(self):
        if self.wx_tray_icon:
            return self.wx_tray_icon.Destroy()
        self.stop_if_running()

    def get_screen_rect(self):
        if self.wx_tray_icon:
            return self.wx_tray_icon.get_screen_rect()
