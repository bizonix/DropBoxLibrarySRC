#Embedded file name: dropbox/build_common.py
from __future__ import absolute_import
import os
import shutil
import subprocess
import sys
PYTHON_DROPBOX_BUILD = 20
DROPBOX_SQLITE_VERSION = '3.7.13'
ICON_SUFFIX_PROD = ''
ICON_SUFFIX_LOCAL = '-local'
ICON_SUFFIX_LEOPARD = '-lep'
ICON_SUFFIX_LEOPARD_INV = '-lep-inv'
_ICON_SUFFIX_MAP = {'Dropbox': ICON_SUFFIX_PROD}

def get_icon_suffix(build_key):
    return _ICON_SUFFIX_MAP.get(build_key, ICON_SUFFIX_LOCAL)


def get_platform():
    if sys.platform.startswith('win'):
        plat = 'win'
    elif sys.platform.startswith('darwin'):
        plat = 'mac'
    elif sys.platform.startswith('linux'):
        machine = os.uname()[4]
        if machine[0] == 'i' and machine[1].isdigit() and machine[2:4] == '86':
            machine = 'x86'
        plat = 'lnx.' + machine
    else:
        raise
    return plat


def get_build_number():
    import build_number
    return '%s-%s-%s' % (build_number.BUILD_KEY, get_platform(), build_number.VERSION)


def compile_pofiles(is_dev = False):
    args = ['python', 'tools/compile_pofiles.py']
    if is_dev:
        args.append('--dev')
    retcode = subprocess.call(args)
    if retcode != 0:
        raise Exception('Compilation of pofiles to mofiles failed.')


def write_mofiles_as_pyfiles(is_dev = False):
    compile_pofiles(is_dev)
    try:
        os.makedirs('lang')
    except OSError:
        pass

    f2 = open('lang/__init__.py', 'w')
    f2.close()
    subdirs = os.listdir('i18n')
    for code in subdirs:
        if not os.path.isdir(os.path.join('i18n', code)):
            continue
        if code.startswith('.'):
            continue
        mofile = 'i18n/%s/client.mo' % (code,)
        pyfile = 'lang/mofile_%s.py' % (code,)
        with open(mofile, 'rb') as f:
            with open(pyfile, 'wb') as f2:
                f2.write('mo_binary = %r' % (f.read(),))


def unpack_mac_deps():
    framework_dir = os.path.join(os.getcwd(), 'Frameworks')
    framework_src_dir = os.path.join(os.getcwd(), 'mac_dependencies')
    if not os.path.exists(framework_dir):
        os.makedirs(framework_dir)
        shutil.copytree(os.path.join(framework_src_dir, 'Growl.framework'), os.path.join(framework_dir, 'Growl.framework'))


def system_or_die(s):
    code = os.system(s)
    if code != 0:
        raise SystemExit(code)


if __name__ == '__main__':
    is_dev = False
    if len(sys.argv) > 2 and sys.argv[2] == '--dev':
        is_dev = True
    if sys.platform.startswith('darwin'):
        unpack_mac_deps()
        (os.system if is_dev else system_or_die)('python arch/mac/symbol.py')
    system_or_die('python %s %s' % (os.path.join('ui', 'serializeimages.py'), get_icon_suffix(sys.argv[1])))
    if sys.platform.startswith('darwin') or sys.platform.startswith('win32'):
        system_or_die('python %s' % (os.path.join('tools', 'build-xui-views.py'),))
    system_or_die('python %s' % ('make_explicit_imports.py',))
    write_mofiles_as_pyfiles(is_dev)
