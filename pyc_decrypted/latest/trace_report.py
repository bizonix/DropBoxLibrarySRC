#Embedded file name: trace_report.py
import traceback
import sys
from hashlib import md5
MAX_REPORT_LENGTH = 4096
try:
    import pywintypes
except:
    pywintypes = None

def make_report(exc_info = None):
    if exc_info is None:
        exc_info = sys.exc_info()
    type, val, tb = exc_info
    report = ''.join(traceback.format_exception(type, val, tb))
    stack = traceback.format_tb(tb)[:-1]
    try:
        last = traceback.format_tb(tb)[-1].split('\n')
    except IndexError:
        last = None

    if last:
        stack.append(last[0])
        try:
            if issubclass(type, EnvironmentError):
                stack.append('%s %s' % (type, getattr(val, 'errno', None)))
            elif pywintypes and issubclass(type, pywintypes.error):
                stack.append('%s %s' % (type, val[0]))
            else:
                stack.append('%s' % type)
        except:
            stack.append('<unknown type>')

    tohash = ''.join(stack).replace('\\', '/')
    hash = md5(tohash.replace('.py"', '.pyc"') if sys.platform.startswith('linux') else tohash).hexdigest()
    return (report, hash)
