#Embedded file name: babel/core.py
import os
import pickle
from babel import localedata
__all__ = ['UnknownLocaleError',
 'Locale',
 'default_locale',
 'negotiate_locale',
 'parse_locale']
__docformat__ = 'restructuredtext en'
_global_data = None

def get_global(key):
    global _global_data
    if _global_data is None:
        dirname = os.path.join(os.path.dirname(__file__))
        filename = os.path.join(dirname, 'global.dat')
        fileobj = open(filename, 'rb')
        try:
            _global_data = pickle.load(fileobj)
        finally:
            fileobj.close()

    return _global_data.get(key, {})


LOCALE_ALIASES = {'ar': 'ar_SY',
 'bg': 'bg_BG',
 'bs': 'bs_BA',
 'ca': 'ca_ES',
 'cs': 'cs_CZ',
 'da': 'da_DK',
 'de': 'de_DE',
 'el': 'el_GR',
 'en': 'en_US',
 'es': 'es_ES',
 'et': 'et_EE',
 'fa': 'fa_IR',
 'fi': 'fi_FI',
 'fr': 'fr_FR',
 'gl': 'gl_ES',
 'he': 'he_IL',
 'hu': 'hu_HU',
 'id': 'id_ID',
 'is': 'is_IS',
 'it': 'it_IT',
 'ja': 'ja_JP',
 'km': 'km_KH',
 'ko': 'ko_KR',
 'lt': 'lt_LT',
 'lv': 'lv_LV',
 'mk': 'mk_MK',
 'nl': 'nl_NL',
 'nn': 'nn_NO',
 'no': 'nb_NO',
 'pl': 'pl_PL',
 'pt': 'pt_PT',
 'ro': 'ro_RO',
 'ru': 'ru_RU',
 'sk': 'sk_SK',
 'sl': 'sl_SI',
 'sv': 'sv_SE',
 'th': 'th_TH',
 'tr': 'tr_TR',
 'uk': 'uk_UA'}

class UnknownLocaleError(Exception):

    def __init__(self, identifier):
        Exception.__init__(self, 'unknown locale %r' % identifier)
        self.identifier = identifier


