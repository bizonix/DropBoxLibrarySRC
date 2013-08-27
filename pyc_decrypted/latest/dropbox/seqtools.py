#Embedded file name: dropbox/seqtools.py
from __future__ import absolute_import
import itertools

class seqmap(object):
    __slots__ = ('ps', 'func')

    def __init__(self, func, parent_seq):
        self.ps = parent_seq
        self.func = func

    def __len__(self):
        return len(self.ps)

    def __getitem__(self, key):
        try:
            return seqmap(self.func, seqslice(self, *key.indices(len(self))))
        except AttributeError:
            return self.func(self.ps[key])

    def __iter__(self):
        return iter((self.func(a) for a in self.ps))

    def __repr__(self):
        return '%s.seqmap(%r, %r)' % (self.__module__, self.ps, self.func)


class seqslice(object):
    __slots__ = ('ps', 'start', 'stop', 'step')

    def __init__(self, parent_seq, *args):
        self.ps = parent_seq
        self.start, self.stop, self.step = slice(*args).indices(len(parent_seq))

    def __len__(self):
        toret = (self.stop - self.start + self.step - 1) / self.step
        if toret < 0:
            toret += len(self.ps)
        return toret

    def __getitem__(self, key):
        try:
            return seqslice(self, *key.indices(len(self)))
        except AttributeError:
            if key >= len(self):
                raise IndexError()
            if key < 0:
                key += len(self)
            return self.ps[self.start + key]

    def __iter__(self):
        return iter((self.ps[(i + self.start) % len(self.ps)] for i in xrange(len(self))))

    def __repr__(self):
        return '%s.seqslice(%r)' % (self.__module__, self.ps)


_reversed = reversed

class seqreversed(object):
    __slots__ = ('parent_seq',)

    def __init__(self, parent_seq):
        self.parent_seq = parent_seq

    def __len__(self):
        return len(self.parent_seq)

    def __getitem__(self, key):
        try:
            return seqslice(self, *key.indices(len(self)))
        except AttributeError:
            if key >= len(self):
                raise IndexError
            if key < 0:
                key += len(self)
            if key < 0:
                raise IndexError()
            return self.parent_seq[len(self.parent_seq) - 1 - key]

    def __iter__(self):
        return iter(_reversed(self.parent_seq))

    def __repr__(self):
        return '%s.seqreversed(%r)' % (self.__module__, self.parent_seq)


reversed = seqreversed

class seqchain(object):
    __slots__ = ('sequences', 'len')

    def __init__(self, *sequences):
        self.sequences = sequences
        self.len = sum((len(a) for a in sequences))

    def __repr__(self):
        return '%s.seqchain(*%r)' % (self.__module__, self.sequences)

    def __getitem__(self, key):
        try:
            start, stop, stride = key.indices(self.len)
            is_slice = True
        except AttributeError:
            if key < 0:
                key += len(self)
            if key < 0:
                raise IndexError()
            start, stop, stride = key, key, 1
            is_slice = False

        i = 0
        seqs_start = 0
        seqs_stop = len(self.sequences[0])
        while start >= seqs_stop:
            i += 1
            if i == len(self.sequences):
                if is_slice:
                    return []
                raise IndexError()
            seqs_start = seqs_stop
            seqs_stop += seqs_start + len(self.sequences[i])

        if not is_slice:
            return self.sequences[i][start - seqs_start]
        to_ret = []
        while True:
            if start <= seqs_start:
                if stop >= seqs_stop:
                    to_ret.append(self.sequences[i])
                else:
                    to_ret.append(seqslice(self.sequences[i], 0, stop - seqs_start))
            elif stop >= seqs_stop:
                to_ret.append(seqslice(self.sequences[i], start - seqs_start, None))
            else:
                to_ret.append(seqslice(self.sequences[i], start - seqs_start, stop - seqs_start))
            if stop <= seqs_stop:
                break
            i += 1
            if i == len(self.sequences):
                break
            seqs_start += len(self.sequences[i])
            seqs_stop += len(self.sequences[i])

        to_ret = seqchain(*to_ret)
        if stride != 1:
            return seqslice(to_ret, 0, None, stride)
        else:
            return to_ret

    def __len__(self):
        return self.len

    def __iter__(self):
        return iter(itertools.chain(*self.sequences))
