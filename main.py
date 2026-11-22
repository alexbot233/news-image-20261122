#!/usr/bin/env python3
"""Front page of 22 November 2026 -- deterministic, standard-library PNG renderer.

The page is drawn directly into an RGB pixel buffer; a small hand-rolled PNG
encoder writes the result.  No randomness, clocks, network calls or external
packages are used, so repeated runs are byte-identical.
"""

import math
import os
import re
import struct
import zlib

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------

WIDTH = 1024
HEIGHT = 1024

PAPER = (246, 242, 232)
PANEL = (255, 254, 249)
INK = (22, 27, 33)
MUTED = (96, 101, 106)
RULE = (198, 192, 177)
DARK = (19, 24, 30)
WHITE = (255, 255, 255)
GOLD = (226, 176, 62)
FIRE = (213, 79, 36)
DATE = "22 NOVEMBER 2026"

MARGIN = 24
COL_W = 480
COL_X = (24, 520)
ROW_Y = (170, 364, 558, 752)
CARD_H = 182
ROW_GAP = 12

ICON_W = 140
ICON_H = 132
TEXT_X_OFFSET = 160
TEXT_W = 306

# ---------------------------------------------------------------------------
# 5x7 bitmap font.  Every glyph is seven rows of five pixels; '1' is ink.
# Zero carries a diagonal slash so that it can never be read as the letter O.
# ---------------------------------------------------------------------------

FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10011", "10101", "10101", "10101", "11001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "00100", "00100", "00000", "00100", "00100", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    ";": ("00000", "00100", "00100", "00000", "00100", "00100", "01000"),
}

ALL_STRINGS = []


# ---------------------------------------------------------------------------
# Pixel primitives
# ---------------------------------------------------------------------------

def new_canvas():
    return bytearray(WIDTH * HEIGHT * 3)


