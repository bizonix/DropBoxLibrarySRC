#Embedded file name: babel/numbers.py
import math
import re
try:
    from decimal import Decimal
    have_decimal = True
except ImportError:
    have_decimal = False

from babel.core import default_locale, Locale
from babel.util import rsplit
__all__ = ['format_number',
 'format_decimal',
 'format_currency',
 'format_percent',
 'format_scientific',
 'parse_number',
 'parse_decimal',
 'NumberFormatError']
__docformat__ = 'restructuredtext en'
LC_NUMERIC = default_locale('LC_NUMERIC')

def get_currency_name(currency, locale = LC_NUMERIC):
    return Locale.parse(locale).currencies.get(currency, currency)


def get_currency_symbol(currency, locale = LC_NUMERIC):
    return Locale.parse(locale).currency_symbols.get(currency, currency)


def get_decimal_symbol(locale = LC_NUMERIC):
    return Locale.parse(locale).number_symbols.get('decimal', u'.')


def get_plus_sign_symbol(locale = LC_NUMERIC):
    return Locale.parse(locale).number_symbols.get('plusSign', u'+')


def get_minus_sign_symbol(locale = LC_NUMERIC):
    return Locale.parse(locale).number_symbols.get('minusSign', u'-')


def get_exponential_symbol(locale = LC_NUMERIC):
    return Locale.parse(locale).number_symbols.get('exponential', u'E')


def get_group_symbol(locale = LC_NUMERIC):
    return Locale.parse(locale).number_symbols.get('group', u',')


def format_number(number, locale = LC_NUMERIC):
    return format_decimal(number, locale=locale)


def format_decimal(number, format = None, locale = LC_NUMERIC):
    locale = Locale.parse(locale)
    if not format:
        format = locale.decimal_formats.get(format)
    pattern = parse_pattern(format)
    return pattern.apply(number, locale)


def format_currency(number, currency, format = None, locale = LC_NUMERIC):
    locale = Locale.parse(locale)
    if not format:
        format = locale.currency_formats.get(format)
    pattern = parse_pattern(format)
    return pattern.apply(number, locale, currency=currency)


def format_percent(number, format = None, locale = LC_NUMERIC):
    locale = Locale.parse(locale)
    if not format:
        format = locale.percent_formats.get(format)
    pattern = parse_pattern(format)
    return pattern.apply(number, locale)


def format_scientific(number, format = None, locale = LC_NUMERIC):
    locale = Locale.parse(locale)
    if not format:
        format = locale.scientific_formats.get(format)
    pattern = parse_pattern(format)
    return pattern.apply(number, locale)


class NumberFormatError(ValueError):
    pass


def parse_number(string, locale = LC_NUMERIC):
    try:
        return long(string.replace(get_group_symbol(locale), ''))
    except ValueError:
        raise NumberFormatError('%r is not a valid number' % string)


def parse_decimal(string, locale = LC_NUMERIC):
    locale = Locale.parse(locale)
    try:
        return float(string.replace(get_group_symbol(locale), '').replace(get_decimal_symbol(locale), '.'))
    except ValueError:
        raise NumberFormatError('%r is not a valid decimal number' % string)


PREFIX_END = '[^0-9@#.,]'
NUMBER_TOKEN = '[0-9@#.\\-,E+]'
PREFIX_PATTERN = "(?P<prefix>(?:'[^']*'|%s)*)" % PREFIX_END
NUMBER_PATTERN = '(?P<number>%s+)' % NUMBER_TOKEN
SUFFIX_PATTERN = '(?P<suffix>.*)'
number_re = re.compile('%s%s%s' % (PREFIX_PATTERN, NUMBER_PATTERN, SUFFIX_PATTERN))

def split_number(value):
    if have_decimal and isinstance(value, Decimal):
        text = str(value)
    else:
        text = ('%.9f' % value).rstrip('0')
    if '.' in text:
        a, b = text.split('.', 1)
        if b == '0':
            b = ''
    else:
        a, b = text, ''
    return (a, b)


def bankersround(value, ndigits = 0):
    sign = int(value < 0) and -1 or 1
    value = abs(value)
    a, b = split_number(value)
    digits = a + b
    add = 0
    i = len(a) + ndigits
    if i < 0 or i >= len(digits):
        pass
    elif digits[i] > '5':
        add = 1
    elif digits[i] == '5' and digits[i - 1] in '13579':
        add = 1
    scale = 10 ** ndigits
    if have_decimal and isinstance(value, Decimal):
        return Decimal(int(value * scale + add)) / scale * sign
    else:
        return float(int(value * scale + add)) / scale * sign


