#Embedded file name: ui/common/setupwizard.py
from __future__ import absolute_import
import collections
import os
import re
import json
import time
import urllib
from functools import partial
import arch
from client_api.connection_hub import DropboxServerError
from dropbox.event import report
from dropbox.features import feature_enabled
from dropbox.gui import assert_message_queue
from dropbox.i18n import get_country_code, get_current_code
from dropbox.language_data import DEFAULT_CODE
from dropbox.native_event import AutoResetEvent
from dropbox.native_threading import NativeCondition
from dropbox.platform import platform
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from .countries import by_locale
from .misc import MiscStrings
from .phonecodes import PHONECODES
from .strings import UIStrings
if platform == 'win':
    from dropbox.win32.version import VISTA, WINDOWS_VERSION
DISALLOW_PREV = 'disallow_prev_button'
SSO_ENABLED = True
if platform == 'mac':
    from ..cocoa.constants import Images
else:
    from ..images import wximages as Images

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


class SetupWizardStrings(UIStrings):
    _strings = dict(advanced_choice=(u'Advanced', 'as in, "advanced installation setup"'), advanced_description=u"Choose a location for your Dropbox and select the folders you'd like to sync.", advanced_install_location=(u'Advanced setup - Dropbox location', 'the title for one part of advanced setup'), advanced_install_ss=(u'Advanced setup - Selective Sync', 'the title for another part of advanced setup'), arrow_explanation=u'Click the icon to open your Dropbox folder, access the Dropbox website, get help, and change your preferences.', arrow_note=u'A green arrow on your screen shows the location of the Dropbox menu bar icon.', billing_address_label=(u'Billing address:', u'SHORT'), billing_city_label=(u'City:', u'SHORT'), billing_country_label=(u'Country:', u'SHORT'), billing_name_label=(u"Cardholder's name:", u'SHORT'), billing_state_label=(u'State/Province:', u'SHORT'), billing_title=(u'Billing information', u'SHORT'), billing_zip_label=(u'ZIP:', u'SHORT. This is for ZIP code; aka post code in many countries.'), ccn_label=(u'Card number:', u'SHORT'), ccode_tip1=u'VISA and Mastercard: The last 3 digits on the back', ccode_tip2=u'American Express: A 4 digit number on the front', choose_size_title=(u'Select your Dropbox size', 'as in Dropbox plan size, for example. 50GB or 100GB'), computer_name_label=u'Computer name:', computer_name_sublabel=(u"(e.g. Drew's Laptop)", 'an example of a computer name. feel free to translate "Drew" into a common name for this language.'), connection_options_button=(u'Connection Options...', 'connection refers to internet connection'), connection_trouble_title=u'Connection Error', continue_with_normal_setup_choice=u'Continue with full setup', custom_dropbox_choice=u'I want to choose where to put my Dropbox', cvn_label=(u'CVN:', 'SHORT. card verification number. If there isnt a corresponding 3 or 4-letter abbreviation in the target language, keep it untranslated.'), default_dropbox_choice=u'Put Dropbox in my home folder', default_dropbox_choice_new_windows=(u'Install the Dropbox folder in the "%(path)s" folder', u'path is a file path, e.g. C:\\Documents and Settings'), default_or_advanced_title=(u'Choose setup type', 'setup type is either typical or advanced'), dropbox_error_title=u'Dropbox Error', dropbox_explanation=u'Dropbox is a special folder on your computer. Simply drop your files into the Dropbox folder and they will instantly appear on all your devices and at Dropbox.com.', dropbox_missing_title=(u'Dropbox Folder Missing', u'Abbreviation for: "your Dropbox folder is missing". SHORT'), dropbox_missing_text1=u'Your Dropbox folder has been moved or deleted from its original location. Dropbox will not work properly until you move it back. It used to be located at:', dropbox_missing_text2=(u'To move it back, click "%(exit_button)s" below, move the Dropbox folder back to its original location, and launch Dropbox again.', u'exit_button is the button label that they should click on'), dropbox_missing_text3=(u'If you\'d like to link to an account again to download and restore your Dropbox from the web version, click "%(relink_button)s".', u'relink_button is the button label that they should click on'), dropbox_linked=(u'This computer is now linked to Dropbox! Files in your Dropbox folder automatically sync and backup online.', u'note: sync and backup are both verbs here.'), dropbox_linked_title=u'Linked to Dropbox!', email_label=u'Email:', email_placeholder=(u'drew@dropbox.com', 'an example email address. feel free to translate drew into a common name for this language.'), existing_account_choice=u'I already have a Dropbox account', exit_tour_button=(u'Skip Tour', u'BUTTON'), exit_wizard_button=(u'Exit', u'BUTTON'), exit_tour_caption=(u'Skip Dropbox Tour?', u'abbreviation for: "skip the Dropbox tour?'), exit_wizard_caption=u'Exit Dropbox?', exit_tour_prompt=u'Are you sure you want to skip the Dropbox tour?', exit_wizard_prompt=u'Are you sure you want to exit Dropbox?', expdate_label=(u'Expiration date:', u'as in, credit card expiration date. SHORT'), finish_button=(u'Finish', 'as in, finish the installation process'), first_name_label=(u'First name:', 'feel free to translate this as "nickname" if it\'s uncommon to give a first name for this language.'), first_name_placeholder=(u'Drew', u"This is an example first name. Feel free to translate 'Drew' into a common name for the given language."), forgot_password_label=(u'Forgot password?', u'SHORT for "Have you forgotten your password?"'), install_button=(u'Install', u'BUTTON - this should be a verb'), last_name_label=(u'Last name:', u'SHORT'), last_name_placeholder=(u'Houston', 'an example last name. feel free to translate into a common last name for this language.'), link_this_computer=u'Link this computer to a Dropbox account', login_title=u'Log in to Dropbox', menu_icon_title=(u'The Dropbox Menu Bar Icon', u"the dropbox menu bar icon is the little icon on the user's desktop screen, to the lower right of the screen on windows, or upper right on mac"), merge_title=u'Merge with existing Dropbox folder?', merge_explanation=u"There's already a folder called %(folder_name)s in %(folder_path)s. Do you want to merge all the existing files in that folder into your Dropbox or choose another location for your Dropbox?", merge_button_ok=(u'Merge', u'verb, as in, to merge two folders. BUTTON'), merge_button_cancel=u'Choose Another Location', mobile_button=(u'Send', u'BUTTON'), mobile_example=(u'Ex: %(number)s', u'SHORT Short for "example"; this is followed by a fictitious mobile number'), mobile_label1=u'Mobile phone number', mobile_label2=u'(optional):', mobile_malformed_number=(u'Invalid phone number.', u'SHORT'), mobile_setup_explanation=u"Enter your mobile phone number below and we'll text you a link to get Dropbox on your phone.", mobile_setup_header=u'Set up your mobile device to access your stuff from anywhere.', mobile_setup_title=u'Set up your smartphone', modify_defaults_choice=u'Modify default settings (Advanced)', new_account_choice=u"I don't have a Dropbox account", next_button=(u'Next', u'BUTTON'), os_name=(u'Windows', 'The short name for  Microsoft Windows.'), password_label=(u'Password:', u'SHORT'), password_strength_label=(u'Password Strength:', u'SHORT'), password_strength_very_weak=u'Very weak', password_strength_weak=u'Weak', password_strength_okay=u'So-so', password_strength_good=u'Good', password_strength_great=u'Great!', plan_choice_label=u'Pricing terms', previous_button=(u'Previous', u'BUTTON'), previous_installation_text=u'This computer was previously linked to %(email_address)s. Would you like to install Dropbox using the settings from that account? These include Dropbox location and selective sync preferences.', previous_installation_title=u'Install with previous settings?', previous_link_email=(u"This computer was previously linked to %(email)s's account.", u'The apostrophe and s should be translated to a possessive.'), previously_linked_better=u"This computer was previously linked to %(email)s's account.", progress_text=(u'Part %(current_panel)s of %(total_panels)s', u"for example 'Part 3 of 4'"), proxy_server_text=u'If your computer connects to the Internet through a proxy, please specify your settings here.', reconnect_now_button=(u'Reconnect Now', u'BUTTON'), relink_button=(u'Relink', u'BUTTON'), relink_confirmation1=u'Are you sure you want to unlink Dropbox?', relink_confirmation2=u'Dropbox will restart and help you relink your account.', requesting_link=u'Connecting to Dropbox...', requesting_upgrade=u'Connecting to Dropbox...', share_folders_explanation=u'You can share any folder in your Dropbox with friends or colleagues, even if they use a different operating system than you. ', share_folders_title=u'Share folders with people you know', signup_title=u'Create your Dropbox', skip_button=(u'Skip Tour', u'BUTTON'), ssl_info=(u'All transactions are secured with SSL', 'SSL stands for Secure Socket Layer, probably best to leave untranslated'), sync_all_choice=u'I want this computer to sync all of the folders in my Dropbox', sync_some_choice=u'I want to choose which folders to sync to this computer', terms_of_service_checkbox_link=(u'I have read and agree to the <a href="%(url)s">Terms of Service</a>.', u'SHORT. This must be a direct translation and include the words read and agree'), thats_it_checkbox=u'Open my Dropbox folder now', thats_it_text=u"Dropbox has finished installing. You're all set up and ready to go. We hope you enjoy Dropbox!", thats_it_title=(u"That's it!", 'this means, setup is complete'), tour_welcome_title=u'Welcome to Dropbox, %(first_name)s!', twofactor_label=u'Security code:', twofactor_text=u'In order to link your computer, you need to enter a security code. We sent the code as a text message to your mobile phone.', twofactor_link=(u'<a href="%(url)s">I need more help</a>', u'This help link is provided when users enter the verification code for two factor authentication.'), twofactor_title=u'Enter security code', twofactor_send_sms_button=u'Send New Code', twofactor_sending_sms=u'Sending code...', typical_choice=(u'Typical', 'refers to the Typical (basic) install type, as opposed to Advanced'), typical_description=u'Set up Dropbox with normal settings.', typical_sublabel=(u'(recommended)', u'as in, this option is recommended'), unexpected_error=u'An unexpected error occurred. Please try again later.', unlink_problem1=u"You tried to unlink Dropbox but something went wrong. This is probably because Dropbox doesn't have permissions to delete certain configuration files from your computer.", unlink_problem2=u'To learn how to delete these files manually, visit: <a href="%(unlink_help_url)s">%(unlink_help_url)s</a>.', unlink_title=u'Failed to unlink Dropbox', upgrade_title=(u'Upgrade your Dropbox?', 'meaning, upgrade the Dropbox desktop application?'), use_previous_settings_choice=u'Use previous settings (recommended)', verify_password_label=u'Verify password:', waiting_for_connection=u'Waiting For Connection...', waiting_for_server=u'Waiting for server...', window_title=u'Dropbox Setup', web_interface_title=u'Access your files from anywhere using dropbox.com', web_interface_instructions=u'If you need to access your files from someone else\'s computer, simply log in to <a href="%(website_url)s">%(website)s</a>. You can view, download, and upload your files securely from any web browser.', welcome_title=u'Welcome to Dropbox', xattr_enable_choice=(u'Yes, turn on syncing for extended file attributes (may require root password)', 'root, as in root user (superuser), is a technical term. see http://en.wikipedia.org/wiki/Root_user "extended file attributes" is also a technical term, see http://en.wikipedia.org/wiki/Extended_file_attributes'), xattr_disable_choice=(u"No, don't modify my mount settings", 'mount is a technical term, see http://en.wikipedia.org/wiki/Mount_(computing)'), xattr_error=(u"Dropbox can't set user_xattr in /etc/fstab.  Please set this manually.", u'user_xattr is a configuration parameter, and /etc/fstab is a location. Please leave both terms untranslated.'), xattr_title=(u'Advanced setup - Extended attributes', u'the title for one part of advanced setup. "extended attributes" is a technical term, see http://en.wikipedia.org/wiki/Extended_file_attributes'), secure_connection_error=u"Dropbox can't make a secure connection because your computer's date and time are incorrect. Please update your date and time settings.", secure_connection_error_title=u"Dropbox can't make a secure connection", sso_error_entered_password=u'To use single sign-on, enter your email without a password.', sso_launch_link_text=u'Get your link code', sso_detected_text=u'First, click the button below to get your link code on the web.', sso_login_title=u'Connect to Dropbox', sso_paste_instructions=u'Then enter your link code below:', sso_paste_button=u'Paste')
    _platform_overrides = dict(linux=dict(advanced_description=u"Choose your Dropbox's location, which folders will be synced, and if extended attributes should be synced.", arrow_note=u'', menu_icon_title=u'The Dropbox Notification Area Icon'), mac=dict(exit_wizard_button=(u'Quit', u'BUTTON'), exit_wizard_caption=u'Quit Dropbox Setup?', exit_wizard_prompt=u'Are you sure you want to quit Dropbox setup?', next_button=(u'Continue', u'BUTTON'), previous_button=(u'Go Back', u'BUTTON')), win=dict(arrow_note=u'A green arrow on your screen shows the location of the Dropbox notification area icon.', default_dropbox_choice=u"Install the Dropbox folder in the 'My Documents' folder", merge_button_cancel=u'Choose another location', menu_icon_title=u'The Dropbox Notification Area Icon', skip_button=(u'Skip tour', u'BUTTON'), waiting_for_connection=u'Waiting for connection...'))


