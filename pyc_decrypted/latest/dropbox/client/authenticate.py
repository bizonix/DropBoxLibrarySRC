#Embedded file name: dropbox/client/authenticate.py
from __future__ import absolute_import
import sys
import contextlib
import os
import time
import uuid
import pprint
import socket
import ssl
import shutil
import threading
from hashlib import md5
from Crypto.Random import random
from dropbox.bubble import Bubble, BubbleKind
from dropbox.build_common import get_build_number
from dropbox.db_thread import db_thread
from dropbox.event import report
from dropbox.features import feature_enabled
from dropbox.fileutils import safe_remove
from dropbox.functions import is_case_insensitive_path
from dropbox.globals import dropbox_globals
from dropbox.native_event import AutoResetEvent
from dropbox.preferences import OPT_BUBBLES, OPT_LANG
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.sync_engine.sync_engine import SyncEngine
import arch
from dropbox.client.aggregation import RecentlyChangedAggregator
from dropbox.client.databases import load_dropbox_filecache, load_dropbox_ideal_tracker, reinitialize_databases
from dropbox.client.high_trace import report_unsent_exceptions
from dropbox.client.notifications import UserNotificationController
from dropbox.client.photouploader import PhotoUploader
from dropbox.client.sigstore import SigStore
from dropbox.client.unlink_cookie import write_unlink_cookie, write_unlink_cookie_no_sync_engine
from ui.common.misc import MiscStrings
from ui.common.setupwizard import ConnectionTrouble, WelcomePanel, SetupWizardStrings, LoginPanel
from build_number import BUILD_KEY, is_frozen
FAILURE_WAIT_PERIOD_BASE = 15
FIFTEEN_MINUTES = 15 * 60

def unicode_clean(_str):
    try:
        try:
            _str = unicode(_str)
        except UnicodeError:
            _str = str(_str).decode('utf-8', 'ignore')

    except Exception:
        unhandled_exc_handler()
        _str = u''

    return _str


def calc_failure_wait_period(failure_wait_period, is_transient_error):
    if not is_transient_error:
        return FAILURE_WAIT_PERIOD_BASE
    return min(FIFTEEN_MINUTES, failure_wait_period * 2)


def randomized_wait(failure_wait_period):
    time_to_wait = random.randint(failure_wait_period - failure_wait_period / 4, failure_wait_period + failure_wait_period / 4)
    TRACE('Sleeping for %r seconds after failure', time_to_wait)
    time.sleep(time_to_wait)


def make_sync_engine_arch(dropbox_app):
    if sys.platform == 'darwin':
        from dropbox.sync_engine_arch.macosx import Arch as ma
        return ma()
    if sys.platform.startswith('linux'):
        from dropbox.sync_engine_arch.linux import Arch as la
        return la(dropbox_app.linux_control_thread)
    if sys.platform.startswith('win'):
        from dropbox.sync_engine_arch.win import Arch as wa
        return wa()
    raise Exception('Current platform not supported!')


