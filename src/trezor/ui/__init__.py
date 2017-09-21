from micropython import const

import sys
import math
import utime

from trezorui import Display

from trezor import io
from trezor import loop
from trezor import res

display = Display()

if sys.platform != 'trezor':
    loop.after_step_hook = display.refresh


def rgbcolor(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)


TEMP_BLUE   = rgbcolor(0x01, 0x02, 0x19)
LIGHT_RED   = rgbcolor(0xFF, 0x00, 0x00)

# ACTIVE DARK RED A64022
ACTIVE_RED  = rgbcolor(0xA6, 0x40, 0x22)
PINK        = rgbcolor(0xE9, 0x1E, 0x63)
PURPLE      = rgbcolor(0x9C, 0x27, 0xB0)
DEEP_PURPLE = rgbcolor(0x67, 0x3A, 0xB7)
INDIGO      = rgbcolor(0x3F, 0x51, 0xB5)
CYAN        = rgbcolor(0x00, 0xBC, 0xD4)
TEAL        = rgbcolor(0x00, 0x96, 0x88)

# ACTIVE DARK GREEN 1A8C14
ACTIVE_GREEN = rgbcolor(0x1A, 0x8C, 0x14)

LIGHT_GREEN = rgbcolor(0x87, 0xCE, 0x26)
LIME        = rgbcolor(0xCD, 0xDC, 0x39)
YELLOW      = rgbcolor(0xFF, 0xEB, 0x3B)
AMBER       = rgbcolor(0xFF, 0xC1, 0x07)
DEEP_ORANGE = rgbcolor(0xFF, 0x57, 0x22)
BROWN       = rgbcolor(0x79, 0x55, 0x48)
LIGHT_GREY  = rgbcolor(0xDA, 0xDD, 0xD8)
DARK_GREY   = rgbcolor(0x3E, 0x3E, 0x3E)
BLUE_GRAY   = rgbcolor(0x60, 0x7D, 0x8B)
BLACK       = rgbcolor(0x00, 0x00, 0x00)


# COLORS IN USE

DARK_BLUE   = rgbcolor(0x01, 0x2E, 0x53)
BLUE        = rgbcolor(0x02, 0x3D, 0x6E)
LIGHT_BLUE  = rgbcolor(0x45, 0x62, 0x7B)
GREEN       = rgbcolor(0x4C, 0xC1, 0x48)
RED         = rgbcolor(0xFF, 0x00, 0x00)
WHITE       = rgbcolor(0xFA, 0xFA, 0xFA)
ORANGE      = rgbcolor(0xFF, 0xAA, 0x22)
GREY        = rgbcolor(0x9C, 0x9C, 0x9C)


# ASSGIGNED ELEMENTS COLORS

C_SCREEN_BG             = BLUE

# BTNS
C_CONFIRM_BTN           = GREEN
C_CONFIRM_BTN_DIS       = GREEN
C_CANCEL_BTN            = RED
C_CANCEL_BTN_DIS        = RED
C_KEY_BTN               = DARK_BLUE
C_KEY_BTN_DIS           = LIGHT_BLUE
C_HOLD_BTN              = ORANGE
C_HOLD_BTN_DIS          = ORANGE
C_CLEAN_BTN             = ORANGE
C_CLEAN_BTN_DIS         = ORANGE

# FONT
C_FONT                  = WHITE
C_FONT_DIS              = GREY

# ELEMENTS
C_CIRCLE_BORDER         = GREY
C_BULLET                = GREY
C_BULLET_DIS            = LIGHT_BLUE

BLACKISH     = rgbcolor(0x20, 0x20, 0x20)
MONO   = Display.FONT_MONO
NORMAL = Display.FONT_NORMAL
BOLD   = Display.FONT_BOLD

# radius for buttons and other elements
BTN_RADIUS = const(2)

BACKLIGHT_NORMAL = const(60)
BACKLIGHT_DIM = const(5)
BACKLIGHT_NONE = const(2)
BACKLIGHT_MAX = const(255)

# display width and height
SCREEN = const(240)

# icons
ICON_RESET    = 'trezor/res/header_icons/reset.toig'
ICON_WIPE     = 'trezor/res/header_icons/wipe.toig'
ICON_RECOVERY = 'trezor/res/header_icons/recovery.toig'
ICON_CONFIRM  = 'trezor/res/confirm.toig'
ICON_CLEAR    = 'trezor/res/clear.toig'
ICON_CANCEL   = 'trezor/res/lock.toig'


def contains(pos: tuple, area: tuple) -> bool:
    x, y = pos
    ax, ay, aw, ah = area
    return ax <= x <= ax + aw and ay <= y <= ay + ah


def lerpi(a: int, b: int, t: float) -> int:
    return int(a + t * (b - a))


def blend(ca: int, cb: int, t: float) -> int:
    return rgbcolor(lerpi((ca >> 8) & 0xF8, (cb >> 8) & 0xF8, t),
                    lerpi((ca >> 3) & 0xFC, (cb >> 3) & 0xFC, t),
                    lerpi((ca << 3) & 0xF8, (cb << 3) & 0xF8, t))


def pulse(delay):
    while True:
        # normalize sin from interval -1:1 to 0:1
        yield 0.5 + 0.5 * math.sin(utime.ticks_us() / delay)


async def alert(count=3):
    short_sleep = loop.sleep(20000)
    long_sleep = loop.sleep(80000)
    current = display.backlight()
    for i in range(count * 2):
        if i % 2 == 0:
            display.backlight(BACKLIGHT_MAX)
            yield short_sleep
        else:
            display.backlight(BACKLIGHT_NORMAL)
            yield long_sleep
    display.backlight(current)


async def backlight_slide(val, delay=20000):
    sleep = loop.sleep(delay)
    current = display.backlight()
    for i in range(current, val, -1 if current > val else 1):
        display.backlight(i)
        await sleep


def rotate(pos: tuple) -> tuple:
    r = display.orientation()
    if r == 0:
        return pos
    x, y = pos
    if r == 90:
        return (y, 240 - x)
    if r == 180:
        return (240 - x, 240 - y)
    if r == 270:
        return (240 - y, x)


def header(title, icon=ICON_RESET, fg=BLACK, bg=BLACK):
    display.bar(0, 0, 240, 32, bg)
    if icon is not None:
        display.icon(8, 4, res.load(icon), fg, bg)
    display.text(8 + 24 + 2, 24, title, BOLD, fg, bg)


class Widget:

    def render(self):
        pass

    def touch(self, event, pos):
        pass

    def __iter__(self):
        touch = loop.select(io.TOUCH)
        while True:
            self.render()
            event, *pos = yield touch
            result = self.touch(event, pos)
            if result is not None:
                return result
