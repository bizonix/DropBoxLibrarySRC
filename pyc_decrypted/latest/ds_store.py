#Embedded file name: ds_store.py
import itertools
import math
import struct
from dropbox.trace import TRACE

class DsStoreException(Exception):
    pass


class DsStoreFileReadError(DsStoreException):
    pass


class DsStoreInfiniteLoopException(DsStoreException):
    pass


def offset_and_nbits_from_addr(addr):
    return (addr & -32, addr & 31)


class OffsetManager(dict):

    def __init__(self, offset_list = None):
        if offset_list is not None:
            for k, v in enumerate(offset_list):
                if v == 0:
                    continue
                self[k] = v

    def findNextBlockNum(self):
        n = 1
        while n in self:
            n += 1

        return n

    def largestBlockNum(self):
        if not self:
            return -1
        return max(self.keys())

    def numBlocksUsed(self):
        return len(self.keys())


class ReadBlock(object):

    def __init__(self, allocator, offset, size):
        self.allocator = allocator
        self.pos = 0
        self.block = allocator.read(offset, size)
        self.offset = offset
        self.size = size
        assert self.block, 'no block allocated'

    def read(self, l, format = None):
        assert self.pos + l <= len(self.block), 'end of writing (%s + %s = %s) not within block len %s' % (self.pos,
         l,
         self.pos + l,
         len(self.block))
        data = self.block[self.pos:self.pos + l]
        self.pos += l
        if format is None:
            return data
        retval = struct.unpack(format, data)
        if len(retval) == 1:
            return retval[0]
        return retval

    def readInt(self):
        return self.read(4, '>I')

    def seek(self, pos):
        self.pos = pos

    def __len__(self):
        return len(self.block)

    def __repr__(self):
        return '<read-only Block at offset %s of size %s>' % (self.offset, self.size)

    def readBtreeNode(self):
        pointer = self.readInt()
        count = self.readInt()
        values = []
        pointers = []
        if pointer > 0:
            for i in xrange(count):
                pointers.append(self.readInt())
                values.append(Entry.readEntry(self))

            pointers.append(pointer)
        else:
            for i in xrange(count):
                values.append(Entry.readEntry(self))

        return (values, pointers)


class WriteBlock(object):

    def __init__(self, allocator, offset, size):
        assert offset > 0, 'offset %s is not positive' % (offset,)
        self.allocator = allocator
        self.pos = 0
        self.offset = offset
        self.size = size

    def read(self, *n, **kw):
        raise NotImplementedError('This is a write-only block.')

    def __len__(self):
        return self.size

    def seek(self, pos):
        self.pos = pos

    def write(self, what):
        l = len(what)
        if self.pos + l > self.size:
            raise DsStoreException('Writing past end of block; %s bytes at %s goes past %s' % (l, self.pos, self.size))
        assert self.pos >= 0, 'position %s is negative' % (self.pos,)
        self.allocator.write(what, self.offset + self.pos)
        self.pos += l

    def close(self, fill = False):
        if fill and self.pos < self.size:
            self.write('\x00' * (self.size - self.pos))

    def __repr__(self):
        return '<WriteBlock at offset %s of size %s; curr pos %s>' % (self.offset, self.size, self.pos)

    def writeBtreeNode(self, values, pointers):
        if not pointers:
            self.write(struct.pack('>II', 0, len(values)))
            for val in values:
                data = val.asByteString()
                self.write(data)

        else:
            assert len(pointers) == len(values) + 1, 'Value count should be one less than pointer count'
            self.write(struct.pack('>II', pointers[-1], len(values)))
            for i, val in enumerate(values):
                self.write(struct.pack('>I', pointers[i]))
                data = val.asByteString()
                self.write(data)


