#Embedded file name: dropbox/client/photocontroller.py
import functools
import uuid
import arch
from dropbox.client.multiaccount.constants import Roles
from dropbox.client.photo_constants import DEVICE_DEFAULTS_SET, FIRST_USE, OLD_PHOTO_ACTION
from dropbox.client.photoimporter import PhotoImporter, PhotoGalleryImporter
from dropbox.event import report
from dropbox.functions import handle_exceptions
from dropbox.lock_ordering import NonRecursiveLock
from dropbox.platform import platform
from dropbox.preferences import OPT_PHOTO
from dropbox.trace import TRACE, unhandled_exc_handler

class PhotoController(object):

    def __init__(self, app, uploader, **kwargs):
        self.app = app
        TRACE('Creating camera UI')
        self.ui = self.app.ui_kit.create_camera_ui(bubble_context=self.app.bubble_context, tray_controller=self.app.tray_controller, app=app, **kwargs)
        self.uploader = uploader
        self.photodb = self.uploader.photodb
        self.lock = NonRecursiveLock()
        self.importer = None
        self.import_id = uuid.uuid4().hex

    def report_camera_event(self, event_name, device, **event):
        event.update(dict(import_id=self.import_id, mfg=device.manufacturer, model=device.model, device_uid=device.uid, device_name=device.name, type=device.__class__.__name__))
        report(event_name, data=event)

    def report_step(self, step, device, **event):
        event['step'] = step
        self.report_camera_event('photo-import', device, **event)

    def on_change_state(self, device, importer, new_state, always = False, done_cb = None, never_cb = None, old_action = None, highlight = True):
        if new_state == PhotoImporter.DONE:
            transferred_files = importer.transferred_files.get()
            failed_files = importer.remaining_files
            skipped_files = importer.skipped_files
            error = importer.error.get()
            total_size = sum((f.size for f in transferred_files))
            try:
                if error or failed_files:
                    self.report_step('error', device, imported=len(transferred_files), imported_size=total_size, failed=len(failed_files), error=error.__class__.__name__ if error else 'unknown')
                else:
                    self.report_step('done', device, imported=len(transferred_files), imported_size=total_size, failed=len(failed_files))
                transferred = [ f.path for f in transferred_files ]
                failed = [ f.f_name for f in failed_files ]
                skipped = [ f.f_name for f in skipped_files ]
                import_result = self.ui.done(device, self.photodb.get_device_last_import(device.uid), transferred, skipped, failed, error, never_cb, old_action, highlight=highlight)
                self.photodb.set_device_last_import(device.uid, import_result)
            except Exception:
                unhandled_exc_handler()

            if done_cb:
                done_cb(device, error, failed_files, transferred_files)
        elif new_state == PhotoImporter.STARTING:
            self.report_step('start', device, always=always)
        elif new_state == PhotoImporter.SCANNING:
            self.ui.importing()

    def hook_up_ui(self, device, importer, done_cb = None, never_cb = None, old_action = None, highlight = True):
        self.ui.set_on_cancel(importer.cancel)
        with self.lock:
            self.on_cancel = importer.cancel
            self.on_disconnect = importer.disconnected
        self.ui.starting(self.import_id)
        importer.total_bytes.register(self.ui.finding)
        importer.cur_bytes.register(self.ui.progress)
        importer.transferred_files.register(self.ui.file_imported)
        on_change_state = functools.partial(self.on_change_state, device, importer, done_cb=done_cb, never_cb=never_cb, old_action=old_action, highlight=highlight)
        importer.state.register(on_change_state)
        importer.found_files.register(self.ui.file_count)
        importer.report_camera_event = self.report_camera_event


