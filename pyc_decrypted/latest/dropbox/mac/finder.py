#Embedded file name: dropbox/mac/finder.py
import MacOS
import aem.send.PSN as PSN
import mactypes
import os
import plistlib
import shutil
import struct
import tarfile
import threading
from AppKit import NSWorkspace, NSWorkspaceLaunchDefault
from CarbonX.AE import AECreateList, AECreateDesc, AECreateAppleEvent
from CarbonX import kAE
from Foundation import NSAutoreleasePool, NSDate, NSMachBootstrapServer, NSObject, NSPortMessage, NSString
try:
    from Foundation import NSUTF16StringEncoding
except ImportError:
    pass

try:
    from Foundation import NSRunningApplication
except ImportError:
    pass

from .helper_installer import get_package_location
from .internal import osa_send_piped, find_finder_pid
from .version import MAC_VERSION, LEOPARD
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.gui import SafeValue, event_handler
PROBABLY_NOT_INJECTED = 0
INJECTED_CURRENT_VERSION = 1
INJECTED_OTHER_VERSION = 2

class NoPortFoundError(Exception):
    pass


class FinderNotRunningError(Exception):
    pass


class FinderTimeoutError(Exception):
    pass


class FinderBusyError(Exception):
    pass


class FinderRestartError(Exception):
    pass


class LegacyFinderController(object):
    FINDER_LOCATION = u'/System/Library/CoreServices/Finder.app'

    def __init__(self):
        self._target = None

    def touch(self, paths):
        try:
            self._update(paths)
            return
        except Exception:
            unhandled_exc_handler()

        for item in paths:
            try:
                self._update([item], no_recurse=True)
            except Exception:
                unhandled_exc_handler(False)

    def touch_all(self):
        return False

    def clear_all(self):
        return False

    @staticmethod
    def _get_target(path):
        highPSN, lowPSN, fsRef = PSN.GetNextProcess(0, 0)
        while True:
            try:
                fsRef.FSCompareFSRefs(path)
                break
            except Exception:
                highPSN, lowPSN, fsRef = PSN.GetNextProcess(highPSN, lowPSN)

        return AECreateDesc(kAE.typeProcessSerialNumber, struct.pack('LL', highPSN, lowPSN))

    def _update(self, fn_list, no_recurse = False):
        if not self._target:
            self._target = self._get_target(self.FINDER_LOCATION)
        try:
            evt = AECreateAppleEvent('fndr', 'fupd', self._target, kAE.kAutoGenerateReturnID, kAE.kAnyTransactionID)
            lst = AECreateList('', False)
            added = 0
            for fn in fn_list:
                try:
                    lst.AEPutDesc(0, mactypes.File(fn).aedesc)
                    added += 1
                except MacOS.Error as e:
                    if e[0] == -43:
                        continue
                    else:
                        raise

            if not added:
                return
            evt.AEPutParamDesc(kAE.keyDirectObject, lst)
            evt.SendMessageThreadSafe(kAE.kAENoReply + kAE.kAECanInteract, kAE.kAEDefaultTimeout)
        except MacOS.Error as e:
            self._target = self._get_target(self.FINDER_LOCATION)
            if no_recurse:
                raise
            else:
                unhandled_exc_handler(False)
                return self._update(fn_list, True)

    def get_injection_state(self):
        return PROBABLY_NOT_INJECTED

    def request_finder_bundle_version(self):
        pass


class FinderController(object):
    EVENT_TIMEOUT = 5
    MAX_QUEUED_EVENTS = 10
    EVENT_NIL = 0
    EVENT_TOUCH = 1
    EVENT_TOUCH_ALL = 2
    EVENT_CLEAR_ALL = 3
    EVENT_INQUIRE_VERSION = 4

    def __init__(self):
        self._port = None
        self._init_version()

    def _init_version(self):
        try:
            tarball = get_package_location('DropboxBundle.bundle')
            t = tarfile.open(tarball, mode='r')
            f = t.extractfile('DropboxBundle.bundle/Contents/Info.plist')
            info = plistlib.readPlist(f)
            self.version = info['CFBundleShortVersionString']
        except Exception:
            unhandled_exc_handler()
            self.version = None

    def touch(self, paths):
        for path in paths:
            try:
                self._send_message(self.EVENT_TOUCH, path)
            except Exception:
                break

        else:
            return

        try:
            self._fallback_touch(paths)
        except Exception:
            unhandled_exc_handler()

    def touch_all(self):
        try:
            self._send_message(self.EVENT_TOUCH_ALL)
        except Exception:
            return False

        return True

    def clear_all(self):
        try:
            self._send_message(self.EVENT_CLEAR_ALL)
        except Exception:
            return False

        return True

    @staticmethod
    def _fallback_touch(fn_list, no_recurse = False):
        try:
            fn_list = [ f.replace('\\', '\\\\').replace('"', '\\"') for f in fn_list if os.path.exists(f) ]
            if not fn_list:
                return
            cmd = 'tell application "Finder" to update {%s}' % ', '.join([ 'alias POSIX file "%s"' % s for s in fn_list ])
            out, err = osa_send_piped(cmd, trace=False, parse_results=True)
        except Exception:
            if no_recurse:
                raise
            else:
                unhandled_exc_handler(False)
                return FinderController._fallback_touch(fn_list, True)

    def _port_name(self, compatibility = False):
        if compatibility or not self.version:
            return 'dropbox_%s' % os.getuid()
        else:
            return 'dropbox_%s_%s' % (os.getuid(), self.version)

    def _connect_port(self):
        self._port = NSMachBootstrapServer.sharedInstance().portForName_(self._port_name())
        if not self._port:
            self._port = NSMachBootstrapServer.sharedInstance().portForName_(self._port_name(compatibility=True))
        if not self._port:
            raise NoPortFoundError('Could not obtain a Mach port to send messages.')

    def _send_message(self, event_type, *arguments):
        if not self._port:
            self._connect_port()
        message_type = bytearray([event_type])
        message_args = [ NSString.stringWithString_(arg).dataUsingEncoding_(NSUTF16StringEncoding) for arg in arguments ]
        components = [message_type] + message_args
        try:
            message = NSPortMessage.alloc().initWithSendPort_receivePort_components_(self._port, None, components)
            if not message.sendBeforeDate_(NSDate.dateWithTimeIntervalSinceNow_(self.EVENT_TIMEOUT)):
                raise Exception('Failed to send the port message.')
        except Exception:
            TRACE('Mach port became invalid.')
            self._port = None
            raise

    def get_injection_state(self):
        try:
            self._connect_port()
            return INJECTED_CURRENT_VERSION
        except NoPortFoundError:
            if NSMachBootstrapServer.sharedInstance().portForName_(self._port_name(compatibility=True)):
                return INJECTED_OTHER_VERSION
            return PROBABLY_NOT_INJECTED

    def request_finder_bundle_version(self):
        try:
            self._send_message(self.EVENT_INQUIRE_VERSION)
        except Exception:
            unhandled_exc_handler(False)
            return False

        return True


