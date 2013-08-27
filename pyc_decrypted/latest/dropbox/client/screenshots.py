#Embedded file name: dropbox/client/screenshots.py
import arch
import errno
import threading
from functools import partial
from os.path import getctime
from time import strftime, localtime
from client_shmodel import ClientShmodelOrigin
from dropbox.bubble import BubbleKind, Bubble
from dropbox.client.background_worker import MessageProcessingThread
from dropbox.client.multiaccount.constants import Roles
from dropbox.fsutil import create_unique_file_name, is_exists, move, root_relative_to_local_path
from dropbox.platform import platform
from dropbox.event import report
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.gui import message_sender
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.preferences import OPT_SCREENSHOTS
from ui.common.screenshots import ScreenshotsStrings
from ui.common.preferences import PanelNames

class ScreenshotsProcessingThread(MessageProcessingThread):

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'SCREENSHOTS_PROCESSING'
        super(ScreenshotsProcessingThread, self).__init__(*args, **kwargs)


class ScreenshotsController(object):
    STATE_UNKNOWN = 1
    NEVER_SAVE = 0
    ALWAYS_SAVE = 2
    DORMANT_UNKNOWN = 3
    DORMANT_YES = 4
    SCREENSHOTS_FOLDER_CONFIG_KEY = 'screenshots_folder'
    SCREENSHOTS_FOLDER_SERVER_KEY = 'screenshots'

    @classmethod
    def is_supported(cls, app):
        if platform == 'mac':
            from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
            if MAC_VERSION >= SNOW_LEOPARD:
                return True
        if platform == 'win':
            return True
        return False

    @classmethod
    def should_listen_for_screenshots(cls, app):
        primary_enabled = app.config.get(OPT_SCREENSHOTS, ScreenshotsController.STATE_UNKNOWN) != ScreenshotsController.NEVER_SAVE
        secondary_enabled = app.mbox.enabled and app.mbox.get_config().get(OPT_SCREENSHOTS, ScreenshotsController.STATE_UNKNOWN) != ScreenshotsController.NEVER_SAVE
        return primary_enabled or secondary_enabled

    @classmethod
    def current_prefs_state(cls, app):
        if app.config.get(OPT_SCREENSHOTS, cls.STATE_UNKNOWN) in [cls.ALWAYS_SAVE, cls.STATE_UNKNOWN]:
            return (True, app.mbox.role)
        try:
            if app.mbox.enabled and app.mbox.get_config().get(OPT_SCREENSHOTS, cls.STATE_UNKNOWN) == cls.ALWAYS_SAVE:
                return (True, app.mbox.secondary_role)
        except Exception:
            TRACE('Could not fetch config from mbox.')

        return (False, Roles.BUSINESS)

    def __init__(self, app):
        self._app = app
        self._mbox = app.mbox
        assert ScreenshotsController.is_supported(self._app)
        TRACE('Screenshots supported, starting initialization')
        if OPT_SCREENSHOTS not in self._app.config:
            self._app.config[OPT_SCREENSHOTS] = self.STATE_UNKNOWN
        if self._mbox.is_secondary:
            if self._app.config[OPT_SCREENSHOTS] == self.STATE_UNKNOWN and self._mbox.get_config().get(OPT_SCREENSHOTS) == self.NEVER_SAVE:
                self._app.config[OPT_SCREENSHOTS] = self.NEVER_SAVE
            self._mbox.register_screenshots_cb()
            if platform == 'win':
                self._mbox.update_screenshot_preferences()
        else:
            app.screenshots_callbacks.set_primary(self.screenshot_handler)
            self.screenshots_provider = arch.screenshots.ScreenshotsProvider(app)
        self.file_queue = []
        self.is_dialog_open = False
        self._thread = ScreenshotsProcessingThread()
        self._thread.start()
        self.error_bubbled = False
        self.processed_set = set()
        self.last_screenshot_time = get_monotonic_time_seconds()
        self._mbox.on_secondary_link.add_handler(self.on_secondary_link)

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def on_secondary_link(self, arg):
        if not arg:
            new_state = None
            if self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.DORMANT_YES:
                new_state = self.ALWAYS_SAVE
            elif self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.DORMANT_UNKNOWN:
                new_state = self.STATE_UNKNOWN
            if new_state is not None:
                self.update_preferences(primary_state=new_state)
        self._app.ui_kit.refresh_panel(PanelNames.IMPORT)

    def should_show_dialog(self):
        if self.is_dialog_open:
            return False
        if self._mbox.is_secondary:
            return False
        TRACE('SCREENSHOTS: should_show_dialog %s' % self._app.config[OPT_SCREENSHOTS])
        if self._mbox.has_secondary:
            TRACE('SCREENSHOTS: should_show_dialog (mbox) %s' % self._mbox.config[OPT_SCREENSHOTS])
        return self._app.config[OPT_SCREENSHOTS] == self.STATE_UNKNOWN or self._mbox.has_secondary and self._mbox.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.STATE_UNKNOWN

    def get_screenshots_folder(self):
        folder = self._app.config.get(self.SCREENSHOTS_FOLDER_CONFIG_KEY, None)
        if folder:
            full_path = root_relative_to_local_path(self._app, folder)
        if not folder or not is_exists(self._app.sync_engine.fs, full_path):
            error_message = None
            try:
                TRACE("Trying to get screenshots' folder name from server")
                response = self._app.conn.get_special_folder_name(self.SCREENSHOTS_FOLDER_SERVER_KEY)
                TRACE('Response from server: %r', response)
                if response[u'ret'] == u'ok':
                    folder = response[u'folder_name']
                else:
                    error_message = ScreenshotsStrings.error_generic
            except Exception as e:
                is_transient_error = self._app.conn.is_transient_error(e)
                if is_transient_error:
                    TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                    error_message = ScreenshotsStrings.error_connection
                else:
                    unhandled_exc_handler()
                    error_message = ScreenshotsStrings.error_generic

            if error_message:
                if not self.error_bubbled:
                    TRACE('Show bubble with error message: %r', error_message)
                    bubble = Bubble(BubbleKind.SCREENSHOTS_ERROR, error_message, ScreenshotsStrings.error_caption, show_when_disabled=True)
                    if self._mbox.is_primary:
                        self._app.ui_kit.show_bubble(bubble)
                    else:
                        self._mbox.show_bubble(bubble)
                    self.error_bubbled = True
                if platform == 'win':
                    self.remove_files(self.file_queue)
                self.file_queue = []
                return
            self._app.config[self.SCREENSHOTS_FOLDER_CONFIG_KEY] = folder
        return folder

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def handle_splash_result_on_thread(self):
        self.handle_splash_result()

    def handle_splash_result(self, remove_temp_files = False):
        if self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.ALWAYS_SAVE:
            for file_path, copy_link, show_bubble in self.file_queue:
                TRACE('Screenshot file_path under processing: %r', file_path)
                self.do_move(file_path, copy_link, show_bubble)

            TRACE('Queue processing finished')
        if remove_temp_files:
            TRACE('Removing temp files')
            self.remove_files(self.file_queue)
        self.file_queue = []

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def update_from_prefs_window(self, checkbox, role):
        TRACE('Updating from preferences window (checkbox: %s, role: %s)' % (checkbox, role))
        primary_state = None
        secondary_state = None
        if not checkbox:
            primary_state = self.NEVER_SAVE
            if self._mbox.enabled:
                secondary_state = self.NEVER_SAVE
        elif not self._mbox.enabled:
            primary_state = self.ALWAYS_SAVE
        elif self._mbox.role == role:
            primary_state = self.ALWAYS_SAVE
            secondary_state = self.DORMANT_UNKNOWN
        else:
            primary_state = self.DORMANT_UNKNOWN
            secondary_state = self.ALWAYS_SAVE
        TRACE('Updating to preferences primary: %s, secondary: %s' % (primary_state, secondary_state))
        self.update_preferences(primary_state=primary_state, secondary_state=secondary_state)

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def update_preferences(self, primary_state = None, secondary_state = None):
        if primary_state is not None:
            self._app.config[OPT_SCREENSHOTS] = primary_state
        if secondary_state is not None:
            self._app.mbox.update_preferences({OPT_SCREENSHOTS: secondary_state})
        if platform == 'win':
            self.screenshots_provider.check_and_modify_listener()

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def always_cb(self, role = None):
        TRACE('User activated screenshots feature from splash screen')
        if role is not None:
            TRACE('User selected screenshots for role: %s, is_primary: %s' % ('Personal' if role == Roles.PERSONAL else 'Business', role == self._mbox.role))
            if role == self._mbox.role:
                self._app.config[OPT_SCREENSHOTS] = self.ALWAYS_SAVE
                remote_value = self.DORMANT_UNKNOWN
            else:
                new_value = self.NEVER_SAVE
                if self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.ALWAYS_SAVE:
                    new_value = self.DORMANT_YES
                elif self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.STATE_UNKNOWN:
                    new_value = self.DORMANT_UNKNOWN
                self._app.config[OPT_SCREENSHOTS] = new_value
                remote_value = self.ALWAYS_SAVE
            self._mbox.update_preferences({OPT_SCREENSHOTS: remote_value})
            self._mbox.handle_splash_result_on_thread()
            report('screenshots_choice_made', accepted=self.ALWAYS_SAVE, role=role, is_primary=role == self._mbox.role, multiaccount=True)
        else:
            self._app.config[OPT_SCREENSHOTS] = self.ALWAYS_SAVE
            report('screenshots_choice_made', accepted=self.ALWAYS_SAVE)
        self.handle_splash_result()
        self.splash_screen = None
        self.is_dialog_open = False
        self._app.ui_kit.refresh_panel(PanelNames.IMPORT)

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def never_cb(self):
        TRACE("User DOESN'T activated screenshots feature from splash screen")
        self._app.config[OPT_SCREENSHOTS] = self.NEVER_SAVE
        if self._mbox.enabled:
            report('screenshots_choice_made', accepted=self.NEVER_SAVE, multiaccount=True)
            self._mbox.update_preferences({OPT_SCREENSHOTS: self.NEVER_SAVE})
            self._mbox.handle_splash_result_on_thread()
        else:
            report('screenshots_choice_made', accepted=self.NEVER_SAVE)
        self.handle_splash_result(platform == 'win')
        self.splash_screen = None
        self.is_dialog_open = False
        self._app.ui_kit.refresh_panel(PanelNames.IMPORT)

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def close_cb(self):
        TRACE('User closed splash screen')
        if self._mbox.enabled:
            report('screenshots_choice_made', accepted=self.STATE_UNKNOWN, multiaccount=True)
            self._mbox.handle_splash_result_on_thread()
        else:
            report('screenshots_choice_made', accepted=self.STATE_UNKNOWN)
        self.handle_splash_result(platform == 'win')
        self.splash_screen = None
        self.is_dialog_open = False

    def remove_files(self, file_queue):
        for file_path, copy_link, show_bubble in file_queue:
            if is_exists(self._app.sync_engine.fs, unicode(file_path)):
                self._app.sync_engine.fs.remove(unicode(file_path))

    def show_splash_screen(self, file_path):
        TRACE('Show screenshots splash screen')
        self.is_dialog_open = True
        mbox_selector = None
        if self._mbox.has_secondary:
            role = Roles.BUSINESS
            if self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.ALWAYS_SAVE:
                role = self._mbox.role
            mbox_selector = MultiAccountSelector(ScreenshotsStrings.mbox_save, self._mbox.account_labels_plain_long.personal, self._mbox.account_labels_plain_long.business, role)
            report('screenshots_choice_shown', role=role, multiaccount=True)
        else:
            report('screenshots_choice_shown')
        self._app.ui_kit.show_screenshots_dialog(self.always_cb, self.never_cb, self.close_cb, unicode(file_path), mbox_selector)

    @message_sender(ScreenshotsProcessingThread.call_after, handle_exceptions=True)
    def screenshot_handler(self, file_path, copy_link = True, show_bubble = True):
        TRACE('New Screenshot found: %r', file_path)
        if self.should_show_dialog():
            self.file_queue.append((file_path, copy_link, show_bubble))
            self.show_splash_screen(file_path)
        elif self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.STATE_UNKNOWN:
            self.file_queue.append((file_path, copy_link, show_bubble))
        elif self._app.config.get(OPT_SCREENSHOTS, self.STATE_UNKNOWN) == self.ALWAYS_SAVE:
            self.do_move(file_path, copy_link, show_bubble)
        if not self.should_listen_for_screenshots(self._app) and self._mbox.is_primary and platform == 'win':
            if file_path is not None and is_exists(self._app.sync_engine.fs, unicode(file_path)):
                self._app.sync_engine.fs.remove(unicode(file_path))

    def do_move(self, file_path, copy_link, show_bubble):
        if get_monotonic_time_seconds() - self.last_screenshot_time > 30:
            TRACE('Clear set')
            self.processed_set = set()
        destination_folder = self.get_screenshots_folder()
        if not file_path or not destination_folder:
            TRACE("!!do_move can't be done file_path: %r, destination_folder: %r", file_path, destination_folder)
            return
        if self._app.sync_engine.case_sensitive:
            unicode_path = unicode(file_path)
        else:
            unicode_path = file_path.lower()
        if unicode_path in self.processed_set:
            TRACE('Screenshot already processed: %r', file_path)
            return
        new_path = self.move_file_to_dropbox(file_path, destination_folder)
        TRACE('Screenshot moved to: %r', new_path)
        if new_path is None:
            return
        if self._mbox.enabled or self._mbox.is_secondary:
            report('screenshot_moved', copy_link=copy_link, multiaccount=True, is_primary=self._mbox.is_primary, role=self._mbox.role)
        else:
            report('screenshot_moved', copy_link=copy_link)
        server_path = self._app.sync_engine.local_to_server(new_path)
        if copy_link:
            TRACE('Trying to copy link of: %r', server_path)
            self._app.client_shmodel.shmodel_to_clipboard_async(server_path, is_dir=False, origin=ClientShmodelOrigin.SCREENSHOTS)
        elif show_bubble and platform == 'win':
            if self._mbox.is_primary:
                self.show_success_bubble(new_path)
            else:
                self._mbox.show_screenshot_success_bubble(new_path)
        if self._app.sync_engine.case_sensitive:
            self.processed_set.add(unicode(new_path))
        else:
            self.processed_set.add(new_path.lower())
        self.last_screenshot_time = get_monotonic_time_seconds()

    def show_success_bubble(self, new_path):
        self._app.ui_kit.show_bubble(Bubble(BubbleKind.WINDOWS_SCREENSHOT, ScreenshotsStrings.file_created_bubble_message, ScreenshotsStrings.file_created_bubble_title, self._app.bubble_context, self._app.bubble_context.make_func_context_ref(partial(self._user_clicked_screenshot_bubble, new_path))))

    def _user_clicked_screenshot_bubble(self, file_path):
        assert platform == 'win'
        arch.util.highlight_file(unicode(file_path))

    def move_file_to_dropbox(self, file_path, destination_folder):
        assert destination_folder
        try:
            dest_path = root_relative_to_local_path(self._app, destination_folder)
            file_base_name = ScreenshotsStrings.file_name % dict(local_time=strftime('%Y-%m-%d %H.%M.%S', localtime(getctime(unicode(file_path)))), ext=unicode(file_path).rsplit('.', 1)[1])
            full_dest_path = dest_path.join(file_base_name)
            TRACE('Screenshots new path: %r \nold path: %r, \ncase case_sensitive:%r', full_dest_path, file_path, self._app.sync_engine.case_sensitive)
            if file_path.lower() != full_dest_path.lower() or self._app.sync_engine.case_sensitive and file_path != full_dest_path:
                full_dest_path = create_unique_file_name(self._app.sync_engine.fs, dest_path, file_base_name)
                if is_exists(self._app.sync_engine.fs, file_path):
                    TRACE('Moving screenshot :%r', file_path)
                    move(self._app.sync_engine.fs, file_path, unicode(full_dest_path))
                    TRACE('Screenshot moved to Dropbox: %r', file_path)
                else:
                    return None
        except OSError as e:
            if e.errno == errno.ENOENT:
                TRACE('File not found during move: %r', file_path)
            else:
                unhandled_exc_handler()
            return None
        except Exception:
            unhandled_exc_handler()
            return None

        return full_dest_path


class MultiAccountSelector(object):

    def __init__(self, text, personal_string, business_string, default_selection = Roles.PERSONAL):
        self._text = text
        self._personal_string = personal_string
        self._business_string = business_string
        self._default_selection = default_selection

    @property
    def text(self):
        return self._text

    @property
    def selections(self):
        return [self._personal_string, self._business_string]

    @property
    def default_index(self):
        if self._default_selection == Roles.PERSONAL:
            return 0
        return 1

    def translate_index(self, index):
        if index == 0:
            return Roles.PERSONAL
        return Roles.BUSINESS


class ScreenshotsCallbacks(object):

    def __init__(self):
        self._lock = threading.Lock()
        self._callbacks = [None, None]

    @property
    def callbacks(self):
        callbacks = []
        with self._lock:
            callbacks = [self._callbacks[0], self._callbacks[1]]
        return callbacks

    def set_primary(self, cb):
        with self._lock:
            self._callbacks[0] = cb

    def set_secondary(self, cb):
        with self._lock:
            self._callbacks[1] = cb