class Panel(object):

    def __init__(self, wizard):
        self._wizard = wizard
        self._focus_attr = None
        self._form_contents = []
        self.default_values = {}

    def _normal_prev_button(self):
        return (SetupWizardStrings.previous_button, u'prev')

    def _normal_next_button(self):
        return (SetupWizardStrings.next_button, u'next')

    def add_form_item(self, item):
        self._form_contents.append(item)
        item.add_default_value(self)

    def set_initial_focus_on_control(self, attr):
        self._focus_attr = attr

    @property
    def form_contents(self):
        return self._form_contents

    @property
    def focus_attr(self):
        return self._focus_attr

    @property
    def buttons(self):
        if not hasattr(self, '_buttons'):
            return None
        if self.get_prev_panel() != DISALLOW_PREV:
            return self._buttons
        return [ b for b in self._buttons if b[1] != 'prev' ]

    @property
    def background_image(self):
        return getattr(self, '_background_image', None)

    @property
    def title(self):
        return getattr(self, '_title', None)

    @property
    def next(self):
        return getattr(self, '_next', None)

    @property
    def prev(self):
        return getattr(self, '_prev', None) or self.get_prev_panel()

    def get_prev_panel(self):
        return getattr(self, '_dynamic_prev_panel', None)

    def set_prev_panel(self, value):
        TRACE('Setting dynamic prev panel value for %s to %s', self.__class__.__name__, value)
        self._dynamic_prev_panel = value

    @property
    def full_sized_form(self):
        return getattr(self, '_full_sized_form', False)

    @property
    def left_side_image(self):
        return getattr(self, '_left_side_image', None)

    @property
    def left_side_image_padding(self):
        return getattr(self, '_left_side_image_padding', 0)

    @property
    def panel_title_lower_padding(self):
        return getattr(self, '_panel_title_lower_padding', 0)

    @property
    def tour(self):
        return getattr(self, '_tour', False)

    @property
    def advanced(self):
        return getattr(self, '_advanced', False)

    @property
    def form_is_valid(self):
        return True

    def form_item_changed(self, attr, new_value):
        pass

    def on_swap_out(self):
        TRACE('Panel %s swapping out' % self.__class__.__name__)

    def on_swap_in(self):
        TRACE('Panel %s swapping in' % self.__class__.__name__)


class ControlDescriptor(object):

    def __init__(self, attr, label, default_value, hide_on = [], disabled = False):
        self._attr = attr
        self._label = label
        self._default_value = default_value
        self._hide_on = hide_on
        self._disabled = disabled

    @property
    def attr(self):
        return self._attr

    @property
    def label(self):
        return self._label

    @property
    def default_value(self):
        return self._default_value

    @property
    def disabled(self):
        return self._disabled

    @property
    def hide_on(self):
        return self._hide_on

    def add_default_value(self, panel):
        if self.attr is not None:
            panel.default_values[self.attr] = self.default_value
            setattr(panel, self.attr, self.default_value)


class Button(ControlDescriptor):

    def __init__(self, attr, label, action, hide_on = []):
        super(Button, self).__init__(attr, label, None, hide_on=hide_on)
        self._action = action

    @property
    def action(self):
        return self._action


class Checkbox(ControlDescriptor):

    def __init__(self, attr, label, default_value = False, left_align = False, bottom_align = False, checked = False, center = False, hide_on = []):
        super(Checkbox, self).__init__(attr, label, bool(default_value), hide_on=hide_on)
        self._bottom_align = bottom_align
        self._checked = checked
        self._left_align = left_align
        self._center = center

    @property
    def center(self):
        return self._center

    @property
    def bottom_align(self):
        return self._bottom_align

    @property
    def checked(self):
        return self._checked

    @property
    def left_align(self):
        return self._left_align


class CheckboxLink(Checkbox):
    pass


class Choice(ControlDescriptor):

    def __init__(self, attr, label, choices, default_value = 0, width = -1, hide_on = []):
        super(Choice, self).__init__(attr, label, default_value, hide_on=hide_on)
        self._choices = choices
        self._width = width

    @property
    def choices(self):
        return self._choices

    @property
    def width(self):
        return self._width


class FlagChoice(Choice):
    pass


class CreditCardType(ControlDescriptor):

    def __init__(self, attr, hide_on = []):
        super(CreditCardType, self).__init__(attr, None, None, hide_on=hide_on)


class Date(ControlDescriptor):

    def __init__(self, attr, label, hide_on = []):
        super(Date, self).__init__(attr, label, None, hide_on=hide_on)


class FancyRadioGroup(ControlDescriptor):

    def __init__(self, attr, choices, default_value = 0, hide_on = []):
        super(FancyRadioGroup, self).__init__(attr, None, int(default_value), hide_on=hide_on)
        self._choices = choices

    @property
    def choices(self):
        return self._choices


class AdvancedPanelRadioGroup(FancyRadioGroup):

    def __init__(self, attr, choices, embedded_controls, default_value = 0, hide_on = []):
        super(AdvancedPanelRadioGroup, self).__init__(attr, choices, default_value, hide_on=hide_on)
        self._embedded_controls = embedded_controls

    @property
    def embedded_controls(self):
        return self._embedded_controls


class HelpButton(ControlDescriptor):

    def __init__(self, hover_text, url = None, hide_on = []):
        super(HelpButton, self).__init__(None, None, None, hide_on=hide_on)
        self._hover_text = hover_text
        self._url = url

    @property
    def hover_text(self):
        return self._hover_text

    @property
    def url(self):
        return self._url


class HorizSpacer(ControlDescriptor):

    def __init__(self, width = 100, hide_on = []):
        super(HorizSpacer, self).__init__(None, None, None, hide_on=hide_on)
        self._width = width

    @property
    def width(self):
        return self._width


class Image(ControlDescriptor):

    def __init__(self, image, label, border = False, inline = False, bottom_align = False, hide_on = []):
        super(Image, self).__init__(None, None, None, hide_on=hide_on)
        self._image = image
        self._label = label
        self._border = border
        self._inline = inline
        self._bottom_align = bottom_align

    @property
    def image(self):
        return self._image

    @property
    def label(self):
        return self._label

    @property
    def border(self):
        return self._border

    @property
    def inline(self):
        return self._inline

    @property
    def bottom_align(self):
        return self._bottom_align


class ExampleText(ControlDescriptor):

    def __init__(self, attr, text, hide_on = []):
        super(ExampleText, self).__init__(attr, None, None, hide_on=hide_on)
        self._text = text

    @property
    def text(self):
        return self._text


class LocationChanger(ControlDescriptor):

    def __init__(self, attr, default_value = None, hide_on = []):
        super(LocationChanger, self).__init__(attr, None, default_value, hide_on=hide_on)


class MultiControlLine(ControlDescriptor):

    def __init__(self, controls, close_spacing = False, hide_on = []):
        super(MultiControlLine, self).__init__(None, None, None, hide_on=hide_on)
        self._close_spacing = close_spacing
        self._controls = controls

    @property
    def close_spacing(self):
        return self._close_spacing

    @property
    def controls(self):
        return self._controls

    def add_default_value(self, panel):
        for c in self.controls:
            c.add_default_value(panel)


class MultiControlLineSimple(MultiControlLine):
    pass


class CenteredMultiControlLine(ControlDescriptor):

    def __init__(self, controls, offset = 0, hide_on = []):
        super(CenteredMultiControlLine, self).__init__(None, None, None, hide_on=hide_on)
        self._controls = controls
        self._offset = offset

    @property
    def controls(self):
        return self._controls

    @property
    def close_spacing(self):
        return True

    @property
    def offset(self):
        return self._offset


class PlanChoices(ControlDescriptor):

    def __init__(self, attr, choices, default_value = None, hide_on = []):
        super(PlanChoices, self).__init__(attr, None, default_value, hide_on=hide_on)
        self._choices = choices

    @property
    def choices(self):
        return self._choices


class RadioGroup(ControlDescriptor):

    def __init__(self, attr, choices, default_value = 0, vertical_spacing = None, max_width = None, hide_on = []):
        super(RadioGroup, self).__init__(attr, None, int(default_value), hide_on=hide_on)
        self._choices = choices
        self._vertical_spacing = vertical_spacing
        self._max_width = max_width

    @property
    def choices(self):
        return self._choices

    @property
    def vertical_spacing(self):
        return self._vertical_spacing

    @property
    def max_width(self):
        return self._max_width


class SelectiveSync(ControlDescriptor):

    def __init__(self, attr, hide_on = []):
        super(SelectiveSync, self).__init__(attr, None, None, hide_on=hide_on)


class Spacer(ControlDescriptor):

    def __init__(self, size, hide_on = []):
        super(Spacer, self).__init__(None, None, None, hide_on=hide_on)
        self._size = size

    @property
    def size(self):
        return self._size


class FancyGauge(ControlDescriptor):
    if platform == 'mac':
        DEFAULT_WIDTH = 225
    else:
        DEFAULT_WIDTH = 200

    def __init__(self, attr, label, meters, colors, width = DEFAULT_WIDTH, hide_on = [], skip = 1):
        super(FancyGauge, self).__init__(attr, None, None, hide_on=hide_on)
        assert len(colors) > 0, 'Must pass in a non-empty color list'
        self._width = width
        self._meters = meters
        self._label = label
        self._colors = colors
        self._default_color = colors[0]
        self._skip = skip

    @property
    def label(self):
        return self._label

    @property
    def width(self):
        return self._width

    @property
    def meters(self):
        return self._meters

    @property
    def colors(self):
        return self._colors

    @property
    def default_color(self):
        return self._default_color

    @property
    def skip(self):
        return self._skip


class TextBlock(ControlDescriptor):

    def __init__(self, text, center = False, right_align = False, bottom_align = False, bold = False, greedy = True, size_diff = 0, line_height = 0, hide_on = []):
        super(TextBlock, self).__init__(None, None, None, hide_on=hide_on)
        self._bold = bold
        self._bottom_align = bottom_align
        self._center = center
        self._greedy = greedy
        self._line_height = line_height
        self._right_align = right_align
        self._size_diff = size_diff
        self._text = text

    @property
    def bold(self):
        return self._bold

    @property
    def bottom_align(self):
        return self._bottom_align

    @property
    def center(self):
        return self._center

    @property
    def greedy(self):
        return self._greedy

    @property
    def line_height(self):
        return self._line_height

    @property
    def right_align(self):
        return self._right_align

    @property
    def size_diff(self):
        return self._size_diff

    @property
    def text(self):
        return self._text


