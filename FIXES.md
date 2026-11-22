# FIXES.md — defect sweep, one defect per line

## Defects found and fixed

- [x] Card 4 headline "BY UKRAINIAN STRIKES" measured 360 px against the 356 px text column; shortened to "UKRAINIAN STRIKES" (306 px).
- [x] Bottom ticker left roughly 220 px of unused dark space on the right; extended both lines with "INDIA AWAITS" and "GAZA TRUCK" (876 px and 864 px of the available 916 px).
- [x] Summit pictogram sat low in its panel with blank space above and stubby table legs; raised the three flags by 8 px and extended the legs to the bottom of the icon box.
- [x] Re-verification: card 8 headline "PSG WIN 3-2 AT NICE" was the tightest line in the layout at 339 px of ink in the 356 px text column — only 18 px of clearance; retightened to "PSG WIN 3-2, NICE" (303 px of ink, 53 px of line clearance), keeping win, score and venue. Card 8's minimum clearance rises to 42 px and the layout-wide minimum from 18 px to 23 px.

## Sweep checks (all clean)

- [x] Date: the only date text in the image is "22 NOVEMBER 2026"; a regex sweep of every rendered string rejects other month names and 19xx/20xx years.
- [x] Clipping: every headline, sub-line, chip, ticker line, header label and masthead line is measured against its container before any pixel is written; the decoded PNG confirms the tightest card line now has 23 px of ink clearance.
- [x] Digits: digit glyphs are used for 3-2, 31, #14, 129 and 132; zero carries a slash so it cannot be mistaken for O.
- [x] Artifacts: left/right margins, all three horizontal gutters, the vertical gutter and the masthead rule gap contain zero non-paper pixels; no counts or legend labels appear beside icons.
- [x] Whitespace: decoded-PNG pixel counts show icon-panel ink density of 13.5-29.6% and text-column density of 14.4-20.0% across all eight cards, with no empty or prefix-only cards.
- [x] Coverage: eight cards carry the eight verified stories; every headline and status word renders in full.
- [x] Determinism: baseline re-verified before the fix with two runs of `OUT_DIR=out python3 main.py` (both sha256 19d49d2877de95a691681137d0ddecf10ab62e2ca60acfddc4ba8d0576e2d2a2); after the single fix, two more runs both produced sha256 c9f3614ee6239a065c66507d659dcfe828ac686d04b218b1b3012d8b55dc9255.
- [x] File: valid 1024x1024 RGB PNG with IHDR/IDAT/IEND, all CRCs and scanline filters verified, 24,675 bytes (well under 1 MiB).