class GalleryImportController(PhotoController):

    def __init__(self, app, done_cb, check_space_callback = None, import_albums = False, create_subdirs = False):
        super(GalleryImportController, self).__init__(app=app, uploader=app.photo_uploader, show_progress_by_default=True, use_busy_icon=True)
        self.done_cb = done_cb
        self.check_space_callback = check_space_callback
        self.import_albums = import_albums
        self.create_subdirs = create_subdirs

    @handle_exceptions
    def handle_start(self, gallery):
        self.gallery = gallery
        self.importer = PhotoGalleryImporter(device=gallery, uploader=self.uploader, app=self.app, check_space_callback=self.check_space_callback, import_albums=self.import_albums, create_subdirs=self.create_subdirs)
        self.photodb.add_device(self.gallery.uid, setting=self.photodb.PROMPT_NO_ALWAYS)
        self.importer.device_ready()
        highlight = not self.create_subdirs
        if not self.check_space_callback:
            TRACE('IPHOTOIMPORT: Hooking up the UI')
            self.hook_up_ui(self.gallery, self.importer, done_cb=self.done_cb, highlight=highlight)
        self.importer.start()

    def cancel(self):
        self.importer.cancel()


class CameraController(PhotoController):

    def __init__(self, app, downloader, uploader):
        super(CameraController, self).__init__(app, uploader)
        self.downloader = downloader
        self.waiting_devices = {}
        self.handled_devices = set()
        self.on_disconnect = None
        self.on_cancel = None
        if self.app.pref_controller[OPT_PHOTO] is None:
            self._set_default_opt_photo()
        if self.app.mbox.linked and self.app.mbox.role != Roles.PERSONAL:
            TRACE('Disabling camera uploads for business account %r!', self.app.config.get('email'))
            return
        self.photo_pref_startup()
        self.downloader.register(self)
        if platform == 'mac' and (self.app.is_update or self.app.is_freshly_linked):
            self.ignore_currently_connected_devices()
        else:
            self.refresh_devices()

    def _set_default_opt_photo(self):
        self.app.pref_controller.update({OPT_PHOTO: not self.app.mbox.is_dfb_user_without_linked_pair})

    def _add_device(self, device, **kw):
        try:
            device.establish_uid()
        except Exception:
            pass

        self.photodb.add_device(device.uid, **kw)

    @handle_exceptions
    def ignore_currently_connected_devices(self):
        devices = self.downloader.get_connected_devices()
        if not devices:
            return
        TRACE('Ignoring %r currently connected devices', len(devices))
        device_ids = [ device.id for device in devices ]
        with self.lock:
            self.handled_devices.union(device_ids)

    @handle_exceptions
    def refresh_devices(self):
        unnamed_devices = []
        for device in self.downloader.get_connected_devices():
            if device.name is None and device.model is None and self.photodb.device_setting(device.uid) in self.photodb.PROMPT:
                unnamed_devices.append(device)
            else:
                self.connected(device)

        if unnamed_devices:
            if len(unnamed_devices) == 1:
                self.connected(unnamed_devices[0])
            else:
                TRACE('Not connecting ambiguous devices %r', unnamed_devices)
        self.handle_next_device()

    def set_current_device(self, device):
        assert self.lock.locked()
        if device:
            if self.importer:
                assert device == self.importer.device
                self.importer.device = device
            else:
                self.importer = PhotoImporter(device, self.uploader, self.app)
        else:
            if self.importer:
                self.importer = None
            self.on_disconnect = None
            self.on_cancel = None

    def get_current_device(self):
        assert self.lock.locked()
        if self.importer:
            return self.importer.device

    current_device = property(get_current_device, set_current_device)

    @handle_exceptions
    def connecting(self, device):
        TRACE('Camera connecting %r', device)
        device.ready = False
        with self.lock:
            if device.id in self.waiting_devices or self.photodb.device_disabled(device.uid):
                return
            if self.current_device == device:
                if not self.current_device.ready:
                    self.current_device = device
                return
            if device.id in self.handled_devices:
                return
            self.waiting_devices[device.id] = device
        self.handle_next_device()

    @handle_exceptions
    def connected(self, device):
        TRACE('Camera connected %r', device)
        device.ready = True
        with self.lock:
            if self.photodb.device_disabled(device.uid) and not device.override_disabled():
                return
            if self.current_device == device:
                if not self.current_device.ready:
                    self.current_device = device
                    self.importer.device_ready()
                return
            if device.id in self.handled_devices:
                return
            self.waiting_devices[device.id] = device
        self.handle_next_device()

    @handle_exceptions
    def disconnected(self, device):
        TRACE('Camera disconnected %r', device)
        handle_next = True
        with self.lock:
            if self.current_device == device:
                if self.on_disconnect:
                    handle_next = self.on_disconnect()
                if handle_next:
                    self.current_device = None
            try:
                del self.waiting_devices[device.id]
            except KeyError:
                pass

            try:
                self.handled_devices.remove(device.id)
            except KeyError:
                pass

        if handle_next:
            self.handle_next_device()

    def handle_next_device(self):
        with self.lock:
            if not arch.photouploader.should_handle_devices(self.app.pref_controller[OPT_PHOTO]):
                return
            if self.current_device or not self.waiting_devices:
                return
            device = self.waiting_devices.popitem()[1]
            self.current_device = device
            self.on_disconnect = None
            self.on_cancel = None
            if device:
                self.handled_devices.add(device.id)
        if device:
            setting = self.photodb.device_setting(device.uid)
            self.import_id = uuid.uuid4().hex
            self.report_step('handling', device, setting=setting)
            if setting == self.photodb.SILENT:
                TRACE('Camera splash: skipping splash screen for device %r', device)
                self.handle_start(device, always=True)
            elif setting in self.photodb.PROMPT or setting == self.photodb.DISABLED and device.override_disabled():
                never_ever = self.photodb.get_config(FIRST_USE)
                saved_old_action = self.photodb.get_config(OLD_PHOTO_ACTION)
                old_action = self.downloader.get_action(saved_old_action)
                if old_action is not None:
                    self.photodb.set_config(OLD_PHOTO_ACTION, old_action)
                    self.set_dropbox_as_default_action()
                    never_ever = True
                self.on_disconnect = self.on_cancel = None
                TRACE('Camera splash: showing splash screen for device %r', device)
                ask_user_cb = self.ui.ask_user(device, self.handle_start, self.handle_cancel, self.handle_never, self.photodb.get_config(OLD_PHOTO_ACTION), setting == self.photodb.PROMPT_ALWAYS, never_ever=never_ever)
                if ask_user_cb:

                    def on_disconnect(*n, **kw):
                        ret = ask_user_cb(*n, **kw)
                        TRACE('Camera splash: user closed splash or disconnected device %r', device)
                        self.report_step('cancel', device, splash=True)
                        return ret

                    self.on_disconnect = self.on_cancel = on_disconnect
            else:
                with self.lock:
                    self.current_device = None
                self.handle_next_device()

    @handle_exceptions
    def handle_cancel(self, device):
        TRACE('Camera splash: user not importing from %r', device)
        self.report_step('cancel', device)
        device.release()
        with self.lock:
            if device == self.current_device:
                self.current_device = None
        self.handle_next_device()

    @handle_exceptions
    def handle_never(self, device):
        TRACE('Camera splash: user chose never for %r', device)
        self.report_step('never', device)
        old_action = self.photodb.get_config(OLD_PHOTO_ACTION)
        device_arg = device
        if self.photodb.get_config(FIRST_USE) and old_action is not None:
            TRACE('Camera splash: first use!  Disabling photouploader, reverting all defaults to the old_action: %r', old_action)
            self.photodb.del_config(FIRST_USE)
            device_arg = None
        if old_action is not None:
            self.downloader.handle_never(old_action, device_arg)
        if device_arg is None:
            self.app.pref_controller.update({OPT_PHOTO: False})
        else:
            self._add_device(device, setting=self.photodb.DISABLED)
            assert self.photodb.device_disabled(device.uid) or device.uid is None
        device.release()
        with self.lock:
            if device == self.current_device:
                self.current_device = None
        self.handle_next_device()

    @handle_exceptions
    def done(self, always, device, error, failed_files, transferred_files):
        if not (error or failed_files) or transferred_files:
            if always:
                try:
                    device.make_default()
                except Exception:
                    unhandled_exc_handler()

                self._add_device(device, setting=self.photodb.SILENT)
        with self.lock:
            if device == self.current_device:
                self.current_device = None
        self.handle_next_device()

    @handle_exceptions
    def handle_start(self, device, always = False):
        checkbox = 'always checkbox is %schecked' % ('' if always else 'un')
        TRACE('Camera splash: starting import (%s) from %r', checkbox, device)
        self.photodb.del_config(FIRST_USE)
        with self.lock:
            importer = self.importer if device == self.current_device else None
        if not importer:
            self.handle_next_device()
            return
        if not always:
            self._add_device(device, setting=self.photodb.PROMPT_NO_ALWAYS)
        elif not self.photodb.device_exists(device.uid):
            self._add_device(device, setting=self.photodb.PROMPT_ALWAYS)
        elif self.photodb.device_setting(device.uid) == self.photodb.PROMPT_NO_ALWAYS:
            self._add_device(device, setting=self.photodb.PROMPT_ALWAYS)
        self.hook_up_ui(device, importer, done_cb=functools.partial(self.done, always), never_cb=self.handle_never, old_action=self.photodb.get_config(OLD_PHOTO_ACTION))
        importer.start()

    def cancel_current_import(self):
        handle_next = True
        with self.lock:
            if self.on_cancel:
                handle_next = self.on_cancel()
            if handle_next:
                self.current_device = None
        if handle_next:
            self.handle_next_device()

    def photo_pref_startup(self):
        if self.app.pref_controller[OPT_PHOTO]:
            old_saved_action = self.photodb.get_config(OLD_PHOTO_ACTION)
            old_action = self.downloader.get_action(old_saved_action)
            if old_action is None:
                defaults_overwritten, new_defaults_set = self.downloader.check_for_new_devices(self.photodb.get_config(DEVICE_DEFAULTS_SET, default=[]))
                if new_defaults_set:
                    self.photodb.update_device_defaults_set(new_defaults_set)
                if defaults_overwritten:
                    old_saved_action.update(defaults_overwritten)
                    self.photodb.set_config(OLD_PHOTO_ACTION, old_saved_action)
            else:
                self.photodb.set_config(OLD_PHOTO_ACTION, old_action)
                self.set_dropbox_as_default_action()
        self.app.pref_controller.add_pref_callback(OPT_PHOTO, self.photo_pref_update)
        self.app.add_quit_handler(self.photo_pref_quit)

    @handle_exceptions
    def photo_pref_update(self, pref_controller):
        if pref_controller[OPT_PHOTO]:
            self.downloader.listen()
            self.set_dropbox_as_default_action()
            self.handled_devices.clear()
            self.refresh_devices()
        else:
            old_action = self.photodb.get_config(OLD_PHOTO_ACTION)
            if old_action is not None:
                self.photodb.set_config(OLD_PHOTO_ACTION, None)
                self.downloader.set_action(old_action)
            self.cancel_current_import()
            self.photodb.clear_device_settings()
            self.downloader.unregister()
        self.photodb.del_config(FIRST_USE)

    def photo_pref_quit(self, *n, **kw):
        old_action = self.photodb.get_config(OLD_PHOTO_ACTION)
        self.downloader.app_quit(old_action)

    def set_dropbox_as_default_action(self):
        defaults_set = self.downloader.set_action(None)
        if defaults_set:
            self.photodb.update_device_defaults_set(defaults_set)
