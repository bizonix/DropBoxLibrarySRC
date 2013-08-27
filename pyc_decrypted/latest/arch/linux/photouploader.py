#Embedded file name: arch/linux/photouploader.py
USE_PHOTOUPLOADER = False

def is_disconnected_error(exc):
    return False


def should_handle_devices(*args, **kwargs):
    return False


class PhotoUploader(object):

    def __init__(self, app, *n, **kw):
        pass

    def register(self, *args, **kwargs):
        pass

    def listen():
        pass

    def unregister(self):
        pass

    def get_connected_devices(self):
        return []

    def get_action(self, *args, **kwargs):
        return ''

    def set_action(self, *args, **kwargs):
        pass

    def app_quit(self, *args, **kwargs):
        pass

    def handle_never(self, *args, **kwargs):
        return None

    def check_for_new_devices(self, *args, **kwargs):
        return (None, None)


def install_photo_components(*args, **kwargs):
    pass


def uninstall_photo_components(*args, **kwargs):
    pass
