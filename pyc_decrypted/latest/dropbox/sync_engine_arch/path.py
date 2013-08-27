#Embedded file name: dropbox/sync_engine_arch/path.py
import re

def sanitize_filename(invalid_chars_re):

    def f(filename, repl):
        sanitized_name = re.sub(pattern='%s+' % invalid_chars_re, repl=repl, string=filename)
        sanitized_name = re.sub(pattern='^\\.+', repl=repl, string=sanitized_name).strip()
        return sanitized_name

    return f


def sanitize_filename_unix():
    return sanitize_filename(u'[/\x00]')
