#Embedded file name: dropbox/mac/helper_installer.py
import errno
import grp
import os
import re
import shutil
import stat
import tarfile
import tempfile
from subprocess32 import PIPE, Popen
import build_number
from .internal import get_resources_dir, groupname_to_gid, raise_application, username_to_uid
from dropbox.dropbox_helper_installer import read_header_info, verify_signature
from dropbox.i18n import trans
from dropbox.trace import unhandled_exc_handler, TRACE
from pymac.helpers.authorization import AuthorizationCanceled, OSStatusError, request_authorization_from_user_and_run
from pymac.helpers.process import find_instances
BUILD_KEY = build_number.BUILD_KEY
BASE_HELPERS_DIR = '/Library/DropboxHelperTools'
REL_HELPERS_DIR = '%s_u%d' % (BUILD_KEY, os.getuid())
HELPERS_DIR = os.path.join(BASE_HELPERS_DIR, REL_HELPERS_DIR)
HELPER_INSTALLER_PATH = '/Library/DropboxHelperTools/DropboxHelperInstaller'

class InstallError(Exception):
    pass


class Digestor(object):

    def __init__(self, f, info):
        self.f = f
        self.end = info['end']
        self.digest = info['digest']
        self.cur = 0

    def read(self, n):
        data = self.f.read(min(n, self.end - self.cur))
        self.cur += len(data)
        self.digest.update(data)
        return data

    def finish(self):
        while self.cur != self.end:
            if not self.read(10240):
                raise Exception('No more data')


def verify_and_extract_installer(fn, path):
    with open(fn, 'r') as f:
        info = read_header_info(f)
        digestor = Digestor(f, info)
        t = tarfile.open(fileobj=digestor, mode='r|*')
        exf = t.extractall(path=path)
        digestor.finish()
        verify_signature(info)


def install_dropbox_helper_installer(auth_text = None, keep_focus = False):
    tmpdir = tempfile.mkdtemp()
    try:
        tgz = 'DropboxHelperInstaller.tgz'
        tgz_full = os.path.join(get_resources_dir(), tgz).encode('utf8') if hasattr(build_number, 'frozen') else os.path.abspath('mac_dependencies/' + tgz)
        verify_and_extract_installer(tgz_full, tmpdir)
        installer_path = os.path.join(tmpdir, 'DropboxHelperInstaller')
        os.chmod(installer_path, stat.S_IRWXU)
        try:
            TRACE('Requesting authorization from user to install DropboxHelperInstaller')
            f = request_authorization_from_user_and_run(installer_path, ['install', BUILD_KEY, tgz_full], auth_text=auth_text)
        except AuthorizationCanceled:
            user_refused_to_enter_password = True
            return False
        except OSStatusError:
            TRACE('!! error in authorization os.path.exists(%r) = %r', installer_path, os.path.exists(installer_path))
            raise
        else:
            if keep_focus:
                raise_application()

        pid = -1
        ret = None
        for l in f:
            TRACE('DropboxHelperInstaller log:%s', l.strip())
            if pid == -1:
                m = re.match('\\<pid\\>(?P<pid>\\d+)\\</pid\\>\\n', l)
                if m:
                    pid = int(m.group('pid'))
            if ret is None:
                if l == '<ok>\n':
                    ret = 1

        if pid != -1:
            os.waitpid(pid, 0)
        if ret != 1:
            raise Exception('Error in DropboxHelperInstaller')
        return verify_helper_installer(True)
    except Exception:
        unhandled_exc_handler()
        return False
    finally:
        shutil.rmtree(tmpdir)


def check_perm(st, uid, gid, mode):
    return st.st_uid == uid and (gid is None or st.st_gid in gid) and stat.S_IMODE(st.st_mode) == mode


def verify_helper_installer(report_error = False):
    try:
        st = os.stat(BASE_HELPERS_DIR)
        if not stat.S_ISDIR(st.st_mode) or not check_perm(st, 0, None, 493) and not check_perm(st, 0, [grp.getgrnam('admin').gr_gid, 0], 509):
            if report_error:
                raise Exception('Bad Perms on %s %r' % (BASE_HELPERS_DIR, st))
            else:
                raise Exception('Pre:Bad Perms on %s %r' % (BASE_HELPERS_DIR, st))
        st = os.stat(HELPER_INSTALLER_PATH)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 2377:
            if report_error:
                raise Exception('Bad Perms on %s %r' % (HELPER_INSTALLER_PATH, st))
            else:
                raise Exception('Pre:Bad Perms on %s %r' % (BASE_HELPERS_DIR, st))
        install_dropbox_helper('DropboxHelperInstaller')
        return True
    except OSError as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
        return False
    except Exception:
        unhandled_exc_handler()
        return False


def get_package_location(package):
    if hasattr(build_number, 'frozen'):
        return os.path.join(get_resources_dir(), package + '.tgz').encode('utf8')
    return os.path.abspath('mac_dependencies/' + package + '.tgz')


def install_dropbox_helper(package = None, fullpath = None, tmp = False):
    if not os.path.exists(HELPER_INSTALLER_PATH):
        raise InstallError('no installer')
    assert package or fullpath
    if not fullpath:
        fullpath = get_package_location(package)
    TRACE('Installing %s', package or fullpath)
    cmd = 'install-tmp' if tmp else 'install'
    p = Popen([HELPER_INSTALLER_PATH,
     cmd,
     BUILD_KEY,
     fullpath], stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        if out:
            TRACE('stdout: %s', out)
        if err:
            TRACE('stderr: %s', err)
        raise InstallError('Installer returned %d' % p.returncode)
    if tmp:
        path = None
        for l in out.split('\n'):
            m = re.match('\\<path\\>(?P<path>.+)\\</path\\>', l)
            if m:
                path = m.group('path')

        if path:
            return os.path.join(path, REL_HELPERS_DIR)
        raise InstallError('no path')


def install_dropbox_helpers_with_fallback(b_perm_info):
    for b, info in b_perm_info.iteritems():
        b_path = os.path.join(HELPERS_DIR, b).encode('utf8')
        if 'kill' in info:
            for pid in find_instances(b_path, other_users=True, unhandled_exc_handler=unhandled_exc_handler):
                try:
                    os.kill(pid, info['kill'])
                    TRACE('killed old running %s (pid %d)' % (b, pid))
                except Exception:
                    unhandled_exc_handler()

        try:
            install_dropbox_helper(b)
        except Exception:
            if hasattr(build_number, 'frozen'):
                unhandled_exc_handler()
                return False
            try:
                tgz = get_package_location(b)
                msg = trans(u'Manually installing %s') % (tgz,)
                f = request_authorization_from_user_and_run('/usr/bin/tar', ['xzvf',
                 tgz,
                 '-C',
                 HELPERS_DIR], auth_text=msg)
                TRACE('Manual Installer: %s', f.read())
                f.close()
            except Exception:
                unhandled_exc_handler()
                TRACE("!!Failed to manually install.  We're still trusting the binaries that are installed")

        else:
            st = os.stat(b_path)
            TRACE("OK, now %s's stat: uid %d, gid %d, mode %o" % (b_path,
             st.st_uid,
             st.st_gid,
             st.st_mode))
            if 'mode' in info:
                assert st.st_mode & info['mode'] == info['mode']
            if 'user' in info:
                assert st.st_uid == username_to_uid(info['user'])
            if 'group' in info:
                assert st.st_gid == groupname_to_gid(info['group'])

    return True