if MAC_VERSION <= LEOPARD:
    FinderController = LegacyFinderController

class FinderRestarterHelper(NSObject):
    FinderTerminatedContext = 72
    FinderRestartTimeLimit = 5
    FinderIdentifier = 'com.apple.finder'
    FinderTerminationKey = 'isTerminated'

    def initAndRestartFinder(self):
        if threading.currentThread().getName() == 'MainThread':
            raise Exception('Attempting to restart the Finder on the MainThread.')
        if MAC_VERSION <= LEOPARD:
            raise Exception('Finder restart is only supported on Snow Leopard or above.')
        if self is None:
            raise Exception('Self is None')
        self.init()
        apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(self.FinderIdentifier)
        if not apps:
            raise FinderNotRunningError()
        self.finder = apps[0]
        self.ret = SafeValue()
        TRACE('Terminating finder %r', self.finder)
        self.finder.addObserver_forKeyPath_options_context_(self, self.FinderTerminationKey, 0, self.FinderTerminatedContext)
        try:
            self.finder.terminate()
            ret = self.ret.wait(self.FinderRestartTimeLimit)
        finally:
            self.finder.removeObserver_forKeyPath_(self, self.FinderTerminationKey)

        if ret is None:
            raise FinderTimeoutError()
        if ret is False:
            raise FinderRestartError()
        if find_finder_pid() is None:
            raise FinderRestartError()

    @event_handler
    def observeValueForKeyPath_ofObject_change_context_(self, path, obj, change, context):
        if context == self.FinderTerminatedContext:
            if path == self.FinderTerminationKey:
                TRACE('Restarting finder %r', obj)
                self.ret.set(NSWorkspace.sharedWorkspace().launchAppWithBundleIdentifier_options_additionalEventParamDescriptor_launchIdentifier_(self.FinderIdentifier, NSWorkspaceLaunchDefault, None, None))
        else:
            return super(FinderRestarterHelper, self).observeValueForKeyPath_ofObject_change_context_(path, obj, change, context)


def restart():
    report_bad_assumption('Trying to restart finder.')
    if has_progress_windows():
        raise FinderBusyError()
    pool = NSAutoreleasePool.alloc().init()
    try:
        return FinderRestarterHelper.alloc().initAndRestartFinder()
    finally:
        del pool


def cleanup_old_plugins(HELPERS_DIR):
    try:
        home_dir = os.environ['HOME']
    except KeyError:
        home_dir = os.path.expanduser('~')

    plugin = '%s/Library/Contextual Menu Items/DropboxPlugin.plugin' % home_dir
    if os.path.exists(plugin):
        if os.path.islink(plugin):
            os.unlink(plugin)
        else:
            shutil.rmtree(plugin)
    if MAC_VERSION < LEOPARD:
        path = os.path.dirname(plugin)
        if not os.path.exists(path):
            os.makedirs(path)
        os.symlink('%s/DropboxPlugin.plugin' % HELPERS_DIR.encode('utf8'), plugin)


def has_progress_windows():
    script = '\n    tell application "Finder"\n        set wnds to every window\n        repeat with wnd in wnds\n                if class of wnd is window and wnd is not closeable then return yes\n        end repeat\n    end tell\n    return no\n    '
    out, err = osa_send_piped(script, trace=False, parse_results=True)
    return out == 'yes'


def paths_open_in_finder():
    script = 'tell application "Finder"\n        set af to (target of every Finder window) & {folder "Desktop" of home}\n        set pf to {}\n        repeat with i from 1 to count of af\n          try\n            set pf to pf & {POSIX path of ((item i of af) as text)}\n          end try\n        end repeat\n    end tell\n    '
    try:
        out, err = osa_send_piped(script, trace=False, parse_results=True)
    except Exception:
        unhandled_exc_handler()
        return []

    return out
