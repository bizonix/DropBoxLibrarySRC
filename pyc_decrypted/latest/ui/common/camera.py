#Embedded file name: ui/common/camera.py
import functools
import os.path
import time
import weakref
import arch
from ui.common.constants import SECONDS_PER_DAY, SECONDS_PER_HOUR
from .strings import UIStrings
from .tray import TrayOptionStrings, PHOTO_STATE_SHOW_NOTHING, PHOTO_STATE_SHOW_LAST_IMPORT, PHOTO_STATE_SHOW_UPLOADS_FOLDER, PHOTO_STATE_SHOW_PROGRESS, PHOTO_STATE_SHOW_PROGRESS_BUSY
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.callbacks import Observable
from dropbox.camera import PhotoImportCanceled, PhotoImportDisconnected, PhotoImportDeviceLocked, PhotoImportLowDropboxSpace, PhotoImportSelectiveSync, PhotoImportAlbumCreationError, PhotoImportNoConnectionError, IMPORT_SUCCESS, IMPORT_UNKNOWN_ERROR, IMPORT_LOW_DROPBOX_SPACE, IMPORT_LOW_DISK_SPACE
from dropbox.camera.filetypes import IMAGE_EXTENSIONS, PHOTO_EXTENSIONS, VIDEO_EXTENSIONS
from dropbox.dbexceptions import LowDiskSpaceError
from dropbox.gui import TimedThrottler
from dropbox.i18n import ungettext, format_bytes, format_number, trans
from dropbox.path import ServerPath
from dropbox.preferences import OPT_PHOTO
from dropbox.bubble import BubbleKind, Bubble
PHOTO_EXTENSIONS = PHOTO_EXTENSIONS.union(IMAGE_EXTENSIONS)

