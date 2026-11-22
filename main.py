#!/usr/bin/env python3
"""Deterministic, stdlib-only front page for 22 November 2026.

Renders one PNG (1024x1024) to $OUT_DIR/main.png (default /output).
No network, no randomness, no timestamps: two runs are byte-identical.
"""

from __future__ import annotations

import math
import os
import re
import struct
import zlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Canvas constants
# ---------------------------------------------------------------------------

W = 1024
H = 1024
DATE_TEXT = "22 NOVEMBER 2026"

PAPER = (244, 241, 232)
INK = (16, 20, 26)
SUBINK = (74, 81, 90)
BORDER = (198, 194, 183)
ICON_BG = (232, 229, 220)
ICON_LIGHT = (212, 218, 226)
WATER = (126, 142, 154)
RED = (166, 42, 33)
GOLD = (214, 163, 55)

GRID_X = 14
GRID_Y = 158
CARD_W = 492
CARD_H = 194
GUTTER_X = 12
GUTTER_Y = 6

ICON_W = 112
ICON_H = 150
TEXT_X = 128
TEXT_W = CARD_W - TEXT_X - 8  # 356 px

TICKER_Y = 952
TICKER_H = 72
TICKER_X = 96
TICKER_W = W - TICKER_X - 12

# ---------------------------------------------------------------------------
# Embedded 5x7 bitmap font.  Digit zero has a slash so 0 != O.
# ---------------------------------------------------------------------------

FONT: dict[str, tuple[str, ...]] = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "#....", "####.", "....#", "....#", "####."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "|": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "%": ("##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"),
}

for _glyph in FONT.values():
    assert len(_glyph) == 7 and all(len(_row) == 5 for _row in _glyph)


def text_width(text: str, scale: int) -> int:
    """Conservative advance width: 5 ink columns + 1 space, times scale."""
    return len(text) * 6 * scale


# ---------------------------------------------------------------------------
# Canvas primitives
# ---------------------------------------------------------------------------


