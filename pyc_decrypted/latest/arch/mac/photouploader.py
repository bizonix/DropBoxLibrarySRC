#Embedded file name: arch/mac/photouploader.py
from __future__ import absolute_import
import datetime
import os
import re
import time
from Foundation import NSDistributedNotificationCenter
from AppKit import NSObject, NSWorkspace
from PyObjCTools import AppHelper
from contextlib import contextmanager
from functools import partial
from objc import typedSelector
from dropbox.callbacks import Handler
from dropbox.camera import Device
from dropbox.camera.util import find_dcim, get_images
from dropbox.camera.uuidstore import SDCardDevice
from dropbox.debugging import easy_repr
from dropbox.gui import event_handler, message_sender, spawn_thread_with_name
from dropbox.preferences import OPT_PHOTO
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox import fsutil
from pymac.constants import kICADeviceScanner, kICADirectory, kICAFileImage, kICAFileMovie, kICAInvalidObjectErr, kICAPropertyImageDateOriginal, kICAPropertyImageDateDigitized, kICAPropertyImageFilename, kICAPropertyImageSize
from pymac.helpers.core import OSStatusError, Preference
from pymac.helpers.imagecapture import ImageCapture, IMAGE_CAPTURE_ENABLED
from pymac.helpers.disk import drive_name_from_path, get_all_removable_drives, is_path_removable_drive
from pymac.helpers.iokit import find_usb_device_path, get_property_dict_from_path
from .util import launch_app
HOT_PLUG_APP_ID = u'com.apple.ImageCapture2'
HOT_PLUG_PATH = u'HotPlugActionPath'
HOT_PLUG_PATH_LAST = u'LastHotPlugActionPath'
HOT_PLUG_ACTION_ARRAY = u'HotPlugActionArray'
USE_PHOTOUPLOADER = IMAGE_CAPTURE_ENABLED
FILE_SIZE_LIMIT = 2147483648L
LARGE_FILE_WAIT = 1

class UnsupportedDevice(Exception):
    pass


def is_disconnected_error(exc):
    return False


def should_handle_devices(opt_photo):
    return opt_photo


