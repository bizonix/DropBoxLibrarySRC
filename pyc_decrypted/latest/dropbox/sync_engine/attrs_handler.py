#Embedded file name: dropbox/sync_engine/attrs_handler.py
from __future__ import absolute_import
import errno
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE
from dropbox.attrs import Attributes, BLOCKABLE_DEFAULT, convert_attr_data, get_attr_data, serialize_attr_dict, serialize_attr_dict_only, unfreeze_attr_dict, unserialize_attr_dict
from dropbox.trace import TRACE, WARNING, unhandled_exc_handler, report_bad_assumption
from dropbox.low_functions import safe_navigate
from dropbox.functions import frozendict, loop_delete
from dropbox.fileutils import safe_chdir
import dropbox.fsutil as fsutil
from dropbox.sync_engine_file_system.exceptions import AttrsModifiedError, FileNotFoundError, NotADirectoryError
from .exceptions import UnreconstructableError
from .sync_engine_util import AttributeMergeError
_DROPBOX_SAFE_ATTR_FILE = u'.dropbox.attr'

def _dir_safe_filename(local_path):
    return local_path.join(_DROPBOX_SAFE_ATTR_FILE)


def _safe_open_file(fs, local_path, mode):
    try:
        return fs.open(_dir_safe_filename(local_path), mode)
    except IOError as e:
        if e.errno == errno.ENAMETOOLONG:
            with safe_chdir(local_path):
                return fs.open(_DROPBOX_SAFE_ATTR_FILE, mode)
        raise


def dir_safe_read_attributes(fs, local_path):
    with _safe_open_file(fs, local_path, 'r') as f:
        return Attributes.unmarshal(f.read())


def dir_safe_write_attributes(arch, attr, local_path):
    attr_file = _dir_safe_filename(local_path)
    if attr is not None:
        try:
            fsutil.clear_fs_bits(arch.file_system, attr_file)
        except Exception:
            unhandled_exc_handler()

        with _safe_open_file(arch.file_system, local_path, 'w') as f:
            f.write(attr.marshal())
        try:
            arch.hide_folder(attr_file)
        except Exception:
            unhandled_exc_handler()

    else:
        try:
            arch.file_system.remove(attr_file)
        except FileNotFoundError:
            pass
        except OSError as detail:
            if detail.errno == errno.ENAMETOOLONG:
                with safe_chdir(local_path):
                    arch.file_system.remove(_DROPBOX_SAFE_ATTR_FILE)
                    return
            raise


def read_attributes(fs, local_path, block_handler = None, whitelist = None, max_inline_attr_size = None, read_preserved = True):
    try:
        attr_handle = fs.open_attributes(local_path)
    except Exception as e:
        if getattr(e, 'errno', None) != errno.EOPNOTSUPP:
            raise
        return Attributes()

    attr_dict = {}
    data_plats = set()
    try:
        if read_preserved:
            try:
                _preserved_attr_handle = attr_handle.open_preserved('r')
            except Exception as e:
                if not fsutil.is_file_not_found_exception(e):
                    raise
            else:
                try:
                    unserialized_dict = unserialize_attr_dict(_preserved_attr_handle.read())
                except Exception:
                    unhandled_exc_handler()
                else:
                    for plat, plat_attrs in unserialized_dict.iteritems():
                        if whitelist is not None:
                            try:
                                platform_whitelist = whitelist[plat]
                            except KeyError:
                                continue

                            if not platform_whitelist:
                                continue
                        else:
                            platform_whitelist = None
                        attr_dict[plat] = new_plat_attrs = {}
                        for key, v in plat_attrs.iteritems():
                            if platform_whitelist is None or key in platform_whitelist:
                                new_plat_attrs[key] = v

                finally:
                    _preserved_attr_handle.close()

        for plat in attr_handle:
            if whitelist is not None:
                try:
                    platform_whitelist = whitelist[plat]
                except KeyError:
                    continue

            else:
                platform_whitelist = None
            data_plats.add(plat)
            with attr_handle.open(plat) as plat_attrs:
                p_attr_dict = {}
                while True:
                    try:
                        attr_key = plat_attrs.readattr()
                    except AttrsModifiedError:
                        plat_attrs.reset()
                        p_attr_dict = {}
                        continue
                    else:
                        if attr_key is None:
                            break

                    blockable = BLOCKABLE_DEFAULT
                    if platform_whitelist is not None:
                        try:
                            platform_whitelist[attr_key]
                        except KeyError:
                            continue
                        else:
                            blockable = platform_whitelist[attr_key].get('blockable', blockable)

                    try:
                        attr_data_handler = plat_attrs.open(attr_key, 'r')
                    except Exception as e:
                        if not fsutil.is_file_not_found_exception(e):
                            raise
                        plat_attrs.reset()
                        p_attr_dict = {}
                        continue

                    try:
                        p_attr_dict[attr_key] = convert_attr_data(attr_data_handler, max_inline_attr_size=max_inline_attr_size, block_handler=block_handler, blockable=blockable)
                    finally:
                        attr_data_handler.close()

            if p_attr_dict:
                attr_dict[plat] = p_attr_dict
            else:
                try:
                    del attr_dict[plat]
                except KeyError:
                    pass

    finally:
        attr_handle.close()

    return Attributes(attr_dict, data_plats)