class Locale(object):

    def __init__(self, language, territory = None, script = None, variant = None):
        self.language = language
        self.territory = territory
        self.script = script
        self.variant = variant
        self.__data = None
        identifier = str(self)
        if not localedata.exists(identifier):
            raise UnknownLocaleError(identifier)

    def default(cls, category = None, aliases = LOCALE_ALIASES):
        return cls(default_locale(category, aliases=aliases))

    default = classmethod(default)

    def negotiate(cls, preferred, available, sep = '_', aliases = LOCALE_ALIASES):
        identifier = negotiate_locale(preferred, available, sep=sep, aliases=aliases)
        if identifier:
            return Locale.parse(identifier, sep=sep)

    negotiate = classmethod(negotiate)

    def parse(cls, identifier, sep = '_'):
        if isinstance(identifier, basestring):
            return cls(*parse_locale(identifier, sep=sep))
        return identifier

    parse = classmethod(parse)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Locale "%s">' % str(self)

    def __str__(self):
        return '_'.join(filter(None, [self.language,
         self.script,
         self.territory,
         self.variant]))

    def _data(self):
        if self.__data is None:
            self.__data = localedata.LocaleDataDict(localedata.load(str(self)))
        return self.__data

    _data = property(_data)

    def get_display_name(self, locale = None):
        if locale is None:
            locale = self
        locale = Locale.parse(locale)
        retval = locale.languages.get(self.language)
        if self.territory or self.script or self.variant:
            details = []
            if self.script:
                details.append(locale.scripts.get(self.script))
            if self.territory:
                details.append(locale.territories.get(self.territory))
            if self.variant:
                details.append(locale.variants.get(self.variant))
            details = filter(None, details)
            if details:
                retval += ' (%s)' % u', '.join(details)
        return retval

    display_name = property(get_display_name, doc="        The localized display name of the locale.\n\n        >>> Locale('en').display_name\n        u'English'\n        >>> Locale('en', 'US').display_name\n        u'English (United States)'\n        >>> Locale('sv').display_name\n        u'svenska'\n\n        :type: `unicode`\n        ")

    def english_name(self):
        return self.get_display_name(Locale('en'))

    english_name = property(english_name, doc="        The english display name of the locale.\n\n        >>> Locale('de').english_name\n        u'German'\n        >>> Locale('de', 'DE').english_name\n        u'German (Germany)'\n\n        :type: `unicode`\n        ")

    def languages(self):
        return self._data['languages']

    languages = property(languages, doc="        Mapping of language codes to translated language names.\n\n        >>> Locale('de', 'DE').languages['ja']\n        u'Japanisch'\n\n        :type: `dict`\n        :see: `ISO 639 <http://www.loc.gov/standards/iso639-2/>`_\n        ")

    def scripts(self):
        return self._data['scripts']

    scripts = property(scripts, doc="        Mapping of script codes to translated script names.\n\n        >>> Locale('en', 'US').scripts['Hira']\n        u'Hiragana'\n\n        :type: `dict`\n        :see: `ISO 15924 <http://www.evertype.com/standards/iso15924/>`_\n        ")

    def territories(self):
        return self._data['territories']

    territories = property(territories, doc="        Mapping of script codes to translated script names.\n\n        >>> Locale('es', 'CO').territories['DE']\n        u'Alemania'\n\n        :type: `dict`\n        :see: `ISO 3166 <http://www.iso.org/iso/en/prods-services/iso3166ma/>`_\n        ")

    def variants(self):
        return self._data['variants']

    variants = property(variants, doc="        Mapping of script codes to translated script names.\n\n        >>> Locale('de', 'DE').variants['1901']\n        u'Alte deutsche Rechtschreibung'\n\n        :type: `dict`\n        ")

    def currencies(self):
        return self._data['currency_names']

    currencies = property(currencies, doc="        Mapping of currency codes to translated currency names.\n\n        >>> Locale('en').currencies['COP']\n        u'Colombian Peso'\n        >>> Locale('de', 'DE').currencies['COP']\n        u'Kolumbianischer Peso'\n\n        :type: `dict`\n        ")

    def currency_symbols(self):
        return self._data['currency_symbols']

    currency_symbols = property(currency_symbols, doc="        Mapping of currency codes to symbols.\n\n        >>> Locale('en', 'US').currency_symbols['USD']\n        u'$'\n        >>> Locale('es', 'CO').currency_symbols['USD']\n        u'US$'\n\n        :type: `dict`\n        ")

    def number_symbols(self):
        return self._data['number_symbols']

    number_symbols = property(number_symbols, doc="        Symbols used in number formatting.\n\n        >>> Locale('fr', 'FR').number_symbols['decimal']\n        u','\n\n        :type: `dict`\n        ")

    def decimal_formats(self):
        return self._data['decimal_formats']

    decimal_formats = property(decimal_formats, doc="        Locale patterns for decimal number formatting.\n\n        >>> Locale('en', 'US').decimal_formats[None]\n        <NumberPattern u'#,##0.###'>\n\n        :type: `dict`\n        ")

    def currency_formats(self):
        return self._data['currency_formats']

    currency_formats = property(currency_formats, doc="\\\n        Locale patterns for currency number formatting.\n\n        >>> print Locale('en', 'US').currency_formats[None]\n        <NumberPattern u'\\xa4#,##0.00'>\n\n        :type: `dict`\n        ")

    def percent_formats(self):
        return self._data['percent_formats']

    percent_formats = property(percent_formats, doc="        Locale patterns for percent number formatting.\n\n        >>> Locale('en', 'US').percent_formats[None]\n        <NumberPattern u'#,##0%'>\n\n        :type: `dict`\n        ")

    def scientific_formats(self):
        return self._data['scientific_formats']

    scientific_formats = property(scientific_formats, doc="        Locale patterns for scientific number formatting.\n\n        >>> Locale('en', 'US').scientific_formats[None]\n        <NumberPattern u'#E0'>\n\n        :type: `dict`\n        ")

    def periods(self):
        return self._data['periods']

    periods = property(periods, doc="        Locale display names for day periods (AM/PM).\n\n        >>> Locale('en', 'US').periods['am']\n        u'AM'\n\n        :type: `dict`\n        ")

    def days(self):
        return self._data['days']

    days = property(days, doc="        Locale display names for weekdays.\n\n        >>> Locale('de', 'DE').days['format']['wide'][3]\n        u'Donnerstag'\n\n        :type: `dict`\n        ")

    def months(self):
        return self._data['months']

    months = property(months, doc="        Locale display names for months.\n\n        >>> Locale('de', 'DE').months['format']['wide'][10]\n        u'Oktober'\n\n        :type: `dict`\n        ")

    def quarters(self):
        return self._data['quarters']

    quarters = property(quarters, doc="        Locale display names for quarters.\n\n        >>> Locale('de', 'DE').quarters['format']['wide'][1]\n        u'1. Quartal'\n\n        :type: `dict`\n        ")

    def eras(self):
        return self._data['eras']

    eras = property(eras, doc="        Locale display names for eras.\n\n        >>> Locale('en', 'US').eras['wide'][1]\n        u'Anno Domini'\n        >>> Locale('en', 'US').eras['abbreviated'][0]\n        u'BC'\n\n        :type: `dict`\n        ")

    def time_zones(self):
        return self._data['time_zones']

    time_zones = property(time_zones, doc='        Locale display names for time zones.\n\n        >>> Locale(\'en\', \'US\').time_zones[\'Europe/London\'][\'long\'][\'daylight\']\n        u\'British Summer Time\'\n        >>> Locale(\'en\', \'US\').time_zones[\'America/St_Johns\'][\'city\']\n        u"St. John\'s"\n\n        :type: `dict`\n        ')

    def meta_zones(self):
        return self._data['meta_zones']

    meta_zones = property(meta_zones, doc="        Locale display names for meta time zones.\n\n        Meta time zones are basically groups of different Olson time zones that\n        have the same GMT offset and daylight savings time.\n\n        >>> Locale('en', 'US').meta_zones['Europe_Central']['long']['daylight']\n        u'Central European Summer Time'\n\n        :type: `dict`\n        :since: version 0.9\n        ")

    def zone_formats(self):
        return self._data['zone_formats']

    zone_formats = property(zone_formats, doc="\\\n        Patterns related to the formatting of time zones.\n\n        >>> Locale('en', 'US').zone_formats['fallback']\n        u'%(1)s (%(0)s)'\n        >>> Locale('pt', 'BR').zone_formats['region']\n        u'Hor\\xe1rio %s'\n\n        :type: `dict`\n        :since: version 0.9\n        ")

    def first_week_day(self):
        return self._data['week_data']['first_day']

    first_week_day = property(first_week_day, doc="        The first day of a week, with 0 being Monday.\n\n        >>> Locale('de', 'DE').first_week_day\n        0\n        >>> Locale('en', 'US').first_week_day\n        6\n\n        :type: `int`\n        ")

    def weekend_start(self):
        return self._data['week_data']['weekend_start']

    weekend_start = property(weekend_start, doc="        The day the weekend starts, with 0 being Monday.\n\n        >>> Locale('de', 'DE').weekend_start\n        5\n\n        :type: `int`\n        ")

    def weekend_end(self):
        return self._data['week_data']['weekend_end']

    weekend_end = property(weekend_end, doc="        The day the weekend ends, with 0 being Monday.\n\n        >>> Locale('de', 'DE').weekend_end\n        6\n\n        :type: `int`\n        ")

    def min_week_days(self):
        return self._data['week_data']['min_days']

    min_week_days = property(min_week_days, doc="        The minimum number of days in a week so that the week is counted as the\n        first week of a year or month.\n\n        >>> Locale('de', 'DE').min_week_days\n        4\n\n        :type: `int`\n        ")

    def date_formats(self):
        return self._data['date_formats']

    date_formats = property(date_formats, doc="        Locale patterns for date formatting.\n\n        >>> Locale('en', 'US').date_formats['short']\n        <DateTimePattern u'M/d/yy'>\n        >>> Locale('fr', 'FR').date_formats['long']\n        <DateTimePattern u'd MMMM yyyy'>\n\n        :type: `dict`\n        ")

    def time_formats(self):
        return self._data['time_formats']

    time_formats = property(time_formats, doc="        Locale patterns for time formatting.\n\n        >>> Locale('en', 'US').time_formats['short']\n        <DateTimePattern u'h:mm a'>\n        >>> Locale('fr', 'FR').time_formats['long']\n        <DateTimePattern u'HH:mm:ss z'>\n\n        :type: `dict`\n        ")

    def datetime_formats(self):
        return self._data['datetime_formats']

    datetime_formats = property(datetime_formats, doc="        Locale patterns for datetime formatting.\n\n        >>> Locale('en').datetime_formats[None]\n        u'{1} {0}'\n        >>> Locale('th').datetime_formats[None]\n        u'{1}, {0}'\n\n        :type: `dict`\n        ")


