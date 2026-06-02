#!/usr/bin/env python3
"""Soften the bowl→foot bracket spur on lowercase 'd' (Bold).

Bold counterpart of regular/d.py. The right serif foot's inner bracket
(on-curve point 35) juts up ~147 units; lower the peak and ease the off-curve
control (36).

Note: unlike Regular, Bold 'd' does NOT need its next on-curve point lowered.
There the analogous point (37) already sits at y=72 — well below the lowered
control — so the bowl rises 72 → 80 → 88 cleanly with no plateau. Idempotent
and self-guarding.

    python3 scripts/glyph_patches/bold/d.py path/to/Readerly-Bold.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "d"
LABEL = "d bowl/foot bracket"

ORIGINAL = {35: (836, 147), 36: (778, 103)}
# Lower the spur; 37(72) is already below, so 37 → 36 → 35 stays monotonic.
TARGET = {35: (836, 88), 36: (783, 80)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
