#Embedded file name: pymac/helpers/security.py
import socket
from ctypes import byref, c_char_p, c_uint32, string_at
from ..constants import errSecItemNotFound, errSecParam, kSecAccountItemAttr, kSecCommentItemAttr, kSecGenericPasswordItemClass, kSecLabelItemAttr, kSecServiceItemAttr, CSSM_ACL_AUTHORIZATION_CHANGE_ACL, CSSM_ACL_AUTHORIZATION_DECRYPT, CSSM_ACL_AUTHORIZATION_DERIVE, CSSM_ACL_AUTHORIZATION_EXPORT_CLEAR, CSSM_ACL_AUTHORIZATION_EXPORT_WRAPPED, CSSM_ACL_AUTHORIZATION_MAC, CSSM_ACL_AUTHORIZATION_SIGN
from ..dlls import Security, Core, libc
from ..types import SecKeychainAttributeList, SecKeychainItemRef, SecAccessRef, SecTrustedApplicationRef, CFArrayRef, CFStringRef, CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR, CFDataRef, CSSM_ACL_AUTHORIZATION_TAG
from .core import CFArray, CFRelease, OSStatusError, python_to_property, releasing

def _gethostname():
    try:
        return socket.gethostname().split('.')[0]
    except Exception:
        return 'localhost'


def _yield_all_trusted_app_data(aclref):
    ps = CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR()
    with releasing(CFArrayRef()) as trustedapplist:
        with releasing(CFStringRef()) as sr:
            Security.SecACLCopySimpleContents(aclref, byref(trustedapplist), byref(sr), byref(ps))
            if not trustedapplist:
                return
            for app in CFArray(trustedapplist).refs():
                with releasing(CFDataRef()) as dr2:
                    Security.SecTrustedApplicationCopyData(app, byref(dr2))
                    yield string_at(Core.CFDataGetBytePtr(dr2), Core.CFDataGetLength(dr2))


def _add_app_to_aclref(aclref, app, replace = False):
    ps = CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR()
    with releasing(CFArrayRef()) as trustedapplist:
        with releasing(CFStringRef()) as sr:
            with releasing(CFDataRef()) as dr:
                Security.SecTrustedApplicationCopyData(app, byref(dr))
                Security.SecACLCopySimpleContents(aclref, byref(trustedapplist), byref(sr), byref(ps))
                if not trustedapplist:
                    return
                to_replace = []
                if replace:
                    for i, val2 in enumerate(CFArray(trustedapplist).refs()):
                        with releasing(CFDataRef()) as dr2:
                            Security.SecTrustedApplicationCopyData(val2, byref(dr2))
                            if not libc.memcmp(Core.CFDataGetBytePtr(dr), Core.CFDataGetBytePtr(dr2), min(Core.CFDataGetLength(dr), Core.CFDataGetLength(dr2))):
                                to_replace.append(i)

                with releasing(Core.CFArrayCreateMutableCopy(None, Core.CFArrayGetCount(trustedapplist) + 1, trustedapplist)) as mutablearray:
                    for j in reversed(to_replace):
                        Core.CFArrayRemoveValueAtIndex(mutablearray, j)

                    Core.CFArrayAppendValue(mutablearray, app)
                    Security.SecACLSetSimpleContents(aclref, mutablearray, sr, byref(ps))


def _each_aclref(access):
    with releasing(CFArrayRef()) as acllist:
        Security.SecAccessCopyACLList(access, byref(acllist))
        for item in CFArray(acllist).refs():
            yield item


def _get_authorizations(aclref):
    amt = c_uint32(0)
    try:
        Security.SecACLGetAuthorizations(aclref, None, byref(amt))
    except OSStatusError as e:
        if e.errno != errSecParam:
            raise

    authos = (CSSM_ACL_AUTHORIZATION_TAG * amt.value)()
    Security.SecACLGetAuthorizations(aclref, authos, amt)
    return authos


def _add_app_to_acl_with_any_authorization(access, authorizations, app, replace = False):
    for aclref in _each_aclref(access):
        for auth in _get_authorizations(aclref):
            if auth in authorizations:
                break
        else:
            continue

        _add_app_to_aclref(aclref, app, replace=replace)