class PhotoUploader(object):

    def __init__(self, app, *n, **kw):
        self.app = app
        self.ic = ImageCapture()
        self.notifier = CameraNotifier()
        self.pref = Preference(HOT_PLUG_APP_ID, host_only=True)
        self.is_screen_busy = False

    def check_for_new_devices(self, *n, **kw):
        return (None, None)

    def get_action(self, saved_action):
        action = self.pref.get(HOT_PLUG_PATH, '')
        if not action and saved_action is not None:
            return
        return action

    def set_action(self, path, device = None):
        try:
            path = path or ''
            cur_path = self.pref.get(HOT_PLUG_PATH, '')
            if cur_path != path:
                self.pref[HOT_PLUG_PATH_LAST] = cur_path
                self.pref[HOT_PLUG_PATH] = path
        except Exception:
            unhandled_exc_handler()

    def app_quit(self, saved_old_action):
        if saved_old_action and not self.get_action():
            TRACE('Dropbox quitting. Setting camera connected action to %r', saved_old_action)
            self.set_action(saved_old_action)

    def handle_never(self, old_action, device):
        if device is None and old_action:
            launch_app(old_action)

    @message_sender(AppHelper.callAfter, block=True)
    def register(self, handler):
        self.handler = handler
        if self.app.pref_controller[OPT_PHOTO]:
            self.listen()

    def listen(self):
        self.notifier.add_mount_handler(self._handle_nsworkspacemount_event)
        self.notifier.add_screen_handler(self._handle_availability_changed)
        self.ic.subscribe(self._handle_ic_event)

    def unregister(self):
        pass

    def _handle_availability_changed(self, is_screen_busy):
        TRACE('Screen is busy: %s (%s)', is_screen_busy, time.time())
        self.is_screen_busy = is_screen_busy
        if not self.is_screen_busy:
            self.handler.refresh_devices()

    def _handle_nsworkspacemount_event(self, event):
        try:
            cmd = event.name()
            info = event.userInfo()
            path = info['NSDevicePath']
            if cmd == u'NSWorkspaceDidMountNotification':
                if self.is_screen_busy:
                    TRACE('Skipping NSWorkspaceDidMountNotification because the screen is not available.')
                    return
                if is_path_removable_drive(path):
                    try:
                        name = info['NSWorkspaceVolumeLocalizedNameKey']
                    except KeyError:
                        name = drive_name_from_path(path)

                    TRACE('MOUNTING: %r %r', path, name)
                    self.handler.connected(MacFileDevice(path, name, self.app.uid))
            elif cmd == u'NSWorkspaceWillUnmountNotification':
                TRACE('WILL UNMOUNT: %r', path)
            elif cmd == u'NSWorkspaceDidUnmountNotification':
                TRACE('UNMOUNTED: %r', path)
                self.handler.disconnected(Device(path))
        except KeyError:
            TRACE("Can't get device properties: %r", event)
        except UnsupportedDevice:
            TRACE('Unsupported Device %r', event)
        except Exception:
            unhandled_exc_handler()

    @event_handler
    def _handle_ic_event(self, event):
        try:
            cmd = event['ICANotificationTypeKey']
            obj_id = event['ICANotificationICAObjectKey']
            if cmd == u'ICANotificationTypeDeviceConnectionProgress':
                if self.is_screen_busy:
                    TRACE('Skipping ImageCapture event because the screen is not available.')
                    return
                self.handler.connecting(MacConnectingDevice(obj_id, event))
            elif cmd == u'ICANotificationTypeDeviceAdded':
                if self.is_screen_busy:
                    TRACE('Skipping ImageCapture event because the screen is not available.')
                    return
                self.handler.connected(MacConnectedDevice(obj_id))
            elif cmd == u'ICANotificationTypeDeviceRemoved':
                self.handler.disconnected(Device(obj_id))
        except KeyError:
            TRACE("Device doesn't exist %r", event)
        except UnsupportedDevice:
            TRACE('Unsupported Device %r', event)
        except Exception:
            unhandled_exc_handler()

    def get_connected_devices(self):
        ret = []
        try:
            for dev in self.ic.get_connected_devices():
                if dev.get('clients'):
                    TRACE('ignoring busy device %r', dev['icao'])
                    continue
                try:
                    ret.append(MacConnectedDevice(dev['icao']))
                except UnsupportedDevice:
                    TRACE('Unsupported Device %r', dev)
                except KeyError:
                    TRACE('Device information unavailable (maybe disconnected) %r', dev)

        except Exception:
            unhandled_exc_handler()

        try:
            for path, name in get_all_removable_drives().iteritems():
                try:
                    ret.append(MacFileDevice(path, name, self.app.uid))
                except UnsupportedDevice:
                    TRACE('Unsupported Device %r', path)

        except Exception:
            unhandled_exc_handler()

        TRACE('Connected devices: %s', ret)
        return ret


class CameraNotifier(NSObject):

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls):
        return CameraNotifier.alloc().init()

    def init(self):
        self = super(CameraNotifier, self).init()
        if self is None:
            return

        def register(events, center):
            for event, selector in events.iteritems():
                center.addObserver_selector_name_object_(self, selector, event, None)

        self._screen_handler = Handler()
        self.add_screen_handler = self._screen_handler.add_handler
        self.remove_screen_handler = self._screen_handler.remove_handler
        self._mount_handler = Handler()
        self.add_mount_handler = self._mount_handler.add_handler
        self.remove_mount_handler = self._mount_handler.remove_handler
        notifications = {'com.apple.screensaver.didstart': self.onScreenSaverStarted_,
         'com.apple.screensaver.didstop': self.onScreenSaverStopped_,
         'com.apple.screenIsLocked': self.onScreenLocked_,
         'com.apple.screenIsUnlocked': self.onScreenUnlocked_}
        register(notifications, NSDistributedNotificationCenter.defaultCenter())
        notifications = {'NSWorkspaceSessionDidBecomeActiveNotification': self.onFastUserSwitchEnd_,
         'NSWorkspaceSessionDidResignActiveNotification': self.onFastUserSwitchStart_,
         'NSWorkspaceWillUnmountNotification': self.onMountEvent_,
         'NSWorkspaceDidUnmountNotification': self.onMountEvent_,
         'NSWorkspaceDidMountNotification': self.onMountEvent_}
        register(notifications, NSWorkspace.sharedWorkspace().notificationCenter())
        self._fast_user_switching = False
        self._screen_saver_running = False
        self._screen_locked = False
        self._screen_busy = False
        return self

    def dealloc(self):
        try:
            NSDistributedNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            unhandled_exc_handler()

        try:
            NSWorkspace.sharedWorkspace().notificationCenter().removeObserver_(self)
        except Exception:
            unhandled_exc_handler()

        super(CameraNotifier, self).dealloc()

    def _refresh_screen_state(self):
        screen_busy = self._fast_user_switching or self._screen_saver_running or self._screen_locked
        try:
            if screen_busy != self._screen_busy:
                self._screen_handler.run_handlers(screen_busy)
        finally:
            self._screen_busy = screen_busy

    @typedSelector('v@:@')
    @event_handler
    def onFastUserSwitchStart_(self, notification):
        TRACE('Fast User Switch Started!')
        self._fast_user_switching = True
        self._refresh_screen_state()

    @typedSelector('v@:@')
    @event_handler
    def onFastUserSwitchEnd_(self, notification):
        TRACE('Fast User Switch Ended!')
        self._fast_user_switching = False
        self._refresh_screen_state()

    @typedSelector('v@:@')
    @event_handler
    def onScreenSaverStarted_(self, notification):
        TRACE('Screen Saver Started!')
        self._screen_saver_running = True
        self._refresh_screen_state()

    @typedSelector('v@:@')
    @event_handler
    def onScreenSaverStopped_(self, notification):
        TRACE('Screen Saver Stopped!')
        self._screen_saver_running = False
        self._refresh_screen_state()

    @typedSelector('v@:@')
    @event_handler
    def onScreenLocked_(self, notification):
        TRACE('Screen Locked!')
        self._screen_locked = True
        self._refresh_screen_state()

    @typedSelector('v@:@')
    @event_handler
    def onScreenUnlocked_(self, notification):
        TRACE('Screen Unlocked!')
        self._screen_locked = False
        self._refresh_screen_state()

    @typedSelector('v@:@')
    @event_handler
    def onMountEvent_(self, notification):
        self._mount_handler.run_handlers(notification)


