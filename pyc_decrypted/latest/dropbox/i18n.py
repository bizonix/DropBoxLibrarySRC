#Embedded file name: dropbox/i18n.py
from __future__ import absolute_import
import cStringIO
import ctypes
import gettext as gettext_module
import locale
import math
import os
import time
import types
from datetime import datetime, timedelta
import babel
import babel.numbers
import dropbox.language_data
from dropbox.platform import platform
from dropbox.trace import TRACE, debugging_features_are_enabled, report_bad_assumption, unhandled_exc_handler
LOCALE_SPLITCHAR = dropbox.language_data.LOCALE_SPLITCHAR
APPLE_LANGUAGES = 'AppleLanguages'
_translation = gettext_module.NullTranslations()
_curr_code = dropbox.language_data.DEFAULT_CODE
_requested_code = dropbox.language_data.SYSTEM_LANG_CODE
_translation_activated = False

class TranslationInitializationException(Exception):
    pass


class TranslationAlreadyInitialized(TranslationInitializationException):
    pass


class TranslationLanguageError(TranslationInitializationException):
    pass


def ago(dt, now = None):
    if now is None:
        now = time.time()
    secs = now - dt
    if secs < 15:
        return trans(u'Just now')
    if secs < 60:
        formatted = int(secs)
        result = ungettext(u'%s sec ago', u'%s secs ago', formatted)
    elif secs < 3600:
        formatted = int(secs / 60)
        result = ungettext(u'%s min ago', u'%s mins ago', formatted)
    elif secs < 86400:
        formatted = int(secs / 3600)
        result = ungettext(u'%s hour ago', u'%s hours ago', formatted)
    elif secs < 2592000:
        formatted = int(secs / 86400)
        result = ungettext(u'%s day ago', u'%s days ago', formatted)
    elif secs < 4838400:
        formatted = int(secs / 604800)
        result = ungettext(u'%s week ago', u'%s weeks ago', formatted)
    elif secs < 31536000:
        formatted = int(secs / 2592000)
        result = ungettext(u'%s month ago', u'%s months ago', formatted)
    else:
        formatted = int(secs / 31536000)
        result = ungettext(u'%s year ago', u'%s years ago', formatted)
    return result % (format_number(formatted, frac_precision=0),)


def format_number(n, frac_precision = None):
    try:
        _locale = babel.Locale.parse(get_current_code())
        pattern = _locale.decimal_formats.get(None)
        if frac_precision is not None:
            pattern = babel.numbers.parse_pattern(pattern.pattern)
            pattern.frac_prec = (frac_precision, frac_precision)
        return pattern.apply(n, _locale)
    except Exception:
        unhandled_exc_handler()
        if frac_precision is None:
            return unicode(n)
        elif not frac_precision:
            return unicode(int(n))
        else:
            return u'%%.%df' % frac_precision % n


def format_percent(n, frac_precision = None):
    try:
        _locale = babel.Locale.parse(get_current_code())
        pattern = _locale.percent_formats.get(None)
        if frac_precision is not None:
            pattern = babel.numbers.parse_pattern(pattern.pattern)
            pattern.frac_prec = (frac_precision, frac_precision)
        return pattern.apply(n, _locale)
    except Exception:
        unhandled_exc_handler()
        n = float(n) * 100
        if frac_precision is None:
            return unicode(n) + u'%'
        elif not frac_precision:
            return unicode(int(n)) + u'%'
        else:
            return u'%%.%df' % frac_precision % n + u'%'


KB = 1024
MB = KB ** 2
GB = KB ** 3
TB = KB ** 4

def format_bytes(value, digits = 1, include_space = True, trailing_zeros = False):
    value = float(value)
    abs_value = abs(value)
    if abs_value < KB:
        digits = 0
        include_space = True
        amt = value
        suffix = ungettext(u'byte', u'bytes', value)
    elif abs_value < 900 * KB:
        amt = value / KB
        suffix = trans(u'KB')
    elif abs_value < 900 * MB:
        amt = value / MB
        suffix = trans(u'MB')
    elif abs_value < 900 * GB or digits == 0 and value < TB:
        amt = value / GB
        suffix = trans(u'GB')
    else:
        amt = value / TB
        suffix = trans(u'TB')
    amt = round(amt * 10 ** digits) / float(10 ** digits)
    if not trailing_zeros and digits > 0 and amt == math.floor(amt):
        digits = 0
    amt = format_number(amt, frac_precision=digits)
    return u'%s%s%s' % (amt, ' ' if include_space else '', suffix)


