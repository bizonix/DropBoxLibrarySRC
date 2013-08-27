#Embedded file name: babel/dates.py
from datetime import date, datetime, time, timedelta, tzinfo
import re
from babel.core import default_locale, get_global, Locale
from babel.util import UTC
__all__ = ['format_date',
 'format_datetime',
 'format_time',
 'get_timezone_name',
 'parse_date',
 'parse_datetime',
 'parse_time']
__docformat__ = 'restructuredtext en'
LC_TIME = default_locale('LC_TIME')
date_ = date
datetime_ = datetime
time_ = time

def get_period_names(locale = LC_TIME):
    return Locale.parse(locale).periods


def get_day_names(width = 'wide', context = 'format', locale = LC_TIME):
    return Locale.parse(locale).days[context][width]


def get_month_names(width = 'wide', context = 'format', locale = LC_TIME):
    return Locale.parse(locale).months[context][width]


def get_quarter_names(width = 'wide', context = 'format', locale = LC_TIME):
    return Locale.parse(locale).quarters[context][width]


def get_era_names(width = 'wide', locale = LC_TIME):
    return Locale.parse(locale).eras[width]


def get_date_format(format = 'medium', locale = LC_TIME):
    return Locale.parse(locale).date_formats[format]


def get_datetime_format(format = 'medium', locale = LC_TIME):
    patterns = Locale.parse(locale).datetime_formats
    if format not in patterns:
        format = None
    return patterns[format]


def get_time_format(format = 'medium', locale = LC_TIME):
    return Locale.parse(locale).time_formats[format]