class BuddyAllocator(object):
    MAGIC1 = 1
    MAGIC2 = 'Bud1'

    def __init__(self, fileobj, unknown = None, is_new = True):
        self.fileobj = fileobj
        self.fudge = 4
        if unknown is not None:
            self.unknown = unknown
        else:
            self.unknown = struct.pack('>IIII', 4108, 135, 8203, 0)
        self.unknown2 = 0
        self.offset_manager = OffsetManager()
        self.freelist = {}
        self.toc = {}
        if is_new:
            for nbits in xrange(31):
                self.freelist[nbits] = []

            self.freelist[31] = [0]
            header_offset = self._alloc(5)
            assert header_offset == 0, 'header offset is %s, should be zero' % (header_offset,)

    @property
    def offsets(self):
        offset_list = [None] * (self.offset_manager.largestBlockNum() + 1)
        for k, v in self.offset_manager.iteritems():
            offset_list[k] = v

        return offset_list

    @classmethod
    def open(cls, fileobj):
        header = fileobj.read(36)
        if len(header) < 36:
            raise DsStoreFileReadError("can't read header")
        magic1, magic2, offset1, size, offset2, unknown = struct.unpack('>I 4s III 16s', header)
        if not (magic1 == cls.MAGIC1 and magic2 == cls.MAGIC2 and offset1 == offset2):
            raise DsStoreFileReadError('header magic or offset mismatch')
        self = cls(fileobj, unknown=unknown, is_new=False)
        root_block = self.getBlock(offset1, size)
        offset_count, unknown2 = root_block.read(8, '>II')
        self.unknown2 = unknown2
        offset_list = []
        while offset_count > 0:
            offset_list += list(root_block.read(1024, '>256I'))
            offset_count -= 256

        self.offset_manager = OffsetManager(offset_list)
        toc_count = root_block.readInt()
        for i in xrange(toc_count):
            l = root_block.read(1, '>B')
            name = root_block.read(l)
            val = root_block.readInt()
            self.toc[name] = val

        for nbits in xrange(32):
            block_count = root_block.readInt()
            format = '>%dI' % (block_count,)
            self.freelist[nbits] = list(struct.unpack(format, root_block.read(4 * block_count)))

        return self

    def close(self):
        if self.fileobj:
            self.fileobj.close()
            self.fileobj = None

    def read(self, pos, l):
        self.fileobj.seek(pos + self.fudge)
        data = self.fileobj.read(l)
        assert len(data) == l, 'wanted to read %s bytes; got %s' % (l, len(data))
        return data

    def write(self, what, pos):
        fudgedpos = pos + self.fudge
        self.fileobj.seek(fudgedpos)
        self.fileobj.write(what)
        newpos = self.fileobj.tell()
        assert newpos == fudgedpos + len(what), 'newpos %s != fudgedpos (%s) + len(what) %s' % (newpos, fudgedpos, len(what))

    def blockOffset(self, block_num):
        try:
            addr = self.offset_manager[block_num]
        except KeyError:
            raise DsStoreException('Block %s not allocated' % (block_num,))

        offset, nbits = offset_and_nbits_from_addr(addr)
        return (offset, 1 << nbits)

    def buddy(self, offset, nbits):
        return offset ^ 1 << nbits

    def allocate(self, bytes, block_num = None):
        if block_num is None:
            block_num = self.offset_manager.findNextBlockNum()
        nbits = 5
        while bytes > 1 << nbits:
            nbits += 1

        if block_num in self.offset_manager:
            addr = self.offset_manager[block_num]
            offset, width = offset_and_nbits_from_addr(addr)
            if width == nbits:
                return block_num
            self._free(offset, width)
            self.offset_manager[block_num] = None
        offset = self._alloc(nbits)
        addr = offset | nbits
        self.offset_manager[block_num] = addr
        return block_num

    def free(self, block_num):
        addr = self.offset_manager[block_num]
        if addr:
            self._free(*offset_and_nbits_from_addr(addr))
        del self.offset_manager[block_num]

    def _alloc(self, nbits):
        freelist = self.freelist[nbits]
        if freelist:
            block = freelist[0]
            del freelist[0]
            return block
        else:
            offset = self._alloc(nbits + 1)
            other = self.buddy(offset, nbits)
            self._free(other, nbits)
            return offset

    def _free(self, offset, nbits):
        buddy = self.buddy(offset, nbits)
        freelist = self.freelist[nbits]
        if buddy in freelist:
            freelist.remove(buddy)
            self._free(offset & buddy, nbits + 1)
        else:
            freelist.append(offset)
            freelist.sort()

    def listBlocks(self, verbose = False):

        def str_of_use(use_tuple):
            return '%s (%s)' % use_tuple

        byaddr = {}
        byaddr[0] = [(5, 'file header')]
        for block_num, addr in self.offset_manager.iteritems():
            offset, nbits = offset_and_nbits_from_addr(addr)
            if verbose:
                print 'addr 0x%08x -> 0x%08x of bitwidth %2s (size 0x%08x)' % (addr,
                 offset,
                 nbits,
                 1 << nbits)
            desc = 'infoless'
            if verbose:
                try:
                    block = self.blockByNumber(block_num)
                except AssertionError as e:
                    print 'block %s at 0x%08x raised %r' % (block_num, addr, e)
                    continue

                ptr = block.readInt()
                nvalues = block.readInt()
                if block_num == 1:
                    root_node = ptr
                    height = nvalues
                    nrecs = block.readInt()
                    nnodes = block.readInt()
                    block_size = block.readInt()
                    desc = 'root_node %s, height %s, %s records, %s nodes, 0x%08x block size' % (root_node,
                     height,
                     nrecs,
                     nnodes,
                     block_size)
                elif ptr:
                    block.seek(0)
                    try:
                        values, pointers = block.readBtreeNode()
                        assert ptr in pointers, 'separate pointer not in pointer list'
                        assert nvalues == len(values), "value count doesn't match #values we got back"
                        desc = '%s values, %s pointers: %s' % (nvalues, len(pointers), pointers)
                    except DsStoreException:
                        desc = '%s values, 1st pointer %s BORKED' % (nvalues, ptr)

                else:
                    desc = '%s values, no pointers' % (nvalues,)
                if block_num == 0:
                    desc = 'root block, len offsets: %s, unknown2 = %s' % (ptr, nvalues)
            use_tuple = (nbits, 'blkid %s: %s' % (block_num, desc))
            if offset not in byaddr:
                byaddr[offset] = []
            byaddr[offset].append(use_tuple)

        for nbits in self.freelist.iterkeys():
            for offset in self.freelist[nbits]:
                if offset not in byaddr:
                    byaddr[offset] = []
                byaddr[offset].append((nbits, 'free'))

        gaps = overlaps = 0
        offsets = sorted(byaddr.keys())
        offset = 0
        for next_offset in offsets:
            if next_offset > offset:
                if verbose:
                    print '... %s bytes unaccounted for' % (next_offset - offset,)
                gaps += 1
            uses = byaddr[next_offset]
            if verbose:
                print '%08x %s' % (next_offset, ', '.join([ str_of_use(x) for x in uses ]))
            if len(uses) > 1:
                overlaps += 1
            nbits = uses[0][0]
            offset = next_offset + 1 << nbits

        return gaps == 0 and overlaps == 0

    def getBlock(self, offset, size):
        return ReadBlock(self, offset, size)

    def blockByNumber(self, num, write = False):
        try:
            addr = self.offset_manager[num]
        except IndexError:
            raise DsStoreException('No block found for block number %s' % (num,))

        offset, nbits = offset_and_nbits_from_addr(addr)
        assert nbits, 'nbits is zero'
        l = 1 << nbits
        if not write:
            return ReadBlock(self, offset, l)
        else:
            return WriteBlock(self, offset, l)

    def freeBtreeNode(self, block_num):
        block = self.blockByNumber(block_num)
        if block.readInt() != 0:
            block.seek(0)
            pointers = block.readBtreeNode()[1]
            for pointer in pointers:
                self.freeBtreeNode(pointer)

        self.free(block_num)

    def getBtreeRootBlock(self):
        block_num = self.toc['DSDB']
        return self.blockByNumber(block_num).read(20, '>IIIII')

    def getDsdbEntries(self, verbose = False):
        retval = []
        root_node, height, nrecs, nnodes, block_size = self.getBtreeRootBlock()
        n, h = self.traverse_btree(root_node, retval)
        if n != nrecs:
            if verbose:
                print 'number of records (%s) != n (%s) from BTree traversal' % (nrecs, n)
        if nnodes + 2 != self.offset_manager.numBlocksUsed():
            if verbose:
                print 'number of nodes (%s) != number of blocks - 2 (%s)' % (nnodes, self.offset_manager.numBlocksUsed() - 2)
        if h != height:
            if verbose:
                print 'height (%s) != h (%s) from BTree traversal' % (height, h)
        return retval

    def putDsdbEntries(self, recs):
        if 'DSDB' in self.toc:
            tocblock = self.toc['DSDB']
            values = self.getBtreeRootBlock()
            old_root_block = values[0]
            pagesize = values[4]
            self.freeBtreeNode(old_root_block)
        else:
            tocblock = self.allocate(20)
            self.toc['DSDB'] = tocblock
            pagesize = 4096
        reccount = len(recs)
        height = 0
        pagecount = 0
        children = []
        loop_count = 0
        while True:
            loop_count += 1
            if loop_count > max(200, 2 * len(recs)):
                raise DsStoreInfiniteLoopException('loop count is %d, exceeding max, aborting' % (loop_count,))
            if children:
                sizes = [ 4 + rec.byteSize() for rec in recs ]
            else:
                sizes = [ rec.byteSize() for rec in recs ]
            interleaf = partition_sizes(pagesize - 8, sizes)
            new_children = []
            start = 0
            for non in itertools.chain(interleaf, [len(recs)]):
                if start == non and children:
                    new_children.append(children[start])
                    start = non + 1
                    continue
                block_num = self.allocate(pagesize)
                new_children.append(block_num)
                block = self.blockByNumber(block_num, write=True)
                if children:
                    block.writeBtreeNode(recs[start:non], children[start:non + 1])
                elif start == non:
                    bogus = Entry('', 'cmmt', '')
                    block.writeBtreeNode([bogus], [])
                    reccount += 1
                else:
                    block.writeBtreeNode(recs[start:non], [])
                block.close(fill=True)
                start = non + 1
                pagecount += 1

            height += 1
            recs = [ recs[i] for i in interleaf ]
            children = new_children
            assert len(children) == 1 + len(recs), 'children ()%s) != #records (%s) + 1' % (len(children), len(recs))
            if len(children) <= 1:
                break

        assert len(recs) == 0, '#records (%s) != 0' % (len(recs),)
        master_block = self.blockByNumber(tocblock, write=True)
        data = struct.pack('>IIIII', children[0], height - 1, reccount, pagecount, pagesize)
        master_block.write(data)
        master_block.close()

    def traverse_btree(self, node_num, retlist):
        values, pointers = self.blockByNumber(node_num).readBtreeNode()
        count = len(values)
        height = 0
        if pointers:
            assert len(pointers) == len(values) + 1, 'Value count should be one less than pointer count'
            subcount, subheight = self.traverse_btree(pointers[0], retlist)
            count += subcount
            height = max(height, subheight + 1)
            for i in xrange(len(values)):
                retlist.append(values[i])
                subcount, subheight = self.traverse_btree(pointers[i + 1], retlist)
                count += subcount
                height = max(height, subheight + 1)

        else:
            retlist += values
        return (count, height)

    def writeMetadata(self):
        block_num = 0
        size = self.rootBlockSize()
        self.allocate(size, block_num)
        block = self.blockByNumber(block_num, write=True)
        assert len(block) >= size, 'block length %s < size %s' % (len(block), size)
        self.writeRootBlock(self.blockByNumber(block_num, write=True))
        block_offset, block_len = self.blockOffset(block_num)
        self.fileobj.seek(0)
        self.fileobj.write(struct.pack('>I', self.MAGIC1))
        header = struct.pack('>4s III 16s', self.MAGIC2, block_offset, block_len, block_offset, self.unknown)
        self.write(header, 0)
        self.fileobj.flush()

    def rootBlockSize(self):
        size = 8
        if not self.offset_manager:
            offsetcount = 1
        else:
            offsetcount = self.offset_manager.largestBlockNum() + 1
        tail = offsetcount % 256
        if tail:
            offsetcount += 256 - tail
        size += 4 * offsetcount
        size += 4
        for key in self.toc.iterkeys():
            size += 5 + len(key)

        for nbits in xrange(32):
            size += 4 + 4 * len(self.freelist[nbits])

        return size

    def writeRootBlock(self, block):
        len_offsets = self.offset_manager.largestBlockNum() + 1
        block.write(struct.pack('>II', len_offsets, self.unknown2))
        for i in xrange(len_offsets):
            block.write(struct.pack('>I', self.offset_manager.get(i, 0)))

        offsetcount = len_offsets % 256
        if offsetcount > 0:
            block.write('\x00\x00\x00\x00' * (256 - offsetcount))
        tockeys = self.toc.keys()
        tockeys.sort()
        block.write(struct.pack('>I', len(tockeys)))
        for key in tockeys:
            format = '>B%dsI' % (len(key),)
            block.write(struct.pack(format, len(key), key, self.toc[key]))

        for nbits in xrange(32):
            blist = self.freelist[nbits]
            block.write(struct.pack('>I', len(blist)))
            for num in blist:
                block.write(struct.pack('>I', num))

        block.close(fill=True)


