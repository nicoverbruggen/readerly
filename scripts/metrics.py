"""
FontForge: Set Vertical Metrics
───────────────────────────────
Follows the Google Fonts vertical-metrics methodology:

  • OS/2 Typo  → controls line spacing  (with USE_TYPO_METRICS / fsSelection bit 7)
  • OS/2 Win   → clipping boundary on Windows  (must cover every glyph)
  • hhea       → line spacing + clipping on macOS/iOS

Run inside FontForge  (File → Execute Script → paste, or fontforge -script).
"""

import fontforge
import math

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Extra padding on Win and hhea metrics, as a fraction of UPM.
# Prevents clipping of glyphs that sit right at the bounding-box edge.
#   0.0  = trust the bounding boxes exactly
#   0.01 = 1% pad (conservative)
#   0.02 = 2% pad (safe for hinting artefacts / composites)
CLIP_MARGIN = 0.01

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _bbox(name):
    """Return bounding box (xmin, ymin, xmax, ymax) or None."""
    if name in f and f[name].isWorthOutputting():
        bb = f[name].boundingBox()
        if bb != (0, 0, 0, 0):          # skip empty glyphs (space, CR, …)
            return bb
    return None


def measure_chars(chars, *, axis="top"):
    """
    Measure a set of reference characters.
      axis="top"    → return the highest yMax  (ascenders, cap height)
      axis="bottom" → return the lowest  yMin  (descenders)
    Returns (value, display_char) or (None, None).
    """
    idx   = 3 if axis == "top" else 1
    pick  = max if axis == "top" else min
    hits  = []
    for ch in chars:
        name = fontforge.nameFromUnicode(ord(ch))
        bb   = _bbox(name)
        if bb is not None:
            hits.append((bb[idx], ch))
    if not hits:
        return None, None
    return pick(hits, key=lambda t: t[0])


def scan_font_extremes():
    """Walk every output glyph; return (yMax, yMin, max_name, min_name)."""
    y_max, y_min     = 0, 0
    max_nm, min_nm   = None, None
    for g in f.glyphs():
        if not g.isWorthOutputting():
            continue
        bb = g.boundingBox()
        if bb == (0, 0, 0, 0):
            continue
        if bb[3] > y_max:
            y_max, max_nm = bb[3], g.glyphname
        if bb[1] < y_min:
            y_min, min_nm = bb[1], g.glyphname
    return y_max, y_min, max_nm, min_nm


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — Measure design landmarks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("─── Design landmarks ───\n")

cap_h, cap_c = measure_chars("HIOXE",    axis="top")
asc_h, asc_c = measure_chars("bdfhkl",   axis="top")
xht_h, xht_c = measure_chars("xzouv",    axis="top")
dsc_h, dsc_c = measure_chars("gpqyj",    axis="bottom")
acc_h, acc_c = measure_chars("\u00c0\u00c1\u00c2\u00c3\u00c4\u00c5\u00c8\u00c9\u00ca\u00cb", axis="top")
acd_h, acd_c = measure_chars("\u00c7\u015e\u0162",  axis="bottom")

for label, val, ch in [("Cap height", cap_h, cap_c),
                        ("Ascender",   asc_h, asc_c),
                        ("Accent top", acc_h, acc_c),
                        ("x-height",   xht_h, xht_c),
                        ("Descender",  dsc_h, dsc_c),
                        ("Accent bot", acd_h, acd_c)]:
    if val is not None:
        print(f"  {label:12s}  {int(val):>6}  ('{ch}')")
    else:
        print(f"  {label:12s}  {'N/A':>6}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — Full-font bounding-box scan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n─── Full font scan ───\n")

font_ymax, font_ymin, ymax_name, ymin_name = scan_font_extremes()
print(f"  Highest glyph:  {int(font_ymax):>6}  ({ymax_name})")
print(f"  Lowest  glyph:  {int(font_ymin):>6}  ({ymin_name})")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — Compute the three metric sets
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

upm = f.em

# Design top = tallest Latin ascender (fall back to cap height)
design_top = asc_h if asc_h is not None else cap_h
design_bot = dsc_h   # negative value

if design_top is None or design_bot is None:
    raise SystemExit(
        "ERROR: Could not measure ascender/cap-height or descender.\n"
        "       Make sure your font contains basic Latin glyphs (H, b, p, etc.)."
    )

