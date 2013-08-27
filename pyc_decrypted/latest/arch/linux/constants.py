#Embedded file name: arch/linux/constants.py
import unicodedata
import os
from build_number import BUILD_KEY
default_dropbox_folder_name = BUILD_KEY
local_form = 'NFC'

def path_from_name(dropbox_folder_name):
    return unicodedata.normalize(local_form, os.path.expanduser(u'~/%s' % dropbox_folder_name))


assert '-master' not in BUILD_KEY, 'BUILD_KEY (%s) cannot contain the master suffix' % BUILD_KEY
instance_config_path = unicodedata.normalize(local_form, os.path.expanduser(u'~/.%s-master' % BUILD_KEY.lower()))
appdata_path = unicodedata.normalize(local_form, os.path.expanduser(u'~/.%s' % BUILD_KEY.lower()))
default_dropbox_path = path_from_name(default_dropbox_folder_name)
seven_default_dropbox_path = default_dropbox_path
hash_wait_time = 0
platform = 'linux'
update_root = os.path.expanduser(u'~/.dropbox-dist')
