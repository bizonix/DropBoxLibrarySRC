#Embedded file name: dropbox/sync_engine/move_dropbox.py
from __future__ import absolute_import
import collections
import errno
import itertools
from dropbox.i18n import trans
from dropbox.trace import TRACE, unhandled_exc_handler
import arch as global_arch
import dropbox.fsutil as fsutil
from dropbox.fastwalk import fastwalk_strict
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR, FILE_TYPE_POSIX_SYMLINK
from dropbox.sync_engine_file_system.exceptions import FileSystemError, FileExistsError
import dropbox.client.unlink_cookie

def safe_copystat(fs, src, dest):
    fsutil.copystat(fs, src, dest)
    fsutil.copyxattr(fs, src, dest)


def copy3(fs, src, dst):
    fsutil.copyfile(fs, src, dst)
    safe_copystat(fs, src, dst)


def lower_eq(a, b):
    return a.lower() == b.lower()


def path_endswith_dropbox(path, care_about_existing_dropbox = True, arch = None):
    if not care_about_existing_dropbox:
        if arch is None:
            raise Exception('Must have an arch')
        path = arch.file_system.make_path(path)
        dropbox_folder = arch.DEFAULT_DROPBOX_FOLDER_NAME
        path = arch.file_system.realpath(path)
        if lower_eq(path.basename, dropbox_folder):
            d = {'folder_name': path.join(dropbox_folder),
             'dropbox_name': dropbox_folder}
            return trans(u'The path you\'ve chosen ends with %(dropbox_name)s. This will create a folder named "%(folder_name)s" for Dropbox.') % d
    return False


def path_makes_invalid_dropbox_parent(path, sync_engine = None, care_about_existing_dropbox = True, arch = None):
    if arch is None:
        raise Exception('Must have an arch')
    if sync_engine is not None and sync_engine.arch is not arch:
        raise Exception('file systems are inconsistent')
    if care_about_existing_dropbox and (sync_engine is None or sync_engine.dropbox_folder is None):
        raise Exception('Dropbox path is None, yet user requested we care about existing dropbox')
    path = arch.file_system.make_path(path)
    dirs_created = []
    try:
        fsutil.makedirs(arch.file_system, path, dirs_created=dirs_created)
        path_ = fsutil.make_random_dir(arch.file_system, path)
        dirs_created.append(path_)
    except Exception:
        unhandled_exc_handler()
        return trans(u"Can't create a Dropbox folder in the requested location ")
    finally:
        for d in reversed(dirs_created):
            fsutil.safe_rmdir(arch.file_system, d)

    current_appdata = arch.APPDATA_PATH
    if lower_eq(current_appdata, path):
        return trans(u'This folder is where the Dropbox settings live!')
    if current_appdata.lower().is_parent_of(path.lower()):
        return trans(u'This folder is inside of the Dropbox settings!')
    if care_about_existing_dropbox:
        current_dropbox = arch.file_system.realpath(sync_engine.dropbox_folder)
        if lower_eq(path, current_dropbox):
            return trans(u'This folder is your current Dropbox!')
        if current_dropbox.lower().is_parent_of(path.lower()):
            return trans(u'This folder is inside your current Dropbox.')
        new_dropbox_path = path.join(arch.DEFAULT_DROPBOX_FOLDER_NAME)
        if fsutil.is_exists(arch.file_system, new_dropbox_path):
            if fsutil.is_directory(arch.file_system, new_dropbox_path):
                return trans(u'This folder already contains a Dropbox directory.')
            else:
                return trans(u'This folder already has a file inside named %(filename)s!') % {'filename': new_dropbox_path.basename}
        if fsutil.is_exists(arch.file_system, current_dropbox) and not fsutil.on_same_device(arch.file_system, path, current_dropbox) and sync_engine.get_space_used() >= sync_engine.get_disk_free_space(path):
            return trans(u'This folder is on a device that does not have enough free space.')
    return arch.path_makes_invalid_dropbox_parent(path)


class MoveCancelled(Exception):
    pass


def posix_normpath(posix_path):
    assert posix_path[0] == '/', 'Only support absolute paths, got %r' % posix_path
    full_path = []
    for comp in itertools.islice(posix_path.split('/'), 1, None):
        if comp == '..':
            if full_path:
                full_path.pop()
        elif comp == '.':
            continue
        else:
            full_path.append(comp)

    return '/%s' % '/'.join(full_path)