def put(canvas, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        canvas[i] = color[0]
        canvas[i + 1] = color[1]
        canvas[i + 2] = color[2]


def rect(canvas, x, y, w, h, color):
    if w <= 0 or h <= 0:
        return
    row = bytes(color) * w
    for yy in range(max(0, y), min(HEIGHT, y + h)):
        i = (yy * WIDTH + max(0, x)) * 3
        end = (yy * WIDTH + min(WIDTH, x + w)) * 3
        canvas[i:end] = row[: end - i]


def frame(canvas, x, y, w, h, color):
    rect(canvas, x, y, w, 1, color)
    rect(canvas, x, y + h - 1, w, 1, color)
    rect(canvas, x, y, 1, h, color)
    rect(canvas, x + w - 1, y, 1, h, color)


def hline(canvas, x, y, w, color, thick=1):
    rect(canvas, x, y, w, thick, color)


def vline(canvas, x, y, h, color, thick=1):
    rect(canvas, x, y, thick, h, color)


def line(canvas, x0, y0, x1, y1, color, thick=2):
    steps = max(abs(x1 - x0), abs(y1 - y0))
    if steps == 0:
        rect(canvas, x0 - thick // 2, y0 - thick // 2, thick, thick, color)
        return
    for i in range(steps + 1):
        px = round(x0 + (x1 - x0) * i / steps)
        py = round(y0 + (y1 - y0) * i / steps)
        rect(canvas, px - thick // 2, py - thick // 2, thick, thick, color)


def polygon(canvas, points, color):
    ys = [p[1] for p in points]
    for yy in range(max(0, math.floor(min(ys))), min(HEIGHT, math.ceil(max(ys)) + 1)):
        xs = []
        for i, (xa, ya) in enumerate(points):
            xb, yb = points[(i + 1) % len(points)]
            if ya == yb:
                continue
            if min(ya, yb) <= yy < max(ya, yb):
                xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            left = math.ceil(xs[i])
            right = math.floor(xs[i + 1])
            rect(canvas, left, yy, right - left + 1, 1, color)


def disc(canvas, cx, cy, radius, color):
    for dy in range(-radius, radius + 1):
        half = int(math.sqrt(max(0, radius * radius - dy * dy)))
        rect(canvas, cx - half, cy + dy, 2 * half + 1, 1, color)


def mix(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


# ---------------------------------------------------------------------------
# Text: measured before it is drawn, and every string is registered so the
# final date sweep can inspect exactly what reached the page.
# ---------------------------------------------------------------------------

def text_width(value, scale):
    if not value:
        return 0
    return (len(value) * 6 - 1) * scale


def text(canvas, x, y, value, scale, color, max_width=None):
    if value != value.upper():
        raise ValueError("font is uppercase only: %r" % value)
    for ch in value:
        if ch not in FONT:
            raise ValueError("missing glyph %r in %r" % (ch, value))
    width = text_width(value, scale)
    if max_width is not None and width > max_width:
        raise ValueError("text overflow: %r is %d px, limit %d px" % (value, width, max_width))
    if x < 0 or y < 0 or x + width > WIDTH or y + 7 * scale > HEIGHT:
        raise ValueError("text off canvas: %r at (%d,%d)" % (value, x, y))
    ALL_STRINGS.append(value)
    for pos, ch in enumerate(value):
        glyph = FONT[ch]
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    rect(canvas, x + (pos * 6 + col) * scale, y + row * scale, scale, scale, color)
    return width


def centered_text(canvas, cy, value, scale, color, max_width):
    width = text_width(value, scale)
    if width > max_width:
        raise ValueError("text overflow: %r is %d px, limit %d px" % (value, width, max_width))
    text(canvas, (WIDTH - width) // 2, cy, value, scale, color, max_width)


# ---------------------------------------------------------------------------
# Pictograms: flat, label-free shapes that fill the 140x132 icon panels.
# ---------------------------------------------------------------------------

def icon_ship(canvas, x, y, dark, hot):
    for dy in (108, 117, 126):
        rect(canvas, x + 10, y + dy, 120, 3, dark)
    polygon(canvas, [(x + 12, y + 76), (x + 128, y + 76),
                     (x + 112, y + 104), (x + 28, y + 104)], dark)
    rect(canvas, x + 22, y + 83, 96, 4, hot)
    rect(canvas, x + 54, y + 54, 38, 22, dark)
    rect(canvas, x + 62, y + 47, 20, 7, dark)
    rect(canvas, x + 71, y + 26, 3, 21, dark)
    polygon(canvas, [(x + 18, y + 30), (x + 40, y + 26), (x + 30, y + 40)], hot)
    line(canvas, x + 30, y + 27, x + 30, y + 43, dark, 2)
    polygon(canvas, [(x + 100, y + 22), (x + 122, y + 28), (x + 106, y + 38)], hot)
    line(canvas, x + 112, y + 25, x + 108, y + 42, dark, 2)
    polygon(canvas, [(x + 56, y + 54), (x + 66, y + 28), (x + 74, y + 54)], FIRE)
    polygon(canvas, [(x + 76, y + 54), (x + 88, y + 34), (x + 94, y + 54)], GOLD)
    polygon(canvas, [(x + 88, y + 54), (x + 98, y + 40), (x + 104, y + 54)], FIRE)


def icon_nato(canvas, x, y, dark, hot):
    polygon(canvas, [(x + 70, y + 12), (x + 122, y + 30), (x + 118, y + 76),
                     (x + 70, y + 116), (x + 22, y + 76), (x + 18, y + 30)], dark)
    polygon(canvas, [(x + 70, y + 24), (x + 110, y + 38), (x + 107, y + 72),
                     (x + 70, y + 102), (x + 33, y + 72), (x + 30, y + 38)], hot)
    polygon(canvas, [(x + 70, y + 36), (x + 78, y + 54), (x + 98, y + 54),
                     (x + 82, y + 66), (x + 88, y + 86), (x + 70, y + 74),
                     (x + 52, y + 86), (x + 58, y + 66), (x + 42, y + 54),
                     (x + 62, y + 54)], dark)
    line(canvas, x + 20, y + 8, x + 30, y + 22, dark, 3)
    line(canvas, x + 120, y + 8, x + 110, y + 22, dark, 3)


def icon_jet(canvas, x, y, dark, hot):
    polygon(canvas, [(x + 8, y + 44), (x + 60, y + 34), (x + 102, y + 42),
                     (x + 130, y + 52), (x + 104, y + 58), (x + 78, y + 70),
                     (x + 56, y + 66), (x + 40, y + 54), (x + 8, y + 56)], dark)
    polygon(canvas, [(x + 60, y + 34), (x + 52, y + 14), (x + 76, y + 36)], dark)
    line(canvas, x + 22, y + 112, x + 80, y + 62, hot, 5)
    polygon(canvas, [(x + 80, y + 62), (x + 68, y + 60), (x + 78, y + 50)], hot)
    points = []
    for i in range(12):
        angle = i * math.pi / 6
        radius = 18 if i % 2 == 0 else 7
        points.append((x + 86 + math.cos(angle) * radius, y + 58 + math.sin(angle) * radius))
    polygon(canvas, points, FIRE)
    disc(canvas, x + 86, y + 58, 5, dark)


def icon_bridge(canvas, x, y, dark, hot):
    for dy in (106, 116, 126):
        rect(canvas, x + 8, y + dy, 124, 3, dark)
    rect(canvas, x + 28, y + 28, 12, 76, dark)
    rect(canvas, x + 100, y + 28, 12, 76, dark)
    rect(canvas, x + 20, y + 84, 46, 10, dark)
    rect(canvas, x + 74, y + 84, 46, 10, dark)
    polygon(canvas, [(x + 66, y + 84), (x + 74, y + 78), (x + 70, y + 90),
                     (x + 78, y + 86), (x + 74, y + 96)], hot)
    for left in (34, 106):
        for k in range(3):
            line(canvas, x + left, y + 34, x + left - 26 + k * 13, y + 82, dark, 2)
            line(canvas, x + left, y + 34, x + left + 26 - k * 13, y + 82, dark, 2)
    line(canvas, x + 20, y + 26, x + 120, y + 26, dark, 4)
    polygon(canvas, [(x + 60, y + 54), (x + 70, y + 42), (x + 76, y + 58),
                     (x + 68, y + 68)], FIRE)


def icon_scales(canvas, x, y, dark, hot):
    disc(canvas, x + 70, y + 66, 44, hot)
    rect(canvas, x + 44, y + 112, 52, 8, dark)
    rect(canvas, x + 67, y + 24, 6, 88, dark)
    rect(canvas, x + 26, y + 36, 88, 6, dark)
    disc(canvas, x + 70, y + 26, 7, dark)
    for cx in (38, 102):
        line(canvas, x + cx, y + 42, x + cx, y + 76, dark, 2)
        polygon(canvas, [(x + cx - 22, y + 76), (x + cx + 22, y + 76),
                         (x + cx + 14, y + 94), (x + cx - 14, y + 94)], dark)
    rect(canvas, x + 32, y + 104, 76, 5, dark)


def icon_summit(canvas, x, y, dark, hot):
    rect(canvas, x + 10, y + 92, 120, 14, dark)
    rect(canvas, x + 18, y + 106, 104, 8, hot)
    figures = ((34, 54, 20), (70, 46, 24), (106, 54, 20))
    for cx, top, height in figures:
        disc(canvas, x + cx, y + top, 10, dark)
        rect(canvas, x + cx - 15, y + top + 12, 30, height, dark)
    for cx, flag_color in ((34, dark), (70, hot), (106, FIRE)):
        rect(canvas, x + cx, y + 12, 2, 28, dark)
        polygon(canvas, [(x + cx + 2, y + 13), (x + cx + 22, y + 19),
                         (x + cx + 2, y + 25)], flag_color)
    rect(canvas, x + 30, y + 82, 80, 4, hot)


def icon_tankers(canvas, x, y, dark, hot):
    polygon(canvas, [(x + 8, y + 34), (x + 132, y + 34),
                     (x + 118, y + 60), (x + 22, y + 60)], dark)
    rect(canvas, x + 24, y + 18, 22, 16, dark)
    for start in (52, 78, 104):
        rect(canvas, x + start, y + 18, 18, 16, hot)
    for dy in (66, 74):
        rect(canvas, x + 14, y + dy, 112, 3, dark)
    rect(canvas, x + 22, y + 88, 32, 28, dark)
    rect(canvas, x + 54, y + 80, 58, 36, dark)
    rect(canvas, x + 60, y + 86, 46, 8, hot)
    disc(canvas, x + 34, y + 118, 7, dark)
    disc(canvas, x + 92, y + 118, 7, dark)
    points = []
    for i in range(12):
        angle = i * math.pi / 6
        radius = 16 if i % 2 == 0 else 6
        points.append((x + 118 + math.cos(angle) * radius,
                       y + 82 + math.sin(angle) * radius))
    polygon(canvas, points, FIRE)


def icon_sports(canvas, x, y, dark, hot):
    disc(canvas, x + 50, y + 52, 38, dark)
    polygon(canvas, [(x + 50, y + 36), (x + 64, y + 46), (x + 59, y + 62),
                     (x + 41, y + 62), (x + 36, y + 46)], hot)
    for point in ((x + 50, y + 18), (x + 84, y + 44), (x + 72, y + 80),
                  (x + 28, y + 80), (x + 16, y + 44)):
        line(canvas, point[0], point[1], x + 50, y + 52, hot, 3)
    polygon(canvas, [(x + 82, y + 98), (x + 98, y + 82), (x + 124, y + 88),
                     (x + 132, y + 104), (x + 116, y + 118), (x + 90, y + 114)], dark)
    line(canvas, x + 102, y + 85, x + 112, y + 113, hot, 4)
    rect(canvas, x + 18, y + 110, 60, 6, dark)
    rect(canvas, x + 24, y + 122, 48, 4, hot)


ICONS = (icon_ship, icon_nato, icon_jet, icon_bridge,
         icon_scales, icon_summit, icon_tankers, icon_sports)

# ---------------------------------------------------------------------------
# The eight stories.  Headlines stay at or below 16 characters so scale-3
# glyphs fit the 306 px text column; details/status lines are measured too.
# ---------------------------------------------------------------------------

STORIES = (
    {
        "label": "EUROPE",
        "accent": (35, 72, 116),
        "second": GOLD,
        "head": ("UKRAINIAN DRONES", "HIT SPARTA II"),
        "detail": ("RUSSIAN SHIP ABLAZE", "IN GULF OF FINLAND"),
        "status": "PM: WAR SPILLS TO BALTIC",
    },
    {
        "label": "NATO",
        "accent": (29, 58, 92),
        "second": (104, 152, 196),
        "head": ("RUTTE PLEDGES", "TO DEFEND POLAND"),
        "detail": ("RUSSIAN MISSILES", "LANDED IN POLAND"),
        "status": "ALLIANCE TOP BODY MEETS",
    },
    {
        "label": "IRAN-US",
        "accent": (124, 55, 43),
        "second": GOLD,
        "head": ("IRAN CLAIMS HIT", "ON US F-16 JET"),
        "detail": ("MISSILE OVER GULF", "US DENIES DAMAGE"),
        "status": "DECISION AFTER NEW YEAR",
    },
    {
        "label": "UKRAINE",
        "accent": (26, 84, 140),
        "second": GOLD,
        "head": ("KERCH BRIDGE HIT", "PARTLY DESTROYED"),
        "detail": ("UKRAINIAN STRIKES", "CRIMEAN CROSSING"),
        "status": "RUSSIAN SUPPLY STRAINED",
    },
    {
        "label": "WORLD COURT",
        "accent": (86, 62, 120),
        "second": (186, 166, 214),
        "head": ("ICJ RULES ON", "MYANMAR GENOCIDE"),
        "detail": ("EU PRAISES, US CAUTIOUS", "CHINA CRITICAL"),
        "status": "DIVIDED OVER THE COURT",
    },
    {
        "label": "TRILATERAL",
        "accent": (110, 74, 34),
        "second": GOLD,
        "head": ("TRUMP-XI-PUTIN", "SUMMIT WRAPS UP"),
        "detail": ("INDIA TAKES NOTE", "AWAITS DETAILS"),
        "status": "INDIA AWAITS DETAILS",
    },
    {
        "label": "MIDEAST",
        "accent": (150, 70, 28),
        "second": (232, 178, 92),
        "head": ("TANKERS STRUCK", "IN IRAN ATTACKS"),
        "detail": ("ISRAELI HIT ON", "GAZA FOOD TRUCK"),
        "status": "3 KILLED IN GAZA HIT",
    },
    {
        "label": "SPORTS",
        "accent": (30, 100, 66),
        "second": GOLD,
        "head": ("PSG COMES BACK", "3-2 AT NICE"),
        "detail": ("NEBRASKA 31,", "VS #14 OHIO STATE"),
        "status": "NBA MIL 129 - PHI 132",
    },
)

TICKER_LINES = (
    "BALTIC SPILL  |  POLAND DEFENSE  |  KERCH BRIDGE  |  ICJ SPLIT  |  F-16 DENIED",
    "TRUMP DEFERS  |  3 DEAD IN GAZA  |  PSG 3-2  |  NEB 31  |  MIL 129 - PHI 132",
)


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

def draw_masthead(canvas):
    hline(canvas, MARGIN, 12, WIDTH - 2 * MARGIN, INK, 2)
    hline(canvas, MARGIN, 17, WIDTH - 2 * MARGIN, INK, 1)
    centered_text(canvas, 28, "WORLD NEWS", 8, INK, 700)
    hline(canvas, MARGIN, 90, WIDTH - 2 * MARGIN, RULE, 2)

    rect(canvas, MARGIN, 98, WIDTH - 2 * MARGIN, 50, DARK)
    rect(canvas, MARGIN + 18, 112, 18, 22, GOLD)
    rect(canvas, WIDTH - MARGIN - 36, 112, 18, 22, GOLD)
    centered_text(canvas, 105, DATE, 5, WHITE, 900)
    hline(canvas, MARGIN, 158, WIDTH - 2 * MARGIN, INK, 2)


def draw_card(canvas, story, index, cx, cy):
    accent = story["accent"]
    rect(canvas, cx, cy, COL_W, CARD_H, PANEL)
    frame(canvas, cx, cy, COL_W, CARD_H, RULE)

    rect(canvas, cx + 1, cy + 1, COL_W - 2, 30, accent)
    text(canvas, cx + 12, cy + 5, story["label"], 3, WHITE, 440)

    ix = cx + 10
    iy = cy + 38
    rect(canvas, ix, iy, ICON_W, ICON_H, mix(accent, PAPER, 0.86))
    frame(canvas, ix, iy, ICON_W, ICON_H, mix(accent, PAPER, 0.55))
    ICONS[index](canvas, ix + 2, iy + 2, mix(accent, DARK, 0.18), story["second"])

    tx = cx + TEXT_X_OFFSET
    text(canvas, tx, cy + 40, story["head"][0], 3, INK, TEXT_W)
    text(canvas, tx, cy + 64, story["head"][1], 3, INK, TEXT_W)
    text(canvas, tx, cy + 94, story["detail"][0], 2, MUTED, TEXT_W)
    text(canvas, tx, cy + 112, story["detail"][1], 2, MUTED, TEXT_W)

    rect(canvas, tx, cy + 136, TEXT_W, 32, accent)
    text(canvas, tx + 8, cy + 145, story["status"], 2, WHITE, TEXT_W - 16)


def draw_ticker(canvas):
    rect(canvas, MARGIN, 948, WIDTH - 2 * MARGIN, 56, DARK)
    centered_text(canvas, 954, TICKER_LINES[0], 2, WHITE, WIDTH - 2 * MARGIN - 24)
    hline(canvas, MARGIN + 16, 973, WIDTH - 2 * MARGIN - 32, GOLD, 1)
    centered_text(canvas, 980, TICKER_LINES[1], 2, WHITE, WIDTH - 2 * MARGIN - 24)


def validate_strings():
    if ALL_STRINGS.count(DATE) != 1:
        raise ValueError("the contest date must be rendered exactly once")
    months = ("JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY",
              "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")
    for value in ALL_STRINGS:
        if value == DATE:
            continue
        for month in months:
            if month in value:
                raise ValueError("unexpected date-like month in %r" % value)
        if re.search(r"(?:19|20)[0-9]{2}", value):
            raise ValueError("unexpected year in %r" % value)


def render():
    ALL_STRINGS.clear()
    canvas = new_canvas()
    rect(canvas, 0, 0, WIDTH, HEIGHT, PAPER)
    draw_masthead(canvas)
    for index, story in enumerate(STORIES):
        col = index % 2
        row = index // 2
        draw_card(canvas, story, index, COL_X[col], ROW_Y[row])
    draw_ticker(canvas)
    validate_strings()
    return canvas


# ---------------------------------------------------------------------------
# PNG encoder (RGB, 8 bit, no ancillary chunks and therefore no timestamps)
# ---------------------------------------------------------------------------

def chunk(tag, payload):
    body = tag + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def png_bytes(canvas):
    stride = WIDTH * 3
    raw = bytearray((HEIGHT * (stride + 1)))
    for y in range(HEIGHT):
        start = y * stride
        dst = y * (stride + 1)
        raw[dst] = 0
        raw[dst + 1:dst + 1 + stride] = canvas[start:start + stride]
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    image = png_bytes(render())
    out_dir = os.environ.get("OUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as handle:
        handle.write(image)


if __name__ == "__main__":
    main()
