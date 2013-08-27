#Embedded file name: ui/common/xui/wizkit.py
import arch
import socket
import urllib
import os
from dropbox.event import report
from ui.common.uikit import on_main_thread
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.i18n import format_number, get_current_code
from dropbox.language_data import DEFAULT_CODE
from ui.common.setupwizard import SetupWizardRequestThread
from ui.common.strings import UIStrings
from ui.common.xui import XUIController, XUINotReadyError
from ui.common.countries import by_locale
from dropbox.platform import platform
from ui.common.misc import MiscStrings
from functools import partial

def default_tour_dropbox_location(dropbox_app, with_test = False):
    if platform == 'win' and not os.path.isdir(dropbox_app.default_dropbox_path) and not dropbox_app.mbox.paired and (os.path.isdir(arch.constants.seven_default_dropbox_path) or os.path.isdir(arch.constants.default_desktop_dropbox_path)):
        oldpath = arch.constants.default_desktop_dropbox_path
        pathtype = 'desktop'
        if not os.path.isdir(oldpath):
            oldpath = arch.constants.seven_default_dropbox_path
            pathtype = '0.7'
        try:
            dropbox_app.event.report('relinking_with_nonstandard_default_path', pathtype=pathtype)
        except Exception:
            unhandled_exc_handler()

        return oldpath
    return dropbox_app.default_dropbox_path


class WizkitStrings(UIStrings):
    _strings = dict(forgot_password=(u'Forgot password', 'as in, "I forgot my password"'), single_signon=(u'Single sign-on', 'as in, "I want to do single sign-on"'), choose_size_title=(u'Select your Dropbox size', 'as in Dropbox plan size, for example. 50GB or 100GB'), payment_amount_text=(u'You will be charged:', 'as in, you will need to pay $#'), upgrade_title=(u'Upgrade your Dropbox?', 'meaning, upgrade the Dropbox desktop application?'), exit_wizard_caption=u'Exit Dropbox?', exit_wizard_prompt=u'Are you sure you want to exit Dropbox?', current_plan_description=u'Your current plan', password_strength_0=u'Very Weak', password_strength_1=u'Weak', password_strength_2=u'So-so', password_strength_3=u'Good', password_strength_4=u'Great!', ok_text=u'OK', cancel_text=u'Cancel', window_title=u'Dropbox Setup', sso_error_entered_password=u'To use single sign-on, enter your email without a password.', sso_login_title=u'Connect to Dropbox', sso_paste_button=u'Paste', sso_error_email=u'Single sign-on is not available for this account.', unexpected_error=u'An unexpected error occurred. Please try again later.', merge_title=u'Merge with existing Dropbox folder?', merge_explanation=u"There's already a folder called %(folder_name)s in %(folder_path)s. Do you want to merge all the files in that folder into your Dropbox or choose another location for your Dropbox?", merge_button_ok=(u'Merge', u'verb, as in, to merge two folders. BUTTON'), merge_button_cancel=u'Choose Another Location', connection_options_button=(u'Connection Options...', 'connection refers to internet connection'), connection_trouble_title=u'Connection Error', proxy_server_text=u'If your computer connects to the Internet through a proxy server, please specify your settings here.', reconnect_now_button=(u'Reconnect Now', u'BUTTON'))
    _platform_overrides = dict()


