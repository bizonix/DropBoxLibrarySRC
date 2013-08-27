#Embedded file name: dropbox/sync_engine/sync_engine_util.py
import zlib
from client_api.hashing import dropbox_hash
from dropbox.trace import unhandled_exc_handler, report_bad_assumption
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError
import dropbox.librsync

class SyncEngineStoppedError(Exception):
    pass


class AttributeMergeError(Exception):
    pass


class BlockContentsError(Exception):
    pass


class BlockContentsNotFoundError(BlockContentsError):
    pass


class BlockContentsBadDataError(BlockContentsError):
    pass


def add_sig_and_check(hashes_to_prune, sigstore, sha1_digest, s):
    try:
        sig, size = dropbox.librsync.sig(s), len(s)
        old_row = sigstore.set_if_new(sha1_digest, sig, size)
        if not old_row:
            hashes_to_prune.add(sha1_digest)
        elif not (old_row.size == size and old_row.sig == sig):
            report_bad_assumption('Bad info in sigstore!!')
    except:
        unhandled_exc_handler()


def block_cache_contents(fs, cache_path, _hash):
    fn = cache_path.join(unicode(_hash))
    try:
        with fs.open(fn) as f:
            s = f.read()
    except FileNotFoundError:
        pass
    except Exception as e:
        print e
        unhandled_exc_handler()
    else:
        try:
            decompressed = zlib.decompress(s)
            _decompressed_hash = dropbox_hash(decompressed)
            if _decompressed_hash != _hash:
                raise Exception('Hashed block file contents are incorrect! %r vs %r' % (_decompressed_hash, _hash))
        except Exception as e:
            print e
            try:
                fs.remove(fn)
            except Exception:
                unhandled_exc_handler()

            raise BlockContentsBadDataError('Data in block cache was invalid for hash %r, %r' % (_hash, e))
        else:
            return decompressed

    try:
        fs.remove(fn)
    except FileNotFoundError:
        pass
    except Exception:
        unhandled_exc_handler()

    raise BlockContentsNotFoundError('Contents of %s not available' % (_hash,))