def copytree(fs, src, dest, progress_callback = None):
    log = collections.deque()
    try:
        try:
            fsutil.makedirs(fs, dest)
        except FileExistsError:
            pass

        log.append((FILE_TYPE_DIRECTORY, (src, dest)))
        for dir_to_explore, ents in fastwalk_strict(fs, src, follow_symlinks=False):
            for dirent in ents:
                fn_src = dir_to_explore.join(dirent.name)
                fn_dest = fsutil.reparent_path(src, dest, fn_src)
                if fsutil.win32_is_junction_point(fs, fn_src, dirent=dirent):
                    raise MoveCancelled(trans(u"Couldn't move junction point: %s") % fn_src)
                try:
                    ent_type = dirent.type
                except AttributeError:
                    ent_type = fs.indexing_attributes(fn_src).type

                if ent_type == FILE_TYPE_DIRECTORY:
                    log.append((FILE_TYPE_DIRECTORY, (fn_src, fn_dest)))
                    try:
                        fsutil.makedirs(fs, fn_dest)
                    except FileExistsError:
                        pass

                    safe_copystat(fs, fn_src, fn_dest)
                else:
                    if dirent.name == u'.dropbox':
                        log.append(('ignored', (fn_src,)))
                        continue
                    if fsutil.is_exists(fs, fn_dest, resolve_link=False):
                        raise MoveCancelled(trans(u"There's already a copy of %(filename)s here") % {'filename': fn_dest})
                    if ent_type == FILE_TYPE_POSIX_SYMLINK:
                        if fs.supports_extension('posix'):
                            target_dest = target_src = fs.posix_readlink(fn_src)
                            try:
                                if not target_dest.startswith('/'):
                                    target_abs = posix_normpath(unicode(dir_to_explore).encode('utf8') + '/' + target_dest)
                                    if not target_abs.startswith(unicode(src).encode('utf8') + '/'):
                                        target_dest = target_abs
                            except Exception:
                                unhandled_exc_handler()

                            log.append((FILE_TYPE_POSIX_SYMLINK, (fn_src,
                              target_src,
                              fn_dest,
                              target_dest)))
                            fs.posix_symlink(target_dest, fn_dest)
                        else:
                            raise MoveCancelled(trans(u"Couldn't move symlink: %s") % fn_src)
                    else:
                        log.append((FILE_TYPE_REGULAR, (fn_src, fn_dest)))
                        copy3(fs, fn_src, fn_dest)
                if progress_callback:
                    progress_callback()

        safe_copystat(fs, src, dest)
        return log
    except Exception:
        log2 = collections.deque()
        for t, data in log:
            if t == FILE_TYPE_DIRECTORY:
                log2.append(':%s' % (data[1],))
            elif t == FILE_TYPE_POSIX_SYMLINK:
                log2.append('%s (%s) -> %s (%s)' % data)
            elif t == FILE_TYPE_REGULAR:
                log2.append('%s -> %s' % (data[0], data[1]))

        TRACE('\n'.join(log2))
        raise


def really_bad_move(error_callback, warn):
    warn(trans(u'An unrecoverable error occurred when your files were moved. Dropbox will now restart, please link your account again.'), False)
    if error_callback:
        try:
            error_callback()
        except Exception:
            unhandled_exc_handler()


def move(new_dropbox, sync_engine, warn, progress_callback = None, error_callback = None):
    success = sync_engine.status.try_set_status_label('moving', True, fail_if_set=['importing'])
    if not success:
        problem = trans(u"Can't move Dropbox folder while uploading photos")
        return problem
    sync_engine.start_stop_lock.acquire_write()
    try:
        return _move(new_dropbox, sync_engine, warn, progress_callback=progress_callback, error_callback=error_callback)
    finally:
        sync_engine.start_stop_lock.release_write()
        sync_engine.status.set_status_label('moving', False)


