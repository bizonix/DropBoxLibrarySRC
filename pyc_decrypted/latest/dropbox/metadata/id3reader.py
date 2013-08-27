#Embedded file name: dropbox/metadata/id3reader.py
__version__ = '1.53.20070415'
import struct
import sys
import zlib
_encodings = ['iso8859-1',
 'utf-16',
 'utf-16be',
 'utf-8']
_simpleDataMapping = {'album': ('TALB',
           'TAL',
           'v1album',
           'TOAL'),
 'artist': ('TPE1',
            'TP1',
            'v1performer',
            'TOPE'),
 'title': ('TIT2', 'TT2', 'v1title'),
 'track': ('TRCK', 'TRK', 'v1track'),
 'year': ('TYER', 'TYE', 'v1year'),
 'genre': ('TCON', 'TCO', 'v1genre'),
 'comment': ('COMM', 'COM', 'v1comment')}
try:
    (True, False)
except NameError:
    True, False = (1 == 1, 1 == 0)

_t = False

def _trace(msg):
    print msg


_c = False
_features = {}

def _coverage(feat):
    _features[feat] = _features.setdefault(feat, 0) + 1


def _safestr(s):
    try:
        return unicode(s).encode(sys.getdefaultencoding())
    except UnicodeError:
        return '?: ' + repr(s)


_genres = ['Blues',
 'Classic Rock',
 'Country',
 'Dance',
 'Disco',
 'Funk',
 'Grunge',
 'Hip - Hop',
 'Jazz',
 'Metal',
 'New Age',
 'Oldies',
 'Other',
 'Pop',
 'R&B',
 'Rap',
 'Reggae',
 'Rock',
 'Techno',
 'Industrial',
 'Alternative',
 'Ska',
 'Death Metal',
 'Pranks',
 'Soundtrack',
 'Euro - Techno',
 'Ambient',
 'Trip - Hop',
 'Vocal',
 'Jazz + Funk',
 'Fusion',
 'Trance',
 'Classical',
 'Instrumental',
 'Acid',
 'House',
 'Game',
 'Sound Clip',
 'Gospel',
 'Noise',
 'Alt Rock',
 'Bass',
 'Soul',
 'Punk',
 'Space',
 'Meditative',
 'Instrumental Pop',
 'Instrumental Rock',
 'Ethnic',
 'Gothic',
 'Darkwave',
 'Techno - Industrial',
 'Electronic',
 'Pop - Folk',
 'Eurodance',
 'Dream',
 'Southern Rock',
 'Comedy',
 'Cult',
 'Gangsta Rap',
 'Top 40',
 'Christian Rap',
 'Pop / Funk',
 'Jungle',
 'Native American',
 'Cabaret',
 'New Wave',
 'Psychedelic',
 'Rave',
 'Showtunes',
 'Trailer',
 'Lo - Fi',
 'Tribal',
 'Acid Punk',
 'Acid Jazz',
 'Polka',
 'Retro',
 'Musical',
 'Rock & Roll',
 'Hard Rock',
 'Folk',
 'Folk / Rock',
 'National Folk',
 'Swing',
 'Fast - Fusion',
 'Bebob',
 'Latin',
 'Revival',
 'Celtic',
 'Bluegrass',
 'Avantgarde',
 'Gothic Rock',
 'Progressive Rock',
 'Psychedelic Rock',
 'Symphonic Rock',
 'Slow Rock',
 'Big Band',
 'Chorus',
 'Easy Listening',
 'Acoustic',
 'Humour',
 'Speech',
 'Chanson',
 'Opera',
 'Chamber Music',
 'Sonata',
 'Symphony',
 'Booty Bass',
 'Primus',
 'Porn Groove',
 'Satire',
 'Slow Jam',
 'Club',
 'Tango',
 'Samba',
 'Folklore',
 'Ballad',
 'Power Ballad',
 'Rhythmic Soul',
 'Freestyle',
 'Duet',
 'Punk Rock',
 'Drum Solo',
 'A Cappella',
 'Euro - House',
 'Dance Hall',
 'Goa',
 'Drum & Bass',
 'Club - House',
 'Hardcore',
 'Terror',
 'Indie',
 'BritPop',
 'Negerpunk',
 'Polsk Punk',
 'Beat',
 'Christian Gangsta Rap',
 'Heavy Metal',
 'Black Metal',
 'Crossover',
 'Contemporary Christian',
 'Christian Rock',
 'Merengue',
 'Salsa',
 'Thrash Metal',
 'Anime',
 'JPop',
 'Synthpop']
