"""Shared helpers for per-glyph outline patches.

Each patch is defined as two coordinate maps over the glyph's point indices:
  ORIGINAL — the coordinates the patch expects to find (the un-patched build).
  TARGET   — the coordinates it sets.

A patch may also list point indices to REMOVE (deleting nodes to simplify a
contour). Indices in ORIGINAL/TARGET/REMOVE all refer to the un-patched glyph.

`apply_patch` is idempotent and self-guarding:
  - if the touched points already equal TARGET (and nothing is being removed),
    it does nothing;
  - if they equal ORIGINAL, it writes TARGET (and removes any REMOVE indices);
  - otherwise the outline isn't what the patch was authored against (the source
    font changed), so it refuses rather than corrupt the glyph.

Patches set absolute coordinates, so re-running a build never compounds them.
Removal is safe to re-run because the build regenerates each glyph fresh; on an
already-trimmed outline the ORIGINAL guard no longer matches, so it skips.
"""

import array

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def load(path):
    return TTFont(path)


def glyph_for_char(font, ch):
    name = font.getBestCmap()[ord(ch)]
    return name, font["glyf"][name]


def _matches(coords, points):
    return all(tuple(coords[i]) == tuple(xy) for i, xy in points.items())


def _remove_points(glyph, remove):
    """Delete point indices from a simple glyph, fixing contour end offsets."""
    keep = [i for i in range(len(glyph.coordinates)) if i not in remove]
    glyph.coordinates = GlyphCoordinates([glyph.coordinates[i] for i in keep])
    glyph.flags = array.array("B", [glyph.flags[i] for i in keep])
    glyph.endPtsOfContours = [
        end - sum(1 for r in remove if r <= end)
        for end in glyph.endPtsOfContours
    ]


def apply_patch(path, ch, original, target, label, remove=None):
    """Apply one glyph patch in place. Returns one of: applied|already|skip."""
    remove = set(remove or ())
    font = load(path)
    name, glyph = glyph_for_char(font, ch)
    coords = glyph.coordinates

    touched = set(target) | set(original) | remove
    bad = [i for i in touched if i >= len(coords)]
    if bad:
        print(f"  [{ch}] skip: point index out of range {bad} (glyph has "
              f"{len(coords)} points)")
        font.close()
        return "skip"

    if not remove and _matches(coords, target):
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
    if remove:
        _remove_points(glyph, remove)
    if hasattr(glyph, "recalcBounds"):
        glyph.recalcBounds(font["glyf"])
    font.save(path)
    font.close()
    return "applied"


def run_cli(ch, original, target, label, remove=None):
    """Standalone entry point: python3 <patch>.py FONT.ttf [FONT2.ttf ...]."""
    import sys
    fonts = sys.argv[1:]
    if not fonts:
        print(f"usage: {sys.argv[0]} FONT.ttf [FONT.ttf ...]")
        return 2
    rc = 0
    for path in fonts:
        result = apply_patch(path, ch, original, target, label, remove)
        print(f"  [{ch}] {result}: {path}")
        if result == "skip":
            rc = 1
    return rc
