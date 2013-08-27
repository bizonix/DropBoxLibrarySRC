#Embedded file name: arch/mac/symbol.py
from __future__ import absolute_import
import platform
import sys
from distutils.ccompiler import new_compiler
from distutils.sysconfig import customize_compiler
import dropbox.db_thread
MINOR_VERSION = int(platform.mac_ver()[0].split('.')[1])
DECORATION = 'DB____%s____DB'
symbols = {'HashUploadThread': None,
 'HashDownloadThread': None,
 'AuthenticationThread': None,
 'HashThread': None,
 'UploadThread': None,
 'SyncThread': None,
 'ReconstructThread': None,
 'WatchdogThread': None,
 'ReindexThread': None,
 'P2PThread': None,
 'StatusThread': None,
 'DirectoryReaderThread': None,
 'FileEvents': None,
 'FsChangeThread': None,
 'TrayIcon': None,
 'RtraceThread': None,
 'DBFSEventThread': None,
 'PhotoUploader': None,
 'GandalfThread': None,
 'ListThread': None,
 'EventReporterThread': None}

def build_sym_dylib():
    with open('sym.c', 'w') as f:
        f.write('typedef void (*pycallback)();\n')
        func = 'void ' + DECORATION + '(pycallback cb) { cb(); }\n'
        for symbol in symbols:
            f.write(func % symbol)

    compiler = new_compiler()
    customize_compiler(compiler)
    compiler.compiler_so = [ x for x in compiler.compiler_so if not x.startswith('-O') ]
    compiler.linker_so = [ x for x in compiler.linker_so if not x.startswith('-O') ]
    compiler.compile(['sym.c'])
    compiler.link_shared_object(['sym.o'], 'Frameworks/sym.dylib')


if __name__ == '__main__':
    build_sym_dylib()
else:
    import ctypes
    from functools import partial
    import build_number
    import dropbox.db_thread
    from dropbox.trace import unhandled_exc_handler
    from dropbox.mac.internal import get_frameworks_dir
    try:
        PYCALLBACK = ctypes.CFUNCTYPE(None)
        if not hasattr(build_number, 'frozen'):
            try:
                build_sym_dylib()
            except:
                unhandled_exc_handler()

        dylib = ('%s/sym.dylib' % get_frameworks_dir()).encode(sys.getfilesystemencoding())
        sym = ctypes.cdll.LoadLibrary(dylib)
        for symbol in symbols:
            try:
                symbols[symbol] = getattr(sym, DECORATION % symbol)
                symbols[symbol].argtypes = [PYCALLBACK]
                symbols[symbol].restype = ctypes.c_int
            except:
                unhandled_exc_handler()

    except:
        unhandled_exc_handler()

    def symbolize(sym, f, *n, **kw):
        if symbols.get(sym, None) is not None:

            def caller():
                return symbols[sym](PYCALLBACK(partial(f, *n, **kw)))

            return caller
        else:
            return partial(f, *n, **kw)


    dropbox.db_thread.watched_thread_wrapper = symbolize
