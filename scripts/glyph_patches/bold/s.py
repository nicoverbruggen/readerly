#!/usr/bin/env python3
"""Thicken the bottom stroke of lowercase 's' (Bold).

Bold counterpart of regular/s.py. GLYPH_Y_FLOOR clamps s's sub-baseline points
to y=0, flattening the bottom and thinning the lower stroke. Thicken it
*upward* by raising the inner edge of the bottom sweep (points 32–37), keeping
the outer edge flat on the baseline. Point 32 (the terminal/inner-edge corner)
is raised with the rest to avoid a notch. Idempotent and self-guarding.

    python3 scripts/glyph_patches/bold/s.py path/to/Readerly-Bold.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "s"
LABEL = "s bottom inner edge"

# Inner edge of the bottom sweep, as built (un-patched).
ORIGINAL = {32: (302, 141), 33: (329, 137), 34: (356, 135),
            35: (396, 132), 36: (432, 132), 37: (556, 132)}
# Raise the whole run +30 (keeps the profile, lifts the inner edge upward).
TARGET = {32: (302, 171), 33: (329, 167), 34: (356, 165),
          35: (396, 162), 36: (432, 162), 37: (556, 162)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
