#Embedded file name: arch/mac/screenshots.py
import os
from Foundation import NSUserDefaults
from dropbox import fsutil
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.fileevents import FileEvents
from dropbox.directoryevent import DirectoryEvent
from dropbox.client.screenshots import ScreenshotsCallbacks

class ScreenshotsProvider(object):

    def __init__(self, app):
        self._app = app
        self._callbacks = app.screenshots_callbacks
        TRACE('Initializing screenshots for Mac')
        try:
            standardUserDefaults = NSUserDefaults.standardUserDefaults()
            self.screenshot_folder = os.path.expanduser('~/Desktop')
            try:
                user_defaults_for_screencapture = standardUserDefaults.persistentDomainForName_('com.apple.screencapture')
                if user_defaults_for_screencapture is not None:
                    self.screenshot_folder = user_defaults_for_screencapture.get('location', self.screenshot_folder)
            except Exception:
                unhandled_exc_handler()

            TRACE('Screenshots folder discovered: %r', self.screenshot_folder)
            with self._app.sync_engine.start_stop_lock:
                if self._app.sync_engine.check_if_running(self.watch_folder, already_locked=True):
                    self.watch_folder()
        except Exception:
            unhandled_exc_handler()

    def watch_folder(self):
        self._app.file_events.add_watch(unicode(self.screenshot_folder), self.screenshot_handler, FileEvents.RECURSE_ONE)
        self._app.sync_engine.check_if_stopped(self.sync_engine_stopped, already_locked=True)

    def sync_engine_stopped(self):
        self._app.sync_engine.check_if_running(self.watch_folder, already_locked=True)

    def screenshot_handler(self, local_path_iter):
        try:
            try:
                local_path_iter.type
            except AttributeError:
                pass
            else:
                return

            for evt in local_path_iter:
                try:
                    file_path, evtype = evt.path, evt.type
                except AttributeError:
                    file_path, evtype = evt, DirectoryEvent.UNKNOWN

                TRACE('Screenshot event: %s path: %r', evtype, file_path)
                fs_ = self._app.sync_engine.fs
                is_screenshot = False
                try:
                    is_screenshot = fsutil.get_attr(fs_, file_path, 'mac', u'com.apple.metadata:kMDItemIsScreenCapture')
                except IOError as e:
                    TRACE("Can't take xattr of file, file probably deleted or is not accessible: %r, %r", file_path, e)
                except OSError:
                    TRACE("Can't take xattr of file, no xattr found for file : %r", file_path)

                TRACE('New Screenshot is_screenshot:%r file: %r', is_screenshot, file_path)
                if is_screenshot:
                    path_without_ext = unicode(file_path).rsplit('.', 1)[0]
                    path = self._app.sync_engine.fs.make_path(file_path)
                    if self._callbacks is None:
                        report_bad_assumption('screenshots_callbacks is None even though we have a ScreenshotsProvider')
                    else:
                        for cb in self._callbacks.callbacks:
                            if cb is not None:
                                cb(path, copy_link=not u')' == path_without_ext[-1])

        except Exception:
            unhandled_exc_handler()
