#Embedded file name: distutils/sysconfig.py
__revision__ = '$Id$'
import os
import re
import string
import sys
from distutils.errors import DistutilsPlatformError
PREFIX = os.path.normpath(sys.prefix)
EXEC_PREFIX = os.path.normpath(sys.exec_prefix)
project_base = os.path.dirname(os.path.abspath(sys.executable))
if os.name == 'nt' and 'pcbuild' in project_base[-8:].lower():
    project_base = os.path.abspath(os.path.join(project_base, os.path.pardir))
if os.name == 'nt' and '\\pc\\v' in project_base[-10:].lower():
    project_base = os.path.abspath(os.path.join(project_base, os.path.pardir, os.path.pardir))
if os.name == 'nt' and '\\pcbuild\\amd64' in project_base[-14:].lower():
    project_base = os.path.abspath(os.path.join(project_base, os.path.pardir, os.path.pardir))

def _python_build():
    for fn in ('Setup.dist', 'Setup.local'):
        if os.path.isfile(os.path.join(project_base, 'Modules', fn)):
            return True

    return False


python_build = _python_build()

def get_python_version():
    return sys.version[:3]


def get_python_inc(plat_specific = 0, prefix = None):
    if prefix is None:
        prefix = plat_specific and EXEC_PREFIX or PREFIX
    if os.name == 'posix':
        if python_build:
            buildir = os.path.dirname(sys.executable)
            if plat_specific:
                inc_dir = buildir
            else:
                srcdir = os.path.abspath(os.path.join(buildir, get_config_var('srcdir')))
                inc_dir = os.path.join(srcdir, 'Include')
            return inc_dir
        return os.path.join(prefix, 'include', 'python' + get_python_version())
    if os.name == 'nt':
        return os.path.join(prefix, 'include')
    if os.name == 'os2':
        return os.path.join(prefix, 'Include')
    raise DistutilsPlatformError("I don't know where Python installs its C header files on platform '%s'" % os.name)


def get_python_lib(plat_specific = 0, standard_lib = 0, prefix = None):
    if prefix is None:
        prefix = plat_specific and EXEC_PREFIX or PREFIX
    if os.name == 'posix':
        libpython = os.path.join(prefix, 'lib', 'python' + get_python_version())
        if standard_lib:
            return libpython
        else:
            return os.path.join(libpython, 'site-packages')
    elif os.name == 'nt':
        if standard_lib:
            return os.path.join(prefix, 'Lib')
        elif get_python_version() < '2.2':
            return prefix
        else:
            return os.path.join(prefix, 'Lib', 'site-packages')
    elif os.name == 'os2':
        if standard_lib:
            return os.path.join(prefix, 'Lib')
        else:
            return os.path.join(prefix, 'Lib', 'site-packages')
    else:
        raise DistutilsPlatformError("I don't know where Python installs its library on platform '%s'" % os.name)


_USE_CLANG = None

def customize_compiler(compiler):
    global _USE_CLANG
    if compiler.compiler_type == 'unix':
        cc, cxx, opt, cflags, ccshared, ldshared, so_ext, ar, ar_flags = get_config_vars('CC', 'CXX', 'OPT', 'CFLAGS', 'CCSHARED', 'LDSHARED', 'SO', 'AR', 'ARFLAGS')
        newcc = None
        if 'CC' in os.environ:
            newcc = os.environ['CC']
        elif sys.platform == 'darwin' and cc == 'gcc-4.2':
            if _USE_CLANG is None:
                from distutils import log
                from subprocess import Popen, PIPE
                p = Popen('! type gcc-4.2 && type clang && exit 2', shell=True, stdout=PIPE, stderr=PIPE)
                p.wait()
                if p.returncode == 2:
                    _USE_CLANG = True
                    log.warn('gcc-4.2 not found, using clang instead')
                else:
                    _USE_CLANG = False
            if _USE_CLANG:
                newcc = 'clang'
        if newcc:
            if sys.platform == 'darwin' and 'LDSHARED' not in os.environ and ldshared.startswith(cc):
                ldshared = newcc + ldshared[len(cc):]
            cc = newcc
        if 'CXX' in os.environ:
            cxx = os.environ['CXX']
        if 'LDSHARED' in os.environ:
            ldshared = os.environ['LDSHARED']
        if 'CPP' in os.environ:
            cpp = os.environ['CPP']
        else:
            cpp = cc + ' -E'
        if 'LDFLAGS' in os.environ:
            ldshared = ldshared + ' ' + os.environ['LDFLAGS']
        if 'CFLAGS' in os.environ:
            cflags = opt + ' ' + os.environ['CFLAGS']
            ldshared = ldshared + ' ' + os.environ['CFLAGS']
        if 'CPPFLAGS' in os.environ:
            cpp = cpp + ' ' + os.environ['CPPFLAGS']
            cflags = cflags + ' ' + os.environ['CPPFLAGS']
            ldshared = ldshared + ' ' + os.environ['CPPFLAGS']
        if 'AR' in os.environ:
            ar = os.environ['AR']
        if 'ARFLAGS' in os.environ:
            archiver = ar + ' ' + os.environ['ARFLAGS']
        else:
            archiver = ar + ' ' + ar_flags
        cc_cmd = cc + ' ' + cflags
        compiler.set_executables(preprocessor=cpp, compiler=cc_cmd, compiler_so=cc_cmd + ' ' + ccshared, compiler_cxx=cxx, linker_so=ldshared, linker_exe=cc, archiver=archiver)
        compiler.shared_lib_extension = so_ext


