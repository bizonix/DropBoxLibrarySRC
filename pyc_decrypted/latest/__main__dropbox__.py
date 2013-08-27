#Embedded file name: __main__dropbox__.py
from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()
    import dropbox.client.main
    dropbox.client.main.main()
