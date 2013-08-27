#Embedded file name: arch/win32/photouploader/autoplay_proxy.py
import ctypes
import comtypes
import comtypes.server.localserver
from comtypes.client import CreateObject
from comtypes.GUID import GUID
import threading
import win32api
import win32con
from build_number import BUILD_KEY
from dropbox.threadutils import StoppableThread
from dropbox.db_thread import db_thread
from dropbox.trace import TRACE, unhandled_exc_handler
from .constants import DROPBOX_AUTOPLAY_PROGID, DROPBOX_AUTOPLAY_PROXY_PROGID, DROPBOX_AUTOPLAY_PROXY_VERNO
from ..internal import uses_com
from PhotoUploaderLib import DropboxAutoplayProxy, IHWEventHandler, IDropTarget, IWiaEventCallback
PHOTO_INSTALL_URL = 'c/help/photo_install'

def async_call(func):

    def async_func(*args, **kwargs):
        try:
            try:
                funcname = func.func_name
            except AttributeError:
                funcname = 'UnnamedFunction'

            threading.Thread(target=func, name='Async' + funcname, args=args, kwargs=kwargs).start()
            return 0
        except Exception:
            unhandled_exc_handler()
            raise

    return async_func


@async_call
@uses_com
def proxy_wia_event(app, event_guid, device_id, call_when_done):
    try:
        TRACE('DropboxAutoplayProxy_IWiaEventCallback::ImageEventCallback')
        TRACE('event_guid %r', event_guid)
        TRACE('bstrDeviceID %r', device_id)
        try:
            handler = CreateObject(progid=DROPBOX_AUTOPLAY_PROGID, interface=IWiaEventCallback)
        except Exception:
            app.desktop_login.login_and_redirect(PHOTO_INSTALL_URL)
            unhandled_exc_handler()
        else:
            handler.ImageEventCallback(event_guid, 'Device Connected', device_id, '', 0, '', ctypes.byref(ctypes.wintypes.ULONG(1)), 0)

    except Exception:
        unhandled_exc_handler()
    finally:
        call_when_done()


class PhotoUploaderProxy(object):

    def do_your_thing(self, app, call_when_done, cmdline_args):
        if cmdline_args and cmdline_args[0].lower() == '/wia':
            try:
                cmdline_args = cmdline_args[1:]
                arg_dict = {}
                arg_pairs = [ arg.split(':') for arg in cmdline_args ]
                for pair in arg_pairs:
                    arg_dict[pair[0]] = pair[1]

                device_id = arg_dict['/device_id']
                event_id = GUID(arg_dict['/event_id'])
                proxy_wia_event(app, event_id, device_id, call_when_done)
            except Exception:
                unhandled_exc_handler()

        else:
            try:
                self.COMProxyserver = db_thread(COMProxyServerThread)(app, call_when_done)
                self.COMProxyserver.start()
            except Exception:
                unhandled_exc_handler()


class COMProxyServerThread(StoppableThread):

    def __init__(self, app, call_when_done, *n, **kw):
        kw['name'] = 'COMPROXYSERVERTHREAD'
        super(COMProxyServerThread, self).__init__(*n, **kw)
        DropboxAutoplayProxyImpl.app = app
        DropboxAutoplayProxyImpl.call_when_done = call_when_done
        self.call_when_done = call_when_done

    @uses_com
    def run(self):
        self.thread_id = win32api.GetCurrentThreadId()
        TRACE('Proxy COM thread %d starting.', self.thread_id)
        try:
            TRACE('Running local server STA loop')
            comtypes.server.localserver.run([DropboxAutoplayProxyImpl])
        except Exception:
            unhandled_exc_handler()

        TRACE('Proxy COM thread stopping')

    def set_wakeup_event(self):
        TRACE('Proxy COM thread wakeup')
        try:
            thread_id = self.thread_id
        except AttributeError:
            pass
        else:
            win32api.PostThreadMessage(thread_id, win32con.WM_QUIT, 0, 0)

        self.call_when_done()