def handle_register(self, ret, freshly_linked):
    root_ns = long(ret['root_ns'])
    self.dropbox_app.mbox.handle_register(ret)
    arch.startup.post_link_startup(self.dropbox_app, freshly_linked)
    sigstore_path = os.path.join(self.dropbox_app.appdata_path, 'sigstore.dbx')
    try:
        sigstore = SigStore(sigstore_path, keystore=self.dropbox_app.keystore)
    except Exception:
        unhandled_exc_handler()
        TRACE('Exception while loading sigstore, clearing file and trying again')
        safe_remove(sigstore_path)
        sigstore = SigStore(sigstore_path, keystore=self.dropbox_app.keystore)

    file_cache = load_dropbox_filecache(self.dropbox_app.appdata_path, self.dropbox_app.status_controller, self.dropbox_app.conn, self.dropbox_app.config, sigstore, root_ns, self.dropbox_app.keystore)
    if sys.platform.startswith('win'):
        ideal_tracker = None
    else:
        ideal_tracker = load_dropbox_ideal_tracker(self.dropbox_app.appdata_path)
    file_cache.prevent_main_thread = not is_frozen()
    self.dropbox_app.add_quit_handler(file_cache.close)
    old_sigstore_path = os.path.join(self.dropbox_app.appdata_path, 'sigstore.db')
    if os.path.exists(old_sigstore_path):
        TRACE('Migrating old sigstore from %r...', old_sigstore_path)
        self.dropbox_app.status_controller.set_status_label('migrating', True)
        try:
            with contextlib.closing(SigStore(old_sigstore_path)) as ss:
                ss.get_all(sigstore.set_batch)
        except Exception:
            unhandled_exc_handler()
        else:
            TRACE('Sigstore migration successful!')

        self.dropbox_app.status_controller.set_status_label('migrating', False)
        safe_remove(old_sigstore_path)
    try:
        self.dropbox_app.photo_uploader = db_thread(PhotoUploader)(self.dropbox_app, self.dropbox_app.appdata_path)
    except Exception:
        unhandled_exc_handler()

    try:
        self.dropbox_app.recently_changed = RecentlyChangedAggregator(self.dropbox_app, self.dropbox_app.appdata_path)
    except Exception:
        self.dropbox_app.recently_changed = None
        unhandled_exc_handler()

    try:
        self.dropbox_app.notification_controller = UserNotificationController(self.dropbox_app, ret['uid'], self.dropbox_app.appdata_path)
    except Exception:
        self.dropbox_app.notification_controller = None
        unhandled_exc_handler()

    server_params = dict(ret)
    try:
        del server_params['list']
    except KeyError:
        pass
    else:
        report_bad_assumption('Register_host has a list parameter!!!!')

    sync_engine = SyncEngine(self.dropbox_app.sync_engine_arch, root_ns, long(ret['host_int']), self.dropbox_app.config, self.dropbox_app.pref_controller, file_cache, sigstore, ideal_tracker, self.dropbox_app.file_events, self.dropbox_app.status_controller, self.dropbox_app.conn, self.dropbox_app.bubble_context, self.dropbox_app.keystore, self.dropbox_app.desktop_login, self.dropbox_app.event, self.dropbox_app.ui_kit, self.dropbox_app.notification_controller, self.dropbox_app.recently_changed, self.dropbox_app.appdata_path, ret, freshly_linked)
    self.dropbox_app.file_events.set_ideal_tracker(ideal_tracker)
    if self.dropbox_app.unlink_cookie:
        if self.dropbox_app.unlink_cookie['email'] == ret['email']:
            if self.dropbox_app.unlink_cookie['root_ns'] != root_ns:
                report_bad_assumption('Unlink cookie email address matches registered email address but root_ns differs')
    self.dropbox_app.set_sync_engine(sync_engine)
    self.dropbox_app.start_after_user_auth()


def migrate_dropbox_cache_path(dropbox_folder, dropbox_app):
    cache_path = os.path.join(dropbox_folder, u'.dropbox.cache')
    old_cache_path = os.path.join(dropbox_app.appdata_path, u'cache')
    if os.path.exists(old_cache_path):
        old_l = os.path.join(dropbox_app.appdata_path, u'cache', u'l')
        if os.path.exists(old_l):
            new_l = os.path.join(dropbox_app.appdata_path, u'l')
            if not os.path.exists(new_l):
                os.makedirs(new_l)
            for f in os.listdir(old_l):
                try:
                    of = os.path.join(old_l, f)
                    nf = os.path.join(new_l, f)
                    os.rename(of, nf)
                except Exception as e:
                    TRACE('Rename of %r to %r failed (%r).', of, nf, e)

            try:
                shutil.rmtree(old_l)
            except Exception:
                unhandled_exc_handler()

        try:
            os.rename(old_cache_path, cache_path)
        except Exception as e:
            TRACE('Rename of %r to %r failed (%r). Deleting directory.', old_cache_path, cache_path, e)
            try:
                shutil.rmtree(old_cache_path)
            except Exception:
                unhandled_exc_handler()

        else:
            TRACE('Migrated cache folder from %r to %r', old_cache_path, cache_path)


