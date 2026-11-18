#!/usr/bin/env python3
"""news-image-20261117 — make.fun bounty entry.

A newspaper front page summing up Tuesday 17 November 2026 in one image.
Pure Python 3.13 stdlib, fully procedural, deterministic: draws a 1024x1024
PNG pixel by pixel (no assets, no network, fixed seed) and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (245, 240, 224)
INK = (18, 18, 18)
SKY = (148, 186, 222)
SEA = (38, 88, 138)
SEA_DARK = (24, 62, 102)
STEEL = (96, 96, 100)
DECK = (58, 58, 64)
FIRE = (228, 116, 18)
FIRE_Y = (250, 198, 42)
FIRE_R = (198, 38, 28)
SMOKE = (112, 112, 112)
SMOKE_L = (150, 150, 150)
HULL = (64, 48, 44)
TABLE = (122, 82, 42)
WALL = (214, 224, 232)
WHITE = (255, 255, 255)
FLAG_RED = (222, 32, 32)
FLAG_BLUE = (42, 62, 164)
FLAG_YEL = (250, 210, 40)
SUIT = (40, 40, 48)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows, bit 4 = leftmost column.
F = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "—": (0, 0, 0, 0b11111, 0, 0, 0),
    "•": (0, 0, 0b00100, 0b01110, 0b01110, 0b00100, 0),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "(": (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ")": (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
}

# ---------------------------------------------------------------- canvas
px = bytearray(W * H * 3)


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            put(xx, yy, c)


def hline(x0, x1, y, c, t=1):
    for t_ in range(t):
        for xx in range(x0, x1 + 1):
            put(xx, y + t_, c)


def vline(x, y0, y1, c, t=1):
    for t_ in range(t):
        for yy in range(y0, y1 + 1):
            put(x + t_, yy, c)


def line(x0, y0, x1, y1, c, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        for a in range(t):
            for b in range(t):
                put(x0 + a, y0 + b, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                put(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    # scanline fill of a triangle
    ys = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = ys
    for y in range(ay, cy + 1):
        if y < by:
            t = (y - ay) / max(1, by - ay)
            xa = ax + (bx - ax) * t
        else:
            t = (y - by) / max(1, cy - by)
            xa = bx + (cx - bx) * t
        t2 = (y - ay) / max(1, cy - ay)
        xb = ax + (cx - ax) * t2
        for xx in range(int(min(xa, xb)), int(max(xa, xb)) + 1):
            put(xx, y, c)


def text(s, x, y, scale, c):
    for ch in s:
        g = F.get(ch, F[" "])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row >> (4 - col) & 1:
                    rect(x + col * scale, y + r * scale, scale, scale, c)
        x += 6 * scale


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def text_c(s, cx, y, scale, c):
    text(s, cx - text_w(s, scale) // 2, y, scale, c)


def wrap(s, scale, max_w):
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def panel(x, y, w, h, head_lines, scene):
    rect(x, y, w, 3, INK)
    rect(x, y + h - 3, w, 3, INK)
    vline(x, y, y + h - 1, INK, 3)
    vline(x + w - 3, y, y + h - 1, INK, 3)
    sx, sy, sw, sh = x + 10, y + 10, 348, h - 20
    scene(sx, sy, sw, sh)
    vline(sx + sw + 8, y + 10, y + h - 11, INK, 2)
    tx = sx + sw + 24
    tw = x + w - 12 - tx
    lh = 7 * 4 + 12
    total = lh * len(head_lines) - 12
    ty = y + (h - total) // 2
    for i, ln in enumerate(head_lines):
        text(ln, tx, ty + i * lh, 4, INK)


# ---------------------------------------------------------------- scenes
def scene_bridge(x, y, w, h):
    rect(x, y, w, h, SKY)
    sea_y = y + int(h * 0.62)
    rect(x, sea_y, w, y + h - sea_y, SEA)
    for k in range(4):
        wy = sea_y + 14 + k * 16
        hline(x + 12 + (k % 2) * 40, x + w - 30 - (k % 2) * 30, wy, SEA_DARK, 3)
    # bridge deck: left span intact, right span collapsed into the water
    deck_y = y + int(h * 0.42)
    rect(x, deck_y, int(w * 0.42), 12, DECK)
    line(x + int(w * 0.58), deck_y + 6, x + w - 8, sea_y + 26, DECK, 12)
    # pillars
    rect(x + 30, deck_y + 12, 12, sea_y - deck_y - 6, STEEL)
    rect(x + int(w * 0.30), deck_y + 12, 12, sea_y - deck_y - 6, STEEL)
    rect(x + w - 40, sea_y - 8, 12, 34, STEEL)
    # gap: fire + smoke where the span broke
    gx = x + int(w * 0.50)
    tri(gx - 34, deck_y + 8, gx - 8, deck_y - 52, gx + 6, deck_y + 8, FIRE)
    tri(gx - 14, deck_y + 8, gx + 4, deck_y - 66, gx + 22, deck_y + 8, FIRE_Y)
    tri(gx + 8, deck_y + 8, gx + 22, deck_y - 40, gx + 36, deck_y + 8, FIRE_R)
    circle(gx - 6, deck_y - 74, 16, SMOKE)
    circle(gx + 14, deck_y - 92, 20, SMOKE_L)
    circle(gx + 30, deck_y - 70, 13, SMOKE)
    # road markings on the intact span
    for k in range(5):
        rect(x + 14 + k * 26, deck_y + 4, 14, 3, (220, 200, 60))


def scene_tanker(x, y, w, h):
    rect(x, y, w, h, SKY)
    sea_y = y + int(h * 0.60)
    rect(x, sea_y, w, y + h - sea_y, SEA)
    for k in range(3):
        wy = sea_y + 16 + k * 18
        hline(x + 20 + (k % 2) * 50, x + w - 40 - (k % 2) * 40, wy, SEA_DARK, 3)
    # hull
    hy = sea_y - 26
    rect(x + 14, hy, w - 60, 34, HULL)
    tri(x + w - 46, hy, x + w - 6, hy + 17, x + w - 46, hy + 34, HULL)
    rect(x + 14, hy - 22, 60, 22, (170, 60, 40))   # containers
    rect(x + 78, hy - 22, 60, 22, (60, 120, 70))
    rect(x + 142, hy - 22, 60, 22, (200, 160, 40))
    rect(x + 206, hy - 34, 26, 34, (220, 220, 220))  # funnel
    # fire plume midship (narrower, so funnel and containers stay visible)
    fx = x + int(w * 0.55)
    tri(fx - 30, hy - 20, fx - 10, hy - 78, fx + 2, hy - 20, FIRE)
    tri(fx - 12, hy - 20, fx + 2, hy - 96, fx + 18, hy - 20, FIRE_Y)
    tri(fx + 4, hy - 20, fx + 18, hy - 64, fx + 32, hy - 20, FIRE_R)
    circle(fx - 8, hy - 88, 13, SMOKE)
    circle(fx + 10, hy - 106, 16, SMOKE_L)
    circle(fx + 24, hy - 86, 11, SMOKE)
    # mines in the water
    for mx, my in ((x + 60, sea_y + 46), (x + w - 90, sea_y + 58)):
        circle(mx, my, 9, INK)
        for dx, dy in ((-12, 0), (12, 0), (0, -12), (0, 12), (-9, -9), (9, -9)):
            line(mx, my, mx + dx, my + dy, INK, 2)


def scene_summit(x, y, w, h):
    rect(x, y, w, h, WALL)
    # three flags on poles
    poles = [
        (x + 52, "CN", FLAG_RED),
        (x + int(w * 0.5), "US", None),
        (x + w - 52, "RU", None),
    ]
    for px_, tag, solid in poles:
        vline(px_, y + 26, y + h - 58, INK, 4)
        # right-hand flag flies to the LEFT of its pole so it stays in-scene
        fx0 = px_ - 58 if tag == "RU" else px_ + 4
        fy0, fw, fh = y + 26, 54, 40
        if tag == "CN":
            rect(fx0, fy0, fw, fh, FLAG_RED)
            circle(fx0 + 14, fy0 + 12, 5, FLAG_YEL)
            circle(fx0 + 30, fy0 + 8, 3, FLAG_YEL)
            circle(fx0 + 34, fy0 + 18, 3, FLAG_YEL)
        elif tag == "US":
            for s in range(7):
                rect(fx0, fy0 + s * 6, fw, 6, FLAG_RED if s % 2 == 0 else WHITE)
            rect(fx0, fy0, 28, 24, FLAG_BLUE)
            for r_ in range(3):
                for c_ in range(3):
                    put(fx0 + 4 + c_ * 8, fy0 + 4 + r_ * 7, WHITE)
        else:
            rect(fx0, fy0, fw, 14, WHITE)
            rect(fx0, fy0 + 14, fw, 13, FLAG_BLUE)
            rect(fx0, fy0 + 27, fw, 13, FLAG_RED)
        text_c(tag, fx0 + fw // 2, y + 76, 2, INK)
    # table + three seated silhouettes
    ty = y + h - 58
    rect(x + 8, ty, w - 16, 44, TABLE)
    rect(x + 8, ty, w - 16, 6, (90, 58, 28))
    for cx_ in (x + 52, x + int(w * 0.5), x + w - 52):
        rect(cx_ - 26, ty - 24, 52, 24, SUIT)
        circle(cx_, ty - 34, 15, SUIT)


# ---------------------------------------------------------------- PNG writer
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def write_png(path):
    raw = b"".join(b"\x00" + bytes(px[y * W * 3:(y + 1) * W * 3]) for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as fh:
        fh.write(data)


# ---------------------------------------------------------------- page
def main():
    rect(0, 0, W, H, PAPER)
    # masthead
    text_c("17 NOVEMBER 2026", W // 2, 34, 8, INK)
    text_c("WORLD NEWS IN ONE IMAGE", W // 2, 104, 4, INK)
    rect(24, 146, W - 48, 6, INK)
    rect(24, 156, W - 48, 2, INK)
    # three panels
    panel(24, 172, W - 48, 238,
          ["UKRAINE HITS CRIMEA", "BRIDGE AGAIN —", "RUSSIA STRIKES KYIV", "BRIDGES"],
          scene_bridge)
    panel(24, 422, W - 48, 238,
          ["TANKERS HIT BY MINES", "NEAR HORMUZ", "IRAN DRONES HIT US", "RADAR IN BAHRAIN"],
          scene_tanker)
    panel(24, 672, W - 48, 238,
          ["XI • TRUMP • PUTIN", "TO MEET THURSDAY", "IN SHENZHEN"],
          scene_summit)
    # ticker
    rect(24, 922, W - 48, 78, INK)
    tick = [
        "ALSO: JAPAN SCRAMBLES JETS AFTER SUSPECTED RUSSIAN AIRSPACE VIOLATION",
        "US LOSES MEASLES ELIMINATION STATUS • PENTAGON FAILS AUDIT FOR 9TH YEAR",
        "UK SANCTIONS ISRAELI SETTLEMENT FIRMS • WEST URGES ISRAEL TO OPEN GAZA CROSSINGS",
    ]
    for i, ln in enumerate(tick):
        text_c(ln, W // 2, 934 + i * 20, 2, PAPER)
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    write_png(os.path.join(out, "entry.png"))


if __name__ == "__main__":
    main()
