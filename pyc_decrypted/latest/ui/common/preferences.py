#Embedded file name: ui/common/preferences.py
from ui.common.strings import UIStrings
from ui.common.misc import MiscStrings
from dropbox.trace import unhandled_exc_handler
from dropbox.i18n import system_lang_code, get_current_code, lang_is_fully_supported, set_user_interface_language

class SaveOnCloseError(Exception):
    pass


class PanelNames:
    GENERAL = 'general'
    ACCOUNT = 'account'
    IMPORT = 'import'
    NETWORK = 'network'
    ADVANCED = 'advanced'


class SpinnableType(object):

    @classmethod
    def validate(klass, v):
        return (klass.min is None or v > klass.min) and (klass.max is None or v < klass.max)


class ValidPort(SpinnableType):
    max = 65536
    min = 0

    @classmethod
    def from_unicode(klass, s):
        v = int(s)
        if not klass.validate(v):
            raise ValueError('port not between 0 and 65535')
        return v

    @classmethod
    def to_unicode(klass, v):
        if not klass.validate(v):
            raise ValueError('port not between 0 and 65535')
        return u'%d' % v

    @staticmethod
    def to_int(v):
        return v


class ValidBandwidth(SpinnableType):
    max = 99999
    min = 0

    @classmethod
    def from_unicode(klass, s):
        v = float(s)
        if not klass.validate(v):
            raise ValueError('bandwidth <= zero')
        return v

    @classmethod
    def to_unicode(klass, v):
        if not klass.validate(v):
            raise ValueError('bandwidth <= zero')
        if int(v) == v:
            v = int(v)
        return unicode(v)

    @staticmethod
    def to_int(v):
        return int(v)


def change_client_language(dropbox_app, new_code, prompt, on_done, on_cancel, on_restart):
    if dropbox_app.pref_controller['language'] == new_code:
        on_done()
        return
    new_code = new_code or system_lang_code()
    if new_code == get_current_code():
        dropbox_app.conn.set_web_locale(new_code)
        on_done()
        return
    if dropbox_app.sync_engine and dropbox_app.sync_engine.status.is_true('importing'):
        prompt(PrefStrings.language_while_importing, caption=PrefStrings.language_warning_caption, on_ok=lambda : None, ok_button=MiscStrings.ok_button)
        on_cancel()
        return

    def restart():
        on_restart()
        set_user_interface_language(new_code)
        dropbox_app.restart(['/updatelang'])

    if not lang_is_fully_supported(new_code):

        def on_ok():
            try:
                import arch
                arch.util.install_language_pack(new_code)
            except Exception:
                unhandled_exc_handler()
                prompt(pref_strings.install_language_pack_message, caption=pref_strings.install_language_pack_caption, on_ok=restart)
            else:
                restart()

    else:
        on_ok = restart
    prompt(pref_strings.language_restart_message, caption=pref_strings.language_restart_caption, on_ok=on_ok, ok_button=pref_strings.restart_button, on_cancel=on_cancel, cancel_button=pref_strings.cancel_button)