def get_config_h_filename():
    if python_build:
        if os.name == 'nt':
            inc_dir = os.path.join(project_base, 'PC')
        else:
            inc_dir = project_base
    else:
        inc_dir = get_python_inc(plat_specific=1)
    if get_python_version() < '2.2':
        config_h = 'config.h'
    else:
        config_h = 'pyconfig.h'
    return os.path.join(inc_dir, config_h)


def get_makefile_filename():
    if python_build:
        return os.path.join(os.path.dirname(sys.executable), 'Makefile')
    lib_dir = get_python_lib(plat_specific=1, standard_lib=1)
    return os.path.join(lib_dir, 'config', 'Makefile')


def parse_config_h(fp, g = None):
    if g is None:
        g = {}
    define_rx = re.compile('#define ([A-Z][A-Za-z0-9_]+) (.*)\n')
    undef_rx = re.compile('/[*] #undef ([A-Z][A-Za-z0-9_]+) [*]/\n')
    while 1:
        line = fp.readline()
        if not line:
            break
        m = define_rx.match(line)
        if m:
            n, v = m.group(1, 2)
            try:
                v = int(v)
            except ValueError:
                pass

            g[n] = v
        else:
            m = undef_rx.match(line)
            if m:
                g[m.group(1)] = 0

    return g


_variable_rx = re.compile('([a-zA-Z][a-zA-Z0-9_]+)\\s*=\\s*(.*)')
_findvar1_rx = re.compile('\\$\\(([A-Za-z][A-Za-z0-9_]*)\\)')
_findvar2_rx = re.compile('\\${([A-Za-z][A-Za-z0-9_]*)}')

def parse_makefile(fn, g = None):
    from distutils.text_file import TextFile
    fp = TextFile(fn, strip_comments=1, skip_blanks=1, join_lines=1)
    if g is None:
        g = {}
    done = {}
    notdone = {}
    while 1:
        line = fp.readline()
        if line is None:
            break
        m = _variable_rx.match(line)
        if m:
            n, v = m.group(1, 2)
            v = v.strip()
            tmpv = v.replace('$$', '')
            if '$' in tmpv:
                notdone[n] = v
            else:
                try:
                    v = int(v)
                except ValueError:
                    done[n] = v.replace('$$', '$')
                else:
                    done[n] = v

    while notdone:
        for name in notdone.keys():
            value = notdone[name]
            m = _findvar1_rx.search(value) or _findvar2_rx.search(value)
            if m:
                n = m.group(1)
                found = True
                if n in done:
                    item = str(done[n])
                elif n in notdone:
                    found = False
                elif n in os.environ:
                    item = os.environ[n]
                else:
                    done[n] = item = ''
                if found:
                    after = value[m.end():]
                    value = value[:m.start()] + item + after
                    if '$' in after:
                        notdone[name] = value
                    else:
                        try:
                            value = int(value)
                        except ValueError:
                            done[name] = value.strip()
                        else:
                            done[name] = value

                        del notdone[name]
            else:
                del notdone[name]

    fp.close()
    for k, v in done.items():
        if isinstance(v, str):
            done[k] = v.strip()

    g.update(done)
    return g


def expand_makefile_vars(s, vars):
    while 1:
        m = _findvar1_rx.search(s) or _findvar2_rx.search(s)
        if m:
            beg, end = m.span()
            s = s[0:beg] + vars.get(m.group(1)) + s[end:]
        else:
            break

    return s


_config_vars = None

