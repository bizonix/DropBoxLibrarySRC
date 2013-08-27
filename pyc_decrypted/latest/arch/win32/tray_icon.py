#Embedded file name: arch/win32/tray_icon.py
from __future__ import absolute_import
from collections import deque
from contextlib import contextmanager
import os
import time
import threading
import win32api
import win32con
import win32process
import commctrl
import winerror
import pywintypes
import ctypes
from ctypes.wintypes import HANDLE, HICON, RECT
from comtypes.GUID import GUID
import build_number
from build_number import BUILD_KEY
from dropbox.build_common import get_icon_suffix
from dropbox.db_thread import db_thread
from dropbox.functions import non_string_iterable, snippet
from dropbox.gui import running_on_thread_named, event_handler, message_sender
from dropbox.i18n import trans
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.win32.kernel32 import GetLastError
from dropbox.win32.version import VISTA, WIN7, WINXP, WINDOWS_VERSION
from ui.common.tray import TrayController
from .constants import ICON_INDEX_LOGO, ICON_INDEX_IDLE, ICON_INDEX_BUSY, ICON_INDEX_BUSY2, ICON_INDEX_X, ICON_INDEX_BLANK, ICON_INDEX_BLACK, ICON_INDEX_CAM, ICON_INDEX_CAM2, ICON_INDEX_ATTENTION, ICON_INDEX_PAUSED, ICON_PATHS
from .internal import get_dpi_mode, S_OK
from .util import hard_exit, is_x64
from pynt.dlls.kernel32 import kernel32
from pynt.dlls.shell32 import shell32
from pynt.dlls.user32 import user32
from pynt.helpers.general import IsDWMEnabled, windows_error
from pynt.constants import MEM_COMMIT, MEM_RELEASE, NIIF_USER, NOTIFYICON_VERSION, PAGE_READWRITE
from pynt.types import NOTIFYICONDATA, NOTIFYICONIDENTIFIER, MENUITEMINFO
try:
    import winxpgui as win32gui
except ImportError:
    import win32gui

WM_DWMCOMPOSITIONCHANGED = 798
TB_GETBUTTON = 1047
TB_GETITEMRECT = 1053

class TrayQuitException(Exception):
    pass


_THREAD_NAME = 'TRAYICON'

class TrayIconThread(StoppableThread):

    def __init__(self, tray_icon, *args, **kwargs):
        kwargs['name'] = _THREAD_NAME
        self.tray_icon = tray_icon
        super(TrayIconThread, self).__init__(*args, **kwargs)

    def signal_stop(self):
        self.tray_icon.disable()

    def run(self):
        self.tray_icon.loop()


