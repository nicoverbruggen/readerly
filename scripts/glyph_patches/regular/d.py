#!/usr/bin/env python3
"""Soften the bowl→foot bracket spur on lowercase 'd' (Regular).

Same construction as 'u': the right serif foot's inner bracket (on-curve
point 35) juts up ~155 units between the foot and the bowl. Lower the spur
peak and ease the adjacent off-curve control.

Unlike 'u', 'd' also needs point 37 lowered. In 'u' the analogous on-curve
point (25) sits at y=76, so the bowl rises 76→84→92 into a clean peak. In 'd'
that point was left at y=84 — level with the control and only 6 below the peak
— so the top of the bowl read as a flat plateau rather than a curve. Dropping
37 to y=76 mirrors 'u' (76→84→90) and restores the smooth rise. The foot's
lifted toe is intentionally left as-is, matching 'u'. Idempotent/self-guarding.

    python3 scripts/glyph_patches/regular/d.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "d"
LABEL = "d bowl/foot bracket"

ORIGINAL = {35: (871, 155), 36: (815, 113), 37: (772, 84)}
# Lower the spur and drop 37 so 37 → 36 → 35 rises 76 → 84 → 90 like 'u'.
TARGET = {35: (871, 90), 36: (820, 84), 37: (772, 76)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
