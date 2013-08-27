#Embedded file name: dropbox/client/profile.py
import os
import time
from dropbox.bubble import BubbleKind, Bubble
from dropbox.gui import assert_message_queue
from dropbox.platform import platform
from dropbox.trace import TRACE

@assert_message_queue
def plop_profile(app, seconds = 10, filename = None):
    if platform == 'win':
        return
    if not filename:
        filename = '%s-%s.plop' % ('client', time.strftime('%Y%m%d-%H%M-%S'))
    from plop.collector import Collector
    collector = Collector()

    @assert_message_queue
    def stop_profile():
        TRACE('Done profiling')
        collector.stop()
        if collector.samples_taken:
            path = os.path.expanduser(u'~/dropbox_profiles')
            app.safe_makedirs(path)
            path = os.path.join(path, filename)
            with open(path, 'w') as f:
                f.write(repr(dict(collector.stack_counts)))
            TRACE('profile output saved to %s', path)
            overhead = float(collector.sample_time) / collector.samples_taken
            TRACE('overhead was %s per sample (%s%%)', overhead, overhead / collector.interval)
            app.ui_kit.show_bubble(Bubble(BubbleKind.DEBUG_BUBBLE_LONG, u'Profile data saved to %s. Overhead was %s per sample (%s%%)' % (path, overhead, overhead / collector.interval), u'Love bdarns!'))
        else:
            app.ui_kit.show_bubble(Bubble(BubbleKind.DEBUG_BUBBLE_LONG, u'No data collected.', u'Miss bdarns!'))

    collector.start()
    TRACE('Profiling for %f seconds', seconds)
    app.ui_kit.call_later(seconds, stop_profile)
