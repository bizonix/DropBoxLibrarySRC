#Embedded file name: dropbox/keystore/_exceptions.py


class KeychainAuthCanceled(Exception):
    pass


class KeychainAuthFailed(Exception):
    pass


class KeychainNeedsRepair(Exception):
    pass


class KeychainMissingItem(Exception):
    pass


class KeystoreRegKeyError(Exception):
    pass
