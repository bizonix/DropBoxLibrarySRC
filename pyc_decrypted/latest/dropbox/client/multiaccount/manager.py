#Embedded file name: dropbox/client/multiaccount/manager.py
from multiprocessing import current_process
from multiprocessing.managers import BaseManager, Server, State as ManagerState
from dropbox.trace import unhandled_exc_handler
from dropbox.threadutils import ThreadPool
AUTHKEY = 'awesome'

class DropboxServer(Server):

    def __init__(self, *args, **kwargs):
        super(DropboxServer, self).__init__(*args, **kwargs)
        self.thread_pool = ThreadPool('DropboxServer', num_threads=8)

    def serve_forever(self):
        current_process()._manager_server = self
        try:
            while True:
                try:
                    conn = self.listener.accept()
                    self.thread_pool.add_work(self.handle_request, conn)
                except (OSError, IOError):
                    unhandled_exc_handler()

        finally:
            self.thread_pool.wait_for_completion()
            self.stop = True
            self.listener.close()


class DropboxManager(BaseManager):

    def get_server(self):
        assert self._state.value == ManagerState.INITIAL
        return DropboxServer(self._registry, self._address, self._authkey, self._serializer)


def other_client(address):
    m = DropboxManager(address=address, authkey=AUTHKEY)
    m.connect()
    return m