class TextInput(ControlDescriptor):
    if platform == 'mac':
        DEFAULT_WIDTH = 225
    else:
        DEFAULT_WIDTH = 200

    def __init__(self, attr, label, default_value = u'', placeholder = None, secure = False, sublabel = None, width = DEFAULT_WIDTH, disabled = False, hide_on = []):
        default_value = unicode_clean(default_value)
        super(TextInput, self).__init__(attr, label, default_value, hide_on=hide_on, disabled=disabled)
        self._placeholder = placeholder
        self._secure = secure
        self._sublabel = sublabel
        self._width = width

    @property
    def placeholder(self):
        return self._placeholder

    @property
    def secure(self):
        return self._secure

    @property
    def sublabel(self):
        return self._sublabel

    @property
    def width(self):
        return self._width


class SetupWizardWindowBase(object):

    def _create_contents_and_fill(self):
        raise NotImplementedError('Subclasses of SetupWizardWindowBase must implement _create_contents_and_fill')

    def _mark_label_as_error(self, error_msg):
        raise NotImplementedError('Subclasses of SetupWizardWindowBase must implement _mark_label_as_error')

    def _update_next_button(self):
        raise NotImplementedError('Subclasses of SetupWizardWindowBase must implement _update_next_button')

    def set_form_status(self, status, error = False):
        raise NotImplementedError('Subclasses of SetupWizardWindowBase must implement set_form_status')

    def show_window(self):
        raise NotImplementedError('Subclasses of SetupWizardWindowBase must implement show_window')

    def _handle_action(self, action):
        if callable(action):
            self._wizard.append_to_tour_route(action.__name__)
            action()
        elif callable(getattr(self, action, None)):
            a = getattr(self, action)
            self._wizard.append_to_tour_route(a.__name__)
            a()
        elif callable(getattr(self._wizard, action, None)):
            a = getattr(self._wizard, action)
            self._wizard.append_to_tour_route(a.__name__)
            a()
        else:
            TRACE('Unknown action: %s' % action)

    def highlight_invalid_fields(self, field_dict):
        error_set = False
        if 'flash' in field_dict:
            error_set = True
            self.set_form_status(field_dict['flash'], True)
        expanded_contents = []
        for item in self.current_panel.form_contents:
            if isinstance(item, MultiControlLine) or hasattr(item, 'controls'):
                for ctl in item.controls:
                    expanded_contents.append(ctl)

            else:
                expanded_contents.append(item)

        if 'expmo' in field_dict:
            field_dict['exp'] = field_dict['expmo']
        elif 'expyr' in field_dict:
            field_dict['exp'] = field_dict['expyr']
        for attr_name in [ x.attr for x in expanded_contents if x.attr ]:
            if attr_name in field_dict:
                err_msg = field_dict[attr_name]
                self._mark_label_as_error(attr_name, True)
                if not error_set and err_msg:
                    error_set = True
                    self.set_form_status(err_msg, True)
            elif attr_name in self.labels:
                self._mark_label_as_error(attr_name, False)

        if not error_set:
            self.set_form_status('')

    @assert_message_queue
    def update_panel_attr(self, event_object, val, quiet = False):
        if event_object not in self.current_controls:
            TRACE('Received event from unregistered control: %r, %r', event_object, self.current_controls)
            return
        setattr(self.current_panel, self.current_controls[event_object], val)
        if not quiet:
            TRACE("Panel attribute '%r' changed. New value is '%r'" % (self.current_controls[event_object], val))
        self.current_panel.form_item_changed(self.current_controls[event_object], val)
        self._update_next_button()

    @property
    def current_panel(self):
        return self._wizard.current_panel


class WelcomePanel(Panel):

    def __init__(self, wizard):
        super(WelcomePanel, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [self._normal_next_button()]
        self._title = SetupWizardStrings.welcome_title
        self._full_sized_form = True
        self.add_form_item(Spacer(55))
        self.add_form_item(Image(Images.SetupWizardLogo, None, inline=True))
        self.add_form_item(Spacer(25))
        self.add_form_item(RadioGroup('have_dropbox_account', choices=[SetupWizardStrings.new_account_choice, SetupWizardStrings.existing_account_choice], vertical_spacing=25, max_width=325))

    @property
    def _next(self):
        if self.have_dropbox_account == 0:
            return SignupPanel
        elif self.have_dropbox_account == 1:
            return LoginPanel
        else:
            return None

    def on_swap_in(self):
        self._wizard.on_wizard_start()


class LoginPanelBase(Panel):

    def _unknown_error(self):
        self._wizard.enable_buttons()
        self._wizard.highlight_invalid_fields({})
        self._wizard.set_form_status(SetupWizardStrings.unexpected_error, True)

    def _display_errors(self, errors = None):
        self._wizard.highlight_invalid_fields(errors)
        self._wizard.enable_buttons()

    def _login_success(self, new_account):
        self._wizard.new_account = new_account
        self._wizard.highlight_invalid_fields({})
        self._wizard.set_form_status(SetupWizardStrings.waiting_for_server)
        self._wizard.successfully_linked()

    def _pre_link(self):
        self._wizard.set_form_status(SetupWizardStrings.requesting_link)
        self._wizard.disable_buttons()


class SsoLoginPanel(LoginPanelBase):

    def __init__(self, wizard, sso_email, display_name, user_sso_state):
        super(SsoLoginPanel, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.previous_button, self.prev_panel), (SetupWizardStrings.next_button, self.try_login)]
        self._full_sized_form = True
        self._title = SetupWizardStrings.sso_login_title
        self._next = UpgradeChoices
        self._user_sso_state = user_sso_state
        self.display_name = display_name
        try:
            host = arch.util.gethostname()
            report('sso_show_sso_login_panel', user_sso_state=self._user_sso_state)
        except Exception:
            unhandled_exc_handler()
            host = u''

        self.email = sso_email
        form_items = [Spacer(90, hide_on=['win', 'linux']),
         CenteredMultiControlLine([TextBlock(SetupWizardStrings.sso_detected_text, right_align=False, greedy=False)]),
         Spacer(10),
         CenteredMultiControlLine([Button('sso_launch_browser', SetupWizardStrings.sso_launch_link_text, self.on_sso_launch_browser)]),
         Spacer(30),
         CenteredMultiControlLine([TextBlock(SetupWizardStrings.sso_paste_instructions, right_align=False, greedy=False)]),
         Spacer(10),
         CenteredMultiControlLine([Button('sso_paste_link_code', SetupWizardStrings.sso_paste_button, self.on_paste_link_code), HorizSpacer(5), TextInput('link_code', u'', secure=False)])]
        for item in form_items:
            self.add_form_item(item)

    def on_sso_launch_browser(self):
        self._wizard.allow_covering()
        self._wizard.copy_text_to_clipboard(u'')
        sso_url = self._wizard.dropbox_app.dropbox_url_info.construct_full_url('/sso', query_pieces=['from_client=True', 'login_email=%s' % urllib.quote(self.email.encode('utf-8'))])
        self._wizard.dropbox_app.dropbox_url_info.launch_full_url(sso_url)
        report('sso_launch_browser', user_sso_state=self._user_sso_state)

    def on_paste_link_code(self):
        self.link_code = self._wizard.get_text_from_clipboard().strip()
        self._wizard.set_control_value('link_code', self.link_code)
        self._wizard.window._update_next_button()
        if self.link_code:
            self.try_login()

    @property
    def form_is_valid(self):
        return bool(getattr(self, 'link_code', None))

    def prev_panel(self):
        self._wizard.disallow_covering()
        self._wizard.prev()

    def on_success(self, result_dict):
        result = result_dict.get('ret', None)
        if not result:
            report_bad_assumption('Server returned malformed result for link_host_with_ret: %r', result_dict)
        if not result or result == 'fail':
            report('sso_bad_link_code', user_sso_state=self._user_sso_state)
            self._wizard.append_to_tour_route('try_login_bad')
            self._display_errors(result_dict['errors'])
        elif result == 'ok':
            report('sso_successful_link_code', user_sso_state=self._user_sso_state)
            self._wizard.disallow_covering()
            self._wizard.append_to_tour_route('try_login_good')
            self._login_success(new_account=False)
        else:
            report_bad_assumption('Server returned unexpected value for link_host_with_ret: %r', result_dict)
            self._display_errors()

    def on_error(self, *args):
        self._wizard.append_to_tour_route('try_login_error')
        self._unknown_error()

    def try_login(self):
        self._pre_link()
        self._wizard.link_host_with_ret(self._wizard.dropbox_app.conn.host_id, self.email, None, self.display_name, True, self.link_code, self.on_success, self.on_error)


class LoginPanel(LoginPanelBase):

    def __init__(self, wizard):
        super(LoginPanel, self).__init__(wizard)
        secondary = self._wizard.dropbox_app.mbox.is_secondary
        self._background_image = Images.SetupWizardBackground
        if secondary:
            self._buttons = [(SetupWizardStrings.next_button, self.try_login)]
            email_input = TextInput('email', SetupWizardStrings.email_label, default_value=self._wizard.email_address, disabled=True)
        else:
            self._buttons = [(SetupWizardStrings.previous_button, u'prev'), (SetupWizardStrings.next_button, self.try_login)]
            email_input = TextInput('email', SetupWizardStrings.email_label)
        self._full_sized_form = True
        self._title = SetupWizardStrings.login_title
        self._prev = WelcomePanel if not secondary else None
        self._next = UpgradeChoices
        try:
            host = arch.util.gethostname()
        except Exception:
            unhandled_exc_handler()
            host = u''

        forgot_url = self._wizard.dropbox_app.dropbox_url_info.construct_full_url('/forgot')
        form_items = [Spacer(90, hide_on=['win', 'linux']),
         email_input,
         TextInput('password', SetupWizardStrings.password_label, secure=True),
         TextBlock('<a href="%s">%s</a>' % (forgot_url, SetupWizardStrings.forgot_password_label), right_align=True, greedy=False)]
        if not secondary:
            form_items += [Spacer(20), TextInput('display_name', SetupWizardStrings.computer_name_label, sublabel=SetupWizardStrings.computer_name_sublabel, default_value=host)]
        else:
            self.display_name = host
        for item in form_items:
            self.add_form_item(item)

    def on_swap_in(self):
        if self._wizard.dropbox_app.mbox.is_secondary:
            self._wizard.on_wizard_start()

    @property
    def form_is_valid(self):
        return all((getattr(self, attr, None) for attr in self.default_values.iterkeys() if attr != 'password'))

    def on_success(self, result_dict):
        result = result_dict.get('ret', None)
        if not result:
            report_bad_assumption('Server returned malformed result for link_host_with_ret: %r', result_dict)
        if not result or result == 'fail':
            self._wizard.append_to_tour_route('try_login_bad')
            self._display_errors(result_dict['errors'])
        elif result == 'need_twofactor_code':
            self._wizard.append_to_tour_route('try_login_need_twofactor_code')
            panel = LoginTwoFactorPanel(self._wizard, result_dict.get('checkpoint_tkey'), result_dict.get('display_name'), result_dict.get('twofactor_text', SetupWizardStrings.twofactor_text), result_dict.get('include_send_sms_button', False), LoginPanel)
            self._wizard.swap(panel)
        elif result == 'ok':
            self._wizard.append_to_tour_route('try_login_good')
            self._login_success(new_account=False)
        else:
            report_bad_assumption('Server returned unexpected value for link_host_with_ret: %r', result_dict)
            self._display_errors()

    def on_error(self, *args):
        self._wizard.append_to_tour_route('try_login_error')
        self._unknown_error()

    def post_check_sso_user(self, result_dict):
        user_sso_state = result_dict.get('user_sso_state', None)
        if user_sso_state == 'required' and self.password:
            self._display_errors({'password': SetupWizardStrings.sso_error_entered_password})
        elif user_sso_state == 'required' or user_sso_state == 'optional' and not self.password:
            panel = SsoLoginPanel(self._wizard, self.email, self.display_name, user_sso_state)
            self._wizard.swap(panel, set_previous=True)
        else:
            self.link_user_with_password()

    def try_login(self):
        self._pre_link()
        if SSO_ENABLED:
            self._wizard.check_sso_user(self._wizard.dropbox_app.conn.host_id, self.email, self.post_check_sso_user, self.on_error)
        else:
            self.link_user_with_password()

    def link_user_with_password(self):
        self._wizard.link_host_with_ret(self._wizard.dropbox_app.conn.host_id, self.email, self.password, self.display_name, False, None, self.on_success, self.on_error)