class MacDevice(Device):

    def __init__(self, _id):
        super(MacDevice, self).__init__(_id)
        try:
            self._props = ImageCapture.get_property_dict(self.id)
        except OSStatusError as e:
            if e.errno == kICAInvalidObjectErr:
                raise KeyError(self.id)
            raise

        if self._get_multi(u'deviceIsPasscodeLocked'):
            self.locked = True
        if self._get_multi(u'ICADeviceTypeKey') == 'scanner':
            raise UnsupportedDevice()
        if self._get_multi(u'volume', u'bsdName'):
            TRACE('Ignoring imagecapture notification for sd-card %r', self._get_multi(u'volume'))
            raise UnsupportedDevice()
        self.model = self._get_multi(u'modelName', u'DADeviceModel')
        self.name = self._get_multi(u'ICAUserAssignedDeviceNameKey')
        self.serialnum = self._get_multi(u'ICADeviceSerialNumberString', u'persistentIDString')
        self.uid = self._get_multi(u'UUIDString')
        if not self.uid:
            if self._get_multi(u'file') == kICADeviceScanner:
                raise UnsupportedDevice()
            reg_path = self._get_multi(u'IORegPath')
            if reg_path:
                path = find_usb_device_path(reg_path)
                props = get_property_dict_from_path(path)
                self.model = props.get('USB Product Name', None)
                self.uid = props.get('USB Serial Number', None)
                if self.uid == u'0':
                    self.uid = None
            else:
                report_bad_assumption('Unable to get IORegPath')
                TRACE('Device = %r dict = %r', self, dict(self._props))

    def _get_multi(self, *args):
        for x in args:
            try:
                return self._props[x]
            except KeyError:
                pass


def is_hidden(filename):
    return len(filename) > 1 and filename[0:2] == '._' or filename.lower() == u'.thumbnails'


def find_ica_dcim(tree):
    for fobj in tree:
        if fobj[u'file'] != kICADirectory:
            continue
        if fobj[u'ifil'].lower() == u'dcim':
            return fobj
        if fobj[u'ifil'] == u'0x00010001' and u'tree' in fobj:
            return find_ica_dcim(fobj[u'tree'])


def get_ica_files(directory):
    if u'tree' not in directory:
        raise StopIteration
    tree = directory[u'tree']
    for fobj in tree:
        if fobj[u'ifil'].lower() == u'.nomedia':
            raise StopIteration

    for fobj in tree:
        if is_hidden(fobj[u'ifil']):
            continue
        if fobj[u'file'] == kICADirectory:
            for child_fobj in get_ica_files(fobj):
                yield child_fobj

        elif fobj[u'file'] in (kICAFileImage, kICAFileMovie):
            yield fobj


