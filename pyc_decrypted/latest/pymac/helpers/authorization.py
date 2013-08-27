#Embedded file name: pymac/helpers/authorization.py
import time
from ctypes import byref, c_char_p, POINTER, pointer
from ..constants import errAuthorizationToolExecuteFailure, errAuthorizationCanceled, kAuthorizationFlagInteractionAllowed, kAuthorizationFlagExtendRights, kAuthorizationFlagPreAuthorize, kAuthorizationEmptyEnvironment, kAuthorizationRightExecute, kAuthorizationEnvironmentPrompt, kAuthorizationFlagDefaults
from ..dlls import Security
from ..types import AuthorizationRef, AuthorizationRights, AuthorizationItem, AuthorizationEnvironment, FILE
from .core import OSStatusError
from .pythonfile import FILE_to_python_file

class AuthorizationCanceled(Exception):
    pass


def request_authorization_from_user_and_run(cmd, argv, auth_text = None):
    assert isinstance(cmd, str)
    if auth_text:
        if isinstance(auth_text, unicode):
            auth_text = auth_text.encode('utf-8')
        assert isinstance(auth_text, str)
    authorization = AuthorizationRef()
    flags = kAuthorizationFlagInteractionAllowed | kAuthorizationFlagExtendRights | kAuthorizationFlagPreAuthorize
    Security.AuthorizationCreate(POINTER(AuthorizationRights)(), kAuthorizationEmptyEnvironment, flags, byref(authorization))
    try:
        item = AuthorizationItem(name=kAuthorizationRightExecute, valueLength=len(cmd), value=cmd, flags=0)
        rights = AuthorizationRights(count=1, items=pointer(item))
        if not auth_text:
            env_p = kAuthorizationEmptyEnvironment
        else:
            prompt_item = AuthorizationItem(name=kAuthorizationEnvironmentPrompt, valueLength=len(auth_text), value=auth_text, flags=0)
            environment = AuthorizationEnvironment(count=1, items=pointer(prompt_item))
            env_p = pointer(environment)
        Security.AuthorizationCopyRights(authorization, byref(rights), env_p, flags, None)
        argv = (c_char_p * (len(argv) + 1))(*(argv + [None]))
        channel = POINTER(FILE)()
        i = 0
        while True:
            try:
                Security.AuthorizationExecuteWithPrivileges(authorization, cmd, kAuthorizationFlagDefaults, argv, byref(channel))
                break
            except OSStatusError as e:
                if e.errno == errAuthorizationToolExecuteFailure:
                    if i != 5:
                        time.sleep(1)
                        i += 1
                        continue
                    raise

        return FILE_to_python_file(channel, '<channel>', 'r')
    except OSStatusError as e:
        if e.errno == errAuthorizationCanceled:
            raise AuthorizationCanceled()
        raise
    finally:
        try:
            Security.AuthorizationFree(authorization, kAuthorizationFlagDefaults)
        except Exception:
            pass