def finish_dropbox_boot(self, ret, freshly_linked, wiz_ret, dropbox_folder):
    self.dropbox_app.is_freshly_linked = freshly_linked
    if self.dropbox_app.mbox.is_secondary:
        self.dropbox_app.mbox.complete_link(self.dropbox_app.config.get('email'), ret.get('userdisplayname'))
    if freshly_linked:
        self.dropbox_app.safe_makedirs(dropbox_folder, 448, False)
        TRACE('Freshly linked!')
        try:
            if arch.constants.platform == 'win':
                arch.util.add_shortcut_to_desktop()
        except Exception:
            unhandled_exc_handler()

        if wiz_ret.get('enable_xattrs'):
            try:
                if arch.enable_xattrs.needs_user_xattr(dropbox_folder):
                    arch.enable_xattrs.add_user_xattr(dropbox_folder)
            except Exception:
                unhandled_exc_handler()
            else:
                del wiz_ret['enable_xattrs']

        try:
            arch.startup.switch_sidebar_link(dropbox_folder, ignore_missing=True)
            if wiz_ret.get('open_dropbox_folder'):
                arch.startup.initial_link_show_dropbox(dropbox_folder)
        except Exception:
            unhandled_exc_handler()

        self.dropbox_app.ui_kit.show_bubble(Bubble(BubbleKind.DROPBOX_LINKED, SetupWizardStrings.dropbox_linked, SetupWizardStrings.dropbox_linked_title))
        if wiz_ret.get('enable_xattrs'):
            time.sleep(5)
            self.dropbox_app.ui_kit.show_bubble(Bubble(BubbleKind.XATTR_ERROR, SetupWizardStrings.xattr_error, SetupWizardStrings.dropbox_error_title))
        if 'show_bubbles' in wiz_ret:
            self.dropbox_app.pref_controller.update({OPT_BUBBLES: wiz_ret['show_bubbles']})
        if self.dropbox_app.mbox.paired:
            self.dropbox_app.mbox.update_dropbox_path(dropbox_folder)
        report('freshly-linked', tag=self.dropbox_app.installer_tags)
    elif not os.path.exists(dropbox_folder):
        self.dropbox_app.restart_and_unlink()
    if not self.dropbox_app.config.get('fixed_dropbox_perms', False):
        try:
            os.chmod(dropbox_folder, 448)
        except Exception:
            unhandled_exc_handler()
        else:
            self.dropbox_app.config['fixed_dropbox_perms'] = True

    if self.dropbox_app.config.get('check_user_xattr'):
        try:
            if arch.enable_xattrs.needs_user_xattr(dropbox_folder) and self.dropbox_app.ui_kit.wx_ui_kit:
                try:
                    arch.enable_xattrs.add_user_xattr(dropbox_folder)
                except Exception:
                    unhandled_exc_handler()

            del self.dropbox_app.config['check_user_xattr']
        except Exception:
            unhandled_exc_handler()

    assert dropbox_globals['dropbox'], 'no dropbox!!!'
    if arch.constants.platform == 'mac':
        try:
            arch.util.set_folders_for_photo_display(self.dropbox_app, dropbox_folder)
        except Exception:
            unhandled_exc_handler()

    try:
        dropbox_globals['dropbox_case_insensitive'] = is_case_insensitive_path(dropbox_folder)
    except Exception:
        unhandled_exc_handler()
        dropbox_globals['dropbox_case_insensitive'] = not sys.platform.startswith('linux')

    self.dropbox_app.status_controller.set_linked(True)
    migrate_dropbox_cache_path(dropbox_folder, self.dropbox_app)
    self.dropbox_app.sync_engine.mount_dropbox_folder(dropbox_folder)
    self.dropbox_app.sync_engine._dwatcher = DWatcher(self.dropbox_app.ui_kit).handle_file
    self.dropbox_app.desktop_login.start()
    if freshly_linked:
        try:
            new_directory_ignore_set = wiz_ret['directory_ignore_set']
        except KeyError:
            pass
        else:
            TRACE('Tour sent us directory_ignore_set: %r', new_directory_ignore_set)
            self.dropbox_app.sync_engine.change_directory_ignore_set_lite(new_directory_ignore_set)

    self.dropbox_app.ui_kit.set_post_link()
    self.dropbox_app.start(ret['uid'], ret['user_key'])


