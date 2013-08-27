#Embedded file name: ui/common/progress.py
import pprint
import time
from collections import defaultdict
import build_number
from dropbox.debugging import easy_repr
from dropbox.functions import snippet
from dropbox.i18n import format_number, trans, ungettext
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.common.constants import SECONDS_PER_HOUR, SECONDS_PER_DAY
from ui.common.strings import UIStrings
UNICODE_DOWN_ARROW = u'\u25bc'
UNICODE_UP_ARROW = u'\u25b2'
ACTION_DOWNLOADING = 'tss_action_downloading'
ACTION_INDEXING = 'tss_action_indexing'
ACTION_UPLOADING = 'tss_action_uploading'

class TransferStatusStrings(UIStrings):
    _strings = dict(syncing=u'Syncing (%(context)s)', syncing_generic=u'Syncing...', transfer_remaining_a_long_time=(u'a long time left. Grab a Snickers', "'Grab a Snickers' is a joke that mostly only Americans will get, from the catch phrase, 'Not going anywhere for a while? Grab a snickers'. Be creative and substitute an appropriate funny phrase here."), transfer_rate_and_time=(u'(%(speed)s KB/sec, %(time_remaining)s)', u'for example: 35 KB/sec, 5 minutes left'))
    _platform_overrides = dict()


class SpeedContainer(object):
    MAX_WINDOW = 10
    MIN_DELTA = 0.001

    def __init__(self):
        self.stream_samples = defaultdict(list)

    def get_speed(self):
        if not any(self.stream_samples.values()):
            return None
        t_end = max((samples[-1][0] for samples in self.stream_samples.values() if len(samples) > 0))
        for stream, samples in self.stream_samples.iteritems():
            self.stream_samples[stream] = [ x for x in samples if x[0] > t_end - self.MAX_WINDOW ]

        if not any(self.stream_samples.values()):
            return None
        speed = 0
        for samples in self.stream_samples.values():
            if not samples:
                continue
            data = float(sum((x[1] for x in samples)))
            total_time = sum((x[2] for x in samples))
            if total_time > 0:
                speed += data / total_time / 1024.0

        return speed

    def note_data(self, raw_size, t_delta, stream = 0):
        if t_delta < self.MIN_DELTA:
            t_delta = self.MIN_DELTA
        self.stream_samples[stream].append((time.time(), raw_size, t_delta))

    def __repr__(self):
        return easy_repr(self, 'samples')


class BaseTransferStatus(object):

    def __init__(self, verb = None, cant_sync = None, failures = None, file_count = 0, total_size = 0, remaining = 0, speed = 0, speed_samples = None, hash_speed = 0, use_unicode_symbols = False, other_transfer_status = None):
        if other_transfer_status:
            self.verb = other_transfer_status.verb
            self.cant_sync = other_transfer_status.cant_sync
            self.failures = other_transfer_status.failures
            self.file_count = other_transfer_status.file_count
            self.total_size = other_transfer_status.total_size
            self.speed = other_transfer_status.speed_counter.get_speed()
            self.speed_samples = other_transfer_status.speed_counter.stream_samples
            self.hash_speed = other_transfer_status.hash_speed_counter.get_speed()
            self.remaining = other_transfer_status.remaining
            self.use_unicode_symbols = other_transfer_status.use_unicode_symbols
        else:
            self.verb = verb
            self.cant_sync = cant_sync
            self.failures = failures
            self.file_count = file_count
            self.total_size = total_size
            self.remaining = remaining
            self.speed = speed
            self.speed_samples = speed_samples
            self.hash_speed = hash_speed
            self.use_unicode_symbols = use_unicode_symbols
        self.label = None

    def __repr__(self):
        return easy_repr(self, 'verb', 'cant_sync', 'failures', 'file_count', 'total_size', 'remaining', 'label')


