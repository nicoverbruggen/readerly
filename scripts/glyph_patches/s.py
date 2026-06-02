#!/usr/bin/env python3
"""Thicken the bottom stroke of lowercase 's' (Regular).

GLYPH_Y_FLOOR (the baseline-correction pass) clamps s's sub-baseline points up
to y=0, flattening the bottom and thinning the lower stroke — the top of s
still overshoots the x-height (~22 units) but the bottom was cut flat at the
baseline, so the letter reads thin/lopsided at the bottom.

Rather than re-introduce a sub-baseline overshoot (which would undo the floor's
baseline alignment), this thickens the stroke *upward*: it raises the inner
edge of the bottom sweep (the underside of the spine, points 32–37) so the
black stroke grows while the outer edge stays flat on the baseline. Point 32
(the terminal/inner-edge corner) is raised with the rest to avoid a notch.

Idempotent and self-guarding.

    python3 scripts/glyph_patches/s.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import run_cli  # noqa: E402

CHAR = "s"
LABEL = "s bottom inner edge"

# Inner edge of the bottom sweep, as built (un-patched).
ORIGINAL = {32: (299, 121), 33: (327, 116), 34: (356, 114),
            35: (394, 111), 36: (428, 111), 37: (562, 111)}
# Raise the whole run +30 (keeps the profile, lifts the inner edge upward).
TARGET = {32: (299, 151), 33: (327, 146), 34: (356, 144),
          35: (394, 141), 36: (428, 141), 37: (562, 141)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
