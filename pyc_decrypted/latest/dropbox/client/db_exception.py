#Embedded file name: dropbox/client/db_exception.py
import arch
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.sqlite3_helpers import is_corrupted_db_exception
ALL_TABLES = ['file_journal', 'config', 'block_cache']

def handle_corrupted_db(exc_type, exc_value, exc_tb, **kw):
    if exc_tb is None or exc_type is None or exc_value is None:
        return
    cur_tb = exc_tb
    while cur_tb is not None:
        if 'rebuild_database' == cur_tb.tb_frame.f_code.co_name:
            return
        cur_tb = cur_tb.tb_next

    if is_corrupted_db_exception(exc_type, exc_value, exc_tb, tables=ALL_TABLES):
        TRACE('corrupted database, restarting dropbox')
        arch.util.restart(['/corruptdb'])
