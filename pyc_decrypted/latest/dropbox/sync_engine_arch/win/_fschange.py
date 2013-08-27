#Embedded file name: dropbox/sync_engine_arch/win/_fschange.py
import pprint
import threading
import traceback
import win32api
import win32con
from ctypes import c_wchar_p
from pynt.dlls.shell32 import shell32
from win32com.shell import shellcon
from build_number import BUILD_KEY
from dropbox.db_thread import db_thread
from dropbox.fastwalk_bridge import fastwalk
from dropbox.native_threading import NativeCondition
from dropbox.threadutils import StoppableThread
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.win32.version import VISTA, WINDOWS_VERSION
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY

class RegKeyCouldntGetError(Exception):
    pass


cached_installpath = None

def get_installpath(make_path):
    global cached_installpath
    if cached_installpath is None:
        configuration = get_registry(InstallPath=None)
        installpath = configuration['InstallPath']
        if installpath is None:
            TRACE('No installpath in HKCU, checking HKLM')
            default_installpath = win32api.GetModuleFileName(0).rsplit('\\', 1)[0]
            configuration = get_registry(win32con.HKEY_LOCAL_MACHINE, InstallPath=default_installpath)
            installpath = configuration['InstallPath']
        cached_installpath = make_path(installpath.decode('mbcs'))
    return cached_installpath


def get_registry(*hkey, **keys_and_default_values):
    if len(hkey) == 0:
        hkey = (win32con.HKEY_CURRENT_USER, 'SOFTWARE\\%s' % BUILD_KEY)
    elif len(hkey) == 1:
        hkey = (hkey[0], 'SOFTWARE\\%s' % BUILD_KEY)
    elif len(hkey) > 2:
        raise RegKeyCouldntGetError('Too many non-keyword arguments to get_registry')
    try:
        hkey = win32api.RegOpenKeyEx(hkey[0], hkey[1], 0, win32con.KEY_READ)
        TRACE('Opened %s key' % BUILD_KEY)
    except Exception:
        TRACE("Couldn't open %s key" % BUILD_KEY)
        unhandled_exc_handler(False)
        hkey = None

    if hkey:
        try:
            configuration = {}
            for key in keys_and_default_values:
                TRACE('Trying to read value for key: %s' % key)
                try:
                    value, val_typ = win32api.RegQueryValueEx(hkey, key)
                    configuration[key] = value
                    TRACE('Read value: %s' % value)
                except Exception:
                    TRACE(traceback.format_exc())
                    try:
                        raise RegKeyCouldntGetError(key)
                    except Exception:
                        unhandled_exc_handler(False)

                    configuration[key] = keys_and_default_values[key]
                    TRACE("Couldn't read value, using default")

        finally:
            win32api.RegCloseKey(hkey)

        TRACE('Closed %s key' % BUILD_KEY)
    else:
        configuration = keys_and_default_values
    TRACE('get_registry is returning: %s' % pprint.pformat(configuration))
    return configuration


class FsChangeThread(StoppableThread):

    def __init__(self):
        super(FsChangeThread, self).__init__(name='FSCHANGE')
        self.to_touch = set()
        self.touching = NativeCondition()
        self.started = threading.Lock()
        self.touch_tree_event = threading.Event()
        self.should_wakeup = False
        self.should_shell_touch_tree = False
        self.type_of_touch = shellcon.SHCNF_FLUSHNOWAIT if WINDOWS_VERSION >= VISTA else shellcon.SHCNF_FLUSH

    def start_if_necessary(self):
        if self.started.acquire(False):
            self.start()

    def set_wakeup_event(self):
        with self.touching:
            self.should_wakeup = True
            self.touching.notify()

    def shell_touch(self, full_path):
        with self.touching:
            self.to_touch.add(full_path)
            self.touching.notify()

    def shell_touch_tree(self, dropbox_folder, timeout = 2):
        with self.touching:
            self.touch_tree_event.clear()
            self.should_shell_touch_tree = dropbox_folder
            self.touching.notify()
        self.touch_tree_event.wait(timeout)

    def run(self):
        while not self.stopped():
            try:
                with self.touching:
                    while not self.to_touch and not self.should_wakeup and not self.should_shell_touch_tree:
                        self.touching.wait()

                    self.should_wakeup = False
                    if self.should_shell_touch_tree:
                        tree_to_touch = unicode(self.should_shell_touch_tree)
                    else:
                        tree_to_touch = None
                if tree_to_touch:
                    try:
                        for dirpath, ents in fastwalk(tree_to_touch):
                            for dirent in ents:
                                try:
                                    if dirent.type != FILE_TYPE_DIRECTORY:
                                        continue
                                    with self.touching:
                                        self.to_touch.add(dirent.fullpath)
                                except Exception:
                                    unhandled_exc_handler()

                    except Exception:
                        unhandled_exc_handler()
                    finally:
                        tree_to_touch = None
                        self.should_shell_touch_tree = False
                        self.touch_tree_event.set()

                    continue
                with self.touching:
                    full_path = c_wchar_p(unicode(self.to_touch.pop())) if self.to_touch else None
                if full_path:
                    shell32.SHChangeNotify(shellcon.SHCNE_UPDATEITEM, shellcon.SHCNF_PATHW | self.type_of_touch, full_path, 0)
            except Exception:
                unhandled_exc_handler()


fs_change_thread = db_thread(FsChangeThread)()
shell_touch = fs_change_thread.shell_touch
shell_touch_tree = fs_change_thread.shell_touch_tree
enable_fs_change_notifications = fs_change_thread.start_if_necessary
