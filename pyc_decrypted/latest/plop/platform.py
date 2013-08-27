#Embedded file name: plop/platform.py
import signal
if hasattr(signal, 'setitimer'):
    from signal import setitimer, ITIMER_REAL, ITIMER_VIRTUAL, ITIMER_PROF
else:
    import ctypes.util
    libc = ctypes.CDLL(ctypes.util.find_library('c'))

    class Timeval(ctypes.Structure):
        _fields_ = [('tv_sec', ctypes.c_long), ('tv_usec', ctypes.c_long)]


    class Itimerval(ctypes.Structure):
        _fields_ = [('it_interval', Timeval), ('it_value', Timeval)]


    libc.setitimer.argtypes = [ctypes.c_int, ctypes.POINTER(Itimerval), ctypes.POINTER(Itimerval)]

    def seconds_to_timeval(seconds):
        return Timeval(int(seconds), int(seconds % 1 * 1000000))


    def setitimer(which, seconds, interval):
        libc.setitimer(which, Itimerval(seconds_to_timeval(interval), seconds_to_timeval(seconds)), None)


    ITIMER_REAL = 0
    ITIMER_VIRTUAL = 1
    ITIMER_PROF = 2
