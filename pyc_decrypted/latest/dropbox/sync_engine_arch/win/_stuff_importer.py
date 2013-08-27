#Embedded file name: dropbox/sync_engine_arch/win/_stuff_importer.py
import time
from dropbox.features import feature_enabled
from dropbox.client.notifications_exceptions import StickyNotificationKeyError
from dropbox.functions import handle_exceptions
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.common.notifications import PhotoGalleryStickyNotification
from ._lib_import_logic import LibraryImporter, LibraryNames, IMPORT_ALLOWED, IMPORT_CONFLICT_IN_DROPBOX, IMPORT_NOT_ENOUGH_SPACE, IMPORT_LIB_HAS_OTHER_DIRS
MB = 1048576

class GenericImporter(object):

    def __init__(self, app):
        self.app = app
        self._should_import = None

    def on_stats_gathered(self, info_by_library, errors_by_library):
        show_sticky = False
        error = errors_by_library.get(self.LIBRARY_NAME)
        if error:
            TRACE('!! Not importing %s library because of error %r', self.LIBRARY_NAME, error)
            return
        info = info_by_library[self.LIBRARY_NAME]
        self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = info.num_files
        if info.size > self.SIZE_THRESHOLD or info.num_files > self.NUM_FILES_THRESHOLD:
            TRACE('%d files ready to import from %s library!', info.num_files, self.LIBRARY_NAME)
            show_sticky = True
            self.app.config[self.CONFIG_KEY_SHOW_STICKY] = True
        else:
            TRACE('Pictures library size (%s) and num_photos (%d) did not pass the threshold', '%d MB' % (info.size / 1024 / 1024), info.num_files)
            show_sticky = False
            self.app.config[self.CONFIG_KEY_SHOW_STICKY] = False
        return show_sticky

    def should_show_sticky(self):
        return self.app.config.get(self.CONFIG_KEY_SHOW_STICKY, False)

    def clear_sticky_config(self):
        del self.app.config[self.CONFIG_KEY_SHOW_STICKY]

    def import_complete(self):
        return self.app.config.get(self.CONFIG_KEY_LAST_IMPORT, False)

    @property
    def num_files(self):
        return self.app.config.get(self.CONFIG_KEY_NUM_FILES_FOUND, None)

    @property
    def should_import(self):
        if self._should_import is not None:
            return self._should_import
        if not self.app.gandalf.info_received():
            raise Exception('Importer called before gandalf was ready!')
        if not feature_enabled(self.FEATURE_NAME):
            self._should_import = False
        elif not self.app.gandalf.allows(self.GANDALF_NAME):
            self._should_import = False
        elif self.app.config.get(self.CONFIG_KEY_IMPORT_TIME):
            self._should_import = False
        else:
            self._should_import = True
        return self._should_import

    def scanning_error(self):
        self.app.config[self.CONFIG_KEY_SHOW_STICKY] = False
        self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = 0
        self._should_import = False

    def should_scan(self):
        if not self.should_import:
            return False
        elif self.CONFIG_KEY_SHOW_STICKY not in self.app.config or self.num_files is None:
            return True
        else:
            TRACE('IMPORTSCAN: %s files in %s library, %sshowing sticky notification', self.num_files, self.LIBRARY_NAME, '' if self.app.config[self.CONFIG_KEY_SHOW_STICKY] else 'not ')
            return False

    def set_import_button_config(self, setting):
        self.app.config[self.CONFIG_KEY_SHOW_PREFS_BUTTON] = setting

    def clear_import_button_config(self):
        del self.app.config[self.CONFIG_KEY_SHOW_PREFS_BUTTON]