def parse_pattern(pattern):
    if isinstance(pattern, NumberPattern):
        return pattern
    if ';' in pattern:
        pattern, neg_pattern = pattern.split(';', 1)
        pos_prefix, number, pos_suffix = number_re.search(pattern).groups()
        neg_prefix, _, neg_suffix = number_re.search(neg_pattern).groups()
    else:
        pos_prefix, number, pos_suffix = number_re.search(pattern).groups()
        neg_prefix = '-' + pos_prefix
        neg_suffix = pos_suffix
    if 'E' in number:
        number, exp = number.split('E', 1)
    else:
        exp = None
    if '@' in number:
        if '.' in number and '0' in number:
            raise ValueError('Significant digit patterns can not contain "@" or "0"')
    if '.' in number:
        integer, fraction = rsplit(number, '.', 1)
    else:
        integer = number
        fraction = ''
    min_frac = max_frac = 0

    def parse_precision(p):
        min = max = 0
        for c in p:
            if c in '@0':
                min += 1
                max += 1
            elif c == '#':
                max += 1
            elif c == ',':
                continue
            else:
                break

        return (min, max)

    def parse_grouping(p):
        width = len(p)
        g1 = p.rfind(',')
        if g1 == -1:
            return (1000, 1000)
        g1 = width - g1 - 1
        g2 = p[:-g1 - 1].rfind(',')
        if g2 == -1:
            return (g1, g1)
        g2 = width - g1 - g2 - 2
        return (g1, g2)

    int_prec = parse_precision(integer)
    frac_prec = parse_precision(fraction)
    if exp:
        frac_prec = parse_precision(integer + fraction)
        exp_plus = exp.startswith('+')
        exp = exp.lstrip('+')
        exp_prec = parse_precision(exp)
    else:
        exp_plus = None
        exp_prec = None
    grouping = parse_grouping(integer)
    return NumberPattern(pattern, (pos_prefix, neg_prefix), (pos_suffix, neg_suffix), grouping, int_prec, frac_prec, exp_prec, exp_plus)


class NumberPattern(object):

    def __init__(self, pattern, prefix, suffix, grouping, int_prec, frac_prec, exp_prec, exp_plus):
        self.pattern = pattern
        self.prefix = prefix
        self.suffix = suffix
        self.grouping = grouping
        self.int_prec = int_prec
        self.frac_prec = frac_prec
        self.exp_prec = exp_prec
        self.exp_plus = exp_plus
        if '%' in ''.join(self.prefix + self.suffix):
            self.scale = 100
        elif u'\u2030' in ''.join(self.prefix + self.suffix):
            self.scale = 1000
        else:
            self.scale = 1

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.pattern)

    def apply(self, value, locale, currency = None):
        value *= self.scale
        is_negative = int(value < 0)
        if self.exp_prec:
            value = abs(value)
            if value:
                exp = int(math.floor(math.log(value, 10)))
            else:
                exp = 0
            if self.int_prec[0] == self.int_prec[1]:
                exp -= self.int_prec[0] - 1
            elif self.int_prec[1]:
                exp = int(exp) / self.int_prec[1] * self.int_prec[1]
            if not have_decimal or not isinstance(value, Decimal):
                value = float(value)
            if exp < 0:
                value = value * 10 ** (-exp)
            else:
                value = value / 10 ** exp
            exp_sign = ''
            if exp < 0:
                exp_sign = get_minus_sign_symbol(locale)
            elif self.exp_plus:
                exp_sign = get_plus_sign_symbol(locale)
            exp = abs(exp)
            number = u'%s%s%s%s' % (self._format_sigdig(value, self.frac_prec[0], self.frac_prec[1]),
             get_exponential_symbol(locale),
             exp_sign,
             self._format_int(str(exp), self.exp_prec[0], self.exp_prec[1], locale))
        elif '@' in self.pattern:
            text = self._format_sigdig(abs(value), self.int_prec[0], self.int_prec[1])
            if '.' in text:
                a, b = text.split('.')
                a = self._format_int(a, 0, 1000, locale)
                if b:
                    b = get_decimal_symbol(locale) + b
                number = a + b
            else:
                number = self._format_int(text, 0, 1000, locale)
        else:
            a, b = split_number(bankersround(abs(value), self.frac_prec[1]))
            b = b or '0'
            a = self._format_int(a, self.int_prec[0], self.int_prec[1], locale)
            b = self._format_frac(b, locale)
            number = a + b
        retval = u'%s%s%s' % (self.prefix[is_negative], number, self.suffix[is_negative])
        if u'\xa4' in retval:
            retval = retval.replace(u'\xa4\xa4', currency.upper())
            retval = retval.replace(u'\xa4', get_currency_symbol(currency, locale))
        return retval

    def _format_sigdig(self, value, min, max):
        a, b = split_number(value)
        ndecimals = len(a)
        if a == '0' and b != '':
            ndecimals = 0
            while b.startswith('0'):
                b = b[1:]
                ndecimals -= 1

        a, b = split_number(bankersround(value, max - ndecimals))
        digits = len((a + b).lstrip('0'))
        if not digits:
            digits = 1
        if len(a) >= max and a != '0':
            return a
        if digits < min:
            b += '0' * (min - digits)
        if b:
            return '%s.%s' % (a, b)
        return a

    def _format_int(self, value, min, max, locale):
        width = len(value)
        if width < min:
            value = '0' * (min - width) + value
        gsize = self.grouping[0]
        ret = ''
        symbol = get_group_symbol(locale)
        while len(value) > gsize:
            ret = symbol + value[-gsize:] + ret
            value = value[:-gsize]
            gsize = self.grouping[1]

        return value + ret

    def _format_frac(self, value, locale):
        min, max = self.frac_prec
        if len(value) < min:
            value += '0' * (min - len(value))
        if max == 0 or min == 0 and int(value) == 0:
            return ''
        width = len(value)
        while len(value) > min and value[-1] == '0':
            value = value[:-1]

        return get_decimal_symbol(locale) + value
