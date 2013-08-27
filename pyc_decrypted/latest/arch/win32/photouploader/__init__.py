#Embedded file name: arch/win32/photouploader/__init__.py
import comtypes
import sys
import win32api
import win32con
import wx
from comtypes.client import CreateObject
from comtypes.GUID import GUID
from pprint import pformat
from dropbox.client.multiaccount.constants import Roles
from dropbox.db_thread import db_thread
from dropbox.functions import handle_exceptions
from dropbox.preferences import OPT_PHOTO
from dropbox.threadutils import StoppableThread
from dropbox.gui import message_sender
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.url_info import dropbox_url_info
from dropbox.win32.version import WINDOWS_VERSION, WIN8, WIN7, WINXP
from pynt.constants import ERROR_LIBRARY_NOT_REGISTERED
from .autoplay_defaults import any_defaults_are_dropbox, check_for_new_devices, get_autoplay_defaults, set_dropbox_default_autoplay, set_old_default_autoplay
from .autoplay_event_handler import AutoplayEventHandler, AutoplayEventHandlerImpl
from .autoplay_proxy import PhotoUploaderProxy
from .wiacallback import DropboxWiaDataCallbackImpl
from ..internal import uses_com, ShellExecuteW
from .constants import USE_PHOTOUPLOADER, AUTOPLAY_DEFAULTS_SUPPORTED
from .helpers import is_disconnected_error
from .install import install_photo_components, is_photouploader_installed, run_photo_update, uninstall_photo_components

def should_handle_devices(opt_photo):
    return True


class PhotoUploader(object):

    def __init__(self, app, *n, **kw):
        self.app = app
        self._connected_devices = []
        self.old_defaults = None

    def check_for_new_devices(self, known_devices):
        return check_for_new_devices(known_devices)

    def get_action(self, saved_old_defaults):
        if not AUTOPLAY_DEFAULTS_SUPPORTED:
            return
        if saved_old_defaults is None and self.app.is_first_run and self.old_defaults is None:
            self.old_defaults = get_autoplay_defaults()
            TRACE('Photouploader: Saving old autoplay defaults before overriding:\n %s', pformat(self.old_defaults))
        elif saved_old_defaults is not None and self.app.is_first_run and self.app.pref_controller[OPT_PHOTO]:
            if not any_defaults_are_dropbox():
                self.app.pref_controller.update({OPT_PHOTO: False})
        return self.old_defaults

    def set_action(self, old_defaults, device = None):
        if not AUTOPLAY_DEFAULTS_SUPPORTED:
            return
        elif old_defaults is not None:
            TRACE('Resetting autoplay defaults for %s', 'device id %r' % device if device else 'all devices')
            set_old_default_autoplay(old_defaults, device)
            return
        else:
            defaults_set = set_dropbox_default_autoplay()
            self.old_defaults = None
            return defaults_set

    def app_quit(self, unused):
        pass

    def handle_never(self, old_defaults, device = None):
        if old_defaults is not None:
            return self.set_action(old_defaults, device)

    def register(self, handler):
        self.handler = handler
        if self.app.mbox.linked and self.app.mbox.role != Roles.PERSONAL:
            TRACE('COMSERVERTHREAD: Disabling camera uploads for business account!')
            return
        self.COMserver = db_thread(COMServerThread)(self.app, self)
        self.COMserver.start()

    def listen(self):
        pass

    def unregister(self):
        self.COMserver.signal_stop()

    def get_connected_devices(self):
        return self._connected_devices

    def connected(self, device):
        if device not in self._connected_devices:
            self._connected_devices.append(device)
            self.handler.connected(device)

    def disconnected(self, device):
        if device in self._connected_devices:
            self._connected_devices.remove(device)
            self.handler.disconnected(device)


def get_proxy():
    return PhotoUploaderProxy()


@handle_exceptions
def open_autoplay_settings():
    if WINDOWS_VERSION > WINXP:
        ShellExecuteW(0, 'open', 'control.exe', '/name Microsoft.AutoPlay', None, win32con.SW_SHOWNORMAL)
    else:
        dropbox_url_info.launch_full_url(dropbox_url_info.help_url('client_upload_autoplay'))


class COMServerThread(StoppableThread):

    def __init__(self, app, handler, *n, **kw):
        kw['name'] = 'COMSERVERTHREAD'
        super(COMServerThread, self).__init__(*n, **kw)
        self.app = app
        self.handler = handler

    @message_sender(wx.CallAfter)
    def start_keepalive(self):
        try:
            self.keepalive = CreateObject(AutoplayEventHandler)
            TRACE('Created autoplay event handler object for keepalive %r', self.keepalive)
        except WindowsError as e:
            if e.winerror == ERROR_LIBRARY_NOT_REGISTERED:
                TRACE('!! Dropbox autoplay typelib not registered! Attempting registration now!')
                install_photo_components(as_admin=False, force=True)
        except Exception:
            unhandled_exc_handler()

    @uses_com
    def run(self):
        self.thread_id = win32api.GetCurrentThreadId()
        TRACE('COM thread %d starting.', self.thread_id)
        AutoplayEventHandlerImpl.app = self.app
        AutoplayEventHandlerImpl.handler = self.handler
        while not self.stopped():
            try:
                classes = [AutoplayEventHandlerImpl, DropboxWiaDataCallbackImpl]
                classobjects = [ comtypes.server.localserver.ClassFactory(cls) for cls in classes ]
                if WINDOWS_VERSION == WIN8:
                    self.start_keepalive()
                TRACE('Running local server STA loop')
                comtypes.COMObject.__run_localserver__(classobjects)
            except Exception:
                unhandled_exc_handler()

        TRACE('COM thread stopping')

    def set_wakeup_event(self):
        TRACE('COM thread wakeup')
        try:
            thread_id = self.thread_id
        except AttributeError:
            pass
        else:
            win32api.PostThreadMessage(thread_id, win32con.WM_QUIT, 0, 0)


if False:

    def TRACE(str, *n):
        print str % n


    def unhandled_exc_handler():
        import traceback
        TRACE('%s', traceback.format_exc())


    class TestHandler:

        def connected(self, obj):
            files = obj.files()


    if __name__ == '__main__':
        import logging
        logging.basicConfig(filename='C:\\repos\\client\\arch\\win32\\photouploader\\COM.log', filemode='w', level=logging.DEBUG)
        AutoplayEventHandlerImpl.app = None
        AutoplayEventHandlerImpl.handler = TestHandler()
        try:
            if len(sys.argv) > 1 and sys.argv[1] == '-test':
                TRACE('Creating handler object!')
                handler = AutoplayEventHandlerImpl()
                TRACE('Handler created!')
                handler.Initialize('test')
                handler.HandleEvent('\\\\?\\USB#VID_04A9&PID_3174#C9445975B9F746CCA8A28F73F42EC5C4#{6ac27878-a6fa-4155-ba85-f98f491d4f33}', '', 'DeviceArrival')
                from ctypes import byref
                from ctypes.wintypes import ULONG
                guid = GUID('{A28BBADE-64B6-11D2-A231-00C04FA31809}')
                _ulong = ULONG(1)
                handler.ImageEventCallback(byref(guid), 'Device Connected', u'{EEC5AD98-8080-425f-922A-DABF3DE3F69A}\\0001', '', 131072, '', byref(_ulong), 0)
            else:
                from comtypes.server.register import UseCommandLine
                UseCommandLine(AutoplayEventHandlerImpl)
        except Exception:
            unhandled_exc_handler()
