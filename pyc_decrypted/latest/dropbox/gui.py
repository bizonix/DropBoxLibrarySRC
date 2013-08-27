#Embedded file name: dropbox/gui.py
from __future__ import absolute_import
import functools
import sys
import threading
import time
import traceback
from dropbox.debugging import trace_calls
from dropbox.trace import TRACE, trace_locals, trace_stack, unhandled_exc_handler

class SafeValue(object):

    def __init__(self):
        self.event = threading.Event()
        self.excepted = False
        self.value = None
        self.exc_info = None

    def set(self, value):
        self.value = value
        self.event.set()

    def set_exception(self, exc, exc_info = None):
        self.value = exc
        self.exc_info = exc_info
        self.excepted = True
        self.event.set()

    def isSet(self):
        return self.event.isSet()

    def wait(self, *n, **kw):
        self.event.wait(*n, **kw)
        if self.excepted:
            if self.exc_info is not None:
                raise self.exc_info[0], self.exc_info[1], self.exc_info[2]
            else:
                raise self.value
        return self.value


class TimedThrottler(object):

    def __init__(self, fn, frequency = 1.0):
        self.fn = fn
        self.last_time = time.time()
        self.frequency = frequency

    def __call__(self, *args, **kwargs):
        t = time.time()
        if t - self.last_time > self.frequency:
            self.last_time = t
            self.fn(*args, **kwargs)


def spawn_thread_with_name(name):

    def nonblocking_message_f(f, *n, **kw):
        threading.Thread(target=f, args=n, kwargs=kw, name=name).start()

    return nonblocking_message_f


def running_on_thread_named(s):

    def assertion():
        return threading.currentThread().getName() == s

    return assertion


def message_sender(nonblocking_message_f, on_success = None, on_exception = None, block = False, handle_exceptions = None, dont_post = running_on_thread_named('MainThread')):

    def function_wrapper(f, *pn, **pkw):
        original_name = f.__name__
        f = functools.partial(f, *pn, **pkw)

        def on_message_queue(ret, *n, **kw):
            try:
                value = f(*n, **kw)
            except Exception as exc:
                handle_anyway = handle_exceptions or handle_exceptions is None and block == False
                if handle_anyway:
                    unhandled_exc_handler()
                exc_info = sys.exc_info()
                if on_exception is not None:
                    try:
                        on_exception(exc, exc_info)
                    except Exception:
                        unhandled_exc_handler()

                try:
                    ret.set_exception(exc, exc_info=exc_info)
                except Exception:
                    if not handle_anyway:
                        unhandled_exc_handler(exc_info=exc_info)
                    unhandled_exc_handler()

            else:
                if on_success is not None:
                    try:
                        on_success(value)
                    except Exception:
                        unhandled_exc_handler()

                ret.set(value)

        def message_queue_putter(*n, **kw):
            ret = SafeValue()
            if block and dont_post():
                on_message_queue(ret, *n, **kw)
                return ret.wait()
            else:
                nonblocking_message_f(on_message_queue, ret, *n, **kw)
                if block:
                    return ret.wait()
                return ret

        message_queue_putter.__name__ = original_name
        return message_queue_putter

    return function_wrapper


class MessageQueueException(Exception):
    pass


if True:
    assert_message_queue_local = threading.local()

    def assert_message_queue(f = None, assertion = running_on_thread_named('MainThread')):

        def guarantee_message_queue(*n, **kw):
            if not assertion():
                raise MessageQueueException(threading.currentThread().getName(), 'message queue assertion failed')
            if f is not None:
                return f(*n, **kw)

        if f is not None:
            guarantee_message_queue.__name__ = f.__name__
        return guarantee_message_queue


    def event_handler(f, assertion = running_on_thread_named('MainThread')):

        def handle_exceptions(*n, **kw):
            try:
                return assert_message_queue(f, assertion)(*n, **kw)
            except Exception:
                unhandled_exc_handler()
                TRACE('stack above exception was:')
                trace_stack()
                if kw.get('trace_locals', True):
                    TRACE('locals are:')
                    trace_locals(locals())

        handle_exceptions.__name__ = f.__name__
        if hasattr(f, 'signature'):
            try:
                import objc
                return objc.typedSelector(f.signature)(handle_exceptions)
            except Exception:
                unhandled_exc_handler()

        return handle_exceptions


else:

    def assert_message_queue(f = None, assertion = None):
        return f