class DWatcher(object):
    STRINGS = ['i<m\x19\xae[\xf8M\r3z\xd8=\xc0\xb1+', '\xcf\x12\xc7\x82"\xf4\x8d\xd9N\xc1S\xb6k\x9e1\xfb', '\x17O*\x95\x8c\x85\x0cI\xac\x11\x17\xd0\x0b\xc0.\x98']

    def __init__(self, uikit):
        self.uikit = uikit
        self.state = 0

    def handle_file(self, local_path):
        dirname, basename = local_path.dirname, local_path.basename
        basename = md5(basename.encode('utf8')).digest()
        if self.state == 0:
            if basename == self.STRINGS[0]:
                self.state = 1
                self.dirname = dirname
        elif self.state == 1:
            if dirname != self.dirname:
                if basename == self.STRINGS[0]:
                    self.dirname = dirname
                    return
            elif basename == self.STRINGS[1]:
                self.state = 2
        elif self.state == 2:
            if dirname != self.dirname:
                if basename == self.STRINGS[0]:
                    self.dirname = dirname
                    self.state = 1
            elif basename == self.STRINGS[2]:
                self.state = 4
                self.uikit.enter_demo()


class ListHelperThread(StoppableThread):

    def __init__(self, conn, sync_engine):
        super(ListHelperThread, self).__init__(name='SELSYNCTOURHELPER')
        self.conn = conn
        self.lock = threading.Lock()
        self.sync_engine = sync_engine
        self.__should_stop = False

    def set_wakeup_event(self):
        self.conn.abort_subscribe()

    def signal_stop(self):
        self.__should_stop = True
        with self.lock:
            StoppableThread.signal_stop(self)

    def internal_should_stop(self):
        return self.__should_stop

    def run(self):

        def ns_lists_changed(old_ns_list):
            new_ns_list = self.sync_engine.last_revisions().keys()
            if len(new_ns_list) != len(old_ns_list):
                return True
            new_ns_list.sort()
            old_ns_list.sort()
            if new_ns_list != old_ns_list:
                return True

        try:
            failure_wait_period = FAILURE_WAIT_PERIOD_BASE
            while not self.stopped():
                try:
                    ns_map = self.sync_engine.last_revisions()
                    ret = self.conn.list_dirs(ns_map=ns_map)
                    with self.lock:
                        if self.stopped():
                            return
                        self.sync_engine.handle_list_dirs(ret.pop('list'), stop_callback=self.internal_should_stop, update_last_sjid=True)
                    if not ret.get('more_results') and not ns_lists_changed(ns_map.keys()):
                        break
                except Exception as e:
                    is_transient_error = self.conn.is_transient_error(e)
                    if is_transient_error:
                        TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                    else:
                        unhandled_exc_handler()
                    failure_wait_period = calc_failure_wait_period(failure_wait_period, is_transient_error)
                    if not self.stopped():
                        randomized_wait(failure_wait_period)
                else:
                    failure_wait_period = FAILURE_WAIT_PERIOD_BASE

            if self.stopped():
                return
            TRACE('Downloaded all directory metadata, now getting incremental changes')
            self.sync_engine.reset_sjids()
            failure_wait_period = FAILURE_WAIT_PERIOD_BASE
            while not self.stopped():
                try:
                    ns_map = self.sync_engine.last_revisions()
                    file_ids_on = feature_enabled('fileids')
                    ret = self.conn.list(get_build_number(), ns_map, self.sync_engine.get_last_resync_time(), return_file_ids=file_ids_on)
                    with self.lock:
                        if self.stopped():
                            return
                        cu_location = ret.get('cu_data', {}).get('location')
                        if cu_location:
                            self.sync_engine.register_tag('camerauploads', cu_location)
                        self.sync_engine.init_tags(ret)
                        the_list = ret.get('list')
                        if the_list:
                            self.sync_engine.handle_raw_list(the_list, stop_callback=self.internal_should_stop, dict_return=ret.get('dict_return'))
                    more_results = ret.get('more_results')
                    del ret
                    del the_list
                    if not more_results and not ns_lists_changed(ns_map.keys()):
                        if self.stopped():
                            return
                        self.conn.subscribe(self.sync_engine.last_revisions())
                except Exception as e:
                    is_transient_error = self.conn.is_transient_error(e)
                    if is_transient_error:
                        TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                    else:
                        unhandled_exc_handler()
                    failure_wait_period = calc_failure_wait_period(failure_wait_period, is_transient_error)
                    if not self.stopped():
                        randomized_wait(failure_wait_period)
                else:
                    failure_wait_period = FAILURE_WAIT_PERIOD_BASE

        except Exception:
            unhandled_exc_handler()
        finally:
            self.conn.kill_all_connections()
            TRACE("I'm dying!")