class CameraStrings(UIStrings):
    _strings = dict(splash_title=u'Dropbox Camera Upload', splash_heading=u'Add your photos to Dropbox', splash_subheading=u'View and share your photos and videos from your computer or smartphone. Earn up to 3 GB extra space.', splash_always_import=u'Automatically import photos when <b>%(name)s</b> is connected', splash_always_import_no_name=u'Automatically import photos when this device is connected', splash_always_import_disabled=u'Your device is read-only. Make it writable to enable.', splash_always_import_removable=u'Automatically import photos when removable devices are connected', splash_start_button=u'Start Import', splash_cancel_button=u'Cancel', splash_use_button=u'Always use %(application)s', splash_never_button=u'Never for This Device', splash_never_ever_button=u"Don't Ask Again", finding_title=u'Finding photos and videos', importing_title=u'Importing photos and videos', imported_title=u'Import complete', nothing_new_title=u"Dropbox didn't find any new photos or videos", device_disconnected_title=u'%(device_name)s disconnected', device_disconnected_title_no_device=u'Device disconnected', import_canceled_title=u'Import canceled', not_internet_connected_error=u'Dropbox is unable to connect to the Internet. Please check your network connection.', not_internet_connected_error_title=u'No Internet connection', album_creation_error=u'Dropbox encountered an error while creating your albums.', album_creation_error_title=u'Album creation error', locked_device_error_title=u'Device is locked', locked_device_error=u"Dropbox couldn't import photos because %(device_name)s may be locked. Unlock it and try again.", unknown_time_left=u'This could take a while...', imported_partial=u'%(num_imported)s of %(total)s photos were imported to Dropbox.', imported_partial_none=u'No photos have been imported yet.', out_of_space_title=u'Out of disk space!', out_of_space=u'Your computer is out of disk space.', out_of_space_dialog=u"Your hard drive doesn't have enough space to import %(total)s photos and videos from %(device_name)s.", out_of_space_dialog_none=u"Your hard drive doesn't have enough space.", out_of_db_space_title=u'Out of Dropbox space', out_of_db_space=u'Importing these photos would fill up all your Dropbox space.', sel_sync_error_title=u"Dropbox can't upload", sel_sync_error=u"Dropbox can't upload because the Camera Uploads folder isn't synced to this computer.", sel_sync_error_2=u'Click to fix.', import_error_title=u'Camera upload error', import_error=u'Failed to import %(num_failed)s of %(total)s photos.', import_error_none=u"Dropbox couldn't import any photos.", import_error_dialog_caption=u"%(num_failed)s photos or videos from %(device_name)s couldn't be imported.", import_error_dialog_message=u'%(num_imported)s photos and videos were imported.', import_error_dialog_none=u"Some photos or videos couldn't be imported.", progress_title=u'Dropbox Camera Upload', progress_finding_no_photos=u'Finding photos and videos to import...', progress_finding=u'Finding photos and videos to import... (%(num_found)s found)', progress_importing=u'Importing photos and videos...', sel_sync_question=u'Do you want to sync Camera Uploads to this computer?', sel_sync_message=u'Dropbox Camera Upload requires that the Camera Uploads folder is synced to this computer.', sel_sync_enable=u'Sync Camera Uploads Folder', sel_sync_disable=u'Disable Camera Upload', sel_sync_cancel=u'Cancel', sel_sync_no=u'No', quota_more_space_button=u'Get More Space', quota_stop_import_button=u'Stop Import', quota_heading=u'Not Enough Dropbox Space', quota_subheading=u"There isn't enough space in your Dropbox to import %(import_size)s of photos and videos from %(device_name)s.", quota_subheading_nosize=u"There isn't enough space in your Dropbox to import photos and videos from %(device_name)s.", quota_subheading_nodevice=u"There isn't enough space in your Dropbox to import %(import_size)s of photos and videos from this device.", quota_subheading_nosizenodevice=u"There isn't enough space in your Dropbox to import photos and videos from this device.", quota_files_imported=u'Imported %(files_imported)s of %(files_total)s', gallery_import_title=u'Import Your Photos to Dropbox', gallery_import_start_button=u'Import Photos to Dropbox', gallery_import_dialog_caption=u'Are you sure you wish to copy photos from iPhoto to your Dropbox for Business account?', gallery_import_later_button=u'Do This Later', gallery_import_never_button=u'Never', gallery_import_heading=u'Keep your photos safe with Dropbox', gallery_import_subheading=u'Copy %(photos_and_albums)s from <b>iPhoto</b> to Dropbox.\nDropbox will create a new folder for each of your <b>%(num_events)s events</b>.', gallery_import_subheading_one_event=u'Copy %(photos_and_albums)s from <b>iPhoto</b> to Dropbox.', gallery_import_subheading_no_photos=u'Copy photos from <b>iPhoto</b> to Dropbox.', gallery_import_quota_notice=u"We'll give you up to 3 GB of free space to store all your photos!")
    _platform_overrides = dict(win=dict(sel_sync_enable=u'Sync Camera Uploads folder', splash_start_button=u'Start import', splash_never_button=u'Never for this device', splash_never_ever_button=u"Don't ask again", quota_more_space_button=u'Get more space', quota_stop_import_button=u'Stop import', gallery_import_subheading=u"Move your Pictures library to your Dropbox.\nThey'll be safe and available no matter where you are."))


def imported_message(transferred, device_name):
    num = len(transferred)
    has_photos, has_videos = has_photos_and_videos(transferred)
    if device_name:
        if has_photos and has_videos:
            msg = ungettext(u'Imported %(num)s new photo from %(device_name)s.', u'Imported all %(num)s new photos and videos from %(device_name)s.', num)
        elif has_videos:
            msg = ungettext(u'Imported %(num)s new video from %(device_name)s.', u'Imported all %(num)s new videos from %(device_name)s.', num)
        else:
            msg = ungettext(u'Imported %(num)s new photo from %(device_name)s.', u'Imported all %(num)s new photos from %(device_name)s.', num)
    elif has_photos and has_videos:
        msg = ungettext(u'Imported %(num)s new photo.', u'Imported all %(num)s new photos and videos.', num)
    elif has_videos:
        msg = ungettext(u'Imported %(num)s new video.', u'Imported all %(num)s new videos.', num)
    else:
        msg = ungettext(u'Imported %(num)s new photo.', u'Imported all %(num)s new photos.', num)
    return msg % {'device_name': device_name,
     'num': format_number(num, frac_precision=0)}


