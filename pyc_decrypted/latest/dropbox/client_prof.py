#Embedded file name: dropbox/client_prof.py
import threading
import time
from dropbox.trace import TRACE, is_debugging

class ProdSimpleTimer:

    def __init__(*args, **kwargs):
        pass

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass


class SimpleTimer:

    class TimerData:

        def __init__(self, cumulative, id_):
            self.cumulative = cumulative
            self.tot_time = 0.0
            self.call_count = 0
            self.id_ = id_
            self.depth = None

    data = threading.local()

    def __init__(self, info_string, cumulative = False):
        self.info_string = info_string
        self.cumulative = cumulative
        if not hasattr(SimpleTimer.data, 'depth'):
            SimpleTimer.data.depth = 0
            SimpleTimer.data.cumulative_depth = 0
            SimpleTimer.data.msg_dict = {}
            SimpleTimer.data.info_dict = {}
            SimpleTimer.data.cumulative_call_count = {}
            SimpleTimer.data.id_dict = {}
            SimpleTimer.data.depth_dict = {}
            SimpleTimer.data.curr_id = 0
        if info_string not in SimpleTimer.data.info_dict:
            if not cumulative:
                assert SimpleTimer.data.cumulative_depth == 0, "SimpleTimer: Did you do a non-cumulative timer (%s) inside a cumulative timer (one of %s)? That doesn't make sense." % (info_string, repr([ k for k, info in SimpleTimer.data.info_dict.iteritems() if info.cumulative ]))
            SimpleTimer.data.info_dict[info_string] = info = SimpleTimer.TimerData(cumulative, SimpleTimer.data.curr_id)
            info.id_ = SimpleTimer.data.curr_id
            SimpleTimer.data.curr_id += 1
        assert SimpleTimer.data.info_dict[info_string].cumulative == cumulative, 'Did you use multiple SimpleTimer with the same identifier?'

    def __enter__(self):
        SimpleTimer.data.depth += 1
        if self.cumulative:
            SimpleTimer.data.cumulative_depth += 1
        self.t1 = time.time()

    def __exit__(self, type, value, traceback):
        t2 = time.time()
        diff = t2 - self.t1
        info = SimpleTimer.data.info_dict[self.info_string]
        SimpleTimer.data.depth -= 1
        info.depth = SimpleTimer.data.depth
        info.tot_time += diff
        if self.cumulative:
            SimpleTimer.data.cumulative_depth -= 1
            info.call_count += 1
        else:
            self._dump()

    @staticmethod
    def _store_msg(info_string):
        info = SimpleTimer.data.info_dict[info_string]
        cc_str = ' (called %d times)' % info.call_count if info.call_count else ''
        msg = '%6.2fs %s%s%s' % (info.tot_time,
         info.depth * '-> ',
         info_string,
         cc_str)
        if info.call_count == 0:
            TRACE('non-cumulative timer exiting: %s', msg)
        SimpleTimer.data.msg_dict[info.id_] = msg

    def _dump(self):
        assert not self.cumulative
        [ SimpleTimer._store_msg(k) for k, info in SimpleTimer.data.info_dict.iteritems() if info.cumulative ]
        for k in SimpleTimer.data.info_dict.keys():
            if SimpleTimer.data.info_dict[k].cumulative:
                del SimpleTimer.data.info_dict[k]

        SimpleTimer._store_msg(self.info_string)
        del SimpleTimer.data.info_dict[self.info_string]
        if SimpleTimer.data.depth == 0:
            for key in sorted(SimpleTimer.data.msg_dict.iterkeys()):
                TRACE('SimpleTimer: %s', SimpleTimer.data.msg_dict[key])

            SimpleTimer.data.msg_dict.clear()


if not is_debugging():
    SimpleTimer = ProdSimpleTimer
