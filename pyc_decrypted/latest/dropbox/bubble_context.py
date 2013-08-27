#Embedded file name: dropbox/bubble_context.py
from __future__ import absolute_import
from functools import partial
from dropbox.trace import TRACE
from dropbox.functions import lrudict
from dropbox.trace import unhandled_exc_handler
from dropbox.debugging import easy_repr
from threading import Lock

class FunctorCR(object):
    __slots__ = ['f', 'bubble_kind']

    def __init__(self, f, *n, **kw):
        self.f = partial(f, *n, **kw)
        self.bubble_kind = None

    def __repr__(self):
        return 'FunctorCR(%s.%s, *%r, **%r, %s)' % (self.f.func.__module__,
         self.f.func.__name__,
         self.f.args,
         self.f.keywords,
         self.bubble_kind)

    def thunk(self):
        if self.f is not None:
            self.f()


class ServerPathCR(object):
    __slots__ = ['path',
     'isdir',
     'launch_folder',
     'highlight_file',
     'server_to_local',
     'bubble_kind']

    def __init__(self, launch_folder, highlight_file, server_to_local, path, isdir):
        self.launch_folder = launch_folder
        self.highlight_file = highlight_file
        self.server_to_local = server_to_local
        self.path = path
        self.isdir = isdir
        self.bubble_kind = None

    def __eq__(self, spcr):
        return self.path == spcr.path

    def __repr__(self):
        return 'ServerPathCR(%r, %r, %s)' % (self.path, self.isdir, self.bubble_kind)

    def thunk(self):
        try:
            (self.launch_folder if self.isdir else self.highlight_file)(unicode(self.server_to_local(self.path)))
        except:
            unhandled_exc_handler(True)


class MultiboxSecondaryCR(object):
    __slots__ = ('ctxt_ref', 'forward_thunk', 'bubble_kind')

    def __init__(self, ctxt_ref, forward_thunk):
        self.ctxt_ref = ctxt_ref
        self.forward_thunk = forward_thunk
        self.bubble_kind = None

    def thunk(self):
        self.forward_thunk(self.ctxt_ref)


class BubbleContext(object):

    def __init__(self, expire_by_lru = True, app = None):
        self.launch_folder = None
        self.highlight_file = None
        self.server_to_local = None
        if expire_by_lru:
            self.click_context_map = lrudict(cache_size=100)
        else:
            self.click_context_map = {}
        self.next_click_context_ref = 0
        self.lock = Lock()
        self.app = app

    def __repr__(self):
        return easy_repr(self, 'click_context_map', 'next_click_context_ref')

    def clear(self):
        self.click_context_map.clear()

    def set_sp_functions(self, launch_folder, highlight_file, server_to_local):
        self.launch_folder = launch_folder
        self.highlight_file = highlight_file
        self.server_to_local = server_to_local

    def make_sp_context_ref(self, filename, isdir):
        assert self.launch_folder is not None
        assert self.highlight_file is not None
        assert self.server_to_local is not None
        return self.make_context_ref(ServerPathCR(self.launch_folder, self.highlight_file, self.server_to_local, filename, isdir))

    def make_func_context_ref(self, f, *n, **kw):
        return self.make_context_ref(FunctorCR(f, *n, **kw))

    def make_multibox_secondary_context_ref(self, ctxt_ref):
        return self.make_context_ref(MultiboxSecondaryCR(ctxt_ref, self.app.mbox.bubble_context_thunk))

    def make_context_ref(self, theContext):
        with self.lock:
            cr = self.next_click_context_ref
            self.next_click_context_ref += 1
            self.next_click_context_ref %= 65536
            self.click_context_map[cr] = theContext
        return cr

    def is_valid_context_ref(self, cr):
        return cr in self.click_context_map

    def get_context_ref(self, cr):
        with self.lock:
            try:
                return self.click_context_map[cr]
            except KeyError:
                TRACE("Couldn't find %r in %r" % (cr, self.click_context_map))
                raise

    def thunk_and_expire_context_ref(self, cr):
        ctxt = self.get_context_ref(cr)
        bubble_kind = ctxt.bubble_kind
        ctxt.thunk()
        self.expire_context_ref(cr)
        if self.app:
            self.app.report_click_bubble(bubble_kind)

    def expire_context_ref(self, cr):
        with self.lock:
            ctxt = self.click_context_map.get(cr)
            if ctxt:
                del self.click_context_map[cr]
        if isinstance(ctxt, MultiboxSecondaryCR):
            self.app.mbox.bubble_context_expire(ctxt.ctxt_ref)
        return bool(ctxt)
