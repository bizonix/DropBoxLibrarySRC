#Embedded file name: dropbox/sync_engine_arch/posix_invalid_parent.py
from dropbox.i18n import trans

def posix_path_makes_invalid_dropbox_parent(fs, path):
    if any((fs.make_path(tempp).is_parent_of(path) for tempp in (u'/tmp', u'/var/tmp', u'/var/cache', u'/var/lib', u'/var/run', u'/var/local', u'/var/games'))):
        return trans(u'This folder is used for temporary files.')
    if fs.make_path(u'/dev').is_parent_of(path):
        return trans(u'This folder is used for device drivers.')
    if fs.make_path(u'/proc').is_parent_of(path):
        return trans(u'This folder is a virtual folder with information about your running system.')
    return False