class PhotoGalleryImporter(GenericImporter):
    CONFIG_KEY_IMPORT_TIME = 'gallery_import_import_time'
    CONFIG_KEY_NUM_FILES_FOUND = 'gallery_import_num_photos_found'
    CONFIG_KEY_SHOW_STICKY = 'gallery_import_show_sticky'
    CONFIG_KEY_SHOW_PREFS_BUTTON = 'gallery_import_show_prefs_button'
    CONFIG_KEY_OUT_OF_SPACE = 'gallery_import_out_of_space'
    FEATURE_NAME = 'win-pictures-importer'
    GANDALF_NAME = 'desktop-photo-importer-windows'
    LIBRARY_NAME = LibraryNames.Pictures
    SIZE_THRESHOLD = 256 * MB
    NUM_FILES_THRESHOLD = 20

    @staticmethod
    def show_import_button(app):
        if not feature_enabled(PhotoGalleryImporter.FEATURE_NAME) or not app.gandalf.info_received() or not app.gandalf.allows(PhotoGalleryImporter.GANDALF_NAME):
            return False
        return app.config.get(PhotoGalleryImporter.CONFIG_KEY_SHOW_PREFS_BUTTON, False)


class DocumentImporter(GenericImporter):
    CONFIG_KEY_IMPORT_TIME = 'document_import_import_time'
    CONFIG_KEY_NUM_FILES_FOUND = 'document_import_num_files_found'
    CONFIG_KEY_SHOW_STICKY = 'document_import_show_sticky'
    CONFIG_KEY_SHOW_PREFS_BUTTON = 'document_import_show_prefs_button'
    CONFIG_KEY_OUT_OF_SPACE = 'document_import_out_of_space'
    FEATURE_NAME = 'win-documents-importer'
    GANDALF_NAME = 'desktop-document-importer-windows'
    LIBRARY_NAME = LibraryNames.Documents
    SIZE_THRESHOLD = 16 * MB
    NUM_FILES_THRESHOLD = 20

    @staticmethod
    def show_import_button(app):
        if not feature_enabled(DocumentImporter.FEATURE_NAME) or not app.gandalf.info_received() or not app.gandalf.allows(DocumentImporter.GANDALF_NAME):
            return False
        return app.config.get(DocumentImporter.CONFIG_KEY_SHOW_PREFS_BUTTON, False)