def trans(msgid):
    global _translation
    global _translation_activated
    assert type(msgid) == types.UnicodeType, u"string not unicode: '%s'" % (msgid,)
    if not _translation_activated:
        report_bad_assumption(u'not initialized: trans called for %r' % (msgid,), full_stack=True)
    if not msgid:
        return msgid
    return _translation.ugettext(msgid)


def ungettext(singular, plural, n):
    assert type(singular) == types.UnicodeType, u"string not unicode: '%s'" % (singular,)
    assert type(plural) == types.UnicodeType, u"string not unicode: '%s'" % (plural,)
    if not _translation_activated:
        report_bad_assumption(u'not initialized: ungettext called for %r' % (singular,), full_stack=True)
    return _translation.ungettext(singular, plural, n)


def get_default_code_for_prefs():
    return dropbox.language_data.SYSTEM_LANG_CODE


def get_available_languages():
    ret = [(dropbox.language_data.SYSTEM_LANG_CODE, trans(u'System Language'), u'System Language')]
    if debugging_features_are_enabled():
        codes = dropbox.language_data.ORDERED_LANGUAGE_CODES_DEV
    else:
        codes = dropbox.language_data.ORDERED_LANGUAGE_CODES
    for code in codes:
        ret.append((code, dropbox.language_data.get_native_name_for_code(code), dropbox.language_data.get_english_name_for_code(code)))

    return ret


def get_current_code():
    global _curr_code
    if not _translation_activated:
        report_bad_assumption(u'not initialized: get_current_code() called', full_stack=True)
    return _curr_code


def get_requested_code():
    global _requested_code
    if not _translation_activated:
        report_bad_assumption(u'not initialized: get_requested_code() called', full_stack=True)
    return _requested_code


def activate_translation(requested_code = dropbox.language_data.SYSTEM_LANG_CODE, force = False):
    global _translation
    global _curr_code
    global _requested_code
    global _translation_activated
    TRACE(u'activate_translation(%r)', requested_code)
    if _translation_activated and not force:
        raise TranslationAlreadyInitialized()
    code = requested_code
    if code == dropbox.language_data.SYSTEM_LANG_CODE:
        code = system_lang_code()
    try:
        dropbox.language_data.get_native_name_for_code(code)
    except KeyError:
        raise TranslationLanguageError(u'no such language code available %r' % (code,))

    _translation = get_translation(code)
    if _translation.__class__ == gettext_module.NullTranslations:
        TRACE(u'i18n activated with Null Translator; asked for %r', code)
    else:
        TRACE(u'i18n activated for %s', code)
    _requested_code = requested_code
    _curr_code = code
    _translation_activated = True


def safe_activate_translation():
    try:
        activate_translation('')
    except TranslationAlreadyInitialized:
        pass
    except Exception:
        unhandled_exc_handler()


def get_translation(code):
    TRACE('CODE is %s', code)
    if code in dropbox.language_data.NULL_CODES:
        return gettext_module.NullTranslations()
    submodule_name = 'mofile_%s' % (code,)
    module_name = 'lang.%s' % submodule_name
    try:
        mo_binary = getattr(__import__(module_name), submodule_name).mo_binary
    except KeyError:
        raise TranslationInitializationException(u'Missing the translation module for %s' % (code,))

    return gettext_module.GNUTranslations(cStringIO.StringIO(mo_binary))


def system_lang_code():
    for syslang in get_system_languages():
        try:
            if not syslang:
                continue
            TRACE('Finding best match for system language %s', syslang)
            possibilities = dropbox.language_data.POSSIBLE_CODES_FOR_LANG.get(syslang)
            if possibilities:
                return _distinguish_possibilities(syslang, possibilities)
            if LOCALE_SPLITCHAR in syslang:
                short = syslang.split(LOCALE_SPLITCHAR, 1)[0]
                possibilities = dropbox.language_data.POSSIBLE_CODES_FOR_LANG.get(short)
                if possibilities:
                    return _distinguish_possibilities(syslang, possibilities)
        except Exception:
            unhandled_exc_handler()

    return dropbox.language_data.DEFAULT_CODE