class WizkitController(XUIController):
    __xui_resource__ = 'wizkit'
    __xui_properties__ = ('do_sso_password', 'do_sso_email', 'get_clipboard_link_code', 'launch_sso_browser', 'get_text', 'launch_terms_browser', 'show_menu', 'do_sign_in', 'do_sign_up', 'do_upgrade', 'do_payment', 'do_payment_options', 'do_two_factor', 'do_forgot_password', 'launch_forgot_password_browser', 'do_send_twofactor_sms', 'do_two_factor_rescue', 'launch_two_factor_rescue_browser', 'do_finish', 'disable_mouse_drag', 'disallow_covering', 'allow_covering', 'launch_pricing_browser', 'reconnect_action', 'show_network_settings_action', 'view_loaded', 'show_selective_sync_settings', 'show_location_changer', 'get_default_dropbox_path', 'set_current_dropbox_path', 'dropbox_path', 'log_advanced_settings')

    def __init__(self, app):
        self._window = None
        self._window_proxy = None
        self.linked_event = None
        self.dropbox_app = app
        self.checkpoint = None
        self.request_thread = None
        self._connection_error = False
        self.asked_merge = None
        self.done = False
        try:
            hostname = socket.gethostname()
        except Exception:
            unhandled_exc_handler()
            hostname = 'localhost'

        self.display_name = hostname
        self.new_account = False
        self._linked = False
        self.client_plans = None
        self.chosen_plan_index = 0
        self.login_only = False
        self.password = None
        self.email = None
        self.root_ns = None
        self._countries = None
        self._user_sso_state = None
        self.link_code = None
        self.directory_ignore_set = frozenset()
        self.directory_ignore_set_in_cookie = frozenset()
        self.path_in_cookie = None
        self.dropbox_path = self.get_default_dropbox_path()
        self._view_loaded = False
        super(WizkitController, self).__init__()

    def get_default_dropbox_path(self):
        return default_tour_dropbox_location(self.dropbox_app, with_test=True)

    def set_current_dropbox_path(self, path):
        self.dropbox_path = os.path.normpath(path)

    def wizard_strings_class(self):
        return WizkitStrings

    @on_main_thread()
    def view_loaded(self):
        self.show_connection_trouble(self._connection_error)
        self._view_loaded = True
        self.setup_multiaccount_login()

    @on_main_thread()
    def setup_multiaccount_login(self):
        if not self.login_only and self.email:
            return
        if self.login_only:
            TRACE('MULTIACCOUNT: Setting up wizkit login for secondary. Email: %r', self.email)
            self._view.setup_multiaccount_login(self.email)

    def enter(self, linked_event, show_network_settings = None, definitely_connected = True, connection_error = False):
        self.linked_event = linked_event
        self.show_network_settings = show_network_settings
        self._connection_error = connection_error
        self.show_connection_trouble(connection_error)
        if self._view_loaded:
            self.setup_multiaccount_login()
        if self.request_thread is None and definitely_connected:
            self.request_thread = SetupWizardRequestThread(self)
            try:
                self.request_thread.start()
                self.request_thread.wizard_load_strings()
            except RuntimeError:
                unhandled_exc_handler()

    def get_text(self, key):
        return getattr(WizkitStrings, key)

    def show_menu(self, x, y):
        options = None
        options = ((WizkitStrings.single_signon, self._view.show_sso_email), (WizkitStrings.forgot_password, self.launch_forgot_password_browser))
        self._host.show_context(options, x, y)

    @property
    def window(self):
        return self._window

    def ask_yes_no(self, prompt, expl_text = None, on_yes = None, on_no = None, yes_button_text = None, no_button_text = None):
        if yes_button_text is None:
            yes_button_text = MiscStrings.ok_button
        if no_button_text is None:
            no_button_text = MiscStrings.cancel_button
        self.window.ask_yes_no(prompt, yes_button_text, no_button_text, expl_text, on_yes, on_no)

    def check_merge(self, path, on_success):
        if os.path.exists(path):

            def on_location(location):
                if location:
                    on_success(location)

            def on_cancel():
                self.check_merge(path, on_success)

            def on_no():
                self.window.choose_dropbox_location(on_location, on_cancel)

            full_explanation = WizkitStrings.merge_explanation % dict(folder_name=self.dropbox_app.default_dropbox_folder_name, folder_path=os.path.dirname(path))
            self.ask_yes_no(WizkitStrings.merge_title, full_explanation, on_yes=partial(on_success, path), on_no=on_no, yes_button_text=WizkitStrings.merge_button_ok, no_button_text=WizkitStrings.merge_button_cancel)
        else:
            on_success(path)

    @window.setter
    def window(self, value):
        self._window = value

    def linked_successfully(self, when_done):
        TRACE('wizkit acknowledged successful link')
        self.window.linked_successfully(when_done)
        if self.dropbox_app.mbox.paired:
            dropbox_name, self.dropbox_path = self.dropbox_app.mbox.derive_dropbox_name_and_path()
            self.dropbox_app.mbox.update_dropbox_path(self.dropbox_path, dropbox_name)
            TRACE('MULTIACCOUNT wizkit: derive_dropbox_name_and_path %r %r' % (dropbox_name, self.dropbox_path))
        self._linked = True
        if (self.new_account or self.dropbox_app.ui_flags.get('upgrade_prompt', False)) and not self.dropbox_app.mbox.is_secondary:
            self.show_upgrade_wrapper()
        else:
            self.show_done_panel()

    @on_main_thread()
    def show_done_panel(self, payment = False):
        self.done = True
        if self.dropbox_app.unlink_cookie and self.dropbox_app.unlink_cookie['email'] == self.email and self.dropbox_app.unlink_cookie['root_ns'] == self.root_ns and 'path' in self.dropbox_app.unlink_cookie:
            if os.path.isdir(self.dropbox_app.unlink_cookie['path']):
                try:
                    TRACE('Using old settings; ss: %r, path: %r', self.dropbox_app.unlink_cookie['unicode_rr_set'], self.dropbox_app.unlink_cookie['path'])
                    self.directory_ignore_set = self.dropbox_app.unlink_cookie['unicode_rr_set']
                    self.directory_ignore_set_in_cookie = self.directory_ignore_set
                    self.dropbox_path = self.dropbox_app.unlink_cookie['path']
                    self.path_in_cookie = self.dropbox_path
                except Exception:
                    unhandled_exc_handler()

        if payment:
            self._view.show_payments_success(self.new_account)
        else:
            self._view.show_done(self.new_account)

    @on_main_thread()
    def show_upgrade_wrapper(self):
        title = ''
        if self.new_account is True:
            title = WizkitStrings.choose_size_title
        else:
            title = WizkitStrings.upgrade_title
        self.client_plans = self.dropbox_app.ui_flags.get('plans_in_client', None)
        upgrade_array = []
        for plan_dict in self.client_plans:
            plan_info = {}
            try:
                display_info = plan_dict['display_info']
                if display_info == 'quota':
                    quota_string = self.dropbox_app.quota
                    quote_gb = format_number(float(quota_string) / 1073741824, frac_precision=0)
                    plan_info['name'] = '%s GB' % quote_gb
                    plan_info['description'] = WizkitStrings.current_plan_description
                elif display_info == 'increase':
                    plan_info['name'] = '+%s' % plan_dict['name']
                    plan_info['description'] = plan_dict['description']
                else:
                    plan_info['name'] = plan_dict['name']
                    plan_info['description'] = plan_dict['description']
            except KeyError:
                plan_info['name'] = plan_dict['name']
                plan_info['description'] = plan_dict['description']
            except Exception:
                unhandled_exc_handler()
                plan_info['name'] = plan_dict['name']
                plan_info['description'] = plan_dict['description']

            upgrade_array.append(plan_info)

        self._view.show_upgrade(title, tuple(upgrade_array), 0)

    def linked(self):
        self.linked_event.set()

    def close_window(self):
        self.window.Show(False)

    @on_main_thread()
    def show_selective_sync_settings(self):
        self.log_advanced_settings('opened_selective_sync')
        self.window.choose_selective_sync_folders()

    def printDictionary(self, d):
        TRACE('DICTIONARY: ')
        if isinstance(d, list):
            for innerdicts in d:
                if isinstance(innerdicts, tuple) or isinstance(innerdicts, list):
                    for t in innerdicts:
                        TRACE(t)

                else:
                    self.printDictionaryHelper(innerdicts, 0)

        else:
            self.printDictionaryHelper(d, 0)
        TRACE('=====')

    def printDictionaryHelper(self, d, i):
        for k, v in d.items():
            if isinstance(v, dict):
                TRACE(' ' * i + k + ':')
                self.printDictionaryHelper(v, i + 1)
            else:
                TRACE(' ' * i + k + ': ' + str(v))

    def makeDictToString(self, d):
        s = ''
        for k, v in d.items():
            if isinstance(v, dict):
                s += self.makeDictToString(v) + ' '
            else:
                s += k + ': ' + str(v) + ' '

        return s

    def launch_sso_browser(self):
        self.dropbox_app.ui_kit.copy_text_to_clipboard(u'')
        sso_url = self.dropbox_app.dropbox_url_info.construct_full_url('/sso', query_pieces=['from_client=True', 'login_email=%s' % urllib.quote(self.email.encode('utf-8'))])
        self.dropbox_app.dropbox_url_info.launch_full_url(sso_url)
        if self._user_sso_state:
            report('sso_launch_browser', user_sso_state=str(self._user_sso_state))

    def get_clipboard_link_code(self):
        self.link_code = self.dropbox_app.ui_kit.get_text_from_clipboard().strip()
        return self.link_code

    def disallow_covering(self):
        self.window.disallow_covering()

    def allow_covering(self):
        self.window.allow_covering()

    def do_sso_password(self, pw):
        self.request_thread.link_host_with_ret(self.dropbox_app.conn.host_id, self.email, None, self.display_name, True, pw, self.on_sso_password_success, self.on_sso_password_error)

    @on_main_thread()
    def on_sso_password_success(self, result_dict):
        result = result_dict.get('ret', None)
        if not result:
            report_bad_assumption('Server returned malformed result for link_host_with_ret: %r', result_dict)
        if not result or result == 'fail':
            report('sso_bad_link_code', user_sso_state=self._user_sso_state)
            self._view._back_action_handler()
            self.disallow_covering()
            self._view.set_error_with_dict(result_dict['errors'])
        elif result == 'ok':
            report('sso_successful_link_code', user_sso_state=self._user_sso_state)
            self.disallow_covering()
            self.linked()
        else:
            report_bad_assumption('Server returned unexpected value for link_host_with_ret: %r', result_dict)
            self._view.set_error_message(WizkitStrings.unexpected_error)

    @on_main_thread()
    def on_sso_password_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    def do_sso_email(self, email):
        self.email = email
        self.password = None
        self.request_thread.check_sso_user(self.dropbox_app.conn.host_id, email, self.on_sso_email_success, self.on_sso_email_error)

    @on_main_thread()
    def on_sso_email_success(self, result_dict):
        user_sso_state = result_dict.get('user_sso_state', None)
        if user_sso_state in ('required', 'optional'):
            self._user_sso_state = user_sso_state
            self._view.show_sso_pw()
        else:
            self._view.set_error_message(WizkitStrings.sso_error_email)

    @on_main_thread()
    def on_sso_email_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    @on_main_thread()
    def on_sign_in_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    @on_main_thread()
    def on_sign_in_success(self, result_dict):
        result = result_dict.get('ret', None)
        if not result:
            report_bad_assumption('Server returned malformed result for link_host_with_ret: %r', result_dict)
        if not result or result == 'fail':
            errors = result_dict['errors']
            if errors:
                self._view.set_error_with_dict(errors)
            else:
                self._view.set_error_message(WizkitStrings.unexpected_error)
        elif result == 'need_twofactor_code':
            self.checkpoint = result_dict.get('checkpoint_tkey')
            self._view.show_two_factor(result_dict.get('twofactor_text'), result_dict.get('include_send_sms_button'))
        elif result == 'ok':
            self.new_account = False
            self.linked()
        else:
            report_bad_assumption('Server returned unexpected value for link_host_with_ret: %r', result_dict)
            self._view.set_error_message(WizkitStrings.unexpected_error)

    def do_sign_in(self, email, passwd):
        self.email = email
        self.password = passwd
        self.request_thread.check_sso_user(self.dropbox_app.conn.host_id, email, self.on_sso_check_success, self.on_sso_check_error)

    @on_main_thread()
    def on_sso_check_success(self, result_dict):
        user_sso_state = result_dict.get('user_sso_state', None)
        if user_sso_state == 'required' and self.password:
            self._view.set_error_message(WizkitStrings.sso_error_entered_password)
        elif user_sso_state == 'required' or user_sso_state == 'optional' and not self.password:
            self._user_sso_state = user_sso_state
            self._view.show_sso_pw()
        else:
            self.request_thread.link_host_with_ret(self.dropbox_app.conn.host_id, self.email, self.password, self.display_name, False, None, self.on_sign_in_success, self.on_sign_in_error)

    @on_main_thread()
    def on_sso_check_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    def do_sign_up(self, fname, lname, email, passw):
        self.email = email
        fname = fname or ''
        lname = lname or ''
        email = email or ''
        passw = passw or ''
        self.request_thread.register_and_link_with_ret(self.dropbox_app.conn.host_id, fname, lname, email, passw, passw, self.display_name, self.on_sign_up_success, self.on_sign_up_error)

    @on_main_thread()
    def on_sign_up_success(self, result_dict):
        result = result_dict.get('ret')
        if not result:
            report_bad_assumption('Server returned malformed result for register_and_link_with_ret: %r', result_dict)
        if not result or result == 'fail':
            errors = result_dict.get('errors')
            if errors:
                self._view.set_error_with_dict(errors)
            else:
                self._view.set_error_message(WizkitStrings.unexpected_error)
        elif result == 'need_twofactor_code':
            self.checkpoint = result_dict.get('checkpoint_tkey')
            self._view.show_two_factor(result_dict.get('twofactor_text'), result_dict.get('include_send_sms_button'))
        elif result == 'already_registered' or result == 'ok':
            if result == 'already_registered':
                self.new_account = False
            elif result == 'ok':
                self.new_account = True
            self.linked()
        else:
            report_bad_assumption('Server returned unexpected value for register_and_link_with_ret: %r', result_dict)
            self._view.set_error_message(WizkitStrings.unexpected_error)

    @on_main_thread()
    def on_sign_up_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    def get_plans(self):
        return self.dropbox_app.ui_flags.get('plans_in_client', None)

    def get_countries(self):
        if self._countries:
            return self._countries
        try:
            self._countries = by_locale[get_current_code()]
        except KeyError:
            self._countries = by_locale[DEFAULT_CODE]

        return self._countries

    def disable_mouse_drag(self):
        if self.window and hasattr(self.window, '_dragOnInputNode'):
            self.window._dragOnInputNode = True

    def do_upgrade(self, index):
        index = int(index)
        planInfo = self.client_plans[index]
        needs_billing = None
        self.chosen_plan_index = index
        try:
            needs_billing = planInfo['needs_billing']
        except KeyError:
            unhandled_exc_handler()
            needs_billing = bool(planInfo[u'periods'])

        if needs_billing:
            textForAllPeriods = self.dropbox_app.ui_flags.get('periods', None)
            if textForAllPeriods is None:
                report_bad_assumption('Server returned unexpected value for ui_flag periods. Expected two, got null.')
            paymentOptionsList = []
            availableperiods = planInfo[u'periods']
            for p in availableperiods:
                thisPeriodsDict = dict()
                if p == u'month':
                    thisPeriodsDict['cost'] = planInfo[u'month_cost']
                elif p == u'year':
                    thisPeriodsDict['cost'] = planInfo[u'year_cost']
                else:
                    report_bad_assumption('Server returned unexpected value for plan type: %s', p)
                    thisPeriodsDict['cost'] = '0'
                try:
                    thisPeriodsDict['text'] = textForAllPeriods[p] % thisPeriodsDict['cost']
                except KeyError:
                    unhandled_exc_handler()
                    report_bad_assumption('Server returned unexpected value for plan type: %s', p)
                    thisPeriodsDict['text'] = p

                paymentOptionsList.append(thisPeriodsDict)

            self._view.show_payment(planInfo['name'], tuple(paymentOptionsList), tuple(self.get_countries()))
        else:
            self.show_done_panel()

    @on_main_thread()
    def on_payments_success(self, result_dict):
        if len(result_dict):
            self._view.set_error_with_dict(result_dict)
        else:
            self.done = True
            self.show_done_panel(payment=True)

    @on_main_thread()
    def on_payments_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    def do_payment(self, name, cnn, expmo, expyr, ccode, zipcode, country, periodIndex):
        periodIndex = int(periodIndex)
        self.cnn = cnn
        self.expmo = expmo
        self.expyr = expyr
        self.ccode = ccode
        self.zipcode = zipcode
        self.country = country
        self.name = name
        plandata = self.client_plans[self.chosen_plan_index]
        self.request_thread.client_upgrade_design_1(cnn, expmo, expyr, ccode, zipcode, country, plandata['gigabytes'], plandata['periods'][periodIndex], name, self.on_payments_success, self.on_payments_error)

    def do_two_factor(self, code):
        self.request_thread.link_host_twofactor(self.dropbox_app.conn.host_id, self.checkpoint, self.display_name, code, self.on_two_factor_success, self.on_two_factor_error)

    @on_main_thread()
    def on_two_factor_success(self, result_dict):
        result = result_dict.get('ret')
        if not result:
            report_bad_assumption('Server returned malformed result for link_host_twofactor (2FA): %r', result_dict)
        if not result or result == 'fail' or result == 'fail_abort':
            errors = result_dict.get('errors')
            if errors:
                self._view.set_error_with_dict(errors)
            else:
                self._view.set_error_message(WizkitStrings.unexpected_error)
        elif result == 'ok':
            self.linked()
        else:
            report_bad_assumption('Server returned unexpected value for link_host_twofactor (2FA): %r', result_dict)
            self._view.set_error_message(WizkitStrings.unexpected_error)

    @on_main_thread()
    def on_two_factor_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    def launch_terms_browser(self):
        url = self.dropbox_app.dropbox_url_info.construct_full_url('/terms')
        self.dropbox_app.dropbox_url_info.launch_full_url(url)

    def launch_pricing_browser(self):
        url = self.dropbox_app.dropbox_url_info.construct_full_url('/pricingterms')
        self.dropbox_app.dropbox_url_info.launch_full_url(url)

    def launch_forgot_password_browser(self):
        forgot_url = self.dropbox_app.dropbox_url_info.construct_full_url('/forgot')
        self.dropbox_app.dropbox_url_info.launch_full_url(forgot_url)

    def send_twofactor_sms(self, checkpoint_tkey, on_success, on_error):
        return self.request_thread.send_twofactor_sms(checkpoint_tkey, self.on_send_twofactor_sms_success, self.on_send_twofactor_sms_error)

    def do_send_twofactor_sms(self):
        self.send_twofactor_sms(self.checkpoint, None, None)

    @on_main_thread()
    def on_send_twofactor_sms_success(self, result_dict):
        pass

    @on_main_thread()
    def on_send_twofactor_sms_error(self, *args):
        self._view.set_error_message(WizkitStrings.unexpected_error)

    def launch_two_factor_rescue_browser(self):
        twofactor_url = self.dropbox_app.dropbox_url_info.construct_full_url('/c/help/two_step')
        self.dropbox_app.dropbox_url_info.launch_full_url(twofactor_url)

    def done_merge(self, path):
        self.dropbox_path = os.path.normpath(path)
        self.window.onFinish()
        self.request_thread.stop()

    @on_main_thread()
    def do_finish(self):
        if self.path_in_cookie and self.path_in_cookie != self.dropbox_path or not self.path_in_cookie and self.dropbox_path != self.get_default_dropbox_path():
            self.log_advanced_settings('changed_dropbox_path')
        if len(self.directory_ignore_set_in_cookie) != len(self.directory_ignore_set) or len(self.directory_ignore_set.symmetric_difference(self.directory_ignore_set_in_cookie)) > 0:
            self.log_advanced_settings('changed_selective_sync_set')
        if self.path_in_cookie and self.path_in_cookie == self.dropbox_path or self.asked_merge and self.asked_merge == self.dropbox_path:
            self.window.onFinish()
        else:
            self.check_merge(self.dropbox_path, self.done_merge)

    def exit(self):
        arch.util.hard_exit()

    @property
    def exit_caption(self):
        return WizkitStrings.exit_wizard_caption

    @property
    def exit_prompt(self):
        return WizkitStrings.exit_wizard_prompt

    @on_main_thread()
    def _show_connection_trouble(self):
        try:
            self._view.show_connection_trouble()
        except XUINotReadyError:
            TRACE("View isn't ready!")

    def reconnect_action(self):
        self.dropbox_app.conn.reconnect()

    def show_network_settings_action(self):
        if self.show_network_settings:
            self.show_network_settings()

    @on_main_thread(block=True)
    def _is_connection_trouble_showing(self):
        is_showing = False
        try:
            is_showing = bool(self._view.is_connection_trouble_showing())
        except XUINotReadyError:
            TRACE("View isn't ready!")

        return is_showing

    @on_main_thread()
    def _show_previous_panel(self):
        try:
            self._view._back_action_handler(None)
        except XUINotReadyError:
            TRACE("View isn't ready!")

    @on_main_thread()
    def show_connection_trouble(self, show = True):
        if show and not self._is_connection_trouble_showing():
            self._show_connection_trouble()
        elif not show and self._is_connection_trouble_showing():
            self._show_previous_panel()

    @on_main_thread()
    def show_location_changer(self):

        def on_location(location):
            if location:
                self.dropbox_path = os.path.normpath(location)
                self.asked_merge = self.dropbox_path
                self._view.update_dropbox_path()

        self.log_advanced_settings('opened_location_changer')
        self.window.choose_dropbox_location(on_location, None)

    def log_advanced_settings(self, key):
        report('wizkit_advanced_settings', action=key)
