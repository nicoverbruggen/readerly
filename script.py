import fontforge

f = fontforge.activeFont()

CAPS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DESCENT_GLYPHS = list("gjpqy")

# ── Tweak these ───────────────────────────────────────────────────────────────
LINE_GAP_FACTOR = 0.0   # 0.15 = 15% gap, 0.0 = no gap
OVERLAP_FACTOR  = 0.0    # 0.0 = no overlap, 0.05 = 5% overlap (overrides gap)
# ─────────────────────────────────────────────────────────────────────────────

def measure(glyphs, use_max=True):
    values = []
    for ch in glyphs:
        name = fontforge.nameFromUnicode(ord(ch))
        if name in f and f[name].isWorthOutputting():
            bb = f[name].boundingBox()
            values.append(bb[3] if use_max else bb[1])
    if not values:
        return None
    return max(values) if use_max else min(values)

ascent  = measure(CAPS, use_max=True)
descent = measure(DESCENT_GLYPHS, use_max=False)

print(f"Measured ascent:  {ascent}")
print(f"Measured descent: {descent}")

if ascent is None or descent is None:
    print("Could not measure glyphs — check glyph names in your font.")
else:
    ascent_val  = int(ascent)
    descent_val = int(descent)

    # Rescale to preserve original UPM
    upm   = f.em
    total = ascent_val + abs(descent_val)
    ascent_val  =  int(ascent_val        * (upm / total))
    descent_val = -int(abs(descent_val)  * (upm / total))

    print(f"Rescaled to UPM {upm} — Ascent: {ascent_val}, Descent: {descent_val}")

    overlap      = int(ascent_val * OVERLAP_FACTOR)
    half_overlap = overlap // 2
    line_gap     = int(ascent_val * LINE_GAP_FACTOR) if OVERLAP_FACTOR == 0.0 else 0

    f.ascent         = ascent_val
    f.os2_typoascent = ascent_val - half_overlap
    f.hhea_ascent    = ascent_val - half_overlap
    f.os2_winascent  = ascent_val - half_overlap

    f.descent         = abs(descent_val)
    f.os2_typodescent = descent_val + half_overlap
    f.hhea_descent    = descent_val + half_overlap
    f.os2_windescent  = abs(descent_val) - half_overlap

    f.os2_typolinegap = line_gap
    f.hhea_linegap    = line_gap

    try:
        f.os2_stylemap = f.os2_stylemap | (1 << 7)
    except AttributeError:
        print("Note: set USE_TYPO_METRICS manually in Font Info > OS/2")

    line_height = (ascent_val - half_overlap) + (abs(descent_val) - half_overlap) + line_gap
    print(f"Line gap: {line_gap}, Overlap: {overlap}, Effective line height: {line_height}")