def get_timezone_gmt(datetime = None, width = 'long', locale = LC_TIME):
    if datetime is None:
        datetime = datetime_.utcnow()
    elif isinstance(datetime, (int, long)):
        datetime = datetime_.utcfromtimestamp(datetime).time()
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    locale = Locale.parse(locale)
    offset = datetime.tzinfo.utcoffset(datetime)
    seconds = offset.days * 24 * 60 * 60 + offset.seconds
    hours, seconds = divmod(seconds, 3600)
    if width == 'short':
        pattern = u'%+03d%02d'
    else:
        pattern = locale.zone_formats['gmt'] % '%+03d:%02d'
    return pattern % (hours, seconds // 60)


def get_timezone_location(dt_or_tzinfo = None, locale = LC_TIME):
    if dt_or_tzinfo is None or isinstance(dt_or_tzinfo, (int, long)):
        dt = None
        tzinfo = UTC
    elif isinstance(dt_or_tzinfo, (datetime, time)):
        dt = dt_or_tzinfo
        if dt.tzinfo is not None:
            tzinfo = dt.tzinfo
        else:
            tzinfo = UTC
    else:
        dt = None
        tzinfo = dt_or_tzinfo
    locale = Locale.parse(locale)
    if hasattr(tzinfo, 'zone'):
        zone = tzinfo.zone
    else:
        zone = tzinfo.tzname(dt or datetime.utcnow())
    zone = get_global('zone_aliases').get(zone, zone)
    info = locale.time_zones.get(zone, {})
    region_format = locale.zone_formats['region']
    territory = get_global('zone_territories').get(zone)
    if territory not in locale.territories:
        territory = 'ZZ'
    territory_name = locale.territories[territory]
    if territory and len(get_global('territory_zones').get(territory, [])) == 1:
        return region_format % territory_name
    fallback_format = locale.zone_formats['fallback']
    if 'city' in info:
        city_name = info['city']
    else:
        metazone = get_global('meta_zones').get(zone)
        metazone_info = locale.meta_zones.get(metazone, {})
        if 'city' in metazone_info:
            city_name = metazone_info['city']
        elif '/' in zone:
            city_name = zone.split('/', 1)[1].replace('_', ' ')
        else:
            city_name = zone.replace('_', ' ')
    return region_format % (fallback_format % {'0': city_name,
     '1': territory_name})


def get_timezone_name(dt_or_tzinfo = None, width = 'long', uncommon = False, locale = LC_TIME):
    if dt_or_tzinfo is None or isinstance(dt_or_tzinfo, (int, long)):
        dt = None
        tzinfo = UTC
    elif isinstance(dt_or_tzinfo, (datetime, time)):
        dt = dt_or_tzinfo
        if dt.tzinfo is not None:
            tzinfo = dt.tzinfo
        else:
            tzinfo = UTC
    else:
        dt = None
        tzinfo = dt_or_tzinfo
    locale = Locale.parse(locale)
    if hasattr(tzinfo, 'zone'):
        zone = tzinfo.zone
    else:
        zone = tzinfo.tzname(dt)
    zone = get_global('zone_aliases').get(zone, zone)
    info = locale.time_zones.get(zone, {})
    if width in info:
        if dt is None:
            field = 'generic'
        else:
            dst = tzinfo.dst(dt)
            if dst is None:
                field = 'generic'
            elif dst == 0:
                field = 'standard'
            else:
                field = 'daylight'
        if field in info[width]:
            return info[width][field]
    metazone = get_global('meta_zones').get(zone)
    if metazone:
        metazone_info = locale.meta_zones.get(metazone, {})
        if width in metazone_info and (uncommon or metazone_info.get('common')):
            if dt is None:
                field = 'generic'
            else:
                field = tzinfo.dst(dt) and 'daylight' or 'standard'
            if field in metazone_info[width]:
                return metazone_info[width][field]
    if dt is not None:
        return get_timezone_gmt(dt, width=width, locale=locale)
    return get_timezone_location(dt_or_tzinfo, locale=locale)


def format_date(date = None, format = 'medium', locale = LC_TIME):
    if date is None:
        date = date_.today()
    elif isinstance(date, datetime):
        date = date.date()
    locale = Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        format = get_date_format(format, locale=locale)
    pattern = parse_pattern(format)
    return pattern.apply(date, locale)


def format_datetime(datetime = None, format = 'medium', tzinfo = None, locale = LC_TIME):
    if datetime is None:
        datetime = datetime_.utcnow()
    elif isinstance(datetime, (int, long)):
        datetime = datetime_.utcfromtimestamp(datetime)
    elif isinstance(datetime, time):
        datetime = datetime_.combine(date.today(), datetime)
    if datetime.tzinfo is None:
        datetime = datetime.replace(tzinfo=UTC)
    if tzinfo is not None:
        datetime = datetime.astimezone(tzinfo)
        if hasattr(tzinfo, 'normalize'):
            datetime = tzinfo.normalize(datetime)
    locale = Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        return get_datetime_format(format, locale=locale).replace('{0}', format_time(datetime, format, tzinfo=None, locale=locale)).replace('{1}', format_date(datetime, format, locale=locale))
    else:
        return parse_pattern(format).apply(datetime, locale)


def format_time(time = None, format = 'medium', tzinfo = None, locale = LC_TIME):
    if time is None:
        time = datetime.utcnow()
    elif isinstance(time, (int, long)):
        time = datetime.utcfromtimestamp(time)
    if time.tzinfo is None:
        time = time.replace(tzinfo=UTC)
    if isinstance(time, datetime):
        if tzinfo is not None:
            time = time.astimezone(tzinfo)
            if hasattr(tzinfo, 'normalize'):
                time = tzinfo.normalize(time)
        time = time.timetz()
    elif tzinfo is not None:
        time = time.replace(tzinfo=tzinfo)
    locale = Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        format = get_time_format(format, locale=locale)
    return parse_pattern(format).apply(time, locale)


def parse_date(string, locale = LC_TIME):
    format = get_date_format(locale=locale).pattern.lower()
    year_idx = format.index('y')
    month_idx = format.index('m')
    if month_idx < 0:
        month_idx = format.index('l')
    day_idx = format.index('d')
    indexes = [(year_idx, 'Y'), (month_idx, 'M'), (day_idx, 'D')]
    indexes.sort()
    indexes = dict([ (item[1], idx) for idx, item in enumerate(indexes) ])
    numbers = re.findall('(\\d+)', string)
    year = numbers[indexes['Y']]
    if len(year) == 2:
        year = 2000 + int(year)
    else:
        year = int(year)
    month = int(numbers[indexes['M']])
    day = int(numbers[indexes['D']])
    if month > 12:
        month, day = day, month
    return date(year, month, day)


def parse_datetime(string, locale = LC_TIME):
    raise NotImplementedError


def parse_time(string, locale = LC_TIME):
    format = get_time_format(locale=locale).pattern.lower()
    hour_idx = format.index('h')
    if hour_idx < 0:
        hour_idx = format.index('k')
    min_idx = format.index('m')
    sec_idx = format.index('s')
    indexes = [(hour_idx, 'H'), (min_idx, 'M'), (sec_idx, 'S')]
    indexes.sort()
    indexes = dict([ (item[1], idx) for idx, item in enumerate(indexes) ])
    numbers = re.findall('(\\d+)', string)
    hour = int(numbers[indexes['H']])
    minute = int(numbers[indexes['M']])
    second = int(numbers[indexes['S']])
    return time(hour, minute, second)


class DateTimePattern(object):

    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.pattern)

    def __unicode__(self):
        return self.pattern

    def __mod__(self, other):
        assert type(other) is DateTimeFormat
        return self.format % other

    def apply(self, datetime, locale):
        return self % DateTimeFormat(datetime, locale)