LANGUAGE_CODES = ['aar',
 'abk',
 'ace',
 'ach',
 'ada',
 'ady',
 'afa',
 'afh',
 'afr',
 'ain',
 'aka',
 'akk',
 'alb',
 'ale',
 'alg',
 'alt',
 'amh',
 'ang',
 'anp',
 'apa',
 'ara',
 'arc',
 'arg',
 'arm',
 'arn',
 'arp',
 'art',
 'arw',
 'asm',
 'ast',
 'ath',
 'aus',
 'ava',
 'ave',
 'awa',
 'aym',
 'aze',
 'bad',
 'bai',
 'bak',
 'bal',
 'bam',
 'ban',
 'baq',
 'bas',
 'bat',
 'bej',
 'bel',
 'bem',
 'ben',
 'ber',
 'bho',
 'bih',
 'bik',
 'bin',
 'bis',
 'bla',
 'bnt',
 'bos',
 'bra',
 'bre',
 'btk',
 'bua',
 'bug',
 'bul',
 'bur',
 'byn',
 'cad',
 'cai',
 'car',
 'cat',
 'cau',
 'ceb',
 'cel',
 'cha',
 'chb',
 'che',
 'chg',
 'chi',
 'chk',
 'chm',
 'chn',
 'cho',
 'chp',
 'chr',
 'chu',
 'chv',
 'chy',
 'cmc',
 'cop',
 'cor',
 'cos',
 'cpe',
 'cpf',
 'cpp',
 'cre',
 'crh',
 'crp',
 'csb',
 'cus',
 'cze',
 'dak',
 'dan',
 'dar',
 'day',
 'del',
 'den',
 'dgr',
 'din',
 'div',
 'doi',
 'dra',
 'dsb',
 'dua',
 'dum',
 'dut',
 'dyu',
 'dzo',
 'efi',
 'egy',
 'eka',
 'elx',
 'eng',
 'enm',
 'epo',
 'est',
 'ewe',
 'ewo',
 'fan',
 'fao',
 'fat',
 'fij',
 'fil',
 'fin',
 'fiu',
 'fon',
 'fre',
 'frm',
 'fro',
 'frr',
 'frs',
 'fry',
 'ful',
 'fur',
 'gaa',
 'gay',
 'gba',
 'gem',
 'geo',
 'ger',
 'gez',
 'gil',
 'gla',
 'gle',
 'glg',
 'glv',
 'gmh',
 'goh',
 'gon',
 'gor',
 'got',
 'grb',
 'grc',
 'gre',
 'grn',
 'gsw',
 'guj',
 'gwi',
 'hai',
 'hat',
 'hau',
 'haw',
 'heb',
 'her',
 'hil',
 'him',
 'hin',
 'hit',
 'hmn',
 'hmo',
 'hrv',
 'hsb',
 'hun',
 'hup',
 'iba',
 'ibo',
 'ice',
 'ido',
 'iii',
 'ijo',
 'iku',
 'ile',
 'ilo',
 'ina',
 'inc',
 'ind',
 'ine',
 'inh',
 'ipk',
 'ira',
 'iro',
 'ita',
 'jav',
 'jbo',
 'jpn',
 'jpr',
 'jrb',
 'kaa',
 'kab',
 'kac',
 'kal',
 'kam',
 'kan',
 'kar',
 'kas',
 'kau',
 'kaw',
 'kaz',
 'kbd',
 'kha',
 'khi',
 'khm',
 'kho',
 'kik',
 'kin',
 'kir',
 'kmb',
 'kok',
 'kom',
 'kon',
 'kor',
 'kos',
 'kpe',
 'krc',
 'krl',
 'kro',
 'kru',
 'kua',
 'kum',
 'kur',
 'kut',
 'lad',
 'lah',
 'lam',
 'lao',
 'lat',
 'lav',
 'lez',
 'lim',
 'lin',
 'lit',
 'lol',
 'loz',
 'ltz',
 'lua',
 'lub',
 'lug',
 'lui',
 'lun',
 'luo',
 'lus',
 'mac',
 'mad',
 'mag',
 'mah',
 'mai',
 'mak',
 'mal',
 'man',
 'mao',
 'map',
 'mar',
 'mas',
 'may',
 'mdf',
 'mdr',
 'men',
 'mga',
 'mic',
 'min',
 'mis',
 'mkh',
 'mlg',
 'mlt',
 'mnc',
 'mni',
 'mno',
 'moh',
 'mon',
 'mos',
 'mul',
 'mun',
 'mus',
 'mwl',
 'mwr',
 'myn',
 'myv',
 'nah',
 'nai',
 'nap',
 'nau',
 'nav',
 'nbl',
 'nde',
 'ndo',
 'nds',
 'nep',
 'new',
 'nia',
 'nic',
 'niu',
 'nno',
 'nob',
 'nog',
 'non',
 'nor',
 'nqo',
 'nso',
 'nub',
 'nwc',
 'nya',
 'nym',
 'nyn',
 'nyo',
 'nzi',
 'oci',
 'oji',
 'ori',
 'orm',
 'osa',
 'oss',
 'ota',
 'oto',
 'paa',
 'pag',
 'pal',
 'pam',
 'pan',
 'pap',
 'pau',
 'peo',
 'per',
 'phi',
 'phn',
 'pli',
 'pol',
 'pon',
 'por',
 'pra',
 'pro',
 'pus',
 'qaa',
 'que',
 'raj',
 'rap',
 'rar',
 'roa',
 'roh',
 'rom',
 'rum',
 'run',
 'rup',
 'rus',
 'sad',
 'sag',
 'sah',
 'sai',
 'sal',
 'sam',
 'san',
 'sas',
 'sat',
 'scn',
 'sco',
 'sel',
 'sem',
 'sga',
 'sgn',
 'shn',
 'sid',
 'sin',
 'sio',
 'sit',
 'sla',
 'slo',
 'slv',
 'sma',
 'sme',
 'smi',
 'smj',
 'smn',
 'smo',
 'sms',
 'sna',
 'snd',
 'snk',
 'sog',
 'som',
 'son',
 'sot',
 'spa',
 'srd',
 'srn',
 'srp',
 'srr',
 'ssa',
 'ssw',
 'suk',
 'sun',
 'sus',
 'sux',
 'swa',
 'swe',
 'syc',
 'syr',
 'tah',
 'tai',
 'tam',
 'tat',
 'tel',
 'tem',
 'ter',
 'tet',
 'tgk',
 'tgl',
 'tha',
 'tib',
 'tig',
 'tir',
 'tiv',
 'tkl',
 'tlh',
 'tli',
 'tmh',
 'tog',
 'ton',
 'tpi',
 'tsi',
 'tsn',
 'tso',
 'tuk',
 'tum',
 'tup',
 'tur',
 'tut',
 'tvl',
 'twi',
 'tyv',
 'udm',
 'uga',
 'uig',
 'ukr',
 'umb',
 'und',
 'urd',
 'uzb',
 'vai',
 'ven',
 'vie',
 'vol',
 'vot',
 'wak',
 'wal',
 'war',
 'was',
 'wel',
 'wen',
 'wln',
 'wol',
 'xal',
 'xho',
 'yao',
 'yap',
 'yid',
 'yor',
 'ypk',
 'zap',
 'zbl',
 'zen',
 'zha',
 'znd',
 'zul',
 'zun',
 'zxx',
 'zza']

