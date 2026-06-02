#!/usr/bin/env python3
"""Soften the bowl→foot bracket spur on lowercase 'u' (Regular).

The serif foot's inner bracket (on-curve point 23) juts up ~162 units between
the bowl bottom and the foot, pinching the bowl's foot-side terminal into a
sharp spur. This lowers the bracket peak and eases the adjacent off-curve
control point so the bowl flows into the foot. Idempotent and self-guarding.

    python3 scripts/glyph_patches/u.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import run_cli  # noqa: E402

CHAR = "u"
LABEL = "u bowl/foot bracket"

# Points touched (pre-patch coordinates expected in the un-patched build).
ORIGINAL = {23: (831, 162), 24: (772, 110)}
# Lower the spur peak and ease the bowl entry into the foot. Keep the bowl
# descent monotonic (23 → 24 → 25 strictly decreasing) so no wiggle appears.
TARGET = {23: (831, 92), 24: (789, 84)}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL))