class LoginTwoFactorPanel(LoginPanelBase):

    def __init__(self, wizard, checkpoint_tkey, display_name, twofactor_text, include_send_sms_button, previous_panel):
        super(LoginTwoFactorPanel, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.previous_button, u'prev'), (SetupWizardStrings.next_button, self.try_login)]
        self._full_sized_form = True
        self._title = SetupWizardStrings.twofactor_title
        self._prev = previous_panel
        self._next = UpgradeChoices
        self.checkpoint_tkey = checkpoint_tkey
        self.display_name = display_name
        if platform == 'mac':
            center_offset = -30
        else:
            center_offset = 0
        form_items = [TextBlock(twofactor_text, center=True), Spacer(40), CenteredMultiControlLine([TextInput(u'twofactor_code', SetupWizardStrings.twofactor_label, width=150)], offset=center_offset)]
        if include_send_sms_button:
            form_items += [Spacer(5), CenteredMultiControlLine([Button('send_sms', SetupWizardStrings.twofactor_send_sms_button, self.send_twofactor_sms)])]
        twofactor_url = self._wizard.dropbox_app.dropbox_url_info.construct_full_url('/c/help/two_step')
        form_items += [Spacer(5), CenteredMultiControlLine([TextBlock(SetupWizardStrings.twofactor_link % dict(url=twofactor_url), greedy=False)])]
        for item in form_items:
            self.add_form_item(item)

    @property
    def form_is_valid(self):
        return all((getattr(self, attr, None) for attr in self.default_values.iterkeys()))

    def on_success(self, result_dict):
        result = result_dict.get('ret')
        if not result:
            report_bad_assumption('Server returned malformed result for link_host_with_ret (2FA): %r', result_dict)
        if not result or result == 'fail':
            self._wizard.append_to_tour_route('try_login_twofactor_bad')
            self._display_errors(result_dict.get('errors', {}))
        elif result == 'fail_abort':
            self._wizard.append_to_tour_route('try_login_twofactor_abort')
            self._wizard.swap(self.prev)
            self._display_errors(result_dict.get('errors', {}))
        elif result == 'ok':
            self._wizard.append_to_tour_route('try_login_twofactor_good')
            self._login_success(new_account=False)
        else:
            report_bad_assumption('Server returned unexpected value for link_host_with_ret (2FA): %r', result_dict)
            self._display_errors()

    def on_error(self, *args):
        self._wizard.append_to_tour_route('try_login_twofactor_error')
        self._unknown_error()

    def try_login(self):
        self._pre_link()
        self._wizard.link_host_twofactor(self._wizard.dropbox_app.conn.host_id, self.checkpoint_tkey, self.display_name, self.twofactor_code, self.on_success, self.on_error)

    def on_success_send_sms(self, result_dict):
        result = result_dict.get('ret')
        if not result:
            report_bad_assumption('Server returned malformed result for send_twofactor_sms')
        if not result:
            self._wizard.append_to_tour_route('try_login_send_sms_bad')
            self._display_errors(result_dict.get('errors', {}))
        elif result == 'fail_abort':
            self._wizard.append_to_tour_route('try_login_send_sms_abort')
            self._wizard.swap(self.prev)
            self._display_errors(result_dict.get('errors', {}))
        elif result == 'sent_code':
            self._wizard.append_to_tour_route('try_login_send_sms_good')
            self._wizard.highlight_invalid_fields({})
            self._wizard.enable_buttons()
            panel = LoginTwoFactorPanel(self._wizard, self.checkpoint_tkey, self.display_name, result_dict.get('twofactor_text', SetupWizardStrings.twofactor_text), result_dict.get('include_send_sms_button', False), self._prev)
            self._wizard.swap(panel)
        else:
            report_bad_assumption('Server returned unexpected value for send_twofactor_sms')
            self._wizard.highlight_invalid_fields()
            self._wizard.enable_buttons()

    def on_error_send_sms(self, *args):
        self._wizard.append_to_tour_route('try_login_send_sms_error')
        self._unknown_error()

    def send_twofactor_sms(self):
        self._wizard.set_form_status(SetupWizardStrings.twofactor_sending_sms)
        self._wizard.disable_buttons()
        self._wizard.send_twofactor_sms(self.checkpoint_tkey, self.on_success_send_sms, self.on_error_send_sms)


class PreviousInstallationBase(Panel):

    def __init__(self, wizard):
        super(PreviousInstallationBase, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.next_button, self.our_next)]
        self._advanced = True
        self._full_sized_form = True
        self._title = SetupWizardStrings.previous_installation_title

    def our_next(self):
        if self.normal_setup == 1:
            self._wizard.post_link_swap()
        else:
            try:
                TRACE('Using old settings; ss: %r, path: %r', self._wizard.dropbox_app.unlink_cookie['unicode_rr_set'], self._wizard.dropbox_app.unlink_cookie['path'])
                self._wizard.directory_ignore_set = self._wizard.dropbox_app.unlink_cookie['unicode_rr_set']
                self._wizard.dropbox_path = self._wizard.dropbox_app.unlink_cookie['path']
                self._wizard.on_wizard_end()
                self._next = self._wizard.post_wizard_panel()
                self._wizard.next()
            except Exception:
                unhandled_exc_handler()


class PreviousInstallationWin(PreviousInstallationBase):

    def __init__(self, wizard):
        super(PreviousInstallationWin, self).__init__(wizard)
        form_items = [TextBlock(SetupWizardStrings.previous_installation_text % dict(email_address=self._wizard.email_address)), Spacer(15), AdvancedPanelRadioGroup('normal_setup', choices=[SetupWizardStrings.use_previous_settings_choice, SetupWizardStrings.continue_with_normal_setup_choice], embedded_controls=[])]
        for item in form_items:
            self.add_form_item(item)


class PreviousInstallationMac(PreviousInstallationBase):

    def __init__(self, wizard):
        super(PreviousInstallationMac, self).__init__(wizard)
        form_items = [TextBlock(SetupWizardStrings.previous_installation_text % dict(email_address=self._wizard.email_address)), Spacer(15), RadioGroup('normal_setup', choices=[SetupWizardStrings.use_previous_settings_choice, SetupWizardStrings.continue_with_normal_setup_choice], vertical_spacing=35, max_width=500)]
        for item in form_items:
            self.add_form_item(item)


if platform == 'mac':
    PreviousInstallation = PreviousInstallationMac
else:
    PreviousInstallation = PreviousInstallationWin

