"""
FontForge: Condense all glyphs horizontally
────────────────────────────────────────────
Applies a horizontal scale to all glyphs, reducing set width.

Run inside FontForge (or via build.py which sets `f` before running this).
"""

import fontforge
import psMat

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCALE_X = 0.95

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mat = psMat.scale(SCALE_X, 1.0)

f.selection.all()
f.transform(mat, ("round",))

count = sum(1 for g in f.glyphs() if g.isWorthOutputting())
print(f"  Condensed {count} glyphs by X={SCALE_X:.0%}")
print("Done.")
