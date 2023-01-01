# to generate font python file
#
# python3 font-to-py.py -c "0123456789pm %°C" Amatic-Bold.ttf 64 microAmatic64bs.py
#

from micropython import const
from machine import Pin, SPI
from time import sleep

#import amatic96bs
#import amatic32bs
#import oswald32bs

#SSD1608 e-ink display
COLS = const(136)
ROWS = const(250)
OFFSET_X = const(0)
OFFSET_Y = const(6)

WIDTH = const(250)
HEIGHT = const(122)

# this is the SSD1608 class
DRIVER_CONTROL = const(0x01)
GATE_VOLTAGE = const(0x03)
SOURCE_VOLTAGE = const(0x04)
DISPLAY_CONTROL = const(0x07)
NON_OVERLAP = const(0x0B)
BOOSTER_SOFT_START = const(0x0C)
GATE_SCAN_START = const(0x0F)
DEEP_SLEEP = const(0x10)
DATA_MODE = const(0x11)
SW_RESET = const(0x12)
TEMP_WRITE = const(0x1A)
TEMP_READ = const(0x1B)
TEMP_CONTROL = const(0x1C)
TEMP_LOAD = const(0x1D)
MASTER_ACTIVATE = const(0x20)
DISP_CTRL1 = const(0x21)
DISP_CTRL2 = const(0x22)
WRITE_RAM = const(0x24)
WRITE_ALTRAM = const(0x26)
READ_RAM = const(0x25)
VCOM_SENSE = const(0x28)
VCOM_DURATION = const(0x29)
WRITE_VCOM = const(0x2C)
READ_OTP = const(0x2D)
WRITE_LUT = const(0x32)
WRITE_DUMMY = const(0x3A)
WRITE_GATELINE = const(0x3B)
WRITE_BORDER = const(0x3C)
SET_RAMXPOS = const(0x44)
SET_RAMYPOS = const(0x45)
SET_RAMXCOUNT = const(0x4E)
SET_RAMYCOUNT = const(0x4F)
NOP = const(0xFF)

spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4), baudrate=100000)
spi_cs = Pin(5, mode=Pin.OUT, value=1)
spi_dc = Pin(22, mode=Pin.OUT, value=1)
reset = Pin(27, mode=Pin.OUT, value=0)
busy = Pin(17, mode=Pin.IN)

CS_ACTIVE = const(0)
CS_INACTIVE = const(0)

TEXT_TINY = const(1)
TEXT_NORMAL = const(2)
TEXT_MEDIUM = const(3)
TEXT_LARGE = const(4)

WHITE = const(0)
BLACK = const(1)
ACCENT = const(2)

LUTS_BLACK = bytearray([
    0x02, 0x02, 0x01, 0x11, 0x12, 0x12, 0x22, 0x22, 0x66, 0x69,
    0x69, 0x59, 0x58, 0x99, 0x99, 0x88, 0x00, 0x00, 0x00, 0x00,
    0xF8, 0xB4, 0x13, 0x51, 0x35, 0x51, 0x51, 0x19, 0x01, 0x00
])


## writing texts
### copy to font
text_hflip = 1
text_vflip = 1

def char_len(ch, font):
    glyph = font.get_ch(ch)
    return glyph[2]

def text_len(text, font):
    return sum(char_len(c, font) for c in text)

def draw_glyph(glyph, x, y, color=1):
    ox, oy = 0, 0
    dy = 1 if not text_hflip else -1
    dx = 1 if not text_vflip else -1
    for b in glyph[0]:
        for i in range(8):
            if (b >> i) & 1:
                set_pixel(x + ox, y + oy, color)
            oy = oy + dy
            if abs(oy) >= glyph[1]:
                ox = ox + dx
                oy = 0

def draw_ch(ch, x, y, font, color=1):
    glyph = font.get_ch(ch)
    draw_glyph(glyph, x, y, color)

def draw_text(text, x, y, font, color=1):
    ox = 0
    kx = 1 if not text_hflip else -1    
    for letter in text:
        glyph = font.get_ch(letter)
        draw_glyph(glyph, x+ox, y, color)
        ox += kx*glyph[2]

