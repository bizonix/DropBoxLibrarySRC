#Embedded file name: dropbox/fatal_db_exception.py
import arch
from dropbox.trace import TRACE

def do_fatal_db_error_restart(msg):
    TRACE('Fatal db error, restarting dropbox: %r', msg)
    arch.util.restart(['/fataldb'])
