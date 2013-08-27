#Embedded file name: dropbox/mac/internal.py
from __future__ import absolute_import
import functools
import grp
import json
import os
import pwd
import sys
import stat
import struct
import subprocess32 as subprocess
import threading
import time
import build_number
from dropbox.dbexceptions import TimeoutError
from dropbox.features import current_feature_args
from dropbox.gui import SafeValue
from dropbox.mac.version import LEOPARD, MAC_VERSION, SNOW_LEOPARD, MOUNTAIN_LION
from dropbox.trace import unhandled_exc_handler, TRACE
from pymac.helpers.process import find_instances
BUILD_KEY = build_number.BUILD_KEY
BINARIES_READY_TIMEOUT = 120
binaries_ready = SafeValue()
post_linked_yet = threading.Event()

def executable(opts = ()):
    opts = list(opts) + current_feature_args()
    if hasattr(build_number, 'frozen'):
        ex = os.path.join(sys.executable.rsplit('/', 1)[0], BUILD_KEY)
        cmd = [ex] + list(opts)
    else:
        cmd = [sys.executable, os.path.join('bin', 'dropbox')] + list(opts) + ['--key=%s' % BUILD_KEY]
    return cmd


def username_to_uid(username):
    return pwd.getpwnam(username).pw_uid


def groupname_to_gid(groupname):
    return grp.getgrnam(groupname).gr_gid


def find_finder_pid():
    try:
        return iter(find_instances('/System/Library/CoreServices/Finder.app/Contents/MacOS/Finder', unhandled_exc_handler=unhandled_exc_handler)).next()
    except StopIteration:
        return None
    except Exception:
        unhandled_exc_handler()
        return None


def is_intel():
    return struct.pack('@i', 1) == '\x01\x00\x00\x00'


def osa_parse_result(what):
    if not what:
        return what
    end = -1 if what[-1] == '\n' else None
    if what[0] == '{':
        return json.loads('[' + what[1:what.rfind('}')] + ']')
    return what[:end]


if MAC_VERSION >= MOUNTAIN_LION:
    arch_for_osa_send_piped = '-x86_64'
else:
    arch_for_osa_send_piped = '-i386' if is_intel() else '-ppc'

def osa_send_piped(what, async = False, trace = True, parse_results = False, args = None, timeout = None):
    if isinstance(what, unicode):
        what = what.encode('utf8')

    def osa_sender(async):
        if trace:
            TRACE('Sending (piped): %s (%s bytes)' % (what[:5000], len(what)))
        if MAC_VERSION > LEOPARD:
            cmd = ['arch', arch_for_osa_send_piped]
        else:
            cmd = []
        cmd += ['/usr/bin/osascript']
        if parse_results:
            cmd.extend(['-s', 's'])
        if args:
            cmd.extend('-')
            cmd.extend(args)
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.stdin.write(what)
        p.stdin.close()
        if async or parse_results:
            if timeout:
                end = time.time() + timeout
                while p.poll() is None:
                    if time.time() < end:
                        time.sleep(0.1)
                    else:
                        raise TimeoutError()

            else:
                p.wait()
        if async:
            TRACE('ret: %d\nstdout: %s\nstderr: %s' % (p.returncode, p.stdout.read(), p.stderr.read()))
        if parse_results:
            if p.returncode == 0:
                return (osa_parse_result(p.stdout.read()), p.stderr.read())
            raise Exception('osascript failed: stdout: %s\nstderr: %s' % (p.stdout.read(), p.stderr.read()))

    if async:
        threading.Thread(target=osa_sender, name='OSA_SEND_PIPED', args=(True,)).start()
    else:
        return osa_sender(False)


_RAISE_APPLICATIONS_ASCRIPT = 'tell application "%s" to activate' % (BUILD_KEY if hasattr(build_number, 'frozen') else 'Python')
raise_application = functools.partial(osa_send_piped, _RAISE_APPLICATIONS_ASCRIPT, async=True)

