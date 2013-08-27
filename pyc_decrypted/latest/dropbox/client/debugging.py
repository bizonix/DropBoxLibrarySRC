#Embedded file name: dropbox/client/debugging.py
import code
import threading

def run_interactive_shell(env):
    try:
        raise Exception('No IPython right now')
        import IPython
        shell = IPython.Shell.IPShell()
        a = threading.Thread(target=shell.mainloop, args=('-noconfirm_exit', '-nobanner'), name='DEBUG_SHELL')
    except:
        a = threading.Thread(target=code.interact, kwargs=dict(local=env), name='DEBUG_SHELL')

    a.setDaemon(True)
    a.start()
    del a
