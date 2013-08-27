#Embedded file name: arch/linux/authorization.py
from dropbox.i18n import trans
from dropbox.trace import TRACE
from .internal import run_as_root

def request_authorization_from_user_and_run(cmd, argv, auth_text = ''):
    if auth_text:
        auth_text += u'\n'
    auth_text += trans(u'Type your Linux password to let Dropbox make changes.')
    TRACE('Running %s as root', cmd)
    retcode = run_as_root([cmd] + argv, auth_text)
    TRACE('%s returned %s', cmd, retcode)
    if retcode != 0:
        raise Exception('command %s %r returned nonzero retcode %r' % (cmd, argv, retcode))
