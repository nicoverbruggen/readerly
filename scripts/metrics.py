"""
FontForge: Set Vertical Metrics
───────────────────────────────
Measures design landmarks, sets OS/2 Typo metrics to the ink boundaries,
and enables USE_TYPO_METRICS.  Win/hhea are set to initial values here
but will be overridden by lineheight.py.

Run inside FontForge  (File → Execute Script → paste, or fontforge -script).
"""

import fontforge

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _bbox(name):
    """Return bounding box (xmin, ymin, xmax, ymax) or None."""
    if name in f and f[name].isWorthOutputting():
        bb = f[name].boundingBox()
        if bb != (0, 0, 0, 0):
            return bb
    return None


def measure_chars(chars, *, axis="top"):
    """
    Measure a set of reference characters.
      axis="top"    → return the highest yMax
      axis="bottom" → return the lowest  yMin
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

for label, val, ch in [("Cap height", cap_h, cap_c),
                        ("Ascender",   asc_h, asc_c),
                        ("x-height",   xht_h, xht_c),
                        ("Descender",  dsc_h, dsc_c)]:
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
# STEP 3 — Set OS/2 Typo to ink boundaries
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

upm = f.em

design_top = asc_h if asc_h is not None else cap_h
design_bot = dsc_h   # negative value

if design_top is None or design_bot is None:
    raise SystemExit(
        "ERROR: Could not measure ascender/cap-height or descender.\n"
        "       Make sure your font contains basic Latin glyphs (H, b, p, etc.)."
    )

typo_ascender  = int(round(design_top))
typo_descender = int(round(design_bot))

f.os2_typoascent  = typo_ascender
f.os2_typodescent = typo_descender
f.os2_typolinegap = 0

# Win/hhea set to same initial values; lineheight.py overrides these.
f.os2_winascent  = typo_ascender
f.os2_windescent = abs(typo_descender)
f.hhea_ascent    = typo_ascender
f.hhea_descent   = typo_descender
f.hhea_linegap   = 0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — USE_TYPO_METRICS (fsSelection bit 7)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

typo_metrics_set = False

if hasattr(f, "os2_use_typo_metrics"):
    f.os2_use_typo_metrics = True
    typo_metrics_set = True

if not typo_metrics_set and hasattr(f, "os2_fsselection"):
    f.os2_fsselection |= (1 << 7)
    typo_metrics_set = True

if not typo_metrics_set:
    if hasattr(f, "os2_version") and f.os2_version < 4:
        f.os2_version = 4

if not typo_metrics_set:
    print("  WARNING: Could not set USE_TYPO_METRICS programmatically.")
    print("  -> In Font Info -> OS/2 -> Misc, tick 'USE_TYPO_METRICS'.\n")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5 — Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

typo_line = typo_ascender - typo_descender

print(f"\n─── Applied metrics ───\n")
print(f"  UPM:  {upm}")
print(f"  Typo: {typo_ascender} / {typo_descender} (ink span: {typo_line}, {typo_line/upm:.2f}x UPM)")

if cap_h is not None:
    print(f"  Cap height:   {int(cap_h)}")
if xht_h is not None:
    print(f"  x-height:     {int(xht_h)}")

print("\nDone.")