class Canvas:
    def __init__(self, width: int, height: int, bg: tuple[int, int, int]) -> None:
        self.w = width
        self.h = height
        self.buf = bytearray(bytes(bg) * (width * height))

    def px(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            start = (yy * self.w + x0) * 3
            self.buf[start : start + len(row)] = row

    def poly(self, points: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
        """Even-odd scanline fill of an integer polygon."""
        ys = [p[1] for p in points]
        y0 = max(0, min(ys))
        y1 = min(self.h - 1, max(ys))
        n = len(points)
        for y in range(y0, y1 + 1):
            sample = y + 0.5
            xs: list[float] = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if (ay <= sample < by) or (by <= sample < ay):
                    xs.append(ax + (sample - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(xs[k] + 0.5)
                xb = int(xs[k + 1] + 0.5)
                self.rect(xa, y, xb - xa, 1, color)

    def line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        thickness: int = 1,
    ) -> None:
        """Integer Bresenham line with optional square thickness."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        half = thickness // 2
        while True:
            self.rect(x0 - half, y0 - half, thickness, thickness, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx: int, cy: int, r: int, color: tuple[int, int, int]) -> None:
        for dy in range(-r, r + 1):
            span = math.isqrt(r * r - dy * dy)
            self.rect(cx - span, cy + dy, 2 * span + 1, 1, color)

    def text(
        self,
        x: int,
        y: int,
        text: str,
        scale: int,
        color: tuple[int, int, int],
        max_width: int | None = None,
    ) -> int:
        width = text_width(text, scale)
        if max_width is not None and width > max_width:
            raise ValueError(f"line too wide ({width} > {max_width}): {text!r}")
        for index, char in enumerate(text):
            glyph = FONT.get(char, FONT["?"])
            gx = x + index * 6 * scale
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "#":
                        self.rect(gx + col * scale, y + row * scale, scale, scale, color)
        return width

    def text_center(
        self,
        cx: int,
        y: int,
        text: str,
        scale: int,
        color: tuple[int, int, int],
        max_width: int | None = None,
    ) -> int:
        return self.text(cx - text_width(text, scale) // 2, y, text, scale, color, max_width)


# ---------------------------------------------------------------------------
# Story data: all labels are short, uppercase and faithful to the brief.
# ---------------------------------------------------------------------------

STORIES: list[dict[str, object]] = [
    {
        "region": "EUROPE",
        "color": (140, 29, 24),
        "icon": "ship",
        "head": ("UKRAINIAN DRONES", "HIT CARGO SHIP", "SPARTA II"),
        "sub": (
            "GULF OF FINLAND; SHIP ABLAZE",
            "FINLAND PM: WAR SPILLING",
            "OVER INTO THE BALTIC",
        ),
        "chip": "BALTIC FIRE",
    },
    {
        "region": "NATO",
        "color": (29, 60, 106),
        "icon": "shield",
        "head": ("RUSSIAN MISSILES", "LANDED IN POLAND", "NATO VOWS DEFENSE"),
        "sub": (
            "CHIEF RUTTE PLEDGES TO",
            "DEFEND POLAND",
            "ALLIANCE TOP BODY MEETS",
        ),
        "chip": "DEFENSE PLEDGE",
    },
    {
        "region": "IRAN-US",
        "color": (107, 78, 18),
        "icon": "jet",
        "head": ("IRAN CLAIMS HIT ON", "US F-16 OVER GULF", "US DENIES DAMAGE"),
        "sub": (
            "IRAN: AIR-DEFENSE MISSILE",
            "DAMAGED JET; US DENIES",
            "TRUMP DEFERS STRIKE CALL",
        ),
        "chip": "AFTER NEW YEAR",
    },
    {
        "region": "UKRAINE",
        "color": (31, 94, 100),
        "icon": "bridge",
        "head": ("KERCH BRIDGE", "PARTLY DESTROYED", "UKRAINIAN STRIKES"),
        "sub": (
            "CRIMEAN CROSSING HIT;",
            "RUSSIAN LOGISTICS",
            "SUPPLY LINE STRAINED",
        ),
        "chip": "BRIDGE DAMAGE",
    },
    {
        "region": "WORLD COURT",
        "color": (75, 46, 112),
        "icon": "scales",
        "head": ("UN COURT RULES", "ON MYANMAR", "GENOCIDE CASE"),
        "sub": (
            "EU PRAISES; US CAUTIOUS,",
            "CHINA CRITICAL",
            "DEEP DIVISIONS OVER ICJ",
        ),
        "chip": "WORLD DIVIDED",
    },
    {
        "region": "SUMMIT",
        "color": (110, 43, 69),
        "icon": "flags",
        "head": ("TRUMP, XI, PUTIN", "SUMMIT ENDS;", "INDIA TAKES NOTE"),
        "sub": (
            "NEW DELHI AWAITS",
            "FURTHER DETAILS",
            "OF THE TALKS",
        ),
        "chip": "TRILATERAL TALKS",
    },
    {
        "region": "MIDEAST",
        "color": (138, 78, 18),
        "icon": "tanker",
        "head": ("IRAN STRIKES", "TANKERS; GAZA", "AID TRUCK HIT"),
        "sub": (
            "ISRAELI STRIKE ON A",
            "GAZA FOOD TRUCK",
            "KILLS THREE",
        ),
        "chip": "AID TRUCK STRIKE",
    },
    {
        "region": "SPORTS",
        "color": (30, 90, 59),
        "icon": "trophy",
        "head": ("PSG WIN 3-2, NICE", "NEBRASKA 31", "BEATS #14 OHIO ST."),
        "sub": (
            "LIGUE 1: PSG COMEBACK",
            "COLLEGE FOOTBALL RESULT",
            "NBA: MIL 129 - PHI 132",
        ),
        "chip": "FINAL SCORES",
    },
]

TICKER = (
    "BALTIC SHIP FIRE | NATO DEFENDS POLAND | F-16 CLAIM DENIED | INDIA AWAITS",
    "KERCH BRIDGE DAMAGED | ICJ RULING DIVIDES | PSG 3-2, NEB 31 | GAZA TRUCK",
)

# ---------------------------------------------------------------------------
# Pictograms (flat rectangles / polygons in a 98x136 local box)
# ---------------------------------------------------------------------------


def draw_icon(
    canvas: Canvas, ox: int, oy: int, kind: str, accent: tuple[int, int, int]
) -> None:
    def R(dx: int, dy: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        canvas.rect(ox + dx, oy + dy, w, h, color)

    def L(
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        color: tuple[int, int, int],
        thickness: int = 1,
    ) -> None:
        canvas.line(ox + x0, oy + y0, ox + x1, oy + y1, color, thickness)

    def P(pts: list[tuple[int, int]], color: tuple[int, int, int]) -> None:
        canvas.poly([(ox + px, oy + py) for px, py in pts], color)

    def D(cx: int, cy: int, r: int, color: tuple[int, int, int]) -> None:
        canvas.disc(ox + cx, oy + cy, r, color)

    if kind == "ship":
        for yy in (110, 120, 130):
            R(2, yy, 94, 2, WATER)
        R(18, 83, 62, 9, INK)
        R(21, 85, 56, 5, ICON_LIGHT)
        R(30, 68, 28, 16, INK)
        for wx in (34, 43, 52):
            R(wx, 72, 4, 4, ICON_LIGHT)
        R(44, 54, 2, 14, INK)
        P([(45, 68), (39, 56), (46, 59), (49, 44), (58, 60), (54, 68)], RED)
        P([(48, 66), (45, 58), (50, 60), (52, 52), (56, 64), (53, 66)], GOLD)
        P([(6, 92), (92, 92), (82, 110), (16, 110)], INK)

    elif kind == "shield":
        L(6, 10, 30, 30, RED, 2)
        P([(30, 30), (24, 28), (27, 24)], RED)
        P([(49, 20), (84, 32), (81, 76), (49, 108), (17, 76), (14, 32)], INK)
        P([(49, 26), (78, 36), (75, 73), (49, 100), (23, 73), (20, 36)], ICON_LIGHT)
        P(
            [
                (49, 38), (55, 54), (72, 54), (58, 64), (64, 80),
                (49, 70), (34, 80), (40, 64), (26, 54), (43, 54),
            ],
            accent,
        )

    elif kind == "jet":
        L(68, 52, 62, 72, RED, 2)
        P(
            [
                (70, 18), (74, 32), (88, 28), (78, 40), (88, 52),
                (74, 48), (70, 62), (66, 48), (52, 52), (62, 40),
                (52, 28), (66, 32),
            ],
            RED,
        )
        P(
            [
                (49, 6), (55, 28), (60, 44), (90, 68), (90, 78),
                (60, 68), (58, 92), (70, 108), (70, 114), (49, 106),
                (28, 114), (28, 108), (40, 92), (38, 68), (8, 78),
                (8, 68), (38, 44), (43, 28),
            ],
            INK,
        )
        P([(49, 20), (53, 34), (45, 34)], GOLD)

    elif kind == "bridge":
        for yy in (112, 122, 132):
            R(2, yy, 94, 2, WATER)
        R(8, 52, 14, 62, INK)
        R(76, 52, 14, 62, INK)
        R(5, 52, 20, 4, INK)
        R(73, 52, 20, 4, INK)
        L(16, 56, 44, 88, INK, 2)
        L(84, 56, 56, 88, INK, 2)
        P([(4, 90), (45, 90), (41, 100), (4, 100)], INK)
        P([(53, 90), (94, 90), (94, 100), (57, 100)], INK)
        P([(45, 90), (41, 100), (38, 94)], RED)
        P([(53, 90), (57, 100), (60, 94)], RED)
        R(12, 100, 6, 12, INK)
        R(80, 100, 6, 12, INK)

    elif kind == "scales":
        D(49, 14, 4, INK)
        R(46, 16, 6, 10, INK)
        R(14, 24, 70, 6, INK)
        R(46, 30, 6, 84, INK)
        R(34, 114, 30, 8, INK)
        L(20, 30, 10, 66, INK, 2)
        L(20, 30, 30, 66, INK, 2)
        L(78, 30, 68, 66, INK, 2)
        L(78, 30, 88, 66, INK, 2)
        P([(8, 66), (32, 66), (28, 78), (12, 78)], accent)
        P([(66, 66), (90, 66), (86, 78), (70, 78)], accent)

    elif kind == "flags":
        R(8, 96, 82, 8, INK)
        R(18, 104, 6, 22, INK)
        R(74, 104, 6, 22, INK)
        L(24, 20, 24, 96, INK, 2)
        L(49, 12, 49, 96, INK, 2)
        L(74, 20, 74, 96, INK, 2)
        P([(24, 20), (44, 26), (24, 32)], RED)
        P([(49, 12), (69, 19), (49, 26)], INK)
        P([(74, 20), (94, 26), (74, 32)], GOLD)

    elif kind == "tanker":
        for yy in (112, 122, 132):
            R(2, yy, 94, 2, WATER)
        R(12, 90, 74, 4, INK)
        for cx in (30, 54, 78):
            D(cx, 82, 11, INK)
            D(cx, 82, 9, ICON_LIGHT)
        L(68, 52, 62, 72, RED, 2)
        P(
            [
                (70, 18), (74, 32), (88, 28), (78, 40), (88, 52),
                (74, 48), (70, 62), (66, 48), (52, 52), (62, 40),
                (52, 28), (66, 32),
            ],
            RED,
        )
        P([(5, 94), (93, 94), (83, 112), (15, 112)], INK)

    elif kind == "trophy":
        L(18, 36, 8, 36, INK, 3)
        L(8, 36, 8, 52, INK, 3)
        L(8, 52, 18, 52, INK, 3)
        L(72, 36, 82, 36, INK, 3)
        L(82, 36, 82, 52, INK, 3)
        L(82, 52, 72, 52, INK, 3)
        P([(18, 30), (72, 30), (66, 66), (54, 78), (36, 78), (24, 66)], INK)
        P([(24, 36), (66, 36), (61, 62), (52, 70), (38, 70), (29, 62)], GOLD)
        R(43, 78, 6, 16, INK)
        R(32, 94, 28, 8, INK)
        R(26, 102, 40, 6, INK)
        D(82, 110, 12, INK)
        D(82, 110, 10, PAPER)
        P([(82, 102), (89, 107), (86, 115), (78, 115), (75, 107)], accent)

    else:
        raise ValueError(f"unknown icon: {kind}")


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def draw_card(canvas: Canvas, x: int, y: int, story: dict[str, object]) -> None:
    color = story["color"]
    canvas.rect(x, y, CARD_W, CARD_H, PAPER)

    # Region header bar.
    canvas.rect(x, y, CARD_W, 30, color)
    canvas.text(x + 10, y + 5, str(story["region"]), 3, PAPER, max_width=CARD_W - 20)

    # Pictogram panel.
    bx = x + 8
    by = y + 38
    canvas.rect(bx, by, ICON_W, ICON_H, ICON_BG)
    canvas.rect(bx, by, ICON_W, 1, BORDER)
    canvas.rect(bx, by + ICON_H - 1, ICON_W, 1, BORDER)
    canvas.rect(bx, by, 1, ICON_H, BORDER)
    canvas.rect(bx + ICON_W - 1, by, 1, ICON_H, BORDER)
    draw_icon(canvas, bx + 7, by + 7, str(story["icon"]), color)
    canvas.rect(x + 124, y + 38, 1, ICON_H, BORDER)

    # Three headline lines and three explanatory lines.
    tx = x + TEXT_X
    for index, line in enumerate(story["head"]):
        canvas.text(tx, y + 34 + index * 26, line, 3, INK, max_width=TEXT_W)
    for index, line in enumerate(story["sub"]):
        canvas.text(tx, y + 114 + index * 18, line, 2, SUBINK, max_width=TEXT_W)

    # Status chip closes the bottom of the card.
    chip = str(story["chip"])
    chip_w = text_width(chip, 2) + 14
    canvas.rect(tx, y + 170, chip_w, 20, color)
    canvas.text(tx + 7, y + 173, chip, 2, PAPER, max_width=chip_w - 14)


def render() -> Canvas:
    canvas = Canvas(W, H, PAPER)

    # Masthead.
    canvas.rect(0, 0, W, 8, INK)
    canvas.text_center(W // 2, 16, "WORLD NEWS", 10, INK, max_width=W - 40)
    canvas.rect(0, 88, W, 4, INK)
    canvas.rect(0, 94, W, 56, RED)
    canvas.text_center(W // 2, 98, DATE_TEXT, 7, PAPER, max_width=W - 40)
    canvas.rect(0, 152, W, 4, INK)
    canvas.rect(0, 156, W, 2, PAPER)

    # 2 columns x 4 rows of story cards.
    for index, story in enumerate(STORIES):
        col = index % 2
        row = index // 2
        x = GRID_X + col * (CARD_W + GUTTER_X)
        y = GRID_Y + row * (CARD_H + GUTTER_Y)
        draw_card(canvas, x, y, story)

    # Bottom wire strip.  Scores and keywords only: no dates.
    canvas.rect(0, TICKER_Y, W, TICKER_H, INK)
    canvas.rect(0, TICKER_Y, 84, TICKER_H, RED)
    canvas.text_center(42, TICKER_Y + 25, "WIRE", 3, PAPER, max_width=76)
    for index, line in enumerate(TICKER):
        canvas.text(TICKER_X, TICKER_Y + 18 + index * 24, line, 2, PAPER, max_width=TICKER_W)

    return canvas


# ---------------------------------------------------------------------------
# Validation: sweep the defect checklist before writing any bytes.
# ---------------------------------------------------------------------------


def all_rendered_text() -> list[str]:
    strings: list[str] = ["WORLD NEWS", DATE_TEXT, "WIRE"]
    for story in STORIES:
        strings.append(str(story["region"]))
        strings.extend(story["head"])
        strings.extend(story["sub"])
        strings.append(str(story["chip"]))
    strings.extend(TICKER)
    return strings


def validate() -> None:
    strings = all_rendered_text()

    # Exactly one date, rendered once, and no date-like text anywhere else.
    assert strings.count(DATE_TEXT) == 1
    forbidden = re.compile(r"\b(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\b|\b(?:19|20)\d{2}\b")
    for text in strings:
        if text == DATE_TEXT:
            continue
        assert not forbidden.search(text), f"date-like text: {text!r}"
        assert all(char in FONT for char in text), f"missing glyph in: {text!r}"

    # Every line fits its container; measured, never eyeballed.
    for story in STORIES:
        assert text_width(str(story["region"]), 3) <= CARD_W - 20
        for line in story["head"]:
            assert text_width(line, 3) <= TEXT_W, f"headline clipped: {line!r}"
        for line in story["sub"]:
            assert text_width(line, 2) <= TEXT_W, f"sub-line clipped: {line!r}"
        chip = str(story["chip"])
        assert text_width(chip, 2) + 14 <= TEXT_W, f"chip clipped: {chip!r}"
    for line in TICKER:
        assert text_width(line, 2) <= TICKER_W, f"ticker clipped: {line!r}"
    assert text_width("WORLD NEWS", 10) <= W - 40
    assert text_width(DATE_TEXT, 7) <= W - 40
    assert text_width("WIRE", 3) <= 76

    assert len(STORIES) == 8
    assert CARD_W * 2 + GUTTER_X + GRID_X * 2 == W
    assert GRID_Y + CARD_H * 4 + GUTTER_Y * 3 == TICKER_Y


# ---------------------------------------------------------------------------
# Hand-rolled PNG writer
# ---------------------------------------------------------------------------


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def encode_png(canvas: Canvas) -> bytes:
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter type 0 (None)
        start = y * stride
        raw.extend(canvas.buf[start : start + stride])
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )


def main() -> None:
    validate()
    png = encode_png(render())
    out_dir = Path(os.environ.get("OUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "main.png").write_bytes(png)


if __name__ == "__main__":
    main()
