"""Shared helpers for per-glyph outline patches.

Each patch is defined as two coordinate maps over the glyph's point indices:
  ORIGINAL — the coordinates the patch expects to find (the un-patched build).
  TARGET   — the coordinates it sets.

`apply_patch` is idempotent and self-guarding:
  - if the touched points already equal TARGET, it does nothing;
  - if they equal ORIGINAL, it writes TARGET;
  - otherwise the outline isn't what the patch was authored against (the source
    font changed), so it refuses rather than corrupt the glyph.

Patches set absolute coordinates, so re-running a build never compounds them.
"""

from fontTools.ttLib import TTFont


def load(path):
    return TTFont(path)


def glyph_for_char(font, ch):
    name = font.getBestCmap()[ord(ch)]
    return name, font["glyf"][name]


def _matches(coords, points):
    return all(tuple(coords[i]) == tuple(xy) for i, xy in points.items())


def apply_patch(path, ch, original, target, label):
    """Apply one glyph patch in place. Returns one of: applied|already|skip."""
    font = load(path)
    name, glyph = glyph_for_char(font, ch)
    coords = glyph.coordinates

    bad = [i for i in target if i >= len(coords)]
    if bad:
        print(f"  [{ch}] skip: point index out of range {bad} (glyph has "
              f"{len(coords)} points)")
        font.close()
        return "skip"

    if _matches(coords, target):
        font.close()
        return "already"

    if not _matches(coords, original):
        cur = {i: tuple(coords[i]) for i in original}
        print(f"  [{ch}] skip: outline differs from the expected baseline "
              f"({label}). expected {original}, found {cur}")
        font.close()
        return "skip"

    for i, xy in target.items():
        coords[i] = tuple(xy)
    if hasattr(glyph, "recalcBounds"):
        glyph.recalcBounds(font["glyf"])
    font.save(path)
    font.close()
    return "applied"


def run_cli(ch, original, target, label):
    """Standalone entry point: python3 <patch>.py FONT.ttf [FONT2.ttf ...]."""
    import sys
    fonts = sys.argv[1:]
    if not fonts:
        print(f"usage: {sys.argv[0]} FONT.ttf [FONT.ttf ...]")
        return 2
    rc = 0
    for path in fonts:
        result = apply_patch(path, ch, original, target, label)
        print(f"  [{ch}] {result}: {path}")
        if result == "skip":
            rc = 1
    return rc