class StuffImporter(object):
    CONFIG_KEY_DISABLED = 'library_import_disabled'
    CONFIG_KEY_LAST_SCAN = 'library_import_last_scan'
    ALL_LIBRARIES = [LibraryNames.Pictures, LibraryNames.Documents]
    SHOW_PREFS_BUTTON_VALS = set([IMPORT_ALLOWED,
     IMPORT_CONFLICT_IN_DROPBOX,
     IMPORT_NOT_ENOUGH_SPACE,
     IMPORT_LIB_HAS_OTHER_DIRS])
    SCAN_TIMEOUT_SECONDS = 15

    def __init__(self, app):
        self.app = app
        self.importer = LibraryImporter(app)
        self.pics_importer = PhotoGalleryImporter(self.app)
        self.docs_importer = DocumentImporter(self.app)
        if self.app.gandalf.info_received(self._startup):
            self._startup()

    @staticmethod
    def show_import_button(app):
        return (PhotoGalleryImporter.show_import_button(app), DocumentImporter.show_import_button(app))

    @handle_exceptions
    def _startup(self):
        if not self.pics_importer.should_import and not self.docs_importer.should_import:
            return
        self._refresh_scanned_data()
        self.maybe_show_sticky()

    def _refresh_scanned_data(self):
        if self.pics_importer.should_scan() or self.docs_importer.should_scan():
            self._scan_libraries()

    def _libs_to_scan(self):
        libraries = []
        if self.pics_importer.should_import:
            libraries.append(LibraryNames.Pictures)
        if self.docs_importer.should_import:
            libraries.append(LibraryNames.Documents)
        return libraries

    def _scan_libraries(self):
        libraries = self._libs_to_scan()
        TRACE('IMPORTSCAN: Scanning %r libraries for importability', libraries)
        self.pics_importer.clear_sticky_config()
        self.docs_importer.clear_sticky_config()
        self.pics_importer.clear_import_button_config()
        self.docs_importer.clear_import_button_config()
        self.app.config[self.CONFIG_KEY_LAST_SCAN] = int(time.time())
        try:
            db_path = self.app.config['dropbox_path']
        except KeyError:
            TRACE("!! IMPORTSCAN: Couldn't get Dropbox path! Bailing")
            return

        self.importer.background_scan_libraries(db_path, libraries, self._on_stats_gathered, self.SCAN_TIMEOUT_SECONDS)

    def _on_stats_gathered(self, error):
        if error:
            TRACE('!! Not importing any libraries because of fatal error %r', error)
            self.pics_importer.scanning_error()
            self.docs_importer.scanning_error()
            return
        libraries = self._libs_to_scan()
        import_ret = self.importer.check_import_supported(self.app.config['dropbox_path'], libraries)
        if import_ret in self.SHOW_PREFS_BUTTON_VALS:
            self._set_import_button_config(True)
            if import_ret != IMPORT_ALLOWED:
                return
            total_size, info_by_library, errors_by_library = self.importer.get_library_info()
            if self.pics_importer.should_import:
                self.pics_importer.on_stats_gathered(info_by_library, errors_by_library)
            if self.docs_importer.should_import:
                self.docs_importer.on_stats_gathered(info_by_library, errors_by_library)
            self.maybe_show_sticky()

    @handle_exceptions
    def prompt_import(self):
        if self.CONFIG_KEY_DISABLED in self.app.config:
            del self.app.config[self.CONFIG_KEY_DISABLED]
        self.prompt_cb = self.app.ui_kit.show_gallery_import_dialog(import_cb=self._import_pictures_library, cancel_cb=self._handle_cancel, never_cb=self._never_import)
        self._remove_sticky()

    @handle_exceptions
    def _import_pictures_library(self):
        self.prompt_cb = None
        self._remove_sticky()
        self._set_import_button_config(False)
        self.importer.background_scan_libraries(self.app.config['dropbox_path'], [LibraryNames.Pictures], self._on_stats_gathered_before_move, self.SCAN_TIMEOUT_SECONDS)

    def _on_stats_gathered_before_move(self, error):
        if error:
            TRACE('!! Not importing Pictures because of error %r', error)
            return
        import_ret = self.importer.check_import_supported(self.app.config['dropbox_path'], [LibraryNames.Pictures])
        if import_ret == IMPORT_ALLOWED:
            self.importer.move_libraries(self.app.config['dropbox_path'], [LibraryNames.Pictures], self._on_move_complete)
        elif import_ret in self.SHOW_PREFS_BUTTON_VALS:
            self._set_import_button_config(True)

    def _on_move_complete(self, error, libraries_moved):
        if error:
            self._set_import_button_config(True)
        else:
            self._set_import_button_config(False)
        TRACE('IMPORT: Library move complete.  Libraries moved: %r', libraries_moved.keys())

    def _handle_cancel(self):
        self.prompt_cb = None

    @handle_exceptions
    def _never_import(self):
        self.app.config[self.CONFIG_KEY_DISABLED] = True
        self._remove_sticky()
        self.prompt_cb = None
        return True

    @handle_exceptions
    def maybe_show_sticky(self):
        photos_sticky = self.pics_importer.should_show_sticky()
        docs_sticky = self.docs_importer.should_show_sticky()
        if not photos_sticky and not docs_sticky:
            return
        sticky = PhotoGalleryStickyNotification(num_photos=1, import_source='Pictures', import_cb=self.prompt_import, never_cb=self._never_import)
        self.app.notification_controller.add_sticky(sticky)

    def _remove_sticky(self):
        try:
            self.app.notification_controller.remove_sticky(PhotoGalleryStickyNotification.STICKY_KEY)
            TRACE('IMPORT: Removed sticky notification prompting Pictures import')
        except StickyNotificationKeyError:
            TRACE('IMPORT: No sticky to remove')
        except Exception:
            unhandled_exc_handler()

    def _set_import_button_config(self, setting):
        self.pics_importer.set_import_button_config(setting)
        self.docs_importer.set_import_button_config(setting)