class SignupPanel(LoginPanelBase):

    def __init__(self, wizard):
        super(SignupPanel, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [self._normal_prev_button(), (SetupWizardStrings.next_button, self.try_link)]
        self._full_sized_form = True
        self._title = SetupWizardStrings.signup_title
        self._prev = WelcomePanel
        self._next = UpgradeChoices
        try:
            host = arch.util.gethostname()
        except Exception:
            unhandled_exc_handler()
            host = u''

        terms_url = self._wizard.dropbox_app.dropbox_url_info.construct_full_url('/terms')
        name_items = [TextInput('fname', SetupWizardStrings.first_name_label), TextInput('lname', SetupWizardStrings.last_name_label)]
        if get_current_code() == 'ja':
            name_items.reverse()
        form_items = [Spacer(50, hide_on=['win', 'linux'])] + name_items + [TextInput('email', SetupWizardStrings.email_label),
         TextInput('password', SetupWizardStrings.password_label, secure=True),
         TextInput('password2', SetupWizardStrings.verify_password_label, secure=True),
         Spacer(15),
         TextInput('display_name', SetupWizardStrings.computer_name_label, sublabel=SetupWizardStrings.computer_name_sublabel, default_value=host),
         Spacer(15, hide_on=['mac']),
         Spacer(20, hide_on=['win', 'linux']),
         Checkbox(attr='terms_of_service', label=SetupWizardStrings.terms_of_service_checkbox_link % dict(url=terms_url), center=True, hide_on=['win', 'linux']),
         CheckboxLink(attr='terms_of_service', label=SetupWizardStrings.terms_of_service_checkbox_link % dict(url=terms_url), center=True, hide_on=['mac'])]
        for item in form_items:
            self.add_form_item(item)

    def on_success(self, result_dict):
        result = result_dict.get('ret')
        if not result:
            report_bad_assumption('Server returned malformed result for register_and_link_with_ret: %r', result_dict)
        if not result or result == 'fail':
            self._wizard.append_to_tour_route('try_link_bad')
            self._display_errors(result_dict.get('errors', {}))
        elif result == 'need_twofactor_code':
            self._wizard.append_to_tour_route('try_link_need_twofactor_code')
            panel = LoginTwoFactorPanel(self._wizard, result_dict.get('checkpoint_tkey'), result_dict.get('display_name'), result_dict.get('twofactor_text', SetupWizardStrings.twofactor_text), result_dict.get('include_send_sms_button', False), SignupPanel)
            self._wizard.swap(panel)
        elif result == 'already_registered' or result == 'ok':
            if result == 'already_registered':
                new_account = False
            elif result == 'ok':
                new_account = True
            self._wizard.append_to_tour_route('try_link_good')
            self._login_success(new_account)
        else:
            report_bad_assumption('Server returned unexpected value for register_and_link_with_ret: %r', result_dict)
            self._display_errors()

    def form_item_changed(self, attr, new_value):
        pass

    def on_error(self, *args):
        self._wizard.append_to_tour_route('try_link_error')
        self._unknown_error()

    def try_link(self):
        if not self.form_is_valid:
            return
        self._pre_link()
        if not self._wizard.dropbox_app.conn.host_id:
            report_bad_assumption('No host_id when trying to create new account')
            self.on_error()
            return
        self._wizard.register_and_link_with_ret(self._wizard.dropbox_app.conn.host_id, self.fname, self.lname, self.email, self.password, self.password2, self.display_name, self.on_success, self.on_error)

    @property
    def form_is_valid(self):
        return all((getattr(self, item.attr, None) for item in self._form_contents if item.attr is not None))


class UpgradeChoices(Panel):

    def __init__(self, wizard):
        super(UpgradeChoices, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [self._normal_prev_button()] if self.get_prev_panel() else []
        self._buttons.append((SetupWizardStrings.next_button, self.handle_continue))
        self._full_sized_form = True
        if self._wizard.new_account:
            self._title = SetupWizardStrings.choose_size_title
        else:
            self._title = SetupWizardStrings.upgrade_title
        self._next = BillingPanel
        self.add_form_item(PlanChoices('plan_choice', wizard.get_plans(), default_value=wizard.get_plans()[0]))
        url = self._wizard.dropbox_app.dropbox_url_info.construct_full_url('/pricingterms')
        label = u'<a href="%(url)s">%(text)s</a>' % dict(url=url, text=SetupWizardStrings.plan_choice_label)
        self.add_form_item(TextBlock(label, center=True, bottom_align=True))

    def on_swap_in(self):
        self._buttons = [self._normal_prev_button()] if self.get_prev_panel() else []
        self._buttons.append((SetupWizardStrings.next_button, self.handle_continue))

    def handle_continue(self):
        self._wizard.plan_data = self.plan_choice
        try:
            needs_billing = self._wizard.plan_data['needs_billing']
        except KeyError:
            unhandled_exc_handler()
            needs_billing = bool(self._wizard.plan_data[u'periods'])

        if needs_billing:
            self._next = BillingPanel
        else:
            self._next = DefaultOrAdvanced
        self._wizard.next()


class BillingPanel(Panel):

    def __init__(self, wizard):
        super(BillingPanel, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.previous_button, self.go_back), (SetupWizardStrings.next_button, self.try_upgrade)]
        self._full_sized_form = True
        self._title = SetupWizardStrings.billing_title
        self._next = DefaultOrAdvanced
        self._prev = UpgradeChoices
        ccode_tip = SetupWizardStrings.ccode_tip1 + u'\n' + SetupWizardStrings.ccode_tip2
        mac = platform == 'mac'
        form_items = [CreditCardType('cctype'),
         TextInput('ccn', SetupWizardStrings.ccn_label, width=250),
         TextInput('name', SetupWizardStrings.billing_name_label, width=250),
         MultiControlLine([Date('exp', SetupWizardStrings.expdate_label), TextInput('ccode', SetupWizardStrings.cvn_label, width=41), HelpButton(ccode_tip)]),
         TextInput('address', SetupWizardStrings.billing_address_label, width=250),
         MultiControlLine([TextInput('city', SetupWizardStrings.billing_city_label, width=130), TextInput('state', SetupWizardStrings.billing_state_label, width=31)]),
         MultiControlLine([TextInput('zip', SetupWizardStrings.billing_zip_label, width=50), Choice('country', SetupWizardStrings.billing_country_label, choices=[ name for code, name in self._wizard.get_countries() ], default_value=self._wizard.get_default_country_index(), width=146)]),
         Spacer(15),
         RadioGroup('period', choices=self.get_billing_choices(), vertical_spacing=6),
         Spacer(9, hide_on=['win', 'linux']),
         Image(Images.Lock, SetupWizardStrings.ssl_info, border=False, inline=mac, bottom_align=not mac)]
        for item in form_items:
            self.add_form_item(item)

    def go_back(self):
        self._wizard.prev(keep_panel=False)

    def get_billing_choices(self):
        choices = []
        for period in self._wizard.plan_data['periods']:
            cost = self._wizard.plan_data[period + '_cost']
            template = self._wizard.get_period_templates()[period]
            choices.append(template % cost)

        return choices

    def on_success(self, result_dict):
        self._wizard.enable_buttons()
        if len(result_dict):
            self._wizard.highlight_invalid_fields(result_dict)
        else:
            self._wizard.highlight_invalid_fields({})
            self._wizard.next(set_previous=DISALLOW_PREV)

    def on_error(self, *args):
        self._wizard.enable_buttons()
        self._wizard.highlight_invalid_fields({})
        self._wizard.set_form_status(SetupWizardStrings.unexpected_error, True)

    def try_upgrade(self):
        self._wizard.disable_buttons()
        self._wizard.set_form_status(SetupWizardStrings.requesting_upgrade)
        self._wizard.client_upgrade(self.ccn, self.exp[0], self.exp[1], self.ccode, self.address, self.zip, self.city, self.state, self._wizard.get_countries()[self.country][0], self._wizard.plan_data['gigabytes'], self._wizard.plan_data['periods'][self.period], self.name, self.on_success, self.on_error)

    def form_item_changed(self, attr, new_value):
        if attr == 'ccn':
            self._update_card_type()

    def _update_card_type(self):
        needs_refresh = False
        if self.ccn.startswith('4'):
            if self.cctype != 'visa':
                self.cctype = 'visa'
                needs_refresh = True
        elif re.match('^5[1-5]', self.ccn):
            self.cctype = 'mastercard'
            needs_refresh = True
        elif re.match('^3[47]', self.ccn):
            self.cctype = 'amex'
            needs_refresh = True
        elif self.cctype is not None:
            self.cctype = None
            needs_refresh = True
        if needs_refresh:
            self._wizard.set_control_value('cctype', self.cctype)


class TourPanel(Panel):

    def __init__(self, wizard):
        super(TourPanel, self).__init__(wizard)
        self._buttons = [self._normal_prev_button(), (SetupWizardStrings.skip_button, self.skip_tour), self._normal_next_button()]
        self._background_image = Images.SetupWizardBackground
        self._full_sized_form = True
        self._tour = True
        self._handle_neighbor_info()

    def _handle_neighbor_info(self):
        i = self._wizard.tour_sequence.index(self.__class__)
        assert i >= 0
        self._panel_number = i + 1
        if i:
            self._prev = self._wizard.tour_sequence[i - 1]
        if i + 1 < len(self._wizard.tour_sequence):
            self._next = self._wizard.tour_sequence[i + 1]

    @property
    def panel_number(self):
        return self._panel_number

    def _progress_text(self):
        return SetupWizardStrings.progress_text % dict(current_panel=self.panel_number, total_panels=len(self._wizard.tour_sequence))

    progress_text = property(_progress_text)

    def skip_tour(self):
        self._wizard.swap(ThatsIt)


class SetupWizard(object):

    def __init__(self, window_class, linked_event, show_network_settings, dropbox_app, email_address = None):
        self.email_address = email_address or u''
        self.dropbox_app = dropbox_app
        self.tour_sequence = None
        self._dropbox_folder = None
        self.show_network_settings = show_network_settings
        self.start_tray_arrow = self.dropbox_app.ui_kit.start_tray_arrow
        self.stop_tray_arrow = self.dropbox_app.ui_kit.stop_tray_arrow
        self.update_tray_icon = self.dropbox_app.ui_kit.update_tray_icon
        self.get_text_from_clipboard = self.dropbox_app.ui_kit.get_text_from_clipboard
        self.copy_text_to_clipboard = self.dropbox_app.ui_kit.copy_text_to_clipboard
        self._done = False
        self._when_done = None
        self.panels = {}
        self.current_panel = None
        self._tour_route = None
        self.request_thread = SetupWizardRequestThread(self)
        self.window = window_class(self)
        self._linked_event = linked_event
        self.plan_data = None
        self.new_account = False
        self._tour_start_time = None
        self._tour_end_time = None
        self._wizard_start_time = None
        self._wizard_end_time = None
        self._post_link = False
        self.dropbox_path = dropbox_app.default_dropbox_path
        self.show_bubbles = True
        self.directory_ignore_set = []
        self.enable_xattrs = True
        self.open_dropbox_folder = True
        self._countries = None
        self._default_country_index = None
        self._tour_texter_strategy = None

    def wizard_strings_class(self):
        return SetupWizardStrings

    def post_wizard_panel(self):
        try:
            strategy = self.dropbox_app.gandalf.get_variant('desktop-tour-texter')
            if strategy and strategy.upper() == 'CONTROL':
                strategy = None
            self._tour_texter_strategy = strategy
        except Exception:
            unhandled_exc_handler()

        if not self.dropbox_app.mbox.is_secondary and self._tour_texter_strategy:
            return MobileSetup
        else:
            return self.tour_sequence[0]

    def enter(self, panel_t, force = True, definitely_connected = False, should_raise = False, dropbox_folder = None):
        TRACE('entering setupwizard: %r, force=%r, definitely_connected=%r should_raise=%r dropbox_folder=%r', panel_t, force, definitely_connected, should_raise, dropbox_folder)
        if dropbox_folder is not None:
            self._dropbox_folder = dropbox_folder
        if not self.window.is_shown():
            try:
                self.request_thread.start()
                if definitely_connected:
                    self.wizard_load_strings()
            except RuntimeError:
                pass

            self.current_panel = panel_t(self)
            self.current_panel.on_swap_in()
            self.window._create_contents_and_fill()
            self.window.show_window()
            self._tour_route = []
            self.append_to_tour_route(panel_t.__name__)
        else:
            self.swap(panel_t)
        if should_raise:
            self.raise_window()
        TRACE('finished entering setupwizard!')

    def linked_successfully(self, when_done = None):
        TRACE('OK, AUTHENTICATE claims we linked!')
        self._when_done = when_done
        if self.dropbox_app.mbox.paired:
            dropbox_name, self.dropbox_path = self.dropbox_app.mbox.derive_dropbox_name_and_path()
            self.dropbox_app.mbox.update_dropbox_path(self.dropbox_path, dropbox_name)
        self.tour_sequence = TourSequence(self.dropbox_app)
        if self.dropbox_app.unlink_cookie and self.dropbox_app.unlink_cookie['email'] == self.email_address and self.dropbox_app.unlink_cookie['root_ns'] == self.root_ns and 'path' in self.dropbox_app.unlink_cookie:
            if os.path.isdir(self.dropbox_app.unlink_cookie['path']):
                self.swap(PreviousInstallation)
                self._post_link = True
                self.enable_buttons()
                return
        self.post_link_swap()
        self.enable_buttons()

    def post_link_swap(self):
        next_panel = self._get_post_link_panel()
        TRACE('in post_link_swap, _post_link already called is %r, next is %r', self._post_link, next_panel)
        if self._post_link:
            self.current_panel._next = next_panel
            self.next()
        else:
            self.swap(next_panel)
            self._post_link = True

    def _get_post_link_panel(self):
        if u'plans_in_client' in self.dropbox_app.ui_flags and not self.dropbox_app.mbox.is_secondary:
            return UpgradeChoices
        else:
            return DefaultOrAdvanced

    def append_to_tour_route(self, panel_name):
        TRACE('TOUR ROUTE: %r', panel_name)
        self._tour_route.append((panel_name, time.time()))
        try:
            self.send_route_stats(finished=False)
        except Exception:
            unhandled_exc_handler()

    def select_all_in_control(self, attr):
        self.window.select_all_in_control(attr)

    def set_example_text(self, attr, text, error = False):
        self.window.set_example_text(attr, text, error)

    def set_focus_on_control(self, attr):
        self.window.set_focus_on_control(attr)

    def set_form_status(self, status, error = False):
        self.window.set_form_status(status, error=error)

    def highlight_invalid_fields(self, result_dict):
        return self.window.highlight_invalid_fields(result_dict)

    def enable_buttons(self):
        self.window.enable_buttons()

    def disable_buttons(self):
        self.window.disable_buttons()

    def set_next_button_enabled(self, enabled):
        self.window.set_next_button_enabled(enabled)

    def show_form_errors(self, result_dict):
        self.window.show_form_errors(result_dict)

    def successfully_linked(self):
        self._linked_event.set()

    def get_plans(self):
        return self.dropbox_app.ui_flags.get('plans_in_client', None)

    def get_period_templates(self):
        return self.dropbox_app.ui_flags['periods']

    def get_phone_code(self, code):
        if 'phonecodes' in self.dropbox_app.ui_flags:
            return self.dropbox_app.ui_flags['phonecodes'].get(code, '')
        return PHONECODES.get(code, '')

    def on_wizard_start(self):
        if self._wizard_start_time is None:
            self._wizard_start_time = time.time()

    def on_wizard_end(self):
        if self._wizard_end_time is not None:
            return
        self._wizard_end_time = time.time()

    def on_tour_start(self):
        if self._tour_start_time is None:
            self._tour_start_time = time.time()

    def on_tour_end(self):
        self._tour_end_time = time.time()
        if self._when_done:
            self._when_done(dict(dropbox_path=self.dropbox_path, show_bubbles=self.show_bubbles, directory_ignore_set=self.directory_ignore_set, enable_xattrs=self.enable_xattrs, open_dropbox_folder=self.open_dropbox_folder))
            self._when_done = None

    def disallow_covering(self):
        self.window.disallow_covering()

    def allow_covering(self):
        self.window.allow_covering()

    def raise_window(self):
        self.window.raise_window()

    def next(self, set_previous = True):
        TRACE('Moving to next panel')
        if self.current_panel.next:
            self.swap(self.current_panel.next, set_previous=set_previous)
        else:
            TRACE('ERROR: next panel not defined')

    def prev(self, keep_panel = True):
        TRACE('Moving to previous panel')
        if self.current_panel.prev:
            self.swap(self.current_panel.prev, keep_panel=keep_panel, set_previous=False)
        else:
            TRACE('ERROR: previous panel not defined')

    @property
    def exit_caption(self):
        if self._wizard_end_time:
            return SetupWizardStrings.exit_tour_caption
        return SetupWizardStrings.exit_wizard_caption

    @property
    def exit_prompt(self):
        if self._wizard_end_time:
            return SetupWizardStrings.exit_tour_prompt
        return SetupWizardStrings.exit_wizard_prompt

    @property
    def exit_button(self):
        if self._wizard_end_time:
            return SetupWizardStrings.exit_tour_button
        return SetupWizardStrings.exit_wizard_button

    def exit(self):
        self.append_to_tour_route('_exit')
        if self._wizard_end_time is None:
            arch.util.hard_exit()
        else:
            self.finish()

    @property
    def done(self):
        return self._done

    def finish(self):
        if not self.window:
            TRACE('Called finish() twice!')
            return
        self.window.on_finish()
        self._done = True
        self.on_tour_end()
        try:
            self.send_route_stats(finished=True)
        except Exception:
            unhandled_exc_handler()

        self.window = None

    def send_route_stats(self, finished = False):
        kw = {'route': json.dumps(self._tour_route),
         'tour_time': json.dumps(self._tour_end_time - self._tour_start_time if self._tour_start_time and self._tour_end_time else None),
         'wizard_time': json.dumps(self._wizard_end_time - self._wizard_start_time if self._wizard_start_time and self._wizard_end_time else None)}
        TRACE('sending route stats, finished = %r; route = %r', finished, kw['route'])
        if finished:
            TRACE('TOUR ROUTE STATS:')
            TRACE('route = %s', kw['route'])
            TRACE('tour_time = %s', kw['tour_time'])
            TRACE('wizard_time = %s', kw['wizard_time'])
        callback = self.stop_request_thread if finished else None
        self.request_thread.wizard_route(kw['route'], kw['wizard_time'], kw['tour_time'], self.dropbox_app.ui_flags.get('mobile_text_panel'), callback, callback)

    def stop_request_thread(self, *args):
        self.request_thread.stop()

    def swap(self, panel_t, keep_panel = True, set_previous = None):
        if self.done:
            return
        if panel_t in self.panels:
            panel_t = self.panels[panel_t]
        old_panel = self.current_panel
        old_panel.on_swap_out()
        if isinstance(panel_t, type):
            self.current_panel = panel_t(self)
        else:
            self.current_panel = panel_t
        self.append_to_tour_route(self.current_panel.__class__.__name__)
        if set_previous is not False:
            self.current_panel.set_prev_panel(old_panel if set_previous is True else set_previous)
        self.current_panel.on_swap_in()
        self.window._create_contents_and_replace()
        self.window._update_next_button()
        if keep_panel:
            self.panels[old_panel.__class__] = old_panel

    def set_control_hidden(self, attr, value):
        self.window.set_control_hidden(attr, value)

    def set_control_enabled(self, attr, value):
        self.window.set_control_enabled(attr, value)

    def set_control_value(self, attr, value):
        self.window.set_control_value(attr, value)

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

            def on_no():
                self.window.choose_dropbox_location(on_location)

            full_explanation = SetupWizardStrings.merge_explanation % dict(folder_name=self.dropbox_app.default_dropbox_folder_name, folder_path=os.path.dirname(path))
            self.ask_yes_no(SetupWizardStrings.merge_title, full_explanation, on_yes=partial(on_success, path), on_no=on_no, yes_button_text=SetupWizardStrings.merge_button_ok, no_button_text=SetupWizardStrings.merge_button_cancel)
        else:
            on_success(path)

    def update_button_title(self, old_title, new_title):
        self.window.update_button_title(old_title, new_title)

    def register_and_link_with_ret(self, host_id, fname, lname, email, password, password2, display_name, on_success = None, on_error = None):
        return self.request_thread.register_and_link_with_ret(host_id, fname, lname, email, password, password2, display_name, on_success, on_error)

    def link_host_with_ret(self, host_id, email, password, display_name, is_sso_link, post_2fa_token, on_success = None, on_error = None):
        return self.request_thread.link_host_with_ret(host_id, email, password, display_name, is_sso_link, post_2fa_token, on_success, on_error)

    def check_sso_user(self, host_id, email, on_success = None, on_error = None):
        return self.request_thread.check_sso_user(host_id, email, on_success, on_error)

    def link_host_twofactor(self, host_id, checkpoint_tkey, display_name, twofactor_code, on_success = None, on_error = None):
        return self.request_thread.link_host_twofactor(host_id, checkpoint_tkey, display_name, twofactor_code, on_success, on_error)

    def send_twofactor_sms(self, checkpoint_tkey, on_success, on_error):
        return self.request_thread.send_twofactor_sms(checkpoint_tkey, on_success, on_error)

    def wizard_load_strings(self):
        TRACE('WIZARD_LOAD: fetching strings')
        return self.request_thread.wizard_load_strings()

    def client_upgrade(self, ccn, expmo, expyr, ccode, address, zipcode, city, state, country, plan, period, name, on_success = None, on_error = None):
        return self.request_thread.client_upgrade(ccn, expmo, expyr, ccode, address, zipcode, city, state, country, plan, period, name, on_success, on_error)

    def send_text(self, mobile_number, on_success = None, on_error = None):
        return self.request_thread.send_text(mobile_number, self._tour_texter_strategy, on_success, on_error)

    def get_countries(self):
        if self._countries:
            return self._countries
        try:
            self._countries = by_locale[get_current_code()]
        except KeyError:
            self._countries = by_locale[DEFAULT_CODE]

        return self._countries

    def get_default_country_index(self):
        if self._default_country_index is None:
            self.get_countries()
            codes_to_try = [get_country_code(), 'US']
            self._default_country_index = 0
            for country_code in codes_to_try:
                for i, (code, _) in enumerate(self._countries):
                    if code == country_code:
                        self._default_country_index = i
                        return self._default_country_index

        return self._default_country_index


class TourWelcome(TourPanel):

    def __init__(self, wizard):
        super(TourWelcome, self).__init__(wizard)
        self._title = SetupWizardStrings.tour_welcome_title % dict(first_name=self._wizard.first_name)
        form_items = [TextBlock(SetupWizardStrings.dropbox_explanation), Spacer(10), Image(Images.TourWelcomeShot, None, border=True, bottom_align=True)]
        for item in form_items:
            self.add_form_item(item)

    def on_swap_in(self):
        self._wizard.on_tour_start()


class WebInterface(TourPanel):

    def __init__(self, wizard):
        super(WebInterface, self).__init__(wizard)
        self._title = SetupWizardStrings.web_interface_title
        url = self._wizard.dropbox_app.dropbox_url_info.construct_full_url()
        bare_website = url.split('://', 1)[1]
        bare_website = bare_website.split('/')[0]
        form_items = [TextBlock(SetupWizardStrings.web_interface_instructions % dict(website=bare_website, website_url=url)), Spacer(10), Image(Images.WebInterfaceShot, None, border=True, bottom_align=True)]
        for item in form_items:
            self.add_form_item(item)


_MOBILE_NUMBER_RE = re.compile("^[-()\\./'\\*,\\d\\s]*$")
_MOBILE_NUMBER_MIN_DIGITS = 7

def parens_balanced(s):
    try:
        level = 0
        for p in s:
            if p == u'(':
                level += 1
            elif p == u')':
                level -= 1
                if level < 0:
                    return False

        return level == 0
    except Exception:
        unhandled_exc_handler()
        return True


def clean_and_verify_mobile_number(n, code):
    n = n.strip()
    if not n:
        return n
    if not _MOBILE_NUMBER_RE.match(n):
        raise ValueError("mobile_number %r doesn't match regex" % (n,))
    if not parens_balanced(n):
        raise ValueError('mobile_number %r has unbalanced parens' % (n,))
    ndigits = len([ x for x in n if '0' <= x <= '9' ])
    if ndigits < _MOBILE_NUMBER_MIN_DIGITS:
        raise ValueError('mobile_number %r has fewer than %d digits' % (n, _MOBILE_NUMBER_MIN_DIGITS))
    if code == '+1':
        if ndigits != 10:
            raise ValueError("mobile_number %r for code +1 doesn't have exactly 10 digits" % (n,))
    elif code.startswith('+1') and len(code) == 5:
        if ndigits != 7:
            raise ValueError("mobile_number %r for NANP code %s doesn't have exactly 7 digits" % (n, code))
    return n


class MobileSetup(Panel):
    EXAMPLE_MOBILE_NUMBERS = {'+1': '(958) 555-0123',
     '+31': '6 99999999',
     '+33': '9 99 99 99 99',
     '+34': '799 999 999',
     '+378': '549 999 999',
     '+39': '399 999 9999',
     '+41': '71 999 99 99',
     '+44': '7700 900123',
     '+45': '9999 9999',
     '+47': '499 99 999',
     '+48': '88 999 99 99',
     '+49': '9999 999999',
     '+503': '7999-9999',
     '+504': '9999-9999',
     '+506': '8999-9999',
     '+51': '984 999 999',
     '+52': '1331-999-9999',
     '+54': '(11) 159-99-999',
     '+55': '(11) 9999-9999',
     '+599': '99 9999999',
     '+60': '19-999-9999',
     '+61': '(491) 570 156',
     '+65': '9999 9999',
     '+7': '(9999) 99-99-99',
     '+852': '9999 9999',
     '+86': '139 9999 9999',
     '+90': '539 999 99 99',
     '+91': '99999 99999'}
    NANP_EXAMPLE_MOBILE_NUMBER = '555-1212'

    def __init__(self, wizard):
        super(MobileSetup, self).__init__(wizard)
        self._buttons = [(SetupWizardStrings.next_button, self.text_or_next)]
        self.mobile_mixin_setup()
        self._next = self._wizard.tour_sequence[0]

    def ex_number(self, phonecode = None):
        if phonecode is None:
            phonecode = self._wizard.get_phone_code(get_country_code())
        if phonecode in self.EXAMPLE_MOBILE_NUMBERS:
            return self.EXAMPLE_MOBILE_NUMBERS[phonecode]
        if phonecode.startswith('+1') and len(phonecode) == 5:
            return self.NANP_EXAMPLE_MOBILE_NUMBER
        return ''

    def example_number_label(self, phonecode = None):
        number = self.ex_number(phonecode)
        if number:
            return SetupWizardStrings.mobile_example % {'number': number}
        else:
            return ''

    def mobile_mixin_setup(self):
        if platform == 'mac':
            FLAG_DROPDOWN_WIDTH = 185
        elif platform.lower().startswith('win'):
            FLAG_DROPDOWN_WIDTH = 164
        else:
            FLAG_DROPDOWN_WIDTH = 170
        PHONE_INPUT_WIDTH = 115
        self._background_image = Images.SetupWizardBackground
        self._title = SetupWizardStrings.mobile_setup_title
        self._full_sized_form = True
        self._left_side_image = Image(Images.Mobile, None)
        self._left_side_image_padding = 10 if platform == 'mac' else 15
        self._panel_title_lower_padding = 3 if platform == 'win' else 0
        self.flag_choices = [ (getattr(Images, 'flag_%s' % (code.lower(),), Images.flag_blank), name, self._wizard.get_phone_code(code)) for code, name in self._wizard.get_countries() ]
        first_paragraph_spacing = 3 if platform == 'mac' else 16
        second_paragraph_spacing = 23 if platform == 'mac' else 16
        flagchoice_to_input_tweak = 0
        if platform == 'mac':
            horiz_spacer_to_example_width = 6
            vertical_spacer_to_example_text = -13
            first_paragraph_line_height = 24
            second_paragraph_line_height = 20
            first_paragraph_size_diff = 1
        elif platform == 'win':
            horiz_spacer_to_example_width = 5
            vertical_spacer_to_example_text = 3
            first_paragraph_line_height = 20
            second_paragraph_line_height = 15
            first_paragraph_size_diff = 1
        else:
            horiz_spacer_to_example_width = 7
            vertical_spacer_to_example_text = 3
            first_paragraph_line_height = 15
            second_paragraph_line_height = 15
            first_paragraph_size_diff = 0
            flagchoice_to_input_tweak = -2
        form_items = [Spacer(21, hide_on=['win', 'linux']),
         TextBlock(SetupWizardStrings.mobile_setup_header, bold=True, size_diff=first_paragraph_size_diff, line_height=first_paragraph_line_height),
         Spacer(first_paragraph_spacing),
         TextBlock(SetupWizardStrings.mobile_setup_explanation, line_height=second_paragraph_line_height),
         Spacer(second_paragraph_spacing),
         MultiControlLineSimple([TextBlock(SetupWizardStrings.mobile_label1, greedy=False, bold=True), HorizSpacer(3, hide_on=['mac']), TextBlock(SetupWizardStrings.mobile_label2, greedy=False, bold=False)], close_spacing=True),
         Spacer(12, hide_on=['mac']),
         MultiControlLineSimple([FlagChoice('country', u'', choices=self.flag_choices, default_value=self._wizard.get_default_country_index(), width=FLAG_DROPDOWN_WIDTH), HorizSpacer(5 + flagchoice_to_input_tweak, hide_on=['mac']), TextInput('mobile_number', u'', '', width=PHONE_INPUT_WIDTH)]),
         Spacer(vertical_spacer_to_example_text),
         MultiControlLineSimple([HorizSpacer(FLAG_DROPDOWN_WIDTH + horiz_spacer_to_example_width), ExampleText('number_label', self.example_number_label())])]
        for item in form_items:
            self.add_form_item(item)

        self.set_initial_focus_on_control('mobile_number')

    def form_item_changed(self, attr, new_value):
        if attr == 'country':
            phonecode = self.flag_choices[new_value][2]
            self._wizard.set_example_text('number_label', self.example_number_label(phonecode))

    def text_or_next(self):
        code = self.flag_choices[self.country][2]
        try:
            clean_num = clean_and_verify_mobile_number(self.mobile_number, code)
        except ValueError as e:
            TRACE('Error sanity-checking mobile number: %s', e)
            self._wizard.set_example_text('number_label', SetupWizardStrings.mobile_malformed_number, error=True)
            self._wizard.set_focus_on_control('mobile_number')
            self._wizard.select_all_in_control('mobile_number')
            return

        if not clean_num:
            self._wizard.next()
            return
        self._send('%s %s' % (code, clean_num))

    def _send(self, clean_num):
        self._wizard.set_form_status(u'')
        TRACE('Sending mobile number: %r', clean_num)
        self._wizard.send_text(clean_num, self.on_success, self.on_error)
        self._wizard.next()

    def on_success(self, result_dict):
        TRACE('on_success: send_text returned %r', result_dict)

    def on_error(self, *args):
        TRACE('on_error: send_text returned %r', args)


class MenuIcon(TourPanel):

    def __init__(self, wizard):
        super(MenuIcon, self).__init__(wizard)
        self._title = SetupWizardStrings.menu_icon_title
        _arrow_note = SetupWizardStrings.arrow_note
        _arrow_explanation = SetupWizardStrings.arrow_explanation
        t = u'%s %s' % (_arrow_note, _arrow_explanation) if _arrow_note else _arrow_explanation
        form_items = [TextBlock(t), Spacer(10), Image(Images.MenuIconShot, None, border=True, bottom_align=True)]
        for item in form_items:
            self.add_form_item(item)

    def on_swap_in(self):
        self._wizard.start_tray_arrow()
        self._wizard.update_tray_icon(flashing=True)

    def on_swap_out(self):
        self._wizard.stop_tray_arrow()
        self._wizard.update_tray_icon(flashing=False)


class ShareFolders(TourPanel):

    def __init__(self, wizard):
        super(ShareFolders, self).__init__(wizard)
        self._title = SetupWizardStrings.share_folders_title
        form_items = [TextBlock(SetupWizardStrings.share_folders_explanation), Spacer(10), Image(Images.ShareFoldersShot, None, border=True, bottom_align=True)]
        for item in form_items:
            self.add_form_item(item)


class ThatsIt(TourPanel):

    def __init__(self, wizard):
        super(ThatsIt, self).__init__(wizard)
        self._title = SetupWizardStrings.thats_it_title
        self._buttons = [self._normal_prev_button(), (SetupWizardStrings.finish_button, self.finish)]
        form_items = [TextBlock(SetupWizardStrings.thats_it_text),
         Spacer(5),
         Image(Images.WorldBox, None, border=False, inline=True),
         Spacer(5, hide_on='mac'),
         Checkbox('open_dropbox_folder', SetupWizardStrings.thats_it_checkbox, default_value=True, left_align=True, bottom_align=True)]
        for item in form_items:
            self.add_form_item(item)

    def finish(self):
        self._wizard.disable_buttons()
        self._wizard.open_dropbox_folder = self.open_dropbox_folder
        self._wizard.finish()


class TourSequence(object):
    DEFAULT_SEQUENCE = (TourWelcome,
     WebInterface,
     MenuIcon,
     ShareFolders,
     ThatsIt)
    ALL_POSSIBLE_PANELS = DEFAULT_SEQUENCE
    UI_FLAGS_KEY = 'tour_sequence'

    def __init__(self, dropbox_app):
        self.dropbox_app = dropbox_app
        if self.dropbox_app.mbox.is_secondary:
            self.seq = [ThatsIt]
        else:
            self.seq = list(self.DEFAULT_SEQUENCE)
            if self.UI_FLAGS_KEY in self.dropbox_app.ui_flags:
                self.set_sequence()

    def set_sequence(self):
        names = self.dropbox_app.ui_flags[self.UI_FLAGS_KEY]
        name_to_class = dict(((cls.__name__, cls) for cls in self.ALL_POSSIBLE_PANELS))
        seq = []
        failed = False
        for name in names:
            try:
                seq.append(name_to_class[name])
            except KeyError:
                TRACE('Unable to find panel name %s; will fall back to default', name)
                failed = True

        if not failed:
            TRACE('Setting tour sequence to %s', names)
            self.seq = seq

    def __len__(self):
        return len(self.seq)

    def __getitem__(self, key):
        return self.seq[key]

    def __iter__(self):
        return iter(self.seq)

    def index(self, value):
        return self.seq.index(value)


class ConnectionTrouble(Panel):

    def __init__(self, wizard):
        super(ConnectionTrouble, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.waiting_for_connection, None)]
        self._title = SetupWizardStrings.connection_trouble_title
        form_items = [TextBlock(SetupWizardStrings.proxy_server_text), MultiControlLine([Button('connection_options', SetupWizardStrings.connection_options_button, self.on_connection_options_clicked), Button('reconnect', SetupWizardStrings.reconnect_now_button, self.on_reconnect_clicked)])]
        for item in form_items:
            self.add_form_item(item)

    def on_swap_in(self):
        self._wizard.disable_buttons()

    def on_connection_options_clicked(self):
        TRACE('Connection options clicked')
        self._wizard.show_network_settings()

    def on_reconnect_clicked(self):
        TRACE('Reconnect clicked')
        self._wizard.dropbox_app.conn.reconnect()


