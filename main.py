#!/usr/bin/env python3
"""AURHAVEN - a travel poster for a place that isn't there.

Generates a 1024x1024 PNG travel poster with the Python standard library
only (zlib + struct for the PNG encoder). No network, no external files,
deterministic output: the same run always produces the same picture.

The place: AURHAVEN, a cliffside town of lantern-lit white stairways above
a violet-teal lagoon at golden dusk. Its landmark is a tall lighthouse
whose warm amber beam sweeps over floating glass-sail boats.

Run:  python3 main.py        (writes /output/entry.png)
"""

import math
import os
import struct
import zlib

W = H = 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- palette
SKY_TOP = (36, 20, 82)       # deep violet, top of sky
SKY_MID = (98, 46, 126)      # violet-mauve
SKY_LOW = (226, 128, 66)     # amber at the horizon
SUN_CORE = (255, 214, 130)
SUN_GLOW = (255, 170, 80)
CLOUD = (244, 196, 168)
CLIFF_FAR = (74, 44, 110)
CLIFF_NEAR = (48, 28, 84)
CLIFF_DARK = (30, 16, 58)
TOWER = (250, 240, 224)      # warm white lighthouse
TOWER_SHADE = (196, 170, 196)
LAMP = (255, 196, 90)
BEAM = (255, 190, 90)
LAGOON_TOP = (44, 122, 138)  # teal
LAGOON_BOT = (18, 52, 96)
SHIMMER = (255, 190, 110)
SAIL = (214, 240, 240)
HULL = (28, 18, 52)
LANTERN = (255, 196, 96)
TEXT_MAIN = (255, 244, 214)
TEXT_SHADOW = (32, 14, 64)
TAGLINE = (255, 214, 150)

HORIZON = 640  # y where lagoon meets sky

# ---------------------------------------------------------------- canvas
# buf[y] is a bytearray of W*3 RGB bytes.
buf = [bytearray(W * 3) for _ in range(H)]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp3(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def set_px(x, y, color, alpha=1.0):
    """Set one pixel, alpha-blending over what is already there."""
    if 0 <= x < W and 0 <= y < H:
        i = x * 3
        row = buf[y]
        if alpha >= 1.0:
            row[i] = color[0]
            row[i + 1] = color[1]
            row[i + 2] = color[2]
        else:
            row[i] = int(color[0] * alpha + row[i] * (1.0 - alpha))
            row[i + 1] = int(color[1] * alpha + row[i + 1] * (1.0 - alpha))
            row[i + 2] = int(color[2] * alpha + row[i + 2] * (1.0 - alpha))


def fill_row(y, color):
    buf[y][:] = bytes(color) * W


def fill_rect(x0, y0, x1, y1, color, alpha=1.0):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            set_px(x, y, color, alpha)


def disc(cx, cy, r, color, alpha=1.0):
    """Filled circle."""
    r2 = r * r
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0, r2 - dy * dy)))
        for x in range(max(0, cx - dx), min(W, cx + dx + 1)):
            set_px(x, y, color, alpha)


def ellipse(cx, cy, rx, ry, color, alpha=1.0):
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        for x in range(max(0, cx - dx), min(W, cx + dx + 1)):
            set_px(x, y, color, alpha)


def poly(points, color, alpha=1.0):
    """Filled polygon (scanline fill)."""
    if len(points) < 3:
        return
    ys = [p[1] for p in points]
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x1, y1p = points[i]
            x2, y2p = points[(i + 1) % n]
            if y1p == y2p:
                continue
            if (y1p <= y < y2p) or (y2p <= y < y1p):
                xs.append(x1 + (y - y1p) * (x2 - x1) / (y2p - y1p))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(xs[i]))
            xb = min(W - 1, int(xs[i + 1]))
            for x in range(xa, xb + 1):
                set_px(x, y, color, alpha)


def thick_line(x0, y0, x1, y1, width, color, alpha=1.0):
    """Simple thick line drawn as a stack of discs."""
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(steps + 1):
        t = i / steps
        disc(int(lerp(x0, x1, t)), int(lerp(y0, y1, t)), width // 2,
             color, alpha)


# ---------------------------------------------------------------- sky
def draw_sky():
    for y in range(HORIZON):
        if y < 340:
            t = y / 340.0
            c = lerp3(SKY_TOP, SKY_MID, t)
        else:
            t = (y - 340) / (HORIZON - 340)
            c = lerp3(SKY_MID, SKY_LOW, t * t)
        fill_row(y, c)


def draw_sun():
    cx, cy = 660, 492
    # smooth radial glow: per-pixel falloff, no hard ring edges
    R = 230
    for y in range(max(0, cy - R), min(HORIZON, cy + R + 1)):
        dy = y - cy
        for x in range(max(0, cx - R), min(W, cx + R + 1)):
            dx = x - cx
            d = math.sqrt(dx * dx + dy * dy)
            if d < R:
                t = 1.0 - d / R
                set_px(x, y, SUN_GLOW, 0.22 * t * t)
    disc(cx, cy, 58, SUN_CORE)
    disc(cx, cy, 44, (255, 232, 170))