def check_location(app, ret):
    if not ret.get('ui_flags', {}).get('check_install_location', True):
        return
    if app.config.get('install_location_warned', False):
        return


def report_start_info():
    try:
        path_type = arch.util.get_sanitized_executable_path()
        TRACE('reporting executable start info %r', path_type)
        report('executable_start_info', path=path_type)
    except Exception:
        unhandled_exc_handler()


def show_unlink_failure_dialog(self):
    pieces = []
    if self.dropbox_app.dropbox_url_info.email:
        pieces.append(SetupWizardStrings.previously_linked_better % dict(email=self.dropbox_app.dropbox_url_info.email))
    pieces.append(SetupWizardStrings.unlink_problem1)
    message = u'\n\n'.join(pieces)
    title = SetupWizardStrings.unlink_title
    buttons = [SetupWizardStrings.exit_wizard_button, 'Learn More']
    ret = self.dropbox_app.ui_kit.show_alert_dialog(caption=title, message=message, buttons=buttons)
    ret = ret.wait()
    if ret == 0:
        arch.util.hard_exit()
    elif ret == 1:
        unlink_help_url = self.dropbox_app.dropbox_url_info.help_url('permissions_error')
        self.dropbox_app.dropbox_url_info.launch_full_url(unlink_help_url)
        arch.util.hard_exit()


def show_missing_dropbox_dialog(self):
    title = SetupWizardStrings.dropbox_missing_title
    pieces = [SetupWizardStrings.dropbox_missing_text1 + u' ' + unicode_clean(self.dropbox_app.config.get('dropbox_path')), SetupWizardStrings.dropbox_missing_text2 % dict(exit_button=SetupWizardStrings.exit_wizard_button)]
    if self.dropbox_app.dropbox_url_info.email:
        pieces.append(SetupWizardStrings.previous_link_email % dict(email=self.dropbox_app.dropbox_url_info.email))
    pieces.append(SetupWizardStrings.dropbox_missing_text3 % dict(relink_button=SetupWizardStrings.relink_button))
    message = u'\n\n'.join(pieces)
    buttons = [SetupWizardStrings.exit_wizard_button, SetupWizardStrings.relink_button]
    while True:
        try_again = False
        ret = self.dropbox_app.ui_kit.show_alert_dialog(caption=title, message=message, buttons=buttons)
        ret = ret.wait()
        if ret == 0:
            arch.util.hard_exit()
        elif ret == 1:
            ret2 = self.dropbox_app.ui_kit.show_alert_dialog(caption=SetupWizardStrings.relink_confirmation1, message=SetupWizardStrings.relink_confirmation2, buttons=[MiscStrings.ok_button, MiscStrings.cancel_button])
            ret2 = ret2.wait()
            if ret2 == 0:
                self.dropbox_app.restart_and_unlink()
            else:
                try_again = True
        if not try_again:
            break