class Id3Error(Exception):
    pass


class _Header():

    def __init__(self):
        self.majorVersion = 0
        self.revision = 0
        self.flags = 0
        self.size = 0
        self.bUnsynchronized = False
        self.bExperimental = False
        self.bFooter = False

    def __str__(self):
        return str(self.__dict__)


class _Frame():

    def __init__(self):
        self.id = ''
        self.size = 0
        self.flags = 0
        self.rawData = ''
        self.bTagAlterPreserve = False
        self.bFileAlterPreserve = False
        self.bReadOnly = False
        self.bCompressed = False
        self.bEncrypted = False
        self.bInGroup = False

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def _interpret(self):
        if len(self.rawData) == 0:
            return
        if self.bCompressed:
            self.rawData = zlib.decompress(self.rawData)
        if self.id == 'WXXX':
            self.value = 'WXXX\x01' + self.rawData
        elif self.id == 'APIC':
            self.value = 'APIC\x01' + self.rawData
        elif self.id[0] == 'T' or self.id[0] == 'W':
            self.value = binary_data_to_string(self.rawData)
        elif self.id == 'CDM':
            if self.rawData[0] == 'z':
                self.rawData = zlib.decompress(self.rawData[5:])
            else:
                raise Id3Error('Unknown CDM compression: %02x' % self.rawData[0])
        elif self.id in _simpleDataMapping['comment']:
            self.value = binary_data_to_string(str(self.rawData))
        else:
            self.value = binary_data_to_string(str(self.rawData))