def _init_posix():
    global _config_vars
    g = {}
    try:
        filename = get_makefile_filename()
        parse_makefile(filename, g)
    except IOError as msg:
        my_msg = 'invalid Python installation: unable to open %s' % filename
        if hasattr(msg, 'strerror'):
            my_msg = my_msg + ' (%s)' % msg.strerror
        raise DistutilsPlatformError(my_msg)

    try:
        filename = get_config_h_filename()
        parse_config_h(file(filename), g)
    except IOError as msg:
        my_msg = 'invalid Python installation: unable to open %s' % filename
        if hasattr(msg, 'strerror'):
            my_msg = my_msg + ' (%s)' % msg.strerror
        raise DistutilsPlatformError(my_msg)

    if python_build:
        g['LDSHARED'] = g['BLDSHARED']
    elif get_python_version() < '2.1':
        if sys.platform == 'aix4':
            python_lib = get_python_lib(standard_lib=1)
            ld_so_aix = os.path.join(python_lib, 'config', 'ld_so_aix')
            python_exp = os.path.join(python_lib, 'config', 'python.exp')
            g['LDSHARED'] = '%s %s -bI:%s' % (ld_so_aix, g['CC'], python_exp)
        elif sys.platform == 'beos':
            python_lib = get_python_lib(standard_lib=1)
            linkerscript_path = string.split(g['LDSHARED'])[0]
            linkerscript_name = os.path.basename(linkerscript_path)
            linkerscript = os.path.join(python_lib, 'config', linkerscript_name)
            g['LDSHARED'] = '%s -L%s/lib -lpython%s' % (linkerscript, PREFIX, get_python_version())
    _config_vars = g


def _init_nt():
    global _config_vars
    g = {}
    g['LIBDEST'] = get_python_lib(plat_specific=0, standard_lib=1)
    g['BINLIBDEST'] = get_python_lib(plat_specific=1, standard_lib=1)
    g['INCLUDEPY'] = get_python_inc(plat_specific=0)
    g['SO'] = '.pyd'
    g['EXE'] = '.exe'
    g['VERSION'] = get_python_version().replace('.', '')
    g['BINDIR'] = os.path.dirname(os.path.abspath(sys.executable))
    _config_vars = g


def _init_os2():
    global _config_vars
    g = {}
    g['LIBDEST'] = get_python_lib(plat_specific=0, standard_lib=1)
    g['BINLIBDEST'] = get_python_lib(plat_specific=1, standard_lib=1)
    g['INCLUDEPY'] = get_python_inc(plat_specific=0)
    g['SO'] = '.pyd'
    g['EXE'] = '.exe'
    _config_vars = g


def get_config_vars(*args):
    global _config_vars
    if _config_vars is None:
        func = globals().get('_init_' + os.name)
        if func:
            func()
        else:
            _config_vars = {}
        _config_vars['prefix'] = PREFIX
        _config_vars['exec_prefix'] = EXEC_PREFIX
        if sys.platform == 'darwin':
            kernel_version = os.uname()[2]
            major_version = int(kernel_version.split('.')[0])
            if major_version < 8:
                for key in ('LDFLAGS', 'BASECFLAGS', 'LDSHARED', 'CFLAGS', 'PY_CFLAGS', 'BLDSHARED'):
                    flags = _config_vars[key]
                    flags = re.sub('-arch\\s+\\w+\\s', ' ', flags)
                    flags = re.sub('-isysroot [^ \t]*', ' ', flags)
                    _config_vars[key] = flags

            else:
                if 'ARCHFLAGS' in os.environ:
                    arch = os.environ['ARCHFLAGS']
                    for key in ('LDFLAGS', 'BASECFLAGS', 'LDSHARED', 'CFLAGS', 'PY_CFLAGS', 'BLDSHARED'):
                        flags = _config_vars[key]
                        flags = re.sub('-arch\\s+\\w+\\s', ' ', flags)
                        flags = flags + ' ' + arch
                        _config_vars[key] = flags

                m = re.search('-isysroot\\s+(\\S+)', _config_vars['CFLAGS'])
                if m is not None:
                    sdk = m.group(1)
                    if not os.path.exists(sdk):
                        for key in ('LDFLAGS', 'BASECFLAGS', 'LDSHARED', 'CFLAGS', 'PY_CFLAGS', 'BLDSHARED'):
                            flags = _config_vars[key]
                            flags = re.sub('-isysroot\\s+\\S+(\\s|$)', ' ', flags)
                            _config_vars[key] = flags

    if args:
        vals = []
        for name in args:
            vals.append(_config_vars.get(name))

        return vals
    else:
        return _config_vars


def get_config_var(name):
    return get_config_vars().get(name)