# END TEXT STUFF

def set_pixel(x, y, color=1):
    y += OFFSET_Y
    y = COLS - 1 - y
    shift = 7 - y % 8
    y //= 8

    offset = x * (COLS // 8) + y

    if offset >= len(buf_b):
        return

    byte_b = buf_b[offset] | (0b1 << shift)
    byte_r = buf_r[offset] & ~(0b1 << shift)

    if color == 2:
        # Set a bit to set as red/yellow
        byte_r |= 0b1 << shift
    if color == 1:
        # Mask *out* a bit to set as black
        byte_b &= ~(0b1 << shift)

    buf_b[offset] = byte_b
    buf_r[offset] = byte_r


def draw_line(x0, y0, x1, y1, color=1):
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1

    err = dx + dy
    while True:
        set_pixel(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy

def draw_rectangle(x, y, width, height, color=1, filled=False):
    width -= 1
    height -= 1

    draw_line(x, y, x + width, y, color)
    draw_line(x, y, x, y + height, color)
    draw_line(x + width, y, x + width, y + height, color)
    draw_line(x, y + height, x + width, y + height, color)

    if filled:
        x += 1
        y += 1
        width -= 1
        height -= 1
        for px in range(width):
            for py in range(height):
                set_pixel(x + px, y + py, color)

def clear():
    global buf_b, buf_r
    buf_b = bytearray(b'\xFF' * (COLS // 8) * ROWS)
    buf_r = bytearray((COLS // 8) * ROWS)


def _busy_wait():
    while busy.value():
        v = busy.value()
        print(v)
        sleep(0.5)

def _spi_cmd(command, data=None):
    """Send command over SPI.
    :param command: command byte
    :param data: optional list of values
    """
    spi_cs.value(CS_ACTIVE)
    spi_dc.value(0)
    spi.write(bytearray([command]))
    if data is not None:
        spi_dc.value(1)
        spi.write(bytearray(data))
    spi_cs.value(CS_INACTIVE)


def _spi_data(data):
    spi_cs.value(CS_ACTIVE)
    spi_dc.value(1)
    spi.write(bytearray(data))
    spi_cs.value(CS_INACTIVE)

def show():
    spi.init()
    reset.value(0)
    sleep(0.5)
    reset.value(1)
    sleep(0.5)

    _spi_cmd(0x12)
    sleep(1.0)
    _busy_wait()

    _spi_cmd(DRIVER_CONTROL, [ROWS - 1, (ROWS - 1) >> 8, 0x00])
    _spi_cmd(WRITE_DUMMY, [0x1B])
    _spi_cmd(WRITE_GATELINE, [0x0B])
    _spi_cmd(DATA_MODE, [0x03])
    _spi_cmd(SET_RAMXPOS, [0x00, COLS // 8 - 1])
    _spi_cmd(SET_RAMYPOS, [0x00, 0x00, (ROWS - 1) & 0xFF, (ROWS - 1) >> 8])
    _spi_cmd(WRITE_VCOM, [0x70])
    _spi_cmd(WRITE_LUT, LUTS_BLACK)
    _spi_cmd(SET_RAMXCOUNT, [0x00])
    _spi_cmd(SET_RAMYCOUNT, [0x00, 0x00])

    _spi_cmd(WRITE_RAM)
    _spi_data(buf_b)

    _spi_cmd(WRITE_ALTRAM)
    _spi_data(buf_r)

    _busy_wait()
    _spi_cmd(MASTER_ACTIVATE)


clear()

#draw_text("2467", -20, 120, amatic96bs, 2)  # text_len 118
#draw_text("ppm", -145, 120, amatic32bs, 1)  # text_len 37
#draw_text("23.4°C", 105, 56, oswald32bs, 1)  # text_len 98
#draw_text("43%", 47, 95, amatic32bs, 1)

#thresholds 800 for offices, 1000 for schools - above red numbers
# 2000 for headaches - red background white fonts
# display refresh every 6 min or if value diff is more than 10%