def draw_clouds():
    # soft, low-opacity ellipses high in the sky
    clouds = [
        (180, 150, 150, 26), (300, 132, 110, 20), (120, 210, 120, 20),
        (820, 120, 130, 22), (920, 168, 100, 18), (520, 96, 120, 18),
        (640, 200, 150, 20), (60, 300, 110, 18), (940, 300, 120, 18),
    ]
    for cx, cy, rx, ry in clouds:
        # each cloud is a small cluster of overlapping puffs, so it
        # reads as a soft cloud rather than one flat oval
        ellipse(cx, cy, rx, ry, CLOUD, 0.09)
        ellipse(cx - int(rx * 0.45), cy + 6, int(rx * 0.6),
                int(ry * 0.8), CLOUD, 0.08)
        ellipse(cx + int(rx * 0.45), cy + 6, int(rx * 0.6),
                int(ry * 0.8), CLOUD, 0.08)
        ellipse(cx, cy - 8, int(rx * 0.55), int(ry * 0.6), CLOUD, 0.07)


# ---------------------------------------------------------------- cliffs
def draw_cliffs():
    # far headland, left
    poly([(0, HORIZON), (0, 520), (120, 470), (250, 500), (330, HORIZON)],
         CLIFF_FAR)
    # near cliff, left, with a flat top the stairways run down
    poly([(0, HORIZON), (0, 430), (90, 400), (210, 440), (300, 500),
          (330, 560), (300, HORIZON)], CLIFF_NEAR)
    # right cliff the lighthouse stands on
    poly([(1024, HORIZON), (1024, 380), (940, 360), (850, 400),
          (800, 470), (830, 560), (860, HORIZON)], CLIFF_NEAR)
    # darkest foreground sliver at the waterline, left
    poly([(0, HORIZON), (0, 600), (140, 640), (260, 660), (200, HORIZON)],
         CLIFF_DARK)


def draw_stairways():
    """White stairways zig-zagging down the left cliff, lantern dots."""
    # staircase 1: down the left cliff face
    steps = [(96, 408), (130, 436), (168, 452), (150, 478), (190, 500),
             (168, 528), (210, 552), (186, 580), (228, 604), (206, 632)]
    for i in range(len(steps) - 1):
        thick_line(steps[i][0], steps[i][1], steps[i + 1][0],
                   steps[i + 1][1], 7, (238, 228, 244), 0.9)
    # staircase 2: short run on the right cliff
    steps2 = [(930, 392), (905, 430), (928, 462), (902, 500), (922, 540)]
    for i in range(len(steps2) - 1):
        thick_line(steps2[i][0], steps2[i][1], steps2[i + 1][0],
                   steps2[i + 1][1], 6, (238, 228, 244), 0.9)
    # lantern dots along both stairways and cliff tops
    lanterns = [(96, 404), (130, 432), (168, 448), (150, 474), (190, 496),
                (168, 524), (210, 548), (186, 576), (228, 600), (206, 628),
                (930, 388), (905, 426), (928, 458), (902, 496), (922, 536),
                (60, 424), (240, 470), (880, 396), (980, 372)]
    for x, y in lanterns:
        disc(x, y, 6, LANTERN, 0.35)
        disc(x, y, 3, LANTERN, 1.0)


# ---------------------------------------------------------------- lighthouse
def draw_lighthouse():
    # tower: slightly tapered, warm white with a shaded side
    poly([(868, 640), (872, 330), (906, 330), (910, 640)], TOWER)
    poly([(892, 640), (892, 330), (906, 330), (910, 640)], TOWER_SHADE)
    # horizontal bands
    fill_rect(870, 430, 908, 442, (214, 120, 90))
    fill_rect(871, 520, 907, 532, (214, 120, 90))
    # gallery platform and railing
    fill_rect(860, 322, 918, 332, (40, 26, 66))
    for x in range(864, 916, 8):
        fill_rect(x, 306, x + 2, 322, (40, 26, 66))
    # lamp room: glass + dome
    fill_rect(872, 282, 906, 306, LAMP)
    fill_rect(874, 286, 904, 302, (255, 226, 150))
    poly([(868, 282), (910, 282), (898, 262), (880, 262)], (40, 26, 66))
    disc(889, 260, 5, LAMP)
    # the amber beam sweeping down-left from the lamp onto the lagoon,
    # passing below the sun so the sun stays clear of it
    poly([(889, 300), (60, 700), (60, 790), (889, 308)], BEAM, 0.26)
    poly([(889, 302), (300, 712), (300, 760), (889, 306)], BEAM, 0.28)
    # bright lamp glow
    disc(889, 294, 26, LAMP, 0.45)
    disc(889, 294, 14, (255, 236, 180), 0.9)