class MacConnectedDevice(MacDevice):

    @contextmanager
    def files(self):
        dcim = u'tree' in self._props and find_ica_dcim(self._props[u'tree'])
        if dcim:
            yield (MacConnectedDeviceFile(fobj) for fobj in get_ica_files(dcim))
        else:
            yield (MacConnectedDeviceFile(fobj) for fobj in self._props[u'data'] if fobj[u'file'] in (kICAFileImage, kICAFileMovie) and not is_hidden(fobj[u'ifil']))


def datetime_from_string(date_string):
    return datetime.datetime(*time.strptime(date_string, '%Y:%m:%d %H:%M:%S')[0:6])


class MacConnectedDeviceFile(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('fobj', 'cur_pos', 'path', 'needs_write', 'done', 'open')

    def __init__(self, fobj):
        self.fobj = fobj
        self.cur_pos = None
        self.path = None
        self.done = False
        if self.size() > FILE_SIZE_LIMIT:
            self.open = self.open_large
            self.needs_write = False
        else:
            self.needs_write = True
            self.open = self.open_small

    @property
    def id(self):
        return self.fobj

    def time(self):
        try:
            return datetime_from_string(self.fobj[kICAPropertyImageDateOriginal].strip())
        except ValueError:
            try:
                return datetime_from_string(self.fobj[kICAPropertyImageDateDigitized].strip())
            except ValueError:
                return None
            except Exception:
                unhandled_exc_handler()
                return None

        except Exception:
            unhandled_exc_handler()
            return None

    def name(self):
        return self.fobj[kICAPropertyImageFilename]

    def size(self):
        return int(self.fobj[kICAPropertyImageSize])

    @message_sender(spawn_thread_with_name('PHOTODOWNLOADHELPER'), handle_exceptions=False)
    def download_file(self, fs, dest_dir):
        self.path = fs.make_path(ImageCapture.download_file(self.fobj, unicode(dest_dir)))
        return True

    def read_from_download_file(self, f, size):
        done = self.wait_for_download_file(0)
        while True:
            buf = f.read(size)
            if buf or done is True:
                return buf
            done = self.wait_for_download_file(LARGE_FILE_WAIT)
            f.seek(0, 1)

    def wait_for_download_file(self, timeout):
        self.done.event.wait(timeout)
        if self.done.excepted:
            raise self.done.value
        return self.done.value

    @contextmanager
    def open_large(self, fs, dest_dir):
        if self.fobj[u'file'] != kICAFileMovie:
            raise Exception("Why do you have such a large file that's not a movie?")
        fsutil.safe_remove(fs, dest_dir.join(self.name()))
        self.done = self.download_file(fs, dest_dir)
        self.wait_for_download_file(LARGE_FILE_WAIT)
        with fs.open(dest_dir.join(u'.%s_' % self.name()), 'r') as f:
            yield partial(self.read_from_download_file, f)

    @contextmanager
    def open_small(self, *n, **kw):
        self.cur_pos = 0
        yield self.read
        self.cur_pos = None

    def read(self, size = -1):
        start = self.cur_pos
        left = self.fobj[kICAPropertyImageSize] - start
        if size < 0 or size > left:
            size = left
        if size > 0:
            buf = ImageCapture.get_file_data(self.fobj, start, size)
            self.cur_pos += len(buf)
            return buf
        else:
            return ''

    def __repr__(self):
        return easy_repr(self, *self.__slots__)


class MacConnectingDevice(MacDevice):
    PROPS = Device.PROPS + ('percent',)

    def __init__(self, obj_id, event):
        super(MacConnectingDevice, self).__init__(obj_id)
        self.event = event

    @property
    def percent(self):
        try:
            return self.event['ICAContentCatalogPercentCompletedKey']
        except KeyError:
            return 100


class MacFileDevice(SDCardDevice):
    STUPID_NAMES_RE = re.compile('^(NO NAME|UNTITLED).*', re.I)

    def __init__(self, root, name, user_id):
        super(MacFileDevice, self).__init__(root, user_id)
        self.paths = find_dcim(root)
        if not self.paths:
            TRACE('No dcim folder found under: %r', root)
            raise UnsupportedDevice()
        self.root = root
        self.name = name if self.STUPID_NAMES_RE.match(name) is None else None
        self.init_uuid_store(os.path.join(root, u'DCIM'))

    @contextmanager
    def files(self):
        yield get_images(self.root, self.paths, blacklist_nonphotos=False, is_filename_hidden=is_hidden)


def install_photo_components(*args, **kwargs):
    pass


def uninstall_photo_components(*args, **kwargs):
    pass
