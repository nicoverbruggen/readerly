#!/usr/bin/env python3
"""Resolve the bowl→foot junction on lowercase 'd' (Bold).

Bold counterpart of regular/d.py. The right serif foot's inner bracket
(on-curve 35) juts up as a spur, and the run from the bowl up into it
(39-38-37-36-35) read as a lump rather than one curve. This:

  - lowers the spur (35) to a gentle bracket;
  - keeps 36-37-38 collinear, so 37 is a smooth passing node and 39→38→37→36
    is a single continuous quadratic (no kink at 37);
  - drops that run so the bottom-right stroke optically matches the bowl's top
    thickness (≈ the 51↔3 distance, ~185 units in Bold).

Absolute coordinates, idempotent and self-guarding.

    python3 scripts/glyph_patches/bold/d.py path/to/Readerly-Bold.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "d"
LABEL = "d bowl/foot junction"

# Spur (35) and the bowl→foot run, as built (un-patched).
ORIGINAL = {35: (836, 147), 36: (778, 103), 37: (735, 72), 38: (674, 29)}
# Soft bracket + collinear 36-37-38 (37 = midpoint) so the run is one smooth
# curve; lowered to match the bowl's top stroke thickness.
TARGET = {35: (836, 44), 36: (783, 28), 37: (735, 18), 38: (687, 8)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
