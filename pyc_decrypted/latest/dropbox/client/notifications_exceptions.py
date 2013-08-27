#Embedded file name: dropbox/client/notifications_exceptions.py


class UnsupportedNotification(Exception):

    def __init__(self, message, type_id = None, version = None):
        Exception.__init__(self, message)
        self.type_id = type_id
        self.version = version


class UnsupportedNotificationType(UnsupportedNotification):
    pass


class UnsupportedNotificationVersion(UnsupportedNotification):
    pass


class MalformedRawNotification(Exception):
    pass


class StickyNotificationKeyError(Exception):
    pass
