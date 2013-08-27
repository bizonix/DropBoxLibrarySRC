#Embedded file name: dropbox/client/multiaccount/move_dropbox.py
from threading import Thread
import time
from dropbox.bubble import BubbleKind, Bubble
from dropbox.i18n import trans
from dropbox.trace import TRACE, unhandled_exc_handler

def move_dropbox_if_necessary(app):
    dropbox_name = app.mbox.derive_dropbox_name()
    if dropbox_name != app.default_dropbox_folder_name:
        move_dropbox_thread = MoveDropboxThread(app, dropbox_name)
        move_dropbox_thread.start()
        return move_dropbox_thread


class MoveDropboxThread(Thread):
    MAX_RETRIES = 10
    SLEEP_INTERVAL = 60

    def __init__(self, app, new_dropbox_name):
        super(MoveDropboxThread, self).__init__(name='MOVE_MULTIACCOUNT')
        self.new_dropbox_name = new_dropbox_name
        self.app = app
        self.mbox = app.mbox
        self.exit = False

    def warn(self, message, *args, **kwargs):
        TRACE('Warn called with message %r', message)

    def error(self):
        self.app.restart_and_unlink()
        self.exit = True

    def single_attempt(self):
        dropbox_path = self.app.default_dropbox_path
        new_path = unicode(self.app.sync_engine.fs.make_path(dropbox_path).dirname.join(self.new_dropbox_name))
        TRACE('MULTIACCOUNT: Attempting to move to %r', new_path)
        problems = self.app.sync_engine.move(new_path, self.warn, error_callback=self.error)
        if problems:
            TRACE('MULTIACCOUNT: Move failed with problems (%s).  Sleeping for %d seconds', problems, self.SLEEP_INTERVAL)
            time.sleep(self.SLEEP_INTERVAL)
            return False
        else:
            TRACE('MULTIACCOUNT: Move succeeded')
            self.app.mbox.update_dropbox_path(new_path, self.new_dropbox_name)
            msg = trans(u'Your Dropbox folder has been renamed to %(name)s.') % {'name': self.new_dropbox_name}
            bubble = Bubble(BubbleKind.MOVED_DROPBOX_FOLDER, caption=trans(u'Dropbox folder moved'), msg=msg)
            if self.mbox.is_secondary:
                self.mbox.show_bubble(bubble)
            else:
                self.app.ui_kit.show_bubble(bubble)
            return True

    def run(self):
        TRACE('Starting thread for moving Dropbox folder for multiaccount.')
        self.attempts = 0
        while True:
            if self.MAX_RETRIES and self.attempts >= self.MAX_RETRIES:
                TRACE("MULTIACCOUNT: Failed to move user's Dropbox after %d attempts.  Will try again on app restart.", self.MAX_RETRIES)
                break
            try:
                self.attempts += 1
                TRACE('MULTIACCOUNT: Move attempt %d', self.attempts)
                if self.single_attempt():
                    break
            except:
                unhandled_exc_handler()

        TRACE('MULTIACCOUNT: Exiting from MOVE_MULTIACCOUNT thread.')
