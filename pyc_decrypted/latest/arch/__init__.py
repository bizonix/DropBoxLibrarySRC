#Embedded file name: arch/__init__.py
import sys
if sys.platform.startswith('win'):
    import win32.constants as constants
    import win32.util as util
    if not hasattr(sys, 'post_build'):
        import win32.enable_xattrs as enable_xattrs
        import win32.directory_reader as directory_reader
        import win32.startup as startup
        import win32.update as update
        import win32.locked_files as locked_files
        import win32.tray_fix as tray_fix
        import win32.photouploader as photouploader
        import win32.screenshots as screenshots
elif sys.platform.startswith('linux'):
    import linux.constants as constants
    import posix_common.util as posix_util
    import linux.util as util
    if not hasattr(sys, 'post_build'):
        import linux.authorization as authorization
        import linux.enable_xattrs as enable_xattrs
        import linux.tracing as tracing
        import linux.directory_reader as directory_reader
        import posix_common.fixperms as fixperms
        import linux.startup as startup
        import linux.update as update
        import linux.photouploader as photouploader
        import linux.screenshots as screenshots
elif sys.platform.startswith('darwin'):
    import mac.constants as constants
    import posix_common.util as posix_util
    import mac.util as util
    if not hasattr(sys, 'post_build'):
        import mac.enable_xattrs as enable_xattrs
        import mac.symbol as symbol
        import mac.tracing as tracing
        import pymac.helpers.authorization as authorization
        import mac.directory_reader as directory_reader
        import mac.startup as startup
        import posix_common.fixperms as fixperms
        import mac.update as update
        import mac.photouploader as photouploader
        import mac.screenshots as screenshots
else:
    raise Exception('Unsupported platform')