class TransferStatus(BaseTransferStatus):
    THROTTLE_INTERVAL = 3.0

    def __init__(self, trigger_update, lock, *args, **kwargs):
        self.lock = lock
        self.speed_counter = SpeedContainer()
        self.hash_speed_counter = SpeedContainer()
        self.last_filename = None
        self.last_hash_done = 0.0
        self.last_trigger = 0
        self.trigger_update = trigger_update
        self.intermediate_transfer_compressed = 0
        self.compression_ratio_sum = 0
        self.num_compression_ratios = 0
        BaseTransferStatus.__init__(self, *args, **kwargs)

    def __repr__(self):
        return easy_repr(self, 'cant_sync', 'file_count', 'last_hash_done', 'speed_counter', 'hash_speed_counter')

    def _trigger_update_throttled(self):
        now = time.time()
        if now - self.last_trigger < self.THROTTLE_INTERVAL:
            return
        self.last_trigger = now
        self.trigger_update()

    def set_cant_sync(self, fn, why = None):
        with self.lock:
            if fn is None:
                self.cant_sync = None
            else:
                self.cant_sync = (fn, why)
        self.trigger_update()

    def note_hash(self, raw_size, compressed_size, t_delta):
        with self.lock:
            if t_delta != 0:
                kbsec = '%.1f' % (compressed_size / 1024.0 / t_delta,)
            else:
                kbsec = 'DIVBYZERO'
            TRACE(u'Hash transferred: %s bytes (%s uncompressed) in %.3f sec (%s kB/sec)', compressed_size, raw_size, t_delta, kbsec)
            self.total_size -= raw_size
            self.hash_speed_counter.note_data(raw_size, t_delta)
            self.last_hash_done = time.time()
            self.intermediate_transfer_compressed = 0
            self.compression_ratio_sum += compressed_size / float(raw_size)
            self.num_compression_ratios += 1
        self._trigger_update_throttled()

    def note_hashes(self, hash_list, t_delta):
        with self.lock:
            total_raw_size = 0
            total_compressed_size = 0
            for raw_size, compressed_size in hash_list:
                total_raw_size += raw_size
                total_compressed_size += compressed_size
                self.compression_ratio_sum += compressed_size / float(raw_size)
                self.num_compression_ratios += 1

            if t_delta != 0:
                kbsec = '%.1f' % (total_compressed_size / 1024.0 / t_delta,)
            else:
                kbsec = 'DIVBYZERO'
            TRACE(u'Hashes transferred: %s bytes (%s uncompressed) in %.3f sec (%s kB/sec)', total_compressed_size, total_raw_size, t_delta, kbsec)
            self.total_size -= total_raw_size
            self.hash_speed_counter.note_data(total_raw_size, t_delta)
            self.last_hash_done = time.time()
        self.intermediate_transfer_compressed = 0
        self._trigger_update_throttled()

    def note_data(self, size, t_delta, stream = 0):
        with self.lock:
            self.speed_counter.note_data(size, t_delta, stream=stream)
            self.intermediate_transfer_compressed += size
        self._trigger_update_throttled()

    def cancel_intermediate_transfer(self):
        with self.lock:
            self.intermediate_transfer_compressed = 0
        self.trigger_update()

    def set_file_count(self, file_count, total_size, num_hashes, last_filename = None, failures = None):
        should_update = False
        with self.lock:
            if total_size is not None and total_size != self.total_size:
                self.total_size = total_size
                if not self.total_size:
                    self.speed_counter = SpeedContainer()
                    self.hash_speed_counter = SpeedContainer()
                should_update = True
            if file_count is not None and file_count != self.file_count:
                self.file_count = file_count
                if not self.file_count:
                    self.cant_sync = None
                    self.failures = None
                    self.speed_counter = SpeedContainer()
                    self.hash_speed_counter = SpeedContainer()
                else:
                    self.failures = failures
                    self.last_filename = last_filename
                should_update = True
        if should_update:
            self.trigger_update()

    def reset_transfer_speed(self):
        with self.lock:
            self.speed_counter = SpeedContainer()
            self.hash_speed_counter = SpeedContainer()
        self.trigger_update()

    def get_transfer_speed(self):
        with self.lock:
            return self.speed_counter.get_speed()

    def get_label(self, lansync = False):
        with self.lock:
            if not self.file_count:
                return (None, self.file_count, -1)
            if self.file_count == 1 and self.last_filename:
                if self.verb == ACTION_DOWNLOADING:
                    if self.use_unicode_symbols:
                        ret = UNICODE_DOWN_ARROW + u' ' + snippet(self.last_filename)
                    else:
                        ret = trans(u'Downloading "%s"') % (snippet(self.last_filename),)
                elif self.verb == ACTION_INDEXING:
                    ret = trans(u'Indexing "%s"') % (snippet(self.last_filename),)
                elif self.verb == ACTION_UPLOADING:
                    if self.use_unicode_symbols:
                        ret = UNICODE_UP_ARROW + u' ' + snippet(self.last_filename)
                    else:
                        ret = trans(u'Uploading "%s"') % (snippet(self.last_filename),)
                else:
                    assert False, u'self.verb is %r; not an allowed action. For %s' % (self.verb, self)
            else:
                if self.verb == ACTION_DOWNLOADING:
                    if self.use_unicode_symbols:
                        label_template = UNICODE_DOWN_ARROW + u' ' + ungettext(u'%s file', u'%s files', self.file_count)
                    else:
                        label_template = ungettext(u'Downloading %s file', u'Downloading %s files', self.file_count)
                elif self.verb == ACTION_INDEXING:
                    label_template = ungettext(u'Indexing %s file', u'Indexing %s files', self.file_count)
                elif self.verb == ACTION_UPLOADING:
                    if self.use_unicode_symbols:
                        label_template = UNICODE_UP_ARROW + u' ' + ungettext(u'%s file', u'%s files', self.file_count)
                    else:
                        label_template = ungettext(u'Uploading %s file', u'Uploading %s files', self.file_count)
                else:
                    assert False, u'self.verb is %r; not an allowed action. For %s' % (self.verb, self)
                ret = label_template % (format_number(self.file_count, frac_precision=0),)
            if lansync and self.total_size:
                ret += u' (LAN)'
            speed = self.speed_counter.get_speed()
            if self.total_size and speed:
                hash_speed = self.hash_speed_counter.get_speed()
                if not hash_speed or hash_speed > speed:
                    hash_speed = speed
                remaining_bytes = self.total_size - self.intermediate_transfer_compressed * (self.num_compression_ratios / self.compression_ratio_sum if self.compression_ratio_sum else 1)
                remaining = remaining_bytes / hash_speed / 1024.0
                if remaining < 0:
                    remaining = 60
                try:
                    assert not build_number.is_frozen() or self.verb != ACTION_UPLOADING or speed < 100000, u'Upload Transfer is going really fast: %r, %s' % (speed, pprint.pformat(self.speed_counter.stream_samples))
                except Exception:
                    unhandled_exc_handler()

                TRACE(u'Action %s %.1f kB remaining (roughly); finish in %.2f sec at hash_speed: %.1f kB/sec, transfer_speed: %.1f kB/sec', self.verb, remaining_bytes / 1024.0, remaining, hash_speed, speed)
                remaining_str = remaining_to_str(remaining)
                speed_str = format_number(speed, frac_precision=0 if speed >= 1000.0 else 1)
                ret += u' ' + TransferStatusStrings.transfer_rate_and_time % dict(speed=speed_str, time_remaining=remaining_str)
            else:
                if self.total_size:
                    TRACE('%r REALLY slowly (like, not at all), %r %r', self.verb, speed, self.total_size)
                remaining = -1
                ret += u'...'
            return (ret, self.file_count, remaining)


