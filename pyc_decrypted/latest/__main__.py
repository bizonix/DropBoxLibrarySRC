#Embedded file name: __main__.py
import sys, os, zlib, zipimport
installdir = os.path.normpath(os.path.dirname(sys.path[0]))

def find_eggs():
    for x in os.listdir(installdir):
        if x.endswith('.egg'):
            fp = os.path.join(installdir, x)
            sys.path.append(fp)


find_eggs()

def addldlibrarypath():
    if sys.platform == 'darwin':
        LD_LIBRARY_PATH = 'DYLD_LIBRARY_PATH'
    else:
        LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
    p = installdir
    try:
        paths = os.environ[LD_LIBRARY_PATH].split(os.pathsep)
    except KeyError:
        paths = []

    if p not in paths:
        paths.insert(0, p)
        os.environ[LD_LIBRARY_PATH] = os.pathsep.join(paths)
        os.execv(sys.executable, sys.argv)


def addpath():
    p = installdir
    try:
        paths = os.environ['PATH'].split(os.pathsep)
    except KeyError:
        paths = []

    if p not in paths:
        paths.insert(0, p)
        os.environ['PATH'] = os.pathsep.join(paths)


def addtcltk():
    libtk = os.path.join(installdir, 'lib-tk')
    libtcl = os.path.join(installdir, 'lib-tcl')
    if os.path.isdir(libtk):
        os.environ['TK_LIBRARY'] = libtk
    if os.path.isdir(libtcl):
        os.environ['TCL_LIBRARY'] = libtcl


def fixwin32com():
    if sys.platform != 'win32':
        return
    exec '\ntry:\n    import win32com.client\n    import win32com.gen_py\n    import win32api\nexcept ImportError:\n    pass\nelse:\n    win32com.client.gencache.is_readonly=False\n    tmpdir = os.path.join(win32api.GetTempPath(),\n                          "frozen-genpy-%s%s" % sys.version_info[:2])\n    if not os.path.isdir(tmpdir):\n        os.makedirs(tmpdir)\n    win32com.__gen_path__ = tmpdir\n    win32com.gen_py.__path__=[tmpdir]\n'


addpath()
addtcltk()
try:
    import encodings
except ImportError:
    pass

fixwin32com()
exe = os.path.basename(sys.argv[0])
if exe.lower().endswith('.exe'):
    exe = exe[:-4]
m = __import__('__main__')
m.__dict__['__file__'] = exe + '.py'
exe = exe.replace('.', '_')
importer = zipimport.zipimporter(sys.path[0])
while 1:
    try:
        code = importer.get_code('__main__%s__' % exe)
    except zipimport.ZipImportError as err:
        if '-' in exe:
            exe = exe[:exe.find('-')]
        else:
            raise err
    else:
        break

if exe == 'py':
    exec code
else:
    exec code in m.__dict__
