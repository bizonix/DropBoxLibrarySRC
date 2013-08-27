#Embedded file name: arch/win32/screenshots.py
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
import win32gui
import win32con
import win32api
import wx
import tempfile
from dropbox.client.screenshots import ScreenshotsCallbacks, ScreenshotsController
from dropbox.fsutil import create_unique_file_name
from dropbox.gui import message_sender
from dropbox.monotonic_time import get_monotonic_time_seconds
from pynt.dlls.user32 import user32
from time import localtime, strftime
from ui.common.screenshots import ScreenshotsStrings
import threading

class ScreenshotsListeningThread(threading.Thread):
    KILLER_MESSAGE = win32con.WM_USER + 25

    def __init__(self, app, *args, **kwargs):
        kwargs['name'] = 'SCREENSHOTS_LISTENER'
        super(ScreenshotsListeningThread, self).__init__(*args, **kwargs)
        self._app = app
        self._callbacks = app.screenshots_callbacks
        self.last_screenshot_monotime = 0

    def take_screenshot_for_all_monitors(self):
        monitors = self.get_all_monitors()
        if len(monitors) > 1:
            for monitor in monitors:
                self.handle_screenshot(window_rect=monitor[2], copy_link=False, is_monitor=True)

    def handle_desktop_screenshots(self, copy_link = False):
        try:
            self.handle_screenshot(None, copy_link)
        except Exception:
            unhandled_exc_handler()

    def handle_desktop_screenshot_with_control(self):
        try:
            self.handle_desktop_screenshots(copy_link=True)
        except Exception:
            unhandled_exc_handler()

    def handle_active_window_screenshot(self, copy_link = False):
        try:
            window = win32gui.GetForegroundWindow()
            if window is not None:
                window_rect = win32gui.GetWindowRect(window)
                self.handle_screenshot(window_rect, copy_link)
        except Exception:
            unhandled_exc_handler()

    def handle_active_window_screenshot_with_control(self):
        self.handle_active_window_screenshot(copy_link=True)

    @message_sender(wx.CallAfter, block=True)
    def handle_screenshot(self, window_rect = None, copy_link = False, is_monitor = False):
        TRACE('Handling with new screenshot')
        now = get_monotonic_time_seconds()
        try:
            TRACE('Screenshots time: now %r, last %r', now, self.last_screenshot_monotime)
            if now - self.last_screenshot_monotime < 0.02 and not is_monitor:
                TRACE('Screenshot skipped')
                return
            desktop_rect = self.get_desktop_rect()
            if window_rect is None:
                clipped_window_rect = desktop_rect
            else:
                clipped_window_rect = [0,
                 0,
                 0,
                 0]
                clipped_window_rect[0] = max(window_rect[0], desktop_rect[0])
                clipped_window_rect[1] = max(window_rect[1], desktop_rect[1])
                clipped_window_rect[2] = min(window_rect[2], desktop_rect[2])
                clipped_window_rect[3] = min(window_rect[3], desktop_rect[3])
            w = clipped_window_rect[2] - clipped_window_rect[0]
            h = clipped_window_rect[3] - clipped_window_rect[1]
            TRACE('Screenshot sizes w:%d, h:%d', w, h)
            dcScreen = wx.ScreenDC()
            bmp = wx.EmptyBitmap(w, h)
            memDC = wx.MemoryDC()
            memDC.SelectObject(bmp)
            memDC.Blit(0, 0, w, h, dcScreen, clipped_window_rect[0], clipped_window_rect[1])
            if not copy_link and not is_monitor:
                try:
                    TRACE('Copying screenshot to clipboard')
                    if wx.TheClipboard.Open():
                        try:
                            wx.TheClipboard.SetData(wx.BitmapDataObject(bmp))
                        finally:
                            wx.TheClipboard.Close()

                except Exception:
                    TRACE('!!Hey, we just turned off screen shots on Windows ')
                    unhandled_exc_handler()

            memDC.SelectObject(wx.NullBitmap)
            if ScreenshotsController.should_listen_for_screenshots(self._app):
                img = bmp.ConvertToImage()
                file_base_name = ScreenshotsStrings.file_name % dict(local_time=strftime('%Y-%m-%d %H.%M.%S', localtime()), ext='png')
                try:
                    temp_folder_path = self._app.sync_engine.fs.make_path(unicode(tempfile.gettempdir()))
                    file_path = create_unique_file_name(self._app.sync_engine.fs, temp_folder_path, file_base_name)
                    file_name = unicode(file_path)
                    if file_name:
                        TRACE('Saving screenshot to temp file: %s' % file_name)
                        img.SaveFile(file_name, wx.BITMAP_TYPE_PNG)
                        memDC.Destroy()
                        if self._callbacks is None:
                            report_bad_assumption('screenshots_callbacks is null even though we have a listening thread')
                        else:
                            for cb in self._callbacks.callbacks:
                                if cb is not None:
                                    cb(file_path, copy_link, show_bubble=not is_monitor)

                except Exception:
                    unhandled_exc_handler()

        finally:
            self.last_screenshot_monotime = get_monotonic_time_seconds()

    def get_all_monitors(self):
        return win32api.EnumDisplayMonitors(None, None)

    def get_desktop_rect(self):
        window_coordinates = [0,
         0,
         0,
         0]
        monitors = self.get_all_monitors()
        for monitor in monitors:
            window_coordinates[0] = min(window_coordinates[0], monitor[2][0])
            window_coordinates[1] = min(window_coordinates[1], monitor[2][1])
            window_coordinates[2] = max(window_coordinates[2], monitor[2][2])
            window_coordinates[3] = max(window_coordinates[3], monitor[2][3])
            TRACE('Monitor found: %r', monitor)

        return window_coordinates

    def kill_loop(self, thread_id):
        win32api.PostThreadMessage(thread_id, self.KILLER_MESSAGE, 0, 0)

    def run(self):
        TRACE('Run message loop for screenshots')
        HOTKEY_ACTIONS = {1: self.handle_desktop_screenshot_with_control,
         2: self.handle_desktop_screenshots,
         3: self.handle_active_window_screenshot,
         4: self.handle_active_window_screenshot_with_control}
        HOTKEYS = {1: (win32con.VK_SNAPSHOT, win32con.MOD_CONTROL),
         2: (win32con.VK_SNAPSHOT, 0),
         3: (win32con.VK_SNAPSHOT, win32con.MOD_ALT),
         4: (win32con.VK_SNAPSHOT, win32con.MOD_CONTROL | win32con.MOD_ALT)}
        is_registered = False
        for id, (vk, modifiers) in HOTKEYS.items():
            try:
                user32.RegisterHotKey(None, id, modifiers, vk)
                is_registered = True
                TRACE('Hotkey is registered, modifier:%r, key:%r', modifiers, vk)
            except OSError:
                unhandled_exc_handler(False)

        if not is_registered:
            return
        try:
            msg = win32gui.GetMessage(None, 0, 0)
            while msg:
                if msg[1][1] == self.KILLER_MESSAGE:
                    break
                if msg == -1:
                    continue
                if msg[1][1] == win32con.WM_HOTKEY:
                    action_to_take = HOTKEY_ACTIONS.get(msg[1][2])
                    if action_to_take:
                        action_to_take()
                win32gui.TranslateMessage(msg[1])
                win32gui.DispatchMessage(msg[1])
                msg = win32gui.GetMessage(None, 0, 0)

        finally:
            TRACE('Unregistering hot keys')
            for id in HOTKEYS.keys():
                try:
                    user32.UnregisterHotKey(None, id)
                except OSError:
                    unhandled_exc_handler(False)


class ScreenshotsProvider(object):

    def start_thread(self):
        self._thread = ScreenshotsListeningThread(self._app)
        self._thread.should_run = True
        self._thread.start()

    def check_and_modify_listener(self):
        should_listen = ScreenshotsController.should_listen_for_screenshots(self._app)
        if should_listen and not self._thread:
            self.start_thread()
        elif not should_listen and self._thread:
            self._thread.should_run = False
            self._thread.kill_loop(self._thread.ident)
            self._thread = None

    def __init__(self, app):
        self._app = app
        self._thread = None
        self.check_and_modify_listener()