class TrayIcon(object):
    WM_D_NOTIFY = win32con.WM_USER + 20
    WM_D_WAKEUP = win32con.WM_USER + 21
    WM_D_EXIT = win32con.WM_USER + 22
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]
    FIRST_ID = 1023
    ICON_MAP = {TrayController.BUSY: ICON_INDEX_BUSY,
     TrayController.CAM: ICON_INDEX_CAM,
     TrayController.IDLE: ICON_INDEX_IDLE,
     TrayController.CONNECTING: ICON_INDEX_LOGO,
     TrayController.PAUSED: ICON_INDEX_PAUSED,
     TrayController.BROKEN: ICON_INDEX_X}
    THROBBERS = {ICON_INDEX_BUSY: ICON_INDEX_BUSY2,
     ICON_INDEX_CAM: ICON_INDEX_CAM2}
    TIMER_ANIMATION = 1
    TIMER_REFRESH = 100
    icon_size = None
    window_class_name = BUILD_KEY + 'TrayIcon'
    _notify_icon_data_size = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TrayIcon, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    _messages = deque()

    def _post_runner(on_message_queue, *args, **kwargs):
        cls = TrayIcon
        cls._messages.append((on_message_queue, args, kwargs))
        if not cls._instance or not cls._instance._exists:
            return
        if threading.currentThread() == cls._instance._thread:
            cls._instance._process_messages()
        else:
            win32gui.PostMessage(cls._instance.hwnd, cls.WM_D_WAKEUP, 0, 0)

    def _process_messages(self, *args, **kwargs):
        while self._messages:
            function, args, kwargs = self._messages.popleft()
            function(*args, **kwargs)

    @classmethod
    def load_icons(cls, hinst, icon_size):
        cls.icons = {}
        for icon_index, file_path in ICON_PATHS.iteritems():
            if hasattr(build_number, 'frozen'):
                icon_flags = win32con.LR_SHARED | win32con.LR_DEFAULTSIZE
                icon_path = int(icon_index)
            else:
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                icon_path = file_path % {'suffix': get_icon_suffix(BUILD_KEY)}
            TRACE('Loading tray icon from path: %r', icon_path)
            hicon = win32gui.LoadImage(hinst, icon_path, win32con.IMAGE_ICON, icon_size, icon_size, icon_flags)
            cls.icons[icon_index] = hicon

        cls.icon_size = icon_size

    def __init__(self, app):
        self._thread = None
        self._last_cursor = None
        self._dwm_enabled = None
        self._wait_for_taskbar = False
        self._terminated = False
        self._exists = False
        self.app = app

    def loop(self):
        default_icon = 101
        default_text = ''
        default_menu = None
        while True:
            TRACE('Entering tray icon loop ...')
            try:
                self.initialize(default_icon, default_text, default_menu)
                self._exists = True
                try:
                    msg = win32gui.GetMessage(None, 0, 0)
                    while msg:
                        win32gui.TranslateMessage(msg[1])
                        win32gui.DispatchMessage(msg[1])
                        if not self._exists:
                            break
                        msg = win32gui.GetMessage(None, 0, 0)

                finally:
                    try:
                        win32gui.DestroyWindow(self.hwnd)
                    except Exception as exc:
                        if exc.args and exc.args[0] == 1400:
                            TRACE('The window has already been destroyed!')
                        else:
                            unhandled_exc_handler()

                    win32gui.UnregisterClass(self.class_atom, self.hinst)

                TRACE('Exited message loop.')
                if self._terminated:
                    raise TrayQuitException('We have been told to die!')
                default_icon, default_text, default_menu = self.icon, self.hover_text, self.current_menu
            except TrayQuitException:
                TRACE('Received TrayQuitException!')
                return
            except Exception:
                unhandled_exc_handler()

            TRACE('Exited tray icon loop! Sleeping for a bit before restarting')
            time.sleep(0.25)

    def enable(self, ui_kit):
        TRACE('Enabling Tray Icon ...')
        self._ui_kit = ui_kit
        if not self._thread:
            disable_handler = lambda *args, **kwargs: self.disable()
            self.app.add_quit_handler(disable_handler)
            self._thread = db_thread(TrayIconThread)(self)
        self._thread.start()

    def disable(self):
        TRACE('Disabling Tray Icon ...')
        win32gui.SendMessage(self.hwnd, self.WM_D_EXIT, 0, 0)

    def kill(self):
        TRACE('Killing Tray Icon ...')
        win32gui.SendMessage(self.hwnd, win32con.WM_DESTROY, 0, 0)

    def close(self):
        TRACE('Closing Tray Icon ...')
        win32gui.SendMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)

    def initialize(self, icon, hover_text, current_menu):
        self.icon = icon
        self.flashing_state = None
        self.hover_text = hover_text
        self.current_menu = current_menu
        self.default_menu_index = 0
        self.menu_options = None
        self.tracking_menu_actions_by_id = None
        self.bubblelock = threading.Lock()
        self.bubble_ctx_ref = None
        self.class_atom = None
        self.hinst = win32gui.GetModuleHandle(None)
        dpi_mode = get_dpi_mode()
        if WINDOWS_VERSION >= WIN7:
            icon_size = 16 if dpi_mode <= 96 else (20 if dpi_mode <= 120 else (24 if dpi_mode <= 144 else 32))
        elif WINDOWS_VERSION == VISTA:
            icon_size = 16 if dpi_mode <= 96 else (20 if dpi_mode <= 120 else 24)
        else:
            icon_size = 16 if dpi_mode <= 96 else 20
        TRACE('Icon size is %r for DPI setting of %r.' % (icon_size, dpi_mode))
        if icon_size != self.icon_size:
            self.load_icons(self.hinst, icon_size)
        pre_message_map = {win32gui.RegisterWindowMessage('TaskbarCreated'): self._on_taskbar_created,
         win32con.WM_DESTROY: self._on_destroy,
         win32con.WM_COMMAND: self._on_command,
         win32con.WM_TIMER: self._on_timer,
         win32con.WM_POWERBROADCAST: self._on_power_broadcast,
         WM_DWMCOMPOSITIONCHANGED: self._on_dwm_composition_changed,
         self.WM_D_NOTIFY: self._on_notify,
         self.WM_D_WAKEUP: self._process_messages,
         self.WM_D_EXIT: self._on_exit}
        message_map = {message:event_handler(pre_message_map[message], running_on_thread_named(_THREAD_NAME)) for message in pre_message_map}
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = self.hinst
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map
        self.class_atom = win32gui.RegisterClass(window_class)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(self.class_atom, self.window_class_name, style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, self.hinst, None)
        assert self.hwnd is not None, 'hwnd is None!: %s' % win32api.FormatMessage(win32api.GetLastError())
        win32gui.UpdateWindow(self.hwnd)
        self.consecutive_notify_failures = 0
        self.reported_notify_failure = False
        self.did_nim_add = False
        self.unshown_bubble = None
        self.tooltip = ('', '')
        self._refresh_menu()
        user32.SetTimer(self.hwnd, self.TIMER_REFRESH, 60000, 0)

    def _setup_menu_options(self, menu_options):
        menu_options = list(menu_options) + [(trans(u'Exit'), self.QUIT)]
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        del self._next_action_id

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_action = menu_option
            if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                result.append((option_text,
                 None,
                 option_action,
                 self._next_action_id))
            elif option_action is None:
                result.append((option_text,
                 None,
                 None,
                 self._next_action_id))
            elif non_string_iterable(option_action):
                result.append((option_text,
                 None,
                 self._add_ids_to_menu_options(option_action),
                 self._next_action_id))
            self._next_action_id += 1

        return result

    @message_sender(_post_runner)
    def update_tray_icon(self, icon_state = None, tooltip = None, flashing = None, badge_count = 0, trigger_ping = False):
        should_refresh = False

        def stop_timer():
            if self.icon in self.THROBBERS or self.flashing_state is not None:
                user32.KillTimer(self.hwnd, self.TIMER_ANIMATION)

        def start_timer():
            if self.icon in self.THROBBERS or self.flashing_state is not None:
                user32.SetTimer(self.hwnd, self.TIMER_ANIMATION, 500, 0)

        if icon_state is not None:
            stop_timer()
            if badge_count:
                self.icon = ICON_INDEX_ATTENTION
            else:
                self.icon = self.ICON_MAP[icon_state]
            start_timer()
            TRACE('Changing icon to %s' % self.icon)
            should_refresh = True
        if tooltip is not None:
            self.tooltip = tooltip
            should_refresh = True
        if flashing is not None and (self.flashing_state is not None) != flashing:
            stop_timer()
            self.flashing_state = False if flashing else None
            start_timer()
            TRACE('Stop flashing icon' if self.flashing_state is None else 'Flashing icon')
            should_refresh = True
        if should_refresh:
            self.refresh_icon()

    @message_sender(_post_runner)
    def update_tray_menu(self, menu):
        self.current_menu = menu
        self._refresh_menu()

    def _refresh_menu(self):
        if self.current_menu is not None:
            self._setup_menu_options(self.current_menu)
        self.refresh_icon()

    def _on_timer(self, hwnd, msg, wparam, lparam):
        if wparam == self.TIMER_ANIMATION:
            if self.flashing_state is not None:
                self.refresh_icon(refresh_tooltip=False)
            else:
                self.refresh_icon()
        elif wparam == self.TIMER_REFRESH:
            self.refresh_icon()

    def refresh_icon(self, refresh_tooltip = True):
        if refresh_tooltip:
            self.hover_text = self.tooltip[0]
            if len(self.hover_text) > 128:
                self.hover_text = self.tooltip[1]
        icon = int(self.icon)
        if icon in self.THROBBERS:
            icon = icon if int(time.time() * 2) % 2 else self.THROBBERS[icon]
        if self.flashing_state is not None:
            self.hicon = self.icons[int(self.icon) if self.flashing_state else 601]
            self.flashing_state = not self.flashing_state
        elif type(self.icon) in (int, long):
            self.hicon = self.icons[icon]
        else:
            self.hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        notify_id = (self.hwnd,
         0,
         win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
         self.WM_D_NOTIFY,
         self.hicon,
         self.hover_text)
        self.do_notify(notify_id, retry_on_failure=True)
        if self.unshown_bubble is not None:
            unshown_bubble = self.unshown_bubble
            self.unshown_bubble = None
            self.unshown_bubble = self.do_notify(unshown_bubble)

    @message_sender(_post_runner)
    def render_bubble(self, bubble):
        assert bubble.has_no_ctxt_ref() or bubble.has_valid_ctxt_ref()
        with self.bubblelock:
            try:
                if self.bubble_ctx_ref is not None:
                    self.app.bubble_context.expire_context_ref(self.bubble_ctx_ref)
            except Exception:
                unhandled_exc_handler()

            self.bubble_ctx_ref = bubble.ctxt_ref
        msg = bubble.msg
        can_show_custom_icon = WINDOWS_VERSION >= VISTA or WINDOWS_VERSION == WINXP and WINDOWS_VERSION.service_pack() >= 2
        message = msg[:253] + '...' if len(msg) > 256 else msg
        caption = snippet(bubble.caption, maxchars=64)
        notify_id = (self.hwnd,
         0,
         win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO,
         win32con.WM_USER + 20,
         self.icons[ICON_INDEX_LOGO] if can_show_custom_icon else self.hicon,
         self.hover_text,
         message,
         10000,
         caption,
         NIIF_USER if can_show_custom_icon else win32gui.NIIF_INFO)
        self.unshown_bubble = self.do_notify(notify_id)
        if can_show_custom_icon:
            self.refresh_icon()
        self.app.report_show_bubble(bubble)

    @classmethod
    def _make_notify_icon_data(cls, tup):
        if cls._notify_icon_data_size is None:
            if WINDOWS_VERSION >= VISTA:
                cls._notify_icon_data_size = ctypes.sizeof(NOTIFYICONDATA)
            else:
                cls._notify_icon_data_size = ctypes.sizeof(NOTIFYICONDATA) - ctypes.sizeof(HICON) - ctypes.sizeof(GUID)
        ret = NOTIFYICONDATA(cbSize=cls._notify_icon_data_size, hWnd=tup[0], uID=tup[1], uFlags=tup[2], uCallbackMessage=tup[3], hIcon=tup[4], szTip=tup[5], dwState=0, dwStateMask=0, guidItem=GUID(), hBallonIcon=0)
        if len(tup) >= 9:
            ret.szInfo = tup[6]
            ret.uTimeout = tup[7]
            ret.szInfoTitle = tup[8]
            ret.dwInfoFlags = tup[9]
        return ret

    def do_notify(self, notify_id, retry_on_failure = False):
        try:
            data = self._make_notify_icon_data(notify_id)
            err = None
            message = win32gui.NIM_MODIFY if self.did_nim_add else win32gui.NIM_ADD
            if message == win32gui.NIM_ADD:
                self.do_delete()
            if not shell32.Shell_NotifyIconW(message, ctypes.byref(data)):
                err = GetLastError()
                if err == winerror.ERROR_NO_TOKEN and message == win32gui.NIM_ADD:
                    TRACE('ERROR_NO_TOKEN with a NIM_ADD, trying NIM_MODIFY.')
                    err = None
                    if not shell32.Shell_NotifyIconW(win32gui.NIM_MODIFY, ctypes.byref(data)):
                        err = GetLastError()
            if err is not None:
                retry_on_failure = retry_on_failure or err == winerror.ERROR_TIMEOUT
                raise Exception(err, 'Shell_NotifyIcon Error (%s) --> %r' % ('NIM_MODIFY' if message == win32gui.NIM_MODIFY else 'NIM_ADD', err))
        except Exception as e:
            if e.args and e.args[0] == winerror.ERROR_TIMEOUT:
                self.did_nim_add = False
                return notify_id
            self.consecutive_notify_failures += 1
            if self.consecutive_notify_failures > 9 and not self.reported_notify_failure:
                unhandled_exc_handler()
                self.reported_notify_failure = True
            else:
                unhandled_exc_handler(False)
            if self.consecutive_notify_failures <= 9 and retry_on_failure:
                time.sleep(0.25)
                self.refresh_icon()
            return notify_id

        if message == win32gui.NIM_ADD:
            self.did_nim_add = True
            try:
                data.uTimeout = NOTIFYICON_VERSION
                if not shell32.Shell_NotifyIconW(win32gui.NIM_SETVERSION, ctypes.byref(data)):
                    raise Exception('Shell_NotifyIcon Error (%s) --> %r' % ('NIM_SETVERSION', GetLastError()))
            except Exception:
                unhandled_exc_handler()

        self.consecutive_notify_failures = 0
        self.reported_notify_failure = False
        return

    def do_delete(self):
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
        except Exception:
            pass

    def _on_taskbar_created(self, hwnd, msg, wparam, lparam):
        TRACE('Taskbar has been created, resetting state ...')
        if self.did_nim_add:
            self.do_delete()
            self.did_nim_add = False
        self.refresh_icon()

    def _on_exit(self, hwnd, msg, wparam, lparam):
        TRACE('Exiting ...')
        self._terminated = True
        win32gui.SendMessage(self.hwnd, win32con.WM_DESTROY, 0, 0)
        return 0

    def _on_destroy(self, hwnd, msg, wparam, lparam):
        TRACE('Destroying ...')
        if self.did_nim_add:
            self.do_delete()
        self._exists = False
        win32gui.PostQuitMessage(0)
        return 0

    def _on_notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK:
            self.app.event.report_aggregate_event('tray-icon-click', {'double_click': 1}, approx_timeout=1800)
            self._last_cursor = None
            try:
                self.app.ui_kit.wx_ui_kit.tray_popup.ResetSkip()
            except Exception:
                unhandled_exc_handler()

            if self.app.status_controller.is_true('importing'):
                try:
                    self.app.camera_controller.ui.progress_window_show()
                except Exception:
                    unhandled_exc_handler()

            else:
                try:
                    self.app.open_dropbox()
                except Exception:
                    unhandled_exc_handler()

        elif lparam == win32con.WM_LBUTTONDOWN:
            self.app.event.report_aggregate_event('tray-icon-click', {'left_click': 1}, approx_timeout=1800)
            is_control_pressed = win32api.GetKeyState(win32con.VK_CONTROL) >> 15
            self._last_cursor = win32gui.GetCursorPos()
            self.app.ui_kit.show_tray_popup(context_menu=is_control_pressed)
        elif lparam == win32con.WM_RBUTTONUP:
            self.app.event.report_aggregate_event('tray-icon-click', {'right_click': 1}, approx_timeout=1800)
            self._last_cursor = win32gui.GetCursorPos()
            self.app.ui_kit.show_tray_popup()
        elif lparam == 1029:
            with self.bubblelock:
                ctx_ref = self.bubble_ctx_ref
                self.bubble_ctx_ref = None
            try:
                if ctx_ref is not None:
                    self.app.bubble_context.thunk_and_expire_context_ref(ctx_ref)
            except Exception:
                unhandled_exc_handler()

        return True

    def _on_power_broadcast(self, hwnd, msg, wparam, lparam):
        d = {win32con.PBT_APMQUERYSUSPEND: 'QuerySuspend',
         win32con.PBT_APMSUSPEND: 'Suspend',
         win32con.PBT_APMRESUMEAUTOMATIC: 'ResumeAutomatic'}
        TRACE('WM_POWERBROADCAST: %d %s', wparam, d.get(wparam, 'Unknown'))
        if wparam == win32con.PBT_APMQUERYSUSPEND:
            return win32con.TRUE
        if wparam == win32con.PBT_APMSUSPEND:
            try:
                if self.app.sync_engine:
                    self.app.sync_engine.p2p_state.pause()
            except Exception:
                unhandled_exc_handler()

            try:
                if self.app.conn:
                    self.app.conn.kill_all_connections(all_threads=True)
            except Exception:
                unhandled_exc_handler()

        elif wparam == win32con.PBT_APMRESUMEAUTOMATIC:
            try:
                if self.app.sync_engine:
                    self.app.sync_engine.p2p_state.unpause()
            except Exception:
                unhandled_exc_handler()

        return win32con.TRUE

    def is_dwm_enabled(self):
        if self._dwm_enabled is None:
            self._dwm_enabled = IsDWMEnabled() if WINDOWS_VERSION >= VISTA else False
        return self._dwm_enabled

    def _on_dwm_composition_changed(self, hwnd, msg, wparam, lparam):
        if WINDOWS_VERSION >= VISTA:
            self._dwm_enabled = IsDWMEnabled()
        return win32con.TRUE

    @message_sender(_post_runner)
    def show_tray_menu(self, rect = None):
        if rect is not None:
            anchor_x, anchor_y, _, _ = rect
        elif self._last_cursor is not None:
            anchor_x, anchor_y = self._last_cursor
        else:
            anchor_x, anchor_y = win32gui.GetCursorPos()
        self._last_cursor = None
        if self.menu_options is None:
            if self.current_menu is not None:
                self._setup_menu_options(self.current_menu)
            else:
                return
        menu = win32gui.CreatePopupMenu()
        try:
            self.create_menu(menu, self.menu_options)
            try:
                win32gui.SetForegroundWindow(self.hwnd)
            except Exception:
                unhandled_exc_handler(False)

            self.tracking_menu_actions_by_id = dict(self.menu_actions_by_id)
            self.app.event.report('tray-menu')
            TRACE('tracking popup menu, actions available: %r' % (self.tracking_menu_actions_by_id,))
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, anchor_x, anchor_y, 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        finally:
            win32gui.DestroyMenu(menu)

    @staticmethod
    def _make_menu_info(fType = None, fState = None, wID = None, hSubMenu = None, text = None, hbmpItem = None):
        fMask = 0
        cch = 0
        if fType is not None:
            fMask |= win32con.MIIM_FTYPE
        if fState is not None:
            fMask |= win32con.MIIM_STATE
        if wID is not None:
            fMask |= win32con.MIIM_ID
        if hSubMenu is not None:
            fMask |= win32con.MIIM_SUBMENU
        if hbmpItem is not None:
            fMask |= win32con.MIIM_BITMAP
        if text is not None:
            fMask |= win32con.MIIM_STRING
            cch = len(text)
        return MENUITEMINFO(cbSize=ctypes.sizeof(MENUITEMINFO), fMask=fMask, fType=fType or 0, fState=fState or 0, wID=wID or 0, hSubMenu=long(hSubMenu) if hSubMenu else 0, hmbpItem=long(hbmpItem) if hbmpItem else 0, dwTypeData=text, cch=cch, hbmpChecked=0, hbmpUnchecked=0, dwItemData=None)

    def create_menu(self, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = self._prep_menu_icon(option_icon)
            if option_text is None:
                item = self._make_menu_info(fType=win32con.MFT_SEPARATOR)
                user32.InsertMenuItemW(menu, 0, 1, ctypes.byref(item))
            elif option_id in self.menu_actions_by_id or option_action is None:
                item = self._make_menu_info(text=option_text, hbmpItem=option_icon, fState=option_action is None and win32con.MFS_GRAYED or option_id == self.default_menu_index + self.FIRST_ID and win32con.MFS_DEFAULT or 0, wID=option_id)
                user32.InsertMenuItemW(menu, 0, 1, ctypes.byref(item))
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item = self._make_menu_info(text=option_text, hbmpItem=option_icon, hSubMenu=submenu)
                user32.InsertMenuItemW(menu, 0, 1, ctypes.byref(item))

    def _prep_menu_icon(self, icon):
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(win32gui.GetModuleHandle(None), 101, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_SHARED)
        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)
        return hbm

    def _on_command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        if self.tracking_menu_actions_by_id is None:
            TRACE('Early call to command. %d', id)
            return
        menu_action = self.tracking_menu_actions_by_id[id]
        if menu_action == self.QUIT:
            hard_exit()
        else:
            menu_action()

    def toggle_tray_overflow(self, show = True):
        if WINDOWS_VERSION < WIN7:
            return
        tray_window_class = 'Shell_TrayWnd'
        tray_hwnd = win32gui.FindWindowEx(0, 0, tray_window_class, '')
        if not tray_hwnd:
            raise Exception("Couldn't get tray hwnd")
        notification_window_class = 'TrayNotifyWnd'
        notification_hwnd = win32gui.FindWindowEx(tray_hwnd, 0, notification_window_class, '')
        if not notification_hwnd:
            raise Exception("Couldn't get notification hwnd")
        button_hwnd = win32gui.FindWindowEx(notification_hwnd, 0, 'Button', '')
        if show:
            win32api.SendMessage(button_hwnd, win32con.BM_CLICK, 0, 0)
            win32gui.SetForegroundWindow(button_hwnd)
        else:
            win32api.SendMessage(button_hwnd, win32con.BM_CLICK, 0, 0)

    def _get_screen_rect(self):
        tray_hwnd = win32gui.FindWindowEx(0, 0, 'Shell_TrayWnd', '')
        toolbars = []

        def _check_window(hwnd, *args):
            if win32gui.GetClassName(hwnd) == 'ToolbarWindow32':
                toolbars.append(hwnd)

        win32gui.EnumChildWindows(tray_hwnd, _check_window, None)
        proc_pid = win32process.GetWindowThreadProcessId(tray_hwnd)[1]
        _proc_handle = win32api.OpenProcess(win32con.PROCESS_VM_OPERATION | win32con.PROCESS_VM_READ, False, proc_pid)
        proc_handle = HANDLE(int(_proc_handle))
        c_ptr = ctypes.c_int64 if is_x64() else ctypes.c_int32

        class TB_BUTTON(ctypes.Structure):
            _fields_ = [('iBitmap', ctypes.c_int32),
             ('idCommand', ctypes.c_int32),
             ('fsState_fsStyle_padding', c_ptr),
             ('dwData', c_ptr),
             ('iString', c_ptr)]

        foreign_ptr = kernel32.VirtualAllocEx(proc_handle, None, ctypes.sizeof(TB_BUTTON), MEM_COMMIT, PAGE_READWRITE)
        if not foreign_ptr:
            raise windows_error()
        try:
            for toolbar_hwnd in toolbars:
                num_buttons = win32gui.SendMessage(toolbar_hwnd, commctrl.TB_BUTTONCOUNT, 0, 0)
                button = TB_BUTTON()
                data_ptr = c_ptr()
                for i in range(num_buttons):
                    win32gui.SendMessage(toolbar_hwnd, TB_GETBUTTON, i, foreign_ptr)
                    if not kernel32.ReadProcessMemory(proc_handle, foreign_ptr, ctypes.addressof(button), ctypes.sizeof(TB_BUTTON), None):
                        raise windows_error()
                    if not kernel32.ReadProcessMemory(proc_handle, button.dwData, ctypes.addressof(data_ptr), ctypes.sizeof(data_ptr), None):
                        raise windows_error()
                    if data_ptr.value != self.hwnd:
                        continue
                    win32gui.SendMessage(toolbar_hwnd, TB_GETITEMRECT, i, foreign_ptr)
                    rect = RECT()
                    if not kernel32.ReadProcessMemory(proc_handle, foreign_ptr, ctypes.addressof(rect), ctypes.sizeof(rect), None):
                        raise windows_error()
                    lx, ly = win32gui.ClientToScreen(toolbar_hwnd, (rect.left, rect.top))
                    rx, ry = win32gui.ClientToScreen(toolbar_hwnd, (rect.right, rect.bottom))
                    return (lx,
                     ly,
                     rx - lx,
                     ry - ly)

        finally:
            if not kernel32.VirtualFreeEx(proc_handle, foreign_ptr, 0, MEM_RELEASE):
                TRACE('!! Failed to free memory buffer in Explorer!')

    @message_sender(_post_runner, block=True, dont_post=running_on_thread_named(_THREAD_NAME))
    def get_screen_rect(self, force_old = False):
        try:
            if WINDOWS_VERSION >= WIN7 and not force_old:
                identifier = NOTIFYICONIDENTIFIER(hWnd=self.hwnd, uID=0, guidItem=GUID(), cbSize=ctypes.sizeof(NOTIFYICONIDENTIFIER))
                rect = RECT()
                result = shell32.Shell_NotifyIconGetRect(ctypes.byref(identifier), ctypes.byref(rect))
                if result != S_OK:
                    raise Exception("Shell_NotifyIconGetRect didn't return S_OK: %d (probably hidden)." % result)
                rectangle = (rect.left,
                 rect.top,
                 rect.right - rect.left,
                 rect.bottom - rect.top)
            else:
                rectangle = self._get_screen_rect()
                if rectangle is None:
                    raise Exception("Couldn't get the icon's rectangle.")
        except Exception:
            unhandled_exc_handler()
            return

        TRACE('Got the icon rectangle: %r' % (rectangle,))
        return rectangle
