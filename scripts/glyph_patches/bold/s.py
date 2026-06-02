#!/usr/bin/env python3
"""Thicken the bottom and top strokes of lowercase 's' (Bold).

Bold counterpart of regular/s.py. The s terminals read thin at small sizes;
this grows the lower and upper strokes inward, leaving the outer edges in
place, by moving the inner edge of each sweep toward the centre:

  - bottom sweep: raise the underside of the spine (points 32-37) by +30
  - top sweep:    lower the underside of the top arc (points 6-11) by -30

The corner points (32 and 6) move with their runs to avoid a notch. Absolute
coordinates, idempotent and self-guarding.

    python3 scripts/glyph_patches/bold/s.py path/to/Readerly-Bold.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "s"
LABEL = "s top + bottom inner edges"

# Inner edges of the top and bottom sweeps, as built (un-patched).
ORIGINAL = {
    6: (694, 929), 7: (679, 933), 8: (663, 936),
    9: (606, 947), 10: (563, 947), 11: (465, 947),
    32: (302, 141), 33: (329, 137), 34: (356, 135),
    35: (396, 132), 36: (432, 132), 37: (556, 132),
}
# Top run lowered -30, bottom run raised +30: both inner edges move inward,
# thickening the strokes while the outer edges stay put.
TARGET = {
    6: (694, 899), 7: (679, 903), 8: (663, 906),
    9: (606, 917), 10: (563, 917), 11: (465, 917),
    32: (302, 171), 33: (329, 167), 34: (356, 165),
    35: (396, 162), 36: (432, 162), 37: (556, 162),
}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