def remaining_to_str(remaining):
    if remaining < 1:
        remaining = 1
    if remaining < 60:
        nremaining = int(remaining)
        return ungettext(u'%s sec left', u'%s secs left', nremaining) % (format_number(nremaining, frac_precision=0),)
    elif remaining < SECONDS_PER_HOUR:
        nremaining = int(remaining / 60)
        return ungettext(u'%s min left', u'%s mins left', nremaining) % (format_number(nremaining, frac_precision=0),)
    elif remaining < SECONDS_PER_DAY * 2:
        nremaining = int(remaining / SECONDS_PER_HOUR)
        return ungettext(u'%s hour left', u'%s hrs left', nremaining) % (format_number(nremaining, frac_precision=0),)
    elif remaining < SECONDS_PER_DAY * 100:
        nremaining = int(remaining / SECONDS_PER_DAY)
        return ungettext(u'%s day left', u'%s days left', nremaining) % (format_number(nremaining, frac_precision=0),)
    else:
        return TransferStatusStrings.transfer_remaining_a_long_time


def get_summary_label(seconds, files):
    try:
        time_remaining = max(seconds)
        time_remaining_str = None
        if time_remaining >= 0:
            time_remaining_str = remaining_to_str(time_remaining)
        files_remaining = sum(files)
        files_remaining_template = ungettext(u'%s file remaining', u'%s files remaining', files_remaining)
        files_remaining_str = files_remaining_template % format_number(files_remaining, frac_precision=0)
        return TransferStatusStrings.syncing % {'context': '%s%s' % (files_remaining_str, '' if not time_remaining_str else ', %s' % (time_remaining_str,))}
    except Exception:
        unhandled_exc_handler()
        return TransferStatusStrings.syncing_generic
