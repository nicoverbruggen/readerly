"""
FontForge: Scale lowercase glyphs vertically
─────────────────────────────────────────────
Applies a vertical scale to lowercase glyphs only, from glyph origin,
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
import unicodedata

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCALE_X = 1.03
SCALE_Y = 1.10

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mat = psMat.scale(SCALE_X, SCALE_Y)

# Select only lowercase glyphs
f.selection.none()
count = 0
for g in f.glyphs():
    if g.unicode < 0:
        continue
    try:
        cat = unicodedata.category(chr(g.unicode))
    except (ValueError, OverflowError):
        continue
    if cat == "Ll" or g.unicode in (0x00AA, 0x00BA):
        f.selection.select(("more",), g.glyphname)
        count += 1

f.transform(mat, ("round",))

print(f"  Scaled {count} lowercase glyphs by X={SCALE_X:.0%}, Y={SCALE_Y:.0%}")
print("Done.")