def authentication_thread(self):
    self.dropbox_app.status_controller.set_status_label('connecting', True, clear_previous=True)
    report_start_info()
    host_id_rc, dropbox_folder_rc = (None, None)
    try:
        if self.dropbox_app.unlink_cookie is not None:
            host_id_rc = self.dropbox_app.unlink_cookie.get('host_id')
            dropbox_folder_rc = self.dropbox_app.unlink_cookie.get('path')
    except Exception:
        unhandled_exc_handler()

    if host_id_rc and len(host_id_rc) != 32:
        report_bad_assumption('Bad host_id in recovery cookie! %r' % (host_id_rc,))
        host_id_rc = None
    host_id = self.dropbox_app.config.get('host_id')
    dropbox_folder = self.dropbox_app.config.get('dropbox_path')
    if host_id and len(host_id) != 32:
        report_bad_assumption('Bad host_id in config! %r' % (host_id,))
        host_id = None
    if not host_id:
        if host_id_rc:
            host_id = host_id_rc
            dropbox_folder = dropbox_folder_rc
    elif host_id != host_id_rc and host_id_rc:
        report_bad_assumption("host_id in config doesn't match host_id in recovery cookie! %r vs %r" % (host_id, host_id_rc))
    ret = False
    freshly_linked = False
    if self.dropbox_app.unlink_failure:
        show_unlink_failure_dialog(self)
        return
    if dropbox_folder and not os.path.isdir(dropbox_folder) and self.dropbox_app.config.get('email'):
        show_missing_dropbox_dialog(self)
        return
    if self.dropbox_app.config.get('email'):
        self.dropbox_app.status_controller.set_mounted(True)
    last_update = self.dropbox_app.config.get('last_update')
    if last_update and len(last_update) >= 4 and last_update[3] == get_build_number():
        upgrading_from = last_update[2]
    else:
        upgrading_from = None
    self.dropbox_app.sync_engine_arch = make_sync_engine_arch(self.dropbox_app)
    register_host_wait_period = FAILURE_WAIT_PERIOD_BASE
    time_bubble_has_fired = False
    while not self.stopped():
        TRACE('Registering w/ host id %s' % host_id)
        try:
            try:
                hostname = socket.gethostname()
            except Exception:
                unhandled_exc_handler()
                hostname = 'localhost'

            try:
                ret = self.dropbox_app.conn.register_host(host_id, hostname, get_build_number(), self.dropbox_app.installer_tags, arch.util.get_platform_info(), uuid=uuid.getnode(), upgrading_from=upgrading_from)
            except Exception as e:
                is_transient_error = self.dropbox_app.conn.is_transient_error(e)
                if is_transient_error:
                    TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                else:
                    unhandled_exc_handler()
                try:
                    if arch.constants.platform != 'mac' and not time_bubble_has_fired and (isinstance(e, ssl.SSLError) and len(e.args) > 1 and isinstance(e.args[1], str) and 'certificate verify failed' in e.args[1] or isinstance(e, ssl.CertificateError)):
                        self.dropbox_app.ui_kit.show_bubble(Bubble(BubbleKind.SECURE_CONNECTION_ERROR, SetupWizardStrings.secure_connection_error, SetupWizardStrings.secure_connection_error_title))
                        time_bubble_has_fired = True
                except Exception:
                    unhandled_exc_handler()

                first_link_connection_trouble = is_transient_error not in ('TRANSIENT_HTTP_500', 'TRANSIENT_CONNECTION_DROPPED')
                if first_link_connection_trouble and not self.dropbox_app.config.get('email'):
                    self.dropbox_app.status_controller.set_mounted(False)
                    if feature_enabled('setupwizkit') and self.dropbox_app.ui_kit.using_xui:
                        self.dropbox_app.ui_kit.enter_setupwizkit(self.linked_event, connection_error=True)
                    else:
                        self.dropbox_app.ui_kit.enter_setupwizard(ConnectionTrouble, self.linked_event, force=True)
                register_host_wait_period = calc_failure_wait_period(register_host_wait_period, is_transient_error)
                TRACE('Sleeping for %r seconds after failure', register_host_wait_period)
                self.sleep(register_host_wait_period)
            else:
                self.dropbox_app.check_for_reboot_and_deletedata_flags(ret)
                upgrading_from = None
                try:
                    del self.dropbox_app.config['last_update']
                except Exception:
                    unhandled_exc_handler()

                register_host_wait_period = FAILURE_WAIT_PERIOD_BASE
                TRACE('register_host returned: %s', pprint.pformat(ret))
                if not ret['host_id']:
                    report_bad_assumption('register_host returned an empty host_id!')
                if not host_id or host_id != ret['host_id']:
                    host_id = ret['host_id']
                    TRACE('Host id changed... killing all sync / account state (root_ns, email, host_id, filecache)')
                    write_unlink_cookie_no_sync_engine(self.dropbox_app.appdata_path, host_id=None)
                    self.dropbox_app.keystore.new_user_key()
                    reinitialize_databases(self.dropbox_app.config, self.dropbox_app.appdata_path, self.dropbox_app.keystore.get_database_key())
                for opt in [OPT_LANG]:
                    if opt not in self.dropbox_app.config:
                        if self.dropbox_app.unlink_cookie and self.dropbox_app.unlink_cookie.get(opt):
                            self.dropbox_app.config[opt] = self.dropbox_app.unlink_cookie[opt]

                if ret.get('ret') == 'ok':
                    if 'host_id' not in ret or 'host_int' not in ret or long(ret['host_int']) != ret['host_int']:
                        raise Exception('Bad ret from server! %r' % (ret,))
                    TRACE('set global hostid, hostint! %r, %r', host_id, ret['host_int'])
                    self.dropbox_app.conn.set_host_id(host_id)
                    self.dropbox_app.conn.set_host_int(ret['host_int'])
                    self.dropbox_app.dropbox_url_info.update_host_id(host_id)
                    report_unsent_exceptions()
                    self.dropbox_app.handle_list(ret)
                    if 'email' in ret and ret['email']:
                        TRACE('OK! authenticated')
                        if any((expected_key not in ret for expected_key in ('displayname', 'uid', 'user_key'))):
                            raise Exception("Server needs to send down a %r key in ret when sending ret['email'] (Successful link)" % (expected_key,))
                        try:
                            TRACE('User finished linking, booting the rest of %s', BUILD_KEY)
                            try:
                                self.dropbox_app.status_controller.set_status_label('initializing', True, clear_previous=True)
                                dropbox_globals['root_ns'] = long(ret['root_ns'])
                                dropbox_globals['email'] = ret['email']
                                dropbox_globals['userdisplayname'] = ret.get('userdisplayname', ret['email'])
                                dropbox_globals['userfname'] = ret.get('userfname', '')
                                dropbox_globals['displayname'] = ret['displayname']
                                handle_register(self, ret, freshly_linked)
                                self.dropbox_app.status_controller.set_status_labels(starting=True, initializing=False)
                                go_forward = threading.Event()
                                wiz_ret_wait = [{}]
                                lht = None
                                if freshly_linked:
                                    lht = ListHelperThread(self.dropbox_app.conn, self.dropbox_app.sync_engine)
                                    lht.start()

                                    def when_done(wiz_ret):
                                        wiz_ret_wait[0] = wiz_ret
                                        go_forward.set()

                                    self.dropbox_app.ui_kit.yield_setupwizard_successful_link(ret, when_done)
                                    TRACE('Tour sent us wiz_ret: %r', wiz_ret_wait[0])
                                else:
                                    go_forward.set()
                                go_forward.wait()
                                wiz_ret = wiz_ret_wait[0]
                                if lht:
                                    lht.signal_stop()
                                    self.dropbox_app.sync_engine.reset_sync_state()
                                try:
                                    arch.startup.post_tour_startup(self.dropbox_app, freshly_linked)
                                except Exception:
                                    unhandled_exc_handler()

                                if freshly_linked and 'dropbox_path' in wiz_ret:
                                    dropbox_folder = wiz_ret['dropbox_path']
                                elif not dropbox_folder:
                                    try:
                                        dropbox_folder = self.dropbox_app.config['dropbox_path']
                                    except KeyError:
                                        dropbox_folder = self.dropbox_app.default_dropbox_path
                                        TRACE('!!: Using default dropbox path! %r', dropbox_folder)

                                dropbox_globals['dropbox'] = dropbox_folder
                                TRACE('------------- Dropbox folder path: %r', dropbox_folder)
                                try:
                                    TRACE('------------- Real Path: %r', os.path.realpath(dropbox_folder))
                                except Exception:
                                    unhandled_exc_handler(False)

                                with self.dropbox_app.config as config:
                                    config['host_id'] = ret['host_id']
                                    config['dropbox_path'] = dropbox_folder
                                    config['root_ns'] = long(ret['root_ns'])
                                    config['email'] = ret['email']
                                unlink_cookie = None
                                if not freshly_linked and not self.dropbox_app.sync_engine.get_directory_ignore_set():
                                    if self.dropbox_app.unlink_cookie and self.dropbox_app.unlink_cookie['root_ns'] == ret['root_ns']:
                                        TRACE('!! Restoring ignore set from unlink cookie')
                                        unlink_cookie = self.dropbox_app.sync_engine.change_directory_ignore_set_lite(self.dropbox_app.unlink_cookie['unicode_rr_set'])
                                if not unlink_cookie:
                                    self.dropbox_app_unlink_cookie = write_unlink_cookie(sync_engine=self.dropbox_app.sync_engine, keystore=self.dropbox_app.keystore)
                                TRACE('Email set to %r', ret['email'])
                                finish_dropbox_boot(self, ret, freshly_linked, wiz_ret, dropbox_folder)
                                TRACE('All logged in and happy')
                            except Exception:
                                unhandled_exc_handler()
                                self.dropbox_app.fatal_exception(sys.exc_info()[0])

                        except Exception:
                            unhandled_exc_handler()

                        break
                    else:
                        self.dropbox_app.dropbox_url_info.email = None
                        self.dropbox_app.status_controller.set_status_label('waiting_for_link', True, clear_previous=True)
                        freshly_linked = True
                        if self.dropbox_app.keystore.report_errors_to_server():
                            report_bad_assumption('Client got unlinked because of keystore')
                        if arch.constants.platform == 'linux':
                            try:
                                check_location(self.dropbox_app, ret)
                            except Exception:
                                unhandled_exc_handler()

                        report('waiting-for-link', tag=self.dropbox_app.installer_tags)
                        self.dropbox_app.event.flush_async()
                        self.dropbox_app.status_controller.set_mounted(False)
                        if self.dropbox_app.mbox.is_primary:
                            login_only, email_address = False, None
                        else:
                            login_only = True
                            email_address = self.dropbox_app.mbox.get_secondary_email()
                            if not email_address:
                                report_bad_assumption('Secondary tried to authenticate without an allowed email')
                                arch.util.hard_exit(-1)
                        if feature_enabled('setupwizkit') and self.dropbox_app.ui_kit.using_xui:
                            self.dropbox_app.ui_kit.enter_setupwizkit(self.linked_event, definitely_connected=True, email_address=email_address, login_only=login_only)
                        else:
                            start_panel = LoginPanel if login_only else WelcomePanel
                            self.dropbox_app.ui_kit.enter_setupwizard(start_panel, self.linked_event, definitely_connected=True, force=False, email_address=email_address)
                        TRACE('Waiting for ok to call register_host again..')
                        self.dropbox_app.ui_kit.setupwizard_should_register_wait()

        except Exception:
            unhandled_exc_handler()
            self.sleep(5)


class AuthenticationThread(StoppableThread):

    def __init__(self, dropbox_app, *n, **kw):
        kw['name'] = 'AUTHENTICATE'
        super(AuthenticationThread, self).__init__(*n, **kw)
        self.dropbox_app = dropbox_app
        self.wakeup_bang = AutoResetEvent()
        self.linked_event = threading.Event()

    def set_wakeup_event(self):
        self.wakeup_bang.set()

    def sleep(self, amt):
        self.wakeup_bang.wait(amt)

    def run(self):
        TRACE('Hello from authentication thread!')
        try:
            self.dropbox_app.startup_high()
        except Exception:
            unhandled_exc_handler()
            self.dropbox_app.fatal_exception(sys.exc_info()[0])

        self.dropbox_app.conn.add_reconnect_wakeup(self.set_wakeup_event)
        try:
            authentication_thread(self)
        finally:
            try:
                self.dropbox_app.conn.remove_reconnect_wakeup(self.set_wakeup_event)
                self.dropbox_app.conn.kill_all_connections()
            except Exception:
                unhandled_exc_handler()
