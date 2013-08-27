#Embedded file name: dropbox/camera/__init__.py
from dropbox.debugging import easy_repr
IMPORT_SUCCESS, IMPORT_UNKNOWN_ERROR, IMPORT_LOW_DROPBOX_SPACE, IMPORT_LOW_DISK_SPACE = range(4)

class PhotoImportExceptionBase(Exception):
    pass


class PhotoImportCanceled(PhotoImportExceptionBase):
    pass


class PhotoImportDisconnected(PhotoImportExceptionBase):
    pass


class PhotoImportLowDropboxSpace(PhotoImportExceptionBase):
    pass


class PhotoImportDeviceLocked(PhotoImportExceptionBase):
    pass


class PhotoImportSelectiveSync(PhotoImportExceptionBase):

    def __init__(self, server_path):
        super(PhotoImportSelectiveSync, self).__init__()
        self.server_path = server_path


class PhotoImportAlbumCreationError(PhotoImportExceptionBase):
    pass


class PhotoImportNoConnectionError(PhotoImportExceptionBase):
    pass


class Device(object):
    PROPS = ('id', 'manufacturer', 'model', 'name', 'serialnum', 'uid', 'locked')

    def __init__(self, _id):
        self.id = _id
        self.manufacturer = None
        self.model = None
        self.name = None
        self.serialnum = None
        self.uid = None
        self.locked = False

    def __eq__(self, other):
        if not other:
            return False
        return self.id == other.id

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return easy_repr(self, *self.PROPS)

    def make_default(self):
        pass

    def release(self):
        pass

    def handle_disconnect_exceptions(self, e):
        pass

    def formatted_device_id(self):
        return str(self.id)

    def override_disabled(self):
        return False

    def establish_uid(self):
        pass

    def is_trackable(self):
        return True

    @property
    def percent(self):
        return 100


class AlbumInfo(object):
    __slots__ = ('uid', 'name', 'photos_list', 'server_collection_gid', 'album_time', 'path')

    def __init__(self, uid, name, photos_list, album_time = None, path = None):
        self.uid = uid
        self.name = name
        self.photos_list = photos_list
        self.server_collection_gid = None
        self.album_time = album_time
        self.path = path

    def __repr__(self):
        return easy_repr(self, *self.__slots__)