def default_locale(category = None, aliases = LOCALE_ALIASES):
    varnames = (category,
     'LANGUAGE',
     'LC_ALL',
     'LC_CTYPE',
     'LANG')
    for name in filter(None, varnames):
        locale = os.getenv(name)
        if locale:
            if name == 'LANGUAGE' and ':' in locale:
                locale = locale.split(':')[0]
            if locale in ('C', 'POSIX'):
                locale = 'en_US_POSIX'
            elif aliases and locale in aliases:
                locale = aliases[locale]
            try:
                return '_'.join(filter(None, parse_locale(locale)))
            except ValueError:
                pass


def negotiate_locale(preferred, available, sep = '_', aliases = LOCALE_ALIASES):
    available = [ a.lower() for a in available if a ]
    for locale in preferred:
        ll = locale.lower()
        if ll in available:
            return locale
        if aliases:
            alias = aliases.get(ll)
            if alias:
                alias = alias.replace('_', sep)
                if alias.lower() in available:
                    return alias
        parts = locale.split(sep)
        if len(parts) > 1 and parts[0].lower() in available:
            return parts[0]


def parse_locale(identifier, sep = '_'):
    if '.' in identifier:
        identifier = identifier.split('.', 1)[0]
    if '@' in identifier:
        identifier = identifier.split('@', 1)[0]
    parts = identifier.split(sep)
    lang = parts.pop(0).lower()
    if not lang.isalpha():
        raise ValueError('expected only letters, got %r' % lang)
    script = territory = variant = None
    if parts:
        if len(parts[0]) == 4 and parts[0].isalpha():
            script = parts.pop(0).title()
    if parts:
        if len(parts[0]) == 2 and parts[0].isalpha():
            territory = parts.pop(0).upper()
        elif len(parts[0]) == 3 and parts[0].isdigit():
            territory = parts.pop(0)
    if parts:
        if len(parts[0]) == 4 and parts[0][0].isdigit() or len(parts[0]) >= 5 and parts[0][0].isalpha():
            variant = parts.pop()
    if parts:
        raise ValueError('%r is not a valid locale identifier' % identifier)
    return (lang,
     territory,
     script,
     variant)
