#Embedded file name: arch/linux/proxy_watch.py


class ProxyWatch:

    def on_proxy_change(self):
        if self.callback:
            self.callback()

    def __init__(self):
        self.callback = None

    def register_callback(self, function):
        self.callback = function

    def setup_callback(self):
        pass

    def teardown_callback(self):
        self.callback = None
