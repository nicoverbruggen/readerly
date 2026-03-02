"""
FontForge: Scale all glyphs vertically
───────────────────────────────────────
Applies a vertical scale to all glyphs from glyph origin,
matching the Transform dialog with all options checked:

  - Transform All Layers
  - Transform Guide Layer Too
  - Transform Width Too
  - Transform kerning classes too
  - Transform simple positioning features & kern pairs
  - Round To Int

Run inside FontForge (or via build.py which sets `f` before running this).
"""

import fontforge
import psMat

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCALE_X = 1.0
SCALE_Y = 1.0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mat = psMat.scale(SCALE_X, SCALE_Y)

# Select all glyphs
f.selection.all()

# Transform with all options enabled.
# FontForge flag names:
#   partialTrans      — transform selected points only (we don't want this)
#   round             — Round To Int
# The font-level transform handles layers, widths, kerning, and positioning
# when called on the full selection.
f.transform(mat, ("round",))

count = sum(1 for g in f.glyphs() if g.isWorthOutputting())
print(f"  Scaled {count} glyphs by X={SCALE_X:.0%}, Y={SCALE_Y:.0%}")
print("Done.")
