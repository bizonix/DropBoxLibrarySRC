#Embedded file name: arch/win32/photouploader/autoplay_defaults.py
import os
from _winreg import HKEY_CURRENT_USER as HKCU, HKEY_LOCAL_MACHINE as HKLM
from build_number import BUILD_KEY
from dropbox.functions import handle_exceptions
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.win32.version import WINDOWS_VERSION
from pynt.constants import KEY_ALL_ACCESS, KEY_READ, KEY_WOW64_64KEY
from pynt.helpers.registry import create_registry_key, delete_registry_tree, registry_key, safe_read_registry_value, set_registry_value, enum_registry_values, enum_registry_subkeys, REG_SZ
from .constants import AUTOPLAY_KEY, AUTOPLAY_DEFAULTS_SUPPORTED, DROPBOX_AUTOPLAY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME, USE_WIA, VOLUME_EVENT_DEFAULTS, VOLUME_EVENTS
AUTOPLAY_DEFAULTS_KEY = os.path.join(AUTOPLAY_KEY, u'UserChosenExecuteHandlers')
AUTOPLAY_KNOWNDEVICES_KEY = os.path.join(AUTOPLAY_KEY, u'KnownDevices')
IMAGING_DEVICE_CLSGUID = '{6bdd1fc6-810f-11d0-bec7-08002be2092f}'
MASS_STORAGE_CLSGUID = '{10497b1b-ba51-44e5-8318-a65c837b6661}'
GUID_DEVINTERFACE_WPD1 = '{6ac27878-a6fa-4155-ba85-f98f491d4f33}'
GUID_DEVINTERFACE_WPD2 = '{f33fdc04-d1ac-4e8e-9a30-19bbd4b108ae}'
IMAGING_INTERFACES = (IMAGING_DEVICE_CLSGUID,
 MASS_STORAGE_CLSGUID,
 GUID_DEVINTERFACE_WPD1,
 GUID_DEVINTERFACE_WPD2)
WIA_DEVICES_KEY = u'SYSTEM\\CurrentControlSet\\Control\\Class\\' + IMAGING_DEVICE_CLSGUID
WIA_HANDLERS_KEY = u'SYSTEM\\CurrentControlSet\\Control\\StillImage\\Events\\Connected'
DROPBOX_AUTOPLAY_HANDLERS = (DROPBOX_AUTOPLAY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME)

def get_wia_handler(name = BUILD_KEY):
    with registry_key(HKLM, WIA_HANDLERS_KEY, permission=KEY_READ | KEY_WOW64_64KEY) as handlers_key:
        if not handlers_key:
            raise Exception("Handlers key doesn't exist!")
        handler = None
        for subkey_name in enum_registry_subkeys(handlers_key):
            subkey_path = os.path.join(WIA_HANDLERS_KEY, subkey_name)
            with registry_key(HKLM, subkey_path, permission=KEY_READ | KEY_WOW64_64KEY) as handler_key:
                if not handler_key:
                    continue
                handler_name = safe_read_registry_value(handler_key, u'Name')
                if handler_name == name:
                    values = {}
                    for value_name in enum_registry_values(handler_key):
                        if value_name:
                            values[value_name] = safe_read_registry_value(handler_key, value_name)

                    return (subkey_name, values)

        raise Exception('Could not find handler in connected list!')


def get_wia_device_key(device_id):
    with registry_key(HKLM, WIA_DEVICES_KEY, permission=KEY_READ | KEY_WOW64_64KEY) as wia_key:
        if not wia_key:
            raise Exception('Could not open WIA devices key.')
        for subkey_name in enum_registry_subkeys(wia_key):
            subkey_path = os.path.join(WIA_DEVICES_KEY, subkey_name)
            with registry_key(HKLM, subkey_path, permission=KEY_READ | KEY_WOW64_64KEY) as dev_key:
                if not dev_key:
                    continue
                key_id = safe_read_registry_value(dev_key, u'DeviceID')
                if key_id == device_id:
                    return subkey_name

    raise KeyError("Could not find WIA key for device '%s'." % device_id)


