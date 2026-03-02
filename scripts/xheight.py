"""
FontForge: Adjust x-height / cap-height ratio
═══════════════════════════════════════════════
Scales all lowercase glyphs (including full Latin Extended) to hit a target
x-height ratio, with optional stroke-weight compensation and proportional
sidebearing adjustment.

Run inside FontForge  (File → Execute Script → paste, or fontforge -script).

After running:
  1. Visually inspect a handful of glyphs (a e g l ö ñ)
  2. Re-run set_metrics.py to recalculate vertical metrics
  3. Review and regenerate kerning  (Metrics → Auto Kern or manual review)
"""

import fontforge
import psMat
import math
import unicodedata

f = fontforge.activeFont()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Target x-height / cap-height ratio.
#   Bookerly ≈ 0.71,  Georgia ≈ 0.70,  Times New Roman ≈ 0.65
TARGET_RATIO = 0.71

# Stroke-weight compensation.
# Uniform scaling makes stems thicker by the same factor.  This reverses it.
#   1.0  = full compensation (stems restored to original thickness)
#   0.5  = half compensation (split the difference — often looks best)
#   0.0  = no compensation (accept thicker stems)
WEIGHT_COMPENSATION = 0.75

# Sidebearing strategy after scaling.
#   "proportional"  — bearings scale with the glyph (wider set, correct feel)
#   "preserve"      — keep original bearings (tighter, may look cramped)
BEARING_MODE = "proportional"

# Safety: preview what would happen without changing anything.
DRY_RUN = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _measure_top(chars):
    """Return the highest yMax among the given reference characters."""
    best = None
    for ch in chars:
        name = fontforge.nameFromUnicode(ord(ch))
        if name in f and f[name].isWorthOutputting():
            bb = f[name].boundingBox()
            if bb != (0, 0, 0, 0):
                y = bb[3]
                if best is None or y > best:
                    best = y
    return best


def _measure_stem_width():
    """
    Estimate vertical-stem width from lowercase 'l'.

    For sans-serif fonts the bbox width of 'l' ≈ the stem.
    For serif fonts it includes serifs, so we take ~60% as an estimate.
    The WEIGHT_COMPENSATION factor lets the user tune this.
    """
    for ch in "li":
        name = fontforge.nameFromUnicode(ord(ch))
        if name in f and f[name].isWorthOutputting():
            bb = f[name].boundingBox()
            bbox_w = bb[2] - bb[0]
            if bbox_w > 0:
                return bbox_w
    return None


def _is_lowercase_glyph(glyph):
    """
    Return True if this glyph should be treated as lowercase.

    Covers:
      • Unicode category Ll  (Letter, lowercase)  — a-z, à, é, ñ, ø, ß, …
      • A few special cases that live at x-height but aren't Ll
    """
    if glyph.unicode < 0:
        return False
    try:
        cat = unicodedata.category(chr(glyph.unicode))
    except (ValueError, OverflowError):
        return False

    if cat == "Ll":
        return True

    # Catch x-height symbols that should scale with lowercase:
    #   ª (U+00AA, Lo) — feminine ordinal indicator
    #   º (U+00BA, Lo) — masculine ordinal indicator
    if glyph.unicode in (0x00AA, 0x00BA):
        return True

    return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — Measure the font
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("─── Measuring ───\n")

cap_height = _measure_top("HIOXE")
x_height   = _measure_top("xzouv")

if cap_height is None or x_height is None:
    raise SystemExit(
        "ERROR: Cannot measure cap height or x-height.\n"
        "       Make sure the font has basic Latin glyphs (H, x, etc.)."
    )

current_ratio = x_height / cap_height
scale_factor  = (TARGET_RATIO * cap_height) / x_height

print(f"  Cap height:     {int(cap_height)}")
print(f"  x-height:       {int(x_height)}")
print(f"  Current ratio:  {current_ratio:.4f}")
print(f"  Target ratio:   {TARGET_RATIO}")
print(f"  Scale factor:   {scale_factor:.4f}  ({(scale_factor - 1) * 100:+.1f}%)")

