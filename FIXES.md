# FIXES.md — defect sweep, one defect per line

## Defects found and fixed

- [x] `rect()` computed its row end offset from `x` without adding the row index, so only scanline 0 was painted and the rest of the 1024x1024 page decoded as black; both slice bounds now include `yy * WIDTH`.
- [x] Ticker line 2 measured 970 px against a 952 px container; shortened `NEBRASKA 31` to `NEB 31`, leaving 910 px of ink.
- [x] `icon_bridge` passed bare local x values (34/106) to `line()` for its suspension cables, leaking dark diagonals into the left page margin; prefixed the panel origin `x`.
- [x] `icon_scales` used bare local `cx` values for its cords and pans, leaking purple marks into the left page margin; prefixed the panel origin `x`.
- [x] Card 1 attributed the attack to generic "drones" only; rewrote it as `UKRAINIAN DRONES / HIT SPARTA II` with `RUSSIAN SHIP ABLAZE / IN GULF OF FINLAND`.
- [x] The date was drawn at 4x in the masthead band and read as understated; enlarged it to 5x (475 px wide, 35 px tall) inside the 50 px highlight band.
- [x] `render()` kept appending to the module-level string registry, so a second in-process render failed date validation; the registry is now cleared at the start of every render.
- [x] The verification script read IHDR at byte 17 instead of 16 and falsely reported a 262144x262152 image; corrected the offset before trusting the gutter sweep.

## Sweep checks (all clean)

- [x] Date: `22 NOVEMBER 2026` renders exactly once; every other registered string is rejected if it contains a month name or a 19xx/20xx year; the PNG has only IHDR/IDAT/IEND, so there is no metadata timestamp.
- [x] Clipping: all 52 rendered strings are measured against their containers before drawing; minimum reserved clearance is 4 px (12 px of actual chip padding on the tightest status line), with no text off canvas.
- [x] Digits: `3-2`, `31`, `NEB 31`, `#14`, `129`, `132` and `F-16` all come from digit glyphs; `0` carries a diagonal slash and is visibly distinct from the round `O`.
- [x] Artifacts: decoded PNG shows zero non-paper pixels in the left/right margins, the vertical gutter, all three row gutters, the masthead gap, the grid-to-ticker gap and the bottom margin; no labels float beside icons.
- [x] Whitespace: every card carries 55–57% overall ink and 34–38% ink in its text column; icon panels are filled with flat pictograms.
- [x] Coverage: eight cards carry the eight verified stories, with region headers, two-line headlines, two detail lines, a status chip and a label-free pictogram; every status word renders in full.
- [x] Determinism: two fresh processes with different `OUT_DIR` values produced the same sha256, `a5a851f208e06dc26817133068568445c6a4901e4c643a522d4c568206c01037`.
- [x] File: valid 1024x1024 RGB PNG (all chunk CRCs and scanline filters verified), 23,361 bytes — well under 1 MiB — written as `entry.png` to `$OUT_DIR` (default `/output`).
