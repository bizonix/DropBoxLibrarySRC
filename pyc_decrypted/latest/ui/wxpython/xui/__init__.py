#Embedded file name: ui/wxpython/xui/__init__.py
import os
import types
from itertools import count
import win32gui
import win32con
import pycef
import wx
from build_number import is_frozen
from dropbox.functions import handle_exceptions, non_string_iterable
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.common.xui import XUIException, XUIHost
from ui.wxpython.dropbox_controls import DropboxWxMenu
from ui.wxpython.xui.javascript import inject_object, parse_exception

class XUIApplication(pycef.CefApp):
    _instance = None

    def __init__(self):
        assert XUIApplication._instance is None
        pycef.CefApp.__init__(self)
        XUIApplication._instance = self
        self._terminated = False

    @message_sender(wx.CallAfter, block=True)
    def shutdown(self, *args, **kwargs):
        TRACE('Destroying CEF (Wx)')
        self._terminated = True
        pycef.CefShutdown()

    @classmethod
    def is_shutdown(cls):
        if cls._instance is None:
            return True
        return cls._instance._terminated


class _XUIHostLoadHandler(pycef.CefLoadHandler):

    def __init__(self, load_callback):
        self._load_callback = load_callback
        pycef.CefLoadHandler.__init__(self)

    @event_handler
    def OnLoadEnd(self, browser, frame, code):
        self._load_callback(frame)


class _XUIHostMenuHandler(pycef.CefMenuHandler):

    def __init__(self):
        self._DevToolsEnabled = False
        pycef.CefMenuHandler.__init__(self)

    @event_handler
    def OnBeforeMenu(self, browser, menuInfo):
        if is_frozen():
            return True
        return False

    @event_handler
    def OnMenuAction(self, browser, menuId):
        if is_frozen():
            return False
        if menuId != pycef.MENU_ID_VIEWSOURCE:
            return False
        if not self._DevToolsEnabled:
            TRACE('Showing Developer Tools ...')
            browser.ShowDevTools()
            self._DevToolsEnabled = True
        else:
            TRACE('Closing Developer Tools ...')
            browser.CloseDevTools()
            self._DevToolsEnabled = False
        return True


class _XUIHostV8ContextHandler(pycef.CefV8ContextHandler):

    def __init__(self, context_callback, uncaught_callback):
        self._context_callback = context_callback
        self._uncaught_callback = uncaught_callback
        pycef.CefV8ContextHandler.__init__(self)

    @event_handler
    def OnContextCreated(self, browser, frame, context):
        self._context_callback(frame, context)

    @event_handler
    def OnUncaughtException(self, browser, frame, context, exception, stackTrace):
        self._uncaught_callback(exception)


class _XUIHostClient(pycef.CefClient):

    def __init__(self, load_callback, context_callback, uncaught_callback):
        pycef.CefClient.__init__(self)
        self._menu_handler = _XUIHostMenuHandler()
        self._load_handler = _XUIHostLoadHandler(load_callback)
        self._v8_context_handler = _XUIHostV8ContextHandler(context_callback, uncaught_callback)

    @event_handler
    def GetV8ContextHandler(self):
        return self._v8_context_handler

    @event_handler
    def GetLoadHandler(self):
        return self._load_handler

    @event_handler
    def GetMenuHandler(self):
        return self._menu_handler


class WxFrameXUIHost(wx.Frame, XUIHost):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, controller, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        XUIHost.__init__(self, controller)
        self._Loaded = False
        self._Browser = None
        self._DevToolsEnabled = False
        self._ViewURL = None

    @assert_message_queue
    def _InitializeCef(self):
        try:
            self._Client = _XUIHostClient(self._OnLoad, self._OnContext, self._OnException)
            window_info = pycef.CefWindowInfo()
            client_rect = self.GetClientRect()
            rect = pycef.RECT()
            rect.left, rect.top, rect.right, rect.bottom = (0,
             0,
             client_rect.GetWidth(),
             client_rect.GetHeight())
            window_info.SetAsChild(self.GetHandle(), rect)
            browser_settings = pycef.CefBrowserSettings()
            browser_settings.history_disabled = True
            browser_settings.site_specific_quirks_disabled = True
            browser_settings.drag_drop_disabled = True
            browser_settings.load_drops_disabled = True
            browser_settings.remote_fonts_disabled = True
            browser_settings.java_disabled = True
            browser_settings.plugins_disabled = True
            browser_settings.javascript_open_windows_disallowed = True
            browser_settings.javascript_close_windows_disallowed = True
            browser_settings.javascript_access_clipboard_disallowed = True
            browser_settings.universal_access_from_file_urls_allowed = False
            browser_settings.text_area_resize_disabled = True
            browser_settings.page_cache_disabled = True
            browser_settings.hyperlink_auditing_disabled = True
            browser_settings.local_storage_disabled = True
            browser_settings.databases_disabled = True
            browser_settings.application_cache_disabled = True
            browser_settings.webgl_disabled = True
            browser_settings.accelerated_compositing_enabled = False
            browser_settings.developer_tools_disabled = bool(is_frozen())
            browser = pycef.CefBrowser.CreateBrowserSync(window_info, self._Client, 'about:blank', browser_settings)
            if not browser:
                raise XUIException('Failed to create the browser!')
            self._Browser = browser
            data = self.controller._get_view_data().encode('utf-8')
            self._ViewURL = 'xui://%s' % self.controller.__xui_resource__
            frame = browser.GetMainFrame()
            frame.LoadString(data, self._ViewURL)
            self.Bind(wx.EVT_SIZE, self._OnSize)
            self.Bind(wx.EVT_SET_FOCUS, self._OnSetFocus)
        except Exception:
            self._set_failed(fatal=True)
            unhandled_exc_handler()

    def _GetBrowserHandle(self):
        if not self._Browser:
            return None
        hwnd = self._Browser.GetWindowHandle()
        if not hwnd:
            TRACE("!! Couldn't find the inner HWND for the CEF window!")
            return None
        return hwnd

    def _ClearHoverState(self):
        if not self._Browser:
            return
        self._Browser.SendMouseMoveEvent(0, 0, False)

    @event_handler
    def _OnSetFocus(self, event):
        hwnd = self._GetBrowserHandle()
        if hwnd is None:
            return
        win32gui.PostMessage(hwnd, win32con.WM_SETFOCUS, 0, 0)

    @event_handler
    def _OnSize(self, event):
        hwnd = self._GetBrowserHandle()
        if hwnd is None:
            return
        rect = self.GetClientRect()
        win32gui.SetWindowPos(hwnd, 0, rect.GetX(), rect.GetY(), rect.GetWidth(), rect.GetHeight(), win32con.SWP_NOZORDER)

    def show_context(self, options, x, y):
        menu = DropboxWxMenu(options)
        self.PopupMenu(menu, (x, y))

    @assert_message_queue
    def _OnLoad(self, frame):
        TRACE('Loaded frame %r (%r)', frame, frame.GetURL())
        if frame.GetURL() != self._ViewURL:
            return
        self._Loaded = True

    @assert_message_queue
    def _OnException(self, exception):
        TRACE('!! Host failing due to uncaught JavaScript error.')
        self.failed = True
        raise parse_exception(exception)

    @assert_message_queue
    def _OnContext(self, frame, context):
        if frame.GetURL() != self._ViewURL:
            return
        TRACE('Loaded context %r for frame %r.', context, frame)
        inject_object(context, self.controller._OBJECT_NAME, self.controller)