class Reader():

    def __init__(self, file):
        self.file = file
        self.header = None
        self.frames = {}
        self.allFrames = []
        self.bytesLeft = 0
        self.padbytes = ''
        bCloseFile = False
        if isinstance(self.file, (type(''), type(u''))):
            self.file = open(self.file, 'rb')
            bCloseFile = True
        self._readId3()
        if bCloseFile:
            self.file.close()

    def _readBytes(self, num, desc = ''):
        if num > self.bytesLeft:
            raise Id3Error('Long read (%s): (%d > %d)' % (desc, num, self.bytesLeft))
        bytes = self.file.read(num)
        self.bytesLeft -= num
        if len(bytes) < num:
            raise Id3Error('Short read (%s): (%d < %d)' % (desc, len(bytes), num))
        if self.header.bUnsynchronized:
            nUnsync = 0
            i = 0
            while True:
                i = bytes.find('\xff\x00', i)
                if i == -1:
                    break
                nUnsync += 1
                bytes = bytes[:i + 1] + bytes[i + 2:]
                bytes += self.file.read(1)
                self.bytesLeft -= 1
                i += 1

        return bytes

    def _unreadBytes(self, num):
        self.file.seek(-num, 1)
        self.bytesLeft += num

    def _getSyncSafeInt(self, bytes):
        assert len(bytes) == 4
        if type(bytes) == type(''):
            bytes = [ ord(c) for c in bytes ]
        return (bytes[0] << 21) + (bytes[1] << 14) + (bytes[2] << 7) + bytes[3]

    def _getInteger(self, bytes):
        i = 0
        if type(bytes) == type(''):
            bytes = [ ord(c) for c in bytes ]
        for b in bytes:
            i = i * 256 + b

        return i

    def _addV1Frame(self, id, rawData):
        if id == 'v1genre':
            assert len(rawData) == 1
            nGenre = ord(rawData)
            try:
                value = _genres[nGenre]
            except IndexError:
                value = '(%d)' % nGenre

        else:
            value = rawData.strip(' \t\r\n').split('\x00')[0]
        if value:
            frame = _Frame()
            frame.id = id
            frame.rawData = rawData
            frame.value = value
            self.frames[id] = frame
            self.allFrames.append(frame)

    def _pass(self):
        pass

    def _readId3(self):
        header = self.file.read(10)
        if len(header) < 10:
            return
        hstuff = struct.unpack('!3sBBBBBBB', header)
        if hstuff[0] != 'ID3':
            self._readId3v1()
            return
        self.header = _Header()
        self.header.majorVersion = hstuff[1]
        self.header.revision = hstuff[2]
        self.header.flags = hstuff[3]
        self.header.size = self._getSyncSafeInt(hstuff[4:8])
        self.bytesLeft = self.header.size
        self._readExtHeader = self._pass
        if self.header.majorVersion == 2:
            self._readFrame = self._readFrame_rev2
        elif self.header.majorVersion == 3:
            self._readFrame = self._readFrame_rev3
        elif self.header.majorVersion == 4:
            self._readFrame = self._readFrame_rev4
        else:
            raise Id3Error('Unsupported major version: %d' % self.header.majorVersion)
        self._interpretFlags()
        self._readExtHeader()
        while self.bytesLeft > 0:
            frame = self._readFrame()
            if frame:
                frame._interpret()
                try:
                    insert = not (frame.id == 'APIC' and frame.id in self.frames and ord(frame.rawData[frame.rawData.index('\x00', 1) + 1]) != 3)
                except (IndexError, ValueError):
                    insert = False

                if insert:
                    self.frames[frame.id] = frame
                    self.allFrames.append(frame)
            else:
                break

    def _interpretFlags(self):
        if self.header.flags & 128:
            self.header.bUnsynchronized = True
        if self.header.majorVersion == 2:
            if self.header.flags & 64:
                self.header.bCompressed = True
        if self.header.majorVersion >= 3:
            if self.header.flags & 64:
                if self.header.majorVersion == 3:
                    self._readExtHeader = self._readExtHeader_rev3
                else:
                    self._readExtHeader = self._readExtHeader_rev4
            if self.header.flags & 32:
                self.header.bExperimental = True
        if self.header.majorVersion >= 4:
            if self.header.flags & 16:
                self.header.bFooter = True

    def _readExtHeader_rev3(self):
        size = self._getInteger(self._readBytes(4, 'rev3ehlen'))
        self._readBytes(size, 'rev3ehdata')

    def _readExtHeader_rev4(self):
        size = self._getSyncSafeInt(self._readBytes(4, 'rev4ehlen'))
        self._readBytes(size - 4, 'rev4ehdata')

    def _readId3v1(self):
        self.file.seek(0, 2)
        if self.file.tell() < 128:
            return
        self.file.seek(-128, 2)
        tag = self.file.read(128)
        if len(tag) != 128:
            return
            raise Exception('No id3 info')
        if tag[0:3] != 'TAG':
            return
            raise Exception('No id3 info')
        self.header = _Header()
        self.header.majorVersion = 1
        self.header.revision = 0
        self._addV1Frame('v1title', tag[3:33])
        self._addV1Frame('v1performer', tag[33:63])
        self._addV1Frame('v1album', tag[63:93])
        self._addV1Frame('v1year', tag[93:97])
        self._addV1Frame('v1comment', tag[97:127])
        self._addV1Frame('v1genre', tag[127])
        if tag[125] == '\x00' and tag[126] != '\x00':
            self.header.revision = 1
            self._addV1Frame('v1track', str(ord(tag[126])))

    _validIdChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    def _isValidId(self, id):
        for c in id:
            if c not in self._validIdChars:
                return False

        return True

    def _readFrame_rev2(self):
        if self.bytesLeft < 6:
            return None
        id = self._readBytes(3, 'rev2id')
        if len(id) < 3 or not self._isValidId(id):
            self._unreadBytes(len(id))
            return None
        hstuff = struct.unpack('!BBB', self._readBytes(3, 'rev2len'))
        frame = _Frame()
        frame.id = id
        frame.size = self._getInteger(hstuff[0:3])
        frame.rawData = self._readBytes(frame.size, 'rev2data')
        return frame

    def _readFrame_rev3(self):
        if self.bytesLeft < 10:
            return None
        id = self._readBytes(4, 'rev3id')
        if len(id) < 4 or not self._isValidId(id):
            self._unreadBytes(len(id))
            return None
        hstuff = struct.unpack('!BBBBh', self._readBytes(6, 'rev3head'))
        frame = _Frame()
        frame.id = id
        frame.size = self._getInteger(hstuff[0:4])
        cbData = frame.size
        frame.flags = hstuff[4]
        frame.bTagAlterPreserve = frame.flags & 32768 != 0
        frame.bFileAlterPreserve = frame.flags & 16384 != 0
        frame.bReadOnly = frame.flags & 8192 != 0
        frame.bCompressed = frame.flags & 128 != 0
        if frame.bCompressed:
            frame.decompressedSize = self._getInteger(self._readBytes(4, 'decompsize'))
            cbData -= 4
        frame.bEncrypted = frame.flags & 64 != 0
        if frame.bEncrypted:
            frame.encryptionMethod = self._readBytes(1, 'encrmethod')
            cbData -= 1
        frame.bInGroup = frame.flags & 32 != 0
        if frame.bInGroup:
            frame.groupid = self._readBytes(1, 'groupid')
            cbData -= 1
        frame.rawData = self._readBytes(cbData, 'rev3data')
        return frame

    def _readFrame_rev4(self):
        if self.bytesLeft < 10:
            return None
        id = self._readBytes(4, 'rev4id')
        if len(id) < 4 or not self._isValidId(id):
            self._unreadBytes(len(id))
            return None
        hstuff = struct.unpack('!BBBBh', self._readBytes(6, 'rev4head'))
        frame = _Frame()
        frame.id = id
        frame.size = self._getSyncSafeInt(hstuff[0:4])
        cbData = frame.size
        frame.flags = hstuff[4]
        frame.bTagAlterPreserve = frame.flags & 16384 != 0
        frame.bFileAlterPreserve = frame.flags & 8192 != 0
        frame.bReadOnly = frame.flags & 4096 != 0
        frame.bInGroup = frame.flags & 64 != 0
        if frame.bInGroup:
            frame.groupid = self._readBytes(1, 'groupid')
            cbData -= 1
        frame.bCompressed = frame.flags & 8 != 0
        if frame.bCompressed:
            pass
        frame.bEncrypted = frame.flags & 4 != 0
        if frame.bEncrypted:
            frame.encryptionMethod = self._readBytes(1, 'encrmethod')
            cbData -= 1
        frame.bUnsynchronized = frame.flags & 2 != 0
        if frame.bUnsynchronized:
            pass
        if frame.flags & 1:
            frame.datalen = self._getSyncSafeInt(self._readBytes(4, 'datalen'))
            cbData -= 4
        frame.rawData = self._readBytes(cbData, 'rev3data')
        return frame

    def getValue(self, id):
        if id in self.frames:
            if hasattr(self.frames[id], 'value'):
                return self.frames[id].value
        if id in _simpleDataMapping:
            for id2 in _simpleDataMapping[id]:
                v = self.getValue(id2)
                if v:
                    if id == 'genre':
                        if v.isdigit():
                            try:
                                return _genres[int(v)]
                            except:
                                return u'unknown'

                    return v

    def getAllData(self):
        toret = dict([ (id, self.getValue(id)) for id in self.frames ])
        for key in _simpleDataMapping:
            v = self.getValue(key)
            if v:
                toret[key] = v

        return toret

    def getRawData(self, id):
        if id in self.frames:
            return self.frames[id].rawData

    def dump(self):
        import pprint
        print 'Header:'
        print self.header
        print 'Frames:'
        for fr in self.allFrames:
            if len(fr.rawData) > 30:
                fr.rawData = fr.rawData[:30]

        pprint.pprint(self.allFrames)
        for fr in self.allFrames:
            if hasattr(fr, 'value'):
                print '%s: %s' % (fr.id, _safestr(fr.value))
            else:
                print '%s= %s' % (fr.id, _safestr(fr.rawData))

        for label in _simpleDataMapping.keys():
            v = self.getValue(label)
            if v:
                print 'Label %s: %s' % (label, _safestr(v))

    def dumpCoverage(self):
        feats = _features.keys()
        feats.sort()
        for feat in feats:
            print 'Feature %-12s: %d' % (feat, _features[feat])


