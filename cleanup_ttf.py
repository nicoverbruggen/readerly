#!/usr/bin/env python3
"""
Remove zero-area contours from a TTF.

Some FontForge exports emit 1–2 point contours that macOS can treat as
invalid and skip the glyph entirely. This script removes those contours
in-place.
"""

import sys


def clean_ttf_degenerate_contours(ttf_path):
    try:
        from fontTools.ttLib import TTFont
        from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
    except Exception as exc:
        raise SystemExit(f"ERROR: fontTools is required ({exc})")

    font = TTFont(ttf_path)
    glyf = font["glyf"]  # type: ignore[index]

    removed_total = 0
    modified = set()
    for name in font.getGlyphOrder():
        glyph = glyf[name]  # type: ignore[index]
        if glyph.isComposite():
            continue
        end_pts = getattr(glyph, "endPtsOfContours", None)
        if not end_pts:
            continue

        coords = glyph.coordinates
        flags = glyph.flags

        new_coords = []
        new_flags = []
        new_end_pts = []

        start = 0
        removed = 0
        for end in end_pts:
            count = end - start + 1
            if count <= 2:
                removed += 1
            else:
                new_coords.extend(coords[start:end + 1])
                new_flags.extend(flags[start:end + 1])
                new_end_pts.append(len(new_coords) - 1)
            start = end + 1

        if removed:
            removed_total += removed
            modified.add(name)
            glyph.coordinates = GlyphCoordinates(new_coords)
            glyph.flags = new_flags
            glyph.endPtsOfContours = new_end_pts
            glyph.numberOfContours = len(new_end_pts)

    if removed_total:
        glyph_set = font.getGlyphSet()
        for name in modified:
            glyph = glyf[name]  # type: ignore[index]
            if hasattr(glyph, "recalcBounds"):
                glyph.recalcBounds(glyph_set)
        if hasattr(glyf, "recalcBounds"):
            glyf.recalcBounds(glyph_set)  # type: ignore[attr-defined]
        font.save(ttf_path)

    font.close()
    return removed_total


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 cleanup_ttf.py path/to/font.ttf")
    ttf_path = sys.argv[1]
    removed = clean_ttf_degenerate_contours(ttf_path)
    print(f"Cleaned {removed} zero-area contour(s): {ttf_path}")


if __name__ == "__main__":
    main()
