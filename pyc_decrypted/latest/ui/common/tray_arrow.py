#Embedded file name: ui/common/tray_arrow.py
import math
from dropbox.trace import TRACE, unhandled_exc_handler
PERIOD_LENGTH = 2.0
TICK_RATE = 0.025
PADDING_FACTOR = 1.0 / 3.0

def parametrization(t):
    return math.sin(2 * math.pi * t / PERIOD_LENGTH)


def tick(self, event):
    try:
        self.t += self.TICK_RATE
        self.place()
    except:
        unhandled_exc_handler()
        self.stop()


def get_current_position(self):
    a = parametrization(self.t)
    x = int(a * (self.endx - self.startx) + self.startx)
    y = int(a * (self.endy - self.starty) + self.starty)
    return (x, y)


def determine_motion(self):
    assert hasattr(self, 'orientation'), 'determine_motion called before TrayArrow initialized'
    rx, ry, rw, rh = self.pointing_at
    if self.orientation == 0:
        self.endx = rx + rw / 2.0 - self.w / 2.0
        self.endy = ry + self.y_factor
        self.startx = self.endx
        self.starty = self.endy + self.range_of_motion
    elif self.orientation == 90:
        self.endx = rx + rw + self.PADDING_FACTOR * rw
        self.endy = ry + rh / 2.0 - self.h / 2.0
        self.startx = self.endx + self.range_of_motion
        self.starty = self.endy
    elif self.orientation == 180:
        self.endx = rx + rw / 2.0 - self.w / 2.0
        self.endy = ry + self.y_factor
        self.startx = self.endx
        self.starty = self.endy + self.range_of_motion
    else:
        self.endx = rx - (self.w + self.PADDING_FACTOR * rw)
        self.endy = ry + rh / 2.0 - self.h / 2.0
        self.startx = self.endx + self.range_of_motion
        self.starty = self.endy