# ── OS/2 Typo metrics ────────────────────────────────────────────────────────
# These define line spacing when USE_TYPO_METRICS is on.
# Strategy: ascender and descender sit at the design's actual ink boundaries;
#           lineGap absorbs all extra leading.  This keeps the text vertically
#           centred on the line, which matters for UI / web layout.

typo_ascender  = int(round(design_top))
typo_descender = int(round(design_bot))          # negative
typo_extent    = typo_ascender - typo_descender   # total ink span (positive)
typo_linegap   = 0

# ── Win / hhea metrics ───────────────────────────────────────────────────────
# Clipping boundaries.  Based on the design ascender/descender with a small
# margin.  Accented capitals and stacked diacritics may clip, but line
# height stays tight on all platforms.

margin       = int(math.ceil(upm * CLIP_MARGIN))

win_ascent   = int(math.ceil(design_top))  + margin
win_descent  = int(math.ceil(abs(design_bot))) + margin

hhea_ascent  = win_ascent
hhea_descent = -win_descent   # negative
hhea_linegap = 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — Apply to font
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Keep f.ascent / f.descent at their current values — they define UPM
# (f.ascent + f.descent = f.em) and must not be changed.

# OS/2 table
f.os2_typoascent    = typo_ascender
f.os2_typodescent    = typo_descender
f.os2_typolinegap    = typo_linegap
f.os2_winascent      = win_ascent
f.os2_windescent     = win_descent

# hhea table
f.hhea_ascent        = hhea_ascent
f.hhea_descent       = hhea_descent
f.hhea_linegap       = hhea_linegap

# USE_TYPO_METRICS — fsSelection bit 7
# FontForge exposes this differently across versions.  We try three known paths.
typo_metrics_set = False

# Method 1: dedicated boolean (FontForge ≥ 2020-ish)
if hasattr(f, "os2_use_typo_metrics"):
    f.os2_use_typo_metrics = True
    typo_metrics_set = True

# Method 2: direct fsSelection manipulation (if exposed)
if not typo_metrics_set and hasattr(f, "os2_fsselection"):
    f.os2_fsselection |= (1 << 7)
    typo_metrics_set = True

# Method 3: via the OS/2 version (some builds gate the flag on version ≥ 4)
if not typo_metrics_set:
    if hasattr(f, "os2_version") and f.os2_version < 4:
        f.os2_version = 4

if not typo_metrics_set:
    print("⚠  Could not set USE_TYPO_METRICS programmatically.")
    print("   → In Font Info → OS/2 → Misc, tick 'USE_TYPO_METRICS'.\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5 — Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

typo_line  = typo_ascender - typo_descender + typo_linegap
hhea_line  = hhea_ascent   - hhea_descent   + hhea_linegap
win_total  = win_ascent    + win_descent

print("\n─── Applied metrics ───\n")
print(f"  UPM:  {upm}\n")

print(f"  {'':18s}  {'Ascender':>9s}  {'Descender':>10s}  {'LineGap':>8s}  {'Total':>6s}")
print(f"  {'─'*18}  {'─'*9}  {'─'*10}  {'─'*8}  {'─'*6}")
print(f"  {'OS/2 Typo':18s}  {typo_ascender:>9d}  {typo_descender:>10d}  {typo_linegap:>8d}  {typo_line:>6d}")
print(f"  {'hhea':18s}  {hhea_ascent:>9d}  {hhea_descent:>10d}  {hhea_linegap:>8d}  {hhea_line:>6d}")
print(f"  {'OS/2 Win':18s}  {win_ascent:>9d}  {'-'+str(win_descent):>10s}  {'n/a':>8s}  {win_total:>6d}")

print(f"\n  Effective line height:  {typo_line}  ({typo_line/upm:.2f}× UPM)")
print(f"  Design ink span:       {typo_extent}  ({typo_extent/upm:.2f}× UPM)")
print(f"  Clipping headroom:     +{win_ascent - int(round(font_ymax))} above, "
      f"+{win_descent - int(round(abs(font_ymin)))} below")

if cap_h is not None:
    print(f"\n  Cap height:   {int(cap_h)}")
if xht_h is not None:
    print(f"  x-height:     {int(xht_h)}")

print("\nDone. Review in Font Info → OS/2 and Font Info → General.")