class DateTimeFormat(object):

    def __init__(self, value, locale):
        assert isinstance(value, (date, datetime, time))
        if isinstance(value, (datetime, time)) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        self.value = value
        self.locale = Locale.parse(locale)

    def __getitem__(self, name):
        char = name[0]
        num = len(name)
        if char == 'G':
            return self.format_era(char, num)
        if char in ('y', 'Y', 'u'):
            return self.format_year(char, num)
        if char in ('Q', 'q'):
            return self.format_quarter(char, num)
        if char in ('M', 'L'):
            return self.format_month(char, num)
        if char in ('w', 'W'):
            return self.format_week(char, num)
        if char == 'd':
            return self.format(self.value.day, num)
        if char == 'D':
            return self.format_day_of_year(num)
        if char == 'F':
            return self.format_day_of_week_in_month()
        if char in ('E', 'e', 'c'):
            return self.format_weekday(char, num)
        if char == 'a':
            return self.format_period(char)
        if char == 'h':
            if self.value.hour % 12 == 0:
                return self.format(12, num)
            else:
                return self.format(self.value.hour % 12, num)
        else:
            if char == 'H':
                return self.format(self.value.hour, num)
            if char == 'K':
                return self.format(self.value.hour % 12, num)
            if char == 'k':
                if self.value.hour == 0:
                    return self.format(24, num)
                else:
                    return self.format(self.value.hour, num)
            else:
                if char == 'm':
                    return self.format(self.value.minute, num)
                if char == 's':
                    return self.format(self.value.second, num)
                if char == 'S':
                    return self.format_frac_seconds(num)
                if char == 'A':
                    return self.format_milliseconds_in_day(num)
                if char in ('z', 'Z', 'v', 'V'):
                    return self.format_timezone(char, num)
                raise KeyError('Unsupported date/time field %r' % char)

    def format_era(self, char, num):
        width = {3: 'abbreviated',
         4: 'wide',
         5: 'narrow'}[max(3, num)]
        era = int(self.value.year >= 0)
        return get_era_names(width, self.locale)[era]

    def format_year(self, char, num):
        value = self.value.year
        if char.isupper():
            week = self.get_week_number(self.get_day_of_year())
            if week == 0:
                value -= 1
        year = self.format(value, num)
        if num == 2:
            year = year[-2:]
        return year

    def format_quarter(self, char, num):
        quarter = (self.value.month - 1) // 3 + 1
        if num <= 2:
            return '%%0%dd' % num % quarter
        width = {3: 'abbreviated',
         4: 'wide',
         5: 'narrow'}[num]
        context = {'Q': 'format',
         'q': 'stand-alone'}[char]
        return get_quarter_names(width, context, self.locale)[quarter]

    def format_month(self, char, num):
        if num <= 2:
            return '%%0%dd' % num % self.value.month
        width = {3: 'abbreviated',
         4: 'wide',
         5: 'narrow'}[num]
        context = {'M': 'format',
         'L': 'stand-alone'}[char]
        return get_month_names(width, context, self.locale)[self.value.month]

    def format_week(self, char, num):
        if char.islower():
            day_of_year = self.get_day_of_year()
            week = self.get_week_number(day_of_year)
            if week == 0:
                date = self.value - timedelta(days=day_of_year)
                week = self.get_week_number(self.get_day_of_year(date), date.weekday())
            return self.format(week, num)
        else:
            week = self.get_week_number(self.value.day)
            if week == 0:
                date = self.value - timedelta(days=self.value.day)
                week = self.get_week_number(date.day, date.weekday())
            return '%d' % week

    def format_weekday(self, char, num):
        if num < 3:
            if char.islower():
                value = 7 - self.locale.first_week_day + self.value.weekday()
                return self.format(value % 7 + 1, num)
            num = 3
        weekday = self.value.weekday()
        width = {3: 'abbreviated',
         4: 'wide',
         5: 'narrow'}[num]
        context = {3: 'format',
         4: 'format',
         5: 'stand-alone'}[num]
        return get_day_names(width, context, self.locale)[weekday]

    def format_day_of_year(self, num):
        return self.format(self.get_day_of_year(), num)

    def format_day_of_week_in_month(self):
        return '%d' % ((self.value.day - 1) / 7 + 1)

    def format_period(self, char):
        period = {0: 'am',
         1: 'pm'}[int(self.value.hour >= 12)]
        return get_period_names(locale=self.locale)[period]

    def format_frac_seconds(self, num):
        value = str(self.value.microsecond)
        return self.format(round(float('.%s' % value), num) * 10 ** num, num)

    def format_milliseconds_in_day(self, num):
        msecs = self.value.microsecond // 1000 + self.value.second * 1000 + self.value.minute * 60000 + self.value.hour * 3600000
        return self.format(msecs, num)

    def format_timezone(self, char, num):
        width = {3: 'short',
         4: 'long'}[max(3, num)]
        if char == 'z':
            return get_timezone_name(self.value, width, locale=self.locale)
        if char == 'Z':
            return get_timezone_gmt(self.value, width, locale=self.locale)
        if char == 'v':
            return get_timezone_name(self.value.tzinfo, width, locale=self.locale)
        if char == 'V':
            if num == 1:
                return get_timezone_name(self.value.tzinfo, width, uncommon=True, locale=self.locale)
            return get_timezone_location(self.value.tzinfo, locale=self.locale)

    def format(self, value, length):
        return '%%0%dd' % length % value

    def get_day_of_year(self, date = None):
        if date is None:
            date = self.value
        return (date - date_(date.year, 1, 1)).days + 1

    def get_week_number(self, day_of_period, day_of_week = None):
        if day_of_week is None:
            day_of_week = self.value.weekday()
        first_day = (day_of_week - self.locale.first_week_day - day_of_period + 1) % 7
        if first_day < 0:
            first_day += 7
        week_number = (day_of_period + first_day - 1) / 7
        if 7 - first_day >= self.locale.min_week_days:
            week_number += 1
        return week_number