class KeychainItem(object):

    def __init__(self, name, username, item, value):
        self.name = name
        self.username = username
        self.item = item
        self.value = value

    @classmethod
    def find(cls, name, username):
        datalen = c_uint32()
        data = c_char_p()
        item = SecKeychainItemRef()
        try:
            Security.SecKeychainFindGenericPassword(None, len(name), name, len(username), username, byref(datalen), byref(data), byref(item))
            value = string_at(data, datalen.value)
        except OSStatusError as e:
            if e.errno == errSecItemNotFound:
                raise KeyError(name)
            raise
        finally:
            Security.SecKeychainItemFreeContent(None, data)

        toret = cls(name, username, item, value)
        return toret

    def dump_acl(self, tfunc):
        with releasing(SecAccessRef()) as access:
            Security.SecKeychainItemCopyAccess(self.item, byref(access))
            for i, aclref in enumerate(_each_aclref(access)):
                tfunc('ACL #%s, auths: %r', i, list(_get_authorizations(aclref)))
                for app in _yield_all_trusted_app_data(aclref):
                    tfunc('APP: %r', app)

    @classmethod
    def new(cls, name, username, value, application_path):
        attr_list = cls.attr_list(name, username)
        item = SecKeychainItemRef()
        with releasing(SecTrustedApplicationRef()) as app:
            with releasing(SecAccessRef()) as access:
                Security.SecTrustedApplicationCreateFromPath(application_path, byref(app))
                arrayValues = (SecTrustedApplicationRef * 1)()
                arrayValues[0] = app
                with releasing(Core.CFArrayCreate(None, arrayValues, 1, None)) as array:
                    with releasing(python_to_property(name)) as _c:
                        Security.SecAccessCreate(_c, array, byref(access))
                _add_app_to_acl_with_any_authorization(access, (CSSM_ACL_AUTHORIZATION_CHANGE_ACL,), app)
                Security.SecKeychainItemCreateFromContent(kSecGenericPasswordItemClass, attr_list, len(value), value, None, access, byref(item))
                return cls(name, username, item, value)

    @staticmethod
    def attr_list(name, username):
        return SecKeychainAttributeList.from_attrs({kSecCommentItemAttr: '%s on %s' % (name, _gethostname()),
         kSecServiceItemAttr: name,
         kSecAccountItemAttr: username,
         kSecLabelItemAttr: name})

    def update(self, username = None, value = None):
        if value is None:
            value = self.value
        username = username or self.username
        attr_list = self.attr_list(self.name, username)
        Security.SecKeychainItemModifyContent(self.item, attr_list, len(value), value)
        self.username = username
        self.value = value

    def add_trusted_application(self, application_path, replace = False):
        if not isinstance(application_path, str) and not isinstance(application_path, unicode):
            raise ValueError('application_path argument is not stringy: %r' % (application_path,))
        if isinstance(application_path, unicode):
            application_path = application_path.encode('utf-8')
        with releasing(SecTrustedApplicationRef()) as app:
            with releasing(SecAccessRef()) as access:
                Security.SecTrustedApplicationCreateFromPath(application_path, byref(app))
                Security.SecKeychainItemCopyAccess(self.item, byref(access))
                _add_app_to_acl_with_any_authorization(access, set((CSSM_ACL_AUTHORIZATION_CHANGE_ACL,
                 CSSM_ACL_AUTHORIZATION_DECRYPT,
                 CSSM_ACL_AUTHORIZATION_DERIVE,
                 CSSM_ACL_AUTHORIZATION_EXPORT_CLEAR,
                 CSSM_ACL_AUTHORIZATION_EXPORT_WRAPPED,
                 CSSM_ACL_AUTHORIZATION_MAC,
                 CSSM_ACL_AUTHORIZATION_SIGN)), app, replace=replace)
                Security.SecKeychainItemSetAccess(self.item, access)

    def delete(self):
        Security.SecKeychainItemDelete(self.item)

    def __del__(self):
        if self.item:
            CFRelease(self.item)
