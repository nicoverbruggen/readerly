#!/usr/bin/env python3
"""Apply per-glyph outline patches to the given font(s).

    python3 scripts/glyph_patches/apply.py FONT.ttf [FONT.ttf ...]

Patches live in a per-style subfolder next to this file — e.g. all the patches
for the Regular style are in ./regular/. The style is inferred from each font's
filename (Readerly-Regular.ttf -> regular), and only that style's patches are
applied; a font whose style has no subfolder is left untouched. So this can be
run over every built style and each gets exactly its own patches.

Each patch is idempotent and self-guarding, so re-running, or running on an
already-patched / unexpected outline, is a no-op skip rather than a corruption.
Exit code is non-zero only if a patch was skipped due to an unexpected outline.
"""

import glob
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # so patch modules can `from _lib import ...`

from _lib import apply_patch  # noqa: E402


def style_from_path(path):
    """'…/Readerly-Regular.ttf' -> 'regular' (lowercased style suffix)."""
    m = re.search(r"-([A-Za-z]+)\.ttf$", os.path.basename(path))
    return m.group(1).lower() if m else ""


def load_patches(style):
    """Import every patch module in ./<style>/ (sorted, skipping _*)."""
    folder = os.path.join(HERE, style)
    if not os.path.isdir(folder):
        return []
    mods = []
    for f in sorted(glob.glob(os.path.join(folder, "*.py"))):
        if os.path.basename(f).startswith("_"):
            continue
        name = f"glyph_patches_{style}_{os.path.basename(f)[:-3]}"
        spec = importlib.util.spec_from_file_location(name, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mods.append(mod)
    return mods


def apply_all(path):
    """Apply the patches matching this font's style. Returns {char: result}."""
    style = style_from_path(path)
    return {m.CHAR: apply_patch(path, m.CHAR, m.ORIGINAL, m.TARGET, m.LABEL,
                                getattr(m, "REMOVE", None))
            for m in load_patches(style)}


if __name__ == "__main__":
    fonts = sys.argv[1:]
    if not fonts:
        print("usage: apply.py FONT.ttf [FONT.ttf ...]")
        raise SystemExit(2)
    rc = 0
    for path in fonts:
        results = apply_all(path)
        if not results:
            print(f"  (no patches for style "
                  f"'{style_from_path(path) or '?'}'): {os.path.basename(path)}")
        for ch, res in results.items():
            print(f"  [{ch}] {res}: {os.path.basename(path)}")
            if res == "skip":
                rc = 1
    raise SystemExit(rc)
