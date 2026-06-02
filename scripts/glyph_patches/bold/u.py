#!/usr/bin/env python3
"""Soften the bowl→foot bracket spur on lowercase 'u' (Bold).

Bold counterpart of regular/u.py. The serif foot's inner bracket (on-curve
point 24) juts up ~167 units; lower the peak and ease the off-curve control
(25) so the bowl flows into the foot. Idempotent and self-guarding.

    python3 scripts/glyph_patches/bold/u.py path/to/Readerly-Bold.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "u"
LABEL = "u bowl/foot bracket"

ORIGINAL = {24: (828, 167), 25: (768, 113)}
# Lower the spur; keep 24 → 25 → 26(78) monotonic so the bowl stays smooth.
TARGET = {24: (828, 92), 25: (773, 84)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
