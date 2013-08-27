#Embedded file name: dropbox/client/main.py
try:
    import dropbox.overrides
    import autogen_explicit_imports
    import errno
    import functools
    import getopt
    import itertools
    import os
    import pprint
    import stat
    import shutil
    import sqlite3
    import sys
    import threading
    import time
    import traceback
    import urllib
    from Queue import Empty, Queue
    import build_number
    BUILD_KEY = build_number.BUILD_KEY
    import client_api.kv_connection
    from client_api.dropbox_connection import DropboxConnection
    from dropbox.boot_error import boot_error
    from dropbox.globals import dropbox_globals
    import dropbox.platform
    dropbox_globals['platform'] = dropbox.platform.platform
    from dropbox import dispatch
    from dropbox.callbacks import Handler
    from dropbox.dirtraverse import Directory
    from dropbox.trace import TRACE, unhandled_exc_handler, get_extra_trace_info, report_bad_assumption, set_debugging
    from dropbox.url_info import dropbox_url_info
    from dropbox.build_common import PYTHON_DROPBOX_BUILD, DROPBOX_SQLITE_VERSION, get_build_number, get_platform
    from dropbox.db_thread import db_thread, specified_profiler, live_tracer_is_enabled
    from dropbox.bubble_context import BubbleContext
    from dropbox.features import add_feature_overrides, feature_enabled
    from dropbox.functions import lrudict, frozendict
    from dropbox.keystore import KeychainAuthFailed, KeychainNeedsRepair, KeychainAuthCanceled, KeystoreRegKeyError
    from dropbox.livetracer import LiveTraceThread
    from dropbox.low_functions import NullObject, partition
    from dropbox.memory_tracker import MemoryTracker, MemoryTrackHandler
    from dropbox.monotonic_time import get_monotonic_time_seconds
    from dropbox.preferences import OPT_LANG
    from dropbox.throttle import Throttle
    from dropbox.idlehands import IdleHandler
    from dropbox.sqlite3_helpers import set_tracing_sql
    from dropbox.symlink_tracker import SymlinkTracker, SymlinkTrackHandler
    from dropbox.i18n import activate_translation, format_number, get_country_code, get_current_code, get_system_languages, safe_activate_translation, trans, TranslationLanguageError
    from dropbox.fileevents import FileEvents
    from dropbox.bubble import BubbleKind, Bubble
    from dropbox import fsutil
    import arch
    import arch.uikit
    from dropbox.client.aggregation import MultiaccountRecentlyChanged
    from dropbox.client.background_worker import BackgroundWorkerThread
    from dropbox.client.preferences import DropboxPrefController
    from dropbox.client.panda import panda
    from dropbox.client.client_shmodel import ClientShmodel
    from dropbox.client.desktop_login import DesktopLogin
    from dropbox.client.proxy_info import MetaProxyInfo
    from dropbox.client.high_trace import FormattedTraceReporter, send_trace_log, set_trace_conn, start_trace_thread, install_global_trace_handlers
    from dropbox.client.multiaccount.instance_database import InstanceConfig
    from dropbox.client.multiaccount.move_dropbox import move_dropbox_if_necessary
    from dropbox.client.notifications import MultiaccountNotifications
    from dropbox.client.databases import load_dropbox_config, clear_appdata_for_unlink, cleanup_corrupt_databases
    from dropbox.client.debugging import run_interactive_shell
    from dropbox.client.event_reporting import EventReporterThread
    from dropbox.client.gandalf import Gandalf
    from dropbox.client.multiaccount.multibox import MultiBoxServer
    from dropbox.client.watchdog import Watchdog2, WatchdogThread
    from dropbox.client.authenticate import AuthenticationThread
    from dropbox.client.unlink_cookie import read_unlink_cookie, write_unlink_cookie, write_unlink_cookie_no_sync_engine, UNLINK_COOKIE_PREFS
    from dropbox.client.wipe import delete_data
    from dropbox.client.update import UpgradeLogic
    from dropbox.client.mapreduce import DBKeyStore, CLIENT_KEY_NAME
    import dropbox.client.photouploader
    from dropbox.client.photocontroller import CameraController
    from dropbox.client.screenshots import ScreenshotsCallbacks
    from dropbox.client.screenshots import ScreenshotsController
    from dropbox.client.status import StatusController
    from ui.icon_overlay import StatusThread
    from ui.common.tray import TrayController
    if feature_enabled('cffi-printf-on-startup'):
        from printf import printf
        printf('CFFI is working!\n')
except Exception:
    import traceback
    import sys
    import os
    traceback.print_exc()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(-2)

MEMORY_TRACKER_ENABLED = True
FATALDB_RESTART_TIMEOUT = 60 * 60