def write_attributes(fs, attr, get_contents, local_path, whitelist = None):
    unwritten = set()
    data_plats = set()
    to_preserve = set()
    try:
        attr_handle = fs.open_attributes(local_path)
    except Exception as e:
        if getattr(e, 'errno', None) != errno.EOPNOTSUPP:
            unhandled_exc_handler()
        unwritten.update(attr.attr_dict)
        return (unwritten, data_plats)

    try:
        for plat, plat_attrs_dict in attr.attr_dict.iteritems():
            try:
                plat_attrs_handle = attr_handle.open(plat)
            except Exception as e:
                if not fsutil.is_file_not_found_exception(e):
                    unhandled_exc_handler()
                to_preserve.add(plat)
                continue

            try:
                data_plats.add(plat)
                for k, v in plat_attrs_dict.iteritems():
                    the_data = get_attr_data(v, get_contents)
                    try:
                        with plat_attrs_handle.open(k, 'w') as attr_data_handle:
                            attr_data_handle.write(the_data)
                    except Exception:
                        unhandled_exc_handler()
                        unwritten.add(plat)
                        if 'blocklist' in v:
                            data_plats.discard(plat)

            finally:
                plat_attrs_handle.close()

        def create_remove(plat_name, platform_whitelist):

            def remove_(attr_name):
                if platform_whitelist is None or attr_name not in platform_whitelist:
                    return False
                if attr_name not in attr.attr_dict.get(plat_name, ()):
                    try:
                        attr_handle.remove(plat_name, attr_name)
                    except Exception:
                        unhandled_exc_handler()
                    else:
                        return True

                return False

            return remove_

        if whitelist is not None:
            for plat_name in attr_handle:
                try:
                    platform_whitelist = whitelist[plat_name]
                except KeyError:
                    continue

                remove_ = create_remove(plat_name, platform_whitelist)
                with attr_handle.open(plat_name) as plat_handle:
                    loop_delete(plat_handle, remove_, dirmodifiederror=AttrsModifiedError)

        if to_preserve:
            try:
                with attr_handle.open_preserved('w') as _preserved_attr_handle:
                    _preserved_attr_handle.write(serialize_attr_dict(attr, None, only=to_preserve))
            except Exception as e:
                if fsutil.is_file_not_found_exception(e) or fsutil.is_permission_denied_exception(e):
                    WARNING("File System %r doesn't support preserving attrs at %r (was going to preserve: %r)", fs, local_path, to_preserve)
                else:
                    unhandled_exc_handler()
                unwritten.update(to_preserve)

        else:
            try:
                attr_handle.remove_preserved()
            except Exception as e:
                if not (fsutil.is_file_not_found_exception(e) or fsutil.is_permission_denied_exception(e)):
                    unhandled_exc_handler()

    finally:
        attr_handle.close()

    return (unwritten, data_plats)