def open_folder_in_finder(path, cleanup = False):
    script = '\n    tell application "Finder"\n        activate\n        set x to (POSIX file "%s")\n        open x\n        %s\n    end tell\n    '
    script %= (path.encode('utf-8'), 'clean up window 1 by name' if cleanup else '')
    osa_send_piped(script, async=True)


def select_file_in_finder(path):
    st = os.stat(path)
    cmd = 'tell application "Finder"\nactivate\nselect '
    cmd += 'folder' if stat.S_ISDIR(st.st_mode) else 'file'
    cmd += ' (POSIX file "' + path.encode('utf-8') + '")\nend tell'
    osa_send_piped(cmd, async=True)


def select_files_in_finder(paths, cleanup = False):
    script = '\n    on run argv\n        set paths to {}\n        repeat with posixPath in argv\n            try\n                set pf to POSIX file posixPath\n                set a to pf as alias\n                set end of paths to pf\n            on error\n                --\n            end try\n        end repeat\n        if (not paths = {}) then\n            tell application "Finder"\n                reveal paths\n                activate\n                %s\n            end tell\n        end if\n    end run\n    '
    script %= 'clean up window 1 by name' if cleanup else ''
    osa_send_piped(script, args=paths, async=True)


def show_finder_popup(title, msg, buttons, default_button = 0, cancel_button = -1):
    script = '\n    on run argv\n        set alertTitle to (first item of argv)\n        set alertMsg to (item 2 of argv)\n        set defaultButton to (item 3 of argv as integer)\n        set cancelButton to (item 4 of argv as integer)\n        set numArgs to count argv\n        set alertButtons to items 5 through numArgs of argv\n        tell application "Finder"\n            try\n                activate\n                display dialog alertMsg buttons alertButtons default button defaultButton with title alertTitle\n                set selected to (button returned of result)\n            on error number errNum\n                if errNum is -128 then return cancelButton\n            end try\n        end tell\n        repeat with i from 1 to the count of alertButtons\n            if item i of alertButtons is selected then return i\n        end repeat\n        return 0\n    end run\n    '
    args = [title,
     msg,
     str(default_button + 1),
     str(cancel_button + 1)] + buttons
    out, err = osa_send_piped(script, args=args, trace=False, parse_results=True)
    if out:
        return int(out) - 1
    return -1


def get_contents_root():
    if hasattr(build_number, 'frozen'):
        executable = sys.executable.decode('utf8')
        return executable[:executable.rfind(u'/Contents') + 9]
    else:
        return os.getcwdu()


def get_app_path():
    assert hasattr(build_number, 'frozen'), 'no such thing!'
    return get_contents_root()[:-9]


def get_frameworks_dir():
    return u'%s/Frameworks' % get_contents_root()


def get_resources_dir():
    return u'%s/Resources' % get_contents_root()


def get_icons_folder():
    return u'%s/%s' % (get_contents_root(), u'Resources' if hasattr(build_number, 'frozen') else u'icons')


def get_sanitized_executable_path():
    if not hasattr(build_number, 'frozen'):
        return 'dev'
    full_path = get_app_path()
    suffix = '/%s.app' % (BUILD_KEY,)
    path = full_path[:-len(suffix)]
    if path == '/Applications':
        return path
    if path.startswith('/Volumes/'):
        if path.startswith('/Volumes/%s Installer' % (BUILD_KEY,)):
            return 'DMG'
        else:
            return 'external'
    home_dir = os.path.expanduser('~/')
    if not path.startswith(home_dir):
        TRACE('Dropbox installed in an unusual place: %r', full_path)
        return 'other'
    subpath = path[len(home_dir):]
    slash_index = subpath.find('/')
    if slash_index >= 0:
        subpath = subpath[:slash_index]
    if subpath in ('Desktop', 'Downloads'):
        return subpath
    if subpath == 'Applications':
        return 'home/Applications'
    return 'home'