if abs(scale_factor - 1.0) < 0.005:
    raise SystemExit("\nFont is already at (or very near) the target ratio. Nothing to do.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — Stem-width measurement (for weight compensation)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

stem_bbox_w   = _measure_stem_width()
weight_delta  = 0

if WEIGHT_COMPENSATION > 0 and stem_bbox_w:
    # For a serif font the bbox includes serifs; the true stem is narrower.
    # We use 55% of bbox width as a rough stem estimate.  The WEIGHT_COMPENSATION
    # factor (0–1) provides further control.
    estimated_stem  = stem_bbox_w * 0.55
    raw_thickening  = estimated_stem * (scale_factor - 1.0)
    weight_delta    = -(raw_thickening * WEIGHT_COMPENSATION)

    print(f"\n  Stem bbox ('l'):  {stem_bbox_w:.0f}")
    print(f"  Est. stem width:  {estimated_stem:.0f}")
    print(f"  Weight delta:     {weight_delta:.1f}  (compensation = {WEIGHT_COMPENSATION:.0%})")
elif WEIGHT_COMPENSATION > 0:
    print("\n  ⚠  Could not measure stem width — skipping weight compensation.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — Collect target glyphs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

targets = []
for g in f.glyphs():
    if g.isWorthOutputting() and _is_lowercase_glyph(g):
        targets.append(g)

targets.sort(key=lambda g: g.unicode)

print(f"\n─── Target glyphs: {len(targets)} ───\n")

# Show a readable sample
sample = [g for g in targets if g.unicode < 0x0180]  # Basic Latin + Supplement
if sample:
    line = "  "
    for g in sample:
        line += chr(g.unicode)
        if len(line) > 76:
            print(line)
            line = "  "
    if line.strip():
        print(line)

extended = len(targets) - len(sample)
if extended > 0:
    print(f"  … plus {extended} extended glyphs (Latin Extended, Cyrillic, etc.)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4 — Apply transforms
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if DRY_RUN:
    print("\n  ★ DRY RUN — no changes made.  Set DRY_RUN = False to apply.\n")
    raise SystemExit(0)

print(f"\n─── Applying (scale ×{scale_factor:.4f}) ───\n")

mat        = psMat.scale(scale_factor)
errors     = []
weight_ok  = 0
weight_err = 0
skipped_composites = 0

for g in targets:
    gname = g.glyphname

    # ── 1. Skip composites ────────────────────────────────────────────────────
    #    Composite glyphs (é = e + accent) reference base glyphs that we're
    #    already scaling.  The composite automatically picks up the scaled base.
    #    Decomposing would flatten the references and double-scale the outlines.
    if g.references:
        skipped_composites += 1
        continue

    # ── 2. Store original metrics ────────────────────────────────────────────
    orig_lsb   = g.left_side_bearing
    orig_rsb   = g.right_side_bearing
    orig_width = g.width
    orig_bb    = g.boundingBox()

    # ── 3. Uniform scale from origin (0, baseline) ──────────────────────────
    g.transform(mat)

    # ── 4. Stroke-weight compensation ────────────────────────────────────────
    if weight_delta != 0:
        try:
            g.changeWeight(weight_delta)
            g.correctDirection()
            weight_ok += 1
        except Exception as e:
            weight_err += 1
            errors.append((gname, str(e)))

    # ── 5. Fix baseline shift ────────────────────────────────────────────────
    #    changeWeight can shift outlines off the baseline.  If the glyph
    #    originally sat on y=0, nudge it back.
    new_bb = g.boundingBox()
    if orig_bb[1] == 0 and new_bb[1] != 0:
        shift = -new_bb[1]
        g.transform(psMat.translate(0, shift))

    # ── 6. Fix sidebearings / advance width ──────────────────────────────────
    if BEARING_MODE == "proportional":
        # Scale bearings by the same factor → glyph is proportionally wider.
        g.left_side_bearing  = int(round(orig_lsb * scale_factor))
        g.right_side_bearing = int(round(orig_rsb * scale_factor))
    else:
        # Restore original bearings → glyph is same width, just taller.
        g.left_side_bearing  = int(round(orig_lsb))
        g.right_side_bearing = int(round(orig_rsb))

scaled_count = len(targets) - skipped_composites
print(f"  Scaled {scaled_count} glyphs (skipped {skipped_composites} composites).")
if weight_delta != 0:
    print(f"  Weight compensation: {weight_ok} OK, {weight_err} errors.")
if errors:
    print(f"\n  Glyphs with changeWeight errors (review manually):")
    for nm, err in errors[:20]:
        print(f"    {nm}: {err}")
    if len(errors) > 20:
        print(f"    … and {len(errors) - 20} more.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5 — Verify & update OS/2 fields
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

new_xh = _measure_top("xzouv")
new_ratio = new_xh / cap_height if new_xh else None

# Update the OS/2 sxHeight field (informational, used by some renderers)
if hasattr(f, "os2_xheight") and new_xh:
    f.os2_xheight = int(round(new_xh))

# If the font records cap height in OS/2 sCapHeight, keep it consistent
if hasattr(f, "os2_capheight") and cap_height:
    f.os2_capheight = int(round(cap_height))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6 — Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n─── Results ───\n")
print(f"  Cap height:     {int(cap_height)}  (unchanged)")
print(f"  Old x-height:   {int(x_height)}")
print(f"  New x-height:   {int(new_xh) if new_xh else 'N/A'}")
print(f"  Old ratio:      {current_ratio:.4f}")
print(f"  New ratio:      {new_ratio:.4f}" if new_ratio else "  New ratio:      N/A")
print(f"  Target was:     {TARGET_RATIO}")

# Check how ascenders shifted
asc_h = _measure_top("bdfhkl")
if asc_h:
    over = asc_h - cap_height
    if over > 2:
        print(f"\n  ℹ  Ascenders now sit at {int(asc_h)}, which is {int(over)} units above cap height.")
        print(f"     This is normal and common in many typefaces.")
    else:
        print(f"\n  Ascenders at {int(asc_h)} (≈ cap height).")

print("\n─── Next steps ───\n")
print("  1. Inspect glyphs:  a e g l o ö ñ ß — look for weight/shape issues")
print("  2. Run set_metrics.py to recalculate vertical metrics")
print("  3. Regenerate kerning  (Metrics → Auto Kern, or review manually)")
print("  4. If weight looks off, adjust WEIGHT_COMPENSATION and re-run")
print("     (Ctrl+Z to undo all changes first)\n")
print("Done.")
