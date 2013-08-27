#Embedded file name: dropbox/trace_printer.py
from __future__ import absolute_import
import datetime
import itertools
import os
import sys
import threading
_colors = [ '0;%d' % (31 + d) for d in xrange(1, 6) ] + [ '1;%d' % (31 + d) for d in xrange(1, 6) ]

def name_to_color(tn):
    return _colors[abs(hash(tn)) % len(_colors)]


def output_fn_from_file_object(obj):

    def output(*n):
        obj.writelines(itertools.chain(n, (os.linesep,)))

    return output


def generate_high_trace_printer(print_color = False, print_name = False, print_time = False, output = None, output_file = None):
    if output is None:
        if output_file is None:
            output_file = sys.stderr
        output = output_fn_from_file_object(output_file)

    def get_time():
        return datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]

    if print_name and print_color and print_time:

        def hai(threadname, segment):
            tn = threadname
            sg = segment
            c = name_to_color(tn)
            is_bad = sg[:2] == '!!'
            output('\x1b[1m', get_time(), '\x1b[0m \x1b[', c, 'm', tn, '\x1b[0m: ', '\x1b[31;1m' if is_bad else '', sg, '\x1b[0m' if is_bad else '')

    elif print_name and print_color:

        def hai(threadname, segment):
            tn = threadname
            sg = segment
            c = name_to_color(tn)
            is_bad = sg[:2] == '!!'
            output('\x1b[', c, 'm', tn, '\x1b[0m: ', '\x1b[31;1m' if is_bad else '', sg, '\x1b[0m' if is_bad else '')

    elif print_name and print_time:

        def hai(threadname, segment):
            output(get_time(), ' ', threadname, ': ', segment)

    elif print_name:

        def hai(threadname, segment):
            output(threadname, ': ', segment)

    elif print_time:

        def hai(threadname, segment):
            output(get_time(), ' ', segment)

    else:

        def hai(threadname, segment):
            output(segment)

    return hai


def generate_trace_printer(*n, **kw):
    fn = generate_high_trace_printer(*n, **kw)
    t = threading.Lock()

    def new_fn(s):
        try:
            s = s.encode('utf-8') if isinstance(s, unicode) else str(s)
            tn = threading.currentThread().getName()
            lines = s.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            if s.startswith('!!'):
                with t:
                    for seg in lines:
                        if not seg.startswith('!!'):
                            seg = '!! ' + seg
                        fn(tn, seg)

            else:
                for seg in lines:
                    with t:
                        fn(tn, seg)

        except:
            pass

    return new_fn


def generate_default_console_trace_printer():
    print_color = sys.stderr.isatty() and os.getenv('TERM') != 'dumb' and not sys.platform.startswith('win32')
    return generate_trace_printer(print_color=print_color, print_time=True, print_name=True)
