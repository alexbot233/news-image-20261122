# CONTEXT.md — news-image-20261122: "Front page of 22 November 2026"

## Task
main.py (Python 3.13 STDLIB ONLY) renders ONE PNG image (<=1024x1024, <=1 MiB) that reads as the FRONT PAGE of a world newspaper dated **22 November 2026**. It must name the day: render "22 NOVEMBER 2026" prominently in the masthead. NO other date anywhere in the image.

Honor OUT_DIR env (default /output); write the PNG to $OUT_DIR/main.png. Deterministic: two runs byte-identical (no randomness, no timestamps, no network).

## Verified stories for the 8 cards (all reported fact, no hype)
1. EUROPE: Russian cargo ship SPARTA II hit by Ukrainian drones in the Gulf of Finland, catches fire; Finland PM: war "spilling over" to the Baltic.
2. NATO: After Russian missiles landed in Poland, NATO chief Rutte pledges to defend Poland; alliance's top body meets.
3. IRAN-US: Iran claims its air-defense missile damaged a US F-16 over the Gulf; US denies. Trump defers any Iran strike decision to after the New Year.
4. UKRAINE: Ukrainian strikes partially destroy the Kerch (Crimean) bridge, straining Russian logistics.
5. ICJ: UN top court rules on Myanmar genocide case; EU praises ruling, US reacts cautiously, China critical — global divisions over the court.
6. TRILATERAL: Trump-Xi-Putin summit wraps; India says it "takes note" and awaits details.
7. MIDEAST: Iran strikes tankers; Israeli hit on a Gaza food truck kills 3.
8. SPORTS: PSG 3-2 comeback win at Nice (Ligue 1); Nebraska 31, #14 Ohio State (college football). Sub-line can carry: NBA MIL 129 - PHI 132.

## Design criteria (judge is a vision model, in priority order)
1. Names the day: contest date 22 NOVEMBER 2026 prominent; ZERO other dates in the image (no tickers/footnotes/masthead labels with other dates).
2. ~8 consequential stories across regions and fields (war, courts, summit, Mideast, sports, science), not one country/beat.
3. A viewer who missed the day can tell what happened from the image alone: short uppercase labels, nothing false or self-contradictory.
4. Faithful to the reported facts above; no speculation presented as fact.
5. Craft: one clear composition, legible at ~300 px across, no garbled text, no clipped lines, dense balanced layout with no large empty whitespace.

## Verified defect checklist (EVERY line must be swept before finishing)
- No date text other than 22 NOVEMBER 2026, anywhere.
- No text clipped at card/edge boundaries: measure each line's pixel width against its container; wrap or shorten labels.
- Digits must come from digit glyphs — 0 and O must look distinct; verify numbers like "3-2", "31", "129" render as digits.
- No stray tiny artifacts (counts, legend labels) floating near icons.
- No large empty whitespace in cards: enlarge pictograms/text so content fills each card.
- Every headline/status word fully rendered (not clipped to a prefix).

## Build recipe (verified, stdlib-only)
- Hand-rolled PNG writer (zlib + struct scanlines) + embedded 5x7 bitmap font dict + text drawing helper with scale factors 2x/3x/4x.
- Layout: masthead band ("WORLD NEWS" + "22 NOVEMBER 2026" on a highlight band), 2x4 grid of story cards (region/color header bar, flat pictogram from rectangles/polygons, 1-2 line label, small sub-line), bottom ticker strip of extra headlines (ticker may carry scores/keywords but NO dates).
- Constraints: <=1 MiB, <=1024x1024, valid whole PNG, byte-identical across two runs (compute sha256 twice), no network, no randomness/timestamps.
- Verify locally with OUT_DIR=out python3 main.py, then inspect the render at full size; fix defects via FIXES.md (one defect per line) and iterate until the sweep is clean.
- README.md must carry the competition's three live make.fun badge links for slug news-image-20261122 with owner/repo alexbot233/news-image-20261122.

## SCORER REQUIREMENT (critical)
- The harness scorer checks that the program writes /output/entry.png. The output file MUST be named entry.png (honor OUT_DIR env, default /output).
- Do NOT read git history or any backup of a previous main.py; write main.py from scratch based on this CONTEXT.md only.