# ---------------------------------------------------------------- lagoon
def draw_lagoon():
    for y in range(HORIZON, H):
        t = (y - HORIZON) / (H - HORIZON)
        fill_row(y, lerp3(LAGOON_TOP, LAGOON_BOT, t * t))
    # sun reflection: one smooth tapered column under the sun, fading
    # with depth, with a few short shimmering dashes inside it
    poly([(660 - 22, HORIZON + 4), (660 + 22, HORIZON + 4),
          (660 + 90, H - 30), (660 - 90, H - 30)], SHIMMER, 0.07)
    for i, y in enumerate(range(HORIZON + 30, H - 40, 46)):
        w = 30 + i * 9
        x0 = 660 - w // 2 + ((i * 53) % 40) - 20
        for x in range(x0, x0 + w):
            set_px(x, y, SHIMMER, 0.30)
            set_px(x, y + 1, SHIMMER, 0.22)
    # scattered short shimmer dashes across the lagoon
    for k in range(90):
        x = 30 + (k * 173) % 950
        y = HORIZON + 24 + (k * 97) % 330
        ln = 14 + (k * 29) % 42
        a = 0.08 + 0.10 * ((k * 7) % 3) / 2.0
        for xx in range(x, min(1010, x + ln)):
            set_px(xx, y, (190, 230, 235), a)
    # beam light pooling on the water where it lands, left side
    for y in range(700, 800, 2):
        for x in range(70, 320):
            set_px(x, y, BEAM, 0.10)


def draw_boats():
    # (hull x, hull y, scale) - glass-sail boats on the lagoon
    boats = [(300, 760, 1.0), (560, 860, 1.25), (820, 800, 0.85)]
    for bx, by, s in boats:
        mast_top = by - int(120 * s)
        # two glass sails, pale and translucent
        poly([(bx, mast_top), (bx, by - 6),
              (bx - int(52 * s), by - 6)], SAIL, 0.92)
        poly([(bx + 4, mast_top + int(18 * s)), (bx + 4, by - 6),
              (bx + int(38 * s), by - 6)], (168, 214, 220), 0.92)
        # mast
        thick_line(bx, mast_top, bx, by - 4, 3, HULL)
        # hull
        poly([(bx - int(58 * s), by), (bx + int(58 * s), by),
              (bx + int(40 * s), by + int(20 * s)),
              (bx - int(40 * s), by + int(20 * s))], HULL)
        # warm cabin light
        disc(bx, by + 6, 3, LANTERN)
        # reflection
        poly([(bx - int(40 * s), by + int(24 * s)),
              (bx + int(40 * s), by + int(24 * s)),
              (bx + int(26 * s), by + int(46 * s)),
              (bx - int(26 * s), by + int(46 * s))], SAIL, 0.18)


# ---------------------------------------------------------------- bitmap font
# 5x7 glyphs, "#" = on. Only the letters this poster needs, plus friends.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(text, x, y, scale, color, alpha=1.0):
    """Draw text with the built-in 5x7 font, scaled up by `scale`."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch.upper(), FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    fill_rect(cx + col_i * scale, y + row_i * scale,
                              cx + (col_i + 1) * scale,
                              y + (row_i + 1) * scale, color, alpha)
        cx += 6 * scale


def draw_title():
    name = "AURHAVEN"
    scale = 13
    w = text_width(name, scale)
    x = (W - w) // 2
    y = 118
    # dark shadow, offset down-right, for legibility against the sky
    draw_text(name, x + 5, y + 6, scale, TEXT_SHADOW, 0.85)
    draw_text(name, x, y, scale, TEXT_MAIN)
    # thin gold rule under the name
    fill_rect(x + 40, y + 7 * scale + 16, x + w - 40, y + 7 * scale + 20,
              TAGLINE)
    # tagline, smaller
    tag = "WHERE THE LIGHT NEVER SETS"
    tscale = 4
    tw = text_width(tag, tscale)
    tx = (W - tw) // 2
    ty = y + 7 * scale + 34
    draw_text(tag, tx + 2, ty + 2, tscale, TEXT_SHADOW, 0.8)
    draw_text(tag, tx, ty, tscale, TAGLINE)


# ---------------------------------------------------------------- frame
def draw_frame():
    for t in range(6):
        for x in range(W):
            set_px(x, t, (24, 12, 48))
            set_px(x, H - 1 - t, (24, 12, 48))
        for y in range(H):
            set_px(t, y, (24, 12, 48))
            set_px(W - 1 - t, y, (24, 12, 48))


# ---------------------------------------------------------------- PNG writer
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter type 0 (none)
        raw.extend(buf[y])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype, data):
        c = struct.pack(">I", len(data)) + ctype + data
        c += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    draw_sky()
    draw_clouds()
    draw_cliffs()
    draw_stairways()
    draw_lighthouse()
    # sun after the lighthouse so its disc sits in front of the beam
    draw_sun()
    draw_lagoon()
    draw_boats()
    draw_title()
    draw_frame()
    size = write_png(OUT)
    print(f"wrote {OUT}: {W}x{H}, {size} bytes")


if __name__ == "__main__":
    main()