class DropboxMissing(Panel):

    def __init__(self, wizard):
        super(DropboxMissing, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.exit_wizard_button, self.exit), (SetupWizardStrings.relink_button, self.relink)]
        self._title = SetupWizardStrings.dropbox_missing_title
        pieces = [SetupWizardStrings.dropbox_missing_text1 + u'\n' + unicode_clean(wizard.dropbox_app.config.get('dropbox_path')), SetupWizardStrings.dropbox_missing_text2 % dict(exit_button=SetupWizardStrings.exit_wizard_button)]
        if self._wizard.dropbox_app.dropbox_url_info.email:
            pieces.append(SetupWizardStrings.previous_link_email % dict(email=self._wizard.dropbox_app.dropbox_url_info.email))
        pieces.append(SetupWizardStrings.dropbox_missing_text3 % dict(relink_button=SetupWizardStrings.relink_button))
        self.add_form_item(TextBlock(u'\n\n'.join(pieces)))

    def exit(self):
        arch.util.hard_exit()

    def relink(self):
        self._wizard.ask_yes_no(SetupWizardStrings.relink_confirmation1 + u'\n\n' + SetupWizardStrings.relink_confirmation2, on_yes=self.on_okay)

    def on_okay(self):
        self._wizard.dropbox_app.restart_and_unlink()


