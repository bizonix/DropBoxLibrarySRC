#Embedded file name: dropbox/language_data.py
LOCALE_SPLITCHAR = '_'
DEFAULT_CODE = u'en_US'
SYSTEM_LANG_CODE = u''
NULL_CODES = [DEFAULT_CODE, u'en', SYSTEM_LANG_CODE]
from .languages import LANGUAGE_NAME_DICT
_LANGUAGE_NAME_DICT = LANGUAGE_NAME_DICT.copy()
_LANGUAGE_NAME_DICT.update({u'en_FUNKY': (u'\xde\u093d\u1e1d\uff35\u1e13\uff2f\uff34\u044f\u1eab\u014b\u093d\u026d\u1eab\uff34\u1e1d', u'Pseudotranslate'),
 u'igpay_atinlay': (u'Igpay Atinlay', u'Pig Latin')})
DEVELOPMENT_LANGUAGE_CODES = [u'en_FUNKY', u'igpay_atinlay']
_NAME_TO_CODE = dict([ (x[1][0], x[0]) for x in _LANGUAGE_NAME_DICT.items() ])
get_native_name_for_code = lambda x: _LANGUAGE_NAME_DICT[x][0]
get_english_name_for_code = lambda x: _LANGUAGE_NAME_DICT[x][1]
get_code_for_native_name = lambda x: _NAME_TO_CODE[x]
ORDERED_LANGUAGE_CODES_DEV = _LANGUAGE_NAME_DICT.keys()
ORDERED_LANGUAGE_CODES_DEV.sort(key=get_native_name_for_code)
ORDERED_LANGUAGE_CODES = list(ORDERED_LANGUAGE_CODES_DEV)
for code in DEVELOPMENT_LANGUAGE_CODES:
    try:
        ORDERED_LANGUAGE_CODES.remove(code)
    except ValueError:
        pass

POSSIBLE_CODES_FOR_LANG = {}
for code in DEVELOPMENT_LANGUAGE_CODES:
    POSSIBLE_CODES_FOR_LANG[code] = [code]

for code in ORDERED_LANGUAGE_CODES:
    underlings = [code]
    if LOCALE_SPLITCHAR in code:
        underlings.append(code.split(LOCALE_SPLITCHAR)[0])
    for k in underlings:
        if k not in POSSIBLE_CODES_FOR_LANG:
            POSSIBLE_CODES_FOR_LANG[k] = []
        POSSIBLE_CODES_FOR_LANG[k].append(code)

del code
del k
del underlings
_MAC_ENGLISH_NAME_TO_LANG = {'Chinese': 'zh',
 'Dutch': 'nl',
 'English': 'en',
 'French': 'fr',
 'German': 'de',
 'Italian': 'it',
 'Japanese': 'ja',
 'Korean': 'ko',
 'Portuguese': 'pt',
 'Spanish': 'es',
 'Swedish': 'sv'}
get_lang_from_mac_english_name = lambda x: _MAC_ENGLISH_NAME_TO_LANG.get(x, x)
_LANG_VARIANT_MAPPINGS = {'zh_Hans': 'zh_CN',
 'zh_Hant': 'zh_TW',
 'zh_HK': 'zh_TW',
 'zh_MO': 'zh_TW',
 'zh_SG': 'zh_CN',
 'zh_MY': 'zh_CN'}
get_lang_mapped_to_variant = lambda x: _LANG_VARIANT_MAPPINGS.get(x, x)
CAMERA_UPLOAD_FOLDERS_LANGS = [['en_US'],
 ['de', 'fr'],
 ['es', 'ja', 'ko'],
 ['es_ES', 'it'],
 ['pt_BR'],
 [u'ru',
  u'zh_CN',
  u'zh_TW',
  u'ms',
  u'id',
  u'pl']]