def nothing_new_message(skipped, device_name):
    num = len(skipped)
    has_photos, has_videos = has_photos_and_videos(skipped)
    if device_name:
        if not num:
            msg = trans(u"Dropbox couldn't find any photos or videos on %(device_name)s.")
        elif has_photos and has_videos:
            msg = ungettext(u'The photo from %(device_name)s has already been imported.', u'All %(num)s photos and videos from %(device_name)s have already been imported.', num)
        elif has_videos:
            msg = ungettext(u'The video from %(device_name)s has already been imported.', u'All %(num)s videos from %(device_name)s have already been imported.', num)
        else:
            msg = ungettext(u'The photo from %(device_name)s has already been imported.', u'All %(num)s photos from %(device_name)s have already been imported.', num)
    elif not num:
        msg = trans(u"Dropbox couldn't find any photos or videos on this device.")
    elif has_photos and has_videos:
        msg = ungettext(u'The photo from this device has already been imported.', u'All %(num)s photos and videos from this device have already been imported.', num)
    elif has_videos:
        msg = ungettext(u'The video from this device has already been imported.', u'All %(num)s videos from this device have already been imported.', num)
    else:
        msg = ungettext(u'The photo from this device has already been imported.', u'All %(num)s photos from this device have already been imported.', num)
    return msg % {'device_name': device_name,
     'num': format_number(num, frac_precision=0)}


def partial_import_message(transferred, failed):
    num = len(transferred)
    total = len(transferred) + len(failed)
    photos, videos = has_photos_and_videos(transferred + failed)
    if photos and videos:
        msg = ungettext(u'Imported %(num)s of %(total)s photo.', u'Imported %(num)s of %(total)s photos and videos.', total)
    elif videos:
        msg = ungettext(u'Imported %(num)s of %(total)s video.', u'Imported %(num)s of %(total)s videos.', total)
    else:
        msg = ungettext(u'Imported %(num)s of %(total)s photo.', u'Imported %(num)s of %(total)s photos.', total)
    return msg % dict(num=format_number(num, frac_precision=0), total=format_number(total, frac_precision=0))


def remaining_message(remaining):
    if remaining is None:
        return CameraStrings.unknown_time_left
    if remaining < 1:
        remaining = 1
    if remaining < 60:
        nremaining = int(remaining)
        msg = ungettext(u'About %s second left...', u'About %s seconds left...', nremaining)
    elif remaining < SECONDS_PER_HOUR:
        nremaining = int(remaining / 60)
        msg = ungettext(u'About %s minute left...', u'About %s minutes left...', nremaining)
    elif remaining < SECONDS_PER_DAY * 2:
        nremaining = int(remaining / SECONDS_PER_HOUR)
        msg = ungettext(u'About %s hour left...', u'About %s hours left...', nremaining)
    elif remaining < SECONDS_PER_DAY * 100:
        nremaining = int(remaining / SECONDS_PER_DAY)
        msg = ungettext(u'About %s day left...', u'About %s days left...', nremaining)
    else:
        return CameraStrings.unknown_time_left
    return msg % format_number(nremaining, frac_precision=0)


def photos_and_albums_message(num_photos, num_albums):
    photos_msg = ungettext(u'%(num_photos)s photo', u'%(num_photos)s photos', num_photos) % dict(num_photos=format_number(num_photos, frac_precision=0))
    if num_albums:
        albums_msg = ungettext(u'%(num_albums)s album', u'%(num_photos)s albums', num_albums) % dict(num_albums=format_number(num_albums, frac_precision=0))
    msg = '<b>%s</b>' % photos_msg
    if num_albums:
        msg += ' and <b>%s</b>' % albums_msg
    return msg


class Dummy(object):
    pass


def has_photos_and_videos(paths):
    imported_exts = set((os.path.splitext(unicode(name))[1].lower() for name in paths))
    has_photos = bool(imported_exts.intersection(PHOTO_EXTENSIONS))
    has_videos = bool(imported_exts.intersection(VIDEO_EXTENSIONS))
    return (has_photos, has_videos)


def rect_to_centered_square(width, height):
    side = min(width, height)
    return ((width - side) / 2,
     (height - side) / 2,
     (width + side) / 2,
     (height + side) / 2)