class UnlinkFailure(Panel):

    def __init__(self, wizard):
        super(UnlinkFailure, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._buttons = [(SetupWizardStrings.exit_wizard_button, self.exit)]
        self._title = SetupWizardStrings.unlink_title
        unlink_help_url = self._wizard.dropbox_app.dropbox_url_info.help_url('permissions_error')
        pieces = []
        if self._wizard.dropbox_app.dropbox_url_info.email:
            pieces.append(SetupWizardStrings.previously_linked_better % dict(email=self._wizard.dropbox_app.dropbox_url_info.email))
        pieces.append(SetupWizardStrings.unlink_problem1)
        pieces.append(SetupWizardStrings.unlink_problem2 % dict(unlink_help_url=unlink_help_url))
        self.add_form_item(TextBlock(u'\n\n'.join(pieces)))

    def exit(self):
        arch.util.hard_exit()


class AdvancedSetupWizardPanel(Panel):

    def __init__(self, wizard):
        super(AdvancedSetupWizardPanel, self).__init__(wizard)
        self._buttons = [self._normal_prev_button(), self._normal_next_button()]
        self._background_image = Images.SetupWizardBackground
        self._full_sized_form = True
        self._advanced = True


class DefaultOrAdvanced(AdvancedSetupWizardPanel):

    def __init__(self, wizard):
        super(DefaultOrAdvanced, self).__init__(wizard)
        self._background_image = Images.SetupWizardBackground
        self._title = SetupWizardStrings.default_or_advanced_title
        if wizard.get_plans():
            self._buttons = [self._normal_prev_button(), (SetupWizardStrings.install_button, self.our_next)]
        else:
            self._buttons = [(SetupWizardStrings.install_button, self.our_next)]
        self._prev = UpgradeChoices
        choice = FancyRadioGroup('default_or_advanced', choices=[dict(label=SetupWizardStrings.typical_choice, sublabel=SetupWizardStrings.typical_sublabel, description=SetupWizardStrings.typical_description, image=Images.SetupWizardTypicalIcon), dict(label=SetupWizardStrings.advanced_choice, sublabel=None, description=SetupWizardStrings.advanced_description, image=Images.SetupWizardAdvancedIcon)], default_value=0)
        self.add_form_item(choice)

    def on_swap_in(self):
        self.form_item_changed('default_or_advanced', self.default_or_advanced)

    def form_item_changed(self, attr, new_value):
        if attr == 'default_or_advanced':
            try:
                if new_value['label'] == SetupWizardStrings.typical_choice:
                    self._wizard.update_button_title(SetupWizardStrings.next_button, SetupWizardStrings.install_button)
                else:
                    self._wizard.update_button_title(SetupWizardStrings.install_button, SetupWizardStrings.next_button)
            except Exception:
                pass

    def done_merge(self, path):
        TRACE('Dropbox location is %r', path)
        self._wizard.dropbox_path = os.path.normpath(path)
        self._wizard.on_wizard_end()
        self._next = self._wizard.post_wizard_panel()
        self._wizard.next()

    def our_next(self):
        if self.default_or_advanced['label'] == SetupWizardStrings.typical_choice:
            self._wizard.check_merge(default_tour_dropbox_location(self._wizard.dropbox_app, with_test=True), self.done_merge)
        elif self.default_or_advanced['label'] == SetupWizardStrings.advanced_choice:
            self._next = DropboxLocation
            self._wizard.next()
        else:
            TRACE('!! Unknown option selected: %r', self.default_or_advanced['label'])


class DropboxLocationBase(AdvancedSetupWizardPanel):

    def __init__(self, wizard):
        super(DropboxLocationBase, self).__init__(wizard)
        self._buttons = [self._normal_prev_button(), (SetupWizardStrings.next_button, self.our_next)]
        self._prev = DefaultOrAdvanced
        self._title = SetupWizardStrings.advanced_install_location
        self._next_location_change_must_be_from_user = False
        self.asked_merge = None

    def done_merge(self, location):
        TRACE('Dropbox location is %r', location)
        if location != self._wizard.dropbox_path:
            self.choose_dropbox = 1
            self.location = location
        self._wizard.dropbox_path = os.path.normpath(location)
        self.asked_merge = self._wizard.dropbox_path
        self._wizard.next()

    def our_next(self):
        if self.choose_dropbox and self.location:
            path = os.path.normpath(self.location)
        else:
            path = default_tour_dropbox_location(self._wizard.dropbox_app)
        if self.asked_merge == path:
            self.done_merge(path)
        else:
            self._wizard.check_merge(path, self.done_merge)

    def on_swap_in(self):
        self._next_location_change_must_be_from_user = False

    def form_item_changed(self, attr, new_value):
        if attr == 'location':
            if self._next_location_change_must_be_from_user:
                self.asked_merge = os.path.normpath(new_value)
            else:
                self._next_location_change_must_be_from_user = True


class DropboxLocationMac(DropboxLocationBase):

    def __init__(self, wizard):
        super(DropboxLocationMac, self).__init__(wizard)
        self._next = SelectiveSyncSetup
        form_items = [Spacer(10, hide_on=['win']), RadioGroup('choose_dropbox', choices=[SetupWizardStrings.default_dropbox_choice, SetupWizardStrings.custom_dropbox_choice], vertical_spacing=35, max_width=500), LocationChanger('location', wizard.dropbox_path)]
        for item in form_items:
            self.add_form_item(item)

    def on_swap_in(self):
        super(DropboxLocationMac, self).on_swap_in()
        self._next_location_change_must_be_from_user = True

    def form_item_changed(self, attr, new_value):
        super(DropboxLocationMac, self).form_item_changed(attr, new_value)
        if attr == 'choose_dropbox':
            self._wizard.set_control_enabled('location', self.choose_dropbox)


class DropboxLocationWinAndLinux(DropboxLocationBase):

    def __init__(self, wizard):
        super(DropboxLocationWinAndLinux, self).__init__(wizard)
        if platform == 'win' and WINDOWS_VERSION < VISTA:
            default_choice = SetupWizardStrings.default_dropbox_choice
        else:
            default_choice = SetupWizardStrings.default_dropbox_choice_new_windows % dict(path=os.path.dirname(wizard.dropbox_path))
        form_items = [AdvancedPanelRadioGroup('choose_dropbox', choices=[default_choice, SetupWizardStrings.custom_dropbox_choice], embedded_controls=[[], [LocationChanger('location')]])]
        for item in form_items:
            self.add_form_item(item)

    @property
    def _next(self):
        if arch.enable_xattrs.needs_user_xattr(self._wizard.dropbox_path):
            return XattrSetup
        return SelectiveSyncSetup


if platform == 'mac':
    DropboxLocation = DropboxLocationMac
else:
    DropboxLocation = DropboxLocationWinAndLinux

class SelectiveSyncSetupBase(AdvancedSetupWizardPanel):

    def __init__(self, wizard):
        super(SelectiveSyncSetupBase, self).__init__(wizard)
        self._buttons = [self._normal_prev_button(), (SetupWizardStrings.install_button, self.our_next)]
        self._title = SetupWizardStrings.advanced_install_ss

    def on_swap_out(self):
        ss = bool(self.enable_selective_sync)
        TRACE('User decided to %sable selective sync', 'en' if ss else 'dis')
        if ss and self.selective_sync:
            TRACE('Ignoring: %r', self.selective_sync)
            self._wizard.directory_ignore_set = [ unicode(a) for a in self.selective_sync ]

    def our_next(self):
        self._wizard.on_wizard_end()
        self._next = self._wizard.post_wizard_panel()
        self._wizard.next()


class SelectiveSyncSetupMac(SelectiveSyncSetupBase):

    def __init__(self, wizard):
        super(SelectiveSyncSetupMac, self).__init__(wizard)
        self._prev = DropboxLocation
        form_items = [Spacer(10, hide_on=['win']), RadioGroup('enable_selective_sync', choices=[SetupWizardStrings.sync_all_choice, SetupWizardStrings.sync_some_choice], vertical_spacing=35, max_width=500), SelectiveSync('selective_sync')]
        for item in form_items:
            self.add_form_item(item)

    def on_swap_in(self):
        self.form_item_changed('selective_sync', self.enable_selective_sync)

    def form_item_changed(self, attr, new_value):
        self._wizard.set_control_enabled('selective_sync', self.enable_selective_sync)


class SelectiveSyncSetupWin(SelectiveSyncSetupBase):

    def __init__(self, wizard):
        super(SelectiveSyncSetupWin, self).__init__(wizard)
        form_items = [AdvancedPanelRadioGroup('enable_selective_sync', choices=[SetupWizardStrings.sync_all_choice, SetupWizardStrings.sync_some_choice], embedded_controls=[[], [SelectiveSync('selective_sync')]])]
        for item in form_items:
            self.add_form_item(item)

    @property
    def _prev(self):
        if arch.enable_xattrs.needs_user_xattr(self._wizard.dropbox_path):
            return XattrSetup
        return DropboxLocation


if platform == 'mac':
    SelectiveSyncSetup = SelectiveSyncSetupMac
else:
    SelectiveSyncSetup = SelectiveSyncSetupWin

class XattrSetup(AdvancedSetupWizardPanel):

    def __init__(self, wizard):
        super(XattrSetup, self).__init__(wizard)
        self._title = SetupWizardStrings.xattr_title
        self._prev = DropboxLocation
        self._next = SelectiveSyncSetup
        form_items = [AdvancedPanelRadioGroup('enable_xattr', choices=[SetupWizardStrings.xattr_enable_choice, SetupWizardStrings.xattr_disable_choice], embedded_controls=[])]
        for item in form_items:
            self.add_form_item(item)

    def on_swap_out(self):
        xattr = not bool(self.enable_xattr)
        TRACE('User decided to %sable xattr support', 'en' if xattr else 'dis')
        self._wizard.enable_xattrs = xattr


class SetupWizardRequestThread(StoppableThread):

    def __init__(self, setup_wizard, *n, **kw):
        super(SetupWizardRequestThread, self).__init__(name='SETUPWIZARDR')
        self.setup_wizard = setup_wizard
        self.parents_last_panel = None
        self.conn = setup_wizard.dropbox_app.conn
        self.requests = collections.deque()
        self.requests_c = NativeCondition()
        self.wakeup_bang = AutoResetEvent()
        self.unhandled_exceptions = []

    def set_wakeup_event(self):
        self.wakeup_bang.set()

    def client_upgrade(self, ccn, expmo, expyr, ccode, address, zipcode, city, state, country, plan, period, name, on_success = None, on_error = None, version_number = 0):
        cmd = partial(self.conn.client_upgrade, ccn, expmo, expyr, ccode, address, zipcode, city, state, country, plan, period, name, version_number)
        self.queue_cmd(cmd, on_success, on_error)

    def client_upgrade_design_1(self, ccn, expmo, expyr, ccode, zipcode, country, plan, period, name, on_success = None, on_error = None):
        cmd = partial(self.conn.client_upgrade, ccn, expmo, expyr, ccode, None, zipcode, None, None, country, plan, period, name, 1)
        self.queue_cmd(cmd, on_success, on_error)

    def send_text(self, mobile_number, strategy, on_success = None, on_error = None):
        cmd = partial(self.conn.send_text, mobile_number, strategy)
        self.queue_cmd(cmd, on_success, on_error)

    def link_host_with_ret(self, host_id, email, password, display_name, is_sso_link, post_2fa_token, on_success = None, on_error = None):
        cmd = partial(self.conn.link_host_with_ret, host_id, email, password, display_name, is_sso_link, post_2fa_token)
        self.queue_cmd(cmd, on_success, on_error)

    def check_sso_user(self, host_id, email, on_success = None, on_error = None):
        cmd = partial(self.conn.check_sso_user, host_id, email)
        self.queue_cmd(cmd, on_success, on_error)

    def send_twofactor_sms(self, checkpoint_tkey, on_success = None, on_error = None):
        cmd = partial(self.conn.send_twofactor_sms, checkpoint_tkey)
        self.queue_cmd(cmd, on_success, on_error)

    def link_host_twofactor(self, host_id, checkpoint_tkey, display_name, twofactor_code, on_success = None, on_error = None):
        cmd = partial(self.conn.link_host_twofactor, host_id, checkpoint_tkey, display_name, twofactor_code)
        self.queue_cmd(cmd, on_success, on_error)

    def register_and_link_with_ret(self, host_id, fname, lname, email, password, password2, display_name, on_success = None, on_error = None):
        cmd = partial(self.conn.register_and_link_with_ret, host_id, fname, lname, email, password, password2, display_name)
        self.queue_cmd(cmd, on_success, on_error)

    def wizard_load_strings(self):
        cmd = partial(self.conn.wizard_load_strings)

        def on_success(response):
            TRACE('WIZARD_LOAD: updating strings')
            try:
                self.setup_wizard.wizard_strings_class()._server_overrides.update(response.get('overrides', {}))
            except:
                report_bad_assumption('Setup wizard class instance does not have wizard_strings_class method.')

        self.queue_cmd(cmd, on_success)

    def wizard_route(self, route, wizard_time, tour_time, mobile_text_panel = None, on_success = None, on_error = None):
        cmd = partial(self.conn.wizard_route, route, wizard_time, tour_time, mobile_text_panel)
        self.queue_cmd(cmd, on_success, on_error)

    def queue_cmd(self, cmd, on_success = None, on_error = None):
        with self.requests_c:
            self.requests.append((cmd, on_success, on_error))
            self.requests_c.notify()

    def stop(self):
        with self.requests_c:
            self.requests.append('<stop>')
            self.requests_c.notify()

    def _inner_connection_trouble(self):
        if isinstance(self.setup_wizard, SetupWizard):
            if not isinstance(self.setup_wizard.current_panel, ConnectionTrouble):
                self.parents_last_panel = self.setup_wizard.current_panel
                self.setup_wizard.swap(ConnectionTrouble)
        else:
            self.setup_wizard.show_connection_trouble()

    def connection_trouble(self):
        self._inner_connection_trouble()
        self.wakeup_bang.wait(timeout=30)

    def no_connection_trouble(self):
        if isinstance(self.setup_wizard, SetupWizard):
            try:
                if isinstance(self.setup_wizard.current_panel, ConnectionTrouble):
                    if self.setup_wizard.done:
                        return
                    if self.parents_last_panel is not None:
                        self.setup_wizard.swap(self.parents_last_panel, set_previous=False)
                        self.parents_last_panel = None
                    else:
                        self.setup_wizard.swap(WelcomePanel)
            except Exception:
                unhandled_exc_handler()

        else:
            self.setup_wizard.show_connection_trouble(False)

    def setup_wizard_request_loop(self):
        while not self.stopped():
            with self.requests_c:
                while not self.requests:
                    TRACE('Waiting for requests')
                    self.requests_c.wait()

                req = self.requests.popleft()
            if req == '<stop>':
                break
            cmd, on_success, on_error = req
            try:
                ret = cmd()
                try:
                    if callable(on_success):
                        on_success(ret)
                except Exception:
                    unhandled_exc_handler()

                self.no_connection_trouble()
            except DropboxServerError as e:
                TRACE('Dropbox Server Error!!')
                unhandled_exc_handler(False)
                try:
                    if callable(on_error):
                        on_error(e)
                except Exception:
                    unhandled_exc_handler()

            except Exception:
                unhandled_exc_handler()
                TRACE('Oh my. no internets! back around again')
                self.connection_trouble()
                with self.requests_c:
                    self.requests.appendleft(req)

        for exc_info in self.unhandled_exceptions:
            unhandled_exc_handler(exc_info=exc_info)

        TRACE("Job's done!")

    def run(self):
        TRACE('SetupWizardRequestThread started')
        self.conn.add_reconnect_wakeup(self.set_wakeup_event)
        try:
            self.setup_wizard_request_loop()
        finally:
            self.conn.remove_reconnect_wakeup(self.set_wakeup_event)
            self.conn.kill_all_connections()
            TRACE('SetupWizardRequestThread finished')
