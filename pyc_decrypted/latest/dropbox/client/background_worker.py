#Embedded file name: dropbox/client/background_worker.py
import threading
from collections import deque
from dropbox.functions import classproperty
from dropbox.gui import message_sender
from dropbox.native_event import AutoResetEvent
from dropbox.threadutils import StoppableThread
from dropbox.trace import unhandled_exc_handler

class MessageProcessingThread(StoppableThread):

    def __new__(cls, *args, **kwargs):
        assert not cls.initialized, 'Already instantiated.'
        assert cls != MessageProcessingThread, "Shouldn't instantiate directly."
        cls._instance = super(MessageProcessingThread, cls).__new__(cls, *args, **kwargs)
        cls._messages = deque(maxlen=100)
        return cls._instance

    def __init__(self, *args, **kwargs):
        self._event = AutoResetEvent()
        super(MessageProcessingThread, self).__init__(*args, **kwargs)

    @classproperty
    def initialized(cls):
        return getattr(cls, '_instance', None) is not None

    @classmethod
    def _process_messages(cls):
        assert cls != MessageProcessingThread
        while cls._messages:
            function, args, kwargs = cls._messages.popleft()
            try:
                function(*args, **kwargs)
            except Exception:
                unhandled_exc_handler()

    def set_wakeup_event(self):
        self._event.set()

    def run(self):
        while not self.stopped():
            self._process_messages()
            self._event.wait()

        self.cleanup()

    @classmethod
    def cleanup(cls):
        assert cls != MessageProcessingThread
        cls._instance = None

    @classmethod
    def call_after(cls, on_message_queue, *args, **kwargs):
        assert cls != MessageProcessingThread
        cls._messages.append((on_message_queue, args, kwargs))
        if not cls._instance:
            return
        if threading.currentThread() == cls._instance:
            cls._process_messages()
        else:
            cls._instance.set_wakeup_event()


class BackgroundWorkerThread(MessageProcessingThread):

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'BACKGROUNDWORKER'
        super(BackgroundWorkerThread, self).__init__(*args, **kwargs)


on_background_thread = message_sender(BackgroundWorkerThread.call_after, block=False, handle_exceptions=True)