class DropboxApplication(object):

    def __init__(self, unicode_argv):
        self.argv = list(unicode_argv)
        self.usage_lock = threading.Lock()
        self.in_use, self.quota = (0, 0)
        self.past_bubble_map = lrudict(cache_size=20)
        self.ui_flags = frozendict()
        self.should_reveal_dropbox_folder_iff_other_instance_running = False
        self.files_to_add = []
        self.unlink_failure = False
        self.update_lang = False
        self.corruptdb = False
        self.fataldb_restart = False
        self.system_startup = False
        self.is_first_run = False
        self.is_freshly_linked = False
        self.is_update = False
        self.should_restart_explorer = False
        self.sync_engine = None
        self.installer_tags = ''
        self.conn = None
        self.config = None
        self.keystore = None
        self.uid = None
        self.gandalf = None
        self.desktop_login = None
        self.notification_controller = None
        self.screenshots_callbacks = None
        self.screenshots_controller = None
        self.recently_changed = None
        self.ui_kit = None
        self.is_manual_update = False
        self.stuff_importer = None
        self.mbox = MultiBoxServer(self)
        self.instance_id = None
        self.merged_recently_changed = None
        self.merged_notification_controller = None
        self._server_time = None
        self._monotonic_time = 0
        self.bubble_context = None
        self.on_quit = arch.util.hard_exit.pre
        self.on_restart = arch.util.restart.pre
        self.on_quota_changed = Handler()
        self.sync_engine_set_handler = Handler()
        self.set_sync_engine_callback = self.sync_engine_set_handler.add_handler
        self.appdata_path = arch.constants.appdata_path
        self.default_dropbox_path = arch.constants.default_dropbox_path
        self.default_dropbox_folder_name = arch.constants.default_dropbox_folder_name
        self.instance_config = None

    def startup_main_thread(self):
        TRACE('Main Thread Loop Running')

    def boot_error(self, tb = None):
        info = get_extra_trace_info(self.appdata_path, self.get_dropbox_path())
        if tb:
            info += '\n' + tb
        boot_error(info)

    def safe_makedirs(self, path, mode = None, override = True):
        try:
            os.makedirs(path, mode if mode is not None else 511)
        except Exception as e:
            if e.errno == errno.EEXIST:
                if not override:
                    mode = None
            elif e.errno == errno.EACCES and arch.constants.platform == 'mac':
                try:
                    arch.fixperms.fix_perm_on_directory(os.path.dirname(os.path.normpath(path)))
                except Exception:
                    unhandled_exc_handler()

                os.makedirs(path, mode if mode is not None else 511)
            else:
                raise

        if mode is not None:
            try:
                os.chmod(path, mode)
            except Exception:
                unhandled_exc_handler()

    def _parse_command_line_flags(self):
        debug_output = []
        debug_output.append('Command line: %r' % self.argv)
        flags, self.argv = partition(lambda arg: arg.startswith('--'), self.argv)
        flags = add_feature_overrides(flags)
        debug_output.append('Command flags: %r' % flags)
        optlist, remaining = getopt.getopt(flags, '', ['client=',
         'version=',
         'server-address=',
         'key=',
         'secondary-email=',
         'secondary-role=',
         'mbox-folder-prefix='])
        self.argv += remaining
        return (dict(optlist), debug_output)

    def startup_low(self):
        flags, debug_output = self._parse_command_line_flags()
        install_global_trace_handlers(flags=flags, args=self.argv)
        for item in debug_output:
            TRACE(item)

        TRACE('Dropbox called with options: %r %r', flags, self.argv)
        time.strptime('07/25/2013', '%m/%d/%Y')
        if feature_enabled('multiaccount'):
            self.instance_config = InstanceConfig(self)
            instance_id = flags.get('--client', None)
            if instance_id:
                instance_row = self.instance_config.instance_db.get_row(int(instance_id))
                TRACE('Running as secondary client')
                self.mbox.is_secondary = True
                self.mbox.initialize_handlers()
                try:
                    self.mbox.primary_address = flags['--server-address']
                    TRACE('Primary client pipe address is %r', self.mbox.primary_address)
                except Exception:
                    unhandled_exc_handler()

            else:
                instance_row = self.instance_config.instance_db.get_or_create_master()
            TRACE('Multibox configuration info: %r', instance_row)
            self.instance_id = instance_row.id
            self.appdata_path = instance_row.appdata_path
            self.default_dropbox_path = instance_row.default_dropbox_path
            self.default_dropbox_folder_name = instance_row.default_dropbox_folder_name
            TRACE('MULTIACCOUNT: Setting default_path to %r and default_folder_name to %r' % (self.default_dropbox_path, self.default_dropbox_folder_name))
            if not hasattr(build_number, 'frozen'):
                self.mbox.parse_commandline_flags(flags)
        else:
            self.appdata_path = arch.constants.appdata_path
            self.default_dropbox_path = arch.constants.default_dropbox_path
            self.default_dropbox_folder_name = arch.constants.default_dropbox_folder_name
        set_debugging(not build_number.stable_build() or not build_number.is_frozen())
        set_tracing_sql(not build_number.is_frozen() and os.getenv('DBSQLTRACE'))
        self.dropbox_url_info = dropbox_url_info
        self.background_worker = BackgroundWorkerThread()
        self.background_worker.start()
        self.desktop_login = DesktopLogin(self)
        self.client_shmodel = ClientShmodel(self)
        arch.startup.install_early_in_boot(self)
        arch.startup.pre_appdata_use_startup(self.appdata_path)
        for path in (self.appdata_path,):
            self.safe_makedirs(path, 448)

        sqlite3.enable_shared_cache(True)
        try:
            start_trace_thread(self)
        except Exception:
            unhandled_exc_handler(False)

        TRACE('Initializing the event reporter.')
        self.event = db_thread(EventReporterThread)(get_build_number(), self)
        self.event.start()

        def flush(*n, **kw):
            self.event.flush_events(True)

        self.add_quit_handler(flush)

    def startup_delegate_from_arguments(self):
        RETURN_SUCCESS = 3
        RETURN_EXCEPTION = -2
        if feature_enabled('ascii-art-panda'):
            panda()
        try:
            restart = self.argv.index('/restart')
        except ValueError:
            pass
        except Exception:
            unhandled_exc_handler()
        else:
            del self.argv[restart]
            try:
                pid = int(self.argv[restart])
                del self.argv[restart]
                arch.startup.kill_process_by_pid(pid)
                time.sleep(0)
            except Exception:
                unhandled_exc_handler()

        for i, arg in enumerate(self.argv):
            if arg.startswith('/TAGS:'):
                self.installer_tags = arg[len('/TAGS:'):]
                TRACE('installer tags: %r', self.installer_tags)
                del self.argv[i]
                break

        first_arg = None
        if len(self.argv) > 1:
            ret = None
            try:
                first_arg = self.argv[1].lower()
                if first_arg == '/newerversion':
                    self.argv = self.argv[:1] + self.argv[2:]
                    arch.util.kill_other_instances()
                    if len(self.argv) > 1:
                        first_arg = self.argv[1].lower()
                if first_arg in ('/firstrun', '/firstrunupdate', '/firstrunupdatemanual'):
                    try:
                        should_restart_explorer = False
                        if len(self.argv) > 2:
                            should_restart_explorer = int(self.argv[2])
                    except Exception:
                        unhandled_exc_handler()

                    self.should_restart_explorer = should_restart_explorer
                    self.is_first_run = True
                    self.is_update = first_arg.startswith('/firstrunupdate')
                    self.is_manual_update = first_arg == '/firstrunupdatemanual'
                    arch.startup.first_run(is_update=self.is_update)
                elif first_arg in ('/unlink', '/killdata', '/unlinkr'):
                    if feature_enabled('multiaccount'):
                        self.instance_config.instance_db.set_inactive_by_id(self.instance_id)
                        promoted = False
                        if self.mbox.is_primary:
                            slave_row = self.instance_config.get_slave_row()
                            if slave_row:
                                self.instance_config.instance_db.promote_slave_to_master(slave_row.id)
                                promoted = True
                    else:
                        promoted = False
                    self.create_keystore_and_unlink_cookie()
                    try:
                        safe_activate_translation()
                    except Exception:
                        TRACE('!! Failed to activate translation! Uninstall dialog strings will be untranslated')

                    arch.startup.unlink(self.unlink_cookie, is_uninstall=first_arg == '/killdata')
                    if self.unlink_cookie:
                        if self.sync_engine:
                            report_bad_assumption('Sync engine exists when unlinking')
                        self.unlink_cookie = write_unlink_cookie_no_sync_engine(appdata_path=self.appdata_path, in_config=self.config, keystore=self.keystore, host_id=None)
                    did_delete, didnt_delete = clear_appdata_for_unlink(clear_unlink_cookie=first_arg == '/killdata', database_dir=self.appdata_path)
                    if first_arg == '/unlinkr':
                        if arch.constants.platform == 'mac' and not promoted:
                            if didnt_delete:
                                self.unlink_failure = True
                            ret = None
                        else:
                            arch.util.restart(['/unlinkfailure'] if didnt_delete else [])
                            ret = 0
                    else:
                        ret = 0
                elif first_arg == '/migratecheck':
                    ret = 1 if arch.startup.can_migrate_installation() else 2
                elif first_arg == '/kill':
                    arch.startup.kill_process_by_name('%s.exe' % BUILD_KEY.lower())
                    ret = 0
                elif first_arg == '/killeveryone':
                    success = arch.startup.kill_process_by_name('%s.exe' % BUILD_KEY.lower(), other_users=True)
                    if success:
                        success = arch.startup.kill_process_by_name('%sproxy.exe' % BUILD_KEY.lower(), other_users=True)
                    arch.util.clean_tray()
                    ret = RETURN_SUCCESS if success else 1
                elif first_arg == '/updatecheck':
                    ret = RETURN_SUCCESS
                elif first_arg == '/export':
                    ret = 0
                elif first_arg == '/home':
                    if len(self.argv) > 2:
                        self.create_keystore_and_unlink_cookie()
                        if self.unlink_cookie and 'path' in self.unlink_cookie and os.path.isdir(self.unlink_cookie['path']):
                            results = arch.util.handle_extra_command_line_args(self.argv[2:], self.unlink_cookie['path'])
                            if results:
                                TRACE('Reporting drag and drop event')
                                self.event.report('win_drag_and_drop', {'total_file_size': results[1],
                                 'number_of_files': results[0]})
                    else:
                        self.should_reveal_dropbox_folder_iff_other_instance_running = True
                    ret = None
                elif first_arg == '/corruptdb':
                    self.corruptdb = True
                    ret = None
                elif first_arg == '/fataldb':
                    self.fataldb_restart = True
                    ret = None
                elif first_arg == '/unlinkfailure':
                    self.unlink_failure = True
                    ret = None
                elif first_arg == '/initdropbox':
                    ret = RETURN_SUCCESS
                elif first_arg == '/deletedata':
                    if len(self.argv) > 2:
                        path = self.argv[2]
                        delete_data(self, path)
                    else:
                        TRACE('DELETE DATA failed')
                    ret = RETURN_SUCCESS
                elif first_arg == '/updatelang':
                    self.update_lang = True
                    ret = None
                elif first_arg in ('/installphotocomponentsuser', '/installphotocomponentsadmin'):
                    ret = RETURN_SUCCESS
                    safe_activate_translation()
                    arch.photouploader.install_photo_components(as_admin=first_arg == '/installphotocomponentsadmin')
                elif first_arg in ('/uninstallphotocomponentsuser', '/uninstallphotocomponentsadmin'):
                    arch.photouploader.uninstall_photo_components(as_admin=first_arg == '/uninstallphotocomponentsadmin')
                    ret = RETURN_SUCCESS
                elif first_arg == '/autoplayproxy':
                    ret = RETURN_SUCCESS
                    TRACE('Running as autoplay proxy.  Args: %r', self.argv)
                    if os.path.basename(sys.executable) != BUILD_KEY + 'Proxy.exe':
                        TRACE('!! Dropbox photouploader autoplay proxy running from non-standard location %r', sys.executable)
                    safe_activate_translation()
                    try:
                        autoplay_proxy = dropbox.client.photouploader.Proxy()
                    except AttributeError:
                        raise Exception('Dropbox run with /autoplayproxy on an architecture that has no proxy!')
                    else:
                        signal_when_done = threading.Event()
                        TRACE('Calling arch proxy with cmdline args: %r', self.argv[2:])
                        autoplay_proxy.do_your_thing(self, signal_when_done.set, self.argv[2:])
                        signal_when_done.wait()

                elif first_arg == '/autoplay':
                    pass
                elif first_arg == '/wiacallback':
                    report_bad_assumption('Dropbox was launched because someone created IWiaDataCallback (other Dropbox is busy?)')
                elif first_arg == '/systemstartup':
                    TRACE('We are booting with the system!')
                    self.system_startup = True
                else:
                    TRACE('got unexpected first arg: %r' % first_arg)
            except Exception:
                unhandled_exc_handler()
                ret = RETURN_EXCEPTION

            if ret is not None:
                arch.util.hard_exit(ret)
        try:
            if os.path.basename(sys.executable) == BUILD_KEY + 'Proxy.exe' and first_arg != '/autoplayproxy':
                TRACE('!! DropboxProxy running without proper commandline arguments! Exiting.')
                arch.util.hard_exit(RETURN_SUCCESS)
        except Exception:
            unhandled_exc_handler()

    def throttle_settings_from_prefs(self, prefs, throttle):
        if prefs['throttle_upload_style'] == 1:
            throttle.ul_throttle_type = Throttle.THROTTLE_AUTOMATIC
            throttle.ul_throttle_percentage = Throttle.AUTO_PERCENT
            throttle.ul_speed = Throttle.AUTOMATIC_START_SPEED
            TRACE('THROTTLE: setting automatic upload throttle, %0.2f%% of connection speed', throttle.ul_throttle_percentage * 100)
        elif prefs['throttle_upload_style'] == 0:
            throttle.ul_throttle_type = Throttle.THROTTLE_NONE
            TRACE('THROTTLE: setting no upload throttle (unlimited)')
        else:
            throttle.ul_throttle_type = Throttle.THROTTLE_MANUAL
            throttle.ul_speed = prefs['throttle_upload_speed'] * 1024.0
            TRACE('THROTTLE: setting manual upload throttle, %0.2f kB/s', prefs['throttle_upload_speed'])
        if prefs['throttle_download_style'] == 0:
            throttle.dl_throttle_type = Throttle.THROTTLE_NONE
            TRACE('THROTTLE: setting no download throttle (unlimited)')
        else:
            throttle.dl_throttle_type = Throttle.THROTTLE_MANUAL
            throttle.dl_speed = prefs['throttle_download_speed'] * 1024.0
            TRACE('THROTTLE: setting manual download throttle, %0.2f kB/s', prefs['throttle_download_speed'])

    @staticmethod
    def activate_translation(code, force = False):
        try:
            activate_translation(code, force=force)
        except TranslationLanguageError as e:
            TRACE('error initializing language %s: %s', code, e)
            activate_translation(force=force)

    def startup_high(self):
        self.idle_tracker = IdleHandler(self.ui_kit)
        if self.mbox.is_secondary:
            self.mbox.enable()
        arch.startup.reroll_startup_items(self.pref_controller)
        self.pref_controller.add_pref_callback('startupitem', arch.startup.reroll_startup_items)
        if feature_enabled('multiaccount'):
            self.pref_controller.add_pref_callback('dropbox_path', self.mbox.update_dropbox_path_from_pref_controller)
        self.ui_kit.set_prefs(self.pref_controller)
        if self.mbox.is_primary:
            self.ui_kit.start_tray_icon()
        TRACE('%r' % self.dropbox_url_info)
        self.bubble_context = BubbleContext(app=self)
        self.bubble_context.set_sp_functions(arch.util.launch_folder, arch.util.highlight_file, self.server_to_local_caller)
        self.conn = conn = DropboxConnection(hosts=self.dropbox_url_info.api_hosts, set_status_label=self.status_controller.set_status_label, throttle_settings=functools.partial(self.throttle_settings_from_prefs, self.pref_controller), meta_proxy_info=MetaProxyInfo(self.pref_controller, bad_proxy_notification_callback=self._bad_proxy_notification_callback), locale=get_current_code(), event_reporter=self.event, user_agent_dict=arch.util.get_user_agent_dict())
        if self.unlink_cookie and self.unlink_cookie.get('host_id', None):
            self.conn.set_host_id(self.unlink_cookie['host_id'])
        set_trace_conn(self.conn)
        self.event.set_conn(self.conn)
        if self.mbox.is_primary:
            self.upgrade_logic = UpgradeLogic(arch.update, self.config, self.conn, get_build_number(), '%s-%s-' % (BUILD_KEY, get_platform()), dbkeyname=CLIENT_KEY_NAME, flush_events=self.event.flush_events)
            self.set_sync_engine_callback(self.upgrade_logic.set_sync_engine)
        else:
            self.upgrade_logic = None
        self.pref_controller.add_pref_callback('proxy_.*', conn.reconnect)
        self.pref_controller.add_pref_callback('throttle_.*', conn.reconnect)
        for pref in UNLINK_COOKIE_PREFS:
            self.pref_controller.add_pref_callback(pref, self._plain_write_unlink_cookie)

        self.watchdog = db_thread(WatchdogThread)(self)
        self.watchdog.add_handler(self.conn.expire_old_connections)
        if self.update_lang:
            self.set_web_locale(get_current_code())
        self.stat_reporter = NullObject()
        self.formatted_trace = FormattedTraceReporter(get_build_number(), self.conn, self.config, self.pref_controller)
        self.set_sync_engine_callback(self.formatted_trace.set_sync_engine)
        self.watchdog2 = Watchdog2(self.status_controller, self.conn, handler=self.watchdog)
        self.set_sync_engine_callback(self.watchdog2.set_sync_engine)
        try:
            if MEMORY_TRACKER_ENABLED:
                self.memory_tracker = MemoryTracker()
                self.set_sync_engine_callback(self.memory_tracker.set_sync_engine)
                self.watchdog.add_handler(MemoryTrackHandler(self.memory_tracker))
        except Exception:
            unhandled_exc_handler()

        self.file_events = db_thread(FileEvents)(arch.directory_reader.MetaDirectoryWatchManager(), app=self)
        self.proxy_watch.register_callback(conn.reconnect)
        if self.is_manual_update:
            show_bubble = False
            if arch.constants.platform == 'mac':
                from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
                if MAC_VERSION >= SNOW_LEOPARD:
                    show_bubble = True
            if arch.constants.platform == 'win':
                show_bubble = True
            if show_bubble:
                caption = trans(u'Dropbox updated!')
                msg = trans(u'You have successfully updated Dropbox to version %s!') % (build_number.VERSION,)
                self.ui_kit.pass_message(self.ui_kit.show_bubble, Bubble(BubbleKind.MANUAL_INSTALL_SUCCESS, msg, caption))
        try:
            arch.startup.post_init_startup(self)
        except Exception:
            unhandled_exc_handler()

    def start_after_user_auth(self):
        self.gandalf = Gandalf(self)
        self.gandalf.start()
        self.sync_engine.set_gandalf(self.gandalf)
        try:
            if feature_enabled('screenshots') and ScreenshotsController.is_supported(self):
                self.screenshots_callbacks = ScreenshotsCallbacks()
        except Exception:
            unhandled_exc_handler()

        if self.mbox.linked and self.mbox.is_primary:
            self.enable_multiaccount()

    def enable_multiaccount(self):
        if self.mbox.is_secondary:
            TRACE('enable_multiaccount unexpectedly called on the secondary')
        else:
            self.merged_recently_changed = MultiaccountRecentlyChanged(self)
            self.merged_notification_controller = MultiaccountNotifications(self)
            self.ui_kit.enable_multiaccount()
            self.mbox.enable()

    def disable_multiaccount(self):
        if self.mbox.is_primary:
            self.merged_recently_changed = self.merged_notification_controller = None
            self.ui_kit.disable_multiaccount()
            self.mbox.unlink_secondary()

    def _plain_write_unlink_cookie(self, pref_controller):
        TRACE('in _plain_write_unlink_cookie()')
        if self.sync_engine:
            write_unlink_cookie(self.sync_engine, self.keystore)
        else:
            write_unlink_cookie_no_sync_engine(self.appdata_path, self.config, self.keystore)

    def create_keystore_and_unlink_cookie(self):
        if self.keystore:
            return
        try:
            self.keystore = DBKeyStore(self.appdata_path, instance_id=self.instance_id)
        except (KeychainAuthFailed, KeychainNeedsRepair, KeychainAuthCanceled) as e:
            safe_activate_translation()
            if isinstance(e, KeychainNeedsRepair):
                msg = trans(u'Dropbox had a problem accessing your keychain.  This is sometimes caused by a corrupt keychain.  Please open "Keychain Access" and run "Keychain First Aid". Then restart Dropbox.')
            elif isinstance(e, KeychainAuthCanceled):
                msg = trans(u'Dropbox requires access to your Keychain in order to verify your identity. Please restart Dropbox and enter your keychain password to unlock your keychain.')
            else:
                msg = trans(u'Dropbox requires access to your Keychain in order to verify your identity. Please restart Dropbox and "Always Allow" access.')
            boot_error(direct_message=msg, page='keychain_access')
        except Exception as e:
            if arch.constants.platform == 'win':
                safe_activate_translation()
                page = None
                caption = trans(u"Couldn't access Windows system information")
                message = trans(u"Dropbox can't access important system information.")
                message += u'\n' + trans(u'<a href="%(url)s">How do I fix this?</a>')
                if isinstance(e, WindowsError):
                    page = {-2146893813: 'keystore_not_valid',
                     2: 'keystore_not_found',
                     5: 'keystore_access_denied'}.get(e.winerror)
                    if e.winerror == 5:
                        message = trans(u'Please reset your Windows account password.')
                        message += u'\n' + trans(u'<a href="%(url)s">More information</a>')
                elif isinstance(e, KeystoreRegKeyError):
                    page = 'keystore_reg_key_error'
                if page:
                    formatted_tb = traceback.format_exc()
                    TRACE('formatted_tb=%r', formatted_tb)
                    message = message % {'url': self.dropbox_url_info.help_url(page)}
                    boot_error(direct_message=message, caption=caption, more_help=False)
                    arch.util.hard_exit(-1)
                    return
            unhandled_exc_handler(trace_locals=False)
            raise e

        try:
            self.unlink_cookie = read_unlink_cookie(self.appdata_path, self.keystore)
        except Exception:
            self.unlink_cookie = None
            unhandled_exc_handler(False)

    def run(self):
        self.startup_low()
        dropbox_python_version = getattr(sys, 'dropboxbuild', None)
        if build_number.is_frozen():
            assert hasattr(sys, 'lockdown') and sys.lockdown, 'Non-Dropbox python executable'
            assert dropbox_python_version == PYTHON_DROPBOX_BUILD, 'Wrong build of Dropbox (%s vs %s needed)' % (dropbox_python_version, PYTHON_DROPBOX_BUILD)
            assert sqlite3.sqlite_version == DROPBOX_SQLITE_VERSION, 'Wrong version of sqlite (%s vs %s needed)' % (sqlite3.sqlite_version, DROPBOX_SQLITE_VERSION)
        elif dropbox_python_version != PYTHON_DROPBOX_BUILD:
            TRACE('!! Wrong build of Dropbox (%s vs %s needed)', getattr(sys, 'dropboxbuild', None), PYTHON_DROPBOX_BUILD)
        TRACE('%s (%s) starting', get_build_number(), os.getpid())
        for const in ('platform', 'default_dropbox_folder_name', 'hash_wait_time', 'local_form'):
            TRACE('arch.constants.%s = %r', const, getattr(arch.constants, const))

        for const in ('appdata_path', 'default_dropbox_path'):
            try:
                TRACE('realpath for %s: %r', const, os.path.realpath(getattr(self, const)))
            except Exception:
                unhandled_exc_handler()

        try:
            TRACE('Contents of appdata: %r:', self.appdata_path)
            with Directory(self.appdata_path) as d:
                TRACE('%s' % pprint.pformat(list(itertools.islice(d, 15))))
                try:
                    d.next()
                except StopIteration:
                    pass
                else:
                    TRACE('... and possibly more')

        except Exception:
            unhandled_exc_handler()

        self.startup_delegate_from_arguments()
        self.create_keystore_and_unlink_cookie()
        try:
            if self.unlink_cookie and self.unlink_cookie.get('delete_data_on_restart', False):
                if len(self.argv) < 2 or self.argv[1].lower() != '/deletedata':
                    TRACE('Restarting to delete data')
                    arch.util.restart(['/deletedata', arch.util.encode_command_line_arg(self.get_dropbox_path())])
        except:
            unhandled_exc_handler()

        TRACE('%s Dropbox path: %s', 'Primary' if self.mbox.is_primary else 'Secondary', self.get_dropbox_path())
        try:
            path_to_reveal = None
            if self.should_reveal_dropbox_folder_iff_other_instance_running and self.unlink_cookie:
                try:
                    path_to_reveal = self.unlink_cookie['path']
                except KeyError:
                    pass
                except Exception:
                    unhandled_exc_handler()

            arch.startup.limit_to_one_instance(self.appdata_path, path_to_reveal)
            if build_number.is_frozen():
                arch.startup.ensure_latest_version()
        except Exception:
            unhandled_exc_handler()

        if os.path.exists(os.path.join(self.appdata_path, 'moving')):
            TRACE('Dropbox crashed during move; resetting client state and relinking')
            arch.util.restart(['/unlinkr'])
        if self.corruptdb:
            self.event.report('corrupted-db')
            cleanup_corrupt_databases(self.appdata_path)
            if self.instance_config:
                self.instance_config.clear()
        TRACE('Loading config...')
        self.config = load_dropbox_config(self.appdata_path, self.keystore, self.default_dropbox_folder_name)
        TRACE('Loaded config!')
        if self.fataldb_restart:
            restart_timestamps = self.config.get('fataldb_restarts', []) + [time.time()]
            recent_restarts = [ r for r in restart_timestamps if time.time() - r < FATALDB_RESTART_TIMEOUT ]
            if len(recent_restarts) > 1:
                self.config['disable_on_disk_cache'] = True
            self.config['fataldb_restarts'] = recent_restarts
        try:
            dropbox_globals['dropbox'] = self.config['dropbox_path']
        except KeyError:
            dropbox_globals['dropbox'] = self.default_dropbox_path

        with self.config as configd:
            for k in configd.iterkeys():
                if k == u'ns_p2p_key_map' or k.startswith(u'recently_changed'):
                    continue
                TRACE(' %r = %r' % (k, configd[k]))

        if self.config.get('email'):
            self.dropbox_url_info.email = self.config['email']
        self.pref_controller = DropboxPrefController(self.config, app=self)
        for opt in [OPT_LANG]:
            if opt not in self.config:
                if self.unlink_cookie and self.unlink_cookie.get(opt):
                    self.config[opt] = self.unlink_cookie[opt]

        self.activate_translation(self.pref_controller[OPT_LANG], force=True)
        self.csr = NullObject()
        try:
            self.event.report('i18n_startup', {'configured_language': self.pref_controller['language'],
             'country': get_country_code(),
             'current_language': get_current_code(),
             'system_language': get_system_languages()[0]})
        except Exception:
            unhandled_exc_handler()

        self.status_controller = StatusController(self)
        TRACE('Initialized StatusController: %r', self.status_controller)
        self.tray_controller = TrayController(self)
        self.set_sync_engine_callback(self.tray_controller.set_sync_engine)
        self.tray_controller.add_callbacks_for_options({'send_trace_log': send_trace_log})
        TRACE('Initialized TrayController: %r', self.tray_controller)
        arch.startup.pre_network_startup(self)
        self.proxy_watch = arch.util.ProxyWatch()
        self.proxy_watch.setup_callback()
        TRACE('Initialized ProxyWatch: %r', self.proxy_watch)
        if live_tracer_is_enabled():
            LiveTraceThread(self.appdata_path).start()
        if not build_number.is_frozen() and self.mbox.is_primary:
            run_interactive_shell({'app': self})
        self.ui_kit = arch.uikit.PlatformUIKit(self)
        self.set_sync_engine_callback(self.ui_kit.set_sync_engine)
        TRACE('Initialized UIKit: %r', self.ui_kit)
        db_thread(AuthenticationThread)(self).start()
        TRACE('Running uikit mainloop...')
        self.ui_kit.mainloop()

    def fatal_exception(self, e):
        TRACE('!! Unknown fatal exception during startup: %r' % e)
        formatted_tb = traceback.format_exc()
        self.boot_error(formatted_tb)
        arch.util.hard_exit(-1)

    def server_to_local_caller(self, *n, **kw):
        return self.sync_engine.server_to_local(*n, **kw)

    def _bad_proxy_notification_callback(self, msg):
        if not msg:
            msg = trans(u'Incorrect proxy settings.')
        msg_active = msg + u'\n\n' + trans(u'Click here to correct your network settings')
        if self.mbox.is_primary:
            self.ui_kit.show_bubble(Bubble(BubbleKind.PROXY_SETTINGS_INCORRECT, msg_active, trans(u'Incorrect proxy settings'), self.bubble_context, self.bubble_context.make_func_context_ref(self.ui_kit.enter_proxy_settings), msg_passive=msg))

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine
        self.sync_engine_set_handler.run_handlers(sync_engine)
        self.sync_engine_set_handler.clear()
        sync_engine.add_list_callback(self.handle_list)

        def handle_ignore_set_changing(*n, **kw):
            write_unlink_cookie(sync_engine, keystore=self.keystore)

        sync_engine.add_change_directory_ignore_callback(handle_ignore_set_changing)
        self.add_quit_handler(lambda *n, **kw: sync_engine.arch.clear_shell_state())

        def cleanup_sync_hash_queues(*n, **kw):
            sync_engine.to_hash.close()
            sync_engine.updated_hash_queue.close()
            sync_engine.upload_hash_queue.close()

        self.add_quit_handler(cleanup_sync_hash_queues)
        self.watchdog.start()

    def start(self, uid, user_key):
        self.uid = uid
        symlink_tracker = SymlinkTracker(unicode(self.sync_engine.dropbox_folder))
        self.formatted_trace.set_symlink_tracker(symlink_tracker)
        self.watchdog.add_handler(SymlinkTrackHandler(symlink_tracker, self.event, 86400))
        self.idle_tracker.start()
        db_thread(StatusThread)(self.sync_engine, self, uid, user_key).start()
        self.file_events.start()
        self.sync_engine.start()
        try:
            if feature_enabled('screenshots') and ScreenshotsController.is_supported(self):
                self.screenshots_controller = ScreenshotsController(self)
        except Exception:
            unhandled_exc_handler()

        if not fsutil.supports_preserved_attrs(self.sync_engine.fs, self.sync_engine.dropbox_folder):
            report_bad_assumption('This client does not support preserving xattrs!')
        else:
            self.csr.report_stat('supports_xattrs', True)
        try:
            assert self.photo_uploader
            self.photo_uploader.start()
            self.camera_controller = CameraController(self, arch.photouploader.PhotoUploader(self), self.photo_uploader)
        except Exception:
            unhandled_exc_handler()

        try:
            self.stuff_importer = self.mbox.get_stuff_importer()
        except Exception:
            unhandled_exc_handler()
            self.stuff_importer = None

        if not self.is_freshly_linked:
            if self.mbox.paired:
                try:
                    move_dropbox_if_necessary(self)
                except Exception:
                    unhandled_exc_handler()

    @property
    def server_time(self):
        if self._server_time is None:
            return
        delta = get_monotonic_time_seconds() - self._monotonic_time
        return self._server_time + delta

    def handle_list(self, ret):
        try:
            if ret.get('ui_flags') is not None:
                self.set_ui_flags(ret['ui_flags'])
                if arch.constants.platform == 'mac' and self.ui_flags.get('disable_finder_integration') is not None and self.config.get('disable_finder_integration', False) != self.ui_flags['disable_finder_integration']:
                    self.config['disable_finder_integration'] = self.ui_flags['disable_finder_integration']
                    self.sync_engine.arch.fschange.potential_finder_restart()
        except Exception:
            unhandled_exc_handler()

        try:
            server_time = ret.get('server_time')
            if server_time is not None:
                self._server_time = server_time
                self._monotonic_time = get_monotonic_time_seconds()
        except Exception:
            unhandled_exc_handler()

        try:
            in_use, quota = ret['in_use'], ret['quota']
        except KeyError:
            pass
        except Exception:
            unhandled_exc_handler()
        else:
            self.set_usage(in_use, quota)

        try:
            self.dropbox_url_info.update_from_ret(ret)
        except Exception:
            unhandled_exc_handler()

        try:
            self.tray_controller.handle_list(ret)
        except Exception:
            unhandled_exc_handler()

        try:
            self.stat_reporter.set_reporting_interval(float(ret['stat_interval']))
        except (KeyError, ValueError):
            pass
        except Exception:
            unhandled_exc_handler()

        try:
            bubble_dict = ret['bubble']
        except KeyError:
            pass
        except Exception:
            unhandled_exc_handler()
        else:
            try:
                try:
                    _id = bubble_dict['id']
                    message = bubble_dict['message']
                    caption = bubble_dict['caption']
                except KeyError:
                    TRACE('Bad bubble input from server: %r', bubble_dict)
                else:
                    if 'url' in bubble_dict:
                        url_launcher = self.bubble_context.make_func_context_ref(self.dropbox_url_info.launch_full_url, bubble_dict['url'])
                    else:
                        url_launcher = None
                    if _id not in self.past_bubble_map:
                        self.ui_kit.show_bubble(Bubble(BubbleKind.SERVER_BUBBLE_BROADCAST, message, caption, self.bubble_context, url_launcher))

            except Exception:
                unhandled_exc_handler()

        try:
            _val = ret['send_trace']
        except KeyError:
            pass
        except Exception:
            unhandled_exc_handler()
        else:
            try:
                send_trace_log(_val)
                dropbox_globals['latest_trace'] = ret['send_trace']
            except Exception:
                unhandled_exc_handler()

        try:
            self.check_for_reboot_and_deletedata_flags(ret)
        except Exception:
            unhandled_exc_handler()

        try:
            if build_number.is_frozen() and self.upgrade_logic:
                self.upgrade_logic.handle_list(ret)
        except Exception:
            unhandled_exc_handler()

    def check_for_reboot_and_deletedata_flags(self, flags):
        if 'deletedata' in flags:
            arch.util.restart(['/deletedata', arch.util.encode_command_line_arg(self.get_dropbox_path())], flush=False)
        elif 'reboot' in flags:
            arch.util.restart()

    def set_ui_flags(self, ui_flags):
        self.ui_flags = ui_flags

    def set_usage(self, in_use, quota):
        old_quota = self.quota
        if self.quota and quota != self.quota:
            d = dict(total_space=format_number(float(quota) / 1073741824, frac_precision=1))
            if quota > self.quota:
                self.ui_kit.show_bubble(Bubble(BubbleKind.QUOTA_INCREASED, trans(u'Good news: you now have %(total_space)sGB of storage space on Dropbox.') % d, trans(u'Space increased')))
            else:
                self.ui_kit.show_bubble(Bubble(BubbleKind.QUOTA_REDUCED, trans(u'Your Dropbox now has %(total_space)sGB of storage space.') % d, trans(u'Space reduced')))
        self.in_use, self.quota = in_use, quota
        warning, caption = (None, None)
        last_warning = self.config.get('last_quota_warning')
        if in_use > quota:
            warning = trans(u'Your Dropbox is full and cannot store more files. Upgrade and instantly get more space.')
            caption = trans(u'Dropbox full')
        elif in_use * 100 / quota >= self.ui_flags.get('low_space_pct_threshold', 90):
            warning = trans(u'Your Dropbox is almost full. Upgrade and instantly get more space.')
            caption = trans(u'Dropbox almost full')
        elif last_warning:
            TRACE('Quota looks okay; clearing quota warning timer')
            self.config['last_quota_warning'] = None
        if warning and (not last_warning or time.time() > last_warning + self.ui_flags.get('quota_warn_interval', 172800)) and self.ui_flags.get('upgrade_prompt', False):
            warning_active = warning + trans(u'(click here)')
            self.ui_kit.show_bubble(Bubble(BubbleKind.QUOTA_WARNING, warning_active, caption, self.bubble_context, self.bubble_context.make_func_context_ref(functools.partial(self.desktop_login.login_and_redirect, 'plans')), msg_passive=warning))
            TRACE('Displaying warning bubble (%s)' % caption)
            self.config['last_quota_warning'] = time.time()
        if old_quota and old_quota != self.quota:
            self.on_quota_changed.run_handlers(old_quota, self.quota)

    def add_quit_handler(self, callback):
        self.on_quit.add_handler(callback)
        self.on_restart.add_handler(callback)

    def restart(self, *n, **kw):
        arch.util.restart(*n, **kw)

    def restart_and_unlink(self):
        try:
            if self.sync_engine:
                write_unlink_cookie(self.sync_engine, host_id=None, keystore=self.keystore)
            else:
                write_unlink_cookie_no_sync_engine(appdata_path=self.appdata_path, in_config=self.config, keystore=self.keystore, host_id=None)
        except Exception:
            unhandled_exc_handler()

        arch.util.restart(['/unlinkr'])

    def open_dropbox(self):
        self._open_dropbox(self.get_dropbox_path())

    def _open_dropbox(self, path):
        try:
            if arch.constants.platform == 'mac' and self.sync_engine:
                self.sync_engine.arch.fschange.potential_finder_restart()
        except Exception:
            unhandled_exc_handler()

        try:
            arch.util.launch_folder(path)
        except Exception:
            unhandled_exc_handler()

    def get_dropbox_path(self):
        path = None
        if self.config:
            path = self.config.get('dropbox_path')
        if not path:
            try:
                unlink_cookie = read_unlink_cookie(self.appdata_path, self.keystore)
                if unlink_cookie:
                    path = unlink_cookie.get('path')
                else:
                    TRACE('No unlink cookie, returning default and hoping for the best')
            except Exception:
                unhandled_exc_handler()

        return path or self.default_dropbox_path

    def set_web_locale(self, code):
        try:
            self.watchdog.add_one_time_handler(functools.partial(self.conn.set_web_locale, code))
            self.watchdog.set_wakeup_event()
        except Exception:
            unhandled_exc_handler()

    def report_show_bubble(self, bubble):
        if not bubble.bubble_kind:
            report_bad_assumption('bubble_kind not specified when bubbling', full_stack=True)
        self.event.report('show-bubble', {'bubble_kind': bubble.bubble_kind})

    def report_click_bubble(self, bubble_kind):
        self.event.report('click-bubble', {'bubble_kind': bubble_kind})


def main_startup():
    dropbox_app = DropboxApplication(arch.util.decode_command_line_args(sys.argv))
    try:
        dropbox_app.run()
    except Exception:
        unhandled_exc_handler()
        dropbox_app.fatal_exception(sys.exc_info()[0])


def main():
    profiler, directory = specified_profiler()
    profiler(os.path.join(directory, 'MainThread.prof'))(main_startup)()
    arch.util.hard_exit()