class DropboxAutoplayProxyImpl(DropboxAutoplayProxy):
    _reg_threading_ = 'Apartment'
    _reg_progid_ = '%s.%d' % (DROPBOX_AUTOPLAY_PROXY_PROGID, DROPBOX_AUTOPLAY_PROXY_VERNO)
    _reg_novers_progid_ = DROPBOX_AUTOPLAY_PROXY_PROGID
    _reg_desc_ = BUILD_KEY + ' autoplay proxy COM server'
    _reg_clsctx_ = comtypes.CLSCTX_LOCAL_SERVER
    _regcls_ = comtypes.server.localserver.REGCLS_MULTIPLEUSE

    def __del__(self):
        self.call_when_done()

    def Initialize(self, init_params):
        TRACE('DropboxAutoplayProxy_Initialize')
        TRACE('init_params: %s', init_params)
        try:
            if hasattr(self, 'handler'):
                TRACE('!! Initialize being called twice??')
            try:
                self.handler = CreateObject(progid=DROPBOX_AUTOPLAY_PROGID, interface=IHWEventHandler)
            except Exception:
                self.app.desktop_login.login_and_redirect(PHOTO_INSTALL_URL)
                unhandled_exc_handler()
            else:
                self.handler.Initialize(init_params)

        except Exception:
            unhandled_exc_handler()

        return 0

    def HandleEvent(self, device_id, alt_device_id, event_type):
        TRACE('DropboxAutoplayProxy_HandleEvent')
        try:
            self.handler.HandleEvent(device_id, alt_device_id, event_type)
        except AttributeError:
            TRACE('!! HandleEvent was called without preceding call to Initialize')
            try:
                self.handler = CreateObject(progid=DROPBOX_AUTOPLAY_PROGID, interface=IHWEventHandler)
            except Exception:
                self.app.desktop_login.login_and_redirect(PHOTO_INSTALL_URL)
                unhandled_exc_handler()
            else:
                self.handler.HandleEvent(device_id, alt_device_id, event_type)

        except Exception:
            unhandled_exc_handler()

        return 0

    def HandleEventWithContent(self, device_id, alt_device_id, event_type, content_type_handler, obj_data):
        TRACE("!! DropboxAutoplayProxy_HandleEventWithContent shouldn't be called!  But forwarding just in case")
        try:
            self.handler.HandleEventWithContent(device_id, alt_device_id, event_type, content_type_handler, obj_data)
        except AttributeError:
            TRACE('!! HandleEventWithContent was called without preceding call to Initialize')
            try:
                self.handler = CreateObject(progid=DROPBOX_AUTOPLAY_PROGID, interface=IHWEventHandler)
            except Exception:
                self.app.desktop_login.login_and_redirect(PHOTO_INSTALL_URL)
                unhandled_exc_handler()
            else:
                self.handler.HandleEventWithContent(device_id, alt_device_id, event_type, content_type_handler, obj_data)

        except Exception:
            unhandled_exc_handler()

        return 0

    def DragEnter(self, data_obj, grfKeyState, pt):
        TRACE('DropboxAutoplayProxy_IDropTarget::DragEnter - not forwarding')
        return 0

    def DragOver(self, this, grfKeyState, pt, pdwEffect):
        TRACE('DropboxAutoplayProxy_IDropTarget::DragOver - not forwarding')
        return 0

    def DragLeave(self):
        TRACE('DropboxAutoplayProxy_IDropTarget::DragLeave - not forwarding')
        return 0

    def Drop(self, data_obj, key_state, pt, pdw_effect):
        try:
            TRACE('DropboxAutoplayProxy_IDropTarget::Drop')
            TRACE('data_obj: %r, key_state: %r, pt: %r, dw_effect: %r', data_obj, key_state, pt, pdw_effect.contents)
            try:
                handler = CreateObject(progid=DROPBOX_AUTOPLAY_PROGID, interface=IDropTarget)
            except Exception:
                self.app.desktop_login.login_and_redirect(PHOTO_INSTALL_URL)
                unhandled_exc_handler()
            else:
                handler.Drop(data_obj, key_state, pt, pdw_effect)

        except Exception:
            unhandled_exc_handler()

        return 0