def set_wia_default(device_id, name = BUILD_KEY):
    handler, properties = get_wia_handler(name)
    key = get_wia_device_key(device_id)
    handlers_path = os.path.join(WIA_DEVICES_KEY, key, u'Events', u'Connected')
    with registry_key(HKLM, handlers_path, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as handlers_key:
        if not handlers_key:
            raise Exception("Handlers key doesn't exist!")
        handler_path = os.path.join(handlers_path, handler)
        with create_registry_key(HKLM, handler_path, permission=KEY_ALL_ACCESS | KEY_WOW64_64KEY) as handler_key, _:
            if not handler_key:
                raise Exception('Could not create/access the handler subkey')
            for name, value in properties.items():
                if not set_registry_value(handler_key, name, REG_SZ, value):
                    raise Exception('Failed to set property %s=%s' % (name, value))

        if not set_registry_value(handlers_key, u'DefaultHandler', REG_SZ, handler):
            raise Exception('Failed to set DefaultHandler value!')


def change_autoplay_default(event, handler):
    chosen_handlers_key = os.path.join(AUTOPLAY_DEFAULTS_KEY, event)
    with create_registry_key(HKCU, chosen_handlers_key) as key, _:
        set_registry_value(key, u'', REG_SZ, handler)


def get_device_name(device_id):
    name = device_id
    with registry_key(HKCU, os.path.join(AUTOPLAY_KNOWNDEVICES_KEY, device_id)) as dev:
        if dev:
            name = safe_read_registry_value(dev, u'Label')
    return name


def get_wia_device_name(key):
    name = key
    key = os.path.join(WIA_DEVICES_KEY, key)
    with registry_key(HKLM, key, permission=KEY_READ | KEY_WOW64_64KEY) as dev_key:
        name = safe_read_registry_value(dev_key, u'DriverDesc') or safe_read_registry_value(dev_key, u'FriendlyName') or name
    return name


def get_wia_default(key):
    key = os.path.join(WIA_DEVICES_KEY, key, u'Events', u'Connected')
    with registry_key(HKLM, key, permission=KEY_READ | KEY_WOW64_64KEY) as dev_key:
        if not dev_key:
            return
        value = safe_read_registry_value(dev_key, u'DefaultHandler')
    if not value:
        return
    value_name = os.path.join(key, value)
    with registry_key(HKLM, value_name, permission=KEY_READ | KEY_WOW64_64KEY) as action:
        if not action:
            TRACE('!! GUID but no value?')
            return value
        return safe_read_registry_value(action, u'Name')


def get_autoplay_default(event_name, device_name = None):
    with registry_key(HKCU, AUTOPLAY_DEFAULTS_KEY) as defaults_key:
        if defaults_key:
            with registry_key(HKCU, os.path.join(AUTOPLAY_DEFAULTS_KEY, event_name)) as subkey:
                if subkey:
                    value = safe_read_registry_value(subkey, None)
                    if value:
                        if device_name is None:
                            device_name = get_device_name(event_name)
                        return (device_name, value)


def get_autoplay_defaults():
    ret = {}
    try:
        with registry_key(HKCU, AUTOPLAY_DEFAULTS_KEY) as defaults_key:
            if defaults_key:
                for subkey in enum_registry_values(defaults_key):
                    if subkey:
                        name = subkey.split(u'+')[-1]
                        value = safe_read_registry_value(defaults_key, subkey)
                        if value:
                            ret[subkey] = (name, value)

                for subkey_name in enum_registry_subkeys(defaults_key):
                    if subkey_name:
                        with registry_key(HKCU, os.path.join(AUTOPLAY_DEFAULTS_KEY, subkey_name)) as subkey:
                            if subkey:
                                value = safe_read_registry_value(subkey, None)
                                if value:
                                    ret[subkey_name] = (get_device_name(subkey_name), value)

        if USE_WIA:
            with registry_key(HKLM, WIA_DEVICES_KEY, permission=KEY_READ | KEY_WOW64_64KEY) as wia_key:
                if wia_key:
                    for subkey_name in enum_registry_subkeys(wia_key):
                        default = get_wia_default(subkey_name)
                        if default:
                            ret[subkey_name] = (get_wia_device_name(subkey_name), default)

    except Exception:
        unhandled_exc_handler()

    return ret


def is_imaging_device(device_key):
    with registry_key(device_key, u'KnownInterfaces') as interfaces_key:
        if interfaces_key:
            for interface in enum_registry_values(interfaces_key):
                clsguid = interface.lower().split('#')[-1]
                if clsguid in IMAGING_INTERFACES:
                    return True

    return False


@handle_exceptions
def set_dropbox_default_autoplay():
    if not AUTOPLAY_DEFAULTS_SUPPORTED:
        TRACE('Not setting defaults for Windows version %r', WINDOWS_VERSION)
        return
    events = list(VOLUME_EVENT_DEFAULTS)
    for device_id, device_name in known_imaging_devices():
        TRACE('Setting Dropbox as the default handler for %r', device_name)
        events.append(device_id)

    set_default_by_event(events)
    return events


def known_imaging_devices():
    with registry_key(HKCU, AUTOPLAY_KNOWNDEVICES_KEY) as known_devices:
        if known_devices:
            for device in enum_registry_subkeys(known_devices):
                if not device:
                    report_bad_assumption('Subkey name of %s is empty' % AUTOPLAY_KNOWNDEVICES_KEY)
                    continue
                with registry_key(HKCU, os.path.join(AUTOPLAY_KNOWNDEVICES_KEY, device)) as device_key:
                    if not device_key or not is_imaging_device(device_key):
                        continue
                    dev_name = safe_read_registry_value(device_key, u'Label')
                    if dev_name:
                        yield (device, dev_name)


def set_default_by_event(events):
    autoplay_handler = DROPBOX_AUTOPLAY_HANDLER_NAME
    for event in events:
        try:
            keyname = os.path.join(AUTOPLAY_DEFAULTS_KEY, event)
            with create_registry_key(HKCU, keyname, permission=KEY_ALL_ACCESS) as event_key, _:
                if not event_key:
                    raise Exception('Registry error: failed to create key %s', keyname)
                if not set_registry_value(event_key, None, REG_SZ, autoplay_handler):
                    raise Exception('Registry error: could not set default property of %s to %s' % (keyname, autoplay_handler))
                TRACE('Set default autoplay handler of %s to %s', event, autoplay_handler)
        except Exception:
            unhandled_exc_handler()


@handle_exceptions
def set_old_default_autoplay(old_handlers, device = None):
    if not AUTOPLAY_DEFAULTS_SUPPORTED:
        report_bad_assumption('set_old_default_autoplay called for Windows %r', WINDOWS_VERSION)
        return
    events = []
    if device:
        TRACE('Resetting autoplay default for single device: %r', device.id)
        event = device.formatted_device_id()
        events.append(event)
    else:
        try:
            with registry_key(HKCU, AUTOPLAY_DEFAULTS_KEY, permission=KEY_ALL_ACCESS) as defaults_key:
                if defaults_key:
                    for event in enum_registry_subkeys(defaults_key):
                        events.append(event)

        except Exception:
            unhandled_exc_handler()

    if events:
        reset_devices(events, old_handlers)


def reset_devices(events, old_handlers):
    for event in events:
        try:
            keyname = os.path.join(AUTOPLAY_DEFAULTS_KEY, event)
            with registry_key(HKCU, keyname, permission=KEY_ALL_ACCESS) as event_key:
                if not event_key:
                    TRACE('!! Registry error: failed to open key %s\\%s', HKCU, keyname)
                    continue
                cur_handler = safe_read_registry_value(event_key, None)
                if cur_handler in DROPBOX_AUTOPLAY_HANDLERS:
                    try:
                        event_name, handler = old_handlers[event]
                    except KeyError:
                        TRACE('No previous default handler for %r.  Deleting the UserChosenDefault subkey', event)
                        delete_registry_tree(HKCU, keyname)
                    else:
                        if handler in DROPBOX_AUTOPLAY_HANDLERS:
                            TRACE("Dropbox was previous handler for %r, but user doesn't want it. Reverting to ask every time.", event)
                            delete_registry_tree(HKCU, keyname)
                        else:
                            TRACE('%s was previous default handler for %s.  Putting it back', handler, event_name)
                            if not set_registry_value(event_key, None, REG_SZ, handler):
                                raise Exception('Registry error: could not set default property of %s=%s' % (keyname, handler))
                else:
                    TRACE('Not touching %r, it belongs to %r', event, cur_handler)
        except Exception:
            unhandled_exc_handler()


def any_volume_defaults_are_dropbox():
    for event in VOLUME_EVENTS:
        try:
            keyname = os.path.join(AUTOPLAY_DEFAULTS_KEY, event)
            with registry_key(HKCU, keyname, permission=KEY_READ | KEY_WOW64_64KEY) as event_key:
                if not event_key:
                    continue
                cur_handler = safe_read_registry_value(event_key, None)
                if cur_handler in DROPBOX_AUTOPLAY_HANDLERS:
                    TRACE('any_volume_defaults_are_dropbox: Handler for %s is %r. Returning True!', event, cur_handler)
                    return True
        except Exception:
            unhandled_exc_handler()

    with registry_key(HKCU, AUTOPLAY_DEFAULTS_KEY) as defaults_key:
        if not defaults_key:
            return False
        for subkey in enum_registry_values(defaults_key):
            if not subkey:
                continue
            name = subkey.split(u'+')[-1]
            if name in VOLUME_EVENTS:
                cur_handler = safe_read_registry_value(defaults_key, subkey)
                if cur_handler in DROPBOX_AUTOPLAY_HANDLERS:
                    TRACE('any_volume_defaults_are_dropbox: Handler for %s is %r. Returning True!', subkey, cur_handler)
                    return True

    return False


def check_for_new_devices(previously_set_devices):
    if not AUTOPLAY_DEFAULTS_SUPPORTED:
        return (None, None)
    devices = []
    old_defaults = {}
    for device_id, device_name in known_imaging_devices():
        if device_id in previously_set_devices:
            continue
        TRACE('PHOTOUPLOADER: Found new camera %r id %r', device_name, device_id)
        devices.append(device_id)
        current_default = get_autoplay_default(device_id, device_name)
        if current_default:
            old_defaults[device_id] = current_default

    set_default_by_event(devices)
    return (old_defaults, devices)


def any_defaults_are_dropbox():
    defaults = get_autoplay_defaults()
    defaults_they_cant_change = set(VOLUME_EVENTS).difference(set(VOLUME_EVENT_DEFAULTS))
    for event, (event_name, default_handler) in defaults.iteritems():
        if default_handler in DROPBOX_AUTOPLAY_HANDLERS and event not in defaults_they_cant_change:
            return True

    return False