class PrefStrings(UIStrings):
    _platform_overrides = {'mac': {'download_label': u'Download rate:',
             'upload_label': u'Upload rate:'}}
    _strings = {'advanced_tab_label': u'Advanced',
     'main_tab_label': (u'General', u'this is the title for the "General" area of the Dropbox settings'),
     'dropbox_prefs': u'Dropbox Preferences',
     'bandwidth_colon': u'Bandwidth:',
     'bandwidth_tab_label': u'Bandwidth',
     'change_settings_button': (u'Change Settings...', u'BUTTON'),
     'download_label': u'Download rate',
     'download_limit_error': u'Download limit must be a positive number',
     'dont_limit_download': u"Don't limit",
     'speed_limit_download': u'Limit to:',
     'upload_label': u'Upload rate',
     'upload_limit_error': u'Upload limit must be a positive number',
     'dont_limit_upload': u"Don't limit",
     'auto_limit_upload': u'Limit automatically',
     'speed_limit_upload': (u'Limit to:', u'as in, limit download/upload rate to: 50 KB/sec'),
     'rate_units': (u'KB/s', u'as in, kilobytes per second, please keep it short.'),
     'download_rate': u'Download Rate',
     'invalid_download_rate': u'Enter another download rate',
     'upload_rate': u'Upload Rate',
     'invalid_upload_rate': u'Enter another upload rate',
     'invalid_port': u'Invalid Port',
     'network_tab_label': u'Network',
     'import_tab_label': u'Import',
     'proxies_colon': u'Proxies:',
     'proxy_tab_label': u'Proxies',
     'proxy_settings_label': (u'Proxy settings:', '"proxy" is a networking term, as in "proxy server". See http://en.wikipedia.org/wiki/Proxy_server'),
     'no_proxy_choice': u'No proxy',
     'auto_proxy_choice': (u'Auto-detect', "meaning, attempt to automatically determine (the user's proxy server configuration)"),
     'manual_proxy_choice': (u'Manual', 'this option lets the user enter their proxy settings themselves'),
     'proxy_type_label': u'Proxy type:',
     'proxy_server_label': (u'Server:', "meaning, the server's web address"),
     'proxy_port_label': (u'Port:', '"Port" is a networking term, short for "Port number" in this context. See http://en.wikipedia.org/wiki/TCP_and_UDP_port'),
     'proxy_requires_password_checkbox': (u'Proxy server requires a password', 'this text labels a checkbox, asking the user to answer yes (it requires a password) or no'),
     'proxy_username_label': u'Username:',
     'proxy_password_label': u'Password:',
     'proxy_port_error': u'Proxy port must be an integer between 0 and 65535',
     'proxy_server_not_set': u'Please set a proxy server',
     'proxy_server_not_set_explanation': u'You must specify a proxy server.',
     'help_label': u'Help',
     'open_source_label': (u'Dropbox uses <a href="%(url)s">open source software</a>', 'url is the url of the help page related to open source software'),
     'p2p_enabled': u'Enable LAN sync',
     'startup_item': u'Start Dropbox on system startup',
     'photo_import_enabled': u'Enable Camera Upload',
     'camera_upload_dialog_caption': u'Are you sure you wish to enable Camera Upload for your Dropbox for Business account?',
     'iphoto_import_button': u'Import Photos from iPhoto...',
     'leopard_icons': u'Use black and white menu bar icons',
     'screenshots_label': u'Screenshots',
     'screenshots': u'Share screenshots using Dropbox',
     'screenshots_multiaccount': (u'Save screenshots to your', 'This is a prefix for selecting which account (personal or business) to save screenshots to.  It is used next to a pull down menu where you can select Personal or Business account.'),
     'show_bubbles': (u'Show desktop notifications', "Meaning, show notifications on the user's desktop computer. Notifications can also be viewed from the web."),
     'language_colon': (u'Language:', u'Human Language, as in Spanish, Japanese, English, etc.'),
     'language_label': (u'Language', u'Human Language, as in Spanish, Japanese, English, etc.'),
     'language_restart_caption': u'Restarting Dropbox',
     'language_restart_message': u'Dropbox needs to restart to change the language.',
     'install_language_pack_message': u'Dropbox was unable to install the language pack for the requested language. Please install the language pack manually.',
     'install_language_pack_caption': u'Language Pack Installation',
     'language_while_importing': u"Can't change language while uploading photos",
     'language_warning_caption': u'Warning changing language',
     'no_application': u'No application',
     'account_info_with_displayname': (u'Account information for this computer (%(displayname)s)', "displayname is the computer name, eg. Brian's Mac"),
     'account_linked_to_user': (u"This computer is linked to %(user)s's (%(email)s) Dropbox account.", u'for example: "This computer is linked to Dan\'s (dan.lowe.wheeler@gmail.com) Dropbox account."'),
     'multiaccount_linked': u"This computer is linked to %(user)s's personal (%(personal_email)s) and business (%(business_email)s) Dropbox accounts.",
     'account_linked_but_not_connected': u"This computer is linked to %(email)s but hasn't connected yet",
     'account_tab_label': u'Account',
     'account_label': (u'Account:', 'meaning, the Dropbox Account being used on this computer'),
     'account_label_plain': u'Account',
     'hostdisplayname_label': u'Computer name:',
     'hostdisplayname_label_plain': u'Computer name',
     'version_label': u'Version:',
     'version_label_plain': u'Version',
     'buildkey_and_version': (u'Dropbox v%(version_string)s', 'for example, "Dropbox v0.7.111". v is a common abbreviation for version in English.'),
     'buildkey_and_version_installed': (u'Dropbox v%(version_string)s installed', 'for example, "Dropbox v0.7.111". v is a common abbreviation for version in English.'),
     'account_unlinked_display': u"This computer isn't linked to an account",
     'revert_button': (u'Revert', u'BUTTON. Instructs the program to revert the language selection to the previous choice.'),
     'restart_button': (u'Restart Dropbox', u'BUTTON. Instructs the program to restart itself.'),
     'cancel_button': (u'Cancel', u'BUTTON. This is an imperative verb.'),
     'unlink_button': (u'Unlink This Computer...', u'BUTTON'),
     'unlink_button_fix_perms': (u'Fix Permissions', 'BUTTON. "permissions" is short for "file access permissions". "Fix permissions" means, adjust any file permissions that cause Dropbox trouble. see http://en.wikipedia.org/wiki/Filesystem_permissions'),
     'unlink_button_fixing_perms': (u'Fixing Permissions...', 'BUTTON. Means that Dropbox is in the process of fixing permissions'),
     'unlink_dialog_caption': u'Are you sure you want to unlink this computer from Dropbox?',
     'unlink_dialog_caption_short': u'Unlink Dropbox?',
     'unlink_dialog_caption_short_with_displayname': (u'Unlink %(displayname)s from Dropbox?', "displayname is the computer name, eg. Brian's Mac"),
     'unlink_dialog_message': u"This will stop syncing your files with Dropbox, but won't delete the files in the Dropbox folder on this computer.",
     'unlink_warning_caption': u'Warning unlinking Dropbox',
     'unlink_while_importing': u"Can't unlink Dropbox while uploading photos",
     'fix_perms_really_bad_error_caption': u'Unexpected Error',
     'fix_perms_really_bad_error_message': u'Dropbox was unable to fix permissions in your Dropbox. Please contact support if the problem persists.',
     'fix_perms_worked_caption': u'Success',
     'fix_perms_worked_message': u'Dropbox successfully repaired the permissions in your Dropbox.',
     'loc_changer_label': (u'Dropbox location', 'meaning, location of the Dropbox folder'),
     'loc_changer_label_colon': u'Dropbox location:',
     'loc_changer_select_title': u'Select a Folder',
     'loc_changer_select_button': (u'Select', u'BUTTON'),
     'loc_changer_select_message1': u'Choose a new place for your Dropbox.',
     'loc_changer_select_message2': u'A folder named "%(folder_name)s" will be created inside the folder you select.',
     'loc_changer_move_confirm_caption': (u'Are you sure?', u'this is a generic confirmation message, meaningare you sure you want to do this action?'),
     'loc_changer_move_confirm_message': u'This will move the Dropbox folder and all the files inside from its current location to %(folder_name)s.',
     'loc_changer_move_confirm_button': (u'Move', u'BUTTON'),
     'loc_changer_move_progress_indeterminate': (u'Moving Dropbox...', u'meaning: in the process of moving Dropbox'),
     'loc_changer_move_progress_determinate_t': (u'Moving Dropbox (%(completed)s / %(total)s files)', u' meaning: in the process of moving dropbox for example: Moving Dropbox (17 / 50 files) where 17 / 50 means: 17 of the total 50 files have been moved so far'),
     'loc_changer_title_moving_dropbox': (u'Moving Dropbox', u'meaning: in the process of moving Dropbox'),
     'loc_changer_sel_folder_error': u'Error with selected folder',
     'loc_changer_dialog_merge_question': u"There's already a folder here called %s. Do you want to add all the files in that folder to your Dropbox?",
     'loc_changer_dialog_merge_is_file': u'There is a file here called %s. Please select a different location.',
     'loc_changer_moving_warning': u'Warning moving Dropbox',
     'loc_changer_unexpected_error': u"An unexpected error occurred while moving your Dropbox folder. Don't worry, your files are still safe.",
     'loc_changer_unexpected_problem': u'An unexpected problem occurred. The Dropbox team has been notified.',
     'loc_changer_error_moving': u'Error moving Dropbox',
     'loc_changer_move_dotdotdot': (u'Move...', u'BUTTON'),
     'loc_changer_change_dotdotdot': (u'Change...', u'BUTTON'),
     'other_dotdotdot': (u'Other...', u'As in something not on the list'),
     'camera_label': u'Camera Upload',
     'camera_message': u'Import photos and videos to Dropbox',
     'camera_launch_button': u'Install Camera Upload',
     'camera_launch_link': u'<a href="AutoPlay Settings">Change AutoPlay Settings</a>',
     'photo_library_import_label': u'Import Pictures',
     'photo_library_import_message': u'Move your pictures library to Dropbox',
     'photo_library_import_button': u'Move Pictures Library'}


pref_strings = PrefStrings
