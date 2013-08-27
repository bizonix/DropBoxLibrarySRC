#Embedded file name: ui/common/xui/tray_popup.py
import json
import time
from functools import partial
from itertools import chain
import arch
from build_number import BUILD_KEY, is_frozen
from dropbox.client.background_worker import on_background_thread
from dropbox.functions import handle_exceptions
from dropbox.gui import assert_message_queue, message_sender, spawn_thread_with_name
from dropbox.i18n import get_current_code
from dropbox.path import ServerPath
from dropbox.platform import platform
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from ui.common.notifications import UserNotification, UserNotificationActionError, UserNotificationActionNotAvailableError, UserNotificationStrings
from ui.common.strings import UIStrings
from ui.common.tray import TrayController
from ui.common.xui import XUIController, XUINotReadyError

class TrayPopupStrings(UIStrings):
    _strings = dict(quit_dropbox=u'Quit %s', open_dropbox_menu=u'Open Dropbox Menu')
    _platform_overrides = dict(win=dict(quit_dropbox=u'Exit %s'))


class TrayPopupController(XUIController):
    _excluded_options = (TrayController.OPTION_OPEN_FOLDER,
     TrayController.OPTION_OPEN_WEBSITE,
     TrayController.OPTION_RECENTLY_CHANGED,
     TrayController.OPTION_OPEN_PERSONAL_FOLDER,
     TrayController.OPTION_OPEN_BUSINESS_FOLDER,
     TrayController.OPTION_PRIMARY_QUOTA)
    __xui_resource__ = 'tray_popup'
    __xui_properties__ = ('get_options', 'get_status', 'get_timeline', 'report_height', 'show_menu', 'perform_sticky_action', 'perform_notification_action', 'perform_file_action', 'download_thumbnail', 'get_multiaccount_options', 'execute_pause_unpause', 'pause_or_resume', 'multiaccount_enabled', 'change_notification_filter', 'use_japanese_font')

    def __init__(self, app):
        self._app = app
        self._options = {}
        self._state = None
        self._icon = None
        self._message = None
        self._timeline_initialized = False
        self._should_display_quota = None
        self._percent = None
        self._quota_message = None
        self.multiaccount_enabled = False
        super(TrayPopupController, self).__init__()

    def use_japanese_font(self):
        return platform == 'win' and get_current_code() == u'ja'

    @assert_message_queue
    def update_options(self, options):
        self._options = options
        try:
            self._view.refresh_options()
        except XUINotReadyError:
            TRACE("View isn't ready!")

    @assert_message_queue
    def get_options(self):
        return tuple((self._get_option_func(key) for key in (TrayController.OPTION_OPEN_FOLDER, TrayController.OPTION_OPEN_WEBSITE)))

    @assert_message_queue
    def get_multiaccount_options(self):
        return tuple((self._get_option_func(key) for key in (TrayController.OPTION_OPEN_PERSONAL_FOLDER, TrayController.OPTION_OPEN_BUSINESS_FOLDER)))

    def _get_option_func(self, key):
        label, func = self._options.get(key, (None, None))

        def inner(*args, **kwds):
            try:
                if self._app:
                    self._app.ui_kit.hide_tray_popup()
            except Exception:
                unhandled_exc_handler()

            func(*args, **kwds)

        return inner

    @property
    def recently_changed(self):
        if self.multiaccount_enabled:
            return self._app.merged_recently_changed
        else:
            return self._app.recently_changed

    @property
    def notification_controller(self):
        if self.multiaccount_enabled:
            return self._app.merged_notification_controller
        else:
            return self._app.notification_controller

    def on_show(self):
        try:
            self._view.on_show()
        except XUINotReadyError:
            TRACE("View isn't ready!")

    @assert_message_queue
    def refresh(self):
        try:
            self._timeline_initialized = True
            self._view.refresh_status()
            self._view.refresh_timeline()
        except XUINotReadyError:
            TRACE("View isn't ready!")
        except Exception:
            if is_frozen():
                raise
            unhandled_exc_handler()
            TRACE('!! Refreshing the timeline failed. This would have brought down the popup on a frozen build.')

    @assert_message_queue
    def update_status(self, state, icon, message, should_display_quota, percent, quota_message):
        self._state = state
        self._icon = icon
        self._message = message
        self._should_display_quota = should_display_quota
        self._percent = percent
        self._quota_message = quota_message
        try:
            if self._host.is_visible():
                self._view.refresh_status()
        except XUINotReadyError:
            TRACE("View isn't ready!")

    @assert_message_queue
    def get_status(self):
        return (self._state,
         self._icon,
         self._message,
         self._should_display_quota,
         self._percent,
         self._quota_message)

    @assert_message_queue
    def update_notifications(self):
        if self._timeline_initialized:
            return
        try:
            self._timeline_initialized = True
            self._view.refresh_timeline()
        except XUINotReadyError:
            TRACE("View isn't ready!")

    def get_timeline(self):
        if self.notification_controller is None:
            return
        now = self._app.server_time
        if now is None:
            now = time.time()
        if self.notification_controller:
            notifications = self.notification_controller.get_latest()
        else:
            notifications = []
        self._notifications = {entry.key:entry for entry in notifications}
        notification_dicts = [ entry.get_dict(now) for entry in notifications ]
        if self.recently_changed:
            recently_changed = self.recently_changed.get_latest()
        else:
            recently_changed = []
        self._recently_changed = {id(entry):entry for entry in recently_changed}
        recently_changed_dicts = []
        for entry in recently_changed:
            data = entry.get_dict(now)
            data['key'] = id(entry)
            recently_changed_dicts.append(data)

        self._unread = [ entry for entry in notifications if entry.status == UserNotification.STATUS_UNREAD ]
        stickies = self.notification_controller.get_stickies()
        self._stickies = {entry.key:entry for entry in stickies}
        sticky_dicts = [ entry.get_dict() for entry in stickies ]
        self.notification_controller.acknowledge(self._unread)
        return json.dumps([recently_changed_dicts, notification_dicts, sticky_dicts])

    def set_icon_offset(self, width):
        self._view.set_icon_offset(width)

    def _get_filtered_options(self):

        @handle_exceptions
        def wrapper(func):
            try:
                return func()
            finally:
                self._app.ui_kit.hide_tray_popup()

        last_valid = False
        for key, option in self._options.iteritems():
            if key in self._excluded_options:
                continue
            if option == (None, None):
                if last_valid:
                    yield option
                last_valid = False
                continue
            label, extra = option
            if callable(extra):
                yield (label, partial(wrapper, extra))
                continue
            yield (label, extra)
            last_valid = True

    def _quit(self):
        self._app.ui_kit.hide_tray_popup()

        @message_sender(spawn_thread_with_name('QUITHELPER'))
        def quitter():
            arch.util.hard_exit()

        quitter()

    def execute_pause_unpause(self, pause):
        if pause:
            self._app.tray_controller.do_pause()
        else:
            self._app.tray_controller.do_resume()

    def pause_or_resume(self):
        res = self._app.tray_controller.pause_or_resume()
        if res is None:
            return
        if res == TrayController.OPTION_PAUSE:
            return 1
        return 2

    def show_menu(self, x, y):
        assert self._host is not None, "This function should not be called when the host doesn't exist."
        self._app.event.report('gear-menu')
        self._view.hide_notification_filter()
        options = chain(self._get_filtered_options(), ((TrayPopupStrings.quit_dropbox % BUILD_KEY, self._quit),))
        self._host.show_context(options, x, y)

    def report_height(self, height):
        assert self._host is not None, "This function should not be called when the host doesn't exist."
        self._host.set_height(height)

    def perform_command(self, command):
        assert self._host is not None, "This function should not be called when the host doesn't exist."
        self._app.event.report('tray-popup-action', **{'action_id': command})
        try:
            if command == 'open':
                self._app.open_dropbox()
            elif command == 'web':
                self._app.desktop_login.login_and_redirect('home')
            else:
                raise Exception('Unknown command: %r' % (command,))
        finally:
            self._app.ui_kit.hide_tray_popup()

    def download_thumbnail(self, key):
        entry = self._recently_changed.get(int(key))
        if entry.blocklist is None:
            TRACE('!! Entry for %r has no blocklist...', entry.name)
            return

        @on_background_thread
        def do_download(callback):
            TRACE('Downloading thumbnail for entry: %r (%r).', entry.name, entry.blocklist)
            if entry.primary:
                raw_data = self._app.conn.retrieve_thumbnail(entry.name, entry.blocklist, format='jpeg')
            else:
                raw_data = self._app.mbox.recently_changed_retrieve_thumbnail(entry.name, entry.blocklist, format='jpeg')
            data = raw_data.encode('base64').replace('\n', '')
            TRACE('Downloaded thumbnail for entry: %r', entry.name)
            callback(key, 'data:image/jpeg;base64,%s' % data)

        do_download(self._view.on_thumbnail_downloaded)

    def perform_sticky_action(self, key, action):
        refresh = False
        try:
            sticky = self._stickies.get(key)
            if sticky is None:
                report_bad_assumption("Sticky notification couldn't be found by its key.")
                return
            refresh = sticky.perform_action(self._app, action)
            return refresh
        finally:
            if not refresh:
                self._app.ui_kit.hide_tray_popup()

    def perform_notification_action(self, key, action):
        assert self._host is not None, "This function should not be called when the host doesn't exist."
        notification = self._notifications.get(key)
        if notification is None:
            report_bad_assumption("Notification couldn't be found by its key.")
            return

        @message_sender(spawn_thread_with_name('USERNOTIFICATIONACTION'))
        def _wrapper():
            error_message = None
            try:
                notification.perform_action(self._app, action)
            except UserNotificationActionNotAvailableError:
                pass
            except UserNotificationActionError as e:
                error_message = e.localized_message
            except Exception:
                unhandled_exc_handler()
                error_message = UserNotificationStrings.error_generic
            else:
                self._app.ui_kit.hide_tray_popup()

            if error_message:
                self._view.on_action_complete(key, error_message)

        _wrapper()

    def perform_file_action(self, key, action):
        TRACE('Performing file action %r on %r', action, key)
        assert self._host is not None, "This function should not be called when the host doesn't exist."
        key = int(key)
        try:
            entry = self._recently_changed[key]
        except IndexError:
            report_bad_assumption('The recently changed file entry could not be found by its position.')
            return

        @message_sender(spawn_thread_with_name('FILEACTION'), handle_exceptions=True)
        def _wrapper():
            try:
                entry.perform_action(self._app, action)
            finally:
                self._app.ui_kit.hide_tray_popup()

        _wrapper()

    def enable_multiaccount(self):
        try:
            self._view.enable_multiaccount()
            self._view.refresh_timeline()
            self.multiaccount_enabled = True
        except XUINotReadyError:
            TRACE("View isn't ready!")

    def disable_multiaccount(self):
        try:
            self.multiaccount_enabled = False
            self._view.disable_multiaccount()
            self._view.refresh_options()
            self._view.refresh_timeline()
        except XUINotReadyError:
            TRACE("View isn't ready!")

    def change_notification_filter(self, new_state):
        if not self.multiaccount_enabled:
            report_bad_assumption('Notification filter changed without multiaccount!')
            return
        if new_state not in ('everything', 'personal', 'business'):
            report_bad_assumption('Bad new notification filter state: %s', new_state)
            return
        show_personal = new_state in ('everything', 'personal')
        show_business = new_state in ('everything', 'business')
        self._app.merged_recently_changed.update_merge_state(show_personal, show_business)
        self._app.merged_notification_controller.update_merge_state(show_personal, show_business)
        self._view.refresh_timeline()