def decode_picture_frame(v, offset = 0):
    encoding = ord(v[offset + 0])
    assert 0 <= encoding <= 3
    if encoding == 0:
        delim = '\x00'
    elif encoding < 4:
        delim = '\x00\x00'
    mime_end = v.find('\x00', offset + 1)
    mime = v[offset + 1:mime_end]
    pic_type = v[mime_end + 1]
    desc_end = v.find(delim, mime_end + 2)
    desc = v[mime_end + 2:desc_end].decode(_encodings[encoding])
    data = v[desc_end + len(delim):]
    return dict(((k, v) for k, v in {'mime_type': mime,
     'pic_type': pic_type,
     'description': desc,
     'data': data}.iteritems() if v))


def decode_url_frame(v, offset = 0):
    encoding = ord(v[offset + 0])
    assert 0 <= encoding <= 3
    if encoding == 0:
        delim = '\x00'
    elif encoding < 4:
        delim = '\x00\x00'
    desc, url = v[offset + 1:].split(delim)
    return dict(((k, v) for k, v in {'description': desc.decode(_encodings[encoding]),
     'url': url}.iteritems() if v))


def binary_data_to_string(v):
    if v:
        encoding = ord(v[0])
        if encoding < len(_encodings):
            if encoding > 0 and v[1:4] in LANGUAGE_CODES:
                v = v[4:]
            else:
                v = v[1:]
            if encoding == 0:
                delim = '\x00'
            else:
                delim = '\x00\x00'
            return ''.join((y for y in (x.decode(_encodings[encoding]) for x in v.split(delim)) if y))
    return v


def decode_binary_data(v):
    if v:
        if len(v) >= 4 and v[:5] == 'APIC\x01':
            return decode_picture_frame(v, 5)
        elif len(v) >= 4 and v[:5] == 'WXXX\x01':
            return decode_url_frame(v, 5)
        else:
            return v
    return v


def read_id3(f):
    try:
        return {'id3': Reader(f).getAllData()}
    except Id3Error as e:
        raise ValueError(str(e))


if __name__ == '__main__':
    if len(sys.argv) < 2 or '-?' in sys.argv:
        print 'Give me a filename'
    else:
        id3 = Reader(sys.argv[1])
        id3.dump()
