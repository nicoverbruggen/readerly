#!/usr/bin/env python3
"""Simplify the lower bowl→foot junction on lowercase 'd' (Regular).

The original outline has two adjacent on-curve points at the foot underside
(33/34), creating a flat shelf before the bowl rises into the foot. The bowl
bottom also has an on-curve stop plus a run of consecutive off-curves
(37-40), so the green-side curve is broken into too many implied segments.
Remove those extra nodes, keep one low notch and one bowl control, then move
the surviving lower-bowl anchor so the curve rises cleanly into the foot peak.
Idempotent/self-guarding.

    python3 scripts/glyph_patches/regular/d.py path/to/Readerly-Regular.ttf
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib import run_cli  # noqa: E402

CHAR = "d"
LABEL = "d bowl/foot junction"

ORIGINAL = {
    33: (956, -22),
    34: (921, -22),
    35: (871, 155),
    36: (815, 113),
    37: (772, 84),
    38: (706, 38),
    39: (618, -8),
    40: (554, -23),
    41: (522, -23),
    42: (380, -23),
}
TARGET = {
    34: (918, -36),
    35: (882, 52),
    36: (663, -44),
    41: (427, -8),
    42: (345, 5),
}
REMOVE = {33, 37, 38, 39, 40}

if __name__ == "__main__":
    raise SystemExit(run_cli(CHAR, ORIGINAL, TARGET, LABEL, REMOVE))