class CameraUI(object):
    FINDING_DELAY = 2
    FINDING_MIN = 8
    FINDING_REPEAT = 180
    IMPORTING_DELAY = 8
    IMPORTING_MIN = 8
    IMPORTING_REPEAT = 180
    FILE_COUNT_WAIT_TIME = 1
    REMAINING_TIME_REPEAT = 5
    NONE, FINDING, IMPORTING, DONE = range(4)
    STATE2STR = {NONE: 'none',
     FINDING: 'finding',
     IMPORTING: 'importing',
     DONE: 'done'}

    def __init__(self, **kw):
        self.app = kw['app']
        self.state = self.NONE
        self.start_time = None
        self.remaining_time = None
        self.import_id = None
        self.bubble_context = kw['bubble_context']
        self.ref = self.bubble_context.make_func_context_ref
        self.last_bubble_time = 0
        self.last_bubble_state = self.NONE
        self.bubble_click_ctx = None
        self.bubble_click_cbs = weakref.WeakKeyDictionary()
        self.showing_bubbles = True
        self._on_cancel = None
        self.message = Observable('', handle_exc=unhandled_exc_handler)
        self.last_photo = Observable(None, handle_exc=unhandled_exc_handler)
        self.cur_bytes = Observable(0, handle_exc=unhandled_exc_handler)
        self.total_bytes = Observable(0, handle_exc=unhandled_exc_handler)
        self.found_files = Observable(0, handle_exc=unhandled_exc_handler)
        self._file_count_updater = TimedThrottler(self.update_found_files, frequency=self.FILE_COUNT_WAIT_TIME)
        self.show_progress_by_default = kw.get('show_progress_by_default', False)
        self.use_busy_icon = kw.get('use_busy_icon', False)
        self.tray_controller = kw['tray_controller']
        self.tray_controller.add_callbacks_for_options({TrayOptionStrings.view_photo_import_progress: self.on_tray_photo_import_progress,
         TrayOptionStrings.view_last_photo_import: self.on_tray_view_import,
         TrayOptionStrings.view_camera_uploads_folder: self.on_tray_view_import})
        self.last_import = (None, None)
        self.update_tray_menu()

    def set_on_cancel(self, on_cancel):
        self._on_cancel = on_cancel

    def on_cancel(self):
        self.progress_window_hide()
        if callable(self._on_cancel):
            self._on_cancel()

    def _bubble(self, state, message, caption, bubble_kind):
        ctx_ref = self.ref(self.on_bubble, self.bubble_click_ctx)
        self.app.ui_kit.show_bubble(Bubble(bubble_kind, message, caption, self.bubble_context, ctx_ref))
        self.last_bubble_time = time.time()
        self.last_bubble_state = state
        self.report_step('bubble', state=self.STATE2STR.get(state, 'Unknown'))

    def bubble(self, message = None, caption = None, bubble_kind = None):
        state = self.state
        if state == self.IMPORTING:
            if self.showing_bubbles and (self.remaining_time is None or self.remaining_time > self.IMPORTING_MIN):
                delay = self.IMPORTING_DELAY if self.last_bubble_state == self.FINDING else self.IMPORTING_REPEAT
                if time.time() > self.last_bubble_time + delay:
                    self._bubble(self.IMPORTING, remaining_message(self.remaining_time), CameraStrings.importing_title, BubbleKind.CAMERA_IMPORT_TIME_REMAINING)
        elif state == self.FINDING:
            if self.showing_bubbles and (self.remaining_time is None or self.remaining_time > self.FINDING_MIN) and time.time() > self.last_bubble_time + self.FINDING_REPEAT:
                self._bubble(self.FINDING, remaining_message(self.remaining_time), CameraStrings.finding_title, BubbleKind.CAMERA_FIND_TIME_REMAINING)
        elif state == self.DONE:
            assert message
            assert caption
            self._bubble(self.DONE, message, caption, bubble_kind)
        else:
            TRACE('!! bubble called with a state of %r', state)

    def on_bubble(self, ctx):
        try:
            self.bubble_click_cbs[ctx]()
        except KeyError:
            pass
        except Exception:
            unhandled_exc_handler()

    def progress_window_show(self):
        raise NotImplementedError

    def progress_window_hide(self):
        raise NotImplementedError

    def ask_user(self, device, start_cb, cancel_cb, never_cb, old_action, always_state, never_ever):
        if callable(start_cb):
            start_cb(device)

    def report_step(self, step, **event):
        event['step'] = step
        event['import_id'] = self.import_id
        self.app.event.report('photo-import', event)

    def starting(self, import_id):
        assert self.state == self.NONE
        self.state = self.FINDING
        self.start_time = time.time()
        self.remaining_time = None
        self.last_remaining_message_and_time = None
        self.import_id = import_id

        def progress_window_show():
            self.report_step('show-progress')
            self.progress_window_show()

        self.bubble_click_ctx = Dummy()
        self.bubble_click_cbs[self.bubble_click_ctx] = progress_window_show
        self.last_bubble_time = 0
        self.last_bubble_state = self.NONE
        self.showing_bubbles = True
        self.call_later(self.FINDING_DELAY, self._starting_delay_cb)
        self.message.set(CameraStrings.progress_finding_no_photos)
        self.last_photo.set(None)
        self.total_bytes.set(0)
        self.cur_bytes.set(0)
        self.found_files.set(0)
        self.update_tray_menu()
        if self.show_progress_by_default:
            self.progress_window_show()

    def _starting_delay_cb(self, *args, **kwargs):
        try:
            if self.state == self.FINDING:
                self.bubble()
                self.call_later(self.FINDING_DELAY, self._starting_delay_cb)
        except Exception:
            unhandled_exc_handler()

    def finding(self, total_bytes):
        self.message.set(CameraStrings.progress_finding % dict(num_found=0))
        self.total_bytes.set(total_bytes)
        self.start_time = time.time()

    def update_found_files(self, num_found):
        self.message.set(CameraStrings.progress_finding % dict(num_found=format_number(num_found, frac_precision=0)))

    def file_count(self, num_found):
        self._file_count_updater(num_found)
        self.found_files.set(num_found)

    def progress(self, cur_bytes):
        if cur_bytes:
            self.remaining_time = self.get_remaining_time(cur_bytes)
            self.cur_bytes.set(cur_bytes)
            self.bubble()

    def importing(self):
        assert self.state in (self.FINDING, self.IMPORTING)
        self.state = self.IMPORTING
        self.message.set(CameraStrings.progress_importing)
        self.cur_bytes.set(0)

    def file_imported(self, details):
        self.last_photo.set(details.path)
        self.bubble()

    def done(self, device, last_result, transferred, skipped, failed, error, never_cb, old_action, highlight = True):
        assert self.state in (self.FINDING, self.IMPORTING)
        self.state = self.DONE
        self.progress_window_hide()
        if transferred:
            can_select_paths = highlight and self._can_select_paths(transferred)
            names = transferred if can_select_paths else None

            def show_files(report = True):
                try:
                    if names is None:
                        folder = os.path.commonprefix((os.path.dirname(unicode(transferred[0])), os.path.dirname(unicode(transferred[-1]))))
                        arch.util.launch_folder(folder, cleanup=True)
                    else:
                        arch.util.highlight_files(unicode(names[0].dirname), [ unicode(name) for name in names ], cleanup=True)
                except Exception:
                    unhandled_exc_handler()
                finally:
                    if report:
                        self.report_step('show-files')

            self.last_import = (show_files, PHOTO_STATE_SHOW_LAST_IMPORT if can_select_paths else PHOTO_STATE_SHOW_UPLOADS_FOLDER)
            self.bubble_click_cbs[self.bubble_click_ctx] = show_files
        else:
            self.bubble_click_cbs[self.bubble_click_ctx] = lambda : None
        self.update_tray_menu()
        self.last_photo.set(None)
        self.message.set(u'')
        self.cur_bytes.set(self.total_bytes.get())
        import_result, dialog_showing = self._display_import_results(device, last_result, transferred, skipped, failed, error, never_cb, old_action)
        if transferred and not dialog_showing:
            show_files(report=False)
        self.update_tray_menu()
        self.bubble_click_ctx = None
        self.start_time = None
        self.update_tray_menu()
        self.state = self.NONE
        return import_result

    def _display_import_results(self, device, last_result, transferred, skipped, failed, error, never_cb, old_action):
        device_name = device.name or device.model
        num_imported = len(transferred)
        total = len(transferred) + len(failed)
        fmt_dict = dict(total=format_number(total, frac_precision=0), num_imported=format_number(num_imported, frac_precision=0), num_failed=format_number(len(failed), frac_precision=0), device_name=device_name) if total else None
        dialog = False
        import_result = IMPORT_SUCCESS

        def is_error(err_kls):
            return isinstance(error, err_kls)

        def fmt(msg, msg_none):
            if fmt_dict:
                return msg % fmt_dict
            return msg_none

        if error is None and not failed:
            if num_imported:
                title = CameraStrings.imported_title
                msg = imported_message(transferred, device_name)
                bubble_kind = BubbleKind.CAMERA_IMPORT_SUCCEEDED
            else:
                title = CameraStrings.nothing_new_title
                msg = nothing_new_message(skipped, device_name)
                bubble_kind = BubbleKind.CAMERA_IMPORT_NO_NEW_MEDIA
            self.bubble(msg, title, bubble_kind)
        elif is_error(PhotoImportDisconnected):
            self.bubble(partial_import_message(transferred, failed), (CameraStrings.device_disconnected_title if device_name else CameraStrings.device_disconnected_title_no_device) % dict(device_name=device_name), BubbleKind.CAMERA_IMPORT_DISCONNECTED)
        elif is_error(PhotoImportCanceled):
            self.bubble(partial_import_message(transferred, failed), CameraStrings.import_canceled_title, BubbleKind.CAMERA_IMPORT_CANCELLED)
        elif is_error(PhotoImportDeviceLocked):
            self.bubble(CameraStrings.locked_device_error % dict(device_name=device_name), CameraStrings.locked_device_error_title, BubbleKind.CAMERA_IMPORT_DEVICE_LOCKED)
        elif is_error(PhotoImportAlbumCreationError):
            (self.bubble(CameraStrings.album_creation_error, CameraStrings.album_creation_error_title, BubbleKind.CAMERA_IMPORT_ALBUM_CREATION_ERROR),)
        elif is_error(PhotoImportNoConnectionError):
            self.bubble(CameraStrings.not_internet_connected_error, CameraStrings.not_internet_connected_error_title, BubbleKind.CAMERA_IMPORT_NOT_INTERNET_CONNECTED)
        elif is_error(PhotoImportSelectiveSync):
            ctx = self.bubble_click_ctx
            server_path = error.server_path

            def launch_sel_sync_fix():
                self.report_step('show-fix-selsync')

                def on_cancel():
                    self.report_step('fix-selsync-cancel')

                def on_enable():
                    self.report_step('fix-selsync-enable')
                    remove_set = set([server_path.lower()])
                    ignore_set = set((ServerPath(s).lower() for s in self.app.sync_engine.get_directory_ignore_set()))
                    candidate_set = ignore_set - remove_set
                    self.app.sync_engine.change_directory_ignore_set([ unicode(a) for a in candidate_set ])
                    self.bubble_click_cbs[ctx] = lambda : None

                def on_disable():
                    self.report_step('fix-selsync-disable')
                    self.app.pref_controller.update({OPT_PHOTO: False})
                    self.bubble_click_cbs[ctx] = lambda : None

                self.prompt_sel_sync(on_enable, on_disable, on_cancel)

            self.bubble_click_cbs[self.bubble_click_ctx] = launch_sel_sync_fix
            self.bubble(CameraStrings.sel_sync_error + '\n\n' + CameraStrings.sel_sync_error_2, CameraStrings.sel_sync_error_title, BubbleKind.CAMERA_IMPORT_SELECTIVE_SYNC_ERROR)
        elif is_error(LowDiskSpaceError):
            if last_result == IMPORT_LOW_DISK_SPACE:
                self.bubble('%s %s' % (CameraStrings.out_of_space, fmt(CameraStrings.imported_partial, CameraStrings.imported_partial_none)), CameraStrings.out_of_space_title, BubbleKind.CAMERA_IMPORT_LOW_DISK_SPACE)
            else:
                dialog = True
                self.error_dialog(fmt(CameraStrings.out_of_space_dialog, CameraStrings.out_of_space_dialog_none))
            import_result = IMPORT_LOW_DISK_SPACE
        elif is_error(PhotoImportLowDropboxSpace):

            def launch_plans_page():
                self.report_step('show-plans')
                self.app.desktop_login.login_and_redirect('c/getspace')

            if last_result == IMPORT_LOW_DROPBOX_SPACE:
                self.bubble_click_cbs[self.bubble_click_ctx] = launch_plans_page
                self.bubble('%s %s' % (CameraStrings.out_of_db_space, fmt(CameraStrings.import_error, CameraStrings.import_error_none)), CameraStrings.out_of_db_space_title, BubbleKind.CAMERA_IMPORT_LOW_DROPBOX_SPACE)
            else:
                self.out_of_space(device, device_name, len(transferred), total, never_cb, old_action, launch_plans_page)
            import_result = IMPORT_LOW_DROPBOX_SPACE
        else:
            if last_result == IMPORT_UNKNOWN_ERROR:
                self.bubble(fmt(CameraStrings.import_error, CameraStrings.import_error_none), CameraStrings.import_error_title, BubbleKind.CAMERA_IMPORT_UNKNOWN_ERROR)
            else:
                dialog = True
                if fmt_dict:
                    self.error_dialog(CameraStrings.import_error_dialog_caption % fmt_dict, CameraStrings.import_error_dialog_message % fmt_dict)
                else:
                    self.error_dialog(CameraStrings.import_error_dialog_none)
            import_result = IMPORT_UNKNOWN_ERROR
        return (import_result, dialog)

    def generate_never_text(self, never_ever, old_action):
        if never_ever and old_action:
            app = os.path.splitext(os.path.basename(old_action))[0]
            never_text = CameraStrings.splash_use_button % dict(application=app)
        else:
            never_text = CameraStrings.splash_never_button
        return never_text

    def out_of_space(self, device, device_name, num_transferred, num_total, never_cb, old_action, upgrade_cb):
        if old_action:
            never_text = self.generate_never_text(never_ever=False, old_action=old_action)
            never_cb = functools.partial(never_cb, device)
        else:
            never_text = None
            never_cb = None
        import_size = self.total_bytes.get()
        if import_size:
            import_size = format_bytes(import_size)
            quota_message = (CameraStrings.quota_subheading if device_name else CameraStrings.quota_subheading_nodevice) % dict(import_size=import_size, device_name=device_name)
        else:
            quota_message = (CameraStrings.quota_subheading_nosize if device_name else CameraStrings.quota_subheading_nosizenodevice) % dict(device_name=device_name)
        if num_transferred > 0:
            files_imported_label = CameraStrings.quota_files_imported % dict(files_imported=format_number(num_transferred, frac_precision=0), files_total=format_number(num_total, frac_precision=0))
            never_text = None
            never_cb = None
            cancel_text = CameraStrings.quota_stop_import_button
        else:
            files_imported_label = None
            cancel_text = CameraStrings.splash_cancel_button
        self.out_of_space_show(upgrade_cb, lambda : None, cancel_text, never_cb, never_text, quota_message, files_imported_label)

    def out_of_space_show(self, *args, **kwargs):
        raise NotImplementedError

    def _can_select_paths(self, paths):
        return True

    def get_remaining_time(self, cur_bytes):
        return (time.time() - self.start_time) * (self.total_bytes.get() - cur_bytes) / cur_bytes

    def get_remaining_message(self):
        if self.last_remaining_message_and_time and self.last_remaining_message_and_time[0] and self.last_remaining_message_and_time[1] > time.time():
            return self.last_remaining_message_and_time[0]
        remaining_str = remaining_message(self.remaining_time) if self.remaining_time is not None else u''
        self.last_remaining_message_and_time = (remaining_str, time.time() + self.REMAINING_TIME_REPEAT)
        return remaining_str

    def update_tray_menu(self):
        if self.bubble_click_ctx:
            if self.use_busy_icon:
                new_state = PHOTO_STATE_SHOW_PROGRESS_BUSY
            else:
                new_state = PHOTO_STATE_SHOW_PROGRESS
        elif self.last_import[1]:
            new_state = self.last_import[1]
        else:
            new_state = PHOTO_STATE_SHOW_NOTHING
        self.tray_controller.change_photo_menu_state(new_state)

    def on_tray_photo_import_progress(self):
        ctx = self.bubble_click_ctx
        if ctx:
            self.on_bubble(ctx)

    def on_tray_view_import(self):
        if self.last_import[0]:
            self.last_import[0]()
