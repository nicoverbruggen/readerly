#!/usr/bin/env python3
"""Soften the bowl→foot bracket spur on lowercase 'b' (Bold).

Bold counterpart of regular/b.py. The left serif foot's inner bracket (on-curve
point 38) juts up ~170 units; lower the peak and ease the off-curve control
(37). Idempotent and self-guarding.

    python3 scripts/glyph_patches/bold/b.py path/to/Readerly-Bold.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "b"
LABEL = "b bowl/foot bracket"

ORIGINAL = {38: (429, 170), 37: (454, 111)}
# Lower the spur; keep 36(72) → 37 → 38 monotonic so the bowl stays smooth.
TARGET = {38: (429, 88), 37: (454, 80)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