class AttributesHandler(object):

    def __init__(self, arch, event, whitelist = None):
        self.arch = arch
        self.fs = getattr(arch, 'file_system', None)
        self.update(whitelist)
        self.max_inline_attr_size = 4096
        if not isinstance(self.whitelist, dict):
            report_bad_assumption('Whitelist is not a dict! %r', self.whitelist)
            self.whitelist = {}
        self.event = event

    def get_max_inline_attr_size(self):
        return self.max_inline_attr_size

    def get_whitelist_hash(self):
        return self.whitelist_hash

    def _whitelist_hash(self, whitelist):
        return hash(tuple((tuple((tuple((item for item in key_attrs_dict.iteritems())) for key, key_attrs_dict in plat_dict.iteritems())) for plat, plat_dict in whitelist.iteritems())))

    def update(self, new_server_attrs):
        if new_server_attrs is not None:
            self.whitelist = new_server_attrs
            self.whitelist_hash = self._whitelist_hash(new_server_attrs)
        else:
            self.whitelist = {}
            self.whitelist_hash = None

    def update_attr_size(self, new_attr_size):
        self.max_inline_attr_size = new_attr_size

    def merge_for_conflict(self, local_attrs, server_attrs):
        ret_attr_dict = unfreeze_attr_dict(local_attrs.attr_dict)
        for plat_key, plat_attrs in server_attrs.attr_dict.iteritems():
            for attr_key, server_val in plat_attrs.iteritems():
                important = self.whitelist.get(plat_key, frozendict()).get(attr_key, frozendict()).get('important', 0)
                local_val = ret_attr_dict.get(plat_key, frozendict()).get(attr_key, None)
                if important and local_val is not None and server_val != local_val:
                    raise AttributeMergeError()
                if local_val is not None:
                    continue
                if server_val is not None:
                    try:
                        ret_attr_dict[plat_key][attr_key] = server_val
                    except KeyError:
                        ret_attr_dict[plat_key] = {}
                        ret_attr_dict[plat_key][attr_key] = server_val

        return local_attrs.copy(attr_dict=ret_attr_dict)

    def has_important(self, attrs, unwritten = None):
        if unwritten:
            return any((any((self.whitelist.get(platform, frozendict()).get(key, frozendict()).get('important', 0) == 1 for key in plat_attrs)) for platform, plat_attrs in attrs.attr_dict.iteritems() if platform in unwritten))
        else:
            return any((any((self.whitelist.get(platform, frozendict()).get(key, frozendict()).get('important', 0) == 1 for key in plat_attrs)) for platform, plat_attrs in attrs.attr_dict.iteritems()))

    def get_attribute_block(self, attr, local_path, attr_ref):
        plat, key, i = attr.get_location(attr_ref)
        return fsutil.get_attr(self.fs, local_path, plat, key, offset=i * DROPBOX_MAX_BLOCK_SIZE, size=DROPBOX_MAX_BLOCK_SIZE)

    def _read_attributes(self, local_path, block_handler):
        attr = read_attributes(self.fs, local_path, block_handler, whitelist=self.whitelist, max_inline_attr_size=self.max_inline_attr_size)
        return (attr.attr_dict, attr.data_plats)

    def read_attributes(self, local_path, block_handler = None):
        attr_dict, data_plats = self._read_attributes(local_path, block_handler)
        try:
            dir_attr = dir_safe_read_attributes(self.fs, local_path).attr_dict
        except (FileNotFoundError, NotADirectoryError):
            pass
        except Exception:
            unhandled_exc_handler(False)
        else:
            attr_dict = dict(attr_dict)
            for plat, plat_attrs in dir_attr.iteritems():
                if plat not in attr_dict:
                    attr_dict[plat] = plat_attrs

        return Attributes(attr_dict=attr_dict, data_plats=data_plats)

    def get_downloadable_blocklist(self, local_path, attr):
        return {block_hash for plat, plat_attrs in attr.attr_dict.iteritems() for attr_key, attr_value in plat_attrs.iteritems() if 'blocklist' in attr_value if not safe_navigate(self.whitelist, plat, attr_key, 'derived') for block_hash in str(attr_value['blocklist']).split(',')}

    def write_attributes(self, attr, get_contents, local_path, is_dir = None):

        def filter_derived_attrs(plat, plat_data):
            return {attr_key:attr_value for attr_key, attr_value in plat_data.iteritems() if not safe_navigate(self.whitelist, plat, attr_key, 'derived')}

        attr_tuples = ((plat, filter_derived_attrs(plat, plat_data)) for plat, plat_data in attr.attr_dict.iteritems())
        attr_dict = {plat:plat_data for plat, plat_data in attr_tuples if plat_data}
        unwritten, data_plats = write_attributes(self.fs, attr.copy(attr_dict=attr_dict), get_contents, local_path, whitelist=self.whitelist)
        if fsutil.is_directory(self.fs, local_path) if is_dir is None else is_dir:
            try:
                dir_safe_write_attributes(self.arch, attr if unwritten else None, local_path)
                unwritten = set([])
            except Exception:
                unhandled_exc_handler()

        if unwritten and self.has_important(attr, unwritten=unwritten):
            TRACE(u"Couldn't write attributes to %s" % (local_path,))
            raise UnreconstructableError('Failed to write important attributes')
        return (unwritten, data_plats)

    def try_remove_preserved_blocks(self, local_path, blocks_to_remove):
        try:
            attr_handle = self.fs.open_attributes(local_path)
        except Exception:
            return

        try:
            file_changed = False
            with attr_handle.open_preserved('r') as _preserved_attr_handle:
                unserialized_dict = unserialize_attr_dict(_preserved_attr_handle.read())
                for plat, plat_attrs in unserialized_dict.iteritems():
                    keys_to_remove = []
                    for k, v in plat_attrs.iteritems():
                        try:
                            bl = v['blocklist']
                        except KeyError:
                            continue
                        else:
                            for block in str(bl).split(','):
                                if block in blocks_to_remove:
                                    keys_to_remove.append(k)
                                    break

                    if keys_to_remove:
                        for k in keys_to_remove:
                            del plat_attrs[k]

                        file_changed = True

            if file_changed:
                with attr_handle.open_preserved('w') as _preserved_attr_handle:
                    try:
                        _preserved_attr_handle.write(serialize_attr_dict_only(unserialized_dict, unserialized_dict))
                    except Exception:
                        unhandled_exc_handler()
                        return False

            return file_changed
        except Exception as e:
            if not (fsutil.is_file_not_found_exception(e) or fsutil.is_permission_denied_exception(e)):
                unhandled_exc_handler()
            return False
