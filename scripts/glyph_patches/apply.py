#!/usr/bin/env python3
"""Apply every per-glyph outline patch to the given font(s).

    python3 scripts/glyph_patches/apply.py FONT.ttf [FONT.ttf ...]

Authored for the Regular style. Each patch is idempotent and self-guarding, so
running on a font that lacks the expected outlines (a different style, or an
already-patched font) is a no-op skip rather than a corruption. Exit code is
non-zero only if a patch was skipped because the outline was unexpected.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import apply_patch  # noqa: E402
import u, b, d, s  # noqa: E402

PATCHES = [u, b, d, s]


def apply_all(path):
    """Apply all patches to one font. Returns {char: applied|already|skip}."""
    return {m.CHAR: apply_patch(path, m.CHAR, m.ORIGINAL, m.TARGET, m.LABEL)
            for m in PATCHES}


if __name__ == "__main__":
    fonts = sys.argv[1:]
    if not fonts:
        print("usage: apply.py FONT.ttf [FONT.ttf ...]")
        raise SystemExit(2)
    rc = 0
    for path in fonts:
        for ch, res in apply_all(path).items():
            print(f"  [{ch}] {res}: {os.path.basename(path)}")
            if res == "skip":
                rc = 1
    raise SystemExit(rc)
