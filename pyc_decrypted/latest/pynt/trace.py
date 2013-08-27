#Embedded file name: pynt/trace.py
trace_fn = None

def TRACE(*n, **kw):
    global trace_fn
    if trace_fn:
        try:
            trace_fn(*n, **kw)
        except Exception:
            pass


def set_trace(t):
    global trace_fn
    trace_fn = t
