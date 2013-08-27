#Embedded file name: dropbox/callbacks.py
from __future__ import absolute_import
import functools
import operator
import threading

class Handler(object):

    def __init__(self, recursive = True, handle_exc = None):
        self.add_lock = threading.Lock()
        self.handle_exc = handle_exc
        self.recursive = recursive
        self.local = threading.local()
        self.clear()

    def __repr__(self):
        with self.add_lock:
            return '<Handler callbacks=%r>' % (self.l2,)

    def __nonzero__(self):
        with self.add_lock:
            return self.l2

    def add_handler(self, handler, priority = 0):
        with self.add_lock:
            self.l2[handler] = priority
            self.add_flag = True

    def remove_handler(self, handler):
        with self.add_lock:
            try:
                del self.l2[handler]
            except KeyError:
                pass
            else:
                self.add_flag = True

    def clear(self):
        with self.add_lock:
            self.l2 = {}
            self.add_flag = True

    second_item_getter = operator.itemgetter(1)

    def run_handlers(self, *n, **kw):
        if not hasattr(self.local, 'run_count'):
            self.local.run_count = 0
        if not self.recursive and self.local.run_count:
            raise Exception('Recursively called run handlers, %r' % (self.run_count,))
        if self.add_flag:
            with self.add_lock:
                if self.add_flag:
                    l = self.l = sorted(self.l2.iteritems(), key=self.second_item_getter)
                    self.add_flag = False
                else:
                    l = self.l
        else:
            l = self.l
        self.local.run_count += 1
        try:
            for h, p in l:
                try:
                    h(*n, **kw)
                except Exception:
                    if self.handle_exc:
                        self.handle_exc()

        finally:
            self.local.run_count -= 1


def watchable(f):
    f.pre = Handler()
    f.post = Handler()

    @functools.wraps(f)
    def run_handlers_and_call(*n, **kw):
        f.pre.run_handlers(*n, **kw)
        ret = f(*n, **kw)
        f.post.run_handlers(ret)

    return run_handlers_and_call


class Observable(object):

    def __init__(self, val = None, recursive = True, handle_exc = None):
        self.data = val
        self.handler = Handler(recursive=recursive, handle_exc=handle_exc)
        self.register = self.handler.add_handler
        self.unregister = self.handler.remove_handler

    def set(self, data):
        self.data = data
        self.handler.run_handlers(data)

    def get(self):
        return self.data

    def append(self, item):
        self.data.append(item)
        self.handler.run_handlers(item)


class ObservableIterator(object):

    def __init__(self, iterator, recursive = True, handle_exc = None):
        self._iterator = iterator
        self.handler = Handler(recursive=recursive, handle_exc=handle_exc)
        self.register = self.handler.add_handler
        self.unregister = self.handler.remove_handler

    def __iter__(self):
        for i, item in enumerate(self._iterator):
            self.handler.run_handlers(i)
            yield item
