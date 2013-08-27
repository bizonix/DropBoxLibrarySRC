#Embedded file name: dropbox/features.py
import collections
import os
import re
import arch
from dropbox.trace import TRACE, report_bad_assumption
EXPERIMENTAL_FEATURES_ENABLED = True
IN_PROGRESS = 'in-progress'
EXPERIMENTAL = 'experimental'
FINISHED = 'finished'
FEATURE_MAP = {'menu-move-to-dropbox': FINISHED,
 'iphoto-importer': FINISHED,
 'screenshots': FINISHED,
 'ascii-art-panda': IN_PROGRESS,
 'cffi-printf-on-startup': EXPERIMENTAL,
 'fileids': IN_PROGRESS,
 'multiaccount': EXPERIMENTAL,
 'setupwizkit': EXPERIMENTAL,
 'win-pictures-importer': EXPERIMENTAL,
 'win-documents-importer': IN_PROGRESS,
 'mavericks-finder-integration': EXPERIMENTAL}
FEATURE_PLATFORM_BLACKLIST = collections.defaultdict(set)
FEATURE_PLATFORM_BLACKLIST['multiaccount'] = {'linux'}
FEATURE_PLATFORM_BLACKLIST['setupwizkit'] = {'linux'}

def feature_enabled(feature_name):
    try:
        state = FEATURE_MAP[feature_name]
    except KeyError:
        report_bad_assumption('Requesting a feature not in map (%s)', feature_name)
        state = IN_PROGRESS
    else:
        if state not in VALID_STATES:
            report_bad_assumption('Feature %s has invalid state %r.', feature_name, state)
            state = IN_PROGRESS

    try:
        return _FEATURE_OVERRIDE_MAP[feature_name]
    except KeyError:
        if arch.constants.platform in FEATURE_PLATFORM_BLACKLIST[feature_name]:
            return False
        if state == FINISHED:
            return True
        if state == EXPERIMENTAL and EXPERIMENTAL_FEATURES_ENABLED:
            return True
        return False


def add_feature_overrides(args = ()):
    _add_feature_overrides_from_environment()
    args = _add_feature_overrides_from_args(args)
    TRACE('Running with these features enabled: %s', ','.join((feature_name for feature_name in FEATURE_MAP if feature_enabled(feature_name))) or 'None')
    return args


def _add_feature_overrides_from_environment():
    dbfeatures = os.getenv('DBFEATURES') or ''
    features = dbfeatures.split(' ')
    _add_feature_overrides_from_args(features)


def _add_feature_overrides_from_args(args):
    leftover_args = []
    for arg in args:
        m = re.match('--(enable|disable)-(.*)', arg)
        if m:
            endis, feature = m.groups()
            if EXPERIMENTAL_FEATURES_ENABLED:
                _FEATURE_OVERRIDE_MAP[feature] = endis == 'enable'
        else:
            leftover_args.append(arg)

    return leftover_args


def current_feature_args():
    return [ '--%s-%s' % ('enable' if enabled else 'disable', feature_name) for feature_name, enabled in _FEATURE_OVERRIDE_MAP.iteritems() ]


VALID_STATES = (IN_PROGRESS, EXPERIMENTAL, FINISHED)
_FEATURE_OVERRIDE_MAP = {}
