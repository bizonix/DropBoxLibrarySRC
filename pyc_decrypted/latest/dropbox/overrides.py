#Embedded file name: dropbox/overrides.py
from __future__ import absolute_import
import sys
import os
import errno
import functools
import types
from dropbox.functions import convert_to_twos_complement
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
import build_number
from Crypto.Random import random
import dropbox.native_threading
import dropbox.read_write_lock
if not build_number.is_frozen():
    from dropbox.low_functions import OverrideRepr, WrapCall
    from dropbox.lock_ordering import OrderedLockTracker, record_broken_locks_and_raise
    from dropbox import native_threading
    from dropbox import read_write_lock
    import threading
    _olt = OrderedLockTracker(record_broken_locks_and_raise)
    import traceback

    def create_overwrite(ovr, acquire_methods = ('acquire',), release_methods = ('release',)):

        def Lock(*n, **kw):
            obj = ovr(*n, **kw)
            t = type(obj)
            stack_frame = sys._getframe(2)
            try:
                fname, line_no = str(stack_frame.f_code.co_filename), str(stack_frame.f_lineno)
            finally:
                del stack_frame

            return _olt.allocate_lock(OverrideRepr(obj, '%s.%s instantiated at %s' % (t.__module__, t.__name__, '%s:%s' % (fname, line_no))), acquire_methods=acquire_methods, release_methods=release_methods, fname=fname, line_no=line_no)

        return WrapCall(ovr, Lock)


    threading.Lock = create_overwrite(threading.Lock)
    threading.RLock = create_overwrite(threading.RLock)
    dropbox.native_threading.NativeMutex = create_overwrite(dropbox.native_threading.NativeMutex)
    dropbox.read_write_lock.RWLock = create_overwrite(dropbox.read_write_lock.RWLock, acquire_methods=('acquire_read', 'acquire_write'), release_methods=('release_read', 'release_write'))
    assert dropbox.native_threading.NativeCondition.__init__.func_globals['NativeMutex'] is dropbox.native_threading.NativeMutex
else:
    _olt = None
if _olt and build_number.is_frozen():

    def _action(grabbed_lock, conflict_lock, error_string):
        report_bad_assumption(error_string, full_stack=True)


    _olt.action = _action
    del _action
if sys.platform.startswith('win'):
    try:

        def makedirs(name, mode = 511):
            head, tail = os.path.split(name)
            if not tail:
                head, tail = os.path.split(head)
            if head and tail and not os.path.exists(head):
                try:
                    makedirs(head, mode)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise

                if tail == os.curdir:
                    return
            if name != '\\\\':
                os.mkdir(name, mode)


        os.makedirs = makedirs
    except:
        unhandled_exc_handler()

    try:
        import ctypes
        bad_code_pages = (950, 10002, 932)
        GetACP = ctypes.windll.kernel32.GetACP
        GetACP.argtypes = []
        GetACP.restype = ctypes.c_uint
        if GetACP() in bad_code_pages:

            def decode_with_check(arg):
                if isinstance(arg, tuple):
                    return tuple((decode_with_check(x) for x in arg))
                if isinstance(arg, list):
                    return list((decode_with_check(x) for x in arg))
                if isinstance(arg, str):
                    try:
                        uarg = arg.decode('mbcs')
                        if arg == uarg.encode('mbcs'):
                            return uarg
                        raise UnicodeError('Not local encoding')
                    except UnicodeError:
                        TRACE('filename conversion failed for %s', arg)
                        return arg

                else:
                    return arg


            def encode_with_check(arg):
                if isinstance(arg, tuple):
                    return tuple((encode_with_check(x) for x in arg))
                elif isinstance(arg, list):
                    return list((encode_with_check(x) for x in arg))
                elif isinstance(arg, unicode):
                    return arg.encode('mbcs')
                else:
                    return arg


            def wrap(func):

                def wrapped(*args):
                    unicode_out = any((isinstance(arg, unicode) for arg in args))
                    args = decode_with_check(args)
                    ret = func(*args)
                    if unicode_out:
                        return ret
                    return encode_with_check(ret)

                f = wrapped
                f.__name__ = 'acp_wrapped_' + func.__name__
                return f


            import os
            os.path.join = wrap(os.path.join)
            os.path.split = wrap(os.path.split)
            os.path.splitext = wrap(os.path.splitext)
            os.path.splitunc = wrap(os.path.splitunc)
            os.path.normpath = wrap(os.path.normpath)
            os.path.normcase = wrap(os.path.normcase)
            os.makedirs = wrap(os.makedirs)
    except:
        unhandled_exc_handler()

    try:
        import _ctypes

        def repr_COMError(error):
            return 'COMError(0x%08x, %s)' % (convert_to_twos_complement(error.args[0]), ', '.join((repr(item) for item in error.args[1:])))


        _ctypes.COMError.__repr__ = repr_COMError
        _ctypes.COMError.__str__ = repr_COMError
    except Exception:
        unhandled_exc_handler()

    try:
        import _subprocess
        _subprocess.WAIT_TIMEOUT = 258
    except Exception:
        unhandled_exc_handler()

