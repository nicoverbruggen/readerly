"""
FontForge: Remove overlapping contours
───────────────────────────────────────
Merges overlapping contours into clean outlines for all glyphs.
Also corrects winding direction, which can get flipped after overlap removal.

This fixes rendering issues on devices (e.g. Kobo) that struggle with
overlapping paths, especially when applying synthetic bold/weight scaling.

Run inside FontForge (or via build.py which sets `f` before running this).
"""

import fontforge

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

f.selection.all()

f.removeOverlap()
f.correctDirection()

count = sum(1 for g in f.glyphs() if g.isWorthOutputting())
print(f"  Removed overlaps and corrected direction for {count} glyphs")
print("Done.")
