#Embedded file name: arch/linux/xlib.py
import os
import ctypes
import ctypes.util
xlib = ctypes.cdll.LoadLibrary(ctypes.util.find_library('X11'))
Atom = ctypes.c_ulong
Display_p = ctypes.c_void_p
Window = ctypes.c_ulong
Window_p = ctypes.POINTER(Window)
Visual_p = ctypes.c_void_p
Bool = ctypes.c_int
Colormap = ctypes.c_ulong
Screen_p = ctypes.c_void_p
Status = ctypes.c_int

class XWindowAttributes(ctypes.Structure):
    _fields_ = [('x', ctypes.c_int),
     ('y', ctypes.c_int),
     ('width', ctypes.c_int),
     ('height', ctypes.c_int),
     ('border_width', ctypes.c_int),
     ('depth', ctypes.c_int),
     ('visual', Visual_p),
     ('root', Window),
     ('class', ctypes.c_int),
     ('bit_gravity', ctypes.c_int),
     ('win_gravity', ctypes.c_int),
     ('backing_store', ctypes.c_int),
     ('backing_planes', ctypes.c_ulong),
     ('backing_pixel', ctypes.c_ulong),
     ('save_under', Bool),
     ('colormap', Colormap),
     ('map_installed', Bool),
     ('map_state', ctypes.c_int),
     ('all_events_mask', ctypes.c_long),
     ('your_event_mask', ctypes.c_long),
     ('do_not_propagate_mask', ctypes.c_long),
     ('override_redirect', Bool),
     ('screen', Screen_p)]


xlib.XGetWindowAttributes.restype = Status
xlib.XGetWindowAttributes.argtypes = [Display_p, Window, ctypes.POINTER(XWindowAttributes)]
xlib.XTranslateCoordinates.restype = Bool
xlib.XTranslateCoordinates.argtypes = [Display_p,
 Window,
 Window,
 ctypes.c_int,
 ctypes.c_int,
 ctypes.POINTER(ctypes.c_int),
 ctypes.POINTER(ctypes.c_int),
 Window_p]
xlib.XGetWindowProperty.restype = ctypes.c_int
xlib.XGetWindowProperty.argtypes = [Display_p,
 Window,
 Atom,
 ctypes.c_long,
 ctypes.c_long,
 Bool,
 Atom,
 ctypes.POINTER(Atom),
 ctypes.POINTER(ctypes.c_int),
 ctypes.POINTER(ctypes.c_ulong),
 ctypes.POINTER(ctypes.c_ulong),
 ctypes.c_void_p]
xlib.XQueryTree.restype = Status
xlib.XQueryTree.argtypes = [Display_p,
 Window,
 Window_p,
 Window_p,
 ctypes.POINTER(Window_p),
 ctypes.POINTER(ctypes.c_uint)]
xlib.XOpenDisplay.restype = Display_p
xlib.XOpenDisplay.argtypes = [ctypes.c_char_p]
xlib.XInternAtom.restype = Atom
xlib.XInternAtom.argtypes = [Display_p, ctypes.c_char_p, Bool]
xlib.XFree.restype = ctypes.c_int
xlib.XFree.argtypes = [ctypes.c_void_p]
xlib.XDefaultRootWindow.restype = Window
xlib.XDefaultRootWindow.argtypes = [Display_p]
XTrue = 1
XFalse = 0
XAnyProperyType = 0
pid_atom = None
icon_name_atom = None
dpy = None

def window_pid(dpy, w):
    global pid_atom
    prop = ctypes.POINTER(ctypes.c_ubyte)()
    actual_type = Atom()
    actual_format, pid = [ ctypes.c_int() for i in range(2) ]
    bytes_after, nitems = [ ctypes.c_ulong() for i in range(2) ]
    status = xlib.XGetWindowProperty(dpy, w, pid_atom, 0, 1, XFalse, XAnyProperyType, ctypes.byref(actual_type), ctypes.byref(actual_format), ctypes.byref(nitems), ctypes.byref(bytes_after), ctypes.byref(prop))
    if status != 0 or nitems.value != 1:
        return None
    pid = prop[0] + prop[1] * 256
    xlib.XFree(prop)
    return pid


def window_icon_name(dpy, w):
    global icon_name_atom
    prop = ctypes.c_char_p()
    actual_type = Atom()
    actual_format, pid = [ ctypes.c_int() for i in range(2) ]
    bytes_after, nitems = [ ctypes.c_ulong() for i in range(2) ]
    status = xlib.XGetWindowProperty(dpy, w, icon_name_atom, 0, 1024, XFalse, XAnyProperyType, ctypes.byref(actual_type), ctypes.byref(actual_format), ctypes.byref(nitems), ctypes.byref(bytes_after), ctypes.byref(prop))
    if status != 0:
        return None
    cb = ctypes.create_string_buffer(nitems.value)
    ctypes.memmove(cb, prop, nitems.value)
    xlib.XFree(prop)
    return cb.value


ourpid = os.getpid()

def is_the_one(dpy, w):
    global ourpid
    return window_pid(dpy, w) == ourpid and window_icon_name(dpy, w) == 'systray icon'


def get_window_children(dpy, w):
    root, parent = [ Window() for i in range(2) ]
    children = Window_p()
    nchildren = ctypes.c_uint()
    if xlib.XQueryTree(dpy, w, ctypes.byref(root), ctypes.byref(parent), ctypes.byref(children), ctypes.byref(nchildren)) == 0:
        return []
    toret = []
    for i in range(nchildren.value):
        toret.append(children[i])

    xlib.XFree(children)
    return toret


def get_tray_icon_window_id():
    global pid_atom
    global icon_name_atom
    if dpy == None:
        dpy = xlib.XOpenDisplay(None)
        if dpy == None:
            return
        pid_atom = xlib.XInternAtom(dpy, '_NET_WM_PID', XTrue)
        icon_name_atom = xlib.XInternAtom(dpy, 'WM_ICON_NAME', XTrue)
    queue = [xlib.XDefaultRootWindow(dpy)]
    while len(queue) != 0:
        w = queue.pop(0)
        if is_the_one(dpy, w):
            return w
        queue.extend(get_window_children(dpy, w))


def display_width_height():
    win_attributes = XWindowAttributes()
    if xlib.XGetWindowAttributes(dpy, xlib.XDefaultRootWindow(dpy), ctypes.byref(win_attributes)) == 0:
        return None
    return (win_attributes.width, win_attributes.height)


def x_y_for_window(w):
    win_attributes = XWindowAttributes()
    rx, ry = [ ctypes.c_int() for i in range(2) ]
    junkwin = ctypes.c_ulong()
    if xlib.XGetWindowAttributes(dpy, w, ctypes.byref(win_attributes)) == 0:
        return None
    if xlib.XTranslateCoordinates(dpy, w, win_attributes.root, -win_attributes.border_width, -win_attributes.border_width, ctypes.byref(rx), ctypes.byref(ry), ctypes.byref(junkwin)) == XFalse:
        return None
    return (rx.value,
     ry.value,
     win_attributes.width,
     win_attributes.height)
