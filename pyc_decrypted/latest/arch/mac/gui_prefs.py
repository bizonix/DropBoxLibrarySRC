#Embedded file name: arch/mac/gui_prefs.py
import itertools
import os
import shutil
import struct
import sys
from ds_store import BuddyAllocator, Entry, writeDsdbEntries
from dropbox.languages import CAMERA_UPLOADS_FOLDER_NAMES
from dropbox.language_data import CAMERA_UPLOAD_FOLDERS_LANGS
from dropbox.preferences import OPT_CAMERA_UPLOAD_WINDOWS
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.sync_engine_arch.macosx._fschange import trace_ds_store_file
ICON_SIZE = 128
ARRANGED_BY = 'name'
_CAMERA_UPLOAD_FOLDERS = [ [ CAMERA_UPLOADS_FOLDER_NAMES[lang] for lang in langs ] for langs in CAMERA_UPLOAD_FOLDERS_LANGS ]
_CAMERA_UPLOAD_LEVEL = len(_CAMERA_UPLOAD_FOLDERS)

def set_folders_for_photo_display(app, parent):
    TRACE('set_folders_for_photo_display on %r', parent)
    curr_level = app.pref_controller[OPT_CAMERA_UPLOAD_WINDOWS]
    if curr_level >= _CAMERA_UPLOAD_LEVEL:
        TRACE('set_folders_for_photo_display: current level %s >= _CAMERA_UPLOAD_LEVEL (%s)', curr_level, _CAMERA_UPLOAD_LEVEL)
        return
    icvo_data = struct.pack('>4s H 4s 4s HHHHHHHHH', 'icv4', ICON_SIZE, ARRANGED_BY, 'botm', 1, 0, 4, 0, 4, 1, 0, 100, 1)
    structure_id_data = {'BKGD': 'DefB' + '\x00\x00\x00\x00\x00\x00\x00\x00',
     'ICVO': 1,
     'icvo': icvo_data,
     'vstl': 'icnv'}
    subdirs = list(set(list(itertools.chain(*_CAMERA_UPLOAD_FOLDERS[curr_level:]))))
    new_entries = []
    for subdir_name in subdirs:
        for k, v in structure_id_data.iteritems():
            new_entries.append(Entry(subdir_name, k, v))

    true_ds_path = os.path.join(parent, '.DS_Store')
    our_ds_path = os.path.join(parent, '.DS_Store.tmp')
    existing_entries = []
    if os.path.exists(true_ds_path):
        with open(true_ds_path, 'rb') as f:
            try:
                store = BuddyAllocator.open(f)
                existing_entries = store.getDsdbEntries()
                if store.unknown2 != 0:
                    TRACE('set_folders_for_photo_display: DS Store file has unknown2 = %s (not zero)', store.unknown2)
                    trace_ds_store_file(path=true_ds_path)
            except Exception:
                unhandled_exc_handler()
                TRACE('set_folders_for_photo_display: unable to read existing DS Store - aborting')
                trace_ds_store_file(path=true_ds_path)
                report_bad_assumption("can't understand DS Store file")
                return

            store.close()
    entries = existing_entries + new_entries
    cleanup_needed = False
    if os.path.exists(true_ds_path):
        shutil.copyfile(true_ds_path, our_ds_path)
        cleanup_needed = True
    try:
        writeDsdbEntries(our_ds_path, entries)
        TRACE('successfully edited entries for %s', our_ds_path)
        os.rename(our_ds_path, true_ds_path)
        cleanup_needed = False
        TRACE('successfully replaced %s', true_ds_path)
        app.pref_controller.update({OPT_CAMERA_UPLOAD_WINDOWS: _CAMERA_UPLOAD_LEVEL})
    finally:
        if cleanup_needed:
            try:
                os.remove(our_ds_path)
            except Exception:
                unhandled_exc_handler()


def _make_set_and_open(path):

    class FakeApp(object):
        pass

    fake_app = FakeApp()
    fake_app.pref_controller = {OPT_CAMERA_UPLOAD_WINDOWS: 0}
    os.makedirs(path)
    subdirs = list(set(list(itertools.chain(*_CAMERA_UPLOAD_FOLDERS))))
    for subdir in subdirs:
        full_path = os.path.join(path, subdir)
        os.mkdir(full_path)
        cmd = "cp images/about/*.jpg '%s'" % (full_path,)
        print 'running %s' % (cmd,)
        os.system(cmd)

    set_folders_for_photo_display(fake_app, path)
    os.system("open '%s'" % (path,))


if __name__ == '__main__':
    _make_set_and_open(sys.argv[1])