PATTERN_CHARS = {'G': [1,
       2,
       3,
       4,
       5],
 'y': None,
 'Y': None,
 'u': None,
 'Q': [1,
       2,
       3,
       4],
 'q': [1,
       2,
       3,
       4],
 'M': [1,
       2,
       3,
       4,
       5],
 'L': [1,
       2,
       3,
       4,
       5],
 'w': [1, 2],
 'W': [1],
 'd': [1, 2],
 'D': [1, 2, 3],
 'F': [1],
 'g': None,
 'E': [1,
       2,
       3,
       4,
       5],
 'e': [1,
       2,
       3,
       4,
       5],
 'c': [1,
       3,
       4,
       5],
 'a': [1],
 'h': [1, 2],
 'H': [1, 2],
 'K': [1, 2],
 'k': [1, 2],
 'm': [1, 2],
 's': [1, 2],
 'S': None,
 'A': None,
 'z': [1,
       2,
       3,
       4],
 'Z': [1,
       2,
       3,
       4],
 'v': [1, 4],
 'V': [1, 4]}

def parse_pattern(pattern):
    if type(pattern) is DateTimePattern:
        return pattern
    result = []
    quotebuf = None
    charbuf = []
    fieldchar = ['']
    fieldnum = [0]

    def append_chars():
        result.append(''.join(charbuf).replace('%', '%%'))
        del charbuf[:]

    def append_field():
        limit = PATTERN_CHARS[fieldchar[0]]
        if limit and fieldnum[0] not in limit:
            raise ValueError('Invalid length for field: %r' % (fieldchar[0] * fieldnum[0]))
        result.append('%%(%s)s' % (fieldchar[0] * fieldnum[0]))
        fieldchar[0] = ''
        fieldnum[0] = 0

    for idx, char in enumerate(pattern.replace("''", '\x00')):
        if quotebuf is None:
            if char == "'":
                if fieldchar[0]:
                    append_field()
                elif charbuf:
                    append_chars()
                quotebuf = []
            elif char in PATTERN_CHARS:
                if charbuf:
                    append_chars()
                if char == fieldchar[0]:
                    fieldnum[0] += 1
                else:
                    if fieldchar[0]:
                        append_field()
                    fieldchar[0] = char
                    fieldnum[0] = 1
            else:
                if fieldchar[0]:
                    append_field()
                charbuf.append(char)
        elif quotebuf is not None:
            if char == "'":
                charbuf.extend(quotebuf)
                quotebuf = None
            else:
                quotebuf.append(char)

    if fieldchar[0]:
        append_field()
    elif charbuf:
        append_chars()
    return DateTimePattern(pattern, u''.join(result).replace('\x00', "'"))
