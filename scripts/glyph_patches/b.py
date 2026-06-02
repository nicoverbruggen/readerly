#!/usr/bin/env python3
"""Soften the bowl→foot bracket spur on lowercase 'b' (Regular).

Mirror of the 'u' fix: the left serif foot's inner bracket (on-curve point 38)
juts up ~149 units between the bowl and the foot. Lower the spur peak and ease
the off-curve control approaching it. Idempotent and self-guarding.

    python3 scripts/glyph_patches/b.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import run_cli  # noqa: E402

CHAR = "b"
LABEL = "b bowl/foot bracket"

ORIGINAL = {38: (349, 149), 37: (374, 106)}
# Lower the spur; keep 36(74) → 37 → 38 monotonic so the bowl stays smooth.
TARGET = {38: (349, 88), 37: (374, 81)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
