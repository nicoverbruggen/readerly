"""
FontForge: Adjust line height
──────────────────────────────
Sets vertical metrics to control line spacing and selection box height.

- Typo:     controls line spacing (via USE_TYPO_METRICS)
- Win/hhea: controls selection box height and clipping

Run inside FontForge (or via build.py which sets `f` before running this).
"""

import fontforge

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Line height (Typo) as a multiple of UPM.
LINE_HEIGHT = 1.0

# Selection box height (Win/hhea) as a multiple of UPM.
SELECTION_HEIGHT = 1.32

# Ascender share of the line/selection height.
ASCENDER_RATIO = 0.80

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# APPLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

upm = f.em

# OS/2 Typo — controls line spacing
typo_total = int(round(upm * LINE_HEIGHT))
typo_asc   = int(round(typo_total * ASCENDER_RATIO))
typo_dsc   = typo_asc - typo_total   # negative

f.os2_typoascent  = typo_asc
f.os2_typodescent = typo_dsc
f.os2_typolinegap = 0

# Win/hhea — controls selection box height and clipping
sel_total = int(round(upm * SELECTION_HEIGHT))
sel_asc   = int(round(sel_total * ASCENDER_RATIO))
sel_dsc   = sel_total - sel_asc

f.hhea_ascent    = sel_asc
f.hhea_descent   = -sel_dsc
f.hhea_linegap   = 0
f.os2_winascent  = sel_asc
f.os2_windescent = sel_dsc

print(f"  Typo: {typo_asc} / {typo_dsc} / gap 0  (line height: {typo_total}, {LINE_HEIGHT:.2f}x UPM)")
print(f"  hhea: {sel_asc} / {-sel_dsc} / gap 0  (selection: {sel_total}, {SELECTION_HEIGHT:.2f}x UPM)")
print(f"  Win:  {sel_asc} / {sel_dsc}")
print("Done.")
