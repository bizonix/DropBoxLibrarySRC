#Embedded file name: pymac/dlls/SecurityFoundation.py
from __future__ import absolute_import
from ctypes import POINTER, c_uint32, c_char_p, c_void_p
from ..lazyframework import LazyFramework
from ..types import OSStatus, FILE, AuthorizationEnvironment, AuthorizationFlags, AuthorizationRef, AuthorizationRights, SecKeychainRef, SecKeychainItemRef, SecKeychainAttributeList, SecItemClass, SecAccessRef, SecACLRef, SecTrustedApplicationRef, CFArrayRef, CFStringRef, CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR, CFDataRef, CSSM_ACL_AUTHORIZATION_TAG
from .CoreServices import OSStatusCheck
from ..lazydll import FakeDLL

class SecurityFoundation(LazyFramework):

    def __init__(self):
        super(SecurityFoundation, self).__init__()
        self._dllname = u'SecurityFoundation'
        self._func_defs = {}

        def F(name, ret = None, args = [], errcheck = OSStatusCheck):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args,
             'errcheck': errcheck}

        F('SecKeychainCopyDefault', OSStatus, [POINTER(SecKeychainRef)])
        F('SecKeychainItemModifyContent', OSStatus, [SecKeychainItemRef,
         POINTER(SecKeychainAttributeList),
         c_uint32,
         c_char_p])
        F('SecKeychainItemCreateFromContent', OSStatus, [SecItemClass,
         POINTER(SecKeychainAttributeList),
         c_uint32,
         c_char_p,
         SecKeychainRef,
         SecAccessRef,
         POINTER(SecKeychainItemRef)])
        F('SecKeychainAddGenericPassword', OSStatus, [SecKeychainRef,
         c_uint32,
         c_char_p,
         c_uint32,
         c_char_p,
         c_uint32,
         c_char_p,
         POINTER(SecKeychainItemRef)])
        F('SecKeychainFindGenericPassword', OSStatus, [SecKeychainRef,
         c_uint32,
         c_char_p,
         c_uint32,
         c_char_p,
         POINTER(c_uint32),
         POINTER(c_char_p),
         POINTER(SecKeychainItemRef)])
        F('SecKeychainItemFreeContent', OSStatus, [c_void_p, c_char_p])
        F('SecKeychainItemDelete', OSStatus, [SecKeychainItemRef])
        F('SecTrustedApplicationCreateFromPath', OSStatus, [c_char_p, POINTER(SecTrustedApplicationRef)])
        F('SecKeychainItemCopyAccess', OSStatus, [SecKeychainItemRef, POINTER(SecAccessRef)])
        F('SecKeychainItemSetAccess', OSStatus, [SecKeychainItemRef, SecAccessRef])
        F('SecACLCreateFromSimpleContents', OSStatus, [SecAccessRef,
         CFArrayRef,
         CFStringRef,
         POINTER(CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR),
         POINTER(SecACLRef)])
        F('SecAccessCopyACLList', OSStatus, [SecAccessRef, POINTER(CFArrayRef)])
        F('SecACLCopySimpleContents', OSStatus, [SecACLRef,
         POINTER(CFArrayRef),
         POINTER(CFStringRef),
         POINTER(CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR)])
        F('SecAccessCreate', OSStatus, [CFStringRef, CFArrayRef, POINTER(SecAccessRef)])
        F('SecACLSetSimpleContents', OSStatus, [SecACLRef,
         CFArrayRef,
         CFStringRef,
         POINTER(CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR)])
        F('SecTrustedApplicationCopyData', OSStatus, [SecTrustedApplicationRef, POINTER(CFDataRef)])
        F('SecACLGetAuthorizations', OSStatus, [SecACLRef, POINTER(CSSM_ACL_AUTHORIZATION_TAG), POINTER(c_uint32)])
        F('AuthorizationCreate', OSStatus, [POINTER(AuthorizationRights),
         POINTER(AuthorizationEnvironment),
         AuthorizationFlags,
         POINTER(AuthorizationRef)])
        F('AuthorizationCopyRights', OSStatus, [AuthorizationRef,
         POINTER(AuthorizationRights),
         POINTER(AuthorizationEnvironment),
         AuthorizationFlags,
         c_void_p])
        F('AuthorizationExecuteWithPrivileges', OSStatus, [AuthorizationRef,
         c_char_p,
         AuthorizationFlags,
         POINTER(c_char_p),
         POINTER(POINTER(FILE))])
        F('AuthorizationFree', OSStatus, [AuthorizationRef, AuthorizationFlags])


Security = FakeDLL(SecurityFoundation)
