#!/usr/bin/env python3
"""Simplify the bowl→foot junction on lowercase 'u' (Regular).

The serif foot's inner bracket (on-curve point 23) juts up ~162 units between
the bowl bottom and the foot, pinching the bowl's foot-side terminal into a
sharp spur. This lowers the bracket peak, removes an extra on-curve stop in the
lower run, and retunes the adjacent controls so the bowl flows into the foot.
Idempotent and self-guarding.

    python3 scripts/glyph_patches/regular/u.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "u"
LABEL = "u bowl/foot junction"

# Points touched (pre-patch coordinates expected in the un-patched build).
ORIGINAL = {
    5: (664, 186),
    23: (831, 162),
    24: (772, 110),
    25: (730, 76),
    26: (678, 33),
}
TARGET = {
    5: (670, 186),
    23: (831, 92),
    24: (831, 92),
    26: (693, 21),
}
REMOVE = {25}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL, REMOVE))