def _move(new_dropbox, sync_engine, warn, progress_callback = None, error_callback = None):
    fs = sync_engine.fs
    problems = None
    log = []
    old_dropbox = sync_engine.dropbox_folder
    if old_dropbox is None:
        raise Exception('Old path for dropbox folder is None!')
    TRACE('Preparing to move dropbox from %r to %r', old_dropbox, new_dropbox)
    stage = 0
    running = sync_engine.running
    if running:
        running = sync_engine.stop(do_join=True, shell_touch=False, _already_have_start_stop_lock=True)
        if running:
            TRACE('Stopped Sync Engine')
    use_rename = False
    try:
        problems = trans(u"Some files can't be moved. Please select a new location or close some open files and try again.")
        try:
            fs.rename(old_dropbox, new_dropbox)
            use_rename = True
        except FileSystemError as e:
            if getattr(e, 'winerror', None) == 5:
                raise MoveCancelled(trans(u"The Dropbox folder couldn't be moved because it's being used by another program. Please close all programs that are accessing Dropbox and try again."))
            elif e.errno == errno.EXDEV:
                TRACE('Simple rename failed (different devices)... Calling Copy Tree')
                log = copytree(fs, old_dropbox, new_dropbox, progress_callback)
                TRACE('Copy Tree finished')
            else:
                raise
        else:
            TRACE('Simple rename finished')

        problems = None
        stage = 1
        TRACE('Writing new location to preferences')
        sync_engine.pref_controller.update({'dropbox_path': unicode(new_dropbox)})
        stage = 1.5
        TRACE('Rerouting any system locations pointing into Dropbox (Documents/Music locations, etc)')
        try:
            sync_engine.arch.redirect_libraries_to(sync_engine.config, unicode(new_dropbox))
        except Exception:
            unhandled_exc_handler()

        stage = 2
        TRACE('Writing new unlink cookie')
        dropbox.client.unlink_cookie.write_unlink_cookie(sync_engine, path=unicode(new_dropbox), keystore=sync_engine.keystore)
        stage = 3
        TRACE('Telling the sync engine to use the new path.')
        sync_engine.mount_dropbox_folder(unicode(new_dropbox), _already_have_start_stop_lock=True)
        stage = 6
        TRACE('OK! Prepared state for new box.')
    except MoveCancelled as e:
        TRACE('Move was cancelled due to %r', e.message)
        problems = e.message
    except Exception:
        unhandled_exc_handler()

    if stage < 6:
        TRACE('Trouble moving, roll it back...')
        if not problems:
            problems = trans(u'Unexpected errors occurred. Your Dropbox is ok!')
        if stage >= 5:
            TRACE('Telling the sync engine to use the old root directory')
            try:
                sync_engine.mount_dropbox_folder(unicode(old_dropbox), _already_have_start_stop_lock=True)
            except Exception:
                unhandled_exc_handler()
                really_bad_move(error_callback, warn)

        if stage >= 3:
            TRACE('Rewriting old recovery cookie')
            try:
                dropbox.client.unlink_cookie.write_unlink_cookie(sync_engine, path=unicode(old_dropbox), keystore=sync_engine.keystore)
            except Exception:
                unhandled_exc_handler()
                really_bad_move(error_callback, warn)

        if stage >= 2:
            TRACE('Writing old location to preferences')
            try:
                sync_engine.pref_controller.update({'dropbox_path': unicode(old_dropbox)})
            except Exception:
                unhandled_exc_handler()
                really_bad_move(error_callback, warn)

        if stage >= 1.5:
            TRACE('Re-rerouting any system locations pointing into Dropbox (Documents/Music locations, etc)')
            try:
                sync_engine.arch.redirect_libraries_to(sync_engine.config, unicode(old_dropbox))
            except Exception:
                unhandled_exc_handler()

        if stage >= 1 and use_rename:
            TRACE('Renaming back from new location')
            try:
                fs.rename(new_dropbox, old_dropbox)
            except Exception:
                unhandled_exc_handler()
                really_bad_move(error_callback, warn)

    else:
        try:
            folder_tagger = sync_engine.arch.folder_tagger
            try:
                for t, data in reversed(log):
                    if t == FILE_TYPE_DIRECTORY:
                        fsutil.safe_rmdir(fs, data[0])
                    elif t in (FILE_TYPE_POSIX_SYMLINK, FILE_TYPE_REGULAR, 'ignored'):
                        fsutil.safe_remove(fs, data[0])
                    else:
                        TRACE('Unknown log entry %s %r', t, data)
                        continue

            except Exception:
                unhandled_exc_handler()

            if fsutil.is_exists(fs, old_dropbox):
                TRACE("Untagging old dropbox, since it's still hanging around")
                try:
                    folder_tagger.untag_folder(old_dropbox)
                except Exception:
                    unhandled_exc_handler(False)

        except Exception:
            unhandled_exc_handler()

        try:
            TRACE('Switching sidebar link')
            global_arch.startup.switch_sidebar_link(unicode(new_dropbox), old_link=unicode(old_dropbox))
        except Exception:
            unhandled_exc_handler()

    try:
        if running:
            TRACE('Restarting Sync Engine')
            sync_engine.start(_already_have_start_stop_lock=True)
        if problems:
            TRACE('Problems: %s' % problems)
        return problems
    except Exception:
        unhandled_exc_handler()
        really_bad_move(error_callback, warn)