def _distinguish_possibilities(syslang, possibilities, _country_code = None):
    assert len(possibilities)
    if len(possibilities) == 1:
        return possibilities[0]
    syslang = dropbox.language_data.get_lang_mapped_to_variant(syslang)
    if LOCALE_SPLITCHAR in syslang:
        code = syslang
        short = code.split(LOCALE_SPLITCHAR)[0]
    else:
        country_code = _country_code or get_country_code()
        code = '%s%s%s' % (syslang, LOCALE_SPLITCHAR, country_code)
        short = syslang
    if code in possibilities:
        return code
    if short in possibilities:
        return short
    report_bad_assumption('Unhandled language: given %r, how do I pick from %r?', syslang, possibilities)
    return possibilities[0]


def lang_is_fully_supported(code):
    if code in dropbox.language_data.DEVELOPMENT_LANGUAGE_CODES:
        return True
    if platform == 'mac':
        return True
    if platform == 'win':
        return True
    if platform == 'linux':
        import wx
        return wx.Locale.IsAvailable(wx.Locale.FindLanguageInfo(code).Language)


def _mac_get_system_languages():
    assert platform == 'mac'
    from Foundation import NSAutoreleasePool, NSString, NSUserDefaults
    arp = NSAutoreleasePool.alloc().init()
    s = NSString.alloc().initWithString_(APPLE_LANGUAGES)
    try:
        from pymac.helpers.core import get_preference
        langs = list(get_preference('com.apple.systempreferences', APPLE_LANGUAGES))
        TRACE('_mac_get_system_languages real: %r', langs)
        return langs
    except Exception:
        unhandled_exc_handler()

    langs = NSUserDefaults.standardUserDefaults().get(s)
    TRACE('_mac_get_system_languages from user: %r', langs)
    return langs


def get_system_languages():
    if platform == 'mac':
        langs = _mac_get_system_languages()
        return_langs = []
        for lang in langs:
            if len(lang) > 2 and lang[2] == '-':
                rlang = lang.replace('-', LOCALE_SPLITCHAR)
            else:
                rlang = dropbox.language_data.get_lang_from_mac_english_name(lang)
            return_langs.append(rlang)

        return return_langs
    if platform == 'linux':
        if 'LANGUAGE' in os.environ:
            return os.environ['LANGUAGE'].split(':')
    return [locale.getdefaultlocale()[0]]


def set_user_interface_language(code):
    if platform == 'mac':
        from Foundation import NSAutoreleasePool, NSString, NSUserDefaults
        arp = NSAutoreleasePool.alloc().init()
        s = NSString.alloc().initWithString_(APPLE_LANGUAGES)
        defaults = NSUserDefaults.standardUserDefaults()
        if code == '':
            TRACE('Setting language defaults to system language.')
            defaults.removeObjectForKey_(s)
        else:
            TRACE('Updating language defaults to %r.', code)
            defaults.setObject_forKey_([code], s)
        defaults.synchronize()


def get_country_code():
    try:
        if platform == 'linux':
            l = locale.getdefaultlocale()[0]
            if l is not None:
                return l.split(LOCALE_SPLITCHAR, 1)[1][:2].upper()
        elif platform == 'mac':
            from Foundation import NSAutoreleasePool, NSLocale, NSLocaleCountryCode
            pool = NSAutoreleasePool.alloc().init()
            try:
                return NSLocale.currentLocale().objectForKey_(NSLocaleCountryCode).upper()
            finally:
                del pool

        else:
            from dropbox.win32.version import WIN2K, WINDOWS_VERSION
            if WINDOWS_VERSION != WIN2K:
                GEO_ISO2 = 4
                nation = ctypes.windll.kernel32.GetUserGeoID(16)
                buf = ctypes.create_string_buffer(20)
                if ctypes.windll.kernel32.GetGeoInfoA(nation, GEO_ISO2, ctypes.byref(buf), ctypes.sizeof(buf), 0):
                    return buf.value.upper()
    except Exception:
        unhandled_exc_handler()

    return 'US'


def is_i18n():
    return get_current_code() not in dropbox.language_data.NULL_CODES