class Entry(object):
    TYPES = {'BKGD': 'blob',
     'bwsp': 'blob',
     'cmmt': 'ustr',
     'dilc': 'blob',
     'dscl': 'bool',
     'fwi0': 'blob',
     'fwsw': 'long',
     'fwvh': 'shor',
     'icgo': 'blob',
     'icsp': 'blob',
     'icvo': 'blob',
     'icvp': 'blob',
     'ICVO': 'bool',
     'icvt': 'shor',
     'Iloc': 'blob',
     'info': 'blob',
     'logS': 'comp',
     'lssp': 'blob',
     'lsvo': 'blob',
     'LSVO': 'bool',
     'lsvp': 'blob',
     'lsvP': 'blob',
     'lsvt': 'shor',
     'moDD': 'dutc',
     'pict': 'blob',
     'vstl': 'type'}

    def __init__(self, filename, structure_id, data, data_type = None):
        self.filename = filename
        self.structure_id = structure_id
        try:
            expected_data_type = self.TYPES[self.structure_id]
        except KeyError:
            if data_type is None:
                raise DsStoreException('Unsupported structure id %s' % (self.structure_id,))
            TRACE('new structure id %s: data type is %s', self.structure_id, data_type)
            self.data_type = data_type
        else:
            if data_type and data_type != expected_data_type:
                raise DsStoreException('Expected data type %s for structure id %s; got %s instead' % (expected_data_type, self.structure_id, data_type))
            self.data_type = expected_data_type

        if self.data_type in ('blob', 'comp', 'dutc', 'type', 'ustr'):
            self.data = data
            if self.data_type == 'type':
                if len(self.data) != 4:
                    raise DsStoreException("structure id %s has data type 'type' but has length %d != 4" % (self.structure_id, len(self.data)))
            if self.data_type in ('comp', 'dutc'):
                if len(self.data) != 8:
                    raise DsStoreException("structure id %s has data type '%s' but has length %d != 8" % (self.structure_id, self.data_type, len(self.data)))
        elif self.data_type in ('shor', 'long'):
            self.data = int(data)
        elif self.data_type == 'bool':
            self.data = bool(data)
        else:
            raise DsStoreException('Unknown data type %s' % (self.data_type,))

    def __repr__(self):
        value = self.data
        if self.data_type in ('blob', 'comp', 'dutc'):
            value = '<%s bytes>' % (len(value),)
        elif self.data_type == 'ustr':
            if len(value) <= 20:
                value = repr(value)
            else:
                value = '%s:%r...' % (len(value), value[:10])
        else:
            value = repr(value)
        return '<Entry for %r: %s/%s: %s>' % (self.filename,
         self.structure_id,
         self.data_type,
         value)

    def __cmp__(self, other):
        return cmp(self.filename.lower(), other.filename.lower()) or cmp(self.structure_id, other.structure_id)

    def __hash__(self):
        return hash((self.filename, self.structure_id))

    @classmethod
    def readEntry(cls, block):
        filename = cls.readUtf16String(block)
        structure_id = block.read(4)
        data_type = block.read(4)
        if data_type == 'bool':
            value = block.read(1, '>B')
        elif data_type in ('long', 'shor'):
            value = block.readInt()
        elif data_type == 'blob':
            l = block.readInt()
            value = block.read(l)
        elif data_type == 'ustr':
            value = cls.readUtf16String(block)
        elif data_type == 'type':
            value = block.read(4)
        elif data_type in ('comp', 'dutc'):
            value = block.read(8)
        else:
            raise DsStoreException('Unknown data type %s for structure id %s' % (data_type, structure_id))
        return cls(filename, structure_id, value, data_type=data_type)

    @classmethod
    def readUtf16String(cls, block):
        l = block.readInt()
        raw_str = block.read(2 * l)
        return raw_str.decode('utf-16be')

    def byteSize(self):
        size = len(self.filename) * 2 + 12
        if self.data_type in ('long', 'shor', 'type'):
            size += 4
        elif self.data_type in ('comp', 'dutc'):
            size += 8
        elif self.data_type == 'bool':
            size += 1
        elif self.data_type == 'blob':
            size += 4 + len(self.data)
        elif self.data_type == 'ustr':
            size += 4 + 2 * len(self.data)
        else:
            raise DsStoreException('Unknown data type %s' % (self.data_type,))
        return size

    def asByteString(self):
        pieces = []
        name = self.filename.encode('utf-16be')
        pieces.append(struct.pack('>I', len(self.filename)))
        pieces.append(name)
        pieces.append(self.structure_id)
        pieces.append(self.data_type)
        if self.data_type in ('long', 'shor'):
            pieces.append(struct.pack('>I', self.data))
        elif self.data_type == 'bool':
            pieces.append(struct.pack('>B', self.data))
        elif self.data_type == 'blob':
            pieces.append(struct.pack('>I', len(self.data)))
            pieces.append(self.data)
        elif self.data_type == 'ustr':
            pieces.append(struct.pack('>I', len(self.data)))
            pieces.append(self.data.encode('utf-16be'))
        elif self.data_type in ('comp', 'dutc', 'type'):
            pieces.append(self.data)
        else:
            raise DsStoreException('Unknown data type %s' % (self.data_type,))
        return ''.join(pieces)


def partition_sizes(maximum, sizes):
    total = sum(sizes)
    if total <= maximum:
        return []
    ejecta = []
    bcount = math.ceil(total / float(maximum))
    target = total / bcount
    n = 0
    while True:
        bsum = 0
        while n < len(sizes) and bsum < target and bsum + sizes[n] < maximum:
            bsum += sizes[n]
            n += 1

        if n >= len(sizes):
            return ejecta
        ejecta.append(n)
        n += 1


def writeDsdbEntries(ds_path, recs):
    entries = sorted(set(recs))
    f = open(ds_path, 'wb+')
    store = BuddyAllocator(f)
    store.putDsdbEntries(entries)
    store.writeMetadata()
    return store