old_expanduser = os.path.expanduser

def expanduser_safe(path):
    if isinstance(path, unicode):
        encoding = sys.getfilesystemencoding()
        return old_expanduser(path.encode(encoding)).decode(encoding)
    return old_expanduser(path)


os.path.expanduser = expanduser_safe
if not sys.platform.startswith('win'):
    old_normpath = os.path.normpath

    def normpath_safe(path):
        s = old_normpath(path)
        if s.startswith('//'):
            return s[1:]
        return s


    os.path.normpath = normpath_safe
try:
    import opcode
except ImportError:
    opcode = types.ModuleType('opcode')
    opcode.__all__ = []
    opcode.reverse_engineering_note = 'Hi there!'
    sys.modules['opcode'] = opcode

def __backport_match_hostname():
    import re
    import ssl
    try:
        from ssl import CertificateError
    except ImportError:

        class CertificateError(ValueError):
            pass

        ssl.CertificateError = CertificateError

    try:
        from ssl import match_hostname
    except ImportError:

        def _dnsname_to_pat(dn):
            pats = []
            for frag in dn.split('.'):
                if frag == '*':
                    pats.append('[^.]+')
                else:
                    frag = re.escape(frag)
                    pats.append(frag.replace('\\*', '[^.]*'))

            return re.compile('\\A' + '\\.'.join(pats) + '\\Z', re.IGNORECASE)

        def match_hostname(cert, hostname):
            if not cert:
                raise ValueError('empty or no certificate')
            dnsnames = []
            san = cert.get('subjectAltName', ())
            for key, value in san:
                if key == 'DNS':
                    if _dnsname_to_pat(value).match(hostname):
                        return
                    dnsnames.append(value)

            if not dnsnames:
                for sub in cert.get('subject', ()):
                    for key, value in sub:
                        if key == 'commonName':
                            if _dnsname_to_pat(value).match(hostname):
                                return
                            dnsnames.append(value)

            if len(dnsnames) > 1:
                raise CertificateError("hostname %r doesn't match either of %s" % (hostname, ', '.join(map(repr, dnsnames))))
            elif len(dnsnames) == 1:
                raise CertificateError("hostname %r doesn't match %r" % (hostname, dnsnames[0]))
            else:
                raise CertificateError('no appropriate commonName or subjectAltName fields were found')

        ssl.match_hostname = match_hostname


__backport_match_hostname()

def __cffi_import_override():
    if not build_number.is_frozen():
        return
    import imp
    import importlib
    import cffi.vengine_cpy
    import cffi.verifier
    _orig_load_library = cffi.verifier.Verifier.load_library

    def load_library(self):
        TRACE('CFFI: load_library wrapper invoked for %s (modulefilename is %r)', self.get_module_name(), self.modulefilename)
        self._vengine.collect_types()
        self._has_module = True
        return _orig_load_library(self)

    cffi.verifier.Verifier.load_library = load_library

    class ImpModuleWrapper(object):

        def load_dynamic(self, name, pathname, file = None):
            TRACE('CFFI: load_dynamic stub invoked (name=%r, pathname=%r, file=%r)', name, pathname, file)
            return importlib.import_module(name)

        def __getattr__(self, name):
            return getattr(imp, name)

    cffi.verifier.imp = cffi.vengine_cpy.imp = ImpModuleWrapper()


__cffi_import_override()
