#!/usr/bin/env python3
"""Thicken the bottom and top strokes of lowercase 's' (Regular).

The s terminals read thin at small sizes. This grows the lower and upper
strokes inward, leaving the outer edges (baseline overshoot and x-height) in
place, by moving the inner edge of each sweep toward the centre:

  - bottom sweep: raise the underside of the spine (points 32-37) by +30
  - top sweep:    lower the underside of the top arc (points 6-11) by -30

The corner points (32 and 6) move with their runs to avoid a notch. Absolute
coordinates, idempotent and self-guarding.

    python3 scripts/glyph_patches/regular/s.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "s"
LABEL = "s top + bottom inner edges"

# Inner edges of the top and bottom sweeps, as built (un-patched).
ORIGINAL = {
    6: (647, 939), 7: (636, 942), 8: (625, 944),
    9: (565, 958), 10: (517, 958), 11: (409, 958),
    32: (299, 121), 33: (327, 116), 34: (356, 114),
    35: (394, 111), 36: (428, 111), 37: (562, 111),
}
# Top run lowered -30, bottom run raised +30: both inner edges move inward,
# thickening the strokes while the outer edges stay put.
TARGET = {
    6: (647, 909), 7: (636, 912), 8: (625, 914),
    9: (565, 928), 10: (517, 928), 11: (409, 928),
    32: (299, 151), 33: (327, 146), 34: (356, 144),
    35: (394, 141), 36: (428, 141), 37: (562, 141),
}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